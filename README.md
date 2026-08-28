# WiFiDeck

A local, web-based **command center** for the ALFA AWUS036ACH (RTL8812AU) and
similar adapters. See adapter state, flip **MANAGED ⇄ MONITOR**, scan, capture,
share internet to the host — and (later, authorization-gated) run audits — from a
fast, dark, live dashboard in your browser.

> Status: **planning**. The full, phased, testable build plan is the source of
> truth: **[docs/PLAN.md](docs/PLAN.md)**.

## Why

The correct `iw` / `nmcli` / `iptables` / `airodump-ng` sequences are already
captured as CLI scripts in `../alfa-tools`. WiFiDeck wraps that proven logic in a
friendly, live web UI so you don't have to memorize commands — and shows results
as tables and charts instead of scrollback.

## Principles

- **Local-only & safe** — binds to `127.0.0.1`, token-authed, never exposed.
- **Reuse proven logic** — starts by wrapping the `alfa-tools` scripts.
- **Live** — status/scan/capture stream over WebSocket.
- **Testable per phase** — every phase has an automated + manual acceptance gate.
- **Authorization-gated** — transmit/attack features are off by default and scoped.

## Stack

Python + FastAPI backend (root systemd service, localhost) · React + Vite +
TypeScript + Tailwind frontend · WebSocket live streams · pytest / Vitest /
Playwright tests. Rationale in [docs/PLAN.md](docs/PLAN.md#3-technology-decisions).

## Roadmap at a glance

| Phase | Outcome |
|---|---|
| 0 | Skeleton, localhost-only, mock-adapter mode |
| 1 | Live adapter status + health |
| 2 | MANAGED⇄MONITOR toggle |
| 3 | Live network scan  ← **MVP** |
| 4 | Capture + pcap export |
| 5 | Internet sharing to macOS |
| 6 | Charts, driver panel, command-center theme  ← **v1** |
| 7 | Gated audit/attack modules  ← **v2** |
| 8 | Installable, hardened release |

See **[docs/PLAN.md](docs/PLAN.md)** for each phase's build steps, acceptance
tests, and documentation deliverables.
