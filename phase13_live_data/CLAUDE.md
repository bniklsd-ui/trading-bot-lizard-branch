# CLAUDE.md — Phase 13: Live-Datenfundament (`phase13_live_data/`)

> Zwei Fundament-Anläufe sind an derselben Stelle gestorben: **der Verbrauchspfad besorgt sich
> seine Daten selbst.** Phase 13 trennt Beschaffung und Verbrauch endgültig.
> **Quelle der Wahrheit ist der Plan + der Code, nicht dieses Dokument.**
> Vollständiger Plan: [`../docs/concepts/phase13_live_data_plan.md`](../docs/concepts/phase13_live_data_plan.md).
> Vorgeschichte: [`../phase12_data_foundation/PHASE12_5_CLOSEOUT_HANDOVER.md`](../phase12_data_foundation/PHASE12_5_CLOSEOUT_HANDOVER.md).
> Beweiswoche-Auswertung: [`./PHASE13_BEWEISWOCHE_FINDINGS_2026-08-31.md`](./PHASE13_BEWEISWOCHE_FINDINGS_2026-08-31.md) (Mini-Session 23, 2026-08-31) — empirischer Befund: IG-Bars-Lücke seit 2026-08-18, 53.6 % Divergenzrate am letzten Tag mit Bars; Phase-14 D5-Handover **architektonisch freigegeben, operativ vorbehaltlich** Phase-13-Recorder-Mapping-Initiative.

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
| `live_data/backfill.py` | `CapitalSource` (S3, **PARTIAL**) + `run_capital_backfill()` | ✅ Session 12 Step 1 — committed, 11 Tests — final (Block C geschlossen 2026-08-22). Hybrid-Pfad B (Capital.com) liefert DE40 + FR40; SP35 (Spain 35) → 404, fällt auf Path C (Dukascopy, deferred). |
| `live_data/rescue.py` | `GapRescue` (S4, Default AUS) | ✅ C2 — committed, 11 Tests — final (Block C geschlossen 2026-08-22) |
| `scripts/probe_chart_stream.py` | Gating-Live-Check: liefert `CHART:` auf diesem Konto? | ✅ B0 — committed (operator-run, NO 2026-08-19) |
| `scripts/probe_capital.py` | Gating-Live-Check für Hybrid-Pfad B: liefert die Capital.com Demo-API `resolution=MINUTE` für Germany 40 / France 40 / Spain 35? | ✅ Session 11 — committed (operator-run, Probe ausstehend) |
| *(Repo-Wurzel)* `scripts/store_capital_key.py` | Keyring-Seeder für Capital.com Demo-Creds (Service `trading-bot-capital`, drei Felder) | ✅ Session 11 — committed |
| `scripts/capital_backfill.py` | Operator-invokable Gap-Fill-Script: ruft `run_capital_backfill()` für `--epics` oder `--auto` × `[--start, --end]` (UTC) | ✅ Session 12 Step 2 — committed (operator-run) |
| `scripts/source_delta.py` | Doppelauflösung je Quelle, Differenz als Messgröße (P6) | ✅ C3 — committed, 7 Tests — final (Block C geschlossen 2026-08-22) |
| `tests/` | gemockt, kein Netz, kein LLM | ✅ 50 Tests grün |
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

## Session stopped — 2026-08-31 (Session 16: P14-F D5 Hook-Verschärfung + Doku-Sync + IG-Architektur-Sondierung, 3 Commits, 0 Operator-Aktionen)

> **Auftrag:** Nikinger-Chat 2026-08-31 nach Mini-Session 23 (~11:00 UTC): „Erst item #2
> und #3, danach #0 evtl mit Plan nach deiner Einschätzung". Mini-Plan-Modus: drei
> in-line Schritte + eine Sondierung, kein neuer Plan (D5-Ausnahme aus P14-F Plan §2).
> Ausführungs-Scope: **1 Hook-Update + 1 Doku-Sync-Commit + 1 Findings-Update**, exakt
> der Auftrag, keine Scope-Erweiterung.

### Completed

