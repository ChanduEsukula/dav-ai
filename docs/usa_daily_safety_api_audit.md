# USA Daily-Life Safety API Audit

Generated at: 2026-06-22T20:31:34.705889+00:00

Goal: decide which real-time USA APIs are useful for a daily recall/safety app covering cars, bikes, food, medicine, devices, household items, electronics, baby products, and products people buy.

## Summary Table

| Tier | Source | Category | Reachable | JSON | Records | Data Kind | Recommended Use |
|---|---|---|---:|---:|---:|---|---|
| A - Add/keep for USA daily recall MVP | openFDA Food Enforcement | Food / groceries | True | True | 2 | Recall / enforcement | Add / keep |
| A - Add/keep for USA daily recall MVP | openFDA Drug Enforcement | Medicine / OTC / prescriptions | True | True | 2 | Recall / enforcement | Add / keep |
| A - Add/keep for USA daily recall MVP | openFDA Device Enforcement | Medical devices | True | True | 2 | Recall / enforcement | Add / keep |
| B - Signal source, not recall | openFDA Device Event | Medical devices | True | True | 2 | Adverse-event signal, not recall | Keep with strong warning label |
| B - Useful context/reference | openFDA Drug Label | Medicine / labels | True | True | 2 | Official label / warnings / dosage | Add next |
| B - Signal source, not recall | openFDA Drug Event | Medicine / adverse events | True | True | 2 | Adverse-event signal, not recall | Add later with caution label |
| B - Signal source, not recall | openFDA Food Event / CAERS | Food / supplements / cosmetics signals | True | True | 2 | Adverse-event signal, not recall | Investigate |
| A - Add/keep for USA daily recall MVP | CPSC Recalls | Consumer products | True | True | 9862 | Consumer product recalls | Add / keep |
| A - Add/keep for USA daily recall MVP | NHTSA Recalls by Vehicle | Cars / motorcycles / vehicle equipment | True | True | 5 | Vehicle recalls | Add / keep |
| B - Useful context/reference | NHTSA Vehicle Products | Cars / bikes / equipment reference | True | True | 193 | Vehicle reference / metadata | Keep as reference source |
| D - Not reachable / needs fix | Recalls.gov | Multi-agency recall portal | False | False | 0 | RSS / recall aggregation | Investigate RSS parser |
| D - Not reachable / needs fix | EPA ECHO | Environment / facility compliance | False | False | 0 | Facility/environment compliance | Skip for consumer recall MVP |
| C - Not core recall MVP | ClinicalTrials.gov | Drug/device research context | True | True | 0 | Clinical research, not recall | Skip for recall MVP |

## Field Samples

### openFDA Food Enforcement

- Category: Food / groceries
- Owner: FDA / openFDA
- Tier: A - Add/keep for USA daily recall MVP
- Reachable: True
- HTTP status: 200
- Content-Type: application/json; charset=utf-8
- JSON parseable: True
- Record count in sample: 2
- Top-level keys: meta, results
- Sample record keys: address_1, address_2, center_classification_date, city, classification, code_info, country, distribution_pattern, event_id, initial_firm_notification, openfda, postal_code, product_description, product_quantity, product_type, reason_for_recall, recall_initiation_date, recall_number, recalling_firm, report_date, state, status, termination_date, voluntary_mandated
- Error: None

### openFDA Drug Enforcement

- Category: Medicine / OTC / prescriptions
- Owner: FDA / openFDA
- Tier: A - Add/keep for USA daily recall MVP
- Reachable: True
- HTTP status: 200
- Content-Type: application/json; charset=utf-8
- JSON parseable: True
- Record count in sample: 2
- Top-level keys: meta, results
- Sample record keys: address_1, address_2, center_classification_date, city, classification, code_info, country, distribution_pattern, event_id, initial_firm_notification, openfda, postal_code, product_description, product_quantity, product_type, reason_for_recall, recall_initiation_date, recall_number, recalling_firm, report_date, state, status, voluntary_mandated
- Error: None

### openFDA Device Enforcement

