# Phase 2 — Persistenz: Sollkonzept

> **Bauprinzip:** Phase 2 ist 100% Code. Kein einziger LLM-Call.
> Die Persistenz-Schicht ist dumm, schnell und zuverlässig.
> Sie urteilt nicht — sie speichert und gibt zurück.

---

## Ausgangslage (Phase 1 Review)

Phase 1 ist vollständig und live-getestet (Stand 2026-05-21):
- REST Smoke Test ✅ — kompletter Lifecycle inkl. Order open/close gegen IG Demo
- Lightstreamer ✅ — CONOK/SUBOK + echte DAX Ticks bestätigt
- 48 Unit Tests ✅ — envelope(7), filters(10), ig_adapter(14), lightstreamer(17)

**Relevante Phase-1-Outputs für Phase-2-Schema:**
Die Models aus `broker_wrapper/models.py` sind die Datenverträge —
Phase 2 speichert ihre Instanzen. Kein Phase-2-Code importiert
direkt aus `broker_wrapper`; stattdessen empfängt `db.py` Dicts
(via `model.to_dict()`). Saubere Schichttrennung.

Wichtige Phase-1-Erkenntnisse die Phase 2 beeinflussen:
- IG Europe GmbH Account nötig für deutschen Wohnsitz (post-Brexit)
- DAX CFD Epic confirmed: `IX.D.DAX.IFMM.IP`
- Session-Throttling: IG blockt Rapid-Logins → Bot hält eine persistente Session
- `FilterConfig.max_spread_pct = 0.5%` (Grenzwert aus Phase 1)
- `calc_position_size()` gibt Sizing bereits deterministisch aus Phase 1

---

## Was Phase 2 ist / nicht ist

**Ist:**
- Persistente SQLite-Datenbank für historische Trade-Daten
- JSON-basierter operativer Zustand (TTL-getrieben)
- Reader/Writer-Abstraktionen (`db.py`, `state.py`)
- Schema-Migrations-System von Tag 1
- V2-Tabellen als leere Platzhalter (bereit für Phase 9)

**Ist nicht:**
- Business Logic — kein Scoring, kein Filtern, kein Entscheiden
- AI-Schicht — reine Datenhaltung
- Backtesting-Infrastruktur (kommt in Phase 3/4)
- Realtime-Streaming-Speicher (kein Write-Path für Lightstreamer-Ticks)

---

## Dualer Zustandsspeicher: Warum zwei Systeme?

```
SQLite                          JSON State
─────────────────────────────   ──────────────────────────────
Persistent, historisch          Operativ, kurzlebig
Trade-Outcomes, Lessons         Offene Positionen, Kandidaten
Wird nie auto-gelöscht          TTL-basiertes Stale-Check
Analytisch abfragbar            Millisekunden-Zugriff
Wächst über Monate              Wird jede Session überschrieben
```

**Regel:** Wenn die Frage ist "Was hat der Bot letzten Monat getan?" → SQLite.
Wenn die Frage ist "Was tut der Bot gerade?" → JSON State.

---

## SQLite — Schema

### Philosophie
- Alle Timestamps: ISO 8601 UTC Strings (`"2026-05-21T09:34:11.123Z"`)
- Alle Geldbeträge: REAL mit expliziter `currency`-Spalte (nie implizit GBP)
- IDs: INTEGER PRIMARY KEY AUTOINCREMENT (intern), broker deal_id als TEXT
- `NOT NULL` überall wo NULL keinen validen Zustand darstellt
- `CHECK` constraints für bekannte Enums (Direction, DealStatus)
- Kein ORM — reines `sqlite3` mit typed Wrapper-Funktionen

---

### Tabelle 1: `trade_outcomes`

Jeder abgeschlossene Trade — direkt aus `Transaction` + `OrderResult` von Phase 1.

