"""Statusmaschine + Safety — die "promote" Hälfte von discover->verify->promote.

``run_promotion_cycle`` prüft `discovered`/`quarantined`-Kandidaten (Verify + Pricing),
aktiviert verifizierte Kandidaten, und health-recheckt bereits aktive Instrumente
(IG-seitiger Fail demotiert, yFinance-seitiger Fail degradiert nur — Konzept C3).
**Demo-only, fail-closed, hart** (Decision D4): ein Aufruf mit ``is_demo=False`` wirft
sofort, kein Ausnahmepfad.

Verify-Wiederverwendung (Plan §7): ``check_ig_side``/``check_yf_side``/``verdict_for``
kommen aus dem repo-root ``scripts/verify_instrument.py`` (**nicht**
``phase8_scheduler/scripts/`` — das war der Pfad im ursprünglichen Plan-Dokument, aber
das Skript liegt tatsächlich phasenlos im Repo-Root; die im Plan zitierte Signatur
stimmt, nur der Ordner nicht — reconciled hier gegen den echten Baum) via
``importlib.util.spec_from_file_location``, exakt das Muster, das
``tests/test_resolve_epics.py`` bereits etabliert. **Kein Copy-Paste** — eine Wahrheit
für "ist dieses Instrument nutzbar".
"""

from __future__ import annotations

import importlib.util
import logging
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable

from universe.exceptions import UniverseSafetyError
from universe.models import (
    STATUS_ACTIVE,
    STATUS_DISCOVERED,
    STATUS_QUARANTINED,
    STATUS_VERIFIED,
)
from universe.pricing import confirm_curated, resolve_point_value
from universe.store import UniverseStore

logger = logging.getLogger(__name__)

# The reused verify-instrument seam (Plan §7) — repo-root, phaseless script.
_VERIFY_INSTRUMENT_PATH = (
    Path(__file__).resolve().parents[2] / "scripts" / "verify_instrument.py"
)

# IG-side check names in a verify_instrument verdict's ``checks`` dict — a False here
# counts toward demotion. Everything else in ``checks`` is yFinance-side (never demotes,
# only sets data_degraded — Konzept C3).
_IG_SIDE_CHECKS = frozenset({"currency_eur", "min_deal_size_ok", "ig_ohlcv_available"})


def _load_verify_instrument() -> Any:
    """Load the repo-root ``scripts/verify_instrument.py`` module by file path.

    Lazy (called from inside function bodies, never at module import time) so
    ``import universe.promotion`` itself pulls in no cross-phase module — the loaded
    script has no heavy top-level imports of its own either (stdlib + typing only).
    """
    spec = importlib.util.spec_from_file_location(
        "_universe_verify_instrument", _VERIFY_INSTRUMENT_PATH
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)  # type: ignore[union-attr]
    return module


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _parse_iso(ts: str) -> datetime:
    """Parse an ISO 8601 UTC string (optional ``Z`` suffix) to an aware datetime.

    Duplicated (not imported) from Phase 2's ``timeutil.py`` — phase isolation.
    """
    normalized = ts.replace("Z", "+00:00") if ts.endswith("Z") else ts
    dt = datetime.fromisoformat(normalized)
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt


def _backoff_eligible(
    last_verified_at: str | None, fail_count: int, now: datetime
) -> bool:
    """True if enough time has passed since ``last_verified_at`` to re-verify.

    Never-verified (``last_verified_at is None``) is always eligible. Otherwise the
    step is ``2**fail_count`` hours (Plan §7's "einfache Treppe").
    """
    if last_verified_at is None:
        return True
    elapsed_hours = (now - _parse_iso(last_verified_at)).total_seconds() / 3600.0
    return elapsed_hours >= float(2**fail_count)


def _ig_side_failed(verdict: dict[str, Any]) -> bool:
    checks = verdict.get("checks", {})
    return any(checks.get(name) is False for name in _IG_SIDE_CHECKS)


# Error codes that say "this account cannot ask right now", not "this instrument is
# unsuitable". A verdict carrying one of these is INDETERMINATE, not a failure.
_INDETERMINATE_IG_ERRORS = frozenset({"RATE_LIMIT"})


