# src/rules/council_tax_reduction.py
from src.household_profile import HouseholdProfile
from src.rules.base import RuleResult

_SOURCE_URL = "https://www.gov.uk/apply-council-tax-reduction"

# Simplified MVP income bands per household size (illustrative; actual scheme
# rules are set per local council and vary by region).
_INCOME_THRESHOLDS = {
    1: 16_000,
    2: 20_000,
    3: 24_000,
}
_DEFAULT_THRESHOLD = 28_000


def check_council_tax_reduction(profile: HouseholdProfile) -> RuleResult:
    threshold = _INCOME_THRESHOLDS.get(profile.household_size, _DEFAULT_THRESHOLD)

    if profile.housing_status == "owner" and profile.annual_income > threshold:
        return RuleResult(
            entitlement="Council Tax Reduction",
            eligible=False,
            reason=(
                f"Household income (£{profile.annual_income:,.0f}) exceeds the "
                f"illustrative threshold (£{threshold:,.0f}) for this household size."
            ),
            source_url=_SOURCE_URL,
            confidence="medium",
        )

    if profile.annual_income <= threshold:
        return RuleResult(
            entitlement="Council Tax Reduction",
            eligible=True,
            reason=(
                f"Household income (£{profile.annual_income:,.0f}) is at or below the "
                f"illustrative Council Tax Reduction threshold (£{threshold:,.0f}) for "
                f"this household size. Exact reduction amount depends on your council's scheme."
            ),
            source_url=_SOURCE_URL,
            confidence="medium",
        )

    return RuleResult(
        entitlement="Council Tax Reduction",
        eligible=False,
        reason=f"Household income exceeds the illustrative threshold (£{threshold:,.0f}).",
        source_url=_SOURCE_URL,
        confidence="medium",
    )