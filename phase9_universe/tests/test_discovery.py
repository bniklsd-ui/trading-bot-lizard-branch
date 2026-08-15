"""Tests for the discovery sweep (Phase 9 / V2 Step 3).

A fake broker with fixture envelopes — no network. Pacing is asserted via an
injected ``sleep_fn`` recorder, never a real ``time.sleep``.
"""

from __future__ import annotations

import sqlite3
from pathlib import Path
from types import SimpleNamespace

import pytest

from universe.discovery import DiscoveryReport, discover
from universe.models import STATUS_DISCOVERED
from universe.store import UniverseStore

_MIGRATIONS_DIR = Path(__file__).resolve().parents[2] / "phase2_persistence" / "migrations"
# 006 (Phase 12, D5/D7) ALTERs paper_trades too, which needs 005 to have created it first.
_MIGRATION_004 = _MIGRATIONS_DIR / "004_phase9_instrument_universe.sql"
_MIGRATION_005 = _MIGRATIONS_DIR / "005_v3_learning.sql"
_MIGRATION_006 = _MIGRATIONS_DIR / "006_phase12_data_foundation.sql"


@pytest.fixture()
def store(tmp_path) -> UniverseStore:
    db_path = tmp_path / "discovery_test.sqlite"
    bootstrap = sqlite3.connect(str(db_path))
    bootstrap.executescript(_MIGRATION_004.read_text(encoding="utf-8"))
    bootstrap.executescript(_MIGRATION_005.read_text(encoding="utf-8"))
    bootstrap.executescript(_MIGRATION_006.read_text(encoding="utf-8"))
    bootstrap.commit()
    bootstrap.close()
    s = UniverseStore(db_path)
    yield s
    s.close()


def _env(ok: bool, data: dict | None = None) -> SimpleNamespace:
    return SimpleNamespace(ok=ok, data=data or {}, error=None if ok else {"message": "boom"})


def _market_info(
    *, name="Deutschland 40 Kassa (1€)", instrument_type="INDICES", currency="EUR",
    min_deal_size=0.5, lot_size=1.0, market_status="TRADEABLE",
) -> SimpleNamespace:
    return _env(
        True,
        {
            "name": name,
            "instrument_type": instrument_type,
            "currency": currency,
            "min_deal_size": min_deal_size,
            "lot_size": lot_size,
            "market_status": market_status,
        },
    )


class _FakeBroker:
    """Duck-typed broker: ``search_markets(term)`` + ``get_market_info(epic)``.

    ``search_results`` maps term -> list of {"epic": ...} hit dicts.
    ``market_infos`` maps epic -> the ``get_market_info`` envelope to return.
    """

    def __init__(self, search_results: dict, market_infos: dict, *, raise_on_search: set | None = None):
        self.search_results = search_results
        self.market_infos = market_infos
        self.raise_on_search = raise_on_search or set()
        self.search_calls: list[str] = []
        self.info_calls: list[str] = []

    def search_markets(self, term: str):
        self.search_calls.append(term)
        if term in self.raise_on_search:
            raise RuntimeError("simulated 500")
        hits = self.search_results.get(term, [])
        if hits is None:
            return _env(False)
        return _env(True, {"results": hits})

    def get_market_info(self, epic: str):
        self.info_calls.append(epic)
        return self.market_infos.get(epic, _env(False))


def _recording_sleep():
    calls: list[float] = []

    def sleep_fn(s: float) -> None:
        calls.append(s)

    return sleep_fn, calls


# -- happy path + report counting --------------------------------------------


