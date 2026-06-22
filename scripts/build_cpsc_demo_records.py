import json
from pathlib import Path

SNAPSHOT_PATH = Path("data/safety_sources/cpsc/cpsc_recalls_snapshot.json")
OUTPUT_PATH = Path("data/safety_sources/cpsc/cpsc_demo_records.json")

DEMO_RECALL_NUMBERS = {
    "24335",  # Samsung electric ranges
    "23080",  # Samsung top-load washers fire hazard
    "17028",  # Samsung top-load washers impact injuries
    "23130",  # COSORI air fryers
    "24159",  # Insignia air fryers
    "24051",  # PowerXL air fryers
    "25193",  # Segway Ninebot Max G30P/G30LP
    "25052",  # Segway Ninebot P100
    "25338",  # Anker power banks
    "26532",  # Vornado heaters
    "25215",  # Fisher-Price stroller toy
    "26191",  # KEAWIS crib mattresses
}

def normalize_record(record):
    return {
        "id": f"cpsc-{record.get('RecallNumber')}",
        "category": "consumer_product",
        "source_name": "CPSC Recalls API snapshot",
        "source_type": "local_official_snapshot",
        "source_url": record.get("URL"),
        "title": record.get("Title"),
        "product_name": None,
        "brand_name": None,
        "company_name": None,
        "recall_number": record.get("RecallNumber"),
        "published_date": record.get("RecallDate"),
        "hazard_type": None,
        "reason": record.get("Description"),
        "remedy": record.get("Remedy"),
        "consumer_action": record.get("ConsumerContact"),
        "affected_models": None,
        "affected_lots": None,
        "raw_record": record,
        "keywords": [],
        "notes": "Curated from official CPSC recall JSON snapshot for Dav AI demo/search development.",
    }

def main():
    data = json.loads(SNAPSHOT_PATH.read_text(encoding="utf-8"))

    selected = []
    found_numbers = set()

    for record in data:
        recall_number = str(record.get("RecallNumber", "")).strip()
        if recall_number in DEMO_RECALL_NUMBERS:
            selected.append(normalize_record(record))
            found_numbers.add(recall_number)

    missing = sorted(DEMO_RECALL_NUMBERS - found_numbers)

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_PATH.write_text(json.dumps(selected, indent=2, ensure_ascii=False), encoding="utf-8")

    print(f"Created: {OUTPUT_PATH}")
    print(f"Records selected: {len(selected)}")
    print(f"Missing recall numbers: {missing}")

    for record in selected:
        print("-", record["recall_number"], record["title"])

if __name__ == "__main__":
    main()
