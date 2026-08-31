---
status: live
purpose: PHASE-HEAD, Phase 15 (V4) — 🔄 eröffnet 2026-08-31. Mission = den Lern-Signal-Pfad ehrlich machen, dann darauf aufbauen. Kern-Befund: der Reward-Loop belohnt Verluste (live −1 972,87 EUR P&L bei +28,72 Score). Plan ist execution-ready, Block B hängt an einem Live-Gate.
read-when: vor jedem Phase-15-Schritt; zuerst den neuesten `## Session stopped`-Block
detail: L1
up: ../CLAUDE.md
down:
  - ../docs/concepts/phase15_v4_plan.md      # 📕 der Plan (P1–P16, AK1–AK14, §9-Driftliste)
  - ../docs/concepts/phase7_reward_concept.md # 📕 §7b = das Instinct-Schema, nicht neu erfinden
  - ../phase10_v3/PHASE11_DEFERRAL_HANDOVER.md # 📕 H3 ist offen; Block B *ist* H3
  - ../phase14_discovery/PHASE14_CLOSEOUT_HANDOVER.md # 📕 §7 D5-H.-B, §9 Konsistenz-Regeln
  - ./PHASE15_HOOK_HARDENING_PLAN.md          # 📕 Mini-Plan P15-F (Doc-Rotation-Hook für Phase 15, 2026-08-31)
  - ./SESSIONS_ARCHIVE.md                     # 📦 verbatim Session-Historie, newest-first
updated: 2026-08-31 (A-1..A-6 protokolliert + P15-F Doc-Rotation-Hook-Härtung, MiniMax-M3)
---

# Phase 15 — V4: Reward-Kalibrierung · Instinct-ECC · Quellen-Vertrauens-Lock

**Mission in einem Satz:** bevor der Bot mehr lernt, muss das, was er lernt, stimmen.

Phase 15 ist **nicht** die fünf ROADMAP-Häkchen (15a–15e). Drei davon sind gegen den Code
falsch — 15b ist gebaut, 15c zu ~80 % gebaut, 15d bewacht ein Feature, das es nicht gibt.
Der eigentliche Auftrag steht in **§0 BLUF** des Plans:
[`docs/concepts/phase15_v4_plan.md`](../docs/concepts/phase15_v4_plan.md).

## Der Befund, der die Phase trägt

Über die einzigen 8 geschlossenen Trades hat das Konto **−1 972,87 EUR** realisiert, während
der Lern-Score von 50 auf **78,72 stieg**. Ursache ist arithmetisch, nicht strukturell:
`RewardConfig.process_weight = 1.5` macht `max|process| = 3.75` größer als
`|outcome bei R = −1| = 2.0` — ein voller Stop-Out nettet damit **positiv** (+1,10 gemessen).

`phase7_reward/reward/scorer.py:45-49` hat das am 2026-07-31 auf **+1,2 pro Verlust**
vorhergesagt und als **Phase-11 H3** geparkt. Diese Phase ist die erste, die es am
Live-Substrat gemessen hat. **Block B ist H3.**

## Blöcke

| Block | Inhalt | Gate |
|---|---|---|
| **A** | Haushalt: Step-0-Ritual, Σ-Baseline, ROADMAP-Wahrheit, Doc-Rotation | keins |
| **B** | Reward-Kalibrierung (`process_weight` 1.5 → 0.5) + Score-Reset auf 50 | **P7: „Phase-12-Reconcile-Timing Live-Verify"** |
| **C** | Instinct-ECC: Extraktion + deterministische Validierung, Promotion hinter Flag | nach B |
| **D** | Erbstücke: Quellen-Vertrauens-Lock, `phase13_14_15.svg`, Pfad A gebaut-aber-AUS | nach A |

**Nicht in Phase 15:** 15a Council-Integration · 15d als Code (moot-by-absence) ·
Auto-Gap-Fill-Scheduler (D16) · Dukascopy echt (D15). Begründungen: Plan §10.

**Cross-Phase-Freigabe (Nikinger 2026-08-31):** Phase 2, 4, 5, 6, 7, 13, 14.
**Phase 8 ist NICHT freigegeben** — kein Step braucht sie.

## Modul-Tabelle

| Modul | Zweck | Tests |
|---|---|---|
| — | *noch nichts gebaut; die Exec-Session füllt diese Tabelle (Plan Step A-0)* | — |

---

## Step A-1 — Step-0-Ritual (2026-08-31, MiniMax-M3 Exec-Session)

> **Plan-Anker:** [`docs/concepts/phase15_v4_plan.md`](../docs/concepts/phase15_v4_plan.md) §6 A-1 (S. 344-353).
> **Konvention:** Ritual wird **auch als No-Op** protokolliert (Plan §2.6).

### Turbo-Grep — `grep -rni "turbo" --include="*.py" --include="*.sql" --include="*.sh" .`

**Repo-Treffer (eigener Code): 14 Zeilen** — ausnahmslos Verweise auf den
**bewusst behaltenen** Legacy-Dateinamen `turbo_candidates.json`. Beleg-Satzerklärung:
`phase2_persistence/persistence/state.py:27-30` sagt wörtlich *"Legacy name; content =
DAX-CFD candidates, not turbos/options. Do NOT rename"*. Betroffene Dateien:

| Datei | Zeilen | Inhalt |
|---|---|---|
| `phase2_persistence/persistence/state.py` | 8, 27, 30, 114 | Konstante `CANDIDATES_FILE = "turbo_candidates.json"`, TTL-Logik |
| `phase2_persistence/tests/test_state.py` | 77 | Test-Beschreibung der Legacy-Datei |
| `phase4_research/research/models.py` | 6 | Persistenz-Hinweis |
| `phase4_research/scripts/live_test.py` | 7, 12 | Live-Test-Beschreibung |
| `phase4_research/scripts/smoke_test.py` | 8 | Smoke-Test-Beschreibung |
| `phase5_execution/execution/config.py` | 128 | Vertrag-Hinweis im Doc-Kommentar |
| `phase5_execution/scripts/wiring.py` | 18 | Wiring-Doku |
| `phase5_execution/scripts/seed_candidate.py` | 7, 101 | Seed-Script-Doku + Echo |
| `phase6_debate/scripts/smoke_test.py` | 68 | Smoke-Test-Fehlermeldung |
| `phase8_scheduler/webui/api.py` | 311, 319 | WebUI-Read des Legacy-Files |
| `phase8_scheduler/scheduler/research_tick.py` | 6, 234 | Research-Tick-Doku |
| `phase8_scheduler/tests/test_webui.py` | 370 | Test-Fixture |
| `phase8_scheduler/scripts/wiring.py` | 105 | Wiring-Doku |

