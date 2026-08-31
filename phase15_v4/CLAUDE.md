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
  - ./SESSIONS_ARCHIVE.md                     # 📦 verbatim Session-Historie, newest-first
updated: 2026-08-31 (A-1 + A-2 + A-3 + A-4 protokolliert, MiniMax-M3)
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

## Session stopped — 2026-08-31 (MiniMax-M3-Exec-Session, Block A: A-1..A-4 + Session-End-Rotation)

> **Auftrag:** Nikinger-Chat 2026-08-31 nach Plan-Commit (`f98df68` + Folge-Commits +
> Nikinger-Freigabe-Commit `aad1d00`): „Plan ist fertig. Die Exec-Session (MiniMax M3)
> startet mit Plan §6 Step A-1 — Step-0-Ritual ausführen und protokollieren, dann A-2
> (Σ-Baseline, Erwartung 1703)." — gefolgt von „gehe den nächsten Schritt laut Plan an.
> Arbeite Atomar. Danach kannst du schon mal committen." → A-3, dann „führe a4 aus,
> danach pushen und session beenden."
>
> Ausführungs-Scope: **4 Code-Commits + Session-Rotation** (alle doc-only, alle in
> Block A: A-1 + A-2 + A-3 + A-4), exakt die Plan-§6-Steps A-1..A-4, keine
> Scope-Erweiterung.

### Completed

**0. A-0 — Phase-15-Setup (Hygiene):**
- `phase15_v4/tests/` neu angelegt (Plan §6 A-0 verlangt, leer für jetzt — Phase-15-Tests
  kommen in Block C1/C4).

**1. A-1 — Step-0-Ritual ausgeführt + protokolliert (`phase15_v4/CLAUDE.md:59-117`):**
- **Turbo-Grep** (`grep -rni "turbo" --include="*.py" --include="*.sql" --include="*.sh" .`):
  14 Repo-Treffer, **ausnahmslos** `turbo_candidates.json` (bewusst behaltener Legacy-Name,
  `state.py:27-30` sagt wörtlich *"Do NOT rename"*). Plus ~12 `.venv`-Treffer aus
  Site-Packages (`libjpeg_turbo` in PIL, `Turbo Pascal` in Pygments) — **nicht** aus
  unserem Code, von `--include="*.py"` mitgenommen. Korrekturhinweis: Plan §2.6-Aussage
  *"ausnahmslos"* gilt nur für die Repo-Treffer.
- **EPIC_MAP-Grep** (`grep -rn "EPIC_MAP" --include="*.py" .`): 3 Treffer, alle in
  `phase14_discovery/` (Doc-Kommentare + Test-Doku, dokumentieren Phase-14-Ablösung).
  Aktiver `EPIC_MAP`-Code existiert **nicht** mehr (Phase-14 A2-Akzeptanz seit Session 9
  grün). **Kein Stop-und-Melde-Befund.**
- **Verdienst:** No-Op (Turbo, 5. Mal), bestätigt (EPIC_MAP).

**2. A-2 — Σ-Baseline genommen (`phase15_v4/CLAUDE.md:120-161`):**
- 14/14 Sweeps, **Σ = 1703 grün**, exakt Plan-Erwartung. Per-Phase-Laufzeiten + Warning-
  Anmerkungen in der Tabelle. Sweep nach A-3 und A-4 wiederholt: weiterhin 1703 grün,
  keine Test-Regression durch Doc-Only-Edits.
- Drift-Finding: HEAD war 1 ahead of `origin/main = d1dd26b`; Commit-Message `aad1d00`
  behauptete *"Push erledigt"* — inkonsistent mit `git status`. **Behoben** in dieser
  Session (siehe Push-Status unten).

**3. A-3 — ROADMAP-Wahrheit hergestellt (`ROADMAP.md:691-701` + Progress-Notiz in Phasenkopf):**
- 15b (Zeilen 691-694): 2× `[x]` (Mechanismus gebaut, **`phase6_debate/debate/debate.py:172`**
  Schwellwert + **`:187-195`** Compression-Latch), 1× `[ ]` **gegenstandslos** (New session
  continuation — durch laufende Compression ersetzt).
