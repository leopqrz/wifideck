"""ReportService — aggregate what the tool has seen/done into a shareable,
self-contained HTML assessment report (open in a browser, print to PDF)."""
from __future__ import annotations

import html
from datetime import datetime, timezone

from ..models.report import Report, ReportNetwork, ReportSummary
from .audit import AuditLog
from .history import HistoryStore
from .known import KnownNetworks
from .posture import classify_security
from .scope import ScopeList


def gather(
    history: HistoryStore,
    audit: AuditLog,
    scope: ScopeList,
    known: KnownNetworks,
    version: str,
) -> Report:
    sessions = history.entries(500)
    nets = known.list()
    report_nets: list[ReportNetwork] = []
    for n in nets:
        p = classify_security(n.security)
        report_nets.append(ReportNetwork(
            ssid=n.ssid, bssid=n.bssid, band=n.band, channel=n.channel,
            security=n.security, posture_label=p.label, posture_tone=p.tone,
            posture_note=p.note,
        ))
    audits = audit.recent(500)
    scopes = scope.list()
    summary = ReportSummary(
        networks=len(nets),
        sessions=len(sessions),
        handshakes=sum(1 for s in sessions if s.handshake),
        pmkids=sum(1 for s in sessions if s.pmkid),
        cracked=sum(1 for s in sessions if s.crack_key),
        audit_actions=len(audits),
        scoped=len(scopes),
    )
    return Report(
        generated=datetime.now(timezone.utc).isoformat(timespec="seconds"),
        version=version, summary=summary, networks=report_nets,
        sessions=sessions, audit=audits, scope=scopes,
    )


def _e(v: object) -> str:
    return html.escape(str(v)) if v is not None else "—"


_TONE = {"ok": "#37e0a0", "warn": "#ffb84d", "crit": "#ff6b6b", "muted": "#8aa"}