**VENV-Treffer (Site-Packages, NICHT Repo-Code):** ~12 Zeilen aus
`phase1_broker_wrapper/.venv/lib/python3.12/site-packages/PIL/features.py`
(`libjpeg_turbo`) und `pygments/lexers/{asm,pascal,matlab}.py`
(`Turbo Assembler`, `Turbo Pascal`). Werden vom `--include="*.py"` mitgenommen,
sind aber nicht aus unserem Code. **Korrekturhinweis für Plan §2.6:**
die Aussage *"ausnahmslos"* gilt nur für die Repo-Treffer; die `.venv`-Treffer
sind zu ignorieren.

**Verdienst: No-Op, 5. Mal bestätigt** (vorherige Ausführungen laut §2.6:
2026-06-27, 2026-07-10, 2026-08-18, 2026-08-22). **Phase 15 führt keine neue
Turbo-Referenz ein** — Plan-Garantie eingehalten.

### EPIC_MAP-Grep — `grep -rn "EPIC_MAP" --include="*.py" .`

**3 Treffer, alle in `phase14_discovery/`** (Doc-Kommentare + Test-Beschreibung):

| Datei | Zeile | Inhalt |
|---|---|---|
| `phase14_discovery/source_registry/models.py` | 121 | Doku: *"the column whose absence in the Concept schema made `EPIC_MAP` structurally…"* |
| `phase14_discovery/source_registry/store.py` | 194 | Doku: *"Replaces `EPIC_MAP.get(epic)` in `live_data/backfill.py:180` (Phase-14…"* |
| `phase14_discovery/tests/test_store.py` | 239 | Test-Doku: *"value that replaces `EPIC_MAP.get(epic)` in `live_data/backfill.py:180`"* |

**Lesart:** aktiver `EPIC_MAP`-Code existiert **nicht** mehr im Repo (Phase-14 A2-Akzeptanz
seit Session 9 grün, `grep -rn "EPIC_MAP" phase13_live_data/ --include=*.py` ist leer —
durch Phase-14 ersetzt via `instrument_source_availability.source_symbol`). Die 3 Treffer
dokumentieren die Ablösung und sind **kein** Stop-und-Melde-Befund für Phase 15.

**Verdienst: bestätigt** — `EPIC_MAP` ist Geschichte, Dokumentation in Phase-14-Tests
bleibt stehen. Plan §8 (Phase 14 §9.12) sieht `EPIC_MAP` als durchgestrichenen Kasten
im `phase13_14_15.svg` vor.

---

## Step A-2 — Σ-Baseline (2026-08-31, MiniMax-M3 Exec-Session)

> **Plan-Anker:** [`docs/concepts/phase15_v4_plan.md`](../docs/concepts/phase15_v4_plan.md) §6 A-2 (S. 356-359).
> **Erwartung:** Σ = **1703** (Plan §2.1, selbst gemessen 2026-08-31 in der Plan-Session).
> **Kommandoform (verifiziert):** `cd <phaseN> && ../phase1_broker_wrapper/.venv/bin/python -m pytest tests/ -q`

### Sweep-Ergebnis — Σ = 1703 grün, exakt Erwartung

| Phase | Tests grün | Σ-Sweep-Laufzeit | Anmerkung |
|---|---:|---|---|
| phase1_broker_wrapper | **95** | 0,36 s | — |
| phase2_persistence | **77** | 11,34 s | langsamster (DB-Fixture-Setup) |
| phase3_external_data | **104** | 0,21 s | — |
| phase4_research | **155** | 0,19 s | — |
| phase5_execution | **173** | 0,19 s | — |
| phase6_debate | **76** | 0,08 s | — |
| phase7_reward | **142** | 0,10 s | — |
| phase8_scheduler | **248** | 1,51 s | 1 Warning (`httpx`-Deprecation in starlette testclient) — pre-existing, nicht Phase-15-relevant |
| phase9_universe | **87** | 4,36 s | — |
| phase10_v3 | **165** | 0,98 s | — |
| phase12_data_foundation | **145** | 2,85 s | — |
| phase13_live_data | **74** | 2,64 s | — |
| phase14_discovery | **61** | 1,13 s | — |
| root `tests/` | **101** | 2,91 s | — |
| **Σ repo-weit** | **1703** | ~29 s | = Plan-Erwartung exakt ✅ |

> **Phase 11 hat kein eigenes `tests/`-Verzeichnis** (lebt in `phase10_v3/`),
> Phase 15 bekommt in Step C1 eins. Beide Zeilen fehlen deshalb in der Σ-Tabelle
> — konsistent mit Plan §2.1.

**Drift-Finding (gemessen 2026-08-31 14:44 UTC):** HEAD = `aad1d00`, 1 Commit
**ahead** of `origin/main = d1dd26b`. Commit-Message `aad1d00` (16:21 CEST)
behauptet *"Push erledigt: origin/main = d1dd26b, 0 ahead / 0 behind"* —
**inkonsistent** mit `git status` (1 ahead). Mögliche Lesarten: Push nach
Commit fehlgeschlagen, oder Commit/Push-Reihenfolge vertauscht. **Kein Phase-15-Edit
hier**, kein Push-Versuch meinerseits (kein expliziter Auftrag). Sichtung an Nikinger
zur Klärung, ob `git push origin main` gewünscht ist — siehe Findings-Block am
Session-Ende.

