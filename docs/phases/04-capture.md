# Phase 4 — Capture & results

**Status:** ✅ complete (contract + stream verified; live capture is a root+monitor step)

## What shipped

**Backend**
- `models/session.py` — `CaptureSession` + `CaptureDetail` (with live `networks`).
- `services/capture.py`:
  - `CaptureService` — start/stop/list/detail, manages an airodump-ng subprocess
    (`--output-format pcap,csv`, optional `-c channel` / `--bssid`); single active
    session (one adapter), history retained.
  - `refresh()` — reads the session CSV for live AP/client counts and runs
    `aircrack-ng` on the `.cap` for handshake/PMKID flags.
  - `parse_aircrack_handshakes` — reads the **count** ("(1 handshake)"), so a
    "0 handshake" line does not register (unit-tested).
- `routers/capture.py` — start / stop / list / detail / **pcap download** (FileResponse).
- `ws.py` — `WS /ws/capture` streams the active session detail every 2s.
- Mock mode simulates a running session from fixtures.

**Frontend**
- `useCapture` hook on `/ws/capture`; client `startCapture` / `stopCapture` /
  `downloadPcap` (blob download with auth header).
- `CaptureControl` — start form (channel + optional target BSSID), monitor-mode
  hint, live session card (AP/client counts, **handshake / PMKID indicators**),
  Stop, and Download .pcap.

## Acceptance gate — results

| Check | Result |
|---|---|
| Start capture → live AP/client counts stream | ✅ live (mock): `/ws/capture` → running, ap=1, clients=2 |
| Handshake indicator lights | ✅ live (mock handshake=true); parser unit-tested on aircrack output |
| Handshake scoped to target BSSID; "0 handshake" ignored | ✅ unit test (caught a real bug) |
| Session lifecycle (start/list/detail/stop), busy → 409 | ✅ endpoint tests |
| pcap download endpoint (404 until data) | ✅ endpoint test |
| Backend `pytest` | ✅ 35 passed |
| Frontend `vitest` / lint / build | ✅ 15 passed / clean / built |
| **Live capture on real hardware** (handshake on own AP, pcap opens in Wireshark) | ⏳ **root + MONITOR step** |

## Verifying live (root + MONITOR)
Switch to MONITOR (Phase 2), run the backend as root, then Start capture on the
target's channel; reconnect a device on **your own** AP to force a handshake — the
indicator lights and the `.cap` downloads and opens in Wireshark.

## Next: Phase 5 — Internet sharing to the host
`POST /api/share` (NAT the ALFA uplink to macOS) with the copyable route/DNS steps.
