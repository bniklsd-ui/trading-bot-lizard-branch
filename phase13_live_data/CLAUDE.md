# CLAUDE.md — Phase 13: Live-Datenfundament (`phase13_live_data/`)

> Zwei Fundament-Anläufe sind an derselben Stelle gestorben: **der Verbrauchspfad besorgt sich
> seine Daten selbst.** Phase 13 trennt Beschaffung und Verbrauch endgültig.
> **Quelle der Wahrheit ist der Plan + der Code, nicht dieses Dokument.**
> Vollständiger Plan: [`../docs/concepts/phase13_live_data_plan.md`](../docs/concepts/phase13_live_data_plan.md).
> Vorgeschichte: [`../phase12_data_foundation/PHASE12_5_CLOSEOUT_HANDOVER.md`](../phase12_data_foundation/PHASE12_5_CLOSEOUT_HANDOVER.md).
> **Status: ✅ abgeschlossen (Closeout 2026-08-31, Session 18).** Code-complete (Blöcke A + B + C, Stand 2026-08-22) + Beweiswoche ausgewertet (Mini-Session 23) + Pfad-C-Entscheidung (Mini-Session 24) + Befund-Inversion. Phase-14 D5-Handover ist **komplett freigegeben** (kein operativer Vorbehalt mehr).
> Vollständiger Closeout-Handover (das erste Dokument jeder Folge-Session an Phase 13):
> [`./PHASE13_CLOSEOUT_HANDOVER.md`](./PHASE13_CLOSEOUT_HANDOVER.md) — 5-Zeilen-Bilanz + L1–L18 + F1/F2/F3 + B1/B2/B3 + Pfad-C-Entscheidung + Datei-Anker + Konsistenz-Regeln + Don'ts.
> Beweiswoche-Befund (Mini-Session 23): [`./PHASE13_BEWEISWOCHE_FINDINGS_2026-08-31.md`](./PHASE13_BEWEISWOCHE_FINDINGS_2026-08-31.md) — empirischer Befund (B1 IG-Bars-Lücke 2/13 Tage, B2 53.6 % Divergenzrate, B3 `last_verified_utc`-Semantik).
> Pfad-C-Nachtrag: ebd. §8 (Mini-Session 24, 2026-08-31) — IG = S4-GapRescue-Pfad (Default AUS), **Architektur-konform** (kein Recorder-Mapping-Bug).

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
| `tests/` | gemockt, kein Netz, kein LLM | ✅ **74 Tests grün** (Stand 2026-08-31, +24 seit 2026-08-22 durch Phase-14-Cross-Phase-Block-B2/B3-Edits in `live_data/backfill.py`, `scripts/source_delta.py`, `scripts/probe_capital.py` — Cross-Phase-Test-Zuwachs, nicht Phase-13-Eigenleistung) |
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
| `PHASE13_BEWEISWOCHE_FINDINGS_2026-08-31.md` | Beweiswoche-Befund (B1/B2/B3) + §8 Pfad-C-Nachtrag (Mini-Session 23+24) | ✅ — committed |
| `PHASE13_CLOSEOUT_HANDOVER.md` | **Closeout-Handover (2026-08-31, Session 18)** — Phase 13 abgeschlossen | ✅ — committed (diese Session) |

---

## Session stopped — 2026-08-31 (Session 18: Phase-13-Closeout-Handover, 1 Commit, 0 Operator-Aktionen)

> **Auftrag:** Nikinger-Chat 2026-08-31 nach Mini-Session 26½ Phase-7 (~09:30 UTC, nach
> `restart-services.sh restart` der neuen Phase-7-Backoff-Code-Basis): Pre-Test des
> Phase-7-Backoff-Fixes zuerst, dann Phase-13-Closeout-Session starten. Mini-Plan-Modus:
> keine Code-Änderung an Phase-13, nur Doku-Updates (Closeout-Handover neu, Phasenkopf
> Session-Rotation, Status-Flip).
> Ausführungs-Scope: **1 Commit + Doc-Rotation**, exakt der Auftrag, keine Scope-Erweiterung.

