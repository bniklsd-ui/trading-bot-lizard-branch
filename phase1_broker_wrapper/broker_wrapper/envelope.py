"""Standard response envelope for every wrapper call.

Every BrokerAdapter method returns an Envelope. This gives callers
(tests, CLI, FastAPI, bot core) a single shape to consume.

Schema:
    {
        "ok":         bool,
        "ts":         "2026-05-14T13:42:11.123Z",  # ISO 8601 UTC
        "broker":     "ig",
        "method":     "get_price",
        "data":       <any> | null,
        "error":      {"code", "message", "retryable"} | null,
        "latency_ms": int
    }
"""

from __future__ import annotations

import json
import time
from dataclasses import dataclass, asdict, field
from datetime import datetime, timezone
from typing import Any


def _utc_iso_now() -> str:
    """ISO 8601 UTC timestamp with millisecond precision and Z suffix."""
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.") + \
        f"{datetime.now(timezone.utc).microsecond // 1000:03d}Z"


@dataclass
class Envelope:
    ok: bool
    ts: str
    broker: str
    method: str
    data: Any | None = None
    error: dict[str, Any] | None = None
    latency_ms: int = 0

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    def to_json(self, *, pretty: bool = False) -> str:
        if pretty:
            return json.dumps(self.to_dict(), indent=2, default=str)
        return json.dumps(self.to_dict(), default=str)

    def unwrap(self) -> Any:
        """Return data on success, raise on error. Use when you want
        to short-circuit error handling at a call site that knows it
        shouldn't fail."""
        if not self.ok:
            err = self.error or {}
            raise RuntimeError(
                f"{err.get('code', 'UNKNOWN')}: {err.get('message', 'no message')}"
            )
        return self.data


def ok_envelope(
    *,
    broker: str,
    method: str,
    data: Any,
    latency_ms: int,
) -> Envelope:
    return Envelope(
        ok=True,
        ts=_utc_iso_now(),
        broker=broker,
        method=method,
        data=data,
        error=None,
        latency_ms=latency_ms,
    )


def error_envelope(
    *,
    broker: str,
    method: str,
    code: str,
    message: str,
    retryable: bool,
    latency_ms: int,
    data: Any | None = None,
) -> Envelope:
    return Envelope(
        ok=False,
        ts=_utc_iso_now(),
        broker=broker,
        method=method,
        data=data,
        error={"code": code, "message": message, "retryable": retryable},
        latency_ms=latency_ms,
    )


class LatencyTimer:
    """Context manager to measure call latency in milliseconds.

    Usage:
        with LatencyTimer() as t:
            ...
        envelope.latency_ms = t.ms
    """

    def __init__(self) -> None:
        self._start: float = 0.0
        self.ms: int = 0

    def __enter__(self) -> "LatencyTimer":
        self._start = time.perf_counter()
        return self

    def __exit__(self, *exc: Any) -> None:
        self.ms = int((time.perf_counter() - self._start) * 1000)
