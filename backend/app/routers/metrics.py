"""Prometheus /metrics — scrapeable gauges/counters (token-gated, like everything)."""
from __future__ import annotations

from fastapi import APIRouter, Depends, Response

from ..auth import require_token
from ..config import settings
from ..deps import get_history_store, get_watchdog_service, get_wids_service
from ..services.history import HistoryStore
from ..services.watchdog import WatchdogService
from ..services.wids import WidsService

router = APIRouter()


@router.get("/metrics")
async def metrics(
    _: bool = Depends(require_token),
    history: HistoryStore = Depends(get_history_store),
    wd: WatchdogService = Depends(get_watchdog_service),
    wids: WidsService = Depends(get_wids_service),
) -> Response:
    sessions = history.entries(1000)
    lines = [
        "# HELP wifideck_up 1 if the backend is serving",
        "# TYPE wifideck_up gauge",
        "wifideck_up 1",
        f"wifideck_active_enabled {int(settings.enable_active)}",
        f"wifideck_capture_sessions {len(sessions)}",
        f"wifideck_handshakes {sum(1 for s in sessions if s.handshake)}",
        f"wifideck_pmkids {sum(1 for s in sessions if s.pmkid)}",
        f"wifideck_cracked {sum(1 for s in sessions if s.crack_key)}",
        f"wifideck_watchdog_checks {wd.checks}",
        f"wifideck_watchdog_recoveries {wd.recoveries}",
        f"wifideck_wids_alerts {wids.status_info().alert_count}",
    ]
    return Response("\n".join(lines) + "\n", media_type="text/plain; version=0.0.4")
