"""Phase 14 B1b — tests for ``CapitalSource.discover``.

All mocked: no network, no live DB. Same harness shape as
``tests/test_backfill.py`` (``_patch_requests`` against
``live_data.backfill.requests.post``/``.get``).

What these tests pin (the B1b acceptance criteria from
``docs/concepts/phase14_discovery_plan.md`` §6 B1 / §7 A1):

- The discovery response shape ``{ "markets": [...] }`` is iterated and
  filtered to ``instrumentName == name`` AND ``instrumentType == "INDICES"``
  (the Phase-14 B1a Befund 3 insight — the older substring ``"CFD"`` was a
  no-op against the actual response).
- An unknown epic (not in ``_DISPLAY_NAME_BY_EPIC``) emits ``no_source``
  WITHOUT an HTTP call — adding a source is configuration, not guessing
  (Plan §6 B1 / D6).
- ``max_probe_calls`` is a hard deckel (Plan D14). Once exhausted, remaining
  epics emit ``no_source`` without HTTP.
- Failures (network, parse, non-200) populate ``SourceProfile.errors`` and
  the iteration continues. ``discover()`` never raises (Plan §8.5).
"""

from __future__ import annotations

import json
from unittest.mock import patch

import pytest

from live_data import backfill as backfill_mod
from live_data.backfill import CapitalSource
from source_registry.models import (
    SOURCE_CAPITAL,
    STATUS_NO_SOURCE,
    STATUS_OK,
    SourceAvailability,
    SourceProfile,
)


# ---------- helpers --------------------------------------------------------


class _Resp:
    """Minimal response shim — same shape as ``tests/test_backfill.py``."""

    def __init__(self, status_code: int, json_body: dict | None = None,
                 text: str = "", headers: dict | None = None) -> None:
        self.status_code = status_code
        self._json = json_body
        self.text = text or (json.dumps(json_body) if json_body is not None else "")
        self.headers = headers or {}

    def json(self) -> dict:
        if self._json is None:
            raise ValueError("no json body")
        return self._json


def _patch_requests(responses: list[_Resp]):
    """Replace ``live_data.backfill.requests.post``/``.get`` with a queue.

    Mirrors the helper in ``tests/test_backfill.py``. Returns the two
    patchers and a ``calls`` list that captures every URL/method/kwargs
    pair (assertion surface for "no HTTP was made for unknown epics").
    """
    calls: list[dict] = []

    def _fake_post(url, **kwargs):
        calls.append({"method": "post", "url": url, **kwargs})
        if not responses:
            raise AssertionError(f"unexpected POST {url}")
        return responses.pop(0)

    def _fake_get(url, **kwargs):
        calls.append({"method": "get", "url": url, **kwargs})
        if not responses:
            raise AssertionError(f"unexpected GET {url}")
        return responses.pop(0)

    p1 = patch.object(backfill_mod.requests, "post", side_effect=_fake_post)
    p2 = patch.object(backfill_mod.requests, "get", side_effect=_fake_get)
    return p1, p2, calls


def _make_source() -> CapitalSource:
    return CapitalSource("u@example.com", "custom-pwd", "abcdef0123456789")


# ---------- happy path -----------------------------------------------------


def test_discover_dax_happy_path_emits_ok_with_de40_symbol():
    """DE40 / Germany 40 happy path: B1a Befund 2 — the ``epic`` field of
    the first INDICES match is the source's own symbol."""
    markets_body = {
        "markets": [
            # First entry is the wrong type — must be skipped.
            {
                "instrumentName": "Germany 40",
                "instrumentType": "SHARES",
                "epic": "DUMMY-SHARES",
            },
            # Second entry is the canonical INDICES match.
            {
                "instrumentName": "Germany 40",
                "instrumentType": "INDICES",
                "epic": "DE40",
                "delayTime": 0,
            },
        ]
    }
    p1, p2, calls = _patch_requests([
        _Resp(200, headers={"CST": "tok", "X-SECURITY-TOKEN": "sec"},
              json_body={"accounts": [{"preferred": True, "accountType": "CFD"}]}),
        _Resp(200, json_body=markets_body),
    ])
    with p1, p2:
        src = _make_source()
        profile: SourceProfile = src.discover(
            ["IX.D.DAX.IFMM.IP"], max_probe_calls=8,
        )

    # Auth POST + one /markets GET — exactly one probe against the deckel.
    assert [c["method"] for c in calls] == ["post", "get"]
    assert "/api/v1/session" in calls[0]["url"]
    assert calls[1]["url"].endswith("/api/v1/markets")
    assert calls[1]["params"] == {"searchTerm": "Germany 40"}

    # One row, status='ok', source_symbol='DE40', discovery origin.
    assert profile.source == SOURCE_CAPITAL
    assert profile.probe_calls_used == 1
    assert profile.errors == ()
    assert len(profile.rows) == 1
    row: SourceAvailability = profile.rows[0]
    assert row.epic == "IX.D.DAX.IFMM.IP"
    assert row.source == "capital"
    assert row.resolution == "1m"
    assert row.source_symbol == "DE40"
    assert row.status == STATUS_OK
    assert row.origin == "discovery"
    assert row.history_min_days == 30
    assert row.latency_min == 0
    assert row.last_verified_utc.endswith("Z")  # ms-precision ISO format
    assert row.notes is None


