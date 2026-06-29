"""Module 12 (concept §12) — the read-mostly FastAPI dashboard backend.

A thin, **read-mostly** JSON API over the autonomous trader's durable state, plus a tiny control
surface that writes only files the trade core already polls. It deliberately holds **no** handle on
the executor / broker / runner — every observation is a read of the gitignored ``data/`` tree
(``trading_bot.sqlite`` opened **read-only**, ``scheduler_state.json``, the KILL / command files),
and every control action is a file write (``scheduler.killswitch`` / ``scheduler.command``). A UI
crash therefore cannot reach trading (Decision 14: the trader never hangs on the UI).

Hard isolation (concept §12):

- **DB is opened read-only**, per request, via the ``file:...?mode=ro`` URI — a write attempt
  raises ``sqlite3.OperationalError`` (proven by ``test_webui``). The API never opens it RW.
- **Control is files only.** ``POST /api/kill`` / ``clear_kill`` toggle the KILL file (the runner's
  *hard* stop); ``POST /api/command`` writes the start/stop command file (the runner's *soft*
  pause/resume — concept §12 "Daemon pollt", wired in ``scheduler.runner``). The P10 hook
  (``deep_research`` etc.) is intentionally not built; the command path stays generic.

Cross-phase reads (the confidence summary reuses the Phase-7 math) are **lazy inside the
endpoint**, so ``import webui.api`` pulls only ``fastapi`` + ``scheduler.*`` + stdlib. Repo
conventions apply (``from __future__ import annotations``, type hints + docstrings, logging to a
module logger on stderr).
"""

from __future__ import annotations

import dataclasses
import json
import logging
import sqlite3
from pathlib import Path
from typing import Any
from zoneinfo import ZoneInfo

from fastapi import Body, FastAPI, HTTPException
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles

from scheduler import command, killswitch
from scheduler.budget import _load_log, _record_local_date, _record_tokens
from scheduler.clock import Clock
from scheduler.config import SchedulerConfig
from scheduler.state import StateStore

logger = logging.getLogger("webui.api")

# webui/api.py -> webui/ -> phase8_scheduler/ -> repo root (mirrors scripts/wiring.py)
_REPO_ROOT = Path(__file__).resolve().parents[2]
_DATA_DIR = _REPO_ROOT / "data"
_STATIC_DIR = Path(__file__).resolve().parent / "static"

# How many rows the history-style endpoints return (newest first).
_DEFAULT_LIMIT = 200


def default_config() -> SchedulerConfig:
    """A demo-locked config with the canonical absolute ``data/`` paths (mirrors the wiring).

    Used for the module-level ``app`` so ``uvicorn webui.api:app`` reads the same files the daemon
    writes, regardless of the process's working directory.
    """
    return dataclasses.replace(
        SchedulerConfig(),
        live_db_path=str(_DATA_DIR / "trading_bot.sqlite"),
        state_path=str(_DATA_DIR / "state" / "scheduler_state.json"),
        kill_path=str(_DATA_DIR / "state" / "KILL"),
        command_path=str(_DATA_DIR / "state" / "scheduler_command.json"),
    )


def ro_connect(db_path: str) -> sqlite3.Connection:
    """Open the DB **read-only** (``mode=ro``) — any write raises ``OperationalError``.

    The single DB seam of the UI's isolation: every read goes through here, and a write attempt
    is refused by SQLite itself (not by convention). Rows come back as ``sqlite3.Row`` (dict-like).
    Raises ``OperationalError`` if the file does not exist (callers tolerate that as "no data yet").
    """
    conn = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True)
    conn.row_factory = sqlite3.Row
    return conn


