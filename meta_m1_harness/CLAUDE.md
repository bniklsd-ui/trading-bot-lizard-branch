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
  - ./SESSIONS_ARCHIVE.md                             # ältere Session-stopped-Blöcke (L3)
updated: 2026-07-09
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
└── results/                       ← Step 7+ ✅ (trials.jsonl, META_M1_RESULTS.md, META_M1_DECISION.md)
```

## Status

✅ **Steps 0–8 fertig.** Skeleton, Legacy-Grep, Preregistration, Specs, Runner+Tests,
Referenz-Build S1–S7 im Fork (Steps 0–6); der gemessene Bake-off, 20/20 Trials, kein
Budget-/Isolations-Zwischenfall (Step 7, Nikinger-ausgeführt 2026-07-09); Auswertung +
Entscheidung dokumentiert in [`META_M1_RESULTS.md`](./META_M1_RESULTS.md) +
[`META_M1_DECISION.md`](./META_M1_DECISION.md) (Step 8). `meta-m1-harness` per Fast-Forward
in `phase9-v2-foundation` gemergt; aktiver Branch **`meta_working`**. Fork lebt unter
`~/bakeoff/trading-bot-fork`, `base-0`…`base-7` getaggt (Keyring neutralisiert).

**Ergebnis (Details in `META_M1_DECISION.md`): keine Migration** — determiniert bereits vor
der Messung (E=73,50€ < M=120€), jetzt zusätzlich durch die Messung selbst bestätigt: `gate_pass_rate`
90% vs. 90% (Gap = 0,00 pp, "not distinguishable" per Rausch-Regel), beide Harnesse mit genau
einem Fehlschlag von 10 (auf S1, gleiche Root Cause, siehe `META_M1_RESULTS.md`). Der
Feuerlöscher-Zweck ist damit erfüllt: im Zwangsfall ist OpenCode + Sonnet 5 auf diesem Repo ein
belastbarer Fallback-Build-Pfad, nicht nur eine Theorie — auch der Kontext-Portabilitäts-Annex
(M1-D11, hat OpenCode die `CLAUDE.md`-Navigation befolgt?) fiel positiv aus (zitierte Beispiele
in `META_M1_RESULTS.md`).

**Offen: Steps 9–10** (`AGENTS.md`, P4/P6-Kalt-Fallback) — orthogonal zu dieser Entscheidung,
nicht davon gegatet. Noch nicht begonnen.

## Session stopped — 2026-07-09 (Step 7 Messlauf komplett + Step 8 Auswertung: keine Migration, Gap=0pp)

**Vorherige Session** (Steps 0–6 + der erste Isolationsbefund): [SESSIONS_ARCHIVE.md](./SESSIONS_ARCHIVE.md).

### Completed
- **Nikinger hat den vereinbarten S0-Retry selbst ausgeführt** (`--steps S0 --harness
  claude_code,opencode --repeats 1`, `results/trials.jsonl` + `results/logs/` neu
  hinzugekommen, ausgewertet diese Session). **Isolationsfix bestätigt gegen einen echten
  Lauf:** kein Live-Repo-Escape — `git status` im Live-Repo nach dem Lauf sauber, und
  OpenCodes eigener `git status --short` im Trial-Log zeigt `?? phase10_v3/` korrekt **im
  Fork** (`~/bakeoff/trading-bot-fork`), nicht hier. `opencode`-Trial: `gate_passed=true`,
  4 Dateien (`smoke.py`, `tests/test_smoke.py`, zwei `__init__.py` — vom Agenten selbst
  begründet als für den Package-Import nötig, spec-konform: "kein `__init__.py` über das
  hinaus, was `phase10_v3/` als importierbares Paket braucht"). Damit ist der offene Punkt aus
  der letzten Session ("Fix ungetestet gegen echten Lauf") geschlossen.
- **Nebenbefund, kein Bug — der unabhängige Gate-Check tat genau seinen Job:** derselbe
  `claude_code`-Trial dieser Runde self-reportete "Gate command passes" im Ergebnistext, aber
  der Harness' eigener, unabhängiger Gate-Check widersprach: `gate_passed=false`,
  `files_changed=2` (nur `smoke.py` + `test_smoke.py`, kein `__init__.py` — der Agent hatte
  angenommen, "pytest's rootdir insertion" mache den Import auch ohne `__init__.py` auflösbar,
  was der frische Gate-Subprocess in der Praxis widerlegte). Genau das ist der Zweck des
  Gate-Checks als unabhängige Quelle statt Vertrauen auf Modell-Selbstauskunft (S0 ist laut
  Spec "ungemessen" — kein M1-Blocker, aber ein reales Beispiel, warum `gate_passed` nie aus
  dem Harness-Output selbst geparst werden sollte).
- **Budget-Blocker gefunden und noch in derselben Session behoben:** M1-D6 (Plan, gelockt)
  setzt den Bake-off-Hard-Cap auf 50 €. Reale Kosten der bisherigen 5 gemessenen S0-Trials
  (`usage_tokens` gesetzt) summieren sich auf ≈ 1,10 € — aber S0 ist der triviale
  Zwei-Datei-Smoke-Test (44 Zeilen Spec). S1–S5 sind laut Referenz-Build (Step 6, Fork)
  spürbar größer (62–76 Zeilen Spec je Datei, u.a. S5 = Cross-File-Wiring in
  `phase5_execution/`, "der härteste Trial" laut Archiv) und die geplante Matrix ist 5 Specs
  × 2 Repeats × 2 Harnesse = **20 Trials**. Bei einem anfänglich gemeldeten Kontostand von nur
  ~10 € hätte das reale Guthaben nicht für die volle Matrix gereicht (der Code-seitige
  50-€-Cap hätte dabei nie gegriffen, bevor die Anthropic-API selbst mit Insufficient-Credit
  mitten in der Matrix abgebrochen wäre — unsauberer Abbruch statt sauberem Guard-Stop mit
  Teilreport). Surfaced statt selbst editiert (M1-D6 ist eine gelockte Plan-Entscheidung) —
  der Nikinger hat den Key noch in dieser Session auf **$54,03** aufgeladen, womit M1-D6s
  50-€-Cap-Annahme wieder real hält. **Zusätzliche Session-Vereinbarung:** Claude Code führt
  keinen kostenpflichtigen Bake-off-Lauf mehr selbst aus — vorher immer per interaktiver Frage
  fragen und eine Kostenschätzung nennen (Memory-Erweiterung
  `feedback_live_testing.md`).

- **Step 7 — der gemessene Bake-off, komplett** (Nikinger-ausgeführt, wie vereinbart, zwei
  Kommandos): zuerst `--steps S1 --repeats 2` als Kalibrierung ($1,99 real — mittig in der
  vorab geschätzten $1–3-Spanne), dann `--steps S2,S3,S4,S5 --repeats 2` (~$9,30 laut
  Trial-Log-Summe für diesen zweiten Lauf; Nikinger meldete ~$7 Sonnet-5 + ~$0,08 Haiku vom
  Console-Dashboard — Differenz untersucht, kein Doppelzählungs-Bug in OpenCodes
  Pro-Step-Cost-Summierung gefunden [35 nicht-monotone Werte in einem Stichproben-Log, keine
  kumulative Neuzählung], vermutlich ein grob überschlagener Konsolen-Blick; Haiku-Betrag
  verifiziert **nicht** in irgendeiner Trial-eigenen Kostenrechnung versteckt — beide
  Harness-Configs nennen nirgends ein Haiku-Modell, alle "haiku"-Treffer in den Logs sind
  Prosa/Docstring-Inhalt (Zitate aus `phase7_reward`s echtem Haiku-`reflect()`), keine
  Live-Calls. Details + volle Zahlen: `META_M1_RESULTS.md`). **20/20 Trials real gelaufen,
  kein Budget-Stopp, kein Crash, keine Live-Repo-Kontamination** (vor und nach jedem Batch per
  `git status --porcelain` verifiziert, Fork-Tags/HEAD unverändert).
- **S1s gemischtes Ergebnis (dieser Sessions vorheriger Befund) hat sich NICHT wiederholt:**
  S2–S5 liefen 16/16 grün, beide Harnesse. Beide Gesamt-Fehlschläge (1 von 10 je Harness)
  liegen exakt auf S1, unabhängig reproduziert mit derselben Root Cause (bare `pytest` im
  Gate-Kommando fügt kein Repo-Root zu `sys.path` hinzu, abhängig vom Agenten-Judgement zu
  `__init__.py`-Markern) — bewusst NICHT als Gate-Command-Bug behandelt (siehe
  `META_M1_RESULTS.md`), da der Gate-Befehl wörtlich der Spec-Text ist, den jeder Agent sieht.
- **Step 8 — Auswertung + Entscheidung, komplett:** [`META_M1_RESULTS.md`](./META_M1_RESULTS.md)
  (Zahlen, Rausch-Check, Validity-Notes, Portabilitäts-Annex mit zitierten Beispielen — S4 las
  `phase7_reward/CLAUDE.md` für das Haiku-`reflect()`-Vorbild, S5 las
  `phase5_execution/CLAUDE.md` für die Gate/VETO-Struktur, S2 las gar nichts, weil die
  self-contained Spec ausreichte) + [`META_M1_DECISION.md`](./META_M1_DECISION.md) (Regel
  wörtlich angewandt: Gap 0,00 pp ≤ Δ 10 pp = TRUE, aber E 73,50€ ≥ M 120€ = FALSE →
  **keine Migration**, Feuerlöscher-Befund dokumentiert).

### Next
- **Steps 9–10** (`AGENTS.md`, P4/P6-Kalt-Fallback, §11–§12 im Plan) sind der verbleibende
  M1-Scope — noch nicht begonnen, orthogonal zur jetzt geschlossenen Migrationsfrage.
- Branch `meta_working` ist der aktive Arbeits-Branch. Alle Code-Fixes + Doku-Updates dieser
  und der Vorsession, plus `results/trials.jsonl` (**Korrektur zur vorherigen Session-Notiz:**
  Plan §9 verlangt explizit "`results/trials.jsonl` ... ins Haupt-Repo kopieren + committen" —
  die frühere Einordnung als "bewusst uncommittete Rohdaten" war falsch für die
  Preregistration-Trials und wird mit diesem Commit korrigiert), sind jetzt committet
  (Nikinger-Entscheidung 2026-07-09: "seems fine").
- `results/logs/*.log` bleiben bewusst uncommitted (volle Agenten-Transkripte, teils >400KB,
  kein vom Plan benanntes Artefakt — nur `results/trials.jsonl` ist es) — bereits durch die
  bestehende generische `logs/`-Regel in `.gitignore` (Zeile 134) abgedeckt, kein neuer Eintrag
  nötig (per `git check-ignore -v` verifiziert).

### Open questions / blockers
- Kein Blocker mehr — M1s Kernfrage (Migration ja/nein) ist beantwortet und dokumentiert.
  Nächster Schritt ist reine Fortsetzung (Steps 9–10) oder Commit, beides Nikinger-Entscheidung.
- `V2-Baseline-Auswertung` (echter Trade + Variety-These) bleibt offen, orthogonal, kein
  M1-Blocker (Merker in ROADMAP §Phase 9 hinterlegt).
