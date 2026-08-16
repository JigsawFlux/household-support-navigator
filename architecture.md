# UK Household Support Navigator — Technical Architecture Guide

> **Audience:** Software Engineers, Solution Architects, Local Authority Technical Teams, and Open Source Contributors seeking to adopt, configure, or extend the UK Household Support Navigator.

---

## 1. Architectural Overview & Design Philosophy

The **Household Support Navigator** is built on a fundamental architectural tenet: **Deterministic Rule Engines decide; Large Language Models explain; Human Advisers resolve edge cases.**

```mermaid
flowchart LR
    A[Household Profile] --> B[Deterministic Rule Engine]
    B -->|RuleResult Objects| C[Explanation Layer Claude / Ollama]
    B -->|RuleResult Objects| D[Escalation Detector]
    B -->|RuleResult Objects| E[Checklist Renderer]
    D -->|EscalationReasons| E
    C -->|Plain-language text| F[CLI / HTML Output]
    E -->|Formatted checklist| F
```

### Core Architecture Tenets

1. **Deterministic Eligibility (No AI Hallucination):** Entitlement eligibility is calculated exclusively via pure, unit-tested Python rule functions. An LLM is never permitted to make, modify, or override an eligibility calculation.
2. **Strict LLM Boundary:** The LLM's role is strictly confined to plain-language translation and document checklists based on computed `RuleResult` objects. If the LLM provider fails, times out, or returns an empty response, the system seamlessly falls back to pre-compiled deterministic templates.
3. **Duty-of-Care & Human Escalation:** Any complex scenario (e.g. self-employment, large households, low-confidence rules) triggers mandatory escalation signposting to regulated human advice services (Citizens Advice, MoneyHelper).
4. **Zero-Trust Privacy & Anti-Surveillance:** Input payloads are strictly filtered to reject financial credentials (bank accounts, sort codes, card numbers, IBANs). Storage is ephemeral/in-memory by default; disk persistence requires explicit opt-in consent (`HSN_STORAGE_CONSENT=true`).

---

## 2. C4 Model Architecture

### 2.1 Level 1: System Context Diagram

The System Context diagram illustrates how the Household Support Navigator fits into the broader UK welfare and digital advice ecosystem.

```mermaid
C4Context
    title System Context Diagram — UK Household Support Navigator

    Person(resident, "Household / Resident", "A UK resident looking for cost-of-living support, benefits, or grants.")
    Person(advisor, "Caseworker / Local Advisor", "A local authority, charity, or community support worker assisting a household.")

    System(hsn, "Household Support Navigator", "Screens household attributes against official English entitlement rules, generates clear action checklists, and flags complex cases.")

    System_Ext(govuk, "GOV.UK / DWP / NHS", "Official government portals for statutory benefit applications (Pension Credit, Healthy Start, Council Tax Reduction).")
    System_Ext(advice_orgs, "Citizens Advice / MoneyHelper", "Free, regulated human advice services for complex or disputed welfare cases.")
    System_Ext(councils, "Local Authority Portals", "Discretionary Household Support Fund (HSF) and local Council Tax Reduction schemes.")
    System_Ext(llm_service, "LLM Service (Anthropic / Ollama)", "Inference provider for plain-language translation and personalized document checklists.")

    Rel(resident, hsn, "Inputs non-financial household profile; receives prioritised checklist", "CLI / Web UI")
    Rel(advisor, hsn, "Assists resident with profile evaluation and guidance", "CLI / Web UI")
    Rel(hsn, llm_service, "Requests plain-language explanations of deterministic rule results", "HTTPS / REST")
    Rel(hsn, govuk, "Signposts user to official application forms and statutory guidelines", "HTTPS Deep Links")
    Rel(hsn, councils, "Signposts user to localized HSF discretionary funds", "HTTPS Deep Links")
    Rel(hsn, advice_orgs, "Escalates complex cases for human intervention", "HTTPS Deep Links / Phone")
```

---

### 2.2 Level 2: Container Diagram

The Container diagram illustrates the runtime components, data boundaries, and third-party integrations.

