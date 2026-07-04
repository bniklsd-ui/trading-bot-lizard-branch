"""Tests for the per-symbol circuit breaker (Phase 9 / V2 Step 6).

Both the pure ``_TickerCircuit`` class (injected ``now_fn``, no real sleeps) and its
integration into ``MarketDataFetcher._get_records`` (mocked ``_raw_download``, same
convention as ``test_fetcher.py``).
"""

from __future__ import annotations

import pandas as pd
import pytest

from external_data import fetcher
from external_data.exceptions import CircuitOpenError, DataUnavailableError
from external_data.fetcher import MarketDataFetcher, RateLimiter, _TickerCircuit
from external_data.ticker_map import TickerMapper

EPIC = "IX.D.DAX.IFMM.IP"
SYMBOL = "^GDAXI"


# -- pure _TickerCircuit ------------------------------------------------------


def _clock(start: float = 0.0):
    state = {"t": start}

    def now_fn() -> float:
        return state["t"]

    def advance(seconds: float) -> None:
        state["t"] += seconds

    return now_fn, advance


def test_closed_by_default():
    circuit = _TickerCircuit()
    assert circuit.is_open(SYMBOL) is False


def test_opens_after_open_after_consecutive_failures():
    now_fn, _ = _clock()
    circuit = _TickerCircuit(open_after=4, now_fn=now_fn)
    for _ in range(3):
        circuit.record_failure(SYMBOL)
        assert circuit.is_open(SYMBOL) is False
    circuit.record_failure(SYMBOL)  # 4th failure
    assert circuit.is_open(SYMBOL) is True


def test_success_resets_fail_count_and_closes():
    now_fn, _ = _clock()
    circuit = _TickerCircuit(open_after=4, now_fn=now_fn)
    for _ in range(4):
        circuit.record_failure(SYMBOL)
    assert circuit.is_open(SYMBOL) is True
    circuit.record_success(SYMBOL)
    assert circuit.is_open(SYMBOL) is False
    # Fail count was reset -> needs a fresh open_after run, not just 1 more failure.
    circuit.record_failure(SYMBOL)
    assert circuit.is_open(SYMBOL) is False


def test_half_open_after_cooldown_elapses():
    now_fn, advance = _clock()
    circuit = _TickerCircuit(open_after=4, cooldown_s=900.0, now_fn=now_fn)
    for _ in range(4):
        circuit.record_failure(SYMBOL)
    assert circuit.is_open(SYMBOL) is True
    advance(899.0)
    assert circuit.is_open(SYMBOL) is True  # not yet
    advance(2.0)
    assert circuit.is_open(SYMBOL) is False  # cooldown elapsed -> half-open probe allowed


def test_half_open_probe_failure_reopens():
    now_fn, advance = _clock()
    circuit = _TickerCircuit(open_after=4, cooldown_s=900.0, now_fn=now_fn)
    for _ in range(4):
        circuit.record_failure(SYMBOL)
    advance(901.0)
    assert circuit.is_open(SYMBOL) is False
    circuit.record_failure(SYMBOL)  # the probe failed
    assert circuit.is_open(SYMBOL) is True


def test_circuit_is_per_symbol():
    now_fn, _ = _clock()
    circuit = _TickerCircuit(open_after=2, now_fn=now_fn)
    circuit.record_failure(SYMBOL)
    circuit.record_failure(SYMBOL)
    assert circuit.is_open(SYMBOL) is True
    assert circuit.is_open("^STOXX50E") is False


# -- integration into MarketDataFetcher._get_records --------------------------


@pytest.fixture
def no_sleep(monkeypatch):
    monkeypatch.setattr(fetcher, "_SLEEP", lambda *_: None)


@pytest.fixture
def always_empty_download(monkeypatch):
    """Every fetch returns an empty frame -> _fetch_with_retry always raises."""
    calls: list[str] = []

    def _fake(symbol, *, period, interval):
        calls.append(symbol)
        return pd.DataFrame()

    monkeypatch.setattr(fetcher, "_raw_download", _fake)
    return calls


def test_circuit_opens_after_repeated_get_history_failures(
    no_sleep, always_empty_download, tmp_cache
):
    now_fn, _ = _clock()
    circuit = _TickerCircuit(open_after=4, now_fn=now_fn)
    mdf = MarketDataFetcher(TickerMapper(), tmp_cache, circuit=circuit)

    for _ in range(4):
        with pytest.raises(DataUnavailableError):
            mdf.get_history(EPIC, days=5)

    calls_before_open = len(always_empty_download)
    with pytest.raises(CircuitOpenError):
        mdf.get_history(EPIC, days=5)
    # The 5th call never touched _raw_download — the circuit degraded immediately.
    assert len(always_empty_download) == calls_before_open


def test_circuit_success_after_failures_resets(
    no_sleep, monkeypatch, tmp_cache, sample_dax_daily
):
    now_fn, _ = _clock()
    circuit = _TickerCircuit(open_after=4, now_fn=now_fn)
    mdf = MarketDataFetcher(TickerMapper(), tmp_cache, circuit=circuit)

    calls: list[str] = []

    def flaky_then_healthy(symbol, *, period, interval):
        calls.append(symbol)
        if len(calls) <= 3:  # exhausts _fetch_with_retry's 3-attempt budget once
            return pd.DataFrame()
        return sample_dax_daily.copy()

    monkeypatch.setattr(fetcher, "_raw_download", flaky_then_healthy)

    # First call: 3 internal retries all empty -> DataUnavailableError, 1 circuit failure.
    with pytest.raises(DataUnavailableError):
        mdf.get_history(EPIC, days=5)
    assert circuit.is_open(SYMBOL) is False  # only 1 of 4 needed

    # Second call succeeds (the 4th _raw_download call returns the real fixture) -> resets.
    result = mdf.get_history(EPIC, days=5)
    assert result  # non-empty
    assert circuit.is_open(SYMBOL) is False


def test_default_circuit_is_constructed_when_omitted(tmp_cache):
    mdf = MarketDataFetcher(TickerMapper(), tmp_cache)
    assert isinstance(mdf._circuit, _TickerCircuit)
    assert mdf._circuit.is_open(SYMBOL) is False
