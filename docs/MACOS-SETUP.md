# Running WiFiDeck natively on macOS (no VM)

The RTL8812AU does **stable monitor capture on macOS via libusb** (see
[RADIO-ENVIRONMENT.md](RADIO-ENVIRONMENT.md)), so WiFiDeck can run **directly on the
Mac** — no VMware, no Linux, no root — with the ALFA AWUS036ACH you already own.

```
M4 → macOS → WiFiDeck (FastAPI) → libusb → AWUS036ACH
             ├─ radio backend: macos-rtl8812au (drives capture.py)
             └─ verify (tshark) → crack (aircrack/hashcat) → history → report
```

## 1. Prerequisites (Homebrew)

```sh
brew install python@3.12 node libusb tshark aircrack-ng hashcat hcxtools
```
(`tshark` = handshake verify · `aircrack-ng`/`hashcat` = crack · `hcxtools` = pcap→22000.)

## 2. The macOS capture driver

Set up [`xen-proc/rtl8812au-macos`](https://github.com/xen-proc/rtl8812au-macos) once
(see [MACOS-RTL8812AU-RUNBOOK.md](MACOS-RTL8812AU-RUNBOOK.md)), and note its directory —
WiFiDeck points at it via `WIFIDECK_RTL8812AU_DIR`.

## 3. Give the adapter to macOS

If a Kali VM is running, either shut it down **or** set VMware Fusion → *USB &
Bluetooth → "When you plug in a USB device: Connect to my Mac"* and disconnect the
adapter from the VM. Confirm macOS sees it:
```sh
system_profiler SPUSBDataType | grep -i "0x0bda\|realtek"
```

## 4. Run WiFiDeck on macOS

```sh
cd wifideck
# backend
cd backend && python3 -m venv .venv && . .venv/bin/activate && pip install -r requirements.txt
WIFIDECK_TOKEN=dev-token-change-me \
WIFIDECK_RADIO_BACKEND=macos \
WIFIDECK_RTL8812AU_DIR="$HOME/Projects/rtl8812au-macos" \
WIFIDECK_ENABLE_ACTIVE=1 \
PYTHONPATH=. uvicorn app.main:app --host 127.0.0.1 --port 8787 &
# frontend
cd ../frontend && npm install && npm run dev      # http://localhost:5173
```

- **Radio doctor** (`GET /api/radio`, or the Radio panel) should show
  `backend: macos-rtl8812au`, monitor RX + raw TX capable.
- **Capture** now drives `capture.py` under the hood; the pcap flows into
  verify → crack → history.
- Or, capture separately with `capture.py -o cap.pcap` and use **Import pcap** to
  adopt it.

## Notes / current limits

- The macOS radio has **no managed mode** and isn't a macOS Wi-Fi interface — it's a
  pure monitor/injection device. The mode toggle / nmcli-scan don't apply on macOS.
- **5 GHz TX** is limited to channel 36 (driver calibration).
- Bring-up can wedge after an interrupted capture — physically replug if a capture
  errors (the driver can't reset the chip in software).
- **Injection status (macOS):** `tools/inject.py` is a **raw-frame primitive** — it
  injects beacons/probes or an arbitrary frame via `--frame-hex` (hardcoded BSSID; no
  built-in deauth, no `--authorized-test`). So **deauth on macOS = craft an 802.11
  deauth frame → `--frame-hex`**, and the exact frame/radiotap format needs on-hardware
  validation. Until that's confirmed, the macOS backend does **capture only**; deauth /
  the guided flow remain Linux-path features. Capture → verify → crack is fully covered.
- **AP enumeration from a pcap:** `parse_tshark_beacons` lists the APs in a capture
  (feeds the macOS scan / imported-pcap network view).
