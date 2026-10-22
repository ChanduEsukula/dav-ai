"""The 19 contract-v1 tables. Phase 1 only creates them in memory.

STRICT/ANY identity columns deliberately prevent SQLite TEXT affinity from
silently converting numeric identifiers to strings. JSON preserves source values
and explicitly permitted arrays, not product membership or evidence relations.
"""
import sqlite3

from . import SCHEMA_VERSION

TABLES = (
    "ingredients", "products", "formulations", "product_ingredients",
    "product_identifiers", "search_names", "labels", "label_sections",
    "product_labels", "recalls", "product_recalls", "ae_summary", "ae_monthly",
    "ae_top_reactions", "safety_communications", "drug_communications", "sources",
    "coverage", "release_manifest",
)
COVERAGE_STATES = ("READY", "PARTIAL", "UNKNOWN", "UNAVAILABLE")
LABEL_CLASSES = ("EXACT_PRODUCT", "EXACT_FORMULATION", "INGREDIENT_CONTEXT_ONLY",
                 "AMBIGUOUS", "UNRESOLVED", "NOT_APPLICABLE")
RECALL_CLASSES = ("AFFECTED_PACKAGE", "AFFECTED_PRODUCT", "AFFECTED_FORMULATION_CONTEXT",
                  "METADATA_CANDIDATE_ONLY", "INGREDIENT_CONTEXT_ONLY", "AMBIGUOUS",
                  "UNRESOLVED", "NOT_APPLICABLE")
MATCH_METHODS = ("EXACT_SOURCE_PRODUCT", "EXACT_PACKAGE_NDC", "EXACT_NDC",
                 "EXACT_RXCUI", "EXACT_NORMALIZED_NAME")
SECTION_FIELDS = ("boxed_warning", "warnings_and_cautions", "warnings",
                  "contraindications", "adverse_reactions", "drug_interactions",
                  "warnings_and_precautions")


def choices(values):
    return "(" + ",".join("'" + v + "'" for v in values) + ")"


def identity(name, reference=None, nullable=False):
    column = name + " ANY" + ("" if nullable else " NOT NULL")
    if reference:
        column += " REFERENCES " + reference + " ON UPDATE RESTRICT ON DELETE RESTRICT"
    column += f" CHECK ({name} IS NULL OR (typeof({name})='text' AND length(trim({name}))>0))"
    return column


def json_column(name, shape=None, nullable=False):
    column = name + " TEXT" + ("" if nullable else " NOT NULL")
    predicate = f"json_valid({name})"
    if shape:
        predicate += f" AND json_type({name})='{shape}'"
    return column + f" CHECK ({name} IS NULL OR ({predicate}))"


def table(name, fields):
    return f"CREATE TABLE {name} (\n  " + ",\n  ".join(fields) + "\n) STRICT, WITHOUT ROWID;"


