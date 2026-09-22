"""Tests for the Phase 16 C1 Historien-Fenster post-filter (Plan §6 C1 + §7 AK7).

Four cases (Plan §6 C1):
1. ``_drop_older_than`` keeps recent trades and drops old ones (now-injectable).
2. ``_drop_older_than`` fails open on unparseable timestamps (LLM sees more,
   never less).
3. ``build_context`` with the **default** ``recent_trades_max_age_days=14``
   keeps recent trades and drops those older than 14 days.
4. ``build_context`` with ``recent_trades_max_age_days=None`` is bit-identical
   to pre-P16 — no post-filter is applied (the DB query result flows through
   unchanged).

Plus a fifth (Phase 16 AK7 hardening): the prompt header advertises the
configured window when ``max_age_days`` is set, and stays at the pre-P16 string
when ``None``.

No network, no LLM, no real DB — fixtures mirror the patterns in
``test_context_builder.py`` + ``test_prompt.py``.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest

from research.context_builder import _drop_older_than, build_context
from research.models import ResearchConfig
from tests.conftest import (
    DEFAULT_EPIC,
    FakeBroker,
    FakeDB,
    FakeFetcher,
    _make_prompt_dict,
)


# --- _drop_older_than: pure-function tests ---------------------------------- #


_FIXED_NOW = datetime(2026, 9, 5, 12, 0, 0, tzinfo=timezone.utc)


def _trade(close_ts: str | None, *, id_: int = 0) -> dict:
    return {
        "id": id_,
        "close_ts": close_ts,
        "open_ts": close_ts,
        "epic": DEFAULT_EPIC,
        "direction": "BUY",
        "profit_loss": 0.0,
        "status": "CLOSED",
    }


def test_drop_older_than_keeps_recent_drops_old() -> None:
    """Trades within the window survive; trades outside are dropped."""
    recent = _trade("2026-09-01T09:30:00.000Z", id_=1)   # 4 days old
    edge = _trade("2026-08-22T12:00:00.000Z", id_=2)     # exactly 14 days old (= cutoff, kept)
    too_old = _trade("2026-08-15T09:30:00.000Z", id_=3)  # 21 days old (dropped)
    in_trades = [recent, edge, too_old]

    def fixed_now() -> datetime:
        return _FIXED_NOW

    survivors = _drop_older_than(in_trades, 14, now_fn=fixed_now)

    assert [t["id"] for t in survivors] == [1, 2]


def test_drop_older_than_keeps_unparsable() -> None:
    """Trades with unparseable timestamps are KEPT (fail-open).

    Direction matters: dropping a malformed row would *narrow* the LLM's view
    silently, which is the opposite of what we want — better to show a row we
    can't date than to hide it.
    """
    unparsable = _trade("not-a-timestamp", id_=1)
    none_ts = _trade(None, id_=2)
    empty_ts = _trade("", id_=3)
    good_old = _trade("2026-01-01T09:30:00.000Z", id_=4)  # genuinely old

    def fixed_now() -> datetime:
        return _FIXED_NOW

    survivors = _drop_older_than(
        [unparsable, none_ts, empty_ts, good_old], 14, now_fn=fixed_now
    )

    # All three unparseable kept; the genuinely-old one dropped.
    assert [t["id"] for t in survivors] == [1, 2, 3]


# --- build_context integration: default 14-day window ------------------------ #


def _two_epic_config() -> ResearchConfig:
    """A minimal two-epic config (DAX + STXE) so ``build_context`` finds at
    least one tradeable epic and doesn't short-circuit on the universe probe.
    """
    return ResearchConfig(
        epic_allowlist=(DEFAULT_EPIC,),
    )


def test_build_context_window_default_14_days() -> None:
    """With the default ``recent_trades_max_age_days=14``, 6-of-8 trades older
    than 14 days get dropped; 2 within the window survive.

    Plus: the propagated context field carries the configured value so the
    prompt builder can render the matching header.
    """
    # Dated against the REAL clock, not ``_FIXED_NOW``: ``build_context`` has no
    # ``now_fn`` seam — it calls ``_drop_older_than`` with the default (wall-clock)
    # now, which is correct for production. Fixtures pinned to a fixed date
    # therefore age out: on 2026-09-22 the "3 days old" row built from
    # ``_FIXED_NOW`` (2026-09-05) was really 20 days old and got dropped, failing
    # this test 17 days after it was written (corrected 2026-09-22).
    now = datetime.now(timezone.utc)
    recent_iso = (now - timedelta(days=3)).isoformat()  # 3 days old
    recent_iso_2 = (now - timedelta(days=10)).isoformat()  # 10 days old
    old_iso = (now - timedelta(days=20)).isoformat()  # 20 days old (×6)
    trades = [
        _trade(recent_iso, id_=1),
        _trade(recent_iso_2, id_=2),
        *(_trade(old_iso, id_=i + 10) for i in range(6)),
    ]
    broker = FakeBroker()
    db = FakeDB(for_prompt_trades=list(trades))
    fetcher = FakeFetcher(prompt_dict=_make_prompt_dict())

    ctx = build_context(broker, db, fetcher, _two_epic_config())

    assert [t["id"] for t in ctx.recent_trades] == [1, 2]
    # The propagated field is the configured value (default 14).
    assert ctx.recent_trades_max_age_days == 14


def test_window_none_is_bit_identical() -> None:
    """``recent_trades_max_age_days=None`` keeps the DB query result untouched
    and the propagated context field carries ``None`` (so the prompt header
    stays at the pre-P16 string).
    """
    recent_iso = (_FIXED_NOW - timedelta(days=3)).isoformat()
    old_iso = (_FIXED_NOW - timedelta(days=20)).isoformat()
    trades = [
        _trade(recent_iso, id_=1),
        _trade(old_iso, id_=2),
    ]
    broker = FakeBroker()
    db = FakeDB(for_prompt_trades=list(trades))
    fetcher = FakeFetcher(prompt_dict=_make_prompt_dict())

    cfg = ResearchConfig(
        epic_allowlist=(DEFAULT_EPIC,),
        recent_trades_max_age_days=None,  # explicit off
    )
    ctx = build_context(broker, db, fetcher, cfg)

    # Both trades survive — no post-filter.
    assert [t["id"] for t in ctx.recent_trades] == [1, 2]
    assert ctx.recent_trades_max_age_days is None


# --- prompt header: render matches config ------------------------------------ #


def test_prompt_header_advertises_window_when_set() -> None:
    """When the context carries a positive window, the rendered user message
    header reads ``Recent trades (last 14 days, newest first):``.

    Mirrors the Phase-16-C1 UX intent: the LLM knows the recent-trades block is
    a *windowed* sample, not a complete tail.
    """
    from research.prompt import build_prompt

    ctx = _ctx_with_trades(
        max_age_days=14,
        trades=[_trade("2026-09-02T09:30:00.000Z", id_=1)],
    )
    _system, user, _schema = build_prompt(
        ctx, threshold=55.0, allowed_directions=("BUY", "SELL"),
    )
    assert "Recent trades (last 14 days, newest first):" in user


def test_prompt_header_pre_p16_string_when_none() -> None:
    """When the context field is ``None``, the rendered header stays at the
    pre-P16 string (no window advertised — the post-filter didn't run).
    """
    from research.prompt import build_prompt

    ctx = _ctx_with_trades(max_age_days=None, trades=[])
    _system, user, _schema = build_prompt(
        ctx, threshold=55.0, allowed_directions=("BUY", "SELL"),
    )
    assert "Recent trades: none on record." in user


# --- helpers ----------------------------------------------------------------- #


def _ctx_with_trades(
    *,
    max_age_days: int | None,
    trades: list[dict],
):
    """Build a ``ResearchContext`` directly with a populated recent-trades list
    + the configured ``recent_trades_max_age_days`` field, for the prompt tests.
    """
    from research.models import ResearchContext

    return ResearchContext(
        tradeable_epics=[{
            "epic": DEFAULT_EPIC,
            "name": "Germany 40 Cash (1 EUR)",
            "spread_pct": 0.03,
            "market_status": "TRADEABLE",
            "min_deal_size": 0.5,
        }],
        recent_trades=trades,
        recent_lessons=[],
        bot_score=55.0,
        risk_level="AGGRESSIV",
        brain_context=dict(_make_prompt_dict()),
        anchor_epic=DEFAULT_EPIC,
        recent_trades_max_age_days=max_age_days,
    )
