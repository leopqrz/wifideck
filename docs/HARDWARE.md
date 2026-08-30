# WiFiDeck — Radio buying & setup guide

Real capture (handshakes, PMKID, deauth injection) needs an adapter whose driver
supports **monitor RX + frame injection**. Your current **ALFA AWUS036ACH
(RTL8812AU)** does **not** — confirmed 2026-08-30 (`airodump-ng` saw 0 beacons in
36 s; `aireplay-ng --test` found 0 APs). It's great in MANAGED mode, dead in
MONITOR. This guide is the fix.

> **Rule of thumb:** for monitor/injection on Linux, buy **MediaTek**, avoid
> **Realtek**. MediaTek `mt76` drivers are *in the kernel* — no DKMS, no
> kernel-version breakage (the exact pain the 8812au gave you). Realtek chips need
> out-of-tree DKMS drivers that break on new kernels (your kernel is 7.1).

## What to buy

| Pick | Chip / driver | Bands | Why | ~Price |
|---|---|---|---|---|
| **ALFA AWUS036AXML** ⭐ | MT7921U / `mt76` | 2.4 + 5 + **6 GHz** | Wi-Fi 6E; sees **WPA3 & 6 GHz** networks the 8812au can't; monitor + inject + AP mode in-kernel | ~$40 |
| **ALFA AWUS036ACM** (safe budget) | MT7612U / `mt76x2u` | 2.4 + 5 | The **most battle-tested** monitor/injection adapter for aircrack-style work; rock solid | ~$30 |
| Panda / others with **MT7612U** | `mt76x2u` | 2.4 + 5 | Same chip as ACM, cheaper brands | ~$20–30 |

**Recommendation:** the **AWUS036AXML** — it's future-proof (6 GHz/WPA3) and does
everything. If you want the single most-proven-for-monitor option and don't care
about 6 GHz, the **AWUS036ACM** (MT7612U) is the gold standard.

**Avoid** (Realtek — DKMS pain, the problem you already hit): RTL8812AU, RTL8814AU,
RTL8811AU, RTL8188.

## Setup (when it arrives)

**1. Connect it to the Kali VM (Apple Silicon / VMware Fusion).**
- Plug the adapter into the Mac.
- VMware Fusion → **Virtual Machine → USB & Bluetooth → Connect** the adapter to the
  Kali VM (not macOS).
- Set the VM's **USB compatibility to USB 3.1** (Settings → USB & Bluetooth).
- If you hit the `-71` disconnect drops (VMware USB flakiness), a **powered USB hub**
  usually fixes it.

**2. Confirm the kernel picked it up (no driver install needed):**
```bash
lsusb                       # should list a MediaTek device (0e8d:7961 AXML, 0e8d:7612 ACM)
ip link                     # a new wlanX appears
iw dev                      # note its name (may be wlan1 if the old ALFA is still in)
sudo dmesg | grep -i mt76   # driver mt76 / mt7921u / mt76x2u bound — NOT rtw88
```
> Tip: **unplug the old ALFA** so there's only one wireless interface (WiFiDeck uses
> the first one it finds until multi-adapter, Phase 13, lands).

**3. Prove monitor + injection actually work (the tests the 8812au failed):**
```bash
sudo airmon-ng start wlanX          # or use WiFiDeck's MONITOR button
sudo airodump-ng wlanX              # EXPECT: many APs, beacons streaming, CH cycling
sudo aireplay-ng --test wlanX       # EXPECT: "Injection is working!"
```
If those two pass, real capture will work. (On the 8812au they showed 0 APs — that's
the difference you're buying.)

## Then: the full real-capture acceptance test

With a working radio + a **test AP you own** (a spare router or your **phone hotspot**
set to **WPA2** with a **weak password that's in `rockyou.txt`**, e.g. `password123`)
+ **a second device connected to it**:

1. WiFiDeck **Target** → pick your test AP (readout shows WPA2).
2. **Guided capture → Run flow** → expect `monitor ✓ → capture ✓ → deauth ✓ →
   handshake ✓` (your client reconnects; its handshake is caught).
3. **History** → new row, **CAPTURED: handshake ✓** (not `—`).
4. **Handshake cracking** → pick that session → **tshark shows M1 M2 M3 M4** green.
5. Engine **hashcat**, wordlist `/usr/share/wordlists/rockyou.txt`, **Crack** →
   **key found = your weak password**.
6. **History** → that row's **CRACK** column fills with the key.

Also test the **clientless** path: Capture panel → **PMKID** mode → Start → **PMKID ✓**
→ crack with hashcat (needs no client and no deauth).

Passing all of that = the entire tool validated on real RF. Everything else already is.

## Notes

- **Legal/ethical:** only ever on a network **you own or are authorized to test**. The
  weak-password test AP above is the clean, self-contained way to see the full chain.
- **Weak-on-purpose password:** so the crack actually *succeeds* — a strong password
  would (correctly) never crack, and you couldn't tell "working" from "wrong password".
- **6 GHz / WPA3:** only the AXML sees 6 GHz. For WPA3-transition testing on 2.4/5 GHz,
  either adapter is fine.
