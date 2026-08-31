# WiFiDeck — Build log & roadmap tracker

Living tracker for the "modernize everything" build. We go **one phase at a time:
develop → test → commit → next.** Unblocked phases first; blocked ones wait on the
upgrades listed below.

_Last updated: 2026-08-30._

## Available resources

| Resource | Use |
|---|---|
| **Mac M4 Pro Max, 64 GB** | dev host; **hashcat GPU cracking** (Apple Silicon Metal), model training/inference |
| **Jetson Orin Nano 8 GB** | edge **ML inference** (device fingerprinting / anomaly WIDS), always-on sensor node |
| **AWS** | heavier model training, GPU crack bursts, wordlist/rule storage |
| **ALFA AWUS036ACH (RTL8812AU, `rtw88`)** | current radio — MANAGED scan OK; **monitor RX + inject CONFIRMED DEAD** (2026-08-30: 0 beacons in 36s hopping; `aireplay --test` found 0 APs); **no AP mode** |
| Willing to invest | new radios, GPS, more compute as phases need them |

## Status legend

✅ done · 🔨 in progress · ⬜ todo (unblocked) · ⛔ blocked (needs upgrade) · 🧪 built, needs hardware to validate

## Phase status

| # | Phase | Status | Hardware / upgrade needed |
|---|---|---|---|
| 0–13 | core through click-to-connect | ✅ | — (shipped, v2.5) |
| — | security-mode readout (part of 27) | ✅ | — (shipped, v2.6) |
| **28** | **tshark handshake verification** | ✅ | none — CPU/tshark only |
| 14 | hashcat mode 22000 cracking | ✅ | built; **GPU (M4 Metal / AWS)** + `hashcat`/`hcxtools` to run |
| 15 | PMKID clientless capture (hcxdumptool) | 🧪 | built; **live capture needs working monitor + hcxdumptool** |
| 20 | SQLite persistence & history | ✅ | none |
| 27 | WPA3 / SAE posture & recon | ✅ | none (software) |
| 22 | reporting & export (HTML/PDF) | ✅ | none |
| 16 | client/station intelligence | 🧪 | built + mock demo; live data needs monitor |
| 18 | defensive detections++ | 🧪 | detections need monitor; rules/UI unblocked |
| 19 | notifications & integrations | ✅ | none (webhooks/ntfy/Prometheus) |
| 21 | scheduling & automation | ⬜ | none |
| 24 | packaging & distribution | ⬜ | none |
| 25 | E2E tests & mock-hardware CI | ⬜ | none |
| 23 | multi-user / RBAC | ⬜ | none (software) |
| **29** | **ML: device fingerprinting + anomaly WIDS** (new) | ⬜ | **Jetson / AWS** for training + edge inference |
| 13 | multi-adapter support | ⛔ | **2nd Wi-Fi adapter** |
| 26 | WPA3 transition-mode downgrade | ⛔ | **AP-mode-capable adapter** (see upgrades) |
| 17 | GPS / wardriving | ⛔ | **GPS dongle** (or phone GPS bridge) |

## Upgrades we'll likely want (my recommendations)

1. **A modern radio that actually injects + does AP mode** — the single biggest
   unlock. The `rtw88`/RTL8812AU is the bottleneck behind half the offensive phases.
   Best 2026 pick: a **MediaTek MT7921U / MT7925**-based adapter (e.g. ALFA
   **AWUS036AXML**, Wi-Fi 6/6E) — excellent in-kernel `mt76` monitor + injection +
   AP mode, and it can see **WPA3 / 6 GHz** networks the 8812au can't. Unblocks 13,
   26, reliable 14/15/16/18. _(Alternatively fix the 8812au DKMS driver for kernel
   7.1, but a new radio is more reliable and future-proof.)_
2. **GPS dongle** (any u-blox USB) — unblocks 17 (wardriving/mapping).
3. **Compute is covered — but mind *where* hashcat runs.** The backend lives in the
   **Kali ARM VM**, which has **no GPU** — so hashcat there is CPU-only. To use the
   **M4 Metal GPU** or an AWS GPU, run hashcat on the host/cloud and feed it the
   `.22000` file (Phase 14 already produces the portable format). A small **"offload
   crack" phase** (ship the 22000 to a remote hashcat + poll) would unlock full GPU
   speed — worth adding. Jetson handles edge ML; AWS covers training/bursts.
   To use the hashcat engine now, install on the VM: `sudo apt install hashcat hcxtools`.

