import os
import uuid
from typing import Optional

from fastapi import Header, HTTPException


def resolve_session_token() -> str:
    """Return the configured session token or a one-shot dev fallback."""
    token = os.environ.get("GENOMA_SESSION_TOKEN")
    if token:
        return token
    # Dev fallback — regenerated every time the module is loaded.
    return f"genoma_{uuid.uuid4().hex}"


_SESSION_TOKEN: str = resolve_session_token()


async def require_session_token(
    x_hermes_session_token: Optional[str] = Header(None),
) -> str:
    """FastAPI dependency that validates the X-Hermes-Session-Token header."""
    if not x_hermes_session_token:
        raise HTTPException(status_code=401, detail="Missing X-Hermes-Session-Token")
    return x_hermes_session_token
