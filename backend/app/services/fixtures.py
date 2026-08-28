"""Recorded tool output for mock-adapter mode (WIFIDECK_MOCK=1).

Lets the whole app run with no ALFA attached, and drives the same parsers the
real path uses. Values mirror a real AWUS036ACH associated to a 5 GHz network.
"""
from __future__ import annotations

LSUSB = (
    "Bus 003 Device 003: ID 0bda:8812 Realtek Semiconductor Corp. "
    "RTL8812AU 802.11a/b/g/n/ac 2T2R DB WLAN Adapter\n"
)

IW_DEV = """phy#2
\tInterface wlan0
\t\tifindex 4
\t\taddr 62:ce:f2:03:aa:ff
\t\ttype managed
\t\ttxpower 36.00 dBm
"""

IW_LINK = """Connected to 96:04:e3:ec:ab:5a (on wlan0)
\tSSID: Queiroz
\tfreq: 5785.0
\tsignal: -42 dBm
\trx bitrate: 468.0 MBit/s VHT-MCS 5 80MHz VHT-NSS 2
\ttx bitrate: 585.0 MBit/s VHT-MCS 7 80MHz VHT-NSS 2
"""

IP_ADDR = (
    "4: wlan0    inet 10.0.0.145/24 brd 10.0.0.255 scope global dynamic "
    "noprefixroute wlan0\\       valid_lft 6000sec preferred_lft 6000sec\n"
)

DRIVER_PATH = "/sys/bus/usb/drivers/rtw88_8812au\n"


def match(args: list[str]) -> tuple[int, str, str]:
    """Return (returncode, stdout, stderr) for a mocked command."""
    cmd = args[0] if args else ""
    if cmd == "lsusb":
        return (0, LSUSB, "")
    if cmd == "iw":
        if args and args[-1] == "link":
            return (0, IW_LINK, "")
        return (0, IW_DEV, "")
    if cmd == "readlink":
        return (0, DRIVER_PATH, "")
    if cmd == "ip":
        return (0, IP_ADDR, "")
    if cmd == "cat" and args and "operstate" in args[-1]:
        return (0, "up\n", "")
    return (0, "", "")
