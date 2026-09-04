# Radio environment — current state of record

Snapshot of the exact host + guest + adapter state, so radio work is reproducible
and we can tell *which layer* fails. Regenerate the guest section with
[`scripts/radio-diagnostics.sh`](../scripts/radio-diagnostics.sh).

_Captured: 2026-08-30._

## Host (macOS)

| | |
|---|---|
| Machine | Apple MacBook Pro, **M4 Max** |
| RAM | 64 GB |
| Arch | Apple Silicon (arm64) |
| macOS version | _to confirm on host_ (`sw_vers`) |
| VMware Fusion version | _to confirm on host_ |
| USB passthrough | adapter attached to the Kali VM (VMware → USB & Bluetooth) |

> Host-side facts (macOS/Fusion versions, USB controller) must be filled in from
> the **macOS host** — they can't be read from inside the guest.

## Guest (Kali VM) — captured

| | |
|---|---|
| OS | Kali GNU/Linux Rolling **2026.3** |
| Kernel | **7.1.5+kali-arm64** (SMP PREEMPT, built 2026-07-29) |
| Arch | **arm64** (aarch64) |
| Adapter | ALFA AWUS036ACH — **`0bda:8812`** RTL8812AU 2T2R |
| USB bus | **Bus 003** = `xhci_hcd`, **20000M** (USB 3.x) → not a USB-2 bottleneck |
| Driver bound to wlan0 | **`rtw88_8812au`** (in-kernel) |
| Loaded modules | `rtw88_8812au`, `rtw88_8812a`, `rtw88_88xxa`, `rtw88_usb`, `rtw88_core`, `mac80211`, `cfg80211` |
| `phy` supported modes | IBSS, **managed**, **AP**, AP/VLAN, **monitor** |
| Current mode | managed, ch 44 (5220 MHz), 80 MHz |
| rfkill | not blocked (soft/hard: no) |
| DKMS | `realtek-rtl88xxau/5.6.4.2~git20250330` (**added**, not built), `realtek-rtl8814au/5.8.5.1~git20250903` (added) |

## Where it fails (established)

- **MANAGED works** — scans and connects normally.
- **MONITOR is accepted by `iw`** (type monitor, channel hops) but **no 802.11
  frames reach userspace** — `airodump-ng` saw 0 beacons in 36 s; `aireplay-ng
  --test` found 0 APs.
- Root layer: the **`rtw88` driver** does not deliver monitor RX / injection for
  this chip, and the **`rtl88xxau` DKMS** won't build on kernel 7.1 (its
  `BUILD_EXCLUSIVE_KERNEL_MAX="6.15"` cap, and — once patched past it — a
  cfg80211 callback-signature overhaul). See [ADR-001](ADR-001-adapter-swap.md).

**Important correction:** the RTL8812AU *hardware* is capable of monitor + injection
(the `phy` even advertises the modes). This is a **driver/environment** problem on
kernel 7.1, **not** a hardware limitation. Paths under investigation: native-macOS
libusb driver, a compatible-kernel RF VM, and newer upstream `rtl8812au` branches.

## Native-macOS test — 2026-08-30 (PROOF)

Ran [`xen-proc/rtl8812au-macos`](https://github.com/xen-proc/rtl8812au-macos) on the
**macOS host** (adapter detached from the VM), per [MACOS-RTL8812AU-RUNBOOK.md](MACOS-RTL8812AU-RUNBOOK.md):

- **2.4 GHz (ch 6): ✅ WORKS — 1152 frames** captured in 10 s, real beacons + data
  from the operator's own AP `96:04:e3:ec:ab:5a` (Queiroz). Bring-up: "BB/RF tables
  applied, RFE type 3".
- **5 GHz (ch 36): retest pending.** The first attempt returned 0 frames only because
  the adapter **dropped off the USB bus** after an `[Errno 5] I/O Error` at the end of
  the ch6 capture (`error opening device: no USB device 0bda:8812 found`) — the known
  "failed bring-up needs a physical replug" quirk, not a 5 GHz failure. Retest = replug
  + ch36-only run.

**Conclusion:** the ACH does **real native-macOS monitor capture** over libusb — no
VMware, no Linux driver, no kext, no SIP change, no sudo. Native macOS is a **viable
WiFiDeck RF backend**, and the most promising architecture (M4 → macOS → libusb → ACH
→ WiFiDeck). Open item: bring-up **stability** (the mid-capture I/O drop) and 5 GHz
confirmation.
