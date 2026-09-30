"""Tests for the per-symbol circuit breaker (Phase 9 / V2 Step 6).

Both the pure ``_TickerCircuit`` class (injected ``now_fn``, no real sleeps) and its
integration into ``MarketDataFetcher._get_records`` (mocked ``_raw_download``, same
convention as ``test_fetcher.py``).
"""

from __future__ import annotations

import pandas as pd
import pytest

from external_data import fetcher
from external_data.exceptions import CircuitOpenError, DataUnavailableError, RateLimitError
from external_data.fetcher import MarketDataFetcher, RateLimiter, _TickerCircuit
from external_data.ticker_map import TickerMapper

EPIC = "IX.D.DAX.IFMM.IP"
SYMBOL = "^GDAXI"


class YFRateLimitError(Exception):
    """Stand-in for ``yfinance.exceptions.YFRateLimitError`` (matched by class name).

    Mirrors the local definition in ``test_fetcher.py`` — duplicating the 2-line shim is
    cleaner than introducing a cross-test dependency.
    """


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


@pytest.fixture
def always_rate_limit(monkeypatch):
    """Every fetch raises ``YFRateLimitError`` -> ``RateLimitError`` after retries.

    The fetcher matches the class name ``YFRateLimitError`` (see ``_RATE_LIMIT_EXC_NAMES``
    in ``fetcher.py``); yfinance itself does not need to be installed. Used to verify
    that genuine rate-limit outages still open the circuit (Phase 16 C5: only the
    empty-frame path was decoupled — the rate-limit path keeps the prior behaviour).
    """
    calls: list[str] = []

    def _fake(symbol, *, period, interval):
        calls.append(symbol)
        raise YFRateLimitError("429 Too Many Requests")

    monkeypatch.setattr(fetcher, "_raw_download", _fake)
    return calls


def test_circuit_opens_after_repeated_get_history_failures(
    no_sleep, always_rate_limit, tmp_cache
):
    """Phase 16 C5 (2026-09-05): only ``RateLimitError`` opens the circuit.

    The empty-frame path (``DataUnavailableError``) is decoupled in C5 and covered by
    ``test_empty_frame_does_not_open_circuit`` below — rate-limit (HTTP 429) remains a
    genuine transport-side outage signal, so the circuit opens after ``open_after``
    consecutive occurrences (4 here).
    """
    now_fn, _ = _clock()
    circuit = _TickerCircuit(open_after=4, now_fn=now_fn)
    mdf = MarketDataFetcher(TickerMapper(), tmp_cache, circuit=circuit)

    for _ in range(4):
        with pytest.raises(RateLimitError):
            mdf.get_history(EPIC, days=5)

    calls_before_open = len(always_rate_limit)
    with pytest.raises(CircuitOpenError):
        mdf.get_history(EPIC, days=5)
    # The 5th call never touched _raw_download — the circuit degraded immediately.
    assert len(always_rate_limit) == calls_before_open


def test_empty_frame_does_not_open_circuit(
    no_sleep, always_empty_download, tmp_cache
):
    """Phase 16 C5 (2026-09-05, L9): an empty frame at open is a DATA judgment,
    not an outage — it MUST NOT open the circuit.

    L9 root cause (Plan §3 L9): Yahoo returns no intraday bars until ~09:05; the prior
    breaker counted ``DataUnavailableError`` (empty frame after 3 retries) toward
    circuit-open at 4 consecutive failures — locking out ``^GDAXI`` / ``^FCHI`` /
    ``^IBEX`` for 15 min every morning even though the same recorder was busy writing
    500+ 1m-bars/min for the same tickers. After C5 the empty-frame path re-raises
    ``DataUnavailableError`` unchanged but does **not** record_failure on the circuit.
    """
    now_fn, _ = _clock()
    circuit = _TickerCircuit(open_after=4, now_fn=now_fn)
    mdf = MarketDataFetcher(TickerMapper(), tmp_cache, circuit=circuit)

    # 4 empty-frame attempts: each raises DataUnavailableError but circuit stays closed.
    for _ in range(4):
        with pytest.raises(DataUnavailableError):
            mdf.get_history(EPIC, days=5)
    assert circuit.is_open(SYMBOL) is False

    # 5th call: still attempts the network (circuit isn't open to degrade), still raises.
    # _fetch_with_retry does 3 internal _raw_download attempts per call.
    calls_before = len(always_empty_download)
    with pytest.raises(DataUnavailableError):
        mdf.get_history(EPIC, days=5)
    assert len(always_empty_download) > calls_before  # network was actually attempted
    assert circuit.is_open(SYMBOL) is False


def test_circuit_success_after_failures_resets(
    no_sleep, monkeypatch, tmp_cache, sample_dax_daily
):
    now_fn, _ = _clock()
    circuit = _TickerCircuit(open_after=4, now_fn=now_fn)
    mdf = MarketDataFetcher(TickerMapper(), tmp_cache, circuit=circuit)

    calls: list[str] = []

    def flaky_then_healthy(symbol, *, period, interval):
        calls.append(symbol)
        if len(calls) <= fetcher._MAX_RETRIES:  # exhausts _fetch_with_retry's budget once
            return pd.DataFrame()
        return sample_dax_daily.copy()

    monkeypatch.setattr(fetcher, "_raw_download", flaky_then_healthy)

    # First call: _MAX_RETRIES internal retries all empty -> DataUnavailableError,
    # 1 circuit failure (Phase 16 R-Fix: budget is now 5, not 3).
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
