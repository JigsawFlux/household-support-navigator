from src.household_profile import HouseholdProfile
from src.rules.engine import screen_household


def test_pension_credit_eligible_case():
    profile = HouseholdProfile(
        age=70,
        household_size=1,
        region="England",
        annual_income=9_000,
        housing_status="owner",
        employment_status="retired",
    )
    results = screen_household(profile)
    pc = next(r for r in results if r.entitlement == "Pension Credit")
    assert pc.eligible is True
    assert pc.source_url.startswith("https://www.gov.uk")


def test_pension_credit_ineligible_below_age():
    profile = HouseholdProfile(
        age=40,
        household_size=1,
        region="England",
        annual_income=5_000,
        housing_status="renter",
        employment_status="employed",
    )
    results = screen_household(profile)
    pc = next(r for r in results if r.entitlement == "Pension Credit")
    assert pc.eligible is False
    assert "State Pension age" in pc.reason