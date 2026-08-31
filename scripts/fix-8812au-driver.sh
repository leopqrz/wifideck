#!/usr/bin/env bash
#
# fix-8812au-driver.sh — try to make the ALFA AWUS036ACH (RTL8812AU) do monitor +
# injection by building the aircrack-ng 88XXau DKMS driver for a kernel newer than
# its built-in cap, then swapping it in for the in-kernel rtw88 driver.
#
# SAFE BY DESIGN:
#   * If the build fails (kernel API incompatible), NOTHING is changed — rtw88 stays.
#   * The driver swap only happens after a successful build+install, and rolls back
#     (restores rtw88) if the new module won't load — so the adapter is never left
#     driverless.
#
# Run:   sudo bash scripts/fix-8812au-driver.sh
# Undo:  sudo bash scripts/fix-8812au-driver.sh --revert
#
set -uo pipefail

BLACKLIST=/etc/modprobe.d/wifideck-8812au.conf
KVER="$(uname -r)"

revert() {
  echo "== reverting to the stock rtw88 driver =="
  rm -f "$BLACKLIST"
  modprobe -r 88XXau 2>/dev/null || true
  depmod -a 2>/dev/null || true
  modprobe rtw88_8812au 2>/dev/null || true
  echo "done — rtw88_8812au restored. Replug the adapter if it doesn't come back."
  exit 0
}
[ "${1:-}" = "--revert" ] && revert

if [ "$(id -u)" -ne 0 ]; then echo "run with sudo"; exit 1; fi

SRC="$(ls -d /usr/src/realtek-rtl88xxau-* 2>/dev/null | head -1)"
if [ -z "$SRC" ]; then
  echo "driver source not found — install it first: sudo apt install realtek-rtl88xxau-dkms"
  exit 1
fi
DRV_VER="$(basename "$SRC" | sed 's/^realtek-rtl88xxau-//')"
DRV="realtek-rtl88xxau/$DRV_VER"
echo "driver: $DRV"
echo "kernel: $KVER"

echo "== 1/5 raise the kernel cap in dkms.conf (backup kept as dkms.conf.orig) =="
[ -f "$SRC/dkms.conf.orig" ] || cp "$SRC/dkms.conf" "$SRC/dkms.conf.orig"
sed -i 's/^BUILD_EXCLUSIVE_KERNEL_MAX=.*/BUILD_EXCLUSIVE_KERNEL_MAX="9.99"/' "$SRC/dkms.conf"
grep -q 'BUILD_EXCLUSIVE_KERNEL_MAX' "$SRC/dkms.conf" || \
  echo 'BUILD_EXCLUSIVE_KERNEL_MAX="9.99"' >> "$SRC/dkms.conf"

echo "== 2/5 build for $KVER (this is the real test) =="
dkms build "$DRV" -k "$KVER" --force
if [ $? -ne 0 ]; then
  echo
  echo "############################################################"
  echo "BUILD FAILED — kernel $KVER is too new for this driver's code."
  echo "NOTHING was changed. rtw88 is still active; your adapter still"
  echo "works in MANAGED mode. Capture is not possible on this adapter"
  echo "with this kernel -> a MediaTek radio (docs/HARDWARE.md) is the fix,"
  echo "or downgrade the kernel to <= 6.15."
  echo "Build log: /var/lib/dkms/realtek-rtl88xxau/$DRV_VER/build/make.log"
  echo "############################################################"
  exit 1
fi

echo "== 3/5 install the built module =="
dkms install "$DRV" -k "$KVER" --force || { echo "install failed; rtw88 unchanged"; exit 1; }

echo "== 4/5 swap drivers: blacklist rtw88 for this chip, load 88XXau =="
cat > "$BLACKLIST" <<'EOF'
# WiFiDeck: use the aircrack-ng 88XXau driver (monitor+inject) for RTL8812AU
blacklist rtw88_8812au
blacklist rtw88_8812a
EOF
depmod -a
modprobe -r rtw88_8812au 2>/dev/null || true
if ! modprobe 88XXau; then
  echo "88XXau failed to load — rolling back to rtw88 so the adapter still works."
  revert
fi
sleep 2

echo "== 5/5 result =="
if lsmod | grep -q '^88XXau'; then
  echo "SUCCESS: 88XXau is loaded. Interfaces:"
  iw dev 2>/dev/null | grep Interface
  echo
  echo "NOW TEST (replace wlanX with your interface):"
  echo "  sudo iw dev wlanX set type monitor   # or use WiFiDeck's MONITOR button"
  echo "  sudo airodump-ng wlanX               # EXPECT: APs + beacons streaming"
  echo "  sudo aireplay-ng --test wlanX        # EXPECT: Injection is working!"
  echo
  echo "If those work -> your ALFA is fixed, no new hardware needed."
  echo "To undo: sudo bash scripts/fix-8812au-driver.sh --revert"
else
  echo "88XXau not loaded; reverting."
  revert
fi
