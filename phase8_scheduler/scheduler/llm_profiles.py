"""Phase 17 C-1 — which LLM serves which role (T4/T5/T16 + §14/§15 T25–T31).

Pure data + pure functions. Imported by the composition root
(``phase8_scheduler/scripts/wiring.py``) and by the config check; imports nothing
cross-phase (stdlib only). A profile maps every role to a :class:`RoleSpec`;
``model``/``max_tokens``/``timeout_s`` = ``None`` keep the phase config's own
value, so the ``"anthropic"`` profile is **bit-identical** to the pre-Phase-17
wiring.

**One provider = one data entry.** T25: exactly two client classes exist
(:class:`research.llm_client.LLMClient` for Anthropic-native,
:class:`research.llm_openai_compat.OpenAICompatLLMClient` for everything else) —
there is no ``if provider == …`` branch anywhere. A new provider is therefore a
pure data commit on this file (plus its price line + exempt entry when it
becomes *active*); ``check_llm_profile`` names the forgotten piece at startup.

**Provider-level request quirks** (T26/T27) live as three fields on
:class:`ProviderSpec` — never model-level, because Phase 6's ``ask_agent``
rewrites ``client.model`` per debate role, so a model-keyed quirk would decide
for the wrong model. The three quirks are the ones that are actually documented
per provider:

* ``max_tokens_field`` — ``"max_tokens"`` or ``"max_completion_tokens"``
  (the OpenAI GPT-5 line wants the latter),
* ``send_temperature`` — some reasoning models reject the field outright,
* ``extra_body`` — non-standard body fields (``thinking`` / ``enable_thinking``).

The defaults reproduce the **pre-§15 payload byte for byte** (T28): key order
``model, messages, max_tokens, temperature, response_format`` and no extra
fields. ``extra_body`` is merged **first** (client-owned keys always win) and
may not contain a reserved key — that is rejected in the *client constructor*,
the one choke point the bot and the smoke script share.

**The bot never talks to a coding plan.** T31: ``check_provider`` rejects any
``base_url`` that contains ``"coding"`` anywhere (case-insensitive) — the z.ai
Coding Plan endpoint (``/api/coding/paas/v4``) is for the executor harness, and
its usage policy bans use outside officially supported tools. The bot uses the
general APIs: MiniMax (Abo/M Plan, ``https://api.minimax.io/v1`` — the active
provider since 2026-11-03) or z.ai pay-per-use
(``https://api.z.ai/api/paas/v4``, reserve).

Live status per entry is a **comment** on the entry (``# doc <date> <url> · live: —``),
never a data field (T30): a gateway smoke proves the *model family*, not the
native endpoint's ``base_url``/auth/field names. An entry counts as flip-ready
only after a **native** smoke (Stufe 2).
"""

from __future__ import annotations

from dataclasses import dataclass, field, fields
from typing import Any, Mapping

LLM_ROLES: tuple[str, ...] = ("research", "debate", "lesson", "instinct", "reflect", "paper_debate")

#: The only two token-limit field names a client may send (T27).
_MAX_TOKENS_FIELDS: tuple[str, ...] = ("max_tokens", "max_completion_tokens")

#: Provider kinds the two client classes understand (T25).
_PROVIDER_KINDS: tuple[str, ...] = ("anthropic", "openai_compat")


