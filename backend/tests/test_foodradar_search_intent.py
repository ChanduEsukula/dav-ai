from app.services.foodradar_search_intent import classify_foodradar_search_intent


def test_chicken_is_classified_as_poultry_meat_intent():
    intent = classify_foodradar_search_intent("chicken")

    assert intent.intent_type == "poultry_meat"
    assert intent.primary_source_hint == "usda_fsis"
    assert intent.search_strategy_used == "intent_poultry_meat_v1"
    assert "chicken of the sea" in intent.excluded_brand_phrases


def test_chicken_of_the_sea_is_classified_as_brand_intent():
    intent = classify_foodradar_search_intent("Chicken of the Sea")

    assert intent.intent_type == "brand"
    assert intent.primary_source_hint == "openfda_food"
    assert intent.search_strategy_used == "brand_exact_phrase"
    assert intent.excluded_brand_phrases == []


def test_beef_is_classified_as_meat_intent():
    intent = classify_foodradar_search_intent("beef")

    assert intent.intent_type == "meat"
    assert intent.primary_source_hint == "usda_fsis"
    assert "meat" in intent.expanded_terms


def test_salmonella_is_classified_as_hazard_intent():
    intent = classify_foodradar_search_intent("salmonella")

    assert intent.intent_type == "hazard"
    assert intent.primary_source_hint == "multi_source"


def test_unknown_query_falls_back_to_general_food():
    intent = classify_foodradar_search_intent("granola bar")

    assert intent.intent_type == "general_food"
    assert intent.search_strategy_used == "multi_source_exact_phrase"


def test_foodradar_query_normalization_handles_common_typos_and_spacing():
    cases = [
        ("chiken", "chicken", "poultry_meat"),
        ("protien powder", "protein powder", "supplement"),
        ("proteinpowder", "protein powder", "supplement"),
        ("protein-powder", "protein powder", "supplement"),
        ("chicken,", "chicken", "poultry_meat"),
        ("E coli", "e. coli", "hazard"),
        ("e-coli", "e. coli", "hazard"),
        ("e.coli", "e. coli", "hazard"),
        ("multivitamin", "vitamin", "supplement"),
        ("vitamins", "vitamin", "supplement"),
        ("  protein    powder  ", "protein powder", "supplement"),
    ]

    for raw_query, expected_normalized_query, expected_intent in cases:
        intent = classify_foodradar_search_intent(raw_query)

        assert intent.normalized_query == expected_normalized_query
        assert intent.intent_type == expected_intent
