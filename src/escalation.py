# src/escalation.py
"""
HSN-040/041: Complex-case detection and escalation output.
"""
from dataclasses import dataclass

from src.household_profile import HouseholdProfile
from src.rules.base import RuleResult

_CITIZENS_ADVICE_URL = "https://www.citizensadvice.org.uk/benefits/"
_MONEYHELPER_URL = "https://www.moneyhelper.org.uk/en/benefits"


@dataclass(frozen=True)
class EscalationReason:
    code: str
    description: str


def detect_complex_case(profile: HouseholdProfile, results: list[RuleResult]) -> list[EscalationReason]:
    reasons: list[EscalationReason] = []

    if profile.is_complex_case():
        reasons.append(
            EscalationReason(
                code="self_employed",
                description=(
                    "Self-employed income is assessed differently for means-tested "
                    "benefits and cannot be reliably screened by this tool."
                ),
            )
        )

    if profile.household_size >= 5:
        reasons.append(
            EscalationReason(
                code="large_household",
                description=(
                    "Larger households often qualify for additional or different "
                    "thresholds not covered by this tool's simplified rules."
                ),
            )
        )

    # Signpost-only results (e.g. Household Support Fund) are informational and
    # must never trigger this escalation path — only real eligible determinations.
    low_confidence_hits = [
        r for r in results
        if r.eligible and r.confidence in {"low", "needs_review"} and not r.signpost_only
    ]
    if low_confidence_hits:
        names = ", ".join(r.entitlement for r in low_confidence_hits)
        reasons.append(
            EscalationReason(
                code="low_confidence_match",
                description=(
                    f"Possible eligibility for {names} was flagged with low confidence "
                    "and should be confirmed by an adviser."
                ),
            )
        )

    return reasons


def render_escalation_message(reasons: list[EscalationReason]) -> str:
    if not reasons:
        return ""

    lines = [
        "This case needs a human adviser to confirm eligibility. Here's why:",
        "",
    ]
    for r in reasons:
        lines.append(f"- {r.description}")

    lines.extend([
        "",
        "Free, independent advice is available from:",
        f"- Citizens Advice: {_CITIZENS_ADVICE_URL}",
        f"- MoneyHelper: {_MONEYHELPER_URL}",
        "",
        "This tool has not made a final decision on your entitlements — "
        "please confirm with one of the services above.",
    ])
    return "\n".join(lines)