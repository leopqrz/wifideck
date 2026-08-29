"""ShareService — NAT the ALFA's uplink to the host (macOS).

The NAT sharing logic: enable IP forwarding, MASQUERADE out the
uplink, forward from the downlink, and make the uplink the preferred default
route so forwarded traffic doesn't loop back to the Mac.

Requires root in real mode (iptables/sysctl/ip route). Mock mode toggles an
in-memory flag and reports fixture addresses.
"""
from __future__ import annotations

import re

from ..models.share import ShareStatus
from .parsers import parse_ip_addr
from .runner import CommandRunner
from .status import StatusService


class ShareError(Exception):
    """Sharing could not be toggled."""


def parse_default_gateway(text: str) -> str | None:
    m = re.search(r"default\s+via\s+(\d+\.\d+\.\d+\.\d+)", text)
    return m.group(1) if m else None


def mac_commands(vm_ip: str | None) -> list[str]:
    ip = vm_ip or "<VM-IP>"
    return [
        f"sudo route -n add -net 0.0.0.0/1 {ip}",
        f"sudo route -n add -net 128.0.0.0/1 {ip}",
        "networksetup -setdnsservers Wi-Fi 1.1.1.1",
    ]


class ShareService:
    def __init__(
        self, runner: CommandRunner, status: StatusService, downlink: str, mock: bool
    ) -> None:
        self.runner = runner
        self.status = status
        self.downlink = downlink
        self.mock = mock
        self._mock_active = False

    async def _uplink(self) -> str | None:
        return (await self.status.snapshot()).interface

    async def _vm_ip(self) -> str | None:
        r = await self.runner.run(["ip", "-o", "-4", "addr", "show", self.downlink])
        cidr = parse_ip_addr(r.stdout)
        return cidr.split("/")[0] if cidr else None

    async def _gateway(self, uplink: str) -> str | None:
        r = await self.runner.run(["ip", "route", "show", "dev", uplink])
        return parse_default_gateway(r.stdout)

    async def _is_active(self, uplink: str | None) -> bool:
        if self.mock:
            return self._mock_active
        fwd = (await self.runner.run(["cat", "/proc/sys/net/ipv4/ip_forward"])).stdout.strip()
        if fwd != "1" or not uplink:
            return False
        rule = await self.runner.run(
            ["iptables", "-t", "nat", "-C", "POSTROUTING", "-o", uplink, "-j", "MASQUERADE"]
        )
        return rule.ok

    async def status_info(self) -> ShareStatus:
        uplink = await self._uplink()
        vm_ip = await self._vm_ip()
        return ShareStatus(
            active=await self._is_active(uplink),
            uplink=uplink,
            downlink=self.downlink,
            vm_ip=vm_ip,
            gateway=await self._gateway(uplink) if uplink else None,
            mac_commands=mac_commands(vm_ip),
        )

    async def enable(self) -> ShareStatus:
        uplink = await self._uplink()
        if not uplink:
            raise ShareError("No uplink (Wi-Fi) interface — connect the ALFA first.")

        if not self.mock:
            up, down = uplink, self.downlink
            await self.runner.run(["sysctl", "-w", "net.ipv4.ip_forward=1"])
            await self._ensure(["-t", "nat", "POSTROUTING", "-o", up, "-j", "MASQUERADE"])
            await self._ensure(["FORWARD", "-i", down, "-o", up, "-j", "ACCEPT"])
            await self._ensure(
                ["FORWARD", "-i", up, "-o", down, "-m", "state",
                 "--state", "RELATED,ESTABLISHED", "-j", "ACCEPT"]
            )
            gw = await self._gateway(up)
            if gw:
                await self.runner.run(
                    ["ip", "route", "replace", "default", "via", gw, "dev", up, "metric", "50"]
                )
        else:
            self._mock_active = True
        return await self.status_info()

    async def disable(self) -> ShareStatus:
        uplink = await self._uplink()
        if not self.mock and uplink:
            up, down = uplink, self.downlink
            await self.runner.run(
                ["iptables", "-t", "nat", "-D", "POSTROUTING", "-o", up, "-j", "MASQUERADE"]
            )
            await self.runner.run(["iptables", "-D", "FORWARD", "-i", down, "-o", up, "-j", "ACCEPT"])
            await self.runner.run(
                ["iptables", "-D", "FORWARD", "-i", up, "-o", down, "-m", "state",
                 "--state", "RELATED,ESTABLISHED", "-j", "ACCEPT"]
            )
            await self.runner.run(["sysctl", "-w", "net.ipv4.ip_forward=0"])
        else:
            self._mock_active = False
        return await self.status_info()

    async def _ensure(self, rule: list[str]) -> None:
        """Add an iptables rule only if it isn't already present."""
        table = rule[:2] if rule[0] == "-t" else []
        spec = rule[2:] if rule[0] == "-t" else rule
        check = await self.runner.run(["iptables", *table, "-C", *spec])
        if not check.ok:
            await self.runner.run(["iptables", *table, "-A", *spec])