```sql
CREATE TABLE IF NOT EXISTS trade_outcomes (
    id               INTEGER PRIMARY KEY AUTOINCREMENT,

    -- Broker-Identifikatoren
    deal_id          TEXT NOT NULL,
    deal_reference   TEXT,                             -- client-supplied idempotency key
    epic             TEXT NOT NULL,
    broker           TEXT NOT NULL DEFAULT 'ig',

    -- Trade-Parameter
    direction        TEXT NOT NULL CHECK(direction IN ('BUY','SELL')),
    size             REAL NOT NULL CHECK(size > 0),
    open_level       REAL NOT NULL,
    close_level      REAL,                             -- NULL wenn noch offen
    currency         TEXT NOT NULL,

    -- Zeitstempel
    open_ts          TEXT NOT NULL,                    -- ISO 8601 UTC
    close_ts         TEXT,                             -- NULL wenn noch offen
    hold_duration_min REAL,                            -- berechnet bei Close

    -- Ergebnis
    profit_loss      REAL,                             -- in `currency`
    status           TEXT NOT NULL CHECK(status IN ('OPEN','CLOSED','CANCELLED')),

    -- Kontext (wird von Phase 4+ befüllt)
    research_confidence REAL,                          -- LLM Confidence Score (0-100)
    gate_path        TEXT,                             -- JSON: welche Gates bestanden/geblockt
    session_date     TEXT NOT NULL,                    -- "2026-05-21" für Tages-Aggregation

    created_at       TEXT NOT NULL,                    -- Wann dieser Row angelegt wurde
    updated_at       TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_trade_outcomes_deal_id ON trade_outcomes(deal_id);
CREATE INDEX IF NOT EXISTS idx_trade_outcomes_session_date ON trade_outcomes(session_date);
CREATE INDEX IF NOT EXISTS idx_trade_outcomes_epic ON trade_outcomes(epic);
CREATE INDEX IF NOT EXISTS idx_trade_outcomes_status ON trade_outcomes(status);
```

---

### Tabelle 2: `reward_pts`

Score-Delta pro Trade. Wird von Phase 7 (Reward/Punishment) befüllt.
Phase 2 erstellt nur die Tabellenstruktur — Phase 7 schreibt die Werte.

```sql
CREATE TABLE IF NOT EXISTS reward_pts (
    id                    INTEGER PRIMARY KEY AUTOINCREMENT,
    trade_id              INTEGER NOT NULL REFERENCES trade_outcomes(id) ON DELETE CASCADE,

    -- Outcome-basiertes Scoring (aktuelles System)
    outcome_score_delta   REAL NOT NULL DEFAULT 0.0,
    score_after           REAL NOT NULL,               -- akkumulierter Score nach diesem Trade
    win_loss              TEXT NOT NULL CHECK(win_loss IN ('WIN','LOSS','BREAKEVEN')),
    pnl_raw               REAL,                        -- kopiert aus trade_outcomes für schnellen Zugriff

    -- ▲ V2 REFORM: Prozess-Qualitäts-Score (Phase 9 befüllt, Phase 2 erstellt)
    process_score_delta   REAL,                        -- NULL bis Phase 9 aktiv
    veto_trigger_count    INTEGER,                     -- wie viele VETOs feuerten
    gate_fail_count       INTEGER,                     -- wie viele Gates blockierten
    debate_confidence     REAL,                        -- Judge-Confidence aus Bull/Bear
    spread_at_entry_pct   REAL,                        -- Spread zum Eintrittszeitpunkt

    calculated_at         TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_reward_pts_trade_id ON reward_pts(trade_id);
```

---

### Tabelle 3: `trade_lessons`

Von Phase 7 (Longterm Brain) extrahierte Lektionen.
Phase 2 erstellt die Tabelle; Phase 7 schreibt den `lesson_text`.

```sql
CREATE TABLE IF NOT EXISTS trade_lessons (
    id                   INTEGER PRIMARY KEY AUTOINCREMENT,
    trade_id             INTEGER NOT NULL REFERENCES trade_outcomes(id) ON DELETE CASCADE,

    -- Lesson-Inhalt
    lesson_text          TEXT NOT NULL,                -- LLM-extrahierter Lerninhalt
    market_context_json  TEXT,                         -- JSON: Marktbedingungen zur Trade-Zeit

    -- Qualitätsindikatoren
    relevance_score      REAL,                         -- 0.0–1.0, initial NULL
    used_in_research     INTEGER NOT NULL DEFAULT 0,   -- Zählfeld: wie oft als Kontext genutzt
    last_used_ts         TEXT,

    -- ★ V2: Embedding (Phase 9)
    embedding_json       TEXT,                         -- NULL bis Vektor-Store aktiv
    embedding_model      TEXT,                         -- Modell-Version für Invalidierung

    extracted_at         TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_trade_lessons_trade_id ON trade_lessons(trade_id);
CREATE INDEX IF NOT EXISTS idx_trade_lessons_relevance ON trade_lessons(relevance_score);
```

