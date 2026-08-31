"""NotifyService dispatch/dedup + /api/notify and /metrics endpoints."""
from __future__ import annotations

import asyncio

from app.services.notify import NotifyService


def test_enabled_sinks():
    assert NotifyService().enabled_sinks() == []
    n = NotifyService(webhook_url="http://x", slack_url="http://y")
    assert n.enabled_sinks() == ["webhook", "slack"]


def test_send_dispatches_and_dedups():
    n = NotifyService(webhook_url="http://x/hook", cooldown=100)
    calls: list = []

    async def fake_deliver(url, **kw):
        calls.append((url, kw))

    n._deliver = fake_deliver
    r = asyncio.run(n.send("t", "m", dedup_key="k"))
    assert r["sent"] == ["webhook"] and len(calls) == 1
    # same key within cooldown -> skipped, no second call
    r2 = asyncio.run(n.send("t", "m", dedup_key="k"))
    assert r2.get("skipped") == "cooldown" and len(calls) == 1


def test_send_no_sinks_is_noop():
    r = asyncio.run(NotifyService().send("t", "m"))
    assert r["sent"] == [] and "no sinks" in r["skipped"]


def test_notify_endpoints(client, auth_headers):
    assert client.get("/api/notify").status_code == 401
    r = client.get("/api/notify", headers=auth_headers)
    assert r.status_code == 200 and r.json()["sinks"] == []  # none configured in tests
    t = client.post("/api/notify/test", headers=auth_headers)
    assert t.status_code == 200 and t.json()["sent"] == []


def test_metrics_endpoint(client, auth_headers):
    assert client.get("/metrics").status_code == 401
    r = client.get("/metrics", headers=auth_headers)
    assert r.status_code == 200
    assert "wifideck_up 1" in r.text
    assert "wifideck_capture_sessions" in r.text
