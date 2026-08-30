"""Runtime configuration, read from the environment with safe local defaults.

Kept dependency-free (plain os.environ) so Phase 0 has no settings-library
requirement. Everything is overridable via WIFIDECK_* env vars or the .env
consumed by the systemd unit.
"""
from __future__ import annotations

import os
from dataclasses import dataclass


def _bool(name: str, default: bool) -> bool:
    val = os.environ.get(name)
    if val is None:
        return default
    return val.strip().lower() in {"1", "true", "yes", "on"}


@dataclass(frozen=True)
class Settings:
    # Bind to loopback ONLY. Exposing this service to the network is unsupported
    # and a security risk — the bind address is asserted in tests.
    host: str = os.environ.get("WIFIDECK_HOST", "127.0.0.1")
    port: int = int(os.environ.get("WIFIDECK_PORT", "8787"))

    # Shared secret required on every HTTP route and WebSocket.
    token: str = os.environ.get("WIFIDECK_TOKEN", "dev-token-change-me")

    # Mock-adapter mode: serve recorded fixtures instead of touching hardware,
    # so the UI and tests run with no ALFA attached.
    mock: bool = _bool("WIFIDECK_MOCK", False)

    # Where capture sessions (csv + pcap) are written.
    capture_dir: str = os.environ.get("WIFIDECK_CAPTURE_DIR", "/tmp/wifideck/sessions")

    # The last MANAGED scan, snapshotted when switching to MONITOR (where the live
    # scan returns nothing on this adapter) so target pickers still have networks.
    known_file: str = os.environ.get("WIFIDECK_KNOWN_FILE", "/tmp/wifideck/known.json")

    # SQLite history DB — persists capture sessions + crack outcomes across restarts.
    db_file: str = os.environ.get("WIFIDECK_DB", "/tmp/wifideck/wifideck.db")

    # Interface facing the host (macOS) for internet sharing (VMware NAT nic).
    share_downlink: str = os.environ.get("WIFIDECK_SHARE_DOWNLINK", "eth0")

    # --- Active (transmit) modules: OFF by default -------------------------
    # Deauth and other frame-injection actions are disabled unless this is set.
    # Even when enabled they require an in-scope target + per-action auth flag.
    enable_active: bool = _bool("WIFIDECK_ENABLE_ACTIVE", False)
    scope_file: str = os.environ.get("WIFIDECK_SCOPE_FILE", "/tmp/wifideck/scope.json")
    audit_log: str = os.environ.get("WIFIDECK_AUDIT_LOG", "/tmp/wifideck/audit.jsonl")

    # --- Self-healing watchdog ---------------------------------------------
    # Watches for USB disconnects / -71 register errors and auto-recovers the
    # adapter (driver reload, USB reset, reconnect). Off by default; needs root.
    watchdog_enabled: bool = _bool("WIFIDECK_WATCHDOG", False)
    watchdog_interval: float = float(os.environ.get("WIFIDECK_WATCHDOG_INTERVAL", "5"))

    # --- Defensive monitoring (WIDS-lite) ----------------------------------
    # Detect evil-twin APs (from scans) and deauth floods (tshark, monitor mode).
    wids_enabled: bool = _bool("WIFIDECK_WIDS", False)
    wids_interval: float = float(os.environ.get("WIFIDECK_WIDS_INTERVAL", "10"))
    wids_deauth_threshold: int = int(os.environ.get("WIFIDECK_WIDS_DEAUTH_THRESHOLD", "20"))

    # --- Cracking (aircrack-ng) --------------------------------------------
    # Default wordlist for handshake cracking (Kali ships rockyou.txt.gz — gunzip it).
    wordlist: str = os.environ.get("WIFIDECK_WORDLIST", "/usr/share/wordlists/rockyou.txt")

    version: str = "2.5.0"


settings = Settings()
