"""Shared FastAPI dependencies."""
from __future__ import annotations

from .config import settings
from .services.active import ActiveService
from .services.anomaly import AnomalyService
from .services.audit import AuditLog
from .services.capture import CaptureService
from .services.connect import ConnectService
from .services.crack import CrackService
from .services.driver import DriverService
from .services.flow import CaptureFlowService
from .services.handshake import HandshakeVerifier
from .services.history import HistoryStore
from .services.known import KnownNetworks
from .services.mode import ModeService
from .services.notify import NotifyService
from .services.runner import CommandRunner
from .services.scan import ScanService
from .services.scheduler import SchedulerService
from .services.scope import ScopeList
from .services.share import ShareService
from .services.stations import StationService
from .services.status import StatusService
from .services.watchdog import WatchdogService
from .services.wids import WidsService


def get_status_service() -> StatusService:
    return StatusService(CommandRunner(mock=settings.mock))


def get_connect_service() -> ConnectService:
    return ConnectService(
        CommandRunner(mock=settings.mock),
        StatusService(CommandRunner(mock=settings.mock)),
        settings.mock,
    )


def get_driver_service() -> DriverService:
    return DriverService(
        CommandRunner(mock=settings.mock),
        StatusService(CommandRunner(mock=settings.mock)),
    )


# The last MANAGED scan, snapshotted when we switch to MONITOR (shared singleton,
# backed by a JSON file). Read by the /api/scan/known endpoint.
_known_networks = KnownNetworks(settings.known_file)


def get_known_networks() -> KnownNetworks:
    return _known_networks


# ModeService holds the switch state machine, so it must be a single shared
# instance across requests (its asyncio.Lock serializes concurrent switches). It
# also snapshots a fresh scan into _known_networks on the way into monitor.
_mode_service = ModeService(
    runner=CommandRunner(mock=settings.mock),
    status=StatusService(CommandRunner(mock=settings.mock)),
    scan=ScanService(CommandRunner(mock=settings.mock)),
    known=_known_networks,
)


def get_mode_service() -> ModeService:
    return _mode_service


# SQLite history — persists capture sessions + crack outcomes (shared singleton).
_history_store = HistoryStore(settings.db_file)


def get_history_store() -> HistoryStore:
    return _history_store


# Client/station intelligence — accumulates sightings across monitor scans.
_station_service = StationService(settings.mock)


def get_station_service() -> StationService:
    return _station_service


# Device anomaly / risk scoring over the observed stations (heuristic foundation).
_anomaly_service = AnomalyService(_station_service)


def get_anomaly_service() -> AnomalyService:
    return _anomaly_service


# CaptureService holds active sessions/subprocesses, so it's a shared singleton.
_capture_service = CaptureService(
    runner=CommandRunner(mock=settings.mock),
    base_dir=settings.capture_dir,
    mock=settings.mock,
    history=_history_store,
)


def get_capture_service() -> CaptureService:
    return _capture_service


def get_handshake_verifier() -> HandshakeVerifier:
    return HandshakeVerifier(CommandRunner(mock=settings.mock), mock=settings.mock)


# ShareService keeps the mock on/off flag, so it's a shared singleton too.
_share_service = ShareService(
    runner=CommandRunner(mock=settings.mock),
    status=StatusService(CommandRunner(mock=settings.mock)),
    downlink=settings.share_downlink,
    mock=settings.mock,
)


def get_share_service() -> ShareService:
    return _share_service


# Scope allowlist + audit log are shared singletons (backed by files on disk).
_scope_list = ScopeList(settings.scope_file)
_audit_log = AuditLog(settings.audit_log)


def get_scope_list() -> ScopeList:
    return _scope_list


def get_audit_log() -> AuditLog:
    return _audit_log


# Notifications — a shared sink dispatcher (webhook/ntfy/slack), off unless configured.
_notify_service = NotifyService(
    webhook_url=settings.webhook_url,
    ntfy_url=settings.ntfy_url,
    slack_url=settings.slack_url,
)


def get_notify_service() -> NotifyService:
    return _notify_service


_watchdog_service = WatchdogService(
    runner=CommandRunner(mock=settings.mock),
    status=StatusService(CommandRunner(mock=settings.mock)),
    interval=settings.watchdog_interval,
    mock=settings.mock,
    enabled=settings.watchdog_enabled,
    notify=_notify_service,
)


def get_watchdog_service() -> WatchdogService:
    return _watchdog_service


_wids_service = WidsService(
    runner=CommandRunner(mock=settings.mock),
    scan=ScanService(CommandRunner(mock=settings.mock)),
    status=StatusService(CommandRunner(mock=settings.mock)),
    interval=settings.wids_interval,
    deauth_threshold=settings.wids_deauth_threshold,
    mock=settings.mock,
    enabled=settings.wids_enabled,
    notify=_notify_service,
    baseline_file=settings.wids_baseline_file,
)


def get_wids_service() -> WidsService:
    return _wids_service


# Scheduler actions — each returns a short result string for the last-run display.
async def _sched_scan() -> str:
    nets = await ScanService(CommandRunner(mock=settings.mock)).scan_managed()
    _known_networks.save(nets)
    return f"{len(nets)} networks"


async def _sched_wids() -> str:
    await _wids_service.run_once()
    return f"{_wids_service.status_info().alert_count} alerts"


async def _sched_heartbeat() -> str:
    import time as _t

    r = await _notify_service.send("WiFiDeck", "scheduler heartbeat", dedup_key=f"hb:{_t.time()}")
    return f"sent: {r.get('sent')}" if r.get("sent") else (r.get("skipped") or "no sinks")


_scheduler_service = SchedulerService({
    "scan": _sched_scan, "wids": _sched_wids, "heartbeat": _sched_heartbeat,
})


def get_scheduler_service() -> SchedulerService:
    return _scheduler_service


def get_active_service() -> ActiveService:
    return ActiveService(
        runner=CommandRunner(mock=settings.mock),
        scope=_scope_list,
        audit=_audit_log,
        status=StatusService(CommandRunner(mock=settings.mock)),
        enabled=settings.enable_active,
        mock=settings.mock,
    )


# Guided capture flow orchestrates the shared mode/capture services + a gated
# ActiveService; single shared instance (it holds one running flow at a time).
_flow_service = CaptureFlowService(
    mode=_mode_service,
    capture=_capture_service,
    active=ActiveService(
        runner=CommandRunner(mock=settings.mock),
        scope=_scope_list,
        audit=_audit_log,
        status=StatusService(CommandRunner(mock=settings.mock)),
        enabled=settings.enable_active,
        mock=settings.mock,
    ),
    scope=_scope_list,
    status=StatusService(CommandRunner(mock=settings.mock)),
    enabled=settings.enable_active,
    mock=settings.mock,
)


def get_flow_service() -> CaptureFlowService:
    return _flow_service


# Handshake cracking — single shared instance (one crack job at a time).
_crack_service = CrackService(
    capture=_capture_service,
    scope=_scope_list,
    audit=_audit_log,
    default_wordlist=settings.wordlist,
    mock=settings.mock,
    history=_history_store,
)


def get_crack_service() -> CrackService:
    return _crack_service
