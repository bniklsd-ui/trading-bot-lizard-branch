"""Phase 17 C-1 — the LLM routing register (``scheduler/llm_profiles.py``).

Pure data + pure functions: no network, no keyring, no broker, no LLM. The file
under test is the **single place** that decides which provider serves which role
(Plan §6 C-1, §14, §15 T25–T31), so these tests pin:

* the shipped profiles (anthropic = unchanged, ``research_glm`` = only research
  moves, ``all_glm`` = every role moves);
* the four failure classes of ``check_llm_profile`` (unknown profile, claude on
  a foreign provider, missing price line, missing budget exemption) plus the
  coding-plan ban;
* the per-provider well-formedness of **every** shipped entry (a new provider is
  a data commit — the test must not have to be edited for it);
* the quirk-field coverage of ``client_kwargs`` (a new quirk field without a
  mapping must fail loudly — T29).
"""

from __future__ import annotations

import pytest

from scheduler.llm_profiles import (
    LLM_PROFILES,
    LLM_ROLES,
    PROVIDERS,
    ProviderSpec,
    RoleSpec,
    check_llm_profile,
    check_provider,
    client_kwargs,
    role_spec,
)

# A pricing table that is *not* the real one — the real price lines land in C-3
# (P4). The shipped-profile test with the real table comes with C-3.
_PRICING = {
    "claude-sonnet-4-6": (3.0, 15.0),
    "claude-haiku-4-5-20251001": (1.0, 5.0),
    "glm-5.3": (1.4, 4.4),
}
_DEFAULTS = {
    "research": "claude-sonnet-4-6",
    "debate": "claude-sonnet-4-6",
    "lesson": "claude-haiku-4-5-20251001",
    "instinct": "claude-haiku-4-5-20251001",
    "reflect": "claude-haiku-4-5-20251001",
    "paper_debate": "claude-sonnet-4-6",
}
_EXEMPT = ("glm-5.3",)


# --------------------------------------------------------------------------- #
# Profiles
# --------------------------------------------------------------------------- #


def test_anthropic_profile_keeps_phase_defaults() -> None:
    """The ``anthropic`` profile binds **no** override — every role keeps the model,
    the token limit and the timeout of its own phase config (T17: the profile is
    a code default, the bot's behaviour without a flip is bit-identical)."""
    for role in LLM_ROLES:
        spec = role_spec("anthropic", role)
        assert spec.provider == "anthropic"
        assert spec.model is None
        assert spec.max_tokens is None
        assert spec.timeout_s is None


def test_research_glm_routes_only_research_to_zai() -> None:
    """Flip 1 (``research_glm``): only the research role moves to the z.ai/GLM
    provider — every other role stays on Anthropic (T5: one profile = one
    variable; a mixed state would make later model comparisons unreadable)."""
    research = role_spec("research_glm", "research")
    assert research.provider == "zai"
    assert research.model == "glm-5.3"
    for role in LLM_ROLES:
        if role == "research":
            continue
        assert role_spec("research_glm", role).provider == "anthropic", role


def test_all_glm_routes_every_role_to_zai() -> None:
    """Flip 2 (``all_glm``): every role moves to the same provider + model."""
    for role in LLM_ROLES:
        spec = role_spec("all_glm", role)
        assert spec.provider == "zai", role
        assert spec.model == "glm-5.3", role


# --------------------------------------------------------------------------- #
# check_llm_profile — the four failure classes
# --------------------------------------------------------------------------- #


def test_check_rejects_unknown_profile() -> None:
    """A typo in the config default must fail loudly at startup, not as a
    ``KeyError`` deep inside the wiring."""
    with pytest.raises(ValueError, match="unknown llm profile"):
        check_llm_profile(
            "research_glmm",
            pricing=_PRICING,
            default_models=_DEFAULTS,
            exempt_models=_EXEMPT,
        )


def test_check_rejects_claude_on_foreign_provider() -> None:
    """A ``claude-*`` id on a non-Anthropic provider does not exist there."""
    LLM_PROFILES["_t_claude_on_foreign"] = {
        role: RoleSpec(provider="zai", model="claude-sonnet-4-6") for role in LLM_ROLES
    }
    try:
        with pytest.raises(ValueError, match="claude model"):
            check_llm_profile(
                "_t_claude_on_foreign",
                pricing=_PRICING,
                default_models=_DEFAULTS,
                exempt_models=_EXEMPT,
            )
    finally:
        del LLM_PROFILES["_t_claude_on_foreign"]


def test_check_rejects_model_without_pricing() -> None:
    """A model without a price line would be metered as 0 € — the check refuses
    the profile instead."""
    LLM_PROFILES["_t_no_pricing"] = {
        **{role: RoleSpec(provider="anthropic") for role in LLM_ROLES},
        "research": RoleSpec(provider="anthropic", model="claude-mystery-1"),
    }
    try:
        with pytest.raises(ValueError, match="no price line"):
            check_llm_profile(
                "_t_no_pricing",
                pricing=_PRICING,
                default_models=_DEFAULTS,
                exempt_models=_EXEMPT,
            )
    finally:
        del LLM_PROFILES["_t_no_pricing"]


def test_check_rejects_non_exempt_foreign_model() -> None:
    """A foreign model that is not in ``budget_exempt_models`` would count against
    the daily token budget — the model id lives in three places, and this check
    is what catches the forgotten one (T7)."""
    LLM_PROFILES["_t_not_exempt"] = {
        **{role: RoleSpec(provider="anthropic") for role in LLM_ROLES},
        "research": RoleSpec(provider="zai", model="glm-5.3"),
    }
    try:
        with pytest.raises(ValueError, match="budget_exempt_models"):
            check_llm_profile(
                "_t_not_exempt",
                pricing=_PRICING,
                default_models=_DEFAULTS,
                exempt_models=(),
            )
    finally:
        del LLM_PROFILES["_t_not_exempt"]


