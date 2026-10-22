"""Local interactive milestone. No web route or authentication provider is created."""
import argparse
import asyncio
from decimal import Decimal, InvalidOperation
import json
import re
import secrets
import sys

from app.agent.backend import ProcessBackend
from app.agent.contracts import AgentRejected
from app.agent.model import MODELS, OllamaClient
from app.agent.orchestrator import ResearchAgent
from app.agent.state import ProductSession


def format_strength(strength: str | None) -> str:
    if not strength:
        return "Not supplied"
    raw = str(strength).strip()
    match = re.fullmatch(r"\s*(?P<amount>(?:\d+(?:\.\d*)?|\.\d+))\s*mg(?:/1)?\s*", raw, re.IGNORECASE)
    if match:
        try:
            amt = Decimal(match.group("amount"))
            return f"{amt} mg"
        except InvalidOperation:
            pass
    return raw


def format_candidate(index: int, product: dict) -> str:
    brand = ", ".join(product.get("brand_names", [])) or product.get("generic_name") or "Unnamed"
    strength = format_strength(product.get("strength"))
    form = product.get("dosage_form") or "Not supplied"
    product_ndcs = ", ".join(product.get("product_ndcs", [])) or "Not supplied"
    package_ndcs = ", ".join(product.get("package_ndcs", [])) or "Not supplied"
    return (
        f"{index}. {brand} \u2014 {strength} \u2014 {form}\n"
        f"   Product NDC: {product_ndcs}\n"
        f"   Package NDCs: {package_ndcs}"
    )


def format_candidates(candidates: list[dict]) -> str:
    header = "Multiple products found." if len(candidates) > 1 else "One product found."
    items = [format_candidate(i + 1, c) for i, c in enumerate(candidates)]
    return f"{header}\n\n" + "\n\n".join(items)


def resolve_selection(user_input: str, candidates: list[dict]) -> str | None:
    if not isinstance(user_input, str):
        raise AgentRejected("invalid_product_selection")
    stripped = user_input.strip()
    if not stripped:
        return None
    try:
        choice = int(stripped)
    except ValueError:
        raise AgentRejected("invalid_product_selection") from None
    if choice < 1 or choice > len(candidates):
        raise AgentRejected("invalid_product_selection")
    product = candidates[choice - 1]
    if not isinstance(product, dict) or not isinstance(product.get("product_ref"), str):
        raise AgentRejected("invalid_product_selection")
    return product["product_ref"]


def format_briefing(result: dict) -> str:
    """Human-readable source excerpts; full typed JSON remains available separately."""
    if "schema_version" not in result:
        return json.dumps(result, indent=2)
    medication = result["medication"]
    lines = [f"Research workflow: {result['status'].upper()}",
             f"Routing: {result['routing']['mode']} (model suggestions and backend completion are recorded in JSON)",
             format_candidate(1, medication), ""]
    for section in result["sections"]:
        lines.append(f"{section['category'].upper()}: {section['status'].upper()}")
        if section["reason"]:
            lines.append(f"  Reason: {section['reason']}")
        card = section["evidence"]
        if card is None:
            continue
        lines.append(f"  Release: {card['release']['release_id']}; coverage: {card['coverage']['state']}")
        if section["category"] == "labels":
            if not card["records"]:
                lines.append("  No admitted exact-product label; missing linkage does not mean no warnings exist.")
            for record in card["records"]:
                lines.append(f"  Label set {record['label_set_id']}, version {record['label_version']}, effective {record['effective_date']} ({record['selection_status']}).")
                for field in ("boxed_warning", "warnings_and_precautions", "warnings", "contraindications", "drug_interactions", "adverse_reactions"):
                    text = record[field]
                    if text:
                        excerpt = text[:800]
                        suffix = " [excerpt; full stored text available with --json]" if len(text) > 800 else ""
                        lines.append(f"  {field} — quoted label text: {excerpt}{suffix}")
                    else:
                        lines.append(f"  {field}: not available in this stored label; no absence-of-risk inference.")
                lines.append(f"  Source: {record['source_url']} (snapshot {card['source_snapshot_date']})")
        elif section["category"] == "recalls":
            for record in card["records"]:
                lines.extend([f"  {record['recall_number']} — {record['classification']}: {record['reason_for_recall']}",
                    f"  Recalling firm: {record['recalling_firm']}; relationship: {record['applicability_class']}; method: {record['match_method']}; lot scope: {record['lot_scope']}.",
                    f"  Source: {record['source_url']} (snapshot {card['source_snapshot_date']})"])
            if not card["records"]:
                lines.append("  No linked records in this collection; this does not establish no historical recalls.")
        else:
            lines.append("  INGREDIENT-LEVEL reporting only, not observations attributed to this NDC.")
            for record in card["records"]:
                analytics = record["analytics"]
                if analytics is None:
                    lines.append(f"  {record['ingredient_name']}: analytics unavailable, not zero.")
                    continue
                lines.extend([f"  {record['ingredient_name']} — {analytics['report_count']} {analytics['count_unit']}; {analytics['serious_report_count']} marked serious.",
                    f"  Reporting period: {analytics['window_start']} to {analytics['window_end']} ({analytics['date_basis']})."])
                reactions = record["top_reported_reactions"]
                lines.append(f"  Reaction terms (showing {min(5, len(reactions))} of {len(reactions)} stored rankings): " + "; ".join(
                    f"{r['reaction']} (co-report activity {r['co_report_activity']})" for r in reactions[:5]))
                lines.append(f"  Source: {record['source']['source_url']} (snapshot {record['source']['export_date']})")
            lines.append("  Reports do not establish causation, incidence, comparative safety or individual risk; ingredient totals are not summed.")
        lines.append("")
    lines.append("Research limitations:")
    lines.extend(f"- {limitation}" for limitation in result["limitations"])
    return "\n".join(lines)


