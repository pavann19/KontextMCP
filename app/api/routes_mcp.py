"""Stateless MCP Streamable HTTP with JSON responses (2025-03-26)."""
import json
from fastapi import APIRouter, Depends, HTTPException, Request, Response
from fastapi.responses import JSONResponse
from starlette.concurrency import run_in_threadpool
from app.config import settings
from app.core.security import resolve_user_context
from app.mcp.permissions import UserContext
from app.mcp.server import mcp_server

router = APIRouter()
MAX_BODY = 1024 * 1024


def check_origin(request):
    if request.url.hostname not in settings.MCP_ALLOWED_HOSTS:
        raise HTTPException(421, "Unrecognized MCP host.")
    origin = request.headers.get("origin")
    if origin and origin not in settings.ALLOWED_ORIGINS:
        raise HTTPException(403, "MCP origin is not allowed.")


@router.api_route("/mcp", methods=["GET", "DELETE"])
def no_stream(request: Request, user: UserContext = Depends(resolve_user_context)):
    check_origin(request)
    return Response(status_code=405, headers={"Allow": "POST"})


@router.post("/mcp")
async def mcp_http(request: Request, user: UserContext = Depends(resolve_user_context)):
    check_origin(request)
    if "application/json" not in request.headers.get("content-type", ""):
        raise HTTPException(415, "MCP requires application/json.")
    accept = request.headers.get("accept", "")
    if "application/json" not in accept or "text/event-stream" not in accept:
        raise HTTPException(406, "Accept must include application/json and text/event-stream.")
    body = bytearray()
    async for part in request.stream():
        body.extend(part)
        if len(body) > MAX_BODY:
            raise HTTPException(413, "MCP message is too large.")
    try:
        data = json.loads(body)
    except (ValueError, UnicodeError):
        return JSONResponse({"jsonrpc":"2.0", "id":None, "error":{"code":-32700,"message":"Parse error"}}, status_code=400)
    initial = isinstance(data, dict) and data.get("method") in {"initialize", "server/discover"}
    if not initial and request.headers.get("mcp-protocol-version", "2025-03-26") not in {"2025-03-26", "2024-11-05"}:
        raise HTTPException(400, "Unsupported MCP protocol version.")
    messages = data if isinstance(data, list) else [data]
    if not messages or len(messages) > 20:
        raise HTTPException(400, "MCP batch must contain 1 to 20 messages.")
    results = []
    for message in messages:
        if isinstance(message, dict) and message.get("jsonrpc") == "2.0" and "id" not in message and isinstance(message.get("method"), str):
            # Notifications do not execute tools and never produce a response.
            continue
        result = await run_in_threadpool(mcp_server.handle_jsonrpc, message, user)
        if isinstance(message, dict) and message.get("method") == "initialize" and "result" in result:
            result["result"]["protocolVersion"] = "2025-03-26"
        results.append(result)
    if not results:
        return Response(status_code=202)
    return JSONResponse(results if isinstance(data, list) else results[0])
