"""Command-line interface — runs the wrapper standalone, emits JSON.

The CLI is the canonical way to (a) smoke-test the wrapper without the
rest of the bot, (b) pipe broker data into shell scripts, and (c) act
as a contract reference for the future FastAPI layer.

Every command prints exactly one Envelope JSON object to stdout and
exits 0 if ok=True, 1 if ok=False. Logs go to stderr.

Examples:
    python -m broker_wrapper.cli --broker ig_demo connect
    python -m broker_wrapper.cli --broker ig_demo get-account
    python -m broker_wrapper.cli --broker ig_demo get-price --epic IX.D.DAX.IFM.IP
    python -m broker_wrapper.cli --broker ig_demo search --query DAX
    python -m broker_wrapper.cli --broker ig_demo ohlcv --epic IX.D.DAX.IFM.IP --resolution MINUTE_5 --count 20
"""

from __future__ import annotations

import argparse
import logging
import sys

from broker_wrapper import get_broker
from broker_wrapper.envelope import Envelope, error_envelope
from broker_wrapper.exceptions import BrokerError, CredentialNotFoundError


def _setup_logging(verbose: bool) -> None:
    level = logging.DEBUG if verbose else logging.WARNING
    logging.basicConfig(
        stream=sys.stderr,
        level=level,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )


def _emit(env: Envelope) -> int:
    print(env.to_json(pretty=True))
    return 0 if env.ok else 1


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="broker_wrapper")
    parser.add_argument("--broker", default="ig_demo",
                        help="broker name (ig, ig_demo)")
    parser.add_argument("-v", "--verbose", action="store_true")
    sub = parser.add_subparsers(dest="cmd", required=True)

    sub.add_parser("connect", help="open a session")
    sub.add_parser("disconnect", help="close the session")
    sub.add_parser("get-account", help="account balance + currency")
    sub.add_parser("get-positions", help="all open positions")

    p_price = sub.add_parser("get-price", help="latest bid/ask for an epic")
    p_price.add_argument("--epic", required=True)

    p_market = sub.add_parser("get-market-info", help="instrument info")
    p_market.add_argument("--epic", required=True)

    p_search = sub.add_parser("search", help="search markets")
    p_search.add_argument("--query", required=True)

    p_ohlc = sub.add_parser("ohlcv", help="recent OHLCV bars")
    p_ohlc.add_argument("--epic", required=True)
    p_ohlc.add_argument("--resolution", default="MINUTE_5")
    p_ohlc.add_argument("--count", type=int, default=20)

    p_hist = sub.add_parser("historical", help="historical OHLCV by date range")
    p_hist.add_argument("--epic", required=True)
    p_hist.add_argument("--from", dest="from_dt", required=True,
                        help="ISO 8601, e.g. 2026-05-01T00:00:00")
    p_hist.add_argument("--to", dest="to_dt", required=True)
    p_hist.add_argument("--resolution", default="MINUTE_5")

    p_hist2 = sub.add_parser("history", help="trade transaction history")
    p_hist2.add_argument("--days", type=int, default=30)

    p_open = sub.add_parser("open", help="open a position (USE DEMO ONLY for testing)")
    p_open.add_argument("--epic", required=True)
    p_open.add_argument("--direction", choices=["BUY", "SELL"], required=True)
    p_open.add_argument("--size", type=float, required=True)
    p_open.add_argument("--order-type", choices=["MARKET", "LIMIT", "STOP"],
                        default="MARKET")
    p_open.add_argument("--level", type=float, default=None)
    p_open.add_argument("--stop", type=float, default=None)
    p_open.add_argument("--limit", type=float, default=None)
    p_open.add_argument("--ref", default=None,
                        help="client-supplied deal_reference (idempotency)")
    p_open.add_argument("--currency", default="EUR")

    p_close = sub.add_parser("close", help="close a position by deal_id")
    p_close.add_argument("--deal-id", required=True)

    p_mod = sub.add_parser("modify", help="modify stop/limit on an open position")
    p_mod.add_argument("--deal-id", required=True)
    p_mod.add_argument("--stop", type=float, default=None)
    p_mod.add_argument("--limit", type=float, default=None)

    p_rec = sub.add_parser("reconcile", help="compare expected refs to broker truth")
    p_rec.add_argument("--refs", nargs="*", default=None,
                       help="expected deal_references to check")

    args = parser.parse_args(argv)
    _setup_logging(args.verbose)

    try:
        broker = get_broker(args.broker)
    except CredentialNotFoundError as e:
        env = error_envelope(
            broker=args.broker, method="init",
            code="CREDENTIAL_NOT_FOUND", message=str(e),
            retryable=False, latency_ms=0,
        )
        return _emit(env)
    except ValueError as e:
        env = error_envelope(
            broker=args.broker, method="init",
            code="INVALID_BROKER", message=str(e),
            retryable=False, latency_ms=0,
        )
        return _emit(env)

    # connect once for everything except the explicit connect/disconnect commands.
    if args.cmd not in ("connect", "disconnect"):
        conn_env = broker.connect()
        if not conn_env.ok:
            return _emit(conn_env)

    try:
        env = _dispatch(broker, args)
    except BrokerError as e:
        env = error_envelope(
            broker=args.broker, method=args.cmd,
            code=e.code, message=str(e),
            retryable=e.retryable, latency_ms=0,
        )
    finally:
        if args.cmd not in ("connect",):
            broker.disconnect()

    return _emit(env)


def _dispatch(broker, args) -> Envelope:
    c = args.cmd
    if c == "connect":       return broker.connect()
    if c == "disconnect":    return broker.disconnect()
    if c == "get-account":   return broker.get_account()
    if c == "get-positions": return broker.get_open_positions()
    if c == "get-price":     return broker.get_price(args.epic)
    if c == "get-market-info": return broker.get_market_info(args.epic)
    if c == "search":        return broker.search_markets(args.query)
    if c == "ohlcv":
        return broker.get_ohlcv(args.epic, args.resolution, args.count)
    if c == "historical":
        return broker.get_historical_ohlcv(
            args.epic, args.from_dt, args.to_dt, args.resolution,
        )
    if c == "history":       return broker.get_trade_history(days=args.days)
    if c == "open":
        return broker.open_position(
            args.epic, args.direction, args.size, args.order_type,
            level=args.level, stop_level=args.stop, limit_level=args.limit,
            deal_reference=args.ref, currency=args.currency,
        )
    if c == "close":         return broker.close_position(args.deal_id)
    if c == "modify":
        return broker.modify_position(
            args.deal_id, stop_level=args.stop, limit_level=args.limit,
        )
    if c == "reconcile":     return broker.reconcile_positions(args.refs)
    raise ValueError(f"unknown command {c}")


if __name__ == "__main__":
    sys.exit(main())
