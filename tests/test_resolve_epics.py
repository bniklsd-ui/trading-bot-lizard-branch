"""Tests for ``scripts/resolve_epics.py`` (v1.5 hotfix, Step 2 / Issue C).

Loaded via ``importlib`` by file path — root ``scripts/`` is deliberately **not** an
importable package (the phases already collide on a ``scripts.wiring`` module name), so this
phase-less resolver is loaded the same way as ``test_diag_score_distribution.py``.

All offline: the broker is a duck-typed fake returning ``.ok``/``.data`` envelopes — no
network, no keyring, no real order. The resolution functions are broker-injected precisely so
they can be exercised without ``main()`` ever building the real ``ig_demo`` broker.
"""

from __future__ import annotations

import importlib.util
from dataclasses import dataclass
from pathlib import Path
from typing import Any

_SCRIPT_PATH = Path(__file__).resolve().parent.parent / "scripts" / "resolve_epics.py"
_spec = importlib.util.spec_from_file_location("resolve_epics", _SCRIPT_PATH)
assert _spec is not None and _spec.loader is not None
resolve_epics = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(resolve_epics)


@dataclass
class _Env:
    ok: bool
    data: dict[str, Any] | None = None


class _FakeBroker:
    """Duck-typed, read-only broker: search_markets / get_market_info / get_ohlcv only."""

    def __init__(
        self,
        *,
        search_results: dict[str, list[dict[str, Any]]] | None = None,
        search_ok: bool = True,
        info_ok: bool = True,
        ohlcv_bars: bool = True,
        ohlcv_ok: bool = True,
    ) -> None:
        self._search_results = search_results or {}
        self._search_ok = search_ok
        self._info_ok = info_ok
        self._ohlcv_bars = ohlcv_bars
        self._ohlcv_ok = ohlcv_ok
        # Prove the resolver never writes/orders: only these three are ever called.
        self.calls: list[str] = []

    def search_markets(self, term: str) -> _Env:
        self.calls.append(f"search:{term}")
        if not self._search_ok:
            return _Env(ok=False)
        return _Env(ok=True, data={"query": term, "results": self._search_results.get(term, [])})

    def get_market_info(self, epic: str) -> _Env:
        self.calls.append(f"info:{epic}")
        if not self._info_ok:
            return _Env(ok=False)
        return _Env(ok=True, data={
            "epic": epic, "name": f"{epic} Cash", "instrument_type": "INDICES",
            "currency": "EUR", "min_deal_size": 1.0, "lot_size": 1.0, "market_status": "TRADEABLE",
        })

    def get_ohlcv(self, epic: str, resolution: str, count: int) -> _Env:
        self.calls.append(f"ohlcv:{epic}")
        if not self._ohlcv_ok:
            return _Env(ok=False)
        bars = [{"close": 100.0}] if self._ohlcv_bars else []
        return _Env(ok=True, data={"bars": bars})


def test_resolve_epic_shapes_all_fields() -> None:
    broker = _FakeBroker()
    out = resolve_epics.resolve_epic(broker, "IX.D.STXE.IFMM.IP")
    assert out["epic"] == "IX.D.STXE.IFMM.IP"
    assert out["market_info_ok"] is True
    assert out["currency"] == "EUR"
    assert out["min_deal_size"] == 1.0
    assert out["lot_size"] == 1.0
    assert out["market_status"] == "TRADEABLE"
    assert out["ohlcv_available"] is True


def test_probe_ohlcv_false_on_no_bars() -> None:
    assert resolve_epics.probe_ohlcv(_FakeBroker(ohlcv_bars=False), "X") is False
    assert resolve_epics.probe_ohlcv(_FakeBroker(ohlcv_ok=False), "X") is False


def test_resolve_term_resolves_every_hit() -> None:
    broker = _FakeBroker(search_results={
        "EU Stocks 50": [{"epic": "IX.D.STXE.IFMM.IP"}, {"epic": "IX.D.STXE.DAILY.IP"}],
    })
    block = resolve_epics.resolve_term(broker, "EU Stocks 50")
    assert block["search_ok"] is True
    assert [h["epic"] for h in block["hits"]] == ["IX.D.STXE.IFMM.IP", "IX.D.STXE.DAILY.IP"]


def test_resolve_term_failed_search_is_soft() -> None:
    block = resolve_epics.resolve_term(_FakeBroker(search_ok=False), "France 40")
    assert block["search_ok"] is False
    assert block["hits"] == []


def test_resolve_all_covers_terms_and_only_reads() -> None:
    broker = _FakeBroker(search_results={"France 40": [{"epic": "IX.D.CAC.IFMM.IP"}]})
    report = resolve_epics.resolve_all(broker, ("France 40",))
    assert len(report) == 1 and report[0]["hits"][0]["epic"] == "IX.D.CAC.IFMM.IP"
    # Read-only proof: no order/close/persistence method was ever invoked.
    assert all(c.split(":")[0] in {"search", "info", "ohlcv"} for c in broker.calls)


def test_main_handles_connect_failure_gracefully(monkeypatch, capsys) -> None:
    """A failed connect → exit 0, connected:false, empty report (no crash)."""
    class _NoConnect:
        def connect(self) -> _Env:
            return _Env(ok=False)

    import builtins  # noqa: F401 — ensure lazy import path is reachable
    monkeypatch.setattr(resolve_epics, "get_broker", lambda name: _NoConnect(), raising=False)
    # Inject a broker_wrapper stub so the lazy `from broker_wrapper import get_broker` resolves.
    import sys
    import types
    stub = types.ModuleType("broker_wrapper")
    stub.get_broker = lambda name: _NoConnect()  # type: ignore[attr-defined]
    monkeypatch.setitem(sys.modules, "broker_wrapper", stub)

    rc = resolve_epics.main(["--broker", "ig_demo"])
    assert rc == 0
    out = capsys.readouterr().out
    assert '"connected": false' in out
