"""Handshake verification model — what tshark found in a capture's pcap."""
from __future__ import annotations

from pydantic import BaseModel


class HandshakeInfo(BaseModel):
    eapol_messages: list[int] = []   # which of the 4-way messages {1,2,3,4} are present
    frames: int = 0                  # total EAPOL frames seen
    has_pmkid: bool = False
    has_handshake: bool = False      # a crackable 4-way pair is present
    crackable: bool = False          # handshake OR pmkid — worth a crack run
    note: str = ""
