"""SchedulerService — run named actions on an interval (rescan, WIDS sweep,
heartbeat). Jobs are off by default; enable + set an interval, or run one now.
"""
from __future__ import annotations

import asyncio
import time
from collections.abc import Awaitable, Callable
from datetime import datetime, timezone

from ..models.schedule import Job

# label + default interval (seconds) per known action.
_META: dict[str, tuple[str, int]] = {
    "scan": ("Rescan networks", 300),
    "wids": ("WIDS sweep", 120),
    "heartbeat": ("Heartbeat notification", 3600),
}


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


class SchedulerService:
    def __init__(
        self,
        actions: dict[str, Callable[[], Awaitable[str]]],
        tick: float = 5.0,
    ) -> None:
        self.actions = actions
        self.tick = tick
        self._jobs: dict[str, Job] = {}
        self._due: dict[str, float] = {}
        for name in actions:
            label, interval = _META.get(name, (name, 300))
            self._jobs[name] = Job(id=name, label=label, action=name, interval_sec=interval)
        self._task: asyncio.Task | None = None

    def jobs(self) -> list[Job]:
        return list(self._jobs.values())

    def set(self, jid: str, enabled: bool | None = None, interval_sec: int | None = None) -> Job:
        job = self._jobs[jid]  # KeyError -> 404 at the router
        if enabled is not None:
            job.enabled = enabled
        if interval_sec is not None:
            job.interval_sec = max(10, int(interval_sec))
        if job.enabled:
            self._due[jid] = time.monotonic() + job.interval_sec
        return job

    async def run_now(self, jid: str) -> Job:
        await self._run(self._jobs[jid])
        return self._jobs[jid]

    async def _run(self, job: Job) -> None:
        try:
            job.last_result = await self.actions[job.action]()
        except Exception as e:  # a failing job must not kill the loop
            job.last_result = f"error: {e}"
        job.last_run = _now()
        job.runs += 1
        self._due[job.id] = time.monotonic() + job.interval_sec

    def start(self) -> None:
        if self._task is None or self._task.done():
            self._task = asyncio.create_task(self._loop())

    async def stop(self) -> None:
        if self._task and not self._task.done():
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass

    async def _loop(self) -> None:
        while True:
            now = time.monotonic()
            for job in list(self._jobs.values()):
                if job.enabled and self._due.get(job.id, 0.0) <= now:
                    await self._run(job)
            await asyncio.sleep(self.tick)
