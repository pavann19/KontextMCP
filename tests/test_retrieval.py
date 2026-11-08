"""Tests for BM25, Dense, Hybrid retrieval, and Cross-Reranking (P6.3 & P6.4)."""

import pytest
from app.ingestion.pipeline import IngestionPipeline
from app.retrieval.bm25 import BilingualBM25Retriever
from app.retrieval.dense import DenseRetriever
from app.retrieval.hybrid import HybridRetriever
from app.retrieval.reranker import LegalCrossReranker

@pytest.fixture(scope="module")
def chunks():
    return IngestionPipeline().load_cached_chunks()

def test_bm25_retrieval(chunks):
    bm25 = BilingualBM25Retriever()
    bm25.index(chunks)

    # English query for prohibited practices
    hits_en = bm25.search("prohibited AI practices subliminal manipulation", top_k=3)
    assert len(hits_en) > 0
    top_chunk, score = hits_en[0]
    assert "Article 5" in top_chunk.article_id
    assert score > 0

    # German query for penalties
    hits_de = bm25.search("Geldbußen Sanktionen 35 Millionen Euro", top_k=3)
    assert len(hits_de) > 0
    top_de, score_de = hits_de[0]
    assert "Artikel 99" in top_de.article_id
    assert score_de > 0

def test_dense_retrieval(chunks):
    dense = DenseRetriever()
    dense.index(chunks)

    hits = dense.search("risk management system iterative process", top_k=3)
    assert len(hits) > 0
    top_chunk, score = hits[0]
    assert top_chunk.chunk_id
    assert score > 0

def test_hybrid_and_reranking(chunks):
    hybrid = HybridRetriever()
    hybrid.index(chunks)
    reranker = LegalCrossReranker(top_n=3)

    candidates = hybrid.search("What obligations apply to high-risk AI under Article 9?", top_k=6)
    assert len(candidates) >= 3

    reranked = reranker.rerank("What obligations apply to high-risk AI under Article 9?", candidates, top_n=3)
    assert len(reranked) == 3
    assert "Article 9" in reranked[0][0].article_id

