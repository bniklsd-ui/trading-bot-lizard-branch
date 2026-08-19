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
| `live_data/backfill.py` | `ExternalBackfill` (S3) | ⬜ Block C1 (deferred per Plan §6 C1.0 — Wahl auf nach Beweiswoche) |
| `live_data/rescue.py` | `GapRescue` (S4, Default AUS) | ✅ C2 — committed, 11 Tests |
| `scripts/probe_chart_stream.py` | Gating-Live-Check: liefert `CHART:` auf diesem Konto? | ✅ B0 — committed (operator-run, NO 2026-08-19) |
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

## Session stopped — 2026-08-19 (Session 10: B0.5 — TickAggregatorRecorder-Build + Wire + C1-Vorzug)

> **Auftrag:** Nikinger („alles was gebaut werden kann, baue jetzt
> atomar, danach muss die Entscheidung zur Fremd datenquelle fallen").
> B0-Probe lief 2026-08-19 mit Exit-Code 1 (NO) — `CHART:{epic}:1MINUTE`
> liefert `-1 Incorrect instrument setup` auf diesem Konto. Plan §6 B0
> NO-Zweig sagt „TickAggregator wird Primärpfad", aber im Bau klaffte
> eine Lücke: nur die `TickAggregator`-Klasse existierte, kein
> Recorder-Wrapper analog zu `LSBarRecorder`. Diese Session schließt
> die Lücke und zieht danach die C1-Entscheidung vor.

### Completed

**B0.5 — TickAggregatorRecorder-Wrapper (NEU).** Schließt die
Bau-Lücke zwischen Plan und Code:

- `TickAggregator.on_tick` refaktoriert: gibt jetzt das candle-shaped
  dict für die Minute zurück, die gerade geschlossen wurde (None sonst).
  `close_minute` bleibt für Tests / externe Caller.
- Neue Klasse `TickAggregatorRecorder` (~190 Zeilen, Pattern = 
  `LSBarRecorder`): subscribed `PRICE:{epic}` (Phase-1-live-verified),
  pro-Epic-`TickAggregator` aggregiert Ticks zu 1-Min-OHLC, schreibt
  ins `BarArchive` mit `source='ls'` + `tick_count`. Fail-soft überall
  (ArchiveError geloggt, Bad-Tick gedroppt, in-flight-Tick bei
  stop/restart gedroppt). Health-Event: `ls_tickagg_candle_written`
  mit `thin`-Flag für `tick_count <= thin_threshold` (Default 2, per
  Plan §6 B0 NO).
- Wiring: `phase8_scheduler/scripts/wiring.py` baut jetzt
  `TickAggregatorRecorder` statt `LSBarRecorder`. `LSBarRecorder`
  bleibt importierbar (one-line swap back, falls ein zukünftiges
  IG-Update / Account-Tier CHART wieder erlaubt).
- 10 neue Tests (29 → 39 in phase13): 2 on_tick-return-value +
  8 Recorder-Tests (start subscribes, write on minute close, thin flag,
  threshold boundary, drop after stop, resync diff, restart idempotent,
  archive failure survives). `_FakeStream` erweitert um
  `subscribe`/`unsubscribe` (PRICE-Pfad) — derselbe Fake bedient
  beide Recorder.

### Verified

- `pytest phase13_live_data/tests -q` → **39 passed** (war 29, +10).
- `pytest phase1_broker_wrapper/tests -q` → **95 passed** (unverändert).
- `pytest phase8_scheduler/tests -q` → **244 passed** (unverändert).
- `pytest phase12_data_foundation/tests -q` → **143 passed** (unverändert).
- `pytest phase10_v3/tests -q` → **165 passed** (unverändert).
- `py_compile` clean auf `stream.py` + `wiring.py` + `test_stream.py`.

### Note

- **Drei Commits in dieser Session**, jeder Schritt unabhängig grün
  (Nikinger-Auflage „commit after each step"):
  1. `438dbf0` B0.5 — `TickAggregatorRecorder` Klasse + Tests (437 +/−20)
  2. `6703573` B0.5 — Wire `TickAggregatorRecorder` in `wiring.py` (12 +/−8)
  3. *(dieser Docs-Commit)* Session-10-Block + Modul-Tabelle + Rotation
- **B0-Ergebnis hat keinen Build-Pfad geändert** — Plan §6 B0 hatte
  beide Zweige ausgeplant, das `TickAggregatorRecorder`-Wrapper fehlte
  nur als isolierte Komponente. Kein Risiko an A/B/C2/C3.
- **`LSBarRecorder` ist jetzt dormant** auf diesem Konto, nicht
  gelöscht: CHART-Pfad bleibt importierbar, falls IG / Account-Tier
  sich ändert.
- **`_do_subscribe_chart`-Docstring** (`ig_lightstreamer.py:359-362`)
  behauptet weiterhin "the SDK's default is correct for CHART
  (verified in the B0 probe)" — faktisch widerlegt durch B0=NO.
  Bewusst NICHT in dieser Session editiert (cross-phase-Datei, nicht
  im B0.5-Scope, und der Laufzeit-Code-Pfad ist ohnehin dormant).

### Next

- **C1 (S3-Fremdquelle)** — Nikinger-Entscheidung jetzt fällig (nicht
  mehr auf nach der Beweiswoche vertagt — Nikinger-Auflage
  2026-08-19). Plan §6 C1.0 hält vier Kandidaten + Disqualifizierungen
  bereit; die **Capital.com Demo-API** ist die einzige Option ohne
  ToS-Kollision, ohne neue Abhängigkeit, mit IG-naher Preisreihe.
- **C1.5 (Operator live-check)**: Capital.com Demo-API Probe
  (~50 Zeilen, gemockt im Test, echt beim Operator) — liefert sie
  `resolution=MINUTE` für Germany 40 / France 40 / **Spain 35**, und
  wie weit zurück? Ergebnis entscheidet C1-Code-Pfad
  (`live_data/backfill.py`, vier Regeln aus §6 C1.0).
- **Beweiswoche** kann **parallel** zu C1-Code-Bau laufen — Block B
  (S1/TickAggregatorRecorder) ist jetzt wired, Block A (Schnitt) ist
  aktiv. Nikinger-Call: `probe_allowance.py` → A7-Operator-Sequenz
  → 5 Tage `data_health.py` + `source_delta.py`.
- **Push** bleibt bewusste Einzelfreigabe. Stand jetzt: **23 Commits**
  seit `origin/main`, alle Phase 13, alle Suiten grün.
