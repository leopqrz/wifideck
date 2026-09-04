"""StatusService — assembles a Status snapshot from adapter tooling.

Uses the CommandRunner seam, so it works identically against real hardware and
against mock fixtures. All parsing is delegated to the pure functions in parsers.py.
"""
from __future__ import annotations

from ..models.status import Health, Status
from . import parsers
from .runner import CommandRunner

USB_ID = "0bda:8812"  # ALFA AWUS036ACH / RTL8812AU


class StatusService:
    def __init__(self, runner: CommandRunner) -> None:
        self.runner = runner

    async def _macos_snapshot(self) -> Status:
        """Status for the native-macOS libusb radio (a monitor/injection device)."""
        from .radio import MacosRtl8812auBackend

        info = await MacosRtl8812auBackend().info()
        present = info.present
        return Status(
            usb_present=present,
            driver=info.driver,          # "libusb (rtl8812au-macos)"
            interface="libusb",
            mode="MONITOR" if present else None,  # it's a monitor-only radio
            operstate="up" if present else "down",
            ssid=None, ip4=None, signal_dbm=None, tx_bitrate_mbps=None,
            freq_mhz=None, band=None,
            health=Health.OK if present else Health.DISCONNECTED,
            health_detail=None if present else "Plug the ALFA into macOS (native RF backend).",
        )

    async def snapshot(self) -> Status:
        # On the native-macOS RF backend there is no iw/nmcli/sysfs — report the
        # libusb radio's state instead of a false "disconnected".
        from ..config import settings
        from .radio import resolve_backend_name

        if resolve_backend_name(settings.mock, settings.radio_backend) == "macos-rtl8812au":
            return await self._macos_snapshot()

        usb_present = (await self.runner.run(["lsusb", "-d", USB_ID])).ok

        devs = parsers.parse_iw_dev((await self.runner.run(["iw", "dev"])).stdout)
        iface = devs[0]["interface"] if devs else None
        mode = devs[0]["type"].upper() if devs and devs[0].get("type") else None

        driver = operstate = ssid = ip4 = band = None
        signal = freq = None
        bitrate = None

        if iface:
            driver = parsers.driver_from_path(
                (await self.runner.run(
                    ["readlink", "-f", f"/sys/class/net/{iface}/device/driver"]
                )).stdout
            )
            operstate = (
                await self.runner.run(["cat", f"/sys/class/net/{iface}/operstate"])
            ).stdout.strip() or None

            link = parsers.parse_iw_link(
                (await self.runner.run(["iw", "dev", iface, "link"])).stdout
            )
            ssid = link.get("ssid")
            signal = link.get("signal_dbm")
            bitrate = link.get("tx_bitrate_mbps")
            freq = link.get("freq_mhz")
            band = parsers.band_for_freq(freq)

            ip4 = parsers.parse_ip_addr(
                (await self.runner.run(["ip", "-o", "-4", "addr", "show", iface])).stdout
            )

        if not usb_present:
            health, detail = Health.DISCONNECTED, "Adapter not on the USB bus."
        elif not iface:
            health, detail = Health.DEGRADED, "Adapter present but no interface."
        else:
            health, detail = Health.OK, None

        return Status(
            usb_present=usb_present,
            driver=driver,
            interface=iface,
            mode=mode,
            operstate=operstate,
            ssid=ssid,
            ip4=ip4,
            signal_dbm=signal,
            tx_bitrate_mbps=bitrate,
            freq_mhz=freq,
            band=band,
            health=health,
            health_detail=detail,
        )
