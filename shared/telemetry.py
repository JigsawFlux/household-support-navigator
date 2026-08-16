# shared/telemetry.py
"""
HSN-070: Run telemetry.

Tracks per-run metrics: latency, rule match counts, escalation rate, and
entitlement distribution. Each run gets a run_id. Records are appended to an
in-memory list by default; callers may flush to disk explicitly (respecting
the same consent gate as session_store.py).
"""
from __future__ import annotations

import json
import logging
import time
import uuid
from dataclasses import dataclass, field, asdict
from pathlib import Path

from langchain_core.callbacks import BaseCallbackHandler

from src.rules.base import RuleResult
from src.escalation import EscalationReason

logger = logging.getLogger(__name__)


@dataclass
class RunTelemetry:
    run_id: str
    started_at: float
    ended_at: float | None = None
    latency_seconds: float | None = None
    entitlement_counts: dict[str, int] = field(default_factory=dict)
    eligible_count: int = 0
    ineligible_count: int = 0
    escalated: bool = False
    escalation_reasons: list[str] = field(default_factory=list)
    llm_calls: int = 0
    llm_errors: int = 0


class TelemetryCallback(BaseCallbackHandler):
    """LangChain callback handler counting LLM invocations/errors per run."""

    def __init__(self, telemetry: RunTelemetry):
        self._telemetry = telemetry

    def on_llm_start(self, *args, **kwargs):
        self._telemetry.llm_calls += 1

    def on_llm_error(self, *args, **kwargs):
        self._telemetry.llm_errors += 1


class TelemetryRecorder:
    """
    Collects RunTelemetry records in memory. Call start_run() at the beginning
    of a household screening, record_results()/record_escalation() as data
    becomes available, then finish_run() to close it out.
    """

    def __init__(self):
        self._records: list[RunTelemetry] = []

    def start_run(self) -> RunTelemetry:
        telemetry = RunTelemetry(run_id=str(uuid.uuid4()), started_at=time.time())
        self._records.append(telemetry)
        return telemetry

    def record_results(self, telemetry: RunTelemetry, results: list[RuleResult]) -> None:
        for r in results:
            telemetry.entitlement_counts[r.entitlement] = telemetry.entitlement_counts.get(
                r.entitlement, 0
            ) + 1
            if r.eligible:
                telemetry.eligible_count += 1
            else:
                telemetry.ineligible_count += 1

    def record_escalation(self, telemetry: RunTelemetry, reasons: list[EscalationReason]) -> None:
        telemetry.escalated = bool(reasons)
        telemetry.escalation_reasons = [r.code for r in reasons]

    def finish_run(self, telemetry: RunTelemetry) -> None:
        telemetry.ended_at = time.time()
        telemetry.latency_seconds = telemetry.ended_at - telemetry.started_at
        logger.info(
            "telemetry: run_id=%s latency=%.3fs escalated=%s eligible=%d ineligible=%d",
            telemetry.run_id,
            telemetry.latency_seconds,
            telemetry.escalated,
            telemetry.eligible_count,
            telemetry.ineligible_count,
        )

    def all_records(self) -> list[RunTelemetry]:
        return list(self._records)

    def export_json(self, directory: str = "data/telemetry") -> str:
        """
        HSN-071: Exports all collected records as a JSON report for weekly
        review (rule hit rates, escalation reasons). Not gated by storage
        consent — telemetry contains no household-identifying data (no
        HouseholdProfile fields are ever written here).
        """
        Path(directory).mkdir(parents=True, exist_ok=True)
        file_path = Path(directory) / f"telemetry_{uuid.uuid4().hex}.json"
        payload = [asdict(r) for r in self._records]
        with open(file_path, "w") as f:
            json.dump(payload, f, indent=2)
        return str(file_path)