---

### Tabelle 4: `ig_config_state`

Operativer Bot-Zustand der über Sessions hinaus persistent sein muss.
Key-Value Store für Konfigurations-Werte.

```sql
CREATE TABLE IF NOT EXISTS ig_config_state (
    key        TEXT PRIMARY KEY,
    value      TEXT NOT NULL,              -- immer JSON-serialisiert
    updated_at TEXT NOT NULL,
    note       TEXT                        -- optionale Beschreibung
);

-- Vorgeladene Defaults (bei DB-Init eingefügt, nicht überschrieben wenn bereits vorhanden)
-- Beispiel-Keys:
--   "bot_score"           → 50.0
--   "risk_level"          → "KONSERVATIV"
--   "daily_pnl_today"     → 0.0
--   "session_date"        → "2026-05-21"
--   "force_trigger_locked"→ false
```

---

### Tabelle 5: `market_regime_snapshots` *(★ V2 — Phase 9)*

Marktbedingungen zum Zeitpunkt jedes Trades. Phase 2 erstellt die Tabelle leer;
Phase 5/9 befüllt sie.

```sql
CREATE TABLE IF NOT EXISTS market_regime_snapshots (
    id               INTEGER PRIMARY KEY AUTOINCREMENT,
    trade_id         INTEGER NOT NULL REFERENCES trade_outcomes(id) ON DELETE CASCADE,

    -- Markt-Kontext
    volatility_pct   REAL,                -- implizite oder historische Vola
    spread_pct       REAL,                -- Spread zum Snapshot-Zeitpunkt
    drift_pct        REAL,                -- open-to-now drift% aus Phase 1-Filter
    volume_z_score   REAL,                -- Volumen-Anomalie (Standardabweichungen)
    time_of_day_h    REAL,                -- Dezimalstunden (09.5 = 09:30)
    market_status    TEXT,                -- TRADEABLE / AUCTION etc.

    snapshot_ts      TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_market_regime_trade_id ON market_regime_snapshots(trade_id);
```

---

### Tabelle 6: `decision_context` *(★ V2 — Phase 9)*

Vollständiger AI-Entscheidungskontext pro Trade.
Ermöglicht retrospektives Audit: "Was hat der Bull genau gesagt?"

```sql
CREATE TABLE IF NOT EXISTS decision_context (
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    trade_id            INTEGER NOT NULL REFERENCES trade_outcomes(id) ON DELETE CASCADE,

    -- Bull/Bear/Judge
    bull_summary        TEXT,             -- Bull-Position Zusammenfassung
    bear_summary        TEXT,             -- Bear-Position Zusammenfassung
    judge_reasoning     TEXT,             -- Judge-Entscheidungsbegründung
    debate_rounds       INTEGER,          -- Anzahl Debattenrunden (1-5)
    judge_confidence    REAL,             -- 0.0–1.0

    -- VETO-Details
    veto_factors_json   TEXT,             -- JSON: welche VETOs getriggert/bestanden
    pre_trade_checks_json TEXT,           -- JSON: alle pre_trade_option_check() Werte

    -- Council (optional, Phase 9)
    council_verdict     TEXT,             -- SOLIDE / FRAGWÜRDIG / KRITISCH
    council_summary     TEXT,

    stored_at           TEXT NOT NULL
);
```

---

## JSON State — Datei-Schemas

### `ig_state.json` — Account-Snapshot (operativ)

```json
{
    "account_id": "HTADU",
    "balance": 58700.0,
    "available": 55200.0,
    "profit_loss": 0.0,
    "currency": "GBP",
    "open_positions": [
        {
            "deal_id": "DIAAAABBBCCC",
            "epic": "IX.D.DAX.IFMM.IP",
            "direction": "BUY",
            "size": 1.0,
            "open_level": 18342.5,
            "profit_loss": 12.5,
            "currency": "EUR"
        }
    ],
    "session_active": true,
    "last_updated": "2026-05-21T09:34:11.123Z"
}
```

**TTL-Logik:** Wird jedes Mal überschrieben wenn `get_account()` oder
`get_open_positions()` aufgerufen wird. Kein festes TTL — wird
als "fresh" betrachtet wenn `last_updated` < 60 Sekunden alt ist.

---

### `ig_config.json` — Bot-Konfiguration (semi-persistent)

