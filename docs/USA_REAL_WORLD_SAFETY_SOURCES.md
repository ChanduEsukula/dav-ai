# Dav AI U.S. Real-World Safety Sources

This reference is scoped strictly to United States public sources. No non-U.S. sources are included for this product direction.

Dav AI should help users search or track products they eat, take, apply, drive, plug in, or use at home. The core job is to check selected U.S. public sources for recalls, warnings, adverse-event signals, official labels, product identity, model risks, VIN/NDC/UDI matching, and source coverage.

## Required Category Coverage

| Category | Primary source families |
| --- | --- |
| Food and beverages | FDA public recalls and food alerts, openFDA food enforcement, CAERS/openFDA food event, USDA FSIS recalls, FoodData Central, FoodSafety.gov, Recalls.gov, retailer notices |
| Medicines, OTC drugs, prescription drugs, and supplements | FDA public recalls, openFDA drug enforcement, openFDA NDC, FDA NDC Directory, openFDA labels, FAERS/openFDA drug event, DailyMed, RxNorm/RxNav |
| Cosmetics and personal care products | openFDA cosmetic adverse events, FDA public recalls, CPSC recalls for personal-care appliances, retailer notices |
| Cars, VINs, tires, car seats, and vehicle equipment | NHTSA recalls datasets/API, NHTSA vPIC VIN decoder, NHTSA recall portal, manufacturer recall portals, CPSC for non-road consumer mobility products |
| Appliances such as dryers, air fryers, heaters, pressure cookers, refrigerators, washing machines | CPSC Recalls API, CPSC detail pages, retailer notices, manufacturer recall pages |
| Electronics, batteries, chargers, scooters, e-bikes, power banks | CPSC Recalls API, CPSC detail pages, retailer notices, electronics and mobility manufacturer pages |
| Baby/kids products, toys, furniture, mattresses, home goods | CPSC Recalls API, CPSC detail pages, retailer notices, Graco, Fisher-Price/Mattel, IKEA |
| Medical devices | openFDA device recall, enforcement, event/MAUDE, and UDI APIs, AccessGUDID, FDA public recalls |
| Household chemicals and cleaning products | CPSC recalls, EPA CompTox, EPA Safer Choice product list, retailer notices |
| U.S. retailer and manufacturer recall sources | Costco, Sam's Club, Walmart, Target, Amazon, Best Buy, Home Depot, Lowe's, Kroger, Trader Joe's, Whole Foods, Samsung, LG, Whirlpool, Ninja, Instant Brands, Anker, Segway/Ninebot, Toyota, Honda, Ford, GM, Tesla, Graco, Fisher-Price, IKEA |

## Why Dav AI Currently Misses Real-World Recalls

Structured APIs like openFDA are useful, but they do not represent every public safety notice at the moment a user needs it. FDA enforcement datasets can lag public notices, may only include classified recalls, and may not track the lifecycle of a recall after publication. Retailers and manufacturers often publish product notices before, after, or separately from structured federal datasets. Some notices are PDFs, CMS pages, product-specific forms, VIN lookups, model-number lookup tools, or JavaScript-heavy pages with no official API.

Dav AI also needs source coverage awareness. A "no match" result should never imply the product is safe. It should mean Dav AI checked a known set of sources, attempted matching with available identifiers, and found no matching public record in those checked sources.

## Version 1 Implementation Status

Implemented first in V1:

- CPSC Recalls API for high-impact consumer products such as appliances, electronics, batteries, scooters, toys, furniture, baby products, mattresses, and home goods.
- NHTSA vPIC VIN Decoder API plus NHTSA recalls by vehicle for VIN and year/make/model checks.
- FDA Recalls, Market Withdrawals & Safety Alerts public page to cover public FDA notices that may not be returned by openFDA enforcement APIs, including cases like Fry Pie Factory Pepperoni Rolls.

The V1 backend adds normalized source adapters, a RealWorldSafety search workflow, per-source audit/source-pull metadata, partial failure reporting, and source coverage fields such as sources checked, sources failed, records per source, structured API matches, public notice matches, total matches, and no-match explanation.

