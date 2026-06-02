# Phase 3 — External Data (yFinance): Claude-Code-Implementierungsplan

> **Für Claude Code.** Dieser Plan ist die Umsetzungsanleitung zum Konzept
> `docs/concepts/phase3_external_konzept.md`. Wo Plan und Konzept sich
> unterscheiden, **gilt dieser Plan** — er enthält Korrekturen aus der
> yFinance-Recherche (Stand 2026-05) und drei in der Konzept-Session
> getroffene Entscheidungen.
>
> **Bauprinzip (Top-CLAUDE.md):** Phase 3 ist 100 % Code, kein LLM-Call.
> yFinance liefert Rohwerte, Code rechnet Indikatoren, kein Indikator
> entscheidet. So wenig AI wie möglich, so viel AI wie nötig.

---

## 0. Vorab gelöste Punkte (nicht neu diskutieren)

Diese vier Punkte waren im Konzept offen. Sie sind **entschieden** — Claude
Code setzt sie um, ohne sie erneut aufzuwerfen:

| # | Thema | Entscheidung |
|---|---|---|
| 1 | `^GDAXI` Volume | **Graceful degrade + optionaler ETF-Proxy-Hook.** Ohne Proxy: `volume_available=False`, `z_score=0.0`, `is_anomaly=False`. `TickerMapper` kann pro Epic ein separates Volume-Symbol halten. |
| 2 | Momentum-Auflösung | **5m-Bars.** Stabil, niedriges 429-Risiko. Kein 1m. |
| 3 | Off-Hours-Verhalten | **Intraday → `None` + Marker; Daily/History immer erlaubt.** Kein stilles Servieren veralteter Intraday-Werte. |
| 4 | Cache-Pfad | **Kein `DataPaths`-Objekt.** `FileCache(cache_dir: str)`, Default `<repo_root>/data/cache/`, berechnet im Entrypoint — exakt wie Phase 2 `init_db.py`. |

---

## 1. Fünf Korrekturen am Konzept (zwingend umsetzen)

Das Konzept beschreibt yFinance-Verhalten, das seit den 2025er-Änderungen
überholt ist. Diese fünf Punkte überschreiben das Konzept:

1. **Keine eigene `requests.Session` an yFinance übergeben.** yFinance ≥ 0.2.6x
   nutzt intern `curl_cffi` mit Browser-Impersonation und wirft eine
   `YFDataException`, wenn man eine normale `requests.Session` reicht. Wir
   übergeben **nichts** — yFinance handhabt Session/Cookies/Crumb selbst.
   → Die Konzept-Idee „eigene Session / User-Agent" entfällt ersatzlos.

2. **Rate-Limit ist typisiert, nicht nur leeres DataFrame.** yFinance wirft
   seit 2025 `yfinance.exceptions.YFRateLimitError` ("Too Many Requests").
   Der Fetcher fängt **beide** Fehlermodi:
   - `YFRateLimitError` → backoff + retry → bei Erschöpfung eigene `RateLimitError`
   - leeres / zu kurzes DataFrame (Feiertag, Off-Hours, stiller Fehler) →
     backoff + retry → bei Erschöpfung eigene `DataUnavailableError`

3. **Dep-Pin anheben.** `requirements.txt`: `yfinance>=0.2.65,<0.3`
   (aktuell 0.2.66). `curl_cffi` kommt transitiv mit — auf manchen Systemen
   braucht es eine Build-Toolchain; im `README.md` als Install-Hinweis vermerken.

4. **Kein `freezegun`.** Für TTL-/Zeit-Tests wird — wie in Phase 2 `state.py` —
   eine monkeypatchbare `_utcnow()`-Indirektion genutzt. Null Extra-Dep,
   konsistent mit dem Repo.

5. **Marktzeiten = `Europe/Berlin` (DST-aware), nicht fix „CET".** XETRA läuft
   im Sommer auf CEST. Zeitzonen-Logik über `zoneinfo.ZoneInfo("Europe/Berlin")`
   (stdlib ab Python 3.9), kein fester Offset.

---

## 2. Repo-Kontext & Konventionen (aus Top-`CLAUDE.md`)

**Was existiert:** Phase 1 (`phase1_broker_wrapper/`, ✅ live) und Phase 2
(`phase2_persistence/`, ✅ live, 59 Tests). Phase 3 ist ein **neues,
eigenständiges Verzeichnis** `phase3_external_data/` und importiert **nichts**
aus Phase 1 oder 2 (Phasen-Isolation, standalone testbar).

**Verbindliche Konventionen:**
- `from __future__ import annotations`, Type-Hints überall, Docstrings auf jeder
  öffentlichen Funktion/Klasse (Zweck, Args, Raises).
- Eine Datei = eine Verantwortung. Module nicht aufblähen.
- Eigene, typisierte Exception-Hierarchie in `exceptions.py` (Pattern wie
  Phase 1: Basisklasse mit `code`-Klassenattribut, optional `retryable`).
