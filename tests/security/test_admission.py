import asyncio
import json
import logging
import pytest
from app.core.admission import AdmissionMiddleware


def scope(headers=(), path="/api/v1/chat"):
    return {"type": "http", "method": "POST", "path": path, "headers": list(headers),
            "query_string": b"q=secret-person@example.test"}


async def invoke(app, parts, request=None):
    sent = []
    messages = iter(parts)
    async def receive():
        return next(messages, {"type": "http.disconnect"})
    async def send(message): sent.append(message)
    await app(request or scope(), receive, send)
    return sent


async def ok(scope, receive, send):
    await receive()
    await send({"type": "http.response.start", "status": 200, "headers": []})
    await send({"type": "http.response.body", "body": b"ok"})


@pytest.mark.asyncio
@pytest.mark.parametrize("headers", [[], [(b"content-length", b"1")]])
async def test_chunked_or_understated_body_is_rejected_before_handler(headers):
    calls = []
    async def handler(*args): calls.append(True)
    app = AdmissionMiddleware(handler, max_body_bytes=8)
    sent = await invoke(app, [{"type": "http.request", "body": b"12345", "more_body": True},
                              {"type": "http.request", "body": b"6789", "more_body": False}], scope(headers))
    assert sent[0]["status"] == 413 and not calls and app.active == 0


@pytest.mark.asyncio
async def test_declared_size_and_duplicate_length_rejected_without_reading():
    app = AdmissionMiddleware(ok, max_body_bytes=8)
    for headers, status in (([(b"content-length", b"9")], 413),
                            ([(b"content-length", b"9"*5000)], 400),
                            ([(b"content-length", b"1"), (b"content-length", b"2")], 400)):
        sent = await invoke(app, [], scope(headers))
        assert sent[0]["status"] == status


@pytest.mark.asyncio
async def test_slow_body_deadline_releases_slot():
    app = AdmissionMiddleware(ok, body_timeout=.02)
    sent = []
    async def slow():
        await asyncio.sleep(1)
    async def send(message): sent.append(message)
    await app(scope(), slow, send)
    assert sent[0]["status"] == 408 and app.active == 0


@pytest.mark.asyncio
async def test_overload_liveness_and_cancelled_request_release():
    entered = asyncio.Event()
    release = asyncio.Event()
    async def waiting(s, receive, send):
        if s["path"] != "/health":
            entered.set()
            await release.wait()
        await ok(s, receive, send)
    app = AdmissionMiddleware(waiting, max_inflight=1)
    parts = [{"type": "http.request", "body": b"", "more_body": False}]
    task = asyncio.create_task(invoke(app, parts))
    await entered.wait()
    denied = await invoke(app, parts)
    assert denied[0]["status"] == 503 and (b"retry-after", b"1") in denied[0]["headers"]
    health_scope = scope(path="/health"); health_scope["method"] = "GET"
    assert (await invoke(app, parts, health_scope))[0]["status"] == 200
    task.cancel()
    with pytest.raises(asyncio.CancelledError): await task
    assert app.active == 0
    release.set()
    assert (await invoke(app, parts))[0]["status"] == 200


@pytest.mark.asyncio
async def test_access_records_omit_query_and_caller_credentials(caplog):
    caplog.set_level(logging.INFO, logger="uvicorn.error")
    app = AdmissionMiddleware(ok)
    sent = await invoke(app, [{"type": "http.request", "body": b"private-body", "more_body": False}],
                        scope([(b"x-api-key", b"secret-key")]))
    assert b"x-request-id" in dict(sent[0]["headers"])
    assert "secret-person" not in caplog.text and "private-body" not in caplog.text and "secret-key" not in caplog.text
    record = json.loads(caplog.records[-1].message)
    assert record["route"] == "<unmatched>" and record["status"] == 200
