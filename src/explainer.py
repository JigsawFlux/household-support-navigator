# src/explainer.py
"""
HSN-030/031: Plain-language explanation + document-gathering guidance.

Strict constraint: the LLM explains and summarizes RuleResult objects produced
by the deterministic rule engine (src/rules/engine.py). It must never invent
or override an eligibility decision — every explanation is grounded in the
rule's `reason` and `source_url`.
"""
from __future__ import annotations

import logging
from langchain_core.messages import SystemMessage, HumanMessage

from shared.llm import get_llm
from shared.telemetry import TelemetryCallback, RunTelemetry
from src.rules.base import RuleResult

logger = logging.getLogger(__name__)

_SYSTEM = (
    "You are a benefits communication assistant for UK households. You will be given "
    "a list of entitlement check results, each already determined by a deterministic "
    "rule engine (not by you). Your job is ONLY to:\n"
    "1. Explain each result in plain, warm, non-judgmental English.\n"
    "2. List the documents typically needed to apply for each ELIGIBLE entitlement.\n"
    "3. Always reference the official source link provided — never invent a new one.\n\n"
    "You must NOT:\n"
    "- Change or contradict any eligible/ineligible determination given to you.\n"
    "- Claim certainty beyond what the 'confidence' field states.\n"
    "- Give financial, legal, or tax advice.\n"
    "- Invent thresholds, amounts, or eligibility rules not present in the input.\n\n"
    "If confidence is 'needs_review' or 'low', clearly say the person should confirm "
    "on the official site or with a free adviser (Citizens Advice / MoneyHelper).\n\n"
    "Return plain text, organised as one short section per entitlement."
)

_DOCUMENT_HINTS = {
    "Pension Credit": ["Proof of income (pension statements)", "National Insurance number", "Bank details for the claim form (not stored by this tool)"],
    "Council Tax Reduction": ["Council Tax bill", "Proof of income", "Proof of savings"],
    "Warm Home Discount": ["Energy supplier account reference", "Proof of qualifying benefit (if applicable)"],
    "Healthy Start": ["NHS number", "Proof of qualifying benefit", "Proof of pregnancy (if applicable)"],
    "Household Support Fund": ["Check your local council's page — requirements vary"],
}


def _format_results_for_prompt(results: list[RuleResult]) -> str:
    lines = []
    for r in results:
        lines.append(
            f"- Entitlement: {r.entitlement}\n"
            f"  Eligible: {r.eligible}\n"
            f"  Reason: {r.reason}\n"
            f"  Source: {r.source_url}\n"
            f"  Confidence: {r.confidence}\n"
            f"  Suggested documents: {', '.join(_DOCUMENT_HINTS.get(r.entitlement, ['See official site']))}"
        )
    return "\n".join(lines)


def _extract_text(response) -> str:
    """
    Anthropic (and other providers) may return content as a list of content
    blocks (e.g. [{"type": "text", "text": "..."}]) rather than a plain string.
    str(list) would produce a Python repr, not usable text — extract properly.
    """
    content = response.content
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts = []
        for block in content:
            if isinstance(block, dict) and "text" in block:
                parts.append(block["text"])
            elif hasattr(block, "text"):
                parts.append(block.text)
        return "".join(parts)
    return str(content)


def explain_results(results: list[RuleResult], telemetry: RunTelemetry | None = None) -> str:
    """
    HSN-030: Generate plain-language explanations bound strictly to rule engine output.
    HSN-031: Includes document-gathering guidance per entitlement.

    Falls back to a deterministic template (no LLM) if the LLM call fails,
    so the tool never blocks on an explanation failure.
    """
    prompt = _format_results_for_prompt(results)
    callbacks = [TelemetryCallback(telemetry)] if telemetry else []

    try:
        llm = get_llm(temperature=0.0)
        response = llm.invoke(
            [
                SystemMessage(content=_SYSTEM),
                HumanMessage(content=f"Entitlement check results:\n\n{prompt}"),
            ],
            config={"callbacks": callbacks},
        )
        content = _extract_text(response)
        if not content.strip():
            raise ValueError("Empty LLM response")
        return content.strip()
    except Exception:
        logger.warning("explainer: LLM call failed, falling back to template output", exc_info=True)
        return _fallback_template(results)


def _fallback_template(results: list[RuleResult]) -> str:
    sections = []
    for r in results:
        status = "You may qualify" if r.eligible else "You likely do not qualify"
        docs = _DOCUMENT_HINTS.get(r.entitlement, ["See official site"])
        sections.append(
            f"{r.entitlement}\n"
            f"{status} — {r.reason}\n"
            f"Confidence: {r.confidence}\n"
            f"More info: {r.source_url}\n"
            f"Documents you may need: {', '.join(docs)}\n"
        )
    return "\n".join(sections)