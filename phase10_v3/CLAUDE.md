---
status: live
purpose: ACTIVE phase head — V3: Abstain-/No-Trade-Lessons echt auf main + Persistenz-Reform (Regime-Snapshots, Decision-Context) + Paper-Trades; Steps 0–3 (docs-only) done, Steps 4–11 gated on weekend windows
read-when: working in phase10_v3/ — read this head + its newest Session-stopped block first
detail: L2
up: ../CLAUDE.md
down:
  - ../docs/concepts/phase10_v3_plan.md   # full execution-ready plan (L3, ausführungsreif)
  - ../docs/concepts/PHASE10_V3_KICKOFF_HANDOVER.md   # kickoff handover from M1 into V3 (L3)
  - ../meta_m1_harness/specs/S1.md   # ... S7.md — Abstain-Lessons Bauplan-Specs (L3, zweifach real durchgebaut)
updated: 2026-07-10
---
# CLAUDE.md — Phase 10 (V3): Abstain-Lessons + Persistenz-Reform + Paper-Trades (`phase10_v3/`)

> Der Bot wird lernfähig aus seinen eigenen Abstains — mit den Daten, die da sind. Kein
> Research-Layer-Umbau, kein Broker-Wrapper-Umbau (spätere Phase). **Quelle der Wahrheit ist
> der Code, nicht dieses Dokument.** Vollständiger Plan: `../docs/concepts/phase10_v3_plan.md`.
> Kickoff-Kontext: `../docs/concepts/PHASE10_V3_KICKOFF_HANDOVER.md`.

## Mission (zuerst lesen)

Drei Blöcke, sequenziert (§1 des Plans):
1. **Step 0 (docs-only, Fr):** Phasen-Skeleton + Housekeeping + Datenanalyse +
   Contract-Verifikation — **dieser Commit-Satz**.
2. **Block A (Bot-berührend, Wochenende 1):** Abstain-/No-Trade-Lessons echt — Migration 005,
   `AbstainStore`, Classifier, `reflect_abstain`, Sink-Naht am P5-Executor, Wiring im P8-Runner.
3. **Block B (Bot-berührend, Wochenende 2):** Persistenz-Reform (`market_regime_snapshots` +
   `decision_context`, observe-only `regime_tag`) + Paper-Trades (Both-Sides-Shadow-Tracking,
   optionaler Council-Paper-Call hinter Flag).

Block C (UI) ist **nicht Teil dieses Plans** — geparkt, siehe Plan §13.

## Bauprinzip (Projekt-Kernprinzip, unverändert)

„So wenig AI wie möglich, so viel AI wie nötig." Genau **zwei** AI-Nähte in dieser Phase, beide
best-effort, beide triggern nie eine Order: `reflect_abstain` (Haiku, Tages-Cap) und der
optionale Council-Paper-Call (Flag default AUS, Cap 3/Tag, Output nur in `paper_trades`).
Klassifizierung, Persistenz, Paper-Auflösung, Regime-Features = deterministischer Code. VETOs/
Gates unantastbar, keine AI-Order-Triggerung — siehe Root-`CLAUDE.md` Hard Rules.

## Scope

- **DRIN:** `abstain_lessons/` (Store, Classifier, `reflect_abstain`, Sink, Paper-Modul,
  Report-Script), `market_context/` (Regime-Features, Writer, Decision-Context), Migration
  `005_v3_learning.sql`, additive Nähte an P5-Executor (`abstain_sink`, `context_recorder`) und
  P8-Runner (Config-Keys, Wiring, Tracker-Tick), S6-Flag am P4-Prompt-Builder (default OFF).
- **NICHT DRIN:** Research-Layer-Umbau, Broker-Wrapper-Umbau, `lesson_embeddings`,
  Regime-*Nutzung* (Floor/Directions-Modulation), UI (Block C), S6-Aktivierung (eigener
  Operator-Schritt nach Lesson-Review), M2 (geparkt, kein V3-Blocker).

## Modul-Tree (geplant — Verzeichnisse entstehen erst mit Block A/B, WE 1/2)

```
phase10_v3/
├── CLAUDE.md                                  ← dieser Kopf
├── STEP0_DATA_ANALYSIS_2026-07-10.md          ← Step 2 Output (dated)
├── abstain_lessons/                            (WE 1) models.py, exceptions.py, classifier.py,
│                                                reflect.py, sink.py, store.py, paper.py,
│                                                paper_store.py
├── market_context/                             (WE 2) models.py, exceptions.py, regime.py,
│                                                writer.py
├── scripts/                                    (WE 1) abstain_report.py
└── tests/                                      (WE 1/2)
```

## Arbeitsteilung (nicht verhandelbar)

Bot-berührende Steps **nur am Wochenende** (Markt zu, Bot steht). **Wochentags nur
docs-only/read-only** — read-only auf `data/` (SQLite via `mode=ro`-URI), keine Migration, kein
Scheduler-Restart, keine `live_test.py`. Details + volle Decision-Tabelle (V3-D1…D10):
`../docs/concepts/phase10_v3_plan.md` §0.

## Session stopped

_(wird am Ende der heutigen Session befüllt)_