def test_check_rejects_coding_plan_endpoint() -> None:
    """Plan §14.1: the bot must never point at a coding-plan endpoint — the z.ai
    usage policy bans using it outside officially supported tools, and violations
    lead to throttling, lockout and (from the third time) a ban."""
    LLM_PROFILES["_t_coding"] = {
        **{role: RoleSpec(provider="anthropic") for role in LLM_ROLES},
        "research": RoleSpec(provider="_t_coding_provider", model="glm-5.3"),
    }
    PROVIDERS["_t_coding_provider"] = ProviderSpec(
        kind="openai_compat",
        base_url="https://api.z.ai/api/coding/paas/v4",
        api_key_service="trading-bot-zai-bot",
        api_key_username="api_key",
    )
    try:
        with pytest.raises(ValueError, match="coding-plan endpoint"):
            check_llm_profile(
                "_t_coding",
                pricing=_PRICING,
                default_models=_DEFAULTS,
                exempt_models=_EXEMPT,
            )
    finally:
        del LLM_PROFILES["_t_coding"]
        del PROVIDERS["_t_coding_provider"]


# --------------------------------------------------------------------------- #
# check_provider — per-entry rules (Plan §15.4 C-1)
# --------------------------------------------------------------------------- #


def test_check_provider_rejects_http_missing_key_bad_field_and_coding_host() -> None:
    """Four rejection classes in one test (each with its own provider name in the
    message): plain http, a missing keyring service, an unknown token-limit
    field, and a **host** that carries "coding" (not only a path — Alibaba's
    ``coding-intl.dashscope.aliyuncs.com`` and KUAE carry it in the host, T31)."""
    with pytest.raises(ValueError, match="https://"):
        check_provider(
            "p_http",
            ProviderSpec(
                kind="openai_compat",
                base_url="http://api.example.com/v1",
                api_key_service="s",
                api_key_username="api_key",
            ),
        )
    with pytest.raises(ValueError, match="api_key_service"):
        check_provider(
            "p_no_service",
            ProviderSpec(
                kind="openai_compat",
                base_url="https://api.example.com/v1",
                api_key_username="api_key",
            ),
        )
    with pytest.raises(ValueError, match="max_tokens_field"):
        check_provider(
            "p_bad_field",
            ProviderSpec(
                kind="openai_compat",
                base_url="https://api.example.com/v1",
                api_key_service="s",
                api_key_username="api_key",
                max_tokens_field="max_output_tokens",
            ),
        )
    with pytest.raises(ValueError, match="coding-plan endpoint"):
        check_provider(
            "p_coding_host",
            ProviderSpec(
                kind="openai_compat",
                base_url="https://coding-intl.dashscope.aliyuncs.com/v1",
                api_key_service="s",
                api_key_username="api_key",
            ),
        )
    # The anthropic kind needs no endpoint, no keyring and no quirks.
    check_provider("anthropic", PROVIDERS["anthropic"])


def test_every_shipped_provider_is_well_formed() -> None:
    """Every shipped entry must pass its own rules — a new provider is a **data**
    commit, so this test may not need an edit for it (superset, not equality)."""
    for name, spec in PROVIDERS.items():
        check_provider(name, spec)
    assert set(PROVIDERS) >= {
        "anthropic",
        "zai",
        "minimax",
        "openai",
        "deepseek",
        "qwen",
        "kimi",
        "openrouter",
        "opencode_zen",
    }


def test_client_kwargs_covers_every_quirk_field() -> None:
    """T29: ``client_kwargs`` is the ONE mapping of a provider entry onto the
    client kwargs. A new quirk field without a mapping here would silently not
    reach the client — this test makes that fail loudly."""
    from dataclasses import fields

    mapped = set(client_kwargs(PROVIDERS["openai"]))
    expected = {f.name for f in fields(ProviderSpec)} - {"kind"}
    assert mapped == expected


def test_check_accepts_shipped_profiles() -> None:
    """The shipped profiles pass the check against the **real** configuration —
    the real price table (``research.models``), the real default models of the
    three phases and the real exempt list (``SchedulerConfig``).

    Added with C-3: the GLM price lines only exist from that commit on, and a
    commit may not leave a red test behind. The default models are the ones
    ``build_scheduler`` hands to ``check_llm_profile`` (C-4) — the same source
    of truth, so a profile that passes here is a profile the daemon accepts.
    """
    from debate.models import DebateConfig
    from research.models import ResearchConfig
    from reward.models import RewardConfig
    from scheduler.config import SchedulerConfig

    cfg = SchedulerConfig()
    research_cfg = ResearchConfig()
    debate_cfg = DebateConfig()
    reward_cfg = RewardConfig()
    default_models = {
        "research": research_cfg.model,
        "debate": debate_cfg.model_judge,
        "paper_debate": debate_cfg.model_judge,
        "lesson": reward_cfg.lesson_model,
        "instinct": reward_cfg.lesson_model,
        "reflect": reward_cfg.lesson_model,
    }

    for profile in ("anthropic", "research_glm", "all_glm"):
        check_llm_profile(
            profile,
            pricing=research_cfg.pricing_usd_per_mtok,
            default_models=default_models,
            exempt_models=cfg.budget_exempt_models,
        )
