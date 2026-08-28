"""Phase 0 gate: localhost-only bind default, and the WebSocket rejects a bad token."""
from __future__ import annotations

import pytest
from starlette.websockets import WebSocketDisconnect

from app.config import settings


def test_binds_to_loopback_by_default():
    assert settings.host == "127.0.0.1", "service must default to loopback only"


def test_ws_echo_requires_token(client):
    with pytest.raises(WebSocketDisconnect):
        with client.websocket_connect("/ws/echo?token=wrong") as ws:
            ws.receive_text()


def test_ws_echo_roundtrip_with_token(client):
    with client.websocket_connect("/ws/echo?token=test-token") as ws:
        hello = ws.receive_json()
        assert hello["type"] == "hello"
        ws.send_text("ping")
        echoed = ws.receive_json()
        assert echoed == {"type": "echo", "data": "ping"}