def test_discover_finds_new_epic(store: UniverseStore):
    broker = _FakeBroker(
        search_results={"Germany 40": [{"epic": "IX.D.DAX.IFMM.IP"}]},
        market_infos={"IX.D.DAX.IFMM.IP": _market_info()},
    )
    sleep_fn, sleeps = _recording_sleep()
    report = discover(broker, store, search_terms=("Germany 40",), sleep_fn=sleep_fn)

    assert report.new == ["IX.D.DAX.IFMM.IP"]
    assert report.terms_searched == 1
    assert report.hits == 1
    assert report.skipped_known == 0
    assert report.filtered == {}
    assert len(sleeps) > 0  # paced, no real sleep

    rec = store.get("IX.D.DAX.IFMM.IP")
    assert rec is not None
    assert rec.status == STATUS_DISCOVERED
    assert rec.source == "research_promoted"
    assert rec.point_value is None
    # yf_ticker is no longer declared at discovery time (Decision D5, Phase 12) — the
    # SymbolResolver derives + verifies it later; a fresh discovery always starts unmapped.
    assert rec.yf_ticker is None
    assert rec.data_source_status == "unverified"
    assert rec.volume_proxy == "EXS1.DE"


def test_discover_skips_already_known_epic(store: UniverseStore):
    broker = _FakeBroker(
        search_results={"Germany 40": [{"epic": "IX.D.DAX.IFMM.IP"}]},
        market_infos={"IX.D.DAX.IFMM.IP": _market_info()},
    )
    sleep_fn, _ = _recording_sleep()
    discover(broker, store, search_terms=("Germany 40",), sleep_fn=sleep_fn)
    report2 = discover(broker, store, search_terms=("Germany 40",), sleep_fn=sleep_fn)

    assert report2.new == []
    assert report2.skipped_known == 1


# -- individual filter criteria -----------------------------------------------


def test_filter_currency_not_eur(store: UniverseStore):
    broker = _FakeBroker(
        search_results={"US 500": [{"epic": "IX.D.SPTRD.IFM.IP"}]},
        market_infos={"IX.D.SPTRD.IFM.IP": _market_info(currency="USD")},
    )
    sleep_fn, _ = _recording_sleep()
    report = discover(broker, store, search_terms=("US 500",), sleep_fn=sleep_fn)
    assert report.new == []
    assert report.filtered == {"currency": 1}


def test_filter_instrument_type_not_indices(store: UniverseStore):
    broker = _FakeBroker(
        search_results={"Germany 40": [{"epic": "CS.D.EURUSD.CFD.IP"}]},
        market_infos={"CS.D.EURUSD.CFD.IP": _market_info(instrument_type="CURRENCIES")},
    )
    sleep_fn, _ = _recording_sleep()
    report = discover(broker, store, search_terms=("Germany 40",), sleep_fn=sleep_fn)
    assert report.filtered == {"instrument_type": 1}


def test_filter_market_status_not_tradeable(store: UniverseStore):
    broker = _FakeBroker(
        search_results={"Germany 40": [{"epic": "IX.D.DAX.IFMM.IP"}]},
        market_infos={"IX.D.DAX.IFMM.IP": _market_info(market_status="CLOSED")},
    )
    sleep_fn, _ = _recording_sleep()
    report = discover(broker, store, search_terms=("Germany 40",), sleep_fn=sleep_fn)
    assert report.filtered == {"market_status": 1}


def test_filter_min_deal_size_zero(store: UniverseStore):
    broker = _FakeBroker(
        search_results={"Germany 40": [{"epic": "IX.D.DAX.IFMM.IP"}]},
        market_infos={"IX.D.DAX.IFMM.IP": _market_info(min_deal_size=0)},
    )
    sleep_fn, _ = _recording_sleep()
    report = discover(broker, store, search_terms=("Germany 40",), sleep_fn=sleep_fn)
    assert report.filtered == {"min_deal_size": 1}


def test_filter_market_info_fail(store: UniverseStore):
    broker = _FakeBroker(
        search_results={"Germany 40": [{"epic": "IX.D.DAX.IFMM.IP"}]},
        market_infos={"IX.D.DAX.IFMM.IP": _env(False)},
    )
    sleep_fn, _ = _recording_sleep()
    report = discover(broker, store, search_terms=("Germany 40",), sleep_fn=sleep_fn)
    assert report.filtered == {"market_info_fail": 1}


# -- Kassa-variant selection on multi-hit terms ------------------------------