```json
{
    "broker": "ig",
    "account_type": "demo",
    "trading_window": {
        "start_cet": "09:30",
        "end_cet": "11:19"
    },
    "risk": {
        "max_risk_pct": 0.08,
        "position_cap_gbp": 3000,
        "max_concurrent_positions": 1,
        "min_balance_gbp": 5.0
    },
    "filters": {
        "max_spread_pct": 0.5,
        "max_drift_pct_veto": 50.0,
        "max_momentum_pct_veto": 0.5,
        "min_confidence": 55
    },
    "research": {
        "candidates_ttl_min": 30,
        "max_candidates": 1,
        "min_confidence_low_score": 70
    }
}
```

**TTL-Logik:** Kein TTL — wird nur auf expliziten Benutzer-Befehl geändert.
Gelesen beim Bot-Start, gecacht im Prozess.

---

### `turbo_candidates.json` — Research-Output (TTL 30min)

```json
{
    "generated_at": "2026-05-21T09:25:00.000Z",
    "ttl_minutes": 30,
    "expires_at": "2026-05-21T09:55:00.000Z",
    "session_date": "2026-05-21",
    "candidates": [
        {
            "epic": "IX.D.DAX.IFMM.IP",
            "direction": "CALL",
            "confidence": 72,
            "reasoning": "...",
            "spread_pct_at_research": 0.41,
            "drift_pct": 0.85,
            "research_score_context": 50
        }
    ]
}
```

**TTL-Logik:** `expires_at` wird von `state.py` gecheckt.
Wenn abgelaufen oder `candidates` leer → Datei wird gelöscht.
Leere Liste → kein Trade für diese Session.

---

## Code-Architektur

```
phase2_persistence/
├── README.md
├── requirements.txt          # sqlite3 ist stdlib; evtl. keine externen Deps nötig
├── persistence/
│   ├── __init__.py           # exports: Database, StateManager
│   ├── db.py                 # SQLite connection + CRUD für alle Tabellen
│   ├── state.py              # JSON State read/write + TTL-Logik
│   ├── migrations.py         # Schema-Versionierung (migration runner)
│   ├── schema.py             # thin: _schema_version DDL + MIGRATIONS_DIR (KEIN Tabellen-DDL)
│   ├── timeutil.py           # ISO-8601-UTC-Helfer (utc_iso_now, parse_iso) — dupliziert aus Phase 1
│   └── defaults.py           # Seed-Daten für ig_config_state bei DB-Init
├── migrations/
│   ├── 001_initial.sql       # Alle 6 Tabellen
│   └── (002_..., 003_... für zukünftige Erweiterungen)
├── scripts/
│   └── init_db.py            # Einmalig ausführen: DB anlegen + Defaults einfügen
└── tests/
    ├── test_db.py             # CRUD-Tests für alle Tabellen
    ├── test_state.py          # TTL, JSON read/write, stale check
    └── test_migrations.py     # Migration Runner Tests
```

---

## `db.py` — Interface-Konzept

```python
class Database:
    def __init__(self, db_path: str) -> None: ...

    # trade_outcomes
    def insert_trade(self, trade: dict) -> int: ...         # returns rowid
    def update_trade_close(self, deal_id: str, close_data: dict) -> bool: ...
    def get_open_trades(self) -> list[dict]: ...
    def get_trade_by_deal_id(self, deal_id: str) -> dict | None: ...
    def get_recent_trades(self, n: int = 8) -> list[dict]: ...  # für Brain/Research-Kontext

    # reward_pts
    def insert_reward(self, trade_id: int, reward: dict) -> int: ...
    def get_current_score(self) -> float: ...
    def get_risk_level(self) -> str: ...            # "KONSERVATIV" | "AGGRESSIV"

    # trade_lessons
    def insert_lesson(self, trade_id: int, lesson: dict) -> int: ...
    def get_recent_lessons(self, n: int = 5) -> list[dict]: ...
    def mark_lesson_used(self, lesson_id: int) -> None: ...

    # ig_config_state
    def get_config(self, key: str) -> Any | None: ...
    def set_config(self, key: str, value: Any, note: str = "") -> None: ...
    def get_all_config(self) -> dict[str, Any]: ...

    # V2 Tabellen (Phase 9 befüllt, Phase 2 erstellt nur Schema)
    def insert_regime_snapshot(self, trade_id: int, snapshot: dict) -> int: ...
    def insert_decision_context(self, trade_id: int, context: dict) -> int: ...
```