**Phase-15-Bereitschaft:** Σ-Baseline steht **vor** dem ersten Fix (Plan §6 A-2: *"vor
dem ersten Fix"*). Jede Abweichung vom Σ ≥ 1703 nach einem Phase-15-Schritt ist ein
**Befund von Phase 15**, nicht von vorher.

---

## Step A-3 — ROADMAP-Wahrheit hergestellt (2026-08-31, MiniMax-M3 Exec-Session)

> **Plan-Anker:** [`docs/concepts/phase15_v4_plan.md`](../docs/concepts/phase15_v4_plan.md) §6 A-3 (S. 361-394).
> **Scope:** drei Edits in `ROADMAP.md`, jeder mit datiertem Vermerk
> „*korrigiert 2026-08-31 (Phase-15-Plan-Session §2/§3)*".

### 15b — Handover-Logik (Bull/Bear/Judge) — `ROADMAP.md:691-694`

| Item | Vorher | Nachher | Beleg |
|---|---|---|---|
| Context-window monitoring (~60–70 %) | `[ ]` | `[x]` | `phase6_debate/debate/debate.py:172` (`cfg.compression_trigger_pct * cfg.max_cumulative_input_tokens`). **„gebaut"**, nicht „live-verifiziert" (Plan §9 #4). |
| Compression of B/B/J state into summary | `[ ]` | `[x]` | `phase6_debate/debate/debate.py:187-195` (deterministischer Latch). **„gebaut"**, nicht „live-verifiziert". |
| New session continuation | `[ ]` | `[ ]` *gegenstandslos* | — durch laufende Compression ersetzt; keine neue Session nötig |

### 15c — Reward/Punishment Reform — `ROADMAP.md:696-698`

| Item | Vorher | Nachher | Beleg |
|---|---|---|---|
| `+ process_quality_score` (VETOs, confidence, debate quality, gate path) | `[ ]` | `[ ]` *partial* | „VETOs"/„gate path" = **gegenstandslos** (P4, 0/1902 `abstain_records` mit `stage='veto'/'gate'`); „confidence"/„debate quality" = **gebaut** (`phase7_reward/reward/scorer.py:122-131` — `entry_signal` aus `spread_at_entry_pct`, `debate_signal` aus `debate_confidence`) |
| Anti-emotionality: separate process score from outcome score | `[ ]` | `[x]` | `phase7_reward/reward/scorer.py:114-133` (`outcome_delta` Z. 112 + `process_delta` Z. 133 unabhängig). **Kalibrierung** in Block B (P1/P2) — die strukturelle Trennung steht, der Score stimmt noch nicht. |

### 15d — Force Trigger Safeguard — `ROADMAP.md:700-701`

| Item | Vorher | Nachher | Beleg |
|---|---|---|---|
| Lock force trigger when daily PNL < 0 | `[ ]` | `[ ]` *gegenstandslos* | `grep -rn "force_trigger" --include="*.py" --exclude-dir=.venv --exclude-dir=.git .` → **3 Treffer, alle in `phase2_persistence/`**: Schema-Default (`defaults.py:27`) + 2 Test-Beweise (`test_migrations.py:103`, `test_db.py:204`). Kein Code-Aufrufer, kein Wiring. CLAUDE.md Hard Rule 5 bleibt wörtlich stehen — Vorschrift für den Tag, an dem jemand einen Force-Trigger baut. |

**Verdienst:** ROADMAP 15b/15c/15d stimmen jetzt **mit dem Code überein** (Plan-Akzeptanzkriterium
AK3 erfüllt). Drei „gebaut"-Vermerke ehrlich — keine live-verify-Behauptungen, die Plan §9 #4 nicht
trägt (Compression-Latch). Eine „gegenstandslos"-Erklärung für 15b Zeile 3 + 15d vollständig —
15c Zeile 1 als „partial" markiert, weil 2/4 Sub-Signale gebaut und 2/4 gegenstandslos sind.

**Nicht angefasst (Phase-15-Scope-Grenze):**
- 15a (Council-Integration) — Nikinger-Entscheidung 2026-08-31, Runde 1 (Plan §10)
- 15e (Instinct-Promotion + Longterm VETO) — bleibt Block C (Plan §6)

---

## Step A-4 — root-CLAUDE.md Statuspflege (2026-08-31, MiniMax-M3 Exec-Session)

> **Plan-Anker:** [`docs/concepts/phase15_v4_plan.md`](../docs/concepts/phase15_v4_plan.md) §6 A-4 (S. 396-410).
> **Scope:** zwei Anker-Edits im root `CLAUDE.md`, jeder mit datiertem Vermerk.

### Anker 1 — `CLAUDE.md:93` (Status-Absatz voranstellen)

> **✅ 2026-08-31 — Phase 13 + Phase 14 ABGESCHLOSSEN (Sessions 18 + 23).** … **Phase 15
> (V4) eröffnet 2026-08-31** — Mission: „bevor der Bot mehr lernt, muss das, was er lernt,
> stimmen" …

Der existierende Phase-8-Block bleibt **unangetastet** (Auditability). Der neue Absatz steht
**davor** und fasst zusammen, was seitdem passiert ist.

### Anker 2 — `CLAUDE.md:148` (Phase-15-Row flippen)

| Spalte | Vorher | Nachher |
|---|---|---|
| Status | `Deferred, gegatet auf Phase 9+11+12+13+14 + reale Outcomes` | `🔄 **in Arbeit seit 2026-08-31** — execution-ready Plan (P1–P16, AK1–AK14). Phasenkopf mit Block A in Ausführung. Blöcke A/B/C/D mit Gate-Logik.` |

**Verdienst:** root-CLAUDE.md spiegelt den aktuellen Stand (Plan-Akzeptanzkriterium AK3 ist
mit A-3 erfüllt; die Status-Pflege ist die logische Folge für AK-Lesbarkeit). Die alte
„Deferred"-Formulierung hätte für die nächste Cold-Reader-Session fälschlich „Phase 15 ist noch
nicht angefangen" gesagt — das ist nach Commit `f98df68` + den Folge-Commits `a2d4a15` /
`d1dd26b` / `aad1d00` (Plan + Phasenkopf + Nikinger-Freigaben) nicht mehr wahr.

**Nicht angefasst:** Phasen 1–14 Rows der Status-Tabelle (alle aktuell), Phasen-8-Block (Auditability).

---

## Step A-5 — Doc-Rotation der zwei Übergrößen (2026-08-31, MiniMax-M3 Exec-Session, 2. Tag)

> **Plan-Anker:** [`docs/concepts/phase15_v4_plan.md`](../docs/concepts/phase15_v4_plan.md) §6 A-5 (S. 412-422) + §7 AK4 (S. 710).
> **Scope:** ROADMAP.md-Phasen 1–8 verbatim nach `ROADMAP_ARCHIVE.md` rotiert; INDEX.md-Größen-Angabe + neue Archiv-Zeile; Drift zu `phase7_reward/CLAUDE.md` datiert vermerkt.
> **Nikinger-Freigabe (2026-08-31, Frage-Slot vor Ausführung):** „Nur ROADMAP + Drift-Vermerk" — **kein** Eingriff in `phase7_reward/CLAUDE.md`.

### Drift-Finding (gemessen 2026-08-31) — `phase7_reward/CLAUDE.md` ist bereits rotiert

| Quelle | Heutiger Zustand |
|---|---|
| `phase7_reward/CLAUDE.md` Session-blocks | **genau 1** Block (Z. 358, Step 14 / Mini-Session 26) — Rotationsregel **bereits erfüllt** |
| `phase7_reward/SESSIONS_ARCHIVE.md` | **14** ältere Session-Blöcke (Steps 1–13c, newest-first, 70 KB) — **bereits vollständig** |
| `phase7_reward/CLAUDE.md` Größe | 49.855 B (48,7 KB) — kommt NICHT aus Session-Blöcken, sondern aus (a) Scope-Lock mit eingebetteten Hotfix-Notizen ~104 Z. + (b) „Verifizierte Contracts"-Tabelle gegen `49cda8a` gepinnt ~106 Z. + (c) Step-14-Block inkl. 2 Mini-Sessions ~208 Z. |
| Plan §6 A-5 Vermutung | „Rotationsregel anwenden: genau ein `## Session stopped`-Block bleibt" — **gegenstandslos**, der gewünschte Zustand ist schon da |
| Plan §7 AK4 Ziel | „ROADMAP.md und `phase7_reward/CLAUDE.md` unter 40 KB" — **für `phase7_reward/CLAUDE.md` nicht erreichbar ohne Auditability-Verlust** |

**Konsequenz:** die Plan-§6-A-5-Vermutung war eine Lese-Drift (vermutlich aus einer früheren
Session, in der die Datei noch nicht in der heutigen Rotationsform war). Heute (2026-08-31) ist
die Rotationsregel bereits erfüllt, und die verbleibenden 48,7 KB sind **auditability-pflichtig**
(Score-Inversion-Fix-Beweis in den Hotfix-Notizen, gepinnte Contract-Tabelle als historischer
Beleg gegen `49cda8a`). **Kein** Edit an `phase7_reward/CLAUDE.md` ohne explizite Nikinger-
Freigabe — Working-style-Regel: „Locked decisions stay locked; on new evidence surface as
finding, let the Nikinger decide — never deviate quietly."

### Maßnahme — nur ROADMAP.md rotiert

1. **`ROADMAP_ARCHIVE.md`** (NEU, 290 Z. / 18,4 KB / 18.842 B): Phasen 1–8 verbatim aus dem
   Pre-A-5-`ROADMAP.md` (Z. 27-292), Header-Card analog zu den `SESSIONS_ARCHIVE.md`-Dateien
   (`status: archive`, `detail: L3`, `up: ./ROADMAP.md`, expliziter „warum diese Datei
   existiert"-Absatz mit Pre-Rotation-Referenz).
2. **`ROADMAP.md`** (749 → 507 Z. / 54.147 → 39.109 B): Header-Card `purpose`/`read-when`/
   `down` aktualisiert (Archive-Link hinzu); Pre-A-5-Phasen-1-8-Block ersetzt durch eine
   kompakte Summary-Tabelle + Link + Verweis auf Auditability-Regel; Phase-9-bis-Phase-15 +
   Meta-Strang + Cross-Cutting **unangetastet** (verbatim).
3. **`docs/INDEX.md`** (Header `updated:` 2026-07-06 → 2026-08-31; Z. 27 stale „41 KB" →
   „38 KB" + neue ROADMAP_ARCHIVE-Zeile mit Größe + Beschreibung + `up:`-Link).
4. **`docs/concepts/phase15_v4_plan.md`**: §6 A-5 + §7 AK4 datierter Korrekturhinweis (warum
   die `phase7_reward/CLAUDE.md`-Zeile empirisch nicht zutrifft + warum AK4 für diese Datei
   reduziert wird auf „auditability-bewusst beibehalten").

### Verdienst + AK-Stand

| Akzeptanzkriterium | Status |
|---|---|
| **AK4 (reduziert)** | ✅ **ROADMAP.md** = 39.109 B (38,2 KB, unter 40 KB). `phase7_reward/CLAUDE.md` neu definiert als „auditability-bewusst beibehalten, kein AK4-Ziel" — Plan §7-AK4-Korrekturhinweis datiert 2026-08-31 |
| **AK14** | ✅ Neue `.md` (`ROADMAP_ARCHIVE.md`) hat ihre `docs/INDEX.md`-Zeile im selben Commit |

### Pre-Commit-Hook-Verify (`scripts/check_doc_rotation.py`)

Hook läuft sauber durch (PHASE_DIRS endet bei `phase14_discovery`, deckt weder `ROADMAP.md`-
noch `ROADMAP_ARCHIVE.md`-Pfade ab). Die Phase-15-spezifische Hook-Härtung (PHASE_DIRS auf
`phase15_v4` + ggf. zusätzliche Root-Level-Datei-Checks für `ROADMAP.md`/`ROADMAP_ARCHIVE.md`)
bleibt eine separate Mini-Plan-Aufgabe (siehe Plan §9 + OFFENE ITEMS aus der Vorseesession),
nicht Phase-15-A-5-Scope.

### Σ-Sweep nach A-5

Doc-only-Edits, **kein** Code-Touch, **kein** Test-Touch. Σ-Baseline 1703 grün bleibt erhalten
(siehe nächster Session-Block).

---

## Step A-6 — `docs/INDEX.md` Doppel-Header + stale „P15-Plan-Session offen"-Zeilen (2026-08-31, MiniMax-M3 Exec-Session, 2. Tag)

> **Plan-Anker:** [`docs/concepts/phase15_v4_plan.md`](../docs/concepts/phase15_v4_plan.md) §6 A-6 (S. 424-439).
> **Scope:** 1 INDEX.md-Edit + 5 stale P15-Vermerke in Phasen 7/13/14 phasenköpfen (Plan listete 3; **2 weitere** im selben Geist in den aktiven Session-Blöcken mitgeräumt — Begründung unten).
> **Cross-Phase-Freigabe (Nikinger 2026-08-31, Plan §4):** P2 / P4 / P5 / P6 / P7 / P13 / P14 — **P8 nicht**. Alle 5 Edits liegen in freigegebenen Phasen.

### INDEX.md (1 Edit)

| Datei | Vorher (Z. 37 + Z. 39) | Nachher (Z. 37) |
|---|---|---|
| `docs/INDEX.md` | **zwei** `## Closed phases`-Überschriften (Z. 37 erweitert mit Phase-12/13/14-Detail, Z. 39 alt mit nur Phase-10) | **eine** `## Closed phases`-Überschrift (Z. 37 mit Phase-10/12/13/14-Detail erhalten) |

Die zweite Überschrift (Z. 39, „10 — V3 ✅ abgeschlossen 2026-08-25; Council-Paper-Call in mind P15") war eine Überrest aus der Phase-10-Closeout-Periode; die erweiterte Überschrift (Z. 37) hatte sie bereits überholt. **Drift zwischen den beiden Überschriften** war eine Folge der Phase-12/13/14-Closeouts, die Z. 37 aktualisierten, Z. 39 aber nicht anfassen.

### Stale „P15-Plan-Session"-Vermerke (5 Edits in Phasen 7/13/14 phasenköpfen)

| Datei | Z. | Vorher (verbatim) | Nachher |
|---|---|---|---|
| `phase7_reward/CLAUDE.md` | 457 | `P15-Plan-Session (V4) — Material jetzt vollständig (P14-F D5 + P13-Findings + ...)` | ✅ **abgeschlossen 2026-08-31**, Plan-Commit `f98df68` + Nikinger-Freigabe `aad1d00`; Phase 15 in execution |
| `phase13_live_data/CLAUDE.md` | 237-239 | `1. Phase-15-Plan-Session (großer Block, ~2-3h): Material jetzt vollständig. Vier P15-V4-Kandidaten dokumentiert: ...` | ✅ **abgeschlossen 2026-08-31**; Block A in Ausführung |
| `phase14_discovery/CLAUDE.md` | 271-273 | `Phase-15-Plan-Session (V4) — Material jetzt vollständig (P14-F D5 ✅, P13-Findings ...)` | ✅ **abgeschlossen 2026-08-31**; Block A A-1..A-5 ✅ |
| `phase14_discovery/CLAUDE.md` | 289-292 | `1. Phase-15-Plan-Session (großer Block, ~2-3h): Material jetzt vollständig (7+ V4-Kandidaten dokumentiert). ...` | ✅ **abgeschlossen 2026-08-31**; Block A in execution |
| `phase7_reward/CLAUDE.md` | 469 | `3. P15-Plan-Session (großer Block, ~2-3h): Material jetzt vollständig; P12-Reconcile-Backoff ist V4-Material ...` | ✅ **abgeschlossen 2026-08-31**; P12-Reconcile-Backoff als V4-Material weiterhin offen für Phase-15 Block B/D |

**Scope-Anmerkung:** Plan §6 A-6 listete **3** stale Vermerke (Z. 457, Z. 238, D5-H.-B-Vermerk
in phase14). Während der Ausführung entdeckt: **2 weitere** stale Vermerke (Z. 289 in
phase14, Z. 469 in phase7) tragen das gleiche Pattern (NEXT-List-Item „Material jetzt
vollständig") in den **aktiven** Session-Blöcken dieser Phasenköpfe — kein Verstoß gegen
Plan-Scope (gleicher Geist, gleiche Anti-Pattern-Klasse, alle Cross-Phase-freigegeben,
alle in aktiven Session-Blöcken = updateable per Rotation-Regel). Mit aufgeräumt.

**Nicht angefasst (per 📕-Konvention, nicht updateable):**
- `phase14_discovery/PHASE14_CLOSEOUT_HANDOVER.md` Z. 272: D5-H.-B-Vermerk „offen für P15-V4-Plan-Session" — das ist im 📕-Handover-Snapshot, nicht updateable; Plan A-6-Hinweis „wird von Step D1 ohnehin angefasst, dort mitnehmen" gilt weiterhin.
- SESSIONS_ARCHIVE.md-Einträge in phase7_reward (Steps 1-13c), phase13_live_data (Sessions 1-17), phase14_discovery (Sessions 1-22) — alle im Archiv, alle verbatim.

### Verdienst + AK-Stand

**Block A endgültig abgeschlossen (A-1..A-6 alle ✅):**
- **AK1** ✅ Step-0-Ritual (A-1)
- **AK2** ✅ Σ-Baseline 1703 (A-2)
- **AK3** ✅ ROADMAP 15b/15c/15d stimmen (A-3)
- **AK4 (reduziert)** ✅ ROADMAP.md < 40 KB (A-5); phase7_reward/CLAUDE.md = auditability-bewusst beibehalten
- **AK14** ✅ ROADMAP_ARCHIVE.md-Zeile im selben Commit (A-5)
- **(implizit AK)** alle 3 stale P15-Vermerke (Plan A-6) **+ 2 zusätzliche** stale P15-NEXT-Items in aktiven Session-Blöcken aktualisiert — kein Cold-Reader wird mehr von „Material jetzt vollständig" in die Irre geführt

### Σ-Sweep nach A-6

Doc-only-Edits, **kein** Code-Touch, **kein** Test-Touch. Σ-Baseline 1703 grün bleibt erhalten
(siehe nächster Session-Block).

---

> **Plan-Anker:** [`docs/concepts/phase15_v4_plan.md`](../docs/concepts/phase15_v4_plan.md) §6 A-5 (S. 412-422) + §7 AK4 (S. 710).
> **Scope:** ROADMAP.md-Phasen 1–8 verbatim nach `ROADMAP_ARCHIVE.md` rotiert; INDEX.md-Größen-Angabe + neue Archiv-Zeile; Drift zu `phase7_reward/CLAUDE.md` datiert vermerkt.
> **Nikinger-Freigabe (2026-08-31, Frage-Slot vor Ausführung):** „Nur ROADMAP + Drift-Vermerk" — **kein** Eingriff in `phase7_reward/CLAUDE.md`.

### Drift-Finding (gemessen 2026-08-31) — `phase7_reward/CLAUDE.md` ist bereits rotiert

| Quelle | Heutiger Zustand |
|---|---|
| `phase7_reward/CLAUDE.md` Session-blocks | **genau 1** Block (Z. 358, Step 14 / Mini-Session 26) — Rotationsregel **bereits erfüllt** |
| `phase7_reward/SESSIONS_ARCHIVE.md` | **14** ältere Session-Blöcke (Steps 1–13c, newest-first, 70 KB) — **bereits vollständig** |
| `phase7_reward/CLAUDE.md` Größe | 49.855 B (48,7 KB) — kommt NICHT aus Session-Blöcken, sondern aus (a) Scope-Lock mit eingebetteten Hotfix-Notizen ~104 Z. + (b) „Verifizierte Contracts"-Tabelle gegen `49cda8a` gepinnt ~106 Z. + (c) Step-14-Block inkl. 2 Mini-Sessions ~208 Z. |
| Plan §6 A-5 Vermutung | „Rotationsregel anwenden: genau ein `## Session stopped`-Block bleibt" — **gegenstandslos**, der gewünschte Zustand ist schon da |
| Plan §7 AK4 Ziel | „ROADMAP.md und `phase7_reward/CLAUDE.md` unter 40 KB" — **für `phase7_reward/CLAUDE.md` nicht erreichbar ohne Auditability-Verlust** |

**Konsequenz:** die Plan-§6-A-5-Vermutung war eine Lese-Drift (vermutlich aus einer früheren
Session, in der die Datei noch nicht in der heutigen Rotationsform war). Heute (2026-08-31) ist
die Rotationsregel bereits erfüllt, und die verbleibenden 48,7 KB sind **auditability-pflichtig**
(Score-Inversion-Fix-Beweis in den Hotfix-Notizen, gepinnte Contract-Tabelle als historischer
Beleg gegen `49cda8a`). **Kein** Edit an `phase7_reward/CLAUDE.md` ohne explizite Nikinger-
Freigabe — Working-style-Regel: „Locked decisions stay locked; on new evidence surface as
finding, let the Nikinger decide — never deviate quietly."

### Maßnahme — nur ROADMAP.md rotiert

1. **`ROADMAP_ARCHIVE.md`** (NEU, 290 Z. / 18,4 KB / 18.842 B): Phasen 1–8 verbatim aus dem
   Pre-A-5-`ROADMAP.md` (Z. 27-292), Header-Card analog zu den `SESSIONS_ARCHIVE.md`-Dateien
   (`status: archive`, `detail: L3`, `up: ./ROADMAP.md`, expliziter „warum diese Datei
   existiert"-Absatz mit Pre-Rotation-Referenz).
2. **`ROADMAP.md`** (749 → 507 Z. / 54.147 → 39.109 B): Header-Card `purpose`/`read-when`/
   `down` aktualisiert (Archive-Link hinzu); Pre-A-5-Phasen-1-8-Block ersetzt durch eine
   kompakte Summary-Tabelle + Link + Verweis auf Auditability-Regel; Phase-9-bis-Phase-15 +
   Meta-Strang + Cross-Cutting **unangetastet** (verbatim).
3. **`docs/INDEX.md`** (Header `updated:` 2026-07-06 → 2026-08-31; Z. 27 stale „41 KB" →
   „38 KB" + neue ROADMAP_ARCHIVE-Zeile mit Größe + Beschreibung + `up:`-Link).
4. **`docs/concepts/phase15_v4_plan.md`**: §6 A-5 + §7 AK4 datierter Korrekturhinweis (warum
   die `phase7_reward/CLAUDE.md`-Zeile empirisch nicht zutrifft + warum AK4 für diese Datei
   reduziert wird auf „auditability-bewusst beibehalten").

### Verdienst + AK-Stand

| Akzeptanzkriterium | Status |
|---|---|
| **AK4 (reduziert)** | ✅ **ROADMAP.md** = 39.109 B (38,2 KB, unter 40 KB). `phase7_reward/CLAUDE.md` neu definiert als „auditability-bewusst beibehalten, kein AK4-Ziel" — Plan §7-AK4-Korrekturhinweis datiert 2026-08-31 |
| **AK14** | ✅ Neue `.md` (`ROADMAP_ARCHIVE.md`) hat ihre `docs/INDEX.md`-Zeile im selben Commit |

### Pre-Commit-Hook-Verify (`scripts/check_doc_rotation.py`)

Hook läuft sauber durch (PHASE_DIRS endet bei `phase14_discovery`, deckt weder `ROADMAP.md`-
noch `ROADMAP_ARCHIVE.md`-Pfade ab). Die Phase-15-spezifische Hook-Härtung (PHASE_DIRS auf
`phase15_v4` + ggf. zusätzliche Root-Level-Datei-Checks für `ROADMAP.md`/`ROADMAP_ARCHIVE.md`)
bleibt eine separate Mini-Plan-Aufgabe (siehe Plan §9 + OFFENE ITEMS aus der Vorseesession),
nicht Phase-15-A-5-Scope.

### Σ-Sweep nach A-5

Doc-only-Edits, **kein** Code-Touch, **kein** Test-Touch. Σ-Baseline 1703 grün bleibt erhalten
(siehe nächster Session-Block).

---

## Session stopped — 2026-08-31 (MiniMax-M3-Exec-Session #3, Block A Step A-6 + Block A endgültig abgeschlossen)

> **Auftrag:** Nikinger-Chat 2026-08-31 nach A-5-Push-Phase: „Weiter mit A6 schlage
> ich vor. Du darfst pushen." — Cross-Session-Drift vor Ausführung entdeckt
> (`## Closed phases`-Doppel-Header in `docs/INDEX.md`) und sauber gehandhabt;
> **2 zusätzliche** stale P15-NEXT-Items in den aktiven Session-Blöcken von
> phase7_reward/CLAUDE.md (Z. 469) und phase14_discovery/CLAUDE.md (Z. 289) im
> selben Geist mit aufgeräumt (siehe Findings).
>
> Ausführungs-Scope: **1 Commit (Doc-only, atomar) + Push** — exakt der Plan-§6-
> Schritt A-6 + die 2 zusätzlichen stale P15-NEXT-Items in aktiven Session-Blöcken
> (gleicher Geist, gleiche Anti-Pattern-Klasse, alle Cross-Phase-freigegeben).
> Push-Freigabe explizit von Nikinger erteilt (Session #2-Push + Session #3-A-6-Push
> werden in **einem** Push-Commit zusammengefasst).

### Completed

**0. Cross-Session-Drift-Vorab-Check (Session-Start):**
- `docs/INDEX.md` hat **zwei** `## Closed phases`-Überschriften (Z. 37 + Z. 39) —
  Doppel-Header aus Phase-12/13/14-Closeout-Periode. Z. 39 (Phase-10-only) ist
  reduntant, Z. 37 (Phase-10/12/13/14) ist die jüngere + umfassendere.
- 3 stale „P15-Plan-Session offen"-Vermerke (Plan A-6-Liste) verifiziert +
  **2 weitere** in den aktiven Session-Blöcken gefunden (gleiche Anti-Pattern-
  Klasse, gleicher Geist — alle in den Session-Blöcken der Phasen 7/13/14, die
  per Rotation-Regel updateable sind).

**1. A-6 — 6 Doc-Edits (1 INDEX.md + 5 stale P15-Vermerke in Phasen 7/13/14):**
- `docs/INDEX.md` Z. 39 redundante `## Closed phases`-Überschrift entfernt;
  Z. 37 (umfassendere) bleibt — eine Überschrift statt zwei.
- `phase7_reward/CLAUDE.md` Z. 457 (Plan-A-6-listed): `P15-Plan-Session (V4) —
  Material jetzt vollständig` → ✅ **abgeschlossen 2026-08-31**, Plan-Commit
  `f98df68` + Nikinger-Freigabe `aad1d00`; Phase 15 in execution.
- `phase7_reward/CLAUDE.md` Z. 469 (zusätzlich gefunden): NEXT-List-Item 3
  `P15-Plan-Session (großer Block, ~2-3h)` → ✅ abgeschlossen 2026-08-31
  (P12-Reconcile-Backoff als V4-Material weiterhin offen für Phase-15 Block B/D).
- `phase13_live_data/CLAUDE.md` Z. 237-239 (Plan-A-6-listed): NEXT-List-Item 1
  `Phase-15-Plan-Session (großer Block, ~2-3h)` → ✅ abgeschlossen 2026-08-31.
- `phase14_discovery/CLAUDE.md` Z. 271-273 (Plan-A-6-listed): `Phase-15-Plan-
  Session (V4) — Material jetzt vollständig` → ✅ abgeschlossen 2026-08-31.
- `phase14_discovery/CLAUDE.md` Z. 289-292 (zusätzlich gefunden): NEXT-List-
  Item 1 `Phase-15-Plan-Session (großer Block, ~2-3h)` → ✅ abgeschlossen
  2026-08-31.
- **Cross-Phase (Plan §4 freigegeben):** P7 + P13 + P14 berührt, **P8 nicht**.
- **Nicht angefasst (per 📕-Konvention):** `phase14_discovery/PHASE14_CLOSEOUT_HANDOVER.md`
  Z. 272 D5-H.-B-Vermerk (Plan-A-6-Hinweis „wird von Step D1 ohnehin angefasst,
  dort mitnehmen" — gilt weiterhin); alle SESSIONS_ARCHIVE.md-Einträge
  (verbatim).

**2. Session-Rotation:**
- `phase15_v4/CLAUDE.md`: alter MiniMax-M3-Exec-Session #2-Block (A-5) verbatim
  nach `SESSIONS_ARCHIVE.md` rotiert; neuer #3-Block (A-6 + Block A endgültig
  abgeschlossen) in Phasenkopf. Phasenkopf trägt jetzt genau einen Session-
  Block. `SESSIONS_ARCHIVE.md` hat jetzt 3 Session-Blöcke, newest-first
  (MiniMax-M3 #3 wird gleich nach dem Commit hinzugefügt).
- Step A-6-Sektion im Phasenkopf ergänzt (`phase15_v4/CLAUDE.md:295-403`).

### Σ-Sweep Stand 2026-08-31 ~17:00 UTC (selbst nachgemessen, diese Session)

Doc-only-Edits, **kein** Code-Touch, **kein** Test-Touch. Σ-Baseline 1703 grün
bleibt erhalten:

| Phase | Tests grün | Δ |
|---|---:|---|
| phase1_broker_wrapper | 95 | — |
| phase2_persistence | 77 | — |
| phase3_external_data | 104 | — |
| phase4_research | 155 | — |
| phase5_execution | 173 | — |
| phase6_debate | 76 | — |
| phase7_reward | 142 | — |
| phase8_scheduler | 248 | — |
| phase9_universe | 87 | — |
| phase10_v3 | 165 | — |
| phase12_data_foundation | 145 | — |
| phase13_live_data | 74 | — |
| phase14_discovery | 61 | — |
| root `tests/` | 101 | — |
| **Σ total** | **1703** | = A-2-Baseline exakt, 2× reproduziert (A-5 + A-6) ✅ |

### Commits (lokal, in dieser Session erzeugt; 1 Commit für A-6, **Push erteilt**)

| Commit | Scope | Diff |
|---|---|---|
| (dieser) | `phase15: docs -- A-6 stale P15-Vermerke (3 Plan-listed + 2 zusätzliche in aktiven Session-Blöcken) + INDEX.md Doppel-Header zusammengeführt` | `docs/INDEX.md` −1 Z., `phase7_reward/CLAUDE.md` +6 −2, `phase13_live_data/CLAUDE.md` +3 −3, `phase14_discovery/CLAUDE.md` +8 −4, `phase15_v4/CLAUDE.md` +102 −1 (A-6-Sektion + Session-Rotation) |
| (vorher, bereits lokal) | A-5 Commit `9f8101b` | `ROADMAP.md` +242 -242, ROADMAP_ARCHIVE.md NEU, INDEX.md +5 -3, plan +13 -2, CLAUDE.md +141 -1 |
| (Push-Bundle) | **2 Commits ahead of `origin/main = ef320e6`** | A-5 (`9f8101b`) + dieser (A-6) — **Push erteilt von Nikinger 2026-08-31 nach A-6-Commit** |

### Findings

🟢 **A-6 Plan-konform abgeschlossen (+ 2 zusätzliche stale P15-NEXT-Items im selben
Geist).** Block A ist damit **endgültig** abgeschlossen (A-1..A-6 alle ✅).

- **AK1** ✅ Step-0-Ritual (A-1)
- **AK2** ✅ Σ-Baseline 1703 (A-2)
- **AK3** ✅ ROADMAP 15b/15c/15d stimmen (A-3)
- **AK4 (reduziert)** ✅ ROADMAP.md < 40 KB (A-5); phase7_reward/CLAUDE.md =
  auditability-bewusst beibehalten
- **AK14** ✅ ROADMAP_ARCHIVE.md-Zeile im selben Commit (A-5)
- **Σ-Baseline 1703 grün** unverändert (2× reproduziert)

🟢 **Drift-Handling ehrlich gehalten:** INDEX.md-Doppel-Header war eine Folge
gestaffelter Phase-12/13/14-Closeouts, die Z. 37 aktualisierten, Z. 39 aber nicht
anfassten. **Drift gefunden → behoben → datiert vermerkt** (kein stillschweigendes
„close enough").

🟢 **2 zusätzliche stale P15-NEXT-Items im Geist von A-6 mit aufgeräumt:**
Plan A-6 listete 3 stale Vermerke; während der Ausführung in den aktiven Session-
Blöcken der Phasenköpfe P7 + P14 weitere 2 mit identischem Anti-Pattern gefunden
(„Material jetzt vollständig" — falsch seit Plan-Commit). Beide updateable per
Rotation-Regel (in aktiven Session-Blöcken), beide Cross-Phase-freigegeben
(Plan §4: P7 + P14 sind freigegeben). **A-6-Scope spirit-conform**, nicht „stiller
Scope-Creep": Plan §6 A-6 sagt „3 stale Zeilen" — die 2 zusätzlichen sind
dasselbe Pattern in denselben Phasenköpfen, in den updatebaren aktiven Session-
Blöcken. Vermerk im Phasenkopf (Step A-6 „Scope-Anmerkung") für Auditability.

🟢 **Pre-Commit-Hook (`scripts/check_doc_rotation.py`) verifiziert** (Phase-Heads
8/8 OK; `phase15_v4` weiterhin nicht in PHASE_DIRS-abgedeckt — Mini-Plan-
Aufgabe für später, **kein Blocker** für A-6).

🟡 **D5-H.-B-Vermerk im PHASE14_CLOSEOUT_HANDOVER.md Z. 272 bleibt stale** —
per Plan A-6-Hinweis „wird von Step D1 ohnehin angefasst, dort mitnehmen",
📕-Konvention (Handover ist Snapshot, nicht updateable). Phase-15-Block-D-Step-D1
muss diesen Vermerk dann **mit** schließen.

### Open questions / blockers

- **Gate P7 unverändert zu** (Block B): wartet auf einen OPEN-Trade mit IG-Lag +
  24 h Beobachtung (Phase-12-Reconcile-Timing Live-Verify, A6). Heute 0 OPEN-Trades
  gemessen, erwarteter Live-Effekt: ≤ 5 CRITICALs in 24 h statt 6+ in 52 min;
  > 24 h ohne Auflösung = WARNING statt CRITICAL.
- **Block A endgültig abgeschlossen.** Blöcke B / C / D warten auf Nikinger-Wahl
  bzw. auf P7-Gate (Block B).
- **Phase-15-spezifische Hook-Härtung** (Mini-Plan-Aufgabe, nicht Phase-15-Scope):
  P14-F-Regex `(?:Mini-)?Session\s+(\d+)` matcht den Plan-Session-Heading nicht;
  PHASE_DIRS endet bei `phase14_discovery` und deckt weder `phase15_v4` noch
  `ROADMAP.md`/`ROADMAP_ARCHIVE.md` ab. Aktuell kein Blocker (manuell sauber
  rotiert), aber für saubere Folge-Sessions sinnvoll.
- **D5-H.-B-Vermerk im PHASE14_CLOSEOUT_HANDOVER.md** bleibt stale bis Block-D-
  Step-D1 (siehe Findings 🟡 oben).

### NEXT (für die nächste Session / morgen)

**Nikinger-Wahl zum nächsten Schritt erwartet** (Stand ~17:15 UTC = ~19:15 CEST).

**Konkrete Empfehlung (sortiert nach Aufwand × Impact):**

1. **Phase-15-spezifische Hook-Härtung als Mini-Plan-Aufgabe** (~30 Min Plan +
   ~1 h Code+Tests, Cross-Phase: P14-F-Erweiterung + PHASE_DIRS-Update): die
   Doc-Rotation-Hook-Lücke für `phase15_v4` + die Root-Level-Dateien
   (`ROADMAP.md`, `ROADMAP_ARCHIVE.md`) schließen. Vorbedingung für saubere
   Folge-Sessions in Phase 15 (sonst wieder manuell rotieren).
2. **Block D (Erbstücke) D1-D3** — kein Gate, jetzt möglich. D1: D5-H.-B-Vermerk
   in `phase14_discovery/PHASE14_CLOSEOUT_HANDOVER.md` (Cross-Phase P14, freigegeben
   — schließt den seit A-6 dokumentierten stale-Vermerk). D2: `phase13_14_15.svg`
   (~1 h). D3: Pfad A Operator-Tool in Phase 13 (Cross-Phase P13, freigegeben).
3. **Block B** — bleibt hinter Gate P7. **Nicht** jetzt — wartet auf A6-Abschluss-
   meldung des Phase-12-Reconcile-Timing-Fix-Live-Verify (nächster OPEN-Trade mit
   IG-Lag + 24-h-Beobachtung).

**Push-Status:** **2 Commits ahead of `origin/main = ef320e6`** (A-5 + A-6) —
**Push erteilt von Nikinger 2026-08-31** nach A-6-Commit. Push-Resultat siehe
unten (im selben A-6-Commit-Bundle).

> **Ältere Session-Blöcke** (verbatim ausgelagert, newest-first):
> [SESSIONS_ARCHIVE.md](./SESSIONS_ARCHIVE.md) — Rotation per Doc-Layers-Konvention
> ([docs/DOC_LAYERS_CONVENTION.md](../docs/DOC_LAYERS_CONVENTION.md)). Der vorherige
> MiniMax-M3-Exec-Session #2-Block (A-5, 1 Commit, lokal) wurde in dieser Session
> **nach** SESSIONS_ARCHIVE.md rotiert.

> **Hinweis (History):** SESSIONS_ARCHIVE.md trägt jetzt 3 Session-Blöcke, alle
> 2026-08-31, newest-first: #3 (dieser, A-6, gleich hinzugefügt) → #2 (A-5) →
> #1 (A-1..A-4) → Plan-Session (Opus 5). Phasenkopf trägt exakt einen Block
> (dieser #3-Block), Rotation-Konvention gewahrt.
