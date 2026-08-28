# Architecture

```
   Mac browser  ──HTTP + WebSocket──▶  FastAPI backend  (Kali VM, 127.0.0.1:8787)
   React SPA                             │
                                         ├─ StatusService   → lsusb / iw / nmcli / ip     (Phase 1)
                                         ├─ ModeService     → iw set type, NM handoff      (Phase 2)
                                         ├─ ScanService     → nmcli | airodump csv         (Phase 3)
                                         ├─ CaptureService  → airodump-ng -w → csv/pcap    (Phase 4)
                                         ├─ ShareService    → sysctl / iptables (NAT)      (Phase 5)
                                         ├─ HealthWatcher   → USB presence, -71 detection  (Phase 1)
                                         └─ AuditService    → gated active modules         (Phase 7)
                                         │
                                 root systemd service, localhost-bound, token-authed.
```

## Layers

- **Frontend** (`frontend/`) — React + Vite + TypeScript + Tailwind SPA. Holds no
  privilege; renders WebSocket streams and issues token-authed commands. Dev server
  on `:5173` proxies `/api` and `/ws` to the backend.
- **Backend** (`backend/app/`) — FastAPI app.
  - `config.py` — env-driven settings; loopback bind + token + mock flag.
  - `auth.py` — token dependency (HTTP) and WS handshake check.
  - `routers/` — HTTP endpoints (Phase 0: `health`).
  - `ws.py` — WebSocket endpoints (Phase 0: `echo`).
  - `services/runner.py` — the command-runner seam: real subprocess vs. mock
    fixtures, so the app runs with no hardware.

## Key decisions

- **Privilege:** one root systemd service on localhost. Simplest safe model; the
  browser never has privilege. (Alt considered: unprivileged web layer + sudoers
  allowlist — revisit if multi-user.)
- **Real-time:** one WebSocket per concern; backend pushes deltas.
- **Mock-adapter mode:** `WIFIDECK_MOCK=1` swaps hardware calls for fixtures.
- **Reuse:** early services may shell out to the `alfa-tools` `wifi-*` scripts,
  then migrate to native, structured calls.

See [PLAN.md](PLAN.md) for the full phased roadmap and acceptance gates.
