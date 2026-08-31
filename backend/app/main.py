"""WiFiDeck backend entrypoint.

A single FastAPI app, served by a root systemd service bound to localhost.
Run in dev:  uvicorn app.main:app --reload --host 127.0.0.1 --port 8787
"""
from __future__ import annotations

from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles

from . import ws
from .auth import role_for_token, token_from_headers
from .config import settings
from .deps import get_scheduler_service, get_watchdog_service, get_wids_service
from .routers import (
    active,
    anomaly,
    capture,
    connect,
    crack,
    driver,
    flow,
    health,
    history,
    me,
    metrics,
    mode,
    notify,
    report,
    scan,
    schedule,
    share,
    stations,
    status,
    watchdog,
    wids,
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Auto-start background services that are enabled.
    wd = get_watchdog_service()
    wids_svc = get_wids_service()
    scheduler = get_scheduler_service()
    if settings.watchdog_enabled and not settings.mock:
        wd.start()
    if settings.wids_enabled:  # evil-twin detection works from scans in any mode
        wids_svc.start()
    scheduler.start()  # jobs are off by default; loop just idles until one is enabled
    yield
    await wd.stop()
    await wids_svc.stop()
    await scheduler.stop()


app = FastAPI(title="WiFiDeck", version=settings.version, lifespan=lifespan)


# RBAC: a viewer token may read but not mutate. Enforced in one place so every
# mutating /api route is covered without per-route edits. No-op unless a viewer
# token is configured (then some tokens resolve to the "viewer" role).
@app.middleware("http")
async def enforce_viewer_readonly(request: Request, call_next):
    if request.url.path.startswith("/api") and request.method not in ("GET", "HEAD", "OPTIONS"):
        role = role_for_token(
            token_from_headers(
                request.headers.get("authorization"), request.headers.get("x-auth-token")
            )
        )
        if role == "viewer":
            return JSONResponse(
                {"detail": "read-only (viewer) token — this action needs an operator token"},
                status_code=403,
            )
    return await call_next(request)


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
app.include_router(me.router)
app.include_router(status.router)
app.include_router(connect.router)
app.include_router(mode.router)
app.include_router(scan.router)
app.include_router(capture.router)
app.include_router(share.router)
app.include_router(driver.router)
app.include_router(active.router)
app.include_router(watchdog.router)
app.include_router(flow.router)
app.include_router(wids.router)
app.include_router(crack.router)
app.include_router(history.router)
app.include_router(report.router)
app.include_router(notify.router)
app.include_router(metrics.router)
app.include_router(stations.router)
app.include_router(anomaly.router)
app.include_router(schedule.router)
app.include_router(ws.router)

# In production the built frontend (frontend/dist) is served from the same origin.
_dist = Path(__file__).resolve().parents[2] / "frontend" / "dist"
if _dist.is_dir():
    app.mount("/", StaticFiles(directory=str(_dist), html=True), name="frontend")
