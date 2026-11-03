"""Tests for ``scripts/store_minimax_key.py`` (Phase 17 C-6 — generic key seeder).

Loaded via ``importlib`` by file path — root ``scripts/`` is deliberately **not** an
importable package (the phases already collide on a ``scripts.wiring`` module name),
so this phase-less harness is loaded the same way as ``test_check_doc_rotation.py``.

The seeder must stay a **generic** tool: every provider of the bot has its own
keyring namespace (``trading-bot-zai-bot``, ``trading-bot-minimax-bot``, …), and the
script name is only a historical artifact. The test pins that ``--service`` /
``--username`` really reach the keyring — the key lives **only** in the OS keyring,
never in a file (Hard Rule 1).
"""

from __future__ import annotations

import importlib.util
from pathlib import Path

_SCRIPT_PATH = Path(__file__).resolve().parent.parent / "scripts" / "store_minimax_key.py"
_spec = importlib.util.spec_from_file_location("store_minimax_key", _SCRIPT_PATH)
assert _spec is not None and _spec.loader is not None
store_minimax_key_mod = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(store_minimax_key_mod)


def test_status_honours_service_and_username(monkeypatch, capsys) -> None:
    """``--status`` reads the key from the **given** namespace, not from the
    script's default one — that is what makes one script usable for every
    provider of the bot (Phase 17 C-6 / §14.1: ``trading-bot-zai-bot`` /
    ``api_key``).

    The keyring is monkeypatched — a unit test must never touch the real OS
    keyring (and the key itself never leaves it).
    """
    seen: list[tuple[str, str]] = []

    def _fake_get_password(service: str, username: str) -> str | None:
        seen.append((service, username))
        return "fake-key-not-a-secret"

    monkeypatch.setattr(store_minimax_key_mod.keyring, "get_password", _fake_get_password)

    rc = store_minimax_key_mod.main(
        ["--status", "--service", "trading-bot-zai-bot", "--username", "api_key"]
    )

    assert rc == 0
    assert seen == [("trading-bot-zai-bot", "api_key")]
    out = capsys.readouterr().out
    assert "trading-bot-zai-bot/api_key" in out
    # The value itself is never printed (only a ✓/✗ marker).
    assert "fake-key-not-a-secret" not in out


def test_status_defaults_to_the_dev_harness_namespace(monkeypatch, capsys) -> None:
    """Without ``--service``/``--username`` the script keeps its historical
    default (the dev-harness key) — the bot's namespaces are opt-in, so the
    isolation pattern of M-1 stays intact."""
    seen: list[tuple[str, str]] = []

    def _fake_get_password(service: str, username: str) -> str | None:
        seen.append((service, username))
        return None

    monkeypatch.setattr(store_minimax_key_mod.keyring, "get_password", _fake_get_password)

    rc = store_minimax_key_mod.main(["--status"])

    assert rc == 0
    assert seen == [("trading-bot-minimax", "minimax_api_key")]
    assert "trading-bot-minimax/minimax_api_key" in capsys.readouterr().out
