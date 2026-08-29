"""Handshake-cracking endpoints."""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from ..auth import require_token
from ..deps import get_crack_service
from ..models.crack import CrackStatus
from ..services.crack import CrackBusy, CrackNotFound, CrackRefused, CrackService

router = APIRouter()


class CrackRequest(BaseModel):
    session_id: str
    wordlist: str | None = None
    authorized: bool = False


@router.post("/api/crack", response_model=CrackStatus)
async def start_crack(
    req: CrackRequest,
    _: bool = Depends(require_token),
    svc: CrackService = Depends(get_crack_service),
) -> CrackStatus:
    try:
        return await svc.start(req.session_id, req.wordlist, req.authorized)
    except CrackBusy:
        raise HTTPException(status_code=409, detail="A crack job is already running.") from None
    except CrackNotFound:
        raise HTTPException(status_code=404, detail="Unknown capture session.") from None
    except CrackRefused as e:
        raise HTTPException(status_code=403, detail=str(e)) from e


@router.post("/api/crack/stop", response_model=CrackStatus)
async def stop_crack(
    _: bool = Depends(require_token),
    svc: CrackService = Depends(get_crack_service),
) -> CrackStatus:
    return await svc.stop()


@router.get("/api/crack", response_model=CrackStatus)
async def crack_status(
    _: bool = Depends(require_token),
    svc: CrackService = Depends(get_crack_service),
) -> CrackStatus:
    return svc.status_info()
