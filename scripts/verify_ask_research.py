#!/usr/bin/env python3
"""Real local browser/API/Agent v2 verification. No mocks or model downloads.

Run from repository root with PYTHONPATH=backend .venv/bin/python
scripts/verify_ask_research.py --output /tmp/dav-ai-real-research-next.
A generated capability is transferred to the child browser in its process environment,
never printed, stored in a URL, or written to disk. Services bind loopback only.
"""
import asyncio
import argparse
import os
from pathlib import Path
import secrets
import signal
import socket

import httpx
import uvicorn

from app.local_research.api import create_app

ROOT = Path(__file__).resolve().parents[1]


async def main(args):
    output = Path(args.output).expanduser().resolve()
    output.mkdir(parents=True, exist_ok=False)
    with socket.socket() as listener:
        listener.bind(("127.0.0.1", 8001))
        listener.listen(32)
        capability = secrets.token_urlsafe(48)
        app = create_app(listener, capability)
        server = uvicorn.Server(uvicorn.Config(app, access_log=False, proxy_headers=False,
                                               limit_concurrency=32, log_level="critical"))
        task = asyncio.create_task(server.serve(sockets=[listener]))
        vite = None
        try:
            if not args.reuse_frontend:
                vite = await asyncio.create_subprocess_exec("npm", "run", "dev", "--", "--host", "127.0.0.1",
                    "--port", "15173", "--strictPort", cwd=ROOT / "frontend", start_new_session=True,
                    stdout=asyncio.subprocess.DEVNULL, stderr=asyncio.subprocess.DEVNULL)
            async with httpx.AsyncClient(trust_env=False) as client:
                for _ in range(100):
                    if vite is not None and vite.returncode is not None:
                        raise RuntimeError("Vite could not start; port 15173 must be free")
                    try:
                        response = await client.get("http://127.0.0.1:15173/ask")
                        if response.status_code == 200 and server.started:
                            break
                    except httpx.HTTPError:
                        pass
                    await asyncio.sleep(.1)
                else:
                    raise RuntimeError("Local services did not start")
            child = await asyncio.create_subprocess_exec("node", "e2e/verify-local-research.mjs",
                cwd=ROOT / "frontend", env={**os.environ, "ASK_DAV_PAIRING": capability,
                    "ASK_DAV_OUTPUT": str(output), "ASK_DAV_MODEL": args.model})
            try:
                code = await asyncio.wait_for(child.wait(), 300)
            except BaseException:
                if child.returncode is None:
                    child.kill()
                    await child.wait()
                raise
            if code:
                raise RuntimeError("Real browser verification failed")
            if app.state.registry.entries or app.state.registry.active:
                raise RuntimeError("Session or task cleanup failed")
        finally:
            if vite and vite.returncode is None:
                os.killpg(vite.pid, signal.SIGTERM)
                await vite.wait()
            server.should_exit = True
            await task


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', required=True, help='New output directory; existing paths are refused')
    parser.add_argument('--reuse-frontend', action='store_true', help='Use an already running loopback frontend on 15173')
    parser.add_argument('--model', choices=('llama3.2:3b', 'qwen3.5:4b-q4_K_M'), default='llama3.2:3b')
    asyncio.run(main(parser.parse_args()))