def _ig_side_indeterminate(verdict: dict[str, Any]) -> bool:
    """True when the IG probe failed for an account-wide reason, so the verdict says
    nothing about the instrument.

    **Live finding 2026-08-04/08:** the paper tracker exhausted the account's historical-
    data allowance. Every ``get_ohlcv`` then returned ``RATE_LIMIT``, so ``check_ig_side``
    reported ``ig_ohlcv_available: false`` for **every** epic in the same verify round —
    and the demotion path below read that as 22 simultaneously unsuitable instruments.
    18 of 22 were quarantined, including the DAX/CAC/IBEX/AEX/STXE core that Phase 9 had
    spent weeks verifying to ``point_value_source='ig_fields'``.

    The distinction that was missing: ``currency_eur``/``min_deal_size_ok`` come from
    ``get_market_info``, which stayed healthy the whole time. One endpoint being
    rate-limited is a fact about our API budget, not about the instrument — and the right
    response to "we learned nothing" is to change nothing, not to count a strike.

    **Accepted side effect:** writing nothing also means ``last_verified_at`` does not
    advance, so ``_backoff_eligible``'s ``2**fail_count`` staircase stops throttling
    re-probes of discovered/quarantined candidates while the condition lasts. At 3 data
    points per probe (``_OHLCV_COUNT``) that cost is negligible against the 300 the paper
    tracker spends per fetch, so it is accepted rather than fixed — but note the direction
    is opposite to the "a repeated failure must not raise call volume" property this
    session otherwise enforces. Revisit if a future indeterminate cause is expensive to
    probe.
    """
    return verdict.get("ig_ohlcv_error_code") in _INDETERMINATE_IG_ERRORS


def _yf_side_failed(verdict: dict[str, Any]) -> bool:
    checks = verdict.get("checks", {})
    return any(
        checks.get(name) is False for name in checks if name not in _IG_SIDE_CHECKS
    )


@dataclass
class PromotionReport:
    """Outcome of one :func:`run_promotion_cycle`."""

    verified: list[str] = field(default_factory=list)
    activated: list[str] = field(default_factory=list)
    demoted: list[str] = field(default_factory=list)
    quarantined: list[str] = field(default_factory=list)
    confirmed_pricing: list[str] = field(default_factory=list)
    unchanged: int = 0


def _emit(health_sink: Callable[[dict], None] | None, event: dict[str, Any]) -> None:
    if health_sink is not None:
        health_sink(event)


