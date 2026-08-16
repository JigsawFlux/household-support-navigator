# Household Support Navigator

[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![Rule Engine](https://img.shields.io/badge/eligibility-rule--based-green.svg)](#architecture)
[![Claude Sonnet](https://img.shields.io/badge/LLM-Claude%20Sonnet-orange.svg)](https://www.anthropic.com/)
[![Tests](https://img.shields.io/badge/tests-57%20passed-success.svg)](tests/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE.md)

> **One-Line Purpose:** Help UK households discover which benefits, grants, and bill-reduction schemes they may be entitled to — via deterministic rule-based screening, plain-language LLM explanation, and mandatory human-adviser escalation for complex cases.

Part of the **JigsawFlux** duty-of-care MVP portfolio, alongside `appointment-guardian`, `graduate-career-navigator`, and `verification-agent`.

---

## Executive Summary & Context

DWP and Policy in Practice estimate that **£23 billion in benefits goes unclaimed every year** in the UK. Pension Credit alone is unclaimed by around 800,000 eligible pensioners — many of whom are among the most financially vulnerable households in the country.

The barriers are not lack of entitlement. They are:

- **Complexity** — overlapping schemes with different thresholds, councils, and qualifying conditions
- **Trust** — people do not trust AI with money or government decisions ([JigsawFlux research.md](research.md): only 4–5% of surveyed users would trust AI to act autonomously on financial decisions)
- **Access** — those who most need help are least likely to navigate GOV.UK unaided

The **Household Support Navigator** addresses this gap as an advisory-only, radically transparent screening tool. It tells households what they may be entitled to, explains why in plain English, and points them to the official application channel — but it never submits anything, stores financial data, or makes a final eligibility determination.

---

## Key Features & Safety Principles

1. **Deterministic eligibility engine** — `src/rules/*.py` are pure functions returning a `RuleResult`. Eligibility is never determined by an LLM.
2. **LLM explains, not decides** — Claude rephrases rule engine output in plain, warm language, strictly bounded to the `reason` and `source_url` already computed.
3. **Mandatory escalation** — self-employed income, large households (5+), and low-confidence matches are always routed to Citizens Advice / MoneyHelper. This path cannot be bypassed.
4. **No financial data collection** — `reject_if_financial_data_present()` guards every input boundary. Bank account, sort code, IBAN, and card fields are refused at the schema level.
5. **No persistence without explicit consent** — sessions are in-memory by default. Disk persistence requires `HSN_STORAGE_CONSENT=true` and is still subject to the same financial-data guard.
6. **Deterministic fallback** — if the LLM call fails for any reason, a template-based explanation is generated automatically. The tool never blocks on an LLM failure.
7. **Signpost-only results** — discretionary local schemes (Household Support Fund) are rendered as signposts, not eligibility determinations, and never trigger the low-confidence escalation path.

---

## Architecture

### Core principle: rule engine decides, LLM explains

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

### Entitlement rules covered

| Rule module | Entitlement | Trigger |
|---|---|---|
| `pension_credit.py` | Pension Credit | Age ≥ 66 + income below guarantee threshold |
| `council_tax_reduction.py` | Council Tax Reduction | Income below per-household-size band |
| `warm_home_discount.py` | Warm Home Discount | Qualifying benefit or low income |
| `healthy_start.py` | Healthy Start | Qualifying benefit + pregnancy or child under 4 |
| `household_support_fund.py` | Household Support Fund | Signpost — discretionary, varies by council |

### Escalation triggers

| Trigger | Reason |
|---|---|
| `self_employed` | Self-employed income cannot be reliably screened by simplified rules |
| `large_household` | Households of 5+ often qualify for thresholds not modelled here |
| `low_confidence_match` | Eligible result with `low` or `needs_review` confidence |

---

## Setup

### 1. Requirements

Python 3.9 or later.

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 2. Configure environment

```bash
cp .env.example .env
```

Edit `.env`:

| Variable | Required | Description |
|---|---|---|
| `ANTHROPIC_API_KEY` | Yes (default provider) | [console.anthropic.com](https://console.anthropic.com) |
| `CLAUDE_MODEL` | No | Override the Claude model. Default: `claude-sonnet-4-6` |
| `LLM_PROVIDER` | No | `anthropic` (default) or `ollama` |
| `OLLAMA_MODEL` | Only if Ollama | Model name. Default: `llama3.1:8b` |
| `OLLAMA_BASE_URL` | Only if Ollama | Default: `http://localhost:11434` |
| `HSN_STORAGE_CONSENT` | No | Set `true` to enable optional session persistence |

### 3. Run tests

```bash
pytest -q
# → 57 passed in <1s
```

---

## Running

### End-to-end smoke test

`run_e2e.py` exercises the full pipeline for two sample households and saves CLI output, HTML output, and LLM explanations to `data/e2e_output/`:

```bash
python3 run_e2e.py
```

Example output:

```text
Running e2e test — model: claude-sonnet-4-6

--- pensioner_low_income ---
  Rules run: 5  |  Escalation triggers: 0
  LLM calls: 1  |  Latency: 18.10s
  Saved: pensioner_low_income_<ts>.txt, pensioner_low_income_<ts>.html, pensioner_low_income_<ts>_explanation.txt

--- young_family ---
  Rules run: 5  |  Escalation triggers: 0
  LLM calls: 1  |  Latency: 18.07s
  Saved: young_family_<ts>.txt, young_family_<ts>.html, young_family_<ts>_explanation.txt

Telemetry: telemetry_<uuid>.json
```

### Sample CLI checklist output

```text
Household Support Navigator — Your Checklist
============================================

✅ You may qualify: Pension Credit
  Why: Household income (£10,500) is at or below the Pension Credit guarantee threshold (£11,960).
  Confidence: medium
  More info: https://www.gov.uk/pension-credit/eligibility

✅ You may qualify: Council Tax Reduction
  Why: Household income (£10,500) is at or below the illustrative CTR threshold (£16,000).
  Confidence: medium
  More info: https://www.gov.uk/apply-council-tax-reduction

✅ You may qualify: Warm Home Discount
  Why: Household reports a qualifying means-tested benefit.
  Confidence: medium
  More info: https://www.gov.uk/the-warm-home-discount-scheme

ℹ️ Check locally: Household Support Fund
  More info: https://www.gov.uk/cost-of-living/find-help-in-your-area
```

---

## Key files

| File | Role |
|---|---|
| `src/household_profile.py` | `HouseholdProfile` dataclass + validation. `reject_if_financial_data_present()` guards all input boundaries. |
| `src/rules/engine.py` | Registers all rule modules; `screen_household()` runs them deterministically with per-rule fault isolation. |
| `src/rules/*.py` | One pure function per entitlement returning a frozen `RuleResult`. |
| `src/explainer.py` | LLM-based plain-language explanation + document checklist. Falls back to a template on LLM failure. |
| `src/escalation.py` | `detect_complex_case()` — flags self-employment, large households, and low-confidence matches for human-adviser routing. |
| `src/renderer.py` | `build_checklist()` sorts results (eligible-high-confidence first); `render_cli()` / `render_html()` produce the output. |
| `src/session_store.py` | In-memory by default. `persist_to_disk()` requires `HSN_STORAGE_CONSENT=true` and rejects financial fields. |
| `shared/llm.py` | LLM factory — `get_llm()` reads `LLM_PROVIDER` and returns the appropriate LangChain chat model. |
| `shared/telemetry.py` | Tracks `run_id`, latency, entitlement hit counts, and escalation rate. No household-identifying data included. |

---

## Project Roadmap

| Milestone | Scope | Status |
|---|---|---|
| **M0** Foundation | Project skeleton, config contract | **Done** |
| **M1** Data Model | `HouseholdProfile` dataclass + validation | **Done** |
| **M2** Rule Engine | Pension Credit, CTR, WHD, Healthy Start, HSF | **Done** |
| **M3** Explanation Layer | Plain-language LLM explainer + document guidance | **Done** |
| **M4** Escalation & Safety | Complex-case detector + escalation output | **Done** (immigration status trigger pending) |
| **M5** Output / UX | CLI + HTML checklist renderer | **Done** |
| **M6** Privacy & Data Controls | Session-only storage + consent gate | **Done** |
| **M7** Telemetry | Per-run metrics, weekly review export | **Done** |
| **M8** Test Suite | Unit + scenario tests (57 passing) | **Done** |
| **M9 — Pre-pilot** | Verify GOV.UK thresholds · Expand pilot council links · Go/No-Go checklist | **In progress** |

---

## Governance Hard Limits

These constraints are structural and must not be removed:

1. **No autonomous claim submission** — the agent produces a checklist with official links only; a human always submits.
2. **No financial/bank data collection** — enforced by `reject_if_financial_data_present()` in both `household_profile.py` and `session_store.py`.
3. **Eligibility is rule-based, not LLM-guessed** — `explainer.py` may only rephrase `RuleResult` fields already computed by the rule engine.
4. **Complex cases always escalate** — `detect_complex_case()` must never be bypassed for self-employment, large households, or low-confidence matches.
5. **No persistence without explicit consent** — `HSN_STORAGE_CONSENT=true` is required; defaults to session-only/in-memory.

---

## Known Pre-Pilot Limitations

Rule thresholds in `src/rules/*.py` are illustrative approximations of GOV.UK guidance, not verified current-year figures. Before any pilot use, reconcile against live GOV.UK/DWP data:

- Pension Credit guarantee credit thresholds (`pension_credit.py`)
- Council Tax Reduction income bands (`council_tax_reduction.py`)
- Warm Home Discount low-income threshold (`warm_home_discount.py`)
- Pilot council links in `household_support_fund.py` (currently Manchester, Birmingham, Leeds placeholders only)

---

## License

MIT — see [LICENSE.md](LICENSE.md).

*Part of the JigsawFlux open-source suite for health tech, humanitarian response, and digital duty-of-care.*