- Exceptions **nie still schlucken** — entweder loggen + raisen, oder loggen +
  definiertes `None`/Fehlerobjekt zurückgeben.
- **Logging:** stdlib `logging`, **immer nach stderr**, nie stdout. (stdout
  bleibt für maschinenlesbare Ausgabe reserviert — relevant im `smoke_test.py`.)
- `pytest`, **gemockt, keine Netzwerk-Calls in Unit-Tests.**
- Eigenes `external_data/timeutil.py` (dupliziert, identisches ISO-Format wie
  Phase 1/2 — `"2026-05-21T09:34:11.123Z"`), damit Timestamps phasenübergreifend
  vergleichbar sind, ohne Cross-Import.

**Pfad-Muster (von Phase 2 `init_db.py` übernommen):**
```python
_PACKAGE_ROOT = Path(__file__).resolve().parent.parent   # phase3_external_data/
_REPO_ROOT    = _PACKAGE_ROOT.parent                      # <repo_root>
_DEFAULT_CACHE_DIR = _REPO_ROOT / "data" / "cache"
```
`data/cache/` ist über `.gitignore` ausgeschlossen (Runtime-Artefakt).

> **Angepasst 2026-06-02 (Step 5 / Cache):** Diese Annahme stimmte ursprünglich
> *nicht* — die Root-`.gitignore` deckte nur `*.sqlite` und die benannten
> State-JSONs ab, **nicht** `data/cache/*.json`. Beim Bau von `cache.py` wurde
> eine explizite Regel `data/cache/` in der Root-`.gitignore` ergänzt; damit
> trifft die obige Aussage jetzt zu (Mismatch Konzept↔Code bereinigt).

---

## 3. Modul-Struktur (Soll)

```
phase3_external_data/
├── README.md
├── CLAUDE.md
├── requirements.txt
├── external_data/
│   ├── __init__.py          # exports: MarketDataFetcher, TickerMapper, FileCache
│   ├── exceptions.py        # ExternalDataError-Hierarchie
│   ├── models.py            # Dataclasses (Contracts) — siehe §4
│   ├── timeutil.py          # utc_iso_now(), parse_iso() — dupliziert
│   ├── market_hours.py      # is_market_open(now) für Europe/Berlin
│   ├── ticker_map.py        # TickerMapper (epic→yf, epic→volume-yf)
│   ├── cache.py             # FileCache (JSON, TTL-aware)
│   ├── indicators.py        # reine Funktionen: Drift/Momentum/Volume/HighLow
│   └── fetcher.py           # MarketDataFetcher + RateLimiter + Retry + _raw_download
├── scripts/
│   └── smoke_test.py        # Live-Test gegen ^GDAXI (nur Marktzeiten)
└── tests/
    ├── conftest.py          # Fixtures: FileCache in tmp_path, Sample-DataFrames, fake clock
    ├── test_ticker_map.py
    ├── test_market_hours.py
    ├── test_cache.py
    ├── test_indicators.py
    └── test_fetcher.py
```

**Testbarkeits-Kerngedanke:** Der **einzige** Netzwerk-Punkt ist eine winzige
Funktion `_raw_download(symbol, period, interval) -> pd.DataFrame` in
`fetcher.py`. Alles andere arbeitet auf DataFrames. Tests monkeypatchen
`_raw_download` und injizieren Fixture-DataFrames — kein echter yFinance-Call,
nie.

---

## 4. Contracts — Dataclasses (`models.py`)

Diese Felder sind die Integrationsfläche zu Phase 4/5/7. Gegenüber dem Konzept
**erweitert** (Ehrlichkeit über Datenherkunft/Verzögerung/Verfügbarkeit):

```python
from __future__ import annotations
from dataclasses import dataclass, field

@dataclass
class PriceBar:
    ts: str            # ISO 8601 UTC (Bar-Startzeit)
    open: float
    high: float
    low: float
    close: float
    volume: float      # 0.0 wenn Quelle kein Volumen liefert

@dataclass
class DriftResult:
    ticker: str        # yf-Symbol
    today_open: float
    current_price: float
    drift_pct: float           # (now - open) / open * 100; + = bullish
    as_of: str                 # ISO 8601 UTC der zugrunde liegenden Bar
    is_realtime: bool = False  # yFinance ist verzögert → immer False

@dataclass
class MomentumResult:
    ticker: str
    window_minutes: int        # angefragtes Fenster (default 15)
    momentum_pct: float
    price_now: float
    price_start: float
    as_of: str                 # ts der jüngsten Bar
    source_resolution: str = "5m"
    is_realtime: bool = False  # ← yFinance ~15min verzögert. EHRLICH labeln.

@dataclass
class VolumeAnomaly:
    ticker: str
    today_volume: float
    rolling_mean: float
    rolling_std: float
    z_score: float             # 0.0 wenn kein Volumen verfügbar
    is_anomaly: bool           # abs(z) >= 2.0 (und volume_available)
    is_extreme: bool           # abs(z) >= 3.0 (Warnung)
    lookback_days: int
    as_of: str
    volume_available: bool = True   # False bei ^GDAXI ohne Proxy
    volume_source: str | None = None  # welches yf-Symbol das Volumen lieferte

@dataclass
class HighLowDistance:
    ticker: str
    lookback_days: int             # default 90
    rolling_high: float
    rolling_low: float
    current_price: float
    distance_to_high_pct: float
    distance_to_low_pct: float
    is_near_high: bool             # distance_to_high_pct < 1.5
    is_near_low: bool              # distance_to_low_pct < 1.5
    as_of: str

@dataclass
class BrainContext:
    ticker: str                    # IG epic (Eingangswert)
    yf_symbol: str
    drift: DriftResult | None
    momentum_15m: MomentumResult | None
    volume: VolumeAnomaly | None
    high_low: HighLowDistance | None
    price_history_30d: list[PriceBar]
    generated_at: str
    def to_prompt_dict(self) -> dict: ...   # kompakt, für LLM-Prompt (§4.1)
    def to_dict(self) -> dict: ...          # vollständig, für market_context_json
```