```mermaid
C4Container
    title Container Diagram — UK Household Support Navigator

    Person(user, "User / Caseworker", "Interacts via terminal or web interface")

    Container_Boundary(c1, "Household Support Navigator Application") {
        Component(entrypoint, "Entrypoint / Interface", "Python (run_e2e.py / CLI / Web Adapter)", "Captures user profile and orchestrates the screening and rendering pipeline.")
        Component(guard, "Data Ingestion & Boundary Guard", "src/household_profile.py", "Validates input and strictly sanitizes/rejects any banking or sensitive financial fields.")
        Component(rules_engine, "Deterministic Rules Engine", "src/rules/engine.py", "Runs isolated entitlement checks against statutory thresholds without LLM involvement.")
        Component(escalation_svc, "Escalation Service", "src/escalation.py", "Evaluates complexity triggers and formats human referral paths.")
        Component(explainer_svc, "Explanation Service", "src/explainer.py", "Coordinates prompt assembly, LLM invocation via LangChain, and deterministic fallback.")
        Component(renderer_svc, "Checklist Renderer", "src/renderer.py", "Formats sorted results into terminal text or accessible HTML.")
        Component(session_store, "Session Store", "src/session_store.py", "In-memory store with consent-gated persistence to disk.")
        Component(telemetry_svc, "Telemetry Recorder", "shared/telemetry.py", "Captures execution latencies, match rates, and escalation counts without PII.")
    }

    System_Ext(anthropic_api, "Anthropic Claude API", "External LLM provider (claude-sonnet-4-6) via LangChain.")
    System_Ext(ollama_api, "Local Ollama Instance", "Local air-gapped LLM provider (llama3.1:8b) for private/offline deployments.")
    ContainerDb(local_storage, "Consented Storage", "Local JSON files (data/)", "Optional disk persistence enabled only when HSN_STORAGE_CONSENT=true.")

    Rel(user, entrypoint, "Submits profile, views checklist", "CLI / Web")
    Rel(entrypoint, guard, "Validates raw input", "Python Calls")
    Rel(guard, rules_engine, "Passes validated HouseholdProfile", "In-Memory")
    Rel(rules_engine, escalation_svc, "Supplies RuleResults for complexity scan", "In-Memory")
    Rel(rules_engine, explainer_svc, "Supplies RuleResults for plain-language summary", "In-Memory")
    Rel(explainer_svc, anthropic_api, "Calls API (if LLM_PROVIDER=anthropic)", "HTTPS")
    Rel(explainer_svc, ollama_api, "Calls local endpoint (if LLM_PROVIDER=ollama)", "HTTP")
    Rel(rules_engine, renderer_svc, "Passes RuleResults", "In-Memory")
    Rel(escalation_svc, renderer_svc, "Passes EscalationReasons", "In-Memory")
    Rel(renderer_svc, entrypoint, "Returns CLI / HTML outputs", "In-Memory")
    Rel(explainer_svc, entrypoint, "Returns plain-language explanation string", "In-Memory")
    Rel(entrypoint, session_store, "Saves session if consent granted", "In-Memory")
    Rel(session_store, local_storage, "Writes JSON if consented", "File I/O")
    Rel(entrypoint, telemetry_svc, "Logs run metrics", "In-Memory")
```

---

### 2.3 Level 3: Component Diagram (Core Processing Pipeline)

The Component diagram details the internal structural decomposition of `src/` and `shared/`.

