"""Prompt Injection Detection and Adversarial Guardrails (P6.8 & P6.12).

Detects adversarial prompt injections, role-play escapes, system prompt extraction,
privilege escalation attempts, malicious tool manipulation patterns, and
indirect prompt injections embedded inside retrieved documents, including
obfuscated, unicode homoglyph, zero-width, URL-encoded, HTML-encoded, and multi-chunk attacks.
"""

import re
import html
import base64
import urllib.parse
from typing import Tuple, Optional, Dict, Any, List
from pydantic import BaseModel

class PromptGuardResult(BaseModel):
    is_safe: bool
    risk_category: Optional[str] = None
    severity: str = "none"  # none, low, medium, high, critical
    details: Optional[str] = None
    sanitized_text: str

class PromptGuard:
    """Security guardrail inspecting user queries, tool inputs, and retrieved documents."""

    # Cyrillic and Greek homoglyphs mapped to ASCII equivalents
    HOMOGLYPH_MAP = {
        'а': 'a', 'с': 'c', 'е': 'e', 'о': 'o', 'р': 'p', 'ѕ': 's', 'х': 'x', 'у': 'y', 'і': 'i', 'ј': 'j',
        'А': 'A', 'В': 'B', 'С': 'C', 'Е': 'E', 'Н': 'H', 'І': 'I', 'Ј': 'J', 'К': 'K', 'М': 'M', 'О': 'O',
        'Р': 'P', 'Т': 'T', 'Х': 'X', 'Ү': 'Y',
        'α': 'a', 'ο': 'o', 'ρ': 'p', 'ν': 'v'
    }

    # Zero-width and invisible control characters
    ZERO_WIDTH_PATTERN = re.compile(r"[\u200b\u200c\u200d\ufeff\u200e\u200f\u00ad\u2060\u200a]")

    # Explicit attack heuristic signatures for user input
    INJECTION_PATTERNS = [
        # Instruction override (English)
        (r"(?i)\b(?:ignore|disregard|forget|override|bypass|stop\s+following)\s+(?:all\s+)?(?:previous\s+|prior\s+|above\s+|system\s+)?(?:instructions|rules|prompts|directions|guidelines|filters?|safety)", "INSTRUCTION_OVERRIDE", "critical"),
        (r"(?i)\boverride\s+instruction(?:\s+set)?\b", "INSTRUCTION_OVERRIDE", "critical"),
        # Instruction override (German)
        (r"(?i)\b(?:ignoriere|vergiss|uebergehe|missachte)\s+(?:alle\s+)?(?:vorherigen\s+|bisherigen\s+|obigen\s+)?(?:anweisungen|regeln|befehle|richtlinien|sicherheitsrichtlinien)", "INSTRUCTION_OVERRIDE_DE", "critical"),
        # Persona switch & jailbreak
        (r"(?i)\b(?:you\s+are\s+now|act\s+as|pretend\s+to\s+be)\s+(?:unrestricted|dan|developer\s+mode|chaos|jailbreak|root)", "JAILBREAK_PERSONA", "high"),
        (r"(?i)\b(?:do\s+anything\s+now|jailbreak\s+prompt|unfiltered\s+mode)\b", "JAILBREAK_PERSONA", "high"),
        # System prompt leakage & credential dumping
        (r"(?i)\b(?:print|show|repeat|display|output|dump)\s+(?:the\s+)?(?:system\s+prompt|initial\s+instructions|core\s+rules|developer\s+prompt|developer\s+instructions)", "SYSTEM_PROMPT_LEAK", "high"),
        (r"(?i)\b(?:what\s+is\s+your\s+system\s+prompt|reveal\s+(?:your\s+)?instructions|repeat\s+everything\s+above)\b", "SYSTEM_PROMPT_LEAK", "high"),
        (r"(?i)\b(?:zeige|wiederhole|drucke)\s+(?:den\s+)?(?:system-prompt|systemprompt|ursprüngliche\s+anweisungen)", "SYSTEM_PROMPT_LEAK_DE", "high"),
        (r"(?i)\b(?:was\s+ist\s+dein\s+systemprompt|gib\s+deine\s+anweisungen\s+aus|wiederhole\s+alles\s+obige)\b", "SYSTEM_PROMPT_LEAK_DE", "high"),
        (r"(?i)\b(?:display|dump|print|reveal|show|expose)\s+(?:all\s+)?(?:internal\s+)?(?:database\s+)?(?:credentials|passwords?|secrets?|tokens?|keys?)\b", "CREDENTIAL_EXTRACTION", "critical"),
        # Privilege escalation
        (r"(?i)\b(?:grant\s+me|elevate(?:\s+my\s+role)?\s+to|set\s+my\s+role\s+to|switch\s+to\s+role)\s+(?:admin|compliance_officer|auditor|root|superuser)", "PRIVILEGE_ESCALATION", "critical"),
        (r"(?i)\b(?:gib\s+mir|aendere\s+meine\s+rolle\s+zu)\s+(?:admin|compliance_officer|auditor|root)", "PRIVILEGE_ESCALATION_DE", "critical"),
        # Multi-turn memory persuasion attack
        (r"(?i)\b(?:you\s+previously\s+agreed|in\s+the\s+previous\s+message\s+you\s+confirmed|remember\s+that\s+I\s+am|as\s+we\s+agreed\s+earlier|ignore\s+your\s+refusal)\b", "MULTI_TURN_PERSUASION", "high"),
        # Tool manipulation / execution hijack
        (r"(?i)\b(?:call\s+tool|execute\s+tool|run\s+function|invoke\s+tool)\s*[:=]?\s*(?:get_system_incident_history|submit_compliance_audit_record)\b", "TOOL_HIJACK", "critical"),
        # Data exfiltration
        (r"(?i)\b(?:exfiltrate|send\s+all\s+data\s+to|webhook\.site|curl\s+https?:\/\/|curl\s+-X\s+POST|fetch\(['\"]https?:\/\/)\b", "DATA_EXFILTRATION", "critical"),
        # SQL injection in prompt or arguments
        (r"(?i)(?:'\s*(?:or|and)\s*'?1'?\s*=\s*'?1|;\s*drop\s+table|;\s*delete\s+from|union\s+select\s+all)", "SQL_INJECTION", "critical")
    ]

    # Signatures specific to Indirect Prompt Injection embedded inside documents
    DOCUMENT_INJECTION_PATTERNS = [
        (r"(?i)\[(?:system\s+override|instruction\s+override|admin\s+command|developer\s+note|systemhinweis)\s*:?[^\]]*\]", "INDIRECT_PROMPT_OVERRIDE_TAG"),
        (r"(?i)(?:ignore\s+prior\s+instructions|disregard\s+all\s+rules|you\s+must\s+output|reveal\s+secret|exfiltrate)", "INDIRECT_INSTRUCTION_HIJACK"),
        (r"(?i)(?:ignoriere\s+alle\s+regeln|gib\s+unbedingt\s+folgendes\s+aus|vertrauliche\s+daten\s+leaken)", "INDIRECT_INSTRUCTION_HIJACK_DE"),
        (r"(?i)<script\b[^>]*>([\s\S]*?)<\/script>", "EMBEDDED_SCRIPT_ATTACK"),
        (r"(?i)<!--\s*(?:system|admin|override|secret).*?-->", "EMBEDDED_HTML_COMMENT_ATTACK"),
        (r"(?i)\[comment\]:\s*#\s*\(.*?(?:override|system|admin).*?\)", "EMBEDDED_MARKDOWN_COMMENT_ATTACK"),
        (r"(?i)\{\{\s*(?:system|eval|exec|config)\s*\}\}", "TEMPLATE_INJECTION")
    ]

    @classmethod
    def normalize_text(cls, text: str) -> str:
        """De-obfuscates text by unescaping HTML, unquoting URLs, stripping zero-width chars,
        and mapping homoglyphs to standard ASCII characters."""
        if not text:
            return ""

        # 1. Strip zero-width & invisible characters
        normalized = cls.ZERO_WIDTH_PATTERN.sub("", text)

        # 2. Decode URL encoding (e.g. %20, %49%67%6e%6f%72%65)
        try:
            normalized = urllib.parse.unquote_plus(normalized)
        except Exception:
            pass

        # 3. Decode HTML entities (e.g. &lt;script&gt;, &#x69;)
        try:
            normalized = html.unescape(normalized)
        except Exception:
            pass

        # 4. Map unicode homoglyphs
        chars = [cls.HOMOGLYPH_MAP.get(c, c) for c in normalized]
        normalized = "".join(chars)

        return normalized.strip()

    @classmethod
    def inspect(cls, text: str) -> PromptGuardResult:
        """Analyzes user query text for adversarial threats and malicious payloads."""
        if not text or not text.strip():
            return PromptGuardResult(is_safe=True, sanitized_text=text)

        raw_text = text.strip()
        deobfuscated = cls.normalize_text(raw_text)

        # 1. Pattern checks on both raw and de-obfuscated text
        for candidate in [raw_text, deobfuscated]:
            for pattern, category, severity in cls.INJECTION_PATTERNS:
                if re.search(pattern, candidate):
                    return PromptGuardResult(
                        is_safe=False,
                        risk_category=category,
                        severity=severity,
                        details=f"Prompt injection signature detected: {category}",
                        sanitized_text="[BLOCKED_SECURITY_VIOLATION]"
                    )

        # 2. Check for suspicious base64 payloads
        base64_candidates = re.findall(r"\b[A-Za-z0-9+/]{20,}={0,2}\b", deobfuscated)
        
        # Also check for base64 with internal spaces or command prefix
        b64_prefix_match = re.search(r"(?i)(?:decode|run|execute|payload)\s*[:=]?\s*([A-Za-z0-9+/= ]{16,})", deobfuscated)
        if b64_prefix_match:
            cleaned_b64 = re.sub(r"\s+", "", b64_prefix_match.group(1))
            if len(cleaned_b64) >= 16:
                base64_candidates.append(cleaned_b64)
        for cand in base64_candidates:
            try:
                decoded = base64.b64decode(cand).decode("utf-8", errors="ignore")
                decoded_norm = cls.normalize_text(decoded)
                for pattern, category, severity in cls.INJECTION_PATTERNS:
                    if re.search(pattern, decoded_norm):
                        return PromptGuardResult(
                            is_safe=False,
                            risk_category="ENCODED_INJECTION",
                            severity="critical",
                            details=f"Obfuscated base64 injection payload detected: {category}",
                            sanitized_text="[BLOCKED_SECURITY_VIOLATION]"
                        )
            except Exception:
                pass

        return PromptGuardResult(
            is_safe=True,
            risk_category=None,
            severity="none",
            details="Input passed security inspection.",
            sanitized_text=raw_text
        )

    @classmethod
    def inspect_document_chunk(cls, text: str) -> PromptGuardResult:
        """Inspects a retrieved text chunk for indirect / secondary prompt injection."""
        if not text or not text.strip():
            return PromptGuardResult(is_safe=True, sanitized_text=text)

        sanitized = text
        deobfuscated = cls.normalize_text(text)
        detected_threats = []

        # 1. Check document-specific hijack patterns first (enclosing tags like [...], <!--...-->, <script>)
        for pattern, category in cls.DOCUMENT_INJECTION_PATTERNS:
            if re.search(pattern, sanitized):
                detected_threats.append(category)
                sanitized = re.sub(pattern, "[REDACTED_INDIRECT_INJECTION]", sanitized)

        # 2. Check remaining primary injection patterns
        for pattern, category, severity in cls.INJECTION_PATTERNS:
            if re.search(pattern, sanitized):
                detected_threats.append(f"DOCUMENT_{category}")
                sanitized = re.sub(pattern, "[REDACTED_INDIRECT_INJECTION]", sanitized)

        if detected_threats:
            return PromptGuardResult(
                is_safe=False,
                risk_category=detected_threats[0],
                severity="high",
                details=f"Indirect prompt injection neutralized in document chunk: {', '.join(detected_threats)}",
                sanitized_text=sanitized
            )

        return PromptGuardResult(
            is_safe=True,
            risk_category=None,
            severity="none",
            details="Document chunk verified safe.",
            sanitized_text=text
        )

    @classmethod
    def inspect_multi_chunk_distribution(
        cls,
        chunks: List[Dict[str, Any]]
    ) -> Tuple[bool, Optional[str]]:
        """Inspects boundary text across consecutive retrieved chunks to detect split attacks."""
        if len(chunks) < 2:
            return True, None

        for i in range(len(chunks) - 1):
            tail = chunks[i].get("text", "")[-150:]
            head = chunks[i + 1].get("text", "")[:150]
            joined = f"{tail} {head}"
            res = cls.inspect(joined)
            if not res.is_safe:
                return False, f"Split-chunk distributed injection detected across chunks {i} and {i+1}: {res.details}"

        return True, None

    @classmethod
    def sanitize_retrieved_chunks(
        cls,
        chunks: List[Dict[str, Any]]
    ) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
        """Scans and sanitizes all retrieved chunks before synthesis.
        
        Returns (clean_chunks, quarantined_threat_chunks).
        """
        clean_chunks = []
        quarantined = []

        for c in chunks:
            raw_text = c.get("text", "")
            guard_res = cls.inspect_document_chunk(raw_text)

            chunk_copy = dict(c)
            if not guard_res.is_safe:
                chunk_copy["text"] = guard_res.sanitized_text
                chunk_copy["context_header"] = f"{c.get('context_header', '')} [SECURITY NOTICE: Indirect injection neutralized]"
                chunk_copy["has_indirect_injection"] = True
                chunk_copy["injection_details"] = guard_res.details
                quarantined.append(chunk_copy)
            else:
                chunk_copy["has_indirect_injection"] = False

            clean_chunks.append(chunk_copy)

        # Check multi-chunk distribution
        is_safe_multi, multi_threat = cls.inspect_multi_chunk_distribution(clean_chunks)
        if not is_safe_multi:
            for c in clean_chunks:
                c["text"] = "[REDACTED_SPLIT_CHUNK_INJECTION]"
                c["has_indirect_injection"] = True
                c["injection_details"] = multi_threat
                quarantined.append(c)

        return clean_chunks, quarantined

# Global singleton
prompt_guard = PromptGuard()
