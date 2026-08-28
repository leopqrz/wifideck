"""Internet-sharing status model."""
from __future__ import annotations

from pydantic import BaseModel


class ShareStatus(BaseModel):
    active: bool
    uplink: str | None = None       # interface WITH internet (the ALFA)
    downlink: str                   # interface facing the Mac
    vm_ip: str | None = None        # this VM's Mac-facing IP
    gateway: str | None = None      # the uplink's gateway
    mac_commands: list[str] = []    # commands to run on macOS to route through us
