---
status: live
purpose: Human-facing overview + machine setup (venv, keyring credentials, smoke test)
read-when: onboarding or setting up a new machine
read-when-extra: status snapshot — re-read after any phase closeout
detail: L2
up: CLAUDE.md
updated: 2026-09-01
---
# Trading Bot

A multi-phase, AI-augmented CFD trading bot for the DAX.
Primary broker: IG Markets (EUR account). Multi-broker abstraction in place.

> **Bauprinzip:** So wenig AI wie möglich, so viel AI wie nötig.
> Code macht alles was Code kann. AI trifft nur Entscheidungen die genuines
> Urteilsvermögen erfordern (Richtung, Debatte, Lesson, Council-Evaluation).

---

## Status

| Phase | Komponente                          | Status                                              |
|-------|-------------------------------------|-----------------------------------------------------|
| 1     | Broker API Wrapper                  | ✅ Abgeschlossen (live-verifiziert, Demo)            |
| 2     | Persistenz (SQLite + JSON)          | ✅ Abgeschlossen (live-verifiziert, Demo)            |
| 3     | External Data (yFinance)            | ✅ Abgeschlossen (live-verifiziert, ^GDAXI)          |
| 4     | research.py + LLM (`turbo_*` = legacy) | ✅ Abgeschlossen — live-**getestet** (Logik), noch nicht profit-validiert ¹ |
| 5     | ig_bot.py Gates 1–5 + 4 VETOs + place/monitor/close | ✅ Abgeschlossen — live-**verifiziert** (Order-/Monitor-Pfad, Demo), noch nicht profit-validiert ² |
| 6     | Bull/Bear/Judge Debate              | ✅ Abgeschlossen — live-**verifiziert** (Debatte-Pfad, Demo), noch nicht profit-validiert ³ |
| 7     | Reward/Punishment + Brain           | ✅ live-verifiziert (Demo, 2026-06-26) — `live_test.py` 5/5; 142 Unit-Tests ⁴ |
| 8     | Scheduler                           | ✅ **live-verifiziert (2026-07-03)** — zwei autonome Trades + ein tatsächlich auslösender Safety-Breaker (Token-Budget) live bewiesen, noch nicht profit-validiert ⁵ |
| 9     | V2 — Foundation (autonome Epic-Research + Daten-Zuverlässigkeit) | 🔄 in execution — V2a end-to-end bewiesen 2026-07-07 (erster DB-Universum-Pick: CAC); V2b-Teile offen, in Wartestellung seit Phase-12-Notbremse (2026-08-11) ⁶ |
| 10    | V3 — Persistenz-Reform + No-Trade-Lessons + Paper-Pipeline | ✅ **abgeschlossen (Closeout 2026-08-25)** — Block A + Block B live auf `main`; Council-Paper-Call ✅ gebaut, default `False`, in mind Phase 15 ⁷ |
| 11    | V3-Fortsetzung: Funnel-/Mess-Fixes (aus Datenwoche-2-Review) | 🛑 **DEFERRED (Notbremse, 2026-08-11)** — drei Datenwochen an drei Infrastruktur-Ausfällen gescheitert, nie an der Messung; die gemeinsame Wurzel (das **Datenfundament**) ist wichtiger als die Phase |
| 12    | Datenfundament (Registry + BarService + Bar-Archiv + Recorder) | ✅ **abgeschlossen (Closeout 2026-08-25)** — Steps 0–8.5 auf `main`; P12.5 formal CLOSED + GESCHEITERT 2026-08-18, die fünf Code-Fixes bleiben korrekt; strukturelle Antwort in Phase 13+14 ⁸ |
| 13    | Live-Datenfundament (4-stufige Beschaffung, Lightstreamer live, Konsumenten fetchen nie) | ✅ **abgeschlossen (Closeout 2026-08-31, Session 18)** — Code-complete + Beweiswoche ausgewertet + Pfad-C-Entscheidung + Befund-Inversion ⁹ |
| 14    | Discovery-Then-Deterministic (Quellen-Registry + Discovery-Daemon) | ✅ **abgeschlossen (Closeout 2026-08-31, Session 23)** — Akzeptanz A1–A8 grün; D5-Handover komplett freigegeben ¹⁰ |
| 15    | V4: Reward-Kalibrierung · Instinct-ECC · Quellen-Vertrauens-Lock | 🔄 **in execution seit 2026-09-01** — Block A endgültig ✅ (A-1..A-7 + P15-F), Block D endgültig ✅ (D-1..D-3); Block B hinter Gate P7, Block C nach B ¹¹ |

