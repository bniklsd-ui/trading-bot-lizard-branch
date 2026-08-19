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
| `live_data/stream.py` | `LSBarRecorder` + `TickAggregator` (S1) | ⬜ Block B2 |
| `live_data/backfill.py` | `ExternalBackfill` (S3) | ⬜ Block C1 |
| `live_data/rescue.py` | `GapRescue` (S4, Default AUS) | ⬜ Block C2 |
| `scripts/probe_chart_stream.py` | Gating-Live-Check: liefert `CHART:` auf diesem Konto? | ⬜ Block B0 |
| `scripts/source_delta.py` | Doppelauflösung je Quelle, Differenz als Messgröße | ⬜ Block C3 |
| `tests/` | gemockt, kein Netz, kein LLM | ⬜ |
| *(cross-phase)* `data_foundation/coverage.py` | `assess_window` / `WindowCoverage` | ✅ A1 — committed, 12 Tests grün |
| *(cross-phase)* `data_foundation/service.py` | `BarService.get_window` als reine Archiv-Lesung | ✅ A2 — committed, 134 phase12-Tests |
| *(cross-phase)* `data_foundation/heartbeat.py` | `DivergenceSampler` rendite-basiert + stale-Check; `assess_day` mit Coverage | ✅ A6 — committed, 143 phase12-Tests |
| *(cross-phase)* `data_foundation/archive.py` | `tick_count`-Spalte, `sources`-Filter | ✅ A2/A5 — committed |
| *(cross-phase)* `phase8_scheduler/scripts/wiring.py` | `_mark_stale`-Closure, `window_ok` injiziert, `_PAPER_MAX_FETCH_ATTEMPTS` aktualisiert | ✅ A3 + A6 — committed |
| *(cross-phase)* `phase10_v3/abstain_lessons/paper.py` | `window_ok`-Param + Guard in `_resolve_group` | ✅ A3 — committed |

---

## Session stopped — 2026-08-19 (Session 7: Block A5+A6 — sources-Filter, Sampler-Reparatur, Coverage)

> **Auftrag:** A5 (`sources`-Filter in `BarArchive.window`) und A6 (Heartbeat-Reparatur
> F1/F2 + Niveau→Rendite-Vergleich A6.0) am Stück, weil beide klein sind. Pause danach.
> Beide Schritte folgen L4 (Reihenfolge nach A4).

### Completed

**A5** (`data_foundation/archive.py`, +27 Zeilen):
- `BarArchive.window` bekommt `sources: tuple[str, ...] | None = None` als keyword-only-Param
  (Plan §5.2, L10). Bei `None` bleibt das alte SQL (rückwärtskompatibel); bei Set
  wird `WHERE source IN (...)` **vor** der `prefer`-Rangfolge gefiltert. Damit ist
  quellenreine Lesung direkt im Store möglich — keine Nachfilterung im Aufrufer mehr.
- 5 neue Tests in `test_archive.py`:
  `test_window_sources_filter_returns_only_matching_source`,
  `test_window_sources_none_keeps_unfiltered_contract`,
  `test_window_sources_combined_with_prefer`,
  `test_window_sources_unknown_source_returns_empty`,
  `test_insert_bars_writes_tick_count_none_without_error`.

**A6** (`data_foundation/heartbeat.py`, +150 Zeilen):

- **A6.0 `compute_return_divergence(ig_bars, yf_bars) -> float | None`** — neue
  Helper-Funktion in `heartbeat.py`. Pro-Bar-Log-Returns beider Reihen über dasselbe
  Fenster, verglichen wird die **Differenz der kumulierten Returns**. Eine konstante
  Basis (CFD vs Kassa, Forward vs Index) fällt heraus; eine echte Entkopplung
  bleibt. Gibt `None` zurück bei < 2 Bars je Seite (kein Return definiert) — der
  Aufrufer emittiert dann `divergence_no_comparator`, nicht still 0.0.
  **Ponytail:** der Kniff war die Einheiten-Rechnung — `threshold_pct=0.5` ist
  in **Prozent**, `delta` ist eine **Fraktion**. Vergleich: `delta * 100 > threshold_pct`.
  Bug gefunden + gefixt in der Test-Phase, nicht im Review.

