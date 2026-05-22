"""Tests for the JSON StateManager (TTL, freshness, atomic round-trips)."""

from __future__ import annotations

import json

import pytest

ACCOUNT = {
    "account_id": "HTADU",
    "balance": 58700.0,
    "available": 55200.0,
    "profit_loss": 0.0,
    "currency": "GBP",
}
POSITIONS = [{
    "deal_id": "DIAAAABBBCCC",
    "epic": "IX.D.DAX.IFMM.IP",
    "direction": "BUY",
    "size": 1.0,
    "open_level": 18342.5,
    "profit_loss": 12.5,
    "currency": "EUR",
}]
CANDIDATE = {
    "epic": "IX.D.DAX.IFMM.IP",
    "direction": "CALL",
    "confidence": 72,
}


# -- ig_state.json ----------------------------------------------------------

def test_save_load_account_state_roundtrip(sm):
    sm.save_account_state(ACCOUNT, POSITIONS)
    state = sm.load_account_state()
    assert state["account_id"] == "HTADU"
    assert state["open_positions"] == POSITIONS
    assert state["session_active"] is True
    assert state["last_updated"].endswith("Z")


def test_load_account_state_missing_returns_none(sm):
    assert sm.load_account_state() is None


def test_is_account_state_fresh_true_after_save(sm):
    sm.save_account_state(ACCOUNT, POSITIONS)
    assert sm.is_account_state_fresh() is True


def test_is_account_state_fresh_false_when_old(sm):
    sm.save_account_state(ACCOUNT, POSITIONS)
    state = sm.load_account_state()
    state["last_updated"] = "2020-01-01T00:00:00.000Z"
    sm._atomic_write(sm._account_path, state)
    assert sm.is_account_state_fresh() is False


def test_is_account_state_fresh_false_when_missing(sm):
    assert sm.is_account_state_fresh() is False


# -- ig_config.json ---------------------------------------------------------

def test_save_load_bot_config_roundtrip(sm):
    config = {"broker": "ig", "account_type": "demo", "risk": {"max_risk_pct": 0.08}}
    sm.save_bot_config(config)
    assert sm.load_bot_config() == config


def test_load_bot_config_missing_raises(sm):
    with pytest.raises(FileNotFoundError):
        sm.load_bot_config()


# -- turbo_candidates.json --------------------------------------------------

def test_save_then_load_candidates(sm):
    sm.save_candidates([CANDIDATE])
    assert sm.load_candidates() == [CANDIDATE]


def test_save_candidates_writes_ttl_fields(sm):
    sm.save_candidates([CANDIDATE])
    payload = json.loads(sm._candidates_path.read_text())
    assert payload["ttl_minutes"] == 30
    assert payload["generated_at"].endswith("Z")
    assert payload["expires_at"].endswith("Z")
    assert payload["session_date"] == payload["generated_at"][:10]


def test_load_candidates_missing_returns_empty(sm):
    assert sm.load_candidates() == []


def test_load_candidates_expired_returns_empty_and_deletes(sm):
    sm.save_candidates([CANDIDATE])
    payload = json.loads(sm._candidates_path.read_text())
    payload["expires_at"] = "2020-01-01T00:00:00.000Z"
    sm._atomic_write(sm._candidates_path, payload)
    assert sm.load_candidates() == []
    assert not sm._candidates_path.exists()


def test_load_candidates_empty_list_deletes(sm):
    sm.save_candidates([])
    assert sm.load_candidates() == []
    assert not sm._candidates_path.exists()


def test_clear_candidates(sm):
    sm.save_candidates([CANDIDATE])
    sm.clear_candidates()
    assert not sm._candidates_path.exists()


def test_clear_candidates_when_missing_is_noop(sm):
    sm.clear_candidates()  # must not raise
    assert not sm._candidates_path.exists()


def test_candidates_are_fresh_true_after_save(sm):
    sm.save_candidates([CANDIDATE])
    assert sm.candidates_are_fresh() is True


def test_candidates_are_fresh_false_when_expired(sm):
    sm.save_candidates([CANDIDATE])
    payload = json.loads(sm._candidates_path.read_text())
    payload["expires_at"] = "2020-01-01T00:00:00.000Z"
    sm._atomic_write(sm._candidates_path, payload)
    assert sm.candidates_are_fresh() is False


def test_candidates_are_fresh_false_when_empty(sm):
    sm.save_candidates([])
    assert sm.candidates_are_fresh() is False


def test_candidates_are_fresh_false_when_missing(sm):
    assert sm.candidates_are_fresh() is False
