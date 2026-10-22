"""Local interactive milestone. No web route or authentication provider is created."""
import argparse
import asyncio
import json
import secrets

from app.agent.backend import ProcessBackend
from app.agent.contracts import AgentRejected
from app.agent.model import MODELS, OllamaClient
from app.agent.orchestrator import ResearchAgent
from app.agent.state import ProductSession


async def run(arguments):
    owner = "local-cli:" + secrets.token_urlsafe(16)
    session = ProductSession(owner, backend=ProcessBackend())
    agent = ResearchAgent(OllamaClient(arguments.model))
    try:
        result = await session.resolve_for_user(arguments.query, owner_id=owner) if arguments.query else await agent.run(
            arguments.question, session=session, owner_id=owner)
        print(json.dumps(result, indent=2))
        if result["status"] == "confirmation_required":
            # This input is deliberately outside the model/tool executor.
            reference = input("Confirm the exact product by entering its product_ref (empty to stop): ").strip()
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