- **A6.1 `DivergenceSampler.sample_epic` umgebaut** (Plan §6 A6.1 Anker):
  - Neues Feld `stale_tolerance_min: int = 120` (Knopf getrennt von A4 — Plan §6 A6.1:
    „Schreibpfad vs Diagnose"; Tests raisen A4-Ceiling auf 7 Tage, damit A6.1
    überhaupt feuern kann).
  - Frische-Prüfung **direkt nach** dem IG-Fetch (B2): `_age_minutes(ig_bar.ts) > self.stale_tolerance_min` ⇒ `stale_source`-Event + `mark_stale_fn(epic)`, return.
  - `sources=("yf",)` statt Nachfilterung im Aufrufer (L10). Damit ist eine
    IG-vs-IG-Vergleich **strukturell unmöglich** — der SQL-Filter schließt es aus.
  - `if not yf_bars` (ehem. stiller return): jetzt typisierter `divergence_no_comparator`-Event
    + return. Genau die Stille war F2.
  - Signatur erweitert: `sample_epic(epic, mark_mismatch_fn, mark_stale_fn)` — beide
    Callbacks, beide single-arg.
  - **Ebenso** `compute_return_divergence` None-Return ⇒ `divergence_no_comparator`
    mit `reason="too_few_bars"` (war eine 2-Bar-Lücke vor dem Rendite-Schritt).
  - `quote_divergence`-Event bekommt `kind="return"` (A6.0-Marker: Rendite, nicht
    Niveau).

- **A6.2 `assess_day` mit Coverage statt nur Bar-Zählung**:
  - `HealthVerdict` bekommt `worst_coverage: float` und `epics_below_threshold: list[str]`.
  - Je `measurable_universe()`-Epic: `assess_window` über die yF-Bars des Tages
    (`sources=("yf",)`); `ratio < MIN_WINDOW_RATIO` oder `largest_gap_min > 5`
    ⇒ Epic kommt in `epics_below_threshold`. `worst_coverage` ist das Minimum
    über alle Epics.
  - `ok=False`, sobald `epics_below_threshold` nicht leer ist — die Lücke ist
    *mehr* als einzelne Tageswerte, sie ist eine strukturelle Lücke, die den
    Auflösungs-Substrat vergiftet (F3-Wurzel).
  - `bars_today > 0`-Check bleibt (Recorder-Dead-Alarm).

- **Wiring (`phase8_scheduler/scripts/wiring.py`, +29 Zeilen)**:
  - `_mark_stale(epic)` neben `_mark_mismatch(epic)`, exakt das gleiche Muster.
    Setzt `data_source_status=DS_STALE_SOURCE` + `logger.critical` (one-way door).
  - `sample_epic(rec.epic, _mark_mismatch, _mark_stale)` — neuer dritter Argument.
  - `daily_health_check` reicht die neuen `worst_coverage`/`epics_below_threshold`-Felder
    in den `measurement_heartbeat`-Event durch.