### 4.1 `BrainContext.to_prompt_dict()` — exakte Keys

Nur die für das LLM relevanten Felder, kein Roh-OHLCV. **Fehlende Werte als
`None`, nicht weglassen** (das LLM soll Lücken sehen):

```python
{
  "ticker": "IX.D.DAX.IFMM.IP",
  "drift_pct": 0.85 | None,
  "momentum_15m_pct": -0.12 | None,
  "momentum_is_realtime": False,          # Hinweis an Prompt: verzögert!
  "volume_z_score": 1.7 | None,
  "volume_available": True,
  "distance_to_high_pct": 0.4 | None,
  "distance_to_low_pct": 6.2 | None,
  "range_30d": {"low": 17900.0, "high": 18600.0} | None,
  "generated_at": "2026-05-27T09:35:11.123Z"
}
```
`to_dict()` gibt zusätzlich das volle `price_history_30d` als Liste von
`PriceBar`-Dicts zurück (für `trade_lessons.market_context_json` in Phase 2/7).

---

## 5. `exceptions.py`

Pattern wie Phase 1 (`BrokerError`): Basisklasse mit `code`, optional `retryable`.

```python
class ExternalDataError(Exception):
    code: str = "EXTERNAL_DATA_ERROR"
    retryable: bool = False
    def __init__(self, message: str, *, retryable: bool | None = None) -> None:
        super().__init__(message)
        if retryable is not None:
            self.retryable = retryable

class EpicNotMappedError(ExternalDataError):   # code="EPIC_NOT_MAPPED", retryable=False
class DataUnavailableError(ExternalDataError): # code="DATA_UNAVAILABLE", retryable=True
class RateLimitError(ExternalDataError):       # code="RATE_LIMIT", retryable=True
```
Eigene `RateLimitError` (kein Import aus Phase 1 — Isolation). Wo nötig
fängt der Fetcher `yfinance.exceptions.YFRateLimitError` und übersetzt.

---

## 6. `timeutil.py` (dupliziert)

Exakt das Phase-2-Format. Monkeypatchbarer Clock-Punkt:

```python
def _utcnow() -> datetime:               # ← Tests monkeypatchen DIESEN Punkt
    return datetime.now(timezone.utc)

def utc_iso_now() -> str:                # "...T...Z" ms-Präzision
def parse_iso(ts: str) -> datetime:      # akzeptiert Z-Suffix, gibt aware UTC
```
Alle anderen Module rufen `utc_iso_now()` / `parse_iso()` auf, nie
`datetime.now()` direkt — damit ist die Zeit testbar steuerbar.

---

## 7. `market_hours.py`

```python
from zoneinfo import ZoneInfo
_TZ = ZoneInfo("Europe/Berlin")
_OPEN  = time(9, 0)
_CLOSE = time(17, 30)

def is_market_open(now: datetime | None = None) -> bool:
    """True wenn now (UTC-aware) ein XETRA-Handelszeitpunkt ist:
    Mo–Fr, 09:00–17:30 Europe/Berlin. now=None → _utcnow()."""
```
**Feiertage** werden in v1 **nicht** über einen Kalender abgebildet — sie fallen
ohnehin in den `DataUnavailableError`-Pfad (yFinance gibt an Feiertagen leere
DataFrames). Im Code-Kommentar als bewusste Vereinfachung + TODO-Hook
(`exchange_calendars`/`pandas_market_calendars` optional ab späterer Phase)
vermerken — keine schwere Dep jetzt.

---

## 8. `ticker_map.py`

