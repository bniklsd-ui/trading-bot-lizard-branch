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
| `live_data/stream.py` | `LSBarRecorder` + `TickAggregator` (S1) | ✅ B2 — committed, 11 Tests |
| `live_data/backfill.py` | `ExternalBackfill` (S3) | ⬜ Block C1 (deferred per Plan §6 C1.0 — Wahl auf nach Beweiswoche) |
| `live_data/rescue.py` | `GapRescue` (S4, Default AUS) | ✅ C2 — committed, 11 Tests |
| `scripts/probe_chart_stream.py` | Gating-Live-Check: liefert `CHART:` auf diesem Konto? | ✅ B0 — committed (operator-run) |
| `scripts/source_delta.py` | Doppelauflösung je Quelle, Differenz als Messgröße (P6) | ✅ C3 — committed, 7 Tests |
| `tests/` | gemockt, kein Netz, kein LLM | ✅ 29 Tests grün |
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

## Session stopped — 2026-08-19 (Session 9: Block B (B0–B3) + Block C (C2/C3) — Phase 13 CODE-COMPLETE)

> **Auftrag:** Nikinger („going on until I am needed"). Block A war
> abgeschlossen, also weiter mit Block B (B0–B3) und Block C (C2/C3;
> C1 nach Plan §6 C1.0 auf nach der Beweiswoche vertagt). Beide Blöcke
> sind in dieser Session fertig geworden.

### Completed

**A7.5 — Tracker-Stale-Mini-Step** (5 Zeilen + 1 Test). `paper.py`
bekommt einen dritten Stale-Hook (neben A4 Schreibpfad, A6.1 Sampler-
Diagnose) — der Tracker lehnt einen Trade ab, dessen einzige Archive-Bar
älter als `_TRACKER_STALE_TOLERANCE_MIN=120` ist. Bewusst NICHT in
A2/A3/A6 mitgenommen, weil die Test-Fixtures erneut anfasst — jetzt
vor dem ersten Neustart.

**Block B (B0 + B1 + B2 + B3)** — die Live-Stream-Kette:
- **B0** `phase13_live_data/scripts/probe_chart_stream.py` (NEU,
  ~50 Zeilen, operator-run, kostenlos). Subscribed `CHART:{epic}:1MINUTE`
  mit 11 Feldern, Exit-Codes YES/NO/PARTIAL/AUTH, beide B0-Zweige
  ausgeplant.
- **B1** `phase1_broker_wrapper/broker_wrapper/streaming/ig_lightstreamer.py`
  erweitert um Kerzen-Abo parallel zum Tick-Abo. `ChartCandle` (frozen
  dataclass) + `CandleCallback`. `_CandleListener` akkumuliert Felder
  über LS-Updates, emittiert genau ein ChartCandle bei `CONS_END==1`
  mit mid = (BID+OFR)/2 (L7). 8 neue Tests (alle gemockt).
- **B2** `phase13_live_data/live_data/stream.py` (NEU, ~150 Zeilen).
  `LSBarRecorder` (write-through LS-Kerzen ins Archiv mit `source='ls'`
  + `tick_count`) + `TickAggregator` (L6-Fallback für PRICE-Ticks,
  wenn CHART nicht verfügbar). Fail-soft ueberall: ArchiveError geloggt,
  Callback-Exception isoliert, complete=False ignoriert, in-flight
  Candle nach stop() gedroppt. 11 neue Tests.
- **B3** Scheduler-Lebenszyklus + Token-Rotation. Vier Stellen
  verdrahtet: `bar_stream`-Param in `runner.__init__`, `_start_bar_stream()`
  in preflight() nach `_run_universe_refresher()`, `_restart_bar_stream()`
  in `_warm_session()` nach erfolgreichem `connect()` (Token-Rotation,
  IG rotiert CST/XST bei jedem connect), `_stop_bar_stream()` als
  eigener guarded Block in shutdown(). `--enable-bar-stream` CLI-Flag
  in `run.py`, `enable_bar_stream: bool = False` in `config.py`.
  wiring.py baut nur, wenn Flag an. 7 neue Tests (6 in test_runner
  + 1 CLI in test_run).

**Block C (C2 + C3; C1 deferred per Plan §6 C1.0):**
- **C2** `phase13_live_data/live_data/rescue.py` (NEU, ~190 Zeilen).
  S4-Rettungs-Stufe für gealterte Restlücken. Direkter IG-REST-call
  (Bereichs-API `from`/`to`) am Chain-Provider vorbei, gedrosselt auf
  1 Call/Epic/Tag, Stale-Assertion am Kaufort (L8 wiederverwendet,
  dritter Stale-Hook). `RescueReport` mit `skipped_reason` immer
  zurück (kein `None`, nie raise). Eigener spend-Knopf `'rescue'`
  (Ledger-Eintrag auffindbar). 11 Tests.
- **C3** `phase13_live_data/scripts/source_delta.py` (NEU, ~210 Zeilen).
  Read-only Diagnostic. Liest paper_trades + bars.sqlite im `mode=ro`,
  löst jeden resolved Trade je Quelle (yf / ls) ein zweites Mal auf
  und weist die Differenz aus. CLI: `--day` oder `--days N` (mutually
  exclusive), `--quiet`. Exit-Codes: 0 OK (immer, auch bei Divergenz
  — Divergenz ist Daten, kein Fehler), 1 READ ERROR. P6-Kriterium
  erfüllt: „Anteil der Zeilen, bei denen die Quelle das Ergebnis dreht".
  7 Tests.

### Verified

- `pytest phase12_data_foundation/tests -q` → **137 passed** (A0–A6,
  unverändert seit Session 7).
- `pytest phase1_broker_wrapper/tests -q` → **95 passed** (war 87, +8 B1).
- `pytest phase8_scheduler/tests -q` → **244 passed** (war 237, +7 B3).
- `pytest phase13_live_data/tests -q` → **29 passed** (war 0, +29
  aus B2 + C2 + C3).
- `py_compile` clean auf allen geänderten cross-phase-Dateien.
- **Voller Regression-Sweep**: alle 13 Suiten grün, kein Regress.

### Note

- **Phase 13 ist CODE-COMPLETE.** Block A (A0–A7 + A7.5), Block B
  (B0–B3) und Block C (C2 + C3) sind gebaut + committet + getestet.
  Was bleibt, ist **ausschließlich Live-Arbeit**:
  - **B0-Probe** (`probe_chart_stream.py`) — der einzige Test, der
    entscheidet, ob Block B auf S1 (CHART) oder L6-Fallback läuft.
  - **Beweiswoche** — 5 Handelstage mit scharfem Messarm, gemessen
    gegen P1–P9 (Plan §7). A7-Operator-Sequenz ist der konkrete
    Fahrplan; C3 (source_delta.py) ist die laufende Diagnostik.
- **C1 (S3-Fremdquelle) bleibt bewusst offen** — Plan §6 C1.0 hat die
  Wahl explizit auf nach der Beweiswoche vertagt: erst messen, dann
  entscheiden. Heißt nicht „vergessen", heißt „nicht spekulieren".
- **Drei Stale-Hooks, drei unabhängige Konstanten** (per Design):
  A4 (Schreibpfad) / A6.1 (Diagnose) / A7.5 (Tracker) — und C2 nutzt
  den A4-Knopf wiederverwendet (vierte Konstante wäre Drift). Wer
  einen lockert, lockert ihn explizit.
- **Vier Commits in dieser Session**, jeder einzelne Schritt
  unabhängig grün:
  1. `139f7d6` A7.5 Tracker-Stale
  2. `6cc43e0` B0 + B1
  3. `042e969` B2
  4. `a58a352` B3
  5. `fd6755f` C2
  6. `50a417e` C3

### Next

- **PAUSE für den Nikinger.** Phase 13 ist fertig gebaut. Was den
  Nikinger jetzt braucht, ist Operator-Arbeit (B0-Probe, dann
  A7-Operator-Sequenz) — keine Coding-Sessions.
- **Erste messbare Aussage** kommt nach 5 Handelstagen Beweiswoche:
  ``data_health.py`` täglich, ``source_delta.py`` zum Wochenende,
  Review-Doc nach Block-A-Vorbild.
- **C1** (S3-Fremdquelle) ist die einzige Code-Frage, die nach der
  Beweiswoche zu entscheiden ist — basierend auf realen Quoten-/Latenz-
  Zahlen, die bis dahin vorliegen.
- **Push** bleibt bewusste Einzelfreigabe des Nikinger. Stand
  2026-08-19: 15 Commits seit `origin/main`, alle Phase 13, alle
  Phase-12+13-Suiten grün.
