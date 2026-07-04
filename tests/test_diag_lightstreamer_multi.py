"""Tests for ``scripts/diag_lightstreamer_multi.py`` (Phase 9 / V2 Step 7a).

Loaded via ``importlib`` by file path (root ``scripts/`` is deliberately not an
importable package — the phases already collide on a ``scripts.wiring`` module
name), same convention as ``test_resolve_epics.py``/
``test_diag_score_distribution.py``.

Only the pure logic is exercised here (``classify_hypotheses``, the dataclasses,
``--help``) — the actual subscribe-and-wait-for-SDK-callbacks mechanics are a
live-only diagnostic (no meaningful fake for the Lightstreamer SDK's async
callback threading model), consistent with ``scripts/test_lightstreamer.py``
having no pytest tests either.
"""

from __future__ import annotations

import importlib.util
import subprocess
import sys
from pathlib import Path

_SCRIPT_PATH = Path(__file__).resolve().parent.parent / "scripts" / "diag_lightstreamer_multi.py"
_spec = importlib.util.spec_from_file_location("diag_lightstreamer_multi", _SCRIPT_PATH)
assert _spec is not None and _spec.loader is not None
diag = importlib.util.module_from_spec(_spec)
# Registered in sys.modules before exec: the module defines @dataclass classes, and
# the dataclasses machinery looks up sys.modules[cls.__module__] internally — a
# module loaded via module_from_spec without this registration has __module__ set
# but no sys.modules entry, so that lookup returns None and dataclass() crashes.
sys.modules[_spec.name] = diag
_spec.loader.exec_module(diag)


def _no_sleep(_seconds: float) -> None:
    pass


# -- EpicOutcome / ModeReport --------------------------------------------------


def test_epic_outcome_defaults():
    outcome = diag.EpicOutcome(epic="X")
    assert outcome.subscribed is False
    assert outcome.errors == []
    assert outcome.item_updates == 0


def test_mode_report_to_dict_roundtrips():
    report = diag.ModeReport(mode="M1", client_status="CONNECTED:WS-STREAMING")
    report.outcomes["X"] = diag.EpicOutcome(epic="X", subscribed=True, item_updates=3)
    d = report.to_dict()
    assert d["mode"] == "M1"
    assert d["outcomes"]["X"]["subscribed"] is True
    assert d["outcomes"]["X"]["item_updates"] == 3


# -- classify_hypotheses --------------------------------------------------------


def _report(mode: str, failing_epics: set[str], all_epics: list[str]) -> "diag.ModeReport":
    report = diag.ModeReport(mode=mode)
    for epic in all_epics:
        if epic in failing_epics:
            report.outcomes[epic] = diag.EpicOutcome(epic=epic, subscribed=False, errors=[{"code": 1, "message": "x"}])
        else:
            report.outcomes[epic] = diag.EpicOutcome(epic=epic, subscribed=True)
    return report


def test_no_failures_hits_nothing():
    epics = ["A", "B"]
    m1 = _report("M1", set(), epics)
    m2 = _report("M2", set(), epics)
    hits = diag.classify_hypotheses(m1, m2)
    assert hits == {
        "H1_item_string": False,
        "H2_subscription_limit": False,
        "H3_mode_dependent": False,
        "H4_instrument_class": False,
    }


def test_h1_item_string_same_epic_fails_both_modes():
    epics = ["A", "B"]
    m1 = _report("M1", {"A"}, epics)
    m2 = _report("M2", {"A"}, epics)
    hits = diag.classify_hypotheses(m1, m2)
    assert hits["H1_item_string"] is True


def test_h2_subscription_limit_only_m1_fails():
    epics = ["A", "B", "C"]
    m1 = _report("M1", {"B", "C"}, epics)
    m2 = _report("M2", set(), epics)
    hits = diag.classify_hypotheses(m1, m2)
    assert hits["H2_subscription_limit"] is True
    assert hits["H3_mode_dependent"] is True  # different failing sets


