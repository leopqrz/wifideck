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
  "mode": "MANAGED", "operstate": "up", "ssid": "Queiroz", "ip4": "10.0.0.145/24",
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

## Planned (later phases)

| Phase | Endpoint | Purpose |
|---|---|---|
| 3 | `WS /ws/scan` | live network list |
| 4 | `POST /api/capture`, `GET /api/capture/{id}.pcap` | capture control + export |
| 5 | `POST /api/share` | internet sharing on/off |
| 7 | `POST /api/audit/*` | gated active modules |