> **Repo-weit Σ:** **1714 grün** (Stand 2026-09-01, Phase-15-D3-Verifikation).
> **Detaillierter Plan:** [`ROADMAP.md`](./ROADMAP.md) (Phasen 9–15 + Cross-Cutting)
> **Architektur-Diagramme:** [`docs/architecture/`](./docs/architecture/) (Phase-12/13/14-Closeout-SVGs + das neue `phase13_14_15.svg` von Phase 15 Block D)
> **Komponenten-Übersicht:** [`ARCHITECTURE.md`](./ARCHITECTURE.md)
> **Doku-Index:** [`docs/INDEX.md`](./docs/INDEX.md)

---

## Footnotes (ehrliche Trennung: was bewiesen ist vs. was *nicht* bewiesen ist)

¹ **Live-getestet ≠ profit-validiert** (Phase 4 — research.py + LLM). Die Research-Pipeline
läuft nachweislich korrekt end-to-end (IG Demo + echter LLM-Call): korrekter Kontext,
contract-valider Pick oder sauberer Abstain, sicherer No-Trade auf jedem Fehlerpfad.
**Ob der Bot profitable Trades macht, ist unbekannt.** Ausführung kommt in Phase 5, Edge/
Profitabilität später (Phase 7 + Live-Betrieb). „Die Logik funktioniert" ≠ „der Bot ist
profitabel".

² **Live-verifiziert ≠ profit-validiert** (Phase 5 — ig_bot.py). Der Phase-5-Execution-Pfad
platziert und schließt nachweislich korrekt: `live_test.py` (SELL-Seed, im Handelsfenster)
öffnete eine echte IG-Demo-Order (ACCEPTED) und schloss sie per Time-Stop → `RESULT: 4/4
passed` (Gates → Sizing → 4 VETOs → place → monitor → close, end-to-end live, nicht nur
in CI). **Die Profitabilität ist unbekannt** — nur ein Trade, kein Edge gemessen. Demo
only, manueller Trigger (Scheduler = Phase 8).

³ **Live-verifiziert ≠ profit-validiert** (Phase 6 — Bull/Bear/Judge). Die Debatte läuft
nachweislich korrekt end-to-end: `phase6_debate/scripts/live_test.py` (IG Demo) fuhr die
Debatte im vollen Executor → 3 echte Bull/Bear/Judge-Calls → fail-closed ABSTAIN →
`NO_TRADE` → `debate_log.json` angehängt → `RESULT: 4/4 passed`. **Die Profitabilität ist
unbekannt** — ein ABSTAIN-Zyklus, keine echte Order durch die Debatte; Edge/Outcome-
Anchoring ist Phase 7 + Live-Betrieb. AI **nur** für Bull/Bear-Argumente + Judge-Synthese;
`confidence` gatet nichts. Demo only.

⁴ **live-verifiziert ≠ profit-validiert** (Phase 7 — Reward/Brain). Live-verifiziert
2026-06-26: `phase7_reward/scripts/live_test.py` lief **5/5** gegen IG Demo — eine
SELL-Order wurde platziert → Time-Stop-Close → `trade_outcomes` CLOSED + `reward_pts` +
`trade_lessons` geschrieben, P&L **lag-frei aus dem Close-Confirm** aufgelöst (IG-Demo
bucht `get_trade_history` erst nach Settlement). **142 P7-Unit-Tests** grün. AI **nur**
für die Lesson-Extraktion (`reflect()`, ein Haiku-Call, best-effort). ⚠ Nur **ein**
Trade beweist den Pfad, **nicht** die Profitabilität.

