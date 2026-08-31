"""WidsService — defensive monitoring (WIDS-lite).

Two detectors:
  * evil-twin (from scans): an SSID advertised on multiple BSSIDs with MISMATCHED
    security (e.g. an open clone of a WPA2 network). Normal enterprise roaming —
    same SSID, consistent security across BSSIDs — is NOT flagged.
  * deauth-flood (monitor mode, via tshark): a burst of deauth/disassoc frames.

Read-only / passive. Raises alerts; never transmits.
"""
from __future__ import annotations

import asyncio
import json
import os
from collections import defaultdict, deque
from datetime import datetime, timezone

from ..models.network import Network
from ..models.wids import WidsAlert, WidsStatus
from .runner import CommandRunner
from .scan import ScanService
from .status import StatusService

# 802.11 mgmt subtypes: 0x0c = deauth, 0x0a = disassoc
_DEAUTH_FILTER = "wlan.fc.type_subtype==0x0c || wlan.fc.type_subtype==0x0a"


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def find_evil_twins(networks: list[Network]) -> list[dict]:
    """SSIDs seen on 2+ BSSIDs with differing security profiles."""
    by_ssid: dict[str, list[Network]] = defaultdict(list)
    for n in networks:
        if n.ssid:
            by_ssid[n.ssid].append(n)

    out: list[dict] = []
    for ssid, nets in by_ssid.items():
        bssids = {n.bssid for n in nets if n.bssid}
        if len(bssids) < 2:
            continue
        profiles = {tuple(sorted(n.security)) for n in nets}
        if len(profiles) < 2:
            continue  # consistent security across BSSIDs -> normal roaming
        has_open = any(not n.security for n in nets)
        has_secured = any(n.security for n in nets)
        severity = "high" if (has_open and has_secured) else "medium"
        out.append({
            "ssid": ssid,
            "bssids": sorted(bssids),
            "severity": severity,
            "detail": (
                f"SSID '{ssid}' on {len(bssids)} BSSIDs with mismatched security "
                f"{sorted(' '.join(p) or 'OPEN' for p in profiles)} — possible evil twin"
            ),
        })
    return out


def detect_rogue_aps(networks: list[Network], baseline: dict) -> list[dict]:
    """APs present now but not in the known-good baseline. Only with a baseline set."""
    if not baseline:
        return []
    out: list[dict] = []
    for n in networks:
        if n.bssid and n.bssid not in baseline:
            out.append({
                "bssid": n.bssid, "ssid": n.ssid, "severity": "low",
                "detail": f"new AP not in baseline: {n.ssid or '<hidden>'} ({n.bssid})",
            })
    return out


def detect_downgrades(networks: list[Network], baseline: dict) -> list[dict]:
    """A baselined AP that has since dropped its encryption (now OPEN) — a classic
    downgrade / evil-twin signal."""
    out: list[dict] = []
    for n in networks:
        if n.bssid and n.bssid in baseline:
            base_sec = baseline[n.bssid].get("security") or []
            if base_sec and not n.security:
                out.append({
                    "bssid": n.bssid, "ssid": n.ssid, "severity": "high",
                    "detail": (
                        f"'{n.ssid or '<hidden>'}' ({n.bssid}) is now OPEN "
                        f"(baseline had {sorted(base_sec)}) — possible downgrade/evil-twin"
                    ),
                })
    return out


