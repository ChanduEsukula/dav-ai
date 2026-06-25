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

RXNORM_RXNAV_API = {
    "source_id": "rxnorm_rxnav_api",
    "source_name": "RxNorm/RxNav API",
    "endpoint": "https://rxnav.nlm.nih.gov/REST",
    "module": "RealWorldSafety",
    "description": "U.S. National Library of Medicine RxNorm drug terminology source used for drug-name normalization and RXCUI reference lookup.",
    "update_cadence": "NLM RxNorm releases and RxNav API updates",
}

DAILYMED_SPL_API = {
    "source_id": "dailymed_spl_api",
    "source_name": "DailyMed SPL API",
    "endpoint": "https://dailymed.nlm.nih.gov/dailymed/services/v2/spls.json",
    "module": "RealWorldSafety",
    "description": "U.S. National Library of Medicine DailyMed Structured Product Label source for official drug label references.",
    "update_cadence": "DailyMed SPL label updates",
}

OPENFDA_DRUG_LABEL = {
    "source_id": "openfda_drug_label",
    "source_name": "openFDA Drug Label API",
    "endpoint": "https://api.fda.gov/drug/label.json",
    "module": "RealWorldSafety",
    "description": "Official openFDA drug label records for active ingredients, warnings, dosage, and usage sections.",
    "update_cadence": "Source-dependent FDA drug label updates",
}

OPENFDA_NDC_DIRECTORY = {
    "source_id": "openfda_ndc_directory",
    "source_name": "openFDA NDC Directory API",
    "endpoint": "https://api.fda.gov/drug/ndc.json",
    "module": "RealWorldSafety",
    "description": "Official openFDA National Drug Code directory records for drug identity, labeler, active ingredients, dosage form, route, product NDC, and packaging reference. This is a reference source, not a recall source.",
    "update_cadence": "Source-dependent FDA NDC directory updates",
}

OPENFDA_DEVICE_ENFORCEMENT = {
    "source_id": "openfda_device_enforcement",
    "source_name": "openFDA Device Enforcement API",
    "endpoint": "https://api.fda.gov/device/enforcement.json",
    "module": "RealWorldSafety",
    "description": "FDA medical device recall enforcement records from openFDA.",
    "update_cadence": "Source-dependent FDA device enforcement updates",
}

OPENFDA_DEVICE_EVENT = {
    "source_id": "openfda_device_event",
    "source_name": "openFDA Device Event API",
    "endpoint": "https://api.fda.gov/device/event.json",
    "module": "RealWorldSafety",
    "description": "FDA medical device adverse-event reports from openFDA. These are signal reports, not recalls or proof of causation.",
    "update_cadence": "Source-dependent FDA device event updates",
}

OPENFDA_UDI_DIRECTORY = {
    "source_id": "openfda_udi_directory",
    "source_name": "openFDA UDI Directory API",
    "department": "HHS",
    "agency": "FDA",
    "module": "RealWorldSafety",
    "source_type": "structured_api",
    "endpoint": "https://api.fda.gov/device/udi.json",
    "description": "FDA Unique Device Identifier reference records for medical-device identity matching.",
    "update_frequency": "FDA published updates",
    "update_cadence": "FDA published updates",
    "reliability_tier": 1,
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
    "integration_mode": "curated_official_snapshot",
    "reference_endpoint": "https://www.fsis.usda.gov/fsis/api/recall/v/1",
    "local_snapshot": "data/safety_sources/food/usda_fsis_curated_records.json",
    "update_cadence": "Curated official-source snapshot for prototype demo; live FSIS refresh not automated yet",
}

FOODRADAR_MULTI_SOURCE = {
    "source_id": "foodradar_multi_source",
    "source_name": "FoodRadar Multi-Source Recall Search",
    "endpoint": "https://api.fda.gov/food/enforcement.json + https://www.fsis.usda.gov/fsis/api/recall/v/1",
    "module": "FoodRadar",
    "description": "Aggregate FoodRadar workflow combining openFDA Food Enforcement and USDA FSIS recall/public-health-alert records.",
    "integration_mode": "mixed_live_and_curated_sources",
    "update_cadence": "Source-dependent openFDA updates plus curated USDA FSIS official-source snapshot; live FSIS refresh not automated yet",
}