def _query(db_path: str, sql: str, params: tuple[Any, ...] = ()) -> list[dict[str, Any]]:
    """Run a read-only query, returning a list of plain dicts; ``[]`` if the DB/table is absent.

    Fail-soft: a missing DB file or a not-yet-created table (the daemon may not have run
    ``init_db.py`` yet) yields ``[]`` rather than a 500 — the dashboard renders empty cards.
    """
    try:
        conn = ro_connect(db_path)
    except sqlite3.OperationalError:
        return []  # DB file not created yet
    try:
        rows = conn.execute(sql, params).fetchall()
        return [dict(r) for r in rows]
    except sqlite3.OperationalError as exc:
        logger.warning("read query failed (%s): %s", db_path, exc)
        return []
    finally:
        conn.close()


def _load_json_array(path: str) -> list[dict[str, Any]]:
    """Load a gitignored ``data/state`` JSON array (candidates / debate log), fail-soft.

    Missing file → ``[]``; corrupt JSON or a non-array payload → one WARNING + ``[]``. Mirrors
    the ``_query`` discipline (the dashboard renders an empty card rather than 500ing) and the
    ``scheduler.budget._load_log`` pattern these files share.
    """
    p = Path(path)
    if not p.exists():
        return []
    try:
        data = json.loads(p.read_text(encoding="utf-8"))
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        logger.warning("state file at %s unreadable (%s) — treating as empty.", p, exc)
        return []
    return data if isinstance(data, list) else []