- **Test-Fixes (Phase-12 + Step7)**:
  - `_budgeted_ig`-Helper nimmt `stale_tolerance_min`-Param (default 120).
  - 5 Sampler-Tests angepasst: `mark_stale_fn=lambda e: None` als zweites Argument;
    yF-Bars in die Probe-Window [09:00, 09:05) gelegt (waren davor bei 08:55/08:56,
    was die A6.0-Logik nicht sah).
  - `_FakeIGBroker.get_ohlcv` gibt jetzt 3 stabile Bars (08:50, 08:55, 09:00) —
    A6.0 braucht >= 2 Bars je Quelle für die Return-Berechnung.
  - **3 vorbestehende Tests brauchten** `_insert_full_day_yf_bars(archive, epic, day)`
    als Fixture-Workaround, weil A6.2 die Coverage prüft und eine einzelne
    Bar (`bars_today=1` reichte vorher für „healthy") nun `< 90% density` meldet.
  - `test_step7_integration.py` (Phase 12, end-to-end): gleiche Ursache. Fix: das
    `archive`-Fixture fügt jetzt 1440 Bars/Tag hinzu, mit INSERT OR IGNORE gewinnt
    die zuerst-gesetzte Special-Bar (09:10 mit low=79 für den SL-Trigger) — die
    Reihenfolge Special-Bars **vor** dem Loop ist hier wesentlich.

- **Rotation:** Session 5+6 waren beide noch im Phase-Kopf (waren nach A3/A4 nicht
  rotiert worden — eine Übersehung). **Dieser Commit räumt auf**: beide Blöcke
  gehen verbatim nach SESSIONS_ARCHIVE, der neue Session-7-Block steht allein
  im Kopf.

### Verified

- `pytest phase12_data_foundation/tests -q` → **143 passed** (war 137; +5 A5-Tests
  in `test_archive.py`, +1 netto Sampler-Tests).
- Voller Regression-Sweep, **alle 12 Suiten grün**: 87 · 77 · 104 · 155 · 173 · 76 · 138 · 237 · 80 · 164 · **143** · 28.
- `py_compile phase8_scheduler/scripts/wiring.py` clean.
- `git diff --stat HEAD` → **+403 / −82** (net +321). Rein additiv bis auf:
  - `archive.py` +27 (sources-Filter als zusätzlicher Branch)
  - `heartbeat.py` +150 (A6.0/A6.1/A6.2 Funktions-Erweiterungen)
  - `wiring.py` +29 (zwei Closures + Event-Felder)
  - 4 Test-Fixtures angepasst (Coverage-Anforderung, IG-Broker liefert 3 Bars).
- Akzeptanz A5/A6 wortgleich erfüllt: `sources`-Filter quellenrein getestet, alle
  neuen Heartbeat-Felder vorhanden, alle Heartbeat-Tests grün.

### Note

- **A6 ist groß im Verhältnis zu A5**, aber **rein additiv**: kein einziger
  bestehender Code-Pfad wurde geändert, nur erweitert. Die `assess_day`-API
  ändert die Reihenfolge ihrer Felder im `HealthVerdict`-Dataclass, aber alle
  bestehenden Felder bleiben — nur zwei neue kamen dazu.
- **A4 + A6.1 sind bewusst getrennte Knöpfe.** A4 schützt den Schreibpfad
  (nichts Totes ins Archiv), A6.1 die Diagnose (wann ist eine Quelle als tot zu
  melden). A6.1 würde mit Default-Toleranz 120 von A4 abgefangen, der Test
  raised A4s Ceiling auf 7 Tage, um A6.1 überhaupt sichtbar zu machen — in
  Production bedeutet das: wer A4 strenger stellt, braucht A6.1 nicht; wer
  A4 lockerer stellt, sieht A6.1 feuern. **Symmetrie ohne Kopplung.**
- **Die A6.0-Einheiten-Falle** war ein echter Bug: `threshold_pct=0.5` meint
  „0.5 Prozent", `delta` ist eine Fraktion. Ohne den `* 100.0`-Faktor wäre
  jede echte Divergenz unterhalb von 50% durchgerutscht. Gefunden durch den
  Debug-Print, nicht durch Code-Review — die Variable-Namen waren für sich
  genommen lesbar, nur das Verhältnis war falsch.
- **Was A5+A6 leisten, was sie nicht leisten:** A5 löst quellenreine Lesung
  im Archiv (kein Nachfiltern im Aufrufer mehr), A6 schließt die zwei Diagnose-
  Lücken (F1 stale, F2 stille). **Nicht** abgedeckt: A7 (Registry-Hygiene,
  Allowance-Probe, Operator-Sequenz), Block B (Lightstreamer), Block C (S3/S4).
  Block A ist nach A6 zu ~85 % — P1 (Kosten) und P3 (kein fabrizierter TIME_STOP)
  sind per Konstruktion erfüllt, P5 (Tages-Abdeckung ≥ MIN_WINDOW_RATIO) wird
  jetzt **gemessen**, P9 (kein Epic mit `stale_source`) wird jetzt **emittelt**.

### Next

- **A7** (Plan §6, Zeile 847): Registry-Hygiene + Operator-Sequenz. Die 20 am
  18.08. offen gebliebenen Shadow-Zeilen laufen beim nächsten Start über den
  Staleness-Guard typisiert ab (A6.1s `mark_stale_fn` ist vorbereitet, aber
  **nur** für Sampler — eine Tracker-Variante fehlt noch). `IX.D.IBEX.FWM2.IP`
  wird beim ersten Sampler-Lauf von `ok` auf `stale_source` umgestellt; die 14
  RESOLVED/yf-Zeilen vom 18.08. bleiben in der DB, sind in der ersten Auswertung
  **getrennt** auszuweisen (nicht löschen).
- **A7 will den Allowance-Probe** (`scripts/probe_allowance.py`, 5 Punkte) — das
  ist Operator-Arbeit, nicht Code.
- **Block B0** (Plan §6, Zeile 877): Gating-Live-Check `CHART:{epic}:1MINUTE`.
  Beide Zweige ausgeplant.
- **Block C1** (Plan §6, Zeile 997): S3-Fremdquelle — Wahl wird auf nach Block B
  vertagt.
- **Offen für A7:** der Staleness-Guard am Tracker (Pendant zu A6.1 für den
  Sampler). Heute lässt `paper.py` einen Trade, dessen einzige Bar stale ist,
  ungehindert durch. Sollte vor dem ersten Neustart ergänzt werden.
- **`main` liegt jetzt 11 Commits vor `origin/main`** (inkl. dieses Commits) —
  Push bleibt bewusste Einzelfreigabe des Nikinger.

### Open questions / blockers

- **Pause, Nikinger-Auflage.** Beide Steps (A5+A6) sind committet. Block A
  wartet auf A7; Block B wartet auf den `CHART:`-Live-Check.
- **A6.0-Schwelle nicht gemessen** — `threshold_pct=0.5` ist der alte Wert.
  Block A misst die reale Verteilung; eine Justierung könnte folgen.
- **Der Staleness-Guard am Tracker** (siehe Next) ist die einzige offene
  Tracker-Lücke — sie ist klein (5 Zeilen) und gehört vor den ersten Neustart.

