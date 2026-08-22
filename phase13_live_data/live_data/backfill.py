"""Phase 13 §6 C1 — S3 ExternalBackfill (Pfad B: Capital.com, PARTIAL).

Hybrid-Entscheidung 2026-08-19 (Session 11): B-first (Capital.com),
C-fallback (Dukascopy). Probe-Ergebnis 2026-08-19: Capital.com
liefert MINUTE-Bars für **2 von 3** Ziel-Indizes — Germany 40 (DE40)
und France 40 (FR40) liefern 59 Bars pro 1-h-Fenster, Spain 35
(SP35) gibt HTTP 404 ``error.prices.not-found``. **PARTIAL**-Pfad
aktiv: dieser Backfill füllt die zwei funktionierenden Indizes aus
Capital.com, Spain 35 fällt auf den Dukascopy-Backfill (Pfad C,
deferred zu einer Folge-Session).

Lückengetrieben, nicht zeitgetrieben (Plan §6 C1): Operator-Script
findet Lücken im Archiv, ruft :meth:`CapitalSource.fetch_window`
für die fehlenden Spannen, schreibt mit ``source='capital'`` ins
Archiv.

Vier quellenunabhängige Regeln aus Plan §6 C1.0 sind implementiert:

1. **Antwortfenster nach dem Fetch prüfen.** Jeder zurückgegebene
   ``snapshotTime`` muss innerhalb ``[start_utc - 1min, end_utc + 1min]``
   liegen — sonst verwerfen + Warn-Log. Empirisch motiviert:
   mindestens eine untersuchte API beantwortet ein Fenster jenseits
   ihrer Historientiefe mit aktuellen Bars.
2. **Keine synthetischen Bars übernehmen.** ``O == H == L == C``
   (und Volume 0) ⇒ Skip (Off-Hours-Auffüll-Bars).
3. **Vergleiche nie über absolute Niveaus.** Sampler-Konzern (A6.0),
   nicht Backfill.
4. **Backoff ist Pflicht.** HTTP 429/503 ⇒ exponentielles Backoff
   (Basis 2 s, max 3 Retries) vor Re-Request.

Quellen-spezifische Erkenntnisse (empirisch, Session 11):

- Demo-Account hat **eigene API-Keys** (Capital.com-Doku FAQ §8.5).
  Ein LIVE-Key authentifiziert sich NICHT gegen die DEMO-URL.
- Auth: ``POST /api/v1/session`` mit Header ``X-CAP-API-KEY: <key>`` +
  Body ``{identifier, password, encryptedPassword: false}``. Der
  ``password`` ist der **API-Key-Custom-Password** (FAQ §8.8.7), NICHT
  das Account-Login-Passwort.
- Datumsformat ``from``/``to``: ``YYYY-MM-DDTHH:MM:SS`` (kein ``Z``,
  keine Millisekunden). Server-Parser ist strikt.
- Returnierte ``snapshotTime`` ohne TZ-Marker. Empirischer Offset zur
  UTC-Anfrage: **+2 h im Sommer** (CEST/UTC+2). ``CAPITAL_TZ`` unten
  ist ``Europe/Madrid`` (UTC+2 Sommer / +1 Winter), DST-aware via
  ``zoneinfo``.
- Epic-Mapping: ``IX.D.DAX.IFMM.IP`` → ``DE40``, ``IX.D.CAC.IFE.IP``
  → ``FR40``. ``IX.D.IBEX.FWM2.IP`` (Spain 35) → nicht in ``SUPPORTED_EPICS``,
  fällt auf Path C.

Langlebigkeit: ``KNOWN_SOURCES`` (``data_foundation/models.py:22``)
muss ``'capital'`` enthalten, sonst weigert sich ``BarArchive.insert_bars``
die Zeilen aufzunehmen. ``BarArchive.window``'s ``prefer``-Default
muss ``'capital'`` enthalten (Position: zwischen ``'ig'`` und
``'ls'``, weil die Broker-CFD-Reihe näher an IG liegt als der
yF-Kassaindex).
"""

from __future__ import annotations

import logging
import time
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Any, Sequence
from zoneinfo import ZoneInfo

