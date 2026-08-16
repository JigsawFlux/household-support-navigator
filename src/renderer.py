# src/renderer.py
"""
HSN-050: Prioritized checklist renderer.
"""
from __future__ import annotations

import html
from dataclasses import dataclass
from urllib.parse import urlparse

from src.rules.base import RuleResult
from src.escalation import EscalationReason, render_escalation_message

_CONFIDENCE_ORDER = {"high": 0, "medium": 1, "low": 2, "needs_review": 3}
_ALLOWED_SCHEMES = {"http", "https"}


@dataclass(frozen=True)
class ChecklistItem:
    entitlement: str
    status_label: str
    reason: str
    source_url: str
    confidence: str


def _sort_key(result: RuleResult):
    eligible_rank = 0 if result.eligible or result.signpost_only else 1
    confidence_rank = _CONFIDENCE_ORDER.get(result.confidence, 99)
    return (eligible_rank, confidence_rank, result.entitlement)


def build_checklist(results: list[RuleResult]) -> list[ChecklistItem]:
    ordered = sorted(results, key=_sort_key)
    items = []
    for r in ordered:
        if r.signpost_only:
            status_label = "ℹ️ Check locally"
        else:
            status_label = "✅ You may qualify" if r.eligible else "❌ Likely not eligible"
        items.append(
            ChecklistItem(
                entitlement=r.entitlement,
                status_label=status_label,
                reason=r.reason,
                source_url=r.source_url,
                confidence=r.confidence,
            )
        )
    return items


def render_cli(
    checklist: list[ChecklistItem],
    escalation_reasons: list[EscalationReason] | None = None,
) -> str:
    lines = ["Household Support Navigator — Your Checklist", "=" * 44, ""]

    for item in checklist:
        lines.append(f"{item.status_label}: {item.entitlement}")
        lines.append(f"  Why: {item.reason}")
        lines.append(f"  Confidence: {item.confidence}")
        lines.append(f"  More info: {item.source_url}")
        lines.append("")

    escalation_reasons = escalation_reasons or []
    escalation_text = render_escalation_message(escalation_reasons)
    if escalation_text:
        lines.append("-" * 44)
        lines.append(escalation_text)
        lines.append("")

    return "\n".join(lines)


def _safe_url(url: str) -> str:
    try:
        parsed = urlparse(url)
    except ValueError:
        return "#"
    if parsed.scheme not in _ALLOWED_SCHEMES:
        return "#"
    return html.escape(url, quote=True)


def render_html(
    checklist: list[ChecklistItem],
    escalation_reasons: list[EscalationReason] | None = None,
) -> str:
    rows = []
    for item in checklist:
        rows.append(
            "<tr>"
            f"<td>{html.escape(item.status_label)}</td>"
            f"<td>{html.escape(item.entitlement)}</td>"
            f"<td>{html.escape(item.reason)}</td>"
            f"<td>{html.escape(item.confidence)}</td>"
            f'<td><a href="{_safe_url(item.source_url)}" target="_blank" rel="noopener">Official source</a></td>'
            "</tr>"
        )

    escalation_reasons = escalation_reasons or []
    escalation_text = render_escalation_message(escalation_reasons)
    escalation_html = (
        f"<div class='escalation'><pre>{html.escape(escalation_text)}</pre></div>"
        if escalation_text else ""
    )

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <title>Household Support Navigator — Checklist</title>
  <style>
    body {{ font-family: system-ui, sans-serif; margin: 2rem; color: #1a1a1a; }}
    table {{ border-collapse: collapse; width: 100%; }}
    th, td {{ border: 1px solid #ddd; padding: 0.5rem; text-align: left; vertical-align: top; }}
    th {{ background: #f5f5f5; }}
    .escalation {{ margin-top: 2rem; padding: 1rem; background: #fff8e1; border: 1px solid #f0c14b; }}
  </style>
</head>
<body>
  <h1>Your Household Support Checklist</h1>
  <table>
    <thead>
      <tr><th>Status</th><th>Entitlement</th><th>Why</th><th>Confidence</th><th>Source</th></tr>
    </thead>
    <tbody>
      {''.join(rows)}
    </tbody>
  </table>
  {escalation_html}
</body>
</html>"""