"""Handshake-cracking status model."""
from __future__ import annotations

from pydantic import BaseModel


class CrackStatus(BaseModel):
    state: str            # idle / running / found / exhausted / failed / stopped
    session_id: str | None = None
    bssid: str | None = None
    wordlist: str | None = None
    tested: int = 0
    total: int | None = None
    rate: float | None = None    # thousands of keys/sec (k/s)
    key: str | None = None
    message: str | None = None
