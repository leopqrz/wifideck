# WiFiDeck — Future roadmap (post-v2.4)

Phases 0–12 are complete (v2.4). This doc collects candidate future phases to
review **after** you've used/tested everything that exists. Nothing here is built
yet — it's a menu. Each phase notes its value, rough effort, and whether it's
offensive / defensive / platform / quality, plus any gating it should carry.

Effort key: **S** ≈ a session, **M** ≈ a couple sessions, **L** ≈ larger.

---

> Shipped since this doc was written: **click-to-connect** (join/leave/forget Wi-Fi
> from the Networks table) landed in **v2.5** — see `docs/phases/13-connect.md`.

## Track A — Capability (do more with the radio)

### Phase 13 · Multi-adapter support  — *M · platform*
Select among multiple wireless interfaces; per-adapter status/mode. Unlocks the
thing you originally asked for: **one adapter in MANAGED (internet) + another in
MONITOR (capture) at the same time**, no toggling. Adapter picker in the UI.

### Phase 14 · hashcat / GPU cracking  — *M · offensive (gated)*
Convert `pcap → 22000` (`hcxpcapngtool`) and crack with `hashcat -m 22000`
(rules, masks, GPU). Much faster than aircrack-ng; a cracker dropdown
(aircrack / hashcat) on the existing Crack panel. Same scope+auth gate.

### Phase 15 · PMKID (clientless) capture  — *M · offensive (gated)*
`hcxdumptool` to grab a PMKID from an AP **without deauthing clients** — faster
and less disruptive than the handshake flow. Feeds the same crack pipeline.

### Phase 16 · Client/station intelligence  — *M · recon*
Track stations over time in monitor mode: probe-request history, OUI/vendor
lookup, per-AP client lists, a presence timeline. "Who's around" view.

### Phase 17 · GPS / wardriving & mapping  — *L · recon*
Optional GPS (USB/phone), map view of APs, Kismet-style logging, KML/CSV export
for wardriving. Clearly a bigger lift; nice-to-have.

---

## Track B — Defense (grow the WIDS-lite into a real WIDS)

### Phase 18 · Defensive detections++  — *M · defensive*
Beyond evil-twin/deauth: karma/probe-response attacks, rogue-DHCP hints,
beacon-flood, WPS-brute detection, and a **known-good baseline** (your APs/clients)
so anything new is flagged. Severity tuning + per-rule enable.

### Phase 19 · Notifications & integrations  — *S–M · platform*
Webhooks + ntfy/Slack/email on WIDS alerts and watchdog recoveries; a Prometheus
`/metrics` endpoint (Grafana-friendly). Turns passive monitoring into real alerting.

---

## Track C — Platform (make it a product)

### Phase 20 · Persistence & history (SQLite)  — *M · platform*
Store scans, capture sessions, audit, and alerts in SQLite. A session/history
browser with search and a timeline across time (today it's mostly in-memory + files).

### Phase 21 · Scheduling & automation  — *M · platform*
Scheduled scans, timed capture windows, recurring WIDS sweeps, retention/cleanup
policies. A small job scheduler + a "jobs" panel.

### Phase 22 · Reporting & export  — *M · platform*
Generate an assessment report (HTML/PDF) from a time range: networks seen,
captures, cracks, WIDS alerts, and the audit trail. CSV/JSON export. Great for
authorized-engagement write-ups.

### Phase 23 · Multi-user, RBAC & safe remote access  — *L · platform/security*
Real users + roles (viewer / operator / admin), per-user audit, and a documented
safe remote path (TLS + reverse proxy, or an SSH-tunnel helper) — without ever
breaking the localhost-only default. Active modules restricted to operator+.

---

## Track D — Quality & distribution

### Phase 24 · Packaging & distribution  — *M · quality*
Docker image, a Debian `.deb`, a one-line installer, auto-update, and a Phase-8
systemd-hardening re-review. Make install a single command anywhere.

### Phase 25 · E2E tests & hardware-in-the-loop CI  — *M · quality*
Playwright end-to-end tests against the real SPA, coverage gates, and a
mock-hardware test harness so the full stack is exercised in CI (today CI runs
unit + build; hardware paths are manual).

---

## Suggested ordering

If/when you resume, a sensible sequence:
1. **13 (multi-adapter)** — biggest day-to-day quality-of-life win, and it grants
   simultaneous managed+monitor.
2. **20 (SQLite history)** — foundation the reporting/scheduling phases build on.
3. **14 (hashcat)** + **15 (PMKID)** — round out the offensive pipeline.
4. **18 + 19 (defense++ / alerting)** — grow the WIDS.
5. **22 (reporting)**, **24 (packaging)**, **25 (E2E)** — product polish.

Reorder freely — this is for your review, not a commitment. All offensive phases
inherit the existing Phase-7 guardrails (scope allowlist + explicit authorization
+ audit); all networked/remote phases must preserve the loopback-only,
token-authed default.
