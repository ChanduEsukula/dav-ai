import json
import sys
from pathlib import Path

DEMO_PATH = Path("data/safety_sources/cpsc/cpsc_demo_records.json")


def blob(record):
    return json.dumps(record, ensure_ascii=False).lower()


def main():
    if len(sys.argv) < 2:
        print("Usage: python3 scripts/search_cpsc_demo_records.py 'search term'")
        sys.exit(1)

    query = " ".join(sys.argv[1:]).lower().strip()
    terms = [term for term in query.split() if term]

    records = json.loads(DEMO_PATH.read_text(encoding="utf-8"))

    hits = []
    for record in records:
        text = blob(record)
        if query in text or all(term in text for term in terms):
            hits.append(record)

    print(f"Query: {query}")
    print(f"Demo records: {len(records)}")
    print(f"Matches: {len(hits)}")
    print()

    for record in hits:
        print("Title:", record.get("title"))
        print("Recall Number:", record.get("recall_number"))
        print("Date:", record.get("published_date"))
        print("Source:", record.get("source_name"))
        print("URL:", record.get("source_url"))
        print("Reason:", (record.get("reason") or "")[:300].replace("\n", " "))
        print("-" * 80)


if __name__ == "__main__":
    main()
