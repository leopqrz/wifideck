"""HistoryStore — SQLite persistence for capture sessions and crack outcomes, so
past work survives a restart and is browsable. Additive: services still hold their
live state in memory; this records the durable record on the side.

sqlite3 is synchronous; calls are short and serialized with a lock, which is fine
at this volume (a handful of writes per session).
"""
from __future__ import annotations

import os
import sqlite3
import threading

from ..models.history import HistoryEntry
from ..models.session import CaptureSession


class HistoryStore:
    def __init__(self, path: str) -> None:
        self.path = path
        self._lock = threading.Lock()
        # Never let a DB problem (e.g. an unwritable dir) crash app startup — history
        # just degrades to a no-op if it can't open.
        self.ok = self._init()

    def _conn(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.path)
        conn.row_factory = sqlite3.Row
        return conn

    def _init(self) -> bool:
        try:
            os.makedirs(os.path.dirname(self.path) or ".", exist_ok=True)
            with self._lock, self._conn() as c:
                c.execute(
                    """CREATE TABLE IF NOT EXISTS sessions(
                        id TEXT PRIMARY KEY, started TEXT, stopped TEXT, mode TEXT,
                        channel INTEGER, target_bssid TEXT, handshake INTEGER,
                        pmkid INTEGER, pcap_available INTEGER)"""
                )
                c.execute(
                    """CREATE TABLE IF NOT EXISTS cracks(
                        session_id TEXT, engine TEXT, state TEXT, key TEXT, ended TEXT)"""
                )
            return True
        except (sqlite3.Error, OSError):
            return False

    def record_session(self, s: CaptureSession) -> None:
        if not self.ok:
            return
        try:
            with self._lock, self._conn() as c:
                c.execute(
                    """INSERT INTO sessions
                       (id, started, stopped, mode, channel, target_bssid, handshake, pmkid, pcap_available)
                       VALUES (?,?,?,?,?,?,?,?,?)
                       ON CONFLICT(id) DO UPDATE SET
                         stopped=excluded.stopped, mode=excluded.mode, channel=excluded.channel,
                         target_bssid=excluded.target_bssid, handshake=excluded.handshake,
                         pmkid=excluded.pmkid, pcap_available=excluded.pcap_available""",
                    (s.id, s.started, s.stopped, s.mode, s.channel, s.target_bssid,
                     int(s.handshake), int(s.pmkid), int(s.pcap_available)),
                )
        except sqlite3.Error:
            pass

    def record_crack(self, session_id: str, engine: str, state: str, key: str | None, ended: str) -> None:
        if not self.ok:
            return
        try:
            with self._lock, self._conn() as c:
                c.execute(
                    "INSERT INTO cracks (session_id, engine, state, key, ended) VALUES (?,?,?,?,?)",
                    (session_id, engine, state, key, ended),
                )
        except sqlite3.Error:
            pass

    def entries(self, limit: int = 100) -> list[HistoryEntry]:
        if not self.ok:
            return []
        try:
            with self._lock, self._conn() as c:
                rows = c.execute(
                    """SELECT s.*, c.engine AS crack_engine, c.state AS crack_state, c.key AS crack_key
                       FROM sessions s
                       LEFT JOIN cracks c
                         ON c.session_id = s.id
                         AND c.ended = (SELECT MAX(ended) FROM cracks WHERE session_id = s.id)
                       ORDER BY s.started DESC LIMIT ?""",
                    (limit,),
                ).fetchall()
        except sqlite3.Error:
            return []
        return [
            HistoryEntry(
                id=r["id"], started=r["started"], stopped=r["stopped"], mode=r["mode"],
                channel=r["channel"], target_bssid=r["target_bssid"],
                handshake=bool(r["handshake"]), pmkid=bool(r["pmkid"]),
                pcap_available=bool(r["pcap_available"]),
                crack_engine=r["crack_engine"], crack_state=r["crack_state"], crack_key=r["crack_key"],
            )
            for r in rows
        ]
