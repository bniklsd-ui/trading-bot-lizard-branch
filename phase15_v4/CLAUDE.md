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
updated: 2026-08-31
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

### Next

**Block A und Block D können sofort starten** — sie hängen nicht am Gate P7.
Konkret der erste Schritt: Plan §6 Step **A-1** (Step-0-Ritual ausführen und protokollieren),
dann **A-2** (Σ-Baseline, Erwartung 1703).

**Block B startet nicht**, bevor das „Phase-12-Reconcile-Timing Live-Verify" (in
`phase7_reward/CLAUDE.md` „A6" genannt) abgeschlossen gemeldet ist — 24-h-Beobachtung am
laufenden Bot, wartet auf den nächsten OPEN-Trade.

### Open questions / blockers

- **Gate P7** ist der einzige harte Blocker: Operator-Aktion, wartet auf einen OPEN-Trade.
- **Push steht aus** — `git push origin main` ist Nikinger-Sache (Working-Style-Regel).
- Die vollständige Drift-Liste steht in **Plan §9** (7 Punkte). Was dort nicht steht,
  ist in der Plan-Session gegen Code oder Live-DB geprüft.
