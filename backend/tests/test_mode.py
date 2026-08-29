"""ModeService state machine + /api/mode endpoint tests."""
from __future__ import annotations

import asyncio

import pytest

from app.deps import get_known_networks, get_mode_service
from app.main import app
from app.services.known import KnownNetworks
from app.services.mode import ModeBusy, ModeError, ModeService
from app.services.runner import CommandResult, CommandRunner
from app.services.scan import ScanService
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


class ScanningRunner(RecordingRunner):
    """Also answers `nmcli device wifi list` with one network, so a monitor
    switch can snapshot a real MANAGED scan into the known store."""

    async def run(self, args, timeout=15.0):
        self.calls.append(list(args))
        if args[:2] == ["iw", "dev"] and len(args) == 2:
            return CommandResult(0, "\tInterface wlan0\n\t\ttype managed\n", "")
        if args[:3] == ["nmcli", "-t", "-f"]:
            return CommandResult(0, r":02\:00\:00\:00\:00\:01:MockNet-5G:36:70:WPA2" + "\n", "")
        if args and args[0] == "lsusb":
            return CommandResult(0, "0bda:8812\n", "")
        return CommandResult(0, "", "")


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


def test_to_managed_kills_scanners_holding_the_card():
    r = RecordingRunner()
    asyncio.run(_svc(r).set_mode("managed"))
    # airodump-ng pins monitor mode; the switch must clear it first.
    assert r.issued("pkill", "-f", "airodump-ng")


def test_to_managed_raises_if_still_in_monitor():
    """A driver that reports success but stays in monitor is surfaced, not hidden."""

    class StuckMonitorRunner(RecordingRunner):
        async def run(self, args, timeout=15.0):
            self.calls.append(list(args))
            if args[:2] == ["iw", "dev"] and len(args) == 2:
                return CommandResult(0, "\tInterface wlan0\n\t\ttype monitor\n", "")
            if args and args[0] == "lsusb":
                return CommandResult(0, "0bda:8812\n", "")
            return CommandResult(0, "", "")

    r = StuckMonitorRunner()
    with pytest.raises(ModeError, match="still in MONITOR"):
        asyncio.run(_svc(r).set_mode("managed"))


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


def test_to_monitor_snapshots_known_scan(tmp_path):
    r = ScanningRunner()
    known = KnownNetworks(str(tmp_path / "known.json"))
    svc = ModeService(runner=r, status=StatusService(r), scan=ScanService(r), known=known)
    asyncio.run(svc.set_mode("monitor"))
    nets = known.list()
    assert [n.bssid for n in nets] == ["02:00:00:00:00:01"]
    assert nets[0].channel == 36  # channel travels with the remembered target
    assert known.saved_at is not None


def test_empty_scan_does_not_clobber_known(tmp_path):
    known = KnownNetworks(str(tmp_path / "known.json"))
    # Seed a good list via a monitor switch.
    r = ScanningRunner()
    svc = ModeService(runner=r, status=StatusService(r), scan=ScanService(r), known=known)
    asyncio.run(svc.set_mode("monitor"))
    assert len(known.list()) == 1
    # An empty scan/save must not wipe the remembered list.
    known.save([])
    assert len(known.list()) == 1


def test_known_endpoint(client, auth_headers, tmp_path):
    store = KnownNetworks(str(tmp_path / "known.json"))
    r = ScanningRunner()
    svc = ModeService(runner=r, status=StatusService(r), scan=ScanService(r), known=store)
    asyncio.run(svc.set_mode("monitor"))
    app.dependency_overrides[get_known_networks] = lambda: store
    try:
        resp = client.get("/api/scan/known", headers=auth_headers)
        assert resp.status_code == 200
        body = resp.json()
        assert body["saved_at"]
        assert body["networks"][0]["bssid"] == "02:00:00:00:00:01"
    finally:
        app.dependency_overrides.clear()


def test_known_endpoint_requires_token(client):
    assert client.get("/api/scan/known").status_code == 401
