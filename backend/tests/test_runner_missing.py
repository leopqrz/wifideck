"""A missing command degrades to a failed result (macOS: no iw/nmcli) — no crash."""
from __future__ import annotations

import asyncio

from app.services.runner import CommandRunner


def test_missing_command_returns_failed_not_raises():
    r = asyncio.run(CommandRunner(mock=False).run(["definitely-not-a-real-cmd-xyz123"]))
    assert r.returncode == 127 and not r.ok
