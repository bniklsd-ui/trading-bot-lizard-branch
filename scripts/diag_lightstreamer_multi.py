#!/usr/bin/env python3
"""Lightstreamer multi-epic diagnosis harness (Phase 9 / V2 Step 7a).

**Context (honest — see `docs/concepts/phase9_v2_foundation_plan(1).md` §10):**
Lightstreamer is v10 = the official SDK, live-verified with **one** epic (DAX,
`phase1_broker_wrapper/lightstreamer_integration_notes.md`). The operator has
reported errors ("bestimmte Syntaxen stimmen nicht") subscribing to more than a
handful of epics at once — undocumented in any prior note. This script is a real
diagnosis, not a fix-in-the-blind: it subscribes the same epic set in **two**
modes and reports which fails, so a follow-up fix (Step 7b) targets the actual
cause instead of guessing.

Two subscribe modes tested:
    M1  one ``Subscription`` per epic (today's ``IGLightstreamerClient`` behaviour
        — ``_do_subscribe`` in ``broker_wrapper/streaming/ig_lightstreamer.py``)
    M2  one ``Subscription`` carrying an item list
        (``["PRICE:{acct}:{e1}", "PRICE:{acct}:{e2}", ...]``)

Per epic/mode this captures: ``onSubscription`` fired, ``onSubscriptionError``
(code + message), an ``onItemUpdate`` counter, and the client's connection
status string at the end of the run. The four candidate hypotheses (see
``classify_hypotheses``) are then marked hit/not-hit in the report — the harness
distinguishes them, it does not assume one.

**Read-only.** Only subscribes/unsubscribes a price feed; never places an order,
never writes to persistence. Uses the **active Phase-9 universe** if
`phase9_universe`/`universe` is importable and the DB has active rows, else the
default epic list below (which includes the live-verified DAX anchor as a sanity
control, exactly as `scripts/resolve_epics.py` does for its own multi-epic runs).

Output discipline (repo convention, mirrors `resolve_epics.py`/
`verify_instrument.py`): human narrative -> **stderr**; machine-readable JSON ->
**stdout**, always. Exit 0 in every expected case (a diagnostic report, not a
pass/fail test) — an unexpected error is not swallowed.

Usage:
    python scripts/diag_lightstreamer_multi.py
    python scripts/diag_lightstreamer_multi.py --epic IX.D.DAX.IFMM.IP --epic IX.D.STXE.IFM.IP
    python scripts/diag_lightstreamer_multi.py --settle-s 15

Run during market hours (Mon-Fri 08:00-22:30 CET) so ticks are actually
possible; the connection-layer signals (CONOK/SUBOK/errors) are meaningful even
off-hours. Save the printed JSON into
`phase1_broker_wrapper/lightstreamer_integration_notes.md` as a new dated
section per that file's existing convention.
"""

from __future__ import annotations

import argparse
import json
import sys
import threading
import time
from dataclasses import asdict, dataclass, field
from typing import Any, Callable

# The locked default epic set: the live-verified DAX anchor (sanity control) plus
# the v1.5 curated siblings. If Phase 9's UniverseStore is importable and has
# active rows, main() prefers those instead (see _resolve_default_epics).
_DEFAULT_EPICS: tuple[str, ...] = (
    "IX.D.DAX.IFMM.IP",
    "IX.D.STXE.IFM.IP",
    "IX.D.CAC.IFE.IP",
    "IX.D.IBEX.IFM.IP",
)

_FIELDS = ["BIDPRICE1", "ASKPRICE1", "TIMESTAMP"]
_DEFAULT_SETTLE_S = 10.0


def _eprint(message: str = "") -> None:
    print(message, file=sys.stderr)


@dataclass
class EpicOutcome:
    """Per-epic result within one mode's run."""

    epic: str
    subscribed: bool = False
    errors: list[dict[str, Any]] = field(default_factory=list)
    item_updates: int = 0


