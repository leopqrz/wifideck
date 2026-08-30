"""CrackService — run aircrack-ng on a captured handshake against a wordlist.

Gated: the session's target BSSID must be in the scope allowlist AND the request
must carry explicit authorization; every attempt is audited. Compute-only (no
transmit). For authorized testing of handshakes you captured from your own
networks.
"""
from __future__ import annotations

import asyncio
import json
import os
import re
import tempfile

from ..models.crack import CrackStatus
from .audit import AuditLog
from .capture import CaptureService
from .scope import ScopeList

_PROGRESS = re.compile(r"(\d+)\s*/\s*(\d+)\s+keys tested.*?\(([\d.]+)\s*k/s\)", re.IGNORECASE)
_KEY = re.compile(r"KEY FOUND!\s*\[\s*(.+?)\s*\]")


def parse_hashcat_status(text: str) -> dict:
    """Latest hashcat `--status-json` line → {tested,total,rate,recovered}."""
    out: dict = {}
    for line in text.splitlines():
        line = line.strip()
        if not line.startswith("{") or '"progress"' not in line:
            continue
        try:
            j = json.loads(line)
        except ValueError:
            continue
        prog = j.get("progress")
        if isinstance(prog, list) and len(prog) == 2:
            out["tested"], out["total"] = int(prog[0]), int(prog[1])
        devs = j.get("devices") or []
        speed = sum(d.get("speed", 0) for d in devs if isinstance(d, dict))
        if speed:
            out["rate"] = round(speed / 1000, 1)  # H/s → k/s
        rec = j.get("recovered_hashes")
        if isinstance(rec, list) and rec and rec[0] > 0:
            out["recovered"] = True
    return out


class CrackBusy(Exception):
    pass


class CrackNotFound(Exception):
    pass


class CrackRefused(Exception):
    pass


def parse_aircrack_progress(text: str) -> dict:
    """Extract the latest {tested,total,rate} and any found key from aircrack output."""
    out: dict = {}
    matches = list(_PROGRESS.finditer(text))
    if matches:
        m = matches[-1]
        out["tested"] = int(m.group(1))
        out["total"] = int(m.group(2))
        out["rate"] = float(m.group(3))
    key = _KEY.search(text)
    if key:
        out["key"] = key.group(1)
    return out


