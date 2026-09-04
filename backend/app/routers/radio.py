"""Radio doctor — which backend is active and what the radio can do."""
from __future__ import annotations

from fastapi import APIRouter, Depends, Query

from ..auth import require_token
from ..config import settings
from ..deps import get_known_networks
from ..models.network import Network
from ..models.radio import RadioInfo
from ..services.known import KnownNetworks
from ..services.radio import macos_scan, resolve_backend_name, select_backend

router = APIRouter()


@router.get("/api/radio", response_model=RadioInfo)
async def radio(_: bool = Depends(require_token)) -> RadioInfo:
    return await select_backend(settings.mock, settings.radio_backend).info()


@router.post("/api/scan/once", response_model=list[Network])
async def scan_once(
    channel: int = Query(6, ge=1, le=196),
    seconds: int = Query(4, ge=2, le=30),
    _: bool = Depends(require_token),
    known: KnownNetworks = Depends(get_known_networks),
) -> list[Network]:
    """macOS monitor-scan: brief capture on a channel → APs heard. Saves them so the
    Target picker fills. (Linux uses the /ws/scan stream instead.)"""
    if resolve_backend_name(settings.mock, settings.radio_backend) != "macos-rtl8812au":
        return []
    nets = await macos_scan(settings.rtl8812au_dir, channel, seconds)
    if nets:
        known.save(nets)
    return nets