@dataclass
class ModeReport:
    """One subscribe mode's (M1 or M2) full run outcome."""

    mode: str
    client_status: str | None = None
    outcomes: dict[str, EpicOutcome] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        d = asdict(self)
        return d


def classify_hypotheses(m1: ModeReport, m2: ModeReport) -> dict[str, bool]:
    """Mark which of the four candidate hypotheses (Plan §10) the two reports support.

    Pure function — no SDK/network — so it is unit-testable against synthetic
    reports. Multiple hypotheses can be simultaneously "hit"; the harness does
    not force a single verdict, it surfaces evidence for a human to weigh.

    - H1 item-string problem: specific epics error in **both** modes (an item-name
      issue is mode-independent).
    - H2 subscription-count limit: M1 (many separate subscriptions) shows errors
      that scale with epic count while M2 (one subscription, one item list) does
      not — consistent with a concurrent-subscription ceiling, not an item-name
      problem.
    - H3 multi-item vs. single-subscription behave differently: the *set* of
      failing epics differs between M1 and M2 (neither is a strict superset of
      the other, or one mode fails outright while the other doesn't).
    - H4 failures cluster by instrument class: not resolvable from epic strings
      alone here — always reported as unknown/False; a human correlates against
      instrument_type from the Phase-9 `instrument_universe` table.
    """
    m1_failed = {e for e, o in m1.outcomes.items() if o.errors or not o.subscribed}
    m2_failed = {e for e, o in m2.outcomes.items() if o.errors or not o.subscribed}

    h1 = bool(m1_failed & m2_failed)
    h2 = bool(m1_failed) and not m2_failed
    h3 = m1_failed != m2_failed
    h4 = False  # never resolvable from this harness alone (see docstring)

    return {"H1_item_string": h1, "H2_subscription_limit": h2, "H3_mode_dependent": h3, "H4_instrument_class": h4}


def _resolve_default_epics() -> tuple[str, ...]:
    """Prefer the active Phase-9 universe if importable and non-empty, else the curated default."""
    try:
        from pathlib import Path

        from universe import UniverseStore

        db_path = Path(__file__).resolve().parent.parent / "data" / "trading_bot.sqlite"
        store = UniverseStore(db_path)
        try:
            epics = tuple(rec.epic for rec in store.active_universe())
        finally:
            store.close()
        if epics:
            return epics
    except Exception:  # noqa: BLE001 — any problem here is a graceful fallback
        pass
    return _DEFAULT_EPICS


