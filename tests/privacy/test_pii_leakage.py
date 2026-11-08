"""PII leakage, zero-width obfuscation, and dictionary scanning privacy tests (P2 - Section 10)."""

import pytest
from app.core.pii_guard import pii_guard
from app.core.audit import AuditLogger

def test_zero_width_obfuscated_email_detection():
    # Email with zero-width spaces (\u200b)
    obfuscated_email = "c\u200bo\u200bm\u200bp\u200bl\u200bi\u200ba\u200bn\u200bc\u200be@enterprise.de"
    report = pii_guard.mask(f"Please reach out to {obfuscated_email} regarding Article 14.")
    assert report.has_pii is True
    assert "EMAIL" in report.entity_breakdown

def test_scan_nested_dictionary_for_pii():
    nested_payload = {
        "system": "SYS-HR-001",
        "operator": {
            "name": "Dr. Schmidt",
            "contact": {
                "email": "dr.schmidt@berlin-ai.de",
                "phone": "+49 30 1234567"
            }
        },
        "tax_data": {
            "steuernummer": "12 345 678 901"
        }
    }
    findings = pii_guard.scan_dict(nested_payload)
    assert len(findings) >= 3
    found_types = {f[1] for f in findings}
    assert "EMAIL" in found_types
    assert "PHONE" in found_types
    assert "GERMAN_TAX_ID" in found_types

def test_audit_logger_redacts_credentials():
    entry = AuditLogger.log_event(
        user_id="alice",
        user_role="compliance_officer",
        action="TEST_CREDENTIAL_MASKING",
        status="EXECUTED",
        details="Attempted access with api_key='sk-prod-secret-999988887777' and password='SuperSecretPassword123'"
    )
    assert "sk-prod-secret" not in entry.details
    assert "SuperSecretPassword123" not in entry.details
    assert "[REDACTED_CREDENTIAL]" in entry.details

