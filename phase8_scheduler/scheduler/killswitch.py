"""Module 5 — the file-based kill-switch (``data/state/KILL``, Decision 8).

A dead-simple, **stateless** halt control: if the file exists, the daemon stops
attempting trades. Its own module precisely because two parties share it — ``safety.py``
(Module 6) and the loop *read* it every cycle, the auto-backoff trip and the later Web-UI
*write* it (one file = one responsibility). It works UI-independently and is operator-
touchable by hand (``touch data/state/KILL``).

The contract is **fail-soft — these functions never raise** (recorded in
``exceptions.py``): a data-collection daemon must not die on a flag-file blip, and the safe
direction of any ambiguity is "stay killed". So:

- :func:`is_set` is a pure existence check, robust to *any* content (incl. an empty
  hand-``touch``ed file or a half-written one — either still reads as halted).
- :func:`set_kill` writes a small JSON ``{reason, ts}`` payload **atomically** (``.tmp`` +
  ``os.replace`` — the package pattern, mirroring ``state.py`` / Phase-2), creating the
  parent dir if needed. By convention (concept §4) the backoff trip writes
  ``"auto:backoff"`` and the UI/operator writes ``"manual:<text>"``.
- :func:`clear_kill` removes the file (no-op if absent).
- :func:`read_reason` tolerantly recovers the reason for display: missing/empty/unparseable
  → ``None``; valid JSON object → its ``"reason"``; non-JSON plain text → the raw text (an
  operator may hand-write a reason).

The loud operator-facing log on a trip lives in the **runner** (the loop already logs
``critical("kill switch set: %s")``); this module is silent on the happy path and only logs
the genuine read-error path. Stdlib-only, imports nothing cross-phase. Repo conventions
apply (``from __future__ import annotations``, type hints + docstrings).
"""

from __future__ import annotations

import json
import logging
import os
from datetime import datetime, timezone
from pathlib import Path

logger = logging.getLogger("scheduler.killswitch")


def is_set(kill_path: str) -> bool:
    """Return whether the kill-switch is engaged — i.e. the file exists.

    Existence is the whole truth: content (or lack of it) is irrelevant, so an empty
    ``touch``ed file or a half-written one both read as halted (the fail-safe direction).
    """
    return Path(kill_path).exists()


def set_kill(kill_path: str, reason: str) -> None:
    """Engage the kill-switch, atomically recording ``reason`` + a UTC timestamp.

    Ensures the parent directory exists, then writes a JSON ``{"reason", "ts"}`` payload
    via ``.tmp`` + ``os.replace`` so the live file is never half-written. By convention the
    backoff trip passes ``"auto:backoff"`` and the UI/operator passes ``"manual:<text>"``.
    """
    path = Path(kill_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = {"reason": reason, "ts": datetime.now(timezone.utc).isoformat()}
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    os.replace(tmp, path)


def clear_kill(kill_path: str) -> None:
    """Disengage the kill-switch by deleting the file. No-op if it is absent (fail-soft)."""
    Path(kill_path).unlink(missing_ok=True)


def read_reason(kill_path: str) -> str | None:
    """Return the recorded kill reason for display, or ``None`` — fail-soft, never raises.

    Missing file → ``None``. Empty (hand-``touch``ed) file → ``None``. Valid JSON object →
    its ``"reason"`` (``None`` if the key is absent). Non-JSON plain text → the stripped raw
    text (an operator may hand-write a reason). An unreadable existing file → one WARNING +
    ``None`` (never swallow silently, never raise).
    """
    path = Path(kill_path)
    if not path.exists():
        return None
    try:
        raw = path.read_text(encoding="utf-8").strip()
    except OSError as exc:
        logger.warning("kill file at %s unreadable (%s)", path, exc)
        return None
    if not raw:
        return None
    try:
        data = json.loads(raw)
    except (ValueError, json.JSONDecodeError):
        return raw  # hand-written plain text
    if isinstance(data, dict):
        return data.get("reason")
    return raw  # valid JSON but not an object (e.g. a bare string) — return as-is
