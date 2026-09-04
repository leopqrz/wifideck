"""CaptureService — airodump-ng capture sessions with handshake/PMKID detection.

Requires root and MONITOR mode in real use. Mock mode simulates a running
session from fixtures so the UI works with no hardware.
"""
from __future__ import annotations

import asyncio
import glob
import os
import re
import shutil
import time
from datetime import datetime, timezone

from ..models.network import Network
from ..models.session import CaptureDetail, CaptureSession
from . import fixtures
from .runner import CommandRunner
from .scan import parse_airodump_csv


class CaptureError(Exception):
    """Capture could not start/stop."""


class CaptureBusy(Exception):
    """A capture is already running."""


_HS_COUNT = re.compile(r"(\d+)\s+handshake", re.IGNORECASE)


def parse_aircrack_handshakes(text: str, target_bssid: str | None = None) -> dict:
    """Detect WPA handshakes / PMKID from `aircrack-ng <cap>` output.

    Only a *positive* handshake count counts (aircrack prints "(1 handshake)");
    a "0 handshake" line does not.
    """
    hs = pmkid = False
    target = target_bssid.lower() if target_bssid else None
    for line in text.splitlines():
        low = line.lower()
        in_scope = target is None or target in low
        if not in_scope:
            continue
        m = _HS_COUNT.search(low)
        if m and int(m.group(1)) > 0:
            hs = True
        if "pmkid" in low:
            pmkid = True
    return {"handshake": hs, "pmkid": pmkid}


