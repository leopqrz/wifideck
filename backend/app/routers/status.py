"""Adapter status endpoint."""
from __future__ import annotations

from fastapi import APIRouter, Depends

from ..auth import require_token
from ..deps import get_status_service
from ..models.status import Status
from ..services.status import StatusService

router = APIRouter()


@router.get("/api/status", response_model=Status)
async def status(
    _: bool = Depends(require_token),
    svc: StatusService = Depends(get_status_service),
) -> Status:
    return await svc.snapshot()
