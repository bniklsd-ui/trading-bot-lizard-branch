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
updated: 2026-09-01 (A-1..A-7 protokolliert + P15-F Doc-Rotation-Hook-Härtung + D1 D5-H.-B geschlossen, MiniMax-M3)
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

## Step A-7 — Phase-15-spezifische Doc-Rotation-Hook-Härtung (P15-F, 2026-08-31, MiniMax-M3 Exec-Session, 3. Tag)

> **Plan-Anker:** [`./PHASE15_HOOK_HARDENING_PLAN.md`](./PHASE15_HOOK_HARDENING_PLAN.md) (Mini-Plan P15-F, analog P14-F).
> **Scope:** `PHASE_DIRS` um `phase15_v4` erweitert + permissive MiniMax-M3-Exec-Session-Regex + 4 neue Tests A3–A6 + INDEX.md + Phasenkopf-Header-Card-Update. **Push erteilt** (Nikinger 2026-08-31).

### Befund vor Ausführung (gemessen 2026-08-31)

| Check | Ergebnis |
|---|---|
| `python3 scripts/check_doc_rotation.py --strict` (Repo-weit) | 14 Phasen OK, **`phase15_v4` nicht abgedeckt** |
| `python3 scripts/check_doc_rotation.py --strict --phase phase15_v4` | `[OK] phase15_v4: 1 session block` — Step-1 grün, **Step-2 silent-skipped** weil `_max_session_num` für „MiniMax-M3-Exec-Session #N" `None` returnt |
| Verifizierter Regex-Match-Test (manuell, Python) | Alte Regex `(?:Mini-)?Session\s+(\d+)` matched **nicht** „MiniMax-M3-Exec-Session #3" / „Exec-Session #5" |
| `PHASE_DIRS` Endstand | `phase14_discovery` (letzter Eintrag, kein `phase15_v4`) |

### Maßnahme — 3 Edits + 1 neue Datei