- Category: Medical devices
- Owner: FDA / openFDA
- Tier: A - Add/keep for USA daily recall MVP
- Reachable: True
- HTTP status: 200
- Content-Type: application/json; charset=utf-8
- JSON parseable: True
- Record count in sample: 2
- Top-level keys: meta, results
- Sample record keys: address_1, address_2, center_classification_date, city, classification, code_info, country, distribution_pattern, event_id, initial_firm_notification, openfda, postal_code, product_description, product_quantity, product_type, reason_for_recall, recall_initiation_date, recall_number, recalling_firm, report_date, state, status, termination_date, voluntary_mandated
- Error: None

### openFDA Device Event

- Category: Medical devices
- Owner: FDA / openFDA
- Tier: B - Signal source, not recall
- Reachable: True
- HTTP status: 200
- Content-Type: application/json; charset=utf-8
- JSON parseable: True
- Record count in sample: 2
- Top-level keys: meta, results
- Sample record keys: adverse_event_flag, date_added, date_changed, date_of_event, date_received, date_report, device, distributor_address_1, distributor_address_2, distributor_city, distributor_name, distributor_state, distributor_zip_code, distributor_zip_code_ext, event_key, event_location, event_type, exemption_number, health_professional, initial_report_to_fda, manufacturer_address_1, manufacturer_address_2, manufacturer_city, manufacturer_contact_address_1, manufacturer_contact_address_2, manufacturer_contact_area_code, manufacturer_contact_city, manufacturer_contact_country, manufacturer_contact_exchange, manufacturer_contact_extension, manufacturer_contact_f_name, manufacturer_contact_l_name, manufacturer_contact_pcity, manufacturer_contact_pcountry, manufacturer_contact_phone_number, manufacturer_contact_plocal, manufacturer_contact_postal_code, manufacturer_contact_state, manufacturer_contact_t_name, manufacturer_contact_zip_code, manufacturer_contact_zip_ext, manufacturer_country, manufacturer_g1_address_1, manufacturer_g1_address_2, manufacturer_g1_city, manufacturer_g1_country, manufacturer_g1_name, manufacturer_g1_postal_code, manufacturer_g1_state, manufacturer_g1_zip_code, manufacturer_g1_zip_code_ext, manufacturer_link_flag, manufacturer_name, manufacturer_postal_code, manufacturer_state, manufacturer_zip_code, manufacturer_zip_code_ext, mdr_report_key, mdr_text, mfr_report_type, noe_summarized, number_devices_in_event, number_patients_in_event, patient, pma_pmn_number, previous_use_code, product_problem_flag, remedial_action, removal_correction_number, report_number, report_source_code, report_to_fda, report_to_manufacturer, reporter_country_code, reporter_occupation_code, reporter_state_code, reprocessed_and_reused_flag, single_use_flag, source_type, summary_report_flag
- Error: None

### openFDA Drug Label

- Category: Medicine / labels
- Owner: FDA / openFDA
- Tier: B - Useful context/reference
- Reachable: True
- HTTP status: 200
- Content-Type: application/json; charset=utf-8
- JSON parseable: True
- Record count in sample: 2
- Top-level keys: meta, results
- Sample record keys: active_ingredient, ask_doctor, ask_doctor_or_pharmacist, do_not_use, dosage_and_administration, effective_time, id, inactive_ingredient, indications_and_usage, keep_out_of_reach_of_children, openfda, package_label_principal_display_panel, pregnancy_or_breast_feeding, purpose, questions, set_id, spl_product_data_elements, stop_use, storage_and_handling, version, warnings
- Error: None

### openFDA Drug Event

- Category: Medicine / adverse events
- Owner: FDA / openFDA
- Tier: B - Signal source, not recall
- Reachable: True
- HTTP status: 200
- Content-Type: application/json; charset=utf-8
- JSON parseable: True
- Record count in sample: 2
- Top-level keys: meta, results
- Sample record keys: companynumb, duplicate, fulfillexpeditecriteria, occurcountry, patient, primarysource, primarysourcecountry, receiptdate, receiptdateformat, receivedate, receivedateformat, receiver, reportduplicate, reporttype, safetyreportid, safetyreportversion, sender, serious, transmissiondate, transmissiondateformat
- Error: None

