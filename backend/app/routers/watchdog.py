"""Self-healing watchdog endpoints."""
from __future__ import annotations

from fastapi import APIRouter, Depends
from pydantic import BaseModel

from ..auth import require_token
from ..deps import get_watchdog_service
from ..models.watchdog import WatchdogStatus
from ..services.watchdog import WatchdogService

router = APIRouter()


class WatchdogRequest(BaseModel):
    enabled: bool


@router.get("/api/watchdog", response_model=WatchdogStatus)
async def watchdog_status(
    _: bool = Depends(require_token),
    svc: WatchdogService = Depends(get_watchdog_service),
) -> WatchdogStatus:
    return svc.status_info()


@router.post("/api/watchdog", response_model=WatchdogStatus)
async def set_watchdog(
    req: WatchdogRequest,
    _: bool = Depends(require_token),
    svc: WatchdogService = Depends(get_watchdog_service),
) -> WatchdogStatus:
    if req.enabled:
        svc.start()
    else:
        await svc.stop()
    return svc.status_info()
