# src/rules/household_support_fund.py
from src.household_profile import HouseholdProfile
from src.rules.base import RuleResult

_GENERIC_SOURCE_URL = "https://www.gov.uk/cost-of-living/find-help-in-your-area"

# Pilot council index (HSN-090). Start small; expand after pilot validation.
_PILOT_COUNCIL_LINKS = {
    "manchester": "https://www.manchester.gov.uk/householdsupportfund",
    "birmingham": "https://www.birmingham.gov.uk/householdsupportfund",
    "leeds": "https://www.leeds.gov.uk/householdsupportfund",
}


def check_household_support_fund(profile: HouseholdProfile) -> RuleResult:
    """
    Always signposts — never determines eligibility, since Household Support Fund
    schemes are discretionary and vary council-by-council.
    """
    region_key = profile.region.strip().lower()
    council_url = _PILOT_COUNCIL_LINKS.get(region_key, _GENERIC_SOURCE_URL)

    return RuleResult(
        entitlement="Household Support Fund",
        eligible=True,  # "eligible to check" — discretionary, not a determination
        reason=(
            "Household Support Fund schemes are run locally and vary by council. "
            "This is a signpost to check current local eligibility and available grants — "
            "it is not a guaranteed entitlement."
        ),
        source_url=council_url,
        confidence="needs_review",
    )