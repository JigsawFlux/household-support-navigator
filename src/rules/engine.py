# src/rules/engine.py
from src.household_profile import HouseholdProfile
from src.rules.base import RuleResult
from src.rules.pension_credit import check_pension_credit
from src.rules.council_tax_reduction import check_council_tax_reduction
from src.rules.warm_home_discount import check_warm_home_discount
from src.rules.healthy_start import check_healthy_start
from src.rules.household_support_fund import check_household_support_fund

_RULES = [
    check_pension_credit,
    check_council_tax_reduction,
    check_warm_home_discount,
    check_healthy_start,
    check_household_support_fund,
]


def screen_household(profile: HouseholdProfile) -> list[RuleResult]:
    """
    Deterministic screening pass — no LLM involvement.
    Returns one RuleResult per registered rule (HSN-025 stable contract).
    """
    return [rule(profile) for rule in _RULES]