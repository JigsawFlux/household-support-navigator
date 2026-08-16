# src/rules/base.py
from dataclasses import dataclass

_VALID_CONFIDENCE = {"high", "medium", "low", "needs_review"}


class InvalidRuleResultError(ValueError):
    """Raised when a RuleResult is constructed with an invalid confidence value."""

@dataclass(frozen=True)
class RuleResult:
    entitlement: str
    eligible: bool
    reason: str
    source_url: str
    confidence: str  # "high" | "medium" | "low" | "needs_review"
    signpost_only: bool = False  # True = informational link, not an eligibility claim

    def __post_init__(self):
        if self.confidence not in _VALID_CONFIDENCE:
            raise InvalidRuleResultError(
                f"Invalid confidence '{self.confidence}'. Must be one of {sorted(_VALID_CONFIDENCE)}."
            )