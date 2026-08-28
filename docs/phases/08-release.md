# Phase 8 — Release hardening → v2.0

**Status:** ✅ complete

## What shipped

- **Versioning:** backend + frontend bumped to **2.0.0**; top rail reads `v2.0 · release`.
- **systemd unit finalized** (`backend/systemd/wifideck.service`): loopback bind,
  `EnvironmentFile`, restart-on-failure, and hardening (`ProtectSystem=full`,
  `ProtectHome`, `PrivateTmp`, `ProtectControlGroups`, `RestrictSUIDSGID`,
  `LockPersonality`, `ReadWritePaths=/opt/wifideck/data`).
- **Installer** (`install.sh`): copies to `/opt/wifideck`, builds a venv + installs
  deps, creates `data/`, writes `.env` with an `openssl`-generated token (chmod 600),
  installs + enables the service. Serves the built SPA same-origin from the backend.
- **Runtime token entry** (`TokenGate`): the SPA reads its token from `localStorage`
  (falling back to the build-time value), so a random per-install token works without
  rebuilding — on a 401 the user is prompted to paste the token once.
- **Security re-review** (`scripts/security_check.py`): inspects the live app object.
- **README** rewritten: features, dev quickstart, production install, security, tests.

## Acceptance gate — results

| Check | Result |
|---|---|
| Security re-review (6 invariants) | ✅ **6/6**: loopback bind · active-off default · **every /api route token-guarded** · localhost CORS · all 4 WS endpoints guarded · constant-time compare |
| `install.sh` valid + logic | ✅ syntax OK; venv + .env(token) + systemd flow |
| systemd unit hardened | ✅ finalized |
| Token gate works without SPA rebuild | ✅ localStorage override + 401 prompt |
| Backend `pytest` | ✅ 54 passed |
| Frontend `vitest` / lint / build | ✅ 25 passed / clean / built |

## 🏁 v2.0
All eight phases complete: status · mode · scan · capture · share · charts · driver ·
gated active/audit · installable hardened release. Run `sudo ./install.sh` (after a
frontend build) to deploy the localhost service.

## Live deploy test (your machine)
```bash
cd frontend && npm run build && cd .. && sudo ./install.sh
# open http://127.0.0.1:8787, paste the printed token
systemctl status wifideck ; journalctl -u wifideck -f
```
