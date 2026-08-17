---
status: live
purpose: PHASE-HEAD, Phase 12 (Datenfundament) — Registry + BarService + Bar-Archiv + Recorder + Heartbeat. Steps 0-8.5 gebaut, getestet und auf main committed. Session 6 (2026-08-17): Tag-1 live ausgewertet — Pipeline end-to-end bewiesen, ABER Messarm aus (0 Paper-Zeilen) + vier Ultrareview-Befunde U1-U5, ungefixt (Handover §3.0). Session 7 (P12.5, gleicher Tag): U1/U3/Entscheidung B + U2/U5 gefixt + committed (83d5ef3, ff5741c; P12 117→123, P10 159→160), lokal auf main, NICHT gepusht. Pausiert nach Nikinger-Auftrag vor Step 4 (Neustart, Operator-Job). Step 9 (Beweiswoche) weiterhin nicht begonnen.
read-when: working in phase12_data_foundation/ — read PHASE12_5_MEASUREMENT_ARM_PLAN.md first (aktueller Bauauftrag, E1-E9, §4 Step-Sequenz), dann diesen Kopf + den newest Session-stopped block; PHASE12_PREPROOF_HANDOVER.md ist der Befund-Vorlauf zum Plan; der Mutterplan (docs/concepts/phase12_data_foundation_plan.md) bleibt der §7-PASS-Kriterien-Ausführungsvertrag
detail: L2
up: ../CLAUDE.md
down:
  - ./PHASE12_5_MEASUREMENT_ARM_PLAN.md                 # aktueller Bauauftrag: E1-E9, Steps 1-7 (L3, execution-ready)
  - ./PHASE12_PREPROOF_HANDOVER.md                      # Befundlage vor P12.5, Tag-1-Ergebnisse (L3, dated)
  - ../docs/concepts/phase12_data_foundation_plan.md   # full execution-ready plan, D1-D20, Steps 0-10, §7 PASS-Kriterien (L3)
  - ../phase10_v3/PHASE11_DEFERRAL_HANDOVER.md          # why this track exists (L3, dated)
  - ../docs/architecture/phase12_preproof.svg           # Tag-1-Bild: was steht, was fehlt
  - ../docs/architecture/data_foundation.svg            # Fehlerbild + Zielbild
  - ./SESSIONS_ARCHIVE.md                               # rotierte Session-Blöcke (L3)
updated: 2026-08-17
---
# CLAUDE.md — Phase 12: Datenfundament (`phase12_data_foundation/`)

> Three data weeks (Phase 11) died on infrastructure, never on measurement. Root cause: one
> instrument fact lived in three divergent stores, the Phase-9 multi-source bar chain
> (`ChainedBarProvider`) was built and never switched on (`enable_ig_bars` default `False`).
> **Source of truth is the plan doc + the code, not this file.** Full plan:
> `../docs/concepts/phase12_data_foundation_plan.md`.

## Mission (zuerst lesen)
Ein neues Fundament, sequenziell (Überweg C, D1, Nikinger-Entscheidung 2026-08-11):
1. **Instrument-Registry** wird die eine Wahrheit für Instrument-Fakten; Symbol-Mapping
   abgeleitet + code-verifiziert statt deklariert.
2. **BarService** wird der eine Bar-Pfad für alle Konsumenten (Research + Paper Tracker).
3. **Bar-Archiv** (`data/bars.sqlite`) — jede gefetchte Bar wird persistiert, quellenagnostisch.
4. **Recorder** — eigener yF-only-Prozess, schreibt kontinuierlich, unabhängig vom Bot-Zustand.
5. **Mess-Heartbeat** — ein Ausfalltag fällt am selben Tag auf.
6. **Lightstreamer-Mitschrieb** (Step 10) — gated auf die bestandene Beweiswoche.

**Done-Kriterium der Phase:** eine echte Beweis-Messwoche läuft durch, ohne dass Infrastruktur
die Messung tötet (Plan §7). Die WI-2-Auswertung selbst bleibt Phase-11-Wiederaufnahme.

