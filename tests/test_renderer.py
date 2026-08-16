from src.rules.base import RuleResult
from src.escalation import EscalationReason
from src.renderer import build_checklist, render_cli, render_html


def _results():
    return [
        RuleResult(
            entitlement="Council Tax Reduction",
            eligible=False,
            reason="Income too high.",
            source_url="https://www.gov.uk/apply-council-tax-reduction",
            confidence="medium",
        ),
        RuleResult(
            entitlement="Pension Credit",
            eligible=True,
            reason="Income below threshold.",
            source_url="https://www.gov.uk/pension-credit/eligibility",
            confidence="high",
        ),
        RuleResult(
            entitlement="Household Support Fund",
            eligible=True,
            reason="Local signpost.",
            source_url="https://example.gov.uk/hsf",
            confidence="needs_review",
        ),
    ]


def test_build_checklist_orders_eligible_before_ineligible():
    checklist = build_checklist(_results())
    labels = [item.entitlement for item in checklist]
    assert labels.index("Pension Credit") < labels.index("Council Tax Reduction")


def test_build_checklist_orders_by_confidence_within_eligible():
    checklist = build_checklist(_results())
    eligible_items = [i for i in checklist if i.status_label.startswith("✅")]
    assert eligible_items[0].entitlement == "Pension Credit"  # high confidence first
    assert eligible_items[1].entitlement == "Household Support Fund"  # needs_review last


def test_render_cli_includes_all_entitlements():
    checklist = build_checklist(_results())
    output = render_cli(checklist)
    assert "Pension Credit" in output
    assert "Council Tax Reduction" in output
    assert "Household Support Fund" in output


def test_render_cli_includes_escalation_when_present():
    checklist = build_checklist(_results())
    reasons = [EscalationReason(code="self_employed", description="Needs review.")]
    output = render_cli(checklist, reasons)
    assert "Citizens Advice" in output


def test_render_cli_omits_escalation_when_absent():
    checklist = build_checklist(_results())
    output = render_cli(checklist, [])
    assert "Citizens Advice" not in output


def test_render_html_contains_table_and_links():
    checklist = build_checklist(_results())
    html = render_html(checklist)
    assert "<table>" in html
    assert 'href="https://www.gov.uk/pension-credit/eligibility"' in html


def test_render_html_includes_escalation_block_when_present():
    checklist = build_checklist(_results())
    reasons = [EscalationReason(code="large_household", description="Needs review.")]
    html = render_html(checklist, reasons)
    assert "escalation" in html
    assert "Citizens Advice" in html