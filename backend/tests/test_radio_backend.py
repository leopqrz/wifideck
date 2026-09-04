"""Radio abstraction: backend selection, capabilities, macOS capture argv, endpoint."""
from __future__ import annotations

import asyncio

from app.services.radio import (
    LinuxNl80211Backend,
    MacosRtl8812auBackend,
    macos_capture_argv,
    resolve_backend_name,
)
from app.services.runner import CommandRunner
from app.services.status import StatusService


def test_resolve_backend_name():
    assert resolve_backend_name(mock=True) == "mock"
    assert resolve_backend_name(mock=False, pref="macos") == "macos-rtl8812au"
    assert resolve_backend_name(mock=False, pref="linux") == "linux-nl80211"


def test_macos_capture_argv():
    argv = macos_capture_argv("/opt/rtl", 6, "/tmp/out.pcap", seconds=30)
    assert argv[0] == "/opt/rtl/.venv/bin/python"
    assert argv[1].endswith("tools/capture.py")
    assert argv[2:] == ["-c", "6", "-t", "30", "-o", "/tmp/out.pcap"]


def test_macos_backend_declares_capture():
    info = asyncio.run(MacosRtl8812auBackend().info())
    assert info.backend == "macos-rtl8812au"
    assert info.capabilities.monitor_rx is True
    assert info.capabilities.raw_tx is True
    assert info.capabilities.managed is False  # not a macOS Wi-Fi interface


def test_linux_backend_detects_chip_mock():
    r = CommandRunner(mock=True)
    info = asyncio.run(LinuxNl80211Backend(r, StatusService(r)).info())
    assert info.backend == "linux-nl80211"
    assert info.chipset == "RTL8812AU"  # mock lsusb reports the ACH
    assert info.capabilities.managed is True


def test_radio_endpoint(client, auth_headers):
    assert client.get("/api/radio").status_code == 401
    r = client.get("/api/radio", headers=auth_headers)
    assert r.status_code == 200
    d = r.json()
    assert "backend" in d and "capabilities" in d