When no match is found, Dav AI must say: "No matching public record was found in the checked U.S. sources. This does not certify that the product is safe."

Still skipped for V1: retailer scraping, manufacturer scraping, barcode scanning, Amazon order import, browser extension, mobile app, AI medical advice, drug interaction checking, ingredient danger scoring, and international sources.

## Government, Public API, Dataset, and Cross-Agency Sources

| Source name | Agency/company | Category covered | Type | Official URL | What data it provides | How Dav AI should use it | Limitations/gaps | Free/open status | Priority |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| openFDA Food Enforcement API | FDA/openFDA | Food and beverages | API | https://open.fda.gov/apis/food/enforcement/ | FDA food recall enforcement reports from the Recall Enterprise System | Pull classified FDA food recall records, match by brand, product description, firm, reason, distribution, and dates | May lag public alerts; not every public notice has a press release; recall status may not be updated after classification | Free public API; rate limits apply | Must-have |
| FDA Recalls, Market Withdrawals & Safety Alerts | FDA | Food, drugs, supplements, cosmetics, medical devices | Public notice page/search portal/downloadable file | https://www.fda.gov/safety/recalls-market-withdrawals-safety-alerts | Recent FDA-regulated product recalls, withdrawals, and safety alerts with searchable product type filters and XLSX download | Use as a public-notice adapter for current high-signal FDA recalls across product types | Only recent years on page before archive; not all recalls have press releases | Free public page and download | Must-have |
| FDA Food Alerts, Advisories & Safety Information | FDA | Food, beverages, dietary supplements, infant formula | Public notice page | https://www.fda.gov/food/recalls-outbreaks-emergencies/alerts-advisories-safety-information | FDA consumer advisories, safety alerts, public health alerts, and food safety notices | Add a scraper/parser for current food alerts that may not be in enforcement data yet | Mixed notice formats; some shellfish/import notices may involve non-U.S. origin but U.S. consumer alerts | Free public page | Useful |
| openFDA Drug Enforcement API | FDA/openFDA | Medicines, OTC drugs, prescription drugs, supplements | API | https://open.fda.gov/apis/drug/enforcement/ | FDA drug recall enforcement reports from RES | Match user medicines and supplements by brand, generic name, firm, NDC when present, lot, and recall reason | Classified enforcement data can lag public notices; not a medical advice source | Free public API; rate limits apply | Must-have |
| openFDA Drug NDC API | FDA/openFDA | Medicines, OTC drugs, prescription drugs | API | https://open.fda.gov/apis/drug/ndc/ | NDC Directory data in JSON including listed drug products, labelers, marketing status, and packaging | Normalize NDCs from labels, medication lists, or user input and connect products to labels/recalls/events | NDC listing does not mean FDA approval or safety; labeler-submitted content may be incomplete | Free public API; rate limits apply | Must-have |
| FDA NDC Directory | FDA | Medicines, OTC drugs, prescription drugs | Search portal/dataset/downloadable file | https://www.fda.gov/drugs/drug-approvals-and-databases/national-drug-code-directory | Official NDC search and downloadable directory context | Use as canonical NDC reference and fallback when openFDA mappings are incomplete | NDC presence is not approval; excludes some products and package cases | Free public search/download | Must-have |
| openFDA Drug Label API | FDA/openFDA | Medicines, OTC drugs, prescription drugs | API | https://open.fda.gov/apis/drug/label/ | Structured Product Labeling data for drug labels | Retrieve warnings, indications, dosage, boxed warnings, active ingredients, and contraindication text for product reports | Labels are not recall signals and do not replace clinician guidance | Free public API; rate limits apply | Useful |
| openFDA Drug Adverse Event / FAERS API | FDA/openFDA | Medicines, OTC drugs, prescription drugs, supplements | API | https://open.fda.gov/apis/drug/event/ | FAERS adverse event reports submitted to FDA | Show aggregate signal context and source caveats for matched drugs, never causal claims | Voluntary reports, duplicates, confounding, and reporting bias; not incidence data | Free public API; rate limits apply | Useful |
| openFDA Cosmetic Adverse Event API | FDA/openFDA | Cosmetics and personal care products | API | https://open.fda.gov/apis/cosmetic/event/ | Cosmetic adverse event reports | Provide signal context for personal care and cosmetic products or brands | Adverse reports are not recalls and do not prove causation; product identity may be inconsistent | Free public API; rate limits apply | Must-have |
| CAERS / openFDA Food Event API | FDA/openFDA | Food, beverages, supplements, cosmetics | API | https://open.fda.gov/apis/food/event/ | CFSAN Adverse Event Reporting System data for foods, dietary supplements, and cosmetics | Add adverse-event context for supplements, foods, and cosmetics after recall matching is working | Voluntary reports, duplicates, weak product normalization, no causality | Free public API; rate limits apply | Useful |
| openFDA Device Recall API | FDA/openFDA | Medical devices | API | https://open.fda.gov/apis/device/recall/ | Medical device recall records | Match devices by product code, device name, manufacturer, and recall number | Device identity can be hard without UDI; data may lag public notices | Free public API; rate limits apply | Useful |
| openFDA Device Enforcement API | FDA/openFDA | Medical devices | API | https://open.fda.gov/apis/device/enforcement/ | Device enforcement recall reports | Add classified enforcement records to device safety checks | Not every device notice is easy to match from consumer text | Free public API; rate limits apply | Useful |
| openFDA Device Event / MAUDE API | FDA/openFDA | Medical devices | API | https://open.fda.gov/apis/device/event/ | MAUDE medical device adverse event reports | Provide adverse-event signal context for matched device types, manufacturers, and model names | Voluntary and mandatory reports are not incidence or causality data; duplicate/noisy records | Free public API; rate limits apply | Useful |
| openFDA Device UDI API | FDA/openFDA | Medical devices | API | https://open.fda.gov/apis/device/udi/ | Device UDI and GUDID-derived device identification data | Normalize UDI-DI, device identifier, manufacturer, brand, version/model, and device descriptions | UDI must be captured accurately; not every older device has complete UDI data | Free public API; rate limits apply | Useful |
| USDA FSIS Recall API | USDA FSIS | Meat, poultry, egg products | API | https://www.fsis.usda.gov/fsis/api/recall/v/1 | Machine-readable FSIS recall/public-health-alert records | Pull meat, poultry, and egg product recalls into the food adapter and match by establishment number, brand, product, and dates | Endpoint should be manually verified before implementation; FSIS jurisdiction excludes many FDA-regulated foods | Public endpoint appears free; verify terms | Must-have |
| USDA FSIS Recalls & Public Health Alerts | USDA FSIS | Meat, poultry, egg products | Public notice page | https://www.fsis.usda.gov/recalls | FSIS recall releases and public health alerts | Use as public notice fallback and source of narrative details, labels, establishment numbers, and photos | HTML/PDF details vary; not a universal food recall source | Free public page | Must-have |
| USDA FoodData Central API | USDA ARS | Food and beverages | API/dataset | https://fdc.nal.usda.gov/api-guide.html | Food identity, branded foods, ingredients, nutrients, and FDC identifiers | Use for product identity enrichment and branded food matching, not safety scoring | Requires API key; nutrition database is not a recall database; branded coverage varies | Free with data.gov API key; public-domain data | Useful |
| CPSC Recalls API | Consumer Product Safety Commission | Appliances, electronics, batteries, toys, furniture, mattresses, home goods, personal care appliances, household products | API | https://www.cpsc.gov/Recalls/CPSC-Recalls-Application-Program-Interface-API-Information | Machine-readable CPSC recalls in XML/JSON | First V1 recall adapter for consumer products; match by product name, brand, model, hazard, remedy, dates, and manufacturer | Categories can be broad; model/serial fields may require detail-page parsing | Free public API | Must-have |
| CPSC recall detail pages | Consumer Product Safety Commission | Appliances, electronics, kids products, furniture, home goods, household chemicals | Public notice page | https://www.cpsc.gov/Recalls | Rich recall pages with hazard, remedy, incidents, model numbers, images, sellers, and manufacturer contact | Fetch detail pages for evidence snippets, model numbers, affected units, and report PDFs/screenshots | HTML structure can change; some details are in narrative text | Free public page | Must-have |
| NHTSA Recalls API / datasets | NHTSA | Cars, VINs, tires, car seats, vehicle equipment | API/dataset/downloadable file | https://www.nhtsa.gov/nhtsa-datasets-and-apis | Vehicle, tire, child seat, and equipment recall datasets plus API examples | Build vehicle recall adapter by year/make/model, campaign, component, and VIN-derived metadata | API by vehicle needs year/make/model; VIN-specific open recall status may require portal/manufacturer lookup | Free public API/datasets | Must-have |
| NHTSA vPIC VIN Decoder API | NHTSA | VINs, vehicle identity | API | https://vpic.nhtsa.dot.gov/api/ | VIN decoding, make, model, model year, plant, body class, and vehicle attributes | Decode VIN to normalize vehicle identity before recall matching | VIN decode is identity, not recall status; malformed VINs need validation | Free public API | Must-have |
| NHTSA recall search portal | NHTSA | Cars, tires, car seats, vehicle equipment | Search portal | https://www.nhtsa.gov/recalls | Consumer recall search by VIN, vehicle, car seat, tire, and equipment | Link users to official VIN recall checks and use as verification fallback | Portal may be interactive; scraping VIN results can be restricted | Free public portal | Must-have |
| DailyMed API | NIH/NLM | Medicines, OTC drugs, prescription drugs | API/downloadable files | https://dailymed.nlm.nih.gov/dailymed/app-support-web-services.cfm | Current SPL drug label data, NDCs, RxCUIs, packaging, media, and label PDFs | Retrieve official label sections and PDFs for medication reports and NDC/RxCUI matching | Label data is not recall/adverse-event data; only as current as submitted labels | Free public API | Must-have |
| RxNorm / RxNav API | NIH/NLM | Medicines, OTC drugs, prescription drugs | API | https://lhncbc.nlm.nih.gov/RxNav/APIs/ | RxNorm concepts, RxCUIs, synonym/ingredient/brand relationships, drug classes | Normalize drug names, ingredients, brands, and aliases before matching FDA/NLM sources | Does not cover all supplements or non-drug products; terminology matching still needs caution | Free public API | Must-have |
| AccessGUDID API | NIH/NLM | Medical devices | API | https://accessgudid.nlm.nih.gov/resources/developers | GUDID device records by UDI/device identifier | Match UDI-DI to device brand, version/model, company, and device identifiers | Developer URL and current API shape should be manually verified before implementation | Free public API | Useful |
| EPA CompTox Chemicals Dashboard APIs | EPA | Household chemicals, cleaning products, ingredients | API/dataset | https://api-ccte.epa.gov/docs/ | Chemical identity, synonyms, CASRN/DTXSID identifiers, properties, and exposure/use context | Normalize chemical ingredient names and identifiers for household chemical reports | API documentation URL should be manually verified; not a recall source and not consumer risk scoring by itself | Free public API/dataset; verify terms | Future Expansion |
| EPA Safer Choice product list | EPA | Household chemicals and cleaning products | Public notice page/downloadable file | https://www.epa.gov/saferchoice/products | Searchable and downloadable list of Safer Choice-certified products | Enrich household-cleaner reports with safer-choice certification status where relevant | Certification is not a recall/safety guarantee; product list can have multiple entries per product | Free public page/download | Future Expansion |
| Recalls.gov | Cross-agency federal portal | Cross-category recalls | Public notice page/search portal | https://www.recalls.gov/ | Portal linking U.S. government recall sources from CPSC, NHTSA, FDA, USDA, EPA, and others | Use as a user-facing fallback and coverage explainer, not the primary data pipeline | Aggregator/link portal, not a complete structured API | Free public portal | Useful |
| FoodSafety.gov | HHS/USDA/FDA partner site | Food and beverages | Public notice page/widget | https://www.foodsafety.gov/recalls-and-outbreaks | Real-time recall/public-health-alert widget and consumer guidance from FDA/USDA | Use as food recall coverage explanation and fallback link in reports | Widget/source details may be embedded; not a canonical API for all food recalls | Free public page | Useful |

