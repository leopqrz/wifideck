#!/usr/bin/env bash
#
# radio-diagnostics.sh — READ-ONLY snapshot of the radio stack, layer by layer, so
# we can tell *where* monitor RX fails without changing anything. Safe to run any
# time; it modifies nothing. (Live monitor-RX / injection validation is a separate,
# state-changing step — see scripts/radio-acceptance-test.sh, Phase 8.)
#
# Usage: bash scripts/radio-diagnostics.sh [iface]   (default: wlan0)
#
set -uo pipefail
IFACE="${1:-wlan0}"
line() { printf '\n=== %s ===\n' "$1"; }

line "KERNEL / OS / ARCH"
uname -a
grep -E "PRETTY_NAME|VERSION_ID" /etc/os-release 2>/dev/null
echo "dpkg arch: $(dpkg --print-architecture 2>/dev/null)"

line "USB DEVICE (0bda:8812 expected)"
lsusb | grep -iE "0bda:8812|realtek" || echo "  adapter not found on USB bus"
echo "--- topology (speed/driver) ---"
lsusb -t 2>/dev/null

line "DRIVER BINDING"
if [ -e "/sys/class/net/$IFACE/device/driver" ]; then
  echo "$IFACE driver: $(readlink -f /sys/class/net/$IFACE/device/driver)"
else
  echo "  no /sys/class/net/$IFACE (interface missing?)"
fi
echo "--- loaded 802.11 modules ---"
lsmod | grep -iE "rtw|8812|88xx|mt76|mac80211|cfg80211" || echo "  none"

line "PHY CAPABILITIES"
iw phy 2>/dev/null | grep -A8 "Supported interface modes" | head -12

line "INTERFACE STATE"
iw dev 2>/dev/null | grep -E "Interface|type|channel|txpower"
ip link show "$IFACE" 2>/dev/null | head -2
rfkill list 2>/dev/null

line "DKMS"
dkms status 2>/dev/null || echo "  (dkms not available)"

line "RECENT KERNEL MESSAGES (wifi/usb)"
if command -v journalctl >/dev/null 2>&1; then
  sudo -n journalctl -k --no-pager 2>/dev/null | grep -iE "rtw88|8812|usb .*disconnect|-71|firmware" | tail -15 \
    || echo "  (need sudo for kernel log; skipped)"
fi

line "SUMMARY"
DRV=$(readlink -f "/sys/class/net/$IFACE/device/driver" 2>/dev/null | xargs -r basename)
echo "interface : $IFACE"
echo "driver    : ${DRV:-none}"
echo "kernel    : $(uname -r)"
echo "monitor in phy modes: $(iw phy 2>/dev/null | grep -q '\* monitor' && echo yes || echo no)"
echo
echo "NOTE: 'monitor in phy modes: yes' means the driver ACCEPTS monitor mode — it"
echo "does NOT prove frames reach userspace. Confirm real RX with the acceptance test."
