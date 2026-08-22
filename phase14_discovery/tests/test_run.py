"""Phase-14 Block C2 — tests for ``source_registry.run.DiscoveryDaemon``.

All mocked: duck-typed stores, no network, no live DB, no scheduler process. The
daemon is the orchestration layer above :mod:`arm`, :mod:`store` and
:mod:`sources`; this file pins the *behaviour* — fail-soft, fail-closed, gated by
ARM + stale — without touching any of those collaborators.

Test list (Plan §6 C2, ≥ 6; 12 here to cover the cycle-result shape + the
``run_forever`` loop + the CLI ``--once`` path explicitly):

1. unarmed → no ``discover`` call, no DB write, ``armed=False`` in state
2. armed but nothing stale → no ``discover`` call, ``stale_count=0``
3. armed + stale → exactly one ``discover`` per registered Source, ``upsert_many``
   called with the profile's rows
4. a raising Source does not kill the cycle (its error lands in ``CycleResult.errors``;
   the other sources still run)
5. ``probe_calls_used == 0`` ⇒ ``record_spend`` is NOT called (default Phase-14
   sources are net-free; the budget ledger is untouched)
6. ``probe_calls_used > 0`` ⇒ ``record_spend(points, kind='discovery')`` IS called,
   once, with the cumulative sum across all sources
7. state file is written on every cycle, atomic ``.tmp`` + ``os.replace``
8. ``CycleResult`` is frozen + the JSON state file has the documented shape
9. ``run_forever`` calls ``run_once`` in a loop and exits on ``request_stop``
10. ``run_forever`` sleeps ``interval_s`` seconds between cycles (uses injected
    ``sleep_fn`` so the test stays fast)
11. ``main --once`` runs one cycle and exits 0 (CLI end-to-end smoke)
12. ``main`` with a live PID file pointing at this test process exits 0 immediately
"""

from __future__ import annotations

import json
import signal
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any
from unittest.mock import MagicMock

import pytest

from source_registry.arm import arm, disarm
from source_registry.models import (
    ORIGIN_DERIVED,
    RESOLUTION_1M,
    SOURCE_IG,
    STATUS_OK,
    SourceAvailability,
    SourceProfile,
)
from source_registry.run import (
    DiscoveryDaemon,
    _already_running,
    _build_default_sources,
    _clear_pid,
    _iso,
    _pid_alive,
    _write_pid,
    _write_state,
    main,
)
from source_registry.store import utc_iso_now


# ---------------------------------------------------------------------------
# Fakes — duck-typed stores and Sources.
# ---------------------------------------------------------------------------


@dataclass
class FakeSource:
    """A configurable Source for daemon-cycle tests.

    ``raise_in_discover`` simulates the "this source is broken today" branch
    (Plan §8.5 — one bad row must not kill the cycle).
    ``rows`` and ``probe_calls_used`` are returned by ``discover``.
    """

    name_str: str
    rows: tuple[SourceAvailability, ...] = ()
    probe_calls_used: int = 0
    raise_in_discover: bool = False
    discover_calls: list[tuple[tuple[str, ...], int]] = field(default_factory=list)

    def name(self) -> str:
        return self.name_str

    def discover(self, epics, *, max_probe_calls: int) -> SourceProfile:
        self.discover_calls.append((tuple(epics), max_probe_calls))
        if self.raise_in_discover:
            raise RuntimeError(f"{self.name_str} simulated network failure")
        return SourceProfile(
            source=self.name_str,
            rows=self.rows,
            probe_calls_used=self.probe_calls_used,
            errors=(),
        )


@dataclass
class FakeUniverseRecord:
    epic: str


@dataclass
class FakeUniverseStore:
    records: list[FakeUniverseRecord]
    list_by_status_calls: list[tuple[str, ...]] = field(default_factory=list)

    def list_by_status(self, *statuses: str) -> list[FakeUniverseRecord]:
        self.list_by_status_calls.append(statuses)
        return list(self.records)


