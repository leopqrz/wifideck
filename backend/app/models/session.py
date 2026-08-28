"""Capture session model."""
from __future__ import annotations

from pydantic import BaseModel

from .network import Network


class CaptureSession(BaseModel):
    id: str
    started: str                    # ISO timestamp
    stopped: str | None = None
    running: bool = False
    channel: int | None = None
    target_bssid: str | None = None
    handshake: bool = False
    pmkid: bool = False
    ap_count: int = 0
    client_count: int = 0
    pcap_available: bool = False


class CaptureDetail(CaptureSession):
    """A session plus its current live network/client view."""

    networks: list[Network] = []
