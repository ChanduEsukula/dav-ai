# DAV AI ProductScan / Receipt Recall Checker Roadmap

## Purpose

ProductScan is the future image and receipt intake layer for DAV AI. It should let users upload or capture a product photo, package label, medicine box, supplement container, cosmetic product, or receipt, then identify product candidates and check trusted public recall and safety-report sources.

This is public-data safety intelligence only. It is not medical advice, diagnosis, treatment guidance, clinical decision support, or a medical device.

## Future user flow

1. User uploads or captures a receipt, food label, supplement container, medicine box, cosmetic package, or product photo.
2. OCR/computer vision extracts visible text.
3. DAV AI redacts or ignores sensitive information.
4. Product candidate extraction identifies product names, brands, lot numbers, sizes, and categories when visible.
5. USDA FoodData Central can normalize food/product identity where appropriate.
6. User reviews and confirms extracted product candidates.
7. DAV AI searches source-specific public safety endpoints.
8. DAV AI generates a layered report:
   - Simple Summary
   - Key Findings
   - Technical Details
   - Source Timestamps
   - Limitations
   - Audit Context
   - Save / Email / Monitor

## Future endpoints

These are roadmap endpoints and are not implemented in the current backend foundation.

- POST /api/v1/product-scan/extract
- POST /api/v1/product-scan/confirm
- POST /api/v1/product-scan/check
- GET /api/v1/food-identity/search?q=protein%20powder

## Data-source responsibilities

| Layer | Responsibility |
|---|---|
| OCR / computer vision | Reads image text from products, labels, boxes, and receipts. |
| Sensitive-info redaction | Ignores card numbers, addresses, phone numbers, membership IDs, Rx numbers, patient names, and pharmacy labels. |
| USDA FoodData Central | Normalizes food/product identity, branded-food candidates, categories, ingredients, and product metadata. |
| openFDA Food Enforcement | Checks food, supplement, grocery, and packaged-food recall enforcement records. |
| openFDA Drug Enforcement | Checks medicine, OTC, eye-drop, and drug product recall records. |
| openFDA Drug Event | Checks public adverse-event reporting patterns without claiming causation. |
| openFDA Cosmetic Event | Future cosmetic adverse-event and product complaint exploration. |
| DAV AI report engine | Produces source-grounded reports with disclaimers, limitations, and audit context. |

## Privacy and safety boundaries

DAV AI should not ask users to upload private medical or financial information.

Users should be warned not to upload:
- prescription labels with patient names
- Rx numbers
- pharmacy addresses
- insurance cards
- medical bills
- full receipts containing payment card details
- full addresses
- phone numbers
- membership IDs
- date of birth
- patient records

Images should not be stored by default. If storage is later added, it must require explicit user consent, retention controls, and deletion controls.

## Future OCR options

Cloud options:
- Google Cloud Vision
- AWS Textract
- Azure Document Intelligence

Local options:
- Tesseract OCR
- EasyOCR
- OpenCV preprocessing
- Pillow/PIL image handling

## Future matching and confidence scores

ProductScan should expose confidence scores such as:
- OCR text confidence
- product candidate confidence
- brand match confidence
- category match confidence
- lot number match confidence
- recall relevance score
- source freshness score

## Engineering rule

ProductScan should not become a separate application. It should be an input layer that feeds the same DAV AI Everyday Safety source adapter, normalization, scoring, reporting, and audit pipeline.