⁵ **Phase 8 (Scheduler) ✅ live-verifiziert (2026-07-03).** Der weiterlaufende Live-Test
lieferte einen **zweiten** net-new autonomen open→close **und** den ersten **tatsächlich
auslösenden** Safety-Breaker (Tages-Token-Budget, fail-closed, kein Crash). Beide zuletzt
offenen Beweis-Punkte geschlossen. „Scheduler" ist nur der Name; das Ziel ist die
**autonome, unbeaufsichtigte Erzeugung echter Demo-Trades** (Datennachschub für P9).
**Keine neue AI** — reine Mechanik. Alle 12 Module gebaut, 248 Unit-Tests grün.
Details: [`phase8_scheduler/CLAUDE.md`](./phase8_scheduler/CLAUDE.md),
[`phase8_scheduler/PHASE8_CLOSEOUT_HANDOVER.md`](./phase8_scheduler/PHASE8_CLOSEOUT_HANDOVER.md),
[`docs/architecture/phase10_v3.svg`](./docs/architecture/phase10_v3.svg).

⁶ **Phase 9 (V2 — Foundation) — 🔄 in execution.** V2a end-to-end bewiesen 2026-07-07
~11:31 (erster DB-Universum-Pick: CAC über `instrument_universe` statt hand-kuratierte
`EXTENDED_UNIVERSE`-Tupel); V2b-Teile (Lightstreamer-Vollverdrahtung, Divergenz-Check
nach Live-Läufen, Step 8 mehrtägiger Autonomie-Lauf) **offen**, in Wartestellung seit
der Phase-12-Notbremse (2026-08-11) — die gemeinsame Wurzel aller drei gescheiterten
Datenwochen ist das Datenfundament, nicht die Messung. **87 P9-Tests** grün.
Plan: [`docs/concepts/phase9_v2_foundation_plan(1).md`](./docs/concepts/phase9_v2_foundation_plan(1).md),
Live-Ergebnisse: [`phase9_universe/PHASE9_V2_LIVE_RESULTS_HANDOVER.md`](./phase9_universe/PHASE9_V2_LIVE_RESULTS_HANDOVER.md).

⁷ **Phase 10 (V3) ✅ abgeschlossen (Closeout 2026-08-25).** Block A (Migration 005 +
`abstain_lessons/`, WE 1 2026-07-11) live auf main, **Monday-Restart-Beweis erbracht
2026-07-14** (66 echte `abstain_records`-Zeilen, 100 % `REASON_NO_CANDIDATES`); Block B
(`market_context/` + Paper-Pipeline, WE 2 2026-07-17) live auf main. **Council-Paper-Call
✅ gebaut, default `False`, bis auf weiteres in mind Phase 15** (Nikinger 2026-08-25).
Bugfix-Block 2026-07-25/31/08-08 (Wiring-`MINUTE_1`, Reflect-Schema, B1 point_value
40×-Oversizing, Allowance-Incident). **165 Phase-10-Tests grün, 25 phase10_v3-Commits
auf `origin/main`.** Closeout:
[`phase10_v3/PHASE10_CLOSEOUT_HANDOVER.md`](./phase10_v3/PHASE10_CLOSEOUT_HANDOVER.md).

⁸ **Phase 12 (Datenfundament) ✅ abgeschlossen (Closeout 2026-08-25).** Steps 0–8.5 auf
`main`; **P12.5 war 2026-08-18 formal CLOSED + GESCHEITERT** (IG-Budget-Kollaps am ersten
Handelstag: 4731/10 000 Wochenpunkte durch `get_window`s Vollfenster-Refetch verbrannt).
Die fünf Code-Fixes (U1/U2/U3/U5/EntscheidungB) bleiben korrekt; die **strukturelle
Antwort** steht in Phase 13+14 (Nikinger 2026-08-25). **Phase-12-Beweiswoche (Plan §7)
wird nicht wieder aufgenommen** — Phase-13-Beweiswoche läuft separat (Beweiswoche-Track).
**143 Phase-12-Tests grün, 18 Phase-12-Commits auf `origin/main`.** Closeout:
[`phase12_data_foundation/PHASE12_CLOSEOUT_HANDOVER.md`](./phase12_data_foundation/PHASE12_CLOSEOUT_HANDOVER.md),
P12.5-Analyse: [`phase12_data_foundation/PHASE12_5_CLOSEOUT_HANDOVER.md`](./phase12_data_foundation/PHASE12_5_CLOSEOUT_HANDOVER.md).

