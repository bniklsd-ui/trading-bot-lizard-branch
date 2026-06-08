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
| 4     | research.py + LLM (`turbo_*` = legacy) | ✅ Abgeschlossen (live-verifiziert, IG Demo + LLM) |
| 5     | ig_bot.py Gates 1–5 + pre_trade     | Nicht begonnen                                      |
| 6     | Bull/Bear/Judge Debate              | Nicht begonnen                                      |
| 7     | Reward/Punishment + Brain           | Nicht begonnen                                      |
| 8     | Scheduler                           | Nicht begonnen                                      |
| 9     | V2 (Council, Handover, SQLite V2)   | Konzept fertig (Council standalone existiert)       |

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
