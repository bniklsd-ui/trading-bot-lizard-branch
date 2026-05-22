"""Half-automated live / smoke tests for the Phase 2 persistence layer.

Unlike ``pytest tests/`` (mocked, temp dirs, single connection), these exercise
the things only a real run can prove:

  durability  — data written by one connection survives a *fresh* connection /
                process restart (real on-disk SQLite, not in-memory temp).
  ttl         — the candidates file self-clears on expiry.
  integration — real Phase-1 IG-demo ``Envelope.data`` dicts flow into Phase 2
                (the actual cross-phase contract). Hits the live demo API.

Usage:
    python scripts/live_test.py all                     # durability + ttl (no network)
    python scripts/live_test.py durability              # write + verify in one process
    python scripts/live_test.py durability --phase write    # true 2-process: step 1
    python scripts/live_test.py durability --phase verify   # true 2-process: step 2
    python scripts/live_test.py ttl
    python scripts/live_test.py integration             # needs IG-demo creds + phase1 venv

Exit code 0 = PASS, 1 = FAIL. Test data is written under <repo_root>/data/
(gitignored) using dedicated `livetest*` paths, so it never touches a real
trading_bot.sqlite. Reset anytime by deleting those files.

The integration test must run from the Phase-1 virtualenv (which has `keyring`):
    source phase1_broker_wrapper/.venv/bin/activate
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

# Make the Phase-2 `persistence` package importable when run as a script,
# and the Phase-1 `broker_wrapper` package importable for the integration test.
_PACKAGE_ROOT = Path(__file__).resolve().parent.parent          # phase2_persistence
_REPO_ROOT = _PACKAGE_ROOT.parent
sys.path.insert(0, str(_PACKAGE_ROOT))
sys.path.insert(0, str(_REPO_ROOT / "phase1_broker_wrapper"))

_DB = _REPO_ROOT / "data" / "livetest.sqlite"
_STATE = _REPO_ROOT / "data" / "livetest_state"
_INT_DB = _REPO_ROOT / "data" / "livetest_integration.sqlite"

# Expected values for the durability fixture (must match _durability_write).
_EXP_SCORE = 58.0
_EXP_PNL = 90.0
_EXP_HOLD_MIN = 45.0


class _Check:
    """Tiny PASS/FAIL recorder so the script reads like a checklist."""

    def __init__(self) -> None:
        self.failures = 0

    def __call__(self, label: str, condition: bool, detail: str = "") -> bool:
        mark = "PASS" if condition else "FAIL"
        if not condition:
            self.failures += 1
        suffix = f" — {detail}" if detail else ""
        print(f"  [{mark}] {label}{suffix}")
        return bool(condition)


# ---------------------------------------------------------------------------
# durability
# ---------------------------------------------------------------------------

def _durability_write(db_path: Path, state_dir: Path) -> None:
    from persistence import Database, StateManager

    db_path.parent.mkdir(parents=True, exist_ok=True)
    db_path.unlink(missing_ok=True)  # start fresh for deterministic assertions

    db = Database(str(db_path))
    db.run_migrations()
    trade_id = db.insert_trade({
        "deal_id": "LIVE-1",
        "epic": "IX.D.DAX.IFMM.IP",
        "direction": "BUY",
        "size": 1.0,
        "open_level": 18000.0,
        "currency": "EUR",
        "open_ts": "2026-05-22T09:00:00.000Z",
        "session_date": "2026-05-22",
    })
    db.update_trade_close("LIVE-1", {
        "close_level": 18090.0,
        "profit_loss": _EXP_PNL,
        "close_ts": "2026-05-22T09:45:00.000Z",
    })
    db.insert_reward(trade_id, {
        "score_after": _EXP_SCORE, "win_loss": "WIN", "outcome_score_delta": 8.0,
    })
    db.insert_lesson(trade_id, {"lesson_text": "Trend day; held to target."})
    db.close()

    StateManager(str(state_dir)).save_candidates(
        [{"epic": "IX.D.DAX.IFMM.IP", "direction": "CALL", "confidence": 72}]
    )
    print(f"  wrote LIVE-1 (+reward +lesson) and candidates to {db_path}")


def _durability_verify(db_path: Path, state_dir: Path, check: _Check) -> None:
    from persistence import Database, StateManager

    if not db_path.exists():
        check("db file exists", False, f"{db_path} missing — run --phase write first")
        return

    db = Database(str(db_path))  # fresh connection, intentionally no run_migrations
    check(f"score persisted == {_EXP_SCORE}",
          db.get_current_score() == _EXP_SCORE, f"got {db.get_current_score()}")
    check("risk_level == AGGRESSIV", db.get_risk_level() == "AGGRESSIV")

    trades = db.get_recent_trades(1)
    found = bool(trades) and trades[0]["deal_id"] == "LIVE-1"
    check("trade LIVE-1 persisted", found)
    if found:
        t = trades[0]
        check("status == CLOSED", t["status"] == "CLOSED", t["status"])
        check(f"profit_loss == {_EXP_PNL}", t["profit_loss"] == _EXP_PNL, f"got {t['profit_loss']}")
        check(f"hold_duration_min == {_EXP_HOLD_MIN}",
              t["hold_duration_min"] == _EXP_HOLD_MIN, f"got {t['hold_duration_min']}")
    check("lesson persisted", bool(db.get_recent_lessons(1)))
    db.close()

    cands = StateManager(str(state_dir)).load_candidates()
    check("candidates persisted (1)", len(cands) == 1, f"got {len(cands)}")


def _run_durability(args, check: _Check) -> None:
    db_path, state_dir = Path(args.db_path), Path(args.state_dir)
    if args.phase in ("write", "all"):
        print("durability — write phase:")
        _durability_write(db_path, state_dir)
    if args.phase in ("verify", "all"):
        print("durability — verify phase (fresh connection):")
        _durability_verify(db_path, state_dir, check)


# ---------------------------------------------------------------------------
# ttl
# ---------------------------------------------------------------------------

def _run_ttl(args, check: _Check) -> None:
    from persistence import StateManager

    print("ttl — candidates expiry self-clear:")
    sm = StateManager(str(args.state_dir))
    sm.save_candidates([{"epic": "X", "direction": "CALL", "confidence": 60}])
    check("file exists after save", sm._candidates_path.exists())
    check("candidates_are_fresh() after save", sm.candidates_are_fresh())

    payload = json.loads(sm._candidates_path.read_text())
    payload["expires_at"] = "2020-01-01T00:00:00.000Z"
    sm._atomic_write(sm._candidates_path, payload)

    check("expired load_candidates() returns []", sm.load_candidates() == [])
    check("expired file self-deleted", not sm._candidates_path.exists())


# ---------------------------------------------------------------------------
# integration (live IG demo)
# ---------------------------------------------------------------------------

def _run_integration(args, check: _Check) -> None:
    print("integration — live IG demo -> Phase 2:")
    try:
        from broker_wrapper import get_broker
    except Exception as exc:  # noqa: BLE001 - report any import failure clearly
        check("import broker_wrapper", False,
              f"{exc} — activate the phase1 venv first")
        return

    from persistence import Database, StateManager
    from persistence.timeutil import utc_iso_now

    try:
        broker = get_broker("ig_demo")
    except Exception as exc:  # noqa: BLE001 - missing keyring creds, etc.
        check("build ig_demo adapter (keyring creds)", False, str(exc))
        return

    conn_env = broker.connect()
    if not check("connect() ok", getattr(conn_env, "ok", False),
                 _err(conn_env)):
        return

    acct_env = broker.get_account()
    check("get_account() ok", acct_env.ok, _err(acct_env))
    pos_env = broker.get_open_positions()
    check("get_open_positions() ok", pos_env.ok, _err(pos_env))

    acct = acct_env.data or {}
    # get_open_positions().data is {"positions": [...]} (per ig_adapter), not a bare list.
    positions = (pos_env.data or {}).get("positions", [])
    print(f"  account={acct.get('account_id')} balance={acct.get('balance')} "
          f"{acct.get('currency')}; {len(positions)} open position(s)")

    # 1) account snapshot round-trip through StateManager
    sm = StateManager(str(args.state_dir))
    sm.save_account_state(acct, positions)
    check("account state fresh after save", sm.is_account_state_fresh())
    loaded = sm.load_account_state()
    check("account state round-trips",
          loaded is not None and loaded.get("account_id") == acct.get("account_id"))

    # 2) map live positions -> trade rows (the Phase-5 glue: created_at -> open_ts)
    db_path = Path(args.db_path)
    db_path.parent.mkdir(parents=True, exist_ok=True)
    db_path.unlink(missing_ok=True)
    db = Database(str(db_path))
    db.run_migrations()
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    inserted = 0
    for pos in positions:
        if not isinstance(pos, dict):
            check("position payload is a dict", False, f"got {type(pos).__name__}")
            continue
        db.insert_trade({
            **pos,
            "open_ts": pos.get("created_at") or utc_iso_now(),
            "session_date": today,
        })
        inserted += 1
    check("live positions inserted as trades",
          inserted == len(positions) and len(db.get_open_trades()) == inserted,
          f"{len(positions)} position(s)")
    db.close()

    try:
        broker.disconnect()
    except Exception:  # noqa: BLE001 - disconnect is best-effort
        pass

    if not positions:
        print("  note: no open demo positions — open one (market hours) to fully "
              "exercise insert_trade from live data")


def _err(env) -> str:
    e = getattr(env, "error", None)
    return json.dumps(e) if e else ""


# ---------------------------------------------------------------------------

def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("test", choices=["durability", "ttl", "integration", "all"],
                        help="which live test to run")
    parser.add_argument("--phase", choices=["write", "verify", "all"], default="all",
                        help="durability only: split into two processes")
    parser.add_argument("--db-path", default=None, help="override SQLite path")
    parser.add_argument("--state-dir", default=None, help="override JSON state dir")
    args = parser.parse_args(argv)

    # Per-test defaults (kept separate so tests don't clobber each other).
    args.state_dir = args.state_dir or str(_STATE)
    if args.test == "integration":
        args.db_path = args.db_path or str(_INT_DB)
    else:
        args.db_path = args.db_path or str(_DB)

    check = _Check()
    if args.test in ("durability", "all"):
        _run_durability(args, check)
    if args.test in ("ttl", "all"):
        _run_ttl(args, check)
    if args.test == "integration":
        _run_integration(args, check)

    if args.test == "durability" and args.phase == "write":
        print("\nWrite phase done. Now run: "
              "python scripts/live_test.py durability --phase verify")
        return 0

    print()
    if check.failures == 0:
        print("RESULT: PASS")
        return 0
    print(f"RESULT: FAIL ({check.failures} check(s) failed)")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
