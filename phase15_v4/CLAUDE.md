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
updated: 2026-08-31 (A-1 + A-2 + A-3 protokolliert, MiniMax-M3)
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

## Session stopped — 2026-08-31 (Plan-Session, Opus 5)

### Completed

- **`docs/concepts/phase15_v4_plan.md`** (NEU, 746 Zeilen): execution-ready Plan.
  P1–P16 gelockt mit Begründung je Zeile · §2 selbst gemessene Fakten · §3 fünf Befunde ·
  §5 Contracts mit exakten Namen · §6 Schritt-Sequenz mit Verbatim-Ankern ·
  §7 Akzeptanz AK1–AK14 · §8 „Fehlgriffe, die wie andere Fehler aussehen" ·
  §9 vollständige „bei Ausführung verifizieren"-Liste · §10 Out-of-Scope ·
  §11 Operator-Aktionen. Commit `f98df68` (+ Folge-Commit mit den Korrekturen unten).
- **`docs/INDEX.md`**: Index-Zeile im selben Commit (P16).
- **Σ-Baseline selbst gemessen: 1703 grün**, per-Phase-Tabelle in Plan §2.1.
  Kommandoform verifiziert. Die Memory-Notiz mit den 2026-07-02-Baselines ist **stale**.
- **Live-DB read-only inventarisiert** (Plan §2.3/§2.4) — 8 Trades, 1902 Abstains
  (davon 1852 `research_empty`, **0** `veto`/`gate`), 5 von 1596 Snapshots mit Spread.
- **Fünf Befunde** (Plan §3): B1 Reward belohnt Verluste · B2 Clean-Entry-Bonus ist eine
  Konstante · B3 vier Live-Zeilen tragen noch die 120×-Vergiftung · B4 `GapRescue` (S4)
  hat nachweislich nie gelaufen und ist nicht verdrahtet · B5 `spread_at_entry_pct = 1.0`
  bei Trade 8 (unaufgeklärt, in §9).
- **Advisor-Review eingearbeitet** (2 Runden): Akzeptanzkriterien auf `AK*` umbenannt
  (kollidierten mit den Step-Buchstaben und mit dem „A6"-Gate), Gate überall voll
  ausgeschrieben, VETO-5-`rules`-Quelle als `ExecutionConfig.longterm_rules` festgelegt
  und gegen `vetos.py:23-31` + `config.py:30` verifiziert, D3 auf ein Operator-Tool in
  Phase 13 zusammengezogen (die Phase-8-Frage entfällt damit ganz).

### Nikinger-Entscheidungen dieser Session (2026-08-31)

| # | Frage | Entscheidung |
|---|---|---|
| 1 | Blöcke | **A + B + C** (nicht 15a Council) |
| 2 | A6 vs. Block B | **A6 zuerst**, Block B als spät gegateter Step |
| 3 | 15d Force-Trigger | **moot-by-absence** erklären und dokumentieren |
| 4 | Cross-Phase | **P2 + P4 + P5 + P6 + P7 + P13 + P14** freigegeben |
| 5 | Block B Schnitt | **Kalibrierung fixen**, die zwei NULL-Spalten dokumentiert leer lassen |
| 6 | Score-Historie | **Score auf 50 zurücksetzen**, alte Deltas bleiben stehen |
| 7 | Block C Akzeptanz | Extraktion + Validierung, Promotion hinter Flag, **Akzeptanz = „verweigert korrekt bei n=8"** |
| 8 | Erbstücke | Quellen-Vertrauens-Lock + `phase13_14_15.svg` + **Pfad A** (nicht D15/D16) |
| 9 | Startblock | **Block A** (nicht Block D zuerst) — Nikinger 2026-08-31, nach dem Plan-Commit |
| 10 | Gate P7 | **A6 ist freigegeben** (Beobachtung autorisiert) — ⚠ freigegeben ≠ abgeschlossen, siehe unten |

### Next

**Startblock ist Block A** (Nikinger 2026-08-31). Erster Schritt: Plan §6 Step **A-1**
(Step-0-Ritual ausführen und protokollieren), dann **A-2** (Σ-Baseline, Erwartung 1703),
dann A-3 … A-6. Block D danach — er hängt auch nicht am Gate, ist aber nachgeordnet.

**Block B startet nicht.** Gate P7 ist **zu**.

### Gate-P7-Stand (gemessen 2026-08-31, nach der Nikinger-Freigabe)

Der Nikinger hat A6 **freigegeben** — das heißt: die Beobachtung ist autorisiert und der
Bot läuft dafür (PIDs 21184 / 21197 / 21207). Es heißt **nicht**, dass A6 abgeschlossen ist:

| geprüft | Ergebnis |
|---|---|
| OPEN-Trades in `trade_outcomes` | **0** — alle 8 Zeilen `status='CLOSED'` |
| neuester Trade | `id=11`, `2026-08-27T08:15:08Z`, geschlossen |
| `reward_pts` | 8 Zeilen, unverändert |

A6 braucht einen **OPEN-Trade mit IG-Lag** und danach 24 h Beobachtung. Beides ist noch
nicht passiert. **Gate P7 öffnet erst, wenn A6 als abgeschlossen gemeldet ist** — nicht
mit der Freigabe. Wer Block B vorher anfängt, macht die Messung wertlos (P7-Begründung).

### Open questions / blockers

- **Gate P7 ist der einzige harte Blocker** und weiterhin zu: wartet auf einen OPEN-Trade
  + 24 h. Erwarteter Live-Effekt: ≤ 5 CRITICALs in 24 h statt 6+ in 52 min;
  > 24 h ohne Auflösung = WARNING statt CRITICAL.
- **Push ist erledigt** — `origin/main` = `d1dd26b` (Nikinger, 2026-08-31), 0 ahead / 0 behind.
- Die vollständige Drift-Liste steht in **Plan §9** (8 Punkte). Was dort nicht steht,
  ist in der Plan-Session gegen Code oder Live-DB geprüft.
