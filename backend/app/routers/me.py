"""Who am I — the caller's role, for the UI to reflect."""
from __future__ import annotations

from fastapi import APIRouter, Depends
from pydantic import BaseModel

from ..auth import current_role, require_token
from ..config import settings

router = APIRouter()


class Me(BaseModel):
    role: str
    active_enabled: bool
    rbac: bool  # whether a viewer token is configured (read-only role available)


@router.get("/api/me", response_model=Me)
async def me(
    _: bool = Depends(require_token),  # satisfies the "every /api route is token-gated" invariant
    role: str = Depends(current_role),
) -> Me:
    return Me(role=role, active_enabled=settings.enable_active, rbac=bool(settings.viewer_token))
