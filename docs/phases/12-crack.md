# Phase 12 — Handshake cracking → v2.4

**Status:** ✅ complete — final planned phase.

Runs `aircrack-ng` on a handshake you captured, against a wordlist — for
**authorized testing of your own networks**.

## What shipped

**Backend**
- `models/crack.py` — `CrackStatus`.
- `services/crack.py`:
  - `parse_aircrack_progress` — pure: latest `keys tested`/rate + any `KEY FOUND!`.
  - `CrackService` — background `aircrack-ng` job streaming progress. Gated: the
    session's target BSSID must be in the scope allowlist AND the request must
    carry explicit authorization; every attempt is audited. Compute-only (no transmit).
- `routers/crack.py` — `POST /api/crack`, `POST /api/crack/stop`, `GET /api/crack`;
  `WS /ws/crack`. Default wordlist via `WIFIDECK_WORDLIST`.

**Frontend**
- `useCrack` hook; `CrackPanel` (danger-zone): capture-session dropdown (pcaps),
  wordlist input, authorization checkbox, progress bar + rate, and a highlighted
  **key found** box.

## Acceptance gate — results

| Check | Result |
|---|---|
| Progress + key parsed from aircrack output | ✅ unit tests |
| Refused: not in scope / not authorized; unknown session 404 | ✅ unit + endpoint |
| Full mock crack → found + key, streamed | ✅ live (mock): `/ws/crack` → found `mock-passphrase` |
| Endpoints token-gated | ✅ test |
| Backend `pytest` | ✅ 81 passed |
| Frontend `vitest` / lint / build | ✅ 34 passed / clean / built |
| Security re-review | ✅ 6/6 |
| **Live crack on a real handshake** | ⏳ capture a handshake you own + a wordlist (gunzip rockyou) |

## 🏁 All phases complete
Phases 0–12: status · mode · scan · capture · share · charts · driver · active/audit ·
release · watchdog · guided flow · WIDS-lite · cracking. A full offensive + defensive
localhost command center for the ALFA.
