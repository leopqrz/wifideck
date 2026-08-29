# API

Base URL (dev): `http://127.0.0.1:8787` (proxied at `/api` and `/ws` from the
Vite dev server on `:5173`).

**Auth:** every route and WebSocket requires the token.
- HTTP: `Authorization: Bearer <token>` or `X-Auth-Token: <token>`.
- WebSocket: `?token=<token>` query parameter.
Missing/invalid → HTTP `401`, or WS close code `1008`.

## Endpoints

### `GET /api/health`
Liveness + build info. **Phase 0 gate.**

```json
{ "status": "ok", "service": "wifideck", "version": "0.1.0", "mock": false }
```

### `WS /ws/echo`
Authenticated echo channel proving a live connection.
- On connect → `{ "type": "hello", "service": "wifideck" }`
- Any text sent back as → `{ "type": "echo", "data": "<text>" }`

### `GET /api/status`  *(Phase 1)*
Current adapter snapshot.
```json
{ "usb_present": true, "driver": "rtw88_8812au", "interface": "wlan0",
  "mode": "MANAGED", "operstate": "up", "ssid": "MockNet-5G", "ip4": "192.0.2.10/24",
  "signal_dbm": -22, "tx_bitrate_mbps": 175.5, "freq_mhz": 5785, "band": "5 GHz",
  "health": "ok", "health_detail": null }
```
`health` ∈ `ok` | `disconnected` | `degraded`.

### `WS /ws/status`  *(Phase 1)*
Pushes `{ "type": "status", "data": <Status> }` on connect and whenever the
snapshot changes (polled every 2s).

### `POST /api/mode`  *(Phase 2)*
Switch the adapter. Body: `{ "mode": "managed" | "monitor", "channel": <1-196|null> }`.
Returns the resulting `Status`. Serialized by a state machine:
- `409` if a switch is already in progress.
- `422` on an invalid mode or out-of-range channel.
- `500` if the switch fails (e.g. not running as root).

### `WS /ws/scan`  *(Phase 3)*
Streams `{ "type": "scan", "source": "managed"|"monitor", "data": [<Network>...] }`
every 5s. Source auto-selected from the current mode (nmcli in MANAGED, airodump
in MONITOR). `Network`: bssid, ssid, band, channel, signal_pct, signal_dbm,
security[], is_current, clients.

### Capture  *(Phase 4)*
- `POST /api/capture` — start. Body `{ "channel": <1-196|null>, "bssid": <str|null> }`.
  `409` if one is running or not in MONITOR mode.
- `POST /api/capture/{id}/stop` — stop a session.
- `GET /api/capture` — list sessions.
- `GET /api/capture/{id}` — session detail incl. live `networks[]`.
- `GET /api/capture/{id}/pcap` — download the `.cap` (`404` until data is written).
- `WS /ws/capture` — streams `{ "type": "capture", "data": <CaptureDetail|null> }`
  every 2s for the active session (ap/client counts, handshake/PMKID flags).

### Internet sharing  *(Phase 5)*
- `GET /api/share` — status: `{ active, uplink, downlink, vm_ip, gateway, mac_commands[] }`.
- `POST /api/share` — body `{ "enabled": true|false }`. Enables/disables NAT of the
  ALFA uplink to the host; returns the updated `ShareStatus`. `mac_commands` are the
  route/DNS lines to run on macOS. `500` if there's no uplink.

### `GET /api/driver`  *(Phase 6)*
Read-only driver/DKMS report: `{ current, kernel, dkms[], recommended,
using_recommended, note, install_hint[] }`. `current` prefers the interface-bound
driver, falling back to the loaded module when the adapter is unplugged. Switching
drivers is left to the documented `install_hint` root commands (not automated).

### Active modules, scope & audit  *(Phase 7)*
Transmit actions are **off by default** (`WIFIDECK_ENABLE_ACTIVE=1` to enable) and
gated by an in-scope allowlist + per-action authorization. Every attempt is audited.
- `GET /api/active` — `{ enabled }`.
- `GET /api/scope` · `POST /api/scope {bssid, ssid?, note?}` · `DELETE /api/scope/{bssid}` — manage the authorized-target allowlist (`422` on invalid BSSID).
- `GET /api/audit?limit=` — recent audit entries (newest first).
- `POST /api/active/deauth {bssid, client?, count, authorized}` — gated deauth. Refusals: `403` (active disabled / not authorized / not in scope), `409` (not in MONITOR mode). Success returns the `AuditEntry`. **Authorized testing of your own networks only.**

### Self-healing watchdog  *(Phase 9)*
- `GET /api/watchdog` — status: `{ enabled, running, healthy, usb_present, interface, checks, recoveries, last_check, events[] }`.
- `POST /api/watchdog {enabled}` — start/stop the watchdog loop.
- `WS /ws/watchdog` — streams `{ "type": "watchdog", "data": <WatchdogStatus> }` every 2s (health + recovery events). Recovery escalates: driver reload → USB reset → reconnect; a full off-bus drop is reported as a host (passthrough) issue.

## Planned (later phases)

| Phase | Endpoint | Purpose |
|---|---|---|
| 7 | `POST /api/audit/*` | gated active modules |