1. **`scripts/check_doc_rotation.py`** (2 Edits):
   - `PHASE_DIRS` um `"phase15_v4"` ergänzt (am Ende, nach `phase14_discovery`).
   - `_SESSION_NUM_RE` permissiver: `(?:Mini-|MiniMax-\w+-Exec-|Exec-)?Session\s+#?(\d+)`. Matcht weiterhin P14-F-Stand („Session N", „Mini-Session N") plus Phase-15-Vokabulare („Exec-Session #N", „MiniMax-M3-Exec-Session #N"). `\w+` deckt zukünftige Modell-Varianten (MiniMax-4, MiniMax-Opus) ab.

2. **`tests/test_check_doc_rotation.py`** (4 neue Tests am Ende, Mini-Plan §5 A3–A6):
   - `test_archive_sequence_handles_exec_session_with_hash` — A3: head=#3, archive=#2+Plan-Session (Opus 5 wird ignoriert, kein `\d+` nach „Plan-Session") → OK
   - `test_archive_sequence_drift_when_phase15_skips_a_session` — A4: head=#3, archive=#1 (überspringt #2) → ❌ DRIFT, Diagnostik „expected 2" + „Session 1"
   - `test_archive_sequence_ignores_plan_session_without_number` — A5: archive enthält „Plan-Session, Opus 5" → wird **nicht** als Session-Nummer extrahiert, archive-max bleibt korrekt
   - `test_strict_check_passes_for_phase15_v4_against_real_repo` — A6: Subprozess-Aufruf `--strict --phase phase15_v4` exit 0 gegen die echte Repo-Struktur

3. **`docs/INDEX.md`** (1 neue Zeile analog P14-F):
   - `phase15_v4/PHASE15_HOOK_HARDENING_PLAN.md` mit Mini-Plan-Beschreibung + Cross-Phase-Freigabe-Vermerk.

4. **`phase15_v4/CLAUDE.md`** (Header-Card-Update):
   - `down:`-Block um `./PHASE15_HOOK_HARDENING_PLAN.md` ergänzt.
   - `updated:`-Feld auf `2026-08-31 (A-1..A-6 protokolliert + P15-F Doc-Rotation-Hook-Härtung, MiniMax-M3)`.

5. **`phase15_v4/PHASE15_HOOK_HARDENING_PLAN.md`** (NEU, 322 Zeilen): Mini-Plan analog P14-F mit §0 BLUF, §1 Rahmen, §2 D1–D3 Locks, §3 verifizierte Befunde, §4 drei Schritte, §5 Akzeptanz A1–A6, §6 Out-of-Scope, §7 Fehlgriffe, §8 Drift-Liste, §9 Cross-Referenz.

### Cross-Phase-Freigabe

P14-F-Stand reicht — keine neue Cross-Phase-Freigabe nötig:
- `scripts/check_doc_rotation.py` und `tests/test_check_doc_rotation.py` sind Phase-14-eigener Hygiene-Code (seit Session 16 / P14-F); Erweiterung ist **kein** Cross-Phase-Touch.
- `scripts/install_hooks.sh` ruft bereits `--strict --quiet` (P14-F §4 Schritt 3); Härtung greift automatisch nach Commit, kein Installer-Edit.
- `scripts/dev_install.sh` ruft `install_hooks.sh` bereits (Z. 85, P14-F-Anker); keine Anbindung nötig.

**Nicht angefasst:** `phase15_v4/CLAUDE.md` Heading-Form („MiniMax-M3-Exec-Session #N") bleibt unverändert — die aktuelle Form ist lesbar + auditability-pflichtig (Modell-Name), das Tool ist permissiv genug (D2-Regex), **nicht** die Doku.

### Verdienst + Akzeptanz

| Akzeptanz | Status |
|---|---|
| **A1** (Regex-Stand P14-F bleibt) | ✅ — `test_archive_sequence_handles_mini_session_naming` + `test_archive_sequence_ok_for_continuous_block` unverändert grün |
| **A2** (Regex-Stand P14-F bleibt) | ✅ — `test_archive_sequence_drift_when_archive_skips_a_session` unverändert grün |
| **A3** (Phase-15-Form `Exec-Session #N`) | ✅ — `test_archive_sequence_handles_exec_session_with_hash` |
| **A4** (Phase-15-Sequenz-Lücke #1↔#3) | ✅ — `test_archive_sequence_drift_when_phase15_skips_a_session` |
| **A5** (Plan-Session-Block ignoriert) | ✅ — `test_archive_sequence_ignores_plan_session_without_number` |
| **A6** (echte Phase-15-Struktur Step-2-konform) | ✅ — `test_strict_check_passes_for_phase15_v4_against_real_repo` |

**Σ-Sweep:** `pytest tests/ -q` → **1707 grün** (101 root + 4 P15-F-Tests = +4 vs. A-6-Baseline 1703). Keine Test-Regression in den 13 Phasen-Suites.

### Pre-Commit-Hook-Verifikation (`scripts/check_doc_rotation.py --strict`)

```
[OK]   phase1_broker_wrapper: 1 session block
[OK]   phase2_persistence: no session history
... (12 weitere) ...
[OK]   phase14_discovery: 1 session block
[OK]   phase15_v4: 1 session block            ← NEU seit P15-F
All phase heads OK.
```

**15 Phasen OK** (war 14). Phase 15 ist jetzt mit echter Step-2-Prüfung (`head=3`, `archive-newest=2`, `expected=2` → ✅ konform).

---

## Step D1 — D5-H.-B geschlossen (2026-09-01, MiniMax-M3 Exec-Session, Block-D-Start)

> **Plan-Anker:** [`../docs/concepts/phase15_v4_plan.md`](../docs/concepts/phase15_v4_plan.md) §6 D1 (S. 641-652).
> **Scope:** Datierter Absatz in `phase14_discovery/CLAUDE.md` (Cross-Phase P14, freigegeben §4). **Kein** Code, **keine** Migration, **kein** Phase-14-Code-Touch.
> **Nikinger-Freigabe (2026-09-01, Block-D-Auftrag):** „Ich schlage vor, mit Block D weiter zu machen. Laut Plan hat dieser keine Blocker. Bitte arbeite atomar." — Reihenfolge: D1 → D2 → D3, jeder Step ein eigener atomischer Commit.

### Was

Cross-Phase-Edit in [`phase14_discovery/CLAUDE.md`](../phase14_discovery/CLAUDE.md): neuer
Abschnitt **„Phase 15 — Block D Step D1 — D5-H.-B geschlossen (2026-09-01, MiniMax-M3-
Exec-Session #5)"** zwischen Session-23-Block und dem `SESSIONS_ARCHIVE.md`-Footer.
Inhalt:

- D5-H.-B geschlossen: `instrument_source_availability` bleibt **Verfügbarkeits-Modell**;
  `last_verified_utc` markiert die letzte **Discovery-Ableitung** für das Tripel
  (Epic, Quelle, Auflösung) — **nicht** „Quelle hat gerade geliefert". Unter Pfad C
  (Default AUS, Phase-13-L18 + Phase-14-D19, Mini-Session 24) heißt `status='ok'`
  „GapRescue-Pfad (S4) verfügbar".
- B3-Beleg aus Phase-13-Beweiswoche [`../phase13_live_data/PHASE13_BEWEISWOCHE_FINDINGS_2026-08-31.md`](../phase13_live_data/PHASE13_BEWEISWOCHE_FINDINGS_2026-08-31.md)
  unverändert seit 2026-08-31 — Verweis geht in den Phasenkopf, **nicht** in den
  📕-Findings-Snapshot (per Plan §6 D1).

### 📕-Konvention (eingehalten)

| Datei | Status | Begründung |
|---|---|---|
| `phase14_discovery/PHASE14_CLOSEOUT_HANDOVER.md` §7 Z. 272 | **nicht** angefasst | L3-Snapshot, Plan §6 D1 verbietet Edit; der dortige Eintrag *„offen für P15-V4-Plan-Session"* ist die korrekte historische Aussage |
| `phase13_live_data/PHASE13_BEWEISWOCHE_FINDINGS_2026-08-31.md` | **nicht** angefasst | L3-Findings-Snapshot; Verweis geht in den Phasenkopf |
| `phase14_discovery/source_registry/`, `data_foundation/`, `live_data/`, `phase9_universe/universe/`, `phase8_scheduler/webui/` | **nicht** angefasst | kein Step braucht einen Code-Touch |

### Verdienst + Akzeptanz

| Akzeptanzkriterium (Plan §7) | Status |
|---|---|
| **AK10** | ✅ Datierter Absatz in `phase14_discovery/CLAUDE.md` vorhanden; Plan §6 D1 formalisiert; 📕-Konvention eingehalten |

### Σ-Sweep

Doc-only, **kein** Code-Touch, **kein** Test-Touch. Σ-Baseline **1707 grün**
(Phase-15-A-7-Stand 2026-08-31, MiniMax-M3-Exec-Session #4) bleibt erhalten.

### Doc-Rotation-Hook-Verify

```
$ python3 scripts/check_doc_rotation.py --strict --quiet
exit=0
$ python3 scripts/check_doc_rotation.py --strict --phase phase14_discovery
[OK]   phase14_discovery: 1 session block
All phase heads OK.
```

Der Phase-14-Phasenkopf trägt weiterhin **genau einen** `## Session stopped`-Block
(Session 23). Der neue Abschnitt „Phase 15 — Block D Step D1" ist **kein** Session-Block
(er hat **kein** „Session stopped" im Titel) und triggert damit **keine** Rotation.

### NEXT (für die Folge-Session)

- **Step D2** (`docs/architecture/phase13_14_15.svg`) — kein Gate, jetzt möglich.
- **Step D3** (`RescueConfig` + `gap_rescue_operator.py` in Phase 13) — kein Gate,
  Cross-Phase-Freigabe Phase 13 (Plan §4).

---

## Session stopped — 2026-08-31 (MiniMax-M3-Exec-Session #4, A-7 P15-F Doc-Rotation-Hook-Härtung + Dienste sauber pausiert für VM-Wartung)

> **Auftrag:** Nikinger-Chat 2026-08-31 nach A-6-Push-Phase: „ich schlage vor
> Phase-15-spezifische Hook-Härtung als Mini-Plan-Aufgabe (P14-F-Erweiterung +
> PHASE_DIRS-Update) — Vorbedingung für saubere Folge-Sessions zu bearbeiten.
> Danach: Der an dem Server, auf dem die VM läuft, finden kurzzeitig
> Wartungsarbeiten statt. Bitte pausiere alle Dienste sauber, sodass die VM
> passend pausiert werden kann. ich gebe dir bescheid, sobald die VM wieder
> oben ist, dann beendest du die Session. Alles klar?"
>
> Antwort: „Ja, alles klar, Nikinger." — Reihenfolge: (1) P15-F jetzt komplett
> (Mini-Plan-Doc + Code + Tests + INDEX.md + Phasenkopf-Update, 1 Commit + Push),
> (2) danach Dienste sauber stoppen + verifizieren, (3) bei VM-Comeback von
> Nikinger: Session-Stop-Block schreiben, Final-Commit/Push.
>
> Ausführungs-Scope: **1 Commit (Code+Tests+Doku, atomar) + Push + 1
> Session-Rotation-Commit + Push + Dienste-Stop (Außerhalb von Git)** — exakt
> P15-F Mini-Plan + Dienste-Pause. Push-Freigabe explizit von Nikinger erteilt
> (Session #2-Push + Session #3-Push für A-6 sind bereits auf `origin/main`,
> HEAD war `933167a` zu Session-Start; Session #4 pusht `0349797` für P15-F +
> Session-Rotation-Commit).

### Completed

**0. Cross-Session-Drift-Vorab-Check (Session-Start):**
- `python3 scripts/check_doc_rotation.py --strict` → 14 Phasen OK, **`phase15_v4`
  nicht abgedeckt** (PHASE_DIRS endet bei `phase14_discovery`).
- `python3 scripts/check_doc_rotation.py --strict --phase phase15_v4` →
  `[OK] phase15_v4: 1 session block`, aber Step-2 silent-skipped weil
  `_max_session_num` für „MiniMax-M3-Exec-Session #N" `None` returnt.
- Verifiziert per Python-REPL: alte Regex `(?:Mini-)?Session\s+(\d+)` matched
  **nicht** „MiniMax-M3-Exec-Session #3" / „Exec-Session #5".
- Pre-Commit-Hook (P14-F-Stand mit `--strict`) ist bereits installiert
  (`scripts/install_hooks.sh` ruft `--strict --quiet`); P15-F-Erweiterung greift
  nach Commit automatisch, kein Installer-Edit nötig.

**1. P15-F — Mini-Plan + Code + Tests + INDEX + Phasenkopf (1 Commit `0349797`):**
- `phase15_v4/PHASE15_HOOK_HARDENING_PLAN.md` (NEU, 322 Zeilen): Mini-Plan
  analog P14-F mit §0 BLUF, §1 Rahmen, §2 D1–D3 Locks, §3 verifizierte Befunde,
  §4 drei Schritte, §5 Akzeptanz A1–A6, §6 Out-of-Scope, §7 Fehlgriffe,
  §8 Drift-Liste, §9 Cross-Referenz.
- `scripts/check_doc_rotation.py` (2 Edits): `PHASE_DIRS` um `"phase15_v4"`
  ergänzt + `_SESSION_NUM_RE` permissiver
  (`(?:Mini-|MiniMax-\w+-Exec-|Exec-)?Session\s+#?(\d+)`).
- `tests/test_check_doc_rotation.py` (4 neue Tests A3–A6):
  `test_archive_sequence_handles_exec_session_with_hash` (A3, OK),
  `test_archive_sequence_drift_when_phase15_skips_a_session` (A4, DRIFT),
  `test_archive_sequence_ignores_plan_session_without_number` (A5, OK),
  `test_strict_check_passes_for_phase15_v4_against_real_repo` (A6, OK).
- `docs/INDEX.md` (1 neue Zeile): Mini-Plan-Index analog P14-F-Stand.
- `phase15_v4/CLAUDE.md` Header-Card: `down:`-Block um
  `./PHASE15_HOOK_HARDENING_PLAN.md` ergänzt + `updated:` auf
  `2026-08-31 (A-1..A-6 protokolliert + P15-F Doc-Rotation-Hook-Härtung, MiniMax-M3)`.
- **Push erteilt** (Nikinger 2026-08-31, Commit `0349797`).

**2. Dienste sauber pausiert (Post-Push, vor VM-Wartung):**
- `bash scripts/restart-services.sh status` (vor Stop, 2026-08-31, ~18:00 UTC):
  - Recorder (Phase 12) ALIVE, PID 21184
  - Discovery (Phase 14) ALIVE, PID 21197
  - Scheduler (Phase 8) ALIVE, PID 21207
  - WebUI (Phase 8) ALIVE, PID 21248
  - DISCOVERY_ARMED present (Operator+UI-controlled, untouched)
- `bash scripts/restart-services.sh stop`:
  - WebUI TERM pid=21248 → graceful ✅
  - Scheduler TERM pid=21207 → KILL nach 5 s (POST_WINDOW-Sleep-Cap-Bug, P14-D-
    Muster, **kein** P15-F-Thema; gleiches Verhalten wie A-5-Push-Phase
    Session 18 + Phase-7-CLAUDE.md Session-26-Block)
  - Discovery TERM pid=21197 → graceful ✅
  - Recorder TERM pid=21184 → KILL nach 5 s (gleicher POST_WINDOW-Sleep-Cap-
    Bug wie Scheduler)
  - Beide KILLs sind **bekannt + sicher** (POST_WINDOW-Sleep-Cap-Fix ist
    live-verified in P14-D Mini-Session 21; der 5-s-Timeout ist
    restart-services.sh-Default, nicht der Signal-Cap).
- `bash scripts/restart-services.sh status` (nach Stop):
  - 4/4 Dienste: **dead** ✅
  - DISCOVERY_ARMED: **present** (Operator-Intent konserviert, untouched) ✅
- VM-Wartung möglich, kein Crash, kein Datenverlust-Risiko (DISCOVERY_ARMED
  bleibt, PID-Files werden beim nächsten Start sauber neu geschrieben).

### Σ-Sweep Stand 2026-08-31 ~18:00 UTC (selbst nachgemessen, diese Session)

P15-F = Code + Test-Touch. Σ-Baseline 1703 → **1707 grün** (+4 neue P15-F-Tests):

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
| root `tests/` | **105** | **+4** (P15-F-Tests) |
| **Σ total** | **1707** | +4 vs. A-6-Baseline 1703 ✅ |

### Commits (lokal, in dieser Session erzeugt; **2 Commits, beide gepusht**)

| Commit | Scope | Diff |
|---|---|---|
| `0349797` | `phase15: hook-hardening -- PHASE_DIRS um phase15_v4 erweitert + permissive MiniMax-M3-Exec-Session-Regex (P15-F)` | 5 files, +575 −5 |
| (dieser, geplant) | Session-Rotation-Commit: alter #3-Block verbatim nach SESSIONS_ARCHIVE.md + neuer #4-Block im Phasenkopf + Step-A-7-Sektion | `phase15_v4/CLAUDE.md` +X (Session-Rotation), `phase15_v4/SESSIONS_ARCHIVE.md` +X (alter Block) |

**Push-Status (geplant nach Commit):** HEAD = `0349797` + Session-Rotation-Commit;
Push-Bundle geht raus, sobald dieser Commit fertig ist.

### Findings

🟢 **P15-F Plan-konform abgeschlossen** (Mini-Plan P15-F §5 Akzeptanz A1–A6 alle ✅).

🟢 **Kein Cross-Phase-Code-Edit:** `scripts/check_doc_rotation.py` + `tests/test_check_doc_rotation.py`
sind Phase-14-eigener Hygiene-Code seit Session 16 / P14-F; Erweiterung ist **kein**
Cross-Phase-Touch im Sinne der Phase-15-Freigabe-Liste (Plan §4: P2/4/5/6/7/13/14
freigegeben — `scripts/` ist Phase-14-intern, weil das Tool dort schon lebt).

🟢 **Pre-Commit-Hook (`scripts/check_doc_rotation.py --strict`) jetzt mit Phase-15-
Abdeckung:** 15 Phasen OK (vorher 14). Phase-15-Sequenz-Invariante aktiv geprüft
(`head=3, archive-newest=2, expected=2 → ✅`).

🟢 **`scripts/install_hooks.sh` + `scripts/dev_install.sh` unverändert:** P14-F-Stand
reicht (`--strict` ist bereits Default, `install_hooks.sh` ist als letzter Schritt
in `dev_install.sh` angeflanscht). P15-F ist **rein additiv** zur bestehenden
Hook-Infrastruktur.

🟡 **Heading-Form in Phase 15 unverändert** (Plan-D3): „MiniMax-M3-Exec-Session #N"
bleibt — lesbar + auditability-pflichtig (Modell-Name). Das Tool ist permissiv
genug (D2-Regex), nicht die Doku. Plan-Akzeptanz D3 eingehalten.

🟡 **Dienste-Pause mit bekannten KILLs (Scheduler + Recorder):** POST_WINDOW-Sleep-
Cap-Bug aus P14-D Mini-Session 18 — Scheduler + Recorder hängen im Sleep zwischen
Cycles, TERM-grace 5 s reicht nicht, SIGKILL nach 5 s (restart-services.sh-
Default). **Bekannt** (P14-D Mini-Session 18, dokumentiert in
[`phase14_discovery/PHASE14_D_DAEMON_SIGNAL_CAP_PLAN.md`](../phase14_discovery/PHASE14_D_DAEMON_SIGNAL_CAP_PLAN.md)
+ Live-Verified P14-D Mini-Session 21), **kein** Sicherheitsproblem (Restart ist
sauber, Datenbank-Konsistenz gewahrt, `restart-services.sh` idempotent beim Start).
Cross-Phase-Fix (Phase 8 Scheduler + Phase 12 Recorder Sleep-Cap vereinheitlichen)
ist Phase-15-Territorium (Block-D D5 oder eigener Mini-Plan).

🟡 **Push-Drift nicht mehr offen:** A-5-Push-Phase endete mit „1 Commit ahead,
Push wartet auf Nikinger" — Nikinger hat in dieser Session erteilt (A-6-Push),
A-6 pushte im Bundle (2 Commits), P15-F pushte als 1 Commit. **HEAD = `0349797`
auf `origin/main`, 0 ahead / 0 behind, working tree clean (außer
Session-Rotation-Edits, die im folgenden Schritt committed werden).**

### Open questions / blockers

- **Gate P7 unverändert zu** (Block B): wartet auf einen OPEN-Trade mit IG-Lag +
  24 h Beobachtung (Phase-12-Reconcile-Timing Live-Verify). Heute 0 OPEN-Trades
  gemessen.
- **Block A endgültig abgeschlossen** (A-1..A-6 + P15-F ✅). Blöcke B / C / D
  warten auf Nikinger-Wahl bzw. auf P7-Gate.
- **Phase-15-spezifische Hook-Härtung (P15-F) ✅ abgeschlossen** — diese Session.
- **Dienste gepausiert** (2026-08-31 ~18:00 UTC, vor VM-Wartung). **Warten auf
  VM-Comeback von Nikinger.** Bei Comeback: `bash scripts/restart-services.sh
  start` (alle 4), dann Session-Stop + Final-Push.
- **D5-H.-B-Vermerk im PHASE14_CLOSEOUT_HANDOVER.md Z. 272** bleibt stale bis
  Block-D-Step-D1 (per 📕-Konvention, nicht updateable).
- **Scheduler + Recorder POST_WINDOW-Sleep-Cap** (P14-D-Muster): KILL nach 5 s
  ist bekannt + sicher; ein **Phase-15-Block-D-Step** könnte das vereinheitlichen
  (Cross-Phase P8/12 — heute nicht freigegeben).

### NEXT (für die nächste Session / nach VM-Comeback)

**Nikinger-Wahl + VM-Comeback-bedingt.** Stand ~18:00 UTC = ~20:00 CEST, 2026-08-31.

**Aktion bei VM-Comeback (Nikinger-Bescheid):**
1. **`bash scripts/restart-services.sh status`** — alle 4 Dienste sollten weiter
   „dead" sein (VM-Wartung hat den Prozess-State vermutlich nicht zurückgesetzt).
2. **`bash scripts/restart-services.sh start`** — startet Recorder → Discovery →
   Scheduler → WebUI (Reihenfolge aus dem Skript).
3. **`bash scripts/restart-services.sh status`** — alle 4 sollten „ALIVE" sein.
4. **`pytest phase7_reward/tests -q`** — Pre-Test des Phase-7-Backoffs (Backoff-Tests
   A2–A5 müssen grün sein; war vor der Wartung grün, sollte nach Restart wieder
   grün sein, weil Code unverändert).
5. **Optional:** Smoke-Test `python3 scripts/smoke_test.py --help` (Operator-Smoke,
   kein Auto-Run).

**Konkrete Empfehlung für die Folge-Session (nach VM-Comeback + Restart):**

1. **Block D (Erbstücke) D1-D3** — kein Gate, jetzt möglich. D1: D5-H.-B-Vermerk
   in `phase14_discovery/PHASE14_CLOSEOUT_HANDOVER.md` (Cross-Phase P14, freigegeben
   — schließt den seit A-6 dokumentierten stale-Vermerk). D2: `phase13_14_15.svg`
   (~1 h). D3: Pfad A Operator-Tool in Phase 13 (Cross-Phase P13, freigegeben).
2. **Phase-15-Block-B-Vorbereitung** (`process_weight` 1.5 → 0.5 + Score-Reset auf 50):
   rein Code-Vorbereitung (Datenbank-Migration + Scorer-Config), kann jetzt
   geschrieben werden, **applied** erst nach P7-Abschluss (Operator-Aktion).
3. **Phase-15-Block-C-Vorbereitung** (Instinct-ECC): Extraktion-Logik + Validierung
   kann geplant + implementiert werden, **Promotion hinter Flag** (default
   `False`), `n=8` verweigert korrekt.
4. **Block B** — bleibt hinter Gate P7 (wartet auf A6-Abschlussmeldung des
   Phase-12-Reconcile-Timing-Fix-Live-Verify).

**Push-Status dieser Session:** **2 Commits gepusht** (A-6 in Session #3 + P15-F
`0349797` in Session #4); **1 Commit pending** (Session-Rotation-Commit, wird in
diesem Schritt erzeugt + gepusht).

> **Ältere Session-Blöcke** (verbatim ausgelagert, newest-first):
> [SESSIONS_ARCHIVE.md](./SESSIONS_ARCHIVE.md) — Rotation per Doc-Layers-Konvention
> ([docs/DOC_LAYERS_CONVENTION.md](../docs/DOC_LAYERS_CONVENTION.md)). Der vorherige
> MiniMax-M3-Exec-Session #3-Block (A-6, 1 Commit, lokal) wird in dieser Session
> **nach** SESSIONS_ARCHIVE.md rotiert.

> **Hinweis (History):** SESSIONS_ARCHIVE.md trägt jetzt 4 Session-Blöcke, alle
> 2026-08-31, newest-first: #4 (dieser, P15-F, gleich hinzugefügt) → #3 (A-6) →
> #2 (A-5) → #1 (A-1..A-4) → Plan-Session (Opus 5). Phasenkopf trägt exakt einen
> Block (dieser #4-Block), Rotation-Konvention gewahrt.
