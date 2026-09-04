"""Enumerate APs from tshark beacon output (macOS scan / imported-pcap networks)."""
from __future__ import annotations

from app.services.scan import parse_tshark_beacons


def test_parse_tshark_beacons_dedupes_and_maps_band():
    text = (
        "02:00:00:00:00:01\tMockNet-5G\t157\n"
        "02:00:00:00:00:02\tTestAP-2G\t6\n"
        "02:00:00:00:00:01\tMockNet-5G\t157\n"  # dup
        "\t\t\n"  # blank
    )
    nets = parse_tshark_beacons(text)
    assert len(nets) == 2  # deduped by BSSID
    five = next(n for n in nets if n.bssid == "02:00:00:00:00:01")
    assert five.ssid == "MockNet-5G" and five.channel == 157 and five.band == "5 GHz"
    two = next(n for n in nets if n.bssid == "02:00:00:00:00:02")
    assert two.band == "2.4 GHz"


def test_parse_tshark_beacons_hidden_ssid():
    nets = parse_tshark_beacons("02:00:00:00:00:03\t\t11\n")
    assert nets[0].ssid is None and nets[0].channel == 11
