"""Driver/DKMS parser + /api/driver (mock mode)."""
from __future__ import annotations

from app.services.driver import parse_dkms_status


def test_parse_dkms_status_simple():
    text = "realtek-rtl88xxau/5.6.4.2~git20250330.c3fb89a: added\n"
    mods = parse_dkms_status(text)
    assert len(mods) == 1
    assert mods[0].name == "realtek-rtl88xxau"
    assert mods[0].version.startswith("5.6.4.2")
    assert mods[0].status == "added"


def test_parse_dkms_status_full_form():
    text = "realtek-rtl88xxau/5.6.4.2, 7.1.5+kali-arm64, aarch64: installed\n"
    mods = parse_dkms_status(text)
    assert mods[0].name == "realtek-rtl88xxau"
    assert mods[0].status == "installed"


def test_driver_endpoint(client, auth_headers):
    r = client.get("/api/driver", headers=auth_headers)
    assert r.status_code == 200
    d = r.json()
    assert d["current"] == "rtw88_8812au"
    assert d["kernel"].startswith("7.1.5")
    assert d["using_recommended"] is False          # in-kernel driver
    assert d["note"]                                  # explains the recommendation
    assert any("dkms install" in h for h in d["install_hint"])
    assert any(m["name"] == "realtek-rtl88xxau" for m in d["dkms"])


def test_driver_requires_token(client):
    assert client.get("/api/driver").status_code == 401
