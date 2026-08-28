"""Shared FastAPI dependencies."""
from __future__ import annotations

from .config import settings
from .services.mode import ModeService
from .services.runner import CommandRunner
from .services.status import StatusService


def get_status_service() -> StatusService:
    return StatusService(CommandRunner(mock=settings.mock))


# ModeService holds the switch state machine, so it must be a single shared
# instance across requests (its asyncio.Lock serializes concurrent switches).
_mode_service = ModeService(
    runner=CommandRunner(mock=settings.mock),
    status=StatusService(CommandRunner(mock=settings.mock)),
)


def get_mode_service() -> ModeService:
    return _mode_service
