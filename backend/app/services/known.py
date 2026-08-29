"""KnownNetworks — the last MANAGED scan, snapshotted at the moment we switch to
MONITOR. In monitor this adapter's live (airodump) scan usually returns nothing,
so the deauth / capture target pickers reuse this remembered list — each entry
still carrying its channel. Persisted as JSON so it survives a reload or restart.
"""
from __future__ import annotations

import json
import os
from datetime import datetime, timezone

from ..models.network import Network


class KnownNetworks:
    def __init__(self, path: str) -> None:
        self.path = path
        self._nets: list[Network] = []
        self._saved_at: str | None = None
        self._load()

    def _load(self) -> None:
        if not os.path.isfile(self.path):
            return
        try:
            with open(self.path, errors="replace") as f:
                data = json.load(f)
            self._saved_at = data.get("saved_at")
            self._nets = [Network(**n) for n in data.get("networks", [])]
        except (ValueError, OSError, TypeError):
            self._nets = []
            self._saved_at = None

    def save(self, networks: list[Network]) -> None:
        # Keep only targetable entries; never clobber a good list with an empty scan.
        nets = [n for n in networks if n.bssid]
        if not nets:
            return
        self._nets = nets
        self._saved_at = datetime.now(timezone.utc).isoformat(timespec="seconds")
        try:
            os.makedirs(os.path.dirname(self.path) or ".", exist_ok=True)
            with open(self.path, "w") as f:
                json.dump(
                    {
                        "saved_at": self._saved_at,
                        "networks": [n.model_dump(mode="json") for n in nets],
                    },
                    f,
                    indent=2,
                )
        except OSError:
            pass

    def list(self) -> list[Network]:
        return list(self._nets)

    @property
    def saved_at(self) -> str | None:
        return self._saved_at
