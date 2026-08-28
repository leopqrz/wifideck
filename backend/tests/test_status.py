"""StatusService + /api/status tests, using mock fixtures and a fake runner."""
from __future__ import annotations

import asyncio

from app.deps import get_status_service
from app.main import app
from app.models.status import Health
from app.services.runner import CommandResult, CommandRunner
from app.services.status import StatusService


def test_status_endpoint_mock(client, auth_headers):
    app.dependency_overrides[get_status_service] = lambda: StatusService(
        CommandRunner(mock=True)
    )
    try:
        resp = client.get("/api/status", headers=auth_headers)
        assert resp.status_code == 200
        d = resp.json()
        assert d["usb_present"] is True
        assert d["interface"] == "wlan0"
        assert d["mode"] == "MANAGED"
        assert d["driver"] == "rtw88_8812au"
        assert d["ssid"] == "Queiroz"
        assert d["signal_dbm"] == -42
        assert d["band"] == "5 GHz"
        assert d["ip4"] == "10.0.0.145/24"
        assert d["health"] == "ok"
    finally:
        app.dependency_overrides.clear()


def test_status_endpoint_requires_token(client):
    assert client.get("/api/status").status_code == 401


class _FakeRunner:
    """Runner that reports the adapter as absent."""

    def __init__(self, present: bool) -> None:
        self.present = present

    async def run(self, args, timeout=15.0):
        if args and args[0] == "lsusb":
            return CommandResult(0 if self.present else 1, "", "")
        # no interfaces, nothing else
        return CommandResult(0, "", "")


def test_health_disconnected_when_absent():
    status = asyncio.run(StatusService(_FakeRunner(present=False)).snapshot())
    assert status.usb_present is False
    assert status.health is Health.DISCONNECTED
    assert status.interface is None


def test_health_degraded_when_present_no_iface():
    status = asyncio.run(StatusService(_FakeRunner(present=True)).snapshot())
    assert status.usb_present is True
    assert status.interface is None
    assert status.health is Health.DEGRADED
