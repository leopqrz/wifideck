"""Command runner abstraction — the seam between the app and the OS.

Real mode shells out to system tools (iw, nmcli, iptables, airodump-ng).
Mock mode returns recorded fixtures so the whole app runs with no hardware.
Phase 0 only establishes the abstraction; later phases add concrete callers.
"""
from __future__ import annotations

import asyncio
from dataclasses import dataclass

from ..config import settings


@dataclass
class CommandResult:
    returncode: int
    stdout: str
    stderr: str

    @property
    def ok(self) -> bool:
        return self.returncode == 0


class CommandRunner:
    def __init__(self, mock: bool | None = None) -> None:
        self.mock = settings.mock if mock is None else mock

    async def run(self, args: list[str], timeout: float = 15.0) -> CommandResult:
        if self.mock:
            return self._mock(args)
        proc = await asyncio.create_subprocess_exec(
            *args,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        try:
            out, err = await asyncio.wait_for(proc.communicate(), timeout=timeout)
        except asyncio.TimeoutError:
            proc.kill()
            return CommandResult(124, "", f"timeout after {timeout}s")
        return CommandResult(proc.returncode or 0, out.decode(errors="replace"), err.decode(errors="replace"))

    def _mock(self, args: list[str]) -> CommandResult:
        # Placeholder for Phase 0. Phase 1+ maps commands to fixtures.
        return CommandResult(0, "", "")


runner = CommandRunner()
