---
status: snapshot
purpose: Phase-10-Closeout-Handover (2026-08-25, Nikinger-Freigabe 2026-08-25) — Phase 10 (V3: Abstain-Lessons + Persistenz-Reform + Paper-Trades) ist ✅ abgeschlossen. Council-Paper-Call ist **bis auf weiteres in mind Phase 15 verschoben** (Nikinger 2026-08-25). Was die nächste Session wissen muss, BEVOR sie einen Plan schreibt — knapp, code-zentriert, kein Plan-Reprint. Read-only-Inventur, jeder Datenpunkt selbst nachgemessen. **§8 (diese Datei): Phase-11-Wiederaufnahme-Inputs von Nikinger 2026-08-25 (Wait-Default + Positive-Lessons-Pflicht) — keine Plan-Arbeit vor Phase-13-Beweiswoche.**
read-when: vor jedem Plan, der Phase 11 wieder aufnimmt; vor jedem Touch an `enable_paper_debate`/Council; vor jedem Re-Read der Bugfix-Block-Historie; vor jeder Frage „ist Phase 10 eigentlich fertig?"; **für Phase-11-Wiederaufnahme-Inputs: §8 dieser Datei (Nikinger 2026-08-25)**
detail: L3
up: ./CLAUDE.md
down:
  - ./PHASE11_DEFERRAL_HANDOVER.md   # 📕 die Notbremse vom 2026-08-11 — Phase-10-Status dort unverändert ✅; **Einstieg für Phase-11-Wiederaufnahme + §8 dieser Datei für Nikinger-Inputs 2026-08-25**
  - ../docs/concepts/phase10_v3_plan.md   # 📕 execution-ready Plan (L1–L11, Decisions V3-D1…D10, 📕 Convention „never edit")
  - ../docs/concepts/PHASE10_V3_KICKOFF_HANDOVER.md   # 📕 Kickoff-Handover aus M1 → V3
  - ./DATA_SOURCE_STRATEGY_2026-08-11.md   # 📕 die Richtung (mit Korrektur §2.6: nur Workaround, kein Bestätigungs-Beweis)
  - ./ALLOWANCE_INCIDENT_2026-08-08.md   # 📕 das IG-Kontingent + Restart-Gate
  - ./DATA_WEEK_REVIEW_2026-07-25.md   # 📕 WI-1..WI-6 + 2 Bugfixes + N1/N2
  - ./DATA_WEEK_REVIEW_2026-07-31.md   # 📕 Datenwoche 2 (W1/W5 bestätigt + Phase-11-Hypothesen H1-H7)
  - ./DATA_WEEK_REVIEW_2026-08-07.md   # 📕 Datenwoche 3 (Allowance-Incident, §3 SUPERSEDED durch ALLOWANCE_INCIDENT_2026-08-08.md)
  - ../docs/architecture/phase10_v3.svg   # 📕 diese Phase, bildlich (1080×1080)
  - ./SESSIONS_ARCHIVE.md   # 📦 volle Session-Historie (verbatim, newest-first)
updated: 2026-08-25
---

# Phase 10 (V3) — Closeout-Handover (2026-08-25)

> **Autor:** Claude Code, Read-only-Analyse 2026-08-25, **kein** Produktionscode-Edit.
> **Adressat:** die nächste Session an Phase 11 / Datenfundament / Phase 15 (V4).
> **Quelle aller Zahlen:** eigene Re-Sweeps + Git-Historie + Live-DB `mode=ro`. Nichts aus
> Vordokumenten übernommen, was sich selbst hat prüfen lassen.

---

## §0 BLUF

Phase 10 ist **abgeschlossen**. Block A (Abstain-Lessons) und Block B (Persistenz-Reform +
Paper-Pipeline) sind live auf `main` und dort seit dem **Montag-Restart-Beweis 2026-07-14**
laufend verifiziert — 66 echte `abstain_records`-Zeilen als erster Real-Kontakt. Der Bugfix-
Block 2026-07-25/31/08-08 hat drei stille 100-%-Failure-Rate-Bugs behoben (Wiring-MINUTE_1-Resolution,
Reflect-Schema, point_value-Drift) und die Allowance-Incident-Wurzel aus der dritten Datenwoche
adressiert.

