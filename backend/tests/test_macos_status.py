"""macOS status snapshot reports the libusb radio, not a false 'disconnected'."""
from __future__ import annotations

import asyncio

from app.services.runner import CommandRunner
from app.services.status import StatusService


def test_macos_snapshot_reports_libusb():
    snap = asyncio.run(StatusService(CommandRunner(mock=True))._macos_snapshot())
    assert snap.driver == "libusb (rtl8812au-macos)"
    assert snap.interface == "libusb"
