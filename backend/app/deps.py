"""Shared FastAPI dependencies."""
from __future__ import annotations

from .config import settings
from .services.runner import CommandRunner
from .services.status import StatusService


def get_status_service() -> StatusService:
    return StatusService(CommandRunner(mock=settings.mock))