def run_promotion_cycle(
    broker: Any,
    fetcher: Any,
    store: UniverseStore,
    *,
    is_demo: bool,
    max_active: int = 8,
    demote_after_fails: int = 3,
    pace_s: float = 2.5,
    sleep_fn: Callable[[float], None] = time.sleep,
    health_sink: Callable[[dict], None] | None = None,
    now_fn: Callable[[], datetime] = _utc_now,
) -> PromotionReport:
    """Run one discover->verify->promote cycle's verify/activate/health-recheck steps.

    Fail-closed, demo-only, hart (Decision D4): raises :class:`UniverseSafetyError`
    immediately if ``is_demo`` is not ``True`` — no exception path, no "for now" bypass.

    2026-07-04: IGAdapter._request now also retries 429s itself (Phase 1 hardening
    Step 1) — the pace_s/sleep_fn pacing here stays belt-and-braces, not duplication.
    """
    if not is_demo:
        raise UniverseSafetyError("promotion is demo-only")

    verify_instrument = _load_verify_instrument()
    now = now_fn()
    report = PromotionReport()

    # -- Step 1: verify discovered/quarantined candidates (with backoff) --------
    candidates = store.list_by_status(STATUS_DISCOVERED, STATUS_QUARANTINED)
    for rec in candidates:
        if not _backoff_eligible(rec.last_verified_at, rec.fail_count, now):
            report.unchanged += 1
            continue

        verdict = verify_instrument.verify_instrument(
            broker, fetcher, rec.epic, volume_proxy=rec.volume_proxy,
            sleep_fn=sleep_fn, pace_s=pace_s,
        )
        # Konzept C3: only an IG-side failure quarantines — a yFinance-side
        # failure is tolerated as reduced-signal (data_degraded), exactly like
        # Step 3 already does for active instruments. The raw ``verdict_for``
        # FAIL covers both sides, so it must NOT gate here (2026-07-06 live
        # finding: one flaky-yf afternoon quarantined 7 IG-green instruments
        # at discovery, and the 2**fail_count backoff then froze the whole
        # universe for hours — an activation obstacle C3 explicitly forbids).
        if _ig_side_indeterminate(verdict):
            # No DB write at all — not the status, not the fail_count, not checks_json.
            # The round told us nothing about this instrument (see _ig_side_indeterminate).
            report.unchanged += 1
            _emit(health_sink, {
                "event": "universe_verify_indeterminate", "epic": rec.epic,
                "reason": verdict.get("ig_ohlcv_error_code"), "verdict": verdict,
            })
            continue
        if _ig_side_failed(verdict):
            store.set_status(
                rec.epic, STATUS_QUARANTINED, checks=verdict, fail_increment=True
            )
            report.quarantined.append(rec.epic)
            _emit(health_sink, {"event": "universe_quarantined", "epic": rec.epic, "verdict": verdict})
            continue
        yf_degraded = _yf_side_failed(verdict)

        market_info_env = broker.get_market_info(rec.epic)
        market_info = getattr(market_info_env, "data", None) or {}
        resolved = resolve_point_value(market_info)
        if resolved is None:
            # IG-side PASS but no point_value proof yet — stays discovered,
            # checks_json documents why (Decision D6: no proof, no activation).
            store.set_status(
                rec.epic, STATUS_DISCOVERED, checks=verdict,
                data_degraded=yf_degraded, reset_fail_count=True,
            )
            report.unchanged += 1
            continue

        point_value, source = resolved
        store.set_pricing(rec.epic, point_value, source)
        # reset_fail_count: an IG-green verify PASS clears the counter — without
        # this, a fail_count inherited from the quarantine era survives the
        # promotion and one later IG wobble demotes an otherwise healthy
        # instrument straight from the threshold (2026-07-07 live finding:
        # DAX active at fail_count=3 == demote_after_fails).
        store.set_status(
            rec.epic, STATUS_VERIFIED, checks=verdict,
            data_degraded=yf_degraded, reset_fail_count=True,
        )
        report.verified.append(rec.epic)
        _emit(health_sink, {"event": "universe_verified", "epic": rec.epic, "point_value": point_value})

    # -- Step 2: auto-activate verified candidates up to the cap ------------------
    active_count = len(store.active_universe())
    for rec in store.list_by_status(STATUS_VERIFIED):
        if active_count >= max_active:
            report.unchanged += 1
            continue
        store.set_status(rec.epic, STATUS_ACTIVE)
        report.activated.append(rec.epic)
        active_count += 1
        _emit(health_sink, {"event": "universe_activated", "epic": rec.epic})

    # -- Step 3: health-recheck actives (+ curated-pricing confirmation) ---------
    for rec in store.active_universe():
        # Skip instruments activated in Step 2 of THIS cycle (2026-07-04 review
        # polish): they carry a full verify PASS from Step 1 moments ago — a second
        # verify_instrument here is pure duplicate paced IG/yF traffic with no new
        # information. They rejoin the normal health-recheck from the next cycle on.
        # (Their pricing was just set in Step 1, so the curated-confirmation branch
        # below — which only fires on point_value_source IS NULL — never applied.)
        if rec.epic in report.activated:
            report.unchanged += 1
            continue
        verdict = verify_instrument.verify_instrument(
            broker, fetcher, rec.epic, volume_proxy=rec.volume_proxy,
            sleep_fn=sleep_fn, pace_s=pace_s,
        )
        if _ig_side_indeterminate(verdict):
            # Neither a strike nor a reset: the round is discarded. This is the path that
            # would have saved the DAX/CAC/IBEX/AEX/STXE core on 2026-08-04.
            report.unchanged += 1
            _emit(health_sink, {
                "event": "universe_verify_indeterminate", "epic": rec.epic,
                "reason": verdict.get("ig_ohlcv_error_code"), "verdict": verdict,
            })
            continue
        ig_failed = _ig_side_failed(verdict)
        yf_failed = _yf_side_failed(verdict)

        if ig_failed:
            new_fail_count = rec.fail_count + 1
            if new_fail_count >= demote_after_fails:
                store.set_status(rec.epic, STATUS_QUARANTINED, checks=verdict, fail_increment=True)
                report.demoted.append(rec.epic)
                _emit(health_sink, {"event": "universe_demoted", "epic": rec.epic, "verdict": verdict})
            else:
                store.set_status(rec.epic, STATUS_ACTIVE, checks=verdict, fail_increment=True)
                report.unchanged += 1
        else:
            # IG side is healthy: fail_count resets to 0 regardless of yF health
            # (the counter is IG-specific — Konzept C3). data_degraded tracks the
            # yFinance-side signal independently and never demotes on its own.
            store.set_status(
                rec.epic, STATUS_ACTIVE, checks=verdict,
                reset_fail_count=True, data_degraded=yf_failed,
            )
            report.unchanged += 1

        # Curated confirmation — only for actives still lacking a confirmed source.
        if rec.point_value_source is None and not ig_failed:
            market_info_env = broker.get_market_info(rec.epic)
            market_info = getattr(market_info_env, "data", None) or {}
            confirmation = confirm_curated(rec, market_info)
            if confirmation is True:
                resolved = resolve_point_value(market_info)
                if resolved is not None:
                    _, resolved_source = resolved
                    store.set_pricing(rec.epic, rec.point_value, resolved_source)
                    report.confirmed_pricing.append(rec.epic)
                    _emit(health_sink, {"event": "universe_pricing_confirmed", "epic": rec.epic})
            elif confirmation is False:
                logger.warning(
                    "universe: curated point_value for %s contradicted by verify data — quarantining",
                    rec.epic,
                )
                store.set_status(rec.epic, STATUS_QUARANTINED, checks=verdict, fail_increment=True)
                if rec.epic not in report.demoted:
                    report.demoted.append(rec.epic)
                _emit(health_sink, {"event": "universe_pricing_contradicted", "epic": rec.epic})
            # confirmation is None -> no evidence either way, no change.

    return report
