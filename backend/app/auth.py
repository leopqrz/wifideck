"""Token authentication for HTTP routes and WebSockets.

Accepts either `Authorization: Bearer <token>` or `X-Auth-Token: <token>` on
HTTP, and a `?token=` query parameter on WebSocket handshakes.
"""
from __future__ import annotations

import secrets

from fastapi import Header, HTTPException, status

from .config import settings


def _valid(token: str | None) -> bool:
    if not token:
        return False
    # Constant-time compare to avoid leaking the token via timing.
    return secrets.compare_digest(token, settings.token)


def require_token(
    authorization: str | None = Header(default=None),
    x_auth_token: str | None = Header(default=None),
) -> bool:
    """FastAPI dependency: raise 401 unless a valid token is presented."""
    token: str | None = None
    if authorization and authorization.lower().startswith("bearer "):
        token = authorization[7:].strip()
    elif x_auth_token:
        token = x_auth_token.strip()

    if not _valid(token):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing or invalid token.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return True


def valid_ws_token(token: str | None) -> bool:
    """Plain check for the WebSocket handshake (can't raise HTTP there)."""
    return _valid(token)