@dataclass
class FakeAvailabilityStore:
    stale: list[SourceAvailability]
    upsert_calls: list[tuple[SourceAvailability, ...]] = field(default_factory=list)

    def stale_rows(self, *, ttl_days: int, now_utc: str | None = None) -> list[SourceAvailability]:
        return list(self.stale)

    def upsert_many(self, rows) -> int:
        self.upsert_calls.append(tuple(rows))
        return len(rows)


# ---------------------------------------------------------------------------
# Helpers.
# ---------------------------------------------------------------------------


def _make_row(epic: str, source: str = SOURCE_IG) -> SourceAvailability:
    return SourceAvailability(
        epic=epic,
        source=source,
        resolution=RESOLUTION_1M,
        source_symbol=None,
        status=STATUS_OK,
        origin=ORIGIN_DERIVED,
        history_min_days=30,
        latency_min=0,
        last_verified_utc=utc_iso_now(),
    )


def _make_daemon(
    tmp_path: Path,
    *,
    sources: list[FakeSource],
    stale: list[SourceAvailability] | None = None,
    universe: list[FakeUniverseRecord] | None = None,
    budget: Any = None,
    interval_s: int = 3600,
    sleep_fn=None,
):
    arm_path = tmp_path / "DISCOVERY_ARMED"
    state_path = tmp_path / "discovery_state.json"
    universe_store = FakeUniverseStore(records=universe or [])
    availability_store = FakeAvailabilityStore(stale=stale or [])
    return DiscoveryDaemon(
        sources=sources,
        universe_store=universe_store,
        availability_store=availability_store,
        budget=budget,
        arm_path=str(arm_path),
        state_path=str(state_path),
        interval_s=interval_s,
        sleep_fn=sleep_fn or (lambda _s: None),
    ), arm_path, state_path, universe_store, availability_store


# ---------------------------------------------------------------------------
# Tests.
# ---------------------------------------------------------------------------


def test_run_once_unarmed_does_nothing(tmp_path: Path) -> None:
    """The arm-flag is the only operator-visible gate — absent ⇒ zero work."""
    src = FakeSource(name_str=SOURCE_IG, rows=(_make_row("DAX"),))
    daemon, arm_path, state_path, _, _ = _make_daemon(tmp_path, sources=[src])
    # No arm() call → no flag file → is_armed returns False.
    assert not arm_path.exists()

    result = daemon.run_once()

    assert result.armed is False
    assert result.rows_written == 0
    assert result.stale_count == 0
    assert src.discover_calls == [], "unarmed cycle must not call discover()"
    # State file is still written — operator can see "skipped, not armed".
    assert state_path.exists()
    state = json.loads(state_path.read_text(encoding="utf-8"))
    assert state["armed"] is False


def test_run_once_armed_with_no_stale_does_nothing(tmp_path: Path) -> None:
    """Armed + fresh table ⇒ no ``discover`` calls (Plan D14: nothing stale ⇒ sleep)."""
    src = FakeSource(name_str=SOURCE_IG, rows=(_make_row("DAX"),))
    daemon, arm_path, state_path, _, _ = _make_daemon(tmp_path, sources=[src])
    arm(str(arm_path), by="dashboard")

    result = daemon.run_once()

    assert result.armed is True
    assert result.stale_count == 0
    assert result.rows_written == 0
    assert src.discover_calls == [], "no stale rows ⇒ no discover()"


