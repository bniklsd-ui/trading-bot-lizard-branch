---
status: live
purpose: Meta-Phase M1 head — Harness-Unabhängigkeit (Build-Front). Vorregistrierter Bake-off
  Claude Code vs. OpenCode + kalter P4/P6-Provider-Fallback. Orthogonal zum funktionalen Strang.
read-when: Arbeit an M1 — read this head + newest Session-stopped block first
detail: L2
up: ../docs/INDEX.md
down:
  - ../docs/concepts/meta_m1_harness_plan.md          # ausführungsreifer Plan (L3, Quelle der Schritte)
  - ../docs/concepts/meta_phase_unabhaengigkeit_konzept.md   # Hypothese/Theorie-Dokument (L3)
  - ./META_M1_PREREGISTRATION.md                      # Δ/P/K/E/M gelockt (Step 2)
updated: 2026-07-08
---

# Meta-Phase M1 — Harness-Unabhängigkeit — Claude Code context

## Project

Eine vorregistrierte Messung, ob der Bot-Code mit einem offenen Harness (OpenCode) statt
Claude Code gebaut werden kann — plus, unabhängig vom Ausgang, zwei Feuerlöscher: (a) ein
harness-neutraler Kontext-Einstieg (`AGENTS.md`), (b) ein getesteter, **kalter**
provider-agnostischer LLM-Fallback für P4/P6. **Kein Bot-Feature. Kein Umbau der Live-Pfade.**
Der Phase-9-Live-Test bleibt vollständig unberührt.

Eigener Meta-Strang „M" (orthogonal zur funktionalen Roadmap-Nummerierung 1–11), hochzählbar
(M2, M3, …). Voller Plan (Steps 0–10, Decisions M1-D1…D13): `meta_m1_harness_plan.md`. Volle
Hypothese/Theorie: `meta_phase_unabhaengigkeit_konzept.md`.

**⚠ Vorab bekannt (kein Bug):** mit den vorregistrierten Werten gilt E = 73,50 € < M = 120 € —
die Migrationsentscheidung ist bereits determiniert (KEINE Migration), unabhängig vom
Messergebnis. Der Bake-off läuft trotzdem voll durch — Zweck ist der Feuerlöscher-Test des
Build-Pfads, nicht Entscheidungsinput.

## Module-Tree (wächst mit den Steps)

```
meta_m1_harness/
├── CLAUDE.md                      ← dieser Kopf
├── META_M1_PREREGISTRATION.md     ← Step 2 (Δ/P/K/E/M gelockt, vor jedem Trial committet)
├── specs/                         ← Step 3 (S0–S7, self-contained Trial-Prompts)
├── bakeoff/                       ← Step 4 (harness_bakeoff.py, analyze.py, preamble.txt)
├── tests/                         ← Step 4 (mocked, kein Subprocess/Netz)
└── results/                       ← Step 7+ (trials.jsonl, META_M1_RESULTS.md, META_M1_DECISION.md)
```

## Status

🔄 Steps 0–4 in Arbeit (docs + Instrument, kein Fork/Operator-Prereq nötig). Steps 5–10
(Fork, OpenCode-Install, 20-Trial-Messlauf, Ergebnisse, `AGENTS.md`, P4/P6-Kalt-Fallback)
gegatet auf Nikinger-Operator-Aktion (Fork anlegen, OpenCode installieren, separater
Bake-off-API-Key) — eigener Plan, sobald diese Prerequisites stehen.

## Session stopped — <offen>

Wird am Ende dieser Session befüllt (Rotationsregel: genau ein Block pro Phasen-CLAUDE.md).
