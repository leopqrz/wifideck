"""Shared FastAPI dependencies."""
from __future__ import annotations

from .config import settings
from .services.capture import CaptureService
from .services.driver import DriverService
from .services.mode import ModeService
from .services.runner import CommandRunner
from .services.share import ShareService
from .services.status import StatusService


def get_status_service() -> StatusService:
    return StatusService(CommandRunner(mock=settings.mock))


def get_driver_service() -> DriverService:
    return DriverService(
        CommandRunner(mock=settings.mock),
        StatusService(CommandRunner(mock=settings.mock)),
    )


# ModeService holds the switch state machine, so it must be a single shared
# instance across requests (its asyncio.Lock serializes concurrent switches).
_mode_service = ModeService(
    runner=CommandRunner(mock=settings.mock),
    status=StatusService(CommandRunner(mock=settings.mock)),
)


def get_mode_service() -> ModeService:
    return _mode_service


# CaptureService holds active sessions/subprocesses, so it's a shared singleton.
_capture_service = CaptureService(
    runner=CommandRunner(mock=settings.mock),
    base_dir=settings.capture_dir,
    mock=settings.mock,
)


def get_capture_service() -> CaptureService:
    return _capture_service


# ShareService keeps the mock on/off flag, so it's a shared singleton too.
_share_service = ShareService(
    runner=CommandRunner(mock=settings.mock),
    status=StatusService(CommandRunner(mock=settings.mock)),
    downlink=settings.share_downlink,
    mock=settings.mock,
)


def get_share_service() -> ShareService:
    return _share_service