---

## `state.py` — Interface-Konzept

```python
class StateManager:
    def __init__(self, state_dir: str) -> None: ...

    # ig_state.json
    def save_account_state(self, account: dict, positions: list[dict]) -> None: ...
    def load_account_state(self) -> dict | None: ...
    def is_account_state_fresh(self, max_age_s: int = 60) -> bool: ...

    # ig_config.json
    def load_bot_config(self) -> dict: ...          # raises if missing
    def save_bot_config(self, config: dict) -> None: ...

    # turbo_candidates.json
    def save_candidates(self, candidates: list[dict]) -> None: ...
    def load_candidates(self) -> list[dict]:        # returns [] if expired/missing
    def clear_candidates(self) -> None: ...
    def candidates_are_fresh(self) -> bool: ...
```

---

## Migrations-System

Einfacher, selbst-geschriebener Migration Runner — kein Alembic, kein ORM.

```python
# migrations.py Konzept:
# DB-Tabelle `_schema_version` (INTEGER) hält aktuellen Stand.
# Migration-Dateien: migrations/001_initial.sql, 002_xyz.sql, ...
# Runner prüft aktuelle Version, führt alle neueren aus, atomisch (BEGIN/COMMIT).

def run_migrations(conn: sqlite3.Connection, migrations_dir: str) -> None:
    current = _get_schema_version(conn)
    pending = _find_pending_migrations(migrations_dir, current)
    for migration in sorted(pending):
        _apply_migration(conn, migration)
```

**Version 1** (`001_initial.sql`): Alle 6 Tabellen.
Wenn Phase 9 die V2-Tabellen erweitert, kommt `002_v2_extensions.sql`.
Keine destruktiven Migrations — nur `ALTER TABLE ADD COLUMN` oder neue Tabellen.

---

## Integration mit Phase 1

Phase 2 importiert **nie** direkt aus `broker_wrapper`.
Die Datenweitergabe läuft über Dicts:

```python
# Phase 5 (ig_bot.py) wird später so arbeiten:
from broker_wrapper import get_broker
from persistence import Database

broker = get_broker("ig_demo")
db = Database("trading_bot.sqlite")

# Nach Order-Close:
position = broker.get_open_positions().data[0]  # dict aus Envelope
db.insert_trade({                                # Envelope.data direkt verwertbar
    "deal_id": position["deal_id"],
    "epic": position["epic"],
    ...
})
```

**Warum nicht direkt importieren?**
Phase-Isolation. Die Persistence-Schicht muss ohne Broker-Verbindung
lauffähig sein (Tests, Offline-Analyse, Backtesting).

---

## Was Code macht, was AI macht

```
Phase 2 ist 100% Code. Kein LLM-Aufruf.

Code macht ALLES:
├── SQLite Reads/Writes
├── JSON Reads/Writes
├── TTL-Berechnung (expires_at - now())
├── Schema-Migrationen
├── Score-Berechnung (Phase 7 befüllt, Code berechnet)
├── risk_level Mapping (score > 50 → AGGRESSIV, sonst KONSERVATIV)
├── Candidate-Freshness-Check
└── Alle Aggregationen (get_recent_trades(n=8) etc.)

AI macht NICHTS in Phase 2.
```

---

## Testing-Strategie

**Keine Netzwerk-Calls in Tests** — reine In-Memory oder Temp-File SQLite.

```python
# Fixture für alle db.py Tests:
@pytest.fixture
def db(tmp_path):
    d = Database(str(tmp_path / "test.sqlite"))
    d.run_migrations()
    return d
```

Abdeckung die Phase 2 benötigt:
- `test_db.py` — CRUD für alle 6 Tabellen, Cascade-Deletes, Index-Nutzung
- `test_state.py` — TTL-Logik (mit frozen time via `freezegun`), Stale-Check,
  leere Candidates-Datei, fehlende Datei
- `test_migrations.py` — Migration Runner, Idempotenz (zweimal ausführen = kein Error),
  Version-Tracking

---

## Offene Punkte / Entscheidungen — ENTSCHIEDEN (2026-05-22, Implementierungs-Session)

1. **Wo liegt die SQLite-Datei?** ✅ `~/trading-bot/data/trading_bot.sqlite`
   (Root-Level, außerhalb aller Phase-Ordner, gitignored). Pfad konfigurierbar
   via `init_db.py --db-path`.