## Where AI/ML genuinely helps (Phase 29, new)

Not bolted-on hype — real, modern uses:
- **Device fingerprinting** — classify vendor/OS/device-type from probe requests,
  MAC-randomization patterns, and IE fingerprints (the "who's around" view, smarter).
- **Anomaly-based WIDS** — learn your environment's baseline and flag deviations
  (evil-twin, karma, new rogue) instead of only fixed-threshold rules.
- **Edge inference on the Jetson Orin Nano** — run the models on the sensor node,
  train on AWS, ship the weights. Modern, and it's exactly what the Jetson is for.

## Real-capture verdict (2026-08-30)

Tested the current adapter directly: `sudo airodump-ng wlan0` → **0 beacons / 0 APs**
in 36s (channel-hopping worked, RX did not); `sudo aireplay-ng --test wlan0` →
**Found 0 APs**. Conclusion: **RTL8812AU + rtw88 cannot do monitor capture or
injection** — not fixable in software. Everything above the radio layer is
validated (mock + live recon + full pipeline execution). **Real capture (Tier 3)
is blocked until a capable radio.** Recommended: ALFA **AWUS036AXML** (MT7921U,
in-kernel `mt76`) — monitor + inject + AP mode + WPA3/6 GHz. Software-only phases
continue in the meantime.

## Running log

- **2026-08-30** — Kicked off the full build. Set order: **28 → 20 → 14 → 15 → 27 →
  22 → 16 → 19 → 18 → 21 → 24 → 25 → 23 → 29**, then the ⛔ hardware phases once the
  radio/GPS land. Started **Phase 28 (tshark handshake verification)**.
- **2026-08-30** — ✅ **Phase 28 done.** `HandshakeVerifier` service + `parse_eapol`
  classifier (M1–M4 from the EAPOL Key-Info bits, PMKID heuristic), `GET
  /api/capture/{sid}/handshake`, and a `tshark:` badge in the Crack panel showing
  `M1 M2 M3 M4 / PMKID / crackable?` for the selected capture. 7 backend + 47
  frontend tests.
- **2026-08-30** — ✅ **Phase 14 done.** hashcat **mode 22000** engine alongside
  aircrack: `hcxpcapngtool` converts pcap → 22000 (PMKID + EAPOL), `hashcat -m 22000`
  with `--status-json` progress parsing (`parse_hashcat_status`), key read from the
  outfile. `engine` on the crack API/model + an **aircrack / hashcat** toggle in the
  panel. 106 backend + 47 frontend tests.
- **2026-08-30** — 🧪 **Phase 15 done (build).** PMKID **clientless** capture: capture
  gains a `mode` (handshake | pmkid); pmkid runs **hcxdumptool** → `.pcapng` (no
  deauth). `mode` on the session model/API, a **handshake / PMKID** toggle in the
  Capture panel, `pcap_path` now finds `.pcapng`, mock flags PMKID. 108 backend + 47
  frontend tests. Live capture needs a working-monitor adapter + hcxdumptool
  (`sudo apt install hcxdumptool`).
