"""
End-to-end smoke test: exercises the full pipeline for two sample households
and writes CLI + HTML output to data/e2e_output/.
"""
import os
import sys
from pathlib import Path
from datetime import datetime

# Load .env before importing project modules
def _load_env(path=".env"):
    try:
        with open(path) as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#") or "=" not in line:
                    continue
                key, _, value = line.partition("=")
                value = value.strip().strip('"').strip("'")
                os.environ.setdefault(key.strip(), value)
    except FileNotFoundError:
        pass

_load_env()

from src.household_profile import HouseholdProfile
from src.rules.engine import screen_household
from src.escalation import detect_complex_case
from src.explainer import explain_results
from src.renderer import build_checklist, render_cli, render_html
from shared.telemetry import TelemetryRecorder

PROFILES = [
    (
        "pensioner_low_income",
        HouseholdProfile(
            age=68,
            household_size=1,
            region="England",
            annual_income=10_500,
            housing_status="renter",
            employment_status="retired",
            existing_benefits=["pension_credit_guarantee"],
            has_partner=False,
        ),
    ),
    (
        "young_family",
        HouseholdProfile(
            age=28,
            household_size=3,
            region="Manchester",
            annual_income=18_000,
            housing_status="renter",
            employment_status="employed",
            existing_benefits=["universal_credit"],
            is_pregnant_or_young_child=True,
        ),
    ),
]

output_dir = Path("data/e2e_output")
output_dir.mkdir(parents=True, exist_ok=True)
timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
recorder = TelemetryRecorder()

print(f"Running e2e test — model: {os.environ.get('CLAUDE_MODEL', 'unknown')}\n")

for label, profile in PROFILES:
    print(f"--- {label} ---")
    telemetry = recorder.start_run()

    results = screen_household(profile)
    recorder.record_results(telemetry, results)

    escalation_reasons = detect_complex_case(profile, results)
    recorder.record_escalation(telemetry, escalation_reasons)

    print(f"  Rules run: {len(results)}  |  Escalation triggers: {len(escalation_reasons)}")

    explanation = explain_results(results, telemetry=telemetry)

    recorder.finish_run(telemetry)
    print(f"  LLM calls: {telemetry.llm_calls}  |  Latency: {telemetry.latency_seconds:.2f}s")

    checklist = build_checklist(results)

    cli_text = render_cli(checklist, escalation_reasons)
    html_output = render_html(checklist, escalation_reasons)

    # Save outputs
    cli_path = output_dir / f"{label}_{timestamp}.txt"
    html_path = output_dir / f"{label}_{timestamp}.html"
    expl_path = output_dir / f"{label}_{timestamp}_explanation.txt"

    cli_path.write_text(cli_text)
    html_path.write_text(html_output)
    expl_path.write_text(explanation)

    print(f"  Saved: {cli_path.name}, {html_path.name}, {expl_path.name}\n")

telemetry_path = recorder.export_json(directory=str(output_dir))
print(f"Telemetry: {Path(telemetry_path).name}")
print("\nDone.")
