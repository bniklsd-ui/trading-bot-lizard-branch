"""Tests for ``reward.brain`` (concept §6 Step 7, ≥8) — the only AI in Phase 7.

Mocked, no network, no real LLM (project rule). The brain's single collaborator is
the duck-typed shared client (``FakeLLM`` from conftest). The load-bearing properties
pinned here are: (1) a valid answer becomes an ``ok=True`` lesson with the model's
text **verbatim**; (2) the prompt carries the R-multiple + exit status + market
context; (3) **every** failure mode (empty/malformed answer, exhausted retry,
arbitrary exception, timeout) becomes ``ok=False`` and **never raises** (best-effort,
Decision E/J); (4) the AI boundary — the brain transforms no numbers, it only relays
language → insight.
"""

from __future__ import annotations

from typing import Any

from reward import Brain, LessonExtractor
from reward.models import LessonResult, RewardConfig

from tests.conftest import FakeLLM, LLMResponseError


def _brain(answers: list[Any], **llm_kwargs: Any) -> tuple[Brain, FakeLLM]:
    """Build a Brain over a scripted FakeLLM; return both for assertions."""
    llm = FakeLLM(answers, **llm_kwargs)
    return Brain(llm, RewardConfig()), llm


# --------------------------------------------------------------------------- #
# Success path                                                                #
# --------------------------------------------------------------------------- #


def test_valid_lesson_returns_ok_result(make_closed, make_reward, market_context):
    brain, llm = _brain([{"lesson": "Enge Spreads vor dem Entry zahlen sich aus."}])
    result = brain.reflect(make_closed(), make_reward(), market_context)

    assert isinstance(result, LessonResult)
    assert result.ok is True
    assert result.error is None
    assert result.lesson_text == "Enge Spreads vor dem Entry zahlen sich aus."
    # market_context echoed back unchanged (the recorder persists it as JSON).
    assert result.market_context is market_context
    assert llm.calls == 1


def test_lesson_text_returned_verbatim_ai_boundary(make_closed, make_reward, market_context):
    """AI boundary: the brain relays the model's text, it does not transform numbers."""
    text = "  TIME_STOP-Exits ohne Edge vermeiden — auf geplante Stops warten.  "
    brain, _ = _brain([{"lesson": text}])
    result = brain.reflect(make_closed(status="TIME_STOP"), make_reward(), market_context)
    # only stripped, never rewritten / no score injected.
    assert result.lesson_text == text.strip()


def test_prompt_contains_r_multiple_status_and_market_context(
    make_closed, make_reward, market_context
):
    brain, llm = _brain([{"lesson": "ok"}])
    brain.reflect(
        make_closed(status="TIME_STOP"),
        make_reward(r_multiple=-1.25, win_loss="LOSS"),
        market_context,
    )
    user = llm.seen_users[0]
    system = llm.seen_systems[0]
    # R-multiple present, exit status present, a market-context key present.
    assert "-1.25" in user
    assert "TIME_STOP" in user
    assert "regime" in user and "trending_up" in user
    # honest None render: volume_z_score is None -> "n/a", never "0".
    assert "volume_z_score: n/a" in user
    # the system prompt states the AI boundary (no number/score/risk decision).
    assert "KEINE" in system
    # schema asks for the single required string field.
    assert llm.seen_schemas[0]["required"] == ["lesson"]


# --------------------------------------------------------------------------- #
# Fail-closed paths (best-effort, never raises — Decision E/J)                 #
# --------------------------------------------------------------------------- #


def test_missing_lesson_key_is_failure_no_raise(make_closed, make_reward, market_context):
    brain, _ = _brain([{"not_lesson": "oops"}])
    result = brain.reflect(make_closed(), make_reward(), market_context)
    assert result.ok is False
    assert result.lesson_text is None
    assert result.error  # carries a reason
    assert result.market_context is market_context


def test_empty_lesson_string_is_failure(make_closed, make_reward, market_context):
    brain, _ = _brain([{"lesson": "   "}])
    result = brain.reflect(make_closed(), make_reward(), market_context)
    assert result.ok is False
    assert result.lesson_text is None


def test_non_dict_answer_is_failure(make_closed, make_reward, market_context):
    brain, _ = _brain(["just a string, not a dict"])
    result = brain.reflect(make_closed(), make_reward(), market_context)
    assert result.ok is False
    assert result.lesson_text is None


def test_llm_response_error_becomes_ok_false(make_closed, make_reward, market_context):
    brain, _ = _brain([{"lesson": "unused"}], raises_exc=LLMResponseError("retry exhausted"))
    result = brain.reflect(make_closed(), make_reward(), market_context)
    assert result.ok is False
    assert result.lesson_text is None
    assert "retry exhausted" in result.error


def test_arbitrary_exception_becomes_ok_false(make_closed, make_reward, market_context):
    brain, _ = _brain([{"lesson": "unused"}], raises_exc=RuntimeError("boom"))
    result = brain.reflect(make_closed(), make_reward(), market_context)
    assert result.ok is False
    assert "boom" in result.error


def test_timeout_becomes_ok_false(make_closed, make_reward, market_context):
    brain, _ = _brain([{"lesson": "unused"}], raises_exc=TimeoutError("slow"))
    result = brain.reflect(make_closed(), make_reward(), market_context)
    assert result.ok is False
    assert result.lesson_text is None


# --------------------------------------------------------------------------- #
# Metering (transitive), market-context passthrough, protocol                 #
# --------------------------------------------------------------------------- #


def test_metering_path_runs_and_sets_last_usage(make_closed, make_reward, market_context):
    """The metered call ran exactly once and the client captured last_usage.

    Real ``token_meter.record`` correctness is covered by Phase-4 ``test_token_meter``;
    here we only prove the brain drives the metered path (Decision F, transitive).
    """
    brain, llm = _brain([{"lesson": "ok"}])
    assert llm.last_usage is None
    brain.reflect(make_closed(), make_reward(), market_context)
    assert llm.calls == 1
    assert llm.last_usage is not None
    assert llm.last_usage["input_tokens"] > 0


def test_empty_market_context_does_not_crash(make_closed, make_reward):
    brain, llm = _brain([{"lesson": "ok"}])
    result = brain.reflect(make_closed(), make_reward(), {})
    assert result.ok is True
    assert "kein Marktkontext" in llm.seen_users[0]


def test_brain_satisfies_lesson_extractor_protocol():
    brain, _ = _brain([{"lesson": "ok"}])
    assert isinstance(brain, LessonExtractor)
