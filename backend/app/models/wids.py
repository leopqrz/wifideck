"""Defensive-monitoring (WIDS-lite) models."""
from __future__ import annotations

from pydantic import BaseModel


class WidsAlert(BaseModel):
    timestamp: str
    kind: str          # evil-twin / deauth-flood / rogue
    severity: str      # high / medium / low
    ssid: str | None = None
    bssid: str | None = None
    detail: str


class WidsStatus(BaseModel):
    enabled: bool
    running: bool
    checks: int = 0
    alert_count: int = 0
    last_check: str | None = None
    baseline: int = 0
    alerts: list[WidsAlert] = []
