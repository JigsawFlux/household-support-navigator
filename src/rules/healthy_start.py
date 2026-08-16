# src/rules/healthy_start.py
from src.household_profile import HouseholdProfile
from src.rules.base import RuleResult

_SOURCE_URL = "https://www.healthystart.nhs.uk/"
_QUALIFYING_BENEFITS = {
    "universal_credit",
    "child_tax_credit",
    "income_support",
    "esa",
    "jsa",
    "pension_credit_guarantee",
}
_MAX_QUALIFYING_AGE_FOR_PARENT = 45  # loose proxy; real rule is about being pregnant or having a child under 4


def check_healthy_start(profile: HouseholdProfile) -> RuleResult:
    has_qualifying_benefit = any(
        b.lower() in _QUALIFYING_BENEFITS for b in profile.existing_benefits
    )

    if not has_qualifying_benefit:
        return RuleResult(
            entitlement="Healthy Start",
            eligible=False,
            reason="No qualifying means-tested benefit reported.",
            source_url=_SOURCE_URL,
            confidence="medium",
        )

    if profile.household_size < 2:
        return RuleResult(
            entitlement="Healthy Start",
            eligible=False,
            reason=(
                "Healthy Start is for pregnant women or households with children under 4 — "
                "a single-person household does not typically qualify."
            ),
            source_url=_SOURCE_URL,
            confidence="low",
        )

    return RuleResult(
        entitlement="Healthy Start",
        eligible=True,
        reason=(
            "Household reports a qualifying benefit and more than one member — "
            "if you are pregnant or have a child under 4, you may be eligible. "
            "Confirm exact eligibility on the official site."
        ),
        source_url=_SOURCE_URL,
        confidence="low",
    )