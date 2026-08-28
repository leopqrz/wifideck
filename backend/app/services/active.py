"""ActiveService — gated transmit actions (deauth).

Layered guardrails, checked in order; every attempt (allowed OR refused) is
written to the audit log:
  1. active modules enabled in config           (else ActiveDisabled)
  2. explicit per-action authorization flag      (else NotAuthorized)
  3. target BSSID present in the scope allowlist  (else NotInScope)
  4. adapter in MONITOR mode                       (else ModeRequired)

Only for authorized testing of networks you own or have permission to assess.
"""
from __future__ import annotations

from ..models.audit import AuditEntry
from .audit import AuditLog
from .runner import CommandRunner
from .scope import ScopeList, normalize_bssid
from .status import StatusService


class ActiveDisabled(Exception):
    pass


class NotAuthorized(Exception):
    pass


class NotInScope(Exception):
    pass


class ModeRequired(Exception):
    pass


class ActiveService:
    def __init__(
        self,
        runner: CommandRunner,
        scope: ScopeList,
        audit: AuditLog,
        status: StatusService,
        enabled: bool,
        mock: bool,
    ) -> None:
        self.runner = runner
        self.scope = scope
        self.audit = audit
        self.status = status
        self.enabled = enabled
        self.mock = mock

    async def deauth(
        self, bssid: str, client: str | None, count: int, authorized: bool
    ) -> AuditEntry:
        norm = normalize_bssid(bssid) or bssid.strip().upper()
        target = next((t for t in self.scope.list() if t.bssid == norm), None)
        ssid = target.ssid if target else None

        def refuse(reason: str):
            self.audit.record(
                "deauth.refused", "refused", target_bssid=norm, target_ssid=ssid, detail=reason
            )

        # 1. globally enabled?
        if not self.enabled:
            refuse("active modules disabled in config")
            raise ActiveDisabled("Active modules are disabled (WIFIDECK_ENABLE_ACTIVE=1 to enable).")

        # 2. explicit authorization for THIS action?
        if not authorized:
            refuse("authorization flag not set")
            raise NotAuthorized("Action requires an explicit authorization confirmation.")

        # 3. target in the scope allowlist?
        if not self.scope.contains(norm):
            refuse("target not in authorized scope")
            raise NotInScope(f"{norm} is not in the authorized scope allowlist.")

        # 4. monitor mode (real hardware)
        snap = await self.status.snapshot()
        if not self.mock and snap.mode != "MONITOR":
            refuse("adapter not in MONITOR mode")
            raise ModeRequired("Deauth requires MONITOR mode.")

        iface = snap.interface or "wlan0"
        if not self.mock:
            args = ["aireplay-ng", "--deauth", str(count), "-a", norm]
            if client:
                args += ["-c", client]
            args.append(iface)
            result = await self.runner.run(args, timeout=30)
            if not result.ok:
                self.audit.record(
                    "deauth", "error", target_bssid=norm, target_ssid=ssid,
                    detail=(result.stderr.strip() or f"exit {result.returncode}")[:200],
                )
                raise RuntimeError(result.stderr.strip() or "aireplay-ng failed")

        return self.audit.record(
            "deauth", "ok", target_bssid=norm, target_ssid=ssid,
            detail=f"count={count}" + (f" client={client}" if client else " (broadcast)"),
        )
