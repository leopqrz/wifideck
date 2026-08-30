"""History entry — a past capture session joined with its latest crack outcome."""
from __future__ import annotations

from pydantic import BaseModel


class HistoryEntry(BaseModel):
    id: str
    started: str
    stopped: str | None = None
    mode: str = "handshake"
    channel: int | None = None
    target_bssid: str | None = None
    handshake: bool = False
    pmkid: bool = False
    pcap_available: bool = False
    crack_engine: str | None = None
    crack_state: str | None = None
    crack_key: str | None = None
