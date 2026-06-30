from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


AssistantModule = Literal["recall", "drug_event", "food", "cosmetic", "public_safety"]


class AssistantSourceCitation(BaseModel):
    model_config = ConfigDict(extra="forbid")

    label: str
    value: str


class AssistantModelInfo(BaseModel):
    model_config = ConfigDict(extra="forbid")

    provider: str
    model: str


class AssistantSafetyInfo(BaseModel):
    model_config = ConfigDict(extra="forbid")

    policy_version: str
    output_checked: bool


class AssistantRecallResultContext(BaseModel):
    model_config = ConfigDict(extra="forbid")

    recall_number: str | None = None
    product_description: str | None = None
    reason_for_recall: str | None = None
    classification: str | None = None
    status: str | None = None
    recall_initiation_date: str | None = None
    distribution_pattern: str | None = None
    recalling_firm: str | None = None
    risk_score_label: str
    risk_score_value: int


class AssistantRecallContext(BaseModel):
    model_config = ConfigDict(extra="forbid")

    top_results: list[AssistantRecallResultContext] = Field(default_factory=list, max_length=5)


class AssistantFoodResultContext(BaseModel):
    model_config = ConfigDict(extra="forbid")

    recall_number: str | None = None
    product_description: str | None = None
    reason_for_recall: str | None = None
    classification: str | None = None
    status: str | None = None
    recall_initiation_date: str | None = None
    report_date: str | None = None
    distribution_pattern: str | None = None
    recalling_firm: str | None = None
    source_type: str | None = None
    risk_score_label: str
    risk_score_value: int


class AssistantFoodContext(BaseModel):
    model_config = ConfigDict(extra="forbid")

    top_results: list[AssistantFoodResultContext] = Field(default_factory=list, max_length=5)


class AssistantCosmeticSignalScoreContext(BaseModel):
    model_config = ConfigDict(extra="forbid")

    score: int
    label: str
    review_priority: str
    data_confidence: str


class AssistantCosmeticReactionContext(BaseModel):
    model_config = ConfigDict(extra="forbid")

    reaction: str
    count: int


class AssistantCosmeticRecordContext(BaseModel):
    model_config = ConfigDict(extra="forbid")

    report_number: str | None = None
    report_date: str | None = None
    serious: str | None = None
    products: list[str] = Field(default_factory=list, max_length=10)
    reactions: list[str] = Field(default_factory=list, max_length=10)
    outcomes: list[str] = Field(default_factory=list, max_length=10)


class AssistantCosmeticContext(BaseModel):
    model_config = ConfigDict(extra="forbid")

    signal_score: AssistantCosmeticSignalScoreContext
    top_reactions: list[AssistantCosmeticReactionContext] = Field(default_factory=list, max_length=5)
    records: list[AssistantCosmeticRecordContext] = Field(default_factory=list, max_length=5)
    cosmetic_disclaimer: str


class AssistantDrugSignalScoreContext(BaseModel):
    model_config = ConfigDict(extra="forbid")

    score: int
    label: str
    review_priority: str
    data_confidence: str


class AssistantDrugReactionContext(BaseModel):
    model_config = ConfigDict(extra="forbid")

    reaction: str
    count: int


class AssistantDrugReactionCategoryContext(BaseModel):
    model_config = ConfigDict(extra="forbid")

    category: str
    count: int
    reactions: list[str] = Field(default_factory=list, max_length=10)


class AssistantDrugEventContext(BaseModel):
    model_config = ConfigDict(extra="forbid")

    intelligence_score: AssistantDrugSignalScoreContext
    top_reactions: list[AssistantDrugReactionContext] = Field(default_factory=list, max_length=5)
    reaction_categories: list[AssistantDrugReactionCategoryContext] = Field(default_factory=list, max_length=5)
    faers_disclaimer: str



class AssistantPublicSafetySummaryContext(BaseModel):
    model_config = ConfigDict(extra="forbid")

    query_type: str
    recall_or_enforcement_found: bool
    reference_or_label_found: bool
    signal_report_found: bool
    plain_language_summary: str
    suggested_next_steps: list[str] = Field(default_factory=list, max_length=6)
    caveat: str


class AssistantPublicSafetyIdentifierItemContext(BaseModel):
    model_config = ConfigDict(extra="forbid")

    type: str
    label: str
    value: str | None = None
    source: str
    reason: str


class AssistantPublicSafetyIdentifierCheckContext(BaseModel):
    model_config = ConfigDict(extra="forbid")

    user_message: str
    detected: list[AssistantPublicSafetyIdentifierItemContext] = Field(default_factory=list, max_length=8)
    to_verify: list[AssistantPublicSafetyIdentifierItemContext] = Field(default_factory=list, max_length=8)


class AssistantPublicSafetyCheckedSourceContext(BaseModel):
    model_config = ConfigDict(extra="forbid")

    source_id: str
    source_name: str
    source_type: str
    source_kind: str
    upstream_status: str
    record_count: int


class AssistantPublicSafetyFailedSourceContext(BaseModel):
    model_config = ConfigDict(extra="forbid")

    source_id: str
    source_name: str
    reason: str


class AssistantPublicSafetyRecordContext(BaseModel):
    model_config = ConfigDict(extra="forbid")

    title: str | None = None
    product_name: str | None = None
    brand_name: str | None = None
    company_name: str | None = None
    source_name: str
    source_type: str
    source_kind: str
    category: str | None = None
    reason: str | None = None
    hazard_type: str | None = None
    remedy: str | None = None
    published_date: str | None = None
    recall_number: str | None = None
    affected_models: list[str] = Field(default_factory=list, max_length=10)
    affected_lots: list[str] = Field(default_factory=list, max_length=10)
    record_url: str | None = None
    extraction_confidence: str | None = None
    source_text_excerpt: str | None = None


class AssistantPublicSafetyContext(BaseModel):
    model_config = ConfigDict(extra="forbid")

    summary: AssistantPublicSafetySummaryContext
    identifier_check: AssistantPublicSafetyIdentifierCheckContext
    sources_checked: list[AssistantPublicSafetyCheckedSourceContext] = Field(default_factory=list, max_length=12)
    sources_failed: list[AssistantPublicSafetyFailedSourceContext] = Field(default_factory=list, max_length=8)
    top_records: list[AssistantPublicSafetyRecordContext] = Field(default_factory=list, max_length=8)

class AssistantPageContext(BaseModel):
    model_config = ConfigDict(extra="forbid")

    query: str
    count: int
    source_name: str
    endpoint: str
    retrieval_timestamp: str
    audit_id: str
    limitations: list[str] = Field(default_factory=list, max_length=8)
    recall: AssistantRecallContext | None = None
    drug_event: AssistantDrugEventContext | None = None
    food: AssistantFoodContext | None = None
    cosmetic: AssistantCosmeticContext | None = None
    public_safety: AssistantPublicSafetyContext | None = None


class AssistantChatRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    module: AssistantModule
    question: str = Field(min_length=1, max_length=1000)
    page_context: AssistantPageContext


class AssistantChatResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    answer: str
    bullets: list[str]
    refused: bool
    refusal_reason: str | None = None
    source_citations: list[AssistantSourceCitation]
    limitations: list[str]
    model_info: AssistantModelInfo
    safety: AssistantSafetyInfo