## Bauprinzip
„So wenig AI wie möglich, so viel AI wie nötig." **Phase 12 fügt NULL neues AI hinzu** (Plan
§1) — Symbol-Verifikation ist ein deterministischer Preisvergleich (IG-Snapshot vs. yF-Last),
kein LLM-Aufruf. Wer hier ein LLM „mappen/prüfen/schätzen" lassen will → stop, das ist Code.

## Scope
- **DRIN:** `data_foundation/` Paket (Archiv, Budget, Resolver, BarService, Recorder,
  Heartbeat), Migration 006 (Registry-Erweiterung + `paper_trades.resolution_source`), die
  Rewiring-Punkte in `phase8_scheduler/scripts/wiring.py` (Steps 3/4/6/7, Wochenend-Arbeit).
- **DRAUSSEN:** WI-2/W2-Auswertung + jede weitere H-Serie (Phase-11-Wiederaufnahme nach PASS),
  Research-Funnel-Fix, B3-Margin-Headroom-Umsetzung (nur Feld-Scouting hier, s. Session-Block),
  Council-Paper-Call, UI, Live-Konto, Lightstreamer für Live-Quotes (Step 10 hier ist reiner
  Archiv-Mitschrieb, anderer Zweck). Momentum-VETO bleibt unangetastet (D16) — sourct immer
  direkt aus P1-IG-Echtzeit-Bars, nie aus BarService/Archiv/yF.

## Rahmen (Plan §1) — ⚠️ seit 2026-08-17 geändert

> **Nikinger-Entscheidung 2026-08-17 (überschreibt Plan §1 für den Rest von Phase 12):**
> **Arbeit findet ab jetzt direkt unter der Woche statt**, auch bot-berührend. Begründung:
> der Bot läuft ohne die ausstehenden Fixes (U1–U3, s. Handover §3.0) **nicht gescheit** —
> die Wochenend-Regel würde einen kaputten Messbetrieb um jeweils eine ganze Woche
> verlängern, also genau das produzieren, wogegen die Notbremse gezogen wurde.
> **Diese Entscheidung ist für die nächste Planungssession verbindlich zu übernehmen.**

Daraus folgt für Werktags-Sessions:
- Bot-berührende Änderungen sind erlaubt. **Vorher den Bot stoppen** (Kill-Switch oder
  `kill <pid>`, `ps aux | grep scheduler.run` als Gegenprobe) — ein Datei-Edit wirkt ohnehin
  nicht auf einen laufenden Prozess, und ein zweiter Scheduler daneben löst die
  Parallel-Login-Falle aus. Nach dem Edit gezielt neu starten.
- Unverändert gültig: Live-/Netz-/kostenpflichtige Läufe macht der **Nikinger**; die
  Live-DB wird von Claude nur read-only (`mode=ro`) gelesen; Cross-Phase-Edits außerhalb
  `data_foundation/` bleiben freigabepflichtig (die U2/U4-Fixorte in `wiring.py` fallen
  darunter).

**Vorherige Regel (historisch, bis 2026-08-17):** bot-berührende Steps nur am Wochenende
(Bot steht, Markt zu); werktags docs-only / `data_foundation/`-Paket-Code selbst.

## Modul-Tabelle
Siehe [`README.md`](./README.md).

---

## Session stopped — 2026-08-17 (Session 7: P12.5 Steps 1–3 — U1/U3/Entscheidung B + U2/U5, pausiert nach Nikinger-Auftrag)

> **Auftrag:** `PHASE12_5_MEASUREMENT_ARM_PLAN.md` ausführen (execution-ready, E1–E9
> gelockt). Umfang dieser Session: Steps 1–3 (Housekeeping, phasen-interne Fixes, die zwei
> freigabepflichtigen Cross-Phase-Fixes). Steps 4–7 (Neustart, falsifizierbarer Nachweis,
> Beweiswoche, Handover) sind Nikinger-/Operator-Arbeit und **nicht** Teil dieser Session —
> Nikinger-Auftrag nach Step-3-Freigabe war explizit „vollständigen Step 3, danach
> pausieren".

### Completed