## Retailer and Manufacturer Recall Sources

These sources are valuable for source coverage and user trust, but most should wait until after the structured government adapters are working. For V1, link to them manually or treat them as "checked only if adapter exists."

| Source name | Agency/company | Category covered | Type | Official URL | What data it provides | How Dav AI should use it | Limitations/gaps | Free/open status | Priority |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Costco recalls | Costco | Food, supplements, appliances, electronics, home goods | Public notice page | https://www.costco.com/f/-/recalls | Costco recall and product notice list, often with item numbers and PDFs | Match Costco item numbers, brand names, and retail-specific notices for user-owned products | Retailer-specific; page structure may change; not all sold products are covered | Free public page; scraping terms should be reviewed | Future Expansion |
| Sam's Club recalls | Sam's Club | Food, supplements, appliances, electronics, home goods | Public notice page | https://help.samsclub.com/app/answers/detail/a_id/151/~/product-recalls | Sam's Club recall notices and help-center guidance | Link users to retailer notices and match Member's Mark/private-label products | Official URL should be manually verified; help-center pages can change | Free public page; scraping terms should be reviewed | Future Expansion |
| Walmart recalls | Walmart | Food, OTC, supplements, appliances, electronics, home goods | Public notice page | https://corporate.walmart.com/recalls | Walmart product recall notices across retail categories | Match Walmart/private-label products, UPCs, and retail notices | Retailer-specific; may duplicate FDA/CPSC notices | Free public page; scraping terms should be reviewed | Future Expansion |
| Target recalls | Target | Food, kids products, home goods, electronics, personal care | Public notice page | https://help.target.com/help/subcategoryarticle?childcat=Product+recalls&parentcat=Product+Safety | Target product recall help and notice pages | Match Target/private-label products and link users to retailer return/remedy instructions | Official URL should be manually verified; dynamic help URLs may change | Free public page; scraping terms should be reviewed | Future Expansion |
| Amazon product safety / recalls | Amazon | Cross-category marketplace products | Search portal/account notice page | https://www.amazon.com/your-product-safety-alerts | Amazon product safety alerts and recall notices, often account/order dependent | Use as a future user-directed link for order-specific recall awareness, not automated import in V1 | Login/account context; scraping/order import should be skipped in V1 | Free account feature; automation terms must be reviewed | Future Expansion |
| Best Buy recalls | Best Buy | Electronics, appliances, batteries, chargers | Public notice page | https://www.bestbuy.com/site/help-topics/product-recalls/pcmcat204400050004.c?id=pcmcat204400050004 | Best Buy recall notices for products it sells | Match electronics/appliance recalls and provide retailer remedy links | Official URL should be manually verified; page may be JS-heavy | Free public page; scraping terms should be reviewed | Future Expansion |
| Home Depot recalls | Home Depot | Appliances, heaters, tools, batteries, home goods | Public notice page | https://www.homedepot.com/c/SF_MS_The_Home_Depot_Recalls | Home Depot product recall notices | Match home improvement, appliance, and tool products by brand/model | Official URL should be manually verified; page may be hard to scrape | Free public page; scraping terms should be reviewed | Future Expansion |
| Lowe's recalls | Lowe's | Appliances, heaters, tools, batteries, home goods | Public notice page | https://www.lowes.com/l/help/recalls-and-product-safety | Lowe's product recall and safety notices | Match Lowe's retail products and provide remedy/return links | Retailer-specific; page can be dense and JS-heavy | Free public page; scraping terms should be reviewed | Future Expansion |
| Kroger recalls | Kroger | Food, OTC, household products | Public notice page | https://www.kroger.com/i/product-recalls | Kroger recall notices for grocery and private-label products | Match Kroger/private-label foods by UPC, brand, and product name | Official URL should be manually verified; regional banners may publish separately | Free public page; scraping terms should be reviewed | Future Expansion |
| Trader Joe's recalls | Trader Joe's | Food and beverages | Public notice page | https://www.traderjoes.com/home/announcements?category=recalls | Trader Joe's recall announcements | Match Trader Joe's private-label food products and alert users | Dynamic page; product identifiers may be narrative text only | Free public page; scraping terms should be reviewed | Future Expansion |
| Whole Foods recalls | Whole Foods Market | Food, supplements, personal care | Public notice page | https://www.wholefoodsmarket.com/legal/product-recalls | Whole Foods product recall notices | Match Whole Foods/private-label products and provide retailer-specific remedy links | Retailer-specific; may duplicate FDA notices | Free public page; scraping terms should be reviewed | Future Expansion |
| Samsung recalls | Samsung | Appliances, electronics, batteries, chargers | Public notice page/search portal | https://www.samsung.com/us/support/recalls/ | Samsung product recall and support notices | Match Samsung model numbers for ranges, appliances, phones, batteries, and electronics | Official URL should be manually verified; product-specific support pages may vary | Free public page; scraping terms should be reviewed | Future Expansion |
| LG recalls | LG Electronics | Appliances, electronics, batteries | Public notice page/search portal | https://www.lg.com/us/support/announcements?category=product-recalls | LG product recall/support announcements | Match LG model numbers for ranges, refrigerators, washers, dryers, and electronics | Official URL should be manually verified; category query may change | Free public page; scraping terms should be reviewed | Future Expansion |
| Whirlpool recalls | Whirlpool | Appliances such as dryers, refrigerators, washers, ranges | Public notice page/search portal | https://producthelp.whirlpool.com/Product_Recall | Whirlpool recall and product help notices | Match Whirlpool family brand/model numbers for appliances | Official URL should be manually verified; brand-family pages may be split | Free public page; scraping terms should be reviewed | Future Expansion |
| Ninja recalls | SharkNinja/Ninja | Air fryers, pressure cookers, kitchen appliances | Public notice page/search portal | https://support.ninjakitchen.com/hc/en-us/categories/4409281115666-Product-Recall | Ninja product recall support notices | Match Ninja model numbers for pressure cookers, air fryers, blenders, and kitchen appliances | Official URL should be manually verified; support-center category may change | Free public page; scraping terms should be reviewed | Future Expansion |
| Instant Brands recalls | Instant Brands | Pressure cookers, air fryers, kitchen appliances | Public notice page | https://instantpot.com/pages/product-recalls | Instant Brands/Instant Pot recall notices | Match Instant Pot and related model numbers | Official URL should be manually verified; ownership/site paths can change | Free public page; scraping terms should be reviewed | Future Expansion |
| Anker recalls | Anker | Power banks, chargers, batteries, electronics | Public notice page/search portal | https://www.anker.com/support/product-recalls | Anker battery, charger, and electronics recall notices | Match power-bank model numbers and battery product names | Official URL should be manually verified; recalls may be product-specific microsites | Free public page; scraping terms should be reviewed | Future Expansion |
| Segway/Ninebot recalls | Segway/Ninebot | Scooters, e-bikes, batteries, mobility products | Public notice page/search portal | https://www.segway.com/support/product-recall/ | Segway/Ninebot product recall notices | Match scooter/e-bike model numbers and serial numbers when available | Official URL should be manually verified; product-specific pages may change | Free public page; scraping terms should be reviewed | Future Expansion |
| Toyota recalls | Toyota | Cars, VINs, vehicle equipment | Search portal | https://www.toyota.com/recall/ | Toyota/Lexus/Scion recall and service campaign lookup by VIN or plate | Use as manufacturer verification link after NHTSA/vPIC identity matching | Interactive lookup; should not be scraped without terms review | Free public portal | Future Expansion |
| Honda recalls | Honda | Cars, VINs, vehicle equipment | Search portal | https://owners.honda.com/service-maintenance/recalls | Honda recall lookup, redirected to Honda MyGarage recall search | Use as manufacturer verification link for Honda VINs | Dynamic portal; VIN lookup automation may be restricted | Free public portal | Future Expansion |
| Ford recalls | Ford | Cars, VINs, vehicle equipment | Search portal | https://www.ford.com/support/recalls/ | Ford recall lookup and recall support pages | Use as manufacturer verification link for Ford/Lincoln VINs | Dynamic portal; VIN lookup automation may be restricted | Free public portal | Future Expansion |
| GM recalls | General Motors | Cars, VINs, vehicle equipment | Search portal | https://experience.gm.com/ownercenter/recalls | GM recall lookup for Chevrolet, Buick, GMC, Cadillac | Use as manufacturer verification link for GM VINs | Dynamic page should be manually verified before implementation | Free public portal | Future Expansion |
| Tesla recalls | Tesla | Cars, VINs, vehicle software/equipment | Public notice page/search portal | https://www.tesla.com/support/recall | Tesla recall support and recall lookup context | Link users to official Tesla recall status after NHTSA matching | Some recall remedies are software updates; VIN-specific state may require account/lookup | Free public page/portal | Future Expansion |
| Graco recalls | Graco | Car seats, strollers, baby products | Public notice page/search portal | https://recalls.gracobaby.com/ | Graco product recall registration and product-specific recall pages | Match model numbers for car seats, strollers, bases, and travel systems | Official URL should be manually verified; pages may be recall-specific forms | Free public page; scraping terms should be reviewed | Future Expansion |
| Fisher-Price recalls | Mattel/Fisher-Price | Baby/kids products, toys, sleepers, furniture | Public notice page | https://service.mattel.com/us/recall.aspx | Fisher-Price and Mattel recall/safety alert list | Match product numbers, names, and dates for baby/kids products | Page may include non-U.S. entries; Dav AI must filter to U.S.-relevant notices | Free public page | Future Expansion |
| IKEA recalls | IKEA U.S. | Furniture, mattresses, home goods, kids products | Public notice page | https://www.ikea.com/us/en/customer-service/product-support/recalls/ | IKEA U.S. product recall notices | Match IKEA product names, article numbers, furniture/home goods categories | Retailer/manufacturer-specific; may duplicate CPSC notices | Free public page; scraping terms should be reviewed | Future Expansion |

