"""Ingestion pipeline coordinator (P6.2)."""

import json
from pathlib import Path
from typing import List, Dict, Any
from app.config import settings
from app.ingestion.document_loader import BilingualDocumentLoader
from app.ingestion.chunker import LegalDocumentChunker, LegalChunk

class IngestionPipeline:
    """Orchestrates loading, chunking, and preparing documents for retrieval."""
    
    def __init__(
        self,
        raw_dir: Path = None,
        chunks_dir: Path = None,
        max_tokens: int = 300
    ):
        raw_dir = raw_dir or (settings.OFFICIAL_RAW_DATA_DIR if settings.CORPUS_VARIANT == "official" else settings.RAW_DATA_DIR)
        chunks_dir = chunks_dir or (settings.CHUNKS_DIR / "official" if settings.CORPUS_VARIANT == "official" else settings.CHUNKS_DIR)
        self.raw_dir = raw_dir
        self.chunks_dir = chunks_dir
        self.loader = BilingualDocumentLoader(raw_data_dir=raw_dir)
        self.chunker = LegalDocumentChunker(max_tokens=max_tokens)
        self.output_chunks_path = self.chunks_dir / "eu_ai_act_chunks.json"

    def run(self) -> List[LegalChunk]:
        """Runs the document ingestion and chunking pipeline."""
        docs = self.loader.load_documents()
        if not docs and settings.CORPUS_VARIANT == "official":
            raise RuntimeError("Import the official corpus before selecting CORPUS_VARIANT=official")
        if not docs:
            # Generate raw datasets if missing
            from app.ingestion.dataset_generator import save_raw_datasets
            save_raw_datasets(self.raw_dir)
            docs = self.loader.load_documents()
            
        chunks = self.chunker.chunk_all(docs)
        self.chunks_dir.mkdir(parents=True, exist_ok=True)
        
        chunks_data = [chunk.model_dump() for chunk in chunks]
        with open(self.output_chunks_path, "w", encoding="utf-8") as f:
            json.dump(chunks_data, f, indent=2, ensure_ascii=False)
            
        return chunks

    def load_cached_chunks(self) -> List[LegalChunk]:
        """Loads precomputed chunks from disk."""
        if not self.output_chunks_path.exists():
            return self.run()
            
        with open(self.output_chunks_path, "r", encoding="utf-8") as f:
            data = json.load(f)
            return [LegalChunk(**item) for item in data]

if __name__ == "__main__":
    pipeline = IngestionPipeline()
    res = pipeline.run()
    print(f"Ingestion complete: {len(res)} chunks saved to {pipeline.output_chunks_path}")

