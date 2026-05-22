"""SQLite persistence — the historical store.

``Database`` wraps a single ``sqlite3`` connection with typed CRUD helpers for
every Phase-2 table. No ORM. It stores and returns plain dicts; it never judges,
scores, or filters (that is the bot's job in later phases).

Phase isolation: this module receives plain dicts (e.g. ``Envelope.data`` or
``model.to_dict()`` from Phase 1) and never imports ``broker_wrapper``.
"""

from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from typing import Any

from persistence import migrations
from persistence.defaults import default_config_state
from persistence.schema import MIGRATIONS_DIR
from persistence.timeutil import parse_iso, utc_iso_now

# Column whitelists per table (everything except the autoincrement `id`).
# Inserts intersect these with the caller's dict, so unknown keys are ignored
# and column names never come from caller-controlled strings.
_TRADE_COLUMNS = (
    "deal_id", "deal_reference", "epic", "broker", "direction", "size",
    "open_level", "close_level", "currency", "open_ts", "close_ts",
    "hold_duration_min", "profit_loss", "status", "research_confidence",
    "gate_path", "session_date", "created_at", "updated_at",
)
_REWARD_COLUMNS = (
    "trade_id", "outcome_score_delta", "score_after", "win_loss", "pnl_raw",
    "process_score_delta", "veto_trigger_count", "gate_fail_count",
    "debate_confidence", "spread_at_entry_pct", "calculated_at",
)
_LESSON_COLUMNS = (
    "trade_id", "lesson_text", "market_context_json", "relevance_score",
    "used_in_research", "last_used_ts", "embedding_json", "embedding_model",
    "extracted_at",
)
_REGIME_COLUMNS = (
    "trade_id", "volatility_pct", "spread_pct", "drift_pct", "volume_z_score",
    "time_of_day_h", "market_status", "snapshot_ts",
)
_DECISION_COLUMNS = (
    "trade_id", "bull_summary", "bear_summary", "judge_reasoning",
    "debate_rounds", "judge_confidence", "veto_factors_json",
    "pre_trade_checks_json", "council_verdict", "council_summary", "stored_at",
)

# Score at/below which the bot stays conservative. The neutral start score is
# 50.0 (see defaults.py), which maps to KONSERVATIV — the bot earns AGGRESSIV
# only by pushing the score above neutral.
_RISK_THRESHOLD = 50.0
_DEFAULT_SCORE = 50.0


