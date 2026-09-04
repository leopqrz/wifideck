"""Radio backends — one per RF path, each reporting capabilities so WiFiDeck adapts
to what the radio can do rather than assuming a Linux wlan interface.

  * LinuxNl80211Backend  — the VM path (nl80211 / airodump / iw).
  * MacosRtl8812auBackend — native macOS libusb (xen-proc/rtl8812au-macos). PROVEN
    to do stable 2.4/5 GHz monitor RX; see docs/RADIO-ENVIRONMENT.md.

Selection is by WIFIDECK_RADIO_BACKEND (auto|linux|macos|mock); auto picks by OS.
"""
from __future__ import annotations

import asyncio
import os
import platform
import re

from ..models.radio import RadioCapabilities, RadioInfo
from .runner import CommandRunner
from .status import StatusService


def resolve_backend_name(mock: bool, pref: str = "auto") -> str:
    """The active backend name, without constructing a backend (cheap, side-effect free)."""
    if mock or pref == "mock":
        return "mock"
    if pref == "macos" or (pref == "auto" and platform.system() == "Darwin"):
        return "macos-rtl8812au"
    return "linux-nl80211"


def macos_capture_argv(
    rtl_dir: str, channel: int | None, out_path: str, seconds: int = 3600
) -> list[str]:
    """argv to run the macOS libusb capture (xen-proc/rtl8812au-macos tools/capture.py)."""
    py = os.path.join(rtl_dir, ".venv", "bin", "python") if rtl_dir else "python3"
    cap = os.path.join(rtl_dir, "tools", "capture.py") if rtl_dir else "tools/capture.py"
    return [py, cap, "-c", str(channel or 6), "-t", str(seconds), "-o", out_path]


async def macos_scan(rtl_dir: str, channel: int = 6, seconds: int = 4):
    """macOS 'scan' — a brief monitor capture on one channel, parsed for beacons →
    the APs heard on that channel. Returns [] on any failure (adapter off the bus, etc.)."""
    import os
    import tempfile

    from .scan import parse_tshark_beacons

    tmp = tempfile.mkdtemp(prefix="wd_scan_")
    pcap = os.path.join(tmp, "scan.pcap")
    argv = macos_capture_argv(rtl_dir, channel, pcap, seconds=max(2, seconds))
    try:
        cap = await asyncio.create_subprocess_exec(
            *argv, stdout=asyncio.subprocess.DEVNULL, stderr=asyncio.subprocess.DEVNULL
        )
        await asyncio.wait_for(cap.communicate(), timeout=seconds + 20)
    except (FileNotFoundError, OSError, asyncio.TimeoutError):
        return []
    if not os.path.isfile(pcap):
        return []
    try:
        ts = await asyncio.create_subprocess_exec(
            "tshark", "-r", pcap, "-n", "-Y", "wlan.fc.type_subtype==0x08",
            "-T", "fields", "-e", "wlan.bssid", "-e", "wlan.ssid", "-e", "wlan_radio.channel",
            stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.DEVNULL,
        )
        out, _ = await asyncio.wait_for(ts.communicate(), timeout=25)
    except (FileNotFoundError, OSError, asyncio.TimeoutError):
        return []
    return parse_tshark_beacons(out.decode(errors="replace"))

_ACH_NOTE = (
    "monitor advertised by phy, but rtw88 delivers no RX on this kernel — use the "
    "macOS backend (docs/RADIO-ENVIRONMENT.md)"
)


def _bands_from_freqs(text: str) -> list[str]:
    bands: list[str] = []
    freqs = [int(m) for m in re.findall(r"(\d{4}) MHz", text)]
    if any(2400 <= f < 2500 for f in freqs):
        bands.append("2.4 GHz")
    if any(5000 <= f < 5900 for f in freqs):
        bands.append("5 GHz")
    if any(5925 <= f <= 7125 for f in freqs):
        bands.append("6 GHz")
    return bands


