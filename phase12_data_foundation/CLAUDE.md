---
status: live
purpose: PHASE-HEAD, Phase 12 (Datenfundament) — Registry + BarService + Bar-Archiv + Recorder + Heartbeat. Steps 4+5+6 committed (49902b6, 473c8e4, 65ebec7). Step 7 (full integration + offline proof) + Step 8's two scripts (probe_allowance.py, reset_universe.py, D18) built Session 4, still UNCOMMITTED. Session 5 (2026-08-17): both real IG allowance bugs fixed (ig_adapter.py metadata-nesting + allowanceExpiry seconds→ISO in service.py/probe_allowance.py) — probe_allowance.py was structurally blind until this fix, full regression green, commit still Nikinger-decision. Steps 8-10 (gated, operator) are next.
read-when: working in phase12_data_foundation/ — read this head + its newest Session-stopped block first (⚠️ operator landmine there before any bot restart — affects epic_filter, the Recorder, and the divergence sampler, but is deliberately NOT a Step-6 CRITICAL alarm); the full plan (docs/concepts/phase12_data_foundation_plan.md) is the execution contract, read its relevant §6 step block before touching anything
detail: L2
up: ../CLAUDE.md
down:
  - ../docs/concepts/phase12_data_foundation_plan.md   # full execution-ready plan, D1-D20, Steps 0-10 (L3, ausführungsreif)
  - ../phase10_v3/PHASE11_DEFERRAL_HANDOVER.md          # why this track exists (L3, dated)
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

## Rahmen (Plan §1, verbindlich)
Bot-berührende Steps nur am Wochenende (Bot steht, Markt zu). Werktags: docs-only /
`data_foundation/`-Paket-Code selbst (eigene Dateien, eigene Tests, kein bestehender
Phasen-Code, nichts in `data/` geschrieben). Live-/Netz-/Kosten-Tests macht der Nikinger.

## Modul-Tabelle
Siehe [`README.md`](./README.md).

---

## Session stopped — 2026-08-17 (Session 5: Allowance-Bugfix — beide Bugs geschlossen)

> **Ausgangslage:** Session 4 endete mit dem exakten, Nikinger-freigegebenen Fix-Plan im
> `CLAUDE.md`-Next-Block (file:line-Anchors für beide Bugs). Diese Session war reine
> Umsetzung des vorgegebenen Plans, keine erneute Diagnose.

### Completed

1. **Bug 1 (root cause, Cross-Phase-Edit Phase 1, Nikinger-freigegeben 2026-08-17):**
   `phase1_broker_wrapper/broker_wrapper/adapters/ig_adapter.py:436` (`get_ohlcv`) UND
   `:466` (`get_historical_ohlcv`): `body.get("allowance", {})` →
   `body.get("metadata", {}).get("allowance", {})` — spiegelt IGs echten,
   Roh-Dump-verifizierten `/prices`-Shape (Session 4).
2. **Der tote Test dafür gefixt:** `phase1_broker_wrapper/tests/test_ig_adapter.py`
   — `test_get_ohlcv_happy_path_envelope_shape` (Zeile ~499) und
   `test_get_historical_ohlcv_happy_path` (Zeile ~525): Mock-Body von top-level
   `"allowance": {...}` auf `"metadata": {"allowance": {...}}}` umgestellt.
3. **Bug 2 (Sekunden→ISO-Konvertierung):**
   - `phase12_data_foundation/data_foundation/service.py`: `BudgetedIGBarProvider`
     bekommt einen `now_fn`-Parameter (Default `_default_now`, gleiche Konvention wie
     `BarService`/`SourceBudget`); `get_bars()` konvertiert `allowanceExpiry`
     (Sekunden-Restwert) via `_iso(now_fn() + timedelta(seconds=int(...)))` vor
     `budget.record_allowance(...)`, `None` bleibt `None`.
   - `phase12_data_foundation/scripts/probe_allowance.py`: gleiche Konvertierung
     (eigene kleine `_iso`-Hilfsfunktion, `datetime.now(timezone.utc)` direkt — das
     Skript hat keinen injizierbaren `now_fn`, Live-Skript, keine Tests dafür nötig).
