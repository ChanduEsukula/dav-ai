from __future__ import annotations

from pydantic import BaseModel


class DrugProvenance(BaseModel):
    source: str
    source_id: str
    source_record_id: str
    source_url: str | None = None
    observed_at: str | None = None


class DrugRxCUI(BaseModel):
    value: str
    concept_type: str | None = None
    is_unique_product: bool
    has_conflict: bool


class DrugOverview(BaseModel):
    id: str
    product_id: str

    generic_name: str | None
    brand_names: list[str]
    active_ingredients: list[str]
    ingredient_ids: list[str]

    strength: str | None
    dosage_form: str | None
    routes: list[str]
    manufacturers: list[str]

    product_ndcs: list[str]
    package_ndcs: list[str]

    # Temporary compatibility field.
    # Only populated when the release has exactly one RxCUI.
    rxcui: str | None

    # Canonical release representation.
    rxcuis: list[DrugRxCUI]

    is_combination: bool
    identity_partial: bool

    formulation_id: str | None
    application_number: str | None
    product_type: str | None
    marketing_category: str | None
    consumer_classification: str

    provenance: DrugProvenance


class DrugSearchResponse(BaseModel):
    query: str
    count: int
    limit: int
    offset: int
    results: list[DrugOverview]
