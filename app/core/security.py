"""Resolve identities exclusively from externally provisioned API credentials."""

import hmac
from typing import Optional
from fastapi import Header, HTTPException
from app.config import settings
from app.mcp.permissions import UserContext, ROLE_CLEARANCE_MAP


def resolve_user_context(
    x_api_key: Optional[str] = Header(None, alias="X-API-Key"),
    x_user_role: Optional[str] = Header(None, alias="X-User-Role"),
    x_user_id: Optional[str] = Header(None, alias="X-User-Id"),
    x_user_department: Optional[str] = Header(None, alias="X-User-Department")
) -> UserContext:
    # Direct Python callers may leave FastAPI Header defaults unresolved.
    key = x_api_key if isinstance(x_api_key, str) else None
    if key:
        for registered, identity in settings.API_KEYS.items():
            if hmac.compare_digest(key.encode(), registered.encode()):
                role = identity.get("role", "")
                if (role not in ROLE_CLEARANCE_MAP or not identity.get("username")
                        or not identity.get("department")):
                    raise HTTPException(401, "Invalid configured identity.")
                return UserContext(
                    username=identity["username"], role=role,
                    department=identity["department"],
                    clearance_level=ROLE_CLEARANCE_MAP[role]
                )
        raise HTTPException(401, "AUTHENTICATION_FAILED: Invalid API key.")
    if isinstance(x_user_role, str) and x_user_role.lower() != "public_viewer":
        raise HTTPException(401, "AUTHENTICATION_REQUIRED: Privileged roles require an API key.")
    return UserContext.public_default()