4. **Kollateralfund beim Testlauf, nicht im Plan genannt, aber derselbe Fehlerklasse:**
   `phase12_data_foundation/tests/test_service.py::test_budgeted_ig_books_spend_and_allowance_on_success`
   mockte `allowanceExpiry` selbst als absolute-ISO-String (die alte, jetzt widerlegte
   Annahme aus `SourceBudget`s Docstring) — mit dem `int(expiry_seconds)`-Cast schlug
   das mit `ValueError` fehl. Fixture auf einen echten Sekunden-Wert (`345_600`)
   umgestellt + `now_fn=lambda: NOW` explizit übergeben, gleiche Korrektur-Logik wie
   Bug 1s Testfix (falsche Annahme, nicht Timing-Zufall).

### Verified

- `pytest phase1_broker_wrapper/tests -q` → **87 passed** (Baseline unverändert).
- `pytest phase12_data_foundation/tests -q` → **116 passed** (Baseline unverändert,
  inkl. des gefixten `test_service.py`-Falls).
- `pytest phase8_scheduler/tests -q` → **237 passed** (Baseline unverändert).
- Volle Regression, alle Phasen + root: P1 87 · P2 77 · P3 104 · P4 155 · P5 173 ·
  P6 76 · P7 138 · P8 237 · P9 80 · P10 159 · P12 116 · meta 28 · root 80 — exakt die
  Session-4-Baseline, keine Regression, keine neuen Tests nötig (reiner Bugfix +
  Testkorrektur, kein neues Verhalten).

### Next

- **Nikinger-Job (freigegeben, per `feedback_live_testing`-Memory):**
  1. `probe_allowance.py` erneut laufen lassen — sollte jetzt ein echtes
     `remaining`/`expiry` in `data/bars.sqlite` schreiben (vorher strukturell blind).
  2. Sobald `remaining > 1500` beobachtet: `scripts/reset_universe.py` (keine Argumente
     nötig) — setzt die quarantined Zeilen zurück.
  3. Recorder-Warmlauf (werktags erlaubt, yF-only): `bash phase12_data_foundation/
     scripts/run_recorder.sh`.
  4. **Erst danach**, falls gewünscht: Scheduler-Neustart (`run_scheduler.sh`) —
     beachtet die Operator-Landmine (leere `measurable_universe()` bis der Resolver
     lief).
- Steps 9-10 (Beweiswoche, Lightstreamer) — gated auf einen laufenden Scheduler + 5
  Handelstage, weiterhin kein heutiger Schritt.
- **Commit:** dieser Stand (Bugfix + alle Session-4-Uncommitted-Dateien) ist
  commit-fertig — Nikinger-Entscheidung, ob jetzt oder nach dem ersten echten
  `probe_allowance.py`-Lauf.
- Die beiden aus Step 6 bekannten, bewusst offenen Lücken (G-Deckungslücke bei einem
  POST_WINDOW-losen Tag; In-Memory-Sampler-Throttle über Neustarts) bleiben unverändert
  offen — kein Teil dieser Session.

### Open questions / blockers

- Keine. Beide Bugs sind gefixt und über die volle Regression verifiziert; ihr erster
  echter Live-Effekt (ein `probe_allowance.py`-Lauf mit echten, nicht-leeren Werten)
  ist weiterhin unbewiesen bis zum nächsten Nikinger-Lauf — nicht mit "verifiziert"
  verwechseln (gleiche Disziplin wie der 08-11-Notbremse-Befund).

---

> **Ältere Session-Blöcke** (verbatim ausgelagert, newest-first): [SESSIONS_ARCHIVE.md](./SESSIONS_ARCHIVE.md) — Rotation per Doc-Layers-Konvention ([docs/DOC_LAYERS_CONVENTION.md](../docs/DOC_LAYERS_CONVENTION.md)).
