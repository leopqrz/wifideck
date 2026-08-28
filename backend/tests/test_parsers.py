"""Unit tests for the pure wireless-output parsers."""
from __future__ import annotations

from app.services import parsers
from app.services.fixtures import IW_DEV, IW_LINK, IP_ADDR


def test_parse_iw_dev():
    devs = parsers.parse_iw_dev(IW_DEV)
    assert devs == [{"interface": "wlan0", "type": "managed"}]


def test_parse_iw_dev_empty():
    assert parsers.parse_iw_dev("") == []


def test_parse_iw_link():
    link = parsers.parse_iw_link(IW_LINK)
    assert link["ssid"] == "MockNet-5G"
    assert link["signal_dbm"] == -42
    assert link["tx_bitrate_mbps"] == 585.0
    assert link["freq_mhz"] == 5785


def test_parse_iw_link_not_connected():
    assert parsers.parse_iw_link("Not connected.") == {}


def test_parse_ip_addr():
    assert parsers.parse_ip_addr(IP_ADDR) == "192.0.2.10/24"
    assert parsers.parse_ip_addr("no address here") is None


def test_driver_from_path():
    assert parsers.driver_from_path("/sys/bus/usb/drivers/rtw88_8812au") == "rtw88_8812au"
    assert parsers.driver_from_path("") is None


def test_band_for_freq():
    assert parsers.band_for_freq(2412) == "2.4 GHz"
    assert parsers.band_for_freq(5785) == "5 GHz"
    assert parsers.band_for_freq(None) is None
