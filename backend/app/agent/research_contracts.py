"""Typed Agent v2 output contracts. These describe evidence, never medical advice."""
from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from app.services.pharma.evidence import official_source

Category = Literal["labels", "recalls", "faers"]
TOOLS = {"labels": "get_drug_label_evidence", "recalls": "search_historical_recalls",
         "faers": "get_faers_reporting_evidence"}


class Contract(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)


class ReleaseInfo(Contract):
    release_id: str
    contract_id: str
    policy_version: str
    schema_version: str
    build_version: str
    build_time_utc: str
    ndc_observation_date: str
    label_export_date: str
    window_start: str
    window_end: str
    publication_authorized: Literal[False]


class IdentitySource(Contract):
    source: str | None = None
    source_id: str | None = None
    source_record_id: str
    source_url: str
    observed_at: str | None = None

    @field_validator("source_url")
    @classmethod
    def official(cls, value):
        if not official_source(value):
            raise ValueError("Missing official source URL")
        return value


class MedicationIdentity(Contract):
    product_ref: str
    brand_names: list[str]
    generic_name: str | None
    strength: str | None
    dosage_form: str | None
    formulation_id: str
    routes: list[str]
    active_ingredients: list[str]
    ingredient_ids: list[str] = Field(default_factory=list)
    product_ndcs: list[str]
    package_ndcs: list[str]
    provenance: IdentitySource


class Coverage(Contract):
    ingredient_id: str | None = None
    state: str
    reason_code: str | None = None
    scope: str | None = None
    as_of_date: str | None = None
    source_date: str | None = None
    measured_count: int | None = None
    unresolved_count: int | None = None
    stored_record_count: int | None = None
    bounded: bool | None = None
    truncated: bool | None = None
    empty_message: str | None = None
    limitations: list[str]


class DatasetSource(Contract):
    source_id: str
    source_name: str
    source_url: str
    export_date: str
    observed_at: str | None = None

    @field_validator("source_url")
    @classmethod
    def official(cls, value):
        return IdentitySource.official(value)


class LabelSection(Contract):
    text: str | None
    field_present: bool
    state: str
    reason_code: str


class LabelRecord(Contract):
    id: str
    label_set_id: str
    label_version: str
    effective_date: str
    applicability_class: Literal["EXACT_PRODUCT"]
    evidence_scope: Literal["PRODUCT"]
    selection_status: Literal["SELECTED_STORED", "EARLIER_STORED"]
    match_method: str
    matched_value: str
    boxed_warning: str | None
    warnings_and_precautions: str | None
    warnings: str | None
    contraindications: str | None
    adverse_reactions: str | None
    drug_interactions: str | None
    section_states: dict[str, LabelSection]
    source: str
    source_record_id: str
    source_url: str

    @field_validator("source_url")
    @classmethod
    def official(cls, value):
        return IdentitySource.official(value)


class LabelCard(Contract):
    type: Literal["drug_label_evidence"] = "drug_label_evidence"
    scope: Literal["PRODUCT_LINKED_LABEL"] = "PRODUCT_LINKED_LABEL"
    product_ref: str
    release: ReleaseInfo
    source_snapshot_date: str
    coverage: Coverage
    records: list[LabelRecord]
    missing_sections: list[str]
    limitations: list[str]


Count = Annotated[int, Field(ge=0)]


class Analytics(Contract):
    window_start: str
    window_end: str
    report_count: Count
    unique_case_count: Count
    serious_report_count: Count
    serious_known_report_count: Count
    death_report_count: Count
    hospitalization_report_count: Count
    disability_report_count: Count
    life_threatening_report_count: Count
    suspect_report_count: Count
    concomitant_report_count: Count
    interacting_report_count: Count
    active_month_count: Count
    reaction_term_count: Count
    co_report_activity: Count
    count_unit: Literal["deduplicated ingredient-report associations"]
    date_basis: Literal["parsed latest-receipt month"]
    limitations: list[str]


class Reaction(Contract):
    reaction: str
    co_report_activity: Count
    active_months: Count
    rank: Annotated[int, Field(ge=1)]


class ReportingMonth(Contract):
    period: str
    report_count: Count
    serious_report_count: Count


class IngredientReporting(Contract):
    ingredient_id: str
    ingredient_name: str
    scope: Literal["INGREDIENT"]
    analytics: Analytics | None
    top_reported_reactions: list[Reaction]
    monthly: list[ReportingMonth]
    coverage: Coverage
    source: DatasetSource | None


class IngredientSummary(Contract):
    scope: Literal["INGREDIENT_COMPONENTS_ONLY"]
    ingredient_count: Count
    ingredients_with_analytics: Count
    ingredients_without_analytics: Count
    product_report_total: None
    limitation: str


