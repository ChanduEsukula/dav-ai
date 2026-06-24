from __future__ import annotations

from dataclasses import dataclass, asdict
from typing import Any

from app.services.safety_source_adapters.base import NormalizedSafetyRecord


@dataclass(frozen=True)
class IdentifierCheckItem:
    type: str
    label: str
    value: str | None
    source: str
    reason: str

    def as_response_dict(self) -> dict[str, str | None]:
        return asdict(self)


def _append_unique_item(
    items: list[IdentifierCheckItem],
    *,
    type: str,
    label: str,
    value: str | None,
    source: str,
    reason: str,
) -> None:
    key = (type, value, source, reason)
    existing = {(item.type, item.value, item.source, item.reason) for item in items}
    if key not in existing:
        items.append(
            IdentifierCheckItem(
                type=type,
                label=label,
                value=value,
                source=source,
                reason=reason,
            )
        )


def _query_identifier_label(identifier_type: str) -> str:
    return {
        "vin": "VIN",
        "ndc": "NDC",
        "upc": "UPC",
        "udi": "UDI",
    }.get(identifier_type, identifier_type.upper())


def _query_identifier_reason(identifier_type: str) -> str:
    return {
        "vin": "Use this VIN to verify the exact vehicle and recall campaign on the official NHTSA page.",
        "ndc": "Use this NDC to verify the exact drug product, package, labeler, and recall status.",
        "upc": "Use this UPC to verify the exact consumer product or food package against official records.",
        "udi": "Use this UDI to verify the exact medical device identity against official records.",
    }.get(identifier_type, "Verify this identifier against the official source record.")


def build_identifier_check(
    *,
    detected_identifiers: dict[str, str | None],
    records: list[NormalizedSafetyRecord],
) -> dict[str, Any]:
    detected: list[IdentifierCheckItem] = []
    to_verify: list[IdentifierCheckItem] = []

    for identifier_type, value in detected_identifiers.items():
        if not value:
            continue

        label = _query_identifier_label(identifier_type)
        reason = _query_identifier_reason(identifier_type)
        _append_unique_item(
            detected,
            type=identifier_type,
            label=label,
            value=value,
            source="query",
            reason=reason,
        )
        _append_unique_item(
            to_verify,
            type=identifier_type,
            label=label,
            value=value,
            source="query",
            reason=reason,
        )

    for record in records:
        source_name = record.source_name or "returned public record"

        if record.recall_number:
            recall_label = (
                "NHTSA campaign number"
                if "NHTSA" in source_name
                else "Recall or reference number"
            )
            _append_unique_item(
                to_verify,
                type="campaign_number" if "NHTSA" in source_name else "recall_number",
                label=recall_label,
                value=record.recall_number,
                source=source_name,
                reason="Match this official record number before acting on the result.",
            )

        for model in record.affected_models:
            _append_unique_item(
                to_verify,
                type="model",
                label="Model or affected item",
                value=model,
                source=source_name,
                reason="Match the affected model, item, year, package, or device identity.",
            )

        for lot in record.affected_lots:
            _append_unique_item(
                to_verify,
                type="lot",
                label="Lot, package, or product identifier",
                value=lot,
                source=source_name,
                reason="Match the exact lot, package, code, strength, route, or listed identifier.",
            )

    if not to_verify:
        _append_unique_item(
            to_verify,
            type="product_identity",
            label="Product identity",
            value=None,
            source="Dav AI",
            reason="Verify product name, brand, model, package, lot, code, date, or official identifier before acting.",
        )

    return {
        "detected": [item.as_response_dict() for item in detected],
        "to_verify": [item.as_response_dict() for item in to_verify],
        "user_message": (
            "Verify exact identifiers before acting on any public safety record. "
            "No returned record proves every unit is recalled or safe."
        ),
    }