class LinuxNl80211Backend:
    name = "linux-nl80211"

    def __init__(self, runner: CommandRunner, status: StatusService) -> None:
        self.runner = runner
        self.status = status

    async def info(self) -> RadioInfo:
        snap = await self.status.snapshot()
        lsusb = (await self.runner.run(["lsusb"])).stdout
        phy = (await self.runner.run(["iw", "phy"])).stdout

        chipset = adapter = None
        if "0bda:8812" in lsusb or "RTL8812AU" in lsusb:
            chipset, adapter = "RTL8812AU", "ALFA AWUS036ACH (or RTL8812AU)"
        elif "mt7921" in lsusb.lower() or "0e8d:7961" in lsusb:
            chipset, adapter = "MT7921AU", "ALFA AWUS036AXML (MT7921AU)"

        modes = phy or ""
        bands = _bands_from_freqs(modes) or (["2.4 GHz", "5 GHz"] if chipset else [])
        caps = RadioCapabilities(
            managed=True,
            monitor_rx="* monitor" in modes,
            raw_tx=False,  # not runtime-detectable; validated by the acceptance test
            channel_control=True,
            ap_mode="* AP" in modes,
            radiotap=True,
            bands=bands,
        )
        notes: list[str] = []
        if (snap.driver or "").startswith("rtw88") and chipset == "RTL8812AU":
            notes.append(_ACH_NOTE)
            caps.monitor_rx = False  # be honest: rtw88 doesn't deliver RX for this chip
        return RadioInfo(
            backend=self.name, present=bool(snap.usb_present), adapter=adapter,
            chipset=chipset, driver=snap.driver, capabilities=caps, notes=notes,
        )


class MacosRtl8812auBackend:
    name = "macos-rtl8812au"

    async def _present(self) -> tuple[bool, str]:
        """Is 0bda:8812 on the USB bus? pyusb if available, else system_profiler (macOS)."""
        try:
            import usb.core

            if usb.core.find(idVendor=0x0BDA, idProduct=0x8812) is not None:
                return True, "libusb sees 0bda:8812"
        except Exception:
            pass
        try:
            proc = await asyncio.create_subprocess_exec(
                "system_profiler", "SPUSBDataType",
                stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.DEVNULL,
            )
            out, _ = await asyncio.wait_for(proc.communicate(), timeout=8)
            if b"0x8812" in out:
                return True, "system_profiler sees 0x8812"
            return False, "adapter not on the USB bus (plug it into macOS)"
        except (FileNotFoundError, OSError, asyncio.TimeoutError):
            return False, "presence unknown (no pyusb / system_profiler)"

    async def info(self) -> RadioInfo:
        present, note_present = await self._present()
        return RadioInfo(
            backend=self.name, present=present,
            adapter="ALFA AWUS036ACH", chipset="RTL8812AU",
            driver="libusb (rtl8812au-macos)",
            capabilities=RadioCapabilities(
                managed=False, monitor_rx=True, raw_tx=True, channel_control=True,
                ap_mode=False, radiotap=True, bands=["2.4 GHz", "5 GHz"],
            ),
            notes=[
                "verified: stable 2.4 + 5 GHz monitor RX (docs/RADIO-ENVIRONMENT.md)",
                "5 GHz TX limited to channel 36 (per-rate power calibration)",
                "no managed mode / not a macOS Wi-Fi interface; LED not driven",
                note_present,
            ],
        )


class MockBackend:
    name = "mock"

    async def info(self) -> RadioInfo:
        return RadioInfo(
            backend=self.name, present=True, adapter="MockNet Adapter",
            chipset="MOCK8812", driver="mock",
            capabilities=RadioCapabilities(
                managed=True, monitor_rx=True, raw_tx=True, channel_control=True,
                ap_mode=True, radiotap=True, bands=["2.4 GHz", "5 GHz"],
            ),
            notes=["mock backend — fixtures, no hardware"],
        )


def select_backend(mock: bool, pref: str = "auto"):
    if mock or pref == "mock":
        return MockBackend()
    if pref == "macos" or (pref == "auto" and platform.system() == "Darwin"):
        return MacosRtl8812auBackend()
    return LinuxNl80211Backend(
        CommandRunner(mock=mock), StatusService(CommandRunner(mock=mock))
    )
