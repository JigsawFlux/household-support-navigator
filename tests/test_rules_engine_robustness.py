import pytest

from src.household_profile import HouseholdProfile
from src.rules import engine as engine_module
from src.rules.base import RuleResult, InvalidRuleResultError


def _profile():
    return HouseholdProfile(
        age=70,
        household_size=1,
        region="England",
        annual_income=10_000,
        housing_status="owner",
        employment_status="retired",
    )


def test_screen_household_isolates_failing_rule(monkeypatch):
    def _broken_rule(profile):
        raise RuntimeError("boom")

    monkeypatch.setattr(engine_module, "_RULES", [_broken_rule, engine_module.check_pension_credit])
    results = engine_module.screen_household(_profile())

    assert len(results) == 2
    failed = next(r for r in results if r.confidence == "needs_review" and r.signpost_only)
    assert failed.eligible is False
    # second rule still ran normally
    assert any(r.entitlement == "Pension Credit" for r in results)


def test_rule_result_rejects_invalid_confidence():
    with pytest.raises(InvalidRuleResultError):
        RuleResult(
            entitlement="Test",
            eligible=True,
            reason="x",
            source_url="https://example.gov.uk",
            confidence="super-sure",
        )


def test_rule_result_accepts_valid_confidence():
    result = RuleResult(
        entitlement="Test",
        eligible=True,
        reason="x",
        source_url="https://example.gov.uk",
        confidence="high",
    )
    assert result.confidence == "high"