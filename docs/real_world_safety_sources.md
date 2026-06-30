# Real-World Safety Sources

This document summarizes the official and public-data sources used by the Dav AI Real-World Safety search workflow.

## Current Source Coverage

| Source | Type | Coverage | Example Queries | Runtime Mode |
|---|---|---|---|---|
| CPSC Recalls API | Government consumer-product recalls | Air fryers, scooters, power banks, appliances, child products | air fryer, power bank, Segway | Local curated official snapshot |
| FDA Recalls, Market Withdrawals & Safety Alerts | FDA public notice page | Public FDA recall notices and safety alerts | pepperoni rolls, allergy alert | Public notice page |
| openFDA Food Enforcement API | FDA enforcement records | Food recalls, undeclared allergens, listeria, salad, produce | undeclared milk, listeria, ice cream | Local curated official snapshot |
| openFDA Drug Enforcement API | FDA drug enforcement records | Drug recalls and enforcement actions | metformin, eye drops, hand sanitizer | Local curated official snapshot |
| RxNorm / RxNav API | NLM drug terminology | Drug-name normalization and RXCUI lookup | Tylenol, Advil, metformin | Local curated official snapshot |
| DailyMed SPL API | NLM official drug labels | Official drug label references, SPL set IDs, published labels | acetaminophen, ibuprofen, metformin | Local curated official snapshot |
| openFDA Device Enforcement API | FDA medical-device enforcement records | Glucose meters, insulin pumps, CPAP, ventilators, device software/battery recalls | glucose meter, insulin pump, CPAP | Local curated official snapshot |
| openFDA Device Event API | FDA medical-device adverse-event reports | Device adverse-event signal reports, not recalls or proof of causation | insulin pump, glucose meter, ventilator | Local curated official snapshot |
| NHTSA VPIC VIN Decoder API | Government vehicle reference API | VIN decoding and vehicle metadata | VIN queries | Structured API / fixture-backed tests |
| NHTSA Recalls API / datasets | Government vehicle recalls | Vehicle recalls by make/model/year | Toyota Camry, Honda Civic | Structured API / fixture-backed tests |

## Why Curated Official Snapshots?

Some official public APIs are live and rate-limited, unstable, or not ideal for deterministic tests. Dav AI uses curated official snapshots for selected sources so tests are deterministic, demos work offline, source provenance remains clear, and records still come from official government or NLM/FDA/CPSC data.

The application labels these as local curated official snapshot.

## Important Distinction

Not every source is a recall source.

- openFDA Food, Drug, and Device Enforcement sources provide recall or enforcement records.
- openFDA Device Event provides adverse-event signal reports, not recalls or proof of causation.
- RxNorm provides drug terminology and name normalization.
- DailyMed provides official drug label references.
- NHTSA provides vehicle identity and recall data.
- CPSC provides consumer-product recall records.

## Example Unified Search Behavior

| Query | Expected Source Behavior |
|---|---|
| air fryer | CPSC consumer-product recalls |
| undeclared milk | openFDA Food Enforcement + FDA public notice results |
| metformin | openFDA Drug Enforcement + RxNorm + DailyMed |
| Tylenol | RxNorm drug concept + DailyMed label references |
| glucose meter | openFDA Device Enforcement + openFDA Device Event |
| insulin pump | openFDA Device Enforcement + openFDA Device Event |
| ventilator | openFDA Device Enforcement + openFDA Device Event |
| CPAP | openFDA Device Enforcement |

## Refresh Tooling

The current refresh script is:

python3 scripts/refresh_real_world_safety_snapshots.py

It refreshes curated records for:

- openFDA Food Enforcement
- openFDA Drug Enforcement
- openFDA Device Enforcement

Future refresh tooling should also include:

- openFDA Device Event curated records
- RxNorm / RxNav curated records
- DailyMed SPL curated records
- CPSC curated records

## Sources Intentionally Not Included Yet

### USDA FSIS

USDA FSIS is not currently included in Real-World Safety because the earlier fetch path was not reliable. It should only be added after a real, reproducible, official-data fetch works.

No synthetic FSIS data should be used.

## Testing

The unified Real-World Safety route has source coverage tests for:

- openFDA Food Enforcement
- openFDA Drug Enforcement
- RxNorm / RxNav
- DailyMed SPL
- openFDA Device Enforcement
- openFDA Device Event
- NHTSA vehicle recall behavior
- CPSC consumer-product recall behavior

Current backend checkpoint:

367 backend tests passing
