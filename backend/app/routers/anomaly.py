"""Device anomaly / risk scoring over observed stations."""
from __future__ import annotations

from fastapi import APIRouter, Depends

from ..auth import require_token
from ..deps import get_anomaly_service
from ..models.anomaly import Anomaly
from ..services.anomaly import AnomalyService

router = APIRouter()


@router.get("/api/anomalies", response_model=list[Anomaly])
async def anomalies(
    _: bool = Depends(require_token),
    svc: AnomalyService = Depends(get_anomaly_service),
) -> list[Anomaly]:
    return svc.anomalies()