def test_run_once_armed_with_stale_calls_each_source_once(tmp_path: Path) -> None:
    """Armed + stale ⇒ every registered source gets exactly one ``discover``."""
    dax_row = _make_row("IX.D.DAX.IFMM.IP")
    cac_row = _make_row("IX.D.CAC.IFE.IP")
    universe = [FakeUniverseRecord(epic=r.epic) for r in (dax_row, cac_row)]
    src_ig = FakeSource(name_str=SOURCE_IG, rows=(dax_row,))
    src_ls = FakeSource(name_str="ls", rows=(_make_row("IX.D.DAX.IFMM.IP", source="ls"),))
    daemon, arm_path, _, universe_store, avail_store = _make_daemon(
        tmp_path,
        sources=[src_ig, src_ls],
        stale=[dax_row],   # one stale row drives the cycle
        universe=universe,
    )
    arm(str(arm_path), by="dashboard")

    result = daemon.run_once()

    assert result.armed is True
    assert result.stale_count == 1
    assert result.rows_written == 2  # one row from each source
    assert len(src_ig.discover_calls) == 1
    assert len(src_ls.discover_calls) == 1
    # The universe's epic list is what sources receive (plan §6 C2 step 3).
    assert src_ig.discover_calls[0][0] == ("IX.D.DAX.IFMM.IP", "IX.D.CAC.IFE.IP")
    assert universe_store.list_by_status_calls == [("active", "discovered")]
    # upsert_many called once per source.
    assert len(avail_store.upsert_calls) == 2


def test_run_once_one_source_raising_does_not_kill_cycle(tmp_path: Path) -> None:
    """A raising Source lands in errors — the other sources still run (Plan §8.5)."""
    dax_row = _make_row("IX.D.DAX.IFMM.IP")
    src_good = FakeSource(name_str=SOURCE_IG, rows=(dax_row,))
    src_bad = FakeSource(name_str="bad", raise_in_discover=True)
    daemon, arm_path, _, _, _ = _make_daemon(
        tmp_path,
        sources=[src_good, src_bad],
        stale=[dax_row],
        universe=[FakeUniverseRecord(epic="IX.D.DAX.IFMM.IP")],
    )
    arm(str(arm_path), by="dashboard")

    result = daemon.run_once()

    assert result.rows_written == 1, "good source's row is still written"
    assert any("bad: discover raised" in e for e in result.errors), \
        f"bad source's exception should be in errors, got {result.errors}"
    assert len(src_good.discover_calls) == 1, "good source still ran"


def test_run_once_with_zero_probe_calls_records_no_spend(tmp_path: Path) -> None:
    """Default Phase-14 sources are net-free — budget ledger stays untouched."""
    dax_row = _make_row("IX.D.DAX.IFMM.IP")
    src = FakeSource(name_str=SOURCE_IG, rows=(dax_row,), probe_calls_used=0)
    budget = MagicMock()
    daemon, arm_path, _, _, _ = _make_daemon(
        tmp_path,
        sources=[src],
        stale=[dax_row],
        universe=[FakeUniverseRecord(epic="IX.D.DAX.IFMM.IP")],
        budget=budget,
    )
    arm(str(arm_path), by="dashboard")

    daemon.run_once()

    budget.record_spend.assert_not_called()


def test_run_once_with_nonzero_probe_calls_records_spend(tmp_path: Path) -> None:
    """A source that uses probes (e.g. Capital.com) books its spend under 'discovery'."""
    dax_row = _make_row("IX.D.DAX.IFMM.IP")
    src_a = FakeSource(name_str="capital", rows=(dax_row,), probe_calls_used=3)
    src_b = FakeSource(name_str="ig", rows=(dax_row,), probe_calls_used=5)
    budget = MagicMock()
    daemon, arm_path, _, _, _ = _make_daemon(
        tmp_path,
        sources=[src_a, src_b],
        stale=[dax_row],
        universe=[FakeUniverseRecord(epic="IX.D.DAX.IFMM.IP")],
        budget=budget,
    )
    arm(str(arm_path), by="dashboard")

    daemon.run_once()

    budget.record_spend.assert_called_once_with(8, kind="discovery")


