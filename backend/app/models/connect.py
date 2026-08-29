"""Client-connection result model."""
from __future__ import annotations

from pydantic import BaseModel


class ConnectResult(BaseModel):
    ok: bool
    ssid: str | None = None
    message: str
