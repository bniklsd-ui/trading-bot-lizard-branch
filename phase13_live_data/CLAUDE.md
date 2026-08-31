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

## Session stopped — 2026-08-31 (Session 17: Pfad-C-Entscheidung + Findings §8-Nachtrag, 1 Commit, 0 Operator-Aktionen)

> **Auftrag:** Nikinger-Chat 2026-08-31 nach Mini-Session 24 / Mini-Session 25-Phase-14 (~13:00 UTC): „Gehe erst
> mal mit C, und vermerke das das ein mögliches P15 v4 item ist". Mini-Plan-Modus:
> keine Code-Änderung, nur Doku-Updates (Findings-§8-Nachtrag + Phasenkopf + root-CLAUDE.md).
> Ausführungs-Scope: **1 Commit + Doc-Rotation**, exakt der Auftrag, keine Scope-Erweiterung.

### Completed

**1. Findings-Notiz §8-Nachtrag (Pfad-C-Lesart):**
- **§8.1 "by design"-Vermerk:** B1 (IG-Bars-Lücke 2/13 Tage) ist **kein Defekt**,
  sondern **Architektur-konform** — Phase-13-Architektur sieht **strukturell keine
  kontinuierliche `source='ig'`-Beschaffung** vor; IG ist als **S4-GapRescue-Pfad**
  designed (Default AUS, Budget-bound). B2 (53.6 % Divergenzrate) bleibt ein
  Stichproben-Befund, eingeschränkt auf den Operator-Run-Tag 2026-08-18. B3
  (`last_verified_utc`) ist **semantisch korrekt** unter Pfad C (zeigt
  "Discovery-Ableitung", nicht "kontinuierliche Live-Coverage"). **Phase-14 D5-Handover
  ist jetzt komplett freigegeben** (kein operativer Vorbehalt mehr).
- **§8.2 P15-V4-Kandidatenliste:** drei Items wandern explizit in die P15-V4-Plan-Session:
  - **Pfad A** (Operator-S4-Aktivierung, ~2-3h Phase-13-Code) — wenn echte IG-Coverage
    für Divergenz-Vergleich gebraucht wird. IG-Budget: ~5.6 % (täglicher 1-Tages-Backfill
    der 8 IG-Epics) + ~1.2 % (enable_divergence_sampler) = ~6.8 % des 10 000/Woche-
    Kontingents. **V4 entscheidet.**
  - **Pfad B** (Schema-Reinterpretation, ~1-2h Phase-14-Code, **aufgehoben solange C gilt**)
    — neuer `status='gap_rescue_only'`-Wert, IG-Rows umklassifiziert.
  - **P15-Quellen-Vertrauens-Modell** (Findings §5.3, mit Befund-Inversion neu gerahmt)
    — V4-Frage: "Quellen-**Verfügbarkeit**-Modell" (was die Tabelle heute ist) statt
    "Quellen-**Aktualität**-Modell" (was der ursprüngliche V4-Vorschlag war). Konkret:
    soll V4 die `last_verified_utc`-Semantik umstellen?
- **§8.3 Update-Liste** für die nächste Session: Pfad C ist umgesetzt; P15-Plan-Material
  ist um drei Items erweitert; **Phase-13 ist close-out-fähig** mit Pfad C + §8-Nachtrag
  (eigenständige Closeout-Session jetzt möglich, Pattern siehe Phase-12-Closeout).
- Header `updated:` von `2026-08-31` auf `2026-08-31 (+ §8 Pfad-C-Nachtrag 2026-08-31,
  Mini-Session 24)` erweitert.
- **Dateiwachstum:** 316 → 395 Zeilen (+79).

**2. Phase-13-Phasenkopf Session-16-Block Update:**
- Mein-Vorschlag-Block (Pfad C + Beobachtungs-Periode) durch
  Nikinger-Entscheidung 2026-08-31 (= Pfad C angenommen) ersetzt.
- Verweis auf §8-Nachtrag in Findings-Notiz + P15-V4-Kandidaten-Vermerk.

