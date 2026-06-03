"""Shared public source registry for Dav AI.

This module is the single source of truth for public/data sources shown by
System/Data Quality and Data Sources. Keep Saved Monitors out of this list
because Saved Monitors is an internal workflow, not an external public source.
"""

OPENFDA_DRUG_ENFORCEMENT = {
    "source_id": "openfda_drug_enforcement",
    "source_name": "openFDA Drug Enforcement API",
    "endpoint": "https://api.fda.gov/drug/enforcement.json",
    "module": "RecallRadar",
    "description": "Drug recall enforcement records from openFDA.",
    "update_cadence": "Source-dependent FDA updates",
}

OPENFDA_DRUG_EVENT = {
    "source_id": "openfda_drug_event",
    "source_name": "openFDA Drug Event API",
    "endpoint": "https://api.fda.gov/drug/event.json",
    "module": "DrugSignal",
    "description": "FAERS adverse-event and medication-error reports from openFDA.",
    "update_cadence": "Periodic FDA FAERS updates",
}


OPENFDA_COSMETIC_EVENT = {
    "source_id": "openfda_cosmetic_event",
    "source_name": "openFDA Cosmetic Event API",
    "endpoint": "https://api.fda.gov/cosmetic/event.json",
    "module": "CosmeticSignal",
    "description": "Cosmetic adverse-event reports from openFDA for skincare, makeup, hair, fragrance, and related products.",
    "update_cadence": "Source-dependent FDA cosmetic event updates",
}


OPENFDA_FOOD_ENFORCEMENT = {
    "source_id": "openfda_food_enforcement",
    "source_name": "openFDA Food Enforcement API",
    "endpoint": "https://api.fda.gov/food/enforcement.json",
    "module": "FoodRadar",
    "description": "Food, supplement, grocery, and packaged-food recall enforcement records from openFDA.",
    "update_cadence": "Source-dependent FDA updates",
}


USDA_FSIS_RECALL = {
    "source_id": "usda_fsis_recall",
    "source_name": "USDA FSIS Recall API",
    "endpoint": "https://www.fsis.usda.gov/fsis/api/recall/v/1",
    "module": "FoodRadar",
    "description": "Meat, poultry, egg-product recall and public-health-alert records from USDA FSIS.",
    "update_cadence": "Real-time FSIS recall and public health alert updates",
}

REGIONAL_HEALTH_PULSE_DEMO = {
    "source_id": "regional_health_pulse_demo",
    "source_name": "Regional Health Pulse MVP scaffold",
    "endpoint": "https://healthdata.gov/",
    "module": "RegionalHealthPulse",
    "description": "Demo public-health signal scaffold for Regional Health Pulse backend v1. This is not live CDC/HHS surveillance yet.",
    "update_cadence": "MVP scaffold; live public source cadence not configured yet",
}

REGISTERED_SOURCES = [
    OPENFDA_DRUG_ENFORCEMENT,
    OPENFDA_DRUG_EVENT,
    OPENFDA_COSMETIC_EVENT,
    OPENFDA_FOOD_ENFORCEMENT,
    USDA_FSIS_RECALL,
    REGIONAL_HEALTH_PULSE_DEMO,
]