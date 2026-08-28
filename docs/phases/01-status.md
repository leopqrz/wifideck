# Phase 1 — Live status & adapter health

**Status:** ✅ complete (verified against real ALFA hardware)

## What shipped

**Backend**
- `models/status.py` — `Status` model + `Health` enum (ok / disconnected / degraded).
- `services/parsers.py` — pure parsers: `iw dev`, `iw … link`, `ip addr`, driver path, band-for-freq.
- `services/status.py` — `StatusService.snapshot()` assembles status via the CommandRunner.
- `services/fixtures.py` — recorded tool output for mock mode.
- `deps.py` — `get_status_service()` dependency.
- `routers/status.py` — `GET /api/status`.
- `ws.py` — `WS /ws/status`, pushes on connect and whenever the snapshot changes (2s poll).

**Frontend**
- `useStatus` hook (subscribes to `/ws/status`).
- `AdapterStatus` panel (mode pill, network, signal meter, band, TX rate, IP, driver, link, USB).
- `SignalMeter` (five bars from dBm), `HealthBanner` (shows on degraded/disconnected).
- `TopRail` gains a live mode pill; `App` reworked to a live telemetry view.

## Acceptance gate — results

| Check | Result |
|---|---|
| `/api/status` matches real adapter (present/driver/mode/ip/signal) | ✅ live: `wlan0 · MANAGED · rtw88_8812au · 192.0.2.10/24 · -22 dBm · 5 GHz` |
| `/ws/status` streams telemetry; pushes on change | ✅ live verified |
| Detach → `health: disconnected` (≤ one 2s poll) | ✅ logic + unit test (`_FakeRunner`) |
| Present-but-no-interface → `degraded` | ✅ unit test |
| Parser unit tests against fixtures | ✅ `test_parsers.py` |
| Backend `pytest` | ✅ 18 passed |
| Frontend `vitest` / lint / build | ✅ 6 passed / clean / built |
| WS auth (bad token rejected) | ✅ live verified |

## Next: Phase 2 — Mode control (MANAGED ⇆ MONITOR)
`POST /api/mode` + a guarded state machine, wired to a toggle in the UI.
