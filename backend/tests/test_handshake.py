"""Handshake verification — EAPOL classification + endpoint."""
from __future__ import annotations

from app.deps import get_handshake_verifier
from app.main import app
from app.services.handshake import HandshakeVerifier, parse_eapol
from app.services.runner import CommandRunner

# key_info values that hit each 4-way message: M1=ACK, M2=MIC, M3=MIC+ACK+INSTALL, M4=MIC+SECURE
M1, M2, M3, M4 = "0x0040", "0x0080", "0x00c8", "0x0180"


def test_complete_handshake():
    info = parse_eapol(f"{M1}\t0\n{M2}\t0\n{M3}\t16\n{M4}\t0\n")
    assert info.eapol_messages == [1, 2, 3, 4]
    assert info.frames == 4
    assert info.has_handshake
    assert info.crackable


def test_m2_m3_pair_is_enough():
    info = parse_eapol(f"{M2}\t0\n{M3}\t16\n")  # MIC source + ANonce source
    assert info.has_handshake and info.crackable


def test_pmkid_only():
    info = parse_eapol(f"{M1}\t22\n")  # M1 carrying key data = PMKID KDE
    assert info.has_pmkid
    assert info.crackable
    assert not info.has_handshake
    assert "PMKID" in info.note


def test_partial_not_crackable():
    info = parse_eapol(f"{M1}\t0\n")  # only an ANonce, no MIC
    assert not info.crackable
    assert "partial" in info.note.lower()


def test_no_eapol():
    info = parse_eapol("")
    assert info.frames == 0 and not info.crackable


def test_endpoint_reports_crackable(client, auth_headers):
    app.dependency_overrides[get_handshake_verifier] = lambda: HandshakeVerifier(
        CommandRunner(mock=True), mock=True
    )
    try:
        resp = client.get("/api/capture/any/handshake", headers=auth_headers)
        assert resp.status_code == 200
        body = resp.json()
        assert body["crackable"] is True
        assert body["eapol_messages"] == [1, 2, 3, 4]
    finally:
        app.dependency_overrides.clear()


def test_endpoint_requires_token(client):
    assert client.get("/api/capture/any/handshake").status_code == 401
