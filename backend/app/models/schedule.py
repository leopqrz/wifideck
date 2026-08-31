"""Scheduled job — a named action run on an interval."""
from __future__ import annotations

from pydantic import BaseModel


class Job(BaseModel):
    id: str
    label: str
    action: str
    interval_sec: int
    enabled: bool = False
    last_run: str | None = None
    last_result: str | None = None
    runs: int = 0
