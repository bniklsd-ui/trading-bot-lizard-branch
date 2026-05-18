"""Tests for the response envelope."""

import json
import time

import pytest

from broker_wrapper.envelope import (
    Envelope, ok_envelope, error_envelope, LatencyTimer,
)


def test_ok_envelope_basic():
    env = ok_envelope(
        broker="ig", method="get_price",
        data={"bid": 100.0, "ask": 100.5}, latency_ms=42,
    )
    assert env.ok is True
    assert env.broker == "ig"
    assert env.method == "get_price"
    assert env.data == {"bid": 100.0, "ask": 100.5}
    assert env.error is None
    assert env.latency_ms == 42
    assert env.ts.endswith("Z")


def test_error_envelope_basic():
    env = error_envelope(
        broker="ig", method="get_price",
        code="MARKET_OFFLINE", message="closed",
        retryable=True, latency_ms=10,
    )
    assert env.ok is False
    assert env.error == {
        "code": "MARKET_OFFLINE",
        "message": "closed",
        "retryable": True,
    }


def test_envelope_json_round_trip():
    env = ok_envelope(broker="ig", method="x", data={"a": 1}, latency_ms=1)
    parsed = json.loads(env.to_json())
    assert parsed["ok"] is True
    assert parsed["data"]["a"] == 1
    assert "ts" in parsed
    assert "broker" in parsed
    assert "method" in parsed
    assert "latency_ms" in parsed


def test_envelope_pretty_json_has_newlines():
    env = ok_envelope(broker="ig", method="x", data={}, latency_ms=0)
    assert "\n" in env.to_json(pretty=True)


def test_unwrap_returns_data_on_success():
    env = ok_envelope(broker="ig", method="x", data=42, latency_ms=0)
    assert env.unwrap() == 42


def test_unwrap_raises_on_error():
    env = error_envelope(
        broker="ig", method="x",
        code="E", message="boom", retryable=False, latency_ms=0,
    )
    with pytest.raises(RuntimeError, match="boom"):
        env.unwrap()


def test_latency_timer_measures():
    with LatencyTimer() as t:
        time.sleep(0.01)
    assert t.ms >= 8  # allow a little slack for sleep precision
