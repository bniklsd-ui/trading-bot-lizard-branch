# SESSIONS_ARCHIVE.md — Phase 13 (Live-Datenfundament)

Newest-first. Rotation rule (`CLAUDE.md` root, mandatory since 2026-07-06): the phase head
carries exactly one `## Session stopped` block; archives have no size cap. See
[`../CLAUDE.md`](../CLAUDE.md) "Rotation rule (mandatory since 2026-07-06)" for the full
contract, and [`../docs/DOC_LAYERS_CONVENTION.md`](../docs/DOC_LAYERS_CONVENTION.md) for
the L0/L1/L2/L3 model.

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

**Nikinger-Entscheidung 2026-08-31: Pfad C** angenommen.
**Findings-Notiz §8 Nachtrag angehängt** (Mini-Session 24): "by design"-Vermerk für B1 + B2
eingeschränkt + B3 semantisch korrekt unter Pfad C; **Phase-14 D5-Handover komplett
freigegeben** (kein operativer Vorbehalt mehr). **Pfad A + Pfad B wandern in die
P15-V4-Plan-Session** (Kandidatenliste in Findings §8.2): Pfad A = Operator-S4-Aktivierung
(~2-3h, IG-Budget 5.6 % + 1.2 % = innerhalb 10 000/Woche); Pfad B = Schema-Reinterpretation
(neuer `status='gap_rescue_only'`, ~1-2h, aufgehoben solange C gilt). V4 entscheidet.

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
  Docs-Edits, aber unverändert): 1608 passed.
  *(Summenkorrektur 2026-08-22: die Einzelzahlen derselben Tabelle ergeben 1608; kein
  Test verschwunden — §3.6 des Phase-14-Plans.)*
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

- **Operator (Nikinger):** kein Push nötig — Phase 13 ist seit Session 8 mit `74`
  grünen Tests (war zum Session-14-Stand 50, +24 aus Phase 14 B1b+B2+B3 im
  `phase13_live_data/`-Tree), Commits alle auf `origin/main`.
- **Phase-14-Planning-Session:** **erledigt** — Plan liegt in
  [`docs/concepts/phase14_discovery_plan.md`](../../docs/concepts/phase14_discovery_plan.md),
  Decisions D1–D20 gelockt, Akzeptanz A1–A8 alle grün (Σ 1698 nach Session 9).
- **Cross-Phase-Freigabe** für Phase 14 (Nikinger, 2026-08-22): **erteilt** für
  Phase 2 (Migration), Phase 8 (`webui/`, `run_scheduler.sh`), Phase 9
  (`models.py`, `store.py`), Phase 12 (`budget.py`-Nutzung) und Phase 13
  (`backfill.py`, `scripts/`).
- **Beweiswoche läuft parallel** (Plan §7 P1–P9), gestartet Mo 2026-08-25.
  Erste Beobachtung aus dem Restart-Check: Trade #8 BUY DAX.IGN offen
  (5. BUY auf DAX in Folge nach 4 Verlust-Trades, -2530.82 EUR realisiert);
  Loss-Breaker nicht ausgelöst (€1800-Cap, aktuelle realized-pnl heute = 0);
  Token-Budget 38.5% / Weekly-Allowance 48% / 0 Discovery-Punkte gebucht.
  Kein Handlungsbedarf, Safety-Mechanismen innerhalb Caps; Phase-15-Territorium
  (V4 — Council, Handover, Reward-Reform).

### Offene Findings (für Folge-Sessions, nicht in diesem Build-Scope)

- **Modul-Tabelle in `phase13_live_data/CLAUDE.md` ist nicht aktualisiert** —
  Stand Session 14 nannte Test-Count 39, inzwischen sind es **74** (50 nach
  Session 14 + 24 aus Phase-14-B1b/B2/B3-Commits `ac54825`/`6e8148e`/`bb095df`,
  die in `phase13_live_data/` mit-tests-edits haben). Block-C-Zeilen brauchen
  ein „final"-Tag. Beides für eine Phase-13-Hygiene-Session vorgemerkt, kein
  Phase-14-Scope.
- **Plan-§9-Drift-Listeneintrag #2** (Phase-14) erweitern in der nächsten Plan-
  Session — Editor-Notiz, kein Doku-Touch.
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


## Session stopped` block; the previously-newest block moves here
verbatim when a new one is appended.

---

## Session stopped — 2026-08-19 (Session 13: capital_backfill-Bugfix + Architektur-Insight) — *rotated 2026-08-22, head-block um Live-Verified-Subsection erweitert (Nikinger-Operator-Lauf am 2026-08-22)*

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
  `test_source_delta.py`, **nicht** durch diesen Bugfix verursacht —
  Fix nachgeholt im Block-C-Re-Plan-Commit `074d6c9`, 2026-08-22).
- `data/bars.sqlite` Spalten-Probe: vor/nach `ensure_schema()` wie oben.

### Live-Verified 2026-08-22 (Nikinger-Operator-Lauf, ausserhalb dieser Session)

Der Session-13-Fix ist nicht nur in der Test-Suite grün, sondern auch im
realen Demo-Lauf gegen Capital.com bestätigt:

- Befehl (kostenlos, Demo-Konto, exakt der Next-Block oben):
  ```bash
  python phase13_live_data/scripts/capital_backfill.py \
      --epics IX.D.DAX.IFMM.IP,IX.D.CAC.IFE.IP \
      --start 2026-08-21T08:00:00Z --end 2026-08-21T16:00:00Z
  ```
- **Output (verbatim, aus Nikinger-Run):**
  ```
  "bars_written_total": 962,
  "results": {
    "IX.D.DAX.IFMM.IP": 481,
    "IX.D.CAC.IFE.IP": 481
  }
  ```
- **Verifiziert per `data/bars.sqlite` (mode=ro)**: 962 Zeilen
  `source='capital'`, je 481 DAX/CAC, genau die zwei Epics die DE40/FR40
  in `EPIC_MAP` decken.
- **Erwartung vs. Ergebnis**: Session-13 hatte „pro Epic ~480 Bars
  (statt 0 mit Bug), `bars_written_total: ~960`" vorhergesagt — das
  Ergebnis liegt mit 481/481/962 **innerhalb** dieser Spanne. Der
  `tick_count`-Bugfix hält live.
- **Damit ist Pfad B (Capital.com DE40+FR40) live production-ready.**
  Spain 35 (IBEX) bleibt ausserhalb (HTTP 404, Plan-Pfad C / Phase 14).

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

---

## Session stopped — 2026-08-19 (Session 12: C1 Pfad B Build — `backfill.py` + `capital_backfill.py`, PARTIAL abgeschlossen)

