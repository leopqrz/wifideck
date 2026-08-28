"""Mode-switch endpoint: MANAGED ⇄ MONITOR."""
from __future__ import annotations

from typing import Literal

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from ..auth import require_token
from ..deps import get_mode_service
from ..models.status import Status
from ..services.mode import ModeBusy, ModeError, ModeService

router = APIRouter()


class ModeRequest(BaseModel):
    mode: Literal["managed", "monitor"]
    channel: int | None = Field(default=None, ge=1, le=196)


@router.post("/api/mode", response_model=Status)
async def set_mode(
    req: ModeRequest,
    _: bool = Depends(require_token),
    svc: ModeService = Depends(get_mode_service),
) -> Status:
    try:
        return await svc.set_mode(req.mode, req.channel)
    except ModeBusy:
        raise HTTPException(status_code=409, detail="A mode switch is already in progress.")
    except ModeError as e:
        raise HTTPException(status_code=500, detail=str(e))
