"""Client/station intelligence — devices seen in monitor mode."""
from __future__ import annotations

from fastapi import APIRouter, Depends

from ..auth import require_token
from ..deps import get_station_service
from ..models.station import Station
from ..services.stations import StationService

router = APIRouter()


@router.get("/api/stations", response_model=list[Station])
async def stations(
    _: bool = Depends(require_token),
    svc: StationService = Depends(get_station_service),
) -> list[Station]:
    return svc.list()
