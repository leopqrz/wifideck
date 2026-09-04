"""Radio backends — one per RF path, each reporting capabilities so WiFiDeck adapts
to what the radio can do rather than assuming a Linux wlan interface.

  * LinuxNl80211Backend  — the VM path (nl80211 / airodump / iw).
  * MacosRtl8812auBackend — native macOS libusb (xen-proc/rtl8812au-macos). PROVEN
    to do stable 2.4/5 GHz monitor RX; see docs/RADIO-ENVIRONMENT.md.

Selection is by WIFIDECK_RADIO_BACKEND (auto|linux|macos|mock); auto picks by OS.
"""
from __future__ import annotations

import platform
import re

from ..models.radio import RadioCapabilities, RadioInfo
from .runner import CommandRunner
from .status import StatusService

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

    async def info(self) -> RadioInfo:
        present = False
        note_present = "live presence checked on macOS via libusb"
        try:  # pragma: no cover - only meaningful on macOS with pyusb installed
            import usb.core

            present = usb.core.find(idVendor=0x0BDA, idProduct=0x8812) is not None
            note_present = "libusb sees 0bda:8812" if present else "0bda:8812 not on USB"
        except Exception:
            pass
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
