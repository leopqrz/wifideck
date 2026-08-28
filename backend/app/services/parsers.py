"""Pure parsers for wireless tool output.

Kept free of I/O so they're trivially unit-tested against recorded fixtures.
Each takes raw command text and returns plain data.
"""
from __future__ import annotations

import re


def parse_iw_dev(text: str) -> list[dict]:
    """Parse `iw dev` into [{interface, type}, ...] (first-seen order)."""
    ifaces: list[dict] = []
    current: dict | None = None
    for line in text.splitlines():
        s = line.strip()
        if s.startswith("Interface "):
            current = {"interface": s.split(None, 1)[1].strip(), "type": None}
            ifaces.append(current)
        elif s.startswith("type ") and current is not None:
            current["type"] = s.split(None, 1)[1].strip()
    return ifaces


def parse_iw_link(text: str) -> dict:
    """Parse `iw dev <if> link` → ssid/signal/bitrate/freq. Empty dict if unassociated."""
    if not text or text.strip().lower().startswith("not connected"):
        return {}
    out: dict = {}
    for line in text.splitlines():
        s = line.strip()
        if s.startswith("SSID:"):
            out["ssid"] = s.split(":", 1)[1].strip()
        elif s.startswith("freq:"):
            try:
                out["freq_mhz"] = int(float(s.split(":", 1)[1].strip()))
            except ValueError:
                pass
        elif s.startswith("signal:"):
            m = re.search(r"(-?\d+)", s)
            if m:
                out["signal_dbm"] = int(m.group(1))
        elif s.startswith("tx bitrate:"):
            m = re.search(r"([\d.]+)\s*MBit/s", s)
            if m:
                out["tx_bitrate_mbps"] = float(m.group(1))
    return out


def parse_ip_addr(text: str) -> str | None:
    """Extract the first IPv4 (a.b.c.d/nn) from `ip -o -4 addr show <if>`."""
    m = re.search(r"inet\s+(\d+\.\d+\.\d+\.\d+/\d+)", text)
    return m.group(1) if m else None


def driver_from_path(text: str) -> str | None:
    """Given the target of /sys/class/net/<if>/device/driver, return the driver name."""
    text = text.strip()
    if not text:
        return None
    return text.rstrip("/").rsplit("/", 1)[-1]


def band_for_freq(freq_mhz: int | None) -> str | None:
    if freq_mhz is None:
        return None
    if 2400 <= freq_mhz < 2500:
        return "2.4 GHz"
    if 4900 <= freq_mhz < 5900:
        return "5 GHz"
    if freq_mhz >= 5925:
        return "6 GHz"
    return None
