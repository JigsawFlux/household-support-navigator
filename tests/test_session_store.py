import os
import pytest

from src.household_profile import HouseholdProfile, ProfileValidationError
from src.session_store import SessionStore, ConsentRequiredError, is_persistence_allowed


def _profile():
    return HouseholdProfile(
        age=40,
        household_size=2,
        region="England",
        annual_income=15_000,
        housing_status="renter",
        employment_status="employed",
    )


def test_save_and_get_in_memory():
    store = SessionStore()
    store.save("s1", _profile())
    assert store.get("s1") is not None
    assert store.get("s1").region == "England"


def test_clear_removes_session():
    store = SessionStore()
    store.save("s1", _profile())
    store.clear("s1")
    assert store.get("s1") is None


def test_persist_raises_without_consent(monkeypatch):
    monkeypatch.delenv("HSN_STORAGE_CONSENT", raising=False)
    store = SessionStore()
    store.save("s1", _profile())
    with pytest.raises(ConsentRequiredError):
        store.persist_to_disk("s1")


def test_persist_succeeds_with_consent(monkeypatch, tmp_path):
    monkeypatch.setenv("HSN_STORAGE_CONSENT", "true")
    store = SessionStore()
    store.save("s1", _profile())
    path = store.persist_to_disk("s1", directory=str(tmp_path))
    assert os.path.exists(path)


def test_persist_raises_for_unknown_session(monkeypatch, tmp_path):
    monkeypatch.setenv("HSN_STORAGE_CONSENT", "true")
    store = SessionStore()
    with pytest.raises(KeyError):
        store.persist_to_disk("does-not-exist", directory=str(tmp_path))


def test_is_persistence_allowed_reflects_env(monkeypatch):
    monkeypatch.setenv("HSN_STORAGE_CONSENT", "true")
    assert is_persistence_allowed() is True
    monkeypatch.setenv("HSN_STORAGE_CONSENT", "false")
    assert is_persistence_allowed() is False