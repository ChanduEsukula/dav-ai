import pytest

from app.services.query_normalization import normalize_safety_query


@pytest.mark.parametrize(
    ("area", "raw_query", "normalized_query"),
    [
        ("food", "strawberries", "strawberry"),
        ("food", "berries", "berry"),
        ("food", "eggs", "egg"),
        ("food", "vitamins", "vitamin"),
        ("food", "cookies", "cookie"),
        ("food", "tomatoes", "tomato"),
        ("food", "potatoes", "potato"),
        ("food", "proteinpowder", "protein powder"),
        ("food", "peanutbutters", "peanut butter"),
        ("food", "chickenbreast", "chicken breast"),
        ("cosmetic", "hairdye", "hair dye"),
        ("cosmetic", "hairdyes", "hair dye"),
        ("cosmetic", "sunscrean", "sunscreen"),
        ("cosmetic", "sun screen", "sunscreen"),
        ("cosmetic", "sunscreens", "sunscreen"),
        ("cosmetic", "moisturizers", "moisturizer"),
        ("cosmetic", "lipsticks", "lipstick"),
        ("cosmetic", "shampoos", "shampoo"),
        ("cosmetic", "conditioners", "conditioner"),
        ("pharmacy", "xanex", "xanax"),
        ("pharmacy", "metforimn", "metformin"),
        ("pharmacy", "metformins", "metformin"),
        ("pharmacy", "ibuprofens", "ibuprofen"),
        ("pharmacy", "amoxycillin", "amoxicillin"),
        ("pharmacy", "acetaminophin", "acetaminophen"),
        ("pharmacy", "aspirins", "aspirin"),
    ],
)
def test_normalizes_only_approved_aliases(area, raw_query, normalized_query):
    result = normalize_safety_query(raw_query, area)

    assert result.raw_query == raw_query
    assert result.normalized_query == normalized_query
    assert result.correction_applied is True
    assert normalized_query in result.suggestion_message
    assert raw_query in result.suggestion_message


def test_does_not_apply_general_plural_stemming():
    result = normalize_safety_query("glasses", "cosmetic")

    assert result.normalized_query == "glasses"
    assert result.correction_applied is False
    assert result.suggestion_message is None


def test_preserves_original_query_and_casing_without_an_alias():
    result = normalize_safety_query("  Xanax   XR  ", "pharmacy")

    assert result.raw_query == "  Xanax   XR  "
    assert result.normalized_query == "xanax xr"
    assert result.correction_applied is False
