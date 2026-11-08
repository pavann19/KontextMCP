"""Fidelity to a local source is distinct from relevance and legal correctness."""
import hashlib
import pytest
from app.core.grounding import citation, verify_excerpts
from app.agent.graph import run_agent_query
from app.core.pii_guard import pii_guard

SOURCE = {"chunk_id": "source-one", "doc_id": "doc-one", "article_id": "Article 9",
          "title": "Risk management", "language": "en", "text": "Risk management shall be continuous."}
# Deliberately constructed independently of the renderer.
ANSWER = ("### Excerpts from the local corpus (Regulation (EU) 2024/1689)\n\n"
          "[[source:source-one]]\n**Article 9 — Risk management**\n\nRisk management shall be continuous.\n[[/source]]\n\n"
          "These retrieved excerpts require independent legal review.")


def test_exact_source_and_metadata_are_required():
    claims = [citation(SOURCE)]
    assert verify_excerpts(ANSWER, claims, {"source-one": SOURCE}, "en")[0]
    for forged in (ANSWER.replace("continuous", "optional"), ANSWER + "\nA fine of EUR 100 applies.",
                   ANSWER.replace("source-one", "invented"), ANSWER.replace("Article 9", "Article 99")):
        assert not verify_excerpts(forged, claims, {"source-one": SOURCE}, "en")[0]
    assert not verify_excerpts(ANSWER, [{**claims[0], "source_text_sha256": "0"*64}], {"source-one": SOURCE}, "en")[0]
    assert not verify_excerpts(ANSWER, [], {"source-one": SOURCE}, "en")[0]


def test_masked_excerpt_is_checked_against_same_source():
    source = {**SOURCE, "text": "Contact private@example.com."}
    answer = pii_guard.mask(ANSWER.replace(SOURCE["text"], source["text"])).clean_text
    assert verify_excerpts(answer, [citation(source)], {"source-one": source}, "en",
                           sanitize=lambda text: pii_guard.mask(text).clean_text)[0]


def test_agent_returns_resolvable_sources():
    from app.agent.nodes import get_retrieval_engine
    from app.agent import nodes
    result = run_agent_query("What does Article 9 require?")
    assert result.grounding_status == "SOURCE_VERIFIED", result.grounding_error
    sources = {c.chunk_id: c for c in nodes._cached_chunks}
    for item in result.citations:
        source = sources[item["chunk_id"]]
        assert item["doc_id"] == source.doc_id
        assert item["source_text_sha256"] == hashlib.sha256(source.text.encode()).hexdigest()


@pytest.mark.parametrize("query", ["What does Article 112 require?", "What does Art.112 require?", "What does Annex IX state?", "What does Article -1 state?"])
def test_absent_provision_does_not_cite_unrelated_chunks(query):
    result = run_agent_query(query)
    assert result.grounding_status == "NOT_APPLICABLE"
    assert result.citations == []
    assert "not available" in result.final_answer


def test_runtime_guard_rejects_changed_answer(monkeypatch):
    from app.agent import nodes
    original = nodes.GroundedLegalSynthesizer.synthesize
    def forged(*args, **kwargs):
        return original(*args, **kwargs) + "\nUncited legal conclusion."
    monkeypatch.setattr(nodes.GroundedLegalSynthesizer, "synthesize", forged)
    result = run_agent_query("What does Article 9 require?")
    assert result.grounding_status == "REJECTED"
    assert result.citations == []
    assert "Uncited legal conclusion" not in result.final_answer


def test_explicit_english_language_is_preserved():
    result = run_agent_query("Welche Pflichten gelten nach Artikel 9?", target_language="en")
    assert result.grounding_status == "SOURCE_VERIFIED"
    assert result.final_answer.startswith("### Excerpts")
