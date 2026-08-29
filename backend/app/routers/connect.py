"""Client Wi-Fi connection endpoints (join / leave / forget / saved)."""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from ..auth import require_token
from ..deps import get_connect_service
from ..models.connect import ConnectResult
from ..services.connect import ConnectError, ConnectService

router = APIRouter()


class ConnectRequest(BaseModel):
    ssid: str
    password: str | None = None
    hidden: bool = False


class ForgetRequest(BaseModel):
    ssid: str


@router.post("/api/connect", response_model=ConnectResult)
async def connect(
    req: ConnectRequest,
    _: bool = Depends(require_token),
    svc: ConnectService = Depends(get_connect_service),
) -> ConnectResult:
    try:
        msg = await svc.connect(req.ssid, req.password, req.hidden)
    except ConnectError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    return ConnectResult(ok=True, ssid=req.ssid, message=msg)


@router.post("/api/disconnect", response_model=ConnectResult)
async def disconnect(
    _: bool = Depends(require_token),
    svc: ConnectService = Depends(get_connect_service),
) -> ConnectResult:
    try:
        msg = await svc.disconnect()
    except ConnectError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    return ConnectResult(ok=True, message=msg)


@router.post("/api/forget", response_model=ConnectResult)
async def forget(
    req: ForgetRequest,
    _: bool = Depends(require_token),
    svc: ConnectService = Depends(get_connect_service),
) -> ConnectResult:
    try:
        msg = await svc.forget(req.ssid)
    except ConnectError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    return ConnectResult(ok=True, ssid=req.ssid, message=msg)


@router.get("/api/saved", response_model=list[str])
async def saved(
    _: bool = Depends(require_token),
    svc: ConnectService = Depends(get_connect_service),
) -> list[str]:
    return await svc.saved()
