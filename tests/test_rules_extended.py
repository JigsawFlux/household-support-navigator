from src.household_profile import HouseholdProfile
from src.rules.healthy_start import check_healthy_start
from src.rules.household_support_fund import check_household_support_fund


def _profile(**overrides):
    base = dict(
        age=30,
        household_size=2,
        region="England",
        annual_income=12_000,
        housing_status="renter",
        employment_status="employed",
        existing_benefits=[],
    )
    base.update(overrides)
    return HouseholdProfile(**base)


def test_healthy_start_requires_pregnancy_or_young_child():
    result = check_healthy_start(_profile(existing_benefits=["universal_credit"], is_pregnant_or_young_child=False))
    assert result.eligible is False


def test_healthy_start_eligible_with_benefit_and_flag():
    result = check_healthy_start(_profile(existing_benefits=["universal_credit"], is_pregnant_or_young_child=True))
    assert result.eligible is True


def test_household_support_fund_is_signpost_not_eligible():
    result = check_household_support_fund(_profile(region="Manchester"))
    assert result.eligible is False
    assert result.signpost_only is True
