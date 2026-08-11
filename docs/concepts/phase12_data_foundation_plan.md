---
status: snapshot
purpose: Execution-ready Plan für Phase 12 (Datenfundament) — gelockte Entscheidungen D1–D20, Schritt-Sequenz 0–10 mit exakten Funktions-/Typnamen, Datei:Zeile-Ankern, Testlisten und Akzeptanzkriterien. Direkt an Sonnet übergebbar; Opus in der CLI muss nichts neu herleiten. Antwort auf die Durability-Anforderungen A–G aus PHASE11_DEFERRAL_HANDOVER.md §3.
read-when: als Bauplan jeder Phase-12-Session; vor jedem Schritt den betreffenden §6-Block + §9 (Drift-Liste) lesen
detail: L3
up: ../INDEX.md
updated: 2026-08-11
---

# Phase 12 — Datenfundament: Execution-Ready Plan (2026-08-11)

> **Autor:** Claude Code (Fable 5, Planungs-Session mit dem Nikinger, 2026-08-11).
> **Kontext-Quellen:** [`../../phase10_v3/PHASE11_DEFERRAL_HANDOVER.md`](../../phase10_v3/PHASE11_DEFERRAL_HANDOVER.md)
> (Anforderungen A–G), [`../../phase10_v3/ALLOWANCE_INCIDENT_2026-08-08.md`](../../phase10_v3/ALLOWANCE_INCIDENT_2026-08-08.md)
> (Kontingent + Restart-Gate), [`../../phase10_v3/DATA_SOURCE_STRATEGY_2026-08-11.md`](../../phase10_v3/DATA_SOURCE_STRATEGY_2026-08-11.md)
> (Richtung, mit §2.6-Korrektur), [`../architecture/data_foundation.svg`](../architecture/data_foundation.svg).
> **Alle Datei:Zeile-Anker** in diesem Plan sind gegen den Repo-Stand `c5d7ef1` (2026-08-11)
> verifiziert — **bei Ausführung erneut prüfen** (§9), nie blind übernehmen.
>
> **Korrigiert gegen Code (2026-08-11, Ausführungs-Session 1, Opus in der CLI):** drei kleine
> Anker-Abweichungen gefunden und hier direkt gefixt (Details: `phase12_data_foundation/CLAUDE.md`
> Session-Block 2026-08-11) — CLI-Subcommand ist `get-market-info`, nicht `market-info`;
> `run_scheduler.sh` hat 33 Zeilen, keine `$REPO_ROOT`-Variable, sondern `PROJECT_DIR`; §9.3s
> IG-Bar-Timestamp ist bestätigt **nicht** ISO (IG-eigenes `yyyy/MM/dd HH:mm:ss`). (D12s
> `scripts/verify_instrument.py:78-79`-Anker war bereits korrekt — Repo-Root, kein
> `phase9_universe/`-Präfix; kein Fix nötig.) Step 0a lässt sich mit `get_market_info`
> (projiziert, keine `openingHours`/Margin-Felder) nicht wie ursprünglich geplant beantworten
> — per Nikinger-Entscheidung per Roh-Dump-Skript gegen `_request()` gelöst (Ergebnis im
> Session-Block, inkl. `specialInfo`-Fund als besseres Wochenend-Signal als `openingHours`).

---

## §0 BLUF

Drei Datenwochen sind an drei Infrastruktur-Ausfällen gescheitert, nie an der Messung. Die
gemeinsame Wurzel: **das Datenfundament ist strukturell unzuverlässig** — eine Tatsache in drei
divergenten Speichern, die absichernde Hälfte von V2 nie eingeschaltet, Ressourcen entdeckt
statt modelliert, Messausfall wochenlang still.

Phase 12 baut das Fundament neu (**Überweg C — Maximalweg, Nikinger-Entscheidung
2026-08-11**, sequenziell):

1. **Instrument-Registry** — `instrument_universe` wird die **eine** Wahrheit für
   Instrument-Fakten; das Symbol-Mapping wird **abgeleitet + code-verifiziert** statt
   deklariert; „keine Quelle" ist ein typisierter, lauter Zustand.
2. **BarService** — der **eine** Bar-Pfad für alle Konsumenten, um die bereits gebaute
   `ChainedBarProvider`-Kette herum, mit persistentem Budget-Ledger (IG-Punkte) und
   Provenienz an jeder Bar.
3. **Bar-Archiv** (`data/bars.sqlite`) — **jede** je gefetchte Bar wird persistiert
   (Write-Through, quellen­agnostisch); Messungen werden replaybar und offline-prüfbar.
4. **Recorder** — ein eigener, kleiner Daemon (yF-only, **keine IG-Session** — §2 D14),
   der während der Handelszeiten kontinuierlich Bars ins Archiv schreibt, unabhängig vom
   Zustand des Trading-Bots.
5. **Mess-Heartbeat** — ein Tag ohne Messung fällt am selben Tag auf, nicht am Freitag.
6. **Lightstreamer-Mitschrieb** — als Step 10 mitgeplant (gleiches Archiv, `source='ls'`),
   gebaut **erst nach** bestandener Beweiswoche.

**Done-Kriterium der Phase:** eine echte Beweis-Messwoche läuft durch, ohne dass
Infrastruktur die Messung tötet (§7). Die WI-2-*Auswertung* selbst bleibt
Phase-11-Wiederaufnahme.

---

## §1 Rahmen, Arbeitsteilung, Gates (unverändert bindend)

- **Bot-berührende Steps nur am Wochenende** (Bot steht, Markt zu). Wochentags docs-only /
  read-only (`mode=ro`-URI auf `data/`), keine Migration, kein Scheduler-Restart.
  Ausnahme: das **neue** `phase12_data_foundation/`-Paket selbst (eigene Dateien, eigene
  Tests, berührt den laufenden Bot nicht) darf werktags gebaut werden, solange kein
  bestehender Phasen-Code editiert und nichts in `data/` geschrieben wird. Die
  Cross-Phase-Edits (§6 Steps 3/4/7) sind Wochenend-Arbeit.
- **Live-/Netz-/Kosten-Tests macht der Nikinger** (Memory `feedback_live_testing`):
  Claude preppt Kommando + Kostenschätzung, fragt vorher.
- **Restart-Gate** (ALLOWANCE_INCIDENT §6) gilt unverändert: Universe-Reset +
  Scheduler-Restart erst nach einem **beobachteten** `remainingAllowance`. Step 8
  operationalisiert das als Code (Gate im Reset-Skript), nicht als Disziplin.
- **IG-Session-Regel:** genau **ein** Prozess hält eine IG-REST-Session
  (Parallel-Login-Falle, Memory `reference_ig_parallel_login_trap`). Konsequenz in §2 D14.
- **Advisor-Regel** (Root-`CLAUDE.md`): konsultieren bei [VERIFY]-Mismatch, nach 2–3
  gescheiterten Fix-Versuchen, vor der Abnahme eines Wochenend-Blocks. Sonst nicht.
- **Kein LLM in dieser Phase.** Das gesamte Fundament ist 100 % Code (Bauprinzip). Wer hier
  ein LLM „mappen/prüfen/schätzen" lassen will → stop.

---

## §2 Gelockte Entscheidungen (D1–D20)

> Gelockt heißt gelockt: nicht mid-implementation re-litigieren. Widerspricht neue Evidenz
> einer Entscheidung → Befund an den Nikinger, nie still abweichen.

| # | Entscheidung | Begründung / Anker |
|---|---|---|
| **D1** | **Überweg C (Maximalweg), sequenziell:** Registry + BarService + Archiv + Recorder (v1 = yF), LS-Mitschrieb als Step 10 nach der Beweiswoche. Ein gemeinsamer Datenspeicher (Archiv), der sich aus allen Quellen deckt. | Nikinger 2026-08-11; zwei Reframes starben an halb gebauten Datenschichten. |
| **D2** | **Nummerierung: Phase 12 = Datenfundament, alter „V4" → Phase 13.** Step 0b zieht die fünf sichtbaren Dokumente nach (Root-`CLAUDE.md`, `ROADMAP.md`, `README.md`, `ARCHITECTURE.md`, `docs/INDEX.md`). | Nikinger 2026-08-11; Präzedenzfall 2026-08-01. |
| **D3** | **Neues Verzeichnis `phase12_data_foundation/`, Paket `data_foundation`**, eigene `tests/`, eigenes `pyproject.toml`/`requirements.txt`/`README.md`/`CLAUDE.md`, editable-Install via `scripts/dev_install.sh` (Kette erweitern). Phasen-Isolation wie `universe`: `import data_foundation.*` zieht **nichts** cross-phase am Modul-Top (lazy in Funktionskörpern). | Repo-Konvention (P9-Muster). |
| **D4** | **Bar-Archiv in eigener SQLite `data/bars.sqlite`** (nicht `trading_bot.sqlite`): eigener Store `BarArchive` (UniverseStore-Muster, eigene Connection, `ensure_schema`, kein `persistence`-Import). Schreiblast getrennt vom Trading-DB-Locking; Archiv-Wartung fasst nie Trading-Daten an. | Nikinger 2026-08-11. |
| **D5** | **Eine Wahrheit pro Instrument-Fakt = `instrument_universe`** (erweitert per Migration 006). `discovery.KNOWN_YF_TICKERS` wandert als Seed-Kandidatenliste nach `data_foundation/symbols.py`; `discovery.py` schreibt `yf_ticker` **nicht mehr** (immer `None` bei Neuanlage). `TickerMapper._MAP` bleibt nur für bare P3-Operator-Skripte, mit Deprecation-Kommentar („Seed/Operator-Fallback, nie Laufzeit-Wahrheit"). **Abnahme-Grep (Kriterium A):** genau **ein** schreibender Ort für `yf_ticker` (`UniverseStore.set_symbol`, gerufen nur vom `SymbolResolver`). | Handover §2.3/§3 A; Anker: `phase9_universe/universe/discovery.py:57-70,240`, `phase3_external_data/external_data/ticker_map.py:31-51`, Laufzeit-Registrierung `phase8_scheduler/scripts/wiring.py:203-210` (bleibt der einzige Lese-Pfad). |
| **D6** | **Symbol-Mapping abgeleitet + code-verifiziert (kein LLM):** `SymbolResolver` generiert Kandidaten (Seed-Tabelle + Namens-Heuristik) und **verifiziert deterministisch** per Preisvergleich IG-Snapshot (`broker.get_price`, kein Historien-Kontingent) vs. yF-Last, marktzeiten­bewusst, Toleranz `2.0 %` (v1, tunable). Ergebnis + Zeitstempel in Registry-Spalten. Läuft **wiederkehrend** (im `universe_refresher`-Pass), nicht einmalig. | Handover §3 B/C: „abgeleitet, nicht deklariert" + „Divergenz erkennbar". |
| **D7** | **Typisierte Degradierung:** neue Spalte `data_source_status` ∈ `{'ok','unverified','no_source','no_intraday_source','mismatch'}`, Default `'unverified'`. **Messung (Paper/Shadow) läuft ausschließlich über Epics mit `'ok'`** (`UniverseStore.measurable_universe()`). Wochenend-Instrumente (SUNDAX & Co.) → `'no_intraday_source'` (für ihr Handelsfenster existiert strukturell keine yF-Quelle) — typisiert, laut (Event), von Messung ausgeschlossen, bis Step 10 (LS) sie deckt. | Nikinger 2026-08-11; Handover §3 D. |
| **D8** | **Alle Bar-Konsumenten über EINE Naht:** `BarService` implementiert das bestehende `BarProvider`-Protocol (`phase3_external_data/external_data/providers.py:28-31`) und wird (a) als `bar_provider` in den Research-Fetcher injiziert (bestehende Naht: `fetcher.py:349-376,433-453`) und (b) als Fenster-Leser in den Paper-Tracker (`bar_fetch`-Closure ersetzt). Der direkte `broker.get_ohlcv`-Call im Tracker (`wiring.py:494-529`) **fällt weg**. | Handover §2.4; DATA_SOURCE_STRATEGY §3. |
| **D9** | **Archiv-first, Write-Through, Provenienz:** `BarService` liest zuerst das Archiv; nur bei Lücke geht er in die Kette (yF gratis zuerst nutzbar, IG budget-gated); **jede** extern geholte Bar wird mit `source` ins Archiv geschrieben. Rückgabe-Bars tragen `source` durch bis zur Messzeile (D11). | Handover §3 E; ALLOWANCE_INCIDENT §7 („Roh-Bars werden nirgends persistiert"). |
| **D10** | **Ressourcen modelliert:** `SourceBudget` mit deklariertem `QuotaModel` (IG: 10 000 Punkte / 7-Tage-Festfenster; Zahl **bei Ausführung** gegen beobachtetes `totalAllowance` bestätigen), persistentem Spend-Ledger (`source_spend` in `bars.sqlite`), Beobachtungs-Tabelle (`allowance_observations`, gespeist aus dem `allowance`-Objekt jeder erfolgreichen `/prices`-Antwort — `ig_adapter.py:436-439`), Reserve-Floor, und `can_spend(points)`-**Vorhersage** vor jedem IG-Fetch. Ersetzt die Platzhalter `_PAPER_ALLOWANCE_FLOOR`/`_PAPER_BUDGET_COOLDOWN_MIN`-Mechanik (`wiring.py:429-461`) strukturell. | Handover §3 F; ALLOWANCE_INCIDENT. |
| **D11** | **Provenienz an jeder Messzeile:** Migration 006 ergänzt `paper_trades.resolution_source` (TEXT, z. B. `'yf'`, `'ig'`, `'ig+yf'`, `'ls'`); `PaperTradeTracker._resolve_group` berechnet sie aus den tatsächlich benutzten Bars und reicht sie an `mark_resolved` weiter (additive Parameter). `scripts/abstain_report.py --paper` gruppiert danach. | Handover §3 E („SL/TP-Verteilung nach Quelle filterbar"). |
| **D12** | **Divergenz-Check verdrahten — im Scheduler-Prozess:** 1×/Tag pro `'ok'`-Epic ein budgetiertes IG-Sample (`MINUTE_5 × 3` = 3 Punkte, dieselbe Größe wie die Promotion-Probe, `scripts/verify_instrument.py:78-79`), verglichen gegen die Archiv-yF-Bars desselben Fensters → `quote_divergence`-Event (`scheduler/observability.py:130-140`, existiert). Persistenter Drift ⇒ `data_source_status='mismatch'` (laut). | Handover §3 C/E; DATA_SOURCE_STRATEGY §5.2. |
| **D13** | **Mess-Heartbeat (G):** (a) Runner bekommt eine additive Naht `daily_health_check: Callable | None = None` (Default `None` = bit-identisch), gerufen im POST_WINDOW-Zweig — schreibt ein `measurement_heartbeat`-Event (Zählwerte: Bars heute, Pairs geöffnet, Pairs aufgelöst, typisierte Ausfälle) und loggt CRITICAL bei Null-Messung trotz aktivem Shadow-Schedule. (b) Operator-Skript `scripts/data_health.py` (read-only, exit ≠ 0 bei Totalausfall) für den täglichen Blick. | Handover §3 G („drei Wochen Totalausfall ohne Alarm sind der eigentliche Skandal"). |
| **D14** | **Recorder = eigener Prozess, yF-only, KEINE IG-Session.** Begründung: zwei gleichzeitige IG-REST-Logins clobbern sich die Tokens (Parallel-Login-Falle) — alles IG-seitige (Divergenz-Samples, Proben, Tracker-Fallback) bleibt im Scheduler-Prozess, der die eine warme Session hält. Recorder startbar (1) standalone via `scripts/run_recorder.sh` und (2) automatisch aus `phase8_scheduler/scripts/run_scheduler.sh` (PID-File-Guard, doppelstart-sicher, `nohup … &` vor dem `exec`ᵃ) — „damit es weniger schnell vergessen wird" (Nikinger). | Nikinger 2026-08-11 + Session-Befund. |

> ᵃ **Korrektur (2026-08-11):** `run_scheduler.sh` hat 33 Zeilen, keine `$REPO_ROOT`-Variable
> (sondern `PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"`), letzte Zeile
> `exec python -m scheduler.run "$@"`. Der `nohup … &` gehört unmittelbar davor.
| **D15** | **Recorder-Betrieb v1:** pollt alle `recorder_interval_s` (Default 300 s) für alle `measurable_universe()`-Epics 1-Minuten-Bars via Phase-3-Fetcher (`get_bars(epic, resolution="1m", count=30)` — Off-Hours-Disziplin, RateLimiter + Circuit inklusive, `fetcher.py`), Dedup über den Archiv-PK (`INSERT OR IGNORE`). Eigener Heartbeat-State `data/state/recorder_state.json` (atomic) + `recorder_heartbeat`-Event. Kein Broker-Import, kein LLM. | D14; yF-1m-Fenster ~7 Tage reicht bequem (Handover-bestätigt). |
| **D16** | **Der Momentum-VETO bleibt unangetastet:** er sourct weiterhin direkt aus P1-IG-Echtzeit-Bars (`phase5_execution/execution/vetos.py`), **niemals** aus BarService/Archiv/yF. BarService ist Research-/Mess-Datenpfad, nie Safety-Input. Ebenso unberührt: Gates, Sizing, P6, P7. | Root-Hard-Rules; P3-`CLAUDE.md`-Notice. |
| **D17** | **Flag-Bereinigung:** `SchedulerConfig.enable_ig_bars` (`scheduler/config.py:150`) — gebaut, nie gelaufen — wird **ersetzt** durch `enable_bar_service: bool = True` (ein Flag für die neue eine Naht). Das CLI-Arm (`scheduler/run.py`, Flag `--enable-ig-bars` — bei Ausführung verifizieren) wird mitgezogen. Kein totes Flag zurücklassen. | Handover §2.4 (die dunkle Hälfte darf sich nicht wiederholen). |
| **D18** | **Restart-Gate als Code:** `scripts/reset_universe.py` verweigert den Reset, solange keine **frische** (< 24 h) Zeile in `allowance_observations` mit `remaining > reserve` existiert. Beobachtungen schreibt `scripts/probe_allowance.py` (wrappt den bekannten CLI-Einzeiler, 5 Punkte, bucht den Spend gleich mit). Kein Hand-SQL mehr. | ALLOWANCE_INCIDENT §6; Handover §4.3/§4.4. |
| **D19** | **PaperEngine bekommt eine additive `epic_filter`-Naht** (`Callable[[str], bool] | None = None`, Default `None` = bit-identisch): das Wiring injiziert `data_source_status=='ok'`-Gating für `on_debate_abstain` **und** `open_scheduled_pairs`, ohne dass `abstain_lessons` die Registry kennt (Phasen-Isolation). | D7; `phase10_v3/abstain_lessons/paper.py:332-347,398-439`. |
| **D20** | **LS-Mitschrieb (Step 10) ist gated auf die bestandene Beweiswoche** und beginnt mit einer eigenen Detail-Design-Session (offene Kernfrage: LS braucht eine IG-Session → Prozess-Platzierung, s. §6 Step 10). Bis dahin bleiben Wochenend-Epics typisiert unmessbar (D7) — gewollt, dokumentiert, laut. | Nikinger 2026-08-11 („beides, sequenziell"). |

---

## §3 Zielarchitektur (Komponenten + Datenfluss)

```
                          ┌────────────────────────────────────────────────┐
                          │  instrument_universe  (Migration 006)          │
                          │  = DIE Wahrheit: epic, name, yf_ticker,        │
                          │    point_value, data_source_status,            │
                          │    symbol_source, symbol_checked_at, …         │
                          └───────▲───────────────────────┬────────────────┘
        einziger Writer:          │                       │ einziger Lese-Pfad:
        SymbolResolver ───────────┘                       │ wiring registriert Mapper
        (wiederkehrend im                                 ▼ aus active_universe()
         universe_refresher)                     Research / Sizing / Tracker
─────────────────────────────────────────────────────────────────────────────────────
  Scheduler-Prozess (hält DIE IG-Session)          Recorder-Prozess (yF-only, D14)
  ┌─────────────────────────────────────┐          ┌──────────────────────────────┐
  │ BarService  (D8/D9)                 │          │ Recorder (D15)               │
  │  Archiv-first → Kette:              │          │  alle 300s: yF-1m-Bars für   │
  │   [BudgetedIG (D10) → yF]           │          │  measurable_universe()       │
  │  Write-Through + source-Tag         │          │  → INSERT OR IGNORE          │
  │ Divergenz-Sampler (D12, 1×/Tag)     │          │  Heartbeat-State + Event     │
  │ daily_health_check (D13)            │          └───────────────┬──────────────┘
  └───────────────┬─────────────────────┘                          │
                  ▼                                                ▼
        ┌───────────────────────────────────────────────────────────────┐
        │ data/bars.sqlite  —  BarArchive (D4)                          │
        │  bars(epic, resolution, ts_utc, OHLCV, source, fetched_at)    │
        │  source_spend · allowance_observations                        │
        └───────────────────────────────────────────────────────────────┘
                  │ window()                       ▲ (Step 10: source='ls')
                  ▼                                │
        PaperTradeTracker → paper_trades.resolution_source (D11)
```

Unverändert daneben: Momentum-VETO ← P1-IG-Bars direkt (D16); Promotion-Probe
(`verify_instrument.check_ig_side`) bleibt IG-seitig im Scheduler-Prozess, künftig
budget-gebucht (Step 4).

---

## §4 Schemata (exakt)

### 4.1 `data/bars.sqlite` — von `BarArchive.ensure_schema()` angelegt (kein P2-Migrationslauf; eigene Datei, D4)

```sql
CREATE TABLE IF NOT EXISTS bars (
    epic        TEXT NOT NULL,
    resolution  TEXT NOT NULL,          -- '1m' | '5m'  (Phase-3-Namen, NICHT IG-Namen)
    ts_utc      TEXT NOT NULL,          -- Bar-Open, ISO 8601 UTC ms 'Z' (normalisiert, §9.3)
    open REAL NOT NULL, high REAL NOT NULL, low REAL NOT NULL, close REAL NOT NULL,
    volume      REAL,
    source      TEXT NOT NULL,          -- 'ig' | 'yf' | 'ls'
    fetched_at  TEXT NOT NULL,
    PRIMARY KEY (epic, resolution, ts_utc, source)
);
CREATE INDEX IF NOT EXISTS idx_bars_epic_res_ts ON bars(epic, resolution, ts_utc);

CREATE TABLE IF NOT EXISTS source_spend (       -- D10: Ledger, nur echte externe Calls
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    source TEXT NOT NULL,                        -- 'ig' (yF wird nicht gebucht: kein Punktemodell)
    ts_utc TEXT NOT NULL,
    points INTEGER NOT NULL,                     -- IG-Datenpunkte = gelieferte Bar-Anzahl
    kind   TEXT NOT NULL                         -- 'tracker'|'probe'|'sample'|'research'|'manual'
);
CREATE TABLE IF NOT EXISTS allowance_observations (   -- D10/D18: beobachtete IG-Antworten
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    observed_at TEXT NOT NULL,
    total INTEGER, remaining INTEGER, expiry TEXT     -- Feldnamen des allowance-Objekts §9.5
);
```

### 4.2 Migration `phase2_persistence/migrations/006_phase12_data_foundation.sql` (additiv; Nummer §9.7 verifizieren)

```sql
-- Phase 12 (Datenfundament) — Registry-Erweiterung + Mess-Provenienz. Additiv only.
ALTER TABLE instrument_universe ADD COLUMN data_source_status TEXT NOT NULL DEFAULT 'unverified';
ALTER TABLE instrument_universe ADD COLUMN symbol_source     TEXT;   -- 'seed'|'resolver'|'operator'|NULL
ALTER TABLE instrument_universe ADD COLUMN symbol_checked_at TEXT;
ALTER TABLE paper_trades        ADD COLUMN resolution_source TEXT;   -- 'yf'|'ig'|'ig+yf'|'ls'|NULL(legacy)
```

Bestehende Zeilen starten `'unverified'` — korrekt: nichts ist verifiziert, bis der
Resolver einmal gelaufen ist. Alte `paper_trades`-Zeilen behalten `NULL` (ehrlich: Provenienz
unbekannt).

### 4.3 Neue/geänderte Spaltenkonsumenten

- `universe/models.py::UniverseRecord`: +3 Felder (`data_source_status: str`,
  `symbol_source: str | None`, `symbol_checked_at: str | None`) inkl. `to_row`/`from_row`.
- `universe/store.py::UniverseStore`: neu `set_symbol(epic, yf_ticker, *, symbol_source,
  status) -> None` (der **einzige** `yf_ticker`-Writer, D5) und `measurable_universe() ->
  list[UniverseRecord]` (`status='active' AND data_source_status='ok'`).
- `abstain_lessons/paper_store.py`: `_CREATE_TABLE` + `resolution_source`-Spalte (ans Ende,
  `paper_store.py:19-40`), `mark_resolved(…, resolution_source: str | None = None)`
  (`paper_store.py:94`), `PaperTrade` (+`resolution_source: str | None = None`-Feld,
  `to_row`/`from_row` **ans Ende anhängen** — Positionslogik, §9.10).

---

## §5 Budgetmodell (Anforderung F, konkret gerechnet)

| Verbraucher | Punkte/Call | Kadenz | Punkte/Woche (5 Handelstage) |
|---|---|---|---|
| Promotion-Probe (`check_ig_side`, `MINUTE_5×3`) | 3 | ≤ 22 Epics × ~2 Runden/Tag | ≤ 660 |
| Divergenz-Sample (D12) | 3 | ~8 `'ok'`-Epics × 1/Tag | ~120 |
| Allowance-Probe (`probe_allowance.py`) | 5 | 1/Tag | 25 |
| Tracker | **0** | Archiv/yF-only (D8/D9) | 0 |
| Research-`get_bars` IG-Leg | 0 im Normalfall | Archiv-first; IG nur bei Lücke + `can_spend` | Reserve |
| **Σ geplant** | | | **< 1 500 von 10 000** |

Reserve-Floor v1: `1 500` Punkte (ersetzt den 2 000-Platzhalter **erst nach** beobachtetem
`totalAllowance`, §9.5/§9.11). `can_spend(points)` = `remaining_estimate() - points >
reserve`. `remaining_estimate()` = min(eigene Fensterrechnung, letzte Beobachtung) —
Beobachtung schlägt Rechnung.

---

## §6 Schritt-Sequenz

> Pro Step: **Dateien → exakte Namen → Anker → Tests → Akzeptanz.** Reihenfolge ist
> verbindlich. Jeder Step endet mit grünem `pytest <phase>/tests -v` (per-Phase separat,
> Memory `reference_running_phase_tests`) + Commit + Session-Block-Update.

### Step 0 — Operator-Live-Check + Housekeeping (docs-only / read-only; werktags erlaubt)

**0a — Nikinger-Live-Check (Gate für Step 3, Handover §4.2) — ✅ erledigt 2026-08-11:**
`get_market_info` (CLI-Subcommand tatsächlich `get-market-info`, nicht `market-info`)
**projiziert** die IG-Antwort auf eine feste `MarketInfo`-Shape ohne `openingHours`/Margin
(`ig_adapter.py:479-513`) — der ursprünglich geplante CLI-Weg hätte keine der beiden
Step-0a-Fragen beantwortet. Stattdessen per Nikinger-Entscheidung ein Roh-Dump-Skript
gegen `broker._request("GET", f"/markets/{epic}", version="3", auth=True)` (kein
Historien-Kontingent, ein Login, drei Epics). Ergebnis + Empfehlung für Step 3
(`specialInfo`-Substring statt/zusätzlich zu `openingHours` als Wochenend-Signal, B3-Margin-
Felder gescoutet): `phase12_data_foundation/CLAUDE.md` Session-Block 2026-08-11.
**0b — Housekeeping:** (1) Nummerierung D2 in den fünf Dokumenten nachziehen + diesen Plan
in `docs/INDEX.md` eintragen (eine Zeile, selber Commit). (2) Legacy-Grep-Ritual
(`grep -rn -i "turbo\|CALL/PUT\|pre_trade_option_check\|expected hold" --include="*.py" --include="*.md"`
→ erwartet sauber bis auf die bekannten annotierten Treffer). (3) .md↔Code-Verify der
Phasen-Status-Zeilen. (4) Regression-Baseline: volle per-Phase-Suite, Zählstand
dokumentieren (zuletzt gemeldet 1 336 grün, §9.8).
**0c — Skeleton:** `phase12_data_foundation/` mit `CLAUDE.md` (Phasenkopf nach
P9/P10-Muster: Mission, Bauprinzip, Scope, Modul-Tabelle, Session-Block), leerem Paket,
`pyproject.toml` (setuptools, Paket `data_foundation`), `requirements.txt` (leer außer
pytest — Runtime-Deps kommen aus den installierten Phasen), Eintrag in
`scripts/dev_install.sh`.
**Akzeptanz:** 0a-Ergebnis dokumentiert; fünf Docs + INDEX aktualisiert; Baseline grün.

### Step 1 — `BarArchive` (WE-frei baubar, berührt nichts Bestehendes)

**Dateien:** `data_foundation/models.py`, `data_foundation/exceptions.py`,
`data_foundation/archive.py`, `tests/test_archive.py`.
**Namen:**
```python
# models.py
@dataclass(frozen=True)
class Bar: epic: str; resolution: str; ts_utc: str; open: float; high: float; low: float; close: float; volume: float | None; source: str; fetched_at: str
SOURCE_IG = "ig"; SOURCE_YF = "yf"; SOURCE_LS = "ls"
DS_OK = "ok"; DS_UNVERIFIED = "unverified"; DS_NO_SOURCE = "no_source"; DS_NO_INTRADAY = "no_intraday_source"; DS_MISMATCH = "mismatch"
def normalize_bar_ts(raw: str) -> str  # → ISO 8601 UTC ms 'Z'; §9.3 (IG-Format live prüfen)
# exceptions.py
class DataFoundationError(Exception)  # code/retryable-Muster wie universe.exceptions
class ArchiveError(DataFoundationError); class BudgetError(DataFoundationError); class ResolverError(DataFoundationError)
# archive.py
class BarArchive:
    def __init__(self, db_path: str | Path) -> None
    def ensure_schema(self) -> None
    def insert_bars(self, bars: Sequence[Bar]) -> int              # INSERT OR IGNORE; Rückgabe: neu
    def window(self, epic: str, resolution: str, start_utc: str, end_utc: str,
               *, prefer: tuple[str, ...] = ("ig", "ls", "yf")) -> list[Bar]
               # ein Eintrag pro ts_utc; bei Mehrquellen gewinnt die prefer-Reihenfolge
    def coverage_ratio(self, epic: str, resolution: str, start_utc: str, end_utc: str) -> float
               # vorhandene distinkte Bar-Minuten / erwartete Minuten im Fenster (naiv, ohne Handelspausen — dokumentiert)
    def latest_ts(self, epic: str, resolution: str) -> str | None
    def bars_written_since(self, ts_utc: str) -> int               # Heartbeat-Zähler (D13)
    def close(self) -> None
```
**Tests (~10):** Schema-Anlage idempotent · Insert-Dedup (identische Bar 2× → 1) ·
`window`-Grenzen inklusiv/exklusiv · Quellen-Präferenz (ig schlägt yf bei gleicher Minute) ·
`coverage_ratio` 0/teil/voll · `latest_ts` leer→`None` · `bars_written_since` ·
`normalize_bar_ts` (IG-Beispielformat, yF-Beispielformat, bereits-normalisiert) ·
Fremd-Quelle-String wird abgelehnt (`ArchiveError`).
**Akzeptanz:** `pytest phase12_data_foundation/tests -v` grün; `import data_foundation.*`
zieht nichts cross-phase (Import-Test nach P9-Muster).

### Step 2 — `SourceBudget` (WE-frei baubar)

**Dateien:** `data_foundation/budget.py`, `tests/test_budget.py`.
**Namen:**
```python
@dataclass(frozen=True)
class QuotaModel: source: str; points_per_window: int | None; window_days: int | None
IG_QUOTA_V1 = QuotaModel("ig", 10_000, 7)   # §9.5: gegen beobachtetes totalAllowance bestätigen
class SourceBudget:
    def __init__(self, db_path: str | Path, model: QuotaModel, *, reserve_points: int = 1_500,
                 now_fn: Callable[[], datetime] = ...) -> None      # nutzt BarArchive-Connection-Muster
    def record_spend(self, points: int, kind: str) -> None
    def record_allowance(self, total: int | None, remaining: int | None, expiry: str | None) -> None
    def window_start(self) -> str | None      # aus jüngster expiry-Beobachtung rückgerechnet; None → eigene Rechnung ab erstem Spend
    def spent_in_window(self) -> int
    def remaining_estimate(self) -> int | None   # min(Modell − spent, letzte Beobachtung.remaining − seitherige Spends)
    def can_spend(self, points: int) -> bool     # False auch bei estimate None UND model None? Nein: model gesetzt ⇒ rechenbar
    def predicted_exhaustion_days(self, daily_rate: float) -> float | None
```
**Tests (~9):** Spend akkumuliert im Fenster · Fensterrollover via `expiry`-Beobachtung ·
`can_spend` respektiert Reserve · Beobachtung < eigene Rechnung ⇒ Beobachtung gewinnt ·
Spends nach Beobachtung werden abgezogen · `predicted_exhaustion_days` · leerer Ledger ·
`record_allowance` mit `None`-Feldern (erschöpfter Zustand liefert kein Objekt) ·
Persistenz über zwei Instanzen (Restart-Fall).
**Akzeptanz:** Der 08-03-Vorfall wäre modellierbar gewesen: Test rechnet 33 Fetches × 300
nach und zeigt `can_spend(300) == False` **vor** dem erschöpfenden Call (F-Kriterium als Test).

### Step 3 — Migration 006 + Registry-Erweiterung + `SymbolResolver` (Cross-Phase: **Wochenende**)

**Dateien:** `phase2_persistence/migrations/006_phase12_data_foundation.sql` (§4.2),
`phase9_universe/universe/models.py` (+3 Felder), `phase9_universe/universe/store.py`
(`set_symbol`, `measurable_universe`), `phase9_universe/universe/discovery.py`
(`KNOWN_YF_TICKERS`-Tupel + `_lookup`-Nutzung für `yf_ticker` **entfernen**; Neuanlage mit
`yf_ticker=None`; `KNOWN_VOLUME_PROXIES` bleibt vorerst — Volume ist kein Messpfad),
`data_foundation/symbols.py`, `tests/test_symbols.py`, P2-/P9-Test-Updates.
**Namen:**
```python
# symbols.py
SEED_SYMBOL_CANDIDATES: tuple[tuple[str, str], ...]  # verbatim discovery.KNOWN_YF_TICKERS (discovery.py:57-70)
                                                     # + ("US 500","^GSPC"),("US Tech 100","^NDX"),
                                                     #   ("Wall Street","^DJI"),("UK 100","^FTSE")   ← die 4 fehlenden Werktags-Klassen
def candidates_for(name: str) -> list[str]           # case-insensitive Substring, Reihenfolge = Tabellenreihenfolge
def is_weekend_instrument(name: str | None, market_info: Mapping[str, Any] | None) -> bool
    # v1-Heuristik: "wochenend"/"weekend" im Namen ODER Epic-Segment "SUN";
    # Step-0a-Ergebnis kann sie durch echte IG-Öffnungszeiten-Felder ersetzen (§9.2)
def price_agreement(ig_mid: float, yf_last: float, *, tolerance_pct: float = 2.0) -> bool
class ResolverReport:  # dataclass: checked, verified, no_source, no_intraday, mismatch, unverified: list[str]
class SymbolResolver:
    def __init__(self, store: Any, quote_fetch: Callable[[str], Mapping[str, float]],
                 yf_last_fetch: Callable[[str], float | None],
                 *, market_open_fn: Callable[[], bool] = ...,   # lazy: external_data.market_hours.is_market_open
                 now_fn: Callable[[], datetime] = ...) -> None
    def resolve_epic(self, rec: Any) -> str          # → neuer data_source_status; schreibt via store.set_symbol
    def resolve_universe(self) -> ResolverReport     # über active + discovered; nie raises (fail-soft je Epic)
```
**Ablauf `resolve_epic` (deterministisch):** Wochenend-Instrument → `no_intraday_source`
(auch bei vorhandenem Symbol — die Quelle liefert im Handelsfenster nichts). Kein Kandidat →
`no_source`. Kandidat + Markt offen + `price_agreement(ig_mid, yf_last)` → `ok` (Symbol
gesetzt, `symbol_source='resolver'` bzw. `'seed'` wenn aus DB bestätigt). Kandidat + Markt
zu → Status bleibt/`unverified` (kein Fehlversuch gebucht — „wir haben nichts gelernt").
Verifiziertes Symbol widerspricht später wiederholt (`price_agreement` False an ≥ 2
aufeinanderfolgenden Checks bei offenem Markt) → `mismatch` + lautes Event. Ein bereits
vom Operator gesetztes Symbol (`symbol_source='operator'`) wird nie überschrieben, nur
geprüft.
**Tests (~15):** UniverseRecord-Roundtrip mit neuen Feldern · Migrations-Versionstest (P2:
`_version_5→6`-Hebungen analog 004-Muster, `phase10_v3/CLAUDE.md` Verified-Anker 3) ·
`set_symbol` schreibt alle 4 Felder + `updated_at` · `measurable_universe` filtert korrekt ·
`candidates_for` Treffer/Nichttreffer · Wochenend-Heuristik (SUNDAX-Name, SUN-Epic, normale
Namen) · Preistoleranz-Grenzfälle · alle 5 Statusübergänge · Operator-Symbol unantastbar ·
Markt-zu bucht keinen Fehlversuch · discovery legt `yf_ticker=None` an (P9-Testupdate) ·
**Grep-Test (Kriterium A):** Quelltext-Scan, dass `yf_ticker` außerhalb `store.set_symbol`
+ `seed_curated` nirgends geschrieben wird.
**Akzeptanz:** Anforderung A+B als Test beweisbar: ein frisch entdecktes Instrument mit
gewöhnlichem Namen wird **ohne Code-Edit** vollständig beschrieben oder trägt einen
typisierten Unvollständig-Status. Volle Regression grün.

### Step 4 — `BarService` + Tracker-/Research-Umverdrahtung (Cross-Phase: **Wochenende**)

**Dateien:** `data_foundation/service.py`, `tests/test_service.py`,
`phase10_v3/abstain_lessons/paper.py` (+`resolution_source`-Durchreichung),
`phase10_v3/abstain_lessons/paper_store.py` (§4.3), `phase10_v3/abstain_lessons/paper.py::PaperEngine`
(+`epic_filter`, D19), `phase8_scheduler/scripts/wiring.py` (Kern-Rewire),
`phase8_scheduler/scheduler/config.py` (D17), `phase8_scheduler/scheduler/run.py` (Flags),
P8-/P10-Test-Updates.
**Namen:**
```python
# service.py
class BudgetedIGBarProvider:                      # BarProvider-Protocol (providers.py:28-31)
    def __init__(self, broker: Any, budget: Any, *, spend_kind: str = "research",
                 health_sink: Callable[[dict], None] | None = None) -> None
    def get_bars(self, epic: str, *, resolution: str, count: int) -> list[PriceBar] | None
        # vor dem Call: budget.can_spend(count) sonst None + 'budget_veto'-Event;
        # nach Erfolg: record_spend(len(bars)) + record_allowance(aus env.data['allowance'], ig_adapter.py:436-439)
class BarService:                                 # implementiert BarProvider (Research-Naht)
    def __init__(self, archive: BarArchive, chain: Any, budget: Any,
                 *, health_sink=None, now_fn=...) -> None
    def get_bars(self, epic: str, *, resolution: str, count: int) -> list[PriceBar] | None
        # Archiv-first (letzte count Bars, falls coverage ausreichend), sonst chain + Write-Through
    def get_window(self, epic: str, resolution: str, start_utc: str, end_utc: str) -> list[dict[str, Any]]
        # Tracker-Naht: dicts {timestamp, open, high, low, close, source};
        # Archiv-first; Lücke → chain.get_bars (yF-Leg gratis) → Write-Through → erneut lesen;
        # bleibt die Lücke: zurückgeben was da ist (der Tracker entscheidet typisiert weiter, paper.py:228-270)
```
**Wiring-Rewire (`phase8_scheduler/scripts/wiring.py`):**
- Neu `_build_data_foundation(broker) -> tuple[BarService, SourceBudget, BarArchive]`
  (lazy imports; `bars.sqlite`-Pfad analog `_DB_PATH`-Konstanten, `wiring.py:75-87`:
  `_BARS_DB_PATH = _DATA_DIR / "bars.sqlite"`).
- `_build_market_data` (`wiring.py:132-178`): der `enable_ig_bars`-Zweig wird durch
  `enable_bar_service` ersetzt; die Kette wird `[("ig", BudgetedIGBarProvider(broker, budget)),
  ("yf", YFinanceBarProvider(raw_fetcher))]`, außen `BarService` als `bar_provider`.
- `_build_paper_tracker` (`wiring.py:464-568`): `bar_fetch(epic)` wird zu einem dünnen
  Closure über `bar_service.get_window(epic, "1m", now−(max_hold_minutes+60), now)`;
  die Konstanten `_PAPER_BAR_COUNT`/`_PAPER_BUDGET_COOLDOWN_MIN`/`_PAPER_ALLOWANCE_FLOOR`
  (`wiring.py:429-461`) **entfallen** (Budget lebt in `SourceBudget`; `budget_ok` bleibt als
  Naht und wird mit `budget.can_spend(0) or True`-Semantik → praktisch: Tracker macht keine
  IG-Calls mehr, `budget_ok` wird `lambda: True` mit Kommentar). `_PAPER_MAX_FETCH_ATTEMPTS`
  + `stale_after_minutes` bleiben (Korrektheitsguards, quellenneutral).
- `PaperTradeTracker._resolve_group` (`paper.py:565-618`): berechnet
  `resolution_source = "+".join(sorted({b["source"] for b in relevant}))` über die tatsächlich
  konsumierten Bars (dazu gibt `resolve_paper_trade` zusätzlich die benutzten Bars zurück
  **oder** — kleiner: `_resolve_group` filtert selbst `b["timestamp"] >= trade.created_utc`
  vor dem Aufruf und reicht das Ergebnis weiter; Implementierung wählt die kleinere Diff-Form)
  und übergibt sie an `mark_resolved(…, resolution_source=…)`.
- `PaperEngine.__init__` (+`epic_filter`, D19); Wiring injiziert
  `lambda epic: epic in {r.epic for r in store.measurable_universe()}` (gecacht pro Tick).
- `SchedulerConfig`: `enable_ig_bars: bool = False` (`config.py:150`) → **ersetzen** durch
  `enable_bar_service: bool = True` (Docstring erklärt die Ablösung, D17);
  `scheduler/run.py`-Flag nachziehen (§9.9).
**Tests (~14 + Updates):** BudgetedIG verweigert bei `can_spend` False (kein Broker-Call —
Fake zählt) · bucht Spend + Allowance nach Erfolg · BarService Archiv-Hit macht null
Chain-Calls · Lücke → Chain + Write-Through + Provenienz im Rückgabe-Dict ·
`get_bars`-Protocol-Kompatibilität (PriceBar-Shape) · Tracker-Ende-zu-Ende gegen
Fake-Archiv: Auflösung schreibt `resolution_source` · Legacy-Zeile ohne Spalte bleibt lesbar
(from_row-Kompat) · `epic_filter` gated `open_scheduled_pairs` und `on_debate_abstain` ·
Config-Default `enable_bar_service=True` · P8/P10-Bestandssuiten grün (Zählstände
dokumentieren).
**Akzeptanz:** `grep -rn "get_ohlcv" phase8_scheduler/scripts/wiring.py` zeigt **keinen**
Tracker-Call mehr; der einzige verbleibende IG-Bar-Direktpfad außerhalb BarService ist der
Momentum-VETO (D16) + `verify_instrument`-Probe. Offline-Smoke (`phase8_scheduler/scripts/
smoke_test.py`) 3/3 PASS.

### Step 5 — Recorder (eigener Prozess; Paket-Code WE-frei, `run_scheduler.sh`-Edit Wochenende)

**Dateien:** `data_foundation/recorder.py`, `data_foundation/run.py`,
`phase12_data_foundation/scripts/run_recorder.sh`, Edit an
`phase8_scheduler/scripts/run_scheduler.sh` (D14), `tests/test_recorder.py`.
**Namen:**
```python
# recorder.py
@dataclass
class RecorderReport: epics: int; bars_written: int; skipped_off_hours: bool; errors: list[str]
class Recorder:
    def __init__(self, archive: BarArchive, get_bars: Callable[..., Any],   # fetcher.get_bars, lazy gebaut
                 epics_fn: Callable[[], list[str]],                          # measurable_universe()-Closure (eigene ro-tauglichkeit: eigene UniverseStore-Connection)
                 *, resolution: str = "1m", count: int = 30, interval_s: int = 300,
                 state_path: str = "data/state/recorder_state.json",
                 health_sink: Callable[[dict], None] | None = None,
                 market_open_fn: Callable[[], bool] = ..., now_fn=..., sleep_fn=...) -> None
    def tick(self) -> RecorderReport      # Markt zu → no-op-Report; je Epic fail-soft; Dedup via Archiv-PK
    def run_forever(self) -> None         # Loop + Heartbeat-State (atomic tmp+os.replace, P8-state-Muster) + stop-Flag
    def request_stop(self) -> None
# run.py  →  python -m data_foundation.run
#   PID-File data/state/recorder.pid (existiert+Prozess lebt → Exit 0 mit Meldung, doppelstart-sicher),
#   SIGTERM/SIGINT → request_stop, Logging → stderr.
```
`run_scheduler.sh` (Anker `:27-35`): vor dem `exec` ein
`nohup bash "$REPO_ROOT/phase12_data_foundation/scripts/run_recorder.sh" >>data/state/recorder.log 2>&1 &`
— `run_recorder.sh` selbst prüft das PID-File und beendet sich sofort, wenn der Recorder
läuft (der Guard lebt im Recorder-Skript, nicht im Scheduler-Skript). Recorder ist
**zusätzlich** standalone startbar (Archiv-Warmlauf vor einem Bot-Restart).
**Tests (~10):** Tick schreibt nur für `epics_fn()`-Epics · Off-Hours no-op (kein Fetch) ·
Overlap-Dedup über zwei Ticks · ein Epic-Fehler stoppt den Tick nicht · Heartbeat-State
geschrieben + atomar · `request_stop` beendet `run_forever` · PID-Logik (Unit über
Hilfsfunktion `_pid_alive`) · Report-Zahlen stimmen · kein `broker_wrapper`-Import im Paket
(Grep-Test, D14) · `recorder_heartbeat`-Event emittiert.
**Akzeptanz:** Recorder läuft offline gegen Fake-Fetcher deterministisch; `run_recorder.sh`
startet/verweigert korrekt (manueller Check); kein IG-Import (D14-Grep grün).

### Step 6 — Divergenz-Sampler + Mess-Heartbeat (Cross-Phase: **Wochenende**)

**Dateien:** `data_foundation/heartbeat.py`, Wiring-Closures in
`phase8_scheduler/scripts/wiring.py`, additive Runner-Naht in
`phase8_scheduler/scheduler/runner.py`, `phase12_data_foundation/scripts/data_health.py`,
`tests/test_heartbeat.py`, P8-Test-Update.
**Namen:**
```python
# heartbeat.py
@dataclass(frozen=True)
class HealthVerdict: day: str; bars_today: int; pairs_opened: int; pairs_resolved: int;
                     pairs_typed_expired: int; measurable_epics: int; ok: bool; problems: list[str]
def assess_day(archive: BarArchive, paper_db_path: str, universe_db_path: str,
               day_utc: str, *, shadow_enabled: bool) -> HealthVerdict
    # ok=False u. a. wenn: shadow_enabled UND pairs_resolved==0 UND pairs_typed_expired==0;
    # oder bars_today==0 bei measurable_epics>0 (Recorder tot)
# runner.py (additiv, Muster paper_tracker):
#   SchedulerRunner.__init__(…, daily_health_check: Callable[[], Any] | None = None)   (runner.py:211-253)
#   POST_WINDOW-Zweig (runner.py:390-395): nach dem force-Reconcile einmal täglich
#   (throttle via _due_after, runner.py:455-470, Intervall 20h) self._run_daily_health_check()
# wiring: Closure baut assess_day + record_event("measurement_heartbeat", verdict-Felder)
#   + logger.critical bei ok=False.
# Divergenz-Sampler (D12): Closure divergence_sampler() im Wiring, aufgerufen aus dem
#   bestehenden universe_refresher-Slot (wiring.py:837-867) im selben Pass:
#   je 'ok'-Epic 1×/Tag broker.get_ohlcv(epic, "MINUTE_5", 3) via BudgetedIGBarProvider
#   (spend_kind='sample') → compute vs. Archiv-yF-Fenster → observability.check_divergence
#   (observability.py:130-140) → record_event; ≥2 Folge-Divergenzen → store.set_symbol(…, status=DS_MISMATCH).
```
`data_health.py` (Operator, read-only, werktags erlaubt): druckt `HealthVerdict` des letzten
Handelstags + Budget-Stand (`spent_in_window`, `remaining_estimate`,
`predicted_exhaustion_days`) + Recorder-Heartbeat-Alter; **Exit 1** bei `ok=False`.
**Tests (~8):** `assess_day`-Verdikte (gesunder Tag · Null-Messung bei aktivem Schedule ·
Recorder tot · kein measurable Epic ⇒ ok mit problem-Hinweis) · Runner ruft die Naht im
POST_WINDOW genau 1×/Tag (Fake-Clock) · Default `None` bit-identisch · Sampler-Throttle
1/Tag · Mismatch nach 2 Folge-Divergenzen, nicht nach 1.
**Akzeptanz:** G als Test beweisbar: ein simulierter Tag ohne Messung erzeugt CRITICAL +
`measurement_heartbeat{ok:false}` **am selben Tag**.

### Step 7 — Gesamtintegration + Offline-Beweis (Wochenende)

- `build_scheduler` (`wiring.py:661-898`): `_build_data_foundation` einmal bauen; BarService
  in Research (`:750`) + Tracker (`:757`) + Sampler/Heartbeat-Closures injizieren;
  `SchedulerRunner(…, daily_health_check=…)` (`:883-898`).
- `scheduler/run.py`: Flags nachziehen (`--disable-bar-service`, `--enable-shadow-schedule`
  vorhanden? — §9.9), `py_compile` + P8-Suite.
- **Offline-Beweiskette (die Abnahme dieses Steps, Advisor-Regel 3 beachten):**
  1. `phase8_scheduler/scripts/smoke_test.py` 3/3 PASS (Fakes).
  2. Neues Szenario im P12-Testbett: synthetischer Tag — Recorder-Fake schreibt Bars,
     Shadow-Pairs öffnen, Tracker löst **ausschließlich aus dem Archiv** auf,
     `resolution_source='yf'` steht in der Zeile, Heartbeat meldet ok.
  3. Volle per-Phase-Regression, Zählstände in den Session-Block.
- **Akzeptanz-Greps (Handover §6 „kein vierter Patch"):**
  `grep -rn "KNOWN_YF_TICKERS" --include="*.py"` → nur noch `data_foundation/symbols.py`
  (Seed) · `yf_ticker=`-Writer nur `set_symbol`/`seed_curated` · kein `enable_ig_bars` mehr.

### Step 8 — Operator-Sequenz: Gate, Reset, Restart (Nikinger; gated, KEIN Datum)

1. **Täglich** `python phase12_data_foundation/scripts/probe_allowance.py` (5 Punkte; wrappt
   den CLI-Einzeiler aus ALLOWANCE_INCIDENT §6, schreibt `allowance_observations` + Spend),
   bis `remaining > 0` beobachtet.
2. Beobachtetes `totalAllowance` → `IG_QUOTA_V1` + Reserve-Floor bestätigen/anpassen (§9.5,
   §9.11) — Code-Commit, kein Konfig-Drift.
3. **Recorder standalone starten** (werktags erlaubt — yF-only): Archiv-Warmlauf ≥ 1 Tag.
4. **Wochenende:** `python phase12_data_foundation/scripts/reset_universe.py` — setzt die 18
   `quarantined`-Zeilen auf `discovered, fail_count=0, last_verified_at=NULL`
   (Präzedenz 2026-07-06), **verweigert ohne frische Beobachtung** (D18).
5. Scheduler-Start via `run_scheduler.sh` (startet Recorder-Guard mit) mit
   `--enable-shadow-schedule` + bestehenden Caps. Erster Tracker-Tick entlädt die 390
   Alt-`OPEN`-Zeilen als `EXPIRED_UNRESOLVED` **ohne Fetch** (erwartet, `OUTAGE_EXPIRED_
   PAPER_IDS_2026-08-08.json` hält die IDs auseinander).
6. Erste Promotion-Runden beobachten: Kern-Epics re-verifizieren sich; Resolver vergibt
   `data_source_status` (Erwartung: DAX/CAC/IBEX/AEX/MIB/STXE + Dow/FTSE/Nasdaq/S&P → `ok`
   nach Marktöffnungs-Check; SUN* → `no_intraday_source`).

### Step 9 — Beweiswoche + Abnahme (Operator + eine Review-Session)

Täglich `data_health.py` (Exit 0 erwartet). Freitags eine Review-Session:
`phase10_v3`-Review-Muster, Ergebnisdoc `phase12_data_foundation/PROOF_WEEK_REVIEW_<date>.md`.
**PASS-Kriterien:** siehe §7. **PASS ⇒ Phase-12-Kern abgenommen**, Phase 11 (WI-2/W2) kann
wiederaufgenommen werden; Step 10 wird freigeschaltet. **FAIL ⇒** Root-Cause-Session, kein
Weiterbau auf wackligem Fundament (dieselbe Notbremsen-Logik wie 2026-08-11).

### Step 10 — Lightstreamer-Mitschrieb (gated auf Step-9-PASS; eigene Detail-Design-Session)

**Ziel:** `source='ls'`-Bars ins **selbe** Archiv; deckt die Wochenend-Epics und macht die
Messung IG-echt. **Vorarbeit liegt vor:** Step 7a lief live negativ-befundfrei
(alle 4 Epics subscriben sauber — `phase9_universe/CLAUDE.md` Step-7a-Zeile,
`phase1_broker_wrapper/lightstreamer_integration_notes.md`,
`lightstreamer_ig_reference.md`, Diag-Skript `scripts/diag_lightstreamer_multi.py`).
**Grobgerüst (Detail-Session entscheidet):** `data_foundation/ls_recorder.py` —
`LSBarAggregator` (Tick/CHART-Stream → 1-Minuten-OHLC, Lückenmarkierung bei Reconnect),
Persistenz via `BarArchive.insert_bars(source='ls')`.
**Die offene Kernfrage (JETZT dokumentiert, DANN entschieden):** LS braucht CST/XST-Tokens
aus einer IG-REST-Session → ein LS-Recorder im eigenen Prozess kollidiert mit der
Parallel-Login-Falle. Optionen: (a) LS-Mitschrieb in den Scheduler-Prozess (stirbt mit dem
Bot — widerspricht der Recorder-Idee), (b) Token-Sharing über eine Datei/IPC (neue
Sicherheitsfläche), (c) prüfen, ob ein zweiter REST-Login die erste Session real
invalidiert oder nur bei ungünstigem Timing (Live-Check). **Keine Vorfestlegung** —
das ist die erste Frage der Step-10-Session.

### Post — Doku-Sync + Handover

Phase-12-`CLAUDE.md`-Session-Block (Rotationsregel), Root-Statuszeile, `docs/INDEX.md`,
Memory-Update, Handover-Doc nach `docs/HANDOVER_PROMPT.md`-Vorlage.

---

## §7 Beweiswoche — PASS-Kriterien (= Abnahme gegen A–G)

| Anf. | Beweis in der Woche |
|---|---|
| A | Grep-Abnahmen aus Step 7 bleiben wahr; kein neuer Parallel-Speicher entstanden. |
| B | Mindestens ein während der Woche neu entdecktes ODER re-verifiziertes Instrument erreicht `ok`/typisierten Status **ohne Code-Edit** (real beobachtet, im Review dokumentiert). |
| C | Divergenz-Sampler lief täglich; `quote_divergence`-Events existieren (auch leere Tage zählen als Beweis der Ausführung via Sampler-Log). |
| D | Jedes nicht-messbare Epic trägt einen typisierten Status; **kein** `NULL`-Fallback-Pfad ausgelöst; SUN*-Epics erzeugen null Paper-Zeilen. |
| E | Jede in der Woche aufgelöste `paper_trades`-Zeile hat `resolution_source ≠ NULL`; `abstain_report.py --paper` gruppiert danach. |
| F | Budget-Prognose vs. Realverbrauch im Review (Soll < 1 500, §5); **kein** 403; `remaining_estimate` monoton plausibel. |
| G | 5/5 Handelstage `measurement_heartbeat` vorhanden; jeder Tag mit Problem wurde **am selben Tag** CRITICAL; `data_health.py` täglich Exit 0 (oder dokumentierter, typisierter Grund). |
| Kern | ≥ 4 von 5 Handelstagen mit aufgelösten Shadow-Pairs pro `ok`-Epic; **null** Quarantäne-Kaskaden durch Budget (nur echte Instrument-Fails erlaubt). |

---

## §8 Drop-Order & Risiken

**Drop-Order bei Zeit-/Budget-Druck (zuerst weglassen):** 1. Step 10 (ohnehin gated) →
2. Divergenz-Sampler (D12; Woche läuft, Messung yF-provenient, ehrlich gelabelt) →
3. `data_health.py`-Komfortausgaben (Event-Heartbeat bleibt) → **nie**: Archiv, Budget,
Registry, Typisierung (das ist die Phase).

**Risiken:**
- **yF-Zuverlässigkeit** (bekannte Intermittenz, 2026-07-02-Befund): Circuit/Retry existieren;
  Restrisiko = Lücken im Archiv → Tracker gibt typisiert auf statt zu raten (Verhalten
  unverändert konservativ). Der LS-Step ist die strukturelle Antwort.
- **`resolve_paper_trade`-Same-Bar-SL+TP-Bias** (ALLOWANCE_INCIDENT §7a): 1-Min-Bars bleiben
  Default — der Bias bleibt klein; der dort skizzierte 360-Punkte-Vergleichstest
  (MINUTE vs MINUTE_5) ist nach dem Reset ein optionaler Operator-Einzeiler.
- **SQLite-Nebenläufigkeit** (Recorder + Scheduler lesen/schreiben `bars.sqlite`):
  getrennte Dateien (D4), kurze Transaktionen, `INSERT OR IGNORE`; bei beobachteten
  `database is locked` → `busy_timeout` setzen (im Plan erlaubt, kein Redesign).
- **Registry-Erwartung an IG-Felder** (Step 3 Wochenend-Heuristik): Step 0a entscheidet, ob
  echte Felder die Heuristik ersetzen — Heuristik ist der sichere Fallback.

---

## §9 Bei Ausführung verifizieren (Drift-Liste — NICHT als gesichert behandeln)

1. **Alle Datei:Zeile-Anker** (Stand `c5d7ef1`, 2026-08-11) per Grep re-verifizieren, bevor
   ein Edit auf sie gebaut wird.
2. **`get_market_info`-Felder** (Öffnungszeiten/Wochenend-Erkennung, Margin) — **✅ Step 0a
   erledigt (2026-08-11):** `get_market_info` selbst liefert diese Felder nicht (projiziert,
   `ig_adapter.py:479-513`); Rohdaten per `_request()`-Skript geholt. Ergebnis:
   `openingHours` ist bei normalen Werktags-Instrumenten `null`, bei SUNDAX populated —
   **aber** `instrument.specialInfo` trägt bei SUNDAX einen wörtlichen "weekend instrument"-
   Satz, ein zuverlässigeres Signal. B3-Margin: `marginDepositBands` + `marginFactor` +
   `marginFactorUnit` vollständig vorhanden. Details:
   `phase12_data_foundation/CLAUDE.md` Session-Block 2026-08-11. Step 3 konsumiert dies beim
   Bau von `symbols.py::is_weekend_instrument` (primär `specialInfo`-Substring, Namens-/
   Epic-Heuristik bleibt Fallback).
3. **IG-Bar-Timestamp-Format** (`get_ohlcv`-Antwort) für `normalize_bar_ts` — **bestätigt
   (2026-08-11, Code-Lesung `ig_adapter.py:901`):** `_parse_bar` nimmt `snapshotTime` oder
   `snapshotTimeUTC`, IG-eigenes Format `"yyyy/MM/dd HH:mm:ss"`, **nicht** ISO. `Step 1`s
   `normalize_bar_ts` deckt diese Form ab (+ ISO mit/ohne `Z`). Live-Wertebereich (echte
   Beispielstrings aus einer realen `/prices`-Antwort) bleibt bei Ausführung zu bestätigen;
   `resolve_paper_trade` vergleicht weiterhin lexikalisch (`paper.py:240`).
4. **yF-1m-Verfügbarkeit** der Kern-Indizes intraday (bekannt gut für ^GDAXI; ^FCHI/^IBEX
   intermittierend — 2026-07-02-Diagnose).
5. **`allowance`-Objekt-Feldnamen** (`totalAllowance`/`remainingAllowance`/`allowanceExpiry`
   — aus `ig_adapter.py:436-439` + IG-Doku; erst nach erstem Erfolgs-Call bestätigt).
6. **Zählt `get_price`/Snapshot gegen ein anderes Kontingent?** (Annahme: nur die
   Per-Minute-API-Allowance, nicht die Historien-Punkte — für Resolver + Shadow-Quotes
   relevant.)
7. **Migrationsnummer 006 frei** (`ls phase2_persistence/migrations/` — Stand heute: 001–005).
8. **Test-Baseline** (Handover nennt 1 336 grün; per-Phase separat laufen, Zählstände neu
   dokumentieren).
9. **`scheduler/run.py`-CLI-Flags** (`--enable-ig-bars` existiert? `--enable-shadow-schedule`
   existiert? — Flag-Liste vor dem D17-Umbau greppen).
10. **`PaperTrade.to_row`/`from_row`-Positionslogik** beim Spalten-Anhang (`paper.py:133-182`)
    — neue Felder strikt ans Ende, Legacy-Rows abfangen.
11. **Reserve-Floor + `IG_QUOTA_V1`** erst nach beobachtetem `totalAllowance` finalisieren
    (bis dahin: 10 000/7 Tage laut DATA_SOURCE_STRATEGY §1).
12. **Aktueller DB-Stand** (heute: 4 aktive SUN*-Epics, 18 quarantined, 390 OPEN paper_trades)
    — vor Step 8 frisch lesen, nicht aus diesem Plan übernehmen.

---

## §10 Explizit NICHT in Phase 12

- **WI-2/W2-Auswertung** und jede weitere H-Serie (H3/H5/H7) — Phase-11-Wiederaufnahme nach
  bestandener Beweiswoche.
- **Research-Funnel-Fix** (0-Kandidaten-Problem, W1/W5) — die Messung ist via
  Shadow-Schedule (H1) bewusst vom Funnel entkoppelt; der Funnel ist ein eigenes Thema.
- **B3 Margin-Headroom** — eigene Session; Step 0a liefert nur die gebündelten Felddaten.
- **Council-Paper-Call-Aktivierung**, UI-Arbeit, Live-Konto, neue bezahlte Provider,
  `lesson_embeddings`.
- **Lightstreamer für Live-Quotes im Research-Kontext** (P9 Step 7b) — bleibt geparkt;
  Step 10 hier ist Mitschrieb fürs Archiv, ein anderer Zweck.
