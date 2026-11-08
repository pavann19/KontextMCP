"""Statutory legal corpus provenance, metadata, and official EUR-Lex alignment tests (P1 - Section 8)."""

import json
import hashlib
import pytest
from app.config import settings

@pytest.fixture(scope="module")
def corpus():
    en_path = settings.RAW_DATA_DIR / "eu_ai_act_en.json"
    de_path = settings.RAW_DATA_DIR / "eu_ai_act_de.json"
    with open(en_path, "r", encoding="utf-8") as f:
        en_docs = json.load(f)
    with open(de_path, "r", encoding="utf-8") as f:
        de_docs = json.load(f)
    return {"en": en_docs, "de": de_docs}

def test_corpus_provenance_metadata(corpus):
    for doc in corpus["en"]:
        assert doc.get("regulation_id") == "Regulation (EU) 2024/1689"
        assert "eur-lex.europa.eu" in doc.get("celex_uri", "")
        assert doc.get("publication_date") == "2024-07-12"
        assert "content_sha256" in doc
        # Validate SHA-256 hash match
        expected_hash = hashlib.sha256(doc["text"].encode("utf-8")).hexdigest()
        assert doc["content_sha256"] == expected_hash

    for doc in corpus["de"]:
        assert "2024/1689" in doc.get("regulation_id", "")
        assert "eur-lex.europa.eu" in doc.get("celex_uri", "")
        assert doc.get("publication_date") == "2024-07-12"
        expected_hash = hashlib.sha256(doc["text"].encode("utf-8")).hexdigest()
        assert doc["content_sha256"] == expected_hash

def test_corpus_official_penalties_article_99(corpus):
    en_art99 = next(d for d in corpus["en"] if d["article_id"] == "Article 99")
    de_art99 = next(d for d in corpus["de"] if d["article_id"] == "Artikel 99")

    # 35M / 7%
    assert "35 000 000 EUR" in en_art99["text"] or "35,000,000 EUR" in en_art99["text"] or "35 000 000" in en_art99["text"]
    assert "7 %" in en_art99["text"] or "7%" in en_art99["text"]
    assert "35 000 000" in de_art99["text"]
    assert "7 %" in de_art99["text"] or "7%" in de_art99["text"]

    # 15M / 3%
    assert "15 000 000" in en_art99["text"]
    assert "3 %" in en_art99["text"] or "3%" in en_art99["text"]

    # 7.5M / 1%
    assert "7 500 000" in en_art99["text"]
    assert "1,5 %" in en_art99["text"] or "1.5 %" in en_art99["text"] or "1.5%" in en_art99["text"]

def test_gpai_compute_threshold_article_51(corpus):
    en_art51 = next(d for d in corpus["en"] if d["article_id"] == "Article 51")
    de_art51 = next(d for d in corpus["de"] if d["article_id"] == "Artikel 51")
    assert "10^25" in en_art51["text"] or "10²⁵" in en_art51["text"]
    assert "10^25" in de_art51["text"] or "10²⁵" in de_art51["text"]