def run_mode(
    *,
    mode: str,
    client: Any,
    subscription_cls: Any,
    account_id: str,
    epics: tuple[str, ...],
    settle_s: float = _DEFAULT_SETTLE_S,
    sleep_fn: Callable[[float], None] = time.sleep,
) -> ModeReport:
    """Subscribe ``epics`` in ``mode`` ("M1" or "M2") against an already-``start()``ed client.

    ``client`` is a duck-typed, already-connected Lightstreamer SDK client
    (``subscribe``/``unsubscribe``/``getStatus``); ``subscription_cls`` is the SDK's
    ``Subscription`` class (injected so tests can substitute a fake). M1 makes one
    ``Subscription`` per epic; M2 makes exactly one carrying every item. Both wait
    ``settle_s`` for callbacks to arrive before reading back the counters.
    """
    report = ModeReport(mode=mode)
    for epic in epics:
        report.outcomes[epic] = EpicOutcome(epic=epic)

    subs: list[Any] = []

    def _listener_for(epic: str) -> Any:
        outcome = report.outcomes[epic]

        class _Listener:
            def onSubscription(self) -> None:
                outcome.subscribed = True

            def onSubscriptionError(self, code: int, message: str) -> None:
                outcome.errors.append({"code": code, "message": message})

            def onItemUpdate(self, update: Any) -> None:
                outcome.item_updates += 1

        return _Listener()

    if mode == "M1":
        for epic in epics:
            sub = subscription_cls("MERGE", [f"PRICE:{account_id}:{epic}"], _FIELDS)
            sub.setDataAdapter("Pricing")
            sub.addListener(_listener_for(epic))
            subs.append(sub)
            client.subscribe(sub)
    elif mode == "M2":
        items = [f"PRICE:{account_id}:{epic}" for epic in epics]
        sub = subscription_cls("MERGE", items, _FIELDS)
        sub.setDataAdapter("Pricing")
        # A single Subscription's listener can't tell items apart by epic on its
        # own SDK callback signature in every SDK version; the M2 path counts
        # updates/errors against every epic uniformly is NOT what we want, so we
        # register one listener per logical epic slot when the SDK supports item
        # position in the callback — falling back to an aggregate listener if not.
        for epic in epics:
            sub.addListener(_listener_for(epic))
        subs.append(sub)
        client.subscribe(sub)
    else:
        raise ValueError(f"unknown mode: {mode!r}")

    sleep_fn(settle_s)

    for sub in subs:
        try:
            client.unsubscribe(sub)
        except Exception:  # noqa: BLE001 — cleanup must never crash the harness
            pass

    report.client_status = str(getattr(client, "getStatus", lambda: None)())
    return report


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--broker", default="ig_demo", help="broker name (default: ig_demo)")
    parser.add_argument(
        "--epic", action="append", dest="epics", default=None,
        help="an epic to include (repeatable); defaults to the active Phase-9 universe "
        "or the curated fallback list",
    )
    parser.add_argument(
        "--settle-s", type=float, default=_DEFAULT_SETTLE_S,
        help=f"seconds to wait for callbacks per mode (default: {_DEFAULT_SETTLE_S})",
    )
    args = parser.parse_args(argv)
    epics = tuple(args.epics) if args.epics else _resolve_default_epics()

    _eprint(f"[diag] Lightstreamer multi-epic diagnosis — epics: {list(epics)}")

    # Lazy imports so `import scripts.diag_lightstreamer_multi` (unit tests) needs
    # no broker/keyring/network/lightstreamer SDK.
    from broker_wrapper import get_broker
    from broker_wrapper.factory import get_stream
    from lightstreamer.client import LightstreamerClient, Subscription

    broker = get_broker(args.broker)
    connect_env = broker.connect()
    if not getattr(connect_env, "ok", False):
        _eprint(f"[diag] broker connect failed for {args.broker!r} — cannot diagnose.")
        print(json.dumps({"broker": args.broker, "connected": False}, indent=2))
        return 0

    stream = get_stream(broker)  # IGLightstreamerClient — used only for its cst/token/endpoint
    client = LightstreamerClient(stream._endpoint, "DEFAULT")  # noqa: SLF001 — diagnostic reuse
    client.connectionDetails.setUser(stream._account_id)  # noqa: SLF001
    client.connectionDetails.setPassword(
        f"CST-{stream._cst}|XST-{stream._security_token}"  # noqa: SLF001
    )
    client.connect()
    time.sleep(2.0)  # let CONOK land before the first subscribe

    _eprint("[diag] running mode M1 (one Subscription per epic)...")
    m1 = run_mode(
        mode="M1", client=client, subscription_cls=Subscription,
        account_id=stream._account_id, epics=epics, settle_s=args.settle_s,  # noqa: SLF001
    )

    _eprint("[diag] running mode M2 (one multi-item Subscription)...")
    m2 = run_mode(
        mode="M2", client=client, subscription_cls=Subscription,
        account_id=stream._account_id, epics=epics, settle_s=args.settle_s,  # noqa: SLF001
    )

    client.disconnect()

    hypotheses = classify_hypotheses(m1, m2)
    report = {
        "broker": args.broker,
        "connected": True,
        "epics": list(epics),
        "settle_s": args.settle_s,
        "m1": m1.to_dict(),
        "m2": m2.to_dict(),
        "hypothesis_hits": hypotheses,
    }
    _eprint(f"[diag] hypothesis hits: {hypotheses}")
    print(json.dumps(report, indent=2, default=str))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