2. **Wo liegen die JSON State Files?** ✅ `~/trading-bot/data/state/`
   (gleicher Root-`data/`-Ordner, gitignored). Konfigurierbar via
   `init_db.py --state-dir`.

3. **`data/` Root-Level oder in `phase2_persistence/`?** ✅ Root-Level `data/` —
   wird von Phase 5, 7, 8 gleichermaßen genutzt.

4. **Migration-Format:** ✅ Pure SQL-Files (`.sql`) als einzige DDL-Quelle;
   `schema.py` bleibt dünn (nur `_schema_version`-DDL + Pfad), kein dupliziertes
   Tabellen-DDL. Runner liest die `.sql`-Files.

5. **`freezegun` für Tests?** ✅ Nein. TTL/Freshness-Tests steuern die Zeit über
   explizite Timestamps in den State-Files (und ein patchbares `_utcnow()`).
   Phase 2 hat damit **null Runtime-Dependencies**, nur `pytest` (dev).

### Weitere Entscheidungen während der Implementierung

- **`get_risk_level()`-Grenze:** `> 50 → "AGGRESSIV"`, sonst `"KONSERVATIV"`.
  Der neutrale Start-Score (50) ist damit KONSERVATIV — konsistent mit dem
  Seed-Default `risk_level = "KONSERVATIV"`. (Die frühere Formulierung
  "score < 50 → KONSERVATIV" weiter oben hätte 50 als AGGRESSIV eingestuft und
  dem Seed widersprochen; Code ist Source of Truth.)
- **`get_current_score()`:** liest das jüngste `reward_pts.score_after`;
  Default `50.0`, solange keine Rewards existieren.
- **`decision_context`:** zusätzlicher Index `idx_decision_context_trade_id`
  ergänzt (FK wird per `trade_id` abgefragt) — im Konzept-DDL oben nicht gelistet.

---

## Nächster Schritt (Implementierungs-Chat) — ✅ ERLEDIGT (2026-05-22)

1. ✅ `phase2_persistence/` Verzeichnis angelegt
2. ✅ `migrations/001_initial.sql` — alle 6 Tabellen + Indizes
3. ✅ `persistence/schema.py` — dünn (`_schema_version`-DDL + Pfad)
4. ✅ `persistence/migrations.py` — Migration Runner (versioniert, idempotent)
5. ✅ `persistence/db.py` — Database Klasse komplett
6. ✅ `persistence/state.py` — StateManager komplett
7. ✅ `scripts/init_db.py` — einmalige Init (idempotent)
8. ✅ Tests für alle drei Module — **59 Tests** (Ziel ≥ 40 übererfüllt)
9. ✅ `README.md` für Phase 2
10. ✅ Phase-2 `CLAUDE.md`

---

## Session stopped — 2026-05-22

### Completed
- `phase2_persistence/` vollständig implementiert: `persistence/` Package
  (`timeutil.py`, `schema.py`, `defaults.py`, `migrations.py`, `db.py`,
  `state.py`, `__init__.py`), `migrations/001_initial.sql` (alle 6 Tabellen +
  Indizes), `scripts/init_db.py`, `tests/` (test_migrations/db/state).
- **59 Tests grün** (`pytest tests/ -v`), keine Netzwerk-Calls.
- `init_db.py` verifiziert: legt `data/trading_bot.sqlite` + `data/state/` an,
  migriert auf Version 1, seedet `ig_config_state`-Defaults; zweiter Lauf =
  sauberer No-Op. `data/` ist per `.gitignore` ausgeschlossen.
- README + CLAUDE.md für Phase 2 geschrieben; Konzept-Entscheidungen oben
  dokumentiert.

### Next
- Phase-2-Code committen (atomare Commits, kein `data/`).
- ROADMAP Phase-2-Checkboxen abhaken (erledigt) und root `CLAUDE.md`
  "Current state" auf Phase 3 umstellen — beim Phasenwechsel (Browser-Konzept-
  Session) entscheiden.
- Phase 3 (External Data / yFinance) Konzept vorbereiten.

### Open questions / blockers
- Keine. Phase 2 ist self-contained und ohne Broker-Verbindung lauffähig.
- Erinnerung: Live-/Netzwerktests sind Sache des Users — Phase 2 hat ohnehin
  keinen Netzwerkpfad, `pytest` + `init_db.py` decken alles ab.