### Completed

**0. Vorab — Phase-7-Backoff Pre-Test (Nikinger-Anweisung Z. 2 „Pre-Test als erste Aktion"):**
- `pytest phase7_reward/tests -v -k backoff` → A2/A3 grün (2 Tests selektiert, weil
  `-k backoff` nur die wortstammhaltigen Tests matcht).
- A4/A5 zusätzlich explizit: `pytest phase7_reward/tests/test_recorder.py -v -k
  "backoff_skip_within_window or persistent_fail_warning or preclaim_idempotent_concurrent
  or backoff_replay_reduces_critical_count"` → **4 passed** (alle A2–A5 grün).
- Optional: historische OPEN-Trades per SQLite manipulieren + `source_delta.py`
  → **0 OPEN-Trades** in `data/trading_bot.sqlite` (`SELECT status, COUNT(*) FROM
  trade_outcomes`: CLOSED|8, OPEN|0). Per Nikinger-Anweisung: optional entfällt,
  A6 bleibt 24-h-Live-Observe.
- **Ergebnis:** Pre-Test grün, Phase-13-Closeout-Session freigegeben.

**1. `phase13_live_data/PHASE13_CLOSEOUT_HANDOVER.md` (NEU voll-strukturiert):**
- **Pattern:** Phase-12-CLOSEOUT-HANDOVER (§0 BLUF + 5-Zeilen-Bilanz, §1 Architektur,
  §2 Locks L1–L17, §3 Befunde F1/F2/F3, §4 As-Built, §5 Test/Live/Produktion,
  §6 Delta, §7 Decisions, §8 Datei-Anker, §9 Konsistenz-Regeln, §10 Don'ts,
  §11 Was diese Session gemacht hat).
- **Phase-13-spezifisch:** L18 (IG ist Default AUS) als zusätzlicher Lock,
  B1/B2/B3 als zusätzliche Befunde-Sektion (§3.2), §4.4 Inventar-Zahlen mit aktuellem
  Stand (74 Tests, 53 Commits, Σ 1703 grün), §7 E8/E9 mit Pfad-C-Entscheidung
  + Quellen-Vertrauens-Modell-Framing.
- **Header:** `status: snapshot`, `purpose: Phase-13-Closeout-Handover (2026-08-31) — Phase 13 ✅ abgeschlossen`, `updated: 2026-08-31`.

**2. Phase-13-Phasenkopf-Status-Flip:**
- Header-Zeile 8: '🔄 code-complete → ✅ abgeschlossen (Closeout 2026-08-31, Session 18)';
  Phase-14 D5-Handover 'komplett freigegeben'.
- Modul-Tabelle: `tests/` Zeile aktualisiert auf **74 Tests grün** (war 50,
  +24 seit 2026-08-22 durch Cross-Phase-Phase-14-Block-B2/B3-Edits in
  `live_data/backfill.py`, `scripts/source_delta.py`, `scripts/probe_capital.py`).
- Modul-Tabelle: zwei neue Zeilen für `PHASE13_BEWEISWOCHE_FINDINGS_2026-08-31.md`
  (Beweiswoche-Befund + §8 Pfad-C-Nachtrag) und `PHASE13_CLOSEOUT_HANDOVER.md`
  (Closeout-Handover).
- **Drift-Korrektur:** "50 Tests" war seit Session 17 stale; Code = source of truth
  (74 ist real, `pytest phase13_live_data/tests -q` reproduziert).

**3. Session-17 → Archiv + Session-18 → Phasenkopf (Doc-Rotation per CLAUDE.md
Rotation rule, mandatory since 2026-07-06):**
- Session-17-Block (Pfad-C-Entscheidung + Findings §8-Nachtrag, 96 Zeilen) verbatim
  aus dem Phasenkopf nach `phase13_live_data/SESSIONS_ARCHIVE.md` verschoben (newest-first
  vor Session-16). Pre-Commit-Hook (`--strict`) **vorher** geprüft (head=17,
  arch-newest=17 → expected 16 → ✅ konform).
- SESSIONS_ARCHIVE-Preamble von truncated backticks auf vollständige
  `## Session stopped`-Rotation-Regel-Referenz korrigiert.
- Phasenkopf trägt jetzt genau einen `## Session stopped`-Block (Session 18).

**4. Akzeptanz:** `python3 scripts/check_doc_rotation.py --strict --quiet` exit 0;
`pytest phase13_live_data/tests -q` 74 passed (war 50 in Session 17, +24 seit
Closeout-Stand 2026-08-22); Σ-Sweep 1703 grün repo-weit.

### Σ-Sweep Stand 2026-08-31 ~11:30 UTC (Session 18, selbst nachgemessen):

| Phase | Tests grün | Δ zu Session 17 |
|---|---:|---|
| **P13 (Live-Datenfundament)** | **74** | **+24** (Cross-Phase-Phase-14-Block-B2/B3-Edits, dokumentiert in §4.4 Closeout) |
| Phase-14 (Discovery) | 61 | unverändert |
| Phase-12 (Datenfundament) | 145 | unverändert |
| Phase-8 (Scheduler) | 248 | unverändert |
| Phase-9 (Universe) | 87 | unverändert |
| Phase-10 (V3) | 165 | unverändert |
| Phase-7 (Reward) | 142 | unverändert |
| Phase-2 (Persistence) | 77 | unverändert |
| Phase-1 (Broker Wrapper) | 95 | unverändert |
| Phase-3 (External Data) | 104 | unverändert |
| Phase-4 (Research) | 155 | unverändert |
| Phase-5 (Execution) | 173 | unverändert |
| Phase-6 (Debate) | 76 | unverändert |
| root tests/ | 101 | unverändert |
| **Σ total** | **1703** | **+24** |

### Findings

🟢 **Phase 13 ist abgeschlossen.** Beweiswoche gelaufen (B1/B2/B3 empirisch), Pfad-C
entschieden (IG = S4-GapRescue, Default AUS, by-design L18), Befund-Inversion
("kein Recorder-Mapping-Bug" — Architektur-konform). Phase-14 D5-Handover
komplett freigegeben (kein Vorbehalt).

🟢 **Pattern-Vergleich zu Phase-12-CLOSEOUT erfüllt:** §0 BLUF + 5-Zeilen-Bilanz,
§1 Architektur-Bild, §2 Locks, §3 Befunde, §4 As-Built, §5 Test/Live, §6 Delta,
§7 Decisions, §8 Datei-Anker, §9 Konsistenz-Regeln, §10 Don'ts, §11 Was diese
Session gemacht hat. Phase-13-spezifisch erweitert um L18 (IG-Default-AUS-Lock)
und B1/B2/B3 (Beweiswoche-Befunde als Ergänzung zu F1/F2/F3).

🟢 **Phase-13-spezifische Konsistenz-Regel §9.6 ergänzt:** "IG ist Default AUS als
Live-Quelle" — die Pfad-C-Entscheidung wird zur achten Konsistenz-Regel (eine mehr
als Phase-12 hat), damit ein zukünftiges Re-Litigieren der IG-Default-Frage
strukturell an dieser Regel hängen bleibt.

