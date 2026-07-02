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
| 7     | Reward/Punishment + Brain           | ✅ live-verifiziert (Demo, 2026-06-26) — `live_test.py` 5/5; 128 Unit-Tests ⁴ |
| 8     | Scheduler                           | 🟡 Code-complete + gemerged; **v1.5+v1.6+v1.7 gemerged (2026-07-02)** — 🎉 erster echter autonomer Trade platziert, Webui-Fix mockgrün; Live-Varietäts-Lauf läuft bewusst bis ~17:30 morgen weiter (Trade-Qualitäts-Daten), Doku-Flip auf ✅ noch offen ⁵ |
| 9     | V2 (Council, Handover, SQLite V2)   | Konzept fertig (Council standalone existiert)       |

¹ **Live-getestet ≠ profit-validiert.** Die Research-Pipeline läuft nachweislich
korrekt end-to-end (IG Demo + echter LLM-Call): korrekter Kontext, contract-valider
Pick oder sauberer Abstain, sicherer No-Trade auf jedem Fehlerpfad. **Ob der Bot
profitable Trades macht, ist unbekannt** — es wurden keine echten Trades platziert.
Das ist hier korrekt: Ausführung kommt erst in Phase 5, Edge/Profitabilität viel
später (Phase 7 + Live-Betrieb). „Die Logik funktioniert" ≠ „der Bot ist profitabel".

² **Live-verifiziert ≠ profit-validiert.** Der Phase-5-Execution-Pfad platziert und
schließt nachweislich korrekt: `live_test.py` (SELL-Seed, im Handelsfenster) öffnete
eine echte IG-Demo-Order (ACCEPTED) und schloss sie per Time-Stop → `RESULT: 4/4 passed`
(Gates → Sizing → 4 VETOs → place → monitor → close, end-to-end live, nicht nur in CI).
**Die Profitabilität ist unbekannt** — nur ein Trade, kein Edge gemessen. Edge/Outcome-
Anchoring ist Phase 7 + Live-Betrieb. Demo only, manueller Trigger (Scheduler = Phase 8).

³ **Live-verifiziert ≠ profit-validiert.** Der Phase-6-Debatte-Pfad läuft nachweislich
korrekt end-to-end: `phase6_debate/scripts/live_test.py` (IG Demo) fuhr die Debatte im
vollen Executor → 3 echte Bull/Bear/Judge-Calls → fail-closed ABSTAIN → `NO_TRADE` →
`debate_log.json` angehängt → `RESULT: 4/4 passed` (`build_executor` → injizierter
`debate_runner` → Gate-2↔3-Naht, end-to-end live). **Die Profitabilität ist unbekannt** —
ein ABSTAIN-Zyklus, keine echte Order durch die Debatte (der Order-/Monitor-Pfad selbst
ist in Phase 5 bereits live bewiesen); Edge/Outcome-Anchoring ist Phase 7 + Live-Betrieb.
AI **nur** für Bull/Bear-Argumente + Judge-Synthese; `confidence` gatet nichts. Demo only,
manueller Trigger (Scheduler = Phase 8).

⁴ **live-verifiziert ≠ profit-validiert.** Phase 7 (Reward/Brain) ist **live-verifiziert**
(2026-06-26): `phase7_reward/scripts/live_test.py` lief **5/5** gegen IG Demo — eine SELL-Order
wurde platziert → Time-Stop-Close → `trade_outcomes` CLOSED + `reward_pts` + `trade_lessons`
geschrieben, P&L **lag-frei aus dem Close-Confirm** aufgelöst (Live-Debug 13b/13c: IG-Demo bucht
`get_trade_history` erst nach Settlement → der Close-Confirm ist die intraday-P&L-Quelle).
**128 P7-Unit-Tests** grün (Regression P1 52 · P2 62 · P4 94 · P5 146 · P6 70). AI **nur** für die
Lesson-Extraktion (`reflect()`, ein Haiku-Call, best-effort); Confidence ist **observe-only und
gatet nichts** (keine VETO-Berührung — Instinct→VETO ist Phase 9f). ⚠ Nur **ein** Trade beweist den
Pfad, **nicht** die Profitabilität (Edge = Live-Betrieb). Demo only, manueller Trigger.

