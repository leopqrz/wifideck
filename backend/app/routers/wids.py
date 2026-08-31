"""Defensive-monitoring (WIDS-lite) endpoints."""
from __future__ import annotations

from fastapi import APIRouter, Depends
from pydantic import BaseModel

from ..auth import require_token
from ..deps import get_wids_service
from ..models.wids import WidsStatus
from ..services.wids import WidsService

router = APIRouter()


class WidsRequest(BaseModel):
    enabled: bool


@router.get("/api/wids", response_model=WidsStatus)
async def wids_status(
    _: bool = Depends(require_token),
    svc: WidsService = Depends(get_wids_service),
) -> WidsStatus:
    return svc.status_info()


@router.post("/api/wids", response_model=WidsStatus)
async def set_wids(
    req: WidsRequest,
    _: bool = Depends(require_token),
    svc: WidsService = Depends(get_wids_service),
) -> WidsStatus:
    if req.enabled:
        svc.start()
    else:
        await svc.stop()
    return svc.status_info()


@router.post("/api/wids/baseline", response_model=WidsStatus)
async def set_baseline(
    _: bool = Depends(require_token),
    svc: WidsService = Depends(get_wids_service),
) -> WidsStatus:
    """Snapshot the current networks as the known-good baseline."""
    await svc.set_baseline()
    return svc.status_info()


@router.delete("/api/wids/baseline", response_model=WidsStatus)
async def clear_baseline(
    _: bool = Depends(require_token),
    svc: WidsService = Depends(get_wids_service),
) -> WidsStatus:
    svc.clear_baseline()
    return svc.status_info()