🟡 **Plan-Drift Closeout-Header:** bestehender PHASE13_CLOSEOUT_HANDOVER.md-Header
(2026-08-22) hatte keinen YAML-Header-Card (war essay-style). Diese Session hat
den Header nachträglich auf YAML-Header-Card-Form gebracht (analog Phase-12).
Header-Inhalt ist **gleichbedeutend**, nur strukturell normalisiert — keine
inhaltliche Änderung an §0–§7 (außer die explizite Pfad-C-/Beweiswoche-/Befund-
Inversion-Sektionen, die 2026-08-22 noch nicht existierten).

🟡 **Substrat-Total-Drift 14 846 → 14 699:** war im 2026-08-22-Closeout stale; +147
durch Coverage/Stale-Assertion-Aufräumarbeiten seit 2026-08-22 (nicht durch
Datenverlust). Substrat-Stand 2026-08-31 self-consistent.

🟢 **Cross-Phase-Touches minimal:** nur Phase-13-Files (1 NEU
PHASE13_CLOSEOUT_HANDOVER.md + 1 Update Phasenkopf + 1 Update SESSIONS_ARCHIVE.md);
Cross-Phase-Files (`live_data/`, `data_foundation/`) **nicht** angefasst.

### Unverändert offen (von Mini-Session 23+24, weiter gültig)