⁵ **Phase 8 (Scheduler) — code-complete, v1.5+v1.6+v1.7 nach `main` gemerged (2026-07-02),
autonomer Trade jetzt live bewiesen, aber Datensammlung + Breaker-Beweis laufen noch.**
„Scheduler" ist nur der Name; das Ziel ist die **autonome, unbeaufsichtigte Erzeugung echter
Demo-Trades** (der Datennachschub, auf den P9 gegatet ist). Der harte Pfad ist die **autonome
Kandidaten-Generierung** über echtes P4-Research (nie der manuelle Seed). **Keine neue AI** — reine
Mechanik: Daemon mit Marktzeiten-Phasen, Auto-Confirm (demo-only, fail-closed), Datei-Kill-Switch,
Tages-Loss-Breaker, Token-Budget, idempotenter Reconcile, read-mostly Web-UI. **Alle 12 Module
gebaut, 199 Unit-Tests grün.**

**v1.5 (gemergt 2026-07-02):** Universum von 1 auf 4 EUR-Instrumente erweitert (DAX/StoxxE50/
CAC40/IBEX35), Clamp/Floor unter Score 50 entkoppelt+relaxt, Lesson-Provenance-Filterung —
behob den Hauptblocker („der Bot abstained fast immer").

**v1.6 (gemergt 2026-07-02):** yFinance-Version-Pin-Drift toleriert (`^FCHI`/`^IBEX` bleiben im
Universum), per-Zyklus Observability-Log (`data/state/research_health.jsonl`) + Instrument-
Verification-Harness (`scripts/verify_instrument.py`) ergänzt, ein zweiter bis dahin unbemerkter
Prompt-Leak-Kanal gefixt (**„Cause A part 2"** — `context_builder` fütterte ungefilterte
Verifikations-Trade-Historie in die LLM-Abstain-Begründung; echte `provenance`-Spalte + Filter +
Archivierungs-Skript beheben es, live bestätigt). **🎉 Direktes Ergebnis, noch am selben Tag: der
erste echte autonome Trade** — DAX BUY (`deal_id=DIAAAAXW7U4AWAP`), echter P4-Pick → echte
P6-Debatte → TRADE-Entscheidung, ACCEPTED → vom Broker per SL/TP geschlossen. Der harte,
bisher unbewiesene Kern der Phase-8-Mission ist damit **mechanisch bewiesen**.

**v1.7 (gemergt 2026-07-02, noch am selben Tag):** der Trade deckte eine kleine, webui-only
Anzeige-Inkonsistenz auf (Trade-Zähler + Realized-P&L-Karte lagen hinter der DB zurück — **kein**
Sicherheitsproblem, DB/Broker/Loss-Breaker bestätigt korrekt und unberührt). Fix: `/api/status`
liest beide Werte jetzt aus der DB statt dem lagging State-Snapshot, mockgrün.

**⚠ Ehrlich weiterhin offen (bewusst, kein ✅-Flip):** der 2026-07-02-Trade beweist die Mechanik
eines einzelnen sauberen open→close, aber **nicht** Trade-*Qualität* über mehrere Zyklen, nicht
**tatsächlich auslösende** Safety-Breaker, nicht Mehr-Tage-Verhalten, nicht Edge/Profitabilität
(nie im Scope). Der Live-Varietäts-Lauf läuft deshalb **bewusst bis ~17:30 morgen** weiter — jetzt
mit dem v1.6-Observability-Log sichtbar —, um mehr Trade-Qualitäts-Daten zu sammeln, statt beim
ersten „er tradet" zu stoppen. Danach folgt Step 5b (Breaker-Fire-Run) und erst dann der finale
Doku-Flip. Details: `phase8_scheduler/CLAUDE.md` (Session-Journal, aktuellster Stand),
`phase8_scheduler/PHASE8_V1.6_HANDOVER.md` (v1.5-Kontext: `PHASE8_V1.5_HOTFIX_HANDOVER.md`),
`docs/concepts/phase8_v1.6_hotfix_plan.md`, `docs/concepts/phase8_v1.7_hotfix_plan.md`. Konzept:
`docs/concepts/phase8_scheduler_concept.md`.

Detaillierter Plan: [`ROADMAP.md`](./ROADMAP.md)
Architektur-Diagramm: [`docs/architecture/tradingbot_v2_architecture.svg`](./docs/architecture/tradingbot_v2_architecture.svg)
Komponenten-Übersicht: [`ARCHITECTURE.md`](./ARCHITECTURE.md)

---

## Kernkonzepte

**5-Gate Execution Pipeline** — Jeder Trade durchläuft fünf sequenzielle Code-Gates
(Time Window → Candidates → Constraints → Broker → Direction). Keine Gate-Logik wird
an AI delegiert.

**Hard VETO Cascade** — Vor jeder Order laufen vier deterministische VETOs in Python
(Spread ≥25%, Drift ≥50%, Momentum ≥0.5% gegen, Spread Guard). VETOs sind Code.

**Adversarial AI Core** — Bull/Bear/Judge Debatte (Claude Sonnet, 5 Runden) als
einzige AI-getriebene Entscheidungsinstanz für Richtung. Output wird Code-seitig
validiert bevor irgendeine Order entsteht.

**Dual State** — SQLite (persistent, historisch) + JSON State (operativ, TTL-basiert).
Trennung zwischen Lern-Daten und Laufzeit-Zustand.

**Reward/Punishment + Longterm Brain** — Nach jedem Trade-Close: Score-Update +
Lesson-Extraktion. Lessons fließen als Kontext in zukünftige Research-Sessions.

---

## Setup (für jede neue Maschine)

```bash
# 1. Ins Projektverzeichnis
cd ~/trading-bot

# 2. Python virtual environment
python3 -m venv .venv
source .venv/bin/activate         # macOS/Linux
# .venv\Scripts\activate          # Windows

# 3. Phase 1 dependencies
cd phase1_broker_wrapper
pip install -r requirements.txt

# 4. Credentials in OS keyring legen (für IG Demo)
python scripts/store_credential.py ig_demo_username
python scripts/store_credential.py ig_demo_password
python scripts/store_credential.py ig_demo_api_key
python scripts/store_credential.py ig_demo_account_id
python scripts/store_credential.py anthropic_api_key

# 5. Smoke test gegen Demo
python scripts/smoke_test.py --epic IX.D.DAX.IFMM.IP
```

**Credentials liegen NIE in Dateien.** Nur im OS-Keyring
(macOS Keychain / Windows Credential Manager / Linux Secret Service).
Siehe [`CLAUDE.md`](./CLAUDE.md) — Abschnitt "Hard Rules".

---

## Arbeitsweise: Planung vs. Implementierung

| Wo                       | Was                                                                 |
|--------------------------|---------------------------------------------------------------------|
| **Claude (Browser/Web)** | Konzeption, Sollkonzepte, README/Doku, Architektur, Council-Sessions |
| **Claude Code (CLI)**    | Implementierung, Debugging, Tests, Refactoring, lokales Ausführen   |

Jede Phase beginnt mit einer **Konzept-Session in Claude (Browser)**. Output: ein
Markdown-Dokument in `docs/concepts/phaseN_*.md`. Erst danach wechselt die Arbeit zu
**Claude Code** mit Verweis auf dieses Konzept-Dokument.

---

## Außerhalb des Repos

Gehört zum Projekt, liegt aber NICHT im Repository:

- **OS Keyring Einträge** — alle Broker-Credentials
- **The Council Artifacts** — `the_council.jsx`, `council_architecture.jsx`
  (laufen als React-Artifacts im Claude.ai Browser-Interface)

---

## Lizenz

Privates Projekt. Nicht für externe Verwendung.
