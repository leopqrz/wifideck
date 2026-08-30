"""Capture control: start/stop sessions, list, detail, and pcap download."""
from __future__ import annotations

import os
from typing import Literal

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field

from ..auth import require_token
from ..config import settings
from ..deps import get_capture_service, get_handshake_verifier, get_status_service
from ..models.handshake import HandshakeInfo
from ..models.session import CaptureDetail, CaptureSession
from ..services.capture import CaptureBusy, CaptureError, CaptureService
from ..services.handshake import HandshakeVerifier
from ..services.status import StatusService

router = APIRouter()


class CaptureRequest(BaseModel):
    channel: int | None = Field(default=None, ge=1, le=196)
    bssid: str | None = None
    mode: Literal["handshake", "pmkid"] = "handshake"


@router.post("/api/capture", response_model=CaptureSession)
async def start_capture(
    req: CaptureRequest,
    _: bool = Depends(require_token),
    svc: CaptureService = Depends(get_capture_service),
    status_svc: StatusService = Depends(get_status_service),
) -> CaptureSession:
    snap = await status_svc.snapshot()
    if not settings.mock:
        if snap.mode != "MONITOR":
            raise HTTPException(status_code=409, detail="Capture requires MONITOR mode.")
        if not snap.interface:
            raise HTTPException(status_code=400, detail="No Wi-Fi interface.")
    iface = snap.interface or "wlan0"
    try:
        return await svc.start(iface, req.channel, req.bssid, req.mode)
    except CaptureBusy:
        raise HTTPException(status_code=409, detail="A capture is already running.") from None
    except CaptureError as e:
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.post("/api/capture/{sid}/stop", response_model=CaptureSession)
async def stop_capture(
    sid: str,
    _: bool = Depends(require_token),
    svc: CaptureService = Depends(get_capture_service),
) -> CaptureSession:
    try:
        return await svc.stop(sid)
    except CaptureError:
        raise HTTPException(status_code=404, detail="Unknown session.") from None


@router.get("/api/capture", response_model=list[CaptureSession])
async def list_captures(
    _: bool = Depends(require_token),
    svc: CaptureService = Depends(get_capture_service),
) -> list[CaptureSession]:
    return svc.list()


@router.get("/api/capture/{sid}", response_model=CaptureDetail)
async def capture_detail(
    sid: str,
    _: bool = Depends(require_token),
    svc: CaptureService = Depends(get_capture_service),
) -> CaptureDetail:
    detail = await svc.detail(sid)
    if detail is None:
        raise HTTPException(status_code=404, detail="Unknown session.")
    return detail


@router.get("/api/capture/{sid}/pcap")
async def download_pcap(
    sid: str,
    _: bool = Depends(require_token),
    svc: CaptureService = Depends(get_capture_service),
) -> FileResponse:
    path = svc.pcap_path(sid)
    if not path or not os.path.isfile(path):
        raise HTTPException(status_code=404, detail="No pcap for this session yet.")
    return FileResponse(path, media_type="application/vnd.tcpdump.pcap", filename=f"{sid}.cap")


@router.get("/api/capture/{sid}/handshake", response_model=HandshakeInfo)
async def capture_handshake(
    sid: str,
    _: bool = Depends(require_token),
    svc: CaptureService = Depends(get_capture_service),
    verifier: HandshakeVerifier = Depends(get_handshake_verifier),
) -> HandshakeInfo:
    """Verify (via tshark) which EAPOL messages / PMKID a session's pcap holds."""
    return await verifier.verify(svc.pcap_path(sid))
