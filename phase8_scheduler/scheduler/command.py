"""Module 12 helper — the file-based start/stop command channel (``scheduler_command.json``).

The Web-UI's pause/resume control (concept §12: ``POST /api/command -> scheduler_command.json
(start/stop)  # Daemon pollt``). Its own module precisely because two parties share it, exactly
like :mod:`scheduler.killswitch`: the Web-UI **writes** it, the runner loop **reads** it every
iteration (one file = one responsibility). It is operator-touchable by hand.

Semantics, deliberately distinct from the kill-switch:

- ``"stop"`` → the daemon **pauses** (keeps the process alive, does no trading work) until the
  command flips to ``"start"`` or the file is removed. The KILL file remains the *hard* stop
  (breaks the loop and exits); a UI stop is a soft, reversible pause so ``start`` can resume the
  same live process without a restart.
- ``"start"`` / missing file → the daemon runs the normal cycle (the default — no command file
  means current behavior, bit-identical).

The contract is **fail-soft — these functions never raise**: a data-collection daemon must not
die on a control-file blip, and the safe direction of any ambiguity is "run normally" (a corrupt
or unknown command reads as ``None`` ⇒ not paused). So:

- :func:`read_command` returns ``"start"`` | ``"stop"`` | ``None``; missing / empty / unparseable
  / unknown value → ``None``.
- :func:`write_command` writes a small JSON ``{cmd, ts}`` payload **atomically** (``.tmp`` +
  ``os.replace`` — the package pattern, mirroring ``killswitch.py`` / ``state.py``), creating the
  parent dir if needed. ``cmd`` must be ``"start"`` or ``"stop"`` (else ``ValueError`` — the writer
  is in-process, so a bad value is a programming error, not a runtime flag-file blip).
- :func:`clear_command` removes the file (no-op if absent) ⇒ back to the default (run normally).

Stdlib-only, imports nothing cross-phase. Repo conventions apply (``from __future__ import
annotations``, type hints + docstrings, logging to a module logger on stderr).
"""

from __future__ import annotations

import json
import logging
import os
from datetime import datetime, timezone
from pathlib import Path

logger = logging.getLogger("scheduler.command")

_VALID_COMMANDS: frozenset[str] = frozenset({"start", "stop"})


def read_command(command_path: str) -> str | None:
    """Return the current command — ``"start"`` | ``"stop"`` | ``None`` — fail-soft, never raises.

    Missing / empty / unreadable / unparseable file → ``None``. Valid JSON object → its ``"cmd"``
    if it is a known command, else ``None``. Any unknown value reads as ``None`` (the safe
    direction: an ambiguous control file must not silently pause the daemon).
    """
    path = Path(command_path)
    if not path.exists():
        return None
    try:
        raw = path.read_text(encoding="utf-8").strip()
    except OSError as exc:
        logger.warning("command file at %s unreadable (%s)", path, exc)
        return None
    if not raw:
        return None
    try:
        data = json.loads(raw)
    except (ValueError, json.JSONDecodeError):
        # Tolerate a hand-written bare word (e.g. ``stop``) as well as JSON.
        cmd = raw
    else:
        cmd = data.get("cmd") if isinstance(data, dict) else data
    if isinstance(cmd, str) and cmd in _VALID_COMMANDS:
        return cmd
    return None


def write_command(command_path: str, cmd: str) -> None:
    """Write ``cmd`` (``"start"`` or ``"stop"``) atomically with a UTC timestamp.

    Ensures the parent directory exists, then writes a JSON ``{"cmd", "ts"}`` payload via ``.tmp``
    + ``os.replace`` so the live file is never half-written. Raises ``ValueError`` on an invalid
    command — the writer is in-process (the Web-UI validates the request first), so a bad value is
    a programming error, not the kind of flag-file blip the readers tolerate.
    """
    if cmd not in _VALID_COMMANDS:
        raise ValueError(f"invalid command {cmd!r}; expected one of {sorted(_VALID_COMMANDS)}")
    path = Path(command_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = {"cmd": cmd, "ts": datetime.now(timezone.utc).isoformat()}
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    os.replace(tmp, path)


def clear_command(command_path: str) -> None:
    """Remove the command file → back to the default (run normally). No-op if absent (fail-soft)."""
    Path(command_path).unlink(missing_ok=True)
