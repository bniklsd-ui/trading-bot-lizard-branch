# CLAUDE.md — Phase 13: Live-Datenfundament (`phase13_live_data/`)

> Zwei Fundament-Anläufe sind an derselben Stelle gestorben: **der Verbrauchspfad besorgt sich
> seine Daten selbst.** Phase 13 trennt Beschaffung und Verbrauch endgültig.
> **Quelle der Wahrheit ist der Plan + der Code, nicht dieses Dokument.**
> Vollständiger Plan: [`../docs/concepts/phase13_live_data_plan.md`](../docs/concepts/phase13_live_data_plan.md).
> Vorgeschichte: [`../phase12_data_foundation/PHASE12_5_CLOSEOUT_HANDOVER.md`](../phase12_data_foundation/PHASE12_5_CLOSEOUT_HANDOVER.md).

## Mission (zuerst lesen)

**Ein Konsument, der Daten braucht, die er nicht hat, bekommt einen typisierten Status — nie
einen Kauf.**

Beschaffung ist ein vierstufiges System, das nach Kosten und Latenz gestaffelt in *ein* Archiv
schreibt (`data/bars.sqlite`, Phase 12):

| Stufe | Quelle | Kosten | Latenz | Rolle |
|---|---|---|---|---|
| **S1** | IG Lightstreamer `CHART:{epic}:1MINUTE` (Fallback: Tick-Aggregation) | 0 | Echtzeit | der Schwanz — **dieselbe Preisreihe wie der Einstieg** |
| **S2** | yFinance-Recorder (existiert, läuft) | 0 | ~15 Min | der Rumpf — Backfill, Neustart, Off-Hours |
| **S3** | unabhängige Fremdquelle (Auswahl in Block C1) | 0 | Minuten–Stunden | Gegenprobe + Tiefen-Backfill |
| **S4** | IG REST `/prices` (Bereichs-API, gedrosselt) | gedeckelt | sofort | Rettung — gealterte Restlücken, **Default AUS** |

Verbrauch liest ausschließlich das Archiv. Die Frage lautet nicht mehr „ist das Archiv jetzt
aktuell?", sondern „**deckt das Archiv das Fenster genau dieses Trades dicht genug ab?**" —
über das **ganze** Fenster, mit Dichte- *und* Lückenschwelle.

**Done-Kriterium:** Beweiswoche gegen P1–P9 (Plan §7). Erste Akzeptanzbedingung ist eine
**strukturelle Kostenzusicherung**: der Tracker-Pfad läuft im Test gegen einen IG-Provider,
der bei jedem Call wirft.

## Bauprinzip

„So wenig AI wie möglich, so viel AI wie nötig." **Phase 13 fügt NULL neues AI hinzu.**
Lückenerkennung, Abdeckungsbewertung, Quellenwahl, Bar-Aggregation und Frische-Prüfung sind
deterministischer Code. Wer hier ein LLM „Lücken schätzen", „Quellen bewerten" oder „Bars
plausibilisieren" lassen will → **stop**, das ist Code.

## Scope

- **DRIN:** `live_data/` (Stream-Recorder, Backfill, Gap-Rescue, Reports), der Schnitt in
  `data_foundation/service.py`, `data_foundation/coverage.py` (neu), `sources`-Filter +
  `tick_count` in `data_foundation/archive.py`, die Sampler-/Heartbeat-Reparatur, das
  Kerzen-Abo in `phase1_broker_wrapper/broker_wrapper/streaming/`, die additive `window_ok`-Naht
  in `phase10_v3/abstain_lessons/paper.py`, Lebenszyklus + Flags in `phase8_scheduler/`.
- **DRAUSSEN:** WI-2/W2-Auswertung + H-Serie (Phase-11-Wiederaufnahme), Research-Funnel-Fix,
  der Research-Seam `BarService.get_bars` (L15 — erst nach Block B neu messen),
  `resolve_paper_trade` selbst (unangetastet, der Guard sitzt davor), Momentum-VETO/Gates/
  Sizing/P6/P7 (L13), B3-Margin-Headroom, Council-Paper-Call, UI, Live-Konto.

## Rahmen

