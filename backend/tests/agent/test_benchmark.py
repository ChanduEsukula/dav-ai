from app.agent.benchmark import response_metrics
from .test_orchestrator import proposal


def test_benchmark_separates_schema_selection_reference_and_hallucination_metrics():
    response = proposal(arguments={"product_ref": "p_correct"}, content="Recall D-9999-2099 is stored.")
    metrics = response_metrics(response, "p_correct")
    assert metrics["valid_tool_call"] and metrics["correct_tool_selection"]
    assert metrics["product_reference_preserved"] and metrics["argument_schema_compliant"]
    assert metrics["unsupported_recall_claim"]
    response = proposal("resolve_drug_product", {"query": "Xanax"})
    metrics = response_metrics(response, "p_correct")
    assert metrics["valid_tool_call"] and not metrics["correct_tool_selection"]
    assert not metrics["product_reference_preserved"]


def test_missing_call_narrative_cannot_be_counted_as_success():
    metrics = response_metrics({"message": {"content": "Recall D-0161-2016 exists."}}, "p_correct")
    assert not metrics["valid_tool_call"]
    assert metrics["unverified_answer_without_tool"]
    assert not metrics["unsupported_recall_claim"]  # No false claim of broad factual verification.