def test_h3_mode_dependent_different_failing_sets():
    epics = ["A", "B"]
    m1 = _report("M1", {"A"}, epics)
    m2 = _report("M2", {"B"}, epics)
    hits = diag.classify_hypotheses(m1, m2)
    assert hits["H3_mode_dependent"] is True
    assert hits["H1_item_string"] is False  # no overlap


def test_h4_never_resolvable_from_harness_alone():
    epics = ["A"]
    m1 = _report("M1", {"A"}, epics)
    m2 = _report("M2", {"A"}, epics)
    hits = diag.classify_hypotheses(m1, m2)
    assert hits["H4_instrument_class"] is False


def test_identical_failures_both_modes_is_not_mode_dependent():
    epics = ["A", "B"]
    m1 = _report("M1", {"A"}, epics)
    m2 = _report("M2", {"A"}, epics)
    hits = diag.classify_hypotheses(m1, m2)
    assert hits["H3_mode_dependent"] is False  # same failing set in both modes


# -- run_mode (fake SDK client/subscription — pure structural correctness) ----


class _FakeSubscription:
    def __init__(self, mode, items, fields):
        self.mode = mode
        self.items = items
        self.fields = fields
        self.listeners = []
        self.data_adapter = None

    def setDataAdapter(self, name):
        self.data_adapter = name

    def addListener(self, listener):
        self.listeners.append(listener)
        # Simulate an immediate successful subscription for every attached listener.
        listener.onSubscription()


class _FakeClient:
    def __init__(self):
        self.subscribed = []
        self.unsubscribed = []

    def subscribe(self, sub):
        self.subscribed.append(sub)

    def unsubscribe(self, sub):
        self.unsubscribed.append(sub)

    def getStatus(self):
        return "CONNECTED:WS-STREAMING"


def test_run_mode_m1_one_subscription_per_epic():
    client = _FakeClient()
    report = diag.run_mode(
        mode="M1", client=client, subscription_cls=_FakeSubscription,
        account_id="ACC1", epics=("A", "B"), settle_s=0.0, sleep_fn=_no_sleep,
    )
    assert len(client.subscribed) == 2  # one Subscription per epic
    assert report.outcomes["A"].subscribed is True
    assert report.outcomes["B"].subscribed is True
    assert len(client.unsubscribed) == 2


def test_run_mode_m2_one_subscription_with_item_list():
    client = _FakeClient()
    report = diag.run_mode(
        mode="M2", client=client, subscription_cls=_FakeSubscription,
        account_id="ACC1", epics=("A", "B"), settle_s=0.0, sleep_fn=_no_sleep,
    )
    assert len(client.subscribed) == 1  # exactly one Subscription
    assert client.subscribed[0].items == ["PRICE:ACC1:A", "PRICE:ACC1:B"]
    assert len(client.unsubscribed) == 1


def test_run_mode_invalid_mode_raises():
    client = _FakeClient()
    import pytest

    with pytest.raises(ValueError):
        diag.run_mode(
            mode="M3", client=client, subscription_cls=_FakeSubscription,
            account_id="ACC1", epics=("A",), settle_s=0.0, sleep_fn=_no_sleep,
        )


def test_run_mode_waits_via_injected_sleep_fn_not_real_sleep():
    calls: list[float] = []
    client = _FakeClient()
    diag.run_mode(
        mode="M1", client=client, subscription_cls=_FakeSubscription,
        account_id="ACC1", epics=("A",), settle_s=3.5, sleep_fn=calls.append,
    )
    assert calls == [3.5]


# -- CLI smoke (no network) ---------------------------------------------------


def test_help_exits_zero():
    result = subprocess.run(
        [sys.executable, str(_SCRIPT_PATH), "--help"],
        capture_output=True, text=True,
    )
    assert result.returncode == 0
    assert "Lightstreamer" in result.stdout