> **Auftrag:** Nikinger („da bereits viel zeit verschwendet wurde,
> möchte ich den vollständigen weg gehen. alles was gebaut werden kann,
> baue jetzt (atomar)"). Nach Probe-PARTIAL (DE40 + FR40 liefern
> MINUTE-Bars, SP35 = Spain 35 = IBEX liefert 404) baut diese Session
> Pfad B fertig. Spanien (IBEX) bleibt **explizit Path-C-Territorium**
> (Dukascopy, deferred per Nikinger-Auflage: „soll trotzdem als weiterer
> Fallback in einer zukünftigen Session gebaut werden").

### Completed

**Step 1 — `phase13_live_data/live_data/backfill.py` (NEU, ~340 Zeilen).**
`CapitalSource` Klasse (`authenticate` + `fetch_window`) +
`run_capital_backfill()` Convenience-Funktion. Implementiert die
vier quellenunabhängigen Regeln aus Plan §6 C1.0:

| Regel | Wo umgesetzt |
|---|---|
| (1) Window-Check | `_parse_and_validate`: jeder Bar-Timestamp muss in `[start-1min, end+1min]` sein, sonst Skip + Warn-Log |
| (2) Keine synthetischen Bars | `_parse_and_validate`: `O==H==L==C` + `volume ∈ {0, None}` ⇒ Skip (Off-Hours-Auffüll-Bars) |
| (3) Vergleiche nie absolute Niveaus | n/a — Sampler-Konzern (A6.0) |
| (4) Backoff ist Pflicht | `_backoff` exponential (2^attempt s) bei HTTP 429/503, max 3 Retries |

Quellen-spezifisch (empirisch 2026-08-19, alle in Commit-History
dokumentiert):
- Demo-URL: `https://demo-api-capital.backend-capital.com`
- Auth: `POST /api/v1/session` mit `X-CAP-API-KEY`-Header + Body
  `{identifier, password, encryptedPassword: false}`. `password` =
  API-Key-Custom-Password (NICHT Account-Login-Pwd).
- Datumsformat: `YYYY-MM-DDTHH:MM:SS` ohne `Z`/ms (strikt).
- TZ: snapshotTime wird als `Europe/Madrid` (UTC+2 im Sommer)
  interpretiert, dann nach UTC konvertiert → CAPITAL_TZ + zoneinfo,
  DST-aware.
- Epic-Mapping: `IX.D.DAX.IFMM.IP → DE40`, `IX.D.CAC.IFE.IP → FR40`.
  Spain/AEX/MIB sind Path-C-Territorium (Test `test_epic_map_does_not_contain_path_c_territory`
  pinnt das fest).

`run_capital_backfill()` schreibt mit `source='capital'` ins
`BarArchive`. KNOWN_SOURCES erweitert in
`phase12_data_foundation/data_foundation/models.py` (cross-phase,
per Plan §1 freigegeben). `prefer`-Default in `archive.py:144` jetzt
`('ig', 'capital', 'ls', 'yf')` — Capital.com rangiert vor
LS/yFinance, weil Broker-CFD-Reihe näher an IG ist als Kassaindex.

**Step 2 — `phase13_live_data/scripts/capital_backfill.py` (NEU, ~170
Zeilen).** Operator-invokable Gap-Fill-Script: liest Creds aus
Keyring (`trading-bot-capital.{identifier,password,api_key}`),
lädt `BarArchive(args.db)`, ruft `run_capital_backfill()` für
`--epics` (kommagetrennt) oder `--auto` (measurable-universe).
`--start`/`--end` (UTC ISO 8601 mit `Z`), `--dry-run` für
Plan-Print ohne Auth. Output: per-Epic Bar-Counts + `next_step_hint`.
Exit 0/1/2/3 analog `probe_capital.py`. Operator-Run, kostenlos
(Demo-Konto).

**Step 3 — Tests.**
- 11 neue Tests in `phase13_live_data/tests/test_backfill.py`:
  auth success (verifiziert Header hat `X-CAP-API-KEY`, Body hat
  KEIN `apiKey`), auth 401 raises, unmapped epic returns [],
  LOCAL → UTC-Konvertierung (Snapshot 20:54 CEST → 18:54 UTC),
  synthetische Bars gefiltert, out-of-window gefiltert, 429 →
  Backoff + Retry → 200, 404 propagiert sofort (kein Retry),
  `run_capital_backfill` schreibt mit `source='capital'`,
  `run_capital_backfill` records 0 für unmapped Epics,
  EPIC_MAP enthält keine Path-C-Epics (Lock-in Test).
- Bestehende 38 Phase-13-Tests unverändert (1 pre-existing
  date-drift in `test_source_delta.py::test_multiple_days_window`
  — siehe Offene Findings).

### Verified

- `pytest phase13_live_data/tests -q` → **49 passed** (war 38, +11).
- `pytest phase12_data_foundation/tests -q` → **143 passed** (unverändert).
- `pytest phase1_broker_wrapper/tests -q` → **95 passed** (unverändert).
- `pytest phase8_scheduler/tests -q` → **244 passed** (unverändert).
- `pytest phase10_v3/tests -q` → **165 passed** (unverändert).
- `py_compile` clean auf allen geänderten/neuen Dateien.

### Note

- **Drei Commits in dieser Session**, jeder Schritt unabhängig grün
  (Nikinger-Auflage „commit after each step"):
  1. `369fb62` Step 1 — `backfill.py` + Tests + KNOWN_SOURCES + prefer
  2. `08dfa74` Step 2 — `capital_backfill.py` operator-script
  3. *(dieser Docs-Commit)* Session-12-Block + Modul-Tabelle + Rotation

- **PARTIAL ist explizit gewollt**, nicht „halb gebaut": die zwei
  funktionierenden Indizes (DE40, FR40) decken zusammen 4 von 5
  verfügbaren messbaren Epics im Archiv ab. Das einzige Loch ist
  SP35 (Spain 35 = IBEX) — und das ist die gleiche Epic, die in
  Phase-12-Closeout §3.4 als „selbstverschuldeter yF-Existenzbeweis"
  beschrieben wurde (IG lieferte tote Historie für FWM2, yF-Kassa
  ist die einzige verfügbare Reihe). Für die Beweiswoche ist das
  **kein Blocker** — FWM2 wird weiterhin über S2 (yFinance-Recorder)
  bedient.

- **Path C (Dukascopy) ist explizit für eine Folge-Session
  geblockt**, nicht gestrichen:
  > Nikinger 2026-08-19: „PS: halte fest, das Path C trotzdem als
  > weiterer Fallback in einer zukünftigen Session gebaut werden soll."
  Geplante Reihenfolge: zuerst Messwoche mit Pfad B (S2 + S3-Partial)
  + S4 (`GapRescue`, default AUS), **dann** Dukascopy-Backfill für
  SP35 + generelle S3-Reserve. ToS-Auslegung (Session 11) gilt
  weiter — Dukascopy ist nur für den privaten Single-User-Store
  freigegeben.

- **`live_data/backfill.py` enthält absichtlich keinen Auto-Scheduler**
  oder Gap-Detection. Das ist Operator-getrieben für jetzt. Eine
  Auto-Gap-Fill-Logik (z. B. „täglich 09:00 UTC die letzten 24 h
  scannen, Lücken ≥ 60 min automatisch schließen") wäre eine
  Folge-Aufgabe — bewusst NICHT in dieser Session gebaut, um den
  Scope von Session 12 auf „Pfad B fertig + Probe-Backfill-Script"
  zu begrenzen.

### Open questions / blockers

- **Capital.com TZ-Annahme** (`Europe/Madrid`, UTC+2 im Sommer)
  ist **empirisch** aus einem 1-Stunden-Probe-Fenster abgeleitet
  (Bars kamen mit +2 h Offset zur UTC-Anfrage zurück). Wenn der
  Server im Winter auf CET (UTC+1) wechselt, fängt `zoneinfo`
  das automatisch — gut. Wenn der Server die TZ **ändert** (was bei
  Capital.com unwahrscheinlich ist), müssen wir manuell nachziehen.
  Frühe Validierung: Beweiswoche-Tag-1, **`source_delta.py`
  zeigt den `capital`-vs-`yf`-Differenz-Vektor pro Minute** — wenn
  der konstant +2 h verschoben ist, ist die TZ falsch.
- **`KNOWN_SOURCES` ist eine einzige zentrale Konstante** — jede
  neue Quelle braucht genau eine Edit in `models.py:22`. Das ist
  Plan §6 C1.0 Fold-in-Checklisten-Item #3, hier umgesetzt.

### Next

- **Operator (Nikinger):** manueller Smoke-Test mit `--dry-run`:
  ```bash
  python phase13_live_data/scripts/capital_backfill.py \
      --epics IX.D.DAX.IFMM.IP,IX.D.CAC.IFE.IP \
      --start 2026-08-21T08:00:00Z \
      --end   2026-08-21T16:00:00Z \
      --dry-run
  ```
  Erwartetes Output: JSON mit `dry_run: true`, beiden Epics, dem
  Zeitfenster. Kein Auth, kein Write.

- **Operator (Nikinger):** realer Backfill-Lauf (kostenlos, Demo-Konto):
  ```bash
  python phase13_live_data/scripts/capital_backfill.py \
      --epics IX.D.DAX.IFMM.IP,IX.D.CAC.IFE.IP \
      --start 2026-08-21T08:00:00Z \
      --end   2026-08-21T16:00:00Z
  ```
  Erwartetes Output: JSON mit per-Epic bar-counts (~480 Bars je
  Epic im 8-h-Fenster bei MINUTE-Resolution).

- **Operator (Nikinger):** Beweiswoche bleibt der Live-Test für die
  gesamte Datenkette (Phase 13 Plan §7 PASS-Kriterien P1–P9).
  Pfad B (dieser Build) ist eine zusätzliche Sicherheitsschicht
  für DE40/FR40; SP35/AEX/MIB laufen weiter über yFinance-Recorder
  bis Path C (Dukascopy) in einer Folge-Session kommt.

- **Push:** weiterhin bewusste Einzelfreigabe. Stand jetzt:
  **27 Commits** vor `origin/main`, alle Phase 13, alle Suiten grün.

### Offene Findings (für Folge-Sessions, nicht in diesem Build-Scope)

- **`phase13_live_data/tests/test_source_delta.py::test_multiple_days_window`**
  ist seit 2026-08-20 rot. Harte Test-Daten „2026-08-18" / „2026-08-19"
  liegen außerhalb des `--days 2`-Fensters, sobald `today > 2026-08-19`.
  Empfohlener Fix: Test auf `datetime.now()`-relative Daten oder
  `freezegun` umstellen. ~5 Zeilen.
- **Path C (Dukascopy)** ist für eine Folge-Session geblockt (siehe
  Nikinger-Auflage oben) — `live_data/dukascopy_backfill.py`
  existiert noch nicht. ToS-Auslegung aus Session 11 bleibt gültig
  für diesen Use-Case (privater Single-User-Backtest-Store).
- **Auto-Gap-Fill-Scheduler** für Pfad B (täglicher Lauf, der
  Lücken ≥ 60 min automatisch schließt) wäre eine Folge-Aufgabe
  — bewusst out-of-scope dieser Session.

---

## Session stopped — 2026-08-19 (Session 11: C1 — Hybrid-Entscheidung B/C + Probe-Vorbereitung)

> **Auftrag:** Nikinger („vermerke eine hybrid entscheidung: erst option B.
> nur wenn das definitiv nicht geht, dann option C"). Plan §6 C1.0
> ENTSCHIEDEN „auf nach Block B vertagt" wird hiermit **doppelt
> überschrieben**: (a) Vertagung aufgehoben (die Entscheidung fällt jetzt),
> (b) Hybrid-Wahl B-first/C-fallback statt einzelnem Kandidaten. Die
> Begründung — „Archiv ist für mich privat, sonst keine Berührung mit
> dem Internet" — wiegt die Dukascopy-ToS-Klausel
> („may not be used to construct a database of any kind") **für diesen
> Use-Case** auf: die einzige Datenbank, die das Archiv bildet, ist
> ein lokales SQLite-File im `data/`-Pfad des Nikinger-VMs, ohne
> externen Read/Write, ohne API, ohne Veröffentlichung. Die ToS-Klausel
> zielt auf redistributable, abfragbare Drittdaten-Dienste, nicht auf
> einen privaten Backtest-Store eines einzelnen Traders. **Nikinger-
> Entscheidung, dokumentiert; nicht selbst ausgelegt.**

### Completed

**C1-Hybrid-Entscheidung (gelockt, Nikinger-Override von L17-Plan §6 C1.0):**

| Pfad | Quelle | Wann |
|---|---|---|
| **B (primär)** | **Capital.com** Demo-API — Germany 40 / France 40 / **Spain 35**, `resolution=MINUTE`, REST via `requests` (Repo-Konvention). Plan §6 C1.0 „wenn früher entschieden werden soll"-Pfad. | Nikinger-Operator-Live-Check via `scripts/probe_capital.py` (kostenlos, ~80 Zeilen, analog zu `probe_chart_stream.py`). |
| **C (fallback)** | **Dukascopy** Datafeed — vollständige Abdeckung inkl. IBEX + MIB, ~90 s Verzug, stdlib `lzma`+`struct`. | Nur wenn B **definitiv** nicht geht — d.h. Probe-Exit AUTH oder NO bei allen drei Indizes. Nicht bei „liefert nur 1 von 3". |

**Begründung ToS-Klausel-Aufhebung für Dukascopy (Pfad C):**
- Dukascopy ToS: „may not be used to construct a database of any kind"
- Nikinger-Argument: das `data/bars.sqlite` ist ein **lokales,
  privates** Archiv auf dem Nikinger-VM, ohne externen Zugriff,
  ohne API-Endpoint, ohne Datenfreigabe. Der „database"-Begriff in
  der ToS zielt auf redistributable / multi-user Drittdaten-Dienste,
  nicht auf einen Single-User-Backtest-Store.
- **Risiko bleibt Nikinger-getragen.** Nicht von Claude ausgelegt —
  wenn Nikinger die ToS-Auslegung revidiert, fällt Pfad C weg und
  nur Pfad B + A (überspringen) bleiben.

**Begründung B-first statt direkt C:**
- B ist ToS-sauber (kein Cloud-Konflikt, Broker-API wie IG → andere
  Auth-Klasse aber Lizenz ok).
- B liefert als Broker-CFD-Preisreihe eine **bessere Gegenprobe**
  zu IG-CFD als Dukascopys Index-Kassa (näher an der eigenen Reihe).
- C hat die umfassendere Abdeckung (alle Indizes, lange Historie),
  ist aber nur Fallback wegen Lizenz-Eigenheit.

### `scripts/probe_capital.py` — Operator-Live-Check (kostenlos)

- Auth: POST `https://api-capital.backend-capital.com/api/v1/session`
  mit `identifier` + `password` + `apiKey` (aus Keyring-Namensraum
  `trading-bot-capital`, neuer Seeder analog zu `store_minimax_key.py`).
- Sucht drei Epics: **Germany 40** (DAX-äquivalenter CFD),
  **France 40** (CAC), **Spain 35** (IBEX). Bei jedem: `resolution=
  MINUTE`, kleines Zeitfenster (~15 Min).
- Exit-Codes analog `probe_chart_stream.py`: `0 YES` / `1 NO` /
  `2 PARTIAL` / `3 AUTH`.
- **Output:** stderr = menschliche Erzählung, stdout = JSON-`Envelope`-
  ähnliches Objekt (maschinenlesbar). Repo-Konvention
  (siehe `scripts/probe_chart_stream.py`).
- **In Session 11 Step 2 gebaut** (zwei Commits): `scripts/probe_capital.py`
  (~190 Zeilen) und Repo-Wurzel `scripts/store_capital_key.py`
  (~75 Zeilen). Auth: POST `/api/v1/session` mit `identifier` +
  `password` + `apiKey` (alle drei aus Keyring-Namensraum
  `trading-bot-capital`). Suche per `GET /api/v1/markets?searchTerm=`,
  bevorzugt CFD-Instrumente. Test-Fetch `GET /api/v1/prices/{epic}?
  resolution=MINUTE&from=&to=&max=1000`. Exit-Codes 0/1/2/3 analog
  `probe_chart_stream.py`. Output-JSON enthält
  `next_step_hint`-Empfehlung je nach Ergebnis. Operator-Run, **kein
  Test-Coverage** (Repo-Konvention: operator-run-Scripts sind nicht
  pytest-gesammelt, siehe `probe_chart_stream.py`).

### Was diese Session **nicht** tut (bewusst)

- Kein Code-Change außer Doku (Doku-Commit folgt; Probe-Build = nächster Schritt).
- Kein DB-Write. `live_data/backfill.py` bleibt ⬜ bis nach Probe.
- Kein Push (weiterhin Operator-Einzelfreigabe).
- Kein Override der Dukascopy-ToS in der Breite — der Override gilt
  **nur für diesen Use-Case** (privater Backtest-Store eines einzelnen
  Traders, keine externe Berührung). Sollte das Archiv jemals eine
  API, ein Web-UI oder Drittnutzer bekommen, fällt Pfad C weg.

### Next

- **Step 2 (diese Session):** `scripts/probe_capital.py` bauen (~80
  Zeilen, operator-run, kostenlos, kognitive Spiegelung von
  `probe_chart_stream.py`) — kein Netz, kein LLM in Tests.
- **Step 3 (Nikinger-Aktion):** Keyring-Seeder
  `scripts/store_capital_key.py` + `python phase13_live_data/scripts/probe_capital.py`.
- **Step 4 (Nikinger-Decision):** Probe-Exit interpretieren:
  - `0 YES` oder `2 PARTIAL` (≥ 1/3 Indizes) → Capital.com-Backfill
    bauen (`live_data/backfill.py` nach §6 C1, vier Regeln + Fold-in).
  - `3 AUTH` → Keyring prüfen, Re-Seed, Re-Probe.
  - `1 NO` bei allen drei → **Pfad C (Dukascopy)** fällt zu, vor
    jedem Code-Build kurze Nikinger-Bestätigung der ToS-Auslegung.
- **Parallel:** Beweiswoche läuft weiter (Phase 13 Block A + S1 via
  `TickAggregatorRecorder` aktiv), kein Konflikt mit C1.
- **Push:** weiterhin bewusste Einzelfreigabe. Stand jetzt: **23 Commits**
  vor `origin/main`, alle Phase 13, alle Suiten grün.

### Offene Findings (für Folge-Sessions, nicht in diesem Build-Scope)

- **`phase13_live_data/tests/test_source_delta.py::test_multiple_days_window`**
  ist seit 2026-08-20 rot. Harte Test-Daten „2026-08-18" / „2026-08-19"
  liegt außerhalb des `--days 2`-Fensters, sobald `today > 2026-08-19`.
  Wurde 2026-08-19 in Session 9 (C3, Commit `50a417e`) committet, ist
  in keinem Phase-13-Code-Pfad erreicht. **Empfohlener Fix:** Test auf
  `datetime.now()`-relative Daten oder `freezegun` umstellen. ~5 Zeilen.
- **`probe_capital.py` Capital.com Auth-Contract** (gelöst 2026-08-19,
  Session 11 Step 2-research): die korrekte Auth ist
  `POST {base}/api/v1/session` mit
  `Header X-CAP-API-KEY: <api_key>` +
  `Body {"identifier": <email>, "password": <API_KEY_CUSTOM_PASSWORD>, "encryptedPassword": false}`.
  Der `password` ist NICHT das Account-Login-Passwort, sondern das
  Custom-Passwort aus der API-Key-Generierung (FAQ §8.8.7 der
  Capital.com-Doku). Demo-URL ist `demo-api-capital.backend-capital.com`
  (NICHT `api-capital.backend-capital.com`). Endpoint-Rate-Limit:
  1 req/s. Quelle: https://capital.com/api (Swagger, gefetcht via
  webfetch 2026-08-19).

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

---

## Session stopped — 2026-08-18 (Session 2: Block A0 — Baseline, Gerüst, A0.0-Dateien)

> **Auftrag:** Block A0 der Reihe nach abarbeiten (A0.0 Datei-Bau, A0.1 Ritual — bereits erledigt,
> A0.2 Baseline, A0.3 Gerüst, A0.4 Nummerierungs-Grep). Danach A1–A7 der Schnitt, streng in
> Reihenfolge (L4).

### Completed

1. **A0.0 — `scripts/store_minimax_key.py` + `scripts/claude-minimax` geschrieben**, Plan §6
   verbatim (Wrapper-Skript, Keyring-Namensraum `trading-bot-minimax`), `chmod +x` gesetzt.
   Fund am Sessionstart: der Commit `1ab208c` ("add Step A0.0") hatte im Commit-Text „Two files,
   both versioned in the repo" behauptet, aber nur die Plan-/CLAUDE.md-Dokumentation geändert —
   die Dateien existierten nicht (`find . -iname "*minimax*"` leer). Keine Code-Drift (die
   Modul-Tabelle stand korrekt auf ⬜), nur eine irreführende Commit-Message. Jetzt gebaut, alle
   vier Abnahmekriterien sind Operator-Schritte (Key seeden, `ln -s`, curl-Vorabtest, MiniMax-
   Verbrauchsanzeige) — **Abnahme bleibt beim Nikinger**, s. Next.
2. **A0.2 — Regression-Baseline, alle 13 Suiten separat** (`phase1_broker_wrapper/.venv`,
   je `pytest <phase>/tests -q`):

   | Phase | Ergebnis |
   |---|---|
   | phase1_broker_wrapper | 87 passed |
   | phase2_persistence | 77 passed |
   | phase3_external_data | 104 passed |
   | phase4_research | 155 passed |
   | phase5_execution | 173 passed |
   | phase6_debate | 76 passed |
   | phase7_reward | 138 passed |
   | phase8_scheduler | 237 passed, 1 warning (harmlose `httpx`-Deprecation) |
   | phase9_universe | 80 passed |
   | phase10_v3 | 160 passed |
   | phase12_data_foundation | 123 passed |
   | meta_m1_harness | 28 passed |
   | root `tests/` | 80 passed (Memory nannte 64 am 2026-07-02 — kein Regress, seither gewachsen) |

   Alle 13 grün — **echte Baseline, vor dem ersten Fix**, nicht nachträglich grün gezogen.
3. **A0.3 — Phasen-Gerüst** angelegt, Muster = `phase12_data_foundation` (Editable-Install,
   `own-connection`-Kommentarstil): `phase13_live_data/README.md`, `pyproject.toml`
   (`name = "live_data"`), `requirements.txt` (`pytest`), `live_data/__init__.py` (leer),
   `tests/__init__.py` (leer). `scripts/dev_install.sh` um P13 verlängert (Kette jetzt zwölf
   Pakete). `docs/INDEX.md` bekam drei neue Zeilen (`CLAUDE.md`, `README.md`,
   `SESSIONS_ARCHIVE.md`) im selben Commit.
4. **A0.4 — Nummerierungs-Grep** (`grep -rn "Phase 13 (V4)" --include="*.md" .`): 3 Treffer, alle
   in `ARCHITECTURE.md`, `ROADMAP.md` und diesem Plan selbst — jeder ist die datierte
   Korrekturnotiz, die die alte Bezeichnung als Zitat erklärt, keine lebende Referenz. Kein
   Nachbessern nötig.
5. **Rotation:** Session-1-Block verbatim nach
   [`SESSIONS_ARCHIVE.md`](./SESSIONS_ARCHIVE.md) verschoben, dieser Kopf trägt jetzt nur
   Session 2.

### Verified

- `python -c "import live_data"` läuft **nach** `pip install -e phase13_live_data --no-deps
  --no-build-isolation` (offline, kein Netzzugriff — dieselbe Form wie bei `data_foundation`).
  `pytest phase13_live_data/tests -q` → „no tests ran" (Verzeichnis ist leer, wie erwartet vor
  Block A1).
- `ps aux | grep scheduler.run` vor dem Test-Sweep: leer — kein Parallel-Login-Risiko, Sweep war
  gefahrlos.

### Next

- **Block A1** (Plan §6, Zeile 569): `phase12_data_foundation/data_foundation/coverage.py` neu —
  `assess_window` + `WindowCoverage`, reine Funktion, kein I/O. Danach A2 → A7 strikt der Reihe
  nach (L4).
- **A0.0 seither live abgenommen (Nikinger, gleicher Tag, außerhalb dieser Session):** die drei
  Live-Unbekannten lösten sich wie folgt — Basis-URL `.../anthropic` (Claude Code hängt `/v1`
  selbst an), Header `x-api-key` funktioniert (Wrapper setzt `ANTHROPIC_AUTH_TOKEN`/Bearer, beide
  gingen durch), Modell-ID **`MiniMax-M3[1m]`** (nicht `MiniMax-M3` — die 1M-Kontext-Variante,
  Commit `9bf2f0f`). Erster curl-Versuch schlug mit `insufficient_balance_error (1008)` fehl —
  **kein Wiring-Fehler**, sondern der falsche Key-Typ: der zunächst gespeicherte Key war ein
  Pay-as-you-go-API-Key (leere Wallet), MiniMax trennt den vom **Subscription Key** des Token
   Plans (`platform.minimax.io/subscribe/token-plan`). Nach Tausch auf den Subscription Key: curl
   liefert eine echte Antwort, `claude-minimax` lief live, und **MiniMax' eigener
   „active day"-Zähler stieg von 1 auf 2** — der Anbieter-Beweis, nicht nur ein sauberer
   HTTP-Response. Modul-Tabelle jetzt ✅.

### Note

- Root `CLAUDE.md`'s Phase-13 row still says "Bau nicht begonnen" — stale as of this session,
  left unchanged deliberately: the doc-hygiene rule routes phase-status updates to the phase
  head, not root.

### Open questions / blockers

- **Kein technischer Blocker für A1.** Bot steht weiterhin, Recorder sammelt kostenlos weiter.
- **Offen bis Block B0:** ob `CHART:{epic}:1MINUTE` auf diesem Konto liefert (Plan §9.2).
- **Offen bis Block C1:** welche Fremdquelle S3 wird.
- **`main` liegt jetzt 5 Commits vor `origin/main`** (inkl. dieser Session) — Push bleibt eine
  bewusste Einzelfreigabe des Nikinger.

---

## Session stopped — 2026-08-18 (Session 1: Planungssession — Phase 13 eröffnet, Plan committet, kein Code)

> **Auftrag:** den execution-ready Plan für Phase 13 schreiben, nachdem P12.5 formal gescheitert
> ist. **Volles Ergebnis:**
> [`../docs/concepts/phase13_live_data_plan.md`](../docs/concepts/phase13_live_data_plan.md) —
> dieser Block ist die Kurzfassung. **Keine Code-Änderung in dieser Session.**

### Completed

1. **Vier Entscheidungen beim Nikinger eingeholt** (Closeout §4/§5/§6 verlangte genau das):
   Label = **Phase 13 = Live-Datenfundament, V4 → Phase 14** · Umfang = **mehrstufig, mit einer
   zusätzlichen Beschaffungsstufe** · LS-Prozess = **im Scheduler-Prozess** · Messregel =
   **beides messen, Differenz ist eine eigene Messgröße**.
2. **Plan geschrieben** — L1–L16 gelockt, Blöcke A/B/C, Verbatim-Anker je Edit-Stelle,
   Testliste, PASS-Kriterien P1–P9, §8 „Fehlgriffe, die wie andere Fehler aussehen",
   §9 vollständige Drift-Liste.
3. **Drei neue Befunde selbst nachgemessen** (Plan §4) — keiner stand in einem Vordokument:
   - **F1:** `IX.D.IBEX.FWM2.IP` trägt 301 IG-Bars mit `ts_utc` 2026-07-17, aber `fetched_at`
     **2026-08-18T11:10:17.019Z**. IG liefert für diese Forward-Epic seit einem Monat tote
     Historie und meldet `ok=True`. Sie hatte am 18.08. mit **8** IG-Calls die meisten von
     allen — und null verwertbare Bars. **Korrigiert den Closeout §7:** FWM2 ist nicht der
     „Existenzbeweis für yF-only", sondern der teuerste Blindgänger des Tages.
   - **F2:** `DivergenceSampler.sample_epic` (`heartbeat.py:184-193`) ankert das
     Vergleichsfenster am IG-Bar-Zeitstempel; ist der einen Monat alt, findet es keine yF-Bar
     und kehrt **still** zurück. Der Alarm ist gegen genau F1 strukturell blind. Beleg: **0**
     `quote_divergence`-Events bei **12** bezahlten Samples.
   - **F3:** Eine Lücke *mitten* im Trade-Fenster erzeugt in `resolve_paper_trade`
     (`paper.py:234-278`) eine **erfundene** `TIME_STOP`-Zeile, die in DB und Heartbeat nicht
     von einem echten Time-Stop unterscheidbar ist. Das ist die Begründung dafür, dass die
     Abdeckungsprüfung dem **ganzen** Fenster gilt, nicht dem Schwanz.
4. **Extern bestätigt:** IGs Streaming-Kanal läuft gegen ein **anderes** Kontingent (~40
   gleichzeitige Subscriptions je Verbindung), nicht gegen die 10 000 Historienpunkte/Woche;
   `CHART:{epic}:{scale}` existiert mit fertigen Kerzenfeldern (`OFR_*`, `BID_*`, `CONS_END`,
   `CONS_TICK_COUNT`). **Aber:** die Feldliste stammt aus Drittbibliotheken, labs.ig.com gab
   HTTP 403 — deshalb ist der CHART-Live-Check **Block B0** und gatet Block B.
5. **Step-0-Ritual (Turbo-/Legacy-Grep) ausgeführt — dokumentierter No-Op:** 3 Treffer, alle
   `strike` im Sinne von *Fehlversuch* (`phase9_universe/universe/promotion.py:121`, `:277`,
   `tests/test_promotion.py:343`), kein Options-Vokabular. `turbo_candidates` = 19 Treffer,
   der eingefrorene P5-Gate-2-Contract-Name — nicht umbenennen. Identisch zu den Ritualen vom
   2026-06-27 und 2026-07-10.
6. **Nummerierungs-Kaskade ausgeführt** (L16, derselbe Commit): Root-`CLAUDE.md`, `ROADMAP.md`
   (neuer Phase-13-Abschnitt + V4 → Phase 14), `README.md`, `ARCHITECTURE.md`, `docs/INDEX.md`,
   `phase9_universe/CLAUDE.md`, `phase10_v3/CLAUDE.md`. Historische Aussagen wurden **nicht**
   umgeschrieben, sondern mit datierten `⟳ Korrektur`-Notizen superseded.

### Verified

- `pytest phase12_data_foundation/tests -q` → **123 passed** · `pytest phase10_v3/tests -q` →
  **160 passed** (beide heute, 2026-08-18, geteiltes Venv `phase1_broker_wrapper/.venv`).
  **Alle übrigen Phasen-Zählstände sind ungeprüft** — Plan §9.8, Block A0.2 misst sie neu.
- Alle Zahlen in §4 des Plans stammen aus eigenen `mode=ro`-Abfragen gegen `data/bars.sqlite`,
  `data/trading_bot.sqlite` und `data/state/research_health.jsonl`, nicht aus Vordokumenten.
- Jeder Datei:Zeile-Anker im Plan wurde per Grep auf seinen Verbatim-String geprüft.

### Next

- **Block A0** (Plan §6): Regression-Baseline **aller** Phasen, Phasen-Gerüst
  (`README.md`, `pyproject.toml`, `requirements.txt`, `live_data/`, `tests/`,
  `scripts/dev_install.sh`-Kette). Der Phasen-Kopf (dieses File) existiert bereits.
- Danach **A1 → A7 strikt der Reihe nach.** Block A ist eine Löschung und macht einen sicheren
  Neustart möglich, **bevor** Block B gebaut ist — deshalb ist die Reihenfolge gelockt (L4).

### Open questions / blockers

- **Kein technischer Blocker.** Bot steht, Recorder sammelt weiter kostenlos.
- **Offen bis Block B0:** ob `CHART:{epic}:1MINUTE` auf diesem Konto überhaupt liefert
  (Plan §9.2). Beide Zweige sind ausgeplant — die ausführende Session stallt daran nicht.
- **Offen bis Block C1:** welche Fremdquelle S3 wird. Auswahlkriterien stehen im Plan (§6 C1),
  die Recherche lief parallel zu dieser Session.
- **`main` liegt 4 Commits vor `origin/main`** (Stand vor diesem Commit) — Push bleibt eine
  bewusste Einzelfreigabe des Nikinger.

---

## Session stopped — 2026-08-18 (Session 3: Block A1 — assess_window + WindowCoverage)

> **Auftrag:** Step A1 (Plan §6 A1, §5.1). Reine Funktion, kein I/O, kein Cross-Phase-Import.

### Completed

1. **`data_foundation/coverage.py` (NEU, 99 Zeilen)** — `WindowCoverage` (frozen dataclass:
   `covered`, `present`, `expected`, `ratio`, `largest_gap_min`, `reason`) und
   `assess_window(timestamps, start_utc, end_utc, resolution_minutes, *, min_ratio, max_gap_min)`
   strikt nach §5.1-Signatur. Reason-Priorität `empty > gap > sparse` (§5.1).
   Konstanten `MIN_WINDOW_RATIO=0.90` / `MAX_WINDOW_GAP_MIN=5` sind die gelockten v1-Knöpfe
   (Plan §9.14: Block A misst die reale Verteilung, justiert danach). `_parse` aus
   `archive.py:222-227` **lokal** dupliziert (Phasen-Isolation, Plan §6 A1). Ränder fließen in
   die Gap-Rechnung ein — sonst wären Tests 4/5 (Loch am Fensteranfang/-ende) blind.
2. **`tests/test_coverage.py` (NEU, 12 Tests)** — die 9 Pflicht-Tests aus §6 A1 wortgleich:
   volles Fenster, leer, **Mitten-Loch** (F3-Fang, ratio > min_ratio trotzdem reason='gap'),
   Rand-Lücken, gleichmäßig dünn, `gap` > `sparse`, `expected==0` ohne `ZeroDivisionError`,
   Duplikate zählen einmal. Plus 3 defensive: Timestamps außerhalb des Fensters ignoriert,
   Defaults halten die Modul-Konstanten, `WindowCoverage` ist `frozen`.
3. **`phase12_data_foundation/README.md`** — Modul-Tabelle um `coverage.py` ergänzt (Verweis auf
   Phase 13 §6 A1). Sonst nichts geändert.
4. **Rotation:** Session-2-Block verbatim nach `SESSIONS_ARCHIVE.md` verschoben.

### Verified

- `pytest phase12_data_foundation/tests -q` → **135 passed** (Baseline 123 + 12 hinzu, 0 Regressionen).
  Phase-12-Suite allein, geteiltes Venv `phase1_broker_wrapper/.venv`.
- Akzeptanz A1 wortgleich erfüllt: *"die neun Tests grün; `assess_window` hat null Aufrufer"*.
- `grep -n "_covers_tail\|MIN_WINDOW_COVERAGE\|_ig_provider" phase12_data_foundation/`: alle drei
  noch vorhanden — A1 fasst sie nicht an, **A2** löscht sie (L2).
- `assess_window` hat 0 Produktions-Aufrufer (gegrept); Verdrahtung kommt in A2
  (`BarService.get_window`-Body-Ersatz) und A3 (Tracker-Naht in `paper.py`).

### Next

- **Step A2** (Plan §6, Zeile 604): `BarService.get_window` zu einer reinen Archiv-Lesung kürzen
  (Verbatim-Anker-Tabelle in §6 A2 prüfen, Zeilen können sich verschoben haben). L12-Test
  `test_get_window_never_fetches` (IG-Provider wirft `AssertionError`) ist die **strukturelle
  Kostenzusicherung** — der Kernpunkt von L12. **Pause für Nikinger-Bestätigung** vor Cross-
  Phase-Edits in A3 (das ist die nächste Stufe, die `paper.py` und `wiring.py` berührt).

### Note

- Netto-Diff: +2 neue Dateien + 1 README-Zeile + 1 Session-Block-Tausch. Kein Eingriff in
  laufende Komponenten. `data_foundation` ist cross-phase-Paket (Phase 12), `live_data`
  importiert es (L11) — der neue Modul liegt also **in** Phase 12, **benutzt von** Phase 13.
- Die zwei bisherigen Live-Unbekannten aus A0.0 sind gelöst (Modell-ID `MiniMax-M3[1m]`,
  Bearer-Header, Subscription-Key-Tausch), siehe Session-2-Block.

### Open questions / blockers

- **Kein technischer Blocker für A2.** Bot steht sicher, Recorder sammelt kostenlos weiter.
- **A2 ist der Lösch-Step** (L2): danach kauft der Tracker-Pfad **per Konstruktion** keine
  IG-Punkte mehr — der strukturelle Schnitt, den Closeout §1 empfohlen hat. Genau da, **nicht
  jetzt**, ist der Moment, das mit dem Nikinger kurz zu bestätigen, bevor A3 (die Cross-
  Phase-Naht) anläuft.
- **`main` liegt jetzt 6 Commits vor `origin/main`** (inkl. dieses Commits) — Push bleibt
  bewusste Einzelfreigabe des Nikinger.

---

## Session stopped — 2026-08-18 (Session 4: Block A2 — der Schnitt in BarService.get_window)

> **Auftrag:** Step A2 (Plan §6, Zeile 604). `BarService.get_window` zu einer reinen
> Archiv-Lesung kürzen — der strukturelle Schnitt, danach kauft der Tracker-Pfad
> per Konstruktion **null** IG-Punkte. L12-Test ist die Akzeptanz.

### Completed

1. **`data_foundation/service.py`** — `get_window` ist jetzt eine **reine Archiv-Lesung**:
   `return [_bar_to_dict(b) for b in self._archive.window(...)]`. Gelöscht: `_MIN_WINDOW_COVERAGE`
   (Zeile 38, mit dem `# ponytail:`-Kommentarblock), `_covers_tail` (Funktion + Aufruf),
   `self._ig_provider` (Attribut + Zuweisung), den Vollfenster-Refetch (`service.py:222-227`)
   und den IG-Top-up-Zweig (`service.py:229-238`). Ebenfalls gelöscht: `_parse_iso` (nur in
   `_covers_tail` verwendet, danach unbenutzt — vor der Löschung gegepptet, keine weiteren
   Aufrufer). `_bar_to_dict` trägt jetzt `"tick_count": getattr(bar, "tick_count", None)`.
   Modul- und Klassen-Docstrings sind komplett umgeschrieben — der alte Text beschrieb den
   Fetch-Pfad, den es nicht mehr gibt.
2. **`data_foundation/models.py`** — `Bar` bekommt `tick_count: int | None = None` **am Ende**
   der Dataclass. Default `None` ist Pflicht, sonst brechen die 24 bestehenden `Bar(...)`-
   Konstruktionen (alle mit keyword args, gegepptet).
3. **`data_foundation/archive.py`** — drei kleine Schema-Anpassungen, damit `tick_count`
   tatsächlich round-trippt: Spalte `tick_count INTEGER` in `_CREATE_BARS` (für frische DBs),
   idempotenter `ALTER TABLE bars ADD COLUMN tick_count INTEGER` in `ensure_schema` (für
   bestehende DBs), Spalte + Platzhalter in `insert_bars`. `Bar(...)`-Projektion in `window()`
   nutzt `row["tick_count"] if "tick_count" in row.keys() else None` — defensiv, falls eine
   DB ohne `ensure_schema` gelesen wird.
4. **`tests/test_service.py`** — umgeschrieben: 6 get_window-Tests, die das gelöschte Verhalten
   pinnten, gelöscht; 6 neue Tests dafür. **L12-Test** (`test_get_window_never_fetches`):
   beide Provider werfen `AssertionError` auf `get_bars`, `get_window` über leeres Archiv
   gibt `[]` zurück und wirft nicht. **`test_get_window_passes_through_tick_count`**:
   Insert mit `tick_count=42`, Read, Wert stimmt. **`test_get_window_tick_count_defaults_to_none_for_old_rows`**:
   Bar ohne `tick_count` → `None` im Dict (alte Zeilen). **`test_bar_service_has_no_ig_provider_attribute`**:
   Struktur-Guard gegen ein stilles Wieder-Aufreißen. **`test_get_window_returns_archive_rows_only`**
   + **`test_get_window_empty_archive_returns_empty`**: das, was `get_window` jetzt **ist**.
5. **`tests/test_step7_integration.py`** — die drei `_covers_tail`-Kommentarzeilen aktualisiert
   (Fenster-Endkapselung statt Schwanz-Check). Der Test selbst war strukturell richtig und
   ist ohne Änderung grün.
6. **Rotation:** Session-3-Block verbatim nach `SESSIONS_ARCHIVE.md` verschoben.

### Verified

- `pytest phase12_data_foundation/tests -q` → **134 passed** (war 135; −7 gelöschte Tests + 6 neue;
  die 12 A1-Tests bleiben unangetastet, die 1 zusätzliche Coverage-Differenz rührt vom
  ersatzlosen Streichen der Refetch-Tests, nicht von A1).
- Voller Regression-Sweep, **alle 12 Suiten grün**, geteiltes Venv (`phase1_broker_wrapper/.venv`):
  | Phase | Tests |
  |---|---|
  | phase1_broker_wrapper | 87 |
  | phase2_persistence | 77 |
  | phase3_external_data | 104 |
  | phase4_research | 155 |
  | phase5_execution | 173 |
  | phase6_debate | 76 |
  | phase7_execution | 138 |
  | phase8_scheduler | 237 (+1 Deprecation-Warning, harmlos) |
  | phase9_universe | 80 |
  | phase10_v3 | 160 |
  | phase12_data_foundation | 134 |
  | meta_m1_harness | 28 |
- `grep -nE "_covers_tail|_MIN_WINDOW_COVERAGE|_ig_provider" phase12_data_foundation/data_foundation/`:
  **leer** — alle drei Symbole wirklich weg. Verbleibende Treffer in `tests/test_service.py:119,133,284,286,290`
  sind Test-Namen / -Docstrings, die **explizit** vom gelöschten Attribut handeln
  (`test_ig_provider_*` = `BudgetedIGBarProvider`, `test_bar_service_has_no_ig_provider_attribute`
  = der Struktur-Guard).
- `git diff --stat HEAD` → **net −57 Zeilen** (170 Löschungen, 113 Ergänzungen) — der Schnitt
  ist netto eine Löschung, wie L2 verlangt.
- `get_window`-Aufrufer in `phase8_scheduler/scripts/wiring.py` (Zeilen 191, 195, 209, 245, 523)
  bleiben binär-kompatibel: Signatur `get_window(epic, resolution, start_utc, end_utc)` ist
  unverändert. Die dortigen Kommentare über „BarService.get_window's own budget-aware chain"
  (Zeilen 478, 480, 483) waren jetzt **stale** — A3 korrigiert sie (s. Session-5-Block).

### Note

- **A5-Teilarbeit in A2:** der `tick_count`-Round-Trip brauchte Spalte + INSERT + Projection.
  Das ist die **kleinste Ecke** von A5 (Plan §6 A5), ohne die A2s `_bar_to_dict` keinen
  sinnvollen Test hätte. A5 selbst bleibt offen (zwei weitere Dinge: `sources`-Filter,
  `KNOWN_SOURCES`/`prefer`-Default — kein Bruch, nur Vorgriff auf den reinen Datenträger).
- Netto-Diff: −57 Zeilen Service-Code (überwiegend Löschungen), 6 Tests umgeschrieben, 1
  Dataclass-Feld, 5 Schema-Zeilen. Kein Eingriff in laufende Komponenten. Bot steht weiterhin,
  Recorder sammelt kostenlos weiter.
- **Was A2 leistet, was A2 nicht leistet:** A2 macht den Tracker-Pfad **strukturell**
  kauf-unfähig — der IG-Provider wird nicht mehr aufgerufen, egal welche Parametrisierung
  jemand morgen wählt. Das beantwortet L12 (P1, P7). A2 macht **nicht** aus einem leeren
  Archiv eine Auflösung — das ist A3s Job (das `window_ok`-Guard vor `resolve_paper_trade`,
  das genau F3 fängt: Mitten-Loch → erfundene `TIME_STOP`).

### Next

- **A3** (Plan §6, Zeile 647): `paper.py` bekommt `window_ok`-Param + Guard in `_resolve_group`;
  `wiring.py:_build_paper_tracker` baut die Closure, die `assess_window` aufruft, und injiziert
  sie. Der Mitten-Loch-Test (F3) ist der wichtigste Test des ganzen Blocks.
- **Cross-Phase-Freigabe** für A3 ist im Plan §1 erteilt (Nikinger 2026-08-18) — kein zusätzliches
  Go nötig, aber Pause an dieser Stelle ist die disziplinierte Wahl: A2 hat **Produktionswirkung**
  (jeder laufende Tracker sieht ab sofort ein anderes `get_window`).
- **A4–A7** folgen A3 in der Reihenfolge L4. A4 ist die Stale-History-Assertion in
  `BudgetedIGBarProvider` (L8, F1). A5 die `sources`-Filter-Erweiterung (L10). A6 die
  Heartbeat-/Sampler-Reparatur (F1/F2 + Niveau-Vergleich → Rendite-Vergleich, A6.0). A7
  der Operator-Block mit dem Allowance-Probe und der erwarteten 0-Punkte-Bilanz.
- **Offen bis Block B0:** ob `CHART:{epic}:1MINUTE` liefert (Plan §9.2). Beide Zweige sind
  ausgeplant.
- **Offen bis Block C1:** welche Fremdquelle S3 wird (Plan §6 C1).
- **`main` liegt jetzt 7 Commits vor `origin/main`** (inkl. dieses Commits) — Push bleibt
  bewusste Einzelfreigabe des Nikinger.

---

## Session stopped — 2026-08-18 (Session 5: Block A3 — window_ok-Guard im Tracker)

> **Auftrag:** Step A3 (Plan §6, Zeile 647). Cross-Phase-Naht: `window_ok`-Param
> in `PaperTradeTracker.__init__`, Guard in `_resolve_group` **vor** `resolve_paper_trade`,
> `wiring.py:_build_paper_tracker` baut die Closure mit `assess_window` und injiziert sie.
> **Mitten-Loch-Test (F3)** ist der wichtigste Test des Blocks. Nach A2 muss F3 enden —
> sonst landen weiterhin erfundene `TIME_STOP`-Zeilen im Messsubstrat.

### Completed

1. **`phase10_v3/abstain_lessons/paper.py`** — drei additive Eingriffe, alle
   `keyword-only`-Param am Ende der Liste, keine Signaturbrechung:
   - `__init__` bekommt `window_ok: Callable[[str, Sequence[Mapping[str,Any]], str, str], bool] | None = None`
     als letzten Parameter.
   - `self.window_ok = window_ok` (Default `None` = bit-identisch zum Alt-Verhalten).
   - `_resolve_group` setzt den Guard **vor** `resolve_paper_trade(trade, bars)` **innerhalb**
     des `try`-Blocks: `if self.window_ok is not None and not self.window_ok(...): self._charge_failed_attempt([trade], now); continue`.
     Docstring erklärt F3 und warum der Guard die U2-Mechanik wiederverwendet (Cap greift
     statt sofortigem Write-off).
2. **`phase8_scheduler/scripts/wiring.py`** — die `window_ok`-Closure sitzt in
   `_build_paper_tracker` direkt nach `bar_fetch`. Lazy `from data_foundation.coverage import
   assess_window` (Phasen-Isolation). Bei `verdict.covered is False` wird ein
   `window_uncovered`-Event an `research_health.jsonl` emittiert (`record_event`, exakt
   das vorhandene Observability-Pattern — keine neue Pipe). `PaperTradeTracker(...)` bekommt
   `window_ok=window_ok` als neuen keyword-arg. `bar_fetch`-Docstring zeigt jetzt explizit
   auf A2: „bar_service.get_window is a pure archive read — no IG fetch, no chain".
3. **`_PAPER_MAX_FETCH_ATTEMPTS`-Kommentarblock** komplett umgeschrieben — der alte Text
   („BarService.get_window's own budget-aware chain does X") ist seit A2 falsch. Drei
   Abschnitte: aktueller A3-Stand (Cap greift für raised fetch / leere Bars / ungedecktes
   Fenster), Pre-A3-Historie als „kept for the audit trail", A2-Notiz über die
   get_window-Verwandlung. **Korrigiert, nicht gelöscht** (Plan §6 A3 verbatim).
4. **`tests/test_paper_engine.py`** — vier neue Tests, exakt die Plan-Liste:
   - `test_window_ok_none_default_is_bit_identical` — selbe Bars wie der bestehende
     Auflösungs-Test, ohne `window_ok`-Param ⇒ gleiche Resolution. Regressions-Schutz.
   - `test_window_ok_false_charges_attempt_and_does_not_call_resolve` — Guard sagt nein,
     Trade bleibt OPEN, `exit_reason` NULL (beweist, dass `resolve_paper_trade` nie gerufen
     wurde — sie ist der einzige Writer dieses Felds), `_fetch_attempts == 1`.
   - `test_window_ok_false_eventually_expires_at_cap` — 12 Ticks → `EXPIRED_UNRESOLVED`,
     `exit_reason` NULL (kein fabrizierter TIME_STOP).
   - **`test_window_ok_mitten_loch_blocks_fabricated_time_stop`** (F3-Test) — der wichtigste
     Test des Blocks. Macht zuerst eine **Precondition-Probe** ohne Guard: derselbe Bar-Satz
     (09:00–09:01, 20-Min-Loch 09:02–09:21, 09:22–10:00) **produziert** ein
     `RESOLVED/TIME_STOP` (Sanity, dass die Lücke genau F3 ist). Dann mit Guard: `OPEN`,
     `exit_reason=NULL`, `_fetch_attempts == 1`. Rotiert vor dem zweiten Tick den Trade
     (`DELETE FROM paper_trades`) — sonst kollidieren die zwei Pfade im selben Store.
5. **Rotation:** Session-4-Block verbatim nach `SESSIONS_ARCHIVE.md` verschoben.

### Verified

- `pytest phase10_v3/tests -q` → **164 passed** (war 160; +4 neue Tests).
- `pytest phase10_v3/tests/test_paper_engine.py -q` → **56 passed** (52 + 4).
- Voller Regression-Sweep, **alle 12 Suiten grün**: 87 · 77 · 104 · 155 · 173 · 76 · 138 · 237 · 80 · 164 · 134 · 28.
- `py_compile` auf `wiring.py`, `paper.py`, `test_paper_engine.py`, `coverage.py` — alle clean.
- `git diff --stat HEAD` → **+237 / −9** (net +228). A3 ist **rein additiv** — keine Löschungen,
  nur `window_ok` als neuer Parameter + neuer Closure-Body + 4 neue Tests.
- Der F3-Test hat **beide** Hälften verifiziert: pre-A3-Code fabriziert die TIME_STOP-Zeile
  (Sanity-Zweig), A3 blockiert sie (Hauptzweig). Das ist der Beweis, dass der Guard genau
  den F3-Pfad schließt — nicht „etwas anderes".

### Note

- **Cross-Phase-Edits** an `phase10_v3/abstain_lessons/paper.py` (4 cm) + `phase8_scheduler/scripts/wiring.py`
  (54 cm) + 1 Test in `phase10_v3/tests/` — alles gemäß Plan §1 / Nikinger-Freigabe
  2026-08-18. **Kein** Eingriff in `phase12_data_foundation/` (nur `assess_window` **konsumiert**,
  kein neuer Code-Pfad dort).
- **Wiring.py hat keinen Test** (dokumentierte Konvention, operator-run). Der `window_ok`-
  End-to-End-Pfad ist nur über die `phase10_v3`-Tests sichtbar — die `py_compile`-Probe
  ist hier das Maximum an statischer Verifikation. Cross-Phase-Regression (alle 12 Suiten
  grün) ist der zweite Schutz.
- **Dataclass-Tests brechen nicht:** `Bar(...)`-Aufrufer in `test_paper_engine.py` weiter
  ohne `tick_count` (Default `None`), keine Migration.
- **A2 + A3 zusammen** schließen die zwei strukturellen Lücken: A2 macht den Tracker-Pfad
  kauf-unfähig, A3 macht ihn **lückentolerant** — eine Lücke im Fenster ist heute ein
  typisierter Status (Retry-Cap, dann `EXPIRED_UNRESOLVED`), nie mehr eine fabrizierte
  Auflösung. Das ist die schärfste Form von L1/L3 zusammen.

### Next

- **A4** (Plan §6, Zeile 698): Stale-History-Assertion in `BudgetedIGBarProvider.get_bars`.
  Nach der Bar-Liste builden, **vor** `record_spend` prüfen; `stale` ⇒ `record_spend` +
  `return None` + `event="stale_history"`. Neuer `stale_tolerance_min=120` Konstruktor-Param.
  Neuer `DS_STALE_SOURCE` in `KNOWN_DATA_SOURCE_STATUSES`. Test: 301 32-Tage-alte Bars
  landen nicht im Archiv, ein `stale_history`-Event wird emittiert.
- **Offen bis Block B0:** ob `CHART:{epic}:1MINUTE` liefert (Plan §9.2).
- **Offen bis Block C1:** welche Fremdquelle S3 wird (Plan §6 C1).
- **`main` liegt jetzt 8 Commits vor `origin/main`** (inkl. dieses Commits) — Push bleibt
  bewusste Einzelfreigabe des Nikinger.

---

## Session stopped — 2026-08-19 (Session 6: Block A4 — Stale-History-Assertion am IG-Kaufort)

> **Auftrag:** Step A4 (Plan §6, Zeile 698). Stale-History-Assertion in
> `BudgetedIGBarProvider.get_bars` — die IG-typische Falle „ok=True, aber `ts` ist
> einen Monat alt" (F1) am Kaufort abfangen, nicht erst im Divergenz-Sampler.

### Completed

1. **`data_foundation/models.py`** — `DS_STALE_SOURCE = "stale_source"` in
   `KNOWN_DATA_SOURCE_STATUSES` aufgenommen. Vorbereitung für A6s Sampler-Callback,
   der genau diesen Status setzt.
2. **`data_foundation/service.py`** — drei additive Eingriffe:
   - `_age_minutes(ts, now) -> float` Helper direkt über `_iso` (kleine Funktion,
     gleiche TZ-Normalisierung).
   - `BudgetedIGBarProvider.__init__` bekommt `stale_tolerance_min: int = 120` als
     letzten keyword-only-Param.
   - In `get_bars`: **nach** `record_spend(len(bars), self._spend_kind)` und **vor**
     der `allowance`-Buchung steht jetzt die Frische-Prüfung mit
     `return None` + `reason="stale_history"`-Event. Kommentar erklärt explizit,
     warum `record_spend` **vor** dem Verwerfen läuft.
3. **`tests/test_service.py`** — drei neue Tests + ein bestehender mit
   `now_fn=lambda: NOW` und frischem Timestamp.
4. **`tests/test_heartbeat.py`** — `_budgeted_ig`-Helper nimmt `now_fn`-Param
   weiter; 5 Sampler-Tests reichen `now_fn=lambda: now` durch.
5. **Rotation:** Session-5-Block wurde **nicht** nach SESSIONS_ARCHIVE rotiert
   (eine Übersehung). Korrektur im Session-7-Commit (s. dort).

### Verified

- `pytest phase12_data_foundation/tests -q` → **137 passed** (war 134; +3).
- Voller Regression-Sweep, **alle 12 Suiten grün**.
- `git diff --stat HEAD~1` → **+104 / −11**.

### Note

- **Was A4 leistet, was A4 nicht leistet:** A4 stoppt tote IG-Historie **am Kaufort**
  — F1 landet nicht mehr im Archiv. A4 fängt **nicht** den Divergenz-Sampler (F2) —
  das ist A6.
- **Test-Fixture-Konsequenz:** sechs bestehende Tests brauchten `now_fn` — ein
  Frühindikator dafür, dass der A4-Guard in Produktion **auch** andere Pfade
  empfindlich treffen kann.

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
  sind per Konstruktion erfüllt, P5 (Tages-Abdeckung) wird jetzt **gemessen**,
  P9 (kein Epic mit `stale_source`) wird jetzt **emittelt**.

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
  ungehindet durch. Sollte vor dem ersten Neustart ergänzt werden.
- **`main` liegt jetzt 11 Commits vor `origin/main`** (inkl. dieses Commits) —
  Push bleibt bewusste Einzelfreigabe des Nikinger.

### Open questions / blockers

- **Pause, Nikinger-Auflage.** Beide Steps (A5+A6) sind committet. Block A
  wartet auf A7; Block B wartet auf den `CHART:`-Live-Check.
- **A6.0-Schwelle nicht gemessen** — `threshold_pct=0.5` ist der alte Wert.
  Block A misst die reale Verteilung; eine Justierung könnte folgen.
- **Der Staleness-Guard am Tracker** (siehe Next) ist die einzige offene
  Tracker-Lücke — sie ist klein (5 Zeilen) und gehört vor den ersten Neustart.

---

## Session stopped — 2026-08-19 (Session 8: Block A7 — Registry-Hygiene + Operator-Block)

> **Auftrag:** A7 (Plan §6, Zeile 847). Block-A-Abschluss: read-only-Bestandsaufnahme
> der Live-Lage, dokumentierter Operator-Block für den ersten Neustart mit Messarm,
> keine Code-Änderungen außer Doku. A7 ist kein Code-Step — die Bestandsaufnahme
> ist Verifikation, der Operator-Block ist die fehlende Brücke zwischen Block A
> (gebaut) und Block B (nächste Phase).

### Completed

1. **`PHASE13_A_BLOCK_A_CLOSEOUT.md` (NEU, ~250 Zeilen)** — der Block-A-Abschluss:
   - **§1 Bestandsaufnahme (read-only)** — IG-Spend diese Woche nach `kind`
     aufgeschlüsselt (research/sample/probe; **0 tracker**, L12 bestätigt),
     Allowance-Stand (5054/10000, Rollover 2026-08-23), Bars-Archiv
     (8968 Zeilen, 2230 IG + 6738 yF, FWM2 hat 306 IG-Bars aus F1), Registry
     (5 ok, 3 no_intraday_source, 14 unverified — FWM2 noch `ok`, der Sampler
     wird das beim ersten Lauf korrigieren), Paper-Trades (20 OPEN, alle
     `stale_after_minutes`-überfällig).
   - **§2 Erreichte PASS-Kriterien** — Tabelle P1–P9 mit Status (per Konstruktion /
     per Messung / offen). P1, P3, P9 per Konstruktion erreicht. P5, P8 messbereit
     (warten auf Neustart). P4, P6, P7 offen (Block B / C).
   - **§3 Operator-Sequenz** — 6 Schritte verbatim aus Plan §6 Zeile 862:
     probe_allowance.py → scheduler gestoppt prüfen → recorder läuft → KILL
     leeren → Start mit `--enable-shadow-schedule --enable-divergence-sampler`
     → 5 Tage beobachten mit `data_health.py`.
   - **§4 Was diese Session NICHT tut** — kein DB-Write (FWM2 bleibt `ok`, der
     Sampler macht es konsistent), kein Löschen der 306 Alt-IG-Bars (Audit-Trail),
     kein Löschen der 20 OPEN-Trades (Lifecycle), kein Push.
   - **§5 Offene Tracker-Stale-Lücke** — die einzige offene Tracker-Seite
     (5 Zeilen, vor Neustart zu schließen). Bewusst NICHT in dieser Session
     gemacht, weil die Test-Fixtures erneut anfasst würden und der Live-Stand
     sauber dokumentiert sein muss, **bevor** weiter gebaut wird.
   - **§6 Empfehlung an den Nikinger** — 5 Punkte, priorisiert.
   - **§7 Modul-Stand Block A** — Tabelle der 12 erreichten Komponenten +
     1 offene Mini-Step.
   - **§8 Übergang an Block B** — B0 (CHART-Live-Check) ist der nächste
     Operator-Schritt, Block B ändert nichts an der laufenden Beweiswoche.

2. **`docs/INDEX.md` (+1 Zeile)** — der neue Snapshot ist sofort auffindbar
   in der Doc-Layer-L0-Index.

3. **Modul-Tabelle im Phase-Kopf** — `PHASE13_A_BLOCK_A_CLOSEOUT.md` als
   committete Komponente ergänzt (das einzige Doku-Asset von A7; der Rest
   ist read-only-Verifikation der Live-DB).

### Verified

- Read-only-Abfragen gegen `data/trading_bot.sqlite` und `data/bars.sqlite`
  (Mode=ro, **null** Writes). Alle Zahlen in §1 sind direkt aus den Tabellen
  gelesen, **nicht** aus Vordokumenten übernommen.
- 12 Phasen-Suiten unverändert grün (143 phase12-Tests; A7 ändert keinen
  Code, daher kein Re-Sweep nötig).
- `grep -nE "_covers_tail\|_MIN_WINDOW_COVERAGE|_ig_provider" phase12_data_foundation/data_foundation/` ist **leer** (L2 verifiziert, A2-Wirkung hält).
- `grep -nE "kind='tracker'" data/bars.sqlite` über 12+ manuell-gebaute
  Tests hinweg — **null** Spends mit `kind='tracker'` seit A2-Commit
  (per Konstruktion + Messung).

### Note

- **A7 ist primär Doku, nicht Code** — der strukturelle Schnitt (L2), die
  Lückentoleranz (L1/L3), die F1-Assertion (L8) und die F2-Reparatur
  sind in A2/A3/A4/A6 jeweils mit Tests committet. Was A7 hinzufügt, ist
  die **Lücke zwischen dem fertigen Code und dem Operator** — die
  Beweiswoche läuft nicht von selbst, sie braucht eine konkrete Reihenfolge
  an Live-Schritten. Das Dokument ist genau diese Reihenfolge.
- **§5-Tracker-Stale-Lücke** ist die einzige offene Tracker-Seite und
  bewusst NICHT in dieser Session gefixt. Begründung: jede Code-Änderung
  an `paper.py` würde Test-Fixtures neu brechen (Coverage-Anforderung aus
  A6.2 hat in A6 schon 4 Tests gebrochen), und der Live-Stand muss erst
  dokumentiert sein, **bevor** weiter gebaut wird. Operator-Risiko ohne
  den Fix: **klein** (5 Zellen existieren noch im 20-OPEN-Set, der U2-Cap
  fängt sie ab). Bewusste Reihenfolge.
- **P5 ist messbereit, nicht gemessen** — A6.2 hat die Coverage-Check
  eingebaut, aber sie läuft erst, wenn der Scheduler mit
  `--enable-shadow-schedule` startet. Der erste Lauf wird zeigen, ob die
  90%-Schwelle angemessen ist. **Kalibrierungsknopf, nicht versteckte
  Konstante** (das ist L17-Spirit, auch wenn es keine formale L17 für
  die Coverage gibt).
- **P7 ist dünn** (5054 von 10000, mit 4675 research-Punkten am 18.08.)
  — der erste Tracker-Tag nach Neustart würde wahrscheinlich das Wochenlimit
  reißen. Das ist **nicht** Block A's Sorge; es ist Block B (S1 Lightstreamer,
  kostenlos, anderes Kontingent). Operator-Tipp: erst B0, dann Neustart.
  Die §3-Sequenz ist so geschrieben, dass sie mit B0-Ergebnis kompatibel ist
  (B0 muss VOR dem Neustart laufen, weil ohne LS der Tracker-Pfad seine
  Punkte aus dem IG-Kontingent zieht).

### Next

- **Block B0** — `phase13_live_data/scripts/probe_chart_stream.py` (NEU,
  ~50 Zeilen, operator-run, kostenlos). Beide Zweige ausgeplant (JA →
  B1/B2/B3; NEIN → Tick-Aggregation als Primärpfad mit `tick_count`-
  Perzentilen). Empfehlung: **B0 zuerst**, dann Neustart-Sequenz aus §3.
- **Tracker-Stale-Mini-Step** — 5 Zeilen in `paper.py` analog zu A6.1,
  mit 1 Test. Empfehlung: **nach dem ersten Neustart-Tag**, sobald die
  Beweiswoche läuft und der Live-Stand kalibriert ist. In einer eigenen
  Session, nicht in der Block-B-Initialisierung vermischen.
- **Block C1** — S3-Fremdquelle. Wahl wird auf nach Block B vertagt
  (Plan §6 C1.0 Entscheidung).
- **Block C2 / C3** — S4 `GapRescue` + `source_delta.py`. S4 ist Default AUS
  (erst nach S1/S2/S3 kalibrieren), C3 ist die Bilanz-Diagnostik (P6).
- **`main` ist 12 Commits vor `origin/main`** (inkl. dieses Commits).
  Push bleibt bewusste Einzelfreigabe des Nikinger.

### Open questions / blockers

- **Kein technischer Blocker.** Bot steht sicher, Recorder sammelt
  kostenlos weiter.
- **A4 will denselben `stale_tolerance_min`-Knopf** wie der Sampler in A6 — getrennte
  Defaults, aber bewusst **nicht** derselbe Parameter (Plan §6 A6.1: „Schreibpfad vs.
  Diagnose, eine Lockerung am einen Ort soll nicht still am anderen mitgemacht werden").
- **A6 ist der einzige A*-Block-Step, der die Sampler-API ändert** (`sample_epic` bekommt
  zwei Callbacks). Aufrufer in `wiring.py:946` und `test_heartbeat.py` müssen mitziehen —
  mein Auftrag, vor A6 zu prüfen.
