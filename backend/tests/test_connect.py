"""Client connect/disconnect/forget/saved + guards."""
from __future__ import annotations

import asyncio

import pytest

from app.models.status import Status
from app.services.connect import ConnectError, ConnectService
from app.services.runner import CommandResult


class FakeStatus:
    def __init__(self, mode: str) -> None:
        self._mode = mode

    async def snapshot(self) -> Status:
        return Status(usb_present=True, interface="wlan0", mode=self._mode)


class FakeRunner:
    def __init__(self, ok: bool) -> None:
        self.ok = ok
        self.calls: list[list[str]] = []

    async def run(self, args, timeout=15.0):
        self.calls.append(list(args))
        err = "" if self.ok else "Error: 802-11-wireless-security.psk: property is invalid"
        return CommandResult(0 if self.ok else 1, "", err)


# ---- service guards ----
def test_connect_builds_nmcli_args():
    r = FakeRunner(True)
    svc = ConnectService(r, FakeStatus("MANAGED"), mock=False)
    asyncio.run(svc.connect("MyNet", "secret", hidden=False))
    call = r.calls[0]
    assert call[:5] == ["nmcli", "device", "wifi", "connect", "MyNet"]
    assert "password" in call and "secret" in call


def test_connect_refused_in_monitor_mode():
    svc = ConnectService(FakeRunner(True), FakeStatus("MONITOR"), mock=False)
    with pytest.raises(ConnectError):
        asyncio.run(svc.connect("MyNet", "pw", hidden=False))


def test_connect_surfaces_failure():
    svc = ConnectService(FakeRunner(False), FakeStatus("MANAGED"), mock=False)
    with pytest.raises(ConnectError):
        asyncio.run(svc.connect("MyNet", "wrongpw", hidden=False))


# ---- endpoints (mock) ----
def test_connect_endpoint(client, auth_headers):
    r = client.post("/api/connect", json={"ssid": "MockNet-5G", "password": "x"}, headers=auth_headers)
    assert r.status_code == 200 and r.json()["ok"] is True


def test_disconnect_and_forget_endpoints(client, auth_headers):
    assert client.post("/api/disconnect", headers=auth_headers).status_code == 200
    assert client.post("/api/forget", json={"ssid": "MockNet-5G"}, headers=auth_headers).status_code == 200


def test_saved_endpoint(client, auth_headers):
    saved = client.get("/api/saved", headers=auth_headers).json()
    assert "MockNet-5G" in saved


def test_connect_requires_token(client):
    assert client.post("/api/connect", json={"ssid": "x"}).status_code == 401
    assert client.get("/api/saved").status_code == 401