# ---------- unknown epic: no HTTP, no_source -------------------------------


def test_discover_unknown_epic_emits_no_source_without_http():
    """An epic outside ``_DISPLAY_NAME_BY_EPIC`` is configuration, not a
    guess. ``discover()`` must NOT make an HTTP call for it — adding a
    source is operator work (Plan §6 B1 / D6)."""
    p1, p2, calls = _patch_requests([
        # Even if auth is configured to succeed, no /markets GET should
        # happen for the unknown epic.
        _Resp(200, headers={"CST": "tok", "X-SECURITY-TOKEN": "sec"},
              json_body={"accounts": [{"preferred": True, "accountType": "CFD"}]}),
    ])
    with p1, p2:
        src = _make_source()
        profile = src.discover(["IX.D.FOO.IP"], max_probe_calls=8)

    # Auth POST is one-off; zero probe GETs.
    assert [c["method"] for c in calls] == ["post"]
    assert profile.probe_calls_used == 0
    assert profile.errors == ()

    assert len(profile.rows) == 1
    row = profile.rows[0]
    assert row.epic == "IX.D.FOO.IP"
    assert row.source_symbol is None
    assert row.status == STATUS_NO_SOURCE
    assert row.origin == "discovery"
    assert "no display name registered" in (row.notes or "")
    assert row.history_min_days is None
    assert row.latency_min is None


# ---------- search hit, but wrong instrumentType → no_source ----------------


def test_discover_search_hit_without_indices_emits_no_source():
    """The search returned the index name, but only in a non-INDICES type
    (SHARES / COMMODITIES / etc.). We must NOT pick it — discover()'s
    contract is INDICES only (B1a Befund 3). The note explains why."""
    markets_body = {
        "markets": [
            {
                "instrumentName": "France 40",
                "instrumentType": "COMMODITIES",
                "epic": "FR40-COMMODITY",
            },
            # A SHARES variant that B1b must also reject.
            {
                "instrumentName": "France 40",
                "instrumentType": "SHARES",
                "epic": "FR40-SHARES",
            },
        ]
    }
    p1, p2, calls = _patch_requests([
        _Resp(200, headers={"CST": "tok", "X-SECURITY-TOKEN": "sec"},
              json_body={"accounts": [{"preferred": True, "accountType": "CFD"}]}),
        _Resp(200, json_body=markets_body),
    ])
    with p1, p2:
        src = _make_source()
        profile = src.discover(["IX.D.CAC.IFE.IP"], max_probe_calls=8)

    assert profile.probe_calls_used == 1
    assert profile.errors == ()
    assert len(profile.rows) == 1
    row = profile.rows[0]
    assert row.epic == "IX.D.CAC.IFE.IP"
    assert row.source_symbol is None
    assert row.status == STATUS_NO_SOURCE
    assert row.history_min_days is None
    assert row.latency_min is None
    assert "no INDICES match" in (row.notes or "")
    assert "France 40" in (row.notes or "")


# ---------- deckel: max_probe_calls=0 → no HTTP, all no_source ------------


def test_discover_max_probe_calls_zero_makes_no_get_calls():
    """``max_probe_calls=0`` is the strict offline-fail mode — zero HTTP,
    every epic emitted as ``no_source`` with the deckel note."""
    p1, p2, calls = _patch_requests([
        _Resp(200, headers={"CST": "tok", "X-SECURITY-TOKEN": "sec"},
              json_body={"accounts": [{"preferred": True, "accountType": "CFD"}]}),
    ])
    with p1, p2:
        src = _make_source()
        profile = src.discover(
            ["IX.D.DAX.IFMM.IP", "IX.D.CAC.IFE.IP", "IX.D.IBEX.FWM2.IP"],
            max_probe_calls=0,
        )

    # Auth POST only — zero /markets GETs against the empty deckel.
    assert [c["method"] for c in calls] == ["post"]
    assert profile.probe_calls_used == 0
    assert profile.errors == ()

    assert len(profile.rows) == 3
    for row in profile.rows:
        assert row.status == STATUS_NO_SOURCE
        assert row.source_symbol is None
        assert "max_probe_calls=0 reached" in (row.notes or "")


