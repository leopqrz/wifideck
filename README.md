# WiFiDeck

A local, web-based **command center** for USB Wi-Fi adapters (RTL8812AU,
MediaTek MT7921U / MT7612U, and similar). See live adapter state, flip
**MANAGED ⇄ MONITOR**, scan, capture handshakes/PMKIDs, verify and crack them,
share internet to the host, watch signal/throughput charts, and run
authorization-gated active tests — all from a fast, dark, live dashboard in your
browser. Binds to `127.0.0.1` only, token-authed.

**Status:** phases 0–13 shipped (v2.5); since then the offensive pipeline was
modernized — **hashcat mode 22000**, **PMKID clientless capture**, **tshark
handshake verification**, **SQLite history**, and **WPA3 / security posture** —
all validated in mock + live recon. Live RF **capture needs a monitor-capable
radio** (see [docs/HARDWARE.md](docs/HARDWARE.md)); the current RTL8812AU/`rtw88`
does MANAGED only. Plan: [docs/PLAN.md](docs/PLAN.md) · progress:
[docs/BUILD-LOG.md](docs/BUILD-LOG.md).

> 📖 **New here?** Read the **[User Guide](docs/USER-GUIDE.md)** — every function
> explained, how to test it and what to expect, a deep take on **monitor mode**,
> and curated learning resources (books, videos, sites).

![WiFiDeck dashboard](docs/screenshot.png)

## Features

| | |
|---|---|
| **Status** | live USB/driver/mode/link/signal + health (disconnect & `-71` detection) |
| **Mode** | MANAGED ⇄ MONITOR toggle with a serialized state machine |
| **Scan** | live network table (nmcli in managed, airodump in monitor), sort/filter |
| **Posture** | flags each network **WPA2 / WPA3 / WPA3-transition / open** and what it means for capture |
| **Connect** | click any SSID to join/leave; NetworkManager saves the password |
| **Target** | pick the network once — shared by deauth + guided capture |
| **Capture** | airodump **handshake** *or* **PMKID clientless (hcxdumptool)** sessions, detection, pcap export |
| **Verify** | tshark confirms a real 4-way handshake (M1–M4) or PMKID before you waste a crack |
| **Cracking** | **aircrack-ng or hashcat (mode 22000)** vs a wordlist, scope-gated, live progress |
| **History** | past capture sessions + crack outcomes persisted to **SQLite**, survive restarts |
| **Share** | NAT the uplink to the host, with copyable macOS route/DNS commands |
| **Charts** | signal & TX-rate sparklines; driver/DKMS panel with switch hints |
| **Active** | deauth — off by default; pick a network, confirm once, every action audited |
| **Watchdog** | auto-recover the `-71` USB drops (driver reload → USB reset → reconnect) |
| **Guided flow** | one gated workflow: monitor → capture → deauth → handshake → export |
| **Defense** | WIDS-lite — evil-twin + deauth-flood detection with an alerts timeline |

## Quick start

**Click to launch** — one clickable app that starts the backend + frontend and
opens the dashboard (works the same on macOS and Linux; it detects the OS and
picks the right RF backend automatically). Run the one-time installer, then
double-click:

```bash
./scripts/install-launchers.sh
#   macOS → WiFiDeck.app in ~/Applications (Spotlight / Launchpad / drag to Dock)
#           the in-repo WiFiDeck.app is also double-clickable directly
#   Linux → “WiFiDeck” in your app menu + a Desktop icon
```

A window opens with the servers' logs; close it (or Ctrl+C) to stop both.

Prefer the terminal? — one command does the same (Ctrl+C stops both). If the
Linux systemd service is running it just opens it:

```bash
./wifideck                 # http://localhost:5173  (view/scan/connect work as your user)
WIFIDECK_SUDO=1 ./wifideck # backend as root — needed for mode-switch / capture / deauth / sharing
WIFIDECK_MOCK=1 ./wifideck # no adapter needed (fixtures; UI shows a MOCK DATA badge)

# enable the offensive modules (deauth + guided capture) — your OWN networks only.
# Pick a network from the scan and confirm once per deauth; every action is audited:
WIFIDECK_SUDO=1 WIFIDECK_ENABLE_ACTIVE=1 ./wifideck
```

Or run the pieces yourself:

```bash
# backend (real hardware needs root for mode/capture/share)
cd backend && python3 -m venv .venv && . .venv/bin/activate && pip install -r requirements.txt
WIFIDECK_TOKEN=dev-token-change-me PYTHONPATH=. uvicorn app.main:app --host 127.0.0.1 --port 8787

# frontend (needs Node 18+; nvm recommended)
cd frontend && npm install && npm run dev      # http://127.0.0.1:5173  (proxies /api + /ws)
```

## Install as a service (production)

```bash
cd frontend && npm run build          # build the SPA first (needs Node)
cd .. && sudo ./install.sh            # venv + deps + systemd service on 127.0.0.1:8787
```

The installer generates a random token in `/opt/wifideck/backend/.env` and prints
it — open `http://127.0.0.1:8787` and paste it once (stored in your browser).
Manage with `systemctl {status,stop,restart} wifideck` and `journalctl -u wifideck -f`.

## Security

Localhost-only, token on every route + WebSocket, constant-time compare. **Active
(transmit) modules are off by default** (`WIFIDECK_ENABLE_ACTIVE=1` to arm) and
gated by an in-scope BSSID allowlist + per-action authorization, with every attempt
audited. Use active features only on networks you own or are authorized to test.
Full model + the release checklist: [docs/SECURITY.md](docs/SECURITY.md). Re-run it
with `python3 scripts/security_check.py`.

## Tests

```bash
cd backend && PYTHONPATH=. pytest -q        # 116 tests
cd frontend && npm run test && npm run lint # 48 tests
python3 scripts/security_check.py           # 6 security invariants
```

## Docs

- [docs/OFFENSIVE.md](docs/OFFENSIVE.md) — **how to use deauth / guided capture / cracking**, with expected results
- [docs/HARDWARE.md](docs/HARDWARE.md) — **radio buying & setup** (what to buy for real capture, and why)
- [docs/ADR-001-adapter-swap.md](docs/ADR-001-adapter-swap.md) — **why the RTL8812AU is being replaced** (decision record)
- [docs/BUILD-LOG.md](docs/BUILD-LOG.md) — live roadmap/progress tracker
- [docs/PLAN.md](docs/PLAN.md) — the full phased plan · [docs/FUTURE.md](docs/FUTURE.md) — candidate future phases
- [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) · [docs/API.md](docs/API.md) · [docs/SECURITY.md](docs/SECURITY.md)
- [docs/phases/](docs/phases/) — per-phase build notes + acceptance results
- [`./wifideck`](wifideck) — launcher · [scripts/security_check.py](scripts/security_check.py) — security re-review
  · [scripts/fix-8812au-driver.sh](scripts/fix-8812au-driver.sh) — (optional) RTL8812AU driver-build attempt

## License

MIT — see [LICENSE](LICENSE).
