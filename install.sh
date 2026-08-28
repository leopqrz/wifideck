#!/usr/bin/env bash
#
# WiFiDeck installer — sets up the root systemd service on 127.0.0.1.
#
# Prereqs: build the frontend first (needs Node):
#     cd frontend && npm run build
# Then:
#     sudo ./install.sh
#
set -euo pipefail
[ "$(id -u)" -eq 0 ] || exec sudo -- "$0" "$@"

SRC="$(cd "$(dirname "$0")" && pwd)"
DEST=/opt/wifideck

if [ ! -d "$SRC/frontend/dist" ]; then
  echo "ERROR: frontend/dist not found. Build it first:" >&2
  echo "         cd frontend && npm run build" >&2
  exit 1
fi

echo "[*] Installing WiFiDeck to $DEST"

# --- copy backend (no venv/tests/caches) + built frontend + docs ------------
rm -rf "$DEST/backend"
mkdir -p "$DEST/backend" "$DEST/frontend" "$DEST/data"
cp -a "$SRC/backend/app" "$SRC/backend/requirements.txt" "$SRC/backend/systemd" "$DEST/backend/"
find "$DEST/backend" -name __pycache__ -type d -prune -exec rm -rf {} +
rm -rf "$DEST/frontend/dist"
cp -a "$SRC/frontend/dist" "$DEST/frontend/dist"
cp -a "$SRC/README.md" "$DEST/" 2>/dev/null || true
cp -a "$SRC/docs" "$DEST/docs" 2>/dev/null || true

# --- python venv ------------------------------------------------------------
echo "[*] Creating venv + installing dependencies"
python3 -m venv "$DEST/backend/.venv"
"$DEST/backend/.venv/bin/pip" install -q --upgrade pip
"$DEST/backend/.venv/bin/pip" install -q -r "$DEST/backend/requirements.txt"

# --- .env with a generated token (only if missing) --------------------------
ENV="$DEST/backend/.env"
if [ ! -f "$ENV" ]; then
  TOKEN="$(openssl rand -hex 24 2>/dev/null || head -c 24 /dev/urandom | od -An -tx1 | tr -d ' \n')"
  cat > "$ENV" <<EOF
WIFIDECK_HOST=127.0.0.1
WIFIDECK_PORT=8787
WIFIDECK_TOKEN=$TOKEN
WIFIDECK_MOCK=0
WIFIDECK_CAPTURE_DIR=$DEST/data/sessions
WIFIDECK_SCOPE_FILE=$DEST/data/scope.json
WIFIDECK_AUDIT_LOG=$DEST/data/audit.jsonl
# Active (transmit) modules — enable ONLY for authorized testing of your own networks.
WIFIDECK_ENABLE_ACTIVE=0
EOF
  chmod 600 "$ENV"
  echo "[+] Generated a random token in $ENV"
else
  echo "[*] Keeping existing $ENV"
fi

# --- systemd service --------------------------------------------------------
echo "[*] Installing systemd service"
install -m 0644 "$DEST/backend/systemd/wifideck.service" /etc/systemd/system/wifideck.service
systemctl daemon-reload
systemctl enable --now wifideck.service

sleep 1
echo
echo "[+] WiFiDeck is running."
echo "    URL:   http://127.0.0.1:8787"
echo "    Token: grep WIFIDECK_TOKEN $ENV   (paste it once in the web UI)"
echo "    Logs:  journalctl -u wifideck -f"
echo "    Stop:  sudo systemctl stop wifideck"
