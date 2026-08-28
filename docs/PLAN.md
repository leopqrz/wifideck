# WiFiDeck — Master Build Plan

> **Codename:** WiFiDeck *(placeholder — see naming ideas at the end)*
> A local, web-based command center for the ALFA AWUS036ACH (RTL8812AU) and
> similar adapters: one place to see adapter state, flip MANAGED⇆MONITOR, scan,
> capture, share internet to the host, and — later, gated — run authorized audits.
>
> **This document is the source of truth.** Each phase has an explicit
> **Acceptance Test** gate. We do not start a phase until the previous phase
> passes its gate, and we update docs on every completion.

---

## 1. Vision & principles

**Vision:** "A control panel for your Wi-Fi adapter." Open a browser on the Mac,
see the ALFA's live state, and drive everything with clicks — seeing results as
tables and charts, not terminal scrollback.

**Principles**

1. **Local-only & safe.** Backend binds to `127.0.0.1` only; token-authed; never
   exposed to the network. Nothing outbound.
2. **Reuse proven logic.** The `alfa-tools` `wifi-*` scripts already encode the
   correct `iw`/`nmcli`/`iptables` sequences. The backend starts by wrapping them,
   then migrates to native, structured calls.
3. **Live.** State, scans, and captures stream over WebSocket. No manual refresh.
4. **Honest state.** The UI always shows the *real* adapter/mode/health, including
   failure conditions (USB drop / `-71` errors we hit in testing).
5. **Testable per phase.** Every phase ships with automated tests and a manual
   acceptance checklist. Green gate = phase done.
6. **Authorization-gated action.** Anything that transmits (deauth, evil-twin) is
   off by default and hard-gated behind explicit, scoped authorization.
7. **Documented as we go.** Each phase updates `docs/` — no undocumented features.

---

## 2. Architecture

```
   Mac browser  ──HTTP + WebSocket──▶  FastAPI backend  (Kali VM, 127.0.0.1:8787)
   React SPA                             │
                                         ├─ StatusService   → lsusb / iw / nmcli / ip
                                         ├─ ModeService     → iw set type, NM handoff
                                         ├─ ScanService     → nmcli (managed) | airodump csv (monitor)
                                         ├─ CaptureService  → airodump-ng -w → CSV/pcap parse
                                         ├─ ShareService    → sysctl / iptables (NAT)
                                         ├─ HealthWatcher   → USB presence, -71 detection
                                         └─ AuditService    → (Phase 7) gated active modules
                                         │
                                 runs as a root systemd service, localhost-bound,
                                 token-authed; privileged ops isolated here.
```

**Privilege model:** a single root **systemd** service bound to localhost. Simplest
safe option for a personal tool. (Alternative considered: unprivileged web layer +
sudoers allowlist for exact commands — more moving parts; revisit if we ever
multi-user.)

**Real-time model:** one WebSocket per concern (`/ws/status`, `/ws/scan`,
`/ws/capture`). Backend pushes deltas; frontend keeps a normalized store.

---

## 3. Technology decisions

| Layer | Choice | Rationale |
|---|---|---|
| Backend | **Python 3.11 + FastAPI + uvicorn** | Async, first-class WebSockets, trivial `subprocess`, native to Kali/security tooling |
| Data models | **Pydantic v2** | Validated, typed API contracts shared with the frontend via generated types |
| Sniffing | **airodump-ng CSV** first → **scapy** later; **Kismet API** optional engine | CSV is the fastest path to live results; scapy for custom logic |
| Frontend | **React 18 + Vite + TypeScript + Tailwind** | Fast HMR, strict typing, rich live tables/charts, extensible |
| Tables | **TanStack Table + TanStack Virtual** | Handles 500+ networks/clients smoothly (virtualized) |
| Charts | **Recharts** (+ custom SVG for the spectrum view) | Signal-over-time and channel-occupancy visuals |
| State/data | **TanStack Query + Zustand** | Server cache + light client store; clean WS integration |
| Styling | **Tailwind + CSS variables**, dark command-center theme | The "CIA tool" look: dark, dense, monospace accents, precise |
| Tests | **pytest** (backend), **Playwright** (E2E), **Vitest** (frontend units) | Per-phase gates; fixtures from recorded tool output |
| Packaging | **install.sh + systemd unit** (+ Makefile) | Native run; USB/monitor in Docker is unreliable |

