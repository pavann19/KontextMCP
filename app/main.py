"""FastAPI application entrypoint for Secure Enterprise RAG Platform."""

import asyncio
from contextlib import asynccontextmanager, suppress
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config import settings
from app.api.router import api_router
from app.db.session import init_db
from app.ingestion.pipeline import IngestionPipeline

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan startup and shutdown events."""
    settings.validate_runtime()
    # Schema setup does not insert demo enterprise records.
    init_db()

    # 2. Ingest legal documents and build cache
    pipeline = IngestionPipeline()
    pipeline.load_cached_chunks()

    # Pre-initialize retrieval engine
    from app.agent.nodes import get_retrieval_engine
    get_retrieval_engine()

    from app.core.outbox import dispatch_pending
    async def deliver():
        while True:
            try:
                await asyncio.to_thread(dispatch_pending)
            except Exception:
                # Outages leave durable intents pending; the worker keeps retrying.
                pass
            await asyncio.sleep(1)
    worker = asyncio.create_task(deliver())
    try:
        yield
    finally:
        worker.cancel()
        with suppress(asyncio.CancelledError):
            await worker

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description=(
        "Local-first enterprise knowledge assistant and secure agentic platform for "
        "bilingual German/English EU AI Act compliance, Model Context Protocol (MCP) "
        "database tools, RBAC/ABAC permission boundaries, PII guardrails, and cryptographic auditability."
    ),
    lifespan=lifespan
)

# Enable CORS for local dashboards and integrations
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=False,
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type", "X-API-Key"],
)
from starlette.middleware.trustedhost import TrustedHostMiddleware
from app.core.admission import AdmissionMiddleware
app.add_middleware(TrustedHostMiddleware, allowed_hosts=settings.HTTP_ALLOWED_HOSTS)
app.add_middleware(AdmissionMiddleware, max_body_bytes=settings.HTTP_MAX_BODY_BYTES,
                   max_inflight=settings.HTTP_MAX_INFLIGHT,
                   body_timeout=settings.HTTP_BODY_TIMEOUT_SECONDS)

# Health endpoint
@app.get("/health", tags=["Health"])
def health_check():
    """System health check and operational status."""
    return {
        "status": "healthy",
        "service": settings.PROJECT_NAME,
        "version": settings.VERSION,
        "environment": settings.ENVIRONMENT
    }

# Mount API v1 router
app.include_router(api_router, prefix=settings.API_V1_PREFIX)
from app.api.routes_mcp import router as mcp_router
app.include_router(mcp_router)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host=settings.HOST, port=settings.PORT, reload=settings.DEBUG)


from app.api.routes_operations import router as operations_router, COUNTS
app.include_router(operations_router)

@app.middleware("http")
async def count_requests(request, call_next):
    import time
    start=time.perf_counter()
    try:
        response=await call_next(request)
        if response.status_code>=500:COUNTS["server_errors"]+=1
        return response
    except Exception:
        COUNTS["server_errors"]+=1
        raise
    finally:
        COUNTS["requests"]+=1
        COUNTS["latency_seconds"]+=time.perf_counter()-start
