from src.household_profile import HouseholdProfile
from src.rules.base import RuleResult
from src.escalation import detect_complex_case, render_escalation_message


def _profile(**overrides):
    base = dict(
        age=40,
        household_size=2,
        region="England",
        annual_income=15_000,
        housing_status="renter",
        employment_status="employed",
        existing_benefits=[],
    )
    base.update(overrides)
    return HouseholdProfile(**base)


def test_no_escalation_for_simple_case():
    reasons = detect_complex_case(_profile(), results=[])
    assert reasons == []


def test_escalates_self_employed():
    reasons = detect_complex_case(_profile(employment_status="self_employed"), results=[])
    codes = [r.code for r in reasons]
    assert "self_employed" in codes


def test_escalates_large_household():
    reasons = detect_complex_case(_profile(household_size=5), results=[])
    codes = [r.code for r in reasons]
    assert "large_household" in codes


def test_escalates_low_confidence_match():
    results = [
        RuleResult(
            entitlement="Household Support Fund",
            eligible=True,
            reason="Signposted for local check.",
            source_url="https://example.gov.uk",
            confidence="needs_review",
        )
    ]
    reasons = detect_complex_case(_profile(), results)
    codes = [r.code for r in reasons]
    assert "low_confidence_match" in codes


def test_render_escalation_message_empty_when_no_reasons():
    assert render_escalation_message([]) == ""


def test_render_escalation_message_includes_advice_links():
    reasons = detect_complex_case(_profile(employment_status="self_employed"), results=[])
    message = render_escalation_message(reasons)
    assert "Citizens Advice" in message
    assert "MoneyHelper" in message
    assert "self-employed" in message.lower() or "self employed" in message.lower()