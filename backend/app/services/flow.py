"""CaptureFlowService — the guided handshake-capture workflow.

Chains existing services into one gated, audited flow:
  MONITOR (target channel) -> start capture (locked to BSSID) -> deauth burst
  -> wait for handshake -> stop capture -> restore MANAGED.

The Phase 7 guardrails are enforced UP FRONT (before touching the radio):
active modules enabled, explicit authorization, and the target in the scope
allowlist. For authorized testing of your own networks only.
"""
from __future__ import annotations

import asyncio
from datetime import datetime, timezone

from ..models.flow import FlowStatus, FlowStep
from .active import ActiveService
from .capture import CaptureService
from .mode import ModeService
from .scope import ScopeList
from .status import StatusService


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


class FlowBusy(Exception):
    pass


class FlowRefused(Exception):
    pass


class CaptureFlowService:
    def __init__(
        self,
        mode: ModeService,
        capture: CaptureService,
        active: ActiveService,
        scope: ScopeList,
        status: StatusService,
        enabled: bool,
        mock: bool,
    ) -> None:
        self.mode = mode
        self.capture = capture
        self.active = active
        self.scope = scope
        self.status = status
        self.enabled = enabled
        self.mock = mock
        self._task: asyncio.Task | None = None
        self._reset()

    def _reset(self) -> None:
        self.state = "idle"
        self.target_bssid: str | None = None
        self.channel: int | None = None
        self.session_id: str | None = None
        self.handshake = False
        self.message: str | None = None
        self.steps: list[FlowStep] = []

    def _step(self, name: str, detail: str) -> FlowStep:
        # mark the previous step done, append the new one
        if self.steps:
            self.steps[-1].done = True
        step = FlowStep(name=name, detail=detail, timestamp=_now())
        self.steps.append(step)
        return step

    def status_info(self) -> FlowStatus:
        return FlowStatus(
            state=self.state,
            target_bssid=self.target_bssid,
            channel=self.channel,
            session_id=self.session_id,
            handshake=self.handshake,
            message=self.message,
            steps=list(self.steps),
        )

    async def start(
        self, bssid: str, channel: int, authorized: bool, count: int, timeout: float
    ) -> FlowStatus:
        if self._task is not None and not self._task.done():
            raise FlowBusy()

        # ---- guardrails, checked before touching the radio ----
        if not self.enabled:
            raise FlowRefused("Active modules are disabled (WIFIDECK_ENABLE_ACTIVE=1).")
        if not authorized:
            raise FlowRefused("Explicit authorization is required for this flow.")
        if not self.scope.contains(bssid):
            raise FlowRefused(f"{bssid.upper()} is not in the authorized scope allowlist.")

        self._reset()
        self.state = "running"
        self.target_bssid = bssid.upper()
        self.channel = channel
        self._task = asyncio.create_task(self._run(bssid, channel, count, timeout))
        return self.status_info()

    async def _run(self, bssid: str, channel: int, count: int, timeout: float) -> None:
        try:
            iface = (await self.status.snapshot()).interface or "wlan0"

            self._step("monitor", f"switching to MONITOR on channel {channel}")
            await self.mode.set_mode("monitor", channel)

            self._step("capture", f"capturing {bssid} on channel {channel}")
            session = await self.capture.start(iface, channel, bssid)
            self.session_id = session.id

            self._step("deauth", f"sending {count} deauth frames to force a handshake")
            await self.active.deauth(bssid, None, count, authorized=True)

            self._step("handshake", "waiting for the 4-way handshake")
            deadline = asyncio.get_event_loop().time() + timeout
            while asyncio.get_event_loop().time() < deadline:
                await self.capture.refresh(session.id)
                if self.capture.sessions[session.id].handshake:
                    self.handshake = True
                    break
                await asyncio.sleep(2)

            self._step("cleanup", "stopping capture and restoring MANAGED")
            await self.capture.stop(session.id)
            await self.mode.set_mode("managed")

            if self.steps:
                self.steps[-1].done = True
            if self.handshake:
                self.state = "done"
                self.message = "Handshake captured — download the pcap from the capture session."
            else:
                self.state = "timeout"
                self.message = "No handshake within the timeout — try again or increase deauth count."
        except asyncio.CancelledError:
            self.state = "stopped"
            self.message = "Flow stopped."
            raise
        except Exception as e:
            self.state = "failed"
            self.message = str(e)

    async def stop(self) -> FlowStatus:
        if self._task is not None and not self._task.done():
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        if self.session_id:
            try:
                await self.capture.stop(self.session_id)
            except Exception:
                pass
        if self.state == "running":
            self.state = "stopped"
        return self.status_info()
