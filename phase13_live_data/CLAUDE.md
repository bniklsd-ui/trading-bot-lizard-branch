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

## Session stopped — 2026-08-22 (Session 14: Block-C-Re-Plan & Phase 14 (Discovery) Concept)

> **Auftrag:** Nikinger-Run 2026-08-22 hat den Session-13-Bugfix live
> gegen das Capital.com-Demo-Konto bestätigt (962 Bars: 481 DAX + 481
> CAC, exakt im Session-13-Erwartungsbereich). Plus Nikinger-Entscheidung:
> die "discovery-then-deterministic"-Architektur aus Session 13 ist
> umfangreich genug für eine **eigene Phase 14** (V4 rutscht auf Phase 15).
> Diese Session: (a) Block C schließen (Re-Plan + Live-Verified), (b) den
> 5-Zeilen-Test-Fix nachholen, (c) das Phase-14-Concept skizzieren, (d) die
> Nummerierungs-Kaskade ausführen.

### Completed

**Test-Fix `test_multiple_days_window` (Commit `074d6c9`).** Hardcoded
Daten `2026-08-18/19` lagen ausserhalb des `--days 2`-Filters (`[today-1, today]`),
sobald `today > 2026-08-19`. Fix: `datetime.now(timezone.utc).date() +
timedelta(days=...)`, ~5 Zeilen. Offen seit Session 12 (zweimal dokumentiert),
heute erstmalig gebaut. Phase-13-Suite jetzt 50 passed (war 49 + 1 jetzt grün).

**Live-Verified-Vermerk in Session-13-Block (vor Rotation).** Der
Operator-Lauf-Befehl + Output + Verifikation wurden in den
Session-13-Block (vor seiner Rotation ins Archiv) als eigene
Subsection eingehängt, damit die Audit-Kette lückenlos ist.

**Rotation: Session 13 → SESSIONS_ARCHIVE.md** (verbatim, mit dem
Live-Verified-Anhängsel aus dem vorherigen Edit), Session 14 = der
aktuelle Head-Block.

**Block-C-Re-Plan** [`docs/concepts/phase13_c_block_c_replan.md`](../../docs/concepts/phase13_c_block_c_replan.md).
Definiert:
- L1: Block C ist final (kein Dukascopy-Code, kein Auto-Gap-Fill,
  keine `EPIC_MAP`-Erweiterung in `live_data/`).
- L2: "Discovery-Then-Deterministic" wird Phase 14, nicht
  Block-C-Erweiterung.
- L3: V4 rutscht auf Phase 15.
- L4: Beweiswoche bleibt gültig; Block C hat die Werkzeuge geliefert.
- §1: was C1/C2/C3 einzeln geleistet haben (live-verifiziert für DE40/FR40).
- §2: warum Block C jetzt schließt (drei strukturelle Gründe).
- §3: was Phase 14 leisten wird (Concept-Skizze).
- §4: Akzeptanz B1–B5 (heute erreicht).
- §5: Schritt-Sequenz für die Phase-14-Planning-Session.
- §6: Drift-Liste.

**Phase-14-Concept-Skizze** [`docs/concepts/phase14_discovery_concept.md`](../../docs/concepts/phase14_discovery_concept.md).
L0-BLUF + Mission, drei Bausteine (Quell-Profil, Kreuzungs-Tabelle,
Konsumenten-Umstellung), Outcome-Tabelle, Scope-Disziplin, Verhältnis
zu Phase 13 + 15, sieben offene Fragen für die Plan-Session, klare
Trennung „was dieses Concept ist / nicht ist". **Bewusst kein
execution-ready Plan** — der folgt in einer eigenen Planungssession.

**Nummerierungs-Kaskade (L3):**
- Root-`CLAUDE.md` Phase-13-Row: Status auf „code-complete + live-verifiziert
  für DE40/FR40" korrigiert (war stale "Bau nicht begonnen"); Phase-14-Row
  **neu** angelegt (Discovery); Phase-15-Row: V4 mit Verweis auf die dritte
  Umnummerierung 2026-08-22.