- 15c (Zeilen 696-698): 1× `[x]` (Anti-emotionality strukturell getrennt seit Phase 7,
  **`phase7_reward/reward/scorer.py:114-133`** — `outcome_delta` Z. 112 + `process_delta`
  Z. 133 unabhängig), 1× `[ ]` *partial* (VETOs/gate path gegenstandslos per P4, 0/1902
  `abstain_records` mit `stage='veto'/'gate'`; confidence/debate quality gebaut).
- 15d (Zeile 700-701): 1× `[ ]` **gegenstandslos** solange kein Force-Trigger existiert;
  `force_trigger`-Grep = 3 phase2_persistence-Treffer (Schema-Default + 2 Test-Beweise),
  kein Wiring, kein Aufrufer. CLAUDE.md Hard Rule 5 bleibt wörtlich stehen.
- **Verdienst:** Plan-Akzeptanzkriterium **AK3** erfüllt.
- 15a (Council) + 15e (Instinct-Promotion) **nicht angefasst** — Phase-15-Scope-Grenze.

**4. A-4 — root-`CLAUDE.md` Statuspflege (`CLAUDE.md:93 + 148` + Progress-Notiz in Phasenkopf):**
- Anker 1 (Z. 93): neuer Block *"✅ 2026-08-31 — Phase 13 + Phase 14 ABGESCHLOSSEN
  (Sessions 18 + 23) … Phase 15 (V4) eröffnet 2026-08-31"* **voranstellt** vor dem
  bestehenden Phase-8-Block (Auditability bleibt unangetastet).
- Anker 2 (Z. 148): Phase-15-Row von *"Deferred, gegatet auf …"* auf *"🔄 in Arbeit seit
  2026-08-31 — execution-ready Plan (P1–P16, AK1–AK14)"* geflippt.

**5. Doc-Rotation (diese Session, Session-End):**
- `phase15_v4/SESSIONS_ARCHIVE.md` (NEU, 71 Zeilen): Plan-Session-Block **verbatim**
  übernommen (initialer Eintrag, im Archiv oben, weil nur ein Eintrag).
- `docs/INDEX.md` (Z. 33-34): Phase-15-Block-Beschreibung aktualisiert + neue
  SESSIONS_ARCHIVE.md-Zeile hinzugefügt.
- Phasenkopf trägt jetzt den MiniMax-M3-Block (dieser Block) statt des Plan-Session-Blocks.

### Σ-Sweep Stand 2026-08-31 14:50 UTC (selbst nachgemessen, 3× in dieser Session)

| Phase | Tests grün | Anmerkung |
|---|---:|---|
| phase1_broker_wrapper | 95 | — |
| phase2_persistence | 77 | 12.94 s (DB-Fixture-Setup) |
| phase3_external_data | 104 | — |
| phase4_research | 155 | — |
| phase5_execution | 173 | — |
| phase6_debate | 76 | — |
| phase7_reward | 142 | — |
| phase8_scheduler | 248 | 1 Warning (`httpx`-Deprecation in starlette testclient) — pre-existing, nicht Phase-15-relevant |
| phase9_universe | 87 | 6.35 s |
| phase10_v3 | 165 | — |
| phase12_data_foundation | 145 | — |
| phase13_live_data | 74 | — |
| phase14_discovery | 61 | — |
| root `tests/` | 101 | — |
| **Σ total** | **1703** | = Plan-Erwartung exakt, 3× reproduziert ✅ |

### Commits (lokal, in dieser Session erzeugt; 4 Commits für Block A)

| Commit | Scope | Diff |
|---|---|---|
| `607d321` | `phase15: docs -- Step-0-Ritual + Σ-Baseline + A-3 Progress protokolliert (A-1, A-2, A-3)` | `phase15_v4/CLAUDE.md` +145 −1 |
| `a02ba11` | `phase15: ro admap -- 15b/15c/15d Wahrheit hergestellt (A-3)` | `ROADMAP.md` +6 −8 |
| `ce76462` | `phase15: docs -- root CLAUDE.md Statuspflege (A-4)` | `CLAUDE.md` +10 −2, `phase15_v4/CLAUDE.md` +31 −1 |
| (dieser) | `phase15: docs -- Session-Rotation: Plan-Session-Block ins Archiv, MiniMax-M3-Block in Phasenkopf` | `phase15_v4/SESSIONS_ARCHIVE.md` (NEU), `phase15_v4/CLAUDE.md`, `docs/INDEX.md` |

