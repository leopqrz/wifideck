"""WebSocket endpoints.

Phase 0 ships a single authenticated echo channel so the frontend can prove a
live connection. Later phases add /ws/status, /ws/scan, /ws/capture on the same
pattern.
"""
from __future__ import annotations

import asyncio

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from .auth import valid_ws_token
from .config import settings
from .deps import get_capture_service, get_watchdog_service
from .services.runner import CommandRunner
from .services.scan import AirodumpScanner, ScanService
from .services.status import StatusService

router = APIRouter()

STATUS_POLL_SECONDS = 2.0
SCAN_POLL_SECONDS = 5.0
CAPTURE_POLL_SECONDS = 2.0
WATCHDOG_POLL_SECONDS = 2.0


@router.websocket("/ws/echo")
async def echo(websocket: WebSocket, token: str = "") -> None:
    # Reject the handshake before accepting if the token is bad (1008 = policy).
    if not valid_ws_token(token):
        await websocket.close(code=1008)
        return

    await websocket.accept()
    await websocket.send_json({"type": "hello", "service": "wifideck"})
    try:
        while True:
            msg = await websocket.receive_text()
            await websocket.send_json({"type": "echo", "data": msg})
    except WebSocketDisconnect:
        return


@router.websocket("/ws/status")
async def status_stream(websocket: WebSocket, token: str = "") -> None:
    """Push an adapter Status snapshot on connect and whenever it changes."""
    if not valid_ws_token(token):
        await websocket.close(code=1008)
        return

    await websocket.accept()
    svc = StatusService(CommandRunner(mock=settings.mock))
    last: dict | None = None
    try:
        while True:
            snap = (await svc.snapshot()).model_dump(mode="json")
            if snap != last:
                await websocket.send_json({"type": "status", "data": snap})
                last = snap
            await asyncio.sleep(STATUS_POLL_SECONDS)
    except WebSocketDisconnect:
        return


@router.websocket("/ws/scan")
async def scan_stream(websocket: WebSocket, token: str = "") -> None:
    """Stream nearby networks. Uses nmcli in MANAGED mode, airodump in MONITOR."""
    if not valid_ws_token(token):
        await websocket.close(code=1008)
        return

    await websocket.accept()
    scan = ScanService(CommandRunner(mock=settings.mock))
    status = StatusService(CommandRunner(mock=settings.mock))
    airodump: AirodumpScanner | None = None
    try:
        while True:
            snap = await status.snapshot()
            if snap.mode == "MONITOR" and snap.interface and not settings.mock:
                if airodump is None:
                    airodump = AirodumpScanner(snap.interface)
                    await airodump.start()
                    await asyncio.sleep(2)  # let it gather a first sweep
                nets = airodump.read()
                source = "monitor"
            else:
                if airodump is not None:
                    await airodump.stop()
                    airodump = None
                nets = await scan.scan_managed()
                source = "managed"
            await websocket.send_json(
                {"type": "scan", "source": source,
                 "data": [n.model_dump(mode="json") for n in nets]}
            )
            await asyncio.sleep(SCAN_POLL_SECONDS)
    except WebSocketDisconnect:
        return
    finally:
        if airodump is not None:
            await airodump.stop()


@router.websocket("/ws/capture")
async def capture_stream(websocket: WebSocket, token: str = "") -> None:
    """Stream the active capture session's live detail (or null if none)."""
    if not valid_ws_token(token):
        await websocket.close(code=1008)
        return

    await websocket.accept()
    svc = get_capture_service()
    try:
        while True:
            active = svc.active
            data = None
            if active is not None:
                detail = await svc.detail(active.id)
                data = detail.model_dump(mode="json") if detail else None
            await websocket.send_json({"type": "capture", "data": data})
            await asyncio.sleep(CAPTURE_POLL_SECONDS)
    except WebSocketDisconnect:
        return


@router.websocket("/ws/watchdog")
async def watchdog_stream(websocket: WebSocket, token: str = "") -> None:
    """Stream the watchdog's live status + recovery events."""
    if not valid_ws_token(token):
        await websocket.close(code=1008)
        return

    await websocket.accept()
    svc = get_watchdog_service()
    try:
        while True:
            await websocket.send_json(
                {"type": "watchdog", "data": svc.status_info().model_dump(mode="json")}
            )
            await asyncio.sleep(WATCHDOG_POLL_SECONDS)
    except WebSocketDisconnect:
        return
