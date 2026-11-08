"""Main API v1 router mounting all modular subrouters."""

from fastapi import APIRouter
from app.api.routes_chat import router as chat_router
from app.api.routes_search import router as search_router
from app.api.routes_tools import router as tools_router
from app.api.routes_audit import router as audit_router
from app.api.routes_benchmark import router as benchmark_router

api_router = APIRouter()
api_router.include_router(chat_router)
api_router.include_router(search_router)
api_router.include_router(tools_router)
api_router.include_router(audit_router)
api_router.include_router(benchmark_router)