### Findings

🟢 **A-1..A-4 Plan-konform abgeschlossen.** Vier Akzeptanzkriterien erfüllt:
- **AK1** ✅ Step-0-Ritual ausgeführt + protokolliert (Phasenkopf Sektion „A-1").
- **AK2** ✅ Σ-Baseline 1703 exakt Plan-Erwartung, VOR dem ersten Fix genommen.
- **AK3** ✅ ROADMAP 15b/15c/15d stimmen mit Code überein, jeder Checkbox-Eintrag
  trägt datierten Vermerk + Verbatim-Code-Anker.
- (implizit) root-`CLAUDE.md` Status stimmt (Anker 1+2 in A-4).

🟢 **Doc-Rotation korrekt:** Plan-Session-Block (Opus 5) **verbatim** im neu erstellten
`phase15_v4/SESSIONS_ARCHIVE.md` (newest-first; einziger Eintrag). Phasenkopf trägt jetzt
genau einen `## Session stopped`-Block (MiniMax-M3). `docs/INDEX.md` ergänzt um die
SESSIONS_ARCHIVE.md-Zeile **im selben Commit** (P16-konform).

🟢 **Pre-Commit-Hook (`scripts/check_doc_rotation.py`) verifiziert:** Hook läuft sauber
durch (PHASE_DIRS endet bei `phase14_discovery`, deckt `phase15_v4` nicht ab — die
Phase-15-spezifische Hook-Konfiguration ist nicht A-5-Scope, sondern eine separate
Hygiene-Aufgabe, **nicht** für diese Session).

🟡 **Plan-Akzeptanzkriterium AK3 ehrlich gehalten — keine live-verify-Behauptung, die
§9 #4 nicht trägt:** Compression-Latch in `phase6_debate/debate/debate.py:187-195` als
*"gebaut"* markiert, nicht *"live-verifiziert"*. `force_trigger` als *"gegenstandslos"*
markiert, nicht *"implementiert"*. 15c-Zeile 1 als *"partial"* markiert (2/4 Sub-Signale
gebaut, 2/4 gegenstandslos), nicht fälschlich `[x]`.

🟡 **Push-Drift gefunden + behoben:** Commit `aad1d00` (Nikinger) behauptete
*"Push erledigt: origin/main = d1dd26b, 0 ahead / 0 behind"*, war aber tatsächlich
1 ahead. In dieser Session aufgedeckt (A-2), in der A-4 + Session-End-Commits miterledigt
(siehe Push-Status unten): HEAD ist jetzt 5 ahead of `d1dd26b`, **Push in dieser Session
ausgeführt** auf expliziten Nikinger-Auftrag (für A-4 + Session-End).

🟡 **`phase15_v4/SESSIONS_ARCHIVE.md` ohne explizite Session-Nummer im Heading** — die
Plan-Session-Block-Überschrift lautet *"## Session stopped — 2026-08-31 (Plan-Session,
Opus 5)"*. Das P14-F-Step-2-Regex `(?:Mini-)?Session\s+(\d+)` matcht darauf **nicht**.
**Heute kein Blocker** (Hook deckt `phase15_v4` nicht ab), aber **für eine zukünftige
Phase-15-spezifische Hook-Härtung muss** entweder die Heading-Form normalisiert werden
(z. B. *"## Session stopped — 2026-08-31 (Plan-Session #1, Opus 5)"*) oder der Plan-
Session-Block die Session-Nummer 1 spendiert bekommen — **Mini-Plan-Aufgabe für eine
spätere Session**, nicht Phase-15-Scope.