**Council-Paper-Call ✅ gebaut, aber bis auf weiteres in mind Phase 15 verschoben**
(Nikinger 2026-08-25). Der `enable_paper_debate`-Flag bleibt default `False`. P15-V4-Council
subsumiert die P10-Paper-Implementation als Eingangs-Schnittstelle, nicht als Endpunkt —
Bull/Bear/Judge für Live-Trades ist ein größeres Architekturthema als nur Paper-Shadow-Trades.

**Was bleibt offen** ist nicht „Phase 10 unvollständig", sondern **das Phase-11-Erbe** —
WI-2/W2, H3/H5/H7, B3-Margin-Headroom. Diese leben im Phase-12/13-Datenfundament-Track,
nicht in Phase 10; sie waren nie Voraussetzung für den Phase-10-Abschluss.

---

## §1 Bilanz (5-Zeilen-Schema, Handover-Prompt-Stand)

| Zeile | Stand 2026-08-25 (selbst nachgemessen) |
|---|---|
| **fertig gestellt** | Block A (Abstain-Lessons: Migration 005 + `AbstainStore` + 12-Reason-Classifier + `reflect_abstain` Haiku-Tages-Cap + Sink-Naht am P5-Executor + Wiring im P8-Runner, Sa WE 1 2026-07-11) · Block B (`market_regime_snapshots` + `decision_context` episcoped statt trade-scoped + `regime.py` quote_only-Degrade + `MarketContextWriter`/`ContextRecorder` + Paper-Engine: `open_shadow_pair` / `resolve_paper_trade` / `PaperEngine` / `PaperTradeTracker` / `paper_store`, Sa WE 2 2026-07-17) · Council-Paper-Call (Folge-Session 2026-07-17, `_AbstainLLMAdapter` für Paper-Trades, default OFF) · Bugfix-Block 2026-07-25 (zwei Wiring-Bugs: `"MINUTE_1"` → `"MINUTE"` + `_SCHEMA additionalProperties: False`) · Bugfix-Block 2026-07-31 (B1 point_value-Drift, 40×-Oversizing-Fix) · Bugfix-Block 2026-08-08 (Allowance-Incident-Fix + B5 Lesson-Salvage + Fetch-Cap + Stale-Expiry) · H1 (time-scheduled Shadow-Pairs, default OFF, 1 Woche gelaufen) · H4-a (Lesson-Alters-Cap, default ON, Wirkung ungemessen) |
| **getestet** | **165** Phase-10-Unit-Tests grün (frisch gemessen 2026-08-25); Σ 1698 repo-weit (Phase 8 248 + Phase 14 57 + alle anderen unverändert) · ⚠ Korrektur zur Phase-10-Head-Doku: dort steht „147 Tests" — Code = source of truth, real 165 |
| **im Rahmen der Möglichkeiten live validiert** | Block A: **66 echte `abstain_records`-Zeilen** auf `data/trading_bot.sqlite`, 100 % `REASON_NO_CANDIDATES`, Mo 2026-07-14 (Restart-Beweis) · Block B observe-only: `regime_tag` lebt, degradiert sauber auf `quote_only` wenn keine Bars da sind · B1-Fix: erklärt die 3 AEX-Rejects (07-15, 07-20, 07-30) **retroaktiv** — der Fix selbst ist offline-bewiesen, die Erklärung ist real-getestet · H1: lief Mo 2026-08-03 bis Fr 2026-08-07 (1 Woche) bis Allowance-Incident ihn stoppte · **Council-Paper-Call: nie live** — `enable_paper_debate=False` seit Build (Operator hat das Flag nie geflippt) · **H4-a: nicht messbar** — der Cap rollt erst ab 2026-08-20; Lessons-Alter war bei keinem realen Restart jung genug, um den Cap zu triggern |
| **gepusht und committet** | **`main` synchron mit `origin/main` (HEAD = 03a0919)** · 25 `phase10_v3:`-Commits auf origin, latest = `6dd5458 phase10_v3: record the four follow-up fixes in the session block` · keine lokalen unpushed Commits |
| **nicht erreicht / offen geblieben** | (a) **Council-Paper-Call live-validierung** — nie enabled; **deferred → Phase 15** (Nikinger 2026-08-25, „bis auf weiteres in mind P15") · (b) **WI-2/W2 Funnel-Antworten** — unbeantwortet, gehören in den Datenfundament-Track (Phase 12/13/14), nicht zu Phase 10 · (c) **H3 / H5 / H7** — nicht gebaut (Phase-11-Restestate, dort dokumentiert) · (d) **B3 Margin-Headroom** — deferred per Session 2026-07-25 · (e) **M2** — geparkt, kein V3-Blocker · (f) **S6 (Prompt-Rückspeisung)** — Code da, Flag default OFF, Operator-Flip wartet auf Lesson-Review · (g) **Block C (UI)** — out of scope per Plan §13 · (h) **H4-a Wirkung** — ungemessen; siehe §6 für die Konsistenz-Regel |

---

## §2 Architektur-Bild (in einer Zeile)

```
                         P5-Executor (NO_TRADE-Pfade)
                                   │
              ┌────────────────────┼─────────────────────┐
              ▼                    ▼                       ▼
     AbstainSink      ContextRecorder (each cycle)   PaperTracker-Tick
         │                       │                      │
         ▼                       ▼                      ▼
   AbstainStore            market_context/             paper_store
   (abstain_records)       (decision_context,          (paper_trades
        │                   market_regime_snapshots)    both sides)
        ▼                                                  │
  reflect_abstain                                          ▼
  (Haiku, Tages-Cap)                              Council-Paper-Call
                                                   (enable_paper_debate
                                                    = False, deferred → P15)
```

Quellen-Tabelle: siehe Code. Der Plan `phase10_v3_plan.md` bleibt `📕` (nicht editieren);
diese Zeile ist die **kanonische Zusammenfassung** für Folge-Sessions, ohne den Plan zu
wiederholen. Bildlich: `../docs/architecture/phase10_v3.svg` (1080×1080, dieses Commits).

---

## §3 Delta seit dem letzten Handover

Letzter Handover: `phase10_v3/PHASE11_DEFERRAL_HANDOVER.md` (2026-08-11) — die Notbremse.
Phase-10-Status dort: `### Phase 10 (V3) — ✅ abgeschlossen, unverändert`. Was sich seitdem
geändert hat (in dieser Reihenfolge der Audit-Relevanz, nicht chronologisch):

### 3.1 Nummerierungs-Kaskade 2026-08-22 (Phase-13-Close)
Phase 14 wurde von „Phase 14 (V4)" zu „Phase 14 (Discovery)" umnummeriert; V4 rutschte
auf Phase 15. **Phase 10 hat diese Kaskade inhaltlich nicht berührt** — der
Council-Paper-Call, der dort als „V4-Vorschau" lief, ist jetzt explizit als **P15-Item**
geführt. Heute, 2026-08-25, faltet der Nikinger das explizit aus („bis auf weiteres in
mind P15"); siehe §1 Zeile 5 und §4.

### 3.2 Migrations-006-Land für Phase 12
Phase-2-Migration 006 (Phase 12, Datenfundament-Registry-Erweiterung) kam nach Phase 10;
**additiv**, kein Phase-10-Touch. Doku-Verweis zur Auditkette.

### 3.3 Phase 14 nutzt Teile der Phase-10-Bibliothek
Phase 14 importiert `source_registry.arm` und braucht dieselben Muster (deterministische
Persistenz, kein LLM in der Discovery-Schleife). Die Phase-10-Entscheidungen — „Code macht,
nur zwei AI-Nähte (reflect_abstain + Council)" — wirken unverändert. Nichts an Phase 14
berührt Phase-10-Schnittstellen.

### 3.4 Heute gemessen, nicht aus Vordokument
- `phase10_v3/` Quell-Files (non-test): **16** (gezählt via `find`)
- `phase10_v3/tests/*.py`: **12** Test-Files
- Phase-10-Tests: **165 grün** (Head-Doku sagt „147", Korrektur siehe §1)
- Σ-Sweep: **1698 grün, 0 fails**
- `git log origin/main -- phase10_v3/ | wc -l`: **20 Commits sichtbar in der jüngsten
  Historie** (5 weitere in `phase10_v3/`-Vorgeschichte liegen vor dem letzten harten
  Push-Window; volle 25 siehe §1, nicht alle jüngster Natur)
- `git log --grep='^phase10_v3:' | wc -l` (lokal + origin, identisch): **25** Commits

---

## §4 Offene Entscheidungen (Nikinger)

1. **Council-Paper-Call-Code: behalten oder entfernen?** **Empfehlung: behalten.**
   Der `enable_paper_debate=False`-Default bleibt; der Code ist getestet und stört den
   Live-Betrieb nicht. Phase 15 (V4) hat ein breiteres Council-Thema — Bull/Bear/Judge für
   Live-Trades + Council-Handover-Logik + Reward-Reform. Die P10-Implementation ist ein
   **Eingangs-Schnittstelle-Vorschlag**, kein Endpunkt. **Was daraus folgt:** wenn P15-Council
   für Paper-Trades einen anderen Schema-Builder braucht, ist das ein P15-Code-Edit, kein
   P10-Edit. Alternative: P10-Council-Code jetzt entfernen → gewinnt klareres Repository,
   verliert die P15-Eingangs-Schnittstelle. **Beide Wege sind valide; ich entscheide
   nicht eigenmächtig** (Edits am V3-Code sind seit 2026-08-22 nicht mehr in der
   Phase-14-Freigabe-Liste).

2. **H4-a Alters-Cap bei Neustarts: jetzt messen oder Cap entfernen?** **Empfehlung: Cap
   stehen lassen, beim nächsten echten Restart den Effekt eine Woche beobachten** (Lessons
   werden jünger, dann greift er). „Entfernen" verliert die automatische Lesson-Frische-Garantie.
   **Was daraus folgt:** wenn der Cap nach 2 Wochen Live-Betrieb weiterhin „null Trigger" zeigt,
   ist er zurecht dead code und sollte dann entfernt werden — eigene Mini-Session.

3. **S6 (Prompt-Rückspeisung): wann aktivieren?** Per Phase-10-Plan-§11 bewusst **Operator-
   geflippt**, nicht automatisch. **Empfehlung: nicht vor Phase-12-Beweiswoche-Ende** —
   sonst fließen Lessons zurück in einen Research-Layer, der noch ohne zuverlässiges
   Datenfundament prompt-ed wird. **Was daraus folgt:** die S6-Aktivierung ist eine
   separate, kleine Session, ~30 Min, reines Operator-Flippen + Lesson-Review vorab.

4. **Phase-10-Modul-Tabelle stale (147 Tests statt 165): Korrektur jetzt oder in Phase-11-
   Wiederaufnahme?** **Empfehlung: jetzt mitnehmen** (in dieser Commit-Kette, ist ein
   Documentation-only-Edit im Phase-Head). Alternative: lassen für Phase-11-Wiederaufnahme.

---

## §5 Datei-Anker

**Zuerst lesen:**
- [`./CLAUDE.md`](./CLAUDE.md) — Phasenkopf + neuester Session-Block
- [`./PHASE11_DEFERRAL_HANDOVER.md`](./PHASE11_DEFERRAL_HANDOVER.md) — die Notbremse, Phase-10-Status dort ✅
- [`../docs/concepts/phase10_v3_plan.md`](../docs/concepts/phase10_v3_plan.md) — der frozen Plan (📕, „never edit")
- [`../docs/architecture/phase10_v3.svg`](../docs/architecture/phase10_v3.svg) — diese Phase, bildlich (1080×1080, dieses Commits)

**Die Nähte, die Phase 10 dem Restprojekt gegeben hat (Code ist Wahrheit — hier nur Wegweiser):**
- `phase2_persistence/migrations/005_v3_learning.sql` — `abstain_records` + `market_regime_snapshots` (epic-scoped) + `decision_context` (epic-scoped)
- `phase10_v3/abstain_lessons/` — Models, Classifier (`AbstainReason` 12-Taxonomie), Store, Sink, Paper-Modul + Paper-Store + Paper-Engine + Tracker-Tick
- `phase10_v3/market_context/` — Regime-Features (`regime.py` quote_only-Degrade), Writer, Context-Recorder
- `phase10_v3/scripts/abstain_report.py` — `--paper`-Sektion für die Both-Sides-Auswertung
- Cross-Phase-Nähte: `phase5_execution/execution/executor.py` (Sink), `phase8_scheduler/scripts/wiring.py` (Tracker-Closure), `phase8_scheduler/scheduler/runner.py` (Tracker-Tick), `phase8_scheduler/scheduler/run.py` + `config.py` (`enable_paper_debate` Flag)

**Historie, nur bei Bedarf:** `phase8_scheduler/PHASE8_CLOSEOUT_HANDOVER.md` (war der
letzte echte Closeout-Handover vor Phase 10), `./STEP0_DATA_ANALYSIS_2026-07-10.md`
(Step-2-Output, dated), `./WEEK1_REVIEW_2026-07-17.md`,
`./TRADE_DATA_DIAGNOSIS_2026-07-19.md`, `./DATA_WEEK_REVIEW_2026-07-25.md` / `-07-31.md`
/ `-08-07.md`, `./H4_LESSON_FEEDBACK_SCOPE_2026-08-08.md`, `./ALLOWANCE_INCIDENT_2026-08-08.md`,
`./DATA_SOURCE_STRATEGY_2026-08-11.md`, `./SESSIONS_ARCHIVE.md`.

---

## §6 Konsistenz-Regeln, die Phase-10-Code aufstellt (nicht antasten, ohne Not)

1. **Genau zwei AI-Nähte** in Phase 10: `reflect_abstain` (Haiku, Tages-Cap, default ON) +
   Council-Paper-Call (`_AbstainLLMAdapter`, default OFF). Alles andere ist deterministischer
   Code. Wer eine dritte AI-Naht an Phase 10 anbringen will — **stop**, ist Code.

2. **VETOs / Gates / Sizing unangetastet.** Kein AI-Output löst je eine Order aus.
   Beweisbar: `abstain_sink` schreibt nur in DB-Tabellen, niemals in eine Order-Schnittstelle.

3. **`paper_trades` ist reine Beobachtung.** Keine echten Trades, keine Order-Pfade.
   Der Tracker ist Beobachter, nicht Akteur — Phase 15 darf das aufweichen (Council +
   Handover-Logik), aber **nicht** in Phase 10.

4. **degradation muss typisiert sein.** Block B's `regime.py` degradiert sauber auf
   `quote_only`. Wer Phase 10 ohne diese Degrade baut, bricht den Beobachter-Pfad.

5. **Alters-Cap rollt, nicht bricht.** H4-a räumt alte Lessons auf, ohne den Prompt-Block
   zu brechen (der rendert bei leerer Liste "none on record"). Diese Konsistenz muss
   jeder Lesson-Lifecycle-Edit behalten.

---

## §7 Was die nächste Session **nicht** tun soll

- **Keine** Council-Paper-Call-Aktivierung ohne expliziten Nikinger-Flip und ohne Phase-15-
  Tracking im Hinterkopf. Das Flag bleibt default `False`.
- **Keine** Phase-10-Code-Edits ohne Cross-Phase-Freigabe (die Liste der Phase-14-Commission
  deckt Phase 10 nicht ab — wer Phase 10 anfasst, holt sich bitte erst eine Freigabe).
- **Kein** „nur schnell"-Touch an `regime.py`, der die `quote_only`-Degrade wegnimmt.
- **Keine** automatische S6-Aktivierung ohne Lesson-Review (das ist **explizit** ein
  Operator-Schritt, kein Plan-Default).
- **Kein** Live-Restart für die H4-a-Messung, ohne dass die Beweiswoche-Lage es erlaubt
  (Phase 13 läuft seit Mo 2026-08-25 den Messarm).

---

## §8 Phase-11-Wiederaufnahme — Nikinger-Inputs (2026-08-25)

> Hänge an diesem Closeout-Handover fest, damit die Anforderungen nicht im
> Chat-Verlauf versickern. **Einstieg für die Phase-11-Plan-Session, BEVOR ein neuer
> Plan geschrieben wird:** §1 hier, dann `PHASE11_DEFERRAL_HANDOVER.md` §3 (Anforderungen
> A–G — alle durch Phase 12+13+14 strukturell erfüllt) + §4 (offene Entscheidungen
> — die meisten durch Phase-10/12-Closeout mit Nikinger-Entscheidungen geklärt).

### 8.1 Timing-Entscheidung: **Warten** auf die Phase-13-Beweiswoche

Phase 11 ist definitionsgemäß eine **Mess-Phase, keine Build-Phase** — sie braucht
gültige Daten als Input, nicht als Hypothese. Solange die Phase-13-Beweiswoche (seit
Mo 2026-08-25) die Datenverlässlichkeit noch nicht unter Beweis gestellt hat, würde
eine Phase-11-Wiederaufnahme das Muster zum 4. Mal reproduzieren, das die Notbremse
2026-08-11 ausgelöst hat (drei Datenwochen, gute Fragen, kaputte Daten).

**Reihenfolge** (Nikinger 2026-08-25 bestätigt):

1. Phase 13 Beweiswoche läuft (seit 2026-08-25, kein Eingriff).
2. Phase 14 D5 Final-Closure, sobald Phase 13 bewiesen hat.
3. **Phase 11 Plan-Session** mit echtem Datenmaterial + aktualisiertem Plan.

In der Zwischenzeit: **keine parallele Arbeit** an Phase 11 (außer dem optionalen
B3-Mini-Schritt, s. §8.3). Wer vor Abschluss der Beweiswoche etwas tut, arbeitet
auf einem Hypothesen-Stand, der drei Mal widerlegt wurde.

### 8.2 Zusatz-Anforderung (Nikinger-Note 2026-08-25): **Positive Lessons**

> *„Es sollte auch positive Lessons geben, das LLM soll ja aktiv dazu ermutigt
> werden funktionierende Methoden aktiv zu wiederholen."* — Nikinger

**Was heute asymmetrisch ist:** der aktuelle Lesson-Pfad
(`phase10_v3/abstain_lessons/reflect.py` + `Classifier`/`AbstainReason`) erfasst
**nur NO_TRADE/ABSTAIN-Vorfälle** — also was zu vermeiden ist. Es gibt **keinen**
Mechanismus, der Trades dokumentiert, die gut gelaufen sind, plus die Methoden/
Setups, die dazu geführt haben. Das LLM wird heute einseitig dazu ermutigt, weniger
zu tun (Avoidance-Bias), nicht aber, das Erfolgreiche zu wiederholen.

**Konsequenz für Phase-11-Wiederaufnahme** (Pflicht-Item, kein „nice to have"):

- **Positives Pendant** zu `reflect_abstain` muss existieren — eine Quelle, die
  geschlossene Trades mit positiver P&L aufnimmt, daraus eine „diese Konfiguration
  / dieses Pattern hat funktioniert"-Lesson extrahiert (deterministischer Code, nicht
  LLM-Schwall — ein Template mit `epic`, `direction`, `entry_context`, `exit_reason`,
  `p_r_multiple`, `lesson_text`).
- **Symmetrische Aktivierung**: das Prompt-Builder-`_render_lessons`-Modul
  (`phase4_research/research/prompt.py:135-142`) muss zwischen „Lessons to avoid"
  und „Lessons to repeat" unterscheiden — sonst kommt der Avoidance-Bias durch die
  Hintertür zurück, diesmal als „nur negativen Stuff rendern".
- **LLM-Encouragement (Nikinger-Anforderung, wörtlich):** der Schritt, der die
  Lessons vor dem Render filtert, muss **aktiv dazu ermutigen**, funktionierende
  Methoden zu wiederholen — also nicht nur „zeig recent_lessons", sondern
  mindestens gewichten, dass die positiven Einträge den negativen gleichwertig
  sichtbar sind. Konkret: der Render-Prompt soll beide Klassen enthalten und
  gleich lang rendern (oder positiv sogar priorisieren, falls die LLM-Confidence
  für Trade-Reproduktion sonst zu konservativ bleibt).

**Anmerkung zum Stand:** diese Anforderung steht **nicht** in der alten
`phase10_v3_plan.md` §5 (Specs S1–S7) und **nicht** im `PHASE11_DEFERRAL_HANDOVER.md` —
beide Dokumente stammen aus dem Zeitfenster 2026-07-10/11, in dem die Lessons-
Asymmetrie noch nicht thematisiert war. Die Anforderung kommt erst jetzt, von
Nikinger, in dieser Session. **Eine neue Phase-11-Plan-Session muss sie als Pflicht-
Scope-Item mit aufnehmen**, sonst bleibt die Asymmetrie strukturell.

### 8.3 Optional in der Zwischenzeit (beweiswoche-unabhängig)

- **B3 (Margin-Headroom)** als Mini-Session (~30 Min): der Live-Check ist eine
  Operator-Task (`/markets/{epic}`-Margin-Felder), die Umsetzung ist Sizing-Code.
  B3 tangiert das WI-2/W2-Messergebnis nicht (Sizing ist VOR dem Trade,
  WI-2/W2 ist NACH dem Trade). Empfehlung: **nicht** parallel starten, weil
  parallele Mini-Schritte in der sonst stillen Phase die Wiederaufnahme-
  Disziplin verwässern. Wenn B3, dann in einer eigenen Session mit eigener
  Freigabe.

### 8.4 Was die Phase-11-Wiederaufnahme NICHT mitnimmt

- **Datenfundament-Aufbau** → bleibt bei Phase 12 (✅ closed 2026-08-25)
  und Phase 13 (laufende Beweiswoche + D-Achse S3-/S4-Vorbereitung).
- **Quell-Auswahl / Source-Registry** → bleibt bei Phase 14 (✅ strukturell,
  D5 wartet auf Phase 13).
- **Council / Handover / Reward-Reform** → bleibt bei Phase 15 (long-horizon,
  gegatet auf reale Outcomes).
- **„Alles gleichzeitig"** → kein Patch auf den Lesson-Pfad, bevor die Beweiswoche
  entschieden hat, ob die jetzige Datenverlässlichkeit überhaupt stabil ist.

### 8.5 Wie diese Inputs in der Phase-11-Plan-Session zu lesen sind

Die Phase-11-Plan-Session öffnet mit dieser Sektion + §8.2 als Pflicht-Scope +
`PHASE11_DEFERRAL_HANDOVER.md` §3 (Anforderungen A–G — Status jetzt: alle erfüllt
außer G „Messfähigkeit als Betriebseigenschaft", das von der Phase-13-Beweiswoche
bewiesen werden muss) + §4 (offene Entscheidungen, davon 2 bereits entschieden:
Weg/Label abgelöst durch P13+14, Wiederanlauf abgelöst, einer offen für die
Plan-Session: konkrete Mess-Endpunkte für WI-2/W2 jenseits von „mehr Trades
abwarten"). Der neue Plan ersetzt nicht den 📕-Snapshot
`phase12_data_foundation_plan.md` — er bekommt einen **eigenen Plan-Pfad** unter
`docs/concepts/phase11_resumption_plan.md` (Nikinger-Entscheidung Vorbehalten,
Nummerierung ist hier nicht mein Bier).

---

> **Autor dieses Files:** Claude Code (Sonnet 5, MiniMax M3 via claude-minimax), Read-only-Session
> 2026-08-25. Cross-Phase-Liste (Plan §4 + Session-9-NEXT) abgearbeitet: Phase-10-Files editiert,
> Phase-9 (CLAUDE.md, models.py, store.py — Sync-Projection), Phase-2 (Migrationen), Phase-8
> (webui + wiring) **nicht** angefasst — diese Liste gilt für Phase-14, nicht für Phase-10-Close.
> **Phase-10-Closeout-Handover ist eine eigene, dokumentationsdominierte Atom-Einheit** — keine
> Cross-Phase-Edits am Produktionscode in dieser Session.
>
> **§8 ergänzt 2026-08-25, am selben Tag, Nikinger-Inputs (Wait-Default + Positive-Lessons-
> Pflicht + B3-Optionale-Separierung) sicherend.** Der Closeout-Handover bleibt sonst
> unverändert.

> **Autor dieses Files:** Claude Code (Sonnet 5, MiniMax M3 via claude-minimax), Read-only-Session
> 2026-08-25. Cross-Phase-Liste (Plan §4 + Session-9-NEXT) abgearbeitet: Phase-10-Files editiert,
> Phase-9 (CLAUDE.md, models.py, store.py — Sync-Projection), Phase-2 (Migrationen), Phase-8
> (webui + wiring) **nicht** angefasst — diese Liste gilt für Phase-14, nicht für Phase-10-Close.
> **Phase-10-Closeout-Handover ist eine eigene, dokumentationsdominierte Atom-Einheit** — keine
> Cross-Phase-Edits am Produktionscode in dieser Session.