def schema_sql():
    src = lambda: identity("source_id", "sources(source_id)")
    ingredient = lambda: identity("ingredient_id", "ingredients(ingredient_id)")
    product = lambda: identity("product_id", "products(product_id)")
    state = lambda name: f"{name} TEXT NOT NULL CHECK ({name} IN {choices(COVERAGE_STATES)})"
    sql = ["-- " + SCHEMA_VERSION, "PRAGMA foreign_keys=ON;", "PRAGMA user_version=1;"]
    sql.append(table("sources", [identity("source_id"), "source_name TEXT NOT NULL",
        "capture_id TEXT NOT NULL", "source_kind TEXT NOT NULL CHECK (source_kind IN ('RAW_SNAPSHOT','DERIVED','CAPTURE'))",
        identity("parent_source_id", "sources(source_id)", True), "source_url TEXT",
        "export_date TEXT", "observed_at TEXT", "captured_at TEXT", "ingested_at TEXT",
        "transform_version TEXT", "verification_basis TEXT NOT NULL",
        json_column("inputs_json", "array"), "PRIMARY KEY(source_id)", "UNIQUE(source_name,capture_id)"]))
    sql.append(table("ingredients", [identity("ingredient_id"), "canonical_name TEXT NOT NULL CHECK(length(trim(canonical_name))>0)",
        "identity_rule TEXT NOT NULL", "observed_at TEXT NOT NULL", src(), "PRIMARY KEY(ingredient_id)"]))
    sql.append(table("formulations", [identity("formulation_id"), json_column("ingredient_ids_json", "array"),
        json_column("strengths_json", "array"), "dosage_form TEXT NOT NULL CHECK(length(trim(dosage_form))>0)",
        json_column("routes_json", "array"), src(), "PRIMARY KEY(formulation_id)",
        "CHECK(json_array_length(ingredient_ids_json)>0 AND json_array_length(routes_json)>0)"]))
    sql.append(table("products", [identity("product_id"), src(), identity("source_record_id"),
        "source_url TEXT", "observed_at TEXT NOT NULL", "generic_name TEXT", "brand_name TEXT", "brand_name_base TEXT", "labeler_name TEXT",
        identity("formulation_id", "formulations(formulation_id)", True), "product_type TEXT", "marketing_category TEXT",
        "marketing_start_date_raw TEXT", "marketing_end_date_raw TEXT", "listing_expiration_date_raw TEXT",
        json_column("active_ingredients_json", "array", True),
        "ingredient_set_complete INTEGER NOT NULL CHECK(ingredient_set_complete IN (0,1))",
        "is_combination INTEGER NOT NULL CHECK(is_combination IN (0,1))",
        "eligibility_mode TEXT NOT NULL CHECK(eligibility_mode IN ('NORMAL_CONSUMER','REGULATORY_ONLY','EXCLUDED_V1'))",
        "eligibility_reason TEXT NOT NULL", json_column("additional_deficiencies_json", "array"),
        "identity_partial INTEGER NOT NULL CHECK(identity_partial IN (0,1))",
        "policy_version TEXT NOT NULL", "PRIMARY KEY(product_id)", "UNIQUE(source_id,source_record_id)"]))
    sql.append(table("product_ingredients", [product(), ingredient(), "PRIMARY KEY(product_id,ingredient_id)"]))
    sql.append(table("product_identifiers", [product(), "identifier_type TEXT NOT NULL CHECK(identifier_type IN ('PRODUCT_NDC','PACKAGE_NDC','RXCUI'))",
        identity("value"), src(), "rxcui_concept_type TEXT",
        "is_unique_product INTEGER NOT NULL CHECK(is_unique_product IN (0,1))",
        "has_conflict INTEGER NOT NULL CHECK(has_conflict IN (0,1))",
        "PRIMARY KEY(product_id,identifier_type,value)", "CHECK(identifier_type='RXCUI' OR rxcui_concept_type IS NULL)"]))
    # Polymorphic IDs still have real, typed foreign keys, with a CHECK linking
    # the public entity_id to exactly one typed target. No additional logical table.
    sql.append(table("search_names", ["entity_type TEXT NOT NULL CHECK(entity_type IN ('INGREDIENT','PRODUCT'))",
        identity("entity_id"), identity("ingredient_id", "ingredients(ingredient_id)", True), identity("product_id", "products(product_id)", True),
        "name_role TEXT NOT NULL CHECK(name_role IN ('INGREDIENT','GENERIC','BRAND','BRAND_BASE'))",
        "normalized_name TEXT NOT NULL CHECK(length(trim(normalized_name))>0)",
        json_column("original_names_json", "array"), src(),
        "PRIMARY KEY(entity_type,entity_id,name_role,normalized_name)",
        "CHECK((entity_type='INGREDIENT' AND ingredient_id IS NOT NULL AND entity_id=ingredient_id AND product_id IS NULL AND name_role='INGREDIENT') OR (entity_type='PRODUCT' AND product_id IS NOT NULL AND entity_id=product_id AND ingredient_id IS NULL AND name_role!='INGREDIENT'))"]))
    sql.append(table("labels", [identity("label_id"), src(), identity("source_record_id"), identity("set_id"),
        json_column("version_raw_json"), "version_number INTEGER CHECK(version_number>=0)",
        "effective_time_raw TEXT", "effective_date TEXT",
        "date_status TEXT NOT NULL CHECK(date_status IN ('VALID','INVALID','FUTURE_AT_SOURCE_EXPORT'))",
        json_column("source_identity_json", "object"), "has_requested_safety_section INTEGER NOT NULL CHECK(has_requested_safety_section IN (0,1))",
        "extraction_valid INTEGER NOT NULL CHECK(extraction_valid IN (0,1))", "source_content_sha256 TEXT NOT NULL",
        "PRIMARY KEY(label_id)", "UNIQUE(source_id,source_record_id)",
        "CHECK(effective_date IS NULL OR (length(effective_date)=10 AND strftime('%Y-%m-%d',effective_date) IS NOT NULL AND strftime('%Y-%m-%d',effective_date)=effective_date))",
        "CHECK(date_status!='VALID' OR effective_date<='2026-09-25')",
        "CHECK(date_status!='FUTURE_AT_SOURCE_EXPORT' OR effective_date>'2026-09-25')",
        "CHECK((date_status='INVALID' AND effective_date IS NULL) OR (date_status!='INVALID' AND effective_date IS NOT NULL))"]))
    sql.append(table("label_sections", [identity("label_id", "labels(label_id)"),
        f"source_field TEXT NOT NULL CHECK(source_field IN {choices(SECTION_FIELDS)})",
        "normalized_section TEXT NOT NULL", "field_present INTEGER NOT NULL CHECK(field_present IN (0,1))",
        json_column("original_value_json", nullable=True), "full_text TEXT", "source_shape TEXT NOT NULL",
        state("state"), "reason_code TEXT NOT NULL", "source_value_sha256 TEXT", "rendering_sha256 TEXT",
        "PRIMARY KEY(label_id,source_field)", "CHECK(normalized_section=source_field)",
        "CHECK(state!='READY' OR (field_present=1 AND full_text IS NOT NULL AND source_value_sha256 IS NOT NULL AND rendering_sha256 IS NOT NULL))"]))
    sql.append(table("product_labels", [product(), identity("label_id", "labels(label_id)"),
        f"applicability_class TEXT NOT NULL CHECK(applicability_class IN {choices(LABEL_CLASSES)})",
        f"match_method TEXT CHECK(match_method IN {choices(MATCH_METHODS)})", "matched_value TEXT",
        "is_combination INTEGER NOT NULL CHECK(is_combination IN (0,1))",
        "ingredient_set_verified INTEGER NOT NULL CHECK(ingredient_set_verified IN (0,1))",
        "formulation_scope_verified INTEGER NOT NULL CHECK(formulation_scope_verified IN (0,1))",
        "evidence_scope TEXT NOT NULL CHECK(evidence_scope IN ('PRODUCT','FORMULATION','INGREDIENT_CONTEXT','UNKNOWN'))",
        json_column("verification_basis_json", "object"), json_column("conflicts_json", "array"), json_column("unresolved_identifiers_json", "array"),
        "selection_status TEXT NOT NULL CHECK(selection_status IN ('NOT_SELECTED','SELECTED_STORED','EARLIER_STORED','AMBIGUOUS'))",
        "consumer_eligible INTEGER NOT NULL CHECK(consumer_eligible IN (0,1))", "policy_version TEXT NOT NULL",
        "PRIMARY KEY(product_id,label_id)", "CHECK((match_method IS NULL)=(matched_value IS NULL))",
        "CHECK(consumer_eligible=0 OR (applicability_class='EXACT_PRODUCT' AND ingredient_set_verified=1 AND formulation_scope_verified=1 AND evidence_scope='PRODUCT' AND selection_status IN ('SELECTED_STORED','EARLIER_STORED') AND match_method IS NOT NULL AND json_array_length(conflicts_json)=0))"]))
    sql.append(table("recalls", [identity("recall_id"), src(), identity("source_record_id"), identity("recall_number"),
        "event_id TEXT", "product_description TEXT NOT NULL", "reason_for_recall TEXT NOT NULL", "classification TEXT",
        "source_reported_status TEXT", "recalling_firm TEXT", "recall_initiation_date_raw TEXT", "report_date_raw TEXT",
        "recall_initiation_date TEXT", "report_date TEXT", "distribution_pattern TEXT", "code_info TEXT",
        json_column("source_identity_json", "object"), "source_content_sha256 TEXT NOT NULL",
        "PRIMARY KEY(recall_id)", "UNIQUE(source_id,source_record_id)"]))
    sql.append(table("product_recalls", [product(), identity("recall_id", "recalls(recall_id)"),
        f"applicability_class TEXT NOT NULL CHECK(applicability_class IN {choices(RECALL_CLASSES)})",
        f"match_method TEXT CHECK(match_method IN {choices(MATCH_METHODS)})", "matched_value TEXT",
        "explicit_scope_verified INTEGER NOT NULL CHECK(explicit_scope_verified IN (0,1))",
        "ingredient_set_verified INTEGER NOT NULL CHECK(ingredient_set_verified IN (0,1))",
        "formulation_scope_verified INTEGER NOT NULL CHECK(formulation_scope_verified IN (0,1))",
        "lot_scope TEXT NOT NULL CHECK(lot_scope IN ('EXPLICIT_RESTRICTION','EXPLICIT_ALL_LOTS','UNKNOWN'))",
        "lot_code_text TEXT", json_column("verification_basis_json", "object"), json_column("conflicts_json", "array"),
        "consumer_eligible INTEGER NOT NULL CHECK(consumer_eligible IN (0,1))", "policy_version TEXT NOT NULL",
        "PRIMARY KEY(product_id,recall_id)", "CHECK((match_method IS NULL)=(matched_value IS NULL))",
        "CHECK(lot_scope='UNKNOWN' OR (lot_code_text IS NOT NULL AND length(trim(lot_code_text))>0))",
        "CHECK(consumer_eligible=0 OR (applicability_class IN ('AFFECTED_PACKAGE','AFFECTED_PRODUCT') AND explicit_scope_verified=1 AND ingredient_set_verified=1 AND formulation_scope_verified=1 AND match_method IS NOT NULL AND json_array_length(conflicts_json)=0))"]))
    window = ["window_start TEXT NOT NULL CHECK(window_start='2020-01-01')", "window_end TEXT NOT NULL CHECK(window_end='2026-06-30')"]
    sql.append(table("ae_summary", [ingredient(), *window, "pair_activity INTEGER NOT NULL CHECK(pair_activity>0)",
        "reaction_term_count INTEGER NOT NULL CHECK(reaction_term_count>0)", "observed_month_count INTEGER NOT NULL CHECK(observed_month_count BETWEEN 1 AND 78)",
        "count_unit TEXT NOT NULL CHECK(count_unit='ingredient-reaction pair activity')",
        "date_basis TEXT NOT NULL CHECK(date_basis='parsed latest-receipt month')", json_column("limitations_json", "array"), src(),
        "PRIMARY KEY(ingredient_id,window_start,window_end)"]))
    sql.append(table("ae_monthly", [ingredient(),
        "period TEXT NOT NULL CHECK(period BETWEEN '2020-01-01' AND '2026-06-01' AND strftime('%Y-%m-%d',period) IS NOT NULL AND strftime('%Y-%m-%d',period)=period AND substr(period,9,2)='01')",
        "pair_activity INTEGER NOT NULL CHECK(pair_activity>0)", "active_reaction_terms INTEGER NOT NULL CHECK(active_reaction_terms>0)", src(),
        "PRIMARY KEY(ingredient_id,period)"]))
    sql.append(table("ae_top_reactions", [ingredient(), *window, "reaction TEXT NOT NULL CHECK(length(trim(reaction))>0)",
        "pair_activity INTEGER NOT NULL CHECK(pair_activity>0)", "active_months INTEGER NOT NULL CHECK(active_months BETWEEN 1 AND 78)",
        "rank INTEGER NOT NULL CHECK(rank BETWEEN 1 AND 20)", src(),
        "PRIMARY KEY(ingredient_id,window_start,window_end,reaction)", "UNIQUE(ingredient_id,window_start,window_end,rank)"]))
    sql.append(table("safety_communications", [identity("communication_id"), src(), identity("source_record_id"),
        "title TEXT NOT NULL", "communication_type TEXT NOT NULL", "published_date TEXT", "body_text TEXT NOT NULL",
        "source_url TEXT NOT NULL", "source_updated_at TEXT", "ingested_at TEXT", json_column("configured_names_json", "array"),
        "editorial_scope TEXT NOT NULL", "PRIMARY KEY(communication_id)", "UNIQUE(source_id,source_record_id)"]))
    sql.append(table("drug_communications", [ingredient(), identity("communication_id", "safety_communications(communication_id)"),
        "applicability_class TEXT NOT NULL CHECK(applicability_class='INGREDIENT_CONTEXT_ONLY')", "configured_name TEXT NOT NULL",
        "source_text_evidence TEXT NOT NULL", "scope_qualifiers TEXT NOT NULL", json_column("review_basis_json", "object"),
        "policy_version TEXT NOT NULL", "PRIMARY KEY(ingredient_id,communication_id)"]))
    target_types = {"INGREDIENT": ("ingredient_id", "ingredients"), "PRODUCT": ("product_id", "products"),
        "FORMULATION": ("formulation_id", "formulations"), "LABEL": ("label_id", "labels"),
        "RECALL": ("recall_id", "recalls"), "COMMUNICATION": ("communication_id", "safety_communications")}
    alternatives = []
    for kind, (column, _) in target_types.items():
        conditions = [f"entity_type='{kind}'", f"{column} IS NOT NULL", f"entity_id={column}"]
        conditions += [f"{other} IS NULL" for other, _ in target_types.values() if other != column]
        alternatives.append("(" + " AND ".join(conditions) + ")")
    sql.append(table("coverage", [f"entity_type TEXT NOT NULL CHECK(entity_type IN {choices(target_types)})", identity("entity_id"),
        *[identity(col, f"{target}({col})", True) for col, target in target_types.values()],
        "domain TEXT NOT NULL CHECK(domain IN ('identity','labels','recalls','ae_analytics','safety_communications'))",
        "window_key TEXT NOT NULL DEFAULT ''", state("state"), "reason_code TEXT NOT NULL", "scope TEXT NOT NULL",
        "as_of_date TEXT", "source_date TEXT", "measured_count INTEGER CHECK(measured_count>=0)", "unresolved_count INTEGER CHECK(unresolved_count>=0)",
        "rule_version TEXT NOT NULL", json_column("limitations_json", "array"),
        "PRIMARY KEY(entity_type,entity_id,domain,window_key)", "CHECK(" + " OR ".join(alternatives) + ")",
        "CHECK(state NOT IN ('UNKNOWN','UNAVAILABLE') OR measured_count IS NULL)"]))
    sql.append(table("release_manifest", [identity("release_id"), "contract_id TEXT NOT NULL", "policy_version TEXT NOT NULL", "schema_version TEXT NOT NULL",
        "build_version TEXT NOT NULL", "build_time_utc TEXT NOT NULL", "ndc_observation_date TEXT NOT NULL CHECK(ndc_observation_date='2026-09-26')",
        "label_export_date TEXT NOT NULL CHECK(label_export_date='2026-09-25')", "label_capture_date TEXT NOT NULL CHECK(label_capture_date='2026-09-26')",
        *window, json_column("source_vintages_json", "array"), json_column("table_counts_json", "object"),
        json_column("eligibility_counts_json", "object"), json_column("unresolved_counts_json", "object"), json_column("validation_results_json", "object"),
        "digest_strategy TEXT NOT NULL CHECK(digest_strategy IN ('CANONICAL_PAYLOAD_EXCLUDING_DIGEST','EXTERNAL_FINAL_FILE_SHA256'))",
        "content_digest TEXT", "PRIMARY KEY(release_id)",
        "CHECK(digest_strategy!='EXTERNAL_FINAL_FILE_SHA256' OR content_digest IS NULL)"]))
    indexes = {
        "products_eligibility": "products(eligibility_mode,product_id)",
        "products_formulation": "products(formulation_id)",
        "products_source": "products(source_id,source_record_id)",
        "product_ingredients_reverse": "product_ingredients(ingredient_id,product_id)",
        "identifiers_lookup": "product_identifiers(identifier_type,value,product_id)",
        "names_lookup": "search_names(normalized_name,entity_type,entity_id)",
        "labels_version": "labels(source_id,set_id,version_number DESC,effective_date DESC)",
        "product_labels_reverse": "product_labels(label_id,product_id)",
        "product_labels_consumer": "product_labels(product_id,consumer_eligible,selection_status)",
        "product_recalls_reverse": "product_recalls(recall_id,product_id)",
        "product_recalls_consumer": "product_recalls(product_id,consumer_eligible)",
        "recalls_dates": "recalls(report_date,recall_id)",
        "communications_reverse": "drug_communications(communication_id,ingredient_id)",
        "coverage_domain": "coverage(domain,state,entity_type,entity_id)",
    }
    sql += [f"CREATE INDEX {name} ON {target};" for name, target in indexes.items()]
    # JSON is expressly allowed for formulation source arrays. These triggers
    # enforce ingredient references and set uniqueness without a twentieth table.
    for event in ("INSERT", "UPDATE"):
        sql.append(f"""CREATE TRIGGER formulation_ingredients_{event.lower()} BEFORE {event} ON formulations BEGIN
          SELECT CASE WHEN EXISTS(SELECT 1 FROM json_each(NEW.ingredient_ids_json) j
            WHERE j.type!='text' OR NOT EXISTS(SELECT 1 FROM ingredients i WHERE i.ingredient_id=j.value))
            OR (SELECT count(*) FROM json_each(NEW.ingredient_ids_json)) !=
               (SELECT count(DISTINCT value) FROM json_each(NEW.ingredient_ids_json))
            THEN RAISE(ABORT,'Invalid formulation ingredient set') END;
        END;""")
    for event in ("DELETE", "UPDATE OF ingredient_id"):
        name = "delete" if event == "DELETE" else "update"
        sql.append(f"""CREATE TRIGGER ingredient_formulation_{name} BEFORE {event} ON ingredients
          WHEN EXISTS(SELECT 1 FROM formulations f,json_each(f.ingredient_ids_json) j WHERE j.value=OLD.ingredient_id)
          BEGIN SELECT RAISE(ABORT,'Ingredient referenced by formulation'); END;""")
    sql.append("""CREATE TRIGGER consumer_label_gate_insert BEFORE INSERT ON product_labels WHEN NEW.consumer_eligible=1 BEGIN
      SELECT CASE WHEN NOT EXISTS(SELECT 1 FROM labels l WHERE l.label_id=NEW.label_id
        AND l.date_status='VALID' AND l.effective_date<='2026-09-25' AND l.version_number IS NOT NULL
        AND l.has_requested_safety_section=1 AND l.extraction_valid=1)
        THEN RAISE(ABORT,'Consumer label document gates failed') END;
    END;""")
    sql.append("""CREATE TRIGGER consumer_label_gate_update BEFORE UPDATE ON product_labels WHEN NEW.consumer_eligible=1 BEGIN
      SELECT CASE WHEN NOT EXISTS(SELECT 1 FROM labels l WHERE l.label_id=NEW.label_id
        AND l.date_status='VALID' AND l.effective_date<='2026-09-25' AND l.version_number IS NOT NULL
        AND l.has_requested_safety_section=1 AND l.extraction_valid=1)
        THEN RAISE(ABORT,'Consumer label document gates failed') END;
    END;""")
    sql.append("""CREATE TRIGGER consumer_label_document_update BEFORE UPDATE ON labels
      WHEN EXISTS(SELECT 1 FROM product_labels pl WHERE pl.label_id=OLD.label_id AND pl.consumer_eligible=1) BEGIN
      SELECT CASE WHEN NEW.date_status!='VALID' OR NEW.version_number IS NULL
        OR NEW.has_requested_safety_section!=1 OR NEW.extraction_valid!=1
        THEN RAISE(ABORT,'Cannot invalidate selected consumer label document') END;
    END;""")
    return "\n\n".join(sql) + "\n"


def create_schema(connection):
    """Explicit schema initialization, refusing any already-populated DB schema."""
    if connection.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchone():
        raise ValueError("Refusing to alter an existing database")
    if connection.in_transaction:
        raise ValueError("Schema initialization requires no active transaction")
    if sqlite3.sqlite_version_info < (3, 37):
        raise RuntimeError("SQLite 3.37+ required for STRICT identity preservation")
    connection.execute("PRAGMA foreign_keys=ON")
    if connection.execute("PRAGMA foreign_keys").fetchone()[0] != 1:
        raise RuntimeError("Foreign keys could not be enabled")
    connection.execute("SELECT json_valid('[]')")  # Fail early if JSON support absent.
    connection.executescript("BEGIN;\n" + schema_sql() + "\nCOMMIT;")
