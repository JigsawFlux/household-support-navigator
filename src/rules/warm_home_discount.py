# src/rules/warm_home_discount.py
from src.household_profile import HouseholdProfile
from src.rules.base import RuleResult

_SOURCE_URL = "https://www.gov.uk/the-warm-home-discount-scheme"
_QUALIFYING_BENEFITS = {
    "pension_credit_guarantee",
    "universal_credit",
    "income_support",
    "esa",
    "jsa",
}
_LOW_INCOME_THRESHOLD = 19_000


def check_warm_home_discount(profile: HouseholdProfile) -> RuleResult:
    has_qualifying_benefit = any(
        b.lower() in _QUALIFYING_BENEFITS for b in profile.existing_benefits
    )

    if has_qualifying_benefit:
        return RuleResult(
            entitlement="Warm Home Discount",
            eligible=True,
            reason=(
                "Household reports a qualifying means-tested benefit, which typically "
                "triggers automatic eligibility for the Warm Home Discount rebate."
            ),
            source_url=_SOURCE_URL,
            confidence="medium",
        )

    if profile.annual_income <= _LOW_INCOME_THRESHOLD:
        return RuleResult(
            entitlement="Warm Home Discount",
            eligible=True,
            reason=(
                f"Household income (£{profile.annual_income:,.0f}) is within the "
                f"illustrative low-income band (£{_LOW_INCOME_THRESHOLD:,.0f}) often used "
                "for the 'broader group' qualification. Check with your energy supplier."
            ),
            source_url=_SOURCE_URL,
            confidence="low",
        )

    return RuleResult(
        entitlement="Warm Home Discount",
        eligible=False,
        reason="No qualifying benefit reported and household income exceeds the low-income band.",
        source_url=_SOURCE_URL,
        confidence="medium",
    )