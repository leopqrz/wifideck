"""State writers must degrade (not 500) when the state dir isn't writable —
e.g. a root-owned /tmp/wifideck from a prior sudo run. Simulated by pointing the
path under a regular file so os.makedirs fails."""
from __future__ import annotations

from app.services.audit import AuditLog
from app.services.scope import ScopeList


def test_scope_degrades_when_unwritable(tmp_path):
    blocker = tmp_path / "blocker"
    blocker.write_text("x")  # a file where a dir is expected → save() OSErrors
    s = ScopeList(str(blocker / "scope.json"))
    t = s.add("02:00:00:00:00:01", "Net")  # must NOT raise
    assert t.bssid == "02:00:00:00:00:01"
    assert s.contains("02:00:00:00:00:01")  # in-memory scope still enforced


def test_audit_degrades_when_unwritable(tmp_path):
    blocker = tmp_path / "blk"
    blocker.write_text("x")
    a = AuditLog(str(blocker / "audit.jsonl"))
    e = a.record("deauth", "ok", target_bssid="02:00:00:00:00:01")  # must NOT raise
    assert e.action == "deauth"
    assert a.recent()[0].action == "deauth"  # in-memory fallback returns it
