from __future__ import annotations

from contextlib import closing

import json
import re
from typing import Any

from app.db.pharma.release_connection import connect_release


def _normalize_name(value: str) -> str:
    return " ".join(value.strip().lower().split())


def _normalize_identifier(value: str) -> str:
    return re.sub(r"\s+", "", value.strip())


def _json_list(value: str | None) -> list[Any]:
    if not value:
        return []
    try:
        parsed = json.loads(value)
    except (TypeError, json.JSONDecodeError):
        return []
    return parsed if isinstance(parsed, list) else []


class FrozenPharmaReleaseRepository:
    """
    Read-only repository for the frozen Dav AI pharmaceutical release.

    This repository never mutates the release database and never falls back
    to PostgreSQL for pharmaceutical catalog reads.
    """

    def find_by_id(self, product_id: str) -> dict[str, Any] | None:
        with closing(connect_release()) as con:
            row = con.execute(
                """
                SELECT *
                FROM products
                WHERE product_id = ?
                  AND eligibility_mode = 'NORMAL_CONSUMER'
                LIMIT 1
                """,
                (product_id,),
            ).fetchone()

            if row is None:
                return None

            return self._project_product(con, row)

    def search(
        self,
        query: str,
        *,
        limit: int = 20,
        offset: int = 0,
    ) -> list[dict[str, Any]]:
        q = query.strip()
        if not q:
            return []

        normalized_name = _normalize_name(q)
        normalized_identifier = _normalize_identifier(q)

        with closing(connect_release()) as con:
            product_ids: list[str] = []

            # 1. Exact identifier matches first.
            identifier_rows = con.execute(
                """
                SELECT DISTINCT pi.product_id
                FROM product_identifiers pi
                JOIN products p ON p.product_id = pi.product_id
                WHERE pi.value = ?
                  AND p.eligibility_mode = 'NORMAL_CONSUMER'
                ORDER BY pi.product_id
                LIMIT ?
                """,
                (normalized_identifier, limit + offset),
            ).fetchall()

            product_ids.extend(row["product_id"] for row in identifier_rows)

            # 2. Exact normalized product-name matches.
            name_rows = con.execute(
                """
                SELECT DISTINCT sn.product_id
                FROM search_names sn
                JOIN products p ON p.product_id = sn.product_id
                WHERE sn.entity_type = 'PRODUCT'
                  AND sn.product_id IS NOT NULL
                  AND sn.normalized_name = ?
                  AND p.eligibility_mode = 'NORMAL_CONSUMER'
                ORDER BY sn.product_id
                LIMIT ?
                """,
                (normalized_name, limit + offset),
            ).fetchall()

            for row in name_rows:
                if row["product_id"] not in product_ids:
                    product_ids.append(row["product_id"])

            # Ingredient names must also discover combination products whose product
            # aliases do not contain the ingredient. Membership uses sealed ingredient IDs.
            ingredient_rows = con.execute(
                """
                SELECT DISTINCT pi.product_id
                FROM product_ingredients pi
                JOIN ingredients i ON i.ingredient_id = pi.ingredient_id
                JOIN products p ON p.product_id = pi.product_id
                WHERE (lower(i.canonical_name) = ? OR lower(i.canonical_name) LIKE ? ESCAPE '\\')
                  AND p.eligibility_mode = 'NORMAL_CONSUMER'
                ORDER BY pi.product_id LIMIT ?
                """,
                (normalized_name, self._escape_like(normalized_name) + "%", limit + offset),
            ).fetchall()
            for row in ingredient_rows:
                if row["product_id"] not in product_ids:
                    product_ids.append(row["product_id"])

            # 3. Prefix-name search for user-friendly catalog browsing.
            if len(product_ids) < limit + offset:
                prefix_rows = con.execute(
                    """
                    SELECT DISTINCT sn.product_id
                    FROM search_names sn
                    JOIN products p ON p.product_id = sn.product_id
                    WHERE sn.entity_type = 'PRODUCT'
                      AND sn.product_id IS NOT NULL
                      AND sn.normalized_name LIKE ? ESCAPE '\\'
                      AND p.eligibility_mode = 'NORMAL_CONSUMER'
                    ORDER BY sn.normalized_name, sn.product_id
                    LIMIT ?
                    """,
                    (
                        self._escape_like(normalized_name) + "%",
                        limit + offset,
                    ),
                ).fetchall()

                for row in prefix_rows:
                    if row["product_id"] not in product_ids:
                        product_ids.append(row["product_id"])

            selected_ids = product_ids[offset : offset + limit]

            results = []
            for product_id in selected_ids:
                row = con.execute(
                    """
                    SELECT *
                    FROM products
                    WHERE product_id = ?
                      AND eligibility_mode = 'NORMAL_CONSUMER'
                    """,
                    (product_id,),
                ).fetchone()

                if row is not None:
                    results.append(self._project_product(con, row))

            return results


    def safety(self, product_id: str) -> dict[str, Any] | None:
        with closing(connect_release()) as con:
            product = con.execute(
                """
                SELECT *
                FROM products
                WHERE product_id = ?
                  AND eligibility_mode = 'NORMAL_CONSUMER'
                LIMIT 1
                """,
                (product_id,),
            ).fetchone()

            if product is None:
                return None

            labels = self._labels(con, product_id)
            recalls = self._recalls(con, product_id)
            adverse_events = self._adverse_events(con, product_id)
            communications = self._communications(con, product_id)

            return {
                "drug_id": product_id,
                "labels": labels,
                "recalls": recalls,
                "adverse_events": adverse_events,
                "communications": communications,
            }

    def timeline(self, product_id: str) -> dict[str, Any] | None:
        with closing(connect_release()) as con:
            product = con.execute(
                """
                SELECT product_id
                FROM products
                WHERE product_id = ?
                  AND eligibility_mode = 'NORMAL_CONSUMER'
                LIMIT 1
                """,
                (product_id,),
            ).fetchone()

            if product is None:
                return None

            events: list[dict[str, Any]] = []
            labels = self._consumer_labels(con, product_id)

            for row in labels:
                if row["effective_date"]:
                    events.append({
                        "source": row["source_name"] or "openfda_drug_label",
                        "event_type": "label",
                        "date": row["effective_date"],
                        "date_type": "effective_date",
                        "title": "Preserved FDA drug label",
                        "summary": (
                            "Earlier stored applicable label"
                            if row["selection_status"] == "EARLIER_STORED"
                            else "Latest selected applicable label in preserved export"
                        ) + (
                            f"; product-scoped version {row['version_number']}."
                        ),
                        "source_url": row["provenance_source_url"],
                        "record_id": row["label_id"],
                    })

            for row in con.execute(
                """
                SELECT
                    r.recall_id,
                    r.recall_number,
                    r.product_description,
                    r.reason_for_recall,
                    r.source_reported_status,
                    r.recall_initiation_date,
                    r.report_date,
                    s.source_name,
                    s.source_url
                FROM product_recalls pr
                JOIN recalls r ON r.recall_id = pr.recall_id
                LEFT JOIN sources s ON s.source_id = r.source_id
                WHERE pr.product_id = ?
                """,
                (product_id,),
            ):
                event_date = row["recall_initiation_date"] or row["report_date"]
                if event_date:
                    events.append({
                        "source": row["source_name"] or "openfda_drug_enforcement",
                        "event_type": "recall",
                        "date": event_date,
                        "date_type": (
                            "recall_initiation_date"
                            if row["recall_initiation_date"]
                            else "report_date"
                        ),
                        "title": row["product_description"],
                        "summary": (
                            f"{row['reason_for_recall']} "
                            f"Source-reported status: "
                            f"{row['source_reported_status'] or 'not supplied'}."
                        ),
                        "source_url": row["source_url"],
                        "record_id": row["recall_id"],
                    })

            for row in con.execute(
                """
                SELECT
                    i.canonical_name,
                    sc.communication_id,
                    sc.title,
                    sc.published_date,
                    sc.source_url
                FROM product_ingredients pi
                JOIN ingredients i
                  ON i.ingredient_id = pi.ingredient_id
                JOIN drug_communications dc
                  ON dc.ingredient_id = pi.ingredient_id
                JOIN safety_communications sc
                  ON sc.communication_id = dc.communication_id
                WHERE pi.product_id = ?
                """,
                (product_id,),
            ):
                if row["published_date"]:
                    events.append({
                        "source": "fda_drug_safety_communications",
                        "event_type": "safety_communication",
                        "date": row["published_date"],
                        "date_type": "published_date",
                        "title": row["title"],
                        "summary": (
                            f"FDA communication discussing ingredient "
                            f"{row['canonical_name']}; ingredient context only, "
                            f"not product-specific applicability."
                        ),
                        "source_url": row["source_url"],
                        "record_id": row["communication_id"],
                    })

            for row in con.execute(
                """
                SELECT
                    i.canonical_name,
                    a.ingredient_id,
                    a.period,
                    a.report_count,
                    a.serious_report_count,
                    a.death_report_count,
                    a.hospitalization_report_count
                FROM product_ingredients pi
                JOIN ingredients i
                  ON i.ingredient_id = pi.ingredient_id
                JOIN ae_monthly a
                  ON a.ingredient_id = pi.ingredient_id
                WHERE pi.product_id = ?
                """,
                (product_id,),
            ):
                events.append({
                    "source": "openfda_drug_event",
                    "event_type": "ingredient_ae_reporting_activity",
                    "date": row["period"],
                    "date_type": "latest_receipt_month",
                    "title": (
                        f"FAERS reporting activity — "
                        f"{row['canonical_name']}"
                    ),
                    "summary": (
                        f"{row['report_count']} deduplicated ingredient-report "
                        f"associations in this month; "
                        f"{row['serious_report_count']} marked serious, "
                        f"{row['hospitalization_report_count']} with a "
                        f"hospitalization outcome flag, and "
                        f"{row['death_report_count']} with a death outcome flag. "
                        f"These are ingredient-level co-reporting associations, "
                        f"not product incidence or causality."
                    ),
                    "source_url": None,
                    "record_id": (
                        f"{row['ingredient_id']}:{row['period']}"
                    ),
                })

            events.sort(
                key=lambda event: (
                    event["date"] or "",
                    event["event_type"],
                    event["record_id"],
                ),
                reverse=True,
            )

            return {
                "drug_id": product_id,
                "events": events,
                "coverage": {
                    "labels": self._label_coverage(con, product_id, labels),
                    "recalls": self._coverage(con, product_id, "recalls"),
                    "adverse_events": self._coverage(
                        con, product_id, "ae_analytics"
                    ),
                },
            }

    @staticmethod
    def _consumer_labels(con, product_id: str):
        """Honor sealed product/source-set decisions; never reselect withheld rows.

        Gates mirror the release contract section 6 and schema/label validator.
        EARLIER_STORED remains usable only with explicit partial/earlier wording.
        Independent source sets are retained, rather than choosing one by date.
        """
        return con.execute(
            """
            SELECT
                l.*,
                pl.applicability_class,
                pl.match_method,
                pl.matched_value,
                pl.evidence_scope,
                pl.selection_status,
                s.source_name,
                s.source_url AS provenance_source_url
            FROM product_labels pl
            JOIN labels l ON l.label_id = pl.label_id
            JOIN products p ON p.product_id = pl.product_id
            LEFT JOIN sources s ON s.source_id = l.source_id
            WHERE pl.product_id = ?
              AND p.eligibility_mode = 'NORMAL_CONSUMER'
              AND pl.consumer_eligible = 1
              AND pl.selection_status IN ('SELECTED_STORED', 'EARLIER_STORED')
              AND pl.applicability_class = 'EXACT_PRODUCT'
              AND pl.evidence_scope = 'PRODUCT'
              AND pl.ingredient_set_verified = 1
              AND pl.formulation_scope_verified = 1
              AND json_array_length(pl.conflicts_json) = 0
              AND l.date_status = 'VALID'
              AND l.version_number IS NOT NULL
              AND l.has_requested_safety_section = 1
              AND l.extraction_valid = 1
            ORDER BY
                COALESCE(l.effective_date, '') DESC,
                COALESCE(l.version_number, -1) DESC,
                l.label_id
            """,
            (product_id,),
        ).fetchall()

    def _label_coverage(self, con, product_id: str, labels) -> dict[str, Any]:
        coverage = self._coverage(con, product_id, "labels")
        count = len(labels)
        coverage["stored_record_count"] = count
        # Stored build counts include regulatory/withheld edges. Consumer counts
        # describe only admitted evidence; no evidence is not an observed zero.
        coverage["measured_count"] = count if count else None
        if not count:
            if coverage["state"] not in {"UNKNOWN", "UNAVAILABLE"}:
                coverage.update(
                    state="UNKNOWN",
                    reason_code="NO_CONSUMER_ELIGIBLE_STORED_LABEL",
                )
            coverage["empty_message"] = (
                "No consumer-eligible product-scoped label evidence is available "
                "in this preserved release. This does not establish the absence "
                "of warnings, contraindications, adverse reactions or interactions."
            )
        elif (
            coverage["state"] != "READY"
            or any(row["selection_status"] == "EARLIER_STORED" for row in labels)
        ):
            coverage.update(
                state="PARTIAL",
                reason_code="STORED_LABEL_TEXT_WITH_SCOPE_DATE_OR_SELECTION_LIMITATIONS",
            )
        coverage["limitations"] = [
            *coverage["limitations"],
            "Label counts describe only consumer-eligible records returned for "
            "this product, not complete labeling or absence of clinical risks.",
        ]
        return coverage

    def _labels(self, con, product_id: str) -> dict[str, Any]:
        records = []
        linked = self._consumer_labels(con, product_id)

        for label in linked:
            section_rows = con.execute(
                """
                SELECT
                    normalized_section,
                    source_field,
                    field_present,
                    full_text,
                    state,
                    reason_code
                FROM label_sections
                WHERE label_id = ?
                ORDER BY normalized_section, source_field
                """,
                (label["label_id"],),
            ).fetchall()

            sections = {
                row["normalized_section"]: {
                    "text": row["full_text"],
                    "field_present": bool(row["field_present"]),
                    "state": row["state"],
                    "reason_code": row["reason_code"],
                }
                for row in section_rows
            }

            records.append({
                "id": label["label_id"],
                "label_set_id": label["set_id"],
                "label_version": (
                    str(label["version_number"])
                    if label["version_number"] is not None
                    else None
                ),
                "effective_date": label["effective_date"],
                "applicability_class": label["applicability_class"],
                "match_method": label["match_method"],
                "matched_value": label["matched_value"],
                "evidence_scope": label["evidence_scope"],
                "selection_status": label["selection_status"],
                "boxed_warning": self._section_text(
                    sections, "boxed_warning"
                ),
                "warnings_and_precautions": self._section_text(
                    sections, "warnings_and_cautions"
                ),
                "warnings": self._section_text(
                    sections, "warnings"
                ),
                "contraindications": self._section_text(
                    sections, "contraindications"
                ),
                "adverse_reactions": self._section_text(
                    sections, "adverse_reactions"
                ),
                "drug_interactions": self._section_text(
                    sections, "drug_interactions"
                ),
                "section_states": sections,
                "source": label["source_name"] or "openfda_drug_label",
                "source_record_id": label["source_record_id"],
                "source_url": label["provenance_source_url"],
            })

        return {
            "records": records,
            # Compatibility key: these are the stored selections for every
            # independent set, including explicitly identified earlier evidence.
            "latest_records": records,
            "coverage": self._label_coverage(con, product_id, linked),
        }

    def _recalls(self, con, product_id: str) -> dict[str, Any]:
        records = []

        for row in con.execute(
            """
            SELECT
                r.*,
                pr.applicability_class,
                pr.match_method,
                pr.matched_value,
                pr.lot_scope,
                pr.lot_code_text,
                s.source_name,
                s.source_url AS provenance_source_url
            FROM product_recalls pr
            JOIN recalls r ON r.recall_id = pr.recall_id
            LEFT JOIN sources s ON s.source_id = r.source_id
            WHERE pr.product_id = ?
            ORDER BY
                COALESCE(r.recall_initiation_date, '') DESC,
                r.recall_id
            """,
            (product_id,),
        ):
            records.append({
                "id": row["recall_id"],
                "recall_number": row["recall_number"],
                "product_description": row["product_description"],
                "reason_for_recall": row["reason_for_recall"],
                "classification": row["classification"],
                "reported_status": row["source_reported_status"],
                "recalling_firm": row["recalling_firm"],
                "recall_initiation_date": row["recall_initiation_date"],
                "report_date": row["report_date"],
                "distribution_pattern": row["distribution_pattern"],
                "lot_information": row["lot_code_text"] or row["code_info"],
                "lot_scope": row["lot_scope"],
                "applicability_class": row["applicability_class"],
                "match_method": row["match_method"],
                "matched_value": row["matched_value"],
                "source": row["source_name"] or "openfda_drug_enforcement",
                "source_record_id": row["source_record_id"],
                "source_url": row["provenance_source_url"],
            })

        return {
            "records": records,
            "coverage": self._coverage(con, product_id, "recalls"),
        }

    def _adverse_events(self, con, product_id: str) -> dict[str, Any]:
        records = []

        ingredients = con.execute(
            """
            SELECT i.ingredient_id, i.canonical_name
            FROM product_ingredients pi
            JOIN ingredients i
              ON i.ingredient_id = pi.ingredient_id
            WHERE pi.product_id = ?
            ORDER BY i.canonical_name, i.ingredient_id
            """,
            (product_id,),
        ).fetchall()

        with_analytics = 0

        for ingredient in ingredients:
            ingredient_id = ingredient["ingredient_id"]

            summary = con.execute(
                """
                SELECT *
                FROM ae_summary
                WHERE ingredient_id = ?
                """,
                (ingredient_id,),
            ).fetchone()

            coverage = self._ingredient_coverage(
                con, ingredient_id, "ae_analytics"
            )

            if summary is None:
                records.append({
                    "ingredient_id": ingredient_id,
                    "ingredient_name": ingredient["canonical_name"],
                    "scope": "INGREDIENT",
                    "analytics": None,
                    "top_reported_reactions": [],
                    "monthly": [],
                    "coverage": coverage,
                })
                continue

            with_analytics += 1

            reactions = [
                {
                    "reaction": row["reaction"],
                    "co_report_activity": row["co_report_activity"],
                    "active_months": row["active_months"],
                    "rank": row["rank"],
                }
                for row in con.execute(
                    """
                    SELECT
                        reaction,
                        co_report_activity,
                        active_months,
                        rank
                    FROM ae_top_reactions
                    WHERE ingredient_id = ?
                    ORDER BY rank, reaction
                    """,
                    (ingredient_id,),
                )
            ]

            records.append({
                "ingredient_id": ingredient_id,
                "ingredient_name": ingredient["canonical_name"],
                "scope": "INGREDIENT",
                "analytics": {
                    "window_start": summary["window_start"],
                    "window_end": summary["window_end"],
                    "report_count": summary["report_count"],
                    "unique_case_count": summary["unique_case_count"],
                    "serious_report_count": summary["serious_report_count"],
                    "serious_known_report_count": (
                        summary["serious_known_report_count"]
                    ),
                    "death_report_count": summary["death_report_count"],
                    "hospitalization_report_count": (
                        summary["hospitalization_report_count"]
                    ),
                    "disability_report_count": (
                        summary["disability_report_count"]
                    ),
                    "life_threatening_report_count": (
                        summary["life_threatening_report_count"]
                    ),
                    "suspect_report_count": summary["suspect_report_count"],
                    "concomitant_report_count": (
                        summary["concomitant_report_count"]
                    ),
                    "interacting_report_count": (
                        summary["interacting_report_count"]
                    ),
                    "active_month_count": summary["active_month_count"],
                    "reaction_term_count": summary["reaction_term_count"],
                    "co_report_activity": summary["co_report_activity"],
                    "count_unit": summary["count_unit"],
                    "date_basis": summary["date_basis"],
                    "limitations": _json_list(summary["limitations_json"]),
                },
                "top_reported_reactions": reactions,
                "monthly": [dict(row) for row in con.execute(
                    "SELECT period, report_count, serious_report_count FROM ae_monthly "
                    "WHERE ingredient_id = ? ORDER BY period", (ingredient_id,)
                )],
                "coverage": coverage,
            })

        return {
            "records": records,
            "coverage": self._coverage(
                con, product_id, "ae_analytics"
            ),
            "summary": {
                "scope": "INGREDIENT_COMPONENTS_ONLY",
                "ingredient_count": len(ingredients),
                "ingredients_with_analytics": with_analytics,
                "ingredients_without_analytics": (
                    len(ingredients) - with_analytics
                ),
                "product_report_total": None,
                "limitation": (
                    "Dav AI does not sum ingredient FAERS counts into a "
                    "product-level adverse-event total. These are descriptive "
                    "ingredient-level co-reporting associations, not incidence "
                    "or causality."
                ),
            },
        }

    def _communications(self, con, product_id: str) -> dict[str, Any]:
        records = []

        for row in con.execute(
            """
            SELECT
                i.ingredient_id,
                i.canonical_name,
                dc.applicability_class,
                dc.scope_qualifiers,
                dc.configured_name,
                sc.*
            FROM product_ingredients pi
            JOIN ingredients i
              ON i.ingredient_id = pi.ingredient_id
            JOIN drug_communications dc
              ON dc.ingredient_id = pi.ingredient_id
            JOIN safety_communications sc
              ON sc.communication_id = dc.communication_id
            WHERE pi.product_id = ?
            ORDER BY
                COALESCE(sc.published_date, '') DESC,
                sc.communication_id,
                i.ingredient_id
            """,
            (product_id,),
        ):
            records.append({
                "id": row["communication_id"],
                "ingredient_id": row["ingredient_id"],
                "ingredient_name": row["canonical_name"],
                "title": row["title"],
                "body_text": row["body_text"],
                "published_date": row["published_date"],
                "communication_type": row["communication_type"],
                "applicability_class": row["applicability_class"],
                "scope_qualifiers": row["scope_qualifiers"],
                "source": "fda_drug_safety_communications",
                "source_record_id": row["source_record_id"],
                "source_url": row["source_url"],
            })

        ingredient_ids = [
            row["ingredient_id"]
            for row in con.execute(
                """
                SELECT ingredient_id
                FROM product_ingredients
                WHERE product_id = ?
                ORDER BY ingredient_id
                """,
                (product_id,),
            )
        ]

        ingredient_coverage = [
            self._ingredient_coverage(
                con, ingredient_id, "safety_communications"
            )
            for ingredient_id in ingredient_ids
        ]

        return {
            "records": records,
            "coverage": {
                "state": (
                    "PARTIAL"
                    if records
                    else "UNKNOWN"
                ),
                "reason_code": (
                    "CURATED_COMMUNICATION_LINK_AVAILABLE"
                    if records
                    else "NO_VERIFIED_COMMUNICATION_LINK"
                ),
                "scope": "CURATED_PARTIAL; INGREDIENT_CONTEXT_ONLY",
                "stored_record_count": len(records),
                "bounded": True,
                "truncated": False,
                "empty_message": (
                    "No verified safety communication is linked in this "
                    "release. Communication coverage is curated and not "
                    "comprehensive."
                ),
                "limitations": self._merge_limitations(
                    ingredient_coverage
                ),
                "ingredients": ingredient_coverage,
            },
        }

    def _coverage(
        self,
        con,
        product_id: str,
        domain: str,
    ) -> dict[str, Any]:
        row = con.execute(
            """
            SELECT *
            FROM coverage
            WHERE entity_type = 'PRODUCT'
              AND entity_id = ?
              AND domain = ?
            ORDER BY window_key
            LIMIT 1
            """,
            (product_id, domain),
        ).fetchone()

        if row is None:
            return {
                "state": "UNKNOWN",
                "reason_code": "NO_RELEASE_COVERAGE_ROW",
                "scope": "UNKNOWN",
                "stored_record_count": 0,
                "bounded": True,
                "truncated": False,
                "empty_message": (
                    "Coverage information is unavailable for this release."
                ),
                "limitations": [],
            }

        limitations = _json_list(row["limitations_json"])

        empty_message = limitations[-1] if limitations else (
            "No verified linked record is stored in this release."
        )

        return {
            "state": row["state"],
            "reason_code": row["reason_code"],
            "scope": row["scope"],
            "as_of_date": row["as_of_date"],
            "source_date": row["source_date"],
            "measured_count": row["measured_count"],
            "unresolved_count": row["unresolved_count"],
            "stored_record_count": row["measured_count"] or 0,
            "bounded": True,
            "truncated": False,
            "empty_message": empty_message,
            "limitations": limitations,
        }

    def _ingredient_coverage(
        self,
        con,
        ingredient_id: str,
        domain: str,
    ) -> dict[str, Any]:
        row = con.execute(
            """
            SELECT *
            FROM coverage
            WHERE entity_type = 'INGREDIENT'
              AND entity_id = ?
              AND domain = ?
            ORDER BY window_key
            LIMIT 1
            """,
            (ingredient_id, domain),
        ).fetchone()

        if row is None:
            return {
                "ingredient_id": ingredient_id,
                "state": "UNKNOWN",
                "reason_code": "NO_RELEASE_COVERAGE_ROW",
                "scope": "UNKNOWN",
                "measured_count": None,
                "limitations": [],
            }

        return {
            "ingredient_id": ingredient_id,
            "state": row["state"],
            "reason_code": row["reason_code"],
            "scope": row["scope"],
            "as_of_date": row["as_of_date"],
            "source_date": row["source_date"],
            "measured_count": row["measured_count"],
            "unresolved_count": row["unresolved_count"],
            "limitations": _json_list(row["limitations_json"]),
        }

    @staticmethod
    def _section_text(
        sections: dict[str, dict[str, Any]],
        name: str,
    ) -> str | None:
        section = sections.get(name)
        if not section:
            return None
        if section["state"] != "READY":
            return None
        return section["text"]

    @staticmethod
    def _merge_limitations(
        coverage_rows: list[dict[str, Any]],
    ) -> list[str]:
        merged = []
        for coverage in coverage_rows:
            for item in coverage.get("limitations", []):
                if item not in merged:
                    merged.append(item)
        return merged

    def _project_product(self, con, row) -> dict[str, Any]:
        product_id = row["product_id"]

        ingredient_rows = con.execute(
            """
            SELECT i.ingredient_id, i.canonical_name
            FROM product_ingredients pi
            JOIN ingredients i ON i.ingredient_id = pi.ingredient_id
            WHERE pi.product_id = ?
            ORDER BY i.canonical_name, i.ingredient_id
            """,
            (product_id,),
        ).fetchall()

        identifier_rows = con.execute(
            """
            SELECT
                identifier_type,
                value,
                rxcui_concept_type,
                is_unique_product,
                has_conflict
            FROM product_identifiers
            WHERE product_id = ?
            ORDER BY identifier_type, value
            """,
            (product_id,),
        ).fetchall()

        product_ndcs = [
            r["value"]
            for r in identifier_rows
            if r["identifier_type"] == "PRODUCT_NDC"
        ]

        package_ndcs = [
            r["value"]
            for r in identifier_rows
            if r["identifier_type"] == "PACKAGE_NDC"
        ]

        rxcuis = [
            {
                "value": r["value"],
                "concept_type": r["rxcui_concept_type"],
                "is_unique_product": bool(r["is_unique_product"]),
                "has_conflict": bool(r["has_conflict"]),
            }
            for r in identifier_rows
            if r["identifier_type"] == "RXCUI"
        ]

        raw_active = _json_list(row["active_ingredients_json"])
        strengths = [
            item.get("strength")
            for item in raw_active
            if isinstance(item, dict) and item.get("strength")
        ]

        return {
            "id": product_id,
            "product_id": product_id,
            "generic_name": row["generic_name"],
            "brand_names": [row["brand_name"]] if row["brand_name"] else [],
            "active_ingredients": [
                ingredient["canonical_name"] for ingredient in ingredient_rows
            ],
            "ingredient_ids": [
                ingredient["ingredient_id"] for ingredient in ingredient_rows
            ],
            "strength": "; ".join(strengths) if strengths else None,
            "dosage_form": row["dosage_form"],
            "routes": _json_list(row["routes_json"]),
            "manufacturers": [row["labeler_name"]] if row["labeler_name"] else [],
            "product_ndcs": product_ndcs,
            "package_ndcs": package_ndcs,
            "rxcui": rxcuis[0]["value"] if len(rxcuis) == 1 else None,
            "rxcuis": rxcuis,
            "is_combination": bool(row["is_combination"]),
            "identity_partial": bool(row["identity_partial"]),
            "formulation_id": row["formulation_id"],
            "application_number": row["application_number"],
            "product_type": row["product_type"],
            "marketing_category": row["marketing_category"],
            "consumer_classification": row["consumer_classification"],
            "provenance": {
                "source": "openfda_ndc_directory",
                "source_id": row["source_id"],
                "source_record_id": row["source_record_id"],
                "source_url": row["source_url"],
                "observed_at": row["observed_at"],
            },
        }

    @staticmethod
    def _escape_like(value: str) -> str:
        return (
            value.replace("\\", "\\\\")
            .replace("%", "\\%")
            .replace("_", "\\_")
        )
