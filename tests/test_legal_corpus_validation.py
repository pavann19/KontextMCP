"""Validation of the legal corpus against official EU AI Act (Regulation (EU) 2024/1689) (P6.1).

Validates:
1. Bilateral structural coverage between English and German texts.
2. Statutory penalty limits and computational thresholds against official text.
3. Alignment of key legal definitions and prohibited practices.
4. Official bilingual legal terminology correspondence.
"""

import json
import pytest
from app.config import settings

@pytest.fixture(scope="module")
def corpus():
    en_file = settings.RAW_DATA_DIR / "eu_ai_act_en.json"
    de_file = settings.RAW_DATA_DIR / "eu_ai_act_de.json"

    with open(en_file, "r", encoding="utf-8") as f:
        en_docs = json.load(f)
    with open(de_file, "r", encoding="utf-8") as f:
        de_docs = json.load(f)

    return {"en": en_docs, "de": de_docs}

def test_bilateral_structural_alignment(corpus):
    """Verifies that every English statutory provision has a corresponding German statutory provision."""
    en_articles = {d["article_id"].replace("Article", "").replace("Annex", "").strip(): d for d in corpus["en"]}
    de_articles = {d["article_id"].replace("Artikel", "").replace("Anhang", "").strip(): d for d in corpus["de"]}

    # All articles present in EN must be present in DE
    assert set(en_articles.keys()) == set(de_articles.keys()), (
        f"Mismatch between EN and DE provisions: {set(en_articles.keys()) ^ set(de_articles.keys())}"
    )

def test_official_penalty_thresholds(corpus):
    """Validates Article 99 administrative fines against the official Regulation (EU) 2024/1689."""
    en_art99 = next(d for d in corpus["en"] if d["article_id"] == "Article 99")
    de_art99 = next(d for d in corpus["de"] if d["article_id"] == "Artikel 99")

    # Official Tier 1: 35 000 000 EUR or 7% turnover for prohibited practices (Article 5)
    assert "35 000 000 EUR" in en_art99["text"]
    assert "7 %" in en_art99["text"] or "7%" in en_art99["text"]
    assert "35 000 000 EUR" in de_art99["text"]
    assert "7 %" in de_art99["text"] or "7%" in de_art99["text"]

    # Official Tier 2: 15 000 000 EUR or 3% turnover for high-risk non-compliance
    assert "15 000 000 EUR" in en_art99["text"]
    assert "3 %" in en_art99["text"] or "3%" in en_art99["text"]
    assert "15 000 000 EUR" in de_art99["text"]
    assert "3 %" in de_art99["text"] or "3%" in de_art99["text"]

    # Official Tier 3: 7 500 000 EUR or 1.5% turnover for misleading information
    assert "7 500 000 EUR" in en_art99["text"]
    assert "1,5 %" in en_art99["text"] or "1.5 %" in en_art99["text"] or "1.5%" in en_art99["text"]
    assert "7 500 000 EUR" in de_art99["text"]
    assert "1,5 %" in de_art99["text"] or "1.5 %" in de_art99["text"] or "1.5%" in de_art99["text"]

def test_gpai_systemic_risk_computation_threshold(corpus):
    """Validates Article 51 GPAI systemic risk presumption threshold (10^25 FLOPs)."""
    en_art51 = next(d for d in corpus["en"] if d["article_id"] == "Article 51")
    de_art51 = next(d for d in corpus["de"] if d["article_id"] == "Artikel 51")

    assert "10^25" in en_art51["text"]
    assert "FLOPs" in en_art51["text"]
    assert "10^25" in de_art51["text"]
    assert "FLOPs" in de_art51["text"]

def test_prohibited_practices_enumeration(corpus):
    """Validates Article 5 prohibited practices against official statutory clauses."""
    en_art5 = next(d for d in corpus["en"] if d["article_id"] == "Article 5")
    de_art5 = next(d for d in corpus["de"] if d["article_id"] == "Artikel 5")

    # EN clauses: subliminal, vulnerabilities, social scoring, predictive policing, untargeted scraping, emotion recognition
    assert "subliminal techniques" in en_art5["text"]
    assert "social scoring" in en_art5["text"].lower() or "social score" in en_art5["text"].lower()
    assert "untargeted scraping" in en_art5["text"]
    assert "workplace" in en_art5["text"]

    # DE clauses: unterschwellig, Social Scoring, ungezieltes Scraping, Arbeitsplatz
    assert "unterschwellige Techniken" in de_art5["text"]
    assert "Social Scoring" in de_art5["text"]
    assert "ungezielte" in de_art5["text"] or "ungezielt" in de_art5["text"]
    assert "Arbeitspl" in de_art5["text"] or "arbeitsplatz" in de_art5["text"].lower()

def test_official_terminology_bilingual_dictionary(corpus):
    """Validates alignment of core regulatory terms between EN and DE."""
    term_pairs = [
        ("AI system", "KI-System"),
        ("provider", "Anbieter"),
        ("deployer", "Betreiber"),
        ("high-risk", "Hochrisiko"),
        ("serious incident", "schwerwiegender Vorfall"),
        ("human oversight", "menschliche Aufsicht"),
        ("risk management system", "Risikomanagementsystem"),
        ("technical documentation", "technische Dokumentation"),
        ("accuracy, robustness and cybersecurity", "Genauigkeit, Robustheit und Cybersicherheit")
    ]

    en_full = " ".join(d["text"].lower() for d in corpus["en"])
    de_full = " ".join(d["text"].lower() for d in corpus["de"])

    for en_term, de_term in term_pairs:
        assert en_term.lower() in en_full, f"English term '{en_term}' missing from corpus"
        assert de_term.lower() in de_full, f"German term '{de_term}' missing from corpus"