⁹ **Phase 13 (Live-Datenfundament) ✅ abgeschlossen (Closeout 2026-08-31, Session 18).**
Code-complete (Blöcke A + B + C, Stand 2026-08-22) + Beweiswoche ausgewertet
(Mini-Session 23, 14-Tage-source_delta-Diagnose, B1/B2/B3) + Pfad-C-Entscheidung
(Mini-Session 24, IG = S4-GapRescue-Pfad Default AUS, by-design) + Befund-Inversion
(kein Recorder-Mapping-Bug, Architektur-konform). **74 Phase-13-Tests grün, 53
`phase13:`-Commits auf `origin/main`**, Σ 1703 grün repo-weit. Phase-14 D5-Handover
**komplett freigegeben** (kein operativer Vorbehalt). Bild:
[`docs/architecture/phase13_live_data.svg`](./docs/architecture/phase13_live_data.svg).
Closeout: [`phase13_live_data/PHASE13_CLOSEOUT_HANDOVER.md`](./phase13_live_data/PHASE13_CLOSEOUT_HANDOVER.md).

¹⁰ **Phase 14 (Discovery-Then-Deterministic) ✅ abgeschlossen (Closeout 2026-08-31,
Session 23).** Code-complete (Blöcke 0/A/B/C/D, Akzeptanz A1–A8 grün seit Session 9) +
D5-Handover komplett freigegeben (Mini-Session 24 Pfad-C-Entscheidung) + 4 Mini-Pläne
P14-C/D/E/F abgeschlossen (Doc-Rotation-Hook `--strict` als Default). **61 Phase-14-Tests
grün, 54 `phase14:`-Commits auf `origin/main`**, Σ 1703 grün repo-weit. Bild:
[`docs/architecture/phase13_14_15.svg`](./docs/architecture/phase13_14_15.svg) (gemeinsames
Drei-Säulen-Bild P13+P14+P15, von Phase 15 Block D2 erstellt). Closeout:
[`phase14_discovery/PHASE14_CLOSEOUT_HANDOVER.md`](./phase14_discovery/PHASE14_CLOSEOUT_HANDOVER.md).

¹¹ **Phase 15 (V4: Reward-Kalibrierung · Instinct-ECC · Quellen-Vertrauens-Lock) 🔄 in
execution seit 2026-09-01.** Mission: **„bevor der Bot mehr lernt, muss das, was er lernt,
stimmen"**. Kern-Befund (live gemessen, Plan §3 B1): der Reward-Loop belohnt Verluste —
über die einzigen 8 geschlossenen Trades hat das Konto **−1 972,87 EUR** realisiert,
während der Lern-Score von 50 auf **78,72 stieg**. Ursache arithmetisch, nicht strukturell:
`RewardConfig.process_weight = 1.5` macht `max|process| = 3.75` größer als
`|outcome bei R = −1| = 2.0` — ein voller Stop-Out nettet damit **positiv** (+1,10
gemessen). Der Bug wurde am 2026-07-31 von `phase7_reward/reward/scorer.py:45-49`
vorhergesagt und als Phase-11 **H3** geparkt. **Block B ist H3.**

**Block-Stand:**
- **Block A** (Haushalt) ✅ endgültig abgeschlossen — A-1..A-7 + P15-F
- **Block D** (Erbstücke) ✅ endgültig abgeschlossen — D-1 (D5-H.-B geschlossen
  2026-09-01, `phase14_discovery/CLAUDE.md` Z. 310) + D-2 (`phase13_14_15.svg`) +
  D-3 (Pfad A Operator-Tool `RescueConfig` + `gap_rescue_operator.py` in Phase 13,
  **gebaut aber AUS** — kein SchedulerConfig-Leak, Doppel-Sperre
  `--enable-gap-rescue` UND `--apply`)
