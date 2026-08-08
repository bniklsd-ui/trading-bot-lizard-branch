"""Tests for ``scripts/verify_instrument.py`` (v1.6 hotfix, Step 2 — the v3 seam).

Loaded via ``importlib`` by file path — root ``scripts/`` is deliberately **not** an
importable package (the phases already collide on a ``scripts.wiring`` module name), so this
phase-less harness is loaded the same way as ``test_diag_score_distribution.py`` /
``test_resolve_epics.py``.

All offline: the broker and the Phase-3 fetcher are duck-typed fakes — no network, no
keyring, no real order, no real sleep (a no-op ``sleep_fn`` is injected everywhere). The pure
check functions (``check_ig_side`` / ``check_yf_side`` / ``verdict_for`` / ``verify_instrument``)
are exercised directly; only the ``main()`` connect-failure test touches the lazy-import path.
"""

from __future__ import annotations

import importlib.util
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

_SCRIPT_PATH = Path(__file__).resolve().parent.parent / "scripts" / "verify_instrument.py"
_spec = importlib.util.spec_from_file_location("verify_instrument", _SCRIPT_PATH)
assert _spec is not None and _spec.loader is not None
verify_instrument_mod = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(verify_instrument_mod)

EPIC = "IX.D.DAX.IFMM.IP"


def _no_sleep(_seconds: float) -> None:
    """A sleep_fn stand-in that does nothing — keeps tests instant."""


@dataclass
class _Env:
    ok: bool
    data: dict[str, Any] | None = None
    error: dict[str, Any] | None = None


class _FakeBroker:
    """Duck-typed, read-only broker: get_market_info / get_ohlcv / connect only."""

    def __init__(
        self,
        *,
        info_ok: bool = True,
        currency: str | None = "EUR",
        min_deal_size: float | None = 0.5,
        info_error: dict[str, Any] | None = None,
        ohlcv_ok: bool = True,
        ohlcv_bars: bool = True,
        ohlcv_error: dict[str, Any] | None = None,
        connect_ok: bool = True,
    ) -> None:
        self._info_ok = info_ok
        self._currency = currency
        self._min_deal_size = min_deal_size
        self._info_error = info_error
        self._ohlcv_ok = ohlcv_ok
        self._ohlcv_bars = ohlcv_bars
        self._ohlcv_error = ohlcv_error
        self._connect_ok = connect_ok
        self.calls: list[str] = []

    def connect(self) -> _Env:
        return _Env(ok=self._connect_ok)

    def get_market_info(self, epic: str) -> _Env:
        self.calls.append(f"info:{epic}")
        if not self._info_ok:
            return _Env(ok=False, error=self._info_error)
        return _Env(ok=True, data={"currency": self._currency, "min_deal_size": self._min_deal_size})

    def get_ohlcv(self, epic: str, resolution: str, count: int) -> _Env:
        self.calls.append(f"ohlcv:{epic}")
        if not self._ohlcv_ok:
            return _Env(ok=False, error=self._ohlcv_error)
        return _Env(ok=True, data={"bars": [{"close": 1.0}] if self._ohlcv_bars else []})


class _FakeVolumeAnomaly:
    def __init__(self, volume_available: bool) -> None:
        self.volume_available = volume_available


_UNSET = object()  # sentinel distinguishing "use the market-open default" from an explicit None


class _FakeFetcher:
    """Duck-typed Phase-3 ``MarketDataFetcher``: get_history / get_bars / get_volume_anomaly."""

    def __init__(
        self,
        *,
        history: list | None = None,
        bars: Any = _UNSET,  # _UNSET default (one bar) / None (market closed) / [] / "raise" / a list
        volume_available: bool = True,
        raise_on_history: bool = False,
        raise_on_volume: bool = False,
    ) -> None:
        self._history = history if history is not None else [{"close": 1.0}]
        self._bars = bars
        self._volume_available = volume_available
        self._raise_on_history = raise_on_history
        self._raise_on_volume = raise_on_volume

    def get_history(self, epic: str, days: int = 5) -> list:
        if self._raise_on_history:
            raise RuntimeError("yfinance boom")
        return self._history

    def get_bars(self, epic: str, resolution: str = "5m", count: int = 5):
        if self._bars == "raise":
            raise RuntimeError("yfinance boom")
        if self._bars is _UNSET:
            return [{"close": 1.0}]  # market-open default: one bar
        return self._bars  # explicit None (market-closed) or [] (empty-but-not-None) or a list

    def get_volume_anomaly(self, epic: str) -> _FakeVolumeAnomaly:
        if self._raise_on_volume:
            raise RuntimeError("yfinance boom")
        return _FakeVolumeAnomaly(self._volume_available)


# -- check_ig_side ------------------------------------------------------------------------


def test_check_ig_side_all_pass() -> None:
    broker = _FakeBroker()
    result = verify_instrument_mod.check_ig_side(broker, EPIC, sleep_fn=_no_sleep)
    assert result["currency_eur"] is True
    assert result["min_deal_size_ok"] is True
    assert result["ig_ohlcv_available"] is True


