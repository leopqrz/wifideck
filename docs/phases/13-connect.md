# Phase 13 — Client connect / disconnect → v2.5

**Status:** ✅ complete

Click any SSID in the Networks table to join or leave it. NetworkManager persists
the profile + password (in its keyring), so it auto-reconnects later — no password
storage of our own.

## What shipped

**Backend**
- `models/connect.py` — `ConnectResult`.
- `services/connect.py` — `ConnectService`: `connect` (nmcli, refuses in MONITOR
  mode, surfaces failures like a wrong password), `disconnect`, `forget` (deletes
  the saved profile), `saved` (lists NM's saved Wi-Fi profiles).
- `routers/connect.py` — `POST /api/connect`, `POST /api/disconnect`,
  `POST /api/forget`, `GET /api/saved`.

**Frontend**
- Client `connectWifi` / `disconnectWifi` / `forgetWifi` / `getSaved`.
- `NetworkTable` gains an action column via `ConnectCell`: **Connect** (open/saved
  networks connect instantly; secured ones show an inline password box), **Connect ★**
  for saved networks, **forget**, and **Disconnect** on the current network.

## Acceptance gate — results

| Check | Result |
|---|---|
| nmcli connect args (ssid/password) built correctly | ✅ unit test |
| Refused in MONITOR mode; failures surfaced (bad password) | ✅ unit tests |
| connect / disconnect / forget / saved endpoints | ✅ live (mock) + tests |
| Row actions (Connect/Disconnect) render | ✅ vitest |
| Endpoints token-gated | ✅ tests |
| Backend `pytest` | ✅ 88 passed |
| Frontend `vitest` / lint / build | ✅ 35 passed / clean / built |
| **Live connect on real hardware** | ⏳ MANAGED mode + a network you can join |
