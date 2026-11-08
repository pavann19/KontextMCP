"""PII detection, anonymization, and privacy controls (P6.8).

Detects German and English Personally Identifiable Information (PII) including
emails, phone numbers, German Tax IDs, IBANs, IP addresses, credit cards, and names.
Supports masking, irreversible redaction, and reversible pseudonymization.
"""

import re
from typing import Dict, List, Tuple, Any, Optional
from pydantic import BaseModel, Field

class PIIMatch(BaseModel):
    entity_type: str
    original_value: str
    replacement_value: str
    start_pos: int
    end_pos: int

class PIIReport(BaseModel):
    has_pii: bool
    detected_count: int
    entity_breakdown: Dict[str, int]
    clean_text: str
    matches: List[PIIMatch] = Field(default_factory=list)

class PIIGuard:
    """Enterprise privacy engine with German & English pattern matching."""

    # Regex definitions
    PATTERNS = {
        "EMAIL": re.compile(
            r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b"
        ),
        "IBAN": re.compile(
            r"\b[A-Z]{2}\d{2}\s?(?:\d{4}\s?){3,6}\d{1,4}\b"
        ),
        "GERMAN_TAX_ID": re.compile(
            r"\b\d{2}\s?\d{3}\s?\d{3}\s?\d{3}\b"
        ),
        "PHONE": re.compile(
            r"(?:\+49|0049|0)\s*(?:\([0-9]+\)\s*)?[0-9]{2,5}(?:[\s/-]*[0-9]){4,9}\b"
        ),
        "IP_ADDRESS": re.compile(
            r"\b(?:[0-9]{1,3}\.){3}[0-9]{1,3}\b"
        ),
        "CREDIT_CARD": re.compile(
            r"\b(?:\d{4}[-\s]?){3}\d{4}\b"
        ),
        "PERSON_NAME": re.compile(
            r"\b(?:Herr|Frau|Dr\.|Prof\.|Mr\.|Mrs\.|Ms\.)\s+[A-Z][a-zäöüß]+(?:\s+[A-Z][a-zäöüß]+)*\b"
        )
    }

    def __init__(self):
        # Session storage for reversible pseudonymization: session_id -> {pseudonym: original}
        self._pseudonym_vaults: Dict[str, Dict[str, str]] = {}
        self._reverse_vaults: Dict[str, Dict[str, str]] = {}

    ZERO_WIDTH = re.compile(r"[\u200b\u200c\u200d\ufeff\u200e\u200f\u00ad]")

    def scan(self, text: str) -> List[Tuple[str, str, int, int]]:
        """Scans text for all PII entity occurrences, including zero-width obfuscated entities.
        
        Returns list of (entity_type, matched_string, start, end).
        """
        all_matches: List[Tuple[str, str, int, int]] = []
        has_zw = bool(self.ZERO_WIDTH.search(text))
        effective_text = self.ZERO_WIDTH.sub("", text) if has_zw else text

        for entity_type, pattern in self.PATTERNS.items():
            # Check original text
            for m in pattern.finditer(text):
                val = m.group()
                if entity_type == "GERMAN_TAX_ID":
                    digits = re.sub(r"\D", "", val)
                    if len(digits) != 11:
                        continue
                elif entity_type == "IBAN":
                    clean_iban = re.sub(r"\s+", "", val)
                    if len(clean_iban) < 15 or len(clean_iban) > 34:
                        continue
                elif entity_type == "PHONE":
                    digits = re.sub(r"\D", "", val)
                    if len(digits) < 7:
                        continue
                all_matches.append((entity_type, val, m.start(), m.end()))

            # If zero-width characters exist, check de-obfuscated text if not already matched
            if has_zw:
                for m in pattern.finditer(effective_text):
                    val = m.group()
                    if not any(val in ex[1] or ex[1] in val for ex in all_matches):
                        all_matches.append((entity_type, val, m.start(), m.end()))

        # Sort matches by start position in ascending order
        all_matches.sort(key=lambda x: x[2])
        return all_matches

    def mask(self, text: str) -> PIIReport:
        """Irreversible masking with typed redaction tokens (e.g. [REDACTED_EMAIL])."""
        matches = self.scan(text)
        if not matches:
            return PIIReport(
                has_pii=False,
                detected_count=0,
                entity_breakdown={},
                clean_text=text,
                matches=[]
            )

        breakdown: Dict[str, int] = {}
        result_chars: List[str] = []
        last_idx = 0
        recorded_matches: List[PIIMatch] = []

        for entity_type, raw_val, start, end in matches:
            if start < last_idx:
                continue  # Skip overlapping matches
            result_chars.append(text[last_idx:start])
            token = f"[REDACTED_{entity_type}]"
            result_chars.append(token)
            last_idx = end

            breakdown[entity_type] = breakdown.get(entity_type, 0) + 1
            recorded_matches.append(
                PIIMatch(
                    entity_type=entity_type,
                    original_value=raw_val,
                    replacement_value=token,
                    start_pos=start,
                    end_pos=end
                )
            )

        result_chars.append(text[last_idx:])
        clean_str = "".join(result_chars)

        return PIIReport(
            has_pii=True,
            detected_count=len(recorded_matches),
            entity_breakdown=breakdown,
            clean_text=clean_str,
            matches=recorded_matches
        )

    def pseudonymize(self, text: str, session_id: str = "default_session") -> PIIReport:
        """Reversible pseudonymization using session-scoped token IDs (e.g. <EMAIL_1>)."""
        if session_id not in self._pseudonym_vaults:
            self._pseudonym_vaults[session_id] = {}
            self._reverse_vaults[session_id] = {}

        vault = self._pseudonym_vaults[session_id]
        reverse_vault = self._reverse_vaults[session_id]

        matches = self.scan(text)
        if not matches:
            return PIIReport(
                has_pii=False,
                detected_count=0,
                entity_breakdown={},
                clean_text=text,
                matches=[]
            )

        breakdown: Dict[str, int] = {}
        result_chars: List[str] = []
        last_idx = 0
        recorded_matches: List[PIIMatch] = []
        counters: Dict[str, int] = {}

        for entity_type, raw_val, start, end in matches:
            if start < last_idx:
                continue
            result_chars.append(text[last_idx:start])

            # Check if this exact entity was already assigned a pseudonym in this session
            if raw_val in reverse_vault:
                pseudonym = reverse_vault[raw_val]
            else:
                idx = counters.get(entity_type, 1)
                counters[entity_type] = idx + 1
                pseudonym = f"<{entity_type}_{idx}>"
                vault[pseudonym] = raw_val
                reverse_vault[raw_val] = pseudonym

            result_chars.append(pseudonym)
            last_idx = end

            breakdown[entity_type] = breakdown.get(entity_type, 0) + 1
            recorded_matches.append(
                PIIMatch(
                    entity_type=entity_type,
                    original_value=raw_val,
                    replacement_value=pseudonym,
                    start_pos=start,
                    end_pos=end
                )
            )

        result_chars.append(text[last_idx:])
        return PIIReport(
            has_pii=True,
            detected_count=len(recorded_matches),
            entity_breakdown=breakdown,
            clean_text="".join(result_chars),
            matches=recorded_matches
        )

    def depseudonymize(self, text: str, session_id: str = "default_session") -> str:
        """Reconstructs original sensitive values from session pseudonym vault."""
        vault = self._pseudonym_vaults.get(session_id, {})
        if not vault:
            return text

        restored = text
        for pseudonym, original in vault.items():
            restored = restored.replace(pseudonym, original)
        return restored

    def cleanup_session(self, session_id: str) -> None:
        """Removes session pseudonym mappings to prevent cross-session contamination and memory leaks."""
        self._pseudonym_vaults.pop(session_id, None)
        self._reverse_vaults.pop(session_id, None)

    def cleanup_all(self) -> None:
        """Clears all session pseudonym vaults."""
        self._pseudonym_vaults.clear()
        self._reverse_vaults.clear()

    def scan_dict(self, data: Any, current_path: str = "") -> List[Tuple[str, str, str]]:
        """Recursively scans dictionaries, lists, or primitive values for PII.
        
        Returns list of (json_path, entity_type, raw_value).
        """
        findings: List[Tuple[str, str, str]] = []
        if isinstance(data, dict):
            for k, v in data.items():
                p = f"{current_path}.{k}" if current_path else k
                findings.extend(self.scan_dict(v, p))
        elif isinstance(data, list):
            for i, item in enumerate(data):
                p = f"{current_path}[{i}]"
                findings.extend(self.scan_dict(item, p))
        elif isinstance(data, str):
            matches = self.scan(data)
            for entity_type, raw_val, _, _ in matches:
                findings.append((current_path, entity_type, raw_val))
        return findings

# Global singleton instance
pii_guard = PIIGuard()

