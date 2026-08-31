"""NotifyService — push alerts to configured sinks (generic webhook, ntfy, Slack).

All sinks are opt-in via env; with none set, everything is a no-op (no external
calls — important for the localhost-only default). A short per-message cooldown
prevents notification spam from a repeating condition.
"""
from __future__ import annotations

import time


class NotifyService:
    def __init__(
        self,
        webhook_url: str = "",
        ntfy_url: str = "",
        slack_url: str = "",
        cooldown: float = 30.0,
    ) -> None:
        self.webhook_url = webhook_url
        self.ntfy_url = ntfy_url
        self.slack_url = slack_url
        self.cooldown = cooldown
        self._last: dict[str, float] = {}
        self.last_error: str | None = None

    def enabled_sinks(self) -> list[str]:
        out = []
        if self.webhook_url:
            out.append("webhook")
        if self.ntfy_url:
            out.append("ntfy")
        if self.slack_url:
            out.append("slack")
        return out

    async def _deliver(self, url: str, *, json=None, content=None, headers=None) -> None:
        import httpx

        async with httpx.AsyncClient(timeout=5.0) as c:
            await c.post(url, json=json, content=content, headers=headers)

    async def send(
        self, title: str, message: str, level: str = "info", dedup_key: str | None = None
    ) -> dict:
        sinks = self.enabled_sinks()
        if not sinks:
            return {"sent": [], "skipped": "no sinks configured"}

        key = dedup_key or f"{title}|{message}"
        now = time.monotonic()
        prev = self._last.get(key)
        if prev is not None and now - prev < self.cooldown:
            return {"sent": [], "skipped": "cooldown"}
        self._last[key] = now

        sent: list[str] = []
        errors: list[str] = []
        for name in sinks:
            try:
                await self._deliver_to(name, title, message, level)
                sent.append(name)
            except Exception as e:  # a sink being down must never break the caller
                errors.append(f"{name}: {e}")
                self.last_error = f"{name}: {e}"
        return {"sent": sent, "errors": errors}

    async def _deliver_to(self, name: str, title: str, message: str, level: str) -> None:
        if name == "webhook":
            await self._deliver(self.webhook_url, json={
                "source": "wifideck", "title": title, "message": message, "level": level,
            })
        elif name == "ntfy":
            prio = {"crit": "urgent", "high": "high", "info": "default", "low": "low"}.get(level, "default")
            await self._deliver(
                self.ntfy_url, content=message.encode(),
                headers={"Title": title, "Priority": prio, "Tags": "wifideck"},
            )
        elif name == "slack":
            await self._deliver(self.slack_url, json={"text": f"*{title}*\n{message}"})