```python
class TickerMapper:
    _MAP = {
        "IX.D.DAX.IFMM.IP":  "^GDAXI",   # Deutschland 40 Kassa (confirmed Phase 1)
        "IX.D.DAX.DAILY.IP": "^GDAXI",
        "CS.D.EURUSD.MINI.IP": "EURUSD=X",
        "IX.D.DOW.DAILY.IP": "^DJI",
    }
    _VOLUME_MAP: dict[str, str] = {}     # leer = kein Proxy → degrade

    def epic_to_yf(self, epic: str) -> str:        # raises EpicNotMappedError
    def epic_to_volume_yf(self, epic: str) -> str | None:  # None = kein Proxy
    def register(self, epic: str, yf_symbol: str) -> None
    def register_volume_proxy(self, epic: str, volume_yf_symbol: str) -> None
```
**ETF-Proxy-Hook (Entscheidung 1):** `_VOLUME_MAP` bleibt v1 leer → `^GDAXI`
degradiert sauber. Will Niklas später echtes Handelsinteresse, ruft die
Bot-Config `register_volume_proxy("IX.D.DAX.IFMM.IP", "EXS1.DE")` (iShares Core
DAX) — **ohne Refactoring**. **Wichtiger Caveat im Docstring vermerken:**
ETF-Volumen ≈ ETF-Handelsinteresse, **nicht** DAX-Index-Volumen; als
Anomalie-Signal brauchbar, nicht als exakte Volumengröße.

---

## 9. `cache.py` — `FileCache`

JSON-Dateien, TTL über gespeicherten `expires_at`-Timestamp. Atomares Schreiben
(temp + `os.replace`, wie Phase-2 `state.py`).

```python
class FileCache:
    def __init__(self, cache_dir: str) -> None:    # mkdir parents=True, exist_ok=True
    def make_key(self, symbol: str, resolution: str, date: str) -> str:
        # deterministisch, dateisystem-sicher: "^GDAXI" → "GDAXI" (^ entfernen),
        # f"{safe_symbol}_{resolution}_{date}"
    def get(self, key: str) -> list[dict] | None:   # None bei missing/expired/korrupt
    def set(self, key: str, data: list[dict], ttl_seconds: int) -> None:
    def clear_expired(self) -> int:                 # Anzahl entfernter Einträge
```

**TTL-Strategie (Entscheidung 2 + 3 berücksichtigt):**

| Auflösung | Zweck | TTL |
|---|---|---|
| `1d` (Tages-Bars) | Drift-Open, Volume-30d, HighLow-90d, History | bis Mitternacht Europe/Berlin (Tages-Bar ist final) |
| `5m` | Momentum + aktueller Preis | 120 s |
| `30m` | optionaler Kontext | 300 s |

**Korruptes/halbes JSON:** `get()` fängt `json.JSONDecodeError`/`OSError`,
loggt WARNING, gibt `None` zurück (Treat-as-miss → Fetcher holt neu). Kein Crash.

---

## 10. `indicators.py` — reine Funktionen (Kern)

Keine I/O, keine Netzwerk-Calls — nur DataFrame rein, Dataclass raus. Jede
Funktion hat ein Div-by-Zero-/Leerdaten-Guard.

```python
def compute_drift(daily_df, intraday_df, *, ticker) -> DriftResult | None
def compute_momentum(bars_5m_df, *, ticker, window_minutes=15) -> MomentumResult | None
def compute_volume_anomaly(daily_df, *, ticker, lookback_days=30,
                           volume_available, volume_source) -> VolumeAnomaly
def compute_high_low_distance(daily_df, current_price, *,
                              ticker, lookback_days=90) -> HighLowDistance | None
```

**Präzise Algorithmik (damit Claude Code nicht rät):**

- **Drift:** `today_open` = `Open` der heutigen Tages-Bar; `current` = `Close`
  der jüngsten 5m-Bar. `drift_pct = (current - today_open)/today_open*100`.
  Guard: `today_open <= 0` oder keine heutige Bar → `None`.
- **Momentum (5m):** Bars nach `ts` sortieren. `price_now` = letzter `Close`.
  `bars_back = max(1, round(window_minutes / 5))` (15 min → 3 Bars).
  `price_start` = `Close` der Bar `bars_back` Positionen vor der letzten.
  Guard: `len(bars) < bars_back + 1` → `None`. `is_realtime=False` setzen.
- **Volume z-score:** rolling mean/std über die letzten `lookback_days`
  Tages-Volumina **vor heute**. `z = (today_vol - mean)/std`.
  Guards: `volume_available is False` → `z_score=0.0, is_anomaly=False,
  is_extreme=False` (kein Crash, Dataclass trotzdem voll befüllt).
  `std == 0` → `z_score=0.0`. `is_anomaly = volume_available and abs(z) >= 2.0`.
  `is_extreme = volume_available and abs(z) >= 3.0`.
- **High/Low:** `rolling_high/low` = max/min `High`/`Low` über `lookback_days`.
  `distance_to_high_pct = (rolling_high - current)/current*100`,
  `distance_to_low_pct = (current - rolling_low)/current*100`. Guard
  `current <= 0` → `None`. `is_near_high = distance_to_high_pct < 1.5`, analog low.
- **Datenhygiene (vor Berechnung, in den `get_*`-Methoden des Fetchers):**
  Wochenend-/Feiertagslücken in Tages-History via `ffill()`; grobe Ausreißer
  per IQR-Filter (Punkte > 3·IQR vom Median im `Close`) droppen. Als kleine
  Helfer in `indicators.py` (`_ffill_gaps`, `_drop_outliers`) — getestet.

