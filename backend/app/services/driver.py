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


def _version_tuple(s: str) -> tuple[int, ...]:
    parts = re.findall(r"\d+", s)
    return tuple(int(p) for p in parts[:2]) if parts else (0,)


def kernel_buildable(kernel: str, kernel_max: str | None) -> bool:
    """True if `kernel` is within the DKMS driver's BUILD_EXCLUSIVE_KERNEL_MAX."""
    if not kernel_max:
        return True  # no declared limit -> assume it builds
    return _version_tuple(kernel) <= _version_tuple(kernel_max)


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

    async def _kernel_max(self) -> str | None:
        """The 88XXau DKMS driver's BUILD_EXCLUSIVE_KERNEL_MAX, if any."""
        r = await self.runner.run(
            ["sh", "-c",
             "grep -h BUILD_EXCLUSIVE_KERNEL_MAX /usr/src/realtek-rtl88xxau-*/dkms.conf 2>/dev/null | head -1"]
        )
        m = re.search(r"(\d+\.\d+)", r.stdout)
        return m.group(1) if m else None

    async def info(self) -> DriverInfo:
        # Prefer the driver bound to the live interface; fall back to the loaded
        # module so the panel still reports something when the adapter is unplugged.
        current = (await self.status.snapshot()).driver or await self._loaded_module()
        kernel = (await self.runner.run(["uname", "-r"])).stdout.strip()
        dkms = parse_dkms_status((await self.runner.run(["dkms", "status"])).stdout)

        kernel_max = await self._kernel_max()
        buildable = kernel_buildable(kernel, kernel_max)
        using = bool(current and current in RECOMMENDED_ALIASES)
        note = None
        hint: list[str] = []

        if not using and buildable:
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
        elif not using and not buildable:
            # The recommended driver won't build on this kernel — do NOT hand out the
            # blacklist commands, or they'd leave the adapter with no working driver.
            note = (
                f"In-kernel rtw88_8812au is loaded. The 88XXau DKMS driver does not support "
                f"this kernel (builds only up to {kernel_max}), so it can't be installed here — "
                f"keep the in-kernel driver and reduce -71 instability with USB 3.1 + a powered hub."
            )

        return DriverInfo(
            current=current,
            kernel=kernel,
            dkms=dkms,
            recommended=RECOMMENDED,
            using_recommended=using,
            recommended_buildable=buildable,
            kernel_max=kernel_max,
            note=note,
            install_hint=hint,
        )
