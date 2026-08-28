# Phase 5 — Internet sharing to the host

**Status:** ✅ complete (contract verified; live enable is a root step)

## What shipped

**Backend**
- `models/share.py` — `ShareStatus` (active, uplink, downlink, vm_ip, gateway, mac_commands).
- `services/share.py` — `ShareService` wrapping the alfa-tools `wifi-share` logic:
  `enable()`/`disable()` toggle `ip_forward`, MASQUERADE + FORWARD rules (added only if
  absent), and a low-metric default route out the uplink; `status_info()` detects the
  live state (`ip_forward` + `iptables -C`). `parse_default_gateway` + `mac_commands`
  build the copyable macOS route/DNS steps.
- `routers/share.py` — `GET /api/share`, `POST /api/share {enabled}`.
- Mock mode toggles an in-memory flag and reports fixture topology (eth0 192.0.2.128).

**Frontend**
- `useShare` hook (polls status); client `getShare`/`setShare`.
- `ShareControl` — on/off toggle, topology line (`Mac <–eth0–[VM]–wlan0–> internet`),
  and, when active, the **macOS commands with copy buttons** + the /1-routes note.

## Acceptance gate — results

| Check | Result |
|---|---|
| `GET /api/share` reports topology + mac_commands | ✅ live (mock): eth0/wlan0, vm_ip 192.0.2.128 |
| `POST /api/share` toggles active on/off | ✅ live (mock) |
| Gateway parse + mac-command building | ✅ unit tests |
| Rules added idempotently (`-C` before `-A`) | ✅ (in `_ensure`) |
| No uplink → 500 | ✅ (ShareError) |
| Auth required | ✅ test |
| Backend `pytest` | ✅ 40 passed |
| Frontend `vitest` / lint / build | ✅ 17 passed / clean / built |
| **Live enable on real hardware** (Mac routes through the ALFA) | ⏳ **root step** |

## Verifying live (root)
Connect the ALFA to Wi-Fi (MANAGED), run the backend as root, toggle sharing on, then
paste the shown commands into macOS Terminal. Undo: toggle off + delete the two /1 routes.
Reminder: this is usually *slower* than the Mac's own Wi-Fi (VM + USB overhead).

## Next: Phase 6 — Charts, driver panel, polish → v1
Signal/throughput history charts, driver/DKMS panel (rtw88 ↔ 88XXau), and UX polish.