def test_run_once_writes_state_file_with_documented_shape(tmp_path: Path) -> None:
    """The state file is the only way the operator sees "what did the last cycle do?"."""
    dax_row = _make_row("IX.D.DAX.IFMM.IP")
    src = FakeSource(name_str=SOURCE_IG, rows=(dax_row,))
    daemon, arm_path, state_path, _, _ = _make_daemon(
        tmp_path,
        sources=[src],
        stale=[dax_row],
        universe=[FakeUniverseRecord(epic="IX.D.DAX.IFMM.IP")],
    )
    arm(str(arm_path), by="dashboard")

    result = daemon.run_once()

    assert state_path.exists()
    payload = json.loads(state_path.read_text(encoding="utf-8"))
    assert set(payload.keys()) == {"ts_utc", "armed", "stale_count", "rows_written", "errors"}
    assert payload["armed"] is True
    assert payload["stale_count"] == 1
    assert payload["rows_written"] == 1
    assert payload["errors"] == []
    assert payload["ts_utc"] == result.ts_utc
    # No leftover .tmp sibling (atomic write).
    siblings = sorted(p.name for p in state_path.parent.iterdir())
    assert ".tmp" not in "".join(siblings), f"unexpected tmp file after cycle: {siblings}"


def test_cycle_result_is_frozen() -> None:
    """CycleResult is frozen — the state file's hash doesn't shift mid-write."""
    from source_registry.run import CycleResult

    cr = CycleResult(ts_utc="2026-08-22T19:00:00.000Z", armed=True,
                     stale_count=1, rows_written=2, errors=())
    with pytest.raises(Exception):  # FrozenInstanceError is a subclass of AttributeError
        cr.armed = False  # type: ignore[misc]


def test_run_forever_calls_run_once_in_loop_until_request_stop(tmp_path: Path) -> None:
    """The loop runs cycles until request_stop — sleep_fn is injected, no real sleep."""
    sleeps: list[float] = []

    def fake_sleep(s: float) -> None:
        sleeps.append(s)
        # request_stop after the first sleep, so run_forever exits after the second cycle.
        if len(sleeps) >= 1:
            daemon.request_stop()

    src = FakeSource(name_str=SOURCE_IG)  # never has stale rows ⇒ armed+stale-less ⇒ sleep immediately
    daemon, arm_path, _, _, _ = _make_daemon(
        tmp_path,
        sources=[src],
        interval_s=42,
        sleep_fn=fake_sleep,
    )
    arm(str(arm_path), by="dashboard")

    daemon.run_forever()

    # Two cycles ran (first + check-at-top), exactly one sleep in between.
    assert len(sleeps) == 1
    assert sleeps[0] == 42.0


def test_run_forever_stops_when_already_stopped_before_first_cycle(tmp_path: Path) -> None:
    """If request_stop is called before the loop starts, run_forever exits immediately."""
    src = FakeSource(name_str=SOURCE_IG)
    daemon, arm_path, _, _, _ = _make_daemon(
        tmp_path,
        sources=[src],
        interval_s=42,
        sleep_fn=lambda _s: None,
    )
    arm(str(arm_path), by="dashboard")
    daemon.request_stop()

    daemon.run_forever()  # must not run any cycle

    assert src.discover_calls == []


def test_main_with_once_flag_runs_one_cycle_and_exits(tmp_path: Path, monkeypatch) -> None:
    """End-to-end CLI smoke: ``--once`` runs a single unarmed cycle and returns 0."""
    arm_path = tmp_path / "DISCOVERY_ARMED"
    state_path = tmp_path / "discovery_state.json"
    pid_path = tmp_path / "discovery.pid"
    db_path = tmp_path / "trading_bot.sqlite"

    # Lazy cross-phase imports require a real Phase-9 store and a real Phase-14 store —
    # we cheat by pointing them at a fresh empty file. UniverseStore + SourceAvailabilityStore
    # both call ensure_schema() / open with idempotent DDL; against an empty file the daemon
    # works, but the cycle is short-circuited at "unarmed" because no flag file exists.
    db_path.touch()

    rc = main([
        "--pid-file", str(pid_path),
        "--state-path", str(state_path),
        "--universe-db", str(db_path),
        "--bars-db", str(db_path),
        "--arm-file", str(arm_path),
        "--once",
    ])
    assert rc == 0
    # PID file is created and cleaned up.
    assert not pid_path.exists()
    # State file is written even on a no-op cycle.
    assert state_path.exists()


