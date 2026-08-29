"""Watchdog health check, escalating recovery, and endpoints."""
from __future__ import annotations

import asyncio

from app.models.status import Status
from app.services.runner import CommandResult, CommandRunner
from app.services.status import StatusService
from app.services.watchdog import WatchdogService


class RecordingRunner:
    def __init__(self) -> None:
        self.calls: list[list[str]] = []

    async def run(self, args, timeout=15.0):
        self.calls.append(list(args))
        if args[:1] == ["sh"] and "idVendor" in " ".join(args):
            return CommandResult(0, "3-1\n", "")
        return CommandResult(0, "", "")

    def issued(self, *needle) -> bool:
        return any(c[: len(needle)] == list(needle) for c in self.calls)


def _wd(runner, mock=False) -> WatchdogService:
    return WatchdogService(runner, StatusService(runner), interval=0.01, mock=mock, enabled=False)


def test_run_once_healthy_in_mock():
    svc = _wd(CommandRunner(mock=True), mock=True)
    asyncio.run(svc.run_once())
    assert svc.healthy is True
    assert svc.recoveries == 0


def test_recover_reloads_driver_first():
    r = RecordingRunner()
    svc = _wd(r)
    svc._unhealthy_streak = 1
    snap = Status(usb_present=True, interface=None, driver="rtw88_8812au")
    asyncio.run(svc._recover(snap))
    assert r.issued("modprobe", "-r", "rtw88_8812au")
    assert r.issued("modprobe", "rtw88_8812au")
    assert svc.recoveries == 1
    assert any(e.kind == "driver-reload" for e in svc._events)


def test_recover_escalates_to_usb_reset():
    r = RecordingRunner()
    svc = _wd(r)
    svc._unhealthy_streak = 2  # second failure -> USB reset
    snap = Status(usb_present=True, interface=None, driver="rtw88_8812au")
    asyncio.run(svc._recover(snap))
    assert any("unbind" in " ".join(c) for c in r.calls)
    assert any(e.kind == "usb-reset" for e in svc._events)


def test_recover_reports_when_off_bus():
    r = RecordingRunner()
    svc = _wd(r)
    svc._unhealthy_streak = 1
    snap = Status(usb_present=False, interface=None)
    asyncio.run(svc._recover(snap))
    assert not r.issued("modprobe", "-r", "rtw88_8812au")  # can't fix a host passthrough drop
    assert any(e.kind == "usb-absent" for e in svc._events)


def test_endpoint_status_and_toggle(client, auth_headers):
    assert client.get("/api/watchdog", headers=auth_headers).status_code == 200
    on = client.post("/api/watchdog", json={"enabled": True}, headers=auth_headers).json()
    assert on["running"] is True
    off = client.post("/api/watchdog", json={"enabled": False}, headers=auth_headers).json()
    assert off["running"] is False


def test_watchdog_requires_token(client):
    assert client.get("/api/watchdog").status_code == 401