**1. P14-F D5-Ausnahme — Hook-Verschärfung auf `--strict`-Default (Item #2):**
- **Begründung (P14-F Plan §2 D5-Ausnahme):** wenn die ausführende Session nachweisen
  kann, dass alle 14 Phasenarchive die Sequenz-Invariante erfüllen, kann `--strict`
  sofort default werden. **D5-Beweis erbracht in Mini-Sessions 22 (initial) + 23
  (re-verifiziert nach Phase-13-Findings-Indizierung).**
- `scripts/install_hooks.sh` CANONICAL_BODY: `python3 scripts/check_doc_rotation.py --quiet`
  → `python3 scripts/check_doc_rotation.py --strict --quiet`. Kommentar-Block von
  "Step 2 ist opt-in via --strict" auf "Step 2 became default after D5-Beweis
  (Mini-Session 24)" umgestellt; Header von "Also (with --strict flag)" auf
  "Two steps (P14-F, 2026-08-31)".
- Operator-Aktion: `mv .git/hooks/pre-commit .git/hooks/pre-commit.bak-20260831-2`
  (Backup), `bash scripts/install_hooks.sh` (install, 1438 bytes), `bash scripts/install_hooks.sh`
  (idempotent), `bash .git/hooks/pre-commit` (exit 0).
- **Akzeptanz:** repo-weit `--strict` grün; Doc-Rotation-Drift-Klasse aus Mini-Session 21
  ist jetzt **maschinell** gefangen (nicht mehr manuell).
- **Commit:** `c4f7d9c scripts: install_hooks.sh -- --strict jetzt default (P14-F D5, Mini-Session 24, 2026-08-31)`.

**2. Doku-Sync (Item #3):**
- root-`CLAUDE.md` Phase-13-Row: Status von "Beweiswoche ausstehend" auf "ausgewertet
  2026-08-31 (Mini-Session 23)" + Verweis-Zeile zur Findings-Notiz + D5-Handover-Status.
- root-`CLAUDE.md` Phase-14-Row: Block-D-Status auf Mini-Sessions 21+22+23+24 erweitert
  + D5-Handover-Status + P14-F-Ergebnis-Vermerk.
- `ROADMAP.md` Phase-13-Section: Status auf "Beweiswoche ausgewertet" + Findings-Verweis.
- `ROADMAP.md` Phase-14-Section: Status auf "architektonisch freigegeben, operativ
  vorbehaltlich" + P14-F Special-Plan-Verweis + D5-Handover-Status-Absatz.
- `docs/INDEX.md`: 4 Einträge aktualisiert (P14-Phasenkopf, P14-Archive, P13-Phasenkopf,
  P13-Archive).
- **Akzeptanz:** `python3 scripts/check_doc_rotation.py --strict --quiet` exit 0.
- **Commit:** `69b239e docs: sync -- root CLAUDE + ROADMAP + INDEX auf Mini-Session-23/24-Stand`.

**3. IG-Architektur-Sondierung (Item #0):**
- **Code-Sondierung** (`grep -rn "source='ig'"` + `grep -rn SOURCE_IG`): vier Stellen
  identifiziert, die `source='ig'`-Bars schreiben könnten:
  - `phase12_data_foundation/data_foundation/recorder.py:144` → schreibt NUR
    `source=SOURCE_YF` (`'yf'`), keine IG-Output.
  - `phase13_live_data/live_data/stream.py` (LSBarRecorder + TickAggregatorRecorder)
    → schreibt `source='ls'` (CHART-Pfad) oder `source='ls_tick_agg'` (Tick-Agg-Fallback).
  - `phase13_live_data/live_data/rescue.py` (GapRescue) → schreibt `source='ig'`,
    **Default AUS** per Phase-13-CLAUDE.md.
  - `phase13_live_data/live_data/backfill.py` (CapitalSource) → schreibt `source='capital'`.
- **Heutige 2 IG-Tage (17.07. + 18.08.)** sind Operator-gefahrene GapRescue-Einmal-Runs
  (vermutlich B1a-Probe + Block-C-Live-Verify), nicht Teil einer kontinuierlichen Pipeline.
- **`fetched_at`-Analyse 2026-08-18:** IG-Bars geschrieben zwischen 11:10:09 und 13:41:48
  UTC (1782 Bars in 2.5h = ~10/s = klassischer REST-Bulk-Backfill), yF-Bars gleicher Tag
  geschrieben 07:18:22-15:25:20 UTC (103 distinct fetched_at = kontinuierlicher Recorder).
- **TickAggregator läuft NICHT** (kein `stream.py`-Prozess in `ps aux`). Der Scheduler
  hätte ihn via `--enable-bar-stream` aktivieren können (Phase-13 Block B3 wired), aber
  das Flag ist `enable_bar_stream: bool = False` per Default in `config.py:215`.

### **Befund-Inversion (wichtig):**

Item #0 ist **kein Recorder-Mapping-Bug**, sondern eine **architektonische
Design-Frage**. Die Phase-13-Architektur sieht **strukturell keine kontinuierliche
`source='ig'`-Beschaffung** vor:

  - IG ist als **S4-Rettungspfad** (GapRescue, Default AUS, Budget-bound) designed.
  - Die "tägliche" Bar-Lieferung kommt von **yF** (Phase 12 Recorder, läuft) +
    **Capital.com** (Phase 13 Block C, Operator-aktiviert).
  - **`instrument_source_availability.status='ok'` für IG** heißt **"GapRescue-Pfad ist
    prinzipiell verfügbar"**, **nicht** "wird kontinuierlich befüllt". Die Tabelle
    lügt nicht — meine Interpretation in Mini-Session 23 war falsch.

**Konsequenz:** es gibt nichts zu fixen, nur eine **Operator-Entscheidung** zu treffen
(siehe §5 Empfehlungen).

### Σ-Sweep Stand 2026-08-31 ~12:00 UTC (Mini-Session 24, selbst nachgemessen):

| Phase | Tests grün | Δ zu Mini-Session 23 |
|---|---:|---|
| P1 (Broker Wrapper) | 95 | unverändert |
| P2 (Persistence) | 77 | unverändert |
| P3 (External Data) | 104 | unverändert |
| P4 (Research) | 155 | unverändert |
| P5 (Execution) | 173 | unverändert |
| P6 (Debate) | 76 | unverändert |
| P7 (Reward) | 138 | unverändert |
| **P8 (Scheduler)** | **248** | unverändert |
| **P9 (Universe)** | **87** | unverändert |
| P10 (V3) | 165 | unverändert |
| **P12 (Datenfundament)** | **145** | unverändert |
| **P13 (Live-Datenfundament)** | **74** | unverändert |
| **P14 (Discovery)** | **61** | unverändert |
| meta_m1_harness | 28 | unverändert |
| **root tests/** | **101** | unverändert |
| **Σ** | **1705** | unverändert |

### Findings

🟢 **Item #2 abgeschlossen:** `--strict` ist jetzt Hook-Default, P14-F D5-Ausnahme umgesetzt.
Repo-weit grün, Idempotenz bestätigt, Doc-Rotation-Drift-Klasse aus Mini-Session 21 jetzt
maschinell gefangen.

🟢 **Item #3 abgeschlossen:** root-CLAUDE.md Phase-13/14, ROADMAP, INDEX alle auf
Mini-Session-23/24-Stand. Reine Status-Pflege, kein Code.

🟡 **Item #0 invertiert:** kein "Recorder-Mapping-Bug", sondern architektonische
Design-Frage. Drei mögliche Pfade (siehe §5 Empfehlungen). **Plan-Skizze nicht
sinnvoll** — keine Code-Änderung nötig, nur Operator-Entscheidung.

🟢 **Code-Sondierung erbracht:** 4 Pfade identifiziert, die `source='ig'` schreiben
könnten, **keiner läuft kontinuierlich**. Das ist **by design** (Phase-13-S4-Pfad).

### Empfehlungen an Nikinger (§5)

**Pfad A — Operator-S4-Aktivierung:** regelmäßige GapRescue-Runs (z. B. 1× pro
Tag nach Markt-Close) einplanen. **Pro:** echte IG-Coverage für Divergenz-Vergleich.
**Contra:** IG-Budget-Kontingent (10 000/Woche), aktuell **nicht in Verwendung** (Recorder
verwendet yF, das keinen IG-Budget verbraucht).

**Pfad B — Status-Reinterpretation:** `instrument_source_availability.status` für IG
auf `'on_demand'` (oder neu `'gap_rescue_only'`) setzen, statt `'ok'`. **Pro:**
semantisch korrekt, keine Lüge. **Contra:** erfordert Schema-Migration oder
neuen Status-Wert im Vokabular, Phase-14-Code-Touch.

**Pfad C — Architektur-Akzeptanz:** den heutigen Stand akzeptieren (IG-Bars nur bei
Operator-Runs, yF als täglicher Standard), Findings-Notiz um "by design" ergänzen.
**Pro:** kein Code-Touch, kein Schema-Touch. **Contra:** Divergenz-Vergleich zwischen
IG und yF weiter eingeschränkt (nur an Tagen mit beiden Quellen).

**Mein Vorschlag:** **Pfad C** (Architektur-Akzeptanz) + **eine Beobachtungs-Periode**
(1-2 Wochen Beweiswoche ohne aktive IG-Beschaffung), um zu sehen, ob die fe
hlenden IG-Bars operativ wirklich ein Problem sind. Falls ja → Pfad A. Die jetzige
Findings-Notiz sollte mit einem "by design"-Vermerk ergänzt werden, damit die
nächste Session nicht wieder denselben Drift entdeckt.

### Unverändert offen (von Mini-Session 23, weiter gültig)

- **Phase-14 D5-Handover (operativ)** — bleibt formal offen, ist aber mit dem heutigen
  Befund-Inversion **weniger dringend** als angenommen: die Tabelle ist **nicht falsch**,
  sie reflektiert eine **GapRescue-Verfügbarkeit**, keine kontinuierliche Befüllung.
- **Phase-15-Plan-Session (V4)** — gegatet auf Outcomes aus Phase 9+11+12+13+14.
  Mit "by design"-Vermerk wird die Phase-15-Quellen-Vertrauens-Frage neu gerahmt.
- **Phase-12-Reconciliation-Timing-Fix** — `reward.recorder: no usable history row`-CRITICALs.
- **Phase-11-Wiederaufnahme (WI-2/W2)** — Datenfundament-Abhängigkeit.

### NEXT (für die nächste Session / morgen)

**Nikinger-Entscheidung zum Pfad (A/B/C) erwartet** — siehe §5 Empfehlungen.

**Konkrete Empfehlung (sortiert nach Aufwand × Impact):**

1. **Pfad-C-Entscheidung + Findings-Update** (~10 Min): Architektur-Akzeptanz,
   "by design"-Vermerk in der Findings-Notiz anhängen (keine Code-Änderung, nur
   Doku-Korrektur). Schließt den vermeintlichen Drift strukturell.
2. **Doku-Updates synchronisieren** (~10 Min): root-CLAUDE.md Phase-13/14 auf
   Mini-Session-24-Stand (P14-F D5 + Befund-Inversion-Vermerk); ggf. Phase-13-Header
   "Beweiswoche abgelöst durch Architektur-Akzeptanz".
3. **Pfad-A (Operator-S4-Aktivierung)** (~2-3h, Phase-13-Code): GapRescue-Skript
   als Operator-Tool, das regelmäßig (z. B. täglich 17:30 UTC) die letzten
   gehandelten Tage mit IG-Bars befüllt. **Nur wenn Pfad C nicht akzeptabel.**
4. **Pfad-B (Schema-Reinterpretation)** (~1-2h, Phase-14-Code): neuer
   `status='gap_rescue_only'` Wert, IG-Rows umklassifiziert.
6. **Phase-15-Plan-Session** (großer Block): wenn die Architektur-Frage gelöst ist.

**Push-Freigabe:** Items #2 + #3 sind bereits gepusht (`c4f7d9c`, `69b239e`).
Die Befund-Inversion + Pfad-Wahl wird in der nächsten Session entschieden —
dieser Doc-Rotations-Commit folgt (1 Commit, Session-15 → Archiv + Session-16 → Kopf).