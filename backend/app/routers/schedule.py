"""Scheduling — list jobs, enable/interval, or run one now."""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from ..auth import require_token
from ..deps import get_scheduler_service
from ..models.schedule import Job
from ..services.scheduler import SchedulerService

router = APIRouter()


class JobUpdate(BaseModel):
    enabled: bool | None = None
    interval_sec: int | None = Field(default=None, ge=10, le=86400)


@router.get("/api/schedule", response_model=list[Job])
async def list_jobs(
    _: bool = Depends(require_token),
    svc: SchedulerService = Depends(get_scheduler_service),
) -> list[Job]:
    return svc.jobs()


@router.post("/api/schedule/{jid}", response_model=Job)
async def update_job(
    jid: str,
    req: JobUpdate,
    _: bool = Depends(require_token),
    svc: SchedulerService = Depends(get_scheduler_service),
) -> Job:
    try:
        return svc.set(jid, enabled=req.enabled, interval_sec=req.interval_sec)
    except KeyError:
        raise HTTPException(status_code=404, detail="unknown job") from None


@router.post("/api/schedule/{jid}/run", response_model=Job)
async def run_job(
    jid: str,
    _: bool = Depends(require_token),
    svc: SchedulerService = Depends(get_scheduler_service),
) -> Job:
    try:
        return await svc.run_now(jid)
    except KeyError:
        raise HTTPException(status_code=404, detail="unknown job") from None