class CrackService:
    def __init__(
        self,
        capture: CaptureService,
        scope: ScopeList,
        audit: AuditLog,
        default_wordlist: str,
        mock: bool,
    ) -> None:
        self.capture = capture
        self.scope = scope
        self.audit = audit
        self.default_wordlist = default_wordlist
        self.mock = mock
        self._task: asyncio.Task | None = None
        self._proc: asyncio.subprocess.Process | None = None
        self._reset()

    def _reset(self) -> None:
        self.state = "idle"
        self.engine = "aircrack"
        self.session_id: str | None = None
        self.bssid: str | None = None
        self.wordlist: str | None = None
        self.tested = 0
        self.total: int | None = None
        self.rate: float | None = None
        self.key: str | None = None
        self.message: str | None = None

    def status_info(self) -> CrackStatus:
        return CrackStatus(
            state=self.state, engine=self.engine, session_id=self.session_id, bssid=self.bssid,
            wordlist=self.wordlist, tested=self.tested, total=self.total,
            rate=self.rate, key=self.key, message=self.message,
        )

    async def start(
        self, session_id: str, wordlist: str | None, authorized: bool, engine: str = "aircrack"
    ) -> CrackStatus:
        if self._task is not None and not self._task.done():
            raise CrackBusy()

        session = self.capture.sessions.get(session_id)
        if session is None:
            raise CrackNotFound()
        bssid = session.target_bssid

        if not bssid:
            raise CrackRefused("Session has no target BSSID to authorize against.")
        if not self.scope.contains(bssid):
            self.audit.record("crack.refused", "refused", target_bssid=bssid, detail="not in scope")
            raise CrackRefused(f"{bssid} is not in the authorized scope allowlist.")
        if not authorized:
            self.audit.record("crack.refused", "refused", target_bssid=bssid, detail="not authorized")
            raise CrackRefused("Explicit authorization is required.")

        wl = wordlist or self.default_wordlist
        cap = self.capture.pcap_path(session_id)
        if not self.mock:
            if not cap:
                raise CrackRefused("No pcap/handshake for this session.")
            if not os.path.isfile(wl):
                raise CrackRefused(f"Wordlist not found: {wl} (gunzip rockyou.txt.gz?)")

        self._reset()
        self.state = "running"
        self.engine = "hashcat" if engine == "hashcat" else "aircrack"
        self.session_id = session_id
        self.bssid = bssid
        self.wordlist = wl
        self.audit.record(
            "crack.start", "ok", target_bssid=bssid, detail=f"{self.engine} wordlist={wl}"
        )
        self._task = asyncio.create_task(self._run(bssid, wl, cap))
        return self.status_info()

    async def _run(self, bssid: str, wordlist: str, cap: str | None) -> None:
        try:
            if self.mock:
                await asyncio.sleep(0)
                self.tested, self.total, self.rate = 1337, 14344391, 250.0
                self.key = "mock-passphrase"
                self.state = "found"
                self.message = f"Key found (mock, {self.engine})."
                self.audit.record("crack.done", "ok", target_bssid=bssid, detail="found (mock)")
                return
            if self.engine == "hashcat":
                await self._run_hashcat(bssid, wordlist, cap)
            else:
                await self._run_aircrack(bssid, wordlist, cap)
        except asyncio.CancelledError:
            self.state = "stopped"
            self.message = "Stopped."
            raise
        except Exception as e:
            self.state = "failed"
            self.message = str(e)
            self.audit.record("crack.done", "error", target_bssid=bssid, detail=str(e)[:200])

    async def _run_aircrack(self, bssid: str, wordlist: str, cap: str | None) -> None:
        self._proc = await asyncio.create_subprocess_exec(
            "aircrack-ng", "-w", wordlist, "-b", bssid, cap,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.STDOUT,
        )
        buf = ""
        while True:
            chunk = await self._proc.stdout.read(4096)
            if not chunk:
                break
            buf += chunk.decode(errors="replace")
            buf = buf[-8000:]
            p = parse_aircrack_progress(buf)
            if "tested" in p:
                self.tested, self.total, self.rate = p["tested"], p["total"], p["rate"]
            if "key" in p:
                self.key = p["key"]
                self.state = "found"
                break
        if self._proc.returncode is None:
            self._proc.terminate()
        await self._proc.wait()

        if self.state == "found":
            self.message = "Key found."
            self.audit.record("crack.done", "ok", target_bssid=bssid, detail=f"key length {len(self.key or '')}")
        else:
            self.state = "exhausted"
            self.message = "Wordlist exhausted — no key found."
            self.audit.record("crack.done", "info", target_bssid=bssid, detail="exhausted")

    async def _run_hashcat(self, bssid: str, wordlist: str, cap: str | None) -> None:
        """Modern path: convert pcap → 22000 (hcxpcapngtool), crack with hashcat -m 22000."""
        tmp = tempfile.mkdtemp(prefix="wd_crack_")
        hashfile = os.path.join(tmp, "hash.22000")
        outfile = os.path.join(tmp, "cracked.txt")
        try:
            # 1. pcap → hashcat 22000 (PMKID + EAPOL) via hcxpcapngtool.
            conv = await asyncio.create_subprocess_exec(
                "hcxpcapngtool", "-o", hashfile, cap,
                stdout=asyncio.subprocess.DEVNULL, stderr=asyncio.subprocess.DEVNULL,
            )
            await conv.wait()
            if not os.path.isfile(hashfile) or os.path.getsize(hashfile) == 0:
                self.state = "failed"
                self.message = "No crackable hash in the pcap (need a handshake or PMKID)."
                self.audit.record("crack.done", "error", target_bssid=bssid, detail="no 22000 hash")
                return

            # 2. hashcat -m 22000 (WPA-PBKDF2-PMKID+EAPOL), JSON status for progress.
            self._proc = await asyncio.create_subprocess_exec(
                "hashcat", "-m", "22000", "-a", "0",
                "--status", "--status-json", "--status-timer", "2",
                "--potfile-disable", "--outfile-format", "2", "-o", outfile,
                hashfile, wordlist,
                stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.STDOUT,
            )
            buf = ""
            while True:
                chunk = await self._proc.stdout.read(4096)
                if not chunk:
                    break
                buf += chunk.decode(errors="replace")
                buf = buf[-16000:]
                p = parse_hashcat_status(buf)
                if "tested" in p:
                    self.tested, self.total = p["tested"], p["total"]
                if p.get("rate") is not None:
                    self.rate = p["rate"]
                if p.get("recovered"):
                    break
            if self._proc.returncode is None:
                self._proc.terminate()
            await self._proc.wait()

            # 3. the recovered passphrase lands in the outfile (format 2 = plain).
            key = None
            if os.path.isfile(outfile):
                with open(outfile, errors="replace") as f:
                    key = f.readline().strip() or None
            if key:
                self.key = key
                self.state = "found"
                self.message = "Key found (hashcat)."
                self.audit.record("crack.done", "ok", target_bssid=bssid, detail="found (hashcat)")
            else:
                self.state = "exhausted"
                self.message = "Wordlist exhausted — no key found (hashcat)."
                self.audit.record("crack.done", "info", target_bssid=bssid, detail="exhausted (hashcat)")
        finally:
            for p in (hashfile, outfile):
                try:
                    os.remove(p)
                except OSError:
                    pass
            try:
                os.rmdir(tmp)
            except OSError:
                pass

    async def stop(self) -> CrackStatus:
        if self._proc is not None and self._proc.returncode is None:
            self._proc.terminate()
        if self._task is not None and not self._task.done():
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        if self.state == "running":
            self.state = "stopped"
        return self.status_info()