def test_check_ig_side_wrong_currency_fails() -> None:
    broker = _FakeBroker(currency="USD")
    result = verify_instrument_mod.check_ig_side(broker, EPIC, sleep_fn=_no_sleep)
    assert result["currency_eur"] is False


def test_check_ig_side_bad_min_deal_size_fails() -> None:
    broker = _FakeBroker(min_deal_size=0.0)
    result = verify_instrument_mod.check_ig_side(broker, EPIC, sleep_fn=_no_sleep)
    assert result["min_deal_size_ok"] is False


def test_check_ig_side_no_ohlcv_bars_fails() -> None:
    broker = _FakeBroker(ohlcv_bars=False)
    result = verify_instrument_mod.check_ig_side(broker, EPIC, sleep_fn=_no_sleep)
    assert result["ig_ohlcv_available"] is False


def test_check_ig_side_reports_the_ohlcv_error_code() -> None:
    """The probe must say *why* it failed, so a caller can tell an unsuitable instrument
    apart from an account-wide condition (live finding 2026-08-04: an exhausted
    historical-data allowance made every epic look unsuitable at once)."""
    broker = _FakeBroker(ohlcv_ok=False, ohlcv_error={"code": "RATE_LIMIT", "message": "403"})
    result = verify_instrument_mod.check_ig_side(broker, EPIC, sleep_fn=_no_sleep)
    assert result["ig_ohlcv_available"] is False
    assert result["ig_ohlcv_error_code"] == "RATE_LIMIT"


def test_ohlcv_error_code_rides_on_the_verdict_but_never_in_checks() -> None:
    """It must stay out of ``checks``: both ``failed_checks`` and Phase-9's
    ``_ig_side_failed``/``_yf_side_failed`` scan that dict for boolean False."""
    broker = _FakeBroker(ohlcv_ok=False, ohlcv_error={"code": "RATE_LIMIT"})
    verdict = verify_instrument_mod.verify_instrument(
        broker, _FakeFetcher(), EPIC, sleep_fn=_no_sleep
    )
    assert verdict["ig_ohlcv_error_code"] == "RATE_LIMIT"
    assert "ig_ohlcv_error_code" not in verdict["checks"]
    assert "ig_ohlcv_error_code" not in verdict["failed_checks"]


def test_check_ig_side_error_code_is_none_when_the_probe_succeeds() -> None:
    result = verify_instrument_mod.check_ig_side(_FakeBroker(), EPIC, sleep_fn=_no_sleep)
    assert result["ig_ohlcv_error_code"] is None


def test_check_ig_side_market_info_not_ok_degrades_without_crash() -> None:
    broker = _FakeBroker(info_ok=False, info_error={"message": "not found"})
    result = verify_instrument_mod.check_ig_side(broker, EPIC, sleep_fn=_no_sleep)
    assert result["currency_eur"] is False
    assert result["min_deal_size_ok"] is False
    assert result["market_info_error"] == "not found"


def test_check_ig_side_paces_every_broker_call() -> None:
    broker = _FakeBroker()
    sleeps: list[float] = []
    verify_instrument_mod.check_ig_side(broker, EPIC, sleep_fn=sleeps.append, pace_s=0.6)
    # 1 get_market_info + 1 get_ohlcv = 2 broker calls -> 2 paced sleeps.
    assert sleeps == [0.6, 0.6]


# -- check_yf_side ------------------------------------------------------------------------


def test_check_yf_side_all_pass() -> None:
    fetcher = _FakeFetcher()
    result = verify_instrument_mod.check_yf_side(fetcher, EPIC)
    assert result["yf_daily_ok"] is True
    assert result["yf_intraday_ok"] is True


def test_check_yf_side_market_closed_intraday_is_skip_not_fail() -> None:
    """A None return (Phase-3's own off-hours discipline) is an honest skip, not a failure."""
    fetcher = _FakeFetcher(bars=None)
    result = verify_instrument_mod.check_yf_side(fetcher, EPIC)
    assert result["yf_intraday_ok"] == "skipped(market closed)"
    assert result["yf_intraday_ok"] is not False  # never scored as a failure


def test_check_yf_side_empty_intraday_bars_in_hours_fails() -> None:
    """An empty (but non-None) bar list — a genuine in-hours failure, not a skip."""
    fetcher = _FakeFetcher(bars=[])
    result = verify_instrument_mod.check_yf_side(fetcher, EPIC)
    assert result["yf_intraday_ok"] is False


def test_check_yf_side_daily_fetch_raises_degrades_without_crash() -> None:
    fetcher = _FakeFetcher(raise_on_history=True)
    result = verify_instrument_mod.check_yf_side(fetcher, EPIC)
    assert result["yf_daily_ok"] is False


def test_check_yf_side_intraday_raises_degrades_without_crash() -> None:
    fetcher = _FakeFetcher(bars="raise")
    result = verify_instrument_mod.check_yf_side(fetcher, EPIC)
    assert result["yf_intraday_ok"] is False


