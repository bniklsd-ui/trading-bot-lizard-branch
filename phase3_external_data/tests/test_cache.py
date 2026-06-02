"""Tests for ``external_data.cache.FileCache`` (concept §9 / §15).

No network. Time is driven through the ``frozen_clock`` fixture (which patches
``timeutil._utcnow``) so TTL expiry is deterministic — ``FileCache`` reads the
clock via ``timeutil._utcnow`` for both ``set`` (computing ``expires_at``) and
``get`` / ``clear_expired`` (comparing against it).
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

from external_data.cache import FileCache


def _utc(year, month, day, hour=12, minute=0) -> datetime:
    """Build a timezone-aware UTC datetime."""
    return datetime(year, month, day, hour, minute, tzinfo=timezone.utc)


SAMPLE = [
    {"ts": "2026-05-25T07:00:00.000Z", "open": 18000.0, "high": 18100.0,
     "low": 17950.0, "close": 18050.0, "volume": 0.0},
    {"ts": "2026-05-25T07:05:00.000Z", "open": 18050.0, "high": 18120.0,
     "low": 18030.0, "close": 18090.0, "volume": 0.0},
]


# -- make_key -----------------------------------------------------------------

def test_make_key_deterministic(tmp_cache):
    # Same inputs → identical key, every time.
    k1 = tmp_cache.make_key("^GDAXI", "1d", "2026-05-25")
    k2 = tmp_cache.make_key("^GDAXI", "1d", "2026-05-25")
    assert k1 == k2


def test_make_key_strips_caret_and_is_fs_safe(tmp_cache):
    # Leading ^ removed (index symbols); '=' (FX pairs) replaced — no FS-unsafe chars.
    assert tmp_cache.make_key("^GDAXI", "1d", "2026-05-25") == "GDAXI_1d_2026-05-25"
    assert tmp_cache.make_key("EURUSD=X", "5m", "2026-05-25") == "EURUSD_X_5m_2026-05-25"
    key = tmp_cache.make_key("^GDAXI", "5m", "2026-05-25")
    assert "^" not in key and "=" not in key


def test_make_key_distinguishes_resolution(tmp_cache):
    # Daily vs. 5m for the same symbol/date must be different keys (no collision).
    daily = tmp_cache.make_key("^GDAXI", "1d", "2026-05-25")
    five_m = tmp_cache.make_key("^GDAXI", "5m", "2026-05-25")
    assert daily != five_m


# -- set / get roundtrip ------------------------------------------------------

def test_set_get_roundtrip(tmp_cache, frozen_clock):
    frozen_clock(_utc(2026, 5, 25, 12, 0))
    key = tmp_cache.make_key("^GDAXI", "5m", "2026-05-25")
    tmp_cache.set(key, SAMPLE, ttl_seconds=120)
    assert tmp_cache.get(key) == SAMPLE


def test_missing_key_returns_none(tmp_cache):
    assert tmp_cache.get("does_not_exist") is None


# -- TTL ----------------------------------------------------------------------

def test_ttl_fresh_is_hit(tmp_cache, frozen_clock):
    set_clock = frozen_clock
    base = _utc(2026, 5, 25, 12, 0)
    set_clock(base)
    key = "GDAXI_5m_2026-05-25"
    tmp_cache.set(key, SAMPLE, ttl_seconds=120)
    # 119 s later — still inside the 120 s TTL → hit.
    set_clock(base + timedelta(seconds=119))
    assert tmp_cache.get(key) == SAMPLE


def test_ttl_expired_returns_none(tmp_cache, frozen_clock):
    set_clock = frozen_clock
    base = _utc(2026, 5, 25, 12, 0)
    set_clock(base)
    key = "GDAXI_5m_2026-05-25"
    tmp_cache.set(key, SAMPLE, ttl_seconds=120)
    # 121 s later — past the TTL → miss.
    set_clock(base + timedelta(seconds=121))
    assert tmp_cache.get(key) is None


# -- corruption / self-heal ---------------------------------------------------

def test_corrupt_json_returns_none_and_self_heals(tmp_cache):
    key = "GDAXI_1d_2026-05-25"
    # Write garbage directly to the entry's file path.
    bad_path = tmp_cache.cache_dir / f"{key}.json"
    bad_path.write_text("{not valid json", encoding="utf-8")
    assert tmp_cache.get(key) is None
    # Self-heal: the corrupt file is removed so the next set is clean.
    assert not bad_path.exists()


def test_missing_expires_at_key_is_treated_as_corrupt(tmp_cache):
    key = "GDAXI_1d_2026-05-25"
    path = tmp_cache.cache_dir / f"{key}.json"
    # Valid JSON but missing the envelope contract → treated as miss + removed.
    path.write_text('{"data": []}', encoding="utf-8")
    assert tmp_cache.get(key) is None
    assert not path.exists()


# -- clear_expired ------------------------------------------------------------

def test_clear_expired_counts_and_removes(tmp_cache, frozen_clock):
    set_clock = frozen_clock
    base = _utc(2026, 5, 25, 12, 0)
    set_clock(base)
    tmp_cache.set("a_5m_2026-05-25", SAMPLE, ttl_seconds=120)   # will expire
    tmp_cache.set("b_5m_2026-05-25", SAMPLE, ttl_seconds=120)   # will expire
    tmp_cache.set("c_1d_2026-05-25", SAMPLE, ttl_seconds=86400)  # still fresh
    # A corrupt file should also be swept.
    (tmp_cache.cache_dir / "corrupt_1d_2026-05-25.json").write_text("garbage", encoding="utf-8")

    # Jump past the 5m TTL but inside the daily TTL.
    set_clock(base + timedelta(seconds=200))
    removed = tmp_cache.clear_expired()

    assert removed == 3  # two expired + one corrupt
    assert tmp_cache.get("c_1d_2026-05-25") == SAMPLE  # fresh one survived
    assert not (tmp_cache.cache_dir / "a_5m_2026-05-25.json").exists()
    assert not (tmp_cache.cache_dir / "corrupt_1d_2026-05-25.json").exists()


# -- directory creation & atomic write ---------------------------------------

def test_cache_dir_is_created(tmp_path):
    target = tmp_path / "nested" / "cache"
    assert not target.exists()
    FileCache(str(target))
    assert target.is_dir()


def test_set_is_atomic_no_tmp_left(tmp_cache, frozen_clock):
    frozen_clock(_utc(2026, 5, 25, 12, 0))
    key = "GDAXI_5m_2026-05-25"
    tmp_cache.set(key, SAMPLE, ttl_seconds=120)
    # The final file exists and no temp artefact is left behind.
    assert (tmp_cache.cache_dir / f"{key}.json").exists()
    assert list(tmp_cache.cache_dir.glob("*.tmp")) == []
