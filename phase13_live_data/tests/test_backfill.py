"""Phase 13 §6 C1 — tests for ``live_data.backfill``.

All mocked: no network, no live DB. ``CapitalSource`` exercises real
``requests.post``/``requests.get`` through a monkey-patch in the
``requests`` namespace (the module imports ``requests`` directly).
``archive`` is a real in-memory ``BarArchive`` on a tmp_path SQLite
(per Phase 12 D4).
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from unittest.mock import MagicMock, patch

import pytest

from data_foundation.archive import BarArchive
from live_data import backfill as backfill_mod
from live_data.backfill import (
    CapitalSource,
    EPIC_MAP,
    SOURCE_TAG,
    run_capital_backfill,
)


# ---------- helpers --------------------------------------------------------


class _Resp:
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
    """Replace ``live_data.backfill.requests.post`` and ``.get`` with a
    MagicMock that pops responses in order."""
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


def _make_source(identifier: str = "u@example.com",
                 password: str = "custom-pwd",
                 api_key: str = "abcdef0123456789") -> CapitalSource:
    return CapitalSource(identifier, password, api_key)


@pytest.fixture
def archive(tmp_path) -> BarArchive:
    a = BarArchive(tmp_path / "bars.sqlite")
    a.ensure_schema()
    yield a
    a.close()


# ---------- tests -----------------------------------------------------------


def test_authenticate_success_sets_cst_and_security_token():
    p1, p2, calls = _patch_requests([
        _Resp(200, headers={"CST": "tok-cst", "X-SECURITY-TOKEN": "tok-sec"}),
    ])
    with p1, p2:
        src = _make_source()
        src.authenticate()
    assert src._cst == "tok-cst"
    assert src._security_token == "tok-sec"
    assert calls[0]["method"] == "post"
    assert "/api/v1/session" in calls[0]["url"]
    # Body must contain identifier + password + encryptedPassword:false
    sent = calls[0]["json"]
    assert sent["identifier"] == "u@example.com"
    assert sent["password"] == "custom-pwd"
    assert sent["encryptedPassword"] is False
    # Header must carry the API key (NOT in the body).
    sent_headers = calls[0]["headers"]
    assert sent_headers["X-CAP-API-KEY"] == "abcdef0123456789"
    assert "apiKey" not in sent
    assert "api_key" not in sent


def test_authenticate_401_raises():
    p1, p2, _ = _patch_requests([
        _Resp(401, text='{"errorCode":"error.invalid"}'),
    ])
    with p1, p2:
        src = _make_source()
        with pytest.raises(RuntimeError, match="auth failed"):
            src.authenticate()


def test_fetch_window_returns_empty_for_unknown_epic():
    """Spain 35 is not in EPIC_MAP — fetch_window returns [] without any HTTP call."""
    p1, p2, calls = _patch_requests([])
    with p1, p2:
        src = _make_source()
        bars = src.fetch_window(
            "IX.D.IBEX.FWM2.IP",
            datetime(2026, 8, 21, 18, 0, tzinfo=timezone.utc),
            datetime(2026, 8, 21, 19, 0, tzinfo=timezone.utc),
        )
    assert bars == []
    assert calls == [], "no HTTP call expected for unmapped epic"


def test_fetch_window_parses_local_timestamps_to_utc():
    """Empirically (2026-08-19): Capital.com returns LOCAL timestamps
    (Europe/Madrid, UTC+2 in summer). A timestamp '2026-08-21T20:54:00'
    is 18:54 UTC, NOT 20:54 UTC. Verify our conversion."""
    p1, p2, _ = _patch_requests([
        _Resp(200, headers={"CST": "c", "X-SECURITY-TOKEN": "s"}),
        _Resp(200, json_body={
            "prices": [
                {
                    "epic": "DE40",
                    "snapshotTime": "2026-08-21T20:54:00",   # LOCAL (CEST)
                    "openPrice": {"bid": 100.0, "ask": 100.2},
                    "highPrice": {"bid": 101.0, "ask": 101.2},
                    "lowPrice":  {"bid":  99.0, "ask":  99.2},
                    "closePrice":{"bid": 100.5, "ask": 100.7},
                },
            ],
        }),
    ])
    with p1, p2:
        src = _make_source()
        bars = src.fetch_window(
            "IX.D.DAX.IFMM.IP",
            datetime(2026, 8, 21, 17, 0, tzinfo=timezone.utc),
            datetime(2026, 8, 21, 21, 0, tzinfo=timezone.utc),
        )
    assert len(bars) == 1
    bar = bars[0]
    # 2026-08-21T20:54:00 CEST = 2026-08-21T18:54:00 UTC
    assert bar.ts_utc == datetime(2026, 8, 21, 18, 54, tzinfo=timezone.utc)
    # OHLC mid prices
    assert bar.open == pytest.approx(100.1)
    assert bar.high == pytest.approx(101.1)
    assert bar.low == pytest.approx(99.1)
    assert bar.close == pytest.approx(100.6)


def test_fetch_window_filters_synthetic_off_hours_bars():
    """O==H==L==C + volume 0 ⇒ skip per Plan §6 C1.0 Rule 2."""
    p1, p2, _ = _patch_requests([
        _Resp(200, headers={"CST": "c", "X-SECURITY-TOKEN": "s"}),
        _Resp(200, json_body={
            "prices": [
                # Real bar
                {"snapshotTime": "2026-08-21T20:00:00", "openPrice": 100.0,
                 "highPrice": 101.0, "lowPrice": 99.0, "closePrice": 100.5, "volume": 42},
                # Synthetic off-hours bar (all equal + no volume)
                {"snapshotTime": "2026-08-21T20:01:00", "openPrice": 50.0,
                 "highPrice": 50.0, "lowPrice": 50.0, "closePrice": 50.0, "volume": 0},
                # Synthetic with no volume field at all
                {"snapshotTime": "2026-08-21T20:02:00", "openPrice": 60.0,
                 "highPrice": 60.0, "lowPrice": 60.0, "closePrice": 60.0},
            ],
        }),
    ])
    with p1, p2:
        src = _make_source()
        bars = src.fetch_window(
            "IX.D.DAX.IFMM.IP",
            datetime(2026, 8, 21, 18, 0, tzinfo=timezone.utc),
            datetime(2026, 8, 21, 21, 0, tzinfo=timezone.utc),
        )
    assert len(bars) == 1, "the two synthetic bars must be filtered out"
    assert bars[0].ts_utc == datetime(2026, 8, 21, 18, 0, tzinfo=timezone.utc)


def test_fetch_window_filters_out_of_window_bars():
    """Rule 1: bar timestamps outside the requested window are rejected."""
    p1, p2, _ = _patch_requests([
        _Resp(200, headers={"CST": "c", "X-SECURITY-TOKEN": "s"}),
        _Resp(200, json_body={
            "prices": [
                # Inside window (window is 18:00-20:00 UTC)
                {"snapshotTime": "2026-08-21T20:00:00", "openPrice": 100.0,
                 "highPrice": 101.0, "lowPrice": 99.0, "closePrice": 100.5, "volume": 42},
                # Way outside the window (>1 min tolerance)
                {"snapshotTime": "2026-08-21T22:30:00", "openPrice": 200.0,
                 "highPrice": 201.0, "lowPrice": 99.0, "closePrice": 200.5, "volume": 99},
            ],
        }),
    ])
    with p1, p2:
        src = _make_source()
        bars = src.fetch_window(
            "IX.D.DAX.IFMM.IP",
            datetime(2026, 8, 21, 18, 0, tzinfo=timezone.utc),
            datetime(2026, 8, 21, 20, 0, tzinfo=timezone.utc),
        )
    assert len(bars) == 1
    assert bars[0].open == pytest.approx(100.0)


def test_fetch_window_retries_on_429_then_succeeds():
    """Rule 4: HTTP 429 ⇒ exponential backoff + retry."""
    p1, p2, calls = _patch_requests([
        _Resp(200, headers={"CST": "c", "X-SECURITY-TOKEN": "s"}),  # auth
        _Resp(429, text="rate limited"),
        _Resp(200, json_body={
            "prices": [
                {"snapshotTime": "2026-08-21T20:00:00", "openPrice": 100.0,
                 "highPrice": 101.0, "lowPrice": 99.0, "closePrice": 100.5, "volume": 42},
            ],
        }),
    ])
    # Make the backoff effectively zero for the test.
    original_backoff = backfill_mod.CapitalSource._backoff
    backfill_mod.CapitalSource._backoff = lambda self, attempt, reason: None
    try:
        with p1, p2:
            src = _make_source()
            bars = src.fetch_window(
                "IX.D.DAX.IFMM.IP",
                datetime(2026, 8, 21, 18, 0, tzinfo=timezone.utc),
                datetime(2026, 8, 21, 21, 0, tzinfo=timezone.utc),
            )
        assert len(bars) == 1
        # 1 auth call + 2 price calls (1 × 429 + 1 × 200)
        price_calls = [c for c in calls if "get" in c["method"] and "/prices/" in c["url"]]
        assert len(price_calls) == 2
    finally:
        backfill_mod.CapitalSource._backoff = original_backoff


def test_fetch_window_non_retriable_error_propagates():
    """HTTP 404 / 400 / 401 must NOT be retried — surface immediately
    so the script can decide (e.g. fall back to path C for 404)."""
    p1, p2, calls = _patch_requests([
        _Resp(200, headers={"CST": "c", "X-SECURITY-TOKEN": "s"}),
        _Resp(404, text='{"errorCode":"error.prices.not-found"}'),
    ])
    with p1, p2:
        src = _make_source()
        # Use a MAPPED epic (DE40) so the HTTP /prices/ call actually
        # happens — Spain 35 / IX.D.IBEX.FWM2.IP would short-circuit
        # at the EPIC_MAP check before any HTTP.
        with pytest.raises(RuntimeError, match="HTTP 404"):
            src.fetch_window(
                "IX.D.DAX.IFMM.IP",
                datetime(2026, 8, 21, 18, 0, tzinfo=timezone.utc),
                datetime(2026, 8, 21, 21, 0, tzinfo=timezone.utc),
            )
    # No retry — exactly one /prices/ call.
    price_calls = [c for c in calls if "get" in c["method"] and "/prices/" in c["url"]]
    assert len(price_calls) == 1


def test_run_capital_backfill_writes_to_archive(tmp_path):
    """End-to-end: fetch + write + verify archive has the bar with
    ``source='capital'``.

    Uses ``tmp_path`` (Phase-14 finding B5): a per-test fresh archive so the
    ``written += archive.insert_bars(...)`` counter reflects *genuinely new*
    rows, not duplicates against a leftover ``/tmp/test_capital_backfill_e2e/``
    from a prior session — which is what the previous hardcoded-path version
    silently did, and what the old ``written += 1`` hid.
    """
    p1, p2, _ = _patch_requests([
        _Resp(200, headers={"CST": "c", "X-SECURITY-TOKEN": "s"}),
        _Resp(200, json_body={
            "prices": [
                {"snapshotTime": "2026-08-21T20:00:00", "openPrice": 100.0,
                 "highPrice": 101.0, "lowPrice": 99.0, "closePrice": 100.5, "volume": 42},
                {"snapshotTime": "2026-08-21T20:01:00", "openPrice": 100.5,
                 "highPrice": 101.5, "lowPrice": 99.5, "closePrice": 101.0, "volume": 17},
            ],
        }),
    ])
    archive = BarArchive(tmp_path / "bars.sqlite")
    archive.ensure_schema()
    try:
        with p1, p2:
            src = _make_source()
            results = run_capital_backfill(
                src, archive,
                epics=["IX.D.DAX.IFMM.IP"],
                start_utc=datetime(2026, 8, 21, 18, 0, tzinfo=timezone.utc),
                end_utc=datetime(2026, 8, 21, 21, 0, tzinfo=timezone.utc),
            )
        assert results == {"IX.D.DAX.IFMM.IP": 2}
        # Verify the rows landed in the archive under source='capital'.
        rows = archive.window(
            "IX.D.DAX.IFMM.IP", "1m",
            "2026-08-21T18:00:00.000Z",
            "2026-08-21T21:00:00.000Z",
            sources=(SOURCE_TAG,),
        )
        assert len(rows) == 2
        assert all(r.source == "capital" for r in rows)
        ts_set = {r.ts_utc for r in rows}
        assert ts_set == {
            "2026-08-21T18:00:00.000Z",
            "2026-08-21T18:01:00.000Z",
        }
    finally:
        archive.close()


def test_run_capital_backfill_records_zero_for_unmapped_epics(tmp_path):
    """Spain 35 + AEX + MIB are not in EPIC_MAP — run_capital_backfill
    returns 0 for each, leaves archive untouched. Script-level fallback
    to Path C (Dukascopy) is the caller's job (deferred to a future
    session per Nikinger-Auflage 2026-08-19)."""
    p1, p2, _ = _patch_requests([])
    archive = BarArchive(tmp_path / "bars.sqlite")
    archive.ensure_schema()
    try:
        with p1, p2:
            src = _make_source()
            results = run_capital_backfill(
                src, archive,
                epics=["IX.D.IBEX.FWM2.IP", "IX.D.AEX.IFM.IP", "IX.D.MIB.MFM.IP"],
                start_utc=datetime(2026, 8, 21, 18, 0, tzinfo=timezone.utc),
                end_utc=datetime(2026, 8, 21, 21, 0, tzinfo=timezone.utc),
            )
        assert results == {
            "IX.D.IBEX.FWM2.IP": 0,
            "IX.D.AEX.IFM.IP": 0,
            "IX.D.MIB.MFM.IP": 0,
        }
    finally:
        archive.close()


def test_epic_map_does_not_contain_path_c_territory():
    """Phase-13 Hybrid-Entscheidung: Spain 35 (IBEX), AEX (Netherlands),
    MIB (Italy) are Path C territory (Dukascopy), not Path B.
    Lock this in via test — if anyone later adds them to EPIC_MAP,
    the test fails loud."""
    assert "IX.D.IBEX.FWM2.IP" not in EPIC_MAP
    assert "IX.D.AEX.IFM.IP" not in EPIC_MAP
    assert not any("IX.D.MIB" in k for k in EPIC_MAP.keys())
