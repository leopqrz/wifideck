"""WiFiDeck backend entrypoint.

A single FastAPI app, served by a root systemd service bound to localhost.
Run in dev:  uvicorn app.main:app --reload --host 127.0.0.1 --port 8787
"""
from __future__ import annotations

from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from . import ws
from .config import settings
from .deps import get_watchdog_service, get_wids_service
from .routers import (
    active,
    capture,
    crack,
    driver,
    flow,
    health,
    mode,
    share,
    status,
    watchdog,
    wids,
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Auto-start background services that are enabled.
    wd = get_watchdog_service()
    wids_svc = get_wids_service()
    if settings.watchdog_enabled and not settings.mock:
        wd.start()
    if settings.wids_enabled:  # evil-twin detection works from scans in any mode
        wids_svc.start()
    yield
    await wd.stop()
    await wids_svc.stop()


app = FastAPI(title="WiFiDeck", version=settings.version, lifespan=lifespan)

# The Vite dev server (5173) talks to this API cross-origin during development.
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://127.0.0.1:5173",
        "http://localhost:5173",
    ],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health.router)
app.include_router(status.router)
app.include_router(mode.router)
app.include_router(capture.router)
app.include_router(share.router)
app.include_router(driver.router)
app.include_router(active.router)
app.include_router(watchdog.router)
app.include_router(flow.router)
app.include_router(wids.router)
app.include_router(crack.router)
app.include_router(ws.router)

# In production the built frontend (frontend/dist) is served from the same origin.
_dist = Path(__file__).resolve().parents[2] / "frontend" / "dist"
if _dist.is_dir():
    app.mount("/", StaticFiles(directory=str(_dist), html=True), name="frontend")
