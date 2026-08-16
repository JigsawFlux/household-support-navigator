from shared.telemetry import TelemetryRecorder
from src.rules.base import RuleResult
from src.escalation import EscalationReason


def _results():
    return [
        RuleResult(
            entitlement="Pension Credit",
            eligible=True,
            reason="Below threshold.",
            source_url="https://www.gov.uk/pension-credit/eligibility",
            confidence="high",
        ),
        RuleResult(
            entitlement="Council Tax Reduction",
            eligible=False,
            reason="Above threshold.",
            source_url="https://www.gov.uk/apply-council-tax-reduction",
            confidence="medium",
        ),
    ]


def test_start_run_creates_unique_run_id():
    recorder = TelemetryRecorder()
    t1 = recorder.start_run()
    t2 = recorder.start_run()
    assert t1.run_id != t2.run_id


def test_record_results_counts_eligible_and_ineligible():
    recorder = TelemetryRecorder()
    telemetry = recorder.start_run()
    recorder.record_results(telemetry, _results())
    assert telemetry.eligible_count == 1
    assert telemetry.ineligible_count == 1
    assert telemetry.entitlement_counts["Pension Credit"] == 1


def test_record_escalation_sets_flag_and_reasons():
    recorder = TelemetryRecorder()
    telemetry = recorder.start_run()
    reasons = [EscalationReason(code="self_employed", description="x")]
    recorder.record_escalation(telemetry, reasons)
    assert telemetry.escalated is True
    assert telemetry.escalation_reasons == ["self_employed"]


def test_record_escalation_no_reasons_means_not_escalated():
    recorder = TelemetryRecorder()
    telemetry = recorder.start_run()
    recorder.record_escalation(telemetry, [])
    assert telemetry.escalated is False


def test_finish_run_sets_latency():
    recorder = TelemetryRecorder()
    telemetry = recorder.start_run()
    recorder.finish_run(telemetry)
    assert telemetry.ended_at is not None
    assert telemetry.latency_seconds is not None
    assert telemetry.latency_seconds >= 0


def test_export_json_writes_file(tmp_path):
    recorder = TelemetryRecorder()
    telemetry = recorder.start_run()
    recorder.record_results(telemetry, _results())
    recorder.finish_run(telemetry)
    path = recorder.export_json(directory=str(tmp_path))
    assert path.endswith(".json")
    import json
    with open(path) as f:
        data = json.load(f)
    assert len(data) == 1
    assert data[0]["eligible_count"] == 1