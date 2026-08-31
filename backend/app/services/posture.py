"""Security-posture classifier — the Python mirror of the frontend `securityClass`
so the report matches the UI. The point: which networks are attackable, and why."""
from __future__ import annotations

from pydantic import BaseModel


class Posture(BaseModel):
    kind: str
    label: str
    tone: str  # ok | warn | crit | muted
    note: str


def classify_security(security: list[str]) -> Posture:
    s = [x.upper().strip() for x in security if x and x.strip()]

    def has(*keys: str) -> bool:
        return any(k in v for k in keys for v in s)

    is_open = len(s) == 0 or all(v in ("--", "OPN", "OPEN", "NONE") for v in s)
    wpa3 = has("WPA3", "SAE")
    wpa2 = has("WPA2", "RSN", "PSK") or ("WPA" in s)
    enterprise = has("802.1X", "EAP", "MGT", "ENTERPRISE")

    if is_open:
        return Posture(kind="open", label="OPEN", tone="crit",
                       note="no encryption — anyone can join and sniff traffic")
    if has("WEP"):
        return Posture(kind="wep", label="WEP", tone="crit",
                       note="obsolete cipher — crackable in minutes")
    if wpa3 and wpa2:
        return Posture(kind="wpa3-transition", label="WPA3-TRANSITION", tone="warn",
                       note="also accepts WPA2 — capture & crack the WPA2 fallback")
    if wpa3 and enterprise:
        return Posture(kind="enterprise", label="WPA3-ENTERPRISE", tone="muted",
                       note="RADIUS/802.1X — no PSK to crack")
    if wpa3:
        return Posture(kind="wpa3", label="WPA3 (SAE)", tone="ok",
                       note="SAE resists offline cracking — no capture-and-crack path")
    if enterprise:
        return Posture(kind="enterprise", label="802.1X", tone="muted",
                       note="enterprise auth — no PSK to capture/crack")
    if wpa2:
        return Posture(kind="wpa2", label="WPA2", tone="warn",
                       note="capture the 4-way handshake, then crack offline")
    return Posture(kind="unknown", label="/".join(security) or "?", tone="muted", note="")