import requests
from source_registry.models import (
    SOURCE_CAPITAL,
    STATUS_NO_SOURCE,
    STATUS_OK,
    SourceAvailability,
    SourceProfile,
)

logger = logging.getLogger("live_data.backfill")

# Capital.com demo accounts return timestamps in their own TZ
# (no explicit TZ marker on the wire). Empirically (2026-08-19): the
# offset from our UTC request to the response is +2 h in summer —
# consistent with CEST (UTC+2). Europe/Madrid picks up the same DST
# rules as the rest of Western/Central Europe; if the account zone
# differs, override CAPITAL_TZ here once per account.
CAPITAL_TZ = ZoneInfo("Europe/Madrid")

REQUEST_TIMEOUT_SEC = 30
MAX_RETRIES = 3
BACKOFF_BASE_SEC = 2.0

# Map our internal IG-style epics to Capital.com's short epic codes
# (per the probe result 2026-08-19). Spain 35 = IBEX is intentionally
# absent — falls back to Dukascopy (Path C, deferred).
EPIC_MAP: dict[str, str] = {
    "IX.D.DAX.IFMM.IP": "DE40",   # Germany 40
    "IX.D.CAC.IFE.IP":  "FR40",   # France 40
}

# Phase-14 B1b (2026-08-22): each Capital.com ``/markets?searchTerm=…``
# call needs the *human-readable* index name. The B1a operator probe
# observed what each IG epic maps to — see
# ``phase14_discovery/PHASE14_B1A_PROBE_OUTPUT_2026-08-22.md`` §5.
# Today this is the same three pairs that ``EPIC_MAP`` covers; B2 will
# replace ``EPIC_MAP`` with a runtime DB lookup (``SourceAvailabilityStore
# .symbol_for``) but the search-term dict remains here — the source
# itself opens no DB (Plan §5.2).
_DISPLAY_NAME_BY_EPIC: dict[str, str] = {
    "IX.D.DAX.IFMM.IP":  "Germany 40",
    "IX.D.CAC.IFE.IP":   "France 40",
    "IX.D.IBEX.FWM2.IP": "Spain 35",
}

SOURCE_TAG = "capital"


def _utc_iso_now() -> str:
    """Current UTC time as an ISO 8601 string with ms precision and Z suffix.

    Mirrors the formatter used by ``phase9_universe/universe/store.py::utc_iso_now``
    and ``phase14_discovery/source_registry/store.py::utc_iso_now`` (duplicated
    for phase isolation, not imported — keeps ``live_data.backfill`` importable
    without dragging in P9/P14). Used by :meth:`CapitalSource.discover` to stamp
    ``last_verified_utc`` on every emitted ``SourceAvailability`` row.
    """
    now = datetime.now(timezone.utc)
    return now.strftime("%Y-%m-%dT%H:%M:%S.") + f"{now.microsecond // 1000:03d}Z"


@dataclass(frozen=True)
class PriceBar:
    """One normalized OHLC bar in UTC, ready for archive insertion."""

    epic: str
    ts_utc: datetime
    open: float
    high: float
    low: float
    close: float
    volume: float | None = None