@dataclass(frozen=True)
class ProviderSpec:
    """One endpoint + its credentials + its request quirks.

    Attributes:
        kind: ``"anthropic"`` (native SDK) or ``"openai_compat"`` (everything
            else — OpenAI, z.ai/GLM, DeepSeek, Qwen, Kimi, OpenRouter, …).
        base_url: API base for ``openai_compat``; ``/chat/completions`` is
            appended by the client. ``None`` for ``anthropic`` (the SDK has its
            own base).
        api_key_service: OS-keyring **service** name holding the API key.
            Never the live bot's ``tradingbot`` namespace — every provider gets
            its own (isolation pattern from M1).
        api_key_username: OS-keyring **username** under that service.
        max_tokens_field: which payload key carries the token limit (T27).
        send_temperature: whether the payload may carry ``temperature`` (T27).
        extra_body: non-standard body fields merged into the payload (T27);
            may not contain a client-owned key (rejected by the client).
    """

    kind: str
    base_url: str | None = None
    api_key_service: str | None = None
    api_key_username: str | None = None
    # §15 T26/T27: provider-level request quirks (never model-level — P6 ask_agent rewrites
    # client.model per role). Defaults reproduce the pre-§15 payload byte for byte (T28).
    max_tokens_field: str = "max_tokens"
    send_temperature: bool = True
    extra_body: Mapping[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class RoleSpec:
    """What one role's client looks like.

    Attributes:
        provider: key into :data:`PROVIDERS`.
        model: model id override; ``None`` keeps the phase config's own model.
        max_tokens: token-limit override; ``None`` keeps the phase config's.
        timeout_s: transport timeout override; ``None`` keeps the phase config's.
    """

    provider: str
    model: str | None = None
    max_tokens: int | None = None
    timeout_s: float | None = None


PROVIDERS: dict[str, ProviderSpec] = {
    # --- Anthropic (native SDK) — unchanged, live since Phase 4 ------------------
    "anthropic": ProviderSpec(kind="anthropic"),
    # --- z.ai / GLM — Reserve-Eintrag, kein Profil (Planwechsel 2026-11-03 → MiniMax)
    # doc 2026-10-19 docs.z.ai/api-reference/llm/chat-completion · live: —
    "zai": ProviderSpec(
        kind="openai_compat",
        base_url="https://api.z.ai/api/paas/v4",
        api_key_service="trading-bot-zai-bot",
        api_key_username="api_key",
    ),
    # --- MiniMax (Abo-Kontingent M Plan, gültig bis 2026-11-15) — aktiver Bot-Provider
    # doc 2026-11-03 platform.minimax.io/docs/api-reference/text-openai-api ·
    #      platform.minimax.io/docs/guides/text-generation.md · live: —
    # Quirks (Doku 2026-11-03): das Token-Limit-Feld für neue Integrationen ist
    # ``max_completion_tokens`` (``max_tokens`` = Legacy, wird aber akzeptiert);
    # ``temperature``/``top_p`` werden **ignoriert**, nicht abgelehnt ⇒
    # ``send_temperature`` bleibt True. ``thinking`` ist default AN — für
    # ``MiniMax-M3`` abschaltbar (``{"type": "disabled"}``), für
    # ``MiniMax-M3.1-Flash`` ein 400 (Doku: „Thinking cannot be turned off").
    "minimax": ProviderSpec(
        kind="openai_compat",
        base_url="https://api.minimax.io/v1",
        api_key_service="trading-bot-minimax-bot",
        api_key_username="api_key",
        max_tokens_field="max_completion_tokens",
    ),
    # --- OpenAI — die GPT-5-Linie will max_completion_tokens und lehnt temperature ab
    # doc 2026-10-19 platform.openai.com (403 für WebFetch; indirekter Beleg über die
    # Microsoft-Foundry-Doku) · live: —
    "openai": ProviderSpec(
        kind="openai_compat",
        base_url="https://api.openai.com/v1",
        api_key_service="trading-bot-openai-bot",
        api_key_username="api_key",
        max_tokens_field="max_completion_tokens",
        send_temperature=False,
    ),
    # --- DeepSeek (Denk-Modus default an) ---------------------------------------
    # doc 2026-10-19 api-docs.deepseek.com/api/create-chat-completion · live: —
    "deepseek": ProviderSpec(
        kind="openai_compat",
        base_url="https://api.deepseek.com",
        api_key_service="trading-bot-deepseek-bot",
        api_key_username="api_key",
    ),
    # --- Qwen (DashScope, international) ----------------------------------------
    # doc 2026-10-19 alibabacloud …/compatibility-of-openai-with-dashscope
    # (zeigt workspace-spezifische Hosts — base_url ggf. anpassen) · live: —
    "qwen": ProviderSpec(
        kind="openai_compat",
        base_url="https://dashscope-intl.aliyuncs.com/compatible-mode/v1",
        api_key_service="trading-bot-qwen-bot",
        api_key_username="api_key",
    ),
    # --- Kimi / Moonshot (max_tokens deprecated) --------------------------------
    # doc 2026-10-19 platform.kimi.ai/docs/api/chat · live: —
    "kimi": ProviderSpec(
        kind="openai_compat",
        base_url="https://api.moonshot.ai/v1",
        api_key_service="trading-bot-kimi-bot",
        api_key_username="api_key",
        max_tokens_field="max_completion_tokens",
    ),
    # --- OpenRouter (Gateway; nicht der M1-Key „openrouter") --------------------
    # doc 2026-10-19 M1-Smoke 2026-07 (Memory) · live: —
    "openrouter": ProviderSpec(
        kind="openai_compat",
        base_url="https://openrouter.ai/api/v1",
        api_key_service="trading-bot-openrouter-bot",
        api_key_username="api_key",
    ),
    # --- OpenCode Zen (Gateway) — eigener API-Key, NIE ~/.local/share/opencode/auth.json
    # doc 2026-10-19 opencode.ai/docs/zen · live: —
    "opencode_zen": ProviderSpec(
        kind="openai_compat",
        base_url="https://opencode.ai/inference/openai/v1",
        api_key_service="trading-bot-opencode-bot",
        api_key_username="api_key",
    ),
}

_ANTHROPIC = RoleSpec(provider="anthropic")
# The MiniMax research model — the Plan-§6 baseline, re-activated as the bot's
# provider on 2026-11-03 (Planwechsel z.ai → MiniMax Abo/M Plan).
# **Provisional**: the Nikinger confirms the model after the C-7 family smoke.
# max_tokens=8192 (not the §6 baseline 4096): MiniMax-M3 thinks by default and the
# reasoning tokens count against the limit — a too-small limit yields
# ``finish_reason=length`` with an **empty** content (MiniMax doc 2026-11-03; Plan
# §15.6 failure table). timeout_s=90 leaves room for the reasoning block.
_M3 = RoleSpec(provider="minimax", model="MiniMax-M3", max_tokens=8192, timeout_s=90.0)
# Phase 17 §26.2 G1 (Generalprobe 2026-11-13, Nikinger 2026-11-14): the instinct
# extraction thinks far longer than every other role — 4 of 5 calls ended with
# finish_reason=length at 8 192 (the one success used 8 026; Haiku answers the same
# ~2 600-token input in 360–524). The role is not time-critical ⇒ 4× the limit; the
# timeout covers 32 768 tokens at ≥ 68 tok/s (measured 120–160). The call is
# synchronous in the trade-close path (reward/recorder.py instinct_hook): a slow
# call only delays the next cycle. M3's output ceiling is undocumented (1 M context).
_M3_INSTINCT = RoleSpec(provider="minimax", model="MiniMax-M3", max_tokens=32_768, timeout_s=480.0)

LLM_PROFILES: dict[str, dict[str, RoleSpec]] = {
    "anthropic": {role: _ANTHROPIC for role in LLM_ROLES},
    "research_m3": {**{role: _ANTHROPIC for role in LLM_ROLES}, "research": _M3},
    "all_m3": {**{role: _M3 for role in LLM_ROLES}, "instinct": _M3_INSTINCT},
}


def role_spec(profile: str, role: str) -> RoleSpec:
    """Return the :class:`RoleSpec` of ``role`` inside ``profile``.

    KeyError-free by design: an unknown profile/role raises ``ValueError`` and
    names the valid values (a typo in a config default must fail loudly at
    startup, not as a ``KeyError`` deep inside the wiring).

    Args:
        profile: key into :data:`LLM_PROFILES`.
        role: one of :data:`LLM_ROLES`.

    Raises:
        ValueError: unknown profile or unknown role.
    """
    if profile not in LLM_PROFILES:
        raise ValueError(
            f"unknown llm profile {profile!r} — known profiles: {sorted(LLM_PROFILES)}"
        )
    roles = LLM_PROFILES[profile]
    if role not in roles:
        raise ValueError(
            f"unknown llm role {role!r} in profile {profile!r} — known roles: {sorted(roles)}"
        )
    return roles[role]


def check_provider(name: str, spec: ProviderSpec) -> None:
    """Raise ``ValueError`` if ``spec`` cannot work. Pure; no network, no keyring.

    Called by :func:`check_llm_profile` for every provider of the active profile
    and directly by the shipped-provider test. The rules (T31 tightens the §14
    ``/coding/`` path rule to a host rule):

    * ``kind`` must be one of ``"anthropic"`` / ``"openai_compat"``;
    * for ``openai_compat``: ``base_url`` must start with ``https://`` and must
      **not** contain ``"coding"`` anywhere (case-insensitive) — the bot must
      never point at a coding-plan endpoint;
    * for ``openai_compat``: ``api_key_service`` and ``api_key_username`` must
      be set (the key lives in the OS keyring, never in a file);
    * ``max_tokens_field`` must be one of the two known names.

    Args:
        name: the provider key (used in the error messages).
        spec: the provider entry to validate.

    Raises:
        ValueError: with the provider name, the offending field and its value.
    """
    if spec.kind not in _PROVIDER_KINDS:
        raise ValueError(
            f"provider {name!r}: unknown kind {spec.kind!r} — expected one of {_PROVIDER_KINDS}"
        )
    if spec.kind == "anthropic":
        return
    if not spec.base_url or not spec.base_url.startswith("https://"):
        raise ValueError(
            f"provider {name!r}: base_url must start with 'https://', got {spec.base_url!r}"
        )
    if "coding" in spec.base_url.lower():
        raise ValueError(
            f"provider {name!r}: base_url must not point at a coding-plan endpoint, "
            f"got {spec.base_url!r} — the bot uses the general pay-per-use API"
        )
    if not spec.api_key_service:
        raise ValueError(f"provider {name!r}: api_key_service must not be empty")
    if not spec.api_key_username:
        raise ValueError(f"provider {name!r}: api_key_username must not be empty")
    if spec.max_tokens_field not in _MAX_TOKENS_FIELDS:
        raise ValueError(
            f"provider {name!r}: max_tokens_field must be one of {_MAX_TOKENS_FIELDS}, "
            f"got {spec.max_tokens_field!r}"
        )


def client_kwargs(spec: ProviderSpec) -> dict[str, Any]:
    """The ONE ``ProviderSpec`` → ``OpenAICompatLLMClient`` kwargs mapping (T29).

    ``_build_llm`` (the bot) and ``scripts/openrouter_smoke.py`` (``--provider``)
    both use this function — so the smoke tests exactly the construction the bot
    performs, and a new quirk field without a mapping makes the field-coverage
    test fail loudly.

    Args:
        spec: the provider entry to map.

    Returns:
        The keyword arguments for :class:`OpenAICompatLLMClient` (without
        ``model``/``max_tokens``/``temperature``/``timeout_s``, which come from
        the role/phase config).
    """
    return {
        "base_url": spec.base_url,
        "api_key_service": spec.api_key_service,
        "api_key_username": spec.api_key_username,
        "max_tokens_field": spec.max_tokens_field,
        "send_temperature": spec.send_temperature,
        "extra_body": dict(spec.extra_body),
    }


def check_llm_profile(
    profile: str,
    *,
    pricing: Mapping[str, tuple[float, float]],
    default_models: Mapping[str, str],
    exempt_models: tuple[str, ...],
) -> None:
    """Validate one LLM profile against the live configuration. Pure; never raises
    anything but ``ValueError``.

    Four failure classes (each names the profile, the role and the value):

    1. unknown profile / unknown provider / malformed provider entry
       (:func:`check_provider`),
    2. a ``claude-*`` model id bound to a provider whose kind is not
       ``"anthropic"`` — that model does not exist there,
    3. a resolved model (``spec.model`` or ``default_models[role]``) **without a
       price line** — the meter would silently price it at 0,
    4. a model of a non-Anthropic provider that is **not** in ``exempt_models``.

    Case 4 exists because the model id is a literal in three places (this file's
    ``_M3.model``, the price line in ``research/models.py`` and
    ``SchedulerConfig.budget_exempt_models``). A rename that forgets the exempt
    list would silently put the research calls back under the daily token cap —
    this check makes that fail loudly at startup instead.

    Args:
        profile: key into :data:`LLM_PROFILES`.
        pricing: model id → ``(input, output)`` USD per Mtok.
        default_models: role → the model id that phase config would use.
        exempt_models: model ids whose calls do not count against the budget.

    Raises:
        ValueError: on any of the four failure classes.
    """
    if profile not in LLM_PROFILES:
        raise ValueError(
            f"unknown llm profile {profile!r} — known profiles: {sorted(LLM_PROFILES)}"
        )
    roles = LLM_PROFILES[profile]
    for role in LLM_ROLES:
        spec = roles.get(role)
        if spec is None:
            raise ValueError(f"llm profile {profile!r} has no entry for role {role!r}")
        if spec.provider not in PROVIDERS:
            raise ValueError(
                f"llm profile {profile!r}, role {role!r}: unknown provider {spec.provider!r} — "
                f"known providers: {sorted(PROVIDERS)}"
            )
        provider = PROVIDERS[spec.provider]
        check_provider(spec.provider, provider)

        model = spec.model or default_models.get(role)
        if not model:
            raise ValueError(
                f"llm profile {profile!r}, role {role!r}: no model — neither the role spec "
                f"nor default_models carries one"
            )
        if provider.kind != "anthropic" and model.startswith("claude-"):
            raise ValueError(
                f"llm profile {profile!r}, role {role!r}: claude model {model!r} cannot run "
                f"on provider {spec.provider!r} (kind={provider.kind!r})"
            )
        if model not in pricing:
            raise ValueError(
                f"llm profile {profile!r}, role {role!r}: model {model!r} has no price line "
                f"in research.models._DEFAULT_PRICING_USD_PER_MTOK — add it before the flip"
            )
        if provider.kind != "anthropic" and model not in exempt_models:
            raise ValueError(
                f"llm profile {profile!r}, role {role!r}: model {model!r} (provider "
                f"{spec.provider!r}) is not in budget_exempt_models={list(exempt_models)} — "
                f"its calls would count against the daily token budget"
            )


__all__ = [
    "LLM_PROFILES",
    "LLM_ROLES",
    "PROVIDERS",
    "ProviderSpec",
    "RoleSpec",
    "check_llm_profile",
    "check_provider",
    "client_kwargs",
    "role_spec",
]
