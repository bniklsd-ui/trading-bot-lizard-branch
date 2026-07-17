"""S7 tests — abstain_report.py. Golden-output against a tmp_path DB. No network, no AI."""

from __future__ import annotations

import sqlite3

from scripts.abstain_report import build_report

_CREATE_TABLE = """
CREATE TABLE abstain_records (
    record_id           TEXT PRIMARY KEY,
    created_utc          TEXT NOT NULL,
    epic                 TEXT,
    stage                TEXT NOT NULL,
    reason               TEXT NOT NULL,
    detail               TEXT NOT NULL DEFAULT '',
    context_json         TEXT NOT NULL DEFAULT '{}',
    lesson               TEXT,
    lesson_extracted     INTEGER NOT NULL DEFAULT 0
)
"""

_FIXTURE_ROWS = [
    ("r1", "2026-07-11T09:00:00.000Z", "IX.D.DAX.IFMM.IP", "gate", "reason_gate_time_window", 0),
    ("r2", "2026-07-11T09:05:00.000Z", "IX.D.DAX.IFMM.IP", "veto", "reason_veto_spread", 0),
    ("r3", "2026-07-11T09:10:00.000Z", "IX.D.DAX.IFMM.IP", "debate", "reason_debate_abstain", 1),
    ("r4", "2026-07-11T09:15:00.000Z", None, "research_empty", "reason_no_candidates", 0),
]


def _seed_db(path) -> None:
    conn = sqlite3.connect(str(path))
    conn.execute(_CREATE_TABLE)
    for record_id, created_utc, epic, stage, reason, lesson_extracted in _FIXTURE_ROWS:
        conn.execute(
            "INSERT INTO abstain_records "
            "(record_id, created_utc, epic, stage, reason, lesson, lesson_extracted) "
            "VALUES (?, ?, ?, ?, ?, ?, ?)",
            (record_id, created_utc, epic, stage, reason,
             "a lesson" if lesson_extracted else None, lesson_extracted),
        )
    conn.commit()
    conn.close()


def test_report_golden_output(tmp_path):
    db_path = tmp_path / "test.sqlite"
    _seed_db(db_path)

    report = build_report(str(db_path), recent_n=10)

    expected = "\n".join([
        "=== Abstain-Records Report ===",
        "",
        "Counts by reason:",
        "  reason_debate_abstain: 1",
        "  reason_gate_time_window: 1",
        "  reason_no_candidates: 1",
        "  reason_veto_spread: 1",
        "",
        "Lesson coverage: 1/4",
        "",
        "Last 10 record(s):",
        "  [-] 2026-07-11T09:15:00.000Z research_empty reason_no_candidates -",
        "  [L] 2026-07-11T09:10:00.000Z debate reason_debate_abstain IX.D.DAX.IFMM.IP",
        "  [-] 2026-07-11T09:05:00.000Z veto reason_veto_spread IX.D.DAX.IFMM.IP",
        "  [-] 2026-07-11T09:00:00.000Z gate reason_gate_time_window IX.D.DAX.IFMM.IP",
    ])
    assert report == expected


def test_report_empty_db(tmp_path):
    db_path = tmp_path / "empty.sqlite"
    conn = sqlite3.connect(str(db_path))
    conn.execute(_CREATE_TABLE)
    conn.commit()
    conn.close()

    report = build_report(str(db_path))

    expected = "\n".join([
        "=== Abstain-Records Report ===",
        "",
        "Counts by reason:",
        "  (none)",
        "",
        "Lesson coverage: 0/0",
        "",
        "Last 10 record(s):",
        "  (none)",
    ])
    assert report == expected


