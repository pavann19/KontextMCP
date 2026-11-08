"""Rule-based lexical reranker (P6.4).

Refines candidate retrieval pools with token-level interaction, legal article matching,
metadata alignment, and diversity deduplication.
"""

import re
from typing import List, Tuple, Optional, Set
from app.ingestion.chunker import LegalChunk

class LegalCrossReranker:
    """Weighted lexical and metadata scoring; no trained cross-encoder."""

    def __init__(self, top_n: int = 3):
        self.top_n = top_n

    def _extract_legal_references(self, text: str) -> Set[str]:
        """Extracts article or annex identifiers (e.g. 'article 5', 'art. 99', 'annex iii')."""
        norm = text.lower()
        refs = set()
        
        # Matches Article/Artikel X or Art. X
        art_matches = re.findall(r"\b(?:article|artikel|art\.?)\s*(\d+)", norm)
        for m in art_matches:
            refs.add(f"article_{m}")
            
        # Matches Annex/Anhang X
        annex_matches = re.findall(r"\b(?:annex|anhang)\s*([ivx]+|\d+)", norm)
        for m in annex_matches:
            refs.add(f"annex_{m}")
            
        return refs

    def compute_rerank_score(
        self,
        query: str,
        chunk: LegalChunk,
        initial_score: float,
        target_language: Optional[str] = None
    ) -> float:
        """Computes fine-grained reranking score combining semantic alignment and metadata."""
        query_lower = query.lower()
        content_lower = chunk.full_content.lower()
        
        query_tokens = set(re.findall(r"[a-z0-9]{3,}", query_lower))
        content_tokens = set(re.findall(r"[a-z0-9]{3,}", content_lower))
        
        # Jaccard lexical overlap
        overlap = len(query_tokens.intersection(content_tokens))
        overlap_score = overlap / len(query_tokens) if query_tokens else 0.0

        # Title & Article ID match
        title_bonus = 0.0
        if chunk.title.lower() in query_lower:
            title_bonus += 0.20
        elif any(w in chunk.title.lower() for w in query_tokens if len(w) > 4):
            title_bonus += 0.10

        # Exact Article number mention match
        query_refs = self._extract_legal_references(query)
        chunk_refs = self._extract_legal_references(f"{chunk.article_id} {chunk.context_header}")
        article_match_bonus = 0.0
        if query_refs and chunk_refs:
            if query_refs.intersection(chunk_refs):
                article_match_bonus = 0.35  # High-confidence exact citation match

        # Language preference bonus
        lang_bonus = 0.0
        if target_language and chunk.language == target_language.lower():
            lang_bonus = 0.05

        # Keywords overlap
        kw_bonus = 0.0
        chunk_kws = {k.lower() for k in chunk.keywords}
        for q_tok in query_tokens:
            if q_tok in chunk_kws:
                kw_bonus += 0.05
        kw_bonus = min(kw_bonus, 0.15)

        final_score = (
            (initial_score * 0.30) +
            (overlap_score * 0.25) +
            title_bonus +
            article_match_bonus +
            lang_bonus +
            kw_bonus
        )
        return float(final_score)

    def rerank(
        self,
        query: str,
        candidates: List[Tuple[LegalChunk, float]],
        top_n: Optional[int] = None,
        target_language: Optional[str] = None,
        deduplicate_by_article: bool = False
    ) -> List[Tuple[LegalChunk, float]]:
        """Reranks candidate chunks and applies optional deduplication."""
        limit = top_n or self.top_n
        if not candidates:
            return []

        scored_candidates: List[Tuple[LegalChunk, float]] = []
        for chunk, base_score in candidates:
            score = self.compute_rerank_score(
                query=query,
                chunk=chunk,
                initial_score=base_score,
                target_language=target_language
            )
            scored_candidates.append((chunk, score))

        scored_candidates.sort(key=lambda x: x[1], reverse=True)

        if not deduplicate_by_article:
            return scored_candidates[:limit]

        # Deduplicate to ensure article diversity if requested
        seen_articles = set()
        deduped: List[Tuple[LegalChunk, float]] = []
        for chunk, score in scored_candidates:
            art = chunk.article_id
            if art not in seen_articles:
                seen_articles.add(art)
                deduped.append((chunk, score))
            if len(deduped) >= limit:
                break
                
        return deduped

