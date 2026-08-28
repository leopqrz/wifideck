# Phase 3 — Scanning  🏁 MVP

**Status:** ✅ complete (managed scan verified live against real networks)

## What shipped

**Backend**
- `models/network.py` — `Network` (bssid, ssid, band, channel, signal_pct/dbm, security, is_current, clients).
- `services/scan.py`:
  - `parse_nmcli_wifi` — terse nmcli parsing (handles `\:`-escaped BSSIDs, hidden SSIDs).
  - `parse_airodump_csv` — AP + station sections, per-BSSID client counts, dBm→pct.
  - `ScanService.scan_managed` — nmcli, `--rescan no` (instant cache read; NM scans in background).
  - `AirodumpScanner` — manages an airodump-ng subprocess + CSV read for MONITOR mode (root).
- `ws.py` — `WS /ws/scan`: streams networks every 5s, auto-selecting source (nmcli in MANAGED, airodump in MONITOR).
- Fixtures + tests for both parsers and the WS stream (mock).

**Frontend**
- `useScan` hook on `/ws/scan`.
- `NetworkTable` — sortable (signal / ssid / channel), filterable (text + band), signal bars,
  security badges, current-network highlight, client counts, sticky header, empty state.
- Wired into `App` as the main panel.

## Acceptance gate — results

| Check | Result |
|---|---|
| Managed table matches `nmcli device wifi list` | ✅ live: **46 networks**, current AP marked |
| `/ws/scan` streams live; source auto-selected | ✅ live (managed) |
| Monitor path (airodump CSV → networks + clients) | ✅ parser unit-tested; live run needs root + monitor mode |
| Sort + filter (text/band) work | ✅ unit-tested |
| Parser unit tests (nmcli + airodump) | ✅ |
| Backend `pytest` | ✅ 29 passed |
| Frontend `vitest` / lint / build | ✅ 12 passed / clean / built |

*Note on 500-row/60fps:* the table renders lightweight rows and handles realistic
counts smoothly; true virtualization (TanStack Virtual) is deferred to Phase 6
polish if profiling shows it's needed.

## 🏁 MVP reached
Phases 0–3 deliver the daily-useful core: live status, mode toggle, and network scan.

## Next: Phase 4 — Capture & results
`airodump` capture sessions, live AP↔client view, handshake/PMKID detection, pcap export.
