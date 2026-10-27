"""Additive medication discovery wire contract; not an exact-product authorization."""
from typing import Any, Literal
from pydantic import BaseModel, Field
from app.schemas.drugs import DrugOverview

class LabelInventory(BaseModel):
    distinct_admitted_records: int = Field(ge=0)
    product_label_links: int = Field(ge=0)
    products_with_labels: int = Field(ge=0)

class FormulationGroup(BaseModel):
    formulation_id: str | None
    product_ids: list[str]

class RecallInventory(BaseModel):
    distinct_linked_records: int = Field(ge=0)
    product_recall_links: int = Field(ge=0)
    records: list[dict[str, Any]]

class MedicationOverview(BaseModel):
    query: str
    match_scope: Literal['stored_brand_alias_matches', 'bounded_catalog_search_matches']
    matched_product_count: int = Field(ge=0, le=100)
    truncated: bool
    products: list[DrugOverview]
    formulations: list[FormulationGroup]
    labels: LabelInventory
    recalls: RecallInventory
    ingredients: list[dict[str, Any]]
    release: dict[str, Any]
    limitations: list[str]

class InventoryMetric(BaseModel):
    key: str
    label: str
    value: int = Field(ge=0)
    definition: str
    source: str
    window: str

class DataInventory(BaseModel):
    release: dict[str, Any]
    metrics: list[InventoryMetric]
    limitations: list[str]
