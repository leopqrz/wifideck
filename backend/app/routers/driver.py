"""Driver / DKMS info endpoint (read-only)."""
from __future__ import annotations

from fastapi import APIRouter, Depends

from ..auth import require_token
from ..deps import get_driver_service
from ..models.driver import DriverInfo
from ..services.driver import DriverService

router = APIRouter()


@router.get("/api/driver", response_model=DriverInfo)
async def driver(
    _: bool = Depends(require_token),
    svc: DriverService = Depends(get_driver_service),
) -> DriverInfo:
    return await svc.info()
