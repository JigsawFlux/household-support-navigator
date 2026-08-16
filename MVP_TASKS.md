# MVP_TASKS — Household Support Navigator

Delivery board for v1, aligned to: **Plan → Execute → Adapt → Follow-up** (no autonomous submission).

## Status Legend
- `TODO` not started · `DOING` in progress · `DONE` complete · `BLOCKED` waiting dependency

---

## Milestone 0 — Foundation

### HSN-001 — Project skeleton
- **Status:** DONE
- **Scope:** `src/`, `tests/`, `configs/`, `data/`, `docs/`
- **Acceptance:** runnable entrypoint; README run instructions

### HSN-002 — Config + env contract
- **Status:** DONE
- **Scope:** thresholds per entitlement, region list, escalation rules
- **Acceptance:** `.env.example` present; fails fast on missing required vars

---

## Milestone 1 — Data Model

### HSN-010 — `HouseholdProfile` dataclass
- **Status:** DONE
- **Fields:** income, age, household_size, region, existing_benefits, housing_status, employment_status
- **Acceptance:** validation errors are explicit and user-safe

### HSN-011 — State machine
- **Status:** TODO
- **Scope:** `PROFILE_CAPTURED → SCREENED → PRESENTED → USER_FEEDBACK → {DISMISSED|IN_PROGRESS|ESCALATED} → CLAIMED`
- **Acceptance:** every transition logged; invalid transitions rejected

---

## Milestone 2 — Rule Engine (deterministic, not LLM)

### HSN-020 — Pension Credit rule
- **Status:** DONE
- **Acceptance:** cites official GOV.UK threshold source; unit tested against known eligible/ineligible cases

### HSN-021 — Council Tax Reduction rule
- **Status:** DOING
- **Acceptance:** region-aware; cites source; tested
- **Note:** Rule implemented with illustrative thresholds; region-aware per-council thresholds not yet done

### HSN-022 — Warm Home Discount rule
- **Status:** DONE
- **Acceptance:** cites source; tested

### HSN-023 — Healthy Start rule
- **Status:** DONE
- **Acceptance:** cites source; tested

### HSN-024 — Household Support Fund signposting
- **Status:** DONE
- **Scope:** per-council link lookup (start with 3–5 pilot councils)
- **Acceptance:** falls back to generic GOV.UK signpost if council not indexed

### HSN-025 — Rule engine adapter/interface
- **Status:** DONE
- **Acceptance:** each rule module returns `{eligible, reason, source_url, confidence}` — stable contract

---

## Milestone 3 — Explanation Layer (Claude, bounded)

### HSN-030 — Plain-language explainer tool
- **Status:** DONE
- **Scope:** Claude explains rule engine output only — never invents eligibility
- **Acceptance:** explanation always cites the rule's `source_url`; no unsupported claims test

### HSN-031 — Document-gathering guidance
- **Status:** DONE
- **Acceptance:** returns checklist of documents per matched entitlement

---

## Milestone 4 — Escalation & Safety

### HSN-040 — Complex-case detector
- **Status:** DOING
- **Scope:** self-employment, multiple households, immigration status, disputed benefit history
- **Note:** self-employment and large household triggers implemented; immigration status not yet modelled
- **Acceptance:** always routes to `ESCALATED` with Citizens Advice / MoneyHelper links; never resolved by agent

### HSN-041 — Escalation output template
- **Status:** DONE
- **Acceptance:** clear "this needs a human adviser" message; no guessed eligibility given

---

## Milestone 5 — Output / UX

### HSN-050 — Prioritized checklist renderer
- **Status:** DONE
- **Template:** Entitlement → Why you may qualify → Source → Deadline → Next step
- **Acceptance:** CLI and static HTML both supported; consistent across both

---

## Milestone 6 — Privacy & Data Controls

### HSN-060 — Session-only storage enforcement
- **Status:** DONE
- **Acceptance:** no persistence by default; explicit consent flag required for any save

### HSN-061 — No financial/bank data collection
- **Status:** DONE
- **Acceptance:** schema validation rejects bank/account-like fields if submitted

---

## Milestone 7 — Telemetry & Evaluation

### HSN-070 — Run telemetry
- **Status:** DONE
- **Track:** latency, rule match counts, escalation rate, entitlement distribution
- **Acceptance:** one telemetry record per run with `run_id`

### HSN-071 — Weekly review report
- **Status:** DONE
- **Acceptance:** exportable report of escalation reasons + rule hit rates for tuning

---

## Milestone 8 — Test Suite

### HSN-080 — Rule engine unit tests
- **Status:** DONE
- **Acceptance:** minimum 3 cases per rule (eligible, ineligible, boundary)

### HSN-081 — Explanation contract tests
- **Status:** DONE
- **Acceptance:** every explanation includes source citation; test fails otherwise

### HSN-082 — Escalation path tests
- **Status:** DONE
- **Acceptance:** complex-case inputs always escalate, never guessed

### HSN-083 — Privacy tests
- **Status:** DONE
- **Acceptance:** bank/account fields rejected; no persistence without consent flag

---

## Milestone 9 — Pilot Readiness

### HSN-090 — Pilot council selection (3–5)
- **Status:** DOING
- **Acceptance:** Household Support Fund data indexed for pilot councils only

### HSN-091 — Go/No-Go checklist
- **Status:** TODO
- **Acceptance:** all MVP acceptance criteria signed off before wider rollout

---

## Suggested Execution Order

1. HSN-001, HSN-002
2. HSN-010, HSN-011
3. HSN-020..025
4. HSN-030, HSN-031
5. HSN-040, HSN-041
6. HSN-050
7. HSN-060, HSN-061
8. HSN-070, HSN-071
9. HSN-080..083
10. HSN-090, HSN-091

---

## Definition of Done (MVP)

- All Milestones 1–9 tasks `DONE`
- Every recommendation cites a rule + official source (no LLM-guessed eligibility)
- Complex cases always escalate, never resolved by the agent
- No financial/bank data collected; no persistence without consent
- Pilot council data indexed and checklist output validated end-to-end