class FaersCard(Contract):
    type: Literal["faers_reporting_evidence"] = "faers_reporting_evidence"
    scope: Literal["INGREDIENT_LEVEL_REPORTING_EVIDENCE"] = "INGREDIENT_LEVEL_REPORTING_EVIDENCE"
    product_ref: str  # Selection context only, never the scope of FAERS observations.
    release: ReleaseInfo
    coverage: Coverage
    records: list[IngredientReporting]
    summary: IngredientSummary
    limitations: list[str]


class RecallRecord(Contract):
    id: str
    recall_number: str
    classification: str
    reported_status: str | None
    reason_for_recall: str
    recalling_firm: str | None
    recall_initiation_date: str | None
    report_date: str | None
    lot_information: str | None
    lot_scope: str
    applicability_class: str
    match_method: str
    matched_value: str
    source_record_id: str
    source_url: str


class RecallCard(Contract):
    type: Literal["historical_recall_evidence"]
    product_ref: str
    product: MedicationIdentity
    release: ReleaseInfo
    records: list[RecallRecord]
    coverage: Coverage
    source_snapshot_date: str
    record_count: Count
    returned_count: Count
    results_truncated: bool
    limitations: list[str]
    interpretation: str


Card = Annotated[LabelCard | FaersCard | RecallCard, Field(discriminator="type")]


class BriefingSection(Contract):
    category: Category
    status: Literal["not_requested", "available", "incomplete", "unavailable", "failed"]
    reason: str | None = None
    evidence: Card | None = None


class RoutingInfo(Contract):
    mode: Literal["model", "deterministic", "deterministic_completion"]
    model_planned_tools: list[str]
    backend_completed_tools: list[str]
    discarded_model_content: bool


class RagPassage(Contract):
    chunk_id: str
    section: str
    ordinal: int
    text: str
    source_record_id: str | None = None
    source_url: str | None = None
    citation_tag: str


class RagEvidence(Contract):
    type: Literal["hybrid_rag_evidence"] = "hybrid_rag_evidence"
    status: Literal["supported", "candidate_only", "insufficient_evidence", "not_configured"]
    reason: str
    product_ref: str
    product_id: str
    requested_sections: list[str] = Field(default_factory=list)
    missing_sections: list[str] = Field(default_factory=list)
    route: str = "none"
    verified_answer: bool = False
    confidence: Literal["calibrated", "uncalibrated", "none"] = "none"
    passages: list[RagPassage] = Field(default_factory=list)
    degraded_reason: str | None = None
    limitations: list[str] = Field(default_factory=list)


class AnswerCitation(Contract):
    evidence_id: str = Field(pattern=r"^E[1-9][0-9]?$")
    category: Literal["labels"] = "labels"
    product_ref: str
    source_record_id: str
    source_url: str
    label_set_id: str
    label_version: str
    section: Literal["boxed_warning", "warnings_and_precautions", "warnings",
                     "contraindications", "drug_interactions", "adverse_reactions"]
    start: int = Field(ge=0)
    end: int = Field(gt=0)
    text_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    source_snapshot_date: str
    release_id: str

    @field_validator("source_url")
    @classmethod
    def official(cls, value):
        return IdentitySource.official(value)


class GroundedAnswer(Contract):
    status: Literal["generated", "insufficient_evidence", "unavailable", "invalid_output"]
    reason: str
    text: str | None = Field(default=None, max_length=1200)
    product_ref: str
    citations: list[AnswerCitation] = Field(default_factory=list)
    method: Literal["local_model_extractive"] = "local_model_extractive"
    limitations: list[str] = Field(default_factory=list)

    @model_validator(mode="after")
    def consistent_status(self):
        if self.status == "generated":
            if not self.text or not self.text.strip() or not 1 <= len(self.citations) <= 3:
                raise ValueError("Generated answers require text and citations")
            if (len({c.evidence_id for c in self.citations}) != len(self.citations)
                    or any(c.product_ref != self.product_ref or c.end <= c.start for c in self.citations)):
                raise ValueError("Answer citation binding mismatch")
        elif self.text is not None or self.citations:
            raise ValueError("Fallback answers cannot contain generated text or citations")
        return self


class ResearchBriefing(Contract):
    schema_version: Literal["agent-research-v2"] = "agent-research-v2"
    status: Literal["completed", "partial", "stopped"]
    workflow_state: Literal["COMPLETE", "PARTIAL", "STOPPED"]
    medication: MedicationIdentity
    requested_categories: list[Category]
    routing: RoutingInfo
    sections: list[BriefingSection]
    limitations: list[str]
    rag: RagEvidence | None = None
    answer: GroundedAnswer | None = None

