"""Release security re-review — inspects the live app object and asserts the
Phase 0/7 security invariants still hold. Run with a clean env for defaults:

    env -u WIFIDECK_ENABLE_ACTIVE -u WIFIDECK_HOST PYTHONPATH=backend \
        python3 scripts/security_check.py
"""
from __future__ import annotations

import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "backend"))

from app.auth import require_token  # noqa: E402
from app.config import settings  # noqa: E402
from app.main import app  # noqa: E402
from fastapi.routing import APIRoute  # noqa: E402
from starlette.middleware.cors import CORSMiddleware  # noqa: E402

results: list[tuple[bool, str]] = []


def check(ok: bool, msg: str) -> None:
    results.append((ok, msg))


def deps_of(route: APIRoute) -> set:
    calls = set()
    stack = list(route.dependant.dependencies)
    while stack:
        d = stack.pop()
        if d.call is not None:
            calls.add(d.call)
        stack.extend(d.dependencies)
    return calls


# 1. loopback bind
check(settings.host == "127.0.0.1", f"binds to loopback (host={settings.host})")

# 2. active modules off by default
check(settings.enable_active is False, f"active modules OFF by default (enable_active={settings.enable_active})")

# 3. every /api route requires the token
unprotected = []
for route in app.routes:
    if isinstance(route, APIRoute) and route.path.startswith("/api"):
        if require_token not in deps_of(route):
            unprotected.append(f"{sorted(route.methods)} {route.path}")
check(not unprotected, f"every /api route requires token ({len(unprotected)} unprotected: {unprotected})")

# 4. CORS restricted to localhost dev origins
cors = next((m for m in app.user_middleware if m.cls is CORSMiddleware), None)
origins = cors.kwargs.get("allow_origins", []) if cors else []
bad = [o for o in origins if "127.0.0.1" not in o and "localhost" not in o]
check(cors is not None and not bad, f"CORS origins are localhost-only ({origins})")

# 5. WebSocket endpoints validate the token
ws_src = (pathlib.Path(__file__).resolve().parents[1] / "backend/app/ws.py").read_text()
ws_count = ws_src.count("@router.websocket")
guard_count = ws_src.count("valid_ws_token")
check(ws_count > 0 and guard_count >= ws_count, f"all {ws_count} WS endpoints check valid_ws_token ({guard_count} guards)")

# 6. token compared in constant time
auth_src = (pathlib.Path(__file__).resolve().parents[1] / "backend/app/auth.py").read_text()
check("compare_digest" in auth_src, "token compared with constant-time compare_digest")

# ---- report ----
print("Security re-review:")
for ok, msg in results:
    print(f"  [{'PASS' if ok else 'FAIL'}] {msg}")
passed = sum(1 for ok, _ in results if ok)
print(f"{passed}/{len(results)} invariants hold")
sys.exit(0 if passed == len(results) else 1)
