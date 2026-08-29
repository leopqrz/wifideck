"""Watchdog status + event models."""
from __future__ import annotations

from pydantic import BaseModel


class WatchdogEvent(BaseModel):
    timestamp: str
    kind: str        # degraded / driver-reload / usb-reset / reconnect / recovered / usb-absent
    detail: str
    result: str      # ok / failed / wait / info


class WatchdogStatus(BaseModel):
    enabled: bool
    running: bool
    healthy: bool | None = None       # None until first check
    usb_present: bool | None = None
    interface: str | None = None
    checks: int = 0
    recoveries: int = 0
    last_check: str | None = None
    events: list[WatchdogEvent] = []
