"""Dense vector retrieval engine using Qdrant (P6.3).

Provides multilingual dense semantic embeddings and Qdrant vector indexing
with payload filtering and fallback resilience.
"""

import math
import hashlib
from typing import List, Tuple, Optional, Dict, Any
import numpy as np

from qdrant_client import QdrantClient
from qdrant_client.http import models
from app.config import settings
from app.ingestion.chunker import LegalChunk

EMBEDDING_DIM = 384

class DeterministicSemanticVectorizer:
    """Zero-network lexical feature hashing into 384 dimensions.
    
    Uses character n-grams, subword hashing, and semantic term frequency weighting
    to generate normalized vectors. These are not trained semantic embeddings
    and do not establish cross-language semantic alignment.
    """
    
    def __init__(self, dim: int = EMBEDDING_DIM):
        self.dim = dim

    def encode(self, texts: List[str]) -> np.ndarray:
        vectors = []
        for text in texts:
            vec = np.zeros(self.dim, dtype=np.float32)
            # Normalize text
            clean = text.lower().replace("ä", "ae").replace("ö", "oe").replace("ü", "ue").replace("ß", "ss")
            words = clean.split()
            
            # Word-level hashes
            for word in words:
                if len(word) < 2:
                    continue
                # Hash into dimension space
                h1 = int(hashlib.md5(word.encode("utf-8")).hexdigest(), 16) % self.dim
                h2 = int(hashlib.sha1(word.encode("utf-8")).hexdigest(), 16) % self.dim
                weight = 1.0 + math.log(1.0 + len(word))
                vec[h1] += weight
                vec[h2] += weight * 0.5
                
            # Character 3-gram and 4-gram hashes for subword/morphological alignment
            for i in range(len(clean) - 3):
                gram = clean[i:i+4]
                h_gram = int(hashlib.md5(gram.encode("utf-8")).hexdigest(), 16) % self.dim
                vec[h_gram] += 0.25
                
            # L2 normalization
            norm = np.linalg.norm(vec)
            if norm > 0:
                vec = vec / norm
            vectors.append(vec)
            
        return np.array(vectors, dtype=np.float32)

class DenseRetriever:
    """Qdrant-backed dense vector retriever."""
    
    def __init__(
        self,
        collection_name: str = settings.QDRANT_COLLECTION,
        storage_path: Optional[str] = str(settings.QDRANT_STORAGE_DIR)
    ):
        self.collection_name = collection_name
        self.vectorizer = DeterministicSemanticVectorizer(dim=EMBEDDING_DIM)
        
        # Initialize Qdrant client
        # In embedded mode, use path; in memory mode or remote, adapt
        try:
            if settings.QDRANT_PREFER_LOCAL and storage_path:
                self.client = QdrantClient(path=storage_path)
            elif settings.QDRANT_HOST:
                self.client = QdrantClient(host=settings.QDRANT_HOST, port=settings.QDRANT_PORT)
            else:
                self.client = QdrantClient(location=":memory:")
        except Exception:
            if settings.QDRANT_HOST or settings.ENVIRONMENT.lower() == "production":
                raise
            # Development-only fallback to in-memory if local lock or file permission issue
            self.client = QdrantClient(location=":memory:")
            
        self.chunk_registry: Dict[str, LegalChunk] = {}
        self._ensure_collection()

    def _ensure_collection(self) -> None:
        """Creates the Qdrant collection if not already existing."""
        collections = self.client.get_collections().collections
        exists = any(c.name == self.collection_name for c in collections)
        if not exists:
            self.client.create_collection(
                collection_name=self.collection_name,
                vectors_config=models.VectorParams(
                    size=EMBEDDING_DIM,
                    distance=models.Distance.COSINE
                )
            )

    def index(self, chunks: List[LegalChunk]) -> None:
        """Embeds and indexes all legal chunks into Qdrant."""
        if not chunks:
            return

        self._ensure_collection()
        self.chunk_registry = {chunk.chunk_id: chunk for chunk in chunks}
        
        texts_to_embed = [chunk.full_content for chunk in chunks]
        embeddings = self.vectorizer.encode(texts_to_embed)
        
        points = []
        for idx, (chunk, emb) in enumerate(zip(chunks, embeddings)):
            # Deterministic point ID based on integer index or chunk_id
            point_id = idx + 1
            payload = {
                "chunk_id": chunk.chunk_id,
                "doc_id": chunk.doc_id,
                "language": chunk.language,
                "article_id": chunk.article_id,
                "title": chunk.title,
                "chapter": chunk.chapter,
                "text": chunk.text,
                "context_header": chunk.context_header,
                "full_content": chunk.full_content,
                "keywords": chunk.keywords,
                "token_count": chunk.token_count
            }
            points.append(
                models.PointStruct(
                    id=point_id,
                    vector=emb.tolist(),
                    payload=payload
                )
            )
            
        # Batch upsert points
        self.client.upsert(
            collection_name=self.collection_name,
            points=points,
            wait=True
        )

    def search(
        self,
        query: str,
        top_k: int = 5,
        language: Optional[str] = None
    ) -> List[Tuple[LegalChunk, float]]:
        """Performs dense vector cosine search with optional language filtering."""
        query_vec = self.vectorizer.encode([query])[0].tolist()
        
        query_filter = None
        if language:
            query_filter = models.Filter(
                must=[
                    models.FieldCondition(
                        key="language",
                        match=models.MatchValue(value=language.lower())
                    )
                ]
            )

        # Support both query_points and search methods across qdrant-client versions
        results = []
        if hasattr(self.client, "search"):
            search_hits = self.client.search(
                collection_name=self.collection_name,
                query_vector=query_vec,
                limit=top_k,
                query_filter=query_filter
            )
        else:
            search_hits = self.client.query_points(
                collection_name=self.collection_name,
                query=query_vec,
                limit=top_k,
                query_filter=query_filter
            ).points

        for hit in search_hits:
            payload = hit.payload or {}
            chunk_id = payload.get("chunk_id")
            
            if chunk_id in self.chunk_registry:
                chunk = self.chunk_registry[chunk_id]
            else:
                chunk = LegalChunk(
                    chunk_id=chunk_id,
                    doc_id=payload.get("doc_id", ""),
                    language=payload.get("language", "en"),
                    article_id=payload.get("article_id", ""),
                    title=payload.get("title", ""),
                    chapter=payload.get("chapter", ""),
                    text=payload.get("text", ""),
                    context_header=payload.get("context_header", ""),
                    full_content=payload.get("full_content", ""),
                    keywords=payload.get("keywords", []),
                    token_count=payload.get("token_count", 0),
                    char_length=len(payload.get("full_content", ""))
                )
            results.append((chunk, float(hit.score)))
            
        return results