class CapitalSource:
    """S3 partial: 1-min OHLC bars from Capital.com for the indices
    that DO work. See module docstring for the PARTIAL/C-fallback
    semantics.
    """

    def __init__(
        self,
        identifier: str,
        custom_password: str,
        api_key: str,
        base_url: str = "https://demo-api-capital.backend-capital.com",
    ) -> None:
        self._identifier = identifier
        self._custom_password = custom_password
        self._api_key = api_key
        self._base_url = base_url
        self._cst: str | None = None
        self._security_token: str | None = None

    # -- lifecycle ----------------------------------------------------------

    def authenticate(self) -> None:
        """POST /api/v1/session. Idempotent within the 10-min token window."""
        resp = requests.post(
            f"{self._base_url}/api/v1/session",
            json={
                "identifier": self._identifier,
                "password": self._custom_password,
                "encryptedPassword": False,
            },
            headers={
                "X-CAP-API-KEY": self._api_key,
                "Content-Type": "application/json",
            },
            timeout=REQUEST_TIMEOUT_SEC,
        )
        if resp.status_code != 200:
            raise RuntimeError(
                f"Capital.com auth failed: HTTP {resp.status_code}: "
                f"{(resp.text or '')[:300]}"
            )
        self._cst = resp.headers.get("CST", "")
        self._security_token = resp.headers.get("X-SECURITY-TOKEN", "")
        if not self._cst or not self._security_token:
            raise RuntimeError(
                "Capital.com auth response missing CST/X-SECURITY-TOKEN headers"
            )

    @property
    def _session_headers(self) -> dict[str, str]:
        if not self._cst or not self._security_token:
            raise RuntimeError("not authenticated — call authenticate() first")
        return {
            "CST": self._cst,
            "X-SECURITY-TOKEN": self._security_token,
            "Content-Type": "application/json",
        }

    # -- fetch --------------------------------------------------------------

    def fetch_window(
        self,
        epic: str,
        start_utc: datetime,
        end_utc: datetime,
        resolution: str = "MINUTE",
    ) -> list[PriceBar]:
        """Fetch bars for ``epic`` between ``[start_utc, end_utc)``.

        Returns an empty list (not an error) for epics not in
        :data:`EPIC_MAP` — the script-level gap-fill will then fall
        back to Path C (Dukascopy) for those.
        """
        capital_epic = EPIC_MAP.get(epic)
        if capital_epic is None:
            logger.warning(
                f"CapitalSource: epic {epic!r} not in EPIC_MAP — "
                f"caller should fall back to path C (Dukascopy)"
            )
            return []

        if self._cst is None:
            self.authenticate()

        # Capital.com's documented date format: 'YYYY-MM-DDTHH:MM:SS',
        # NO 'Z' suffix, NO milliseconds (validated empirically — see
        # commit history of probe_capital.py for the exact error codes
        # encountered).
        from_str = start_utc.strftime("%Y-%m-%dT%H:%M:%S")
        to_str = end_utc.strftime("%Y-%m-%dT%H:%M:%S")
        url = f"{self._base_url}/api/v1/prices/{capital_epic}"
        params = {"resolution": resolution, "from": from_str, "to": to_str, "max": 1000}

        last_error: str | None = None
        for attempt in range(MAX_RETRIES):
            try:
                resp = requests.get(
                    url, params=params, headers=self._session_headers,
                    timeout=REQUEST_TIMEOUT_SEC,
                )
            except requests.RequestException as exc:
                last_error = f"network: {exc}"
                self._backoff(attempt, last_error)
                continue

            if resp.status_code == 200:
                return self._parse_and_validate(resp, start_utc, end_utc)
            if resp.status_code in (429, 503):
                last_error = f"HTTP {resp.status_code}"
                self._backoff(attempt, last_error)
                continue
            # Non-retriable: 400/401/404/etc. — surface immediately so
            # the script can decide (e.g. fall back to path C for 404).
            raise RuntimeError(
                f"Capital.com fetch {capital_epic}: HTTP {resp.status_code}: "
                f"{(resp.text or '')[:300]}"
            )

        raise RuntimeError(
            f"Capital.com fetch {capital_epic}: exhausted {MAX_RETRIES} retries; "
            f"last error: {last_error}"
        )

    # -- discover -----------------------------------------------------------

    def discover(
        self,
        epics: Sequence[str],
        *,
        max_probe_calls: int = 8,
    ) -> SourceProfile:
        """Phase-14 B1b. Discover what Capital.com can serve for ``epics``.

        For each ``epic`` known to :data:`_DISPLAY_NAME_BY_EPIC` the method
        issues exactly ONE HTTP GET against ``/api/v1/markets?searchTerm=<name>``,
        filters the response to the first entry with ``instrumentName == name``
        AND ``instrumentType == "INDICES"`` (Phase-14 B1a Befund 3, observed
        2026-08-22 — Capital.com's CFD index entries carry ``"INDICES"``, not
        ``"CFD"``), and emits one :class:`SourceAvailability` per epic:

        - **Hit**: ``status='ok'``, ``source_symbol = match["epic"]`` (the
          ``"DE40"`` / ``"FR40"`` / ``"SP35"`` short code), ``origin='discovery'``,
          ``history_min_days=30``, ``latency_min=0`` (B1a Befund 6: ``delayTime: 0``
          for all three).
        - **Miss**: ``status='no_source'``, ``source_symbol=None``, ``notes`` carries
          the searchTerm we tried.

        Epics unknown to :data:`_DISPLAY_NAME_BY_EPIC` emit
        ``status='no_source'`` WITHOUT an HTTP call (the integration of additional
        indices is a configuration step, not a runtime guess — Plan §6 B1 / D6).

        Fail-soft per Plan §8.5: network / parse / non-200 errors are appended to
        ``SourceProfile.errors`` and the iteration continues — one bad row does
        not poison the cycle. ``max_probe_calls`` is the hard deckel (Plan D14);
        once exhausted, remaining epics emit ``status='no_source'`` with the
        note ``"max_probe_calls=N reached"``. The auth POST is a one-off warm-up
        and is NOT counted against ``max_probe_calls`` — only ``/markets`` GETs
        are. The daemon (Phase-14 C2) wraps the returned ``probe_calls_used``
        in ``SourceBudget.record_spend(points, kind='discovery')`` (Plan D13).
        """
        rows: list[SourceAvailability] = []
        errors: list[str] = []
        calls_used = 0

        # Auth warm-up — one-off; not counted against max_probe_calls. A failure
        # here aborts the whole discovery cycle loudly (errors carry the cause).
        if self._cst is None:
            try:
                self.authenticate()
            except Exception as exc:  # noqa: BLE001 — fail-soft per Plan §8.5
                return SourceProfile(
                    source=SOURCE_CAPITAL,
                    rows=(),
                    probe_calls_used=0,
                    errors=(f"auth: {exc}",),
                )

        now = _utc_iso_now()
        for epic in epics:
            name = _DISPLAY_NAME_BY_EPIC.get(epic)
            if name is None:
                rows.append(SourceAvailability(
                    epic=epic, source=SOURCE_CAPITAL, resolution="1m",
                    source_symbol=None,
                    status=STATUS_NO_SOURCE,
                    origin="discovery",
                    history_min_days=None, latency_min=None,
                    last_verified_utc=now,
                    notes=f"no display name registered for epic {epic!r}",
                ))
                continue

            if calls_used >= max_probe_calls:
                rows.append(SourceAvailability(
                    epic=epic, source=SOURCE_CAPITAL, resolution="1m",
                    source_symbol=None,
                    status=STATUS_NO_SOURCE,
                    origin="discovery",
                    history_min_days=None, latency_min=None,
                    last_verified_utc=now,
                    notes=f"max_probe_calls={max_probe_calls} reached",
                ))
                continue

            url = f"{self._base_url}/api/v1/markets"
            params = {"searchTerm": name}
            try:
                resp = requests.get(
                    url, params=params, headers=self._session_headers,
                    timeout=REQUEST_TIMEOUT_SEC,
                )
                calls_used += 1
            except requests.RequestException as exc:
                errors.append(f"{epic}: network: {exc}")
                continue

            if resp.status_code != 200:
                errors.append(f"{epic}: http_{resp.status_code}")
                continue

            try:
                body = resp.json()
            except ValueError as exc:
                errors.append(f"{epic}: parse: {exc}")
                continue

            markets = (body or {}).get("markets") or []
            match = self._pick_markets_match(markets, name)
            if match is None:
                rows.append(SourceAvailability(
                    epic=epic, source=SOURCE_CAPITAL, resolution="1m",
                    source_symbol=None,
                    status=STATUS_NO_SOURCE,
                    origin="discovery",
                    history_min_days=None, latency_min=None,
                    last_verified_utc=now,
                    notes=f"no INDICES match for searchTerm={name!r}",
                ))
                continue

            rows.append(SourceAvailability(
                epic=epic, source=SOURCE_CAPITAL, resolution="1m",
                source_symbol=match.get("epic") or None,
                status=STATUS_OK,
                origin="discovery",
                history_min_days=30, latency_min=0,
                last_verified_utc=now,
                notes=None,
            ))

        return SourceProfile(
            source=SOURCE_CAPITAL,
            rows=tuple(rows),
            probe_calls_used=calls_used,
            errors=tuple(errors),
        )

    # -- internals ----------------------------------------------------------

    def _backoff(self, attempt: int, reason: str) -> None:
        delay = BACKOFF_BASE_SEC ** attempt
        logger.warning(
            f"CapitalSource: backoff {delay:.1f}s before retry "
            f"(attempt {attempt + 1}/{MAX_RETRIES}, reason: {reason})"
        )
        time.sleep(delay)

    def _parse_and_validate(
        self,
        resp: requests.Response,
        start_utc: datetime,
        end_utc: datetime,
    ) -> list[PriceBar]:
        try:
            body = resp.json()
        except ValueError as exc:
            raise RuntimeError(f"Capital.com fetch: invalid JSON: {exc}")

        # Defensive shape: try common field-name conventions. The exact
        # shape depends on Capital.com's REST /prices/{epic} response,
        # which the official Swagger documents but we couldn't inspect
        # during this session (only the WebSocket example was fetched).
        raw_prices = body.get("prices") or body.get("data") or []
        if not raw_prices:
            logger.warning(
                f"Capital.com fetch: empty 'prices'/'data' array. "
                f"Response keys: {list(body.keys())}"
            )
            return []

        out: list[PriceBar] = []
        window_loose = timedelta(minutes=1)  # 1-min TZ tolerance per Rule 1
        rejected_out_of_window = 0
        rejected_synthetic = 0
        rejected_malformed = 0

        for raw in raw_prices:
            ts_str = raw.get("snapshotTime") or raw.get("t") or raw.get("time")
            if not ts_str:
                rejected_malformed += 1
                continue

            ts_utc = self._parse_snapshot(ts_str)
            if ts_utc is None:
                rejected_malformed += 1
                continue

            # Rule 1: window check
            if ts_utc < start_utc - window_loose or ts_utc > end_utc + window_loose:
                logger.warning(
                    f"CapitalSource: bar {ts_str} (={ts_utc.isoformat()}) "
                    f"outside requested window "
                    f"[{start_utc.isoformat()}, {end_utc.isoformat()}] — skip"
                )
                rejected_out_of_window += 1
                continue

            ohlc = self._extract_ohlc(raw)
            if ohlc is None:
                rejected_malformed += 1
                continue
            o, h, l, c = ohlc

            vol = raw.get("volume") or raw.get("vol")

            # Rule 2: synthetic off-hours bars (O==H==L==C + no volume)
            if o == h == l == c and vol in (0, 0.0, None):
                rejected_synthetic += 1
                continue

            out.append(PriceBar(
                epic=raw.get("epic") or raw.get("instrumentName") or "",
                ts_utc=ts_utc,
                open=o, high=h, low=l, close=c,
                volume=vol if isinstance(vol, (int, float)) else None,
            ))

        logger.info(
            f"CapitalSource: parsed {len(out)}/{len(raw_prices)} bars "
            f"in window (rejected: {rejected_out_of_window} out-of-window, "
            f"{rejected_synthetic} synthetic, {rejected_malformed} malformed)"
        )
        return out

    @staticmethod
    def _parse_snapshot(ts_str: str) -> datetime | None:
        """Parse a Capital.com ``snapshotTime`` to UTC.

        Empirically, returned timestamps have **no TZ marker** but
        the server's local time is ``Europe/Madrid`` (UTC+2 in summer,
        UTC+1 in winter). We attach that TZ then convert to UTC.
        """
        if not ts_str:
            return None
        # Try the documented format first, fall back to fromisoformat.
        try:
            local_dt = datetime.strptime(ts_str, "%Y-%m-%dT%H:%M:%S")
        except ValueError:
            try:
                local_dt = datetime.fromisoformat(ts_str)
            except ValueError:
                return None
        if local_dt.tzinfo is not None:
            return local_dt.astimezone(timezone.utc)
        return local_dt.replace(tzinfo=CAPITAL_TZ).astimezone(timezone.utc)

    @staticmethod
    def _extract_ohlc(raw: dict) -> tuple[float, float, float, float] | None:
        """Defensive OHLC extraction — Capital.com's exact REST field
        shape is not in the doc pages we fetched (only WebSocket
        ``ohlc.event`` was), so we try the common variants.
        """
        candidates = {
            "open":  ["openPrice", "open", "o", "openMid"],
            "high":  ["highPrice", "high", "h", "highMid"],
            "low":   ["lowPrice",  "low",  "l", "lowMid"],
            "close": ["closePrice","close","c", "closeMid"],
        }
        result: dict[str, float] = {}
        for canon, opts in candidates.items():
            for opt in opts:
                val = raw.get(opt)
                if isinstance(val, (int, float)):
                    result[canon] = float(val)
                    break
                if isinstance(val, dict):
                    bid = val.get("bid")
                    ask = val.get("ask")
                    if isinstance(bid, (int, float)) and isinstance(ask, (int, float)):
                        result[canon] = (float(bid) + float(ask)) / 2.0
                        break
            else:
                return None  # this OHLC field not found in any variant
        return (result["open"], result["high"], result["low"], result["close"])

    @staticmethod
    def _pick_markets_match(markets: list[dict], index_name: str) -> dict | None:
        """Pick the first market whose ``instrumentName == index_name`` AND
        whose ``instrumentType == "INDICES"`` — the strict filter against
        Capital.com's observed response form (Phase-14 B1a Befund 3,
        2026-08-22).

        Strict by design: ``CapitalSource.discover`` writes into the
        ``instrument_source_availability`` table, where ``status='ok'``
        means "Capital.com has a CFD index bar stream under this symbol".
        Anything outside ``INDICES`` (SHARES / COMMODITIES / …) is a wrong
        answer that must NOT propagate — that would mislead
        ``run_capital_backfill`` into fetching from a market we cannot
        actually backfill. The fallback to non-INDICES entries that
        ``scripts.probe_capital._pick_index_match`` uses is intentionally
        NOT carried over: the probe is operator tooling (forward-compat
        loses nothing if a future type rename mis-routes), the discover
        path is contract-binding.

        Returns ``None`` when no INDICES entry exists for ``index_name`` —
        the caller emits ``status='no_source'`` with the searchTerm in
        ``notes``.
        """
        for m in markets:
            if m.get("instrumentName") == index_name \
                    and (m.get("instrumentType") or "").upper() == "INDICES":
                return m
        return None


