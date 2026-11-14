"""Phase 17 C-4 — the LLM routing in the composition root.

``phase8_scheduler/scripts/wiring.py`` used to construct **seven** LLM clients
inline (``LLMClient(...)``), each with its own model/key/limits. Since C-4 there
is exactly **one** construction site — :func:`_build_llm` — and the routing
decision lives in :mod:`scheduler.llm_profiles`.

These tests pin:

* the ``anthropic`` profile is **bit-identical** to the old inline calls
  (same class, same model, same token limit) — the default must not change the
  bot's behaviour;
* a non-Anthropic profile really produces an ``OpenAICompatLLMClient`` with the
  provider's **quirks** (the §15 fields) — the routing is not a label;
* the debate config renames all three roles when the profile moves the debate
  (Phase 6 rewrites ``client.model`` per role, so a rename that is missing here
  would call Anthropic models on a foreign provider).

No network, no keyring (the credential module is stubbed), no LLM.
"""

from __future__ import annotations

import sys
import types
from pathlib import Path
from typing import Any

import pytest

# scripts/ -> phase8_scheduler/ (so ``from scripts.wiring import ...`` resolves)
_PROJECT_DIR = Path(__file__).resolve().parent.parent
if str(_PROJECT_DIR) not in sys.path:
    sys.path.insert(0, str(_PROJECT_DIR))

from scheduler.llm_profiles import LLM_PROFILES, LLM_ROLES, RoleSpec  # noqa: E402
from scripts.wiring import _build_llm, _debate_config  # noqa: E402


@pytest.fixture
def no_keyring(monkeypatch: pytest.MonkeyPatch) -> None:
    """Stub ``research.credentials`` — ``_build_llm`` reads the Anthropic key from
    there (lazy import inside the function ⇒ ``sys.modules`` wins). A unit test
    must never touch the real OS keyring (Plan §8)."""
    monkeypatch.setitem(
        sys.modules,
        "research.credentials",
        types.SimpleNamespace(get_credential=lambda *a, **k: "fake-key-not-a-secret"),
    )


def test_build_llm_anthropic_profile_is_bit_identical_for_research(
    no_keyring: None,
) -> None:
    """The default profile must not change the bot: the research client is the
    same ``LLMClient`` with the same model and the same token limit as before
    C-4 (Plan §6 C-4, AK „bit-identical")."""
    from research.llm_client import LLMClient

    client = _build_llm(
        "research",
        "anthropic",
        default_model="claude-sonnet-4-6",
        max_tokens=1024,
        temperature=0.2,
        timeout_s=30.0,
    )

    assert isinstance(client, LLMClient)
    assert client.model == "claude-sonnet-4-6"
    assert client.max_tokens == 1024
    assert client.temperature == 0.2
    assert client.timeout_s == 30.0


def test_build_llm_research_m3_returns_openai_compat_minimax(no_keyring: None) -> None:
    """With the ``research_m3`` profile the research role is served by the
    OpenAI-compatible client on the MiniMax endpoint (Plan §6 baseline, re-activated
    2026-11-03)."""
    from research.llm_openai_compat import OpenAICompatLLMClient

    client = _build_llm(
        "research",
        "research_m3",
        default_model="claude-sonnet-4-6",
        max_tokens=1024,
        temperature=0.2,
        timeout_s=30.0,
    )

    assert isinstance(client, OpenAICompatLLMClient)
    assert client.model == "MiniMax-M3"
    assert client.base_url == "https://api.minimax.io/v1"
    assert client.api_key_service == "trading-bot-minimax-bot"
    assert client.api_key_username == "api_key"
    # The provider's documented quirk reaches the client (MiniMax docs 2026-11-03).
    assert client.max_tokens_field == "max_completion_tokens"
    # The profile's own limits win over the phase config's.
    assert client.max_tokens == 8192
    assert client.timeout_s == 90.0


def test_build_llm_passes_provider_quirks_to_openai_compat(
    no_keyring: None, monkeypatch: pytest.MonkeyPatch
) -> None:
    """§15 T27/T28: the provider's quirks reach the client — the wiring must use
    ``client_kwargs(spec)``, not a hand-written subset. The OpenAI entry is the
    one with two quirks (``max_completion_tokens`` + no ``temperature``)."""
    from research.llm_openai_compat import OpenAICompatLLMClient

    monkeypatch.setitem(
        LLM_PROFILES,
        "t_openai",
        {role: RoleSpec(provider="openai", model="gpt-x") for role in LLM_ROLES},
    )
    try:
        client = _build_llm(
            "research",
            "t_openai",
            default_model="claude-sonnet-4-6",
            max_tokens=1024,
            temperature=0.2,
            timeout_s=30.0,
        )
    finally:
        del LLM_PROFILES["t_openai"]

    assert isinstance(client, OpenAICompatLLMClient)
    assert client.max_tokens_field == "max_completion_tokens"
    assert client.send_temperature is False
    assert client.base_url == "https://api.openai.com/v1"


