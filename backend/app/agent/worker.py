"""Private subprocess entrypoint; not a model-accessible tool/HTTP endpoint."""
import sys

from app.agent.backend import WORKER_BYTES
from app.agent.contracts import decode, encode
from app.agent.tools import resolve_drug_product, search_historical_recalls
from app.agent.source_tools import get_source_evidence
from app.db.pharma.release_repository import FrozenPharmaReleaseRepository


def main():
    try:
        request = decode(sys.stdin.buffer.read(8193), 8192)
        if set(request) != {"operation", "arguments"}:
            raise ValueError("Invalid worker envelope")
        operation, arguments = request["operation"], request["arguments"]
        if not isinstance(arguments, dict):
            raise ValueError("Invalid worker arguments")
        if operation == "resolve" and set(arguments) == {"query"}:
            result = resolve_drug_product(arguments["query"])
        elif operation == "product" and set(arguments) == {"product_id"}:
            result = FrozenPharmaReleaseRepository().find_by_id(arguments["product_id"])
        elif operation == "recalls" and set(arguments) == {"product_id"}:
            result = search_historical_recalls(arguments["product_id"])
        elif operation in {"labels_v2", "recalls_v2", "faers_v2"} and set(arguments) == {"product_id"}:
            result = get_source_evidence(operation.removesuffix("_v2"), arguments["product_id"])
        else:
            raise ValueError("Unknown worker operation")
        output = encode({"ok": True, "result": result}, WORKER_BYTES)
    except Exception:
        output = b'{"ok":false}'
    sys.stdout.buffer.write(output)


if __name__ == "__main__":
    main()
