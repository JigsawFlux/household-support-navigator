# src/rules/base.py
from dataclasses import dataclass


@dataclass
class RuleResult:
    entitlement: str
    eligible: bool
    reason: str
    source_url: str
    confidence: str  # "high" | "medium" | "needs_review"