"""Exact local-source fidelity checks, not semantic entailment or legal validation."""
import hashlib
import re
from typing import Callable, Mapping

BLOCK = re.compile(r"\[\[source:([^\]\r\n]+)\]\]\n(.*?)\n\[\[/source\]\]", re.DOTALL)


def citation(chunk):
    return {"chunk_id": chunk["chunk_id"], "doc_id": chunk["doc_id"],
            "article_id": chunk["article_id"], "title": chunk["title"], "language": chunk["language"],
            "source_text_sha256": hashlib.sha256(chunk["text"].encode("utf-8")).hexdigest()}


def excerpt_body(chunk):
    return f"**{chunk['article_id']} — {chunk['title']}**\n\n{chunk['text']}"


def frame(language):
    if language == "de":
        return ("### Auszüge aus dem lokalen Korpus (Regulation (EU) 2024/1689)",
                "Eine eigenständige rechtliche Prüfung bleibt erforderlich.")
    return ("### Excerpts from the local corpus (Regulation (EU) 2024/1689)",
            "These retrieved excerpts require independent legal review.")


def render_excerpts(chunks, language):
    prefix, suffix = frame(language)
    blocks = [f"[[source:{c['chunk_id']}]]\n{excerpt_body(c)}\n[[/source]]" for c in chunks[:3]]
    return "\n\n".join([prefix, *blocks, suffix])


def verify_excerpts(answer: str, citations: list, trusted: Mapping, language: str,
                    sanitize: Callable[[str], str] = lambda value: value):
    """Reject changed text, invented sources, metadata substitution and added prose."""
    blocks = list(BLOCK.finditer(answer))
    if not 1 <= len(blocks) <= 3 or len(citations) != len(blocks):
        return False, "Missing source blocks or citation count mismatch."
    ids = [match.group(1) for match in blocks]
    if len(set(ids)) != len(ids):
        return False, "Duplicate source IDs."
    for match, claimed in zip(blocks, citations):
        source = trusted.get(match.group(1))
        if source is None:
            return False, "Unknown local source."
        if claimed != citation(source):
            return False, "Citation metadata or source hash differs from local corpus."
        if match.group(2) != sanitize(excerpt_body(source)):
            return False, "Excerpt differs from local source."
    prefix, suffix = frame(language)
    framed = "\n\n".join([sanitize(prefix), *(m.group(0) for m in blocks), sanitize(suffix)])
    if answer != framed:
        return False, "Answer contains additional or changed prose."
    return True, None


def requested_references(query):
    """Only explicit identifiers; no attempt to infer legal relevance."""
    result = set()
    for kind, token in re.findall(r"\b(article|artikel|art\.?|annex|anhang)\s*(-?\d+|[ivxlcdm]+)\b", query.lower()):
        family = "article" if kind.startswith("art") else "annex"
        roman = {"i":1, "v":5, "x":10, "l":50, "c":100, "d":500, "m":1000}
        if token.lstrip("-").isdigit():
            value = int(token)
        elif family == "annex":
            value = sum(-roman[c] if i+1 < len(token) and roman[c] < roman[token[i+1]] else roman[c]
                        for i,c in enumerate(token))
        else:
            continue
        result.add((family, value))
    return result
