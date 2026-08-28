"""Adapter status model — the shape streamed to the dashboard."""
from __future__ import annotations

from enum import Enum

from pydantic import BaseModel


class Health(str, Enum):
    OK = "ok"                    # adapter present, interface up
    DISCONNECTED = "disconnected"  # not on the USB bus
    DEGRADED = "degraded"        # present but something's wrong (no iface, USB errors)


class Status(BaseModel):
    usb_present: bool
    driver: str | None = None
    interface: str | None = None
    mode: str | None = None            # MANAGED / MONITOR / ... (upper-case)
    operstate: str | None = None       # up / down / dormant
    ssid: str | None = None
    ip4: str | None = None
    signal_dbm: int | None = None
    tx_bitrate_mbps: float | None = None
    freq_mhz: int | None = None
    band: str | None = None            # "2.4 GHz" / "5 GHz"
    health: Health = Health.DISCONNECTED
    health_detail: str | None = None
