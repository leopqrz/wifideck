"""History — past capture sessions + their crack outcomes, from the SQLite store."""
from __future__ import annotations

from fastapi import APIRouter, Depends, Query

from ..auth import require_token
from ..deps import get_history_store
from ..models.history import HistoryEntry
from ..services.history import HistoryStore

router = APIRouter()


@router.get("/api/history", response_model=list[HistoryEntry])
async def history(
    limit: int = Query(100, ge=1, le=1000),
    _: bool = Depends(require_token),
    store: HistoryStore = Depends(get_history_store),
) -> list[HistoryEntry]:
    return store.entries(limit)
