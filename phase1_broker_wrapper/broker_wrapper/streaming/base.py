"""Streaming layer — abstraction over real-time price feeds.

Modularity design:
    StreamClient is the abstract base.
    PollingStreamClient is a working fallback that REST-polls.
    IGLightstreamerClient (separate file) is the production target.

The bot's higher layers only ever see `StreamClient.subscribe()` and
a callback. Switching from polling to Lightstreamer is a one-line
factory change, no consumer code touched.
"""

from __future__ import annotations

import threading
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Callable

from broker_wrapper.adapters.base import BrokerAdapter


@dataclass
class PriceTick:
    epic: str
    bid: float
    ask: float
    timestamp: str  # ISO 8601 UTC


PriceCallback = Callable[[PriceTick], None]


class StreamClient(ABC):
    """Abstract real-time price feed."""

    @abstractmethod
    def start(self) -> None:
        """Open the feed. No-op if already started."""

    @abstractmethod
    def stop(self) -> None:
        """Close the feed cleanly. No-op if not started."""

    @abstractmethod
    def subscribe(self, epic: str, callback: PriceCallback) -> None:
        """Subscribe a callback to price ticks for an epic."""

    @abstractmethod
    def unsubscribe(self, epic: str) -> None:
        """Stop sending ticks for an epic."""

    @property
    @abstractmethod
    def is_running(self) -> bool: ...


class PollingStreamClient(StreamClient):
    """Polls the REST adapter on an interval. Functional fallback for
    when Lightstreamer is not set up. Not production-grade for tight
    intraday loops — use the Lightstreamer client in production.
    """

    def __init__(self, adapter: BrokerAdapter, *, interval_s: float = 1.0) -> None:
        self._adapter = adapter
        self._interval = interval_s
        self._subscriptions: dict[str, PriceCallback] = {}
        self._lock = threading.Lock()
        self._thread: threading.Thread | None = None
        self._stop_event = threading.Event()

    def start(self) -> None:
        if self._thread and self._thread.is_alive():
            return
        self._stop_event.clear()
        self._thread = threading.Thread(target=self._loop, daemon=True)
        self._thread.start()

    def stop(self) -> None:
        self._stop_event.set()
        if self._thread:
            self._thread.join(timeout=self._interval * 2)
        self._thread = None

    def subscribe(self, epic: str, callback: PriceCallback) -> None:
        with self._lock:
            self._subscriptions[epic] = callback

    def unsubscribe(self, epic: str) -> None:
        with self._lock:
            self._subscriptions.pop(epic, None)

    @property
    def is_running(self) -> bool:
        return self._thread is not None and self._thread.is_alive()

    def _loop(self) -> None:
        while not self._stop_event.is_set():
            with self._lock:
                items = list(self._subscriptions.items())
            for epic, cb in items:
                env = self._adapter.get_price(epic)
                if env.ok:
                    d = env.data
                    try:
                        cb(PriceTick(
                            epic=epic,
                            bid=d["bid"], ask=d["ask"],
                            timestamp=d["timestamp"],
                        ))
                    except Exception:
                        # Never let a bad callback kill the loop.
                        pass
            self._stop_event.wait(self._interval)
