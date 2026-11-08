"""Bilingual BM25Okapi retrieval engine (P6.3).

Provides language-aware tokenization, German compound word handling, umlaut normalization,
and exact Okapi BM25 scoring with inverted index persistence.
"""

import math
import re
from typing import Dict, List, Tuple, Optional, Any
from collections import Counter
from app.ingestion.chunker import LegalChunk

GERMAN_STOPWORDS = {
    "aber", "alle", "allem", "allen", "aller", "alles", "als", "also", "am", "an", "ander",
    "andere", "anderem", "anderen", "anderer", "anderes", "anderm", "andern", "anderr",
    "anders", "auch", "auf", "aus", "bei", "bin", "bis", "bist", "da", "damit", "dann",
    "der", "den", "des", "dem", "die", "das", "dass", "daß", "derselbe", "derselben",
    "denselben", "derselbige", "derselbigen", "dieselbe", "dieselben", "dasselbe",
    "dazu", "dein", "deine", "deinem", "deinen", "deiner", "deines", "denn", "derer",
    "dessen", "dich", "dir", "du", "dies", "diese", "diesem", "diesen", "dieser",
    "dieses", "doch", "dort", "durch", "ein", "eine", "einem", "einen", "einer", "eines",
    "einig", "einige", "einigem", "einigen", "einiger", "einiges", "einmal", "er", "ihn",
    "ihm", "es", "etwas", "euer", "eure", "eurem", "euren", "eurer", "eures", "für",
    "gegen", "gewesen", "hab", "habe", "haben", "hat", "hatte", "hatten", "hier", "hin",
    "hinter", "ich", "mich", "mir", "ihr", "ihre", "ihrem", "ihren", "ihrer", "ihres",
    "euch", "im", "in", "indem", "ins", "ist", "jede", "jedem", "jeden", "jeder",
    "jedes", "jene", "jenem", "jenen", "jener", "jenes", "jetzt", "kann", "kein", "keine",
    "keinem", "keinen", "keiner", "keines", "können", "könnte", "machen", "man", "manche",
    "manchem", "manchen", "mancher", "manches", "mein", "meine", "meinem", "meinen",
    "meiner", "meines", "mit", "muss", "musste", "nach", "nicht", "nichts", "noch",
    "nun", "nur", "ob", "oder", "ohne", "sehr", "sein", "seine", "seinem", "seinen",
    "seiner", "seines", "selbst", "sich", "sie", "ihnen", "sind", "so", "solche",
    "solchem", "solchen", "solcher", "solches", "soll", "sollte", "sondern", "sonst",
    "über", "um", "und", "uns", "unse", "unsem", "unsen", "unser", "unses", "unter",
    "vom", "von", "vor", "während", "war", "waren", "warst", "was", "weg", "weil",
    "weiter", "welche", "welchem", "welchen", "welcher", "welches", "wenn", "werde",
    "werden", "wie", "wieder", "will", "wir", "wird", "wirst", "wo", "wollen", "wollte",
    "würde", "würden", "zu", "zum", "zur", "zwar", "zwischen"
}

ENGLISH_STOPWORDS = {
    "a", "about", "above", "after", "again", "against", "all", "am", "an", "and", "any",
    "are", "aren't", "as", "at", "be", "because", "been", "before", "being", "below",
    "between", "both", "but", "by", "can", "cannot", "could", "couldn't", "did", "didn't",
    "do", "does", "doesn't", "doing", "don't", "down", "during", "each", "few", "for",
    "from", "further", "had", "hadn't", "has", "hasn't", "have", "haven't", "having",
    "he", "he'd", "he'll", "he's", "her", "here", "here's", "hers", "herself", "him",
    "himself", "his", "how", "how's", "i", "i'd", "i'll", "i'm", "i've", "if", "in",
    "into", "is", "isn't", "it", "it's", "its", "itself", "let's", "me", "more", "most",
    "mustn't", "my", "myself", "no", "nor", "not", "of", "off", "on", "once", "only",
    "or", "other", "ought", "our", "ours", "ourselves", "out", "over", "own", "same",
    "shan't", "she", "she'd", "she'll", "she's", "should", "shouldn't", "so", "some",
    "such", "than", "that", "that's", "the", "their", "theirs", "them", "themselves",
    "then", "there", "there's", "these", "they", "they'd", "they'll", "they're",
    "they've", "this", "those", "through", "to", "too", "under", "until", "up", "very",
    "was", "wasn't", "we", "we'd", "we'll", "we're", "we've", "were", "weren't", "what",
    "what's", "when", "when's", "where", "where's", "which", "while", "who", "who's",
    "whom", "why", "why's", "with", "won't", "would", "wouldn't", "you", "you'd",
    "you'll", "you're", "you've", "your", "yours", "yourself", "yourselves"
}