class WidsService:
    def __init__(
        self,
        runner: CommandRunner,
        scan: ScanService,
        status: StatusService,
        interval: float,
        deauth_threshold: int,
        mock: bool,
        enabled: bool,
        notify=None,
        baseline_file: str | None = None,
    ) -> None:
        self.runner = runner
        self.scan = scan
        self.status = status
        self.interval = interval
        self.deauth_threshold = deauth_threshold
        self.mock = mock
        self.enabled = enabled
        self.notify = notify
        self.baseline_file = baseline_file
        self._baseline: dict = {}
        self._load_baseline()
        self._task: asyncio.Task | None = None
        self._alerts: deque[WidsAlert] = deque(maxlen=100)
        self._seen: set[tuple] = set()
        self.checks = 0
        self.last_check: str | None = None

    def _alert(self, kind, severity, ssid, bssid, detail) -> None:
        self._alerts.appendleft(
            WidsAlert(timestamp=_now(), kind=kind, severity=severity, ssid=ssid, bssid=bssid, detail=detail)
        )
        if self.notify:
            try:
                asyncio.get_running_loop().create_task(
                    self.notify.send(
                        f"WIDS: {kind}", detail, level=severity,
                        dedup_key=f"wids:{kind}:{bssid or ssid or ''}",
                    )
                )
            except RuntimeError:
                pass  # no running loop (e.g. a direct unit-test call)

    def _load_baseline(self) -> None:
        if not self.baseline_file or not os.path.isfile(self.baseline_file):
            return
        try:
            with open(self.baseline_file, errors="replace") as f:
                self._baseline = json.load(f)
        except (ValueError, OSError):
            self._baseline = {}

    def _save_baseline(self) -> None:
        if not self.baseline_file:
            return
        try:
            os.makedirs(os.path.dirname(self.baseline_file) or ".", exist_ok=True)
            with open(self.baseline_file, "w") as f:
                json.dump(self._baseline, f, indent=2)
        except OSError:
            pass

    async def set_baseline(self) -> int:
        nets = await self.scan.scan_managed()
        self._baseline = {
            n.bssid: {"ssid": n.ssid, "security": n.security} for n in nets if n.bssid
        }
        self._save_baseline()
        return len(self._baseline)

    def clear_baseline(self) -> None:
        self._baseline = {}
        self._save_baseline()

    @property
    def baseline_count(self) -> int:
        return len(self._baseline)

    async def _deauth_count(self, iface: str) -> int:
        r = await self.runner.run([
            "sh", "-c",
            f'tshark -i {iface} -a duration:3 -Y "{_DEAUTH_FILTER}" -T fields -e wlan.sa 2>/dev/null | wc -l',
        ])
        try:
            return int(r.stdout.strip() or "0")
        except ValueError:
            return 0

    async def run_once(self) -> None:
        self.checks += 1
        self.last_check = _now()

        networks = await self.scan.scan_managed()
        for tw in find_evil_twins(networks):
            key = ("evil-twin", tw["ssid"], tuple(tw["bssids"]))
            if key not in self._seen:
                self._seen.add(key)
                self._alert("evil-twin", tw["severity"], tw["ssid"], None, tw["detail"])
        for r in detect_rogue_aps(networks, self._baseline):
            key = ("rogue-ap", r["bssid"])
            if key not in self._seen:
                self._seen.add(key)
                self._alert("rogue-ap", r["severity"], r["ssid"], r["bssid"], r["detail"])
        for d in detect_downgrades(networks, self._baseline):
            key = ("downgrade", d["bssid"])
            if key not in self._seen:
                self._seen.add(key)
                self._alert("downgrade", d["severity"], d["ssid"], d["bssid"], d["detail"])

        snap = await self.status.snapshot()
        if not self.mock and snap.mode == "MONITOR" and snap.interface:
            count = await self._deauth_count(snap.interface)
            if count >= self.deauth_threshold:
                self._alert(
                    "deauth-flood", "high", None, None,
                    f"{count} deauth/disassoc frames in 3s (threshold {self.deauth_threshold})",
                )

    def status_info(self) -> WidsStatus:
        return WidsStatus(
            enabled=self.enabled,
            running=self._task is not None and not self._task.done(),
            checks=self.checks,
            alert_count=len(self._alerts),
            last_check=self.last_check,
            alerts=list(self._alerts),
            baseline=self.baseline_count,
        )

    async def _loop(self) -> None:
        while self.enabled:
            try:
                await self.run_once()
            except Exception as e:
                self._alert("rogue", "low", None, None, f"wids error: {e}")
            await asyncio.sleep(self.interval)

    def start(self) -> None:
        self.enabled = True
        if self._task is None or self._task.done():
            self._task = asyncio.create_task(self._loop())

    async def stop(self) -> None:
        self.enabled = False
        if self._task is not None:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
            self._task = None
