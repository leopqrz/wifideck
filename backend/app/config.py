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

    # Interface facing the host (macOS) for internet sharing (VMware NAT nic).
    share_downlink: str = os.environ.get("WIFIDECK_SHARE_DOWNLINK", "eth0")

    version: str = "0.1.0"


settings = Settings()
