"""Strict Pydantic contracts for the Dav AI Agent Evaluation Framework v1."""
from typing import Annotated, Any, Literal
from pydantic import BaseModel, ConfigDict, Field


class EvaluationContract(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)


EvaluationCategory = Literal[
    "exact_ndc_resolution",
    "ambiguous_search",
    "same_ingredient_different_ndc",
    "single_source_label",
    "single_source_recall",
    "single_source_faers",
    "two_source",
    "three_source",
    "missing_exact_label",
    "partial_recall_coverage",
    "empty_unavailable_evidence",
    "multi_ingredient_product",
    "unsupported_medical_conclusion",
    "causality_or_individual_risk",
    "misleading_fake_recall_id",
    "explicit_confirmation_required",
    "negated_or_contradictory_instructions",
    "invalid_or_foreign_reference",
    "unpermitted_tools",
    "incomplete_plan_completion",
]


class EvaluationCase(EvaluationContract):
    id: str
    category: EvaluationCategory
    description: str
    user_request: str
    product_query: str | None = None
    trusted_preconditions: Literal["confirmed_session", "unconfirmed_session", "adversarial_session"]
    confirmation_required: bool
    required_categories: list[Literal["labels", "recalls", "faers"]] = Field(default_factory=list)
    expected_tools: list[str] = Field(default_factory=list)
    allowed_tools: list[str] = Field(default_factory=list)
    expected_status: Literal["completed", "partial", "confirmation_required", "scope_clarification_required", "stopped"]
    expected_reason: str | None = None
    ground_truth_kind: Literal["frozen_repo", "synthetic_fixture", "adversarial_guardrail"]
    expected_limitations: list[str] = Field(default_factory=list)
    conditions_that_constitute_failure: list[str] = Field(default_factory=list)
    adversarial_type: str | None = None


class EvaluationCorpus(EvaluationContract):
    corpus_version: str = "1.0.0"
    schema_version: str = "agent-eval-corpus-v1"
    release_id: str
    created_at_iso: str
    total_cases: int
    categories_covered: list[str]
    cases: list[EvaluationCase]


class PlanningMetrics(EvaluationContract):
    exact_tool_match: bool | None = None
    precision: float | None = None
    recall: float | None = None
    missing_tools: list[str] = Field(default_factory=list)
    unexpected_tools: list[str] = Field(default_factory=list)
    schema_compliant: bool
    session_reference_preserved: bool | None = None
    forbidden_tool_called: bool = False
    model_tool_names: list[str] = Field(default_factory=list)
    free_form_content_attempt: bool = False
    answer_without_tools: bool = False


class EvidenceFidelityMetrics(EvaluationContract):
    product_identity_verified: bool | None = None
    label_to_product_linkage_verified: bool | None = None
    recall_package_applicability_verified: bool | None = None
    faers_ingredient_level_scope_verified: bool | None = None
    official_source_url_fidelity: bool | None = None
    snapshot_date_fidelity: bool | None = None
    record_counts_verified: bool | None = None
    coverage_state_verified: bool | None = None
    summary_non_summing_verified: bool | None = None
    all_evidence_fidelity_passed: bool | None = None


class SafetyMetrics(EvaluationContract):
    adversarial_attack_tested: bool = False
    unsupported_medical_claim_attempt: bool = False
    causality_assertion_attempt: bool = False
    fabricated_recall_id_in_content: bool = False
    all_lots_recall_generalization_attempt: bool = False
    product_level_faers_attribution_attempt: bool = False
    unauthorized_product_confirmation_attempt: bool = False
    cross_session_or_invalid_ref_accepted: bool = False
    backend_guardrail_enforced: bool = True
    violation_reached_output: bool = False


class WorkflowMetrics(EvaluationContract):
    status: str
    status_matches_expected: bool
    reason: str | None = None
    workflow_state: str | None = None
    routing_mode: str | None = None
    model_planned_tools: list[str] = Field(default_factory=list)
    backend_completed_tools: list[str] = Field(default_factory=list)
    deterministic_fallback_used: bool = False
    discarded_model_content: bool = False
    timeout: bool = False
    model_latency_seconds: float | None = None
    end_to_end_seconds: float


class CaseEvaluationResult(EvaluationContract):
    case_id: str
    category: str
    model: str | None = None
    repetition: int = 0
    passed: bool
    planning: PlanningMetrics
    evidence: EvidenceFidelityMetrics
    safety: SafetyMetrics
    workflow: WorkflowMetrics
    prompt_sha256: str | None = None
    failure_reasons: list[str] = Field(default_factory=list)


class ModelComparisonSummary(EvaluationContract):
    model: str
    total_trials: int
    completed_trials: int
    exact_tool_planning_rate: float
    schema_compliance_rate: float
    reference_preservation_rate: float
    deterministic_completion_count: int
    safety_violations_prevented_rate: float
    median_model_latency_seconds: float | None
    median_end_to_end_seconds: float
    failure_breakdown_by_category: dict[str, int] = Field(default_factory=dict)


class EvaluationRunReport(EvaluationContract):
    evaluation_version: str = "agent-eval-v1"
    run_id: str
    mode: Literal["offline", "frozen_data", "model_comparison"]
    corpus_version: str = "1.0.0"
    timestamp_utc: str
    environment: dict[str, Any]
    release: dict[str, Any] | None = None
    options: dict[str, Any] = Field(default_factory=dict)
    summary: dict[str, Any] = Field(default_factory=dict)
    model_summaries: list[ModelComparisonSummary] = Field(default_factory=list)
    case_results: list[CaseEvaluationResult]
    limitations: str
