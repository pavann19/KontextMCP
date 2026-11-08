"""Tests for document loading and legal chunking (P6.1 & P6.2)."""

import pytest
from app.ingestion.document_loader import BilingualDocumentLoader
from app.ingestion.chunker import LegalDocumentChunker, LegalChunk
from app.ingestion.pipeline import IngestionPipeline

def test_bilingual_document_loader():
    loader = BilingualDocumentLoader()
    docs = loader.load_documents()
    assert len(docs) > 0, "No documents loaded"

    en_docs = loader.load_by_language("en")
    de_docs = loader.load_by_language("de")

    assert len(en_docs) > 0, "English documents missing"
    assert len(de_docs) > 0, "German documents missing"
    assert all(d["language"] == "en" for d in en_docs)
    assert all(d["language"] == "de" for d in de_docs)

def test_legal_chunker_structure():
    loader = BilingualDocumentLoader()
    docs = loader.load_documents()
    chunker = LegalDocumentChunker(max_tokens=250)

    chunks = chunker.chunk_all(docs)
    assert len(chunks) >= len(docs), "Chunking should produce at least as many chunks as source docs"

    for chunk in chunks:
        assert isinstance(chunk, LegalChunk)
        assert chunk.chunk_id
        assert chunk.article_id
        assert chunk.language in ["en", "de"]
        assert chunk.context_header.startswith("[")
        assert len(chunk.full_content) > len(chunk.text)

def test_ingestion_pipeline_caching():
    pipeline = IngestionPipeline()
    chunks = pipeline.load_cached_chunks()
    assert len(chunks) > 0
    assert pipeline.output_chunks_path.exists()

