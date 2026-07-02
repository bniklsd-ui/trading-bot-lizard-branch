"""v1.6 (Phase-8 hotfix Step 0) — the per-cycle diagnostic health log.

No network, no broker, no LLM: pure file I/O against ``tmp_path``, plus a ``caplog`` probe of
the write-failure CRITICAL and the malformed-line WARNING. Mirrors ``test_killswitch.py``'s
style (fail-soft file module, no fixtures beyond ``tmp_path``/``caplog``).
"""

from __future__ import annotations

import json
import logging
from datetime import datetime, timezone

import pytest

from scheduler import observability as exported_observability
from scheduler import observability


def _log_path(tmp_path) -> str:
    """A nested path so parent-dir auto-creation is covered."""
    return str(tmp_path / "state" / "research_health.jsonl")


def _ts() -> datetime:
    return datetime(2026, 7, 2, 9, 5, tzinfo=timezone.utc)


def test_record_cycle_appends_valid_jsonl(tmp_path) -> None:
    """One call writes exactly one well-formed JSON line with all fields present."""
    path = _log_path(tmp_path)
    health = {"IX.D.DAX.IFMM.IP": {"status": "full", "missing": [], "errors": {}}}

    observability.record_cycle(
        path, ts=_ts(), context_health=health, picked=True, n=1, reason=None, abort_detail=None
    )

    lines = open(path, encoding="utf-8").read().splitlines()
    assert len(lines) == 1
    record = json.loads(lines[0])
    assert record["ts"] == _ts().isoformat()
    assert record["context_health"] == health
    assert record["picked"] is True
    assert record["n"] == 1
    assert record["reason"] is None
    assert record["abort_detail"] is None


def test_multiple_cycles_accumulate(tmp_path) -> None:
    """Repeated calls append, never overwrite — one line per cycle."""
    path = _log_path(tmp_path)
    for i in range(3):
        observability.record_cycle(
            path, ts=_ts(), context_health={}, picked=False, n=0,
            reason="LLM_ABSTAIN", abort_detail=f"cycle {i}",
        )

    lines = open(path, encoding="utf-8").read().splitlines()
    assert len(lines) == 3
    assert [json.loads(line)["abort_detail"] for line in lines] == ["cycle 0", "cycle 1", "cycle 2"]


def test_missing_parent_dir_is_created(tmp_path) -> None:
    """The nested ``data/state/`` directory does not need to pre-exist."""
    path = str(tmp_path / "a" / "b" / "c" / "research_health.jsonl")
    observability.record_cycle(
        path, ts=_ts(), context_health={}, picked=True, n=1, reason=None, abort_detail=None
    )
    assert (tmp_path / "a" / "b" / "c" / "research_health.jsonl").exists()


def test_none_context_health_defaults_to_empty_dict(tmp_path) -> None:
    """A ``None`` health snapshot (e.g. a cap-blocked cycle) is stored as ``{}``, not null."""
    path = _log_path(tmp_path)
    observability.record_cycle(
        path, ts=_ts(), context_health=None, picked=False, n=0,
        reason="CAP_BLOCK", abort_detail=None,
    )
    record = json.loads(open(path, encoding="utf-8").read().splitlines()[0])
    assert record["context_health"] == {}


def test_write_failure_is_logged_critical_and_swallowed(
    tmp_path, caplog: pytest.LogCaptureFixture
) -> None:
    """A write failure never raises out of ``record_cycle`` — logged critical, swallowed.

    Forces a real ``OSError`` without monkeypatching stdlib globals: the "log path" is made
    to be an existing *directory*, so ``Path(path).open("a")`` raises ``IsADirectoryError``
    (an ``OSError`` subclass) — a realistic, self-contained failure mode.
    """
    path = _log_path(tmp_path)
    import os
    os.makedirs(path)  # path itself is a directory, not a file

    with caplog.at_level(logging.CRITICAL, logger="scheduler.observability"):
        observability.record_cycle(  # must NOT raise
            path, ts=_ts(), context_health={}, picked=True, n=1, reason=None, abort_detail=None
        )

    crit = [r for r in caplog.records if r.levelno == logging.CRITICAL]
    assert len(crit) == 1


# --- iter_records (operator/reader tooling) --------------------------------


def test_iter_records_reads_back_written_records(tmp_path) -> None:
    """A round-trip: write two cycles, read them back in order via iter_records."""
    path = _log_path(tmp_path)
    observability.record_cycle(
        path, ts=_ts(), context_health={}, picked=True, n=1, reason=None, abort_detail=None
    )
    observability.record_cycle(
        path, ts=_ts(), context_health={}, picked=False, n=0,
        reason="LLM_ABSTAIN", abort_detail="weak setup",
    )

    records = list(observability.iter_records(path))
    assert len(records) == 2
    assert records[0]["picked"] is True
    assert records[1]["abort_detail"] == "weak setup"


def test_iter_records_missing_file_yields_nothing(tmp_path) -> None:
    """No log file yet (daemon hasn't run a WINDOW cycle) → an empty iterator, not an error."""
    path = str(tmp_path / "never_written.jsonl")
    assert list(observability.iter_records(path)) == []


def test_iter_records_skips_malformed_trailing_line(
    tmp_path, caplog: pytest.LogCaptureFixture
) -> None:
    """A truncated/malformed line (interrupted append) is skipped with a WARNING, not raised."""
    path = _log_path(tmp_path)
    observability.record_cycle(
        path, ts=_ts(), context_health={}, picked=True, n=1, reason=None, abort_detail=None
    )
    # Simulate an interrupted append: a truncated trailing line.
    with open(path, "a", encoding="utf-8") as f:
        f.write('{"ts": "2026-07-02T09:10:00+00:00", "picked": fal')  # cut off mid-write

    with caplog.at_level(logging.WARNING, logger="scheduler.observability"):
        records = list(observability.iter_records(path))

    assert len(records) == 1  # only the well-formed first record survives
    warn = [r for r in caplog.records if r.levelno == logging.WARNING]
    assert len(warn) == 1


def test_exported_from_package_root() -> None:
    """``from scheduler import observability`` is the same module object."""
    assert exported_observability is observability