- **Block B** (Reward-Kalibrierung `process_weight` 1.5 → 0.5 + Score-Reset auf 50)
  ⏸ hinter **Gate P7** (Phase-12-Reconcile-Timing Live-Verify, wartet auf nächsten
  OPEN-Trade + 24-h-Beobachtung)
- **Block C** (Instinct-ECC) ⏸ nach B

**Akzeptanz-Status (Plan §7):** AK1–AK9 ✅ (A-Block), **AK10 ✅** (D-1), **AK11 ✅**
(D-2), **AK12 ✅** (D-3), **AK13 ✅** (Σ 1714 grün), **AK14 ✅** (D-2 INDEX-Zeile im
selben Commit). Plan:
[`docs/concepts/phase15_v4_plan.md`](./docs/concepts/phase15_v4_plan.md),
Phasenkopf: [`phase15_v4/CLAUDE.md`](./phase15_v4/CLAUDE.md).

---

## Kernkonzepte

**5-Gate Execution Pipeline** — Jeder Trade durchläuft fünf sequenzielle Code-Gates
(Time Window → Candidates → Constraints → Broker → Direction). Keine Gate-Logik wird
an AI delegiert.

**Hard VETO Cascade** — Vor jeder Order laufen vier deterministische VETOs in Python
(Spread ≥25 %, Drift ≥50 %, Momentum ≥0.5 % gegen, Spread Guard). VETOs sind Code.

**Adversarial AI Core** — Bull/Bear/Judge Debatte (Claude Sonnet, 5 Runden) als
einzige AI-getriebene Entscheidungsinstanz für Richtung. Output wird Code-seitig
validiert bevor irgendeine Order entsteht.

**Dual State** — SQLite (persistent, historisch) + JSON State (operativ, TTL-basiert).
Trennung zwischen Lern-Daten und Laufzeit-Zustand.

**Reward/Punishment + Longterm Brain** — Nach jedem Trade-Close: Score-Update +
Lesson-Extraktion. Lessons fließen als Kontext in zukünftige Research-Sessions.

**Beschaffung ≠ Verbrauch (Phase 13)** — Vier Stufen (S1 Lightstreamer → S2 yF-Recorder
→ S3 Capital.com → S4 GapRescue, Default AUS) schreiben in **ein** Archiv
(`data/bars.sqlite`); Verbraucher lesen nur das Archiv, **nie** eine Quelle direkt.
L1+L12 sind die strukturelle Garantie: `test_get_window_never_fetches` (ein
IG-Provider-Fake, der bei jedem Call wirft) beweist, dass der Tracker-Pfad nie kaufen
kann. Bild: [`docs/architecture/phase13_live_data.svg`](./docs/architecture/phase13_live_data.svg).

**Quellen-Vertrauens-Lock (Phase 14)** — `instrument_source_availability` (Migration
007, 38 Zeilen) ist die **einzige** Kreuzungs-Wahrheit (IG-Epic × Quelle × Auflösung +
quelleneigenes Symbol); Konsumenten lesen die Tabelle, nicht den Code. `EPIC_MAP` ist
Geschichte (`grep -rn "EPIC_MAP" phase13_live_data/ --include=*.py` ist leer).
**Verfügbarkeits-Modell, kein Aktualitäts-Modell:** `last_verified_utc` markiert die
letzte **Discovery-Ableitung** für das Tripel, **nicht** „Quelle hat gerade geliefert"
(D5-H.-B geschlossen 2026-09-01, Phase 15 Block D1).

**Reward-Score-Kalibrierung (Phase 15 in execution)** — der aktuelle Reward-Loop
belohnt Verluste (siehe ¹¹). Block B ändert `process_weight` von 1.5 auf 0.5, sodass
ein voller Stop-Out den Score tatsächlich **senkt** (AK5: für `r_multiple ≤ −1.0` gilt
`score_after < score_before`). Hinter Gate P7 (Live-Verify des Phase-12-Reconcile-
Timing-Fix).

---

## Setup (für jede neue Maschine)

