"""WebSocket endpoints.

Phase 0 ships a single authenticated echo channel so the frontend can prove a
live connection. Later phases add /ws/status, /ws/scan, /ws/capture on the same
pattern.
"""
from __future__ import annotations

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from .auth import valid_ws_token

router = APIRouter()


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