class CaptureService:
    def __init__(self, runner: CommandRunner, base_dir: str, mock: bool, history=None) -> None:
        self.runner = runner
        self.base_dir = base_dir
        self.mock = mock
        self.history = history  # optional HistoryStore (SQLite) for durable records
        self.sessions: dict[str, CaptureSession] = {}
        self._procs: dict[str, asyncio.subprocess.Process] = {}
        self._active: str | None = None

    def _dir(self, sid: str) -> str:
        return os.path.join(self.base_dir, sid)

    def _prefix(self, sid: str) -> str:
        return os.path.join(self._dir(sid), "capture")

    @property
    def active(self) -> CaptureSession | None:
        return self.sessions.get(self._active) if self._active else None

    async def start(
        self, iface: str, channel: int | None, bssid: str | None, mode: str = "handshake"
    ) -> CaptureSession:
        if self.active and self.active.running:
            raise CaptureBusy()

        sid = time.strftime("%Y%m%d-%H%M%S")
        os.makedirs(self._dir(sid), exist_ok=True)
        session = CaptureSession(
            id=sid,
            started=datetime.now(timezone.utc).isoformat(timespec="seconds"),
            running=True,
            mode="pmkid" if mode == "pmkid" else "handshake",
            channel=channel,
            target_bssid=bssid,
        )
        self.sessions[sid] = session
        self._active = sid
        if self.history:
            self.history.record_session(session)

        if not self.mock:
            if session.mode == "pmkid":
                # hcxdumptool grabs the PMKID clientless (an association request, no
                # deauth). NB: hcxdumptool's CLI differs across versions — tune these
                # flags for the one installed (this matches the 6.2.x series).
                args = ["hcxdumptool", "-i", iface, "-o", self._prefix(sid) + ".pcapng",
                        "--enable_status=1"]
                if bssid:
                    args += [f"--filterlist_ap={bssid}", "--filtermode=2"]
            else:
                args = ["airodump-ng", "--output-format", "pcap,csv", "-w", self._prefix(sid)]
                if channel is not None:
                    args += ["-c", str(channel)]
                if bssid:
                    args += ["--bssid", bssid]
                args.append(iface)
            self._procs[sid] = await asyncio.create_subprocess_exec(
                *args,
                stdout=asyncio.subprocess.DEVNULL,
                stderr=asyncio.subprocess.DEVNULL,
            )
        return session

    async def stop(self, sid: str) -> CaptureSession:
        session = self.sessions.get(sid)
        if not session:
            raise CaptureError("Unknown session.")
        proc = self._procs.pop(sid, None)
        if proc and proc.returncode is None:
            proc.terminate()
            try:
                await asyncio.wait_for(proc.wait(), timeout=3)
            except asyncio.TimeoutError:
                proc.kill()
        await self.refresh(sid)
        session.running = False
        session.stopped = datetime.now(timezone.utc).isoformat(timespec="seconds")
        if self._active == sid:
            self._active = None
        if self.history:
            self.history.record_session(session)
        return session

    async def refresh(self, sid: str) -> list[Network]:
        """Update a session's live counts + handshake flags; return its networks."""
        session = self.sessions.get(sid)
        if not session:
            return []

        if self.mock:
            nets = parse_airodump_csv(fixtures.AIRODUMP_CSV)
            session.ap_count = len(nets)
            session.client_count = sum(n.clients for n in nets)
            if session.mode == "pmkid":
                session.pmkid = True
            else:
                session.handshake = True
            session.pcap_available = True
            return nets

        csvs = sorted(glob.glob(self._prefix(sid) + "-*.csv"))
        nets: list[Network] = []
        if csvs:
            try:
                with open(csvs[-1], errors="replace") as f:
                    nets = parse_airodump_csv(f.read())
            except OSError:
                nets = []
        session.ap_count = len(nets)
        session.client_count = sum(n.clients for n in nets)

        cap = self.pcap_path(sid)
        if cap and os.path.getsize(cap) > 0:
            session.pcap_available = True
            result = await self.runner.run(["aircrack-ng", cap])
            flags = parse_aircrack_handshakes(result.stdout, session.target_bssid)
            session.handshake = session.handshake or flags["handshake"]
            session.pmkid = session.pmkid or flags["pmkid"]
        return nets

    async def import_pcap(
        self, src_path: str, channel: int | None = None, bssid: str | None = None
    ) -> CaptureSession:
        """Adopt an externally-captured pcap (e.g. from the macOS libusb driver) as a
        capture session, so it flows through verify → crack → history like any other."""
        if not os.path.isfile(src_path):
            raise CaptureError(f"pcap not found: {src_path}")
        sid = time.strftime("%Y%m%d-%H%M%S") + "-imp"
        os.makedirs(self._dir(sid), exist_ok=True)
        ext = os.path.splitext(src_path)[1] or ".pcap"
        dst = self._prefix(sid) + ext
        shutil.copy(src_path, dst)

        session = CaptureSession(
            id=sid,
            started=datetime.now(timezone.utc).isoformat(timespec="seconds"),
            stopped=datetime.now(timezone.utc).isoformat(timespec="seconds"),
            running=False, mode="import", channel=channel, target_bssid=bssid,
            pcap_available=True,
        )
        self.sessions[sid] = session

        if self.mock:
            session.handshake = True
        else:
            result = await self.runner.run(["aircrack-ng", dst])
            flags = parse_aircrack_handshakes(result.stdout, bssid)
            session.handshake = flags["handshake"]
            session.pmkid = flags["pmkid"]
        if self.history:
            self.history.record_session(session)
        return session

    def pcap_path(self, sid: str) -> str | None:
        # airodump writes capture-01.cap; hcxdumptool writes capture.pcapng.
        caps = sorted(
            glob.glob(self._prefix(sid) + "-*.cap")
            + glob.glob(self._prefix(sid) + "-*.pcap")
            + glob.glob(self._prefix(sid) + "*.pcapng")
        )
        return caps[-1] if caps else None

    def list(self) -> list[CaptureSession]:
        return sorted(self.sessions.values(), key=lambda s: s.started, reverse=True)

    async def detail(self, sid: str) -> CaptureDetail | None:
        session = self.sessions.get(sid)
        if not session:
            return None
        nets = await self.refresh(sid)
        return CaptureDetail(**session.model_dump(), networks=nets)
