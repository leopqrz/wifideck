"""Station (client device) seen in monitor mode."""
from __future__ import annotations

from pydantic import BaseModel


class Station(BaseModel):
    mac: str
    vendor: str | None = None       # OUI vendor, or "randomized" for a private MAC
    signal_dbm: int | None = None
    bssid: str | None = None        # associated AP, or None if not associated
    probes: list[str] = []          # SSIDs this device is probing for
    packets: int = 0
    first_seen: str | None = None
    last_seen: str | None = None
