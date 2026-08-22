"""Phase-14 Block 0.3 — tests for ``scripts/capital_backfill.py``.

All mocked: no network, no live DB, no keyring. Covers the three Phase-13
findings (B3/B4/B5) that this block fixes:

- **B3** `_resolve_epics(--auto)` must open the universe-db path
  (``trading_bot.sqlite``), not the bars-db path (``bars.sqlite``) —
  ``args.db`` was the wrong default since Session 12.
- **B4** ``main``'s top-level ``except`` must emit valid JSON with
  ``partial_results: {}`` instead of ``NameError`` swallowing the original
  exception (the pre-bind of ``results``).
- **B5** ``run_capital_backfill``'s ``bars_written`` counter must reflect
  the number of *genuinely new* rows ``BarArchive.insert_bars`` actually
  wrote (``cur.rowcount`` over ``INSERT OR IGNORE``), not the number of
  fetch attempts — duplicates don't count.

These tests live in a separate file because they exercise the script
(which is not part of the installed ``live_data`` package) and the
helper module (``BarArchive`` + ``Bar``).
"""

from __future__ import annotations

import argparse
import json
import sqlite3
import sys
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

# Make the script importable the same way ``scripts/source_delta.py`` is
# made importable in test_source_delta.py (L17-L19).
_SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(_SCRIPTS))

import capital_backfill as cb  # noqa: E402

from data_foundation.archive import BarArchive  # noqa: E402
from data_foundation.models import Bar  # noqa: E402
from live_data import backfill as backfill_mod  # noqa: E402
from live_data.backfill import (  # noqa: E402
    CapitalSource,
    run_capital_backfill,
)


# Phase-14 B2: the symbol_lookup is the new source of truth for the
# IG-Epic → Capital-Kürzel mapping. The script's test supplies a
# minimal lookup so the test is independent of any DB state.
_TEST_LOOKUP = lambda e: {
    "IX.D.DAX.IFMM.IP": "DE40",
    "IX.D.CAC.IFE.IP": "FR40",
}.get(e)


# ---------- shared helpers --------------------------------------------------


class _Resp:
    def __init__(self, status_code: int, json_body: dict | None = None,
                 headers: dict | None = None) -> None:
        self.status_code = status_code
        self._json = json_body or {}
        self.headers = headers or {}

    def json(self) -> dict:
        return self._json

    @property
    def text(self) -> str:
        return json.dumps(self._json)


def _patch_requests(responses: list[_Resp]):
    """Replace ``live_data.backfill.requests.post``/``.get`` with a
    MagicMock that pops responses in order."""
    def _fake_post(url, **kwargs):
        if not responses:
            raise AssertionError(f"unexpected POST {url}")
        return responses.pop(0)

    def _fake_get(url, **kwargs):
        if not responses:
            raise AssertionError(f"unexpected GET {url}")
        return responses.pop(0)

    p1 = patch.object(backfill_mod.requests, "post", side_effect=_fake_post)
    p2 = patch.object(backfill_mod.requests, "get", side_effect=_fake_get)
    return p1, p2


def _make_source() -> CapitalSource:
    return CapitalSource(
        "u@example.com", "custom-pwd", "abcdef0123456789",
        symbol_lookup=_TEST_LOOKUP,
    )


@pytest.fixture
def archive(tmp_path) -> BarArchive:
    a = BarArchive(tmp_path / "bars.sqlite")
    a.ensure_schema()
    yield a
    a.close()


def _make_bar(ts_utc: str = "2026-08-21T18:00:00.000Z") -> Bar:
    return Bar(
        epic="IX.D.DAX.IFMM.IP",
        resolution="1m",
        ts_utc=ts_utc,
        open=100.0, high=101.0, low=99.0, close=100.5, volume=42,
        source="capital",
        fetched_at="2026-08-21T18:00:30.000Z",
        tick_count=None,
    )


# ---------- B3: --auto opens universe-db, not bars-db ----------------------


