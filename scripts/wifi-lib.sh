# wifi-lib.sh — shared helpers for the ALFA (RTL8812AU / AWUS036ACH) tools.
#
# This file is NOT a command. The wifi-* scripts `source` it for a few common
# helpers. You never run it directly.

# --- Run as root -----------------------------------------------------------
# If we're not root, re-launch this same script under sudo (asking for the
# password once). $SELF is the script's real path, set by the caller.
become_root_if_needed() {
  if [ "$(id -u)" -ne 0 ]; then
    echo "(need root — re-running under sudo)"
    exec sudo -- "$SELF" "$@"
  fi
}

# --- Find the Wi-Fi interface ---------------------------------------------
# Prints the first wireless interface name (e.g. wlan0), or nothing if none.
find_wifi_interface() {
  local dev
  for dev in /sys/class/net/*/wireless; do
    if [ -e "$dev" ]; then
      basename "$(dirname "$dev")"
      return 0
    fi
  done
  # Fallback: ask iw directly.
  iw dev 2>/dev/null | awk '/Interface/ {print $2; exit}'
}

# Return the interface to use: the name passed in ($1) if given, otherwise
# auto-detect. Exits with a clear message if there is no Wi-Fi interface.
pick_interface() {
  local requested="${1:-}"
  if [ -n "$requested" ]; then
    echo "$requested"
    return 0
  fi

  local found
  found="$(find_wifi_interface)"
  if [ -z "$found" ]; then
    echo "ERROR: no Wi-Fi interface found." >&2
    echo "       Is the ALFA connected to the VM?  Check with:  wifi-status" >&2
    exit 1
  fi
  echo "$found"
}

# Print the current mode of an interface in CAPITALS: MANAGED / MONITOR / ...
current_mode() {
  iw dev "$1" info 2>/dev/null | awk '/type/ {print toupper($2); exit}'
}
