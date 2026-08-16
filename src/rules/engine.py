import logging

from src.household_profile import HouseholdProfile
from src.rules.base import RuleResult
from src.rules.pension_credit import check_pension_credit
from src.rules.council_tax_reduction import check_council_tax_reduction
from src.rules.warm_home_discount import check_warm_home_discount
from src.rules.healthy_start import check_healthy_start
from src.rules.household_support_fund import check_household_support_fund

logger = logging.getLogger(__name__)

_RULES = (
    check_pension_credit,
    check_council_tax_reduction,
    check_warm_home_discount,
    check_healthy_start,
    check_household_support_fund,
)


def _safe_error_result(rule_name: str, exc: Exception) -> RuleResult:
    logger.error("rules.engine: rule %s failed: %s", rule_name, exc, exc_info=True)
    return RuleResult(
        entitlement=rule_name,
        eligible=False,
        reason="This check could not be completed automatically. Please check the official site.",
        source_url="https://www.gov.uk/check-benefits-financial-support",
        confidence="needs_review",
        signpost_only=True,
    )


def screen_household(profile: HouseholdProfile) -> list[RuleResult]:
    """
    Deterministic screening pass — no LLM involvement.
    A failing rule does not abort the whole screening; it is replaced with a
    safe 'needs_review' signpost result so the user still gets partial output.
    """
    results = []
    for rule in _RULES:
        try:
            results.append(rule(profile))
        except Exception as exc:  # noqa: BLE001 - intentional broad catch, isolate per-rule failure
            results.append(_safe_error_result(rule.__name__, exc))
    return results