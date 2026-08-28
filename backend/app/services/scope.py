"""In-scope target allowlist — the set of BSSIDs the operator has declared they
are authorized to actively test. Persisted as a JSON file. Empty by default, so
no target is actionable until explicitly added."""
from __future__ import annotations

import json
import os
import re
from datetime import datetime, timezone

from ..models.audit import ScopeTarget

_BSSID_RE = re.compile(r"^([0-9A-F]{2}:){5}[0-9A-F]{2}$")


def normalize_bssid(bssid: str) -> str | None:
    b = bssid.strip().upper()
    return b if _BSSID_RE.match(b) else None


class ScopeList:
    def __init__(self, path: str) -> None:
        self.path = path
        self._targets: dict[str, ScopeTarget] = {}
        self._load()

    def _load(self) -> None:
        if not os.path.isfile(self.path):
            return
        try:
            with open(self.path, errors="replace") as f:
                data = json.load(f)
            for item in data:
                t = ScopeTarget(**item)
                self._targets[t.bssid] = t
        except (ValueError, OSError):
            self._targets = {}

    def _save(self) -> None:
        os.makedirs(os.path.dirname(self.path) or ".", exist_ok=True)
        with open(self.path, "w") as f:
            json.dump([t.model_dump() for t in self._targets.values()], f, indent=2)

    def list(self) -> list[ScopeTarget]:
        return sorted(self._targets.values(), key=lambda t: t.added, reverse=True)

    def contains(self, bssid: str) -> bool:
        norm = normalize_bssid(bssid)
        return norm is not None and norm in self._targets

    def add(self, bssid: str, ssid: str | None = None, note: str | None = None) -> ScopeTarget:
        norm = normalize_bssid(bssid)
        if norm is None:
            raise ValueError("Invalid BSSID (expected AA:BB:CC:DD:EE:FF).")
        target = ScopeTarget(
            bssid=norm,
            ssid=ssid,
            note=note,
            added=datetime.now(timezone.utc).isoformat(timespec="seconds"),
        )
        self._targets[norm] = target
        self._save()
        return target

    def remove(self, bssid: str) -> bool:
        norm = normalize_bssid(bssid)
        if norm is None or norm not in self._targets:
            return False
        del self._targets[norm]
        self._save()
        return True