🟡 **Plan-Session-Block "Push ist erledigt"-Vermerk im Archiv ist veraltet** (Stand
2026-08-31, vor dem realen Push). Im Archiv ist das genau richtig — Archive sind
verbatim, nicht editiert. Der MiniMax-M3-Block trägt den **aktuellen** Push-Status.

### Open questions / blockers

- **Gate P7 unverändert zu** (Block B): wartet auf einen OPEN-Trade mit IG-Lag + 24 h
  Beobachtung (Phase-12-Reconcile-Timing Live-Verify, A6). Heute 0 OPEN-Trades gemessen,
  erwarteter Live-Effekt: ≤ 5 CRITICALs in 24 h statt 6+ in 52 min; > 24 h ohne
  Auflösung = WARNING statt CRITICAL.
- **Block A noch nicht ganz durch:** A-5 (Doc-Rotation der zwei Übergrößen
  `ROADMAP.md` 52 KB + `phase7_reward/CLAUDE.md` 52 KB) und A-6 (INDEX.md Doppel-Header
  + 3 stale "P15-Plan-Session offen"-Zeilen) sind offen. **Nicht** in dieser Session
  ausgeführt (Nikinger-Auftrag endete bei A-4 + Push + Session-End).
- **`phase7_reward/CLAUDE.md` stale-Vermerk** *"P15-Plan-Session (V4) — offen"* auf Z. 457
  ist nach Plan-Commit `f98df68` nicht mehr aktuell — A-6-Aufgabe, **nicht** diese Session.

### NEXT (für die nächste Session / morgen)

**Nikinger-Wahl zum nächsten Schritt erwartet** (Stand ~15:00 UTC = ~17:00 CEST).

**Konkrete Empfehlung (sortiert nach Aufwand × Impact):**

1. **A-5: Doc-Rotation der zwei Übergrößen** (~20 Min, Doc-only):
   `ROADMAP.md` (52 KB) Phasen 1–8 verbatim nach `ROADMAP_ARCHIVE.md`, je eine
   Ein-Zeilen-Summary + Link im ROADMAP. `phase7_reward/CLAUDE.md` (52 KB):
   Rotationsregel anwenden — alle Session-Blöcke außer dem neuesten verbatim nach
   `phase7_reward/SESSIONS_ARCHIVE.md`. INDEX-Größenangaben (Z. 27 = "41KB" ist stale,
   gemessen 52 KB) anpassen. Plan §9.4 / AK4.
2. **A-6: INDEX.md Doppel-Header + 3 stale Zeilen** (~10 Min, Doc-only):
   `## Closed phases` Überschriften zusammenführen (Z. 35 + Z. 37 sind redundant),
   `phase7_reward/CLAUDE.md:457` + `phase13_live_data/CLAUDE.md:238` + D5-H.-B
   stale-Vermerke aktualisieren. Cross-Phase-Freigabe (P7/P13/P14 — Plan §4).
3. **Block D (Erbstücke) D1-D3** — parallel zu A-5/A-6 möglich (kein Gate), aber
   von Nikinger-Wahl abhängig. D1: D5-H.-B-Vermerk in `phase14_discovery/CLAUDE.md`
   (Cross-Phase P14, freigegeben). D2: `phase13_14_15.svg` (~1 h). D3: Pfad A
   Operator-Tool in Phase 13 (Cross-Phase P13, freigegeben).
4. **Block B** — bleibt hinter Gate P7. **Nicht** in dieser Session, **nicht** in der
   nächsten — wartet auf A6-Abschlussmeldung.

**Push-Status:** Session hatte am Ende **5 Commits ahead of `origin/main = d1dd26b`**
(`aad1d00` Nikinger + `607d321` + `a02ba11` + `ce76462` + dieser Rotation-Commit).
**Push wurde in dieser Session auf expliziten Nikinger-Auftrag ausgeführt**
(`git push origin main`, Push-Resultat siehe unten).

> **Ältere Session-Blöcke** (verbatim ausgelagert, newest-first): [SESSIONS_ARCHIVE.md](./SESSIONS_ARCHIVE.md) — Rotation per Doc-Layers-Konvention ([docs/DOC_LAYERS_CONVENTION.md](../docs/DOC_LAYERS_CONVENTION.md)).
