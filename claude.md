# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project context

Part of the **JigsawFlux** duty-of-care MVP portfolio (alongside `appointment-guardian`, `graduate-career-navigator`, `verification-agent`). Addresses the single largest untouched public concern in `research.md`: **Cost of Living (88%)**.

## One-line purpose

Help UK households discover which benefits, grants, and bill-reduction schemes they may be entitled to — via deterministic rule-based screening, plain-language LLM explanation, and mandatory human-adviser escalation for complex cases. The agent never submits claims or stores financial data.

## Setup

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # fill in ANTHROPIC_API_KEY, or set LLM_PROVIDER=ollama
```

## Running tests

```bash
pytest -q
```

## Architecture

### Core principle: rule engine decides, LLM explains

Eligibility is **never** determined by an LLM. `src/rules/*.py` are deterministic functions returning a `RuleResult(entitlement, eligible, reason, source_url, confidence)`. The LLM (`src/explainer.py`) only rephrases these results in plain language — bound strictly to the given `reason`/`source_url`, with a template-based fallback if the LLM call fails.

### Flow

```
HouseholdProfile → screen_household() → [RuleResult, ...]
                                              │
                        ┌─────────────────────┼─────────────────────┐
                        ▼                     ▼                     ▼
              explain_results()   detect_complex_case()    build_checklist()
                (src/explainer)      (src/escalation)         (src/renderer)
                                              │                     │
                                              ▼                     ▼
                                render_escalation_message()   render_cli() / render_html()
```

### Key files

- **`src/household_profile.py`** — `HouseholdProfile` dataclass + validation. `reject_if_financial_data_present()` guards against bank/account fields at any input boundary.
- **`src/rules/engine.py`** — registers all rule modules (`pension_credit`, `council_tax_reduction`, `warm_home_discount`, `healthy_start`, `household_support_fund`); `screen_household()` runs them all deterministically.
- **`src/explainer.py`** — LLM-based plain-language explanation + document checklist, via `shared/llm.py`'s `get_llm()`. Never invents eligibility; falls back to a template on LLM failure.
- **`src/escalation.py`** — `detect_complex_case()` flags self-employment, large households (5+), and low-confidence matches for mandatory human-adviser routing (Citizens Advice / MoneyHelper). Never resolved by the agent.
- **`src/renderer.py`** — `build_checklist()` sorts results (eligible-high-confidence first), `render_cli()` / `render_html()` produce the "Entitlement → Why → Source → Next step" output format.
- **`src/session_store.py`** — in-memory-only by default. `persist_to_disk()` requires `HSN_STORAGE_CONSENT=true` and rejects financial fields via `reject_if_financial_data_present()`.
- **`shared/llm.py`** — LLM factory (same pattern as `agentic-patterns`): `get_llm(temperature)` reads `LLM_PROVIDER` (`anthropic` default, or `ollama`).
- **`shared/telemetry.py`** — `TelemetryRecorder` tracks `run_id`, latency, entitlement hit counts, escalation rate. `export_json()` writes a review report (no household-identifying data included).

## Governance hard limits (do not remove)

1. **No autonomous claim submission** — the agent only produces a checklist with official links; a human always submits.
2. **No financial/bank data collection** — enforced by `reject_if_financial_data_present()` in both `household_profile.py` and `session_store.py`.
3. **Eligibility is rule-based, not LLM-guessed** — `explainer.py` must only rephrase `RuleResult` fields already computed.
4. **Complex cases always escalate** — `escalation.py`'s `detect_complex_case()` must never be bypassed for self-employment, large households, or low-confidence matches.
5. **No persistence without explicit consent** — `HSN_STORAGE_CONSENT=true` env var required; defaults to session-only/in-memory.

## Known simplifications (MVP-stage, not production thresholds)

Rule thresholds in `src/rules/*.py` (e.g. Pension Credit income bands, Council Tax Reduction bands) are **illustrative approximations** of GOV.UK guidance, not verified current-year figures. Before any pilot use, these must be reconciled against live GOV.UK/Turn2us data — see `research.md` §4 for the source feasibility table.

## Remaining pre-pilot work

- **HSN-090**: Verify and expand pilot council links in `src/rules/household_support_fund.py` (currently Manchester/Birmingham/Leeds placeholders).
- **HSN-091**: Go/No-Go checklist in `MVP_TASKS.md` before wider rollout.
- verify the Pension Credit/Council Tax/Warm Home Discount threshold constants against current GOV.UK figures before treating this as pilot-ready — that's the one substantive gap left before HSN-090/091.