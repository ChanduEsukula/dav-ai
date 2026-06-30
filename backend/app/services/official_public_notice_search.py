from __future__ import annotations

from dataclasses import replace
from typing import Literal

from app.services.safety_source_adapters.base import (
    NormalizedSafetyRecord,
    SourceAdapterResult,
    compact_text,
)
from app.services.safety_source_adapters.fda_public import FDAPublicRecallsAdapter


NoticeDomain = Literal["food", "pharmacy", "cosmetic"]

_DOMAIN_TERMS: dict[NoticeDomain, tuple[str, ...]] = {
    "food": (
        "food",
        "beverage",
        "supplement",
        "grocery",
        "allergen",
        "meat",
        "poultry",
        "egg",
    ),
    "pharmacy": (
        "drug",
        "medicine",
        "medication",
        "pharmaceutical",
        "otc",
        "tablet",
        "capsule",
    ),
    "cosmetic": (
        "cosmetic",
        "skin care",
        "personal care",
        "makeup",
        "sunscreen",
        "hair",
    ),
}

fda_public_adapter = FDAPublicRecallsAdapter()


def _notice_domain_text(record: NormalizedSafetyRecord) -> str:
    return compact_text(
        " ".join(
            value
            for value in (
                record.category,
                record.product_name,
                record.brand_name,
                record.title,
                record.reason,
                record.hazard_type,
            )
            if value
        )
    ).lower()


def notice_matches_domain(
    record: NormalizedSafetyRecord,
    domain: NoticeDomain | None,
) -> bool:
    if domain is None:
        return True

    category = compact_text(record.category).lower()
    searchable = _notice_domain_text(record)
    terms = _DOMAIN_TERMS[domain]

    if any(term in category for term in terms):
        return True

    # FDA rows occasionally omit or generalize product type. Preserve a
    # matching official notice when its normalized content is clearly in scope.
    if not category:
        return any(term in searchable for term in terms)

    return False


async def search_official_public_notices(
    *,
    query: str,
    limit: int,
    request_id: str | None = None,
    domain: NoticeDomain | None = None,
) -> SourceAdapterResult:
    result = await fda_public_adapter.search(
        query=query,
        limit=max(limit, 25),
        request_id=request_id,
    )
    records = [
        record
        for record in result.records
        if notice_matches_domain(record, domain)
    ][:limit]

    return replace(
        result,
        records=records,
        upstream_status="success" if records else "empty",
        context={
            **result.context,
            "notice_domain": domain,
            "normalized_notice_count": sum(
                record.source_kind == "normalized_public_notice"
                for record in records
            ),
        },
    )


def official_notice_source_metadata(result: SourceAdapterResult) -> dict[str, object]:
    has_normalized_records = any(
        record.source_kind == "normalized_public_notice"
        for record in result.records
    )
    return {
        "source_id": result.source_id,
        "source_name": result.source_name,
        "source_type": (
            "FDA_NORMALIZED_PUBLIC_NOTICE"
            if has_normalized_records
            else "FDA_PUBLIC_NOTICE"
        ),
        "endpoint": result.source_url,
        "source_kind": (
            "normalized_public_notice"
            if has_normalized_records
            else result.source_kind
        ),
        "record_type": (
            "normalized official public notice"
            if has_normalized_records
            else result.source_type
        ),
        "upstream_status": result.upstream_status,
        "record_count": len(result.records),
    }