def test_debate_config_all_m3_renames_all_three_roles() -> None:
    """Phase 6's ``ask_agent`` rewrites ``client.model`` per role from the
    ``DebateConfig`` — so a profile that moves the debate must rename **all
    three** (bull/bear/judge), otherwise the debate would call Anthropic models
    on the foreign provider."""
    cfg = _debate_config("all_m3")

    assert cfg.model_bull == "MiniMax-M3"
    assert cfg.model_bear == "MiniMax-M3"
    assert cfg.model_judge == "MiniMax-M3"
    # The profile's token limit wins over the debate default.
    assert cfg.max_tokens_agent == 8192
    assert cfg.max_tokens_judge == 8192


def test_debate_config_all_m3_raises_only_the_wall_clock_cap() -> None:
    """Phase 17 §26.2 G2 (Generalprobe 2026-11-13, Nikinger 2026-11-14): the Phase-6
    wall-clock cap (120 s) is calibrated for Haiku/Sonnet (15–25 s per debate). M3
    thinks — median ≈ 45 s, p90 ≈ 110 s, 2 of 24 debates aborted at 120 s
    (``DebateBudgetExceeded``). A profile that moves the debate gets 240 s; every
    other hard cap stays the Phase-6 default (one change, not a cap sweep)."""
    from debate.models import DebateConfig

    cfg = _debate_config("all_m3")
    default = DebateConfig()

    assert cfg.wall_clock_timeout_s == 240.0
    assert cfg.max_cumulative_output_tokens == default.max_cumulative_output_tokens
    assert cfg.max_cumulative_input_tokens == default.max_cumulative_input_tokens
    assert cfg.max_total_calls == default.max_total_calls


def test_build_llm_all_m3_instinct_gets_room_to_think(no_keyring: None) -> None:
    """Phase 17 §26.2 G1 (Generalprobe 2026-11-13, Nikinger 2026-11-14): on M3 the
    instinct extraction ran into ``finish_reason=length`` in 4 of 5 calls at 8 192
    tokens (the one success used 8 026; Haiku answers the same input in 360–524).
    Under ``all_m3`` the instinct role gets 32 768 tokens and 480 s — built through
    ``_build_llm`` with the real call-site values, so the pin covers the wiring,
    not only the profile table. Every other role keeps 8 192 / 90 s."""
    from scripts.wiring import _INSTINCT_EXTRACTOR_MAX_TOKENS, _INSTINCT_EXTRACTOR_TIMEOUT_S

    instinct = _build_llm(
        "instinct",
        "all_m3",
        default_model="claude-haiku-4-5-20251001",
        max_tokens=_INSTINCT_EXTRACTOR_MAX_TOKENS,
        temperature=0.2,
        timeout_s=_INSTINCT_EXTRACTOR_TIMEOUT_S,
    )
    assert instinct.model == "MiniMax-M3"
    assert instinct.max_tokens == 32_768
    assert instinct.timeout_s == 480.0

    for role in LLM_ROLES:
        if role == "instinct":
            continue
        spec = LLM_PROFILES["all_m3"][role]
        assert (spec.max_tokens, spec.timeout_s) == (8192, 90.0), role


def test_debate_config_anthropic_is_default() -> None:
    """With the ``anthropic`` profile nothing is renamed — the config is the
    plain Phase-6 default."""
    from debate.models import DebateConfig

    cfg = _debate_config("anthropic")
    default = DebateConfig()

    assert cfg.model_bull == default.model_bull
    assert cfg.model_bear == default.model_bear
    assert cfg.model_judge == default.model_judge
    assert cfg.max_tokens_agent == default.max_tokens_agent
    assert cfg.max_tokens_judge == default.max_tokens_judge
    assert cfg.wall_clock_timeout_s == default.wall_clock_timeout_s


def test_build_llm_unknown_profile_raises_before_any_client(no_keyring: None) -> None:
    """A typo in the profile must fail loudly — and **before** a client (and its
    keyring read) is built."""
    with pytest.raises(ValueError, match="unknown llm profile"):
        _build_llm(
            "research",
            "research_glmm",
            default_model="claude-sonnet-4-6",
            max_tokens=1024,
            temperature=0.2,
            timeout_s=30.0,
        )


def test_build_llm_returns_a_client_with_the_expected_surface(no_keyring: None) -> None:
    """Both client classes must expose the surface the callers rely on:
    ``ask_candidate`` + ``.model`` + ``.max_tokens`` (Phase 5/6 read them)."""
    for profile in ("anthropic", "research_m3"):
        client: Any = _build_llm(
            "research",
            profile,
            default_model="claude-sonnet-4-6",
            max_tokens=1024,
            temperature=0.2,
            timeout_s=30.0,
        )
        assert callable(client.ask_candidate)
        assert isinstance(client.model, str)
        assert isinstance(client.max_tokens, int)
