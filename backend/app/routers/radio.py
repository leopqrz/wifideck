"""Radio doctor — which backend is active and what the radio can do."""
from __future__ import annotations

from fastapi import APIRouter, Depends

from ..auth import require_token
from ..config import settings
from ..models.radio import RadioInfo
from ..services.radio import select_backend

router = APIRouter()


@router.get("/api/radio", response_model=RadioInfo)
async def radio(_: bool = Depends(require_token)) -> RadioInfo:
    return await select_backend(settings.mock, settings.radio_backend).info()
