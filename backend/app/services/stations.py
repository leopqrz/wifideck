"""Client/station intelligence from airodump CSV: who's around, what SSIDs they're
probing for, and whether they're using a randomized (private) MAC.

Passive — this only reads what monitor mode already captured; it never transmits.
"""
from __future__ import annotations

import re

from ..models.station import Station

_MAC_RE = re.compile(r"^[0-9A-Fa-f:]{17}$")

# The locally-administered bit (0x02 in the first octet) marks a randomized/private
# MAC — modern phones rotate these for privacy. Worth surfacing on its own.
_LOCAL_BIT = 0x02

# A tiny built-in OUI map (extend, or wire a full oui.txt later). Best-effort.
_OUI: dict[str, str] = {
    "B8:27:EB": "Raspberry Pi", "DC:A6:32": "Raspberry Pi", "E4:5F:01": "Raspberry Pi",
    "F0:18:98": "Apple", "A4:83:E7": "Apple", "3C:06:30": "Apple", "AC:BC:32": "Apple",
    "3C:5A:B4": "Google", "00:1A:11": "Google", "F4:F5:E8": "Google",
    "00:0C:29": "VMware", "00:50:56": "VMware", "00:1B:44": "SanDisk",
    "FC:FB:FB": "Cisco", "00:1D:0F": "TP-Link", "50:C7:BF": "TP-Link",
    "18:FE:34": "Espressif", "24:0A:C4": "Espressif", "A0:20:A6": "Espressif",
}


def _to_int(s: str) -> int | None:
    try:
        return int(s.strip())
    except (ValueError, TypeError):
        return None


def vendor_for(mac: str) -> str | None:
    m = mac.upper().strip()
    if len(m) < 8:
        return None
    try:
        first = int(m[0:2], 16)
    except ValueError:
        return None
    if first & _LOCAL_BIT:
        return "randomized"
    return _OUI.get(m[0:8])


def parse_airodump_stations(text: str) -> list[Station]:
    section = "ap"
    out: list[Station] = []
    for raw in text.splitlines():
        line = raw.strip()
        if not line:
            continue
        if line.startswith("BSSID,"):
            section = "ap"
            continue
        if line.startswith("Station MAC,"):
            section = "station"
            continue
        if section != "station":
            continue
        cells = [c.strip() for c in raw.split(",")]
        if not cells or not _MAC_RE.match(cells[0]):
            continue
        mac = cells[0].upper()
        bssid = cells[5].upper() if len(cells) > 5 and _MAC_RE.match(cells[5]) else None
        probes = [p for p in (c.strip() for c in cells[6:]) if p] if len(cells) > 6 else []
        out.append(Station(
            mac=mac, vendor=vendor_for(mac),
            signal_dbm=_to_int(cells[3]) if len(cells) > 3 else None,
            bssid=bssid, probes=probes,
            packets=_to_int(cells[4]) or 0 if len(cells) > 4 else 0,
            first_seen=cells[1] if len(cells) > 1 else None,
            last_seen=cells[2] if len(cells) > 2 else None,
        ))
    return out


class StationTracker:
    """Accumulates station sightings across polls, keyed by MAC."""

    def __init__(self) -> None:
        self._by_mac: dict[str, Station] = {}

    def observe(self, stations: list[Station]) -> None:
        for s in stations:
            cur = self._by_mac.get(s.mac)
            if cur is None:
                self._by_mac[s.mac] = s
                continue
            cur.last_seen = s.last_seen or cur.last_seen
            if s.signal_dbm is not None:
                cur.signal_dbm = s.signal_dbm
            cur.bssid = s.bssid or cur.bssid
            cur.packets = max(cur.packets, s.packets)
            cur.probes = sorted(set(cur.probes) | set(s.probes))

    def list(self) -> list[Station]:
        return sorted(self._by_mac.values(), key=lambda s: s.last_seen or "", reverse=True)


class StationService:
    def __init__(self, mock: bool) -> None:
        self.mock = mock
        self.tracker = StationTracker()

    def observe_csv(self, csv_text: str) -> None:
        self.tracker.observe(parse_airodump_stations(csv_text))

    def list(self) -> list[Station]:
        if self.mock and not self.tracker._by_mac:
            from . import fixtures
            return parse_airodump_stations(fixtures.AIRODUMP_CSV)
        return self.tracker.list()