- `ROADMAP.md` Phase-13-Section: Block-Stand-Tabelle neu, Phase-14-Section
  **neu** (Concept-Verweis, Goal, Why-this-is-its-own-phase, Scope-Skizze);
  Phase-14→15 Umnummerierung der V4-Sub-Bullets (14a/b/c/d/e → bleibt
  a/b/c/d/e, Heading „Phase 15 — V4 ..."). Directory-Hinweis
  `phase12_v4/` → `phase15_v4/`.
- `docs/INDEX.md`: zwei neue .md-Zeilen (Re-Plan + Concept), Phase-13-Row
  korrigiert (Modul-Status & Live-Verify), Phase-10/11-Row „V4 is now Phase
  14" → „V4 is now Phase 15" (Präzedenzfall), Phase-13-LiveData-Plan-Zeile
  mit Korrekturhinweis auf den Snapshot. „Active phases"-Header ergänzt um
  Phasen 13/14.

**Modul-Tabelle-Update kommt in einem Folge-Commit** — der Plan-Snapshot
selbst bleibt unberührt, der Re-Plan ist die kanonische Aussage.

### Verified

- Regression-Sweep, alle 13 Phasen + root `tests/` (Stand vor den
  Docs-Edits, aber unverändert): 1508 passed.
  | Phase | Tests |
  |---|---|
  | phase1_broker_wrapper | 95 |
  | phase2_persistence | 77 |
  | phase3_external_data | 104 |
  | phase4_research | 155 |
  | phase5_execution | 173 |
  | phase6_debate | 76 |
  | phase7_reward | 138 |
  | phase8_scheduler | 244 (+1 Deprecation-Warning) |
  | phase9_universe | 80 |
  | phase10_v3 | 165 |
  | phase12_data_foundation | 143 |
  | phase13_live_data | 50 (vor Fix: 49 + 1 jetzt grün) |
  | meta_m1_harness | 28 |
  | root `tests/` | 80 |
- `data/bars.sqlite` (`mode=ro`): 962 `source='capital'`-Bars (481 DAX + 481 CAC)
  bestätigt. Kein Bot-Prozess läuft (`ps aux | grep scheduler.run` leer).

### Note

- **Drei Commits in dieser Session** (Nikinger-Auflage „commit after each
  step" gilt weiter):
  1. `074d6c9` `phase13: test -- fix test_multiple_days_window date-drift`
  2. *(dieser Docs-Commit)* `phase13: docs -- Session 14 + Block-C-Re-Plan
     + Phase-14-Concept + Nummerierungs-Kaskade`
- **Plan-Snapshot `phase13_live_data_plan.md` bleibt unverändert** (📕
  Convention, „never edit"). Seine INDEX-Beschreibung wurde mit einem
  Korrekturhinweis „Plan-Snapshot sagt V4 → 14, gilt tatsächlich V4 → 15"
  versehen, damit der historische Stand sichtbar bleibt, ohne den Snapshot
  zu fälschen.
- **`EPIC_MAP = {"IX.D.DAX.IFMM.IP": "DE40", "IX.D.CAC.IFE.IP": "FR40"}`**
  in `live_data/backfill.py:67-72` bleibt im Code. Das ist Absicht: das
  Phase-14-Architektur-Diff ist groß genug für eine eigene Phase, nicht für
  eine Block-C-Erweiterung. Sobald Phase 14 die `instrument_source_availability`-
  Tabelle hat, ist diese Map eine Migrations-Zeile.
- **V4-Inhalt unverändert.** Die Umnummerierung Phase 14 → 15 ist rein
  numerisch, kein Inhalt verschoben. Inhaltlich bleibt V4 das, was es
  immer war: Council, Handover, Reward-Reform, Force-Trigger, Instinct-ECC.
  Es kommt nur **ein** zusätzliches Gate dazu (Phase 14), nicht
  inhaltliche Änderung.

### Next

- **Operator (Nikinger):** Push-Freigabe für die zwei Commits (`074d6c9` +
  dieser Docs-Commit). Stand jetzt: **40 Commits** vor `origin/main`.
- **Phase-14-Planning-Session (eigene, neue):** liest zuerst den
  Block-C-Re-Plan + das Phase-14-Concept, dann den Phase-13-Hauptplan
  (L1–L17), dann die Phase-12.5-Closeout (Lehre „nicht im Konsumentenpfad
  kaufen"). Schreibt `docs/concepts/phase14_discovery_plan.md` mit
  gelockten Decisions D1–D?, Steps 0–?, Drift-Liste, Akzeptanz.
- **Phase-14-Planning-Session Schritt 0.0** (aus Re-Plan §5):
  Regression-Sweep + `ps aux | grep scheduler.run` (Gegenprobe) + Live-DB-
  Stand frisch (heutige `instrument_source_availability`-Substrat-Grösse).
- **Cross-Phase-Freigabe** für Phase 14 (Nikinger): die Discovery-Tabelle
  berührt Phase 2 (Migration), Phase 3 (yFinance), Phase 9 (Universe),
  Phase 13 (`backfill.py`). Vor dem ersten Code-Schritt einholen — analog
  zur Phase-13-Freigabe 2026-08-18.
- **Beweiswoche läuft parallel** (Phase 13 Plan §7 P1–P9). `data_health.py`
  täglich, `source_delta.py` wöchentlich. P6 (Quellen-Delta-Report) hat mit
  den 962 `source='capital'`-Bars jetzt ein echtes Substrat.

### Offene Findings (für Folge-Sessions, nicht in diesem Build-Scope)

- **Modul-Tabelle in `phase13_live_data/CLAUDE.md` ist nicht aktualisiert**
  (Test-Count 39 statt 50, Block-C-Zeilen brauchen ein „final"-Tag).
  Bewusst NICHT in diesem Commit geändert — der Plan-Snapshot und die
  Re-Plan-Datei sind die kanonische Aussage, der Phasen-Kopf folgt in
  einer Folge-Session (oder direkt mit der Phase-14-Eröffnung).
- **Plan-Snapshot `phase13_live_data_plan.md`** könnte im §0 BLUF einen
  kleinen Verweis auf den Re-Plan verdienen (analog zur Phase-12.5-
  Closeout-Anmerkung). Bewusst nicht in diesem Commit — der Snapshot
  ist „never edit", und das Hinzufügen erfordert eine eigene Diskussion
  (Snapshot ergänzen vs. nur per Korrekturhinweis im INDEX).
- **`source_delta.py` P6-Auswertung** mit den 962 Capital-Bars wurde im
  Beweiswoche-Review vermessen — die Belege für die Phase-14-Quell-
  Auswahl kommen erst nach 1–2 Beweiswochen.
- **Live-Substrat für Phase-14-Plan-Session**: heute 962 `source='capital'`-
  Bars + 2230 IG + 11654 yF + LS-Anteil = ~14.846 Bars im Archiv. Das ist
  das **Entdeckungs-Substrat**, gegen das `instrument_source_availability`
  in Phase 14 gefüllt wird. Die Plan-Session sollte den heutigen Stand
  frisch messen.