**Why not htmx/server-rendered?** Fine for a tiny MVP, but the live tables, charts,
multi-stream WebSockets, and the polished command-center feel are exactly where a
typed SPA pays off. We optimize for the finished, robust tool.

**Design language (the "command-center" look):** near-black background, a single
accent (amber or cyan) for live/active state, semantic status colors
(green=managed/ok, amber=monitor/attention, red=error/transmit), monospace for
BSSIDs/channels/counters, tight grid, signal shown as bars + sparklines. Defined
once as design tokens in Phase 0 and reused everywhere.

---

## 4. Cross-cutting concerns (apply to every phase)

- **Mock-adapter mode.** A backend flag that feeds recorded `iw`/`nmcli`/airodump
  fixtures instead of real hardware, so the UI and most tests run with no ALFA
  attached (and survive the USB-drop problem). Built in Phase 0, used throughout.
- **Testing strategy.** Backend: pytest against services with recorded fixtures +
  a fake command runner. Frontend: Vitest for components/stores. E2E: Playwright
  drives the real UI against the mock-adapter backend. Each phase adds tests; the
  gate is "all green + manual checklist done."
- **Documentation standard.** Every phase updates: `README` (how to run new bits),
  `docs/API.md` (endpoints), `docs/DATA-MODELS.md`, and a short `docs/phases/NN-*.md`
  recording what shipped and how it was verified.
- **Git flow.** One branch per phase (`phase/NN-slug`), PR with the acceptance
  checklist filled in, tag `vNN` on merge.
- **Security baseline (enforced from Phase 0).** Localhost bind verified in tests;
  token auth on every route + WS; no secrets in logs; audit log for active actions
  (Phase 7). A `docs/SECURITY.md` checklist is re-run at Phase 8.

---

## 5. Phased roadmap

Each phase: **Goal → Build → Acceptance Test (the gate) → Docs.**

### Phase 0 — Foundation & scaffolding
- **Goal:** the skeleton runs end-to-end with nothing real yet.
- **Build:** repo layout; FastAPI app + `GET /api/health`; root systemd unit bound
  to `127.0.0.1:8787`; token auth middleware; one WebSocket echo; React+Vite+TS+
  Tailwind scaffold with the design tokens + a status shell; **mock-adapter mode**;
  CI (lint + unit tests).
- **Acceptance Test (gate):**
  - `curl 127.0.0.1:8787/api/health` → `200` JSON with version; **401 without token**.
  - `ss -ltnp` shows the service bound to `127.0.0.1` only (not `0.0.0.0`).
  - Browser loads the SPA, opens the WS, shows "connected."
  - `pytest` + `vitest` green; linters clean.
- **Docs:** `README` (run/dev), `docs/ARCHITECTURE.md`, `docs/API.md` (stub), `docs/SECURITY.md` (baseline).

### Phase 1 — Live status & adapter health
- **Goal:** the dashboard shows the real adapter, live.
- **Build:** `StatusService` (present via `lsusb -d 0bda:8812`, driver, mode, IP,
  link/signal/bitrate from `iw dev … link`); `HealthWatcher` (USB presence + `-71`
  / disconnect detection from kernel log); `/api/status` + `/ws/status` (push on
  change); status panel + **adapter-health banner** in the UI.
- **Acceptance Test (gate):**
  - `/api/status` matches `wifi-status` for present/driver/mode/ip on real hardware.
  - Detach the ALFA in Fusion → UI flips to "disconnected" within ~2s; re-attach → recovers.
  - Associated: signal + negotiated bitrate + SSID shown.
  - Parser unit tests pass against recorded `iw`/`lsusb` fixtures.
- **Docs:** `docs/DATA-MODELS.md` (Status), health-state diagram, `docs/phases/01-status.md`.

### Phase 2 — Mode control (MANAGED ⇆ MONITOR)
- **Goal:** one-click, safe mode switching with channel selection.
- **Build:** `ModeService` (NM handoff, `airmon-ng check kill`, `iw set type`,
  optional channel); a **state machine** (idle→switching→idle) that rejects
  concurrent requests; `POST /api/mode`; UI toggle + channel picker; UI confirms
  from the status stream (not optimistic guesses).
