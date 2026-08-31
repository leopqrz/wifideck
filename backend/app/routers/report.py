"""Assessment report — aggregate JSON, or a self-contained HTML page to print/share."""
from __future__ import annotations

from fastapi import APIRouter, Depends
from fastapi.responses import HTMLResponse

from ..auth import require_token
from ..config import settings
from ..deps import (
    get_audit_log,
    get_history_store,
    get_known_networks,
    get_scope_list,
)
from ..models.report import Report
from ..services import report as report_svc
from ..services.audit import AuditLog
from ..services.history import HistoryStore
from ..services.known import KnownNetworks
from ..services.scope import ScopeList

router = APIRouter()


@router.get("/api/report/data", response_model=Report)
async def report_data(
    _: bool = Depends(require_token),
    history: HistoryStore = Depends(get_history_store),
    audit: AuditLog = Depends(get_audit_log),
    scope: ScopeList = Depends(get_scope_list),
    known: KnownNetworks = Depends(get_known_networks),
) -> Report:
    return report_svc.gather(history, audit, scope, known, settings.version)


@router.get("/api/report", response_class=HTMLResponse)
async def report_html(
    _: bool = Depends(require_token),
    history: HistoryStore = Depends(get_history_store),
    audit: AuditLog = Depends(get_audit_log),
    scope: ScopeList = Depends(get_scope_list),
    known: KnownNetworks = Depends(get_known_networks),
) -> HTMLResponse:
    r = report_svc.gather(history, audit, scope, known, settings.version)
    return HTMLResponse(report_svc.render_html(r))
