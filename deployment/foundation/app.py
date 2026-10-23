"""Health-only ASGI boundary. It cannot serve evidence, sessions or model calls.

The separate process deliberately never imports app.main, local_research, agent,
SQLite or cloud clients. Deployment still requires separate human authorization.
"""
import asyncio
from collections.abc import Mapping
import json
import os
import re
import sys
import time
import uuid


class ConfigurationError(ValueError):
    pass


def validate_environment(environment: Mapping[str, str]) -> int:
    if environment.get("DAVAI_ENV") not in {"staging", "production"}:
        raise ConfigurationError("DAVAI_ENV must explicitly identify a hosted environment")
    if environment.get("DAVAI_FOUNDATION_MODE") != "deny":
        raise ConfigurationError("Only the deny foundation mode is supported")
    # An accidentally mounted release or credential must not activate this image.
    forbidden = {"DAV_AI_PHARMA_RELEASE_DB", "DAV_AI_PHARMA_ARTIFACT_ROOT", "DATABASE_URL",
                 "GOOGLE_APPLICATION_CREDENTIALS", "OLLAMA_HOST"}
    if forbidden.intersection(environment):
        raise ConfigurationError("Data, model and key-file configuration is forbidden in the foundation")
    for name in ("APP_ENV", "ENVIRONMENT", "PYTHON_ENV"):
        if name in environment and environment[name] != environment["DAVAI_ENV"]:
            raise ConfigurationError("Conflicting hosted environment markers")
    port = environment.get("PORT", "8080")
    if not re.fullmatch(r"[0-9]{1,5}", port) or not 1024 <= int(port) <= 65535:
        raise ConfigurationError("PORT must be an unprivileged TCP port")
    return int(port)


class FoundationApplication:
    def __init__(self, environment=None):
        self.environment = environment

    async def __call__(self, scope, receive, send):
        if scope["type"] == "lifespan":
            while True:
                event = await receive()
                if event["type"] == "lifespan.startup":
                    try:
                        validate_environment(self.environment if self.environment is not None else os.environ)
                    except ConfigurationError:
                        await send({"type": "lifespan.startup.failed", "message": "Invalid deny-only foundation configuration"})
                        return
                    await send({"type": "lifespan.startup.complete"})
                elif event["type"] == "lifespan.shutdown":
                    await send({"type": "lifespan.shutdown.complete"})
                    return
            return
        if scope["type"] == "websocket":
            await send({"type": "websocket.close", "code": 1008})
            return
        if scope["type"] != "http":
            return
        started = time.monotonic()
        request_id = uuid.uuid4().hex  # Never accept arbitrary client log identifiers.
        healthy = scope.get("path") == "/health" and scope.get("method") in {"GET", "HEAD"}
        try:
            validate_environment(self.environment if self.environment is not None else os.environ)
            status, code = (200, "foundation_alive") if healthy else (503, "serving_not_authorized")
        except ConfigurationError:
            status, code = 503, "foundation_configuration_denied"
        body = json.dumps({"code": code, "pharmaceutical_serving": False, "research_jobs": False},
                          separators=(",", ":")).encode()
        headers = [(b"content-type", b"application/json"), (b"cache-control", b"no-store"),
                   (b"x-content-type-options", b"nosniff"), (b"referrer-policy", b"no-referrer"),
                   (b"x-frame-options", b"DENY"), (b"x-request-id", request_id.encode())]
        await send({"type": "http.response.start", "status": status, "headers": headers})
        await send({"type": "http.response.body", "body": b"" if scope.get("method") == "HEAD" else body})
        # Do not log URL/path/query, prompts, request headers/body, cookies, users,
        # capabilities, caller-supplied IDs or stack traces. Platform logs are separate.
        event = {"severity": "INFO", "event": "foundation_request", "request_id": request_id,
                 "route_class": "health" if healthy else "denied", "status": status,
                 "duration_ms": round((time.monotonic() - started) * 1000, 2)}
        print(json.dumps(event, separators=(",", ":")), file=sys.stdout, flush=True)


app = FoundationApplication()


def main():
    import uvicorn
    try:
        port = validate_environment(os.environ)
    except ConfigurationError:
        raise SystemExit("Invalid deny-only foundation configuration") from None
    # 0.0.0.0 is required inside the container. IaC is private-only; local smoke
    # commands must publish the host port to 127.0.0.1 explicitly.
    config = uvicorn.Config(app, host="0.0.0.0", port=port, access_log=False,
                            proxy_headers=False, log_level="critical", workers=1,
                            limit_concurrency=4, timeout_keep_alive=5)
    asyncio.run(uvicorn.Server(config).serve())


if __name__ == "__main__":
    main()