## Source Priority for Version 1

Recommended implementation order:

1. CPSC Recalls API
2. NHTSA vPIC + NHTSA recalls
3. FDA public recalls page
4. USDA FSIS Recall API
5. openFDA food/drug enforcement
6. DailyMed + RxNorm + openFDA NDC
7. openFDA Cosmetic Event
8. My Products dashboard
9. Source coverage + confidence scoring
10. PDF safety report

## What to Skip for Version 1

Skip:

- International sources
- Retailer scraping at scale
- Manufacturer scraping at scale
- Barcode scanning
- Amazon order import
- Browser extension
- Mobile app
- AI medical advice
- Drug interaction checker
- Ingredient danger scoring
- Predictive risk model
- Review mining

## Recommended Unified Database Schema

| Table | Purpose | Important fields |
| --- | --- | --- |
| safety_sources | Registry of U.S. sources Dav AI knows about | id, name, agency_or_company, category, source_type, official_url, priority, adapter_status, terms_notes |
| source_runs | Audit log for each fetch/import/check | id, source_id, run_started_at, run_finished_at, status, records_seen, records_added, error_message |
| safety_records | Canonical recall, warning, label, adverse-event, or product-safety record | id, source_id, source_record_id, record_type, title, summary, hazard, remedy, event_date, posted_date, raw_url, raw_payload_hash |
| product_entities | Normalized products, vehicles, drugs, devices, chemicals, and aliases | id, entity_type, brand, product_name, company_name, upc, ndc, vin_pattern, udi_di, model_number, serial_pattern, ingredients, aliases |
| user_products | User-tracked products in My Products | id, user_id, product_entity_id, user_label, identifiers_json, purchase_date, retailer, created_at |
| product_matches | Match results between user products/product entities and safety records | id, user_product_id, safety_record_id, match_type, confidence_score, matched_fields, explanation, needs_review |
| source_coverage_summary | What Dav AI checked for a product/report | id, user_product_id, report_id, checked_sources, unchecked_sources, source_gaps, generated_at |