- **Acceptance Test (gate):**
  - Click → MONITOR: `iw dev` shows `type monitor` + channel; UI reflects ≤2s.
  - Click → MANAGED: reconnects to a known network; **`ping -c3 1.1.1.1` succeeds**.
  - Duplicate/rapid clicks don't corrupt state (machine rejects mid-transition).
  - No adapter → clean, surfaced error (no hang).
- **Docs:** mode state-machine diagram, `docs/API.md` (mode), `docs/phases/02-mode.md`.

### Phase 3 — Scanning
- **Goal:** a live, sortable networks table.
- **Build:** `ScanService` unifying two sources into one `Network` model —
  managed: `nmcli … device wifi list`; monitor: airodump CSV tail; fields:
  ssid, bssid, channel, band, signal, security, client-count, first/last-seen,
  in-use. `/ws/scan` streams deltas; virtualized table with sort/filter, signal
  bars, security badges, band filter, `*` in-use marker.
- **Acceptance Test (gate):**
  - Managed: table SSIDs/count match `nmcli device wifi list`.
  - Monitor: APs appear from airodump; entries update live; stale rows age out.
  - Sort + filter correct; **500 synthetic rows scroll at 60fps** (virtualization).
  - CSV/nmcli parser unit tests pass on fixtures.
- **Docs:** `Network` model, scan-source notes, `docs/phases/03-scan.md`.

### Phase 4 — Capture & results
- **Goal:** capture traffic, see results live, export pcap.
- **Build:** `CaptureService` (`airodump-ng --output-format csv,pcap -w`), targeted
  capture (lock channel/BSSID), live **AP→client association** view, handshake /
  PMKID detection indicator, session management (start/stop/list), pcap download
  endpoint.
- **Acceptance Test (gate):**
  - Start capture → clients show associated to APs live.
  - Reconnect a device on **your own** AP → handshake indicator lights.
  - Downloaded `.pcap` opens in Wireshark with real frames.
  - Stop is clean; session files retained; parser tests pass.
- **Docs:** capture workflow, handshake-detection method, legal note, `docs/phases/04-capture.md`.

### Phase 5 — Internet sharing to the host
- **Goal:** share the ALFA's internet to macOS from the UI.
- **Build:** `ShareService` (reuse `wifi-share` logic: `ip_forward`, MASQUERADE,
  low-metric default via ALFA); live sharing status + VM Mac-facing IP; UI toggle;
  **rendered macOS route/DNS commands with copy buttons**; the split-route caveat
  shown inline; optional throughput indicator.
- **Acceptance Test (gate):**
  - Toggle on → `iptables`/`ip_forward`/default-route correct; after running the
    shown commands **on the Mac, the Mac reaches the internet** via the ALFA.
  - Toggle off → rules removed, forwarding disabled; Mac reverts.
  - UI shows correct IP + copyable commands.
- **Docs:** sharing topology, macOS steps, teardown, `docs/phases/05-share.md`.

### Phase 6 — Visualization & polish (the command-center UX)
- **Goal:** make it powerful *and* beautiful; add insight.
- **Build:** signal-over-time sparkline/chart per selected AP; **channel-occupancy /
  spectrum graph** for 2.4 + 5 GHz; finalized dark theme + keyboard shortcuts;
  desktop notification on adapter drop; **driver panel** (one-click morrownr
  `88XXau` DKMS build/install + active-driver status); settings (interface,
  refresh rates, mock mode).
- **Acceptance Test (gate):**
  - Channel graph reflects real scan distribution; signal chart updates live.
  - Driver-install button builds & loads `88XXau`; status shows the change.
  - Dashboard stays responsive under all live streams (perf budget met).
- **Docs:** `docs/DESIGN.md` (tokens/components), viz explanations, `docs/phases/06-polish.md`.

### Phase 7 — Audit / attack modules *(gated, advanced)*
- **Goal:** the "most complete" part — authorized wireless audits.
- **Build:** deauth (`aireplay-ng`), handshake-capture workflow, PMKID
  (`hcxdumptool`), optional WPS, and evil-twin / rogue-AP (`hostapd`). Each module:
  **off by default** via config flag; hard-gated behind an explicit "I am authorized
  on this target" confirmation + a **scope allowlist** of permitted BSSIDs; every
  active action written to an **audit log**; prominent legal/ethics warnings.
