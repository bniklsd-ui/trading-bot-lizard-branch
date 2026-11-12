"""Phase 17 F-2 — the LLM input recorder in the composition root.

``debate_log.json`` stores the *answers* of Bull/Bear/Judge, not the prompt the
Judge actually saw (measured 2026-11-11: 339 debates, none with the Judge's
input) — a later model comparison on identical input is therefore not
reconstructible from the log. :func:`scripts.wiring._record_llm_io` writes one
JSONL line per LLM call (input **and** output) so it becomes reconstructible.

These tests pin the three contract points of Plan §26 F-2:

* one line per call, with the **model at call time** (Phase 6 rewrites
  ``client.model`` per role on exactly this object — a proxy class would break
  the role renaming, hence the instance-level wrapper);
* the error case writes ``error`` and re-raises the **unchanged** exception;
* a write error of the recorder never breaks the call and is logged **exactly
  once per process** as ``critical``.

No network, no keyring, no LLM — a fake client stands in.
"""

from __future__ import annotations

import json
import logging
import sys
from pathlib import Path
from typing import Any

import pytest

# scripts/ -> phase8_scheduler/ (so ``from scripts.wiring import ...`` resolves)
_PROJECT_DIR = Path(__file__).resolve().parent.parent
if str(_PROJECT_DIR) not in sys.path:
    sys.path.insert(0, str(_PROJECT_DIR))

from scripts import wiring  # noqa: E402
from scripts.wiring import _record_llm_io  # noqa: E402


class _FakeClient:
    """Minimal stand-in for an LLM client (no network, no keyring, no LLM)."""

    def __init__(self, answer: Any = None, error: BaseException | None = None) -> None:
        self.model = "MiniMax-M3"
        self.temperature = 0.4
        self.last_usage: dict[str, Any] | None = {"input_tokens": 10, "output_tokens": 20}
        self.last_finish_reason: str | None = "stop"
        self._answer = answer
        self._error = error
        self.calls: list[tuple[str, str, dict]] = []

    def ask_candidate(self, system: str, user: str, json_schema: dict) -> Any:
        self.calls.append((system, user, json_schema))
        if self._error is not None:
            raise self._error
        return self._answer


def test_recorder_writes_one_line_per_call_with_the_model_at_call_time(tmp_path: Path) -> None:
    """One line per call — and the recorded ``model`` is the one the call ran
    with, not the one the client was built with (Phase 6 renames the roles on
    the instance before every turn)."""
    path = tmp_path / "llm_io.jsonl"
    client = _FakeClient(answer={"epic": "IX.D.DAX.IFMM.IP"})

    wrapped = _record_llm_io(client, path, "debate")
    assert wrapped is client  # the instance is returned, not a proxy

    wrapped.ask_candidate("system-bull", "user-bull", {"type": "object"})
    client.model = "claude-sonnet-4-6"          # Phase 6 renames the role
    client.temperature = 0.1
    wrapped.ask_candidate("system-judge", "user-judge", {"type": "object"})

    lines = path.read_text(encoding="utf-8").strip().split("\n")
    assert len(lines) == 2
    first, second = (json.loads(line) for line in lines)

    assert first["role"] == "debate"
    assert first["model"] == "MiniMax-M3"
    assert first["temperature"] == 0.4
    assert first["system"] == "system-bull"
    assert first["user"] == "user-bull"
    assert first["json_schema"] == {"type": "object"}
    assert first["answer"] == {"epic": "IX.D.DAX.IFMM.IP"}
    assert first["error"] is None
    assert first["usage"] == {"input_tokens": 10, "output_tokens": 20}
    assert first["finish_reason"] == "stop"
    assert first["ts"].endswith("Z")

    # The second call carries the model that was set *before* it.
    assert second["model"] == "claude-sonnet-4-6"
    assert second["temperature"] == 0.1
    assert second["system"] == "system-judge"


def test_recorder_writes_error_and_reraises_the_exception(tmp_path: Path) -> None:
    """A failed call is recorded (``error``) and the exception is re-raised
    **unchanged** — the recorder must not swallow or replace it."""
    path = tmp_path / "llm_io.jsonl"
    boom = RuntimeError("llm down")
    client = _FakeClient(error=boom)

    wrapped = _record_llm_io(client, path, "research")
    with pytest.raises(RuntimeError) as excinfo:
        wrapped.ask_candidate("system", "user", {})
    assert excinfo.value is boom

    record = json.loads(path.read_text(encoding="utf-8").strip())
    assert record["role"] == "research"
    assert record["error"] == repr(boom)
    assert record["answer"] is None
    assert record["system"] == "system"


def test_recorder_write_error_does_not_break_the_call_and_logs_once_critical(
    tmp_path: Path,
    caplog: pytest.LogCaptureFixture,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A broken recorder must never break a call — and it must be visible
    exactly **once per process** (visible, but no K5 noise)."""
    monkeypatch.setattr(wiring, "_RECORDER_ERROR_LOGGED", False)
    blocked = tmp_path / "blocked"          # a file where a directory is needed
    blocked.write_text("not a directory", encoding="utf-8")
    path = blocked / "llm_io.jsonl"

    client = _FakeClient(answer={"ok": True})
    wrapped = _record_llm_io(client, path, "research")

    with caplog.at_level(logging.CRITICAL, logger="phase8.wiring"):
        assert wrapped.ask_candidate("system", "user", {}) == {"ok": True}
        assert wrapped.ask_candidate("system", "user", {}) == {"ok": True}

    criticals = [rec for rec in caplog.records if rec.levelno == logging.CRITICAL]
    assert len(criticals) == 1, [rec.getMessage() for rec in caplog.records]
    assert "llm_io recorder failed" in criticals[0].getMessage()
    assert not path.exists()
