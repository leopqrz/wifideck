"""Notifications — which sinks are enabled, and a manual test send."""
from __future__ import annotations

import time

from fastapi import APIRouter, Depends
from pydantic import BaseModel

from ..auth import require_token
from ..deps import get_notify_service
from ..services.notify import NotifyService

router = APIRouter()


class NotifyStatus(BaseModel):
    sinks: list[str]
    last_error: str | None = None


@router.get("/api/notify", response_model=NotifyStatus)
async def notify_status(
    _: bool = Depends(require_token),
    svc: NotifyService = Depends(get_notify_service),
) -> NotifyStatus:
    return NotifyStatus(sinks=svc.enabled_sinks(), last_error=svc.last_error)


@router.post("/api/notify/test")
async def notify_test(
    _: bool = Depends(require_token),
    svc: NotifyService = Depends(get_notify_service),
) -> dict:
    # Unique dedup_key so repeated tests always fire (bypass the cooldown).
    return await svc.send(
        "WiFiDeck test",
        "If you can read this, your WiFiDeck notifications are working.",
        level="info",
        dedup_key=f"test:{time.time()}",
    )
