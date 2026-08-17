---
status: live
purpose: PHASE-HEAD, Phase 12 (Datenfundament) — Registry + BarService + Bar-Archiv + Recorder + Heartbeat. Steps 0-8.5 gebaut, getestet (P12 117) und auf main committed (zuletzt 47d89b0) — die "still UNCOMMITTED"-Aussage früherer Fassungen ist überholt, korrigiert 2026-08-17 gegen git log. Session 6 (2026-08-17): erster voller Handelstag live ausgewertet — Resolver/Recorder/Archiv/Budget end-to-end bewiesen, ABER der Messarm (enable_shadow_schedule) ist aus ⇒ 0 Paper-Zeilen; dazu vier verifizierte Ultrareview-Befunde U1-U4 (Sampler tot, Paper-Retry-Cap wirkungslos, _covers_tail einseitig, Mapper stale) — alle ungefixt, Fix-Orte im Handover §3.0. Step 9 kann so nicht bestehen. Phase 12 ist OFFEN, nicht abgeschlossen; Done-Kriterium (Beweiswoche, Plan §7) nicht erreicht.
read-when: working in phase12_data_foundation/ — read PHASE12_PREPROOF_HANDOVER.md first (Tag-1-Ergebnisse, die drei Befunde vor Step 9, Entscheidungen A-D), dann diesen Kopf + den newest Session-stopped block; der volle Plan (docs/concepts/phase12_data_foundation_plan.md) ist der Ausführungsvertrag, dessen §6-Step-Block vor jedem Bauen lesen
detail: L2
up: ../CLAUDE.md
down:
  - ./PHASE12_PREPROOF_HANDOVER.md                      # Stand vor der Beweiswoche, Tag-1-Ergebnisse, Entscheidungen A-D (L3, dated)
  - ../docs/concepts/phase12_data_foundation_plan.md   # full execution-ready plan, D1-D20, Steps 0-10 (L3, ausführungsreif)
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

## Rahmen (Plan §1, verbindlich)
Bot-berührende Steps nur am Wochenende (Bot steht, Markt zu). Werktags: docs-only /
`data_foundation/`-Paket-Code selbst (eigene Dateien, eigene Tests, kein bestehender
Phasen-Code, nichts in `data/` geschrieben). Live-/Netz-/Kosten-Tests macht der Nikinger.

## Modul-Tabelle
Siehe [`README.md`](./README.md).

---

## Session stopped — 2026-08-17 (Session 6: Tag-1-Live-Auswertung + Pre-Proof-Handover)

> **Auftrag:** Auswertung des ersten vollen Handelstags mit dem kompletten Stack, Antwort
> auf die offenen Fragen aus Session 5, Vorschlag für die Zeit nach Steps 9/10 — und der
> Handover. **Kein Bot-berührender Code angefasst** (Werktag, Bot läuft): read-only DB
> (`mode=ro`), Doku, `.gitignore`. Alle Zahlen unten selbst erhoben, keine aus früheren
> Blöcken übernommen.
>
> **Vollständiges Ergebnis: [`PHASE12_PREPROOF_HANDOVER.md`](./PHASE12_PREPROOF_HANDOVER.md)**
> — dieser Block ist die Kurzfassung, nicht die Quelle.

### Completed

1. **Tag-1-Live-Auswertung** (Recorder `pid 33151` seit 09:56 CEST, Scheduler `pid 35195`
   seit 12:09 CEST mit `--enable-divergence-sampler`). Ergebnis: die Kette
   Resolver → Registry → `measurable_universe()` → Recorder/BarService → `bars.sqlite`
   läuft end-to-end **live**, ohne Operator-Eingriff (Details: Handover §2).
2. **`PHASE12_PREPROOF_HANDOVER.md`** (neu) — Status, Tag-1-Ergebnisse, die drei Befunde
   vor Step 9, Delta gegen `PHASE11_DEFERRAL_HANDOVER.md` (A–G), Entscheidungen A–D,
   Vorschlag für nach Steps 9/10.
3. **`../docs/architecture/phase12_preproof.svg`** (neu, 1080×1080) — was steht, was fehlt,
   warum der Alarm es nicht merkt.
4. **Statuspflege** im selben Commit: Root-`CLAUDE.md`, `ROADMAP.md`, `docs/INDEX.md`,
   dieser Phasenkopf, Rotation des Session-5-Blocks nach `SESSIONS_ARCHIVE.md`.
5. **`.gitignore`**: `data/state/recorder.pid` + `data/state/recorder_state.json` ergänzt
   (Phase-12-Laufzeitdateien, waren als einzige Dateien unter `data/` nicht ignoriert —
   ein `git add -A` hätte Laufzeitstand committet; gleiche Einzelpfad-Konvention wie
   `llm_usage.json`/`execution_state.json`).
6. **Doku-Korrektur gegen Code** (Code gewinnt, datiert vermerkt): Phasenkopf und
   `docs/INDEX.md` behaupteten „Steps 7/8/8.5 uncommitted" — `47d89b0` (+ `37f2f0a`) haben
   sie gelandet. Korrigiert.

### Verified

- **Registry:** 22 Zeilen → 5 `active`/`ok`, 3 `active`/`no_intraday_source` (SUN*), 13
  `verified`/`unverified`, 1 `quarantined`. `measurable_universe()` erstmals **nicht leer**
  ⇒ **Step 8.5 ist live bewiesen**, nicht nur regression-grün.
- **Resolver-Timing:** Pass 1 `10:14:38Z` (Startup-erzwungen — `runner.py:285` ruft
  `_run_universe_refresher()` im Preflight, **vor** der 240-Min-Drossel; korrigiert die
  Session-5-Operator-Notiz, die einen unklaren Wartezeitraum nahelegte), Pass 2 `12:19Z`.
