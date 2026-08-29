"""Guided capture-flow models."""
from __future__ import annotations

from pydantic import BaseModel


class FlowStep(BaseModel):
    name: str          # monitor / capture / deauth / handshake / cleanup
    detail: str
    timestamp: str
    done: bool = False


class FlowStatus(BaseModel):
    state: str         # idle / running / done / timeout / failed / stopped
    target_bssid: str | None = None
    channel: int | None = None
    session_id: str | None = None
    handshake: bool = False
    message: str | None = None
    steps: list[FlowStep] = []