```mermaid
C4Component
    title Component Diagram — Core Processing & Extension Modules

    Container_Boundary(b1, "Household Support Navigator Core") {
        Component(profile_class, "HouseholdProfile", "src/household_profile.py", "Dataclass holding household parameters (age, income, region, benefits, housing status).")
        Component(financial_filter, "reject_if_financial_data_present()", "src/household_profile.py", "Scans raw dictionary payloads and raises ProfileValidationError on financial keys.")
        
        Component(engine, "screen_household()", "src/rules/engine.py", "Iterates registered rules; encapsulates failures with _safe_error_result.")
        
        Component(rule_pc, "check_pension_credit", "src/rules/pension_credit.py", "Pension Credit guarantee threshold check.")
        Component(rule_ctr, "check_council_tax_reduction", "src/rules/council_tax_reduction.py", "Income band evaluation for local council tax reduction.")
        Component(rule_whd, "check_warm_home_discount", "src/rules/warm_home_discount.py", "Qualifying benefit and low-income energy rebate check.")
        Component(rule_hs, "check_healthy_start", "src/rules/healthy_start.py", "Food voucher scheme check for pregnancy/young children on benefits.")
        Component(rule_hsf, "check_household_support_fund", "src/rules/household_support_fund.py", "Signposts to local authority discretionary funds (signpost_only=True).")
        
        Component(escalate, "detect_complex_case()", "src/escalation.py", "Flags self-employment, large households (5+), and low-confidence determinations.")
        Component(explainer, "explain_results()", "src/explainer.py", "Formats prompts, invokes LLM, and falls back to _fallback_template.")
        Component(renderer, "build_checklist()", "src/renderer.py", "Sorts by (eligible, confidence) and generates CLI/HTML representations.")
        Component(llm_factory, "get_llm()", "shared/llm.py", "Instantiates ChatAnthropic or ChatOllama dynamically.")
        Component(telemetry, "TelemetryRecorder", "shared/telemetry.py", "Aggregates latency and hit rates per run_id.")
    }

    Rel(profile_class, financial_filter, "Guarded by")
    Rel(engine, profile_class, "Consumes")
    Rel(engine, rule_pc, "Executes")
    Rel(engine, rule_ctr, "Executes")
    Rel(engine, rule_whd, "Executes")
    Rel(engine, rule_hs, "Executes")
    Rel(engine, rule_hsf, "Executes")
    Rel(escalate, profile_class, "Inspects profile")
    Rel(escalate, engine, "Inspects RuleResults")
    Rel(explainer, engine, "Takes RuleResults")
    Rel(explainer, llm_factory, "Invokes chat model")
    Rel(renderer, engine, "Formats RuleResults")
    Rel(renderer, escalate, "Embeds EscalationReasons")
```

---

## 3. Data Flow & Sequence Diagram

This sequence diagram illustrates the lifecycle of a screening request from input to rendered checklist and telemetry export.

```mermaid
sequenceDiagram
    autonumber
    actor User as User / Caseworker
    participant Entry as Entrypoint / Pipeline
    participant Guard as Profile Guard
    participant Engine as Rules Engine
    participant Rules as Individual Rule Modules
    participant Escalate as Escalation Service
    participant Explainer as Explainer (LLM / Fallback)
    participant Renderer as Checklist Renderer
    participant Telem as Telemetry Recorder

    User->>Entry: Submit household parameters
    Entry->>Guard: reject_if_financial_data_present(payload)
    Guard-->>Entry: Sanitized / Validated
    Entry->>Guard: Instantiate HouseholdProfile
    
    Entry->>Telem: start_run() -> RunTelemetry(run_id)
    
    Entry->>Engine: screen_household(profile)
    loop For each registered rule
        Engine->>Rules: check_rule(profile)
        alt Rule succeeds
            Rules-->>Engine: RuleResult(...)
        else Rule throws Exception
            Engine-->>Engine: _safe_error_result() (confidence="needs_review", signpost_only=True)
        end
    end
    Engine-->>Entry: list[RuleResult]
    Entry->>Telem: record_results(telemetry, results)

    Entry->>Escalate: detect_complex_case(profile, results)
    Escalate-->>Entry: list[EscalationReason]
    Entry->>Telem: record_escalation(telemetry, escalation_reasons)

    Entry->>Explainer: explain_results(results, telemetry)
    alt LLM API available
        Explainer->>Explainer: Invoke LLM with strict grounding prompt
        Explainer-->>Entry: LLM plain-language text
    else LLM API fails / times out
        Explainer->>Explainer: _fallback_template(results)
        Explainer-->>Entry: Template-based plain text
    end
    
    Entry->>Telem: finish_run(telemetry)

    Entry->>Renderer: build_checklist(results)
    Entry->>Renderer: render_cli(checklist, escalation_reasons) / render_html(...)
    Renderer-->>Entry: Formatted checklist & escalation notice
    
    Entry-->>User: Display prioritised action checklist
```

