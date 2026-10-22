"""Killable read-only repository worker. Timeouts cannot later mutate session state."""
import asyncio
import os
from pathlib import Path
import sys

from app.agent.contracts import AgentRejected, decode, encode

WORKER_BYTES = 262144


class ProcessBackend:
    async def execute(self, operation: str, arguments: dict, *, timeout: float):
        environment = dict(os.environ, PYTHONPATH=str(Path(__file__).resolve().parents[2]))
        process = await asyncio.create_subprocess_exec(
            sys.executable, "-m", "app.agent.worker", stdin=asyncio.subprocess.PIPE,
            stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.DEVNULL, env=environment,
        )
        try:
            # The fixed worker bounds its serialized output before writing. It runs
            # only repository reads; model tool names never become executable names.
            stdout, _ = await asyncio.wait_for(process.communicate(
                encode({"operation": operation, "arguments": arguments}, 8192)), timeout)
            if process.returncode != 0:
                raise AgentRejected("evidence_unavailable")
            result = decode(stdout, WORKER_BYTES)
            if result.get("ok") is not True:
                raise AgentRejected("evidence_unavailable")
            return result["result"]
        finally:
            if process.returncode is None:
                try:
                    process.kill()
                except ProcessLookupError:
                    pass
                await process.wait()
