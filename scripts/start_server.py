"""Server launcher with pre-flight checks and diagnostics."""

import sys
import uvicorn
from app.config import settings
from app.db.session import init_db
from app.ingestion.pipeline import IngestionPipeline

def preflight_checks():
    print("=" * 60, flush=True)
    print("🛡️  STARTING SECURE ENTERPRISE RAG PLATFORM PRE-FLIGHT CHECKS", flush=True)
    print("=" * 60, flush=True)

    # 1. Database seed
    print("1. Initializing and verifying relational database...", flush=True)
    settings.validate_runtime()
    init_db()
    print("   [OK] Relational records verified.", flush=True)

    # 2. Ingestion & Vector Index
    print("2. Verifying bilingual EU AI Act documents and vector storage...", flush=True)
    pipeline = IngestionPipeline()
    chunks = pipeline.load_cached_chunks()
    print(f"   [OK] {len(chunks)} legal chunks ready in retrieval index.", flush=True)

    # 3. Model & MCP Server
    print("3. Verifying Model Context Protocol (MCP) tool registrations...", flush=True)
    from app.mcp.server import mcp_server
    tools = mcp_server.list_tools()
    print(f"   [OK] {len(tools)} MCP tools registered.", flush=True)

    print("=" * 60, flush=True)
    print(f"🚀 Server listening at http://{settings.HOST}:{settings.PORT}", flush=True)
    print(f"📚 Interactive Swagger UI: http://{settings.HOST}:{settings.PORT}/docs", flush=True)
    print("=" * 60, flush=True)

if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    preflight_checks()
    uvicorn.run("app.main:app", host=settings.HOST, port=settings.PORT, reload=settings.DEBUG,
                access_log=False, limit_concurrency=64, timeout_graceful_shutdown=30)

