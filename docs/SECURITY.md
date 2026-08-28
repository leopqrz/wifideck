# Security model & baseline checklist

WiFiDeck runs as root (mode switching, capture, and NAT require it) and controls a
wireless radio. The security posture is therefore deliberately conservative.

## Baseline (enforced from Phase 0)

- [x] **Loopback only.** Service binds to `127.0.0.1`. Never bind to `0.0.0.0` or a
      routable address. Asserted in `tests/test_security.py`.
- [x] **Token on everything.** Every HTTP route and WebSocket requires a shared
      token (`WIFIDECK_TOKEN`). Constant-time comparison; `401` / WS `1008` on failure.
- [x] **No secrets in logs.** The token is never logged.
- [ ] **Real token in production.** Replace `dev-token-change-me` — generate with
      `openssl rand -hex 24`. (Enforced/reminded at install, Phase 8.)

## To be added in later phases

- **Audit log** (Phase 7): every transmit/active action recorded with time,
  module, and target.
- **Authorization gate** (Phase 7): active modules off by default; require an
  explicit "authorized on this target" confirmation + an in-scope BSSID allowlist.
- **systemd hardening** (Phase 8): `ProtectSystem`, `ProtectHome`, `PrivateTmp`,
  minimal writable paths.
- **Re-run this checklist** as the Phase 8 release gate.

## Threat notes

- The tool is a **local operator console**, not a network service. The trust
  boundary is the loopback interface + the token. Anyone who can reach
  `127.0.0.1:8787` **and** has the token has full control — so both must hold.
- Do not proxy or port-forward this service. If remote access is ever needed, put
  it behind an SSH tunnel, never a public bind.