**3. Root-CLAUDE.md Phase-13 + Phase-14 Rows Update:**
- Phase-13-Row: 'IG-Bars-Lücke (2/13 Tage, by design — IG = S4-GapRescue-Pfad, Default AUS)'
  + 'Phase-14 D5-Handover ist damit komplett freigegeben (kein operativer Vorbehalt mehr)'
  + 'Pfad A und Pfad B sind als P15-V4-Kandidaten in Findings §8.2 dokumentiert'.
- Phase-14-Status-Zeile: 'architektonisch + operativ komplett freigegeben' (vorher
  'operativ vorbehaltlich der Phase-13-Recorder-Mapping-Initiative').
- Phase-14-D5-Handover-Status-Zeile: 'komplett freigegeben (Mini-Session 24, Pfad-C-
  Entscheidung)' + 'IG-Bars-Lücke seit 2026-08-18 ist architektur-konform und als
  P15-V4-Kandidat (Pfad A/B) in §8.2 dokumentiert'.

**4. Akzeptanz:** `python3 scripts/check_doc_rotation.py --strict --quiet` exit 0;
`pytest tests/ -q` 101 passed (unverändert).
- **Commit:** `9600d79 docs: sync -- Pfad-C-Entscheidung Mini-Session 24 (Phase-14 D5 komplett freigegeben)`.

### Findings

🟢 **Pfad C umgesetzt:** keine Code-Änderung, nur Doku. Findings-Notiz §8 hängt jetzt
die by-design-Lesart an; Phase-14 D5-Handover ist **komplett freigegeben** (kein
operativer Vorbehalt).

🟢 **P15-V4-Plan-Session-Material erweitert:** drei konkrete Items (Pfad A, Pfad B,
Quellen-Vertrauens-Modell-Neu-Framing) sind in Findings §8.2 dokumentiert. V4 kann
direkt mit der Quellen-Vertrauens-Diskussion starten.

🟢 **Phase-13 ist close-out-fähig:** mit Pfad C + §8-Nachtrag ist Phase 13 strukturell
fertig (Beweiswoche abgelöst durch Architektur-Akzeptanz). Eine eigenständige
Phase-13-Closeout-Session ist jetzt möglich — Pattern siehe Phase-12-Closeout-Handover.

### Unverändert offen (von Mini-Session 23+24, weiter gültig)

- **Phase-15-Plan-Session** (V4) — Material jetzt vollständig (P14-F D5 ✅, P13-Findings
  + §8, P13-Architektur-Akzeptanz).
- **Phase-12-Reconciliation-Timing-Fix** — `reward.recorder: no usable history row`-CRITICALs
  laufen weiter (P10-V3-Code, nicht in Phase 13/14-Scope).
- **Phase-11-Wiederaufnahme (WI-2/W2)** — Datenfundament-Abhängigkeit.
- **Phase-13-Closeout (optional)** — Pattern siehe Phase-12; kann eigenständige Session werden.

### NEXT (für die nächste Session / morgen)

**Nikinger-Anweisung zum Session-Ende wird erwartet** (Stand ~13:30 UTC = 15:30 CEST —
warte auf Nikinger-Wahl).

**Konkrete Empfehlung (sortiert nach Aufwand × Impact):**

1. **Phase-13-Closeout-Session** (~1h, Pattern-Vergleich zu Phase-12): die Pfad-C-
   Entscheidung + §8-Nachtrag ist strukturell der letzte fehlende Baustein für
   einen Phase-13-Closeout. Eigenständige Doku-Einheit.
2. **Phase-15-Plan-Session** (großer Block): wenn die Beweiswoche genug Outcomes +
   jetzt das P15-V4-Kandidaten-Material für die Quellen-Vertrauens-Diskussion liefert.
3. **Doku-Updates synchronisieren** (~10 Min): root-CLAUDE.md Phase-13/14 Rows
   bereits aktualisiert; ggf. ROADMAP Phase-13-Status auf 'close-out-fähig'.
4. **Phase-12-Reconciliation-Timing-Fix** (~2-3h, Phase-12-Code): die anhaltenden
   `reward.recorder: no usable history row`-CRITICALs angehen.

**Push-Freigabe:** dieser Doc-Rotations-Commit folgt (1 Commit, Session-16 → Archiv +
Session-17 → Kopf); 9600d79 bereits gepusht.