async def run(arguments, *, session=None, agent=None, owner_id=None):
    owner = owner_id or ("local-cli:" + secrets.token_urlsafe(16))
    if session is None:
        session = ProductSession(owner, backend=ProcessBackend())
    if agent is None:
        agent = ResearchAgent(OllamaClient(arguments.model))
    try:
        result = await session.resolve_for_user(arguments.query, owner_id=owner) if arguments.query else await agent.run(
            arguments.question, session=session, owner_id=owner)
        if result.get("status") == "confirmation_required":
            candidates = result.get("candidates", [])
            if not candidates:
                return
            display = sys.stderr if getattr(arguments, "json", False) else sys.stdout
            print(format_candidates(candidates), file=display)
            if result.get("results_may_be_incomplete"):
                print("Search reached its limit; these candidates may be incomplete. Refine the NDC/formulation if needed.", file=display)
            print(file=display)
            range_label = f"1-{len(candidates)}" if len(candidates) > 1 else "1"
            prompt = f"Select product number ({range_label}, Enter to cancel): "
            if getattr(arguments, "json", False):
                print(prompt, end="", flush=True, file=sys.stderr)
                selection = input("")
            else:
                selection = input(prompt)
            reference = resolve_selection(selection, candidates)
            if not reference:
                return
            await session.confirm(reference, owner_id=owner)
            if hasattr(arguments, "routing"):
                result = await agent.research(arguments.question, session=session, owner_id=owner,
                    categories=arguments.categories, routing=arguments.routing)
            else:
                # Preserve the v1 programmatic run() interface for existing callers.
                result = await agent.run(arguments.question, session=session, owner_id=owner)
        print(json.dumps(result, indent=2) if getattr(arguments, "json", False) or not hasattr(arguments, "routing") else format_briefing(result))
    except (AgentRejected, TimeoutError, EOFError) as exc:
        print(json.dumps({"status": "stopped", "reason": str(exc) or "confirmation_missing"}))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--model", choices=MODELS, default=MODELS[0])
    parser.add_argument("--question", required=True)
    parser.add_argument("--query", help="Optional user-entered product search; still requires confirmation")
    parser.add_argument("--categories", nargs="+", choices=("labels", "recalls", "faers"),
                        help="Explicit evidence scope; otherwise literal category words in the question are used")
    parser.add_argument("--routing", choices=("auto", "model", "deterministic"), default="auto",
                        help="auto may complete a valid subset plan transparently; invalid calls always stop")
    parser.add_argument("--json", action="store_true", help="Print the full typed briefing instead of concise excerpts")
    asyncio.run(run(parser.parse_args()))


if __name__ == "__main__":
    main()