class Database:
    """Typed SQLite wrapper for all Phase-2 tables."""

    def __init__(self, db_path: str) -> None:
        """Open (or create) the SQLite database at ``db_path``.

        Enables ``row_factory`` for dict-like rows and turns on foreign-key
        enforcement so the ``ON DELETE CASCADE`` relationships work.
        """
        self.db_path = db_path
        self.conn = sqlite3.connect(db_path)
        self.conn.row_factory = sqlite3.Row
        self.conn.execute("PRAGMA foreign_keys = ON")

    # -- lifecycle ----------------------------------------------------------

    def run_migrations(self, migrations_dir: Path | str = MIGRATIONS_DIR) -> int:
        """Apply pending migrations and seed default config state.

        Returns the resulting schema version. Idempotent.
        """
        version = migrations.run_migrations(self.conn, migrations_dir)
        self._seed_defaults()
        return version

    def _seed_defaults(self) -> None:
        """Insert default ``ig_config_state`` rows without overwriting existing ones."""
        now = utc_iso_now()
        for key, value, note in default_config_state():
            self.conn.execute(
                "INSERT OR IGNORE INTO ig_config_state (key, value, updated_at, note) "
                "VALUES (?, ?, ?, ?)",
                (key, json.dumps(value), now, note),
            )
        self.conn.commit()

    def close(self) -> None:
        self.conn.close()

    def __enter__(self) -> "Database":
        return self

    def __exit__(self, *exc: Any) -> None:
        self.close()

    # -- internal helpers ---------------------------------------------------

    def _insert(
        self,
        table: str,
        record: dict[str, Any],
        columns: tuple[str, ...],
        json_fields: tuple[str, ...] = (),
    ) -> int:
        """Insert ``record`` into ``table`` using only whitelisted ``columns``.

        Dict/list values for any ``json_fields`` are serialized to JSON text.
        Returns the new row id.
        """
        rec = dict(record)
        for field in json_fields:
            if field in rec and isinstance(rec[field], (dict, list)):
                rec[field] = json.dumps(rec[field])
        cols = [c for c in columns if c in rec]
        placeholders = ", ".join("?" for _ in cols)
        sql = f"INSERT INTO {table} ({', '.join(cols)}) VALUES ({placeholders})"
        cur = self.conn.execute(sql, [rec[c] for c in cols])
        self.conn.commit()
        return int(cur.lastrowid)

    @staticmethod
    def _rows(cursor: sqlite3.Cursor) -> list[dict[str, Any]]:
        return [dict(row) for row in cursor.fetchall()]

    # -- trade_outcomes -----------------------------------------------------

    def insert_trade(self, trade: dict[str, Any]) -> int:
        """Insert a trade. Defaults: status=OPEN, broker=ig, created/updated=now.

        Returns the new row id.
        """
        now = utc_iso_now()
        record = dict(trade)
        record.setdefault("status", "OPEN")
        record.setdefault("broker", "ig")
        record.setdefault("created_at", now)
        record.setdefault("updated_at", now)
        return self._insert(
            "trade_outcomes", record, _TRADE_COLUMNS, json_fields=("gate_path",)
        )

    def update_trade_close(self, deal_id: str, close_data: dict[str, Any]) -> bool:
        """Mark a trade closed; compute ``hold_duration_min`` from open→close.

        ``close_data`` may carry ``close_level``, ``profit_loss``, ``close_ts``
        (defaults to now), and ``status`` (defaults to CLOSED). Returns False if
        no trade with ``deal_id`` exists.
        """
        existing = self.get_trade_by_deal_id(deal_id)
        if existing is None:
            return False
        now = utc_iso_now()
        close_ts = close_data.get("close_ts", now)
        status = close_data.get("status", "CLOSED")
        hold_min: float | None = None
        if existing.get("open_ts"):
            delta = parse_iso(close_ts) - parse_iso(existing["open_ts"])
            hold_min = delta.total_seconds() / 60.0
        self.conn.execute(
            "UPDATE trade_outcomes SET close_level = ?, close_ts = ?, "
            "profit_loss = ?, hold_duration_min = ?, status = ?, updated_at = ? "
            "WHERE deal_id = ?",
            (
                close_data.get("close_level"),
                close_ts,
                close_data.get("profit_loss"),
                hold_min,
                status,
                now,
                deal_id,
            ),
        )
        self.conn.commit()
        return True

    def get_open_trades(self) -> list[dict[str, Any]]:
        """All trades with status OPEN, oldest first."""
        cur = self.conn.execute(
            "SELECT * FROM trade_outcomes WHERE status = 'OPEN' ORDER BY id"
        )
        return self._rows(cur)

    def get_trade_by_deal_id(self, deal_id: str) -> dict[str, Any] | None:
        """Most recent trade for ``deal_id``, or None."""
        cur = self.conn.execute(
            "SELECT * FROM trade_outcomes WHERE deal_id = ? ORDER BY id DESC LIMIT 1",
            (deal_id,),
        )
        row = cur.fetchone()
        return dict(row) if row is not None else None

    def get_recent_trades(self, n: int = 8) -> list[dict[str, Any]]:
        """The ``n`` most recent trades, newest first (for Brain/Research context)."""
        cur = self.conn.execute(
            "SELECT * FROM trade_outcomes ORDER BY id DESC LIMIT ?", (n,)
        )
        return self._rows(cur)

    # -- reward_pts ---------------------------------------------------------

    def insert_reward(self, trade_id: int, reward: dict[str, Any]) -> int:
        """Insert a reward row for ``trade_id``. Defaults: calculated_at=now."""
        record = dict(reward)
        record["trade_id"] = trade_id
        record.setdefault("calculated_at", utc_iso_now())
        return self._insert("reward_pts", record, _REWARD_COLUMNS)

    def get_current_score(self) -> float:
        """Latest accumulated ``score_after``; ``50.0`` if no rewards exist yet."""
        cur = self.conn.execute(
            "SELECT score_after FROM reward_pts ORDER BY id DESC LIMIT 1"
        )
        row = cur.fetchone()
        return float(row["score_after"]) if row is not None else _DEFAULT_SCORE

    def get_risk_level(self) -> str:
        """``"AGGRESSIV"`` if current score is above neutral, else ``"KONSERVATIV"``."""
        return "AGGRESSIV" if self.get_current_score() > _RISK_THRESHOLD else "KONSERVATIV"

    # -- trade_lessons ------------------------------------------------------

    def insert_lesson(self, trade_id: int, lesson: dict[str, Any]) -> int:
        """Insert a lesson for ``trade_id``. Defaults: extracted_at=now."""
        record = dict(lesson)
        record["trade_id"] = trade_id
        record.setdefault("extracted_at", utc_iso_now())
        return self._insert(
            "trade_lessons", record, _LESSON_COLUMNS,
            json_fields=("market_context_json", "embedding_json"),
        )

    def get_recent_lessons(self, n: int = 5) -> list[dict[str, Any]]:
        """The ``n`` most recently extracted lessons, newest first."""
        cur = self.conn.execute(
            "SELECT * FROM trade_lessons ORDER BY id DESC LIMIT ?", (n,)
        )
        return self._rows(cur)

    def mark_lesson_used(self, lesson_id: int) -> None:
        """Increment ``used_in_research`` and stamp ``last_used_ts`` for a lesson."""
        self.conn.execute(
            "UPDATE trade_lessons SET used_in_research = used_in_research + 1, "
            "last_used_ts = ? WHERE id = ?",
            (utc_iso_now(), lesson_id),
        )
        self.conn.commit()

    # -- ig_config_state ----------------------------------------------------

    def get_config(self, key: str) -> Any | None:
        """Return the JSON-deserialized value for ``key``, or None if absent."""
        cur = self.conn.execute(
            "SELECT value FROM ig_config_state WHERE key = ?", (key,)
        )
        row = cur.fetchone()
        return json.loads(row["value"]) if row is not None else None

    def set_config(self, key: str, value: Any, note: str = "") -> None:
        """Upsert ``key`` with a JSON-serialized ``value`` and ``updated_at=now``."""
        self.conn.execute(
            "INSERT INTO ig_config_state (key, value, updated_at, note) "
            "VALUES (?, ?, ?, ?) "
            "ON CONFLICT(key) DO UPDATE SET "
            "value = excluded.value, updated_at = excluded.updated_at, note = excluded.note",
            (key, json.dumps(value), utc_iso_now(), note),
        )
        self.conn.commit()

    def get_all_config(self) -> dict[str, Any]:
        """All config keys mapped to their JSON-deserialized values."""
        cur = self.conn.execute("SELECT key, value FROM ig_config_state")
        return {row["key"]: json.loads(row["value"]) for row in cur.fetchall()}

    # -- V2 tables (Phase 9 fills; Phase 2 only stores) ---------------------

    def insert_regime_snapshot(self, trade_id: int, snapshot: dict[str, Any]) -> int:
        """Insert a market-regime snapshot for ``trade_id``. Defaults: snapshot_ts=now."""
        record = dict(snapshot)
        record["trade_id"] = trade_id
        record.setdefault("snapshot_ts", utc_iso_now())
        return self._insert("market_regime_snapshots", record, _REGIME_COLUMNS)

    def insert_decision_context(self, trade_id: int, context: dict[str, Any]) -> int:
        """Insert an AI decision-context row for ``trade_id``. Defaults: stored_at=now."""
        record = dict(context)
        record["trade_id"] = trade_id
        record.setdefault("stored_at", utc_iso_now())
        return self._insert(
            "decision_context", record, _DECISION_COLUMNS,
            json_fields=("veto_factors_json", "pre_trade_checks_json"),
        )
