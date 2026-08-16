# src/household_profile.py
from dataclasses import dataclass, field
from typing import Optional


class ProfileValidationError(ValueError):
    """Raised when a HouseholdProfile fails validation with a user-safe message."""


_BLOCKED_FIELD_PATTERNS = ("account_number", "sort_code", "iban", "card_number", "bank_")


@dataclass
class HouseholdProfile:
    """
    Session-only household profile used for deterministic entitlement screening.
    No financial/bank data permitted. This object is never persisted by default.
    """
    age: int
    household_size: int
    region: str  # e.g. "England", "Scotland", "Wales", "Northern Ireland"
    annual_income: float
    housing_status: str  # "owner" | "renter" | "social_housing" | "other"
    employment_status: str  # "employed" | "self_employed" | "unemployed" | "retired" | "student"
    existing_benefits: list[str] = field(default_factory=list)

    def __post_init__(self):
        if self.age < 0 or self.age > 120:
            raise ProfileValidationError("Age must be between 0 and 120.")
        if self.household_size < 1:
            raise ProfileValidationError("Household size must be at least 1.")
        if self.annual_income < 0:
            raise ProfileValidationError("Income cannot be negative.")
        if not self.region:
            raise ProfileValidationError("Region is required.")
        if self.housing_status not in {"owner", "renter", "social_housing", "other"}:
            raise ProfileValidationError("Invalid housing status.")
        if self.employment_status not in {
            "employed", "self_employed", "unemployed", "retired", "student"
        }:
            raise ProfileValidationError("Invalid employment status.")

    def is_complex_case(self) -> bool:
        """Cases the deterministic rule engine should not resolve alone."""
        return self.employment_status == "self_employed"


def reject_if_financial_data_present(raw_payload: dict) -> None:
    """
    Guard used at the API/form boundary — never allow bank/account fields
    to enter the system, even if a client sends them.
    """
    for key in raw_payload:
        lowered = key.lower()
        if any(pattern in lowered for pattern in _BLOCKED_FIELD_PATTERNS):
            raise ProfileValidationError(
                "Financial/bank details are not accepted by this service."
            )