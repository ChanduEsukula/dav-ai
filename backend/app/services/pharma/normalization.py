"""Exact matching only. Never guess NDC padding or an ambiguous formulation."""
import re
from dataclasses import dataclass
from typing import Any


def normalize_name(value: str) -> str:
    return " ".join(value.casefold().split())


def normalize_ndc(value: str) -> str | None:
    value = value.strip()
    return value if re.fullmatch(r"\d+(?:-\d+){1,2}|\d{10,12}", value) else None


def normalize_rxcui(value: str) -> str | None:
    value = value.strip()
    return value if re.fullmatch(r"[1-9]\d*", value) else None


@dataclass(frozen=True)
class Resolution:
    drug: dict[str, Any] | None
    method: str | None
    reason: str


def resolve_drug(repository, *, rxcui: str | None = None, ndc: str | None = None,
                 name: str | None = None) -> Resolution:
    """Resolve in priority order; supplied conflicting/ambiguous keys fail closed."""
    candidates = None
    matched_rows = {}
    chosen_method = None
    for method, value, lookup in (
        ("rxcui", rxcui, repository.find_by_rxcui),
        ("ndc", ndc, repository.find_by_ndc),
        ("name", name, repository.find_by_normalized_name),
    ):
        if not value:
            continue
        rows = lookup(value)
        if not rows:
            continue
        identifiers = {str(row['id']) for row in rows}
        matched_rows.update({str(row['id']): row for row in rows})
        candidates = identifiers if candidates is None else candidates & identifiers
        if not candidates:
            return Resolution(None, None, "conflicting_identifiers")
        if len(candidates) == 1 and chosen_method is None:
            chosen_method = method
    if candidates is None:
        return Resolution(None, None, "unresolved")
    if len(candidates) != 1:
        return Resolution(None, None, "ambiguous")
    return Resolution(matched_rows[next(iter(candidates))], chosen_method, "matched")
