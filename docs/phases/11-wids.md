# Phase 11 — Defensive monitoring (WIDS-lite) → v2.3

**Status:** ✅ complete

A defensive, positive-sum feature: *detect* attacks against your network rather
than perform them. Passive — it never transmits.

## What shipped

**Backend**
- `models/wids.py` — `WidsAlert`, `WidsStatus`.
- `services/wids.py`:
  - `find_evil_twins(networks)` — pure detector: an SSID on 2+ BSSIDs with
    **mismatched security** (e.g. an open clone of a WPA2 net). Normal enterprise
    roaming (same SSID, consistent security) is deliberately **not** flagged.
  - `WidsService` — background loop: scans → evil-twin alerts (deduped); in
    MONITOR mode counts deauth/disassoc frames via `tshark` and alerts on floods.
    100-alert ring buffer.
- `routers/wids.py` — `GET`/`POST /api/wids`; `WS /ws/wids`. Lifespan auto-starts
  when `WIFIDECK_WIDS=1`. Off by default.

**Frontend**
- `useWids` hook; `WidsPanel` — enable toggle, check counter, and a severity-coloured
  alerts timeline. Paired with the watchdog in a two-up "health & defense" row.

## Acceptance gate — results

| Check | Result |
|---|---|
| Evil-twin flagged on mismatched security (high) | ✅ unit test |
| **Enterprise roaming NOT false-flagged** | ✅ unit test (the key correctness case) |
| Distinct/single SSIDs → no alert | ✅ unit tests |
| Toggle + live `/ws/wids` stream | ✅ live (mock) |
| Endpoints token-gated | ✅ test |
| Backend `pytest` | ✅ 73 passed |
| Frontend `vitest` / lint / build | ✅ 32 passed / clean / built |
| Security re-review | ✅ 6/6 |
| **Live deauth-flood detection** | ⏳ needs root + MONITOR mode + tshark |

## Next
Phase 12 — cracking integration (aircrack/hashcat a captured handshake, scope-gated).
