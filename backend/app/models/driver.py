"""Driver / DKMS info model."""
from __future__ import annotations

from pydantic import BaseModel


class DkmsModule(BaseModel):
    name: str
    version: str
    status: str          # added / built / installed


class DriverInfo(BaseModel):
    current: str | None          # e.g. rtw88_8812au or 88XXau
    kernel: str
    dkms: list[DkmsModule] = []
    recommended: str = "88XXau"
    using_recommended: bool = False
    recommended_buildable: bool = True   # does the DKMS driver support this kernel?
    kernel_max: str | None = None        # BUILD_EXCLUSIVE_KERNEL_MAX, if declared
    note: str | None = None
    install_hint: list[str] = []
