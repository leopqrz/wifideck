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

## Planned (later phases)

| Phase | Endpoint | Purpose |
|---|---|---|
| 1 | `GET /api/status`, `WS /ws/status` | live adapter telemetry + health |
| 2 | `POST /api/mode` | MANAGED ⇄ MONITOR (+channel) |
| 3 | `WS /ws/scan` | live network list |
| 4 | `POST /api/capture`, `GET /api/capture/{id}.pcap` | capture control + export |
| 5 | `POST /api/share` | internet sharing on/off |
| 7 | `POST /api/audit/*` | gated active modules |