---

## 11. `fetcher.py` — `MarketDataFetcher` (Haupt-Interface)

```python
def _raw_download(symbol: str, *, period: str, interval: str) -> "pd.DataFrame":
    """EINZIGER Netzwerk-Punkt. KEINE session übergeben (curl_cffi intern).
    Tests monkeypatchen genau diese Funktion."""
    import yfinance as yf
    return yf.Ticker(symbol).history(period=period, interval=interval,
                                     auto_adjust=False)

class RateLimiter:
    """Token-bucket: min. 0.5 s zwischen Calls. wait() blockiert bis erlaubt."""

class MarketDataFetcher:
    def __init__(self, ticker_mapper: TickerMapper, cache: FileCache,
                 rate_limiter: RateLimiter | None = None) -> None: ...

    # --- Phase 4 (turbo_research) ---
    def get_drift(self, epic: str) -> DriftResult | None
    def get_bars(self, epic: str, resolution: str = "5m", count: int = 20) -> list[PriceBar] | None
    # --- Phase 5 (pre_trade VETO — KONTEXT, siehe §13) ---
    def get_momentum(self, epic: str, minutes: int = 15) -> MomentumResult | None
    # --- Phase 7 (Longterm Brain) ---
    def get_history(self, epic: str, days: int = 30) -> list[PriceBar]
    def get_volume_anomaly(self, epic: str, lookback_days: int = 30) -> VolumeAnomaly | None
    def get_high_low_distance(self, epic: str, lookback_days: int = 90) -> HighLowDistance | None
    # --- Composite (Phase 4 + 7) ---
    def get_brain_context(self, epic: str) -> BrainContext | None
```

> **Angepasst 2026-06-02 (Step 7 / fetcher):** `get_bars` ist
> `-> list[PriceBar] | None` (im Original `-> list[PriceBar]`). Grund: Mit
> Intraday-Auflösung unterliegt `get_bars` dem Off-Hours-Guard (Punkt 2 unten,
> Entscheidung 3) und §17.2 prüft live explizit `get_bars(resolution="5m") is None`
> außerhalb der Handelszeiten. Ein `None`-Rückgabewert ist daher zwingend; die
> Signatur wurde an den Code angeglichen (Source = Source of Truth). Bei
> Daily-Auflösung (`"1d"`) läuft die Methode immer und liefert nie `None`.

**Fetch-Pipeline pro Methode (Reihenfolge):**
1. `epic → yf_symbol` (raises `EpicNotMappedError`, nicht abfangen — Programmierfehler).
2. **Off-Hours-Guard (Entscheidung 3):** Ist die Methode intraday-abhängig
   (`get_drift`, `get_momentum`, `get_bars` mit Intraday-Auflösung) **und**
   `not is_market_open()` → `return None` + `log.info("market closed, skipping
   intraday fetch for %s", symbol)`. **Daily-basierte** Methoden
   (`get_history`, `get_volume_anomaly`, `get_high_low_distance`) laufen immer.
3. Cache-Key bauen, `cache.get()`. Hit → daraus rechnen, kein Fetch.
4. Miss → `RateLimiter.wait()` → `_fetch_with_retry(...)` → `cache.set()`.
5. Indikator-Funktion aus `indicators.py` aufrufen, Dataclass zurückgeben.

**`_fetch_with_retry` (Korrektur 2 — beide Fehlermodi):**
```python
# Exponential backoff 1s → 2s → 4s, max 3 Versuche.
try:
    df = _raw_download(symbol, period=period, interval=interval)
except YFRateLimitError:
    # backoff, retry; nach max_retries → raise RateLimitError(retryable=True)
if df is None or df.empty or len(df) < min_expected:
    # backoff, retry; nach max_retries → raise DataUnavailableError(retryable=True)
```
**`get_brain_context` ist fehlertolerant:** ruft alle Einzel-`get_*` in einem
`try/except ExternalDataError` je Feld; ein fehlender Wert wird zu `None` im
`BrainContext`, **kein** Gesamt-Crash. Loggt pro Lücke ein WARNING.

**`current_price` für `get_high_low_distance`:** während Handelszeiten letzte
5m-`Close`; außerhalb letzte Tages-`Close`. So funktioniert HighLow auch
nachts (Phase-7-Lesson-Extraktion nach Handelsschluss).

---

## 12. Off-Hours- & Verzögerungs-Disziplin (Entscheidung 3 + Risiko-Flag)

- Intraday-Methoden geben **außerhalb 09:00–17:30 Europe/Berlin / am
  Wochenende `None`** zurück — **niemals** still einen alten Cache-Wert als
  „frisch" ausgeben.
- Wenn ein Aufrufer bewusst den letzten bekannten Wert will, ist das ein
  **expliziter** Pfad (eigene Methode / Flag in späterer Phase), nicht das
  Default-Verhalten.
