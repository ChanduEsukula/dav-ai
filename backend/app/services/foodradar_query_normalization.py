from app.services.query_normalization import (
    QueryNormalization as FoodRadarQueryNormalization,
)
from app.services.query_normalization import normalize_safety_query


def normalize_foodradar_query(raw_query: str) -> FoodRadarQueryNormalization:
    return normalize_safety_query(raw_query, "food")
