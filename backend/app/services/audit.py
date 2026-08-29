"""Append-only audit log for active-module actions (JSON Lines)."""
from __future__ import annotations

import os
from datetime import datetime, timezone

from ..models.audit import AuditEntry


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


class AuditLog:
    def __init__(self, path: str) -> None:
        self.path = path

    def record(
        self,
        action: str,
        result: str,
        *,
        target_bssid: str | None = None,
        target_ssid: str | None = None,
        channel: int | None = None,
        detail: str | None = None,
    ) -> AuditEntry:
        entry = AuditEntry(
            timestamp=_now(),
            action=action,
            result=result,
            target_bssid=target_bssid,
            target_ssid=target_ssid,
            channel=channel,
            detail=detail,
        )
        os.makedirs(os.path.dirname(self.path) or ".", exist_ok=True)
        with open(self.path, "a") as f:
            f.write(entry.model_dump_json() + "\n")
        return entry

    def recent(self, limit: int = 100) -> list[AuditEntry]:
        if not os.path.isfile(self.path):
            return []
        with open(self.path, errors="replace") as f:
            lines = f.readlines()
        out: list[AuditEntry] = []
        for line in lines[-limit:]:
            line = line.strip()
            if line:
                try:
                    out.append(AuditEntry.model_validate_json(line))
                except ValueError:
                    continue
        out.reverse()  # newest first
        return out
