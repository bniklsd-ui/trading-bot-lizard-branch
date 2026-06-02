"""On-disk JSON cache with TTL for the external-data layer.

One responsibility: persist the small ``list[dict]`` payloads (serialised
OHLCV bars) that the fetcher pulls from yFinance, so repeated indicator
computations within a TTL window do not hit the network again.

Design (concept §9):

- One JSON file per key: ``<cache_dir>/<key>.json`` holding
  ``{"expires_at": "<ISO>", "data": [...]}``.
- TTL is encoded in the stored ``expires_at`` timestamp (absolute), compared
  against :func:`timeutil._utcnow` so tests can freeze the clock.
- Writes are atomic (temp file + :func:`os.replace`), exactly like Phase-2
  ``state.py`` — a crash mid-write never leaves a half-written file behind.
- Reads are crash-proof: a missing, expired, or corrupt file is treated as a
  cache miss (``get`` returns ``None``), so the fetcher simply re-fetches.
  Corrupt files self-heal (they are removed) so the next ``set`` is clean.

TTL policy itself (which resolution gets which TTL) lives in the fetcher, not
here — this module only stores whatever ``ttl_seconds`` it is handed.
"""

from __future__ import annotations

import json
import logging
import os
from datetime import timedelta
from pathlib import Path
from typing import Any

from . import timeutil

log = logging.getLogger(__name__)


def _format_iso(dt) -> str:
    """Format an aware datetime as ``"YYYY-MM-DDTHH:MM:SS.mmmZ"``.

    Mirrors :func:`timeutil.utc_iso_now` but for an arbitrary instant (we need
    to format a computed ``expires_at``, not just "now"). Kept identical so the
    cache's timestamps are comparable with the rest of the codebase.
    """
    return dt.strftime("%Y-%m-%dT%H:%M:%S.") + f"{dt.microsecond // 1000:03d}Z"


class FileCache:
    """TTL-aware JSON file cache keyed by ``symbol/resolution/date``."""

    def __init__(self, cache_dir: str) -> None:
        """Create ``cache_dir`` (and parents) if needed and remember it.

        Args:
            cache_dir: Directory for the cache files. Created with
                ``parents=True, exist_ok=True`` — same eager-mkdir pattern as
                Phase-2 ``StateManager``.
        """
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)

    # -- key derivation -----------------------------------------------------

    def make_key(self, symbol: str, resolution: str, date: str) -> str:
        """Build a deterministic, filesystem-safe cache key.

        The leading ``^`` of index symbols (``^GDAXI``) is stripped so the key
        is a clean filename; ``=`` (FX pairs like ``EURUSD=X``) is replaced
        too. The result is ``"{safe_symbol}_{resolution}_{date}"``.

        Args:
            symbol: yFinance symbol (e.g. ``"^GDAXI"``).
            resolution: Bar resolution (e.g. ``"1d"``, ``"5m"``).
            date: Date partition string (e.g. ``"2026-05-27"``).

        Returns:
            A deterministic key usable as a filename stem.
        """
        safe_symbol = symbol.lstrip("^").replace("=", "_")
        return f"{safe_symbol}_{resolution}_{date}"

    def _path(self, key: str) -> Path:
        return self.cache_dir / f"{key}.json"

    # -- read ---------------------------------------------------------------

    def get(self, key: str) -> list[dict[str, Any]] | None:
        """Return the cached payload for ``key`` or ``None``.

        Returns ``None`` on a cache miss, an expired entry, or a corrupt /
        unreadable file. Corrupt files are removed (self-heal) and logged at
        WARNING so a bad write never wedges the cache permanently.

        Args:
            key: Key produced by :meth:`make_key`.

        Returns:
            The stored ``list[dict]`` payload, or ``None``.
        """
        path = self._path(key)
        if not path.exists():
            return None
        try:
            envelope = json.loads(path.read_text(encoding="utf-8"))
            expires_at = timeutil.parse_iso(envelope["expires_at"])
            data = envelope["data"]
        except (json.JSONDecodeError, OSError, KeyError, ValueError) as exc:
            log.warning("cache entry %s unreadable (%s); treating as miss + removing", key, exc)
            self._safe_unlink(path)
            return None

        if timeutil._utcnow() >= expires_at:
            return None
        return data

    # -- write --------------------------------------------------------------

    def set(self, key: str, data: list[dict[str, Any]], ttl_seconds: int) -> None:
        """Atomically store ``data`` under ``key`` with a relative TTL.

        ``expires_at`` is computed as ``now + ttl_seconds`` (now via
        :func:`timeutil._utcnow`, so a frozen clock in tests is honoured).

        Args:
            key: Key produced by :meth:`make_key`.
            data: JSON-serialisable list of dicts (serialised bars).
            ttl_seconds: Lifetime in seconds from now.
        """
        expires_at = timeutil._utcnow() + timedelta(seconds=ttl_seconds)
        envelope = {"expires_at": _format_iso(expires_at), "data": data}
        path = self._path(key)
        tmp = path.with_suffix(path.suffix + ".tmp")
        tmp.write_text(json.dumps(envelope, indent=2, default=str), encoding="utf-8")
        os.replace(tmp, path)

    # -- maintenance --------------------------------------------------------

    def clear_expired(self) -> int:
        """Remove every expired or corrupt cache file.

        Returns:
            The number of files removed.
        """
        removed = 0
        now = timeutil._utcnow()
        for path in self.cache_dir.glob("*.json"):
            try:
                envelope = json.loads(path.read_text(encoding="utf-8"))
                expires_at = timeutil.parse_iso(envelope["expires_at"])
            except (json.JSONDecodeError, OSError, KeyError, ValueError):
                # Corrupt entry — remove it too (self-heal).
                if self._safe_unlink(path):
                    removed += 1
                continue
            if now >= expires_at:
                if self._safe_unlink(path):
                    removed += 1
        return removed

    @staticmethod
    def _safe_unlink(path: Path) -> bool:
        """Best-effort delete; never raises. Returns whether a file was removed."""
        try:
            path.unlink()
            return True
        except OSError:
            return False