- `MomentumResult.is_realtime = False` **immer**. yFinance-`^GDAXI` ist ein
  *Delayed Quote* (~15 min). `to_prompt_dict()` reicht
  `momentum_is_realtime: False` ans LLM weiter.

---

## 13. ⚠ Architektur-Flag für Phase 5 (nicht Phase-3-Scope, aber dokumentieren)

Das Konzept lässt den **harten Momentum-VETO** in Phase 5 aus
`get_momentum()` (yFinance) ziehen. yFinance ist ~15 min verzögert — ein
„15-Minuten-Momentum" misst dann real ein Fenster, das vor ~15 min endete. Für
einen VETO gegen einen *unmittelbar bevorstehenden* Trade ist das untauglich
und widerspricht dem Konzept-Grundsatz „Phase 3 nie für Order-Entscheidungen".

**Empfehlung (in Phase-3-`README.md` + `CLAUDE.md` als Notiz festhalten):** Der
harte Momentum-VETO in Phase 5 sollte aus **Phase-1/IG-Echtzeit-Bars** kommen.
Phase-3-`get_momentum()` bleibt ein **Kontext-Signal** (ehrlich als verzögert
gelabelt) für den Research-Prompt — kein VETO-Input. Phase 3 baut korrekt; die
Entscheidung gehört in die Phase-5-Konzept-Session.

---

## 14. Build-Reihenfolge (für Claude Code, mit Test-Gate nach jedem Schritt)

> Nach **jedem** Schritt `pytest tests/ -v` grün, bevor weiter (Top-CLAUDE.md).

1. `external_data/exceptions.py` + `external_data/models.py` (Contracts zuerst).
2. `external_data/timeutil.py` + `external_data/market_hours.py` → `test_market_hours.py`.
3. `external_data/ticker_map.py` → `test_ticker_map.py`.
4. `external_data/cache.py` → `test_cache.py`.
5. `external_data/indicators.py` → `test_indicators.py` (**Kern — gründlich**).
6. `external_data/fetcher.py` (`_raw_download`, `RateLimiter`, Retry, alle
   `get_*`) → `test_fetcher.py` (mit gemocktem `_raw_download`).
7. `external_data/__init__.py` (Exports), `requirements.txt`.
8. `scripts/smoke_test.py` (schneller Sanity-Lauf, §17.1).
9. `scripts/live_test.py` (vollständiger Verifikations-Test mit Assertions, §17.2).
10. `README.md` + `CLAUDE.md` (inkl. Phase-5-Flag aus §13).

---

## 15. Test-Matrix (Ziel ≥ 45; Plan ≈ 56)

**Kein Netzwerk. Clock via monkeypatch auf `timeutil._utcnow`. yFinance via
monkeypatch auf `fetcher._raw_download`.**

`conftest.py`-Fixtures: `tmp_cache` (FileCache in `tmp_path`), `sample_dax_daily`
(30+ Tages-Bars, realistische Werte, inkl. einer Variante mit `Volume=0` für
^GDAXI), `sample_dax_5m` (genug 5m-Bars für 15-min-Momentum), `frozen_clock`
(setzt `_utcnow` auf festen Mo 11:00 Europe/Berlin).

| Datei | Tests (≈) | Abdeckung |
|---|---|---|
| `test_market_hours.py` | 5 | Mo-im-Fenster True; Sa/So False; vor 09:00 False; nach 17:30 False; DST-Grenze (Sommer/Winter) |
| `test_ticker_map.py` | 7 | epic→yf; unbekannt→`EpicNotMappedError`; `register`; Volume-Proxy fehlt→`None`; `register_volume_proxy`→Treffer; Case-Sensitivität; `^`-Symbole |
| `test_cache.py` | 10 | `make_key` deterministisch + `^`-safe; set/get-Roundtrip; TTL-frisch→Hit; TTL-abgelaufen→`None`; missing→`None`; korruptes JSON→`None`+self-heal; `clear_expired` Count; `cache_dir`-Anlage; Daily- vs 5m-Key; atomares Schreiben |
| `test_indicators.py` | 22 | Drift (normal, open=0-Guard, keine heutige Bar→`None`); Momentum (normal, zu wenig Bars→`None`, negatives Vorzeichen, `is_realtime False`, bars_back-Rundung); Volume (normal-z, std=0-Guard, `volume_available=False`→degrade-Felder, Schwelle 2.0, Extrem 3.0); HighLow (near-high, near-low, mid, current=0-Guard); `_ffill_gaps`; `_drop_outliers` (IQR) |
| `test_fetcher.py` | 12 | Cache-Hit→kein Fetch; Miss→Fetch→`cache.set`; leeres DF→Retry→`DataUnavailableError`; `YFRateLimitError`→Retry→`RateLimitError`; Off-Hours intraday→`None`; Daily außerhalb Hours erlaubt; `get_brain_context` Fehlertoleranz (ein Feld `None`, kein Crash); Momentum-Delay-Flag; Volume-degrade-Pfad; HighLow nutzt Daily-Close außerhalb Hours; `EpicNotMappedError` propagiert; `RateLimiter.wait` wird aufgerufen |

