# ADR-001 — RTL8812AU monitor/injection: fix the environment first, MediaTek later

**Status:** **Revised 2026-08-30** (supersedes the original "replace the adapter now"
decision, kept below as history) · **Owner:** leo

## Decision (TL;DR) — revised

**Do not replace the adapter yet.** Mature WiFiDeck on the hardware we already own
(ALFA AWUS036ACH / RTL8812AU) and get **real monitor-mode capture** from it. The
original conclusion — that it "cannot do monitor/injection and that can't be fixed
in software" — **was too strong and is retracted.**

- **The RTL8812AU *hardware* is capable** of managed, monitor, raw capture, and
  injection. The `phy` even advertises `monitor` + `AP` modes.
- **What actually failed** is the **kernel-7.1 / driver / environment** combination
  (`rtw88` doesn't deliver monitor RX for this chip; the `rtl88xxau` DKMS won't
  build on 7.1). That's a software/environment problem — with several unexplored
  fixes — not a dead end.

**Investigation order (simplest, most reproducible first):**

1. **Native macOS** userspace driver ([`xen-proc/rtl8812au-macos`](https://github.com/xen-proc/rtl8812au-macos))
   — libusb, no kext, no SIP change; claims hardware-verified 2.4/5 GHz monitor RX +
   injection + pcap. If it proves reliable, it could remove VMware from the RF path
   entirely (M4 → macOS → libusb → ACH → WiFiDeck). **Audit + prototype before
   trusting** (it's early-stage: ~2 commits).
2. **Current Kali 7.1** with a newer/patched upstream `rtl8812au` branch, *if* one
   compiles **and** delivers real monitor RX (not just compiles).
3. **Dedicated RF VM** pinned to a known-good kernel + `rtl8812au` — without
   downgrading the main dev VM.
4. **Only then** evaluate the **AWUS036AXML (MT7921AU)** as a *future modernization*
   (Wi-Fi 6E / in-kernel `mt76`), not a rescue for an unresolved software problem.

Full investigation plan and current environment: [RADIO-ENVIRONMENT.md](RADIO-ENVIRONMENT.md).

### Why the original conclusion was wrong

It over-generalized from a true, narrow fact ("**`rtw88` on kernel 7.1** yields no
monitor RX, and the **installed** `rtl88xxau` DKMS won't build there") to a broad,
false one ("the adapter can't do it in software"). It also predated the native-macOS
libusb option. The narrow fact and the driver-port findings below remain accurate and
useful; the *recommendation* built on them was premature.

---

## Original decision (2026-08-30) — HISTORICAL, superseded

> Buy an **ALFA AWUS036AXML** (MediaTek **MT7921AU**, `mt76` driver) for all
> capture/injection work. **Keep** the current ALFA AWUS036ACH — it still works fine
> in MANAGED mode and has better range — but it cannot do monitor capture or frame
> injection on this system. _(Retracted: see the revised decision above — the ACH
> can do monitor/injection with the right driver/environment.)_

## Context

- **Host:** Mac M4 Pro Max (64 GB), VMware Fusion → **Kali Linux ARM64 VM**.
- **Kernel:** `7.1.5+kali-arm64` (aarch64) — a very new kernel.
- **Adapter:** ALFA **AWUS036ACH**, chip **RTL8812AU** (USB `0bda:8812`).
- **What WiFiDeck needs from the radio:** MANAGED (normal Wi-Fi) *and* **MONITOR
  mode + frame injection** — the latter is required for handshake/PMKID capture,
  deauth, and the guided flow. Cracking, reporting, posture, etc. all work; the one
  thing that doesn't is **getting frames off the air**.

## What we observed (evidence)

MANAGED mode works perfectly — the adapter scanned the real environment (home
network + a long list of neighbours). **Monitor mode is dead:**

```text
$ sudo airodump-ng wlan0          # ran 36 s, channel-hopping worked...
 CH  9 ][ Elapsed: 36 s ]
 BSSID   PWR  Beacons  #Data ...   <-- ZERO rows. A working monitor adapter
                                       shows dozens of beacons per second.

$ sudo aireplay-ng --test wlan0
15:29:03  No Answer...
15:29:03  Found 0 APs               <-- injection can't be confirmed either
```

`iw dev` reports `type monitor` and the channel cycles, but **no frames are ever
delivered to userspace** — the driver accepts the mode but doesn't actually
capture or inject.

## Root cause

The RTL8812AU has **two** possible Linux drivers, and neither works here:

| Driver | Where | Monitor + inject? | On kernel 7.1 |
|---|---|---|---|
| **`rtw88`** (in-kernel, currently loaded) | ships with Linux | ❌ broken for this chip — no monitor RX, no injection | active → the 0-beacon result above |
| **`8812au` / `rtl88xxau`** (aircrack-ng, out-of-tree DKMS) | must be compiled per-kernel | ✅ yes | ❌ **won't build** (see below) |

The good driver source is even already installed (`realtek-rtl88xxau` DKMS,
status *added*), but its `dkms.conf` declares `BUILD_EXCLUSIVE_KERNEL_MAX="6.15"`
— it refuses kernels newer than 6.15, and this box runs 7.1.5.

## We tried to fix the driver (and hit a wall)

To avoid buying hardware, we attempted to port the aircrack `rtl88xxau` driver to
kernel 7.1, building in an isolated copy (no changes to the live system). We got
past **four** separate breakages:

1. `EXTRA_CFLAGS` → `ccflags-y` (kernel dropped the legacy variable)
2. include paths → `$(M)` (kbuild `$(src)` semantics changed in ≥6.13)
3. timer-API compat shim (`from_timer`/`del_timer_sync` renamed to
   `timer_container_of`/`timer_delete_sync`)
4. disabled the bridge/PPPoE code (`CONFIG_BR_EXT=n`; its kernel structs changed)

…and then hit the **cfg80211 wireless-API overhaul**: ~**15 driver callbacks**
(`add_station`, `del_station`, `add_key`, `del_key`, `set_tx_power`,
`remain_on_channel`, …) changed signature from `net_device *` to
`wireless_dev *`. That is a large, fragile rewrite with almost certainly **more
walls behind it** (mac80211, netdev, skb APIs) — the driver targets kernels 5+
versions older than 7.1.

**Verdict: porting this driver to kernel 7.1 is not practical.** It's the kind of
multi-day, break-on-every-update work that upstream maintainers do over careful
release cycles.

## Options considered

| Option | Cost | Keeps ACH? | Verdict |
|---|---|---|---|
| **A. New MediaTek radio (AWUS036AXML)** | ~CA$55 | ✅ (as a MANAGED/range adapter) | **Chosen** — works today, zero driver risk, future-proof |
| B. Downgrade the kernel to ≤ 6.15 | $0 | ✅ | Works, but pins Kali to an old kernel (loses updates/fixes), more setup, fragile |
| C. Port the `rtl88xxau` driver to 7.1 | $0 | ✅ | **Rejected** — proven impractical (cfg80211 overhaul + more) |

## Why MediaTek / AWUS036AXML

The deciding fact: **MediaTek's `mt76` driver is *in the Linux kernel*** — no DKMS,
no per-kernel compile, no version cap. It is confirmed already present on this box:

```text
$ find /lib/modules/7.1.5+kali-arm64 -name 'mt7921u.ko*'
.../mediatek/mt76/mt7921/mt7921u.ko.xz     # AWUS036AXML chip — already shipped
$ modinfo mt7921u | grep description
description:  MediaTek MT7921U (USB) wireless driver
```

So the AWUS036AXML is **plug-and-play**: monitor + injection + AP mode work out of
the box, and it additionally sees **WPA3 / 6 GHz** networks the RTL8812AU cannot.
The exact driver saga above simply cannot recur with an in-kernel driver.

## Trade-offs & what the ACH is still good for

- **The ACH is *not* junk** — it has a **high-power amp + high-gain antennas**, so
  its raw **range/sensitivity is better** than the AXML. Keep it as a MANAGED
  long-range adapter, a backup, or for range work on a kernel whose driver supports
  it.
- The AXML's range is good but not a long-range beast. Because it has **detachable
  RP-SMA antennas**, a ~$12 **9 dBi antenna** closes most of the gap if needed —
  antenna gain matters more than the amp for range.

## Cost

| Item | ~Cost | Required? |
|---|---|---|
| ALFA AWUS036AXML (MT7921AU) | ~CA$55 | **Yes** — the only way to get real capture on this kernel |
| High-gain 9 dBi RP-SMA antenna | ~CA$12 | Optional — only if more range is needed |
| GPS dongle (u-blox VK-172) | ~CA$15 | Optional — only for Phase 17 wardriving |
| Jetson Orin Nano | — | **Not needed** — the M4 handles all ML |

## Acceptance criteria (how we'll confirm the new radio works)

On arrival, connect the adapter to the **Kali VM** (VMware → USB & Bluetooth →
USB 3.1), then:

```bash
sudo dmesg | grep mt76            # expect it bound to mt7921u (NOT rtw88)
sudo airodump-ng wlanX            # expect: beacons streaming, many APs, CH cycling
sudo aireplay-ng --test wlanX     # expect: "Injection is working!"
```

Then run the full capture→crack acceptance test in
[docs/HARDWARE.md](HARDWARE.md). Passing it validates the entire tool on real RF.

## References

- [docs/HARDWARE.md](HARDWARE.md) — buying + setup + acceptance test
- [docs/BUILD-LOG.md](BUILD-LOG.md) — the real-capture verdict + driver-port log
- [scripts/fix-8812au-driver.sh](../scripts/fix-8812au-driver.sh) — the (reversible)
  driver-build attempt described above