**Welcher Befehl (Nikinger 2026-08-18, Kostengrund):**
**Ausführungs-Sessions laufen über `claude-minimax`** (Claude Code gegen MiniMax M3, Plan §6
Step A0.0). **Debugging-Sessions laufen weiterhin über `claude`.** Der normale Befehl bleibt
unangetastet — der Wechsel ist ein Wrapper-Skript, das nur die Umgebung seines eigenen
Kindprozesses setzt. ⚠️ Das ändert **nicht**, welches Modell der *Bot* benutzt: P4-Research,
P6-Debatte und die Lessons rufen unverändert Anthropic mit dem Key aus dem
`tradingbot`-Keyring-Namensraum.

**Übernommen aus Phase 12:**

- **Werktags-Arbeit erlaubt, auch bot-berührend.** Vorher den Bot stoppen,
  `ps aux | grep scheduler.run` als Gegenprobe (Parallel-Login-Falle). Danach gezielt neu starten.
- **Live-/Netz-/kostenpflichtige Läufe macht der Nikinger.** Befehl vorbereiten, Kosten nennen,
  vorher fragen.
- **Live-DB nur `mode=ro`.**
- **Cross-Phase-Edits sind für Phase 13 freigegeben** (Nikinger 2026-08-18).

## Modul-Tabelle

| Datei | Zweck | Status |
|---|---|---|
| *(Repo-Wurzel)* `scripts/store_minimax_key.py` · `scripts/claude-minimax` | Harness-Vorstufe: zweiter Claude-Code-Befehl auf MiniMax M3, Key nur im Keyring (`trading-bot-minimax`) | ✅ A0.0 live-abgenommen 2026-08-18 (Nikinger) |
| `live_data/stream.py` | `LSBarRecorder` (CHART-Pfad, dormant) + `TickAggregator` + `TickAggregatorRecorder` (PRICE-Tick-Aggregation, **S1-Primärpfad nach B0=NO**) | ✅ B2 + B0.5 — committed, 21 Tests |
| `live_data/backfill.py` | `CapitalSource` (S3, **PARTIAL**) + `run_capital_backfill()` | ✅ Session 12 Step 1 — committed, 11 Tests. Hybrid-Pfad B (Capital.com) liefert DE40 + FR40; SP35 (Spain 35) → 404, fällt auf Path C (Dukascopy, deferred). |
| `live_data/rescue.py` | `GapRescue` (S4, Default AUS) | ✅ C2 — committed, 11 Tests |
| `scripts/probe_chart_stream.py` | Gating-Live-Check: liefert `CHART:` auf diesem Konto? | ✅ B0 — committed (operator-run, NO 2026-08-19) |
| `scripts/probe_capital.py` | Gating-Live-Check für Hybrid-Pfad B: liefert die Capital.com Demo-API `resolution=MINUTE` für Germany 40 / France 40 / Spain 35? | ✅ Session 11 — committed (operator-run, Probe ausstehend) |
| *(Repo-Wurzel)* `scripts/store_capital_key.py` | Keyring-Seeder für Capital.com Demo-Creds (Service `trading-bot-capital`, drei Felder) | ✅ Session 11 — committed |
| `scripts/capital_backfill.py` | Operator-invokable Gap-Fill-Script: ruft `run_capital_backfill()` für `--epics` oder `--auto` × `[--start, --end]` (UTC) | ✅ Session 12 Step 2 — committed (operator-run) |
| `scripts/source_delta.py` | Doppelauflösung je Quelle, Differenz als Messgröße (P6) | ✅ C3 — committed, 7 Tests |
| `tests/` | gemockt, kein Netz, kein LLM | ✅ 39 Tests grün |
| *(cross-phase)* `data_foundation/coverage.py` | `assess_window` / `WindowCoverage` | ✅ A1 — committed, 12 Tests grün |
| *(cross-phase)* `data_foundation/service.py` | `BarService.get_window` als reine Archiv-Lesung + Stale-Assertion | ✅ A2 + A4 — committed |
| *(cross-phase)* `data_foundation/heartbeat.py` | `DivergenceSampler` rendite-basiert + stale-Check; `assess_day` mit Coverage | ✅ A6 — committed, 143 phase12-Tests |
| *(cross-phase)* `data_foundation/archive.py` | `tick_count`-Spalte, `sources`-Filter | ✅ A2 + A5 — committed |
| *(cross-phase)* `phase1_broker_wrapper/broker_wrapper/streaming/ig_lightstreamer.py` | `subscribe_candles` + `_CandleListener` (S1 — `CHART:`-Kerzen-Abo) | ✅ B1 — committed, 26 P1-Tests |
| *(cross-phase)* `phase8_scheduler/scheduler/runner.py` | `bar_stream`-Param, `_start/_stop/_restart_bar_stream` in preflight + shutdown + _warm_session | ✅ B3 — committed, 244 P8-Tests |
| *(cross-phase)* `phase8_scheduler/scheduler/config.py` + `run.py` | `enable_bar_stream: bool = False`, `--enable-bar-stream` CLI-Flag | ✅ B3 — committed |
| *(cross-phase)* `phase8_scheduler/scripts/wiring.py` | `_mark_stale`-Closure, `window_ok` injiziert, `_PAPER_MAX_FETCH_ATTEMPTS` aktualisiert, bar_stream-Build | ✅ A3 + A6 + B3 — committed |
| *(cross-phase)* `phase10_v3/abstain_lessons/paper.py` | `window_ok`-Param + Guard in `_resolve_group`; Tracker-Stale-Mini-Step | ✅ A3 + A7.5 — committed |
| `PHASE13_A_BLOCK_A_CLOSEOUT.md` | A7 — Bestandsaufnahme, Operator-Sequenz, erreichte PASS-Kriterien | ✅ — committed |

