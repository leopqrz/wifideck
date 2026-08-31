"""ScanService — unified network discovery.

Two sources, one Network model:
  * MANAGED: `nmcli device wifi list` (signal as 0-100 quality)
  * MONITOR: `airodump-ng` CSV (signal as dBm, plus associated client counts)

Parsers are pure and unit-tested; the live monitor scanner manages an
airodump-ng subprocess (root + monitor mode).
"""
from __future__ import annotations

import asyncio
import glob
import os
import re
import tempfile

from ..models.network import Network
from .runner import CommandRunner

_UNESCAPED_COLON = re.compile(r"(?<!\\):")


def band_for_channel(ch: int | None) -> str | None:
    if ch is None:
        return None
    if 1 <= ch <= 14:
        return "2.4 GHz"
    if 32 <= ch <= 177:
        return "5 GHz"
    return None


def _unescape(field: str) -> str:
    return field.replace("\\:", ":").replace("\\\\", "\\")


def _to_int(s: str) -> int | None:
    try:
        return int(s)
    except (ValueError, TypeError):
        return None


def parse_nmcli_wifi(text: str) -> list[Network]:
    """Parse terse `nmcli -f IN-USE,BSSID,SSID,CHAN,SIGNAL,SECURITY device wifi list`."""
    nets: list[Network] = []
    for line in text.splitlines():
        if not line.strip():
            continue
        parts = [_unescape(p) for p in _UNESCAPED_COLON.split(line)]
        if len(parts) < 6:
            continue
        in_use, bssid, ssid, chan, signal, security = parts[:6]
        ch = _to_int(chan)
        nets.append(
            Network(
                bssid=bssid or None,
                ssid=ssid or None,
                band=band_for_channel(ch),
                channel=ch,
                signal_pct=_to_int(signal),
                security=security.split() if security else [],
                is_current=in_use.strip() == "*",
            )
        )
    return nets


def _dbm_to_pct(dbm: int | None) -> int | None:
    if dbm is None:
        return None
    return max(0, min(100, round((dbm + 90) / 60 * 100)))


def parse_airodump_csv(text: str) -> list[Network]:
    """Parse an airodump-ng CSV (AP section + station section for client counts)."""
    lines = text.splitlines()
    # Split into the AP block and the station block (blank line + 'Station MAC').
    ap_rows: list[list[str]] = []
    station_rows: list[list[str]] = []
    section = "ap"
    for raw in lines:
        line = raw.strip()
        if not line:
            continue
        if line.startswith("BSSID,"):
            section = "ap"
            continue
        if line.startswith("Station MAC,"):
            section = "station"
            continue
        cells = [c.strip() for c in raw.split(",")]
        (ap_rows if section == "ap" else station_rows).append(cells)

    # Count stations per BSSID (station's associated BSSID is column index 5).
    clients: dict[str, int] = {}
    for row in station_rows:
        if len(row) > 5 and re.match(r"[0-9A-Fa-f:]{17}", row[5]):
            clients[row[5].upper()] = clients.get(row[5].upper(), 0) + 1

    nets: list[Network] = []
    for row in ap_rows:
        if len(row) < 14:
            continue
        bssid = row[0].upper()
        ch = _to_int(row[3])
        power = _to_int(row[8])
        privacy = row[5].strip()
        auth = row[7].strip()
        essid = row[13].strip()
        sec: list[str] = []
        if privacy and privacy not in ("", "OPN"):
            sec.append(privacy)
        if auth:
            sec.append(auth)
        nets.append(
            Network(
                bssid=bssid,
                ssid=essid or None,
                band=band_for_channel(ch),
                channel=ch,
                signal_dbm=power,
                signal_pct=_dbm_to_pct(power),
                security=sec,
                clients=clients.get(bssid, 0),
            )
        )
    return nets


class ScanService:
    def __init__(self, runner: CommandRunner) -> None:
        self.runner = runner

    async def scan_managed(self, rescan: str = "no") -> list[Network]:
        # rescan="no" reads NetworkManager's cache instantly (it scans in the
        # background), keeping the stream responsive. Callers can force "yes".
        result = await self.runner.run(
            [
                "nmcli", "-t",
                "-f", "IN-USE,BSSID,SSID,CHAN,SIGNAL,SECURITY",
                "device", "wifi", "list", "--rescan", rescan,
            ]
        )
        return parse_nmcli_wifi(result.stdout)


class AirodumpScanner:
    """Manages an airodump-ng subprocess writing CSV, read on each poll.

    Requires root and the interface already in MONITOR mode.
    """

    def __init__(self, iface: str) -> None:
        self.iface = iface
        self.proc: asyncio.subprocess.Process | None = None
        self.tmpdir: str | None = None
        self.prefix: str | None = None

    async def start(self) -> None:
        self.tmpdir = tempfile.mkdtemp(prefix="wd_scan_")
        self.prefix = os.path.join(self.tmpdir, "scan")
        self.proc = await asyncio.create_subprocess_exec(
            "airodump-ng", "--output-format", "csv", "-w", self.prefix, self.iface,
            stdout=asyncio.subprocess.DEVNULL,
            stderr=asyncio.subprocess.DEVNULL,
        )

    def read(self) -> list[Network]:
        return parse_airodump_csv(self.read_raw())

    def read_raw(self) -> str:
        """Latest airodump CSV text (for station parsing); '' if none yet."""
        if not self.prefix:
            return ""
        files = sorted(glob.glob(self.prefix + "-*.csv"))
        if not files:
            return ""
        try:
            with open(files[-1], errors="replace") as f:
                return f.read()
        except OSError:
            return ""

    async def stop(self) -> None:
        if self.proc and self.proc.returncode is None:
            self.proc.terminate()
            try:
                await asyncio.wait_for(self.proc.wait(), timeout=3)
            except asyncio.TimeoutError:
                self.proc.kill()
        if self.tmpdir and os.path.isdir(self.tmpdir):
            for p in glob.glob(os.path.join(self.tmpdir, "*")):
                try:
                    os.remove(p)
                except OSError:
                    pass
            try:
                os.rmdir(self.tmpdir)
            except OSError:
                pass
