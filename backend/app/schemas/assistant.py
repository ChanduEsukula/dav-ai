from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


AssistantModule = Literal["recall", "drug_event", "food", "cosmetic"]


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
