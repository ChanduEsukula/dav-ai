from dataclasses import dataclass


@dataclass(frozen=True)
class FoodRadarSearchIntent:
    raw_query: str
    normalized_query: str
    intent_type: str
    primary_source_hint: str
    expanded_terms: list[str]
    excluded_brand_phrases: list[str]
    search_strategy_used: str


POULTRY_TERMS = {
    "chicken",
    "turkey",
    "duck",
    "poultry",
    "hen",
}

MEAT_TERMS = {
    "beef",
    "ground beef",
    "steak",
    "pork",
    "ham",
    "bacon",
    "sausage",
    "lamb",
}

EGG_TERMS = {
    "egg",
    "eggs",
    "egg product",
    "liquid egg",
}

DAIRY_TERMS = {
    "milk",
    "cheese",
    "butter",
    "yogurt",
    "cream",
}

SUPPLEMENT_TERMS = {
    "protein",
    "protein powder",
    "whey",
    "whey protein",
    "creatine",
    "pre workout",
    "pre-workout",
    "supplement",
    "dietary supplement",
    "vitamin",
}

HAZARD_TERMS = {
    "salmonella",
    "listeria",
    "ecoli",
    "e. coli",
    "allergen",
    "undeclared allergen",
    "foreign material",
    "botulism",
}

KNOWN_BRAND_PHRASES = {
    "chicken of the sea",
}


def _unique_terms(terms: list[str]) -> list[str]:
    return list(dict.fromkeys(term for term in terms if term))


def _build_supplement_terms(normalized_query: str) -> list[str]:
    if normalized_query in {"protein", "protein powder", "whey", "whey protein"}:
        return _unique_terms(
            [
                normalized_query,
                "protein",
                "whey",
                "whey protein",
                "protein powder",
                "dietary supplement",
                "supplement",
            ]
        )

    if normalized_query in {"creatine", "pre workout", "pre-workout"}:
        return _unique_terms(
            [
                normalized_query,
                "creatine",
                "pre workout",
                "pre-workout",
                "dietary supplement",
                "supplement",
            ]
        )

    if normalized_query in {"vitamin", "supplement", "dietary supplement"}:
        return _unique_terms(
            [
                normalized_query,
                "vitamin",
                "dietary supplement",
                "supplement",
            ]
        )

    return [normalized_query]


def classify_foodradar_search_intent(query: str) -> FoodRadarSearchIntent:
    normalized_query = " ".join(query.lower().strip().split())

    if normalized_query in KNOWN_BRAND_PHRASES:
        return FoodRadarSearchIntent(
            raw_query=query,
            normalized_query=normalized_query,
            intent_type="brand",
            primary_source_hint="openfda_food",
            expanded_terms=[normalized_query],
            excluded_brand_phrases=[],
            search_strategy_used="brand_exact_phrase",
        )

    if normalized_query in POULTRY_TERMS:
        return FoodRadarSearchIntent(
            raw_query=query,
            normalized_query=normalized_query,
            intent_type="poultry_meat",
            primary_source_hint="usda_fsis",
            expanded_terms=[normalized_query, "poultry"],
            excluded_brand_phrases=["chicken of the sea"],
            search_strategy_used="intent_poultry_meat_v1",
        )

    if normalized_query in MEAT_TERMS:
        return FoodRadarSearchIntent(
            raw_query=query,
            normalized_query=normalized_query,
            intent_type="meat",
            primary_source_hint="usda_fsis",
            expanded_terms=[normalized_query, "meat"],
            excluded_brand_phrases=[],
            search_strategy_used="intent_meat_v1",
        )

    if normalized_query in EGG_TERMS:
        return FoodRadarSearchIntent(
            raw_query=query,
            normalized_query=normalized_query,
            intent_type="egg_product",
            primary_source_hint="usda_fsis",
            expanded_terms=[normalized_query, "egg product"],
            excluded_brand_phrases=[],
            search_strategy_used="intent_egg_product_v1",
        )

    if normalized_query in DAIRY_TERMS:
        return FoodRadarSearchIntent(
            raw_query=query,
            normalized_query=normalized_query,
            intent_type="dairy",
            primary_source_hint="openfda_food",
            expanded_terms=[normalized_query, "dairy"],
            excluded_brand_phrases=[],
            search_strategy_used="intent_dairy_v1",
        )

    if normalized_query in SUPPLEMENT_TERMS:
        return FoodRadarSearchIntent(
            raw_query=query,
            normalized_query=normalized_query,
            intent_type="supplement",
            primary_source_hint="openfda_food",
            expanded_terms=_build_supplement_terms(normalized_query),
            excluded_brand_phrases=[],
            search_strategy_used="intent_supplement_v1",
        )

    if normalized_query in HAZARD_TERMS:
        return FoodRadarSearchIntent(
            raw_query=query,
            normalized_query=normalized_query,
            intent_type="hazard",
            primary_source_hint="multi_source",
            expanded_terms=[normalized_query],
            excluded_brand_phrases=[],
            search_strategy_used="intent_hazard_v1",
        )

    return FoodRadarSearchIntent(
        raw_query=query,
        normalized_query=normalized_query,
        intent_type="general_food",
        primary_source_hint="multi_source",
        expanded_terms=[normalized_query],
        excluded_brand_phrases=[],
        search_strategy_used="multi_source_exact_phrase",
    )