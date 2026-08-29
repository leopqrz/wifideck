"""ConnectService — join / leave / forget Wi-Fi networks via NetworkManager.

NetworkManager persists the connection profile (and password, in its keyring) on
a successful connect, so it auto-reconnects later — no password storage of our
own. Requires MANAGED mode and NM privilege (the service runs as root).
"""
from __future__ import annotations

import re

from .runner import CommandRunner
from .status import StatusService

_UNESCAPED_COLON = re.compile(r"(?<!\\):")


class ConnectError(Exception):
    pass


def _unescape(s: str) -> str:
    return s.replace("\\:", ":").replace("\\\\", "\\")


class ConnectService:
    def __init__(self, runner: CommandRunner, status: StatusService, mock: bool) -> None:
        self.runner = runner
        self.status = status
        self.mock = mock

    async def saved(self) -> list[str]:
        """SSIDs (connection names) NetworkManager already has saved."""
        if self.mock:
            return ["MockNet-5G", "TestAP-2G"]
        r = await self.runner.run(["nmcli", "-t", "-f", "NAME,TYPE", "connection", "show"])
        out: list[str] = []
        for line in r.stdout.splitlines():
            if not line.strip():
                continue
            parts = [_unescape(p) for p in _UNESCAPED_COLON.split(line)]
            if len(parts) >= 2 and "wireless" in parts[-1]:
                out.append(parts[0])
        return out

    async def connect(self, ssid: str, password: str | None, hidden: bool) -> str:
        if self.mock:
            return f"connected to {ssid} (mock)"
        snap = await self.status.snapshot()
        if snap.mode == "MONITOR":
            raise ConnectError("Adapter is in MONITOR mode — switch to MANAGED first.")

        args = ["nmcli", "device", "wifi", "connect", ssid]
        if password:
            args += ["password", password]
        if hidden:
            args += ["hidden", "yes"]
        if snap.interface:
            args += ["ifname", snap.interface]

        result = await self.runner.run(args, timeout=45)
        if not result.ok:
            detail = (result.stderr.strip() or result.stdout.strip() or "connection failed")
            raise ConnectError(detail[-200:])
        return (result.stdout.strip() or f"connected to {ssid}")[:200]

    async def disconnect(self) -> str:
        if self.mock:
            return "disconnected (mock)"
        iface = (await self.status.snapshot()).interface or "wlan0"
        result = await self.runner.run(["nmcli", "device", "disconnect", iface])
        if not result.ok:
            raise ConnectError(result.stderr.strip() or "disconnect failed")
        return f"disconnected {iface}"

    async def forget(self, ssid: str) -> str:
        """Delete the saved profile (and stored password) for an SSID."""
        if self.mock:
            return f"forgot {ssid} (mock)"
        result = await self.runner.run(["nmcli", "connection", "delete", "id", ssid])
        if not result.ok:
            raise ConnectError(result.stderr.strip() or f"no saved profile for {ssid}")
        return f"forgot {ssid}"