- **Acceptance Test (gate):**
  - Each module works against **your own lab AP** and **refuses** without the
    authorization confirmation + in-scope target.
  - Audit log records every transmit action (time, module, target).
  - Global feature flag off → modules hidden and blocked at the API.
- **Docs:** `docs/AUTHORIZATION.md`, per-module docs, `docs/ETHICS-LEGAL.md`, lab-setup guide.

### Phase 8 — Packaging, hardening & release
- **Goal:** anyone can install it fast; it's robust and fully documented.
- **Build:** `install.sh` + systemd + polkit/sudoers; versioned releases + upgrade
  path; session export/backup; full docs pass; local error logging; coverage targets.
- **Acceptance Test (gate):**
  - Fresh VM: `install.sh` → service up → **dashboard reachable from the Mac in <5 min**.
  - Reboot → service auto-starts, adapter auto-detected.
  - `docs/SECURITY.md` checklist re-run and passes (localhost bind, authz, no
    secret leakage, audit log intact).
- **Docs:** install guide, `docs/SECURITY.md` (final), troubleshooting, user manual.

---

## 6. Milestone summary

| Phase | Outcome | Gate headline |
|---|---|---|
| 0 | Skeleton runs, localhost-only, mock mode | health 200 + 401 without token + bound to 127.0.0.1 |
| 1 | Live adapter status + health | UI matches `wifi-status`; drop detected ≤2s |
| 2 | MANAGED⇆MONITOR toggle | mode flips ≤2s; managed restores internet |
| 3 | Live network scan | matches `nmcli`; 500 rows @60fps |
| 4 | Capture + pcap | handshake lights on own AP; pcap opens in Wireshark |
| 5 | Internet sharing | Mac reaches internet via ALFA |
| 6 | Charts + driver panel + theme | spectrum/signal live; 88XXau install works |
| 7 | Gated audit suite | works in lab; refuses out-of-scope; audit-logged |
| 8 | Installable release | fresh VM → dashboard <5 min; security checklist passes |

**MVP = Phases 0–3** (status + mode + scan): the daily-useful core.
**v1 = Phases 0–6.** **v2 = + Phase 7.** **Release = Phase 8.**

---

## 7. Appendix

### 7.1 Proposed repo layout
```
wifideck/
  backend/
    app/
      main.py
      auth.py
      ws.py
      routers/     status.py mode.py scan.py capture.py share.py audit.py
      services/    status.py mode.py scan.py capture.py share.py health.py runner.py
      models/      network.py status.py session.py
    tests/         fixtures/  test_*.py
    systemd/       wifideck.service
  frontend/
    src/  components/ pages/ hooks/ store/ theme/ api/
    vite.config.ts
  scripts/         (existing alfa-tools wifi-* — reused by the backend early on)
  docs/            PLAN.md ARCHITECTURE.md API.md DATA-MODELS.md DESIGN.md
                   SECURITY.md AUTHORIZATION.md ETHICS-LEGAL.md phases/NN-*.md
  install.sh  Makefile  README.md
```

### 7.2 Core data model (draft)
```
Network   { bssid, ssid, band, channel, signal_dbm, signal_pct,
            security[], is_current, clients, first_seen, last_seen }
Client    { mac, bssid, signal_dbm, packets, last_seen }
Status    { usb_present, driver, interface, mode, operstate,
            ssid?, ip4?, signal_dbm?, tx_bitrate?, health }
Session   { id, started, mode, channel?, target_bssid?, files[], handshake_captured }
```

### 7.3 Prior art (reuse vs. build)
- **Kismet** — reuse as an optional capture engine (REST + WS API); don't reinvent sniffing.
- **aircrack-ng suite** — the actual capture/attack primitives we shell out to.
- **airgeddon / wifite2** — reference for attack workflows (Phase 7).
- **WiFi Pineapple UI** — UX inspiration for the dashboard.
- The novel part is the **unified, friendly, live adapter-control dashboard** — that doesn't exist as a polished web tool.

### 7.4 Naming ideas
WiFiDeck · AlfaControl · Beacon · Nighthawk · Halo · Spectre · Skywave.
(Working name **WiFiDeck** until you pick one.)
```