1. **Step 1 (Housekeeping, No-Op):** Legacy-Grep sauber (nur der bekannte, frozen
   `turbo_candidates.json`-Rest). Fünf Statusdokumente (Root-`CLAUDE.md`, `ROADMAP.md`,
   `docs/INDEX.md`, dieser Kopf, `README.md`) gegen Code geprüft — **keine Abweichung**,
   alle sagen korrekt „Steps 0–8.5 fertig, Step 9 nicht begonnen". Regression-Baseline
   aller Phasen gemessen (s. u.) — deckt sich exakt mit dem Plan-§8.2-Erwartungswert.
   Kein Commit für diesen Step (reiner No-Op-Befund, keine Datei geändert — „less is
   sometimes more").
2. **Step 2 (`data_foundation/`, phasen-intern, Commit `83d5ef3`):**
   - **U1** (`service.py:119`): `BudgetedIGBarProvider.get_bars` normalisiert jetzt IGs
     Roh-Timestamp über `normalize_bar_ts`, fängt `ArchiveError` in ein
     `bad_timestamp`-`bar_fetch`-Event statt es hochzuwerfen zu lassen (E1/E2). Heilt
     `DivergenceSampler`s lexikalischen Timestamp-Vergleich mit, weil `service.py` die
     einzige Stelle ist, an der IGs Rohformat einläuft — **end-to-end bewiesen**, nicht
     nur behauptet: `test_heartbeat.py`s IG-Fake läuft jetzt durch den echten
     `BudgetedIGBarProvider` mit einem Rohformat-Broker statt eines Stand-ins, der die
     Normalisierung übersprang.
   - **U3** (`service.py:207`): `_MIN_WINDOW_COVERAGE = 0.5`-Schwelle neben dem
     bestehenden `_covers_tail`-Check — ein kurzes-aber-tail-deckendes Archiv
     kurzschließt nicht mehr. `:217` (IG-Top-up) unangetastet (E4).
   - **Entscheidung B** (`heartbeat.py`): `assess_day` flaggt `shadow_enabled=False`
     jetzt unbedingt als Problem + `ok=False` — genau die Tag-1-Situation, die live
     `ok=True` meldete.
   - Ein bestehender `assess_day`-Test (`test_assess_day_no_measurable_epic_is_ok_with_problem_note`)
     musste umgebaut werden (mit `shadow_enabled=True` + einem realen Resolve isoliert),
     sonst hätte E8 seine eigentliche Aussage (measurable_epics==0 allein ist nur eine
     Notiz) überdeckt — kommentiert im Testfile.
   - `phase12_data_foundation` Tests: **117 → 122** (5 neu: 2 Provider, 2 `get_window`,
     1 `assess_day`).
3. **Step 3 (Cross-Phase, Nikinger-Freigabe per AskUserQuestion: „Vollständigen step 3,
   danach pausieren", Commit `ff5741c`):**
   - **U2** (`phase10_v3/abstain_lessons/paper.py:588`): `resolve_paper_trade`s
     `outcome is None` bedeutet an **beiden** Return-Stellen „noch nicht genug Bardaten",
     nie „kein Ergebnis" — `_resolve_group` belastet jetzt den Retry-Cap statt beim ersten
     Miss sofort abzuschreiben. Docstring-Korrektur (E6) an zwei Stellen:
     `_charge_failed_attempt` (paper.py) und der zugehörige Kommentar in `wiring.py:468-480`
     (behauptete fälschlich, der Fall sei bereits abgedeckt).
   - Ein bestehender Test (`test_tracker_marks_expired_when_unresolvable`) kodierte exakt
     den Vorher-Bug (sofortiges Expiry bei leeren Bars) — ersetzt durch
     `test_tick_charges_attempt_instead_of_expiring_on_empty_bars` (bleibt OPEN, Attempt-
     Zähler 1) + `test_tick_expires_after_the_attempt_cap` (12 leere Ticks ⇒ expiriert
     trotzdem, Cap-Verhalten unverändert). Den Plan-Vorschlag für einen dritten
     (Healthy-Path-Regressions-)Test bewusst ausgelassen — deckt sich mit dem bereits
     bestehenden `test_tracker_resolves_due_trade_and_marks_resolved`.
     `phase10_v3`: **159 → 160**.
   - **U5** (`phase8_scheduler/scripts/wiring.py:805`): `shadow_pair_scheduler`s
     `deadline` zieht jetzt zwei Zyklus-Intervalle von `window_close` ab —
     `window_close` selbst ließ der letzten Tages-Kohorte (13:30-Öffnung) null
     Tracker-Ticks (Tracker läuft nur in WINDOW, die Kohorte wird fällig genau beim
     Phasenwechsel zu POST_WINDOW). **Pflicht-Gegenprobe durchgeführt** (§8.3):
     `window_close="17:30"` + `cycle_interval_min=5` ⇒ Deadline landet exakt auf **17:20**.
     `wiring.py` hat keine eigene pytest-Suite (dokumentierte Konvention) — verifiziert
     via `py_compile` (sauber) + neuer AST-Guard
     (`phase12_data_foundation/tests/test_shadow_deadline_margin.py`, spiegelt
     `test_resolver_wiring.py`). `phase12_data_foundation`: **122 → 123**.
   - Volle Cross-Phase-Regression nach Step 3 grün und **unverändert** außerhalb der
     beiden berührten Phasen: P1 87 · P2 77 · P3 104 · P4 155 · P5 173 · P6 76 · P7 138 ·
     P8 237 · P9 80 · meta 28 · root 80 — deckt sich exakt mit Plan-§8.2.
4. **Bot unangetastet.** Scheduler (`pid 35195`) und Recorder (`pid 33151`) liefen zu
   Beginn dieser Session unverändert seit dem Pre-Proof-Handover — kein Stop/Restart,
   keine Live-/Netz-Aktion (Plan §1, unverändert Nikinger-Job).

### Verified

- `pytest phase12_data_foundation/tests -q` → **123 passed**.
- `pytest phase10_v3/tests -q` → **160 passed**.
- Volle Phasen-Regression (s. o.) — jede Zahl deckt sich mit dem Plan-§8.2-Erwartungswert,
  außer den beiden bewusst geänderten Phasen.
- U5-Deadline-Rechnung von Hand nachgerechnet: `17:30 - 2×5min = 17:20` ✓.

### Next

- **Step 4 (Nikinger, live):** laufenden Scheduler **erst stoppen**
  (`ps aux | grep scheduler.run` als Gegenprobe — Parallel-Login-Falle), dann
  `bash phase8_scheduler/scripts/run_scheduler.sh --enable-divergence-sampler --enable-shadow-schedule`.
- **Step 5 (am Starttag, nicht am Freitag):** der vierteilige falsifizierbare Nachweis
  (echte argv · Config-Default zurückgelesen · eine Zeile Live-Paper-Trades ·
  zweiteiliger Alarm-Positivtest d-i/d-ii) — Plan §4 Step 5, wörtlich befolgen, nicht
  paraphrasieren.
- **Step 6:** Beweiswoche als reiner Watch-Auftrag (5 Handelstage), Freitags-Review gegen
  Plan §7 A–G + Kern.
- **Step 7:** Handover ⇒ Phase 12 zu, inkl. Doku-Sync (Root-`CLAUDE.md`, `ROADMAP.md`,
  `docs/INDEX.md`, `README.md`, Memory-Updates).
- Diese Session hat **nicht** committet in Richtung `origin/main` gepusht — lokal auf
  `main`, zwei Commits (`83d5ef3`, `ff5741c`) über dem zuletzt gepushten Stand
  (`cc3770e`). Push ist wie gehabt eine bewusste, separate Freigabe.

### Open questions / blockers

- Keine technischen Blocker für Step 4 — beide Cross-Phase-Fixes sind committed + grün.
- Step 4 selbst ist der Blocker für alles Weitere: ohne den Neustart mit beiden Flags
  misst nichts.

---

> **Ältere Session-Blöcke** (verbatim ausgelagert, newest-first): [SESSIONS_ARCHIVE.md](./SESSIONS_ARCHIVE.md) — Rotation per Doc-Layers-Konvention ([docs/DOC_LAYERS_CONVENTION.md](../docs/DOC_LAYERS_CONVENTION.md)).