def test_check_yf_side_missing_volume_proxy_is_none_not_fail() -> None:
    """No volume_proxy configured → not applicable, never a failure."""
    fetcher = _FakeFetcher()
    result = verify_instrument_mod.check_yf_side(fetcher, EPIC, volume_proxy=None)
    assert result["volume_proxy_ok"] is None


def test_check_yf_side_volume_proxy_configured_and_available() -> None:
    fetcher = _FakeFetcher(volume_available=True)
    result = verify_instrument_mod.check_yf_side(fetcher, EPIC, volume_proxy="EXS1.DE")
    assert result["volume_proxy_ok"] is True


def test_check_yf_side_volume_proxy_configured_but_unavailable_fails() -> None:
    fetcher = _FakeFetcher(volume_available=False)
    result = verify_instrument_mod.check_yf_side(fetcher, EPIC, volume_proxy="EXS1.DE")
    assert result["volume_proxy_ok"] is False


def test_check_yf_side_volume_proxy_raises_degrades_without_crash() -> None:
    fetcher = _FakeFetcher(raise_on_volume=True)
    result = verify_instrument_mod.check_yf_side(fetcher, EPIC, volume_proxy="EXS1.DE")
    assert result["volume_proxy_ok"] is False


# -- verdict_for / verify_instrument --------------------------------------------------------


def test_verdict_for_all_pass_is_pass() -> None:
    ig = {"currency_eur": True, "min_deal_size_ok": True, "ig_ohlcv_available": True}
    yf = {"yf_daily_ok": True, "yf_intraday_ok": True, "volume_proxy_ok": None}
    verdict = verify_instrument_mod.verdict_for(EPIC, ig, yf)
    assert verdict["verdict"] == "PASS"
    assert verdict["failed_checks"] == []


def test_verdict_for_lists_every_failed_check() -> None:
    ig = {"currency_eur": False, "min_deal_size_ok": True, "ig_ohlcv_available": False}
    yf = {"yf_daily_ok": True, "yf_intraday_ok": True, "volume_proxy_ok": None}
    verdict = verify_instrument_mod.verdict_for(EPIC, ig, yf)
    assert verdict["verdict"] == "FAIL"
    assert set(verdict["failed_checks"]) == {"currency_eur", "ig_ohlcv_available"}


def test_verdict_for_skip_and_none_never_fail() -> None:
    """A market-closed skip and a not-applicable None don't fail the verdict on their own."""
    ig = {"currency_eur": True, "min_deal_size_ok": True, "ig_ohlcv_available": True}
    yf = {"yf_daily_ok": True, "yf_intraday_ok": "skipped(market closed)", "volume_proxy_ok": None}
    verdict = verify_instrument_mod.verdict_for(EPIC, ig, yf)
    assert verdict["verdict"] == "PASS"


def test_verify_instrument_composes_both_sides() -> None:
    broker = _FakeBroker()
    fetcher = _FakeFetcher()
    result = verify_instrument_mod.verify_instrument(broker, fetcher, EPIC, sleep_fn=_no_sleep)
    assert result["epic"] == EPIC
    assert result["verdict"] == "PASS"
    assert set(result["checks"]) == {
        "currency_eur", "min_deal_size_ok", "ig_ohlcv_available",
        "yf_daily_ok", "yf_intraday_ok", "volume_proxy_ok",
    }


# -- CLI ---------------------------------------------------------------------------------


def test_help_exits_zero(capsys) -> None:
    try:
        verify_instrument_mod.main(["--help"])
    except SystemExit as exc:
        assert exc.code == 0
    else:
        raise AssertionError("--help should raise SystemExit(0)")
    out = capsys.readouterr().out
    assert "verify_instrument" in out or "instrument-verification" in out.lower() or "usage" in out.lower()


def test_main_handles_connect_failure_gracefully(monkeypatch, capsys) -> None:
    """A failed broker connect → exit 0, connected:false, empty results (no crash)."""
    class _NoConnect:
        def connect(self) -> _Env:
            return _Env(ok=False)

    import sys
    import types

    stub = types.ModuleType("broker_wrapper")
    stub.get_broker = lambda name: _NoConnect()  # type: ignore[attr-defined]
    monkeypatch.setitem(sys.modules, "broker_wrapper", stub)

    rc = verify_instrument_mod.main(["--broker", "ig_demo", "--epic", EPIC, "--yf-ticker", "^TEST"])
    assert rc == 0
    out = capsys.readouterr().out
    payload = json.loads(out)
    assert payload["connected"] is False
    assert payload["results"] == []


def test_main_rejects_yf_ticker_with_multiple_epics(capsys) -> None:
    """--yf-ticker only makes sense for exactly one --epic — a clear, non-crashing refusal."""
    rc = verify_instrument_mod.main(
        ["--epic", EPIC, "--epic", "IX.D.STXE.IFM.IP", "--yf-ticker", "^TEST"]
    )
    assert rc == 0
    out = capsys.readouterr().out
    payload = json.loads(out)
    assert payload["connected"] is False