- **Recorder:** erster 1m-Write `10:16:32Z` = **114 s** nach dem ersten Resolver-Write;
  62 Fetch-Batches im 5-Min-Takt, `errors: []`.
- **Archiv:** 1891 Bars, **alle heute** geschrieben.
- **Allowance-Bugfix aus Session 5 wirkt live:** 28 echte `allowance_observations`
  (`total=10000`, `remaining=9724`, `expiry=2026-08-23T20:53Z`), Verbrauch 136 Punkte —
  damit ist die letzte offene Frage aus Session 5 („erster echter Live-Effekt") **geschlossen**.
- **Step-6-Operator-Pfad erstmals real gelaufen:** `data_health.py --day 2026-08-17` →
  `ok: True`, Exit `0`.
- `pytest phase12_data_foundation/tests -q` → **117 passed** (heute nachgelaufen).

### Befunde (Details + Belege: Handover §3)

- 🔴 **Blockierend:** `enable_shadow_schedule` ist Default `False` und im laufenden Prozess
  nicht gesetzt ⇒ **0 Paper-Zeilen heute** (letzte überhaupt 2026-08-07). Der
  abstain-getriebene Pfad kann das nicht auffangen (`open_shadow_pair` braucht ein Epic;
  1465 von 1476 `abstain_records` haben `epic IS NULL`) ⇒ der H1-Timer ist der **einzige**
  lebende Messarm. Plan §7 „Kern" ⇒ **Step 9 kann so nicht bestehen.**
- 🟠 `assess_day`s Bedingung (b) hängt selbst an `shadow_enabled` ⇒ ein Nulltag meldet
  `ok=True`. Requirement G ist im Ist-Zustand blind für genau den laufenden Ausfall —
  heute live vorgeführt.
- 🟡 3 der 8 Aktiv-Plätze halten SUN*-Epics (`max_active=8`, `promotion.py` kennt
  `data_source_status` nicht) ⇒ messbarer Pool auf 5 gedeckelt.
- 🟡 **Nur Befund, fremder Scope:** `reason_no_candidates` vermischt „keine Daten" mit
  „LLM enthält sich bewusst" (der feinere Name `REASON_LLM_ABSTAIN` existiert bereits
  scheduler-seitig); `market_regime_snapshots` ist zu 100 % (1162/1162) degradiert leer.
- 🔴 **Nachtrag gleiche Session — Ultrareview, vier Befunde, alle gegen den Code
  nachverifiziert, keiner gefixt** (Analyse/Fix-Trennung, Werktag, Bot läuft). Details +
  Fix-Orte: Handover §3.0. Kurz:
  **U1** `DivergenceSampler` crasht an IGs `yyyy/MM/dd HH:mm:ss` (`heartbeat.py:175` parst
  mit `fromisoformat`, `service.py:119` normalisiert nicht) — Drossel wird vor dem Crash
  gesetzt, die Ausnahme killt die Epic-Schleife ⇒ **Kriterium C tot**. **Live belegt:**
  je Pass genau ein Epic, jeweils das nächste (`research_health.jsonl`) — meine frühere
  Aussage „Sampler läuft" war damit falsch und ist im Handover korrigiert.
  **U2** Retry-Cap des Paper-Trackers wirkungslos, weil `get_window` nie wirft
  (`wiring.py:514-517`, Kommentar `:477-480` behauptet das Gegenteil).
  **U3** `_covers_tail` prüft nur das Fensterende, nie den Anfang (`service.py:254-261`).
  **U4** Scheduler-`TickerMapper` wird nur beim Start befüllt (`wiring.py:175-180`) —
  reine Kostenfrage, heilt beim Neustart.
  ⇒ **Entscheidung A im Handover ist korrigiert:** erst U1–U3 fixen, dann Neustart,
  dann Step 9. „Nur ein Flag" reicht nicht mehr.

### Next

- **Nikinger-Entscheidungen A–D** (Handover §5). **A ist blockierend für Step 9:**
  laufenden Scheduler **erst stoppen** (Parallel-Login-Falle — sonst zwei IG-Sessions),
  `ps aux | grep scheduler.run` als Gegenprobe, dann
  `bash phase8_scheduler/scripts/run_scheduler.sh --enable-divergence-sampler --enable-shadow-schedule`
  — danach binnen ~30 Min neue `SHADOW_BUY`/`SHADOW_SELL`-Zeilen erwarten.
- Danach erst Step 9 (Beweiswoche, 5 Handelstage, täglich `data_health.py`), dann Step 10.
- Vorschlag für nach 9/10: Funnel-Reason-Split → Promotion lernt `data_source_status` →
  Phase-11/WI-2-Wiederaufnahme (Handover §6). Nummerierung entscheidet der Nikinger.
- Die zwei bekannten Step-6-Lücken (G-Deckung an einem POST_WINDOW-losen Tag;
  In-Memory-Sampler-Throttle über Neustarts) bleiben unverändert offen.

### Open questions / blockers

- **Blocker für Step 9: Entscheidung A** (Messarm einschalten). Ohne sie misst die
  Beweiswoche nichts und läuft in einen garantierten FAIL.
- `main` ist **12 Commits ahead of `origin/main`** — committet wie beauftragt, **nicht
  gepusht** (Entscheidung D).

---

> **Ältere Session-Blöcke** (verbatim ausgelagert, newest-first): [SESSIONS_ARCHIVE.md](./SESSIONS_ARCHIVE.md) — Rotation per Doc-Layers-Konvention ([docs/DOC_LAYERS_CONVENTION.md](../docs/DOC_LAYERS_CONVENTION.md)).
