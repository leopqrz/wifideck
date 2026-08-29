"""Read the remembered network list — the last MANAGED scan, snapshotted when
switching to MONITOR (where the live scan returns nothing on this adapter)."""
from __future__ import annotations

from fastapi import APIRouter, Depends
from pydantic import BaseModel

from ..auth import require_token
from ..deps import get_known_networks
from ..models.network import Network
from ..services.known import KnownNetworks

router = APIRouter()


class KnownNetworksResponse(BaseModel):
    saved_at: str | None
    networks: list[Network]


@router.get("/api/scan/known", response_model=KnownNetworksResponse)
async def known_networks(
    _: bool = Depends(require_token),
    store: KnownNetworks = Depends(get_known_networks),
) -> KnownNetworksResponse:
    return KnownNetworksResponse(saved_at=store.saved_at, networks=store.list())
