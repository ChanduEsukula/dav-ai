from app.services.search_workflows.product_category_classifier import classify_product_category
from app.sources.registry import (
    CPSC_RECALLS_API,
    CDC_FOODBORNE_OUTBREAKS,
    DAILYMED_SPL_API,
    FDA_RECALLS_MARKET_WITHDRAWALS_SAFETY_ALERTS,
    FDA_SAFETY_COMMUNICATIONS,
    NHTSA_RECALLS_API_DATASETS,
    NHTSA_VPIC_VIN_DECODER_API,
    OPENFDA_DEVICE_ENFORCEMENT,
    OPENFDA_DEVICE_EVENT,
    OPENFDA_DRUG_ENFORCEMENT,
    OPENFDA_DRUG_LABEL,
    OPENFDA_FOOD_ENFORCEMENT,
    OPENFDA_NDC_DIRECTORY,
    OPENFDA_UDI_DIRECTORY,
    RXNORM_RXNAV_API,
    USDA_FSIS_RECALL,
)


def _source_ids(query: str) -> set[str]:
    return set(classify_product_category(query).suggested_source_ids)


def test_food_examples_classify_with_food_sources_and_relevant_flags():
    chicken_broth = classify_product_category("chicken broth")
    assert chicken_broth.primary_category == "food"
    assert chicken_broth.flags["fsis_relevant"] is True
    assert {
        OPENFDA_FOOD_ENFORCEMENT["source_id"],
        USDA_FSIS_RECALL["source_id"],
        FDA_RECALLS_MARKET_WITHDRAWALS_SAFETY_ALERTS["source_id"],
        CDC_FOODBORNE_OUTBREAKS["source_id"],
    }.issubset(set(chicken_broth.suggested_source_ids))

    peanut_butter = classify_product_category("peanut butter")
    assert peanut_butter.primary_category == "food"
    assert peanut_butter.flags["allergen_relevant"] is True
    assert {
        OPENFDA_FOOD_ENFORCEMENT["source_id"],
        FDA_RECALLS_MARKET_WITHDRAWALS_SAFETY_ALERTS["source_id"],
        CDC_FOODBORNE_OUTBREAKS["source_id"],
    }.issubset(set(peanut_butter.suggested_source_ids))

    for query in ["protein bar", "baby formula", "frozen chicken"]:
        result = classify_product_category(query)
        assert result.primary_category == "food"
        assert OPENFDA_FOOD_ENFORCEMENT["source_id"] in result.suggested_source_ids

    assert classify_product_category("frozen chicken").flags["fsis_relevant"] is True


def test_sunscreen_classifies_as_drug_with_cosmetic_context():
    result = classify_product_category("sunscreen")

    assert result.primary_category == "drug"
    assert "cosmetic" in result.secondary_categories
    assert result.flags["otc_drug_possible"] is True
    assert result.flags["cosmetic_possible"] is True
    assert OPENFDA_DRUG_ENFORCEMENT["source_id"] in result.suggested_source_ids
    assert FDA_RECALLS_MARKET_WITHDRAWALS_SAFETY_ALERTS["source_id"] in result.suggested_source_ids


def test_drug_device_consumer_and_vehicle_examples_route_to_expected_sources():
    for query in ["eye drops", "metformin", "ibuprofen"]:
        source_ids = _source_ids(query)
        assert OPENFDA_DRUG_ENFORCEMENT["source_id"] in source_ids
        assert RXNORM_RXNAV_API["source_id"] in source_ids
        assert DAILYMED_SPL_API["source_id"] in source_ids
        assert OPENFDA_DRUG_LABEL["source_id"] in source_ids
        assert OPENFDA_NDC_DIRECTORY["source_id"] in source_ids

    for query in ["CPAP", "insulin pump"]:
        source_ids = _source_ids(query)
        assert OPENFDA_DEVICE_ENFORCEMENT["source_id"] in source_ids
        assert OPENFDA_DEVICE_EVENT["source_id"] in source_ids
        assert OPENFDA_UDI_DIRECTORY["source_id"] in source_ids
        assert FDA_SAFETY_COMMUNICATIONS["source_id"] in source_ids

    for query in ["air fryer", "stroller"]:
        assert CPSC_RECALLS_API["source_id"] in _source_ids(query)

    for query in ["Toyota Camry", "BMW X3"]:
        source_ids = _source_ids(query)
        assert NHTSA_RECALLS_API_DATASETS["source_id"] in source_ids
        assert NHTSA_VPIC_VIN_DECODER_API["source_id"] in source_ids


def test_unknown_query_uses_broad_non_vehicle_fallback():
    result = classify_product_category("florble snargle")

    assert result.primary_category == "unknown"
    assert result.confidence == "low"
    assert {
        FDA_RECALLS_MARKET_WITHDRAWALS_SAFETY_ALERTS["source_id"],
        CPSC_RECALLS_API["source_id"],
        OPENFDA_FOOD_ENFORCEMENT["source_id"],
        OPENFDA_DRUG_ENFORCEMENT["source_id"],
        OPENFDA_DEVICE_ENFORCEMENT["source_id"],
    }.issubset(set(result.suggested_source_ids))
    assert NHTSA_RECALLS_API_DATASETS["source_id"] not in result.suggested_source_ids