- **Phase-15-Plan-Session** (V4) — Material jetzt vollständig (P14-F D5 ✅, P13-Findings
  + §8, P13-Architektur-Akzeptanz, P12-Reconcile-Timing-Backoff = 4 P15-V4-Kandidaten).
- **Phase-12-Reconciliation-Timing-Fix Live-Verify (A6)** — wartet auf nächsten OPEN-
  Trade (heute 0 OPEN); 24-h-Beobachtung. Pre-Test grün (4 von 4 Backoff-Tests A2–A5).
- **Phase-11-Wiederaufnahme (WI-2/W2)** — Datenfundament-Abhängigkeit.
- **P14-F `--strict`-Default** — bereits aktiv seit Mini-Session 24 (Session 16-Block
  im Archiv). Folge-Mini-Session kann den Installer `--strict` als Default setzen.
- **Phase-13-closeout.svg** — bewusst aufgeschoben (Phase-13 hat kein Fehlerbild;
  Empfehlung: Phase-15-Plan-Session zeichnet ein gemeinsames
  `phase13_14_15.svg`-Gesamtbild).

### NEXT (für die nächste Session / morgen)

**Nikinger-Anweisung zum Session-Ende wird erwartet** (Stand ~12:00 UTC = 14:00 CEST —
warte auf Nikinger-Wahl).

**Konkrete Empfehlung (sortiert nach Aufwand × Impact):**

1. **Phase-15-Plan-Session** (V4) — ✅ **abgeschlossen 2026-08-31** (Plan-Commit `f98df68`, Nikinger-Freigabe `aad1d00`); Phase 15 in execution seit 2026-08-31, Block A in Ausführung, Blöcke B/C/D danach — siehe [`../phase15_v4/CLAUDE.md`](../phase15_v4/CLAUDE.md) + Plan [`../docs/concepts/phase15_v4_plan.md`](../docs/concepts/phase15_v4_plan.md). *korrigiert 2026-08-31 (Phase-15 A-6):* Material ist nicht nur „vollständig", sondern **schon geplant + in execution**.
2. **Phase-12-Reconciliation-Timing Live-Verify (A6)** (~24-h-Beobachtung am
   Live-Betrieb): nächster OPEN-Trade mit IG-Lag soll ≤ 5 CRITICALs in 24 h
   produzieren (vorher 6+ in 52 min). Pre-Test grün (4 von 4 Backoff-Tests A2–A5,
   Session 18 verifiziert).
3. **Phase-13-closeout.svg** (~1h, optional): Empfehlung gemeinsam mit Phase-15
   als `phase13_14_15.svg`-Gesamtbild, kein Solo-SVG.
4. **Status-Pflege-Hygiene** (~5 Min, Doc-only): root-CLAUDE.md `## Current state`-
   Header (Z. 93) zeigt immer noch "Phase 8 ✅ abgeschlossen" als letzten
   ✅-Status (war vor Phase-10/12/13-Closouts); Phase-13-Closout-Status kann
   dort erwähnt werden, ist aber nicht Phase-13-Closeout-Scope (eher
   Mini-Hygiene-Session).

**Push-Freigabe:** dieser Closeout-Commit ist der einzige Commit dieser Session;
enthält **kein** Cross-Phase-Produktionscode-Edit. Sweep Σ 1703 grün, kein Bot-Touch.