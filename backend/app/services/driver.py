"""DriverService — report the bound driver, kernel, and DKMS module state.

Read-only: switching drivers (blacklist + dkms install) is a deliberate, risky
root operation left to the documented CLI steps, not automated here.
"""
from __future__ import annotations

import re

from ..models.driver import DkmsModule, DriverInfo
from .runner import CommandRunner
from .status import StatusService

# Known RTL8812AU driver modules, most-preferred first.
KNOWN_MODULES = ("88XXau", "8812au", "rtw88_8812au")

RECOMMENDED = "88XXau"
# Module names that mean "the morrownr/aircrack 88XXau out-of-tree driver".
RECOMMENDED_ALIASES = {"88XXau", "8812au", "rtl88xxau"}


def parse_dkms_status(text: str) -> list[DkmsModule]:
    """Parse `dkms status` (handles both 'name/ver: status' and
    'name/ver, kernel, arch: status' forms)."""
    mods: list[DkmsModule] = []
    for line in text.splitlines():
        line = line.strip()
        if not line or ":" not in line:
            continue
        left, _, status = line.rpartition(":")
        namever = left.split(",")[0].strip()
        name, _, version = namever.partition("/")
        mods.append(DkmsModule(name=name.strip(), version=version.strip(), status=status.strip()))
    return mods


class DriverService:
    def __init__(self, runner: CommandRunner, status: StatusService) -> None:
        self.runner = runner
        self.status = status

    async def _loaded_module(self) -> str | None:
        """Which known driver module is loaded (works even with no interface)."""
        lsmod = (await self.runner.run(["lsmod"])).stdout
        for mod in KNOWN_MODULES:
            if re.search(rf"^{re.escape(mod)}\b", lsmod, re.MULTILINE):
                return mod
        return None

    async def info(self) -> DriverInfo:
        # Prefer the driver bound to the live interface; fall back to the loaded
        # module so the panel still reports something when the adapter is unplugged.
        current = (await self.status.snapshot()).driver or await self._loaded_module()
        kernel = (await self.runner.run(["uname", "-r"])).stdout.strip()
        dkms = parse_dkms_status((await self.runner.run(["dkms", "status"])).stdout)

        using = bool(current and current in RECOMMENDED_ALIASES)
        note = None
        hint: list[str] = []
        if not using:
            note = (
                "In-kernel rtw88_8812au is loaded — reliable for MANAGED mode but weak "
                "for injection. The 88XXau DKMS driver is recommended for monitor/injection."
            )
            xxau = next((m for m in dkms if "88xxau" in m.name.lower()), None)
            if xxau:
                hint = [
                    f"sudo dkms install {xxau.name}/{xxau.version} -k {kernel}",
                    "printf 'blacklist rtw88_8812au\\nblacklist rtw88_usb\\n' | "
                    "sudo tee /etc/modprobe.d/blacklist-rtw88-alfa.conf",
                    "sudo modprobe -r rtw88_8812au; sudo modprobe 88XXau",
                ]

        return DriverInfo(
            current=current,
            kernel=kernel,
            dkms=dkms,
            recommended=RECOMMENDED,
            using_recommended=using,
            note=note,
            install_hint=hint,
        )