def test_resolve_epics_auto_opens_universe_db_path(monkeypatch, tmp_path):
    """--auto must open the universe-db (``trading_bot.sqlite``), not the
    bars-db (``bars.sqlite``). The old default (``args.db``) pointed at
    ``bars.sqlite``, where ``instrument_universe`` does not exist, so the
    call raised ``sqlite3.OperationalError`` silently (Session 12 onward)."""
    bars_path = tmp_path / "bars.sqlite"
    universe_path = tmp_path / "trading_bot.sqlite"
    args = argparse.Namespace(
        auto=True,
        epics=None,
        db=str(bars_path),
        universe_db=str(universe_path),
    )

    captured: list[str] = []

    class _FakeStore:
        def __init__(self, path) -> None:
            captured.append(path)

        def measurable_universe(self):
            return []

        def close(self) -> None:
            pass

    # The script does ``from universe import UniverseStore`` inside
    # _resolve_epics; that resolves through the package-level binding
    # ``universe.UniverseStore`` (set in ``phase9_universe/universe/__init__.py:30``).
    # Patch the package symbol so the function-local import picks up our fake.
    import universe
    monkeypatch.setattr(universe, "UniverseStore", _FakeStore)

    epics = cb._resolve_epics(args)

    assert captured == [str(universe_path)], (
        f"_resolve_epics opened {captured!r}; expected [{universe_path!r}]"
    )
    assert epics == []


# ---------- B5: results counts only genuinely-new rows --------------------


def test_run_capital_backfill_counts_only_genuinely_new_rows(archive):
    """Pre-populate the archive with the bar the API will return, then
    run. ``insert_bars`` returns 0 for the duplicate (cur.rowcount over
    ``INSERT OR IGNORE``); the old counter ``written += 1`` would have
    reported 1. With the fix, ``results[epic] == 0``."""
    pre_bar = _make_bar(ts_utc="2026-08-21T18:00:00.000Z")
    archive.insert_bars([pre_bar])

    p1, p2 = _patch_requests([
        _Resp(200, headers={"CST": "c", "X-SECURITY-TOKEN": "s"}),
        _Resp(200, json_body={
            "prices": [
                {"snapshotTime": "2026-08-21T20:00:00",
                 "openPrice": 100.0, "highPrice": 101.0,
                 "lowPrice": 99.0, "closePrice": 100.5, "volume": 42},
            ],
        }),
    ])
    with p1, p2:
        src = _make_source()
        results = run_capital_backfill(
            src, archive,
            epics=["IX.D.DAX.IFMM.IP"],
            start_utc=datetime(2026, 8, 21, 18, 0, tzinfo=timezone.utc),
            end_utc=datetime(2026, 8, 21, 21, 0, tzinfo=timezone.utc),
        )

    # The fetched bar is identical to the pre-populated one; the only way
    # ``results[epic]`` is 0 here is if ``written += archive.insert_bars(...)``
    # is the fix (without it, the counter is ``written += 1`` and reports 1).
    assert results == {"IX.D.DAX.IFMM.IP": 0}


# ---------- B4: except path emits valid JSON, no NameError -----------------


