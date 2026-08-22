"""Phase 14 (Discovery-Then-Deterministic) — the Discovery arm-flag.

A dead-simple, **stateless** operator control over the Discovery daemon: if the
file exists *and* parses to ``{"armed": true}``, the daemon runs; otherwise it
sleeps and does nothing. Its own module precisely because two parties share it
— the ``run.py`` daemon (C2) *reads* it every cycle, the Web-UI (C3) *writes*
it on the ARM/DISARM buttons. It works UI-independently and is operator-t
ouchable by hand (e.g. ``touch data/state/DISCOVERY_ARMED && echo '{"armed":
true, "by": "operator", "ts": "2026-08-22T19:00:00+00:00"}' > data/state/DISCOVERY_ARMED``).

The contract is **fail-soft — these functions never raise** (the same rule as
``scheduler/killswitch.py``, mirrored verbatim below). A data-collection daemon
must not die on a flag-file blip, and the safe direction of any ambiguity is
**"stay unarmed"** (D10) — the opposite of the kill-switch (where "stay killed"
is the safe direction). That inversion belongs in this docstring; copying the
killswitch file without flipping it back is exactly the kind of bug an
inattentive clone invites.

So:

- :func:`is_armed` is the *whole* truth of the file. **The safe direction is
  ``False``** — missing file, empty file (a hand-``touch``ed flag), broken JSON,
  ``{"armed": false}``, ``{"armed": "yes"}`` (string, not JSON-bool), or any
  shape without a literal JSON ``True`` in ``armed`` ⇒ ``False``. Only a strict
  ``armed == True`` reads as armed.
- :func:`arm` writes a small JSON ``{"armed": true, "by", "ts"}`` payload
  **atomically** (``.tmp`` + ``os.replace`` — the package pattern, mirroring
  ``killswitch.py`` / Phase-2 ``state.py``), creating the parent dir if needed.
  By convention the Web-UI passes ``by="dashboard"`` and the operator-script
  passes ``by="operator:<text>"``.
- :func:`disarm` removes the file (no-op if absent — fail-soft).
- :func:`read_state` tolerantly recovers the full payload for the UI display:
  missing/empty/unparseable → ``None``; valid JSON object → the dict. Never
  raises, so the Web-UI polling endpoint can call it every 7 s without a
  try/except cage.

Stdlib-only, imports nothing cross-phase. Repo conventions apply
(``from __future__ import annotations``, type hints + docstrings, one module =
one responsibility).
"""

from __future__ import annotations

import json
import logging
import os
from datetime import datetime, timezone
from pathlib import Path

logger = logging.getLogger("source_registry.arm")

# Default path matches the Web-UI constant (`_ARM_PATH` in `phase8_scheduler/webui/api.py`)
# and the daemon's default. Kept here as a single source of truth — modules that need it
# import this constant; never duplicate the literal in another file.
DEFAULT_ARM_PATH = Path("data") / "state" / "DISCOVERY_ARMED"


def is_armed(arm_path: str) -> bool:
    """Return whether Discovery is armed — i.e. the file exists *and* carries a strict ``armed: true``.

    **The safe direction is ``False``** (D10). The function only returns ``True`` when the
    file exists, parses as JSON, is a JSON object, has an ``"armed"`` key, and that key is
    the JSON boolean ``True`` exactly. Every other shape (missing file, empty file,
    unparseable bytes, non-object JSON, missing key, ``false``, ``"yes"`` / ``1`` /
    ``null`` / any non-bool-true) reads as ``False``. The daemon's first action every
    cycle is ``is_armed()`` → unscharf kostet null.
    """
    path = Path(arm_path)
    if not path.exists():
        return False
    try:
        raw = path.read_text(encoding="utf-8").strip()
    except OSError as exc:
        logger.warning("arm file at %s unreadable (%s)", path, exc)
        return False
    if not raw:
        return False
    try:
        data = json.loads(raw)
    except (ValueError, json.JSONDecodeError):
        return False
    if not isinstance(data, dict):
        return False
    return data.get("armed") is True


def arm(arm_path: str, by: str) -> None:
    """Engage Discovery, atomically recording ``by`` + a UTC timestamp.

    Ensures the parent directory exists, then writes a JSON
    ``{"armed": true, "by", "ts"}`` payload via ``.tmp`` + ``os.replace`` so the live file
    is never half-written (the package pattern, mirroring ``killswitch.set_kill`` and
    ``state.py``). By convention the Web-UI passes ``by="dashboard"`` and an operator
    script passes ``by="operator:<text>"``.
    """
    path = Path(arm_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = {"armed": True, "by": by, "ts": datetime.now(timezone.utc).isoformat()}
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    os.replace(tmp, path)


def disarm(arm_path: str) -> None:
    """Disengage Discovery by deleting the file. No-op if it is absent (fail-soft)."""
    Path(arm_path).unlink(missing_ok=True)


def read_state(arm_path: str) -> dict | None:
    """Return the recorded arm payload for the UI display, or ``None`` — fail-soft, never raises.

    Missing file → ``None``. Empty (hand-``touch``ed) file → ``None``. Unparseable JSON
    → ``None``. Valid JSON object → the dict (caller renders ``by``/``ts`` as it sees fit,
    and may ignore keys it doesn't know). Non-object JSON (a bare string, list, number)
    → ``None`` — the arm payload *is* an object by contract, anything else is malformed.
    """
    path = Path(arm_path)
    if not path.exists():
        return None
    try:
        raw = path.read_text(encoding="utf-8").strip()
    except OSError as exc:
        logger.warning("arm file at %s unreadable (%s)", path, exc)
        return None
    if not raw:
        return None
    try:
        data = json.loads(raw)
    except (ValueError, json.JSONDecodeError):
        return None
    if not isinstance(data, dict):
        return None
    return data
