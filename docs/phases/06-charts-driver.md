# Phase 6 — Charts, driver panel, polish → v1

**Status:** ✅ complete (driver panel verified live; v1)

## What shipped

**Backend**
- `models/driver.py` — `DriverInfo` + `DkmsModule`.
- `services/driver.py` — `DriverService.info()`: bound driver (interface, with an
  **lsmod fallback** so it reports the loaded module even when the adapter is
  unplugged), kernel, parsed `dkms status`, recommendation + copyable install hint.
  `parse_dkms_status` handles both `name/ver: status` and full `name/ver, kernel,
  arch: status` forms. Read-only — driver switching stays a documented root step.
- `routers/driver.py` — `GET /api/driver`.

**Frontend**
- Charts: `useHistory` (rolling status samples), `Sparkline` (auto-scaling inline
  SVG), `MetricsPanel` (live Signal + TX-rate sparklines).
- `useDriver` hook; `DriverPanel` — bound driver (ok/warn tone), kernel, DKMS
  modules with status badges, recommendation note, and copyable switch commands.
- Polish: metrics row, two-up capture/share, driver panel, and a footer; v1 labels.

## Acceptance gate — results

| Check | Result |
|---|---|
| `GET /api/driver` reports driver/kernel/dkms/hint | ✅ live (real): kernel 7.1.5+kali-arm64, both DKMS modules |
| `current` robust when adapter unplugged (lsmod fallback) | ✅ live: `rtw88_8812au` with no interface |
| `dkms status` parser (both forms) | ✅ unit tests |
| Sparklines render + gathering state | ✅ unit tests |
| Backend `pytest` | ✅ 44 passed |
| Frontend `vitest` / lint / build | ✅ 21 passed / clean / built |

## 🏷️ v1 reached
Status, mode, scan, capture, sharing, charts, and driver panel — a complete
localhost command center for the ALFA.

## Next: Phase 7 — Gated active modules (deauth/handshake capture) → v2
Authorization gate + audit log + in-scope BSSID allowlist before any transmit action.
