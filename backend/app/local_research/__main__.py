"""Run only as: PYTHONPATH=backend .venv/bin/python -m app.local_research."""
import secrets
import socket

import uvicorn

from app.db.database import is_deployed_environment
from app.local_research.api import create_app


def main():
    if is_deployed_environment():
        raise SystemExit("Hosted research serving denied")
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as listener:
        listener.bind(("127.0.0.1", 8001))
        listener.listen(32)
        capability = secrets.token_urlsafe(48)
        app = create_app(listener, capability)
        # Interactive delivery only; no credential in request URLs/access logs/files.
        try:
            with open("/dev/tty", "w") as terminal:
                terminal.write("Local pairing capability (paste into Ask Dav AI; expires on server exit):\n")
                terminal.write(capability + "\n")
                terminal.flush()
        except OSError:
            raise SystemExit("An interactive terminal is required for secure local pairing delivery") from None
        config = uvicorn.Config(app, host="127.0.0.1", port=8001, access_log=False,
                                proxy_headers=False, limit_concurrency=32, log_level="critical")
        import asyncio
        asyncio.run(uvicorn.Server(config).serve(sockets=[listener]))


if __name__ == "__main__":
    main()