def test_main_except_path_emits_valid_json_with_empty_partial_results(
    monkeypatch, tmp_path, capsys,
):
    """When ``run_capital_backfill`` raises, ``main`` must emit a JSON
    envelope with ``partial_results: {}`` (pre-bound before the try). The
    pre-fix code raised ``NameError: name 'results' is not defined`` from
    inside the except handler and silently lost the original exception."""

    def _raise(*args, **kwargs):
        raise RuntimeError("test boom from run_capital_backfill")

    # Mock run_capital_backfill (imported inside main, but the script binds
    # the name in the module namespace via ``from live_data.backfill import
    # ...`` — patch at the import target so the local reference picks it up).
    monkeypatch.setattr("live_data.backfill.run_capital_backfill", _raise)

    # Mock keyring-bound credential reads.
    monkeypatch.setattr(cb, "_read_field", lambda field: f"fake-{field}")

    # The script imports ``BarArchive`` inside main() and calls ``ensure_schema``
    # on the result. Don't fake the class — let the script open a real tmp_path
    # BarArchive (the default ``--db`` from ``_DEFAULT_DB_PATH`` would point
    # into the repo, which we override here).
    # No patch needed; the script's own BarArchive reference resolves through
    # ``data_foundation.archive.BarArchive`` and works on a tmp_path file.

    # CapitalSource instantiation succeeds without doing anything (the
    # patched run_capital_backfill raises before any fetch).
    monkeypatch.setattr("live_data.backfill.CapitalSource", MagicMock())

    # Redirect --db to a tmp_path file so BarArchive/ensure_schema succeed.
    monkeypatch.setattr(cb, "_DEFAULT_DB_PATH", tmp_path / "bars.sqlite")

    # ``main(argv)`` exists but is dead code (doesn't reach _parse_args),
    # so we route the args through sys.argv instead.
    monkeypatch.setattr(sys, "argv", [
        "capital_backfill.py",
        "--epics", "IX.D.DAX.IFMM.IP",
        "--start", "2026-08-21T08:00:00Z",
        "--end", "2026-08-21T09:00:00Z",
    ])

    rc = cb.main()

    captured = capsys.readouterr()
    # The script prints ONE JSON envelope on stdout (stderr is narration).
    lines = [ln for ln in captured.out.splitlines() if ln.strip()]
    assert lines, f"expected a JSON envelope on stdout, got: {captured.out!r}"
    payload = json.loads(lines[-1])

    assert rc == 1
    assert payload["ok"] is False
    assert "backfill_raised" in payload["error"]
    assert "test boom from run_capital_backfill" in payload["error"]
    # The whole point of B4: partial_results is a pre-bound empty dict, not
    # a NameError that swallows the original exception.
    assert payload["partial_results"] == {}


# ---------- B2: script builds the symbol lookup from the DB -----------------


def test_build_symbol_lookup_returns_null_when_migration_007_missing(tmp_path):
    """An older ``trading_bot.sqlite`` without the Phase-14 table
    surfaces as a null-lookup — the backfill becomes a no-op rather than
    crashing on the first ``symbol_for`` call. Phase-14 B2 fail-soft."""
    # A fresh empty SQLite — no migration 007.
    db_path = tmp_path / "trading_bot.sqlite"
    sqlite3.connect(str(db_path)).close()

    lookup, store = cb._build_symbol_lookup(str(db_path))
    try:
        # Null lookup: every epic returns None.
        assert lookup("IX.D.DAX.IFMM.IP") is None
        assert lookup("IX.D.CAC.IFE.IP") is None
    finally:
        store.close()


def test_build_symbol_lookup_queries_the_availability_table(tmp_path):
    """With the table present (mocked SourceAvailabilityStore), the
    lookup calls ``symbol_for(epic, 'capital', '1m')`` and returns its
    result. This pins the B2 contract on the script side without
    needing a live DB."""
    from unittest.mock import MagicMock
    fake_store = MagicMock()
    fake_store.symbol_for.side_effect = lambda epic, source, res: {
        ("IX.D.DAX.IFMM.IP", "capital", "1m"): "DE40",
    }.get((epic, source, res))
    fake_store.close = MagicMock()

    # Patch SourceAvailabilityStore to return our fake.
    import source_registry.store as srstore_mod
    real_cls = srstore_mod.SourceAvailabilityStore
    srstore_mod.SourceAvailabilityStore = lambda path: fake_store
    try:
        lookup, store = cb._build_symbol_lookup(str(tmp_path / "any.sqlite"))
    finally:
        srstore_mod.SourceAvailabilityStore = real_cls

    # The lookup resolves DAX to DE40 and rejects anything else.
    assert lookup("IX.D.DAX.IFMM.IP") == "DE40"
    assert lookup("IX.D.CAC.IFE.IP") is None
    # And the underlying store saw exactly one call per request (the
    # probe + the real lookup; we don't count the probe here because
    # we mocked it).
    fake_store.symbol_for.assert_any_call("IX.D.DAX.IFMM.IP", "capital", "1m")
    fake_store.symbol_for.assert_any_call("IX.D.CAC.IFE.IP", "capital", "1m")
