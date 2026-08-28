"""Scope allowlist, audit log, and gated active (deauth) endpoints."""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from ..auth import require_token
from ..config import settings
from ..deps import get_active_service, get_audit_log, get_scope_list
from ..models.audit import ActiveState, AuditEntry, ScopeTarget
from ..services.active import (
    ActiveDisabled,
    ActiveService,
    ModeRequired,
    NotAuthorized,
    NotInScope,
)
from ..services.audit import AuditLog
from ..services.scope import ScopeList

router = APIRouter()


# ---- scope allowlist ------------------------------------------------------
class ScopeAdd(BaseModel):
    bssid: str
    ssid: str | None = None
    note: str | None = None


@router.get("/api/scope", response_model=list[ScopeTarget])
async def list_scope(_: bool = Depends(require_token), scope: ScopeList = Depends(get_scope_list)):
    return scope.list()


@router.post("/api/scope", response_model=ScopeTarget)
async def add_scope(
    req: ScopeAdd,
    _: bool = Depends(require_token),
    scope: ScopeList = Depends(get_scope_list),
    audit: AuditLog = Depends(get_audit_log),
):
    try:
        target = scope.add(req.bssid, req.ssid, req.note)
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
    audit.record("scope.add", "ok", target_bssid=target.bssid, target_ssid=target.ssid)
    return target


@router.delete("/api/scope/{bssid}")
async def remove_scope(
    bssid: str,
    _: bool = Depends(require_token),
    scope: ScopeList = Depends(get_scope_list),
    audit: AuditLog = Depends(get_audit_log),
):
    if not scope.remove(bssid):
        raise HTTPException(status_code=404, detail="Not in scope.")
    audit.record("scope.remove", "ok", target_bssid=bssid.upper())
    return {"removed": bssid.upper()}


# ---- audit log ------------------------------------------------------------
@router.get("/api/audit", response_model=list[AuditEntry])
async def get_audit(
    limit: int = 100,
    _: bool = Depends(require_token),
    audit: AuditLog = Depends(get_audit_log),
):
    return audit.recent(limit=limit)


# ---- active modules -------------------------------------------------------
@router.get("/api/active", response_model=ActiveState)
async def active_state(_: bool = Depends(require_token)):
    return ActiveState(enabled=settings.enable_active)


class DeauthRequest(BaseModel):
    bssid: str
    client: str | None = None
    count: int = Field(default=5, ge=1, le=64)
    authorized: bool = False


@router.post("/api/active/deauth", response_model=AuditEntry)
async def deauth(
    req: DeauthRequest,
    _: bool = Depends(require_token),
    svc: ActiveService = Depends(get_active_service),
):
    try:
        return await svc.deauth(req.bssid, req.client, req.count, req.authorized)
    except ActiveDisabled as e:
        raise HTTPException(status_code=403, detail=str(e))
    except NotAuthorized as e:
        raise HTTPException(status_code=403, detail=str(e))
    except NotInScope as e:
        raise HTTPException(status_code=403, detail=str(e))
    except ModeRequired as e:
        raise HTTPException(status_code=409, detail=str(e))
    except RuntimeError as e:
        raise HTTPException(status_code=500, detail=str(e))