## Search and Matching Strategy

Dav AI should match conservatively and show why a record matched. High-confidence matches require exact identifiers when available. Fuzzy matching should help discovery but should not silently imply certainty.

| Match field | Best use |
| --- | --- |
| Brand | First-pass narrowing across recalls and retailer notices |
| Product name | Primary text match for foods, appliances, toys, home goods, and cosmetics |
| Company name | Link labeler, manufacturer, distributor, and recalling firm aliases |
| UPC | Exact retail/product package matching when available |
| NDC | Exact drug package/product matching across openFDA, NDC Directory, and DailyMed |
| VIN | Decode with vPIC, then check NHTSA and manufacturer recall portals |
| UDI | Exact device identifier matching across openFDA device UDI and AccessGUDID |
| Model number | Critical for appliances, electronics, vehicles, kids products, and devices |
| Serial number | Use when notices specify affected serial ranges or production windows |
| Ingredient | Use for allergen, supplement, cosmetic, and household chemical discovery, with low confidence unless paired with product identity |
| Alias/fuzzy matching | Normalize punctuation, casing, brand aliases, abbreviations, and common misspellings, then require confidence scoring and user-visible evidence |

Recommended confidence bands:

- 0.90 to 1.00: exact identifier match such as VIN, NDC, UDI, UPC, model plus brand, or serial range.
- 0.70 to 0.89: strong brand/product/model text match with corroborating company or category.
- 0.40 to 0.69: possible alias/fuzzy match requiring user review.
- Below 0.40: do not alert as a match; use only as search discovery.

