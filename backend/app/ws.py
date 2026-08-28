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
from .services.runner import CommandRunner
from .services.status import StatusService

router = APIRouter()

STATUS_POLL_SECONDS = 2.0


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
