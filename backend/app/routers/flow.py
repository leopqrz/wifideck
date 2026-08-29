"""Guided capture-flow endpoints."""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from ..auth import require_token
from ..deps import get_flow_service
from ..models.flow import FlowStatus
from ..services.flow import CaptureFlowService, FlowBusy, FlowRefused

router = APIRouter()


class FlowRequest(BaseModel):
    bssid: str
    channel: int = Field(ge=1, le=196)
    authorized: bool = False
    count: int = Field(default=8, ge=1, le=64)
    timeout: float = Field(default=60, ge=5, le=600)


@router.post("/api/flow", response_model=FlowStatus)
async def start_flow(
    req: FlowRequest,
    _: bool = Depends(require_token),
    svc: CaptureFlowService = Depends(get_flow_service),
) -> FlowStatus:
    try:
        return await svc.start(req.bssid, req.channel, req.authorized, req.count, req.timeout)
    except FlowBusy:
        raise HTTPException(status_code=409, detail="A capture flow is already running.") from None
    except FlowRefused as e:
        raise HTTPException(status_code=403, detail=str(e)) from e


@router.post("/api/flow/stop", response_model=FlowStatus)
async def stop_flow(
    _: bool = Depends(require_token),
    svc: CaptureFlowService = Depends(get_flow_service),
) -> FlowStatus:
    return await svc.stop()


@router.get("/api/flow", response_model=FlowStatus)
async def flow_status(
    _: bool = Depends(require_token),
    svc: CaptureFlowService = Depends(get_flow_service),
) -> FlowStatus:
    return svc.status_info()
