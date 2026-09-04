"""Radio backends + /api/radio doctor."""
from __future__ import annotations

import asyncio

from app.services.radio import (
    LinuxNl80211Backend,
    MacosRtl8812auBackend,
    MockBackend,
    select_backend,
)
from app.services.runner import CommandRunner
from app.services.status import StatusService


def test_select_backend():
    assert isinstance(select_backend(mock=True), MockBackend)
    assert isinstance(select_backend(mock=False, pref="linux"), LinuxNl80211Backend)
    assert isinstance(select_backend(mock=False, pref="macos"), MacosRtl8812auBackend)


def test_linux_backend_detects_chipset():
    r = CommandRunner(mock=True)
    info = asyncio.run(LinuxNl80211Backend(r, StatusService(r)).info())
    assert info.backend == "linux-nl80211"
    assert info.chipset == "RTL8812AU"          # mock lsusb reports it
    assert info.capabilities.managed is True
    assert isinstance(info.capabilities.monitor_rx, bool)


def test_macos_backend_declares_capture():
    info = asyncio.run(MacosRtl8812auBackend().info())
    assert info.backend == "macos-rtl8812au"
    assert info.capabilities.monitor_rx is True
    assert info.capabilities.raw_tx is True
    assert info.capabilities.managed is False   # not a macOS Wi-Fi interface
    assert "5 GHz" in info.capabilities.bands


def test_radio_endpoint(client, auth_headers):
    assert client.get("/api/radio").status_code == 401
    r = client.get("/api/radio", headers=auth_headers)
    assert r.status_code == 200
    d = r.json()
    assert "backend" in d and "capabilities" in d
