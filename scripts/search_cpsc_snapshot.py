import json
import sys
from pathlib import Path

SNAPSHOT_PATH = Path("data/safety_sources/cpsc/cpsc_recalls_snapshot.json")


def record_blob(record):
    return json.dumps(record, ensure_ascii=False).lower()


def get_title(record):
    return record.get("Title") or record.get("Name") or record.get("RecallNumber") or "Untitled recall"


def main():
    if len(sys.argv) < 2:
        print("Usage: python3 scripts/search_cpsc_snapshot.py 'search term'")
        sys.exit(1)

    query = " ".join(sys.argv[1:]).lower().strip()
    terms = [term for term in query.split() if term]

    if not SNAPSHOT_PATH.exists():
        print(f"Missing snapshot file: {SNAPSHOT_PATH}")
        sys.exit(1)

    with SNAPSHOT_PATH.open("r", encoding="utf-8") as f:
        data = json.load(f)

    exact_hits = []
    all_word_hits = []

    for record in data:
        blob = record_blob(record)

        if query in blob:
            exact_hits.append(record)
        elif all(term in blob for term in terms):
            all_word_hits.append(record)

    hits = exact_hits + all_word_hits

    print(f"Query: {query}")
    print(f"Total CPSC records: {len(data)}")
    print(f"Exact phrase matches: {len(exact_hits)}")
    print(f"All-word matches: {len(all_word_hits)}")
    print(f"Total matches: {len(hits)}")
    print()

    for record in hits[:10]:
        print("Title:", get_title(record))
        print("Recall Number:", record.get("RecallNumber"))
        print("Recall Date:", record.get("RecallDate"))
        print("URL:", record.get("URL"))
        print("Description:", (record.get("Description") or "")[:350].replace("\n", " "))
        print("-" * 80)


if __name__ == "__main__":
    main()