```bash
# 1. Ins Projektverzeichnis
cd ~/trading-bot

# 2. Python virtual environment (Phase-1-Wurzel)
python3 -m venv phase1_broker_wrapper/.venv

# 3. Alle Phasen installierbar via dev_install.sh (Phase 14 P14-F Anbindung)
bash scripts/dev_install.sh

# 4. Credentials in OS keyring legen (für IG Demo + Anthropic)
python scripts/store_credential.py ig_demo_username
python scripts/store_credential.py ig_demo_password
python scripts/store_credential.py ig_demo_api_key
python scripts/store_credential.py ig_demo_account_id
python scripts/store_credential.py anthropic_api_key

# 5. Operator-Smoke gegen Demo (Phase 1 End-to-End)
python scripts/smoke_test.py --epic IX.D.DAX.IFMM.IP
```

**Credentials liegen NIE in Dateien.** Nur im OS-Keyring (macOS Keychain /
Windows Credential Manager / Linux Secret Service). Siehe
[`CLAUDE.md`](./CLAUDE.md) — Hard Rule 1.

---

## Arbeitsweise: Planung vs. Implementierung

| Wo                       | Was                                                                 |
|--------------------------|---------------------------------------------------------------------|
| **Claude (Browser/Web)** | Konzeption, Sollkonzepte, README/Doku, Architektur, Council-Sessions |
| **Claude Code (CLI)**    | Implementierung, Debugging, Tests, Refactoring, lokales Ausführen   |

Jede Phase beginnt mit einer **Konzept-Session in Claude (Browser)**. Output: ein
Markdown-Dokument in `docs/concepts/phaseN_*.md`. Erst danach wechselt die Arbeit zu
**Claude Code** mit Verweis auf dieses Konzept-Dokument. Phase-Pläne werden in der
Browser-Session **gelockt** (P1–P16, D1–D20, L1–L18 etc.) — die Exec-Session
implementiert gegen den Plan und darf Decisions nicht ohne Sichtung des Nikinger
aufweichen.

**Smoke + Real-Network-Tests** macht der **Nikinger selbst** — die Exec-Session
schreibt und prüft Tests lokal (mocked HTTP), aber Live-Auth + Live-Order +
echte LLM-Calls sind Operator-Aktion (Plan §11).

---

## Meta-Strang M1 — Harness-Unabhängigkeit ✅ CLOSED (2026-07-09)

Orthogonal zur Phasen-Nummerierung 1–15 (kein Bot-Feature, kein Umbau der
Live-Pfade). Vorregistrierte Messung Claude Code vs. OpenCode (20 Trials,
gleiches Modell/Effort): `gate_pass_rate` 90 %/90 %, Gap 0,00 pp — **keine
Migration** (war schon vor der Messung determiniert, E=73,50 € < M=120 €; die
Messung bestätigt es zusätzlich). Zwei Feuerlöscher zusätzlich gebaut: ein
harness-neutraler Einstieg ([`AGENTS.md`](./AGENTS.md)) und ein getesteter, **kalter**
provider-agnostischer LLM-Fallback für Phase 4/6 (`OpenAICompatLLMClient`,
OpenRouter, Operator-Smoke-PASSed) — nirgends live verdrahtet. Details:
[`meta_m1_harness/CLAUDE.md`](./meta_m1_harness/CLAUDE.md),
[`meta_m1_harness/META_M1_PREREGISTRATION.md`](./meta_m1_harness/META_M1_PREREGISTRATION.md),
[`meta_m1_harness/META_M1_RESULTS.md`](./meta_m1_harness/META_M1_RESULTS.md),
[`meta_m1_harness/META_M1_DECISION.md`](./meta_m1_harness/META_M1_DECISION.md).
Optionaler nächster Schritt (ungelockt):
[`meta_m1_harness/META_M1_CLOSEOUT_HANDOVER.md`](./meta_m1_harness/META_M1_CLOSEOUT_HANDOVER.md).

---

## Außerhalb des Repos

Gehört zum Projekt, liegt aber NICHT im Repository:

- **OS Keyring Einträge** — alle Broker-Credentials
- **The Council Artifacts** — `the_council.jsx`, `council_architecture.jsx`
  (laufen als React-Artifacts im Claude.ai Browser-Interface)

---

## Lizenz

Privates Projekt. Nicht für externe Verwendung.