def create_app(config: SchedulerConfig | None = None) -> FastAPI:
    """Build the FastAPI app bound to ``config`` (defaults to :func:`default_config`).

    Registers the read endpoints + the file-only control endpoints, then mounts the static
    dashboard at ``/`` (if the ``static/`` dir exists). No background work, no broker, no executor.
    """
    cfg = config or default_config()
    app = FastAPI(title="Trading Bot — Scheduler Dashboard", docs_url="/api/docs")

    # --- read endpoints ----------------------------------------------------

    @app.get("/api/status")
    def status() -> dict[str, Any]:
        """Phase + running-state + the day's counters (the at-a-glance card)."""
        state = StateStore(cfg.state_path).load()
        clock = Clock(cfg)
        halted = killswitch.is_set(cfg.kill_path)
        paused = command.read_command(cfg.command_path) == "stop"
        running_state = "HALTED" if halted else ("PAUSED" if paused else "RUNNING")
        return {
            "phase": clock.classify(clock.now()).value,
            "running_state": running_state,
            "kill_reason": killswitch.read_reason(cfg.kill_path) if halted else None,
            "session_date": state.date,
            "trades_today": state.trades_today,
            "max_trades_per_day": cfg.max_trades_per_day,
            "realized_pnl_today": state.realized_pnl_today,
            "daily_loss_cap": cfg.daily_loss_cap,
            "consecutive_failures": state.consecutive_failures,
            "max_consecutive_failures": cfg.max_consecutive_failures,
            "last_no_trade_reason": state.last_no_trade_reason,
            "last_research_ts": state.last_research_ts,
            "last_reconcile_ts": state.last_reconcile_ts,
        }

    @app.get("/api/score")
    def score() -> list[dict[str, Any]]:
        """The reward-score history (``reward_pts``), oldest→newest for a sparkline."""
        rows = _query(
            cfg.live_db_path,
            "SELECT id, trade_id, outcome_score_delta, process_score_delta, score_after, "
            "win_loss, pnl_raw, r_multiple, debate_confidence, calculated_at "
            "FROM reward_pts ORDER BY id ASC LIMIT ?",
            (_DEFAULT_LIMIT,),
        )
        return rows

    @app.get("/api/confidence")
    def confidence() -> dict[str, Any]:
        """Observe-only outcome-anchored confidence summary (reuses the Phase-7 math).

        Joins closed trades with their reward row to get the edge-set inputs, then runs the
        Phase-7 ``select_edge_set`` + ``compute_confidence``. Lazy-imports ``reward`` so the
        module import stays light. ``INSUFFICIENT`` (N < n_min) gates nothing — display only.
        """
        rows = _query(
            cfg.live_db_path,
            "SELECT r.r_multiple AS r_multiple, t.account AS account "
            "FROM reward_pts r JOIN trade_outcomes t ON t.id = r.trade_id "
            "WHERE r.r_multiple IS NOT NULL",
        )
        try:
            from reward import RewardConfig, compute_confidence  # lazy, cross-phase
            from reward.synthetic import select_edge_set

            rcfg = RewardConfig()
            r_multiples, wins, n = select_edge_set(rows, rcfg)
            report = compute_confidence(r_multiples, wins, n, rcfg)
            return {
                "state": report.state,
                "n": report.n,
                "confidence_value": report.confidence_value,
                "win_rate_raw": report.win_rate_raw,
                "win_rate_wilson_lb": report.win_rate_wilson_lb,
                "expectancy_r": report.expectancy_r,
                "sqn": report.sqn,
                "n_min": rcfg.n_min,
            }
        except Exception as exc:  # noqa: BLE001 — confidence is display-only; never 500 the dashboard
            logger.warning("confidence summary unavailable: %s", exc)
            return {"state": "UNAVAILABLE", "n": len(rows), "detail": str(exc)}

    @app.get("/api/lessons")
    def lessons() -> list[dict[str, Any]]:
        """The most recent free-text lessons (``trade_lessons``), newest first."""
        return _query(
            cfg.live_db_path,
            "SELECT id, trade_id, lesson_text, used_in_research, extracted_at "
            "FROM trade_lessons ORDER BY id DESC LIMIT ?",
            (_DEFAULT_LIMIT,),
        )

    @app.get("/api/trades")
    def trades() -> list[dict[str, Any]]:
        """Open + closed trades (``trade_outcomes``), newest first."""
        return _query(
            cfg.live_db_path,
            "SELECT id, deal_id, epic, direction, size, open_level, close_level, profit_loss, "
            "status, account, open_ts, close_ts, session_date, research_confidence "
            "FROM trade_outcomes ORDER BY id DESC LIMIT ?",
            (_DEFAULT_LIMIT,),
        )

    @app.get("/api/token_usage")
    def token_usage() -> dict[str, Any]:
        """Today's LLM token + cost spend vs the daemon's daily budget (the cost card).

        Reads the shared 8-field ``llm_usage.json`` (the same meter the daemon's ``TokenBudget``
        gates on) and reuses ``scheduler.budget`` helpers so the day boundary is the identical
        Europe/Berlin one. Fail-soft: a missing / corrupt log → zeros (never 500). ``budget`` is
        ``cfg.daily_token_budget`` (``None`` ⇒ disabled; ``percent`` then ``None``).
        """
        usage_path = str(Path(cfg.state_path).parent / "llm_usage.json")
        tz = ZoneInfo(cfg.tz)
        today = Clock(cfg).now().astimezone(tz).date()
        tokens = calls = 0
        cost_eur = cost_usd = 0.0
        for rec in _load_log(usage_path):
            if not isinstance(rec, dict):
                continue
            if _record_local_date(rec.get("ts"), tz) == today:
                tokens += _record_tokens(rec)
                cost_eur += float(rec.get("est_cost_eur") or 0.0)
                cost_usd += float(rec.get("est_cost_usd") or 0.0)
                calls += 1
        budget = cfg.daily_token_budget
        percent = round(100.0 * tokens / budget, 1) if budget else None
        return {
            "consumed_tokens": tokens,
            "budget": budget,
            "percent": percent,
            "cost_eur_today": round(cost_eur, 4),
            "cost_usd_today": round(cost_usd, 4),
            "calls_today": calls,
        }

    @app.get("/api/last_cycle")
    def last_cycle() -> dict[str, Any]:
        """The last cycle's outcome + the most-recent research pick and Bull/Bear/Judge debate.

        The cycle counters come from ``scheduler_state.json``; the reasoning artifacts come from
        the gitignored ``turbo_candidates.json`` (the research pick) and ``debate_log.json`` (the
        debate). Both are the **most recent on disk** — they only exist when the bot actually
        picked / debated, so on an abstain cycle they may pre-date the latest cycle; the UI labels
        them with their own timestamp + a stale marker. Either is ``None`` when absent.
        """
        state = StateStore(cfg.state_path).load()
        state_dir = Path(cfg.state_path).parent

        candidates = _load_json_array(str(state_dir / "turbo_candidates.json"))
        pick = candidates[-1] if candidates else None
        research_pick = None
        if isinstance(pick, dict):
            research_pick = {
                "epic": pick.get("epic"),
                "direction": pick.get("direction"),
                "llm_confidence": pick.get("llm_confidence"),
                "reasoning": pick.get("reasoning"),
                "score_at_pick": pick.get("score_at_pick"),
                "threshold_applied": pick.get("threshold_applied"),
                "generated_at": pick.get("generated_at"),
            }

        debates = _load_json_array(str(state_dir / "debate_log.json"))
        last = debates[-1] if debates else None
        debate = None
        if isinstance(last, dict):
            transcript = [
                {
                    "round": t.get("round"),
                    "agent": t.get("agent"),
                    "model": t.get("model"),
                    "text": t.get("text"),
                }
                for t in (last.get("transcript") or [])
                if isinstance(t, dict)
            ]
            debate = {
                "ts": last.get("ts"),
                "epic": last.get("epic"),
                "seed_direction": last.get("seed_direction"),
                "final_decision": last.get("final_decision"),
                "final_direction": last.get("final_direction"),
                "confidence": last.get("confidence"),
                "rounds_used": last.get("rounds_used"),
                "rationale": last.get("rationale"),
                "regime_snapshot": last.get("regime_snapshot"),
                "transcript": transcript,
            }

        return {
            "last_no_trade_reason": state.last_no_trade_reason,
            "last_no_trade_detail": state.last_no_trade_detail,
            "last_research_ts": state.last_research_ts,
            "last_reconcile_ts": state.last_reconcile_ts,
            "trades_today": state.trades_today,
            "consecutive_failures": state.consecutive_failures,
            "session_date": state.date,
            "research_pick": research_pick,
            "debate": debate,
        }

    # --- control endpoints (file writes ONLY) ------------------------------

    @app.post("/api/kill")
    def kill(payload: dict[str, Any] = Body(default={})) -> dict[str, Any]:
        """Engage the kill-switch (the *hard* stop) with a ``manual:<reason>`` tag."""
        reason = str(payload.get("reason") or "ui").strip() or "ui"
        killswitch.set_kill(cfg.kill_path, f"manual:{reason}")
        return {"ok": True, "kill_reason": killswitch.read_reason(cfg.kill_path)}

    @app.post("/api/clear_kill")
    def clear_kill() -> dict[str, Any]:
        """Disengage the kill-switch (delete the KILL file)."""
        killswitch.clear_kill(cfg.kill_path)
        return {"ok": True}

    @app.post("/api/command")
    def post_command(payload: dict[str, Any] = Body(default={})) -> dict[str, Any]:
        """Write the start/stop command (the *soft* pause/resume the daemon polls).

        ``{"cmd": "start"|"stop"}``. ``stop`` pauses the live daemon; ``start`` resumes it. Any
        other value is rejected with 400 (the daemon would ignore it anyway, but the UI is the
        in-process writer, so it validates).
        """
        cmd = str(payload.get("cmd", "")).strip().lower()
        if cmd not in ("start", "stop"):
            raise HTTPException(status_code=400, detail="cmd must be 'start' or 'stop'")
        command.write_command(cfg.command_path, cmd)
        return {"ok": True, "cmd": cmd}

    # --- static dashboard --------------------------------------------------

    if _STATIC_DIR.is_dir():
        app.mount("/", StaticFiles(directory=str(_STATIC_DIR), html=True), name="static")
    else:  # pragma: no cover — only when the static bundle is absent
        @app.get("/")
        def _no_static() -> JSONResponse:
            return JSONResponse({"detail": "static dashboard not found", "api": "/api/status"})

    return app


# Module-level app for ``uvicorn webui.api:app`` (binds the canonical data/ paths).
app = create_app()
