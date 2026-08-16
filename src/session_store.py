# src/session_store.py
"""
HSN-060/061: Session-only storage with optional consent-gated persistence.
"""
from __future__ import annotations

import json
import logging
import os
import re
import time
import uuid
from dataclasses import asdict
from pathlib import Path

from src.household_profile import HouseholdProfile, reject_if_financial_data_present

logger = logging.getLogger(__name__)

_CONSENT_ENV_VAR = "HSN_STORAGE_CONSENT"
_SESSION_ID_PATTERN = re.compile(r"^[a-zA-Z0-9_-]{1,64}$")


class ConsentRequiredError(PermissionError):
    """Raised when persistence is attempted without the explicit consent flag."""


def is_persistence_allowed() -> bool:
    return os.environ.get(_CONSENT_ENV_VAR, "false").strip().lower() == "true"


def new_session_id() -> str:
    return str(uuid.uuid4())


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
        if not _SESSION_ID_PATTERN.match(session_id):
            raise ValueError("Invalid session_id: must be alphanumeric, dash, or underscore only.")
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
