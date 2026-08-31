"""SchedulerService job management + /api/schedule endpoints."""
from __future__ import annotations

import asyncio

import pytest

from app.services.scheduler import SchedulerService


def test_seeds_a_job_per_action():
    s = SchedulerService({"demo": _mk([])})
    jobs = s.jobs()
    assert len(jobs) == 1 and jobs[0].id == "demo" and jobs[0].enabled is False


def test_set_and_run_now():
    calls: list[int] = []
    s = SchedulerService({"demo": _mk(calls, "ok-3")})
    s.set("demo", enabled=True, interval_sec=99)
    assert s.jobs()[0].enabled is True and s.jobs()[0].interval_sec == 99
    j = asyncio.run(s.run_now("demo"))
    assert j.runs == 1 and j.last_result == "ok-3" and len(calls) == 1


def test_failing_action_is_captured():
    async def boom() -> str:
        raise RuntimeError("nope")

    s = SchedulerService({"demo": boom})
    j = asyncio.run(s.run_now("demo"))
    assert j.runs == 1 and j.last_result.startswith("error:")


def test_set_unknown_raises():
    with pytest.raises(KeyError):
        SchedulerService({"demo": _mk([])}).set("nope", enabled=True)


def _mk(calls: list, result: str = "ok"):
    async def act() -> str:
        calls.append(1)
        return result

    return act


def test_schedule_endpoints(client, auth_headers):
    assert client.get("/api/schedule").status_code == 401
    r = client.get("/api/schedule", headers=auth_headers)
    assert r.status_code == 200 and "scan" in {j["id"] for j in r.json()}

    u = client.post("/api/schedule/scan", json={"enabled": True, "interval_sec": 60}, headers=auth_headers)
    assert u.status_code == 200 and u.json()["enabled"] is True

    run = client.post("/api/schedule/scan/run", headers=auth_headers)
    assert run.status_code == 200 and run.json()["runs"] >= 1

    assert client.post("/api/schedule/nope", json={"enabled": True}, headers=auth_headers).status_code == 404
