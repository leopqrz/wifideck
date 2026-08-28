# Phase 0 — Foundation & scaffolding

**Status:** ✅ complete (backend verified live; frontend scaffolded, runs once Node is installed)

## What shipped

**Backend** (`backend/`)
- FastAPI app (`app/main.py`) with CORS for the Vite dev origin.
- `GET /api/health` (`app/routers/health.py`) — token-protected liveness.
- `WS /ws/echo` (`app/ws.py`) — authenticated echo channel.
- Token auth (`app/auth.py`) — Bearer / `X-Auth-Token` / WS `?token=`, constant-time.
- Env config (`app/config.py`) — loopback bind, port, token, `WIFIDECK_MOCK`.
- Command-runner seam (`app/services/runner.py`) — real vs. mock foundation.
- systemd unit (`backend/systemd/wifideck.service`), `.env.example`, `requirements.txt`.
- Tests (`backend/tests/`): health 200/401, header variants, loopback-bind assertion, WS token reject + roundtrip.

**Frontend** (`frontend/`)
- Vite + React + TypeScript + Tailwind scaffold with the locked command-center tokens (`tailwind.config.ts`, `index.css`).
- Status shell (`App.tsx`, `TopRail`, `StatusPill`) showing live **API** and **WebSocket** state.
- `useHealth` + `useWebSocket` (reconnecting) hooks; token-attaching API client.
- Vitest setup + `TopRail` test; ESLint flat config; dev-server proxy for `/api` + `/ws`.

**Project**
- `Makefile` (setup/backend/frontend/test/lint), `.gitignore`, GitHub Actions CI, docs.

## Acceptance gate — results

| Check | Result |
|---|---|
| `GET /api/health` → 200 JSON with token | ✅ verified live (`{"status":"ok",...}`) |
| `GET /api/health` → 401 without / wrong token | ✅ verified live + unit tests |
| Service bound to `127.0.0.1` only (not `0.0.0.0`) | ✅ `ss -ltnp` showed `127.0.0.1:8787` |
| WS rejects bad token, echoes with good token | ✅ unit tests pass |
| Backend `pytest` green | ✅ 7 passed |
| Frontend `vitest` green | ✅ 2 passed |
| Frontend type-check + production build | ✅ `tsc --noEmit && vite build` (36 modules) |
| Frontend `eslint` clean | ✅ no errors |
| E2E: SPA served + health + WS echo + WS auth-reject | ✅ all passed |

Node 20+ installed via **nvm** (Node v24 LTS). To run locally:

```bash
cd ~/Projects/wifideck
make backend      # terminal 1  → http://127.0.0.1:8787
make frontend     # terminal 2  → http://127.0.0.1:5173 (proxies /api + /ws)
make test         # backend + frontend suites
```

## Next: Phase 1 — Live status & adapter health
Real adapter telemetry (`/api/status` + `/ws/status`) and the USB/`-71` health watcher.
