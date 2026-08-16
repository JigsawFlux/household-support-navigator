# src/session_store.py
"""
HSN-060/061: Session-only storage enforcement.

By default, household profiles and screening results live only in memory for
the duration of a single run. Persistence to disk requires an explicit,
separate consent flag — mirroring the privacy posture used in the other
JigsawFlux MVPs (verification-agent, graduate-career-navigator).
"""
import json
import logging
import os
import time
from dataclasses import asdict
from pathlib import Path

from src.household_profile import HouseholdProfile, reject_if_financial_data_present

logger = logging.getLogger(__name__)

_CONSENT_ENV_VAR = "HSN_STORAGE_CONSENT"


class ConsentRequiredError(RuntimeError):
    """Raised when persistence is attempted without explicit consent."""


def is_persistence_allowed() -> bool:
    return os.environ.get(_CONSENT_ENV_VAR, "false").strip().lower() == "true"


class SessionStore:
    """
    In-memory-only by default. `persist_to_disk` is opt-in and gated by
    HSN_STORAGE_CONSENT=true, matching the no-default-persistence guardrail.
    """

    def __init__(self):
        self._profiles: dict[str, HouseholdProfile] = {}

    def save(self, session_id: str, profile: HouseholdProfile) -> None:
        self._profiles[session_id] = profile

    def get(self, session_id: str) -> HouseholdProfile | None:
        return self._profiles.get(session_id)

    def clear(self, session_id: str) -> None:
        self._profiles.pop(session_id, None)

    def persist_to_disk(self, session_id: str, directory: str = "data/sessions") -> str:
        """
        Explicit, consent-gated persistence. Raises ConsentRequiredError unless
        HSN_STORAGE_CONSENT=true is set. Rejects any financial/bank-like fields.
        """
        if not is_persistence_allowed():
            raise ConsentRequiredError(
                f"Persistence requires {_CONSENT_ENV_VAR}=true to be set explicitly."
            )

        profile = self._profiles.get(session_id)
        if profile is None:
            raise KeyError(f"No profile found for session_id={session_id!r}")

        payload = asdict(profile)
        reject_if_financial_data_present(payload)

        Path(directory).mkdir(parents=True, exist_ok=True)
        file_path = Path(directory) / f"{session_id}.json"
        with open(file_path, "w") as f:
            json.dump({"saved_at": time.time(), "profile": payload}, f, indent=2)

        logger.info("session_store: persisted session %s to %s", session_id, file_path)
        return str(file_path)