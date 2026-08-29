# Phase 9 — Self-healing watchdog → v2.1

**Status:** ✅ complete

Directly targets the recurring RTL8812AU `-71` USB disconnects: the tool watches
adapter health and auto-recovers instead of leaving you to debug it by hand.

## What shipped

**Backend**
- `models/watchdog.py` — `WatchdogEvent`, `WatchdogStatus`.
- `services/watchdog.py` — `WatchdogService`: a background loop that probes health
  (on the USB bus + interface present) and, on failure, escalates recovery:
  1. **driver reload** (`modprobe -r/-a`) when present but no interface,
  2. **USB reset** via sysfs unbind/bind when still wedged,
  3. **reconnect** via NetworkManager;
  a full off-bus drop is reported as a host/VMware-passthrough issue (Linux can't
  fix it). Keeps a 50-event ring buffer + check/recovery stats.
- `routers/watchdog.py` — `GET`/`POST /api/watchdog`; `WS /ws/watchdog`.
- App lifespan auto-starts it when `WIFIDECK_WATCHDOG=1` (real hardware). Off by default.

**Frontend**
- `useWatchdog` hook; `WatchdogPanel` — enable/stop toggle, health pill, check/recovery
  counters, and a live recovery-event log.

## Acceptance gate — results

| Check | Result |
|---|---|
| Healthy probe → no action | ✅ unit test (mock) |
| Recovery escalates: reload → USB reset | ✅ unit tests (RecordingRunner) |
| Off-bus drop reported, no driver thrash | ✅ unit test |
| Toggle + live stream | ✅ live (mock): enable→running, `/ws/watchdog` streams, disable |
| Endpoints token-gated | ✅ test |
| Backend `pytest` | ✅ 61 passed |
| Frontend `vitest` / lint / build | ✅ 27 passed / clean / built |
| **Live recovery on real `-71` drop** | ⏳ enable with `WIFIDECK_WATCHDOG=1` as root and pull the adapter to watch it recover |

## Next options
Phase 10 (guided capture flow) · 11 (defensive WIDS-lite) · 12 (cracking integration).
