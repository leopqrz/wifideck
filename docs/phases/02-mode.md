# Phase 2 — Mode control (MANAGED ⇆ MONITOR)

**Status:** ✅ complete (logic + contract verified; live switch is a root-run step)

## What shipped

**Backend**
- `services/mode.py` — `ModeService` with an `asyncio.Lock` state machine that
  serializes switches (`ModeBusy` → HTTP 409). Mirrors `wifi-monitor` /
  `wifi-managed`: NM handoff, `airmon-ng check kill`, `iw set type`, channel lock,
  and (for managed) NM restart + reconnect. Critical steps checked (`ModeError`).
- `routers/mode.py` — `POST /api/mode` (`mode`, optional `channel` 1–196).
- `deps.py` — shared singleton `ModeService` so the lock is process-wide.

**Frontend**
- `setMode()` API call; `ModeControl` component — segmented MANAGED/MONITOR toggle,
  channel input, inline confirmation before MONITOR (it drops the link), live
  "switching…" state cleared by the status stream, and error surfacing.
- Wired into `App` beside the adapter panel.

## Acceptance gate — results

| Check | Result |
|---|---|
| `to monitor` issues `iw set type monitor` + channel + NM handoff | ✅ unit test (RecordingRunner) |
| `to managed` issues `iw set type managed` + NM restart/reconnect | ✅ unit test |
| Concurrent switch rejected (`409`) | ✅ unit test (`ModeBusy`) |
| `POST /api/mode` contract (200 / 422 invalid / 422 bad channel / 401) | ✅ live (mock mode) |
| Backend `pytest` | ✅ 24 passed |
| Frontend `vitest` / lint / build | ✅ 8 passed / clean / built |
| **Live switch on real hardware** (type+channel set; managed restores internet) | ⏳ **run under root** (see below) |

## Verifying the live switch (needs root)

Mode switching runs `iw` / `ip` / `nmcli` / `airmon-ng`, which require root. Run the
dev backend under sudo, then use the UI toggle (or curl):

```bash
cd ~/Projects/wifideck/backend
sudo WIFIDECK_TOKEN=dev-token-change-me PYTHONPATH=. \
  python3 -m uvicorn app.main:app --host 127.0.0.1 --port 8787
# then in the UI (make frontend) click MONITOR / MANAGED, or:
curl -X POST localhost:8787/api/mode -H "Authorization: Bearer dev-token-change-me" \
  -H "Content-Type: application/json" -d '{"mode":"monitor","channel":6}'
```

Expected: `iw dev wlan0 info` shows `type monitor` on channel 6; switching back to
`managed` reconnects and restores internet. In production the root systemd service
does this automatically.

## Next: Phase 3 — Scanning (MVP)
`WS /ws/scan` with a unified network table (nmcli in managed, airodump in monitor).
