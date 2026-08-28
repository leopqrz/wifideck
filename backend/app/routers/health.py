"""Health / readiness endpoint — the Phase 0 gate check."""
from __future__ import annotations

from fastapi import APIRouter, Depends

from ..auth import require_token
from ..config import settings

router = APIRouter()


@router.get("/api/health")
def health(_: bool = Depends(require_token)) -> dict:
    return {
        "status": "ok",
        "service": "wifideck",
        "version": settings.version,
        "mock": settings.mock,
    }
