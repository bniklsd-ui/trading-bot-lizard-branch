"""JSON state — the operational store.

Short-lived, fast-access state written as JSON files. Three files, three
lifetimes:

- ``ig_state.json``        — account/positions snapshot; "fresh" if < 60s old.
- ``ig_config.json``       — static bot config; changed only on explicit command.
- ``turbo_candidates.json``— research output; TTL 30 min, self-clearing on expiry.

Writes are atomic (temp file + ``os.replace``) so a crash mid-write never leaves
a half-written file. Phase isolation: dicts in, dicts out; no ``broker_wrapper``
import.
"""

from __future__ import annotations

import json
import os
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

from persistence.timeutil import parse_iso

ACCOUNT_STATE_FILE = "ig_state.json"
BOT_CONFIG_FILE = "ig_config.json"
# Legacy name; content = DAX-CFD candidates, not turbos/options. Do NOT rename —
# Phase-2/Phase-5 Gate-2 contract depends on this exact filename.
# (Adjusted for Phase-4 Step-0 terminology fix — concept-demanded; file unchanged.)
CANDIDATES_FILE = "turbo_candidates.json"

CANDIDATES_TTL_MIN = 30
ACCOUNT_FRESH_S = 60


def _utcnow() -> datetime:
    """Current UTC time. Indirected so tests can monkeypatch the clock."""
    return datetime.now(timezone.utc)


def _format_iso(dt: datetime) -> str:
    """Format a datetime as ISO 8601 UTC with ms precision and Z suffix."""
    return dt.strftime("%Y-%m-%dT%H:%M:%S.") + f"{dt.microsecond // 1000:03d}Z"


class StateManager:
    """Reads/writes the operational JSON state files in ``state_dir``."""

    def __init__(self, state_dir: str) -> None:
        """Create ``state_dir`` if needed and remember the file paths."""
        self.state_dir = Path(state_dir)
        self.state_dir.mkdir(parents=True, exist_ok=True)
        self._account_path = self.state_dir / ACCOUNT_STATE_FILE
        self._config_path = self.state_dir / BOT_CONFIG_FILE
        self._candidates_path = self.state_dir / CANDIDATES_FILE

    # -- internal helpers ---------------------------------------------------

    @staticmethod
    def _atomic_write(path: Path, payload: dict[str, Any]) -> None:
        tmp = path.with_suffix(path.suffix + ".tmp")
        tmp.write_text(json.dumps(payload, indent=2, default=str), encoding="utf-8")
        os.replace(tmp, path)

    @staticmethod
    def _read(path: Path) -> dict[str, Any] | None:
        if not path.exists():
            return None
        return json.loads(path.read_text(encoding="utf-8"))

    # -- ig_state.json ------------------------------------------------------

    def save_account_state(
        self, account: dict[str, Any], positions: list[dict[str, Any]]
    ) -> None:
        """Write the account snapshot, stamping ``last_updated`` with now.

        ``session_active`` defaults to True if the account dict doesn't carry it.
        """
        state = dict(account)
        state["open_positions"] = list(positions)
        state.setdefault("session_active", True)
        state["last_updated"] = _format_iso(_utcnow())
        self._atomic_write(self._account_path, state)

    def load_account_state(self) -> dict[str, Any] | None:
        """Return the account snapshot, or None if it has never been written."""
        return self._read(self._account_path)

    def is_account_state_fresh(self, max_age_s: int = ACCOUNT_FRESH_S) -> bool:
        """True if the snapshot exists and its ``last_updated`` is < ``max_age_s`` old."""
        state = self.load_account_state()
        if not state or "last_updated" not in state:
            return False
        age = (_utcnow() - parse_iso(state["last_updated"])).total_seconds()
        return 0 <= age < max_age_s

    # -- ig_config.json -----------------------------------------------------

    def load_bot_config(self) -> dict[str, Any]:
        """Return the static bot config. Raises FileNotFoundError if missing."""
        config = self._read(self._config_path)
        if config is None:
            raise FileNotFoundError(
                f"Bot config not found at {self._config_path}. "
                "Write it once via save_bot_config()."
            )
        return config

    def save_bot_config(self, config: dict[str, Any]) -> None:
        """Persist the static bot config (overwrites any existing file)."""
        self._atomic_write(self._config_path, config)

    # -- turbo_candidates.json ----------------------------------------------

    def save_candidates(self, candidates: list[dict[str, Any]]) -> None:
        """Write research candidates with a 30-minute TTL stamped from now."""
        now = _utcnow()
        payload = {
            "generated_at": _format_iso(now),
            "ttl_minutes": CANDIDATES_TTL_MIN,
            "expires_at": _format_iso(now + timedelta(minutes=CANDIDATES_TTL_MIN)),
            "session_date": now.strftime("%Y-%m-%d"),
            "candidates": list(candidates),
        }
        self._atomic_write(self._candidates_path, payload)

    def load_candidates(self) -> list[dict[str, Any]]:
        """Return fresh candidates, or ``[]``.

        If the file is missing, expired, or holds an empty list, it is removed
        and ``[]`` is returned (empty = no trade this session).
        """
        data = self._read(self._candidates_path)
        if data is None:
            return []
        if self._is_expired(data):
            self.clear_candidates()
            return []
        candidates = data.get("candidates", [])
        if not candidates:
            self.clear_candidates()
            return []
        return candidates

    def clear_candidates(self) -> None:
        """Delete the candidates file if it exists."""
        self._candidates_path.unlink(missing_ok=True)

    def candidates_are_fresh(self) -> bool:
        """True if the file exists, is unexpired, and holds a non-empty list."""
        data = self._read(self._candidates_path)
        if data is None or self._is_expired(data):
            return False
        return bool(data.get("candidates"))

    @staticmethod
    def _is_expired(data: dict[str, Any]) -> bool:
        expires_at = data.get("expires_at")
        if not expires_at:
            return True
        return _utcnow() >= parse_iso(expires_at)
