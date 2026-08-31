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

## Session stopped — 2026-08-31 (Session 15: Phase-13-Beweiswoche-Auswertung, 2 Commits, 0 Operator-Aktionen)

> **Auftrag:** Nikinger-Chat 2026-08-31 nach P14-F-Push (~09:30 UTC): „Arbeite an item #5
> weiter" (= Phase-13-Beweiswoche-Auswertung, NEXT-Item aus Mini-Session 22). Mini-Plan-Modus:
> bestehendes source_delta.py-Skript (Block C3, 7 Tests grün) reicht — keine Plan-Session,
> direkte Diagnose. Ausführungs-Scope: **1 Findings-Doc + 2 JSON-Outputs + 3 Phasenkopf-Updates**,
> exakt der Plan, keine Scope-Erweiterung.

### Completed

**1. Diagnose-Lauf (Schritt 0, read-only):**
- `python3 phase13_live_data/scripts/source_delta.py --days 7` → 244 RESOLVED trades, alle `available_but_empty`.
- `python3 phase13_live_data/scripts/source_delta.py --days 14` → 332 RESOLVED trades (70 + 262), 56 `compared` (alle am 2026-08-18) + 276 `available_but_empty`, divergence_rate=53.57%.
- Beide Läufe gegen `data/trading_bot.sqlite?mode=ro` + `data/bars.sqlite?mode=ro` (Phase-13-CLAUDE.md Working-Style).

**2. Substrat-Cross-Check (Schritt 1):**
- IG-Bars im Archiv: 2083 bars, **nur an 2 von 13 Handelstagen** (2026-07-17: 306 bars IBEX.FWM2 + 2026-08-18: 1782 bars 5 Epics). **13-Tage-Lücke seit 2026-08-18 15:41 UTC bis heute (31.08.).**
- yF-Bars: 24284 bars, 11 Tage kontinuierlich (2026-08-17 → 2026-08-28).
- Capital-Bars: 962 bars, 1 Tag (2026-08-21, Operator-Live-Verify-Run).
- `instrument_source_availability` IG-Rows: 8 (status='ok', origin='derived', history_min_days=30, last_verified_utc=2026-08-31T06:47Z). Realität: 0 Epics haben 30 Tage Bars.

**3. Findings-Doc** [`./PHASE13_BEWEISWOCHE_FINDINGS_2026-08-31.md`](./PHASE13_BEWEISWOCHE_FINDINGS_2026-08-31.md) (NEU, ~316 Zeilen):
- §0 BLUF: drei Befunde B1/B2/B3 als Tabelle + D5-Handover-Konsequenz.
- §1 Methodik (was, wie, womit).
- §2 Empirische Befunde im Detail: §2.1 Bars-Substrat-Tabelle (3 Quellen, IG-Lücke explizit), §2.2 `instrument_source_availability` vs. Realität (8 IG-Rows, alle behaupten 30 Tage), §2.3 Source-Delta-Ergebnis 14-Tage-Fenster (332 trades, 56 compared, 30 davon divergent, 18/30 TP↔SL-Gegensatz).
- §3 Was funktioniert (Block C3 Source-Delta-Mechanik, 7 Tests grün, live-verify-bestätigt).
- §4 Was nicht funktioniert (Phase-14-Drift B3: `last_verified_utc` reflektiert instrument_universe-Ableitung, NICHT Bars-Substrat).
- §5 Empfohlene Entscheidungen: D5-Handover **TEILWEISE** (architektonisch ja, operativ nein), Phase-13-Folge-Initiative (Recorder-Mapping-Bug-Hypothesen-Test), Phase-15-Plan-Vorbereitung.
- §6 Empfehlung an den Nikinger (4-Punkte-Liste).
- §7 Cross-Refs (Block-C-Re-Plan, P14-CLAUDE.md, Mini-Session-21-Findings).
- **Commit:** `8aa569f phase13: docs -- Beweiswoche-Findings 2026-08-31 (source_delta-Diagnose, B1/B2/B3)`.

**4. JSON-Outputs (machine-readable, Audit-Trail):**
- `docs/diagnostics/2026-08-31-beweiswoche/source_delta_7d.json` (78KB, 244 trades)
- `docs/diagnostics/2026-08-31-beweiswoche/source_delta_14d.json` (106KB, 332 trades)
- Beide reproduzierbar via `python3 phase13_live_data/scripts/source_delta.py --days N`.

**5. Phasenkopf-Indizierung (3 Docs-Updates):**
- `phase13_live_data/CLAUDE.md` Header-Card: Spezial-Pläne-Zeile erweitert um „Beweiswoche-Auswertung" mit Verweis-Zeile + 3-Befund-Summary + D5-Handover-Status.
- `phase14_discovery/CLAUDE.md` Header-Card: Spezial-Pläne-Zeile erweitert um Phase-13-Beweiswoche-Befund-Verweis + D5-Status-Vermerk.
- `docs/INDEX.md`: 2 neue Einträge — Findings-Doc + Diagnostic-Outputs-Verzeichnis.
- **Commit:** `5af060d docs: index + phasenköpfe -- Phase-13-Findings-Indizierung (Mini-Session 23)`.

