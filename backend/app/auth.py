"""Token authentication + roles for HTTP routes and WebSockets.

Accepts either `Authorization: Bearer <token>` or `X-Auth-Token: <token>` on
HTTP, and a `?token=` query parameter on WebSocket handshakes.

Two roles: the main token is **operator** (full access); an optional viewer token
(WIFIDECK_VIEWER_TOKEN) is **viewer** — read-only, enforced by a middleware that
blocks mutating /api requests. RBAC is off unless a viewer token is set.
"""
from __future__ import annotations

import secrets

from fastapi import Header, HTTPException, status

from .config import settings


def role_for_token(token: str | None) -> str | None:
    """Return 'operator' / 'viewer' for a valid token, else None. Constant-time."""
    if not token:
        return None
    if secrets.compare_digest(token, settings.token):
        return "operator"
    if settings.viewer_token and secrets.compare_digest(token, settings.viewer_token):
        return "viewer"
    return None


def _valid(token: str | None) -> bool:
    return role_for_token(token) is not None


def token_from_headers(authorization: str | None, x_auth_token: str | None) -> str | None:
    if authorization and authorization.lower().startswith("bearer "):
        return authorization[7:].strip()
    if x_auth_token:
        return x_auth_token.strip()
    return None


def require_token(
    authorization: str | None = Header(default=None),
    x_auth_token: str | None = Header(default=None),
) -> bool:
    """FastAPI dependency: raise 401 unless a valid token is presented."""
    if not _valid(token_from_headers(authorization, x_auth_token)):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing or invalid token.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return True


def current_role(
    authorization: str | None = Header(default=None),
    x_auth_token: str | None = Header(default=None),
) -> str:
    """FastAPI dependency: the caller's role (401 if the token is invalid)."""
    role = role_for_token(token_from_headers(authorization, x_auth_token))
    if role is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing or invalid token.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return role


def valid_ws_token(token: str | None) -> bool:
    """Plain check for the WebSocket handshake (can't raise HTTP there)."""
    return _valid(token)
