"""ModeService — switch the adapter between MANAGED and MONITOR.

Mirrors the proven sequences from the scripts/wifi-monitor / wifi-managed
scripts, wrapped in a state machine that serializes switches: a request that
arrives mid-transition is rejected (ModeBusy → HTTP 409) rather than corrupting
the radio state.

Requires root in real mode (iw / ip / nmcli / airmon-ng). Mock mode is a no-op
that still exercises the command sequence for tests.
"""
from __future__ import annotations

import asyncio
from typing import Literal

from ..models.status import Status
from .runner import CommandRunner
from .status import StatusService

Target = Literal["managed", "monitor"]


class ModeBusy(Exception):
    """A mode switch is already in progress."""


class ModeError(Exception):
    """A mode switch failed."""


class ModeService:
    def __init__(self, runner: CommandRunner, status: StatusService) -> None:
        self.runner = runner
        self.status = status
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
        # Hand the interface off from NetworkManager and clear radio-grabbing daemons.
        await self.runner.run(["nmcli", "device", "set", iface, "managed", "no"])
        await self.runner.run(["airmon-ng", "check", "kill"])  # best-effort
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
        await self.runner.run(["ip", "link", "set", iface, "down"])
        await self._require(
            ["iw", "dev", iface, "set", "type", "managed"],
            "Failed to set managed mode",
        )
        await self.runner.run(["ip", "link", "set", iface, "up"])
        # Give the interface back to NetworkManager and let it reconnect.
        await self.runner.run(["nmcli", "device", "set", iface, "managed", "yes"])
        await self.runner.run(["systemctl", "restart", "NetworkManager"])
        await self.runner.run(["nmcli", "device", "connect", iface])

    async def _require(self, args: list[str], msg: str) -> None:
        result = await self.runner.run(args)
        if not result.ok:
            detail = result.stderr.strip() or result.stdout.strip() or f"exit {result.returncode}"
            raise ModeError(f"{msg}: {detail}")
