"""Network (and client) models for scan results."""
from __future__ import annotations

from pydantic import BaseModel


class Network(BaseModel):
    bssid: str | None = None
    ssid: str | None = None          # None = hidden
    band: str | None = None          # "2.4 GHz" / "5 GHz"
    channel: int | None = None
    signal_pct: int | None = None    # nmcli quality 0-100
    signal_dbm: int | None = None    # airodump power (monitor mode)
    security: list[str] = []
    is_current: bool = False
    clients: int = 0                 # associated stations (monitor mode)
