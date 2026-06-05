# Phase 4 — Implementierungsplan für Claude Code

> **Status:** Architektur geklärt (8 Entscheidungen unten gelockt), Contracts gegen
> den echten Repo-Code verifiziert. Dieser Plan ersetzt die ungenauen Stubs im
> Konzept dort, wo der Code abweicht.
>
> **Quelle der Wahrheit bleibt das Repo.** Wo dieser Plan eine Signatur nennt, ist
> sie aus `ig_adapter.py` / `filters.py` / `credentials.py` verifiziert. Wo der Plan
> auf Phase-3-Keys verweist (`to_prompt_dict`), ist die **finale** Verifikation gegen
> `phase3_external_data/.../models.py` ein Pflicht-Schritt (Step 0.5).

---

## 0. Geklärte Architektur-Entscheidungen (gelockt)

| # | Entscheidung | Festlegung |
|---|---|---|
| 1 | `direction`-Vokabular | **`"BUY"` / `"SELL"`** — exakt das, was `open_position()` erzwingt. Fließt ohne Mapping in Phase 5. **Kein CALL/PUT irgendwo.** |
| 2 | Komposition | DI via Konstruktor (gesetzt). `wiring.py`/`live_test.py` lösen echte Instanzen via **`sys.path`-Bootstrap** auf (wie Phase-2-`live_test`). Editable installs / Monorepo erst Phase 5. |
| 3 | Strukturierte Ausgabe | **Structured Outputs als Primärpfad** (`output_format` json_schema, `epic` als Enum der realen Liste). Manuelles Parse + Fence-Strip nur als Fallback. Validator unabhängig **immer** aktiv. |
| 4 | Confidence | LLM-Confidence ist **epistemisch schwach** (Forschung: ECE ~0,1, systematisch overconfident, keine Schwelle filtert zuverlässig). Daher: **als Feld speichern, als grober Low-Floor nutzen — NICHT als das Gate.** Reales Gating trägt der deterministische `candidate_filter`. Floor-Semantik im Code als „provisorisch, ersetzt durch Phase-7 outcome-anchored" dokumentiert. |
| 5 | Epic-Universum | **Hybrid, code-kuratiert.** `epic_allowlist` in der Config, Default `("IX.D.DAX.IFMM.IP",)`, Platz für 1–2 kuratierte DAX-Geschwister. **Kein** `search_markets("DAX")`-Schleppnetz (Halluzinations-Oberfläche + Latenz). Pro Epic via `get_price` + `get_market_info` proben, mit `is_tradeable` filtern. |
| 6 | Credentials | **Usecase über Politik:** Phase-1-`get_credential` wiederverwenden (gleicher Keyring `SERVICE_NAME="tradingbot"`). Dünner Phase-4-Shim dokumentiert die bewusste Isolations-Ausnahme. Key: `anthropic_api_key`. |
| 7 | `allowed_directions` | Config-Flag. Default beide. **Long-Bias-Clamp auf `("BUY",)` bei `bot_score < 50` standardmäßig AN.** Clamp arbeitet rein mit BUY/SELL — keine Call-Überbleibsel. |
| 8 | LLM-Fehlerverhalten | **1× Retry** — aber nur bei **transienten** Fehlern (Netzwerk, 5xx, Timeout, Parse-/Schema-Fail). **Kein** Retry bei (a) validem `abstain` (legitime Antwort), (b) `validator`-REJECT (Inhaltsentscheidung → kein Trade; Reject-Retry = „nach einer handelbaren Antwort shoppen" = Anti-Pattern). Jeder Endfehler → `save_candidates([])` → kein Trade. |

---

## Step 0 — Terminologie-Bereinigung + Contract-Fix (eigener Commit, VOR jeder Logik)

> **Angepasst 2026-06-05 (Step 0 ausgeführt, Code = Source of Truth):**
> Aufgabe 2 (`turbo_research.py` → `research.py`, `TurboResearch` → `Research`) war ein
> **No-Op** — es existierte **kein** Phase-4-Stub im Repo (kein `phase4_research/`,
> keine `turbo_research.py`/`TurboResearch`). Die Benennung wird stattdessen **bei der
> Datei-Erstellung in den Steps 1–9 erzwungen** (`research/research.py`, Klasse
> `Research`). Aufgabe 3 (Options-Semantik verbannen) betraf nur noch Doku, da noch
> kein Candidate-/Schema-Code existierte. Die „Done-when"-`grep`-Treffer in `.py`
> waren **ausschließlich False-Positives** (`callable`, `compute_*`, `_last_call`,
> `EpicNotMappedError`, `output`/`input`); der einzige echte `turbo_research`-Treffer
> war ein Phase-3-Kommentar (`fetcher.py:343`), jetzt auf `research` korrigiert.
> Zusätzlich trugen zwei **Phase-2-Fixtures** noch das Alt-Vokabular
> `"direction": "CALL"` (`tests/test_state.py` `CANDIDATE`, `scripts/live_test.py` ×2) —
> auf das BUY/SELL-Contract (`"BUY"`) umgestellt (opake Roundtrip-Dicts, keine
> Direction-Wert-Assertion → verhaltensneutral; concept-Aufgabe 3 „CALL/PUT verbannen").
> Tatsächlich geänderte Dateien: Root-`CLAUDE.md`, `README.md`, `ROADMAP.md`,
> `phase2_persistence/.../state.py` (nur Kommentar),
> `phase2_persistence/tests/test_state.py` + `phase2_persistence/scripts/live_test.py`
> (CALL→BUY), `phase3_external_data/.../fetcher.py` (nur Kommentar).

Der Handover behandelt Step 0 als Kosmetik. Der Code zeigt einen **harten
Contract-Bruch**: `ig_adapter.open_position()` erzwingt `direction in ("BUY","SELL")`
und wirft sonst `ValueError`. Das Konzept trägt durchgängig `CALL/PUT` — Options-Erbe
aus dem Turbo-Bot. Würde Phase 4 `"CALL"` schreiben, crasht Phase 5 beim Order-Call.

**Aufgaben (ein Commit, kein Research-Code):**

1. **`turbo_candidates.json` als Name einfrieren** (Phase-2-Contract, Phase-5 Gate 2
   erwartet ihn). Kommentar an `CANDIDATES_FILE`: *„legacy name; Inhalt = DAX-CFD-
   Kandidaten, keine Turbos."* **Nicht** umbenennen.
2. **`turbo_research.py` → `research.py` umbenennen.** Interner Dateiname, **kein**
   Contract-Bruch, keine Folgephase zeigt darauf. Jetzt sauber, solange noch nichts
   verdrahtet ist. Klasse: `TurboResearch` → **`Research`**.
3. **Options-Semantik aus jedem Candidate-/Schema-Entwurf verbannen:** kein `strike`,
   `otm_distance`, `issuer`, `expiry`, **kein `CALL`/`PUT`**. `direction` ist BUY/SELL.
4. **Top-Level-Doku korrigieren:** Root-`CLAUDE.md` „options trading bot" →
   **„CFD trading bot for the DAX"**; ROADMAP-Phase-4-Filter „OTM distance" →
   „CFD-Filter (Spread, Drift-Eignung, Score-Coupling)"; Hinweis, dass `turbo_*`
   Legacy-Benennung ist.

**Done when:** `grep -ri "call\|put\|strike\|otm\|issuer\|turbo_research" --include=*.py`
liefert keine instrumentenbezogenen Treffer mehr (außer dem bewusst dokumentierten
`turbo_candidates.json`-Legacy-Namen). Eigener, sauberer Commit.

---

## Step 0.5 — Phase-3-Keys final verifizieren (vor `context_builder.py`)

Der Phase-3-Handover sagt: *„The exact key set is part of the Phase-4 contract — do
not rename or drop keys."* **Bevor** der Context-Builder gebaut wird:

> **✅ Verifiziert gegen Code 2026-06-05** (`phase3_external_data/external_data/models.py:194-205`
> `to_prompt_dict()`; `fetcher.py:461-494` `get_brain_context`). Code = Source of Truth.

- **Reales Key-Set (10 Keys, exakt diese Reihenfolge):**
  `ticker, drift_pct, momentum_15m_pct, momentum_is_realtime, volume_z_score,
  volume_available, distance_to_high_pct, distance_to_low_pct, range_30d,
  generated_at`.
  ⚠ **Abweichung 1:** der ursprüngliche Konzept-Erwartungswert nannte **9** Keys und
  **vergaß `generated_at`** — der Code liefert es mit. Context-Builder/Prompt müssen den
  Extra-Key tolerieren (als Snapshot-Zeitstempel nutzen oder ignorieren), nicht von einem
  9-Key-Set ausgehen.
- **Nullability (bestätigt):** `drift_pct`, `momentum_15m_pct`, `volume_z_score`,
  `distance_to_high_pct`, `distance_to_low_pct`, `range_30d` können **je `None`** sein
  (Off-Hours-Guard außerhalb 09:00–17:30 Europe/Berlin; Indikator nicht verfügbar; keine
  History). `momentum_is_realtime` ist **immer `False`** (delay-ehrlich; auch `False`,
  wenn Momentum `None` ist). `volume_available` ist `False` bei fehlendem/degradiertem
  Volume. `range_30d` ist `{"low": float, "high": float}` **oder** `None`. → Prompt rendert
  `None` ehrlich (kein „0"-Fake), crasht nie darauf.
- ⚠ **Abweichung 2 — `get_brain_context` gibt praktisch **nie** `None` zurück:** Die
  Signatur ist `BrainContext | None`, der Body liefert für ein **gemapptes** Epic aber
  immer einen `BrainContext` (jeder Indikator einzeln per `try/except` → `None`-Feld;
  History `or []`). Der **echte** Fehlerfall ist **`EpicNotMappedError`** (propagiert),
  wenn das Epic **nicht** in `TickerMapper._MAP` steht. Das Default-Allowlist-Epic
  `IX.D.DAX.IFMM.IP` **ist** gemappt (→ `^GDAXI`) — für die Default-Config kein Risiko;
  Risiko nur, wenn kuratierte Geschwister-Epics ohne Ticker-Mapping ergänzt werden.
- Volume-Proxy `EXS1.DE` via `register_volume_proxy` auf dem Fetcher/Mapper setzen (in
  `wiring.py`/Config — **Step 8**), sonst ist `volume_z_score` immer `None`.

---

## Verifizierte geerbte Contracts (gegen Repo-Code geprüft)

### Phase 1 — `broker_wrapper`
- `adapter.connect() -> Envelope` · `is_connected() -> bool` · `get_account() -> Envelope`
- `adapter.get_price(epic) -> Envelope`; `.data` enthält u.a. `bid, ask, spread,
  spread_pct, market_status, timestamp`. **`spread_pct` und `market_status` kommen von
  hier** (nicht aus `search_markets`).
- `adapter.get_market_info(epic) -> Envelope`; `.data` enthält `min_deal_size, currency,
  instrument_type, market_status`.
- `adapter.search_markets(query) -> Envelope`; `.data = {"query":..., "results":[...]}`
  — Items: `epic, name, type, expiry, market_status, bid, ask` (**kein** `spread_pct`,
  **kein** `min_size`). → wird in Phase 4 **nicht** als Universums-Quelle genutzt
  (Entscheidung 5), nur das Allowlist-Proben via `get_price`/`get_market_info`.
- `adapter.get_ohlcv(epic, resolution, count)` — `resolution` ∈ `VALID_RESOLUTIONS`
  (`MINUTE`, `MINUTE_5`, …); für Phase 5-VETO, **nicht** Phase 4.
- `open_position(epic, direction, size, ...)` — **`direction in ("BUY","SELL")` Pflicht.**
- `broker_wrapper.filters`: `is_tradeable(price, market_info, FilterConfig) -> FilterVerdict`
  (`.ok`, `.rule`, `.reason`); `calc_spread_pct(bid, ask)`; `calc_position_size(...)`.
- **Envelope:** `.ok` (bool), `.data` (dict bei ok), `.error` (`{code,message,retryable}`).
  Phase 4 prüft **immer** `env.ok` vor `env.data`.

### Phase 2 — `persistence`
- `Database.get_recent_trades(n=8)` · `get_recent_lessons(n=5)` · `get_current_score()`
  · `get_risk_level()` · `mark_lesson_used(id)`
- `StateManager.save_candidates(list[dict])` · `load_candidates()` ·
  `candidates_are_fresh()` · `clear_candidates()` (TTL 30 min, self-clearing).

### Phase 3 — `external_data` *(verifiziert 2026-06-05 — siehe Step 0.5)*
- `MarketDataFetcher.get_brain_context(epic) -> BrainContext | None`, dann
  `.to_prompt_dict()`. **Praktisch nie `None`** für ein gemapptes Epic; wirft aber
  `EpicNotMappedError` für ungemappte Epics → Step-3-Guard ist `try/except
  EpicNotMappedError` (+ defensiver `is None`-Check).
- `to_prompt_dict()` = **10 Keys** inkl. `generated_at` (Step 0.5). Jeder Indikator-Wert
  kann `None` sein; Intraday-Werte außerhalb der Marktzeiten `None` → tolerieren.

### Credentials
- `from broker_wrapper.credentials import get_credential`; `get_credential("anthropic_api_key")`.
  `SERVICE_NAME="tradingbot"`. Seeding via vorhandenes `scripts/store_credential.py`.

### LLM (recherchiert)
- Structured Outputs sind GA (Sonnet 4.5/4.6, Opus 4.5+). Modell-Default
  **`claude-sonnet-4-6`** (Konzept-String `claude-sonnet-4-20250514` ist veraltet),
  als `ResearchConfig.model` **konfigurierbar, nicht hardcoden**.
- Structured Outputs garantieren **Schema-Form, nicht Korrektheit** → Validator bleibt
  Pflicht. `epic` als dynamisches Enum der realen Liste macht Epic-Halluzination auf
  Decoding-Ebene unmöglich; der Validator prüft trotzdem (Defense-in-Depth + Live-Spread).

---

## Der Candidate-Contract (Phase 4 → Phase 5, einmal definiert = stabil)

`turbo_candidates.json` enthält pro Pick ein Dict dieser Form. **Abstain/Reject →
leere Liste** (`save_candidates([])`), kein `abstain`-Feld im persistierten Candidate.

```python
{
    "epic": str,                    # exakt aus dem bereitgestellten Universum
    "direction": "BUY" | "SELL",    # Broker-Vokabular, direkt in open_position
    "llm_confidence": float,        # 0-100, LLM-Selbstbericht — ADVISORY, unkalibriert
    "reasoning": str,               # 2-3 Sätze, LLM
    "spread_pct_at_pick": float,    # Code-erfasst beim Validieren (frischer get_price)
    "drift_at_pick": float | None,  # Code-erfasst, P3-Kontext (~15min verzögert)
    "score_at_pick": float,         # Bot-Score zum Entscheidungszeitpunkt
    "threshold_applied": float,     # angewandter Confidence-Floor (55/70)
    "generated_at": str,            # ISO-8601 UTC
    "source": "research",           # Provenienz
}
```

> Bewusst getrennt: `llm_confidence` (Selbstbericht, schwach) vs. die code-erfassten
> Hartfakten (`spread_pct_at_pick`, `drift_at_pick`, `score_at_pick`). Phase 7 kann
> später `llm_confidence` gegen tatsächliche Outcomes korrelieren und prüfen, ob das
> Modell überhaupt kalibriert war — genau die Daten, die outcome-anchored Confidence braucht.

---

## Modul-Struktur

```
phase4_research/
├── README.md
├── CLAUDE.md                      # inkl. "## Session stopped"-Handover (Pflicht)
├── requirements.txt               # anthropic SDK (einzige neue Dep)
├── research/
│   ├── __init__.py                # exports: Research, ResearchConfig
│   ├── research.py                # Orchestrator run()  (ex turbo_research.py)
│   ├── context_builder.py         # ResearchContext aus P1/P2/P3 (Code)
│   ├── prompt.py                  # (system, user, json_schema) bauen (Code)
│   ├── llm_client.py              # Anthropic-Wrapper, Structured Outputs + Fallback + 1 Retry
│   ├── validator.py               # ★ Halluzinations-Schutz (Code)
│   ├── candidate_filter.py        # ★ deterministisches reales Gate (Code)
│   ├── models.py                  # Candidate, ResearchContext, ResearchConfig, ValidationResult
│   ├── timeutil.py                # ★ Step-2-Ergänzung: utc_iso_now()/_utcnow()/parse_iso (wie P3)
│   └── credentials.py             # dünner Shim → broker_wrapper.credentials.get_credential
├── scripts/
│   ├── wiring.py                  # baut echte P1/P2/P3-Instanzen (sys.path), setzt EXS1.DE-Proxy
│   ├── smoke_test.py              # ein echter LLM-Lauf, DRY (kein save)
│   └── live_test.py               # voller Zyklus → candidates.json, hart asserted, exit 0
└── tests/
    ├── conftest.py                # FakeBroker, FakeDB, FakeFetcher, FakeLLM
    ├── test_validator.py          # ★ höchste Priorität (≥12)
    ├── test_context_builder.py    # (≥6)
    ├── test_prompt.py             # (≥5)
    ├── test_candidate_filter.py   # (≥6)
    ├── test_llm_client.py         # (≥6)
    └── test_research.py           # voller run() (≥5)
```

Repo-Konventionen (gelten auch hier): `from __future__ import annotations`, Type-Hints +
Docstrings, eine Datei = eine Verantwortung, eigene typisierte Exceptions, nie still
schlucken, **Logging → stderr / stdout nur maschinenlesbares JSON**, `pytest` ohne
Netzwerk/echtes LLM, atomic commits, kein Subtask „done" ohne grünes `pytest`.

---

## Build-Reihenfolge (strikt TDD, jede Stufe grün bevor weiter)

### 1. `models.py` (keine Logik, nur Typen)
- `Candidate` (Felder = Contract oben), `ResearchContext`, `ResearchConfig`,
  `ValidationResult`.
- `ResearchConfig`-Felder mindestens: `model: str = "claude-sonnet-4-6"`,
  `max_tokens: int = 1024`, `temperature: float = 0.2`, `timeout_s: float = 30.0`,
  `epic_allowlist: tuple[str, ...] = ("IX.D.DAX.IFMM.IP",)`,
  `allowed_directions: tuple[str, ...] = ("BUY", "SELL")`,
  `long_bias_below_score: float = 50.0`, `enable_long_bias_clamp: bool = True`,
  `max_spread_pct: float = 0.5`, `volume_proxy: str | None = "EXS1.DE"`,
  `confidence_floor_default: float = 55.0`, `confidence_floor_low_score: float = 70.0`.
- Eigene Exceptions: `LLMResponseError`, `ResearchAbort` (Session-Health-Fail).

### 2. `validator.py` + `test_validator.py` ZUERST (Sicherheits-Kern)
Reine Funktion. **Der wichtigste Test der ganzen Phase.**

> **Angepasst 2026-06-05 (Step 2 gebaut, Code = Source of Truth):** Die 6 **positionalen**
> Args bleiben exakt wie unten eingefroren. Der Validator **baut** bei PASS aber den
> **vollen** `Candidate` (Contract oben) — und zwei Contract-Felder (`score_at_pick`,
> `drift_at_pick`) sind Entscheidungs-Kontextwerte, die in den 6 Args **nicht** vorkommen.
> Lösung: zwei **keyword-only** Passthrough-Parameter `*, score_at_pick: float,
> drift_at_pick: float | None` ergänzt (vom Orchestrator aus `context.bot_score` bzw.
> P3-Drift versorgt; in Tests explizit übergeben). Sie beeinflussen **keine**
> Validierungs-Entscheidung — reine Persistenz-Durchreichung. `broker` ist im Code via
> lokalem `typing.Protocol` (`_BrokerLike.get_price`) getypt, **kein** `broker_wrapper`-
> Import (Phasen-Isolation). `generated_at` wird via neuem `research/timeutil.py`
> (`utc_iso_now()`, monkeypatchbares `_utcnow()` — wie Phase 3) gestempelt; das Modul war
> in der Modul-Struktur unten nicht gelistet, ist aber die Phase-1/2/3-Konvention und wird
> ab Step 5 (Token-Meter-`ts`) mitgenutzt. `test_validator.py`: **18 grün** (≥12 erfüllt).

```python
def validate_candidate(
    raw: dict,                       # geparster LLM-Output (oder Structured-Output-Dict)
    epic_universe: list[dict],       # Code-bereitgestellte reale Epics (mit frischen Daten)
    threshold: float,                # score-abhängiger Confidence-Floor
    allowed_directions: tuple[str, ...],
    broker: "BrokerAdapter",         # für Live-Spread-Recheck
    max_spread_pct: float,
    *,                               # ── Step-2-Ergänzung (Passthrough, keine Logik) ──
    score_at_pick: float,            # → Candidate.score_at_pick (aus context.bot_score)
    drift_at_pick: float | None,     # → Candidate.drift_at_pick (P3-Drift)
) -> ValidationResult: ...
```

Prüfreihenfolge (jeder Fail → `valid=False` + `rejected_reason`):
1. `raw["abstain"] is True` → valider „kein Kandidat"-Zustand (`valid=True, candidate=None`).
2. Pflichtfelder vorhanden (`epic, direction, confidence`)?
3. **★ `epic` ∈ `{e["epic"] for e in epic_universe}`?** sonst REJECT (Halluzination).
4. `direction ∈ allowed_directions`? sonst REJECT.
5. `confidence` numerisch, `0 ≤ c ≤ 100`, `c ≥ threshold`? sonst REJECT (grober Floor).
6. **★ Live-Spread-Recheck:** frischer `broker.get_price(epic)`; `env.ok` und
   `spread_pct ≤ max_spread_pct` und `market_status == "TRADEABLE"`? sonst REJECT.
7. PASS → `Candidate` bauen, `spread_pct_at_pick` aus dem frischen Preis übernehmen.

**`test_validator.py` (≥12), Pflichtfälle:**
- erfundenes Epic (nicht in Liste) → REJECT
- `direction="CALL"` (Alt-Müll) bzw. außerhalb allowed → REJECT
- confidence < threshold → REJECT; confidence = threshold → PASS
- confidence > 100 / nicht-numerisch → REJECT
- Epic valide, aber Live-Spread inzwischen zu weit → REJECT
- Epic valide, aber `market_status != TRADEABLE` → REJECT
- `get_price`-Envelope `ok=False` → REJECT (kein blinder Trade)
- fehlende Pflichtfelder → REJECT
- `abstain=True` → PASS mit `candidate=None`
- wohlgeformter valider BUY → PASS, `spread_pct_at_pick` gesetzt
- valider SELL → PASS

### 3. `context_builder.py` + Tests (nach Step 0.5)

> **Angepasst 2026-06-05 (Step 3 gebaut, Code = Source of Truth):** Von den zwei in
> diesem §3 angebotenen Tradeable-Check-Optionen wurde die **zweite** umgesetzt —
> `spread_pct`/`market_status` (+ `currency`) **direkt aus `env.data` prüfen**, **kein**
> `Price`/`MarketInfo`-Rebuild + `is_tradeable`-Aufruf. Grund: Phasen-Isolation
> konsequent wie beim Validator (Step 2) — `context_builder.py` importiert **nichts** aus
> `broker_wrapper`; Kollaborateure sind via lokale `typing.Protocol` (`_BrokerLike` mit
> `get_price`+`get_market_info`, `_DBLike`, `_FetcherLike`) getypt. Der EUR-Check
> (`currency == "EUR"`) spiegelt `FilterConfig.require_currency` + die EUR-Konto-Hard-Rule.
> Der `EpicNotMappedError`-Guard fängt **per Klassennamen** (`type(exc).__name__ ==
> "EpicNotMappedError"`) — kein `external_data`-Import (Codebase-Muster wie P3
> `_is_rate_limit_error`); jede andere Exception propagiert. `build_context` ruft pro Epic
> `get_price` **und** `get_market_info` (Letzteres liefert `name`/`currency`/
> `min_deal_size`). `test_context_builder.py`: **13 grün** (≥6 erfüllt).

`build_context(broker, db, market_data, config) -> ResearchContext`. Rein deterministisch.
- **Epic-Probe (Entscheidung 5):** für jedes Epic in `config.epic_allowlist`:
  `get_price` + `get_market_info`, dann `is_tradeable(price, info, FilterConfig(
  max_spread_pct=config.max_spread_pct))`. Nur `ok`-Verdikte landen im Universum,
  als Dicts `{epic, name, spread_pct, market_status, min_deal_size}`.
  ⚠ **Verifiziert (Step 0):** `is_tradeable(price, market_info, ...)` erwartet
  `Price`/`MarketInfo`-**Objekte** (`broker_wrapper.models`), **keine** Dicts —
  `env.data` ist das Dict. Step 3 muss `Price`/`MarketInfo` aus `env.data`
  rekonstruieren **oder** `spread_pct`/`market_status` direkt aus `env.data` prüfen
  (Envelope immer zuerst `env.ok` checken).
- **Phase-2-Kontext:** `get_recent_trades(8)`, `get_recent_lessons(5)`,
  `get_current_score()`, `get_risk_level()`.
- **Phase-3-Kontext:** `get_brain_context(epic).to_prompt_dict()` für das Anker-Epic;
  `None`-Werte transparent durchreichen. ⚠ **Verifiziert (Step 0.5):** in
  `try/except EpicNotMappedError` kapseln (ungemapptes Epic) + defensiver `is None`-
  Check; bei Fehler P3-Kontext für dieses Epic auf `None` degradieren, nicht crashen.
  Key-Set = 10 Keys inkl. `generated_at`.
- Leeres Universum (alle Epics nicht handelbar / Markt zu) → `ResearchContext` mit
  leerem `tradeable_epics`; der Orchestrator behandelt das als Abstain-Pfad.
- Tests (≥6): vollständiger Kontext; leere Trades/Lessons; `volume_z_score=None`;
  alle Intraday `None` (off-hours); ein Epic nicht handelbar → fällt raus; leeres Universum.

### 4. `prompt.py` + Tests

> **Angepasst 2026-06-05 (Step 4 gebaut, Code = Source of Truth):** Umgesetzt wie
> spezifiziert; präzisiert: (a) Das `direction`-Schema-Enum wird **dynamisch aus
> `allowed_directions`** gebaut (`[*allowed_directions, None]`) — der Konzept-Stub zeigte
> statisch `["BUY","SELL",None]`; der Code reflektiert den Long-Bias-Clamp (BUY-only →
> `["BUY", None]`), wie der §4-Test-Bullet es ohnehin fordert. (b) `None`-Werte werden über
> einen einzigen `_fmt()`-Choke-Point als **`"n/a"`** gerendert (nie „0"); Floats mit 2
> Nachkommastellen. (c) Die Recent-Trades-Tabelle rendert defensiv (`.get()`) die Spalten
> **`date | direction | epic | pnl | status`** (`date` = `session_date`→`close_ts`→`open_ts`),
> Lessons als `lesson_text`-Zeilen — passend zu den realen P2-`trade_outcomes`/`trade_lessons`-
> Spalten. (d) Leeres Universum → `epic`-Enum `[None]` (kein Crash; Orchestrator abstaint
> ohnehin vorher). (e) Der System-Prompt nennt **CALL/PUT explizit als verboten** (statt sie
> nur wegzulassen). Reine Funktion, kein I/O/Clock/AI; Kollaborateur-Typ nur `ResearchContext`
> (kein `broker_wrapper`/`external_data`/`persistence`-Import). `test_prompt.py`: **10 grün**
> (≥5 erfüllt).

`build_prompt(context, threshold, allowed_directions) -> tuple[str, str, dict]`
→ `(system, user, json_schema)`.
- **System:** Rolle = Research-Analyst eines DAX-Intraday-CFD-Bots; wähle ≤1 Instrument
  **nur aus der Liste**; **Marktdaten ~15 min verzögert → Stimmungsbild, kein Echtzeit-
  Signal**; bei Zweifel enthalten.
- **User (Code-gebaut):** Marktlage (verzögert, mit `None` ehrlich markiert) · letzte 8
  Trades als Tabelle · aktive Lessons · Bot-Score + Risk-Level + geforderter Floor ·
  **handelbare Instrumente als Tabelle (epic, name, spread%, min_size)** · Antwortformat.
- **`json_schema`** für Structured Outputs:
  ```python
  {
    "type": "object",
    "properties": {
      "abstain": {"type": "boolean"},
      "epic": {"type": ["string", "null"], "enum": [*epics, None]},  # dynamisch!
      "direction": {"type": ["string", "null"], "enum": ["BUY", "SELL", None]},
      "confidence": {"type": ["number", "null"], "minimum": 0, "maximum": 100},
      "reasoning": {"type": "string"},
    },
    "required": ["abstain", "reasoning"],
    "additionalProperties": False,
  }
  ```
- Tests (≥5): alle Sektionen vorhanden; Epic-Liste korrekt eingebettet; `None`-Werte
  ehrlich gerendert (kein Crash, kein „0"-Fake); Schema-`epic`-Enum = exakt Universum +
  `null`; `allowed_directions`-Clamp im Schema reflektiert (bei BUY-only nur `["BUY", null]`).

### 5. `llm_client.py` + Tests
```python
class LLMClient:
    def __init__(self, model: str, api_key: str, *, max_tokens: int,
                 temperature: float, timeout_s: float) -> None: ...
    def ask_candidate(self, system: str, user: str, json_schema: dict) -> dict:
        """Einziger LLM-Call-Punkt. Primär Structured Outputs, Fallback manueller
        Parse. 1 Retry bei transientem Fehler. LLMResponseError sonst."""
```
- **Primärpfad:** Anthropic SDK mit `output_format`/json_schema (Beta-Header bei Bedarf,
  Version aus Doku gegenchecken). Rückgabe = geparstes Dict.
- **Fallback:** wenn Structured Outputs scheitern → normaler Call, dann Fence-Strip
  (` ```json ` entfernen) + `json.loads`.
- **Retry (Entscheidung 8):** **genau 1×**, nur bei Netzwerk/Timeout/5xx/Parse-Fail
  (kleiner Backoff). **Nicht** bei validem JSON, das `abstain` oder einen REJECT-Pick
  enthält — das ist eine inhaltliche Antwort, kein Transportfehler.
- **Ein einziger mockbarer Punkt** (analog `_raw_download` in Phase 3): die rohe
  SDK-Call-Methode kapseln, damit Tests sie patchen.
- Tests (≥6, gemockt, **kein Netzwerk**): Structured-Output-Dict sauber zurückgegeben;
  Backtick-umrandetes JSON im Fallback geparst; Malformed → 1 Retry → dann
  `LLMResponseError`; transienter Fehler → 1 Retry → Erfolg; valides `abstain` → **kein**
  Retry; API-Key fehlt → klare Exception.

### 6. `candidate_filter.py` + Tests — DAS REALE GATE
Hier sitzt die Gating-Last (Entscheidung 4 + 7), nicht bei der LLM-Confidence.

```python
def confidence_threshold(bot_score: float, config: ResearchConfig) -> float:
    """Score unter neutral → strengerer Floor. NICHT als Wahrscheinlichkeit lesen —
    grober Selbstbericht-Floor, ersetzt durch Phase-7 outcome-anchored."""
    return config.confidence_floor_low_score if bot_score < 50.0 \
        else config.confidence_floor_default

def resolve_allowed_directions(bot_score: float, config: ResearchConfig) -> tuple[str, ...]:
    """Long-Bias-Clamp: bot_score < long_bias_below_score → nur ('BUY',)."""
    if config.enable_long_bias_clamp and bot_score < config.long_bias_below_score:
        return ("BUY",)
    return config.allowed_directions

def apply_filter(candidate: Candidate, context: ResearchContext,
                 config: ResearchConfig) -> FilterVerdict: ...
```
- `apply_filter` führt die **deterministischen** Endregeln: Spread ≤ max (aus dem schon
  geprüften Universum bestätigt), `market_status TRADEABLE`, `direction` im geclampten
  Set, optionale **weiche Drift-Kohärenz-Sanity** (z.B. SELL bei stark positivem Drift →
  Verdict mit Warn-`rule`, **nicht** hart ablehnen, da P3-Daten verzögert sind —
  Entscheidung 4: Bot soll nicht ins „nie sicher"-Extrem kippen).
- Tests (≥6): Floor 55 bei score≥50; Floor 70 bei score<50; Clamp auf BUY-only bei
  score<50; Clamp aus → beide erlaubt; SELL bei score<50 → gefiltert; saubere BUY
  passiert.

### 7. `research.py` Orchestrator + Tests
```python
class Research:
    def __init__(self, broker, db, state, market_data, llm, config): ...  # DI
    def run(self) -> list[Candidate]: ...
```
Flow (alles außer dem einen LLM-Call ist Code):
1. **Session-Health:** `broker.is_connected()` bzw. `connect()`; `get_account().ok`;
   `get_price(anchor_epic).ok` + `TRADEABLE`. Fail → `ResearchAbort` → `save_candidates([])`.
2. `context = build_context(...)`. Leeres Universum → Abstain-Pfad.
3. `threshold = confidence_threshold(score, config)`;
   `allowed = resolve_allowed_directions(score, config)`.
4. `system, user, schema = build_prompt(context, threshold, allowed)`.
5. `raw = llm.ask_candidate(system, user, schema)` — der **einzige** AI-Schritt.
   Bei `LLMResponseError` → Abstain → `save_candidates([])` (kein blinder Trade).
6. `vr = validate_candidate(raw, context.tradeable_epics, threshold, allowed, broker,
   max_spread_pct, score_at_pick=context.bot_score, drift_at_pick=<P3-Drift aus
   context.brain_context>)` (keyword-only Args, Step-2-Ergänzung — siehe §2-Annotation).
   REJECT oder `abstain` → `save_candidates([])`.
7. `fv = apply_filter(vr.candidate, context, config)`; `not fv.ok` → `save_candidates([])`.
8. PASS → `state.save_candidates([candidate.to_dict()])`. Rückgabe der Liste.
9. **Logging:** jede REJECT/Abstain-Begründung nach **stderr** (für Brain/Debug);
   stdout nur das maschinenlesbare Ergebnis-JSON.
- Tests (≥5, alle Mocks): voller PASS-Flow → 1 Candidate gespeichert; `abstain` →
  `save_candidates([])`; Validator-REJECT → leer; LLM-Error → leer; Session-Health-Fail
  → leer, kein LLM-Call.

### 8. `scripts/`
- `wiring.py`: `sys.path`-Bootstrap, baut **echte** `IGAdapter` (Demo-Creds via Keyring),
  `Database`, `StateManager`, `MarketDataFetcher` (**`register_volume_proxy("EXS1.DE")`**),
  `LLMClient` (`get_credential("anthropic_api_key")`). Eine Factory
  `build_research(config) -> Research`.
- `smoke_test.py`: ein echter Research-Lauf, **DRY** (StateManager gemockt/`save` no-op),
  druckt Kontext + LLM-Antwort + Validator-Verdict. Schnell, manuell.
- `live_test.py`: voller Zyklus gegen IG Demo + echtes LLM → schreibt valide
  `turbo_candidates.json` **oder** dokumentiert sauber den Abstain-Grund.
  **Hart asserted**, `exit 0` = PASS. Läuft **nicht** in CI.

### 9. `README.md` + `CLAUDE.md`
- `CLAUDE.md`: AI-Grenze, Candidate-Contract, die 8 Entscheidungen, **`## Session
  stopped`-Handover-Block** (Pflicht). Confidence-Floor explizit als „provisorisch,
  Phase-7 ersetzt" markiert — im Code-Kommentar **nicht** als echtes Confidence-System ausgeben.

---

## Done-Kriterien (Phase-4-Gate)
- `pytest tests/ -v` grün, **≥40 Tests**, davon `test_validator.py` ≥12.
- `python scripts/live_test.py` erzeugt valide `turbo_candidates.json` (oder
  dokumentierten Abstain), `exit 0`.
- `grep` aus Step 0 zeigt keine Options-/CALL-/PUT-/Turbo-Logik mehr.
- **Beweis-Test:** eine LLM-Halluzination (erfundenes Epic, übertriebene Confidence,
  Alt-`CALL`) wird im Validator zuverlässig abgefangen, bevor sie Candidate wird.

## Bewusst NICHT in Phase 4 (Carry-overs)
- Harter Momentum-VETO → **Phase 5**, aus **IG-Echtzeit-Bars** (`get_ohlcv`), **nicht**
  aus dem ~15 min verzögerten P3-`get_momentum()`. P3-Momentum bleibt hier reines
  verzögertes Kontextsignal.
- Outcome-anchored Confidence (`f(win_rate, expectancy, sample_size)`, N_min=10) →
  **Phase 7**. Phase 4 speichert `llm_confidence` als Rohdaten dafür.

---

## Session stopped — 2026-06-05

> Handover liegt hier, weil `phase4_research/` noch nicht existiert. Sobald Step 1 das
> Verzeichnis anlegt, wandert dieser Block nach `phase4_research/CLAUDE.md`.

### Completed — Step 0.5 (Phase-3-Key-Contract verifiziert — doc-only)
- `to_prompt_dict()` final gegen Code gelesen (`models.py:194-205`): **10 Keys** inkl.
  `generated_at` (Konzept-Erwartung nannte nur 9 → korrigiert). Nullability je Indikator
  bestätigt; `momentum_is_realtime` immer `False`; `range_30d` dict|None.
- `get_brain_context` (`fetcher.py:461-494`): Signatur `BrainContext | None`, gibt aber
  **praktisch nie `None`** zurück (gemapptes Epic → immer Objekt); echter Fehlerfall ist
  **`EpicNotMappedError`** für ungemappte Epics → Step-3-Guard `try/except` + `is None`.
- Konzept aktualisiert: Step 0.5, „Verifizierte geerbte Contracts → Phase 3", Step-3-
  Bullets (inkl. `is_tradeable` braucht `Price`/`MarketInfo`-Objekte). **Kein Code,
  keine Tests** (reiner Verifikations-/Doku-Schritt). Noch nicht committet.

### Completed — Step 0 (Terminologie-Bereinigung + Contract-Fix)
- Root-`CLAUDE.md` + `README.md`: „options trading bot" → „CFD trading bot for the DAX";
  README-Statustabelle Phase-4-Zeile auf `research.py + LLM (turbo_* = legacy)`.
- `ROADMAP.md` Phase-4-Block: Überschrift/Done-when `turbo_research.py` → `research.py`;
  Filter „OTM distance" → „CFD-Filter (Spread, Drift-Eignung, Score-Coupling)";
  Legacy-Hinweis zu `turbo_candidates.json`.
- `phase2_persistence/.../state.py`: Legacy-Kommentar an `CANDIDATES_FILE` (Datei/Name
  bewusst **nicht** umbenannt — Phase-2/Phase-5-Contract).
- `phase3_external_data/.../fetcher.py:343`: Kommentar `turbo_research` → `research`.
- `phase2_persistence/tests/test_state.py` + `scripts/live_test.py`: Alt-Vokabular
  `"direction": "CALL"` → `"BUY"` (BUY/SELL-Contract; verhaltensneutral).
- Step-0-Aufgabe 2 (`turbo_research.py`/`TurboResearch` umbenennen) war **No-Op** —
  kein Stub existierte; Benennung wird bei Datei-Erstellung erzwungen (Annotation oben).
- **Verifikation:** Done-when-`grep` über `.py` zeigt nur False-Positives (Verb „call",
  HTTP `PUT /session`, Erklär-Kommentar); `pytest` Phase 2 = 59 grün, Phase 3 = 70 grün;
  `py_compile` der geänderten Dateien sauber. **Noch nicht committet** (User triggert Commit).

### Next — Step 1
- **Step 1:** `phase4_research/` anlegen (`README.md`, `CLAUDE.md`, `requirements.txt`
  mit `anthropic`, `research/`-Package) + `research/models.py` (nur Typen:
  `Candidate`, `ResearchContext`, `ResearchConfig` mit Defaults gem. §1,
  `ValidationResult` + Exceptions `LLMResponseError`, `ResearchAbort`). Danach Step 2 =
  `validator.py` (Sicherheits-Kern, ≥12 Tests). Step-0.5-Erkenntnisse (10-Key-Set,
  `EpicNotMappedError`-Guard, `Price`/`MarketInfo`-Objekte) fließen in Step 3 ein.

### Token-Zähler (User-Zusatz) — Design steht, Bau in Step 5
- Phase-4-`token_meter`: liest `usage.input_tokens`/`output_tokens` (+ Cache-Felder) aus
  jeder Anthropic-Response, **appended** Records `{ts, model, input_tokens, output_tokens,
  est_cost_eur}` an gitignored `data/state/llm_usage.json`; Pro-Modell-Pricing in
  `ResearchConfig`. Bleibt komplett in Phase 4. Wird in `llm_client.py` (Step 5) eingehängt.

### Open questions / blockers
- Keine. Die Step-0-Erkenntnis (`is_tradeable` braucht `Price`/`MarketInfo`-Objekte) und
  die Step-0.5-Erkenntnisse (10-Key-Set inkl. `generated_at`; `EpicNotMappedError` statt
  `None`) sind in Step 0.5 / „Verifizierte geerbte Contracts" / Step 3 eingearbeitet.
