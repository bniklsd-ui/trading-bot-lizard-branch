---
status: live
purpose: PHASE-HEAD, Phase 12 (Datenfundament) ✅ **abgeschlossen (Closeout 2026-08-25)**. Steps 0–8.5 (Migration 006, Registry, BarService, Bar-Archiv, Recorder, Heartbeat) + P12.5 Steps 1–3 (U1/U2/U3/U5 + Entscheidung B) stehen live auf `main` (143 Phase-12-Tests grün, 18 Phase-12-Commits auf `origin/main`, `main` = `origin/main` = `b9327ca`). P12.5 wurde 2026-08-18 formal CLOSED + GESCHEITERT (4731/10000 IG-Wochenpunkte, 92 % der gekauften Bars bereits im Archiv); die fünf Code-Fixes davon bleiben **korrekt im Repo**. **Die strukturelle Antwort steht in Phase 13+14** (Nikinger 2026-08-25): „der Auflöse-Pfad kauft nie wieder Daten" ist nicht mehr Empfehlung, sondern Architektur (Phase 13 Block A, Commit `e8c5b94`). Step 9 (Beweiswoche) wird nicht wieder aufgenommen — Phase-13-Beweiswoche läuft seit Mo 2026-08-25 als separater Track.
read-when: working in phase12_data_foundation/ — **für die Phase selbst**: ZUERST `PHASE12_CLOSEOUT_HANDOVER.md`, dann dieser Kopf + newest Session-stopped block; für die P12.5-Fehlergeschichte (Root Cause, Zahlen, was bleibt gültig): `PHASE12_5_CLOSEOUT_HANDOVER.md` + `PHASE12_5_FAILURE_HANDOVER.md` (in dieser Reihenfolge); für die **strukturelle Antwort**: `phase13_live_data/PHASE13_CLOSEOUT_HANDOVER.md` + `phase14_discovery/CLAUDE.md`. **Vor jedem Scharfstellen eines Messarms**: `PHASE12_5_CLOSEOUT_HANDOVER.md` §3 (Testlücke „keine Kosten-Zusicherung")
detail: L2
up: ../CLAUDE.md
down:
  - ./PHASE12_CLOSEOUT_HANDOVER.md                     # ✅ Closeout (2026-08-25) — Bilanz + strukturelle-Antwort-Narrative + Konsistenz-Regeln (L3, dated) — ZUERST LESEN
  - ./PHASE12_5_CLOSEOUT_HANDOVER.md                   # 📕 P12.5 Closeout-Analyse (2026-08-18) — die zwei Root-Cause-Korrekturen + Option-B-Empfehlung
  - ./PHASE12_5_FAILURE_HANDOVER.md                     # 📕 P12.5 Sofort-Befund (Interventionstag) — bleibt unverändert
  - ./PHASE12_5_MEASUREMENT_ARM_PLAN.md                 # 📕 superseded Bauauftrag: E1-E9, Steps 1-7 (unverändert, nicht editiert)
  - ./PHASE12_PREPROOF_HANDOVER.md                      # 📕 Tag-1-Befund vor P12.5 (L3, dated)
  - ../docs/concepts/phase12_data_foundation_plan.md   # 📕 Phase-12-Plan: D1-D20, Steps 0-10, §7 PASS-Kriterien (durch Phase 13 abgelöst)
  - ../phase10_v3/PHASE11_DEFERRAL_HANDOVER.md          # 📕 warum dieser Track überhaupt entstand
  - ../phase13_live_data/PHASE13_CLOSEOUT_HANDOVER.md # 📕 **die strukturelle Antwort** — vier Stufen, Verbrauch liest nur
  - ../phase14_discovery/CLAUDE.md                     # 🔄 die Source-Registry darüber (instrument_source_availability)
  - ../docs/architecture/phase12_closeout.svg          # 📕 diese Phase, bildlich (1080×1080, Fehlerbild + Zielbild, Closeout)
  - ../docs/architecture/phase12_5_failure.svg          # 📕 P12.5-Fehlerbild im Detail
  - ../docs/architecture/data_foundation.svg             # 📕 Phase-12-Architektur-Überblick
  - ./SESSIONS_ARCHIVE.md                               # 📦 rotierte Session-Blöcke (L3)
updated: 2026-08-25
---
# CLAUDE.md — Phase 12: Datenfundament (`phase12_data_foundation/`)

> Three data weeks (Phase 11) died on infrastructure, never on measurement. Root cause: one
> instrument fact lived in three divergent stores, the Phase-9 multi-source bar chain
> (`ChainedBarProvider`) was built and never switched on (`enable_ig_bars` default `False`).
> **Source of truth is the plan doc + the code, not this file.** Full plan:
> `../docs/concepts/phase12_data_foundation_plan.md`.

## Mission (zuerst lesen) — ✅ abgeschlossen 2026-08-25, Closeout gilt
Ein neues Fundament, sequenziell (Überweg C, D1, Nikinger-Entscheidung 2026-08-11):
1. **Instrument-Registry** wird die eine Wahrheit für Instrument-Fakten; Symbol-Mapping
   abgeleitet + code-verifiziert statt deklariert.
2. **BarService** wird der eine Bar-Pfad für alle Konsumenten (Research + Paper Tracker).
3. **Bar-Archiv** (`data/bars.sqlite`) — jede gefetchte Bar wird persistiert, quellenagnostisch.
4. **Recorder** — eigener yF-only-Prozess, schreibt kontinuierlich, unabhängig vom Bot-Zustand.
5. **Mess-Heartbeat** — ein Ausfalltag fällt am selben Tag auf.
6. **Lightstreamer-Mitschrieb** (Step 10) — gated auf die bestandene Beweiswoche.

**Done-Kriterium (Plan §7) ist durch Phase 13+14 abgelöst** (Nikinger 2026-08-25).
Die Phase-12-Beweiswoche wird nicht wieder aufgenommen; die Phase-13-Beweiswoche läuft
seit Mo 2026-08-25 separat, gegen die Phase-13-Architektur (Beschaffung ≠ Verbrauch,
vier Stufen). Phase 12 ist **die Foundation**; der **Verbrauch**, der sie wert macht,
ist Phase 13+14. Saubere Trennung zwischen Foundation und Validation — genau das,
was die P12.5-Lektion gefordert hat.

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

## Session stopped — 2026-08-25 (Mo — Phase-12-Closeout, „Beweiswoche abgelöst durch Phase 13+14", Σ 1698)

> **BLUF:** Phase 12 (Datenfundament) ist **✅ abgeschlossen** (Closeout 2026-08-25). Die
> „strukturelle Antwort" auf P12.5 — „der Auflöse-Pfad kauft nie wieder Daten" — ist nicht
> mehr Empfehlung, sondern Architektur: Phase 13 Block A trennte Beschaffung und Verbrauch
> (Commit `e8c5b94`), Phase 14 macht Quellen zu einer Registry-Zeile (Migration 007). Die
> Phase-12-Beweiswoche wird nicht wieder aufgenommen; Phase-13-Beweiswoche läuft seit Mo
> 2026-08-25 separat, gegen die Phase-13-Architektur. **Vollständiger Handover — das
> erste Dokument jeder Folge-Session an Phase 12:**
> [`PHASE12_CLOSEOUT_HANDOVER.md`](./PHASE12_CLOSEOUT_HANDOVER.md). Read-only-Analyse, kein
> Produktionscode-Edit; eine eigenständige, dokumentationsdominierte Atom-Einheit.

### Completed

- **As-Built-Inventur** (Read-only): jede Zahl selbst nachgemessen — Phase-12-Tests
  **143 grün**, Σ-Sweep **1698 grün / 0 fails**, **`main` = `origin/main` = `b9327ca`**,
  18 `phase12:`-Commits auf origin, 0 unpushed lokal. Keine Zahl aus Vordokumenten
  übernommen, was sich selbst prüfen ließ.
- **`PHASE12_CLOSEOUT_HANDOVER.md`** geschrieben (L3-Snapshot) — 5-Zeilen-Bilanz
  (fertig/getestet/live-validiert/gepusht/nicht-erreicht), Architektur-Bild in
  einer Zeile mit der Phase-13-13-Antwort gegenüber der Phase-12-Foundation,
  §3 Delta seit P12.5-CLOSEOUT-HANDOVER, §4 4 offene Entscheidungen (alle durch
  Nikinger 2026-08-25 geklärt), §5 Datei-Anker, §6 sechs Konsistenz-Regeln, §7
  sechs Don't-Anweisungen. Nach Handover-Vertrag: keine Implementierungsdetails
  wiederholt, Code bleibt Wahrheit.
- **`docs/architecture/phase12_closeout.svg`** (1080×1080) — drei-Panel-Layout:
  Fehlerbild (Phase-12-Auflöse-Pfad kaufte von IG, 4731/10000 IG-Wochenpunkte,
  92 % verschwendet) + Zielbild (Phase-13-Architektur: vier Stufen Beschaffung
  → ein Archiv → Verbraucher kauft NIE; Phase-14-Quell-Registry als Krönung)
  + Status (Phase 12 abgeschlossen, 4 Entscheidungen geklärt).
  Style-konsistent mit `data_foundation.svg` / `phase12_5_failure.svg` /
  `phase13_live_data.svg`.
- **Status pflegepropagiert in diesem einen Commit**: Root-`CLAUDE.md`
  (Phase-12-Row: `🔄 in Arbeit → ✅ abgeschlossen`, Closeout-Handover-Link,
  Hinweis: „Beweiswoche abgelöst durch Phase 13+14"); `ROADMAP.md`
  (Phase-12-Header gleicher Status-Flip + Closeout-Verweis); `docs/INDEX.md`
  (`Active phases`-Header ohne P12 + `Closed phases`-Header mit P12; zwei neue
  INDEX-Zeilen — Closeout-Handover-Linie + SVG-Linie; phase12_data_foundation-
  Linienreflex: Closeout-Link); Phasenkopf selbst (YAML/Mission/Module-Box).
- **Drei Drift-Korrekturen an Doku** (Code = source of truth):
  1. **Phase-12-Tests 123 → 143 Tests** (Head war stale; +20 Tests seit
     2026-08-18 weil Phase-13-Block-A-`coverage.py` + `service.py`-Edits
     dort mit-testen). Korrektur im selben Commit, gegen `pytest
     phase12_data_foundation/tests -q`.
  2. **P12.5-CLOSEOUT-Head-Zeile „`main` 4 Commits vor `origin/main`**
     status" — war zum damaligen Zeitpunkt real; beim Stand 2026-08-25
     history (heute: `main` = `origin/main`). Wer die Head-Zeile heute liest
     und die Aussage prüft, findet sie **nicht** — richtig, ist Geschichte.
  3. **Header `## Session stopped — 2026-08-18` (Session 9 = Closeout-
     Analyse)** bleibt **unverändert in der Geschichte** — siehe
     SESSIONS_ARCHIVE.md (rotiert verbatim, Auditkette).
- **Keine Cross-Phase-Produktionscode-Edits** in dieser Session. Phase-12-
  Closeout ist eine **eigenständige dokumentationsdominierte Atom-Einheit**
  (analog zu den Closeouts von Phase 10 / 13). Bot läuft unverändert weiter.

### Findings (eines, ehrlich)

- 🟡 **Test-Stand-Drift Phase 12 123 → 143:** die +20 Tests sind **nicht
  Phase-12-Eigenleistung**, sondern Phase-13-Block-A-Erweiterungen, die in
  `phase12_data_foundation/tests/` mitgetestet werden. Code ist source of
  truth (143 ist real); die Modul-Tabelle in `README.md` müsste diese Zählung
  eigentlich widerspiegeln — aufgeschoben für eine separate Hygiene-Mini-
  Session, weil die README-Anpassung nicht Phase-12-Closeout-Scope ist (siehe
  §4 Entscheidung 5 dieses Blocks: Testlücke „keine Kosten-Zusicherung"
  bleibt latent bis zu einer künftigen Messarm-Re-Aktivierung).

### Unverändert offen

- **Phase 11 (V3-Fortsetzung)** bleibt 🛑 DEFERRED — WI-2/W2 + H3/H5/H7
  + B3-Margin-Headroom. Datenfundament ist die Voraussetzung; Beweiswoche läuft;
  weitere Aufnahme ist P12/13/15.
- **Beweiswoche Phase 12** — wird nicht wieder aufgenommen, Beweiswoche
  Phase 13 läuft seit Mo 2026-08-25.
- **Resolution-Source-Drift `IX.D.IBEX.FWM2.IP`** — durch P13+14 überholt,
  bleibt ungelöst im Hintergrund.

### Next

- **Operator (Nikinger):** **Push-Freigabe** für den Phase-12-Closeout-Commit.
  Diff ist dokumentationsdominiert: ein .md-File neu
  (`PHASE12_CLOSEOUT_HANDOVER.md`) + ein .svg-File neu
  (`phase12_closeout.svg`) + Phasenkopf-Updates + Root-CLAUDE.md-Row +
  ROADMAP-Sektion + INDEX.md-Einträge. **Sweep** Σ 1698 grün, kein
  Bot-Touch, kein Cross-Phase-Produktionscode-Edit.
- **Phase 12 ist abgeschlossen und wird nicht wieder aktiv.** Jeder
  Touch am Produktionscode braucht eine **neue Cross-Phase-Freigabe**
  des Nikinger (Cross-Phase-Freigabe-Liste für Phase 14 deckte Phase 12
  teilweise, ist hier nicht relevant).
- **Phase 15 Plan-Session (V4)** — bleibt long-horizon, gegatet auf
  Outcomes aus Phase 9+11+12+13+14.
- **Phase-13-Beweiswoche** läuft seit Mo 2026-08-25, **nicht** vor
  Abschluss WI-2/W2 beantwortbar.

---


> **Ältere Session-Blöcke** (verbatim ausgelagert, newest-first): [SESSIONS_ARCHIVE.md](./SESSIONS_ARCHIVE.md) — Rotation per Doc-Layers-Konvention ([docs/DOC_LAYERS_CONVENTION.md](../docs/DOC_LAYERS_CONVENTION.md)).
