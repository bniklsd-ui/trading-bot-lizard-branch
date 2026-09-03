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
updated: 2026-09-03 (+ Block B B6 --apply ausgeführt unter Nikinger-Freigabe: AK6 ✅, Score 78.72 → 50.00 live, pre-apply Backup `data/trading_bot.sqlite.pre-apply-2026-09-03` archiviert, alle 4 Dienste wieder ALIVE, MiniMax-M3-Exec-Session #8)
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

## Step D2 — `docs/architecture/phase13_14_15.svg` (2026-09-01, MiniMax-M3 Exec-Session, Block-D-2)

> **Plan-Anker:** [`../docs/concepts/phase15_v4_plan.md`](../docs/concepts/phase15_v4_plan.md) §6 D2 (S. 654-668).
> **Scope:** Drei-Säulen-Bild `docs/architecture/phase13_14_15.svg` + `docs/INDEX.md`-Zeile im selben Commit. **Kein** Code, **kein** Cross-Phase-Code-Touch.
> **Nikinger-Freigabe (2026-09-01, Block-D-Auftrag):** „Erst weiter mit dem nächsten D step" — Step D2 nach D1, atomarer Commit pro Step.

### Was

NEU: [`docs/architecture/phase13_14_15.svg`](../docs/architecture/phase13_14_15.svg)
(329 Zeilen / 26.880 B / 1080×1080 / valid SVG per `xml.etree.ElementTree`).
Stil-konsistent mit den Geschwister-SVGs (`phase13_live_data.svg`, `phase12_closeout.svg`,
`phase12_5_failure.svg`, `phase10_v3.svg`, `data_foundation.svg`) — gleiche
`viewBox`, gleiches Farb-Set (`#f7f8fa` Hintergrund, `#1b1f24` Text, `#5b6470`
Sekundärtext, `#1e7a4d` grün OK, `#c0392b` rot STOP/AUS/zu, `#c98a1a` amber aktiv),
gleiche Marker (`a`/`ag`/`ar`/`ay`).

**Drei Spalten:**

1. **① Phase 13 — Beschaffung** (Spalte 1)
   - Vier Stufen S1 LS-Kerzen / S2 yF-Recorder / S3 Capital.com / S4 GapRescue (gestrichelt, „Default AUS · nie gelaufen (§3 B4)")
   - → `BarArchive` (data/bars.sqlite, quellenagnostisch)
   - → 4 Konsumenten (Paper-Tracker, Research P4, DivergenceSampler, measurement_heartbeat)
   - **Linker Callout:** „L1 (gelockt) — kein Pfeil Konsument → Quelle" mit `test_get_window_never_fetches`-Beleg (L12)

2. **② Phase 14 — Vermittlung** (Spalte 2)
   - 4 Quellen oben (IGDerivedSource / LSStaticSource / RegistryYFSource / CapitalSource — alle netzfrei im Discovery-Pfad)
   - → `instrument_source_availability` (Migration 007, 38 Zeilen, „einzige Kreuzungs-Wahrheit")
   - → DISCOVERY_ARMED-Flag
   - → EPIC_MAP als durchgestrichener Kasten mit Strike-through-Linie + „grep ist leer (Akzeptanz A2)"
   - → 4 Konsumenten rechts (phase13_backfill.py B2, phase9_universe.set_symbol, phase13_source_delta.py, webui/api.py)
   - **Rechter Callout:** „D5-H.-B geschlossen (2026-09-01) — Verfügbarkeits-Modell" mit `last_verified_utc`-Semantik + B3-Beleg aus Phase-13-Beweiswoche

3. **③ Phase 15 — Verwertung** (Spalte 3)
   - `reward_pts.score_after (78,72)` (rot — Block B in execution, process_weight 1.5 → 0.5)
   - → `Database.get_current_score()` → `get_risk_level(): AGGRESSIV (>50)` → `select_risk_pct → risk_pct (3.0/2.0)` → `compute_size → Positionsgröße` (Plan §2.5 Kette, jede Zeile mit Datei:Zeile)
   - `trade_lessons` + `reward_pts` → Instinct-Extraktion (LLM, amber) → deterministische Validierung (Code, kein LLM, AK8) → VETO 5 (bit-identisch zu heute, AK9)
   - **Promotion-Gatter ZU** (roter Rahmen + 2 rote Diagonal-Kreuzbalken, „heute n=8 < n_min=10: bleibt ZU", AK7)
   - Unterer Block-D-Callout: „D1 ✅ · D2 ✅ · D3 ⏳"

**Was-das-Bild-trägt-Callout** (gelber Balken unten, das ist der zweite Wert des Bildes):

> „Was das Bild trägt — die zwei Elemente, die man sehen können muss, ohne den Text zu lesen:
> ① **Fehlender Pfeil Konsument → Quelle** (Phase 13): die Pfeile führen immer von Quelle zum Archiv und vom Archiv zum Konsumenten — nie zurück. L1+L12 sind die strukturelle Garantie.
> ② **Geschlossenes Promotion-Gatter** (Phase 15): Instinct-Extraktion ist gebaut, Validierung ist gebaut, VETO 5 ist verkabelt — aber die Promotion auf VETO-5-Beteiligung wartet auf n ≥ n_min. Heute n=8, n_min=10: Gatter bleibt ZU."

**Status-Panel** (3 Spalten: Phase 13 ✅ / Phase 14 ✅ / Phase 15 🔄).

### INDEX-Zeile (im selben Commit)

[`docs/INDEX.md`](../docs/INDEX.md) nach der Phase-15-Plan-Zeile (Z. 60) eingefügt:

```
- [docs/architecture/phase13_14_15.svg](./architecture/phase13_14_15.svg) — 📕 1080×1080:
  Drei-Säulen-Bild für Phase 13 + 14 + 15 (das Bild, das beide Closeouts empfehlen, **kein**
  Solo-SVG). Drei Spalten: ① Phase 13 — Beschaffung (...) · ② Phase 14 — Vermittlung (...)
  · ③ Phase 15 — Verwertung (...) + Callout + Status-Panel. Stil konsistent mit
  `phase13_live_data.svg` / `phase12_closeout.svg`.
```

### Verdienst + Akzeptanz

| Akzeptanzkriterium (Plan §7) | Status |
|---|---|
| **AK11** | ✅ `phase13_14_15.svg` existiert (1080×1080, valid SVG); zeigt den **fehlenden Konsument→Quelle-Pfeil** (Phase 13 L1+L12-Callout + nie gezeichneter Pfeil) und das **geschlossene Promotion-Gatter** (rote Diagonal-Kreuzbalken + „n=8 < n_min=10: bleibt ZU") + INDEX-Zeile im selben Commit |
| **AK14** | ✅ Neue `.svg` hat ihre `docs/INDEX.md`-Zeile im selben Commit |

### Σ-Sweep

Doc-only, **kein** Code-Touch, **kein** Test-Touch. Σ-Baseline **1707 grün** unverändert
(Phase-15-A-7-Stand 2026-08-31, MiniMax-M3-Exec-Session #4, unverändert seit D1).

### Doc-Rotation-Hook-Verify

```
$ python3 scripts/check_doc_rotation.py --strict --quiet
exit=0
```

Keine neuen `.md`-Dateien — keine Doc-Rotation-Auswirkung.

### NEXT (für die Folge-Session)

- **Step D3** (`RescueConfig` + `gap_rescue_operator.py` in Phase 13) — kein Gate,
  Cross-Phase-Freigabe Phase 13 (Plan §4). **Einziges** offenes D-Item.

---

## Step D3 — Pfad A Operator-Tool, gebaut aber AUS (2026-09-01, MiniMax-M3 Exec-Session, Block-D-3)

> **Plan-Anker:** [`../docs/concepts/phase15_v4_plan.md`](../docs/concepts/phase15_v4_plan.md) §6 D3 (S. 670-698).
> **Scope:** `RescueConfig` in `phase13_live_data/live_data/rescue.py` + `phase13_live_data/scripts/gap_rescue_operator.py` (NEU) + 7 Tests in `phase13_live_data/tests/test_rescue.py`. Cross-Phase-Freigabe Phase 13 (Plan §4, Nikinger 2026-08-31).
> **Nikinger-Freigabe (2026-09-01, Block-D-Auftrag):** „D3, danach commiten und Session beenden" — Step D3 nach D2, atomarer Commit, Session-Rotation am Ende.

### Was

**1. `RescueConfig` (NEU in `phase13_live_data/live_data/rescue.py:46-86`)**

Frozen dataclass, drei Felder:
```python
@dataclass(frozen=True)
class RescueConfig:
    enable_gap_rescue: bool = False      # Master-Schalter (Default AUS, Plan §6 D3)
    epics: tuple[str, ...] = field(default_factory=tuple)  # leer = Universe-Resolver
    max_points_per_run: int = 560         # §6 D3 + §9.2: 560/Woche, nicht nachgerechnet
```

`enable_gap_rescue` ist **nur** hier — kein SchedulerConfig-Feld, kein Phase-8-Wiring
(Plan §6 D3 explizit: „Kein Feld in `SchedulerConfig`, kein Wiring in
`phase8_scheduler/`"). D19/L18 (IG Default AUS, Mini-Session 24) bleibt gelockt;
Pfad A macht das Aufheben **erst möglich**, hebt es **nicht** auf.

**2. `phase13_live_data/scripts/gap_rescue_operator.py` (NEU, 299 Zeilen)**

Operator-Tool nach dem Muster von `scripts/capital_backfill.py`. CLI:
- `--start`, `--end` (UTC ISO 8601, beide required)
- `--epics` (comma-separated) oder `--auto` (Universe-Resolver, analog Capital-Backfill)
- `--max-points-per-run` (Default 560)
- `--enable-gap-rescue` (Bedingung 1 der Doppel-Sperre)
- `--apply` (Bedingung 2 der Doppel-Sperre)
- `--broker` (Default `ig_demo`)

**Doppel-Sperre (Plan §6 D3):** Schreib-Pfad aktiviert sich **nur**, wenn
`enable_gap_rescue=True` UND `--apply` beide gesetzt sind. Sonst `--dry-run`-Default
mit JSON-Plan-Output, der die fehlenden Bedingungen explizit auflistet. Analog
`promote_eligible` (P10), `enable_shadow_schedule`, `enable_divergence_sampler`,
`enable_paper_debate` (P10/Phase-15-Disziplin).

Im `--dry-run`-Pfad: **kein** Keyring-Read, **kein** Broker-Connect, **kein**
Archive-Write — Operator kann den Plan sicher inspizieren, bevor er scharf
schaltet. Die Punkteschätzung ist konservativ (`epic_count * 60`, gecappt auf
`max_points_per_run`); Plan §9.2 weist explizit darauf hin, dass die 560/Woche
aus P13-Findings §8.2 stammen und **nicht** nachgerechnet sind.

Im Schreib-Pfad: baut `SourceBudget` + `BarArchive` + `GapRescue` + Broker über
`broker_wrapper.factory.get_broker(args.broker)`, ruft `rescue_epic(epic, start,
end)` pro Epic, aggregiert `RescueReport` ins JSON-Envelope. Top-level Safety
Net fängt Setup-Fehler (Keyring leer, Broker nicht erreichbar, etc.) und gibt
einen `{"ok": false, "error": ...}`-Envelope zurück.

**3. 7 neue Tests in `phase13_live_data/tests/test_rescue.py`**

| Test | Pinnt |
|---|---|
| `test_rescue_config_default_is_aus` | AK12: `RescueConfig()` default `enable_gap_rescue=False`, `epics=()`, `max_points_per_run=560` |
| `test_rescue_config_is_frozen_and_hashable` | frozen-dataclass-Disziplin (Phase-10-Vorbild) |
| `test_rescue_config_epics_default_is_empty_tuple_not_list` | mutable-default-trap-Schutz: `tuple`, kein `list` |
| `test_enable_gap_rescue_is_NOT_in_scheduler_config` | AK12 strukturell: kein `phase8_scheduler/`-Match, nur `phase13_live_data/`-Deklaration |
| `test_gap_rescue_operator_doppel_sperre_default_dry_run` | Default (kein `--enable-gap-rescue`, kein `--apply`) ⇒ `dry_run: True`, beide Bedingungen in `missing` |
| `test_gap_rescue_operator_enable_only_no_apply_still_dry_run` | Bedingung 1 allein reicht nicht |
| `test_gap_rescue_operator_apply_only_no_enable_still_dry_run` | Bedingung 2 allein reicht nicht |

### Verdienst + Akzeptanz

| Akzeptanzkriterium (Plan §7) | Status |
|---|---|
| **AK12** | ✅ `enable_gap_rescue` existiert als Feld einer `RescueConfig` in Phase 13 (`rescue.py:78`) mit Default `False`; Operator-Script mit `--dry-run`-Default (`gap_rescue_operator.py:194`); **kein** `SchedulerConfig`-Feld (`test_enable_gap_rescue_is_NOT_in_scheduler_config` pınnt das strukturell), **kein** `phase8_scheduler/`-Diff |
| **AK13** | ✅ Σ-Sweep am Ende ≥ 1703 — exakt **1714 grün** repo-weit (1707 + 7 neue P15-D3-Tests) |

### Σ-Sweep Stand 2026-09-01 ~08:00 UTC (selbst nachgemessen, diese Session)

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
| **phase13_live_data** | **81** | **+7** (P15-D3: 4 RescueConfig + 3 Operator-Script) |
| phase14_discovery | 61 | — |
| root `tests/` | 105 | — |
| **Σ total** | **1714** | **+7** vs. P15-D2-Stand 1707 ✅ |

### Doc-Rotation-Hook-Verify

```
$ python3 scripts/check_doc_rotation.py --strict --quiet
exit=0
$ python3 scripts/check_doc_rotation.py --strict --phase phase15_v4
[OK]   phase15_v4: 1 session block
```

Keine neuen `.md`-Dateien — keine Doc-Rotation-Auswirkung.

### Cross-Phase-Touch

Nur Phase-13-eigener Code (`live_data/rescue.py`, `scripts/gap_rescue_operator.py`,
`tests/test_rescue.py`); **kein** Touch in `phase8_scheduler/` (AK12 explizit),
**kein** Touch in `phase2_persistence/` oder anderen Phasen.

### NEXT (für die Folge-Session)

- **Block A** endgültig ✅ (A-1..A-7)
- **Block D** endgültig ✅ (D-1..D-3) — diese Session
- **Block B** bleibt hinter Gate P7 (Phase-12-Reconcile-Timing Live-Verify,
  wartet auf nächsten OPEN-Trade + 24-h-Beobachtung)
- **Block C** (Instinct-ECC) erst nach Block B
- **Push-Status:** 3 Commits lokal (D1, D2, D3), 3 ahead of `origin/main`,
  Working-Tree clean nach Commit — Push-Freigabe für die nächste Session

---

## Session stopped — 2026-09-03 (MiniMax-M3-Exec-Session #8, Block B B6 --apply ausgeführt unter Nikinger-Freigabe, AK6 ✅, Score 78.72 → 50.00 live, Backup archiviert)

> **Auftrag:** Nikinger-Chat 2026-09-03 morgens: „Zusammen die letzten offenen Items aus
> Block B angehen - ich bin bereit." — bezogen auf NEXT-Block aus Session #7: Item #1
> (`--apply` für `reset_score_baseline.py`) + Item #4 (Status-Pflege-Hygiene root-CLAUDE.md).
> Nikinger-Antwort auf Frage-Slot zur --apply-Reihenfolge: „erst stoppen, dann backup,
> dann --apply".
> Plan-Anker: [`../docs/concepts/phase15_v4_plan.md`](../docs/concepts/phase15_v4_plan.md)
> §6 Block B B6 + §7 AK6 + §11 #3. Cross-Phase-Freigabe: Phase 7 freigegeben (§4).
>
> Antwort: „Ja, alles klar, Nikinger." — Reihenfolge exakt wie vorgegeben:
> (1) Cross-Session-Drift-Check; (2) Dienste stoppen (alle 4); (3) DB-Backup
> `data/trading_bot.sqlite.pre-apply-2026-09-03` (md5-verify); (4) `--apply`
> (`reward_pts.id=11`, 78.72 → 50.00, idempotent); (5) DB-Direkt-Verify + Idempotenz-
> Test (zweiter `--apply`-Lauf = no-op); (6) Dienste restart; (7) Σ-Sweep 1742 grün;
> (8) Audit-Block in Phasenkopf + Item #4 Status-Pflege-Hygiene (root-CLAUDE.md Phase-15-
> Row); (9) Session-Rotation (dieser Commit).
>
> Ausführungs-Scope: **2 Doc-only-Commits (Audit-Block + Item #4 Status-Pflege) +
> dieser Session-Rotation-Commit** — exakt die freigegebene Aufgabe + Doc-Hygiene.
> **Kein** Code-Touch, **kein** Phase-7-Test-Touch, **kein** Cross-Phase-Code-Touch.
> Push-Freigabe: Nikinger entscheidet am Session-Ende.

### Completed

**0. Cross-Session-Drift-Vorab-Check (Session-Start, 2026-09-03 ~11:55 CEST = ~09:55 UTC):**
- `git status` → `main`, working tree clean (nur `data/` untracked).
- `git log --oneline -5` → HEAD = `40b3ae0 phase15: docs -- Session #7 NEXT-Block
  aktualisiert`. `origin/main = 40b3ae0` (0 ahead / 0 behind) — Session #7 ist gepusht.
- `python3 scripts/check_doc_rotation.py --strict --quiet` → exit 0.
- `bash scripts/restart-services.sh status` → 4/4 Dienste ALIVE seit Session #7-Restart
  (Recorder 122384, Discovery 122397, Scheduler 122407, WebUI 122457).
- DB-State: `SELECT id, score_after FROM reward_pts ORDER BY id DESC LIMIT 1`
  → `11|78.72` (Plan §3 B1: −1 972,87 EUR / +28,72 Score unverändert seit 2026-08-27).
- 0 OPEN-Trades (`SELECT COUNT(*) FROM trade_outcomes WHERE status='OPEN'` → 0).
- `--dry-run` reproduziert exakt das erwartete Update (id=11, 78.72 → 50.00, exit 0).

**1. Dienste-Stop (Session-Aktion, kein eigener Commit):**
- `bash scripts/restart-services.sh stop` → alle 4 Dienste TERM:
  - WebUI pid=122457 → graceful ✅
  - Scheduler pid=122407 → SIGKILL nach 5 s (POST_WINDOW-Sleep, **bekannt** aus P14-D
    Mini-Session 21 + Session #4+#7)
  - Discovery pid=122397 → SIGKILL nach 5 s (gleicher Sleep-Pfad)
  - Recorder pid=122384 → SIGKILL nach 5 s (gleicher Sleep-Pfad)
- `ps aux | grep -E "scheduler\\.run|recorder\\.run|discovery\\.run|webui\\.run"`
  → leer. Disziplin Plan §6 Block B „Bot-berühren" eingehalten.

**2. DB-Backup (Session-Aktion, kein eigener Commit):**
- `cp -p data/trading_bot.sqlite data/trading_bot.sqlite.pre-apply-2026-09-03`
- 3 125 248 B (byte-identisch zur Live-DB zum Backup-Zeitpunkt).
- `md5sum` Pre-Backup-Verify: **beide identisch** (`c2e6bce6...`).
- `data/` ist `.gitignore`-d (Repo-Konvention, kein Commit nötig).

**3. Block-B-B6 `--apply` (kein eigener Commit — DB-Write, kein Code-Touch):**
- `python3 phase7_reward/scripts/reset_score_baseline.py --apply`
- **Effekt:** `UPDATE reward_pts SET score_after = 50.0 WHERE id = (SELECT id FROM
  reward_pts ORDER BY id DESC LIMIT 1)` — exakt 1 row betroffen (id=11).
- **Idempotenz-Test:** zweiter `--apply`-Lauf → `applied=True, before=50.0,
  after=50.0` (no-op, korrekt).
- DB-Direkt-Verify: `SELECT score_after FROM reward_pts ORDER BY id DESC LIMIT 1`
  → **50.0** ✅ (= `Database._DEFAULT_SCORE`, == `_RISK_THRESHOLD` für
  `get_risk_level`).
- Backup-Direkt-Verify: `data/trading_bot.sqlite.pre-apply-2026-09-03` → id=11
  noch **78.72** ✅ (Restore-Pfad: `cp data/trading_bot.sqlite.pre-apply-2026-09-03
  data/trading_bot.sqlite`).

**4. Audit-Block (Plan §6 B6 #5) — applied-Version:**

```
## Score-Reset Audit Block (Phase 15 / Block B / Step B6)

- db_path: `/home/trading-bot/trading-bot/data/trading_bot.sqlite`
- mode: `apply`
- applied: `True`
- latest reward_pts id: `11`
- latest score_after (before): `78.72`
- latest score_after (after):  `50.00`
- neutral baseline: `50.0` (== `Database._DEFAULT_SCORE`)
- AK6 evidence: score-reset script exists; --dry-run output is below; --apply was
  executed under explicit Nikinger-Freigabe (Plan §11 #3) in Session #8
  (2026-09-03 ~12:00 CEST = ~10:00 UTC), with explicit operator sequence
  stop → backup → apply → restart, and pre-apply backup archived at
  `data/trading_bot.sqlite.pre-apply-2026-09-03`.
- known inconsistent row (P5): id=11's `score_after` now reads `50.0` while
  `outcome_score_delta + process_score_delta = -2.017 + 3.15 = +1.133`, so the
  previous `score_after` (78.72) - 1.133 ≠ 50.0. **This is P5's documented
  "bekannte, bewusste Inkonsistenz"** (Plan §1, decision P5) — the deltas are
  the actual measurement history and stay untouched; only the accumulator is
  re-baselined. The Phasenkopf carries this note for auditability.
```

**5. Dienste-Restart (Session-Aktion, kein eigener Commit):**
- `bash scripts/restart-services.sh start` → alle 4 Dienste hochgefahren
  (Recorder 124485, Discovery 124512, Scheduler 124569, WebUI 124611).
- DISCOVERY_ARMED present (Operator-Intent konserviert).
- Phase-15-Code-Basis jetzt **live mit reset score**: Scheduler läuft mit
  `process_weight=0.5` (B2) + `get_current_score() = 50.0` (B6 `--apply`).
- `Database.get_risk_level()` → **KONSERVATIV** (50 ≤ 50, Schwelle aus P2 `db.py:49`),
  d.h. `risk_pct = 2.0 %` statt 3.0 % bis zur nächsten Score-Änderung.

**6. Σ-Sweep Stand 2026-09-03 ~12:05 UTC (selbst nachgemessen, diese Session):**

| Phase | Tests grün | Δ |
|---|---:|---|
| phase1_broker_wrapper | 95 | — |
| phase2_persistence | 77 | — |
| phase3_external_data | 104 | — |
| phase4_research | 155 | — |
| phase5_execution | 173 | — |
| phase6_debate | 76 | — |
| phase7_reward | 166 | — |
| phase8_scheduler | 248 | — |
| phase9_universe | 87 | — |
| phase10_v3 | 165 | — |
| phase12_data_foundation | 145 | — |
| phase13_live_data | 81 | — |
| phase14_discovery | 61 | — |
| phase15_v4 | 4 | — |
| root `tests/` | 105 | — |
| **Σ total** | **1742** | unverändert vs. Session #7 ✅ |

**AK13 ✅** (≥ 1703, null neue Fehler; `--apply` ist reiner DB-Write ohne Code/Tests).

**7. Doc-Rotation-Hook-Verify:**

```
$ python3 scripts/check_doc_rotation.py --strict --quiet
exit=0
$ python3 scripts/check_doc_rotation.py --strict --phase phase15_v4
[OK]   phase15_v4: 1 session block            ← wird durch diesen Commit 1 bleiben
```

### Findings

🟢 **Block B endgültig abgeschlossen** (B1+B2+B3+B4+B5+B6 alle ✅, inkl. `--apply`):
AK5 + AK6 + AK13 **alle grün**. Score-Re-Base auf 50.0 ist live;
`Database.get_risk_level() = KONSERVATIV`, `risk_pct = 2.0 %`.

🟢 **AK6 empirisch vollständig bewiesen:** --dry-run (Session #7) + --apply
(diese Session) + Idempotenz-Test (no-op second run) + DB-Direkt-Verify +
Backup-Verify. Der Reset ist **gemacht**, nicht **vorbereitet**.

🟢 **Auditability gesichert:**
- Pre-apply-Backup unter `data/trading_bot.sqlite.pre-apply-2026-09-03` (md5-verify
  Pre-Backup = identisch zur Live-DB; Post-apply = unterschiedlich, Restore-Pfad
  dokumentiert).
- Audit-Block im Phasenkopf mit `mode: apply, applied: True` + Hinweis auf den
  P5-Score-/Deltas-Mismatch (bewusst, dokumentiert).
- Session-Rotation-Commit (dieser Commit) verschiebt den Session #7-Block
  verbatim nach `SESSIONS_ARCHIVE.md` (Rotation-Regel aus root-CLAUDE.md).

🟢 **Test-Regression = 0:** 1742 grün, identisch zu Session #7. `--apply`
schreibt in eine **bereits validierte** `reward_pts.score_after`-Spalte (gleicher
Typ, gleicher Wertebereich, gleiche Clamping-Logik).

🟡 **H3-Semantik-Frage bleibt offen** (Plan §10): „ist ein Stop-Out ein clean
exit?" — Block B löst die Invariante (P1/P2), nicht die Semantik. Block C wird
diese Frage nicht direkt adressieren; sie ist eine eigenständige
Design-Entscheidung.

🟡 **Plan §9.1 + §9.3 unverändert offen:** `spread_at_entry_pct = 1.0` bei
Trade 8 (Ursache B5 nicht aufgeklärt), exakte Anzahl der Stellen in
`test_migrations.py` für Version 8 → 9. Block C (Step C1) wird die Migrations-
Version anfassen — Test-Anpassung dort mitnehmen.

### Open questions / blockers

- **Block B vollständig abgeschlossen** ✅ (alle 6 Steps inkl. --apply live).
- **Block C (Instinct-ECC)** kann jetzt starten. Cross-Phase Phase 2 + Phase 5
  sind in §4 für Phase 15 freigegeben. Reihenfolge: C1 Migration 009 +
  DB-Methoden → C2 `phase15_v4/instinct/`-Package → C3 VETO 5 +
  `ExecutionConfig.longterm_rules` → C4 Tests. ~2-3 h inkl. Sweep.
- **Phase-12-Reconcile-Timing Live-Verify (A6)** weiterhin ausstehend — wartet auf
  nächsten OPEN-Trade + 24 h Beobachtung (Backoff replay-verifiziert, Item #3
  aus Session #7-NEXT-Block).
- **Pfad A Scharfschalten** ist separate Nikinger-Aktion (Item #2 aus
  Session #7-NEXT-Block, Plan §6 D3 + §9.2).
- **Push-Freigabe** für 2 Commits (Audit-Block + Item #4) + dieser
  Session-Rotation-Commit ausstehend.

### NEXT (für die nächste Session)

**Nikinger-Wahl-bedingt.** Stand 2026-09-03 ~12:10 UTC = ~14:10 CEST.

**Status-Update der Items aus Session #7-NEXT-Block:**

| # | Item | Status nach Session #8 |
|---|---|---|
| **1** | `--apply` für B6 | ✅ **erledigt** (diese Session, mit expliziter Reihenfolge stop→backup→apply→restart) |
| **2** | Pfad A scharfschalten | offen — separate Nikinger-Aktion |
| **3** | Phase-12-Reconcile-Timing Live-Verify (A6) | offen — automatisch beim nächsten OPEN-Trade |
| **4** | Status-Pflege-Hygiene root-CLAUDE.md | 🔄 in Bearbeitung (siehe Commit-Plan unten) |

**Konkrete Empfehlung für die Folge-Session:**

1. **Block C (Instinct-ECC)** starten (~2-3 h inkl. Sweep, ~6-8 Commits):
   - C1: Migration 009 (`phase2_persistence/migrations/009_phase15_instincts.sql`) +
     `_INSTINCT_COLUMNS` + 3 DB-Methoden in `phase2_persistence/persistence/db.py`
     + Test-Migrations-Anpassungen.
   - C2: `phase15_v4/instinct/`-Package (`models.py` + `extractor.py` +
     `validator.py` + `promotion.py`), spiegelt `Brain.reflect`/`promote_eligible`
     (Plan §6 C2 + P9).
   - C3: VETO 5 + `ExecutionConfig.longterm_rules` in Phase 5
     (`phase5_execution/execution/vetos.py` + `config.py`); Cross-Phase P5
     freigegeben.
   - C4: Tests (`phase15_v4/tests/test_instinct.py` +
     `test_promotion.py` + Phase-5-Sweep-Verify).
2. **`phase13_14_15.svg` Polish** (optional, ~10 Min): Spalten-Abstände /
   Callout-Positionen falls nicht 100 % sitzend.
3. **Status-Pflege-Hygiene Item #4** (im selben Commit dieser Session, optional):
   root-CLAUDE.md Phase-15-Row aktualisieren auf
   „Block A + D ✅ · Block B ✅ (--apply live) · Block C 🔓".

**Push-Status dieser Session:** **0 Commits gepusht** (Session #7 ist auf
`origin/main` = `40b3ae0`); **2-3 Commits pending** (Audit-Block + Item #4
optional + Session-Rotation-Commit, je nach Reihenfolge).

**Block-Status nach dieser Session:**

| Block | Status |
|---|---|
| A (Haushalt) | ✅ A-1..A-7 (Sessions #1-#4) |
| B (Reward-Kalibrierung) | ✅ B1..B6 **komplett + live** (--apply ausgeführt 2026-09-03 ~12:00 CEST) |
| C (Instinct-ECC) | 🔓 entsperrt, kann starten |
| D (Erbstücke) | ✅ D-1..D-3 (Session #5) |

## Phase 15 — Block B / Gate-P7-Status-Notiz (2026-09-02, MiniMax-M3 Exec-Session #6)

> **Plan-Anker:** [`../docs/concepts/phase15_v4_plan.md`](../docs/concepts/phase15_v4_plan.md)
> §0 + §6 Block B (GATE P7) + §11 #1.
> **Cross-Phase-Freigabe:** Phase 7 ist freigegeben (§4).

### Was gemessen wurde (Stand 2026-09-02 ~21:20 CEST)

- **„Phase-12-Reconcile-Timing Live-Verify" (P7-A6):** in
  [`../phase7_reward/CLAUDE.md`](../phase7_reward/CLAUDE.md) als „A6" geführt;
  Akzeptanz = ≤ 5 CRITICALs in 24 h nach dem nächsten OPEN-Trade (vorher 6+ in 52 min).
- **Stand 2026-09-02 19:23 UTC = 21:23 CEST = 6 Tage seit letztem OPEN-Trade.**
  Letzter geschlossener Trade ist `trade_outcomes.id = 11` vom **2026-08-27**
  (5 geschlossene Tage dazwischen, 0 OPEN, SQL-verifiziert).
- **24-h-Beobachtungsfenster im strengen Sinne** (= 24 h ununterbrochener
  Live-Betrieb mit **mindestens einem OPEN-Trade**, an dem die Reconcile-Timing
  gemessen werden kann): **de facto nicht möglich** seit dem letzten OPEN. Der
  Scheduler läuft ununterbrochen, das Reconcile-Verhalten selbst ist in
  Mini-Session 26 (Backoff 15 min → 30 min → 1 h → 4 h → 24 h) bereits
  replay-verifiziert (17 → 4 CRITICALs) — aber das ist ein **Unit-Test-Replay**,
  keine Live-Beobachtung.
- **Backoff-Logik ist live** (Mini-Session 26½, Operator-Restart 2026-08-31
  ~08:30 CEST, alle 4 Dienste ALIVE seit Aug 31 20:52 — Stand 2026-09-02 19:23
  UTC: Recorder 42947, Discovery 42958, Scheduler 42968, WebUI 43008).
- **Markt-Verlauf 2026-09-02:** 09:00–17:30 CEST ohne neuen Trade. Scheduler
  hat den Tag über PRE_OPEN/OPEN/WINDOW/POST_WINDOW-Zyklen normal durchlaufen,
  ohne dass die 5-Gate-Pipeline einen Kandidaten bis zum OPEN gebracht hat
  (P4-Research liefert weiter Kandidaten, P5-Gates/VETOs filtern sie offenbar
  weg — separater Befund, nicht Teil dieser Notiz).

### Befund

**Gate P7 ist im strengen Sinne nicht abschließbar, im praktischen Sinne tot:**

- 24 h+ sind vergangen (Anker für A6-Beobachtungsfenster wäre „nächster OPEN-Trade").
- 0 OPEN-Trades seit `id=11` (2026-08-27, also 6 Tage).
- Ohne OPEN-Trade keine IG-Lag-Beobachtung am echten Live-Betrieb möglich.
- Der Backoff-Mechanismus selbst ist replay-verifiziert (Mini-Session 26).

**Nikinger-Entscheidung 2026-09-02 (MiniMax-M3-Exec-Session #6):**
„Ich schlage vor, den heutigen Tag bis Marktschluss noch auf einen open trade
zu warten. Kommt dieser nicht, fängst du mit der Doku Notiz an." — am Abend
kein Trade; Notiz wird hiermit eingefügt.

### Konsequenz für Block B

**Code-Vorbereitung startet jetzt** (Phase 15 Block B §6 B1–B6, alle atomaren
Edits), **Score-Reset-`--apply` bleibt Operator-Aktion** (Plan §11 #3 — Nikinger).

Reihenfolge: B1 (Test, RED) → B2 (`process_weight` 1.5 → 0.5) → B3 (⚠-Docstring-Nachtrag)
→ B4 (`tight_spread_pct` ponytail) → B5 (`veto_trigger_count` Vermerk) →
B6 (`reset_score_baseline.py` + Test + `--dry-run` mit Audit-Block für Nikinger).

**Bot-Stop-Disziplin (§6 Warnung Block B):** wird im Session-#6-Block vor B2
eingehalten (`bash scripts/restart-services.sh stop scheduler`, `ps aux |
grep scheduler.run` Gegenprobe, danach `start scheduler`). B1 ist read-only
gegen `scorer.py` und benötigt **keinen** Bot-Stop.

### Auditability

Diese Notiz ersetzt **nicht** die A6-Akzeptanz aus
[`../phase7_reward/PHASE12_RECONCILIATION_TIMING_PLAN.md`](../phase7_reward/PHASE12_RECONCILIATION_TIMING_PLAN.md) §6.
A6 bleibt formell „ausstehend bis nächster OPEN-Trade + 24 h". Diese Notiz hält
fest, **warum** Block B unter Nikinger-Freigabe 2026-09-02 trotzdem starten kann:
P7s A6 ist eine **Beobachtungs-Akzeptanz**, keine **Code-Akzeptanz**, und der zu
beobachtende Effekt (≤ 5 CRITICALs / 24 h) hängt vom Eintreten eines OPEN-Trades
ab, das im aktuellen Markt-Regime nicht eingetreten ist.

📕-Konvention eingehalten: keine Edits in
[`PHASE12_RECONCILIATION_TIMING_PLAN.md`](../phase7_reward/PHASE12_RECONCILIATION_TIMING_PLAN.md),
[`PHASE13_BEWEISWOCHE_FINDINGS_2026-08-31.md`](../phase13_live_data/PHASE13_BEWEISWOCHE_FINDINGS_2026-08-31.md)
oder anderen L3-Snapshots.

> **Hinweis:** diese Sektion ist **kein** `## Session stopped`-Block und triggert
> damit **keine** Doc-Rotation (`scripts/check_doc_rotation.py` zählt nur
> `Session stopped`-Header). Sie ist ein Phase-15-interner Doku-Absatz; der
> aktuelle Footer wurde mit dem Session-#6-Rotation-Commit aktualisiert (siehe
> `## Session stopped — 2026-09-02` weiter oben).


---

> **Ältere Session-Blöcke** (verbatim ausgelagert, newest-first):
> [SESSIONS_ARCHIVE.md](./SESSIONS_ARCHIVE.md) — Rotation per Doc-Layers-Konvention
> ([docs/DOC_LAYERS_CONVENTION.md](../docs/DOC_LAYERS_CONVENTION.md)). Der vorherige
> MiniMax-M3-Exec-Session #7-Block (Block B B1-B6 Code-Vorbereitung + --dry-run-Audit,
> 221 Z.) wurde in dieser Session **nach** SESSIONS_ARCHIVE.md rotiert (newest-first,
> direkt vor dem #6-Block).

> **Hinweis (History):** SESSIONS_ARCHIVE.md trägt jetzt **8** Session-Blöcke,
> alle 2026-08-31 / 2026-09-01 / 2026-09-02 / 2026-09-03, newest-first: #8 (dieser,
> Block B B6 --apply live) → #7 (B1-B6 Code-Vorbereitung + --dry-run, gleich dazurotiert)
> → #6 (P7-Status-Notiz) → #5 (Block D) → #4 (P15-F) → #3 (A-6) → #2 (A-5) → #1
> (A-1..A-4) → Plan-Session (Opus 5). Phasenkopf trägt exakt einen Block (dieser
> #8-Block), Rotation-Konvention gewahrt.
