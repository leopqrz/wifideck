"""Radio abstraction — describe a radio by what it can *do*, not by OS/interface.

WiFiDeck runs on Linux (nl80211/airodump) and macOS (libusb rtl8812au). Instead of
assuming "radio == a Linux wlan interface", every backend reports capabilities and
the app adapts to them.
"""
from __future__ import annotations

from pydantic import BaseModel


class RadioCapabilities(BaseModel):
    managed: bool = False          # can join networks / normal Wi-Fi
    monitor_rx: bool = False       # delivers raw 802.11 frames to userspace
    raw_tx: bool = False           # frame injection
    channel_control: bool = False
    ap_mode: bool = False
    radiotap: bool = False         # captures carry radiotap headers
    bands: list[str] = []          # e.g. ["2.4 GHz", "5 GHz", "6 GHz"]


class RadioInfo(BaseModel):
    backend: str                   # linux-nl80211 | macos-rtl8812au | mock
    present: bool = False
    adapter: str | None = None     # e.g. "ALFA AWUS036ACH"
    chipset: str | None = None     # e.g. "RTL8812AU"
    driver: str | None = None      # e.g. "rtw88_8812au" | "libusb (rtl8812au-macos)"
    capabilities: RadioCapabilities = RadioCapabilities()
    notes: list[str] = []          # caveats the doctor should surface
