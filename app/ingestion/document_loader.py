"""Document loader for bilingual EU AI Act texts (P6.1 & P6.2)."""

import json
from pathlib import Path
from typing import Dict, List, Any
from app.config import settings

class BilingualDocumentLoader:
    """Loads English and German EU AI Act documents from disk."""
    
    def __init__(self, raw_data_dir: Path = settings.RAW_DATA_DIR):
        self.raw_data_dir = raw_data_dir
        
    def load_documents(self) -> List[Dict[str, Any]]:
        """Loads both English and German raw documents."""
        en_path = self.raw_data_dir / "eu_ai_act_en.json"
        de_path = self.raw_data_dir / "eu_ai_act_de.json"
        
        all_docs: List[Dict[str, Any]] = []
        
        if en_path.exists():
            with open(en_path, "r", encoding="utf-8") as f:
                all_docs.extend(json.load(f))
                
        if de_path.exists():
            with open(de_path, "r", encoding="utf-8") as f:
                all_docs.extend(json.load(f))
                
        return all_docs
        
    def load_by_language(self, lang: str) -> List[Dict[str, Any]]:
        """Loads documents for a specific language ('en' or 'de')."""
        return [doc for doc in self.load_documents() if doc.get("language") == lang.lower()]