- **2026-08-30** — ✅ **Phase 20 done.** SQLite **history**: `HistoryStore` (graceful
  no-op if the DB can't open) persists capture sessions + crack outcomes; capture
  records on start/stop, crack records on finish; `GET /api/history` joins each
  session with its latest crack; a **History** panel (when · mode · target ·
  captured · crack key) that survives restarts. `WIFIDECK_DB` config + conftest.
  113 backend + 48 frontend tests.
- **2026-08-30** — ✅ **Phase 27 done.** WPA3 / security **posture**: `securityClass`
  maps a network's security to open / WPA2 / **WPA3-transition** / WPA3(-only), each
  with a tone + one-line "what it means for capture" note; shown as a chip + readout
  in the **Target** bar. (Detected the tester's own Queiroz as WPA3-transition live.)
  +5 frontend tests.
- **2026-08-30** — 🔧 **Robustness pass** (from live/mock testing): mock mode-switch
  now reflects MONITOR/MANAGED in status (toggle no longer "hangs"); scope/audit
  **degrade instead of 500** when the state dir isn't writable (root-owned
  `/tmp/wifideck` from a prior sudo run) + launcher chowns it back; crack panel
  **polls** so freshly-captured sessions appear; handshake-verify message no longer
  blames tshark for an empty pcap. 116 backend + 48 frontend tests, 6/6 invariants.
- **2026-08-30** — 🧪 **Real-hardware validation.** Mock: full capture→verify→crack→
  history loop confirmed. Live: real scan, WPA3-transition detection, mode switch,
  audit, guided-flow execution all ✅ — but **real capture empty** (adapter limit).
- **2026-08-30** — 🔬 **8812au driver-port attempt (adapter side).** Reproduced the
  aircrack `rtl88xxau` DKMS build as a user in a temp copy (no system changes) and
  fixed **four** breakages for kernel 7.1: `EXTRA_CFLAGS`→`ccflags-y`, include paths
  →`$(M)`, timer-API compat shim (`from_timer`/`del_timer_sync`), and disabling the
  bridge/PPPoE code — then hit the **cfg80211 API overhaul** (~15 wireless callbacks
  changed `net_device*`→`wireless_dev*`). **Verdict: not practical** to port to 7.1
  (multi-day, fragile, more walls behind). Options: kernel ≤6.15 ($0) or a MediaTek
  radio. Left the driver's `dkms.conf` cap for the user to restore.
- **2026-08-30** — ✅ **Hardware decision: buy ALFA AWUS036AXML (MT7921U).** Confirmed
  its driver (`mt7921u`) **and** the MT7612U driver (`mt76x2u`) already ship **in the
  running kernel** → plug-and-play, no DKMS, no version breakage. Wrote
  `docs/HARDWARE.md` (buy + setup + acceptance test) and `scripts/fix-8812au-driver.sh`
  (the attempt, safe/reversible).
- **2026-08-30** — ✅ **Phase 22 done.** Assessment **reporting**: `posture.py`
  (Python mirror of the frontend `securityClass`), a `ReportService` that aggregates
  known networks + posture, capture sessions + crack outcomes, scope, and the audit
  trail into a self-contained styled **HTML** doc (print → PDF); `GET /api/report`
  (HTML) + `/api/report/data` (JSON); a **Report** panel (Open / Download .html).
  +4 backend + 1 frontend test → 119 backend + 49 frontend, 6/6 invariants.
- **2026-08-30** — ✅ **Phase 19 done.** Notifications & integrations: `NotifyService`
  (generic **webhook** / **ntfy** / **Slack** sinks, opt-in via env, per-message
  cooldown to prevent spam) wired into WIDS alerts + watchdog recoveries;
  `GET /api/notify` (enabled sinks) + `POST /api/notify/test`; a Prometheus
  **`/metrics`** endpoint (token-gated) with up/active/session/handshake/pmkid/
  cracked/watchdog/wids gauges; an **Integrations** panel (sinks + Send test).
  +5 backend + 1 frontend test → **124 backend + 50 frontend, 6/6 invariants**.
- **2026-08-30** — 🧪 **Phase 16 done (build + mock demo).** Client/station
  **intelligence**: `parse_airodump_stations` (station section of the airodump CSV),
  OUI `vendor_for` with **randomized-MAC detection** (locally-administered bit — flags
  privacy MACs), a `StationTracker` that accumulates sightings across polls (union of
  probed SSIDs, max signal/packets), fed live from the monitor scan WS; `GET
  /api/stations` + a **Stations ("who's around")** panel (MAC · vendor · signal · AP ·
  probes · pkts). Mock returns fixture stations so it's demoable now; real data needs
  the radio. +4 backend + 1 frontend test → **128 backend + 51 frontend, 6/6
  invariants**. **Next: Phase 21 (scheduling) or 23 (RBAC).**
