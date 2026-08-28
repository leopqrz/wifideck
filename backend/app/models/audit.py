"""Audit and scope models for active (transmit) modules."""
from __future__ import annotations

from pydantic import BaseModel


class AuditEntry(BaseModel):
    timestamp: str
    action: str                 # deauth / deauth.refused / scope.add / scope.remove
    result: str                 # ok / refused / error
    target_bssid: str | None = None
    target_ssid: str | None = None
    channel: int | None = None
    detail: str | None = None


class ScopeTarget(BaseModel):
    bssid: str                  # normalized upper-case
    ssid: str | None = None
    note: str | None = None
    added: str                  # ISO timestamp


class ActiveState(BaseModel):
    enabled: bool               # are active modules enabled in config at all?
