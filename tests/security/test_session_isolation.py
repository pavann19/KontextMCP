"""Session isolation, pseudonym vault lifecycle, and state contamination tests (P0 - Section 4.3)."""

import pytest
from app.core.pii_guard import pii_guard
from app.core.security import resolve_user_context
from fastapi import HTTPException

def test_session_pseudonym_vault_isolation():
    # User 1 session
    sess_1 = "session_user_alice"
    text_1 = "Contact Dr. Schmidt at schmidt@enterprise.de regarding Article 9."
    rep_1 = pii_guard.pseudonymize(text_1, session_id=sess_1)
    assert "<EMAIL_1>" in rep_1.clean_text

    # User 2 session with different data
    sess_2 = "session_user_bob"
    text_2 = "Contact bob@auditor.org regarding Article 10."
    rep_2 = pii_guard.pseudonymize(text_2, session_id=sess_2)
    assert "<EMAIL_1>" in rep_2.clean_text

    # Depseudonymizing with User 2's session should NOT reveal User 1's email
    leak_check = pii_guard.depseudonymize("<EMAIL_1>", session_id=sess_2)
    assert leak_check == "bob@auditor.org"
    assert leak_check != "schmidt@enterprise.de"

def test_session_cleanup_prevents_memory_leak():
    sess = "temp_cleanup_session"
    pii_guard.pseudonymize("Email test@example.com", session_id=sess)
    assert sess in pii_guard._pseudonym_vaults

    # Run cleanup
    pii_guard.cleanup_session(sess)
    assert sess not in pii_guard._pseudonym_vaults

    # Attempting to depseudonymize after cleanup leaves placeholder untouched
    assert pii_guard.depseudonymize("<EMAIL_1>", session_id=sess) == "<EMAIL_1>"

def test_invalid_api_key_raises_401():
    with pytest.raises(HTTPException) as exc_info:
        resolve_user_context(x_api_key="invalid_malicious_key_12345")
    assert exc_info.value.status_code == 401
    assert "AUTHENTICATION_FAILED" in exc_info.value.detail

def test_unauthenticated_request_defaults_to_public():
    ctx = resolve_user_context(x_api_key=None, x_user_role=None)
    assert ctx.username == "anonymous"
    assert ctx.role == "public_viewer"
    assert ctx.clearance_level == 1