def run_capital_backfill(
    source: CapitalSource,
    archive: Any,
    epics: list[str],
    start_utc: datetime,
    end_utc: datetime,
) -> dict[str, int]:
    """Fetch Capital.com bars and write them to the archive.

    Returns ``{epic: bars_written}`` where the count is the number of
    **genuinely new rows** that ``BarArchive.insert_bars`` actually wrote
    (returns the ``cur.rowcount`` over ``INSERT OR IGNORE`` — duplicates
    are NOT counted; re-running on the same window returns 0 per epic).
    Epics not in :data:`EPIC_MAP` return 0 (script-level fallback to
    path C is the caller's job).
    """
    # Lazy import to keep this module importable in tests that mock
    # ``data_foundation.models``.
    from data_foundation.models import Bar

    results: dict[str, int] = {}
    for epic in epics:
        try:
            bars = source.fetch_window(epic, start_utc, end_utc)
        except RuntimeError as exc:
            logger.error(f"CapitalSource: fetch failed for {epic}: {exc}")
            results[epic] = 0
            continue

        if not bars:
            results[epic] = 0
            continue

        written = 0
        now_iso = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.000Z")
        for bar in bars:
            archive_bar = Bar(
                epic=epic,
                resolution="1m",
                ts_utc=bar.ts_utc.strftime("%Y-%m-%dT%H:%M:%S.000Z"),
                open=bar.open,
                high=bar.high,
                low=bar.low,
                close=bar.close,
                volume=bar.volume,
                source=SOURCE_TAG,
                fetched_at=now_iso,
                tick_count=None,  # Capital.com REST prices don't carry it
            )
            try:
                # insert_bars returns the number of *genuinely new* rows
                # (cur.rowcount over INSERT OR IGNORE). Duplicates don't
                # count; that's what the script-level "bars_written" metric
                # is supposed to mean (Phase-14 finding B5).
                written += archive.insert_bars([archive_bar])
            except Exception as exc:  # noqa: BLE001 — fail-soft per Plan §6 C1.0
                logger.warning(
                    f"CapitalSource: insert_bars failed for {epic} "
                    f"@ {bar.ts_utc.isoformat()}: {exc}"
                )
        results[epic] = written
    return results