---

## 4. Extension & Adoption Guide

The Household Support Navigator is intentionally modular. Below are practical guides for extending the platform.

### 4.1 Extension Point 1: Adding a New Entitlement Rule

All rules must implement a standard signature and return an immutable `RuleResult` object.

```mermaid
classDiagram
    class RuleResult {
        +str entitlement
        +bool eligible
        +str reason
        +str source_url
        +str confidence
        +bool signpost_only
        +__post_init__()
    }
```

#### Step 1: Create the rule module in `src/rules/`
Create a new file, e.g., `src/rules/attendance_allowance.py`:

```python
# src/rules/attendance_allowance.py
from src.household_profile import HouseholdProfile
from src.rules.base import RuleResult

_SOURCE_URL = "https://www.gov.uk/attendance-allowance/eligibility"
_MIN_AGE = 66

def check_attendance_allowance(profile: HouseholdProfile) -> RuleResult:
    """
    Evaluates potential eligibility for Attendance Allowance (disability/care need for State Pension age).
    """
    if profile.age < _MIN_AGE:
        return RuleResult(
            entitlement="Attendance Allowance",
            eligible=False,
            reason=f"Applicant must be State Pension age ({_MIN_AGE}+).",
            source_url=_SOURCE_URL,
            confidence="high",
        )

    # If your profile tracks disability or health conditions:
    return RuleResult(
        entitlement="Attendance Allowance",
        eligible=True,
        reason="Applicant meets the age threshold. If you have a physical or mental disability requiring care, you may claim.",
        source_url=_SOURCE_URL,
        confidence="medium",
    )
```

#### Step 2: Register the rule in `src/rules/engine.py`

```python
# In src/rules/engine.py
from src.rules.attendance_allowance import check_attendance_allowance

_RULES = (
    check_pension_credit,
    check_council_tax_reduction,
    check_warm_home_discount,
    check_healthy_start,
    check_household_support_fund,
    check_attendance_allowance,  # <-- Added here
)
```

#### Step 3: Add document guidance in `src/explainer.py`

```python
# In src/explainer.py _DOCUMENT_HINTS
_DOCUMENT_HINTS = {
    # ...
    "Attendance Allowance": [
        "National Insurance number",
        "GP / specialist contact details",
        "List of medications and care requirements",
    ],
}
```

#### Step 4: Write unit tests in `tests/`
Create `tests/test_attendance_allowance.py` covering:
- Eligible boundary case
- Ineligible boundary case
- Source URL presence and confidence validation

---

### 4.2 Extension Point 2: Supporting Local Council Schemes (Discretionary Funds)

Councils administer their own localized Household Support Fund allocations and Council Tax Support bands.

To add new local authorities:
1. Update `_PILOT_COUNCIL_LINKS` in `src/rules/household_support_fund.py`:
   ```python
   _PILOT_COUNCIL_LINKS = {
       "manchester": "https://www.manchester.gov.uk/householdsupportfund",
       "birmingham": "https://www.birmingham.gov.uk/householdsupportfund",
       "leeds": "https://www.leeds.gov.uk/householdsupportfund",
       "newcastle": "https://www.newcastle.gov.uk/householdsupportfund",
       "bristol": "https://www.bristol.gov.uk/householdsupportfund",
   }
   ```
2. When configuring for production, migrate these lookups into an external configuration file (e.g. `configs/councils.json`) to allow non-developer caseworkers to update links without touching code.

---

### 4.3 Extension Point 3: Adding Custom Escalation Triggers

Complex circumstances that cannot be accurately determined by deterministic rule thresholds must escalate to human advisers.

To add a new trigger (e.g., **No Recourse to Public Funds / Immigration Status** or **Disputed Claim History**):

1. Add the field to `HouseholdProfile` in `src/household_profile.py`:
   ```python
   @dataclass
   class HouseholdProfile:
       # ...
       has_recourse_to_public_funds: bool = True
   ```
