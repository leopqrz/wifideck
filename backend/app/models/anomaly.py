"""Device anomaly / risk score for a station."""
from __future__ import annotations

from pydantic import BaseModel


class Anomaly(BaseModel):
    mac: str
    vendor: str | None = None
    score: int
    level: str            # medium / high
    reasons: list[str] = []
    probes: list[str] = []
