import pytest
from src.household_profile import HouseholdProfile, ProfileValidationError, reject_if_financial_data_present


def _valid_kwargs(**overrides):
    base = dict(
        age=70,
        household_size=1,
        region="England",
        annual_income=10_000,
        housing_status="owner",
        employment_status="retired",
    )
    base.update(overrides)
    return base


def test_valid_profile_constructs():
    profile = HouseholdProfile(**_valid_kwargs())
    assert profile.age == 70


def test_rejects_negative_income():
    with pytest.raises(ProfileValidationError):
        HouseholdProfile(**_valid_kwargs(annual_income=-1))


def test_rejects_invalid_housing_status():
    with pytest.raises(ProfileValidationError):
        HouseholdProfile(**_valid_kwargs(housing_status="mansion"))


def test_self_employed_is_complex_case():
    profile = HouseholdProfile(**_valid_kwargs(employment_status="self_employed"))
    assert profile.is_complex_case() is True


def test_rejects_bank_fields_in_raw_payload():
    with pytest.raises(ProfileValidationError):
        reject_if_financial_data_present({"account_number": "12345678"})


def test_allows_clean_payload():
    reject_if_financial_data_present({"age": 70, "region": "England"})