"""Health / readiness endpoint — the Phase 0 gate check."""
from __future__ import annotations

import platform

from fastapi import APIRouter, Depends

from ..auth import require_token
from ..config import settings
from ..services.radio import resolve_backend_name

router = APIRouter()


def _host_os() -> tuple[str, str]:
    """A friendly OS name + a detailed one (for a tooltip)."""
    sysname = platform.system()
    if sysname == "Darwin":
        ver = platform.mac_ver()[0]
        return "macOS", (f"macOS {ver}".strip())
    if sysname == "Linux":
        return "Linux", f"Linux {platform.release()}"
    if sysname == "Windows":
        return "Windows", f"Windows {platform.release()}"
    return (sysname or "unknown"), (sysname or "unknown")


@router.get("/api/health")
def health(_: bool = Depends(require_token)) -> dict:
    os_name, os_detail = _host_os()
    return {
        "status": "ok",
        "service": "wifideck",
        "version": settings.version,
        "mock": settings.mock,
        # Which OS the app is actually running on, and the RF backend it picked
        # for that OS — so the UI can say it plainly, not just infer it from the driver.
        "os": os_name,
        "os_detail": os_detail,
        "arch": platform.machine(),
        "backend": resolve_backend_name(settings.mock, settings.radio_backend),
    }
