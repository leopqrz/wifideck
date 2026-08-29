# scripts/

Helper scripts for WiFiDeck.

## Launch the app

```bash
./scripts/wifideck            # start backend + frontend, open the browser
WIFIDECK_MOCK=1 ./scripts/wifideck   # no adapter needed (fixtures)
```
If the installed **systemd service** is running, `wifideck` just opens
`http://127.0.0.1:8787`. Otherwise it starts the dev servers and opens
`http://localhost:5173` (Ctrl+C stops both). Full mode-switch / capture / sharing
need root — use the service (`sudo ./install.sh`) or run the backend with sudo.

## Terminal fallbacks (no browser / no server needed)

Lightweight CLI equivalents of the app's radio controls — handy when the web app
isn't running. They self-elevate with sudo and auto-detect the interface.

| Script | Does |
|---|---|
| `wifi-status` | adapter health: USB, driver, MANAGED/MONITOR, IP, nearby networks |
| `wifi-monitor [ch]` | switch to MONITOR mode (optionally lock a channel) |
| `wifi-managed` | switch back to MANAGED and reconnect |
| `wifi-share on\|off` | NAT the ALFA's internet to the host |
| `wifi-lib.sh` | shared helpers (sourced by the above; not run directly) |

Put them on your PATH if you like: `sudo ln -sf "$PWD"/scripts/wifi-* /usr/local/sbin/`.

## Other

- `security_check.py` — release security re-review (`python3 scripts/security_check.py`).
- `49-nmcli.rules` — optional polkit rule to let your user run `nmcli` without sudo:
  `sudo install -m 0644 scripts/49-nmcli.rules /etc/polkit-1/rules.d/`.
