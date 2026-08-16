from src.household_profile import HouseholdProfile
from src.rules.council_tax_reduction import check_council_tax_reduction
from src.rules.warm_home_discount import check_warm_home_discount
from src.rules.healthy_start import check_healthy_start
from src.rules.household_support_fund import check_household_support_fund
from src.rules.engine import screen_household


def _profile(**overrides):
    base = dict(
        age=40,
        household_size=2,
        region="Manchester",
        annual_income=15_000,
        housing_status="renter",
        employment_status="employed",
        existing_benefits=[],
    )
    base.update(overrides)
    return HouseholdProfile(**base)


def test_council_tax_reduction_eligible_low_income():
    result = check_council_tax_reduction(_profile(annual_income=10_000, household_size=1))
    assert result.eligible is True


def test_council_tax_reduction_ineligible_high_income():
    result = check_council_tax_reduction(_profile(annual_income=50_000, household_size=1, housing_status="owner"))
    assert result.eligible is False


def test_warm_home_discount_eligible_via_benefit():
    result = check_warm_home_discount(_profile(existing_benefits=["universal_credit"]))
    assert result.eligible is True
    assert result.confidence == "medium"


def test_warm_home_discount_eligible_via_low_income():
    result = check_warm_home_discount(_profile(annual_income=15_000, existing_benefits=[]))
    assert result.eligible is True
    assert result.confidence == "low"


def test_warm_home_discount_ineligible():
    result = check_warm_home_discount(_profile(annual_income=30_000, existing_benefits=[]))
    assert result.eligible is False


def test_healthy_start_requires_benefit():
    result = check_healthy_start(_profile(existing_benefits=[]))
    assert result.eligible is False


def test_healthy_start_eligible_with_benefit_and_household():
    result = check_healthy_start(_profile(existing_benefits=["universal_credit"], household_size=3))
    assert result.eligible is True


def test_household_support_fund_uses_pilot_council_link():
    result = check_household_support_fund(_profile(region="Manchester"))
    assert "manchester.gov.uk" in result.source_url


def test_household_support_fund_falls_back_to_generic_link():
    result = check_household_support_fund(_profile(region="Somewhereville"))
    assert result.source_url.endswith("find-help-in-your-area")


def test_screen_household_returns_all_rules():
    results = screen_household(_profile())
    entitlements = {r.entitlement for r in results}
    assert entitlements == {
        "Pension Credit",
        "Council Tax Reduction",
        "Warm Home Discount",
        "Healthy Start",
        "Household Support Fund",
    }