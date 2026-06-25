from app.services.search_workflows.real_world_query_understanding import (
    understand_real_world_safety_query,
)
from app.services.search_workflows.real_world_source_planner import (
    plan_real_world_safety_sources,
)
from app.sources.registry import (
    CPSC_RECALLS_API,
    DAILYMED_SPL_API,
    FDA_RECALLS_MARKET_WITHDRAWALS_SAFETY_ALERTS,
    NHTSA_RECALLS_API_DATASETS,
    NHTSA_VPIC_VIN_DECODER_API,
    OPENFDA_DEVICE_ENFORCEMENT,
    OPENFDA_DEVICE_EVENT,
    OPENFDA_UDI_DIRECTORY,
    OPENFDA_DRUG_ENFORCEMENT,
    OPENFDA_DRUG_LABEL,
    OPENFDA_FOOD_ENFORCEMENT,
    OPENFDA_NDC_DIRECTORY,
    RXNORM_RXNAV_API,
    USDA_FSIS_RECALL,
)


def _plan(query: str):
    return plan_real_world_safety_sources(understand_real_world_safety_query(query))


def test_microwave_routes_to_consumer_product_sources_without_drug_sources():
    plan = _plan("microwave")

    assert plan.intent == "consumer_product"
    assert CPSC_RECALLS_API["source_id"] in plan.sources_to_check
    assert FDA_RECALLS_MARKET_WITHDRAWALS_SAFETY_ALERTS["source_id"] in plan.sources_to_check

    assert OPENFDA_DRUG_LABEL["source_id"] not in plan.sources_to_check
    assert OPENFDA_NDC_DIRECTORY["source_id"] not in plan.sources_to_check
    assert RXNORM_RXNAV_API["source_id"] not in plan.sources_to_check
    assert DAILYMED_SPL_API["source_id"] not in plan.sources_to_check


def test_air_fryer_routes_to_consumer_product_sources():
    plan = _plan("air fryer")

    assert plan.intent == "consumer_product"
    assert plan.primary_source_ids == [CPSC_RECALLS_API["source_id"]]


def test_advil_routes_to_drug_sources():
    plan = _plan("Advil")

    assert plan.intent == "drug"
    assert OPENFDA_DRUG_ENFORCEMENT["source_id"] in plan.sources_to_check
    assert RXNORM_RXNAV_API["source_id"] in plan.sources_to_check
    assert OPENFDA_NDC_DIRECTORY["source_id"] in plan.sources_to_check
    assert OPENFDA_DRUG_LABEL["source_id"] in plan.sources_to_check

    assert CPSC_RECALLS_API["source_id"] not in plan.sources_to_check


def test_tylonal_routes_to_drug_sources_after_correction():
    plan = _plan("tylonal")

    assert plan.intent == "drug"
    assert OPENFDA_DRUG_LABEL["source_id"] in plan.sources_to_check


def test_toyota_camry_routes_to_vehicle_sources_only():
    plan = _plan("2020 Toyota Camry")

    assert plan.intent == "vehicle"
    assert NHTSA_RECALLS_API_DATASETS["source_id"] in plan.sources_to_check
    assert NHTSA_VPIC_VIN_DECODER_API["source_id"] in plan.sources_to_check
    assert OPENFDA_DRUG_LABEL["source_id"] not in plan.sources_to_check


def test_blood_sugar_monitor_routes_to_medical_device_sources():
    plan = _plan("blood sugar monitor")

    assert plan.intent == "medical_device"
    assert OPENFDA_DEVICE_ENFORCEMENT["source_id"] in plan.sources_to_check
    assert OPENFDA_DEVICE_EVENT["source_id"] in plan.sources_to_check
    assert OPENFDA_UDI_DIRECTORY["source_id"] in plan.sources_to_check
    assert OPENFDA_DRUG_LABEL["source_id"] not in plan.sources_to_check


def test_chicken_routes_to_food_sources():
    plan = _plan("chicken")

    assert plan.intent == "food"
    assert OPENFDA_FOOD_ENFORCEMENT["source_id"] in plan.sources_to_check
    assert USDA_FSIS_RECALL["source_id"] in plan.sources_to_check


def test_bare_sunscreen_requires_clarification_instead_of_broad_fanout():
    plan = _plan("sunscreen")

    assert plan.intent == "ambiguous"
    assert plan.clarification_required is True
    assert plan.sources_to_check == []