def render_html(r: Report) -> str:
    s = r.summary
    tiles = "".join(
        f'<div class="tile"><div class="num">{v}</div><div class="lbl">{k}</div></div>'
        for k, v in [
            ("networks", s.networks), ("captures", s.sessions),
            ("handshakes", s.handshakes), ("PMKIDs", s.pmkids),
            ("keys cracked", s.cracked), ("audited actions", s.audit_actions),
        ]
    )

    net_rows = "".join(
        f"<tr><td>{_e(n.ssid or '<hidden>')}</td><td class='mono'>{_e(n.bssid)}</td>"
        f"<td class='num'>{_e(n.channel)}</td><td>{_e(n.band)}</td>"
        f"<td><span class='pill' style='color:{_TONE.get(n.posture_tone, '#8aa')}'>"
        f"{_e(n.posture_label)}</span><div class='note'>{_e(n.posture_note)}</div></td></tr>"
        for n in r.networks
    ) or "<tr><td colspan=5 class='empty'>no networks recorded</td></tr>"

    ses_rows = "".join(
        f"<tr><td class='mono'>{_e(x.id)}</td><td>{_e(x.mode)}</td>"
        f"<td class='mono'>{_e(x.target_bssid)}</td>"
        f"<td>{'✓' if x.handshake else '—'}</td><td>{'✓' if x.pmkid else '—'}</td>"
        f"<td class='mono key'>{_e(x.crack_key) if x.crack_key else '—'}</td></tr>"
        for x in r.sessions
    ) or "<tr><td colspan=6 class='empty'>no capture sessions</td></tr>"

    audit_rows = "".join(
        f"<tr><td class='mono'>{_e(a.timestamp)}</td><td>{_e(a.action)}</td>"
        f"<td class='mono'>{_e(a.target_bssid)}</td>"
        f"<td class='{a.result}'>{_e(a.result)}</td><td>{_e(a.detail)}</td></tr>"
        for a in r.audit
    ) or "<tr><td colspan=5 class='empty'>no actions logged</td></tr>"

    scope_rows = "".join(
        f"<li class='mono'>{_e(t.bssid)}<span class='note'>{_e(t.ssid or '')}</span></li>"
        for t in r.scope
    ) or "<li class='empty'>none</li>"

    return f"""<!doctype html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>WiFiDeck assessment — {_e(r.generated[:10])}</title>
<style>
  :root {{ color-scheme: light dark; }}
  * {{ box-sizing: border-box; }}
  body {{ margin:0; font:14px/1.5 ui-monospace,"SF Mono",Menlo,monospace;
    background:#0b0e12; color:#c9d4dd; padding:32px; }}
  h1 {{ font-size:22px; margin:0 0 2px; color:#eaf2f7; letter-spacing:.02em; }}
  h2 {{ font-size:12px; text-transform:uppercase; letter-spacing:.14em; color:#2fd6d6;
    margin:32px 0 10px; border-bottom:1px solid #1c2530; padding-bottom:6px; }}
  .sub {{ color:#6b7d8a; margin:0 0 24px; font-size:12px; }}
  .tiles {{ display:grid; grid-template-columns:repeat(auto-fit,minmax(120px,1fr)); gap:10px; }}
  .tile {{ border:1px solid #1c2530; border-radius:10px; padding:14px; background:#11161c; }}
  .tile .num {{ font-size:26px; color:#eaf2f7; font-weight:600; }}
  .tile .lbl {{ font-size:11px; text-transform:uppercase; letter-spacing:.1em; color:#6b7d8a; }}
  table {{ width:100%; border-collapse:collapse; font-size:12.5px; }}
  th {{ text-align:left; color:#6b7d8a; font-weight:400; text-transform:uppercase;
    letter-spacing:.08em; font-size:10px; padding:6px 10px; border-bottom:1px solid #1c2530; }}
  td {{ padding:7px 10px; border-bottom:1px solid #141b22; vertical-align:top; }}
  .mono {{ font-family:inherit; color:#9fb0bd; }}
  .num {{ text-align:right; font-variant-numeric:tabular-nums; }}
  .pill {{ font-weight:700; font-size:11px; }}
  .note {{ color:#6b7d8a; font-size:11px; }}
  .key {{ color:#37e0a0; }}
  .ok {{ color:#37e0a0; }} .refused {{ color:#ffb84d; }} .error {{ color:#ff6b6b; }}
  .empty {{ color:#4b5a66; font-style:italic; }}
  ul {{ list-style:none; padding:0; margin:0; display:flex; flex-wrap:wrap; gap:8px; }}
  li {{ border:1px solid #1c2530; border-radius:6px; padding:4px 10px; background:#11161c; }}
  li .note {{ margin-left:8px; }}
  footer {{ margin-top:36px; color:#4b5a66; font-size:11px; border-top:1px solid #1c2530; padding-top:12px; }}
  @media print {{ body {{ background:#fff; color:#111; padding:0; }}
    .tile,li,table th {{ border-color:#ccc; }} .tile {{ background:#f7f7f7; }} }}
</style></head><body>
<h1>WiFiDeck — Wi-Fi assessment</h1>
<p class="sub">generated {_e(r.generated)} · v{_e(r.version)} · localhost tool</p>

<h2>Summary</h2>
<div class="tiles">{tiles}</div>

<h2>Networks &amp; security posture</h2>
<table><thead><tr><th>SSID</th><th>BSSID</th><th>CH</th><th>Band</th><th>Posture</th></tr></thead>
<tbody>{net_rows}</tbody></table>

<h2>Capture sessions</h2>
<table><thead><tr><th>Session</th><th>Mode</th><th>Target</th><th>Handshake</th><th>PMKID</th><th>Cracked key</th></tr></thead>
<tbody>{ses_rows}</tbody></table>

<h2>Authorized targets (scope)</h2>
<ul>{scope_rows}</ul>

<h2>Audit trail</h2>
<table><thead><tr><th>Time</th><th>Action</th><th>Target</th><th>Result</th><th>Detail</th></tr></thead>
<tbody>{audit_rows}</tbody></table>

<footer>Authorized testing only — actions above were performed on networks the operator
declared they own or are permitted to assess. WiFiDeck binds to localhost; this report
is generated locally and not transmitted anywhere.</footer>
</body></html>"""
