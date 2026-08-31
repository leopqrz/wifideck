"""WatchdogService — detect adapter drops and auto-recover.

Health = adapter on the USB bus AND a Wi-Fi interface present. When that breaks
(the classic RTL8812AU `-71` disconnect), recovery escalates:
  1. reload the driver module          (present but no interface)
  2. reset the USB device via sysfs     (still wedged)
  3. reconnect via NetworkManager
If the adapter is fully off the bus, that's a host-side (VMware passthrough)
problem Linux can't fix — the watchdog reports it and waits.

Requires root in real mode. Mock mode probes fixtures (always healthy) and takes
no actions.
"""
from __future__ import annotations

import asyncio
import re
from collections import deque
from datetime import datetime, timezone

from ..models.status import Status
from ..models.watchdog import WatchdogEvent, WatchdogStatus
from .runner import CommandRunner
from .status import StatusService

KNOWN_MODULES = ("88XXau", "8812au", "rtw88_8812au")


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


class WatchdogService:
    def __init__(
        self,
        runner: CommandRunner,
        status: StatusService,
        interval: float,
        mock: bool,
        enabled: bool,
        notify=None,
    ) -> None:
        self.runner = runner
        self.status = status
        self.interval = interval
        self.mock = mock
        self.enabled = enabled
        self.notify = notify
        self._task: asyncio.Task | None = None
        self._events: deque[WatchdogEvent] = deque(maxlen=50)
        self.checks = 0
        self.recoveries = 0
        self.last_check: str | None = None
        self.healthy: bool | None = None
        self.usb_present: bool | None = None
        self.interface: str | None = None
        self._unhealthy_streak = 0

    def _event(self, kind: str, detail: str, result: str) -> WatchdogEvent:
        e = WatchdogEvent(timestamp=_now(), kind=kind, detail=detail, result=result)
        self._events.appendleft(e)
        # Notify on the meaningful drop/recovery events, not routine checks.
        if self.notify and kind in ("recovered", "usb-absent", "usb-reset"):
            try:
                asyncio.get_running_loop().create_task(
                    self.notify.send(f"Watchdog: {kind}", detail, level="high",
                                     dedup_key=f"watchdog:{kind}")
                )
            except RuntimeError:
                pass
        return e

    async def _driver_name(self, snap: Status) -> str:
        if snap.driver:
            return snap.driver
        lsmod = (await self.runner.run(["lsmod"])).stdout
        for mod in KNOWN_MODULES:
            if re.search(rf"^{re.escape(mod)}\b", lsmod, re.MULTILINE):
                return mod
        return "rtw88_8812au"

    async def _usb_busid(self) -> str | None:
        r = await self.runner.run([
            "sh", "-c",
            'for d in /sys/bus/usb/devices/*/; do '
            '[ -f "$d/idVendor" ] && [ "$(cat "$d/idVendor")" = 0bda ] && '
            '[ "$(cat "$d/idProduct")" = 8812 ] && basename "$d" && break; done',
        ])
        return r.stdout.strip() or None

    async def run_once(self) -> None:
        snap = await self.status.snapshot()
        self.checks += 1
        self.last_check = _now()
        self.usb_present = snap.usb_present
        self.interface = snap.interface
        was_healthy = self.healthy
        self.healthy = bool(snap.usb_present and snap.interface)

        if self.healthy:
            if self._unhealthy_streak > 0:
                self._event("recovered", "adapter healthy again", "ok")
            self._unhealthy_streak = 0
            return

        self._unhealthy_streak += 1
        if was_healthy is not False:
            detail = (
                "adapter is off the USB bus" if not snap.usb_present
                else "adapter present but no interface"
            )
            self._event("degraded", detail, "info")
        await self._recover(snap)

    async def _recover(self, snap: Status) -> None:
        if self.mock:
            return
        if not snap.usb_present:
            self._event("usb-absent", "off the bus — check VMware USB passthrough", "wait")
            return

        driver = await self._driver_name(snap)
        if self._unhealthy_streak <= 1:
            self._event("driver-reload", f"reloading {driver}", "ok")
            await self.runner.run(["modprobe", "-r", driver])
            await self.runner.run(["modprobe", driver])
        else:
            busid = await self._usb_busid()
            if busid:
                self._event("usb-reset", f"resetting USB device {busid}", "ok")
                await self.runner.run([
                    "sh", "-c",
                    f"echo {busid} > /sys/bus/usb/drivers/usb/unbind; sleep 1; "
                    f"echo {busid} > /sys/bus/usb/drivers/usb/bind",
                ])
            else:
                self._event("usb-reset", "could not locate USB device path", "failed")

        # best-effort reconnect
        await self.runner.run(["nmcli", "device", "connect", snap.interface or "wlan0"])
        self.recoveries += 1

    def status_info(self) -> WatchdogStatus:
        return WatchdogStatus(
            enabled=self.enabled,
            running=self._task is not None and not self._task.done(),
            healthy=self.healthy,
            usb_present=self.usb_present,
            interface=self.interface,
            checks=self.checks,
            recoveries=self.recoveries,
            last_check=self.last_check,
            events=list(self._events),
        )

    async def _loop(self) -> None:
        while self.enabled:
            try:
                await self.run_once()
            except Exception as e:  # never let the loop die
                self._event("degraded", f"watchdog error: {e}", "failed")
            await asyncio.sleep(self.interval)

    def start(self) -> None:
        self.enabled = True
        if self._task is None or self._task.done():
            self._task = asyncio.create_task(self._loop())

    async def stop(self) -> None:
        self.enabled = False
        if self._task is not None:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
            self._task = None