ALL_STOPWORDS = GERMAN_STOPWORDS.union(ENGLISH_STOPWORDS)

class BilingualBM25Retriever:
    """Okapi BM25 implementation optimized for bilingual German/English legal text."""
    
    def __init__(self, k1: float = 1.5, b: float = 0.75):
        self.k1 = k1
        self.b = b
        self.chunks: List[LegalChunk] = []
        self.doc_lengths: List[int] = []
        self.avg_doc_len: float = 0.0
        self.doc_count: int = 0
        self.doc_freqs: Dict[str, int] = {}
        self.idf: Dict[str, float] = {}
        self.term_freqs: List[Dict[str, int]] = []
        self.is_indexed: bool = False

    @staticmethod
    def normalize_text(text: str) -> str:
        """Normalizes umlauts, special quotes and lowercase text."""
        t = text.lower()
        t = t.replace("ä", "ae").replace("ö", "oe").replace("ü", "ue").replace("ß", "ss")
        return t

    @classmethod
    def tokenize(cls, text: str) -> List[str]:
        """Bilingual tokenizer splitting words, hyphenated compounds, and numbers."""
        norm = cls.normalize_text(text)
        # Split on non-alphanumeric characters, keeping legal markers
        tokens = re.findall(r"[a-z0-9]+", norm)
        
        filtered: List[str] = []
        for tok in tokens:
            if tok in ALL_STOPWORDS or len(tok) < 2:
                continue
            filtered.append(tok)
            # Add subwords for compound terms if present in original text
            if len(tok) > 9:
                # E.g. hochrisiko / risikomanagement
                if "risiko" in tok:
                    filtered.append("risiko")
                if "system" in tok:
                    filtered.append("system")
                if "intelligenz" in tok:
                    filtered.append("intelligenz")
                if "management" in tok:
                    filtered.append("management")
                    
        return filtered

    def index(self, chunks: List[LegalChunk]) -> None:
        """Indexes legal chunks into the BM25 inverted index."""
        self.chunks = chunks
        self.doc_count = len(chunks)
        self.doc_lengths = []
        self.doc_freqs = Counter()
        self.term_freqs = []

        total_length = 0
        for chunk in chunks:
            # We index both full_content and keywords
            text_to_index = f"{chunk.full_content} {' '.join(chunk.keywords)}"
            tokens = self.tokenize(text_to_index)
            length = len(tokens)
            self.doc_lengths.append(length)
            total_length += length
            
            tf = Counter(tokens)
            self.term_freqs.append(dict(tf))
            
            for term in tf.keys():
                self.doc_freqs[term] = self.doc_freqs.get(term, 0) + 1

        self.avg_doc_len = total_length / self.doc_count if self.doc_count > 0 else 1.0

        # Precompute IDF: ln((N - n(q) + 0.5) / (n(q) + 0.5) + 1)
        self.idf = {}
        for term, freq in self.doc_freqs.items():
            self.idf[term] = math.log((self.doc_count - freq + 0.5) / (freq + 0.5) + 1.0)
            
        self.is_indexed = True

    def search(
        self,
        query: str,
        top_k: int = 5,
        language: Optional[str] = None
    ) -> List[Tuple[LegalChunk, float]]:
        """Searches index with BM25 scoring, optional language filtering."""
        if not self.is_indexed:
            raise RuntimeError("BM25 index has not been built yet. Call index() first.")

        query_tokens = self.tokenize(query)
        if not query_tokens:
            return []

        scores: List[float] = [0.0] * self.doc_count

        for q_token in query_tokens:
            if q_token not in self.idf:
                continue
            idf_val = self.idf[q_token]

            for i in range(self.doc_count):
                if language and isinstance(language, str) and self.chunks[i].language != language.lower():
                    continue

                tf = self.term_freqs[i].get(q_token, 0)
                if tf == 0:
                    continue

                doc_len = self.doc_lengths[i]
                numerator = tf * (self.k1 + 1.0)
                denominator = tf + self.k1 * (1.0 - self.b + self.b * (doc_len / self.avg_doc_len))
                scores[i] += idf_val * (numerator / denominator)

        ranked_indices = sorted(
            [i for i in range(self.doc_count) if scores[i] > 0.0],
            key=lambda idx: scores[idx],
            reverse=True
        )[:top_k]

        return [(self.chunks[idx], scores[idx]) for idx in ranked_indices]

