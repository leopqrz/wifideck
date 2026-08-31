"""Assessment report models — an aggregate of what the tool has seen/done."""
from __future__ import annotations

from pydantic import BaseModel

from .audit import AuditEntry, ScopeTarget
from .history import HistoryEntry


class ReportNetwork(BaseModel):
    ssid: str | None = None
    bssid: str | None = None
    band: str | None = None
    channel: int | None = None
    security: list[str] = []
    posture_label: str = ""
    posture_tone: str = "muted"
    posture_note: str = ""


class ReportSummary(BaseModel):
    networks: int = 0
    sessions: int = 0
    handshakes: int = 0
    pmkids: int = 0
    cracked: int = 0
    audit_actions: int = 0
    scoped: int = 0


class Report(BaseModel):
    generated: str
    version: str
    summary: ReportSummary
    networks: list[ReportNetwork] = []
    sessions: list[HistoryEntry] = []
    audit: list[AuditEntry] = []
    scope: list[ScopeTarget] = []
