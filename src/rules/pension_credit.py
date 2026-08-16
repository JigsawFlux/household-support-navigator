# src/rules/pension_credit.py
from src.household_profile import HouseholdProfile
from src.rules.base import RuleResult

_SOURCE_URL = "https://www.gov.uk/pension-credit/eligibility"
_STATE_PENSION_AGE = 66  # simplified MVP constant; refine per DWP guidance
_SINGLE_INCOME_THRESHOLD = 11_960  # illustrative GOV.UK 2025/26 guarantee credit threshold (annualised)
_COUPLE_INCOME_THRESHOLD = 18_252


def check_pension_credit(profile: HouseholdProfile) -> RuleResult:
    if profile.age < _STATE_PENSION_AGE:
        return RuleResult(
            entitlement="Pension Credit",
            eligible=False,
            reason=f"Applicant is below State Pension age ({_STATE_PENSION_AGE}).",
            source_url=_SOURCE_URL,
            confidence="high",
        )

    threshold = _COUPLE_INCOME_THRESHOLD if profile.has_partner else _SINGLE_INCOME_THRESHOLD

    if profile.annual_income <= threshold:
        return RuleResult(
            entitlement="Pension Credit",
            eligible=True,
            reason=(
                f"Household income (£{profile.annual_income:,.0f}) is at or below the "
                f"Pension Credit guarantee threshold (£{threshold:,.0f})."
            ),
            source_url=_SOURCE_URL,
            confidence="medium",
        )

    return RuleResult(
        entitlement="Pension Credit",
        eligible=False,
        reason=f"Household income exceeds the Pension Credit threshold (£{threshold:,.0f}).",
        source_url=_SOURCE_URL,
        confidence="medium",
    )