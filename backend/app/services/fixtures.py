"""Recorded tool output for mock-adapter mode (WIFIDECK_MOCK=1).

Lets the whole app run with no ALFA attached, and drives the same parsers the
real path uses. All values are synthetic — documentation-range addresses
(RFC 5737 IPs, RFC 7042 locally-administered MACs) and placeholder SSIDs.
"""
from __future__ import annotations

# Mutable so a mock mode-switch is reflected by the next status read (otherwise the
# mode toggle appears to hang in mock mode). Reset between tests via reset_mock_mode.
_MOCK_MODE = "managed"


def reset_mock_mode() -> None:
    global _MOCK_MODE
    _MOCK_MODE = "managed"


LSUSB = (
    "Bus 003 Device 003: ID 0bda:8812 Realtek Semiconductor Corp. "
    "RTL8812AU 802.11a/b/g/n/ac 2T2R DB WLAN Adapter\n"
)

IW_DEV = """phy#2
\tInterface wlan0
\t\tifindex 4
\t\taddr 02:00:00:00:00:0a
\t\ttype managed
\t\ttxpower 36.00 dBm
"""

IW_LINK = """Connected to 02:00:00:00:00:01 (on wlan0)
\tSSID: MockNet-5G
\tfreq: 5785.0
\tsignal: -42 dBm
\trx bitrate: 468.0 MBit/s VHT-MCS 5 80MHz VHT-NSS 2
\ttx bitrate: 585.0 MBit/s VHT-MCS 7 80MHz VHT-NSS 2
"""

IP_ADDR = (
    "4: wlan0    inet 192.0.2.10/24 brd 192.0.2.255 scope global dynamic "
    "noprefixroute wlan0\\       valid_lft 6000sec preferred_lft 6000sec\n"
)

ETH0_ADDR = (
    "2: eth0    inet 192.0.2.128/24 brd 192.0.2.255 scope global dynamic "
    "noprefixroute eth0\\       valid_lft 1500sec preferred_lft 1500sec\n"
)

IP_ROUTE = "default via 192.0.2.1 dev wlan0 proto dhcp src 192.0.2.10 metric 600\n"

DRIVER_PATH = "/sys/bus/usb/drivers/rtw88_8812au\n"

# Terse `nmcli -f IN-USE,BSSID,SSID,CHAN,SIGNAL,SECURITY device wifi list`.
NMCLI_WIFI = (
    "*:02\\:00\\:00\\:00\\:00\\:01:MockNet-5G:157:100:WPA2 WPA3\n"
    " :02\\:00\\:00\\:00\\:00\\:02:TestAP-2G:6:92:WPA2\n"
    " :02\\:00\\:00\\:00\\:00\\:03:OpenLab:11:80:WPA2\n"
    " :02\\:00\\:00\\:00\\:00\\:04::1:64:WPA2\n"
)

KERNEL = "7.1.5+kali-arm64\n"

DKMS_STATUS = (
    "realtek-rtl8814au/5.8.5.1~git20250903.8d82854: added\n"
    "realtek-rtl88xxau/5.6.4.2~git20250330.c3fb89a: added\n"
)

# A small airodump-ng CSV (one AP with two associated stations).
AIRODUMP_CSV = """
BSSID, First time seen, Last time seen, channel, Speed, Privacy, Cipher, Authentication, Power, # beacons, # IV, LAN IP, ID-length, ESSID, Key

02:00:00:00:00:01, 2026-01-01 00:00:00, 2026-01-01 00:05:00, 157, 866, WPA2, CCMP, PSK, -42, 120, 0, 0. 0. 0. 0, 10, MockNet-5G,

Station MAC, First time seen, Last time seen, Power, # packets, BSSID, Probed ESSIDs
02:00:00:00:00:aa, 2026-01-01 00:00:00, 2026-01-01 00:05:00, -50, 40, 02:00:00:00:00:01,
02:00:00:00:00:bb, 2026-01-01 00:00:00, 2026-01-01 00:05:00, -60, 12, 02:00:00:00:00:01,
"""


def match(args: list[str]) -> tuple[int, str, str]:
    """Return (returncode, stdout, stderr) for a mocked command."""
    cmd = args[0] if args else ""
    if cmd == "lsusb":
        return (0, LSUSB, "")
    if cmd == "nmcli" and "wifi" in args and "list" in args:
        return (0, NMCLI_WIFI, "")
    if cmd == "iw":
        global _MOCK_MODE
        if "set" in args and "type" in args:
            # mock mode switch: remember the new type so the next status reflects it
            _MOCK_MODE = args[-1]
            return (0, "", "")
        if args and args[-1] == "link":
            return (0, IW_LINK, "")
        return (0, IW_DEV.replace("type managed", f"type {_MOCK_MODE}"), "")
    if cmd == "readlink":
        return (0, DRIVER_PATH, "")
    if cmd == "ip":
        if "route" in args:
            return (0, IP_ROUTE, "")
        if "eth0" in args:
            return (0, ETH0_ADDR, "")
        return (0, IP_ADDR, "")
    if cmd == "cat" and args and "operstate" in args[-1]:
        return (0, "up\n", "")
    if cmd == "uname":
        return (0, KERNEL, "")
    if cmd == "dkms":
        return (0, DKMS_STATUS, "")
    if cmd == "sh" and any("BUILD_EXCLUSIVE" in a for a in args):
        return (0, 'BUILD_EXCLUSIVE_KERNEL_MAX="6.15"\n', "")
    return (0, "", "")