### openFDA Food Event / CAERS

- Category: Food / supplements / cosmetics signals
- Owner: FDA / openFDA
- Tier: B - Signal source, not recall
- Reachable: True
- HTTP status: 200
- Content-Type: application/json; charset=utf-8
- JSON parseable: True
- Record count in sample: 2
- Top-level keys: meta, results
- Sample record keys: consumer, date_created, date_started, outcomes, products, reactions, report_number
- Error: None

### CPSC Recalls

- Category: Consumer products
- Owner: Consumer Product Safety Commission
- Tier: A - Add/keep for USA daily recall MVP
- Reachable: True
- HTTP status: 200
- Content-Type: application/json; charset=utf-8
- JSON parseable: True
- Record count in sample: 9862
- Top-level keys: N/A
- Sample record keys: ConsumerContact, Description, Distributors, Hazards, Images, Importers, Inconjunctions, Injuries, LastPublishDate, ManufacturerCountries, Manufacturers, ProductUPCs, Products, RecallDate, RecallID, RecallNumber, Remedies, RemedyOptions, Retailers, SoldAtLabel, Title, URL
- Error: None

### NHTSA Recalls by Vehicle

- Category: Cars / motorcycles / vehicle equipment
- Owner: NHTSA
- Tier: A - Add/keep for USA daily recall MVP
- Reachable: True
- HTTP status: 200
- Content-Type: application/json;charset=UTF-8
- JSON parseable: True
- Record count in sample: 5
- Top-level keys: Count, Message, results
- Sample record keys: Component, Consequence, Make, Manufacturer, Model, ModelYear, NHTSACampaignNumber, Notes, Remedy, ReportReceivedDate, Summary, overTheAirUpdate, parkIt, parkOutSide
- Error: None

### NHTSA Vehicle Products

- Category: Cars / bikes / equipment reference
- Owner: NHTSA
- Tier: B - Useful context/reference
- Reachable: True
- HTTP status: 200
- Content-Type: application/json
- JSON parseable: True
- Record count in sample: 193
- Top-level keys: Count, Message, Results, SearchCriteria
- Sample record keys: MakeId, MakeName, VehicleTypeId, VehicleTypeName
- Error: None

### Recalls.gov

- Category: Multi-agency recall portal
- Owner: U.S. government recall portal
- Tier: D - Not reachable / needs fix
- Reachable: False
- HTTP status: None
- Content-Type: None
- JSON parseable: False
- Record count in sample: 0
- Top-level keys: N/A
- Sample record keys: N/A
- Error: HTTP Error 503: Service Unavailable

### EPA ECHO

- Category: Environment / facility compliance
- Owner: EPA
- Tier: D - Not reachable / needs fix
- Reachable: False
- HTTP status: None
- Content-Type: None
- JSON parseable: False
- Record count in sample: 0
- Top-level keys: N/A
- Sample record keys: N/A
- Error: HTTP Error 404: 404

### ClinicalTrials.gov

- Category: Drug/device research context
- Owner: NIH / NLM
- Tier: C - Not core recall MVP
- Reachable: True
- HTTP status: 200
- Content-Type: application/json
- JSON parseable: True
- Record count in sample: 0
- Top-level keys: nextPageToken, studies
- Sample record keys: N/A
- Error: None

## Initial Product Decision

For the USA daily recall MVP, prioritize sources that directly answer: has something people buy/use been recalled or flagged by an official source?

Recommended MVP source groups:

1. Vehicles: NHTSA recalls + vPIC reference.
2. Consumer products: CPSC recalls.
3. Food/groceries: FDA/openFDA Food Enforcement + FDA public recalls page.
4. Medicine: openFDA Drug Enforcement + DailyMed/RxNorm context.
5. Medical devices: openFDA Device Enforcement + Device Event signal warnings.
6. Later: household chemicals/pesticides if a reliable EPA consumer-product source is confirmed.

Avoid synthetic data. Skip sources that cannot be fetched reproducibly.

