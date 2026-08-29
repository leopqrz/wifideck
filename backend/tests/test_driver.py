"""Driver/DKMS parser + kernel-compat check + /api/driver (mock mode)."""
from __future__ import annotations

from app.services.driver import kernel_buildable, parse_dkms_status


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


def test_kernel_buildable():
    # driver builds only up to 6.15
    assert kernel_buildable("6.10.0-kali", "6.15") is True
    assert kernel_buildable("6.15.2", "6.15") is True
    assert kernel_buildable("7.1.5+kali-arm64", "6.15") is False   # the real regression
    assert kernel_buildable("6.16.0", "6.15") is False
    assert kernel_buildable("7.1.5", None) is True                 # no declared limit


def test_driver_endpoint_kernel_too_new(client, auth_headers):
    # mock kernel is 7.1.5, driver max is 6.15 -> NOT buildable: no bricking commands
    r = client.get("/api/driver", headers=auth_headers)
    assert r.status_code == 200
    d = r.json()
    assert d["current"] == "rtw88_8812au"
    assert d["kernel"].startswith("7.1.5")
    assert d["recommended_buildable"] is False
    assert d["kernel_max"] == "6.15"
    assert d["install_hint"] == []                     # must NOT hand out blacklist commands
    assert "does not support this kernel" in d["note"]


def test_driver_requires_token(client):
    assert client.get("/api/driver").status_code == 401
