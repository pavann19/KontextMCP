"""Dedicated statutory retrieval API routes (P6.3 & P6.4)."""

from typing import Optional, List, Dict, Any, Literal
from fastapi import APIRouter, Query, Depends
from pydantic import BaseModel, Field
from app.core.security import resolve_user_context
from app.mcp.permissions import UserContext
from app.ingestion.pipeline import IngestionPipeline
from app.retrieval.bm25 import BilingualBM25Retriever
from app.retrieval.dense import DenseRetriever
from app.retrieval.hybrid import HybridRetriever
from app.retrieval.reranker import LegalCrossReranker

router = APIRouter(prefix="/search", tags=["Hybrid Retrieval"])

_cached_chunks = None
_hybrid = None
_reranker = None

def get_engines():
    from app.agent.nodes import get_retrieval_engine
    return get_retrieval_engine()

class SearchHit(BaseModel):
    chunk_id: str
    article_id: str
    title: str
    chapter: str
    language: str
    score: float
    text: str
    context_header: str

class SearchResponse(BaseModel):
    query: str
    language_filter: Optional[str]
    method: str
    total_returned: int
    hits: List[SearchHit]

@router.get("", response_model=SearchResponse)
def search_provisions(
    q: str = Query(..., description="Legal search query in English or German"),
    method: Literal["bm25", "dense", "hybrid", "reranked"] = Query("hybrid"),
    language: Optional[Literal["en", "de"]] = Query(None),
    top_k: int = Query(5, ge=1, le=20),
    user: UserContext = Depends(resolve_user_context)
):
    """Searches bilingual EU AI Act provisions across lexical, dense, and hybrid channels."""
    hybrid, reranker = get_engines()

    # Sanitize language filter
    lang_str = language if isinstance(language, str) else None

    if method == "bm25":
        raw_hits = hybrid.bm25.search(q, top_k=top_k, language=lang_str)
    elif method == "dense":
        raw_hits = hybrid.dense.search(q, top_k=top_k, language=lang_str)
    elif method == "hybrid":
        raw_hits = hybrid.search(q, top_k=top_k, language=lang_str)
    else:  # reranked
        candidates = hybrid.search(q, top_k=top_k * 2, language=lang_str)
        raw_hits = reranker.rerank(q, candidates, top_n=top_k, target_language=lang_str)

    hits = []
    for chunk, score in raw_hits:
        hits.append(SearchHit(
            chunk_id=chunk.chunk_id,
            article_id=chunk.article_id,
            title=chunk.title,
            chapter=chunk.chapter,
            language=chunk.language,
            score=round(score, 4),
            text=chunk.text,
            context_header=chunk.context_header
        ))

    return SearchResponse(
        query=q,
        language_filter=lang_str,
        method=method,
        total_returned=len(hits),
        hits=hits
    )
