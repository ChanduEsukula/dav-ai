from app.services.search_workflows.real_world_query_understanding import (
    understand_real_world_safety_query,
)


def test_corrects_common_drug_typo_and_expands_brand_to_generic():
    result = understand_real_world_safety_query("tylonal")

    assert result.normalized_query == "tylenol"
    assert result.search_query == "tylenol"
    assert "tylonal → tylenol" in result.corrections_applied
    assert "acetaminophen" in result.expanded_terms
    assert "drug" in result.query_type_hints


def test_expands_advil_to_ibuprofen_without_replacing_user_brand():
    result = understand_real_world_safety_query("Advil")

    assert result.normalized_query == "advil"
    assert result.search_query == "advil"
    assert "ibuprofen" in result.expanded_terms
    assert "drug" in result.query_type_hints


def test_corrects_benadryl_typo_and_expands_generic_name():
    result = understand_real_world_safety_query("benedryl")

    assert result.normalized_query == "benadryl"
    assert "benedryl → benadryl" in result.corrections_applied
    assert "diphenhydramine" in result.expanded_terms
    assert "drug" in result.query_type_hints


def test_normalizes_joined_consumer_product_terms():
    result = understand_real_world_safety_query("airfryer powerbank carseat")

    assert result.normalized_query == "air fryer power bank car seat"
    assert "airfryer → air fryer" in result.corrections_applied
    assert "powerbank → power bank" in result.corrections_applied
    assert "carseat → car seat" in result.corrections_applied
    assert "consumer_product" in result.query_type_hints


def test_normalizes_common_medical_device_wording():
    result = understand_real_world_safety_query("blood sugar monitor")

    assert result.normalized_query == "glucose meter"
    assert "blood sugar monitor → glucose meter" in result.corrections_applied
    assert "medical_device" in result.query_type_hints


def test_normalizes_cpap_machine_wording():
    result = understand_real_world_safety_query("CPAP machine")

    assert result.normalized_query == "cpap"
    assert "cpap machine → cpap" in result.corrections_applied
    assert "medical_device" in result.query_type_hints


def test_detects_vin_with_spaces_and_lowercase():
    result = understand_real_world_safety_query(" 1hg cm82633a 004352 ")

    assert result.detected_identifiers["vin"] == "1HGCM82633A004352"
    assert "vehicle" in result.query_type_hints


def test_detects_ndc_with_spaces():
    result = understand_real_world_safety_query("NDC 66715 6547")

    assert result.detected_identifiers["ndc"] == "667156547"
    assert result.detected_identifiers["upc"] is None
    assert "drug" in result.query_type_hints


def test_detects_upc_without_confusing_it_for_ndc():
    result = understand_real_world_safety_query("0 36000 29145 2")

    assert result.detected_identifiers["upc"] == "036000291452"
    assert result.detected_identifiers["ndc"] is None
    assert "consumer_product" in result.query_type_hints


def test_query_understanding_tracks_expansion_search_terms_used_as_empty_initially():
    result = understand_real_world_safety_query("Advil")

    assert result.expanded_terms == ["ibuprofen"]
    assert result.expansion_search_terms_used == []


def test_detects_udi_identifier_as_medical_device():
    result = understand_real_world_safety_query("UDI 00312345678901")

    assert result.detected_identifiers["udi"] == "00312345678901"
    assert result.detected_identifiers["upc"] is None
    assert "medical_device" in result.query_type_hints


def test_detects_vaccine_query_as_vaccine_signal():
    result = understand_real_world_safety_query("MMR vaccine rash")

    assert "vaccine" in result.query_type_hints
