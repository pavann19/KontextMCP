"""Hybrid retrieval engine combining BM25 and Dense Vector search (P6.4).

Implements Reciprocal Rank Fusion (RRF) and Normalized Convex Score Combination
to achieve superior retrieval coverage across technical and legal phrasing.
"""

from typing import List, Tuple, Optional, Dict
from app.config import settings
from app.ingestion.chunker import LegalChunk
from app.retrieval.bm25 import BilingualBM25Retriever
from app.retrieval.dense import DenseRetriever

class HybridRetriever:
    """Orchestrates multi-channel retrieval fusing BM25 lexical and Qdrant dense vector search."""
    
    def __init__(
        self,
        bm25: Optional[BilingualBM25Retriever] = None,
        dense: Optional[DenseRetriever] = None,
        alpha: float = settings.HYBRID_ALPHA,
        rrf_k: int = settings.RRF_K
    ):
        self.bm25 = bm25 or BilingualBM25Retriever()
        self.dense = dense or DenseRetriever()
        self.alpha = alpha  # Weight for dense; (1 - alpha) for BM25
        self.rrf_k = rrf_k

    def index(self, chunks: List[LegalChunk]) -> None:
        """Indexes chunks in both BM25 and Dense engines."""
        self.bm25.index(chunks)
        self.dense.index(chunks)

    def search_rrf(
        self,
        query: str,
        top_k: int = 5,
        language: Optional[str] = None,
        candidate_pool_size: int = 20
    ) -> List[Tuple[LegalChunk, float]]:
        """Combines rankings via Reciprocal Rank Fusion (RRF).
        
        Formula: RRF_score(d) = sum( 1.0 / (k + rank_i(d)) )
        """
        bm25_hits = self.bm25.search(query, top_k=candidate_pool_size, language=language)
        dense_hits = self.dense.search(query, top_k=candidate_pool_size, language=language)

        rrf_scores: Dict[str, float] = {}
        chunk_map: Dict[str, LegalChunk] = {}

        # BM25 ranks
        for rank, (chunk, _) in enumerate(bm25_hits, start=1):
            cid = chunk.chunk_id
            chunk_map[cid] = chunk
            rrf_scores[cid] = rrf_scores.get(cid, 0.0) + (1.0 / (self.rrf_k + rank))

        # Dense ranks
        for rank, (chunk, _) in enumerate(dense_hits, start=1):
            cid = chunk.chunk_id
            chunk_map[cid] = chunk
            rrf_scores[cid] = rrf_scores.get(cid, 0.0) + (1.0 / (self.rrf_k + rank))

        sorted_items = sorted(rrf_scores.items(), key=lambda x: x[1], reverse=True)[:top_k]
        return [(chunk_map[cid], score) for cid, score in sorted_items]

    def search_convex(
        self,
        query: str,
        top_k: int = 5,
        language: Optional[str] = None,
        candidate_pool_size: int = 20
    ) -> List[Tuple[LegalChunk, float]]:
        """Normalized Convex Combination: alpha * Dense_norm + (1 - alpha) * BM25_norm."""
        bm25_hits = self.bm25.search(query, top_k=candidate_pool_size, language=language)
        dense_hits = self.dense.search(query, top_k=candidate_pool_size, language=language)

        chunk_map: Dict[str, LegalChunk] = {}
        bm25_score_map: Dict[str, float] = {}
        dense_score_map: Dict[str, float] = {}

        for chunk, score in bm25_hits:
            chunk_map[chunk.chunk_id] = chunk
            bm25_score_map[chunk.chunk_id] = score

        for chunk, score in dense_hits:
            chunk_map[chunk.chunk_id] = chunk
            dense_score_map[chunk.chunk_id] = score

        # Min-max normalize BM25
        if bm25_score_map:
            max_b = max(bm25_score_map.values())
            min_b = min(bm25_score_map.values())
            range_b = max_b - min_b if max_b > min_b else 1.0
            norm_bm25 = {k: (v - min_b) / range_b for k, v in bm25_score_map.items()}
        else:
            norm_bm25 = {}

        # Min-max normalize Dense
        if dense_score_map:
            max_d = max(dense_score_map.values())
            min_d = min(dense_score_map.values())
            range_d = max_d - min_d if max_d > min_d else 1.0
            norm_dense = {k: (v - min_d) / range_d for k, v in dense_score_map.items()}
        else:
            norm_dense = {}

        all_ids = set(norm_bm25.keys()).union(set(norm_dense.keys()))
        combined_scores: Dict[str, float] = {}

        for cid in all_ids:
            s_dense = norm_dense.get(cid, 0.0)
            s_bm25 = norm_bm25.get(cid, 0.0)
            combined = (self.alpha * s_dense) + ((1.0 - self.alpha) * s_bm25)
            combined_scores[cid] = combined

        sorted_items = sorted(combined_scores.items(), key=lambda x: x[1], reverse=True)[:top_k]
        return [(chunk_map[cid], score) for cid, score in sorted_items]

    def search(
        self,
        query: str,
        top_k: int = 5,
        language: Optional[str] = None,
        method: str = "rrf"
    ) -> List[Tuple[LegalChunk, float]]:
        """Public search method dispatching to chosen hybrid strategy."""
        if method.lower() == "convex":
            return self.search_convex(query, top_k=top_k, language=language)
        return self.search_rrf(query, top_k=top_k, language=language)

