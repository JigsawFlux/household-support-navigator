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

    if not profile.is_pregnant_or_young_child:
        return RuleResult(
            entitlement="Healthy Start",
            eligible=False,
            reason=(
                "Healthy Start is for pregnant women or households with a child under 4 — "
                "this was not indicated for this household."
            ),
            source_url=_SOURCE_URL,
            confidence="medium",
        )

    return RuleResult(
        entitlement="Healthy Start",
        eligible=True,
        reason=(
            "Household reports a qualifying benefit and a pregnancy or child under 4 — "
            "you are likely eligible. Confirm exact eligibility on the official site."
        ),
        source_url=_SOURCE_URL,
        confidence="medium",
    )