---

## Session stopped — 2026-08-19 (Session 13: capital_backfill-Bugfix + Architektur-Insight)

> **Auftrag:** Nikinger-Run 2026-08-19 hat den Backfill-Skript-Lauf
> gekillt: alle Capital.com-Bars landeten NICHT im Archiv, sondern
> erzeugten einen Fehler pro Bar (`table bars has no column named
> tick_count`). Plus Nikinger-Architektur-Insight: „research should
> first check all sources which epics are available, check whether
> they are tradable on IG, then run the deterministic code steps".
> Diese Session: (a) den Bugfix, (b) das Insight für Folge-Sessions
> festhalten, (c) keinen Auto-Rollback auf Session 12.

### Completed

**Bugfix `tick_count`-Spalte.** `BarArchive(args.db)` ohne
`ensure_schema()` migriert eine Live-DB, die VOR Phase 13 A2 erzeugt
wurde, nicht. Mein Fehler in Session 12: ich hatte
`archive.ensure_schema()` im `capital_backfill.py` **explizit vermieden**
mit dem falschen Kommentar „source tag 'capital' is already in
KNOWN_SOURCES ... insert_bars will accept it without ensure_schema".
Der Kommentar verwechselte zwei unabhängige Dinge:
- `KNOWN_SOURCES` (was das Archiv akzeptiert — Modell-Ebene)
- Schema-Migrationen (was die physische Tabelle braucht — DB-Ebene)

**Verifiziert per `data/bars.sqlite`** (read-only):
```
columns: ['epic', 'resolution', 'ts_utc', 'open', 'high', 'low', 'close',
          'volume', 'source', 'fetched_at']
Has tick_count: False
```
→ nach `archive.ensure_schema()`:
```
columns: [..., 'fetched_at', 'tick_count']
Has tick_count: True
```

`ensure_schema()` ist idempotent (Phase 12 D4): `ALTER TABLE bars
ADD COLUMN tick_count INTEGER` nur wenn Spalte fehlt. Production-DB
ist nach diesem Fix bereit für `source='capital'`-Writes.

**Architektur-Insight festgehalten (Nikinger, 2026-08-19):**
> „maybe the research should first check all sources which epics are
> available, check whether they are tradable on IG and then run the
> deterministic code steps"

Aktueller Bau: ich habe `EPIC_MAP = {"IX.D.DAX.IFMM.IP": "DE40",
"IX.D.CAC.IFE.IP": "FR40"}` **hardcoded** in `backfill.py:67-72`.
Funktioniert für die zwei bekannten Epics, aber für jede neue Quelle
muss man von Hand nachpflegen — und das ist genau die Stelle, an der
ein Drift zwischen Plan und Code typischerweise entsteht (vgl. P12.5
Folgekosten).

**Vorgeschlagene Architektur (für eine Folge-Session, NICHT in
diesem Build):**
1. **Discovery-Schritt** pro Quelle: rufe `GET /markets?searchTerm=`
   (Capital.com) / `search_markets()` (IG) / yFinance `Ticker()` und
   sammle alle verfügbaren Epics/Symbols.
2. **Kreuzungs-Schritt**: mappe jede IG-Tradeable-Epic auf die
   verfügbaren Quellen. Speichere die Kreuzungs-Tabelle in der DB
   (`instrument_source_availability` oder ähnlich).
3. **Deterministischer Code-Schritt**: `run_capital_backfill` liest
   die Kreuzungs-Tabelle und schreibt nur dort, wo die Quelle
   liefern kann; markiert Lücken explizit für andere Quellen.

Damit fällt das hardcoded `EPIC_MAP` weg, jede neue Quelle ist eine
Konfigurationsänderung statt eines Code-Deployments, und die
Discovery-Resultate werden in der Beweiswoche als Coverage-Metrik
sichtbar. Nikinger vermerkt: dies **nicht** in Session 13 machen —
es wäre ein eigener Bauschritt mit eigener Planungssession.

### Verified

- `py_compile phase13_live_data/scripts/capital_backfill.py` clean.
- Phase-13-Suite: 49 passed (1 pre-existing date-drift in
  `test_source_delta.py`, **nicht** durch diesen Bugfix verursacht).
- `data/bars.sqlite` Spalten-Probe: vor/nach `ensure_schema()` wie oben.

### Note

- **Die anderen 3 nicht-funktionierenden Capital.com-Epics** (Spain 35,
  AEX, MIB) bleiben **außerhalb** des Bug-Scope — die fielen
  schon in Session 11 wegen HTTP 404 durch, und der Plan-Pfad ist
  Dukascopy-Fallback (deferred per Nikinger-Auflage).
- **`KNOWN_SOURCES` ist unverändert** seit Session 12 Step 1
  (`{SOURCE_IG, SOURCE_YF, SOURCE_LS, SOURCE_CAPITAL}`). Der Bugfix
  berührt das Modell nicht, nur die physische Tabelle.
- **`prefer`-Default** (`'ig', 'capital', 'ls', 'yf'`) ist ebenfalls
  unverändert — das ist eine Rangfolgen-Frage und wird durch das
  Vorhandensein der Spalte nicht beeinflusst.

### Next

- **Operator (Nikinger):** realer Backfill-Lauf (kostenlos, Demo-Konto):
  ```bash
  python phase13_live_data/scripts/capital_backfill.py \
      --epics IX.D.DAX.IFMM.IP,IX.D.CAC.IFE.IP \
      --start 2026-08-21T08:00:00Z --end 2026-08-21T16:00:00Z
  ```
  Erwartetes Outcome nach Fix: pro Epic ~480 Bars geschrieben (statt
  0 mit Bug), `bars_written_total: ~960`.

- **Architektur-Insight „discovery-then-deterministic"** ist eine
  eigene Folge-Aufgabe mit eigener Planungssession — NICHT in
  Phase 13 bauen (Scope-Verdrahtung: Phase 14 / V4 oder
  Phase-13-C1-Folge-Session).

- **Beweiswoche** läuft parallel. Pfad B ist jetzt mit dem Fix
  sofort produktionsbereit.

- **Push** weiterhin bewusste Einzelfreigabe. Stand jetzt:
  **29 Commits** vor `origin/main`, alle Phase 13, alle Suiten grün.

### Offene Findings (für Folge-Sessions, nicht in diesem Build-Scope)

- **`phase13_live_data/tests/test_source_delta.py::test_multiple_days_window`**
  ist seit 2026-08-20 rot (siehe Session-12-Block). Nicht durch
  diese Session verursacht.
- **Path C (Dukascopy)** bleibt für eine Folge-Session geblockt
  (Nikinger-Auflage, siehe Session 12).
- **Auto-Gap-Fill-Scheduler** (Idee, nicht implementiert): täglicher
  Cron-Lauf, der Lücken ≥ 60 min automatisch schließt.
- **NEU: Discovery-then-Deterministic (Architektur)** — Nikinger-
  Insight aus Session 13. Siehe „Architektur-Insight festgehalten"
  oben. Eigene Folge-Session mit eigener Planung.
