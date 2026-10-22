"""Outermost report boundary: bounded reads and privacy headers on every response."""
import asyncio
from starlette.responses import JSONResponse

REPORT_PATH = "/api/v1/reports/pharmaceutical"
MAX_BODY_BYTES = 4096
BODY_TIMEOUT_SECONDS = 10


class ReportPrivacyMiddleware:
    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http" or scope["path"].rstrip("/") != REPORT_PATH:
            return await self.app(scope, receive, send)

        async def private_send(message):
            if message["type"] == "http.response.start":
                message["headers"] = [(k, v) for k, v in message.get("headers", [])
                                      if k.lower() not in {b"cache-control", b"pragma", b"x-content-type-options"}]
                message["headers"].extend([(b"cache-control", b"no-store, private, max-age=0"),
                                           (b"pragma", b"no-cache"), (b"x-content-type-options", b"nosniff")])
            await send(message)

        async def error(status, detail):
            await JSONResponse({"detail": detail}, status_code=status)(scope, receive, private_send)

        if scope.get("query_string"):
            return await error(400, "Submit report fields in the JSON body only")
        headers = dict(scope.get("headers", []))
        try:
            length = int(headers.get(b"content-length", b"0"))
            if length < 0 or length > MAX_BODY_BYTES:
                return await error(413, "Report request exceeds 4096 bytes")
        except ValueError:
            return await error(400, "Invalid Content-Length")

        body = bytearray()
        try:
            async with asyncio.timeout(BODY_TIMEOUT_SECONDS):
                while True:
                    message = await receive()
                    if message["type"] == "http.disconnect":
                        return
                    chunk = message.get("body", b"")
                    # Check before copying a potentially oversized ASGI chunk.
                    if len(body) + len(chunk) > MAX_BODY_BYTES:
                        return await error(413, "Report request exceeds 4096 bytes")
                    body.extend(chunk)
                    if not message.get("more_body", False):
                        break
        except TimeoutError:
            return await error(408, "Report request body timed out")

        delivered = False

        async def bounded_receive():
            nonlocal delivered
            if delivered:
                return await receive()
            delivered = True
            return {"type": "http.request", "body": bytes(body), "more_body": False}

        await self.app(scope, bounded_receive, private_send)
