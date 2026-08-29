# Phase 10 — Guided capture flow → v2.2

**Status:** ✅ complete

One gated, audited workflow that chains the existing services end to end — for
**authorized testing of your own networks**.

## What shipped

**Backend**
- `models/flow.py` — `FlowStep`, `FlowStatus`.
- `services/flow.py` — `CaptureFlowService`: a background orchestration that runs
  MONITOR (target channel) → start capture (locked to BSSID) → deauth burst →
  wait for the 4-way handshake → stop capture → restore MANAGED. The Phase 7
  guardrails (active enabled + explicit authorization + target in scope) are
  checked **before** touching the radio; each deauth still goes through the
  audited `ActiveService`.
- `routers/flow.py` — `POST /api/flow`, `POST /api/flow/stop`, `GET /api/flow`;
  `WS /ws/flow` streams step-by-step progress.

**Frontend**
- `useFlow` hook; `FlowPanel` (danger-zone): in-scope target dropdown, channel,
  deauth count, authorization checkbox, **Run flow**, a live step checklist
  (monitor/capture/deauth/handshake/cleanup), result message, Stop, and a pcap
  download when a handshake lands.

## Acceptance gate — results

| Check | Result |
|---|---|
| Full orchestration completes with handshake | ✅ live (mock): steps stream monitor→…→cleanup, state=done, handshake=true |
| Refused: not in scope / not authorized / active disabled | ✅ unit + endpoint tests (403) |
| Busy → 409, endpoints token-gated | ✅ tests |
| Backend `pytest` | ✅ 67 passed |
| Frontend `vitest` / lint / build | ✅ 30 passed / clean / built |
| Security re-review | ✅ 6/6 (new flow routes token-gated) |
| **Live on real hardware** | ⏳ needs root + `WIFIDECK_ENABLE_ACTIVE=1` + an in-scope target you own |

## Next options
Phase 11 (defensive WIDS-lite) · 12 (cracking integration).