**6. Doc-Rotation (gemäß Doc-Layers-Konvention):**
- Session 14 verbatim aus dem Phasenkopf (Z. 98–259) oben ins `SESSIONS_ARCHIVE.md` verschoben (vor Session 13).
- Phasenkopf trägt jetzt genau einen `## Session stopped`-Block (Session 15).
- Pre-Commit-Hook war aktiv (`--strict`); vor der Rotation war head=14, archive-newest=13 → expected 13 → OK, nach der Rotation head=15, archive-newest=14 → OK. Drift wäre gefangen worden.

### Σ-Sweep Stand 2026-08-31 ~10:30 UTC (Mini-Session 23, selbst nachgemessen):

| Phase | Tests grün | Δ zu Mini-Session 22 |
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
| **root tests/** | **101** | unverändert (P14-F Schritt-2-Tests) |
| **Σ** | **1705** | unverändert |

### Findings

🟢 **Source-Delta-Mechanik funktioniert wie designed** (Block C3, 7 Tests grün, live-verify-bestätigt in dieser Session mit 332 trades). Das Tool macht die Beschaffungslücke **sichtbar**, nicht unsichtbar — genau der Phase-13-Antwort auf P12.5.

🟢 **Block-C-Re-Plan-These empirisch vollständig bestätigt:** drei Befunde (B1: IG-Bars-Lücke 2/13 Tage; B2: 53.6 % Divergenzrate am letzten Tag mit Bars; B3: `last_verified_utc` reflektiert nur Discovery-Ableitung, nicht Substrat-Validität). Der Plan war richtig, die Realität ist schlimmer als die Plan-Annahme.

🟡 **Phase-14 D5-Handover: TEILWEISE freigegeben** — architektonisch ja (Tabelle + Discovery + Source-Delta arbeiten wie designed), operativ nein (IG-Spalte lügt, bis Phase-13-Recorder-Mapping-Initiative abgeschlossen ist). Findings-Notiz dokumentiert das; Phase-14-Phasenkopf trägt den Vermerk.

🟡 **Phase-13-Recorder-Mapping-Investigations-Pflicht** — die Hypothesen aus §5.2 der Findings (Stream-Disconnect / Source-Filter / Tick-Aggregation-Bug) sind ungeprüft, müssen in einer Phase-13-Folge-Session geklärt werden. **Nicht in dieser Session** (Phase-14-Scope).

🟢 **Phase-15-Plan-Material** — die heutige Empirie verstärkt den V4-„Quellen-Vertrauens-Modell"-Vorschlag strukturell. Konkrete Forderung: jede `status='ok'`-Zeile in `instrument_source_availability` braucht eine **tatsächliche** Substrat-Coverage-Messung. Phase-15-Territorium, nicht Phase-14.

### Unverändert offen (von Mini-Session 22, weiter gültig)

- **Hook-Verschärfung auf `--strict`-Default** — D5-Beweis erbracht (alle 14 Archive Step-2-konform, diese Session verifiziert: head=15, archive-newest=14 → OK). 15-Min-Folge-Session.
- **Phase-12-Reconciliation-Timing-Fix** — die `reward.recorder: no usable history row`-CRITICALs laufen weiter (P10-V3-Code, nicht in Phase 13/14-Scope).
- **Phase-11-Wiederaufnahme (WI-2/W2)** — Datenfundament-Abhängigkeit.
- **Phase-15-Plan-Session (V4)** — Phase-13-Diagnose-Material jetzt vollständig.

### NEXT (für die nächste Session / morgen)

**Nikinger-Anweisung zum Session-Ende wird erwartet** (Stand ~10:30 UTC = 12:30 CEST — warte auf Nikinger-Wahl).

**Konkrete Empfehlung (sortiert nach Aufwand × Impact, kann der Nikinger umstellen):**

1. **Phase-13-Recorder-Mapping-Investigations-Session** (~1-2h): Hypothesen aus Findings §5.2 verifizieren (Stream-Disconnect / Source-Filter / Tick-Aggregation-Bug), Recorder ggf. neu starten oder Source-Filter korrigieren. **Höchste Priorität** — ohne IG-Bars bleibt die Phase-14-Tabelle operativ unzuverlässig.
2. **Hook-Verschärfung auf `--strict`-Default** (~15 Min): `bash scripts/install_hooks.sh --strict`. D5-Beweis erbracht; das ist eine sichere 15-Min-Session.
3. **Doku-Updates synchronisieren** (~10 Min): root-`CLAUDE.md` Phase-13-Row auf Mini-Session-23-Stand (D5-Status-Vermerk); `ROADMAP.md` Phase-13-Block ggf. Status der Findings; `docs/INDEX.md` Mini-Session-23-One-Liner (optional).
4. **Phase-15-Plan-Session** (großer Block): wenn die Recorder-Initiative (Item 1) IG-Bars zurückbringt, sind die Phase-15-Voraussetzungen vollständig.

**Push-Freigabe:** diese Session hat 2 Commits lokal (`8aa569f`, `5af060d`); Doc-Rotation folgt separat (1 Commit). 3 Commits total, pushbar nach Nikinger-Sign-off.