"""HandshakeVerifier — use tshark (Wireshark's engine) to check what a capture's
pcap actually contains BEFORE you spend a crack run on it.

Classifies the EAPOL-Key frames of the WPA 4-way handshake (M1–M4) from the
Key-Information bitfield, and flags a PMKID. A capture is "crackable" if it holds
enough of the handshake (an ANonce source + a MIC source) or a PMKID.
"""
from __future__ import annotations

from ..models.handshake import HandshakeInfo
from .runner import CommandRunner

# EAPOL-Key "Key Information" bit masks (IEEE 802.11).
_INSTALL = 0x0008
_ACK = 0x0040
_MIC = 0x0080
_SECURE = 0x0100


def _classify(ki: int) -> int | None:
    """Map an EAPOL-Key Key-Information field to its 4-way message number."""
    mic, ack = ki & _MIC, ki & _ACK
    secure, install = ki & _SECURE, ki & _INSTALL
    if ack and not mic:
        return 1  # M1: ANonce, from AP, no MIC
    if mic and ack and install:
        return 3  # M3: from AP, install bit set
    if mic and not ack and not secure:
        return 2  # M2: SNonce + MIC, from client
    if mic and not ack and secure:
        return 4  # M4: from client, secure set
    return None


def _to_int(s: str) -> int | None:
    s = s.strip()
    try:
        return int(s, 16) if s.lower().startswith("0x") else int(s)
    except (ValueError, TypeError):
        return None


def parse_eapol(text: str) -> HandshakeInfo:
    """Parse rows of `eapol.keydes.key_info [\\t eapol.keydes.data_len]`."""
    msgs: set[int] = set()
    pmkid = False
    frames = 0
    for line in text.splitlines():
        line = line.strip()
        if not line:
            continue
        parts = line.split("\t")
        ki = _to_int(parts[0]) if parts else None
        if ki is None:
            continue
        frames += 1
        m = _classify(ki)
        if m:
            msgs.add(m)
        # An M1 (ACK, no MIC) carrying key data is a PMKID KDE.
        dlen = _to_int(parts[1]) if len(parts) > 1 else None
        if m == 1 and dlen and dlen > 0:
            pmkid = True

    has_anonce = 1 in msgs or 3 in msgs   # ANonce comes from M1 or M3
    has_mic = 2 in msgs or 4 in msgs      # the client MIC comes from M2 or M4
    handshake = has_anonce and has_mic
    crackable = handshake or pmkid

    if not frames:
        note = "no EAPOL frames — this capture has no handshake"
    elif handshake:
        note = "complete 4-way handshake — crackable"
    elif pmkid:
        note = "PMKID present — crackable without a full handshake"
    else:
        note = "partial handshake — need an ANonce (M1/M3) and a MIC (M2/M4) to crack"

    return HandshakeInfo(
        eapol_messages=sorted(msgs),
        frames=frames,
        has_pmkid=pmkid,
        has_handshake=handshake,
        crackable=crackable,
        note=note,
    )


class HandshakeVerifier:
    def __init__(self, runner: CommandRunner, mock: bool = False) -> None:
        self.runner = runner
        self.mock = mock

    async def verify(self, pcap_path: str | None) -> HandshakeInfo:
        if self.mock:
            return HandshakeInfo(
                eapol_messages=[1, 2, 3, 4], frames=4, has_pmkid=False,
                has_handshake=True, crackable=True,
                note="complete 4-way handshake — crackable (mock)",
            )
        if not pcap_path:
            return HandshakeInfo(note="no pcap for this session yet")
        res = await self.runner.run(
            [
                "tshark", "-r", pcap_path, "-n", "-Y", "eapol",
                "-T", "fields", "-e", "eapol.keydes.key_info", "-e", "eapol.keydes.data_len",
            ],
            timeout=20,
        )
        if not res.ok:
            # tshark ran but couldn't parse it — almost always an empty/partial pcap
            # (nothing was actually captured), not a missing tshark.
            err = (res.stderr or "").lower()
            if "not found" in err and "tshark" in err:
                note = "tshark isn't installed (sudo apt install tshark)"
            else:
                note = "no handshake in this capture — the pcap looks empty (nothing was captured)"
            return HandshakeInfo(note=note)
        return parse_eapol(res.stdout)
