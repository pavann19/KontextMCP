"""Citation quality, precision, and hallucination abstention tests (P1 - Section 7.4)."""

import pytest
from app.agent.graph import run_agent_query
from app.agent.llm import GroundedLegalSynthesizer

def test_statutory_citation_accuracy_article_5():
    state = run_agent_query("What biometric practices are banned under Article 5?")
    citations = state.citations
    assert len(citations) > 0
    # Top citation must cite Article 5
    assert "Article 5" in citations[0]["article_id"] or "Artikel 5" in citations[0]["article_id"]
    # Final answer must cite Article 5
    assert "Article 5" in state.final_answer or "Artikel 5" in state.final_answer

def test_cross_lingual_citation_preserves_language_intent():
    # German query -> German citations
    state_de = run_agent_query("Welche Pflichten gelten für Hochrisiko-KI nach Artikel 9?", session_id="test_cite_de")
    assert state_de.target_language == "de"
    assert "Artikel 9" in state_de.final_answer or "Risikomanagementsystem" in state_de.final_answer

def test_unsupported_citation_abstention():
    # Asks about non-existent Article 150
    state_fake = run_agent_query("What does Article 150 state regarding quantum telepathy?")
    # Must explicitly state Article 150 does not exist rather than fabricating a citation
    assert "113" in state_fake.final_answer or "does not exist" in state_fake.final_answer.lower() or "nicht existiert" in state_fake.final_answer.lower() or "keine" in state_fake.final_answer.lower()

