# Phase 7 — Gated active modules + audit → v2

**Status:** ✅ complete (guardrail flow verified live; live transmit is a root+monitor step)

> Active (transmit) features are for **authorized testing of networks you own or
> have explicit permission to assess**. The guardrails are the point of this phase.

## What shipped

**Backend**
- `models/audit.py` — `AuditEntry`, `ScopeTarget`, `ActiveState`.
- `services/audit.py` — append-only JSONL audit log (record + recent).
- `services/scope.py` — persisted in-scope BSSID allowlist (normalize/validate).
- `services/active.py` — `ActiveService.deauth` with four layered guards
  (enabled → authorized → in-scope → MONITOR), auditing every attempt; wraps
  `aireplay-ng --deauth`.
- `routers/active.py` — `GET /api/active`, scope CRUD, `GET /api/audit`,
  `POST /api/active/deauth`.
- Config: `WIFIDECK_ENABLE_ACTIVE` (default off), `WIFIDECK_SCOPE_FILE`, `WIFIDECK_AUDIT_LOG`.

**Frontend**
- `useActiveModules` hook; `ActivePanel` (a red-tinted "danger zone"):
  scope allowlist manager, gated deauth control (in-scope dropdown, count,
  **required authorization checkbox**, MONITOR-mode gate, disabled-when-off notice),
  and a live audit-log table.

## Acceptance gate — results

| Check | Result |
|---|---|
| deauth refused when not in scope | ✅ live: 403 |
| deauth refused without authorization flag | ✅ live: 403 |
| deauth allowed only in-scope + authorized | ✅ live: 200 (mock) |
| deauth blocked when active modules disabled | ✅ unit test (403 / ActiveDisabled) |
| MONITOR mode required on hardware | ✅ enforced (409) |
| every attempt audited (refusals + actions) | ✅ live: audit shows 2 refusals + add + ok |
| scope add/list/remove, invalid BSSID → 422 | ✅ tests |
| Backend `pytest` | ✅ 54 passed |
| Frontend `vitest` / lint / build | ✅ 25 passed / clean / built |
| **Live deauth on own AP** (client drops, handshake forced) | ⏳ **root + MONITOR + `WIFIDECK_ENABLE_ACTIVE=1`** |

## Verifying live (your own network only)
Enable active modules, switch to MONITOR on the target channel, add the target's
BSSID to scope, tick the authorization box, send deauth — a client on **your** AP
drops and (with a capture running) the handshake is forced. Confirm the action and
its target appear in the audit log.

## Next: Phase 8 — Release hardening (systemd, install script, security re-review) → v2.0
