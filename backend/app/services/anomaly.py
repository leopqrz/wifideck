"""AnomalyService — device risk / anomaly scoring over observed stations.

This is the *statistical / heuristic* layer: it flags trackable devices and
behavioural outliers from features we already extract (randomized-MAC, probe
history, association state). It is the foundation a trained fingerprinting model
(device/OS classification, learned per-environment baselines) would build on — that
model runs on the Jetson/AWS with collected data and is a later step. The scoring
here is honest rules, not a pretend model.
"""
from __future__ import annotations

from ..models.anomaly import Anomaly
from ..models.station import Station
from .stations import StationService


def score_station(s: Station) -> tuple[int, list[str]]:
    score = 0
    reasons: list[str] = []
    if s.vendor and s.vendor != "randomized":
        score += 1
        reasons.append("stable (non-randomized) MAC — trackable across networks")
    if len(s.probes) >= 5:
        score += 2
        reasons.append(f"probing for {len(s.probes)} SSIDs — leaks location/network history")
    elif len(s.probes) >= 1 and not s.bssid:
        score += 1
        reasons.append("actively searching for known networks (unassociated)")
    if not s.bssid and s.packets >= 30:
        score += 1
        reasons.append("chatty but not associated with any AP")
    return score, reasons


class AnomalyService:
    def __init__(self, stations: StationService) -> None:
        self.stations = stations

    def anomalies(self, threshold: int = 2) -> list[Anomaly]:
        out: list[Anomaly] = []
        for s in self.stations.list():
            score, reasons = score_station(s)
            if score >= threshold:
                out.append(Anomaly(
                    mac=s.mac, vendor=s.vendor, score=score,
                    level="high" if score >= 4 else "medium",
                    reasons=reasons, probes=s.probes,
                ))
        return sorted(out, key=lambda a: a.score, reverse=True)
