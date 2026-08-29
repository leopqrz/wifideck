"""ModeService — switch the adapter between MANAGED and MONITOR.

Runs the proven iw / nmcli mode-switch sequences, wrapped in a state
machine that serializes switches: a request that arrives mid-transition is
rejected (ModeBusy → HTTP 409) rather than corrupting the radio state.

Requires root in real mode (iw / ip / nmcli). Mock mode is a no-op
that still exercises the command sequence for tests.
"""
from __future__ import annotations

import asyncio
import contextlib
from typing import Literal

from ..models.status import Status
from .known import KnownNetworks
from .runner import CommandRunner
from .scan import ScanService
from .status import StatusService

Target = Literal["managed", "monitor"]


class ModeBusy(Exception):
    """A mode switch is already in progress."""


class ModeError(Exception):
    """A mode switch failed."""


class ModeService:
    def __init__(
        self,
        runner: CommandRunner,
        status: StatusService,
        scan: ScanService | None = None,
        known: KnownNetworks | None = None,
    ) -> None:
        self.runner = runner
        self.status = status
        self.scan = scan
        self.known = known
        self._lock = asyncio.Lock()
        self.transition: str | None = None  # e.g. "to_monitor" while switching

    @property
    def busy(self) -> bool:
        return self._lock.locked()

    async def set_mode(self, target: Target, channel: int | None = None) -> Status:
        if self.busy:
            raise ModeBusy()

        # Uncontended acquire does not yield, so the busy-check above is race-free.
        async with self._lock:
            self.transition = f"to_{target}"
            try:
                iface = (await self.status.snapshot()).interface
                if not iface:
                    raise ModeError("No Wi-Fi interface found (is the ALFA connected?).")
                if target == "monitor":
                    await self._to_monitor(iface, channel)
                else:
                    await self._to_managed(iface)
                return await self.status.snapshot()
            finally:
                self.transition = None

    async def _to_monitor(self, iface: str, channel: int | None) -> None:
        # Snapshot a fresh MANAGED scan NOW, while the link is still up — monitor
        # mode can't enumerate SSIDs on this adapter, so this remembered list is
        # what the deauth / capture pickers use (each entry keeps its channel). A
        # scan failure must never block the switch.
        if self.scan is not None and self.known is not None:
            with contextlib.suppress(Exception):
                self.known.save(await self.scan.scan_managed())

        # Tell NetworkManager to leave this interface alone (it releases
        # wpa_supplicant for the device). We do NOT kill NetworkManager — doing so
        # left the device 'unmanaged' after switching back, so scans stopped.
        await self.runner.run(["nmcli", "device", "set", iface, "managed", "no"])
        await self.runner.run(["ip", "link", "set", iface, "down"])
        await self._require(
            ["iw", "dev", iface, "set", "type", "monitor"],
            "Failed to set monitor mode",
        )
        await self.runner.run(["ip", "link", "set", iface, "up"])
        if channel is not None:
            await self._require(
                ["iw", "dev", iface, "set", "channel", str(channel)],
                f"Failed to set channel {channel}",
            )

    async def _to_managed(self, iface: str) -> None:
        # A monitor-mode scan (airodump-ng) keeps the adapter attached in monitor,
        # which makes `iw set type managed` a silent no-op — the card stays in
        # monitor while the command still returns success. Clear it first.
        await self._kill_scanners()
        await self._managed_sequence(iface)
        # Some drivers report success but stay in monitor if a scan re-grabbed the
        # radio mid-switch — verify, retry once, then fail loudly rather than
        # returning a misleading "ok" that leaves the UI to time out.
        if await self._is_monitor():
            await self._kill_scanners()
            await self._managed_sequence(iface)
            if await self._is_monitor():
                raise ModeError(
                    "Adapter is still in MONITOR after switching. A monitor scan "
                    "may be holding it — stop any scan/capture and try again."
                )

    async def _managed_sequence(self, iface: str) -> None:
        await self.runner.run(["ip", "link", "set", iface, "down"])
        await self._require(
            ["iw", "dev", iface, "set", "type", "managed"],
            "Failed to set managed mode",
        )
        await self.runner.run(["ip", "link", "set", iface, "up"])
        # Hand the interface back to NetworkManager, reconnect, and kick a scan so
        # the network list repopulates promptly. (No NM restart — it was never killed.)
        await self.runner.run(["nmcli", "device", "set", iface, "managed", "yes"])
        await self.runner.run(["nmcli", "device", "connect", iface])
        await self.runner.run(["nmcli", "device", "wifi", "rescan"])

    async def _kill_scanners(self) -> None:
        # airodump-ng is the only thing WiFiDeck runs that pins monitor mode.
        # pkill exits non-zero when nothing matches — harmless, so it's not _require'd.
        await self.runner.run(["pkill", "-f", "airodump-ng"])

    async def _is_monitor(self) -> bool:
        return ((await self.status.snapshot()).mode or "").upper() == "MONITOR"

    async def _require(self, args: list[str], msg: str) -> None:
        result = await self.runner.run(args)
        if not result.ok:
            detail = result.stderr.strip() or result.stdout.strip() or f"exit {result.returncode}"
            raise ModeError(f"{msg}: {detail}")
