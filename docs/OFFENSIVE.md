# Using the offensive modules

A hands-on guide to the three gated functions — **Deauth**, **Guided capture**,
and **Handshake cracking** — with the exact steps and the results you should
expect. For authorized testing of **your own networks** only.

> These are off by default. See [SECURITY.md](SECURITY.md) for the guardrail model
> (scope + per-action authorization + audit). The background theory (4-way
> handshake, why capture→crack works on WPA2 but not WPA3) is in the README and the
> WPA3 field note.

## Before you start

```bash
# root (for monitor/inject/capture) + active modules armed:
WIFIDECK_SUDO=1 WIFIDECK_ENABLE_ACTIVE=1 ./wifideck
```

Then in the browser:

1. Sit in **MANAGED** a moment so the network list fills (the switch to MONITOR
   snapshots it for you).
2. In the **Target** bar, pick the network you're testing **once** — it feeds
   Deauth and Guided capture, and the security badge tells you if it's even
   attackable (`WPA2` = yes; `WPA3 (SAE)` = no offline path; `WPA3-TRANSITION` =
   attack the WPA2 fallback).

> **Hardware reality check (RTL8812AU / rtw88):** the transmit steps (deauth, and
> the deauth stage of guided capture) need **frame injection**, which the in-kernel
> `rtw88_8812au` driver is unreliable at. Confirm first:
> `sudo aireplay-ng --test wlan0` (injection) and `sudo airodump-ng wlan0` (does it
> see any APs in monitor at all). If injection fails, capture can still succeed when
> a device reconnects on its own — it just won't be *triggered* by the deauth.

---

## 1 · Active modules → Deauth

**What it does:** sends spoofed **deauthentication frames** (`aireplay-ng --deauth`)
to a network, knocking its devices off the air. On its own it's a disruption tool;
in the workflow it's how you *force a reconnect* so a fresh handshake appears.

**Steps**
1. Switch to **MONITOR** (deauth transmits — it needs monitor mode). Best results
   when monitor is on the **target's channel** (set it in Mode control, or use the
   guided flow which does it for you).
2. Confirm the **Target** bar shows your network.
3. In **Deauth**, set **frames** (e.g. `5`), click **Send deauth**, confirm the prompt.

**Expected result**
- A new **audit-log** row: `deauth · <bssid> · ok`, and a `sent · …` message.
- On an injection-capable adapter: a device on that network **briefly loses Wi-Fi
  and reconnects** within a second or two.

**What "not working" looks like**
| You see | Meaning |
|---|---|
| `sent · ok` but no device ever drops | Frames aren't really being injected — `rtw88` limitation. Run `aireplay-ng --test`. |
| Button disabled / "Switch to MONITOR mode first" | You're in MANAGED — flip to MONITOR. |
| Nothing happens on a `WPA3 (SAE)` target | Expected — WPA3 mandates PMF, so deauth frames are rejected by design. |

---

## 2 · Guided capture (the whole chain)

**What it does:** runs the standard capture sequence for you on the chosen target:

```
MONITOR ──▶ CAPTURE ──▶ DEAUTH ──▶ HANDSHAKE ──▶ save .pcap
```

**Steps**
1. Pick the **Target** (channel auto-fills from it — editable).
2. In **Guided capture**, set the **deauth** count (default `8`), click **Run flow**,
   confirm.

**Expected result** — the steps light up live, in order:
- `monitor ✓` — switched to monitor on the target's channel
- `capture ✓` — `airodump-ng` is recording that BSSID
- `deauth ✓` — a burst was sent to trigger a reconnect
- `handshake ✓` — a reconnecting device's 4-way handshake was caught
- state → **done**, a **Download .pcap** button appears, `handshake ✓`

**Success:** state `done` + handshake `true` + a downloadable pcap.

**Failure modes**
| State | Meaning / what to do |
|---|---|
| `timeout` | No handshake in the window — a device has to (re)connect. Retry; make sure the network actually has an active client; or the deauth didn't inject (rtw88). |
| stalls at `capture` | airodump isn't seeing frames — monitor capture may be failing on this driver (`sudo airodump-ng wlan0` to confirm). |
| `failed` | Check the message; usually monitor-switch or a missing tool. |

> **PMKID shortcut:** on some networks the tool can grab a **PMKID** and mark the
> session crackable **without any deauth** — cleaner and quieter when it works.

---

## 3 · Handshake cracking

**What it does:** takes a captured handshake `.pcap` + a **wordlist** and runs
`aircrack-ng` **fully offline**, hashing each candidate password the way WPA2 does
and checking it against the capture. A match = the passphrase.

**Steps**
1. In **Handshake cracking**, open the **capture session** picker. Sessions with a
   green `handshake ✓` are the crackable ones; the one matching your Target is
   auto-selected.
2. Set the **wordlist** path (default `/usr/share/wordlists/rockyou.txt` — on Kali,
   `sudo gunzip /usr/share/wordlists/rockyou.txt.gz` once to unpack it).
3. Click **Crack**.

**Expected result**
- A live progress bar: **keys tested**, **rate (k/s)**, percentage.
- state **found** → the **passphrase** shown in green, if it's in the wordlist.
- state **exhausted** → wordlist ran out; the password isn't in it.

**Success:** `key found` + the passphrase.

**Notes / limits**
- Only finds passwords **present in the wordlist**. A long random passphrase won't
  be found — that's the lesson, not a bug.
- Needs a **real** handshake — verify the `handshake ✓` column (Phase 28 will let
  `tshark` confirm all 4 EAPOL messages before you spend the run).
- **WPA3-SAE cannot be cracked this way** — there's no offline attack on SAE. Only
  WPA2 handshakes (including a WPA3-**transition** network's WPA2 fallback) are
  crackable here.

---

## The chain, end to end

| Step | Tool | You get | Fails if… |
|---|---|---|---|
| Deauth | `aireplay-ng` | device kicked → reconnects | no injection (rtw88) / WPA3 PMF |
| Guided capture | `airodump-ng` + deauth | `.pcap` with a handshake | no client reconnects / no monitor capture |
| Cracking | `aircrack-ng` | the passphrase | password not in wordlist / WPA3-SAE |

Everything is written to the **audit log**. If a step silently "works" but nothing
happens on the air, suspect the driver first — the `rtw88`/RTL8812AU monitor-and-
inject limitation is the usual culprit, not the tool.