2. Update `detect_complex_case()` in `src/escalation.py`:
   ```python
   if not profile.has_recourse_to_public_funds:
       reasons.append(
           EscalationReason(
               code="nrpf_status",
               description=(
                   "Your immigration status indicates No Recourse to Public Funds (NRPF). "
                   "Specialist advice from an immigration and welfare adviser is required before applying."
               ),
           )
       )
   ```

---

### 4.4 Extension Point 4: Switching LLM Providers

The framework supports switching inference providers via environment variables without code modification:

```mermaid
graph TD
    A[Environment Var: LLM_PROVIDER] -->|anthropic| B[ChatAnthropic via langchain_anthropic]
    A -->|ollama| C[ChatOllama via langchain_ollama]
```

#### Running with Anthropic Claude (Cloud Default)
```bash
export LLM_PROVIDER=anthropic
export ANTHROPIC_API_KEY="your-api-key"
export CLAUDE_MODEL="claude-sonnet-4-6"
```

#### Running with Ollama (Local Air-Gapped / Privacy-Preserving)
```bash
export LLM_PROVIDER=ollama
export OLLAMA_MODEL="llama3.1:8b"
export OLLAMA_BASE_URL="http://localhost:11434"
```

---

### 4.5 Extension Point 5: Exposing as a REST / FastApi Service

To deploy the navigator as a backend service for a web portal or caseworker frontend:

```python
# example_api.py (Conceptual Integration)
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from src.household_profile import HouseholdProfile, reject_if_financial_data_present
from src.rules.engine import screen_household
from src.escalation import detect_complex_case
from src.explainer import explain_results
from src.renderer import build_checklist

app = FastAPI(title="Household Support Navigator API")

@app.post("/api/v1/screen")
async def screen_endpoint(raw_payload: dict):
    # 1. Zero-trust financial guard
    try:
        reject_if_financial_data_present(raw_payload)
        profile = HouseholdProfile(**raw_payload)
    except Exception as exc:
        raise HTTPException(status_code=422, detail=str(exc))

    # 2. Deterministic screening
    results = screen_household(profile)
    
    # 3. Escalation check
    escalations = detect_complex_case(profile, results)
    
    # 4. Plain-language explanation
    explanation = explain_results(results)
    
    # 5. Checklist output — asdict() required: ChecklistItem and EscalationReason are frozen dataclasses
    import dataclasses
    checklist = build_checklist(results)

    return {
        "checklist": [dataclasses.asdict(item) for item in checklist],
        "escalations": [dataclasses.asdict(r) for r in escalations],
        "explanation": explanation,
    }
```

---

## 5. Security, Governance & Verification

| Pillar | Governance Mechanism | Verification Method |
| :--- | :--- | :--- |
| **No Financial Data Storage** | `reject_if_financial_data_present()` blocks banking terms | `tests/test_profile.py::test_rejects_bank_fields_in_raw_payload` |
| **Deterministic Eligibility** | Pure rule functions return frozen `RuleResult` | `tests/test_rules_extended.py`, `tests/test_pension_credit.py` |
| **No AI Hallucinations** | Grounding system prompt & `_fallback_template` on failure | `tests/test_explainer.py::test_explain_results_falls_back_on_llm_failure` |
| **Mandatory Escalation** | `detect_complex_case()` checks self-employment & household size | `tests/test_escalation.py::test_escalates_self_employed` |
| **Consent-gated Persistence**| `SessionStore.persist_to_disk` checks `HSN_STORAGE_CONSENT=true` | `tests/test_session_store.py::test_persist_raises_without_consent` |
| **Fault Isolation** | `screen_household` catches per-rule exceptions without crashing | `tests/test_rules_engine_robustness.py::test_screen_household_isolates_failing_rule` |

---

## 6. Running Tests & Validation

```bash
# Activate virtual environment
source .venv/bin/activate

# Execute all unit and integration tests
pytest -v

# Run the end-to-end smoke test pipeline
python3 run_e2e.py
```