---

## 16. `requirements.txt`

```
# runtime
yfinance>=0.2.65,<0.3
pandas>=2.0.0
# curl_cffi kommt transitiv mit yfinance (ggf. Build-Toolchain nötig)

# dev / test
pytest>=7.4.0
```
Kein `freezegun` (Korrektur 4). Kein `pandas-ta`/`ta` (vier triviale Formeln).
`zoneinfo` ist stdlib (Python ≥ 3.9).

---

## 17. Manuelle Netzwerk-Tests (außerhalb `pytest`, kein IG-Account nötig)

**Zwei Scripts, beide treffen das echte yFinance, beide laufen NICHT in `pytest`
und NICHT in CI** (Netzwerk, nicht-deterministisch). Sie werden **manuell**
ausgeführt. Klare Rollentrennung, damit sie sich nicht überlappen:

- **`smoke_test.py`** = schneller Sanity-Lauf („läuft die Pipeline überhaupt und
  liefert sie einen plausiblen Prompt-Dict?"). Druckt, prüft nicht hart.
- **`live_test.py`** = vollständige Verifikation mit harten Assertions und
  PASS/FAIL-Exitcode. Das ist das Gegenstück zu Phase-2 `scripts/live_test.py`,
  mit dem Phase 2 „live-verifiziert" wurde — das **Gate**, bevor Phase 4 sich
  auf Phase-3-Ausgaben verlässt.

Beide: `logging.basicConfig(..., stream=sys.stderr)`, Argparse wie Phase 1/2,
maschinenlesbares JSON auf **stdout**, Mensch-Output auf **stderr**.

### 17.1 `scripts/smoke_test.py` (schneller Sanity-Check)

- Argparse: `--epic IX.D.DAX.IFMM.IP` (default), optional `--volume-proxy EXS1.DE`.
- Baut `TickerMapper`, `FileCache(<repo_root>/data/cache/)`, `MarketDataFetcher`.
- Läuft alle `get_*` + `get_brain_context` einmal durch, druckt das
  `to_prompt_dict()` als JSON auf stdout.
- Erkennt Off-Hours: meldet sauber, dass Intraday `None` ist und nur Daily
  Werte liefert (kein Fehler — erwartetes Verhalten).

```bash
python scripts/smoke_test.py
python scripts/smoke_test.py --epic IX.D.DAX.IFMM.IP --volume-proxy EXS1.DE
```

### 17.2 `scripts/live_test.py` (vollständiger Verifikations-Test, manuell)

Gründlicher als der Smoke-Test: jede öffentliche Methode **gegen reales
`^GDAXI`**, plus Verhaltens-Assertions zu Cache, Rate-Limiter und Off-Hours.
Gibt am Ende eine PASS/FAIL-Summary auf stderr und **Exitcode 0 (alle pass) /
1 (mind. ein fail)** — manuell vor jedem Phasenübergang ausführbar.

**Argparse:**
- `--epic IX.D.DAX.IFMM.IP` (default)
- `--volume-proxy EXS1.DE` (optional — testet den ETF-Volume-Pfad live)
- `--clear-cache` (löscht `data/cache/` vor dem Lauf, damit der Cache-Hit-Test
  aussagekräftig ist — sonst ist Schritt 1 evtl. schon ein Hit)
- `--verbose` (DEBUG-Logging)

**Aufbau (jeder Check ist ein benannter `(name, passed, detail)`-Eintrag):**

1. **Konnektivität & Vollständigkeit.** `get_history(epic, days=30)` →
   assert nicht-leer, `len ≈ 30` (Toleranz für Feiertage), jede `PriceBar` hat
   `high >= low`, `close > 0`. Das ist der „yFinance erreichbar"-Check.
2. **Daily-Indikatoren (immer verfügbar, auch Off-Hours).**
   - `get_volume_anomaly` → `z_score` endlich (`math.isfinite`); ohne Proxy:
     `volume_available is False` und `is_anomaly is False`; mit
     `--volume-proxy`: `volume_available is True`, `volume_source` gesetzt,
     `today_volume > 0`.
   - `get_high_low_distance` → `rolling_high >= rolling_low`, beide Distanzen
     `>= 0`, `current_price > 0`.
3. **Markt-Regime-Verzweigung (Test passt in BEIDEN Zuständen).**
   `is_market_open()` abfragen und entsprechend asserten — so ist der Test
   **jederzeit lauffähig**, nicht nur 09:00–17:30:
   - **Markt offen:** `get_drift`, `get_momentum`, `get_bars(resolution="5m")`
     ≠ `None`; Plausibilität: `abs(drift_pct) < 10`, `abs(momentum_pct) < 5`,
     `momentum.is_realtime is False` (Delay-Ehrlichkeit, §12).
   - **Markt zu/Wochenende:** dieselben drei Methoden **müssen `None`**
     liefern (Entscheidung 3) — das ist hier ein *bestandener* Check, kein Fail.
4. **Cache-Hit verifizieren (echter Netzwerk-Spar-Nachweis).** Vor dem Lauf
   einen Zähler um `fetcher._raw_download` legen (monkeypatch/wrap, der die
   echte Funktion aufruft und `calls += 1` zählt). Dann **dieselbe**
   Daily-Methode (z.B. `get_history`) zweimal aufrufen: nach Aufruf 1 stieg der
   Zähler, nach Aufruf 2 **nicht** (Cache-Hit, kein zweiter Netz-Call).
   `--clear-cache` stellt sicher, dass Aufruf 1 ein Miss ist.
5. **Rate-Limiter-Abstand.** Zwei erzwungene Misses (verschiedene Symbole oder
   nach Cache-Clear) timen → gemessener Abstand `>= 0.5 s` (RateLimiter greift).
   > **Angepasst 2026-06-02 (Finalize):** Statt sich auf `--clear-cache` zu
   > verlassen, provisioniert der Check sich selbst einen frischen Temp-`FileCache`
   > (eigener Probe-`MarketDataFetcher`) → beide Probe-Fetches sind **garantiert
   > Misses**, unabhängig vom Cache-Zustand eines vorherigen Laufs. So produziert
   > der Check bei warmem Cache keinen Falsch-Fehler mehr (Source = Source of Truth).
6. **`get_brain_context` Fehlertoleranz live.** Aufrufen → Ergebnis ≠ `None`,
   `to_prompt_dict()` enthält alle erwarteten Keys (§4.1); fehlende Intraday-
   Felder dürfen `None` sein (Off-Hours), aber der Aufruf crasht nie.

**Output:** Mensch-lesbare Tabelle der Checks auf stderr (`✓/✗ name — detail`),
darunter `RESULT: 6/6 passed` bzw. die Fail-Liste; das vollständige
`brain_context.to_dict()` als JSON auf stdout. Exitcode entsprechend.

```bash
python scripts/live_test.py                                   # gegen ^GDAXI
python scripts/live_test.py --clear-cache --verbose           # frische Fetches, laut
python scripts/live_test.py --volume-proxy EXS1.DE            # ETF-Volume-Pfad mitprüfen
```

> **Wichtig:** `live_test.py` ist KEIN `pytest`-Test und wird von `pytest tests/`
> nicht eingesammelt (liegt unter `scripts/`, nicht `tests/`). Reale 429er können
> einen Lauf zum Scheitern bringen — das ist dann ein yFinance-/Netz-Zustand,
> kein Code-Defekt. Bei Fail erst erneut mit `--clear-cache` nach kurzer Pause
> versuchen, bevor man dem Code misstraut.

---

## 18. Definition of Done

- `pytest tests/ -v` grün, **≥ 45 Tests** (Plan ≈ 56).
- `scripts/smoke_test.py` liefert während Marktzeiten valide Werte für `^GDAXI`
  (alle Indikatoren ≠ `None` außer Volume-Anomaly, die ohne Proxy degradiert);
  außerhalb Marktzeiten korrektes `None` für Intraday + valide Daily-Werte.
- `scripts/live_test.py` **läuft mit Exitcode 0** (alle Checks pass) — manuell
  einmal ausgeführt und dokumentiert. In BEIDEN Regimes lauffähig (Markt offen
  → Intraday-Werte; Markt zu → Intraday `None` als bestandener Check).
  Das ist das Verifikations-Gate vor Phase 4.
- `external_data/__init__.py` exportiert `MarketDataFetcher`, `TickerMapper`,
  `FileCache`.
- `README.md` dokumentiert Install (inkl. curl_cffi-Hinweis), Nutzung,
  Integrationspunkte (Phase 4/5/7), bekannte Limits (Delay, ^GDAXI-Volume).
- `CLAUDE.md` enthält das Phase-5-Momentum-VETO-Flag aus §13.
- **`## Session stopped`-Block** am Ende der Phase-3-`CLAUDE.md` (Pflicht-Handover).
- `docs/concepts/phase3_external_data_konzept.md` ggf. um getroffene
  Entscheidungen + Korrekturen ergänzen (oder Link auf diesen Plan), damit das
  Konzept nicht das veraltete yFinance-Verhalten behauptet.

---

## 19. Anti-Pattern-Wächter (Top-CLAUDE.md, hier relevant)

- **Kein LLM-Call in Phase 3.** Wenn Code „formatieren/filtern/validieren" via
  LLM erwägt — stop, das ist Code.
- **`_raw_download` ist der einzige Netzwerk-Punkt.** Kein zweiter yFinance-Call
  verstreut im Code.
- **Keine eigene Session an yFinance.** (Korrektur 1.)
- **Intraday-Werte nie still aus altem Cache als „frisch" servieren.** (Entsch. 3.)
- **Phase 3 importiert nichts aus Phase 1/2.** Eigenes `timeutil.py`, eigene
  `exceptions.py`.
- **Kein Subtask „done" ohne grünes `pytest`.**