FDA_RECALLS_MARKET_WITHDRAWALS_SAFETY_ALERTS = {
    "source_id": "fda_recalls_market_withdrawals_safety_alerts",
    "source_name": "FDA Recalls, Market Withdrawals & Safety Alerts",
    "endpoint": "https://www.fda.gov/safety/recalls-market-withdrawals-safety-alerts",
    "module": "RealWorldSafety",
    "description": (
        "Public FDA recall, market withdrawal, and safety alert notices visible on FDA.gov, "
        "including notices that may not appear in openFDA enforcement APIs."
    ),
    "integration_mode": "live_public_page",
    "update_cadence": "FDA public notice page updates as recalls, market withdrawals, and safety alerts are posted",
}

CPSC_RECALLS_API = {
    "source_id": "cpsc_recalls_api",
    "source_name": "CPSC Recalls API",
    "endpoint": "https://www.saferproducts.gov/RestWebServices/Recall",
    "module": "RealWorldSafety",
    "description": (
        "Consumer Product Safety Commission recall records for home goods, electronics, "
        "batteries, scooters, toys, baby products, furniture, appliances, and other consumer products."
    ),
    "integration_mode": "curated_official_snapshot",
    "reference_endpoint": "https://www.saferproducts.gov/RestWebServices/Recall",
    "local_snapshot": "data/safety_sources/cpsc/cpsc_daily_products_curated_records.json",
    "update_cadence": "Curated official-source snapshot for prototype demo; live CPSC refresh not automated yet",
}

NHTSA_VPIC_VIN_DECODER_API = {
    "source_id": "nhtsa_vpic_vin_decoder_api",
    "source_name": "NHTSA vPIC VIN Decoder API",
    "endpoint": "https://vpic.nhtsa.dot.gov/api/",
    "module": "RealWorldSafety",
    "description": "NHTSA vPIC vehicle decoder used to turn VIN input into make, model, and model year before recall lookup.",
    "integration_mode": "live_public_api",
    "update_cadence": "NHTSA vPIC public API updates as vehicle product information is refreshed",
}

NHTSA_RECALLS_API_DATASETS = {
    "source_id": "nhtsa_recalls_api_datasets",
    "source_name": "NHTSA Recalls API / datasets",
    "endpoint": "https://api.nhtsa.gov/recalls/recallsByVehicle",
    "module": "RealWorldSafety",
    "description": "NHTSA vehicle recall records by make, model, and model year for vehicle safety checks.",
    "integration_mode": "live_public_api",
    "update_cadence": "NHTSA recall data updates as campaigns and safety notices are published",
}

REGIONAL_HEALTH_PULSE_DEMO = {
    "source_id": "regional_health_pulse_demo",
    "source_name": "Regional Health Pulse MVP scaffold",
    "endpoint": "https://healthdata.gov/",
    "module": "RegionalHealthPulse",
    "description": "Demo public-health signal scaffold for Regional Health Pulse backend v1. This is not live CDC/HHS surveillance yet.",
    "integration_mode": "prototype_scaffold",
    "update_cadence": "MVP scaffold; live public source cadence not configured yet",
}

REGISTERED_SOURCES = [
    OPENFDA_DRUG_ENFORCEMENT,
    OPENFDA_DRUG_EVENT,
    RXNORM_RXNAV_API,
    DAILYMED_SPL_API,
    OPENFDA_DRUG_LABEL,
    OPENFDA_NDC_DIRECTORY,
    OPENFDA_DEVICE_ENFORCEMENT,
    OPENFDA_DEVICE_EVENT,
    OPENFDA_UDI_DIRECTORY,
    OPENFDA_COSMETIC_EVENT,
    OPENFDA_FOOD_ENFORCEMENT,
    USDA_FSIS_RECALL,
    FOODRADAR_MULTI_SOURCE,
    FDA_RECALLS_MARKET_WITHDRAWALS_SAFETY_ALERTS,
    CPSC_RECALLS_API,
    NHTSA_VPIC_VIN_DECODER_API,
    NHTSA_RECALLS_API_DATASETS,
    REGIONAL_HEALTH_PULSE_DEMO,
]