def test_discover_max_probe_calls_one_limits_to_first_get():
    """``max_probe_calls=1`` allows the first epic to be probed; subsequent
    epics emit ``no_source`` with the deckel note."""
    p1, p2, calls = _patch_requests([
        _Resp(200, headers={"CST": "tok", "X-SECURITY-TOKEN": "sec"},
              json_body={"accounts": [{"preferred": True, "accountType": "CFD"}]}),
        _Resp(200, json_body={"markets": [{
            "instrumentName": "Germany 40",
            "instrumentType": "INDICES",
            "epic": "DE40",
        }]}),
    ])
    with p1, p2:
        src = _make_source()
        profile = src.discover(
            ["IX.D.DAX.IFMM.IP", "IX.D.CAC.IFE.IP", "IX.D.IBEX.FWM2.IP"],
            max_probe_calls=1,
        )

    assert profile.probe_calls_used == 1
    # First epic: ok. Remaining two: no_source via deckel.
    assert len(profile.rows) == 3
    assert profile.rows[0].status == STATUS_OK
    assert profile.rows[0].source_symbol == "DE40"
    for row in profile.rows[1:]:
        assert row.status == STATUS_NO_SOURCE
        assert "max_probe_calls=1 reached" in (row.notes or "")


# ---------- fail-soft: network/parse/non-200 → errors, no raise ----------


def test_discover_network_failure_yields_error_no_raise():
    """A real ``requests.ConnectionError`` on the GET must populate ``errors``
    and the iteration continues — ``discover()`` never raises (Plan §8.5)."""
    p1 = patch.object(backfill_mod.requests, "post", return_value=_Resp(
        200, headers={"CST": "tok", "X-SECURITY-TOKEN": "sec"},
        json_body={"accounts": [{"preferred": True, "accountType": "CFD"}]},
    ))
    import requests as _requests
    p2 = patch.object(backfill_mod.requests, "get",
                      side_effect=_requests.ConnectionError("connection reset"))
    with p1, p2:
        src = _make_source()
        # Must not raise, must not silently return rows for this epic.
        profile = src.discover(["IX.D.DAX.IFMM.IP"], max_probe_calls=8)

    assert profile.probe_calls_used == 0  # GET failed before accounting
    assert len(profile.errors) == 1
    assert "IX.D.DAX.IFMM.IP" in profile.errors[0]
    assert "connection reset" in profile.errors[0]
    assert profile.rows == ()  # nothing written to the table on failure


def test_discover_non_200_response_yields_error_no_raise():
    """A non-200 GET response (e.g. 429 from rate-limit) is appended to
    ``errors`` and the iteration continues — Plan §8.5."""
    p1 = patch.object(backfill_mod.requests, "post", return_value=_Resp(
        200, headers={"CST": "tok", "X-SECURITY-TOKEN": "sec"},
        json_body={"accounts": [{"preferred": True, "accountType": "CFD"}]},
    ))
    p2 = patch.object(backfill_mod.requests, "get", return_value=_Resp(
        404, text='{"errorCode":"error.not-found"}',
    ))
    with p1, p2:
        src = _make_source()
        profile = src.discover(["IX.D.IBEX.FWM2.IP"], max_probe_calls=8)

    assert profile.probe_calls_used == 1
    assert len(profile.errors) == 1
    assert "IX.D.IBEX.FWM2.IP" in profile.errors[0]
    assert "http_404" in profile.errors[0]
    assert profile.rows == ()


# ---------- lexical parity: B1a snapshot XML equivalence -----------------


def test_discover_matches_b1a_snapshot_for_three_pairs():
    """The three real B1a probe responses for Germany 40 / France 40 /
    Spain 35 (snapshot 2026-08-22) must round-trip through ``discover``
    to ``SourceAvailability`` rows with ``source_symbol`` set to
    ``"DE40" / "FR40" / "SP35"`` respectively — same identity thesis as
    the migration table (Plan §5.1)."""
    germany_body = {"markets": [{
        "instrumentName": "Germany 40", "instrumentType": "INDICES",
        "epic": "DE40", "delayTime": 0,
    }]}
    france_body = {"markets": [{
        "instrumentName": "France 40", "instrumentType": "INDICES",
        "epic": "FR40", "delayTime": 0,
    }]}
    spain_body = {"markets": [{
        "instrumentName": "Spain 35", "instrumentType": "INDICES",
        "epic": "SP35", "delayTime": 0,
    }]}
    p1, p2, _calls = _patch_requests([
        _Resp(200, headers={"CST": "tok", "X-SECURITY-TOKEN": "sec"},
              json_body={"accounts": [{"preferred": True, "accountType": "CFD"}]}),
        _Resp(200, json_body=germany_body),
        _Resp(200, json_body=france_body),
        _Resp(200, json_body=spain_body),
    ])
    with p1, p2:
        src = _make_source()
        profile = src.discover(
            ["IX.D.DAX.IFMM.IP", "IX.D.CAC.IFE.IP", "IX.D.IBEX.FWM2.IP"],
            max_probe_calls=8,
        )

    assert profile.probe_calls_used == 3
    assert profile.errors == ()
    assert len(profile.rows) == 3
    by_epic = {r.epic: r for r in profile.rows}
    assert by_epic["IX.D.DAX.IFMM.IP"].source_symbol == "DE40"
    assert by_epic["IX.D.CAC.IFE.IP"].source_symbol == "FR40"
    assert by_epic["IX.D.IBEX.FWM2.IP"].source_symbol == "SP35"
    for row in profile.rows:
        assert row.status == STATUS_OK
        assert row.latency_min == 0
        assert row.history_min_days == 30
