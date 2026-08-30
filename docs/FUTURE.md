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

## Track E — WPA3 & deep packet analysis

> Context: a full sourced literature review of WPA3/SAE attacks (2026) informs
> this track. Bottom line: a correctly-configured **WPA3-SAE** network (Hash-to-
> Element, PMF on, no transition mode, patched, strong passphrase) has **no known
> offline crack** — capturing the handshake yields nothing to grind against.
> Everything practical attacks a *fallback* or a *misconfiguration*, not the crypto.
> So this track is deliberately **not** "crack SAE" (that doesn't exist) — it's
> transition-mode downgrade + posture awareness.

> Shipped already: the **security-mode readout** in the Target bar (v2.6) flags
> `OPEN` / `WEP` / `WPA2` / `WPA3-TRANSITION` / `WPA3 (SAE)` / enterprise, with a
> one-line "why" — so you can see at a glance which networks are even attackable.
> That's the first, defensive half of Phase 27 below.

### Phase 26 · WPA3 transition-mode downgrade capture  — *L · offensive (gated)*
The **one practical offline path** to a "WPA3" password. When an SSID runs WPA3 +
WPA2 on the same passphrase (transition mode, very common), stand up a rogue
**WPA2-only AP** (`hostapd`) with the same SSID/BSSID; a client that connects hands
over the first EAPOL frames of a **WPA2** handshake → feed the existing crack
pipeline (aircrack / Phase-14 hashcat). You're cracking the WPA2 fallback, not SAE.
- **Gating:** same scope+authorization+audit as all offensive modules; loud "this
  transmits a rogue AP" confirmation.
- **Hardware caveat:** needs **AP mode** (master) on the adapter — the `rtw88_8812au`
  driver may not support it; verify with `iw list` (look for "AP" under supported
  interface modes) before building. May require the `8812au` DKMS driver.
- **Defeated by:** the target using WPA3-only or *Transition Disable* — which is
  exactly the finding to report on a hardened network.

### Phase 27 · WPA3 / SAE posture & recon  — *S–M · defensive/recon (half shipped)*
Grow the shipped security-readout into a full posture check per network:
- confirm **PMF** required vs. capable; detect **transition mode** (SAE+PSK both
  advertised); flag whether **H2E** is actually negotiated (support ≠ use on
  2.4/5 GHz — it's guaranteed only on 6 GHz);
- **Dragonblood exposure hint** from firmware age / hunting-and-pecking negotiation
  (CVE-2019-9494 / -13377 — closed on patched stacks);
- a per-network "attackability" verdict: offline path? online-only? none?
- **Not on the roadmap:** offline SAE cracking — no published method, tool, or CVE
  exists as of 2026, so we won't pretend to ship one.

### Phase 28 · Wireshark / tshark deep packet analysis  — *M · recon/quality*
Today we use `tshark` for exactly one thing (deauth-flood counting in WIDS). Put
Wireshark's engine to real work on captures:
- **Handshake verification** — before cracking, run `tshark` on the pcap to confirm
  a *complete* 4-way handshake (all 4 EAPOL messages present) or a valid **PMKID**,
  and show which EAPOL messages (M1–M4) were caught. Stops you wasting a crack run
  on a partial capture. (Right now "handshake ✓" comes from airodump's heuristic;
  this verifies it independently.)
- **Capture summary** — post-capture `tshark` rollup: APs, stations, EAPOL count,
  beacons, data frames, encryption seen.
- **Live packet view** — a lightweight streaming packet list during capture
  (`tshark -T fields`), read-only, in the UI.
- **"Open in Wireshark"** — the pcap download already exists; add a hint/command to
  open the `.cap` in the full Wireshark GUI for manual deep-dives.

---

## Suggested ordering

If/when you resume, a sensible sequence:
1. **13 (multi-adapter)** — biggest day-to-day quality-of-life win, and it grants
   simultaneous managed+monitor.
2. **20 (SQLite history)** — foundation the reporting/scheduling phases build on.
3. **14 (hashcat)** + **15 (PMKID)** — round out the offensive pipeline.
4. **28 (Wireshark/tshark)** — cheap, high-value: verify handshakes before cracking
   and see what you actually captured. Good next step after using the current flow.
5. **27 (WPA3 posture)** — small, builds on the shipped security readout.
6. **18 + 19 (defense++ / alerting)** — grow the WIDS.
7. **26 (WPA3 downgrade)** — only if your adapter supports AP mode (check `iw list`).
8. **22 (reporting)**, **24 (packaging)**, **25 (E2E)** — product polish.

Reorder freely — this is for your review, not a commitment. All offensive phases
inherit the existing Phase-7 guardrails (scope allowlist + explicit authorization
+ audit); all networked/remote phases must preserve the loopback-only,
token-authed default.