_PAPER_CREATE_TABLE = """
CREATE TABLE paper_trades (
    paper_id            TEXT PRIMARY KEY,
    abstain_record_id   TEXT NOT NULL,
    variant             TEXT NOT NULL,
    epic                TEXT NOT NULL,
    direction           TEXT NOT NULL,
    created_utc         TEXT NOT NULL,
    entry_level         REAL NOT NULL,
    stop_distance       REAL NOT NULL,
    limit_distance      REAL,
    time_stop_utc       TEXT NOT NULL,
    status              TEXT NOT NULL DEFAULT 'OPEN',
    resolved_utc        TEXT,
    exit_reason         TEXT,
    exit_level          REAL,
    pnl_points           REAL,
    r_multiple          REAL,
    council_confidence  INTEGER,
    lesson              TEXT,
    lesson_extracted    INTEGER NOT NULL DEFAULT 0,
    context_json        TEXT NOT NULL DEFAULT '{}'
)
"""


def _seed_paper_trades(path) -> None:
    conn = sqlite3.connect(str(path))
    conn.execute(_PAPER_CREATE_TABLE)
    rows = [
        # abs-1: both sides resolved, both lost -> abstain validated
        ("p1", "abs-1", "SHADOW_BUY", "X", "BUY", "2026-07-11T09:00:00.000Z", "RESOLVED", "SL", -30.0),
        ("p2", "abs-1", "SHADOW_SELL", "X", "SELL", "2026-07-11T09:00:00.000Z", "RESOLVED", "SL", -30.0),
        # abs-2: both sides resolved, one won -> abstain not validated
        ("p3", "abs-2", "SHADOW_BUY", "X", "BUY", "2026-07-11T09:10:00.000Z", "RESOLVED", "TP", 45.0),
        ("p4", "abs-2", "SHADOW_SELL", "X", "SELL", "2026-07-11T09:10:00.000Z", "RESOLVED", "SL", -30.0),
        # abs-3: still open -> not counted in the resolved-pairs denominator
        ("p5", "abs-3", "SHADOW_BUY", "X", "BUY", "2026-07-11T09:20:00.000Z", "OPEN", None, None),
        ("p6", "abs-3", "SHADOW_SELL", "X", "SELL", "2026-07-11T09:20:00.000Z", "OPEN", None, None),
    ]
    for paper_id, abstain_id, variant, epic, direction, created, status, exit_reason, pnl in rows:
        conn.execute(
            "INSERT INTO paper_trades (paper_id, abstain_record_id, variant, epic, direction, "
            "created_utc, entry_level, stop_distance, limit_distance, time_stop_utc, status, "
            "exit_reason, pnl_points) VALUES (?,?,?,?,?,?,18000,30,45,?,?,?,?)",
            (paper_id, abstain_id, variant, epic, direction, created, created, status,
             exit_reason, pnl),
        )
    conn.commit()
    conn.close()


def test_report_paper_section_golden_output(tmp_path):
    db_path = tmp_path / "test.sqlite"
    _seed_db(db_path)
    _seed_paper_trades(db_path)

    report = build_report(str(db_path), recent_n=10, include_paper=True)

    expected_tail = "\n".join([
        "",
        "=== Paper-Trades Report ===",
        "",
        "Counts by variant:",
        "  SHADOW_BUY: 3",
        "  SHADOW_SELL: 3",
        "",
        "Counts by exit (or status if still open):",
        "  OPEN: 2",
        "  SL: 3",
        "  TP: 1",
        "",
        "Abstain-Validierungsquote: 1/2 resolved pairs (both shadow sides negative or breakeven)",
    ])
    assert report.endswith(expected_tail)


def test_report_without_paper_flag_is_bit_identical_to_block_a(tmp_path):
    """``include_paper=False`` (the default) never touches paper_trades — the table
    doesn't even need to exist."""
    db_path = tmp_path / "test.sqlite"
    _seed_db(db_path)  # no paper_trades table created at all

    report = build_report(str(db_path), recent_n=10)  # default include_paper=False

    assert "Paper-Trades Report" not in report


def test_report_respects_recent_n(tmp_path):
    db_path = tmp_path / "test.sqlite"
    _seed_db(db_path)

    report = build_report(str(db_path), recent_n=2)

    lines = report.splitlines()
    recent_section = lines[lines.index("Last 2 record(s):") + 1:]
    assert len(recent_section) == 2
    assert "2026-07-11T09:15:00.000Z" in recent_section[0]
    assert "2026-07-11T09:10:00.000Z" in recent_section[1]
