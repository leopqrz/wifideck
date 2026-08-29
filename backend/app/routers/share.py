"""Internet-sharing endpoint."""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from ..auth import require_token
from ..deps import get_share_service
from ..models.share import ShareStatus
from ..services.share import ShareError, ShareService

router = APIRouter()


class ShareRequest(BaseModel):
    enabled: bool


@router.get("/api/share", response_model=ShareStatus)
async def get_share(
    _: bool = Depends(require_token),
    svc: ShareService = Depends(get_share_service),
) -> ShareStatus:
    return await svc.status_info()


@router.post("/api/share", response_model=ShareStatus)
async def set_share(
    req: ShareRequest,
    _: bool = Depends(require_token),
    svc: ShareService = Depends(get_share_service),
) -> ShareStatus:
    try:
        return await svc.enable() if req.enabled else await svc.disable()
    except ShareError as e:
        raise HTTPException(status_code=500, detail=str(e)) from e
