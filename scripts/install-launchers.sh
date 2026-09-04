#!/usr/bin/env bash
#
# install-launchers.sh — set up the double-click launcher for this OS.
#
#   macOS : make WiFiDeck.app clickable and (optionally) put a copy in
#           ~/Applications so it shows in Launchpad / Spotlight.
#   Linux : generate WiFiDeck.desktop (with the correct absolute path) into your
#           applications menu and on your Desktop.
#
# Re-run any time; it's idempotent.
#
set -euo pipefail

# repo root = parent of this scripts/ dir
ROOT="$(cd -P "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
OS="$(uname -s)"

if [ ! -x "$ROOT/wifideck" ]; then
  echo "ERROR: $ROOT/wifideck not found or not executable." >&2
  exit 1
fi

case "$OS" in
Darwin)
  APP="$ROOT/WiFiDeck.app"
  chmod +x "$APP/Contents/MacOS/WiFiDeck"
  # Remember where the repo is, so a copied-out .app can still find it.
  mkdir -p "$HOME/.config/wifideck"
  printf '%s\n' "$ROOT" > "$HOME/.config/wifideck/root"

  DEST="$HOME/Applications"
  mkdir -p "$DEST"
  # Fresh copy so Launchpad/Spotlight index it; the copy reads the repo path
  # from ~/.config/wifideck/root, so the in-repo scripts stay the source of truth.
  rm -rf "$DEST/WiFiDeck.app"
  cp -R "$APP" "$DEST/WiFiDeck.app"
  # Clear the quarantine bit so it opens without the unidentified-developer nag.
  xattr -dr com.apple.quarantine "$DEST/WiFiDeck.app" 2>/dev/null || true

  echo "✓ Installed: $DEST/WiFiDeck.app"
  echo "  • Double-click it in Finder, or find “WiFiDeck” in Spotlight / Launchpad."
  echo "  • The in-repo $APP is also clickable directly."
  echo "  • Drag it to your Dock to keep it one click away."
  ;;
Linux)
  APPS="$HOME/.local/share/applications"
  mkdir -p "$APPS"
  gen() {
    local out="$1"
    sed "s#^Exec=.*#Exec=$ROOT/wifideck#" "$ROOT/WiFiDeck.desktop" > "$out"
    chmod +x "$out"
    gio set "$out" metadata::trusted true 2>/dev/null || true
  }
  gen "$APPS/wifideck.desktop"
  update-desktop-database "$APPS" 2>/dev/null || true
  echo "✓ Installed: $APPS/wifideck.desktop  (search “WiFiDeck” in your app menu)"

  if [ -d "$HOME/Desktop" ]; then
    gen "$HOME/Desktop/WiFiDeck.desktop"
    echo "✓ Desktop icon: $HOME/Desktop/WiFiDeck.desktop"
    echo "  (first launch: right-click → Allow Launching, on some desktops)"
  fi
  ;;
*)
  echo "Unsupported OS: $OS  — run ./wifideck directly." >&2
  exit 1
  ;;
esac

echo
echo "Done. Clicking it starts the backend + frontend and opens the dashboard."
