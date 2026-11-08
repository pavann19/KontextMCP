"""Per-process admission bounds and query-free structured HTTP access records."""
import asyncio
import json
import logging
import time
import uuid

REJECTIONS = {"body_size": 0, "body_timeout": 0, "overload": 0, "framing": 0}
logger = logging.getLogger("uvicorn.error")


class AdmissionMiddleware:
    def __init__(self, app, max_body_bytes=1048576, max_inflight=16, body_timeout=5):
        self.app = app
        self.max_body_bytes = max_body_bytes
        self.max_inflight = max_inflight
        self.body_timeout = body_timeout
        self.active = 0

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            return await self.app(scope, receive, send)
        request_id = uuid.uuid4().hex
        started = time.monotonic()
        status = 500
        admitted = False

        async def tracked_send(message):
            nonlocal status
            if message["type"] == "http.response.start":
                status = message["status"]
                message = dict(message)
                message["headers"] = list(message.get("headers", [])) + [(b"x-request-id", request_id.encode())]
            await send(message)

        async def reject(code, reason, detail):
            REJECTIONS[reason] += 1
            body = json.dumps({"detail": detail, "request_id": request_id}).encode()
            headers = [(b"content-type", b"application/json")]
            if code == 503: headers.append((b"retry-after", b"1"))
            await tracked_send({"type": "http.response.start", "status": code, "headers": headers})
            await tracked_send({"type": "http.response.body", "body": body})

        try:
            lengths = [v for k, v in scope.get("headers", []) if k.lower() == b"content-length"]
            if len(lengths) > 1 or (lengths and (len(lengths[0]) > 20 or not lengths[0].isdigit())):
                return await reject(400, "framing", "Invalid request framing.")
            if lengths and int(lengths[0]) > self.max_body_bytes:
                return await reject(413, "body_size", "Request body exceeds the configured limit.")
            # Liveness remains available under overload. Readiness still exercises dependencies.
            liveness = scope.get("path") == "/health" and scope["method"] in {"GET", "HEAD"}
            if not liveness:
                # No await between checking and reserving a slot on this event loop.
                if self.active >= self.max_inflight:
                    return await reject(503, "overload", "Server busy; retry with backoff.")
                self.active += 1
                admitted = True
            body = bytearray()
            try:
                async with asyncio.timeout(self.body_timeout):
                    while True:
                        message = await receive()
                        if message["type"] == "http.disconnect":
                            return
                        part = message.get("body", b"")
                        if len(body) + len(part) > self.max_body_bytes:
                            return await reject(413, "body_size", "Request body exceeds the configured limit.")
                        body.extend(part)
                        if not message.get("more_body", False):
                            break
            except TimeoutError:
                return await reject(408, "body_timeout", "Request body deadline exceeded.")
            consumed = False

            async def replay():
                nonlocal consumed
                if consumed:
                    return await receive()
                consumed = True
                return {"type": "http.request", "body": bytes(body), "more_body": False}

            await self.app(scope, replay, tracked_send)
        finally:
            if admitted:
                self.active -= 1
            # Route templates contain no query values, caller IDs or credentials.
            logger.info(json.dumps({"event": "http_request", "request_id": request_id,
                                   "method": scope["method"],
                                   "route": getattr(scope.get("route"), "path", "<unmatched>"),
                                   "status": status, "duration_ms": round((time.monotonic()-started)*1000, 3)}))
