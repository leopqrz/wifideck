# Native-macOS RTL8812AU capture — host runbook (Phase 2C prototype)

Goal: prove the **AWUS036ACH can do real monitor-mode capture directly on macOS**
via the userspace libusb driver [`xen-proc/rtl8812au-macos`](https://github.com/xen-proc/rtl8812au-macos)
— **no VMware in the RF path**. This runs on the **macOS host**, not in the Kali VM.

**Why this is safe:** the driver is pure userspace over **libusb** — no kernel
extension, no SIP change, no reduced-security boot, no `sudo` for capture. The only
"intrusive" step is telling VMware to hand the USB adapter back to macOS.

> The project is early-stage (~2 commits). Treat this as a **prototype/validation**,
> not a commitment. If it works reliably, we make it a first-class WiFiDeck backend;
> if not, we've lost nothing and move to the RF-VM path.

---

## Step 1 — Give the adapter to macOS (VMware GUI)

Right now the ACH is attached exclusively to the Kali VM, so macOS can't see it.

- VMware Fusion → menu **Virtual Machine → USB & Bluetooth** → find **"Realtek
  802.11ac NIC"** (or `0bda:8812`) → click **Disconnect** (this returns it to macOS).
- *Or* physically unplug/replug it and, if VMware prompts "Connect to Mac / Connect
  to VM", choose **Connect to Mac**.

**Confirm macOS sees it:**
```sh
system_profiler SPUSBDataType | grep -i -A6 "realtek\|0x8812"
```
**Expect:** a Realtek entry with Product ID `0x8812`, Vendor ID `0x0bda`.
❗ If nothing shows, it's still captured by the VM — repeat Step 1.

## Step 2 — Install prerequisites (macOS)

```sh
# Homebrew (skip if you have it) + libusb + Xcode CLT for pip builds
xcode-select --install 2>/dev/null || true
brew install libusb python@3.12 git
```

## Step 3 — Get the driver

```sh
cd ~/Projects            # or wherever you like
git clone https://github.com/xen-proc/rtl8812au-macos.git
cd rtl8812au-macos
python3 -m venv .venv                       # Python 3.10+
.venv/bin/pip install -r requirements.txt
.venv/bin/python -m pip install -e .
```

## Step 4 — Monitor-RX test (the real proof)

Two 10-second captures — 2.4 GHz then 5 GHz (both are the project's hardware-verified
channels):

```sh
.venv/bin/python tools/capture.py -c 6  -t 10 -o capture-ch6.pcap
.venv/bin/python tools/capture.py -c 36 -t 10 -o capture-ch36.pcap
```

**Verify frames actually landed** (macOS ships `tcpdump`):
```sh
echo "ch6  frames: $(tcpdump -r capture-ch6.pcap  2>/dev/null | wc -l)"
echo "ch36 frames: $(tcpdump -r capture-ch36.pcap 2>/dev/null | wc -l)"
tcpdump -r capture-ch6.pcap -c 5 2>/dev/null      # a few decoded 802.11 frames
```
**Expect:** non-zero frame counts (the project reported ~259 on ch6, ~65 on ch36),
and tcpdump showing beacon/probe frames. Open either `.pcap` in **Wireshark** to
eyeball beacons if you have it.

## Step 5 (optional) — Injection, YOUR network only

Only against an AP **you own** (a spare router or your phone hotspot). This transmits.
```sh
.venv/bin/python tools/inject.py --authorized-test      # exact flags: check tools/inject.py --help
```

## If a capture fails or hangs
The chip can get stuck after a failed bring-up. Per the project: a software reset
does **not** recover it — **physically unplug the adapter, wait ~5 s, replug**, and
retry from Step 1. (No other recovery needed.)

## Step 6 — Hand the adapter back to the VM (when done)
VMware Fusion → **Virtual Machine → USB & Bluetooth → Connect "Realtek 802.11ac NIC"**
(re-attaches it to Kali). Back in the VM, `lsusb | grep 0bda:8812` confirms it returned.

---

## Paste back to me

1. The **frame counts** from Step 4 (`ch6 frames: N`, `ch36 frames: N`).
2. The first few lines of `tcpdump -r capture-ch6.pcap -c 5`.
3. Any **errors** from Steps 3–4 (especially libusb "permission"/"no device" or a
   Python traceback).
4. Whether it needed a physical replug.

**What the result means:**
- **Non-zero frames on both** → native-macOS is a viable WiFiDeck RF backend; we add a
  macOS capture backend and can drop VMware from the RF path. 🎯
- **Zero frames / errors** → we log it in RADIO-ENVIRONMENT.md and move to the
  compatible-kernel RF-VM path (still on the ACH, no new hardware).