## One-Month Roadmap

| Week | Goal | Deliverables |
| --- | --- | --- |
| Week 1 | Build source adapters and source registry | Implement source registry, CPSC adapter, NHTSA vPIC adapter, NHTSA recalls adapter, FDA public recalls adapter, FSIS adapter stub, and source run logs |
| Week 2 | Build My Products dashboard | Add product tracking for food, drug, vehicle, appliance, device, and home-good examples with identifier fields for UPC, NDC, VIN, UDI, model, and serial |
| Week 3 | Build matching, deduplication, confidence scoring, and source coverage | Add matching engine, alias normalization, record deduplication, confidence explanations, and coverage summary output |
| Week 4 | Build PDF reports, demo data, tests, README diagrams, and recruiter-ready screenshots | Add PDF safety report, seeded demo products, adapter tests, matching tests, source coverage tests, architecture diagrams, and polished screenshots |

## Professional Disclaimer

“Dav AI does not certify that a product is safe. It checks selected U.S. public sources and reports matching recalls, warnings, labels, and safety signals. No matching result means no matching public record was found in checked sources, not that the product is safe.”

## Manual Verification Watchlist

Before implementation, manually verify official URLs and terms for: USDA FSIS Recall API endpoint, AccessGUDID developer API page, EPA CompTox API documentation endpoint, Sam's Club, Target, Amazon product safety alerts, Best Buy, Home Depot, Kroger, Samsung, LG, Whirlpool, Ninja, Instant Brands, Anker, Segway/Ninebot, GM, and Graco. These are included because they are useful U.S. sources, but their pages may be dynamic, product-specific, account-dependent, or hard to fetch reliably.