def test_main_exits_zero_when_pid_file_names_alive_process(tmp_path: Path) -> None:
    """If the PID file already names a live process, ``main`` exits 0 without running."""
    pid_path = tmp_path / "discovery.pid"
    pid_path.parent.mkdir(parents=True, exist_ok=True)
    pid_path.write_text(str(__import__("os").getpid()), encoding="utf-8")  # this test's own PID
    rc = main([
        "--pid-file", str(pid_path),
        "--universe-db", str(tmp_path / "u.sqlite"),
        "--bars-db", str(tmp_path / "b.sqlite"),
        "--once",
    ])
    assert rc == 0


# ---------------------------------------------------------------------------
# PID-file helper smoke (verbatim pattern from data_foundation/run.py).
# ---------------------------------------------------------------------------


def test_pid_helpers_round_trip(tmp_path: Path) -> None:
    """_write_pid writes a live PID; _already_running sees it; _clear_pid removes it."""
    pid_path = tmp_path / "discovery.pid"
    _write_pid(pid_path)
    assert pid_path.exists()
    assert _already_running(pid_path) is True
    _clear_pid(pid_path)
    assert not pid_path.exists()
    assert _already_running(pid_path) is False


def test_already_running_false_for_stale_pid(tmp_path: Path) -> None:
    """A PID file pointing at a clearly-dead PID is not a conflict."""
    pid_path = tmp_path / "discovery.pid"
    pid_path.parent.mkdir(parents=True, exist_ok=True)
    # Pick a PID that almost certainly does not exist (very high).
    pid_path.write_text("99999999", encoding="utf-8")
    assert _already_running(pid_path) is False


def test_pid_alive_false_for_dead_pid() -> None:
    assert _pid_alive(99999999) is False


def test_iso_format_matches_store_convention() -> None:
    """The daemon's ISO format must match what ``SourceAvailabilityStore.stale_rows``
    uses, or lexicographic comparison in ``stale_rows`` would silently miss rows."""
    from datetime import datetime, timezone
    sample = datetime(2026, 8, 22, 19, 0, 0, 500_000, tzinfo=timezone.utc)
    assert _iso(sample) == "2026-08-22T19:00:00.500Z"


# ---------------------------------------------------------------------------
# Default sources — the net-free Phase-14 set in canonical order.
# ---------------------------------------------------------------------------


def test_default_sources_are_three_and_net_free() -> None:
    """The default source set is IG-derived + LS-static + Registry-YF — all probe_calls_used=0."""
    # Real duck-typed store: ``get(epic)`` returns a UniverseRecord-ähnliches Objekt.
    # (RegistryYFSource validates the status vocabulary in ``SourceAvailability.__post_init__``;
    # a bare MagicMock would fail with "invalid availability status: <MagicMock …>" — pinned here
    # so the canary stays loud.)
    universe_store = MagicMock()
    universe_store.get.return_value = type("Rec", (), {
        "epic": "IX.D.DAX.IFMM.IP",
        "yf_ticker": "DAX",
        "data_source_status": STATUS_OK,
    })()
    sources = _build_default_sources(universe_store=universe_store)
    assert [s.name() for s in sources] == ["ig", "ls", "yf"]
    # None of them makes a network call; all return probe_calls_used == 0.
    for s in sources:
        profile = s.discover(("IX.D.DAX.IFMM.IP",), max_probe_calls=8)
        assert profile.probe_calls_used == 0, \
            f"default source {s.name()} unexpectedly booked probe calls"
