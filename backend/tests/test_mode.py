"""ModeService state machine + /api/mode endpoint tests."""
from __future__ import annotations

import asyncio

import pytest

from app.deps import get_mode_service
from app.main import app
from app.services.mode import ModeBusy, ModeService
from app.services.runner import CommandResult, CommandRunner
from app.services.status import StatusService


class RecordingRunner:
    """Captures issued commands; reports a wlan0 interface via `iw dev`."""

    def __init__(self) -> None:
        self.calls: list[list[str]] = []

    async def run(self, args, timeout=15.0):
        self.calls.append(list(args))
        if args[:2] == ["iw", "dev"] and len(args) == 2:
            return CommandResult(0, "\tInterface wlan0\n\t\ttype managed\n", "")
        if args and args[0] == "lsusb":
            return CommandResult(0, "0bda:8812\n", "")
        return CommandResult(0, "", "")

    def issued(self, *needle) -> bool:
        return any(call[: len(needle)] == list(needle) for call in self.calls)


def _svc(runner) -> ModeService:
    return ModeService(runner=runner, status=StatusService(runner))


def test_to_monitor_sets_type_and_channel():
    r = RecordingRunner()
    asyncio.run(_svc(r).set_mode("monitor", channel=6))
    assert r.issued("iw", "dev", "wlan0", "set", "type", "monitor")
    assert r.issued("iw", "dev", "wlan0", "set", "channel", "6")
    assert r.issued("nmcli", "device", "set", "wlan0", "managed", "no")


def test_to_managed_hands_back_to_nm():
    r = RecordingRunner()
    asyncio.run(_svc(r).set_mode("managed"))
    assert r.issued("iw", "dev", "wlan0", "set", "type", "managed")
    assert r.issued("nmcli", "device", "set", "wlan0", "managed", "yes")
    assert r.issued("nmcli", "device", "connect", "wlan0")


def test_concurrent_switch_is_rejected():
    async def scenario():
        svc = _svc(RecordingRunner())
        await svc._lock.acquire()  # simulate an in-flight switch
        try:
            with pytest.raises(ModeBusy):
                await svc.set_mode("monitor")
        finally:
            svc._lock.release()

    asyncio.run(scenario())


def test_endpoint_ok(client, auth_headers):
    app.dependency_overrides[get_mode_service] = lambda: _svc(
        CommandRunner(mock=True)
    )
    try:
        resp = client.post(
            "/api/mode", json={"mode": "monitor", "channel": 6}, headers=auth_headers
        )
        assert resp.status_code == 200
        assert "mode" in resp.json()
    finally:
        app.dependency_overrides.clear()


def test_endpoint_rejects_bad_mode(client, auth_headers):
    resp = client.post("/api/mode", json={"mode": "sniff"}, headers=auth_headers)
    assert resp.status_code == 422


def test_endpoint_requires_token(client):
    assert client.post("/api/mode", json={"mode": "managed"}).status_code == 401
