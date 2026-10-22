"""Local interactive milestone. No web route or authentication provider is created."""
import argparse
import asyncio
from decimal import Decimal, InvalidOperation
import json
import re
import secrets

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
            print(format_candidates(candidates))
            print()
            range_label = f"1-{len(candidates)}" if len(candidates) > 1 else "1"
            prompt = f"Select product number ({range_label}, Enter to cancel): "
            reference = resolve_selection(input(prompt), candidates)
            if not reference:
                return
            await session.confirm(reference, owner_id=owner)
            result = await agent.run(arguments.question, session=session, owner_id=owner)
        print(json.dumps(result, indent=2))
    except (AgentRejected, TimeoutError, EOFError) as exc:
        print(json.dumps({"status": "stopped", "reason": str(exc) or "confirmation_missing"}))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--model", choices=MODELS, default=MODELS[0])
    parser.add_argument("--question", required=True)
    parser.add_argument("--query", help="Optional user-entered product search; still requires confirmation")
    asyncio.run(run(parser.parse_args()))


if __name__ == "__main__":
    main()