def test_kassa_selection_prefers_smallest_lot_non_forward(store: UniverseStore):
    broker = _FakeBroker(
        search_results={
            "Germany 40": [
                {"epic": "IX.D.DAX.IFMM.IP"},   # Kassa (1€)
                {"epic": "IX.D.DAX.IFD.IP"},    # Kassa (2€) — larger lot
                {"epic": "IX.D.DAX.FWD3.IP"},   # Forward variant
            ]
        },
        market_infos={
            "IX.D.DAX.IFMM.IP": _market_info(name="Deutschland 40 Kassa (1€)", lot_size=1.0),
            "IX.D.DAX.IFD.IP": _market_info(name="Deutschland 40 Kassa (2€)", lot_size=2.0),
            "IX.D.DAX.FWD3.IP": _market_info(name="Deutschland 40 Forward Sep-26", lot_size=1.0),
        },
    )
    sleep_fn, _ = _recording_sleep()
    report = discover(broker, store, search_terms=("Germany 40",), sleep_fn=sleep_fn)

    assert report.new == ["IX.D.DAX.IFMM.IP"]
    assert report.filtered == {"kassa_variant": 2}


def test_single_hit_bypasses_kassa_check(store: UniverseStore):
    broker = _FakeBroker(
        search_results={"Germany 40": [{"epic": "IX.D.DAX.IFMM.IP"}]},
        market_infos={"IX.D.DAX.IFMM.IP": _market_info(lot_size=5.0)},  # would "lose" if compared
    )
    sleep_fn, _ = _recording_sleep()
    report = discover(broker, store, search_terms=("Germany 40",), sleep_fn=sleep_fn)
    assert report.new == ["IX.D.DAX.IFMM.IP"]


# -- fail-soft ----------------------------------------------------------------


def test_fail_soft_on_search_exception(store: UniverseStore):
    broker = _FakeBroker(
        search_results={
            "Germany 40": [{"epic": "IX.D.DAX.IFMM.IP"}],
            "France 40": [{"epic": "IX.D.CAC.IFE.IP"}],
        },
        market_infos={
            "IX.D.DAX.IFMM.IP": _market_info(),
            "IX.D.CAC.IFE.IP": _market_info(name="Frankreich 40 Kassa (1€)"),
        },
        raise_on_search={"Germany 40"},
    )
    sleep_fn, _ = _recording_sleep()
    report = discover(broker, store, search_terms=("Germany 40", "France 40"), sleep_fn=sleep_fn)

    assert report.terms_searched == 2
    assert report.new == ["IX.D.CAC.IFE.IP"]  # the second term still resolved


def test_fail_soft_on_search_not_ok(store: UniverseStore):
    broker = _FakeBroker(search_results={"Netherlands 25": None}, market_infos={})
    sleep_fn, _ = _recording_sleep()
    report = discover(broker, store, search_terms=("Netherlands 25",), sleep_fn=sleep_fn)
    assert report.new == []
    assert report.hits == 0


# -- pacing via injected sleep_fn (no real sleeps) ---------------------------


def test_pacing_calls_sleep_fn_not_real_sleep(store: UniverseStore):
    broker = _FakeBroker(
        search_results={"Germany 40": [{"epic": "IX.D.DAX.IFMM.IP"}]},
        market_infos={"IX.D.DAX.IFMM.IP": _market_info()},
    )
    sleep_fn, sleeps = _recording_sleep()
    discover(broker, store, search_terms=("Germany 40",), pace_s=2.5, sleep_fn=sleep_fn)
    assert all(s == 2.5 for s in sleeps)
    assert len(sleeps) == 2  # one after search_markets, one after get_market_info


def test_report_dataclass_defaults():
    report = DiscoveryReport()
    assert report.terms_searched == 0
    assert report.hits == 0
    assert report.new == []
    assert report.skipped_known == 0
    assert report.filtered == {}


def test_no_anthropic_import_anywhere_in_package():
    """Grep-assertion (plan §6 acceptance): zero AI import anywhere in this package."""
    import subprocess

    package_dir = Path(__file__).resolve().parents[1] / "universe"
    result = subprocess.run(
        ["grep", "-rl", "import anthropic", str(package_dir)],
        capture_output=True,
        text=True,
    )
    assert result.stdout.strip() == ""
