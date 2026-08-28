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

ETH0_ADDR = (
    "2: eth0    inet 172.16.91.128/24 brd 172.16.91.255 scope global dynamic "
    "noprefixroute eth0\\       valid_lft 1500sec preferred_lft 1500sec\n"
)

IP_ROUTE = "default via 10.0.0.1 dev wlan0 proto dhcp src 10.0.0.145 metric 600\n"

DRIVER_PATH = "/sys/bus/usb/drivers/rtw88_8812au\n"

# Terse `nmcli -f IN-USE,BSSID,SSID,CHAN,SIGNAL,SECURITY device wifi list`.
NMCLI_WIFI = (
    "*:96\\:04\\:E3\\:EC\\:AB\\:5A:Queiroz:157:100:WPA2 WPA3\n"
    " :58\\:CB\\:52\\:DE\\:18\\:41:High-Five Wifi:6:92:WPA2\n"
    " :78\\:8A\\:20\\:DD\\:DF\\:B3:MB:6:80:WPA2\n"
    " :86\\:76\\:3F\\:7F\\:7B\\:B2::1:64:WPA2\n"
)


# A small airodump-ng CSV (one AP with two associated stations).
AIRODUMP_CSV = """
BSSID, First time seen, Last time seen, channel, Speed, Privacy, Cipher, Authentication, Power, # beacons, # IV, LAN IP, ID-length, ESSID, Key

96:04:E3:EC:AB:5A, 2026-08-28 03:00:00, 2026-08-28 03:05:00, 157, 866, WPA2, CCMP, PSK, -42, 120, 0, 0. 0. 0. 0, 7, Queiroz,

Station MAC, First time seen, Last time seen, Power, # packets, BSSID, Probed ESSIDs
AA:BB:CC:DD:EE:FF, 2026-08-28 03:00:00, 2026-08-28 03:05:00, -50, 40, 96:04:E3:EC:AB:5A,
11:22:33:44:55:66, 2026-08-28 03:00:00, 2026-08-28 03:05:00, -60, 12, 96:04:E3:EC:AB:5A,
"""


KERNEL = "7.1.5+kali-arm64\n"

DKMS_STATUS = (
    "realtek-rtl8814au/5.8.5.1~git20250903.8d82854: added\n"
    "realtek-rtl88xxau/5.6.4.2~git20250330.c3fb89a: added\n"
)


def match(args: list[str]) -> tuple[int, str, str]:
    """Return (returncode, stdout, stderr) for a mocked command."""
    cmd = args[0] if args else ""
    if cmd == "lsusb":
        return (0, LSUSB, "")
    if cmd == "nmcli" and "wifi" in args and "list" in args:
        return (0, NMCLI_WIFI, "")
    if cmd == "iw":
        if args and args[-1] == "link":
            return (0, IW_LINK, "")
        return (0, IW_DEV, "")
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
    return (0, "", "")
