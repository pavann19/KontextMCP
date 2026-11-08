"""Line-delimited JSON-RPC stdio adapter for the MCP tool dispatcher.

Set MCP_API_KEY to an API credential provisioned in API_KEYS for privileged tools.
Stdout is reserved exclusively for protocol messages.
"""
import contextlib
import json
import os
import sys


def main():
    with contextlib.redirect_stdout(sys.stderr):
        from app.core.security import resolve_user_context
        from app.db.session import init_db
        from app.mcp.server import mcp_server
        from app.config import settings
        settings.validate_runtime()
        user = resolve_user_context(x_api_key=os.getenv("MCP_API_KEY"), x_user_role=None,
                                    x_user_id=None, x_user_department=None)
        init_db()
    for line in sys.stdin:
        try:
            request = json.loads(line)
        except ValueError:
            response = {"jsonrpc": "2.0", "id": None,
                        "error": {"code": -32700, "message": "Parse error"}}
        else:
            # Notifications have no response. Tool calls must carry a request id.
            if (isinstance(request, dict) and request.get("jsonrpc") == "2.0"
                    and isinstance(request.get("method"), str) and "id" not in request):
                continue
            with contextlib.redirect_stdout(sys.stderr):
                response = mcp_server.handle_jsonrpc(request, user=user)
        sys.stdout.write(json.dumps(response, ensure_ascii=False, allow_nan=False) + "\n")
        sys.stdout.flush()


if __name__ == "__main__":
    main()
