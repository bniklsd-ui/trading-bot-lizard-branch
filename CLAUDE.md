---
status: live
purpose: Single source of truth for project rules, conventions, hard rules, and current phase status
read-when: always — auto-loaded at session start; everything else hangs off this file
detail: L2
up: docs/INDEX.md
down:
  - docs/INDEX.md          # L0 map of every project doc
  - ROADMAP.md
  - ARCHITECTURE.md
  - phase9_universe/CLAUDE.md   # active phase head
updated: 2026-09-05
---
# CLAUDE.md — Project Instructions

> Read this file before doing anything in this repository.
> It is the single source of truth for project rules, conventions, and current state.

---

## What this project is

A multi-phase, AI-augmented CFD trading bot for the DAX.
Primary broker: IG Markets (EUR account). Multi-broker abstraction in place.

The bot is structured around a **5-Gate Execution Pipeline** with adversarial
AI-driven direction decisions (Bull/Bear/Judge debate) and a deterministic VETO
cascade.

Full architecture: `docs/architecture/tradingbot_v2_architecture.svg`
Build order: `ROADMAP.md`

---

## Core principle (read carefully)

**Bauprinzip:** So wenig AI wie möglich, so viel AI wie nötig.

**Code macht:**
- Alle API-Calls (GET, POST, DELETE)
- Authentication, Session-Handling, Token-Refresh
- Spread / Drift / Momentum / Sizing — alle Berechnungen
- VETO-Checks (alle vier sind Code, nicht AI)
- Gate-Logik (True/False Entscheidungen)
- Persistenz (SQLite Reads/Writes, JSON Reads/Writes)
- TTL-Verwaltung, Retry-Logik, Error-Handling, Normalisierungen

**AI macht NUR:**
- "Welcher Kandidat?" — Research LLM
- Bull/Bear/Judge Debatte (Richtungsentscheidung)
- Lesson-Extraktion nach Trade (Longterm Brain)
- Council-Evaluation (Strategieprüfung)
- **NICHTS sonst**

If you find yourself reaching for an LLM call to do data fetching, formatting,
filtering, validation, or any deterministic logic — STOP. Use code instead.

---

## Hard Rules (no exceptions)

1. **Never put credentials in files.** Not in `.env`, not in JSON, not in YAML,
   not anywhere on disk. Credentials live ONLY in the OS keyring
   (macOS Keychain / Windows Credential Manager / Linux Secret Service).
   Access via `broker_wrapper/credentials.py`.

2. **Never bypass VETOs.** If you find code that skips a VETO check "for testing"
   or "for now" — flag it loudly. VETOs are the difference between a working bot
   and a blown account.

3. **Never let AI output trigger an order directly.** Every AI output
   (Bull/Bear/Judge APPROVED, Research candidate selection) MUST pass through
   code-side validation before any order is placed. Hallucinations are a real
   risk and are mitigated structurally, not by trust.

4. **Never test against real money first.** All new code is exercised against
   the IG Demo account via `scripts/smoke_test.py` before being trusted with the
   live account. No exceptions.

5. **The Force Trigger must respect Daily PNL.** Per the architecture analysis,
   the manual override (`ig_bot_force_trigger`) should be **locked** when daily
   PNL is negative. Human override at moments of emotional vulnerability is the
   biggest identified risk.

6. **Output envelope is canonical.** Every broker adapter method returns an
   `Envelope` JSON object (see `broker_wrapper/envelope.py`). Do not deviate
   from this shape. Tests, CLI, FastAPI, and bot core all depend on it.

---

## Current state

> **🔄 2026-09-05 — Phase 16 (Freischaltung) ERÖFFNET (Plan-Session, Fable 5.1).** Plan
> [`docs/concepts/phase16_activation_plan.md`](./docs/concepts/phase16_activation_plan.md),
> Phasenkopf [`phase16_activation/CLAUDE.md`](./phase16_activation/CLAUDE.md). Neun selbst
> gemessene Löcher, drei davon legen den Bot heute lahm: **100 % Research-Abstain seit 08-31**
> (Trade-Historie ohne Zeitfenster), **Token-Budget täglich um 15:48 leer**, **Live-DB Schema v7 —
> Migrations 008/009 nie angewendet** (kein Produktions-Caller von `run_migrations()`; die
> „automatisch beim Restart"-Aussage im Absatz darunter ist **falsch**, Korrektur folgt in Plan
> Step A-3). Blöcke A Haushalt · B Substrat · C Research-Loop · D Freischaltung (alle vier Arme
> Default ON, Bridge, B3) · E vorregistrierter 2-Wochen-Autonomie-Test. Cross-Phase frei:
> P1/2/3/4/5/7/8/9/15 (P3 seit Runde 2). Exec-Modell: OpenCode / MiniMax M3.

> **✅ 2026-09-05 — Phase 15 (V4) ABGESCHLOSSEN (Session #13, MiniMax-M3-Exec).** Phase 15 (V4) ist
> seit Session #13 mit Closeout-Handover abgeschlossen ([`phase15_v4/PHASE15_CLOSEOUT_HANDOVER.md`](./phase15_v4/PHASE15_CLOSEOUT_HANDOVER.md),
> Bild [`docs/architecture/phase15_closeout.svg`](./docs/architecture/phase15_closeout.svg)).
> Alle 4 Blöcke ✅: A (Haushalt) endgültig (A-1..A-7 + P15-F) · B (Reward-Kalibrierung)
> **live-validiert** (Score 78,72 → 50,00 live 2026-09-03, AK5+AK6+AK13 grün) · C (Instinct-ECC)
> code-complete (C1 Migration 009 + C2 5 Module + C3 VETO 5 + C4 12 Tests, AK7+AK8+AK9 grün, heute
> bit-identical via leere `longterm_rules`) · D (Erbstücke) endgültig (D-1..D-3 + Folgefix
> Variante C). Σ **1843 grün repo-weit** (selbst nachgemessen 2026-09-05). **18 Commits gepusht**
> (Sessions #1-#9), **6 Commits lokal ahead** (Sessions #10-#13, Push-Freigabe steht aus). **Offen
> (alle nicht-Phase-15-Blocker, delegiert an Folge-Sessions):** (1) **Promotion-Bridge** — die
> Pipeline `list_instincts('validated')` → `promote_eligible` → `config.longterm_rules` existiert
> nicht (Plan §10 out-of-scope); (2) **Ledger-Restore** — 250 fälschlich gebuchte Rescue-Punkte
> aus dem 2026-09-03-Pfad-A-Scharfschaltungs-Bug-Lauf (`DELETE FROM source_spend WHERE
> kind='rescue'`, Nikinger-Aktion); (3) **Gate P7/A6** — Phase-12-Reconcile-Timing-Live-Verify
> wartet auf nächsten OPEN-Trade + 24 h (Backoff replay-verifiziert Mini-Session 26); (4)
> **Live-DB Migration 008+009** — **nicht automatisch**: kein Produktions-Caller von
> `run_migrations()` (korrigiert 2026-09-05, Phase-16-Plan §3 L3); Phase 16 B1 verdrahtet
> den Aufruf **nicht** im Daemon, sondern als **Schema-Floor** im Preflight (B1) +
> einmaligen Operator-Apply mit Backup (B2). Schema heute v7.

> 🟡 **Korrekturhinweis 2026-09-08 (Phase 16 Exec-Session #23, Doc-Drift-Repair):** drei
> Aussagen in den Phase-15-Offen-Items (Ledger-Restore 250 Punkte, Schema v7, 6 Commits
> pending Push) sind heute **positiv überholt** — Code/Repo/Git sind weiter als diese
> Status-Prosa. Belegt am 2026-09-08, in einer Mini-Session speziell zur Drift-Reparatur
> zusammengeführt (Working-style-Regel: *„Tested code > concept doc > README/status
> prose"*). Details siehe Phase-15-Closeout-Handover-Korrekturhinweis 2026-09-08
> (gleicher Tag, mit Quellen) + Phase-16-Session-#23-Block im aktiven Phasenkopf.
>
> - **D1 — Schema heute v9, nicht v7.** `SELECT MAX(version) FROM _schema_version` = 9.
>   `data/trading_bot.sqlite.instincts`-Tabelle existiert (0 Rows, `n_closed=8 <
>   instinct_n_min=50`). Backup `data/trading_bot.sqlite.bak-20260905-pre-mig009` (3,3 MB,
>   2026-09-05 20:28) ist die Pre-Migration-Rückfall-Option. Operator-Apply lief in
>   Phase-16-Session #3 (2026-09-05, Block B2). Die Phase-16-A-3-Korrektur (eine Zeile
>   höher) bleibt korrekt — es gibt **keinen** automatischen Apply im Daemon, der Apply
>   lief als Operator-Aktion.
> - **D2 — Ledger-Restore 250 Punkte erledigt.** `SELECT COUNT(*), SUM(points) FROM
>   source_spend WHERE kind='rescue'` = `0|0` (war `5|250`). Operator-Aktion ausgeführt
>   zwischen Phase-15-Closeout und 2026-09-08.
> - **D3 — Push-Freigabe 6 Commits erteilt.** `git rev-list --left-right --count
>   origin/main...HEAD` = `0 0`, `origin/main = 20a10c1` = HEAD, working tree clean.
>   Alle 6 Commits der Phase-16-Session #22 wurden vom Nikinger gepusht.
>
> **Bilanz:** Phase 15 bleibt ✅ abgeschlossen. Promotion-Bridge (Phase 16 D2 in Commit
> `bfab841` + Hotfixes #1–#3 in Sessions #14–#16) und Gate P7/A6 (Phase-12-Reconcile-
> Timing, wartet auf nächsten OPEN-Trade) sind die einzigen verbleibenden Phase-15-Folge-
> Punkte. Working-Style-Regel: *„On conflict, trust the code, fix the doc immediately,
> and leave a dated note in the doc that it was corrected against code"* — exakt das
> wurde hier umgesetzt; Phase-15-Handover + Phase-15-Phasenkopf + Phase-16-Phasenkopf
> tragen jetzt analoge datierte 🟡-Vermerke.

> 📦 **Doku-Hygiene (2026-07-03):** die volle Phase-1–8-Chronik, die vorher hier stand, ist
> **wortgleich, unverändert** ausgelagert nach
> [`docs/sessions/root_claude_md_phase_status_archive.md`](./docs/sessions/root_claude_md_phase_status_archive.md)
> (root `CLAUDE.md` war über der empfohlenen ~40KB-Grenze; reine Verschiebung, kein Umschreiben —
> gleiche Auditability-Regel wie bei `## Session stopped`-Blöcken). Neue Phase-Status-Updates gehören
> ab jetzt in die jeweilige Phasen-`CLAUDE.md`, nicht mehr hierher.
> **Update 2026-07-06:** dieses Prinzip ist jetzt repo-weit generalisiert — Doc-Layers-Konvention
> (L0-Index + Header-Cards + per-Phase `SESSIONS_ARCHIVE.md` + Rotationsregel), siehe
> [`docs/INDEX.md`](./docs/INDEX.md) und [`docs/DOC_LAYERS_CONVENTION.md`](./docs/DOC_LAYERS_CONVENTION.md).

> ✅ **2026-08-31 — Phase 13 + Phase 14 ABGESCHLOSSEN (Sessions 18 + 23).** Phase 13
> (Live-Datenfundament): Code-complete (Blöcke A + B + C) + Beweiswoche ausgewertet
> (Mini-Session 23, 14-Tage-source_delta-Diagnose, B1/B2/B3) + Pfad-C-Entscheidung
> (Mini-Session 24, IG = S4-GapRescue-Pfad Default AUS, by-design) + Befund-Inversion
> (kein Recorder-Mapping-Bug, Architektur-konform). Phase 14 (Discovery-Then-Deterministic):
> Code-complete (Blöcke 0/A/B/C/D) + Akzeptanz A1–A8 alle grün seit Session 9
> (2026-08-22) + D5-Handover komplett freigegeben (Mini-Session 24, Pfad-C-Entscheidung) +
> 4 Mini-Pläne P14-C/D/E/F abgeschlossen (Doc-Rotation-Hook `--strict` als Default,
> ARM-Pfad absolut, Daemon-Signal-Cap, Recorder-Sleep-Cap). **Beide Phasen haben formale
> Closeout-Handover-Dateien** (Phase-13: [`phase13_live_data/PHASE13_CLOSEOUT_HANDOVER.md`](./phase13_live_data/PHASE13_CLOSEOUT_HANDOVER.md),
> Session 18; Phase-14: [`phase14_discovery/PHASE14_CLOSEOUT_HANDOVER.md`](./phase14_discovery/PHASE14_CLOSEOUT_HANDOVER.md),
> Session 23). **Nächster Track = Phase 15 (V4: Council / Handover / Reward-Reform /
> Force-Trigger / Instinct-ECC)** — Material jetzt vollständig (7+ V4-Kandidaten),
> eigenständige Plan-Session. **Aktiver Live-Effekt:** Phase-7-Backoff (Mini-Session 26,
> 4 von 4 Backoff-Tests A2–A5 grün, Pre-Test bestätigt) wartet auf nächsten OPEN-Trade
> (heute 0 OPEN) für A6-Live-Verify (≤ 5 CRITICALs in 24 h statt 6+ in 52 min).

**Kompakter Stand pro Phase** (Details im Archiv oben oder in der jeweiligen Phasen-`CLAUDE.md`):

| Phase | Status |
|---|---|
| 1 — Broker Wrapper | ✅ Abgeschlossen, live-verifiziert |
| 2 — Persistenz | ✅ Abgeschlossen, live-verifiziert |
| 3 — External Data | ✅ Abgeschlossen, live-verifiziert |
| 4 — research.py + LLM | ✅ Abgeschlossen, live-getestet ≠ profit-validiert |
| 5 — ig_bot Gates 1–5 | ✅ Abgeschlossen, live-verifiziert ≠ profit-validiert |
| 6 — Bull/Bear/Judge Debatte | ✅ Abgeschlossen, live-verifiziert ≠ profit-validiert |
| 7 — Reward/Brain | ✅ live-verifiziert + gemerged (2026-06-26) |
| 8 — Scheduler | ✅ **live-verifiziert (2026-07-03)** — zwei autonome Trades + ein tatsächlich auslösender Safety-Breaker (Token-Budget), Nikinger-bestätigt. Details: `phase8_scheduler/CLAUDE.md` |
| 9 — V2: Foundation (autonome Epic-Research + Daten-Zuverlässigkeit) | 🔄 in Arbeit (Stand 2026-07-07) — Steps 1–6 + 7a ✅ (7b ohne Fix-Target), **Live-Baseline-Lauf seit 2026-07-06** (Tag 1: Pipeline bewiesen, 8 active/7 verified/0 quarantined, erster DB-Pick CAC; offen: Neustart-Pickup + Trade unter V2): [`phase9_universe/CLAUDE.md`](./phase9_universe/CLAUDE.md), [`phase9_universe/PHASE9_V2_LIVE_RESULTS_HANDOVER.md`](./phase9_universe/PHASE9_V2_LIVE_RESULTS_HANDOVER.md) |
| 10 — V3: Persistenz-Reform + No-Trade-Lessons + Paper-Trades | ✅ **abgeschlossen (Closeout 2026-08-25)** — Block A ✅ (Migration 005 + `abstain_lessons/`, WE 1 2026-07-11) live auf main, **Montag-Restart-Beweis erbracht 2026-07-14** (66 echte `abstain_records`-Zeilen, 100 % `REASON_NO_CANDIDATES`); Block B ✅ (`market_context/` + Paper-Pipeline, WE 2 2026-07-17) live auf main; Council-Paper-Call ✅ gebaut, **default `False`, bis auf weiteres in mind Phase 15** (Nikinger 2026-08-25). Bugfix-Block 2026-07-25/31/08-08 (Wiring-`MINUTE_1`, Reflect-Schema, B1 point_value 40×-Oversizing, Allowance-Incident) + H1 (1 Woche gelaufen) + H4-a (Cap rollt). **165 Phase-10-Tests grün, 25 phase10_v3-Commits auf `origin/main`, `main` synchron mit `origin/main` (Stand 2026-08-25).** Phase-11-Inhalte (WI-2/W2, H3/H5/H7, B3) bleiben offen — gehören in den Datenfundament-Track. Closeout-Handover: [`phase10_v3/PHASE10_CLOSEOUT_HANDOVER.md`](./phase10_v3/PHASE10_CLOSEOUT_HANDOVER.md), Bild: [`docs/architecture/phase10_v3.svg`](./docs/architecture/phase10_v3.svg). Phasenkopf: [`phase10_v3/CLAUDE.md`](./phase10_v3/CLAUDE.md). |
| 11 — V3-Fortsetzung: Funnel-/Mess-Fixes (aus Datenwoche-2-Review, H1-H7) | 🛑 **DEFERRED (Notbremse, 2026-08-11)** — B1/B2/B4/B5 + H1 + H4-a gebaut und auf `main`; **WI-2/W2 unbeantwortet**. Drei Datenwochen an drei Infrastruktur-Ausfällen gescheitert, nie an der Messung → die gemeinsame Wurzel (**Datenfundament**) ist wichtiger als die Phase. Nichts zurückgerollt. Handover + Anforderungen A–G: [`phase10_v3/PHASE11_DEFERRAL_HANDOVER.md`](./phase10_v3/PHASE11_DEFERRAL_HANDOVER.md) |
| 12 — Datenfundament (Registry + BarService + Bar-Archiv + Recorder) | ✅ **abgeschlossen (Closeout 2026-08-25)** — Steps 0–8.5 auf `main` (Migration 006, Registry, BarService, Bar-Archiv, Recorder, Heartbeat); P12.5 Steps 1–3 (U1/U2/U3/U5 + Entscheidung B) bleiben **korrekt im Repo**. P12.5 war 2026-08-18 formal CLOSED + GESCHEITERT — die fünf Code-Fixes sind unabhängig vom Scheitern korrekt; gescheitert ist die Betriebsannahme, nicht der Code. **Die strukturelle Antwort auf das P12.5-Scheitern steht in Phase 13 + Phase 14** (Nikinger 2026-08-25): `BarService.get_window` ist seit Phase 13 Block A reine Archiv-Lesung (kein externer Fetch mehr); Phase 14s `instrument_source_availability` macht Quellen zu einer Registry-Zeile. **Phase-12-Beweiswoche (Plan §7) wird nicht wieder aufgenommen** — Phase-13-Beweiswoche läuft seit Mo 2026-08-25 separat. 143 Phase-12-Tests grün, 18 Phase-12-Commits auf `origin/main`, `main` = `origin/main` = `b9327ca` (Σ 1698 grün). Closeout-Handover: [`phase12_data_foundation/PHASE12_CLOSEOUT_HANDOVER.md`](./phase12_data_foundation/PHASE12_CLOSEOUT_HANDOVER.md), Bild: [`docs/architecture/phase12_closeout.svg`](./docs/architecture/phase12_closeout.svg). P12.5-Analyse (Root Cause, 92 %-Verschwendung, Option B): [`PHASE12_5_CLOSEOUT_HANDOVER.md`](./phase12_data_foundation/PHASE12_5_CLOSEOUT_HANDOVER.md). P12.5-Sofort-Befund: [`PHASE12_5_FAILURE_HANDOVER.md`](./phase12_data_foundation/PHASE12_5_FAILURE_HANDOVER.md). Phasenkopf: [`phase12_data_foundation/CLAUDE.md`](./phase12_data_foundation/CLAUDE.md). |. Bilder: [`phase12_preproof.svg`](./docs/architecture/phase12_preproof.svg) · [`data_foundation.svg`](./docs/architecture/data_foundation.svg). **Fortsetzung = Phase 13** (nächste Zeile) — der Schnitt wird dort gebaut, Phase 12 bleibt die Speicherschicht. |
| 13 — **Live-Datenfundament** (Beschaffung ≠ Verbrauch; 4 Stufen: LS-Kerzen → yF-Recorder → Fremdquelle → budgetierte IG-Rettung) | ✅ **abgeschlossen (Closeout 2026-08-31, Session 18)** — Blöcke A + B + C code-complete (Stand 2026-08-22) + Beweiswoche ausgewertet (Mini-Session 23) + Pfad-C-Entscheidung (Mini-Session 24) + Befund-Inversion. **Block C re-planned & live-verifiziert für DE40/FR40.** Eröffnet nach dem Scheitern von P12.5. Kern: kein Konsumentenpfad löst je einen externen Fetch aus; die Abdeckungsfrage gilt dem **ganzen Trade-Fenster** statt dem Schwanz; IG-Lightstreamer (Fallback: Tick-Aggregation) liefert den Live-Schwanz aus **derselben Preisreihe wie der Einstieg** (B0-Probe 2026-08-19: `CHART:` NO → L6-Fallback aktiv). Drei neu nachgemessene Befunde tragen die Phase: IG liefert für eine Forward-Epic seit einem Monat tote Historie mit `ok=True`; der Divergenz-Sampler ist dagegen strukturell blind; eine Lücke *mitten* im Trade-Fenster erzeugt eine **erfundene** `TIME_STOP`-Zeile. **Block C Re-Plan & Live-Verified 2026-08-22:** Capital.com Pfad B live-verifiziert (962 `source='capital'`-Bars: 481 DAX + 481 CAC, exakt Erwartung); Spain 35 (IBEX) wartet auf Phase 14 (Dukascopy wird dort eine Quell-Registry-Zeile). **Beweiswoche-Befund 2026-08-31 (Mini-Session 23) + Pfad-C-Entscheidung (Mini-Session 24):** [`phase13_live_data/PHASE13_BEWEISWOCHE_FINDINGS_2026-08-31.md`](./phase13_live_data/PHASE13_BEWEISWOCHE_FINDINGS_2026-08-31.md) — 14-Tage-Fenster source_delta-Diagnose, drei empirische Befunde: **B1 IG-Bars-Lücke (2/13 Tage, by design — IG = S4-GapRescue-Pfad, Default AUS); B2 53.6 % Divergenzrate** am letzten Tag mit Bars (Stichprobe, eingeschränkt auf Operator-Run-Tag); **B3 `last_verified_utc` semantisch korrekt** unter Pfad C (zeigt "Discovery-Ableitung", nicht "kontinuierliche Live-Coverage"). **Befund-Inversion (Mini-Session 24):** kein "Recorder-Mapping-Bug" — Phase-13-Architektur sieht strukturell keine kontinuierliche `source='ig'`-Beschaffung vor. **Phase-14 D5-Handover ist damit komplett freigegeben** (kein operativer Vorbehalt mehr). **Closeout-Handover (2026-08-31, Session 18):** [`phase13_live_data/PHASE13_CLOSEOUT_HANDOVER.md`](./phase13_live_data/PHASE13_CLOSEOUT_HANDOVER.md) — Phase-13-Closeout, Pattern-Vergleich zu Phase-12-CLOSEOUT (§0 BLUF + 5-Zeilen-Bilanz, L1–L18, F1/F2/F3 + B1/B2/B3, Pfad-C-Entscheidung, §9 Konsistenz-Regeln inkl. IG-Default-AUS, §10 Don'ts); 74 Phase-13-Tests grün, 53 `phase13:`-Commits auf `origin/main`, Σ 1703 grün repo-weit. Phasenkopf: [`phase13_live_data/CLAUDE.md`](./phase13_live_data/CLAUDE.md) (Session-18-Block). Bild: [`docs/architecture/phase13_live_data.svg`](./docs/architecture/phase13_live_data.svg). **Phase 13 wird nicht wieder aktiv** — jede Touch braucht eigene Nikinger-Cross-Phase-Freigabe (Liste deckte Phase 2/8/9/10/12/14; Phase 7 ab 2026-08-31 via Mini-Session 26). Pfad A (Operator-S4-Aktivierung, IG-Budget-bound) und Pfad B (Schema-Reinterpretation) sind als **P15-V4-Kandidaten** in Findings §8.2 dokumentiert. Pläne: [`docs/concepts/phase13_live_data_plan.md`](./docs/concepts/phase13_live_data_plan.md) (L1–L16, Blöcke A/B/C, §9-Drift-Liste) + [`docs/concepts/phase13_c_block_c_replan.md`](./docs/concepts/phase13_c_block_c_replan.md) (Block-C-Closure + Phase-14-Handoff) |
| 14 — **Discovery-Then-Deterministic** *(eröffnet 2026-08-22 aus dem Session-13-Architektur-Insight, abgeschlossen 2026-08-31)* | ✅ **abgeschlossen (Closeout 2026-08-31, Session 23)** — Blöcke 0 + A + B + C code-complete + Block-D-Doku-Updates ✅ (Stand 2026-08-31, Mini-Sessions 21+22+23+24) — D5-Handover **komplett freigegeben** (Mini-Session 24, Pfad-C-Entscheidung) — Phase-13-Recorder-Mapping-Initiative entfällt als architektur-konform (siehe Findings §8.1).** Plan: [`docs/concepts/phase14_discovery_plan.md`](./docs/concepts/phase14_discovery_plan.md) (D1–D20 gelockt, Blöcke 0/A/B/C/D, Akzeptanz A1–A8, §11 Korrekturnotizen). Phasenkopf: [`phase14_discovery/CLAUDE.md`](./phase14_discovery/CLAUDE.md) (Modul-Tabelle jetzt mit Tests-Spalte + Σ-Sweep, Session-22-Block). **Akzeptanz A1–A8 alle grün seit Session 9** (A1 Discovery 0 IG-Punkte strukturell · A2 `grep EPIC_MAP phase13_live_data/*.py` leer · A3+A4 yF-Projektion · A5 Daemon unscharf = nichts · A6 UI warnt + scharf per Datei · A7 source_delta Drei-Fälle · A8 Sweep 1659→1698). **Block-D ✅** (Mini-Sessions 21+22+23+24): Mini-Session 21 P14-D §10 Korrekturnotiz + Modul-Tabelle + P14-E Test-Fix; Mini-Session 22 P14-F (Doc-Rotation-Hook Step 2: `check_archive_sequence` + `--strict`-Flag + 7 Tests A1–A6 + Tracked-Installer `scripts/install_hooks.sh` + `dev_install.sh`-Anbindung — 4 Commits `94e0c35`/`d32e93a`/`8fe439c`/`8db5a1c`); Mini-Session 23 Phase-13-Beweiswoche-Befund-Indizierung in Phasenkopf + INDEX; Mini-Session 24 P14-F D5-Ausnahme (Hook-Verschärfung auf `--strict`-Default nach D5-Beweis — 1 Commit `c4f7d9c`). Cross-Phase-Edits in der freigegebenen Liste (Phase 2/8/9/12/13) eingehalten + Phase-12-Test-Touch (Mini-Session 21 Commit `98cac57`, Cross-Phase-Freigabe via P14-E-Plan-Session-20-Sign-off). **Live-Blocker B1 (Phase 14 A1 gefixt):** `stale_source` ist jetzt im Vokabular (`phase9_universe/universe/models.py`), zündet nicht mehr beim Lesen, sobald die Phase-13-Beweiswoche `enable_divergence_sampler` anschaltet. Jede Quelle (IG, yFinance, LS, Capital.com, später Dukascopy) **exponiert selbst**, was sie liefert; eine DB-Tabelle (`instrument_source_availability`) hält die Kreuzung IG-Epic × verfügbare Quelle; Konsumenten lesen die Tabelle, nicht den Code. Hinzufügen einer Quelle ist eine Konfiguration, kein Code-Deploy. **Absorbiert implizit:** hardcoded `EPIC_MAP` (verschwunden, A2 grün), Path C Dukascopy (wird Quell-Registry-Zeile). **D5-Handover-Status:** **komplett freigegeben** (Mini-Session 24, Pfad-C-Entscheidung) — Tabelle + Discovery + Source-Delta arbeiten wie designed; IG-Bars-Lücke seit 2026-08-18 ist **architektur-konform** (siehe Findings §8.1) und als P15-V4-Kandidat (Pfad A/B) in §8.2 dokumentiert. Concept: [`docs/concepts/phase14_discovery_concept.md`](./docs/concepts/phase14_discovery_concept.md). Handoff: [`docs/concepts/phase13_c_block_c_replan.md`](./docs/concepts/phase13_c_block_c_replan.md) §3 + §5 + [`phase14_discovery/PHASE14_D_DAEMON_SIGNAL_CAP_PLAN.md`](./phase14_discovery/PHASE14_D_DAEMON_SIGNAL_CAP_PLAN.md) §10 + [`phase14_discovery/PHASE14_E_RECORDER_LOOP_PLAN.md`](./phase14_discovery/PHASE14_E_RECORDER_LOOP_PLAN.md). **Closeout-Handover (2026-08-31, Session 23):** [`phase14_discovery/PHASE14_CLOSEOUT_HANDOVER.md`](./phase14_discovery/PHASE14_CLOSEOUT_HANDOVER.md) — Phase-14-CLOSE-OUT, Pattern-Vergleich zu Phase-12/13 (§0 BLUF + 5-Zeilen-Bilanz, D1–D20 mit D19 = IG-Default-AUS + D20 = Brücke zur Phase 15, A1–A8 alle grün seit Session 9, §9 13 Konsistenz-Regeln inkl. ARM-Pfad-absolut + Doc-Rotation-Hook-`--strict`, §10 Don'ts); 61 Phase-14-Tests grün, 54 `phase14:`-Commits auf `origin/main`, 38 Zeilen in `instrument_source_availability`, Σ 1703 grün repo-weit. Phasenkopf: [`phase14_discovery/CLAUDE.md`](./phase14_discovery/CLAUDE.md) (Session-23-Block). Bild: **kein** Solo-SVG (Empfehlung gemeinsam mit Phase-13 + Phase-15 als `phase13_14_15.svg`-Gesamtbild). **Phase 14 wird nicht wieder aktiv** — jede Touch braucht eigene Nikinger-Cross-Phase-Freigabe (Liste deckte Phase 2/8/9/12/13; Phase 7 ab 2026-08-31 via Mini-Session 26; Phase 14 selbst ab 2026-08-31 via Mini-Session 22). |
| 15 — V4: Sophisticated/Optional (Council, Handover, Reward-Reform, Force-Trigger, Instinct-ECC; vormals "Phase 12", dann "Phase 13", dann "Phase 14" — umnummeriert 2026-08-11, 2026-08-18 und 2026-08-22) | ✅ **abgeschlossen (Closeout 2026-09-05, Session #13)** — execution-ready Plan: [`docs/concepts/phase15_v4_plan.md`](./docs/concepts/phase15_v4_plan.md) (P1–P16 gelockt, AK1–AK14). 4 Blöcke alle ✅: **A** Haushalt (A-1..A-7 + P15-F) endgültig · **B** Reward-Kalibrierung (B1..B6 inkl. `--apply`) live-validiert (Score 78,72 → 50,00, AK5+AK6+AK13 grün) · **C** Instinct-ECC (C1..C4: Migration 009 + 5 Module + VETO 5 + 12 Phase-5-Tests, AK7+AK8+AK9 grün, heute bit-identical via leere `longterm_rules`) · **D** Erbstücke (D-1..D-3 + Folgefix Variante C komplett). Σ **1843 grün repo-weit** (selbst nachgemessen 2026-09-05); 18 Commits gepusht, 6 Commits lokal ahead. Phasenkopf: [`phase15_v4/CLAUDE.md`](./phase15_v4/CLAUDE.md) (Session-#13-Block). Closeout-Handover: [`phase15_v4/PHASE15_CLOSEOUT_HANDOVER.md`](./phase15_v4/PHASE15_CLOSEOUT_HANDOVER.md). Bild: [`docs/architecture/phase15_closeout.svg`](./docs/architecture/phase15_closeout.svg). **Offen (alle nicht-Phase-15-Blocker, delegiert):** Promotion-Bridge (Plan §10), Ledger-Restore (250 Punkte, Nikinger-Aktion), Gate P7/A6 (Phase-12-Reconcile-Timing Live-Verify, wartet auf nächsten OPEN-Trade), Live-DB Migration 008+009 (nicht automatisch — Phase 16 B1/B2). |
| 16 — Freischaltung (alle Löcher zu, alle Arme scharf, 2-Wochen-Autonomie-Test) | 🔄 **eröffnet 2026-09-05** — execution-ready Plan [`docs/concepts/phase16_activation_plan.md`](./docs/concepts/phase16_activation_plan.md) (P1–P17, L1–L9, Blöcke A–E, AK1–AK16); Phasenkopf [`phase16_activation/CLAUDE.md`](./phase16_activation/CLAUDE.md). Exec-Session startet mit Block A Step A-0. |

**Meta-Strang M1 — Harness-Unabhängigkeit — ✅ CLOSED (2026-07-09):** orthogonal zur
Nummerierung oben. Vorregistrierter Bake-off Claude Code vs. OpenCode: `gate_pass_rate`
90%/90%, Gap 0,00pp → **keine Migration** (E<M, jetzt zusätzlich messbestätigt). Plus
`AGENTS.md` + ein getesteter, kalter P4/P6-Fallback (`OpenAICompatLLMClient`), beide
smoke-verifiziert. Details: [`meta_m1_harness/CLAUDE.md`](./meta_m1_harness/CLAUDE.md);
optionaler nächster Schritt (ungelockt):
[`META_M1_CLOSEOUT_HANDOVER.md`](./meta_m1_harness/META_M1_CLOSEOUT_HANDOVER.md).

---

## File organization (where things go)

```
~/trading-bot/                              ← root
├── README.md                               ← human-facing overview
├── CLAUDE.md                               ← this file
├── ARCHITECTURE.md                         ← architecture summary + links
├── ROADMAP.md                              ← Phase 1–9 plan
├── .gitignore
│
├── docs/
│   ├── concepts/                           ← Phase-N concept docs
│   │   ├── phase1_broker_api_konzept.md
│   │   ├── phase2_persistence_konzept.md
│   │   └── phase3_external_data_konzept.md
│   ├── architecture/
│   │   ├── tradingbot_v2_architecture.svg
│   │   └── tradingbot_v2_architecture.pdf
│   └── sessions/                           ← (optional) chat session summaries
│
├── data/                                   ← runtime SQLite + JSON state (gitignored)
├── phase1_broker_wrapper/                  ← Phase 1 code ✅
├── phase2_persistence/                     ← Phase 2 code ✅
├── phase3_external_data/                   ← Phase 3 code ✅
└── ...
```

**Rule:** Each phase is a self-contained directory with its own `README.md`,
`requirements.txt`, and optionally its own `CLAUDE.md`. Cross-phase imports
happen only via well-defined contracts (e.g. Envelope JSON for broker_wrapper).

---

## Conventions

**Python:**
- Type hints everywhere (`from __future__ import annotations`)
- Docstrings on every public function/class (purpose, args, raises)
- `pytest` for tests, mock HTTP — no network calls in unit tests
- `requests` for HTTP, NOT `urllib` or `httpx` (consistency)
- One file = one responsibility (do not bloat modules)

**Errors:**
- Custom typed exception hierarchy in `exceptions.py`
- Never swallow exceptions silently — log + raise or log + return error envelope
- HTTP errors map to envelope error codes (see existing IGAdapter for pattern)

**Logging:**
- Use the standard `logging` module
- Logs go to stderr, never stdout (stdout is reserved for envelope JSON)
- DEBUG for internals, INFO for milestones, WARNING/ERROR for problems

**Git:**
- Atomic commits — one logical change per commit
- Commit message format: `<scope>: <imperative>` e.g. `broker_wrapper: fix epic search timeout`
- Never commit credentials. Never commit `.venv/`. Never commit `__pycache__/`.

---

## How to work in this repo

**Starting a session:**

1. Confirm which phase is active (check "Current state" above)
2. Read the relevant phase README (e.g. `phase1_broker_wrapper/README.md`)
3. Check `git status` and `git log -5` to understand recent work
4. Run existing tests before making changes (`pytest tests/ -v`)
5. If a `## Session stopped` block exists in the active phase's `CLAUDE.md` or
   relevant notes file — read it first. It records exactly where the previous
   session ended and what comes next.

**Navigating docs (token discipline — the Doc-Layers model):**

Start at [`docs/INDEX.md`](./docs/INDEX.md) (L0: one line per doc). Living docs carry a
≤15-line YAML header card (L1) — read it via `Read` with `limit: 15` and decide from
`purpose`/`read-when` whether the body (L2) is worth loading; hop between files via the card's
`up:`/`down:` links instead of directory searches. Archives and dated snapshots (L3:
`SESSIONS_ARCHIVE.md`, `docs/concepts/`, handovers) are read only when auditing history —
never at session start. Full spec: [`docs/DOC_LAYERS_CONVENTION.md`](./docs/DOC_LAYERS_CONVENTION.md).

**During a session:**

- After every subtask: run `pytest tests/ -v` before moving on.
  A subtask is not done until its tests are green.
- Write tests in the phase's `tests/` directory for every new function
  (mocked HTTP, no live network calls in unit tests).
- If any architectural decision changes, update the relevant concept doc in
  `docs/concepts/` immediately — not at the end of the session.

**Ending a session (mandatory):**

Before closing, append a `## Session stopped` block to the active phase's
`CLAUDE.md` (or the task's notes file if one exists, e.g.
`lightstreamer_integration_notes.md`). This is the handover to the next session.
Without it, context is lost and the next session starts cold.

```markdown
## Session stopped — <YYYY-MM-DD>

### Completed
- `<file>`: <what was done>

### Next
- <exact next step, specific enough to start without re-reading everything>

### Open questions / blockers
- <anything unresolved>
```

Replace or update this block at the start of each new session once read.

**Rotation rule (mandatory since 2026-07-06):** when appending the new `## Session stopped`
block, move the previously-newest block **verbatim** to the phase's `SESSIONS_ARCHIVE.md`
(newest-first). A phase `CLAUDE.md` carries exactly **one** session block; archives have no
size cap. New .md file created ⇒ add its one-liner to `docs/INDEX.md` in the same commit.

**When in doubt about scope or AI vs. code: default to code.**
The "AI as little as possible" principle resolves most ambiguity.

---

## Working style (how to act, not just what to do)

> Added 2026-07-06 (Fable-5 pass, Nikinger-approved): these calibrate judgment for capable
> models — they complement the rules above, they don't replace them.

- **Source-of-truth precedence: tested code > concept doc > README/status prose.**
  On conflict, trust the code, fix the doc immediately, and leave a dated note in the doc
  that it was corrected against code. Read docs first (cheaper), verify against code before
  building on a contract.

- **Act vs. ask.** Proceed without asking on reversible, in-phase steps that follow from the
  agreed plan — asking permission for routine in-scope work wastes the session. Stop and ask
  (the Nikinger decides) for: destructive or hard-to-reverse actions, cross-phase code edits,
  anything touching live (non-demo) money paths, and genuine scope changes.

- **Locked decisions stay locked.** Phase docs pin decisions and verified contracts
  (e.g. "Decision A–J" blocks). Don't re-litigate or silently "improve" them mid-implementation.
  If new evidence contradicts a locked decision, surface it as a finding and let the Nikinger
  decide — never deviate quietly.

- **Report outcomes faithfully.** If tests fail, say so and show the output. If a step was
  skipped, say that. When something is done and verified, state it plainly — no hedging,
  no "should work". A wrong "it works" costs more than an honest "it's broken";
  this project trades real money on the difference.

- **Root cause over symptom.** Before fixing a bug, find every caller of what you're about to
  touch; fix once at the shared point, not per reported symptom. The smallest diff in the
  wrong place is a second bug.

- **Read enough, then act.** Read the minimum needed (phase head + newest `## Session stopped`
  block first), but never skip comprehension of the code a change touches. Once you have
  enough information to act, act — don't re-derive facts already established in the session.

- **Handovers are written for a cold reader.** Lead with the outcome (what happened, what's
  next), spell out terms instead of session-local shorthand, and make the next step specific
  enough to start without re-reading everything.

- **Advisor usage (Claude Code, `/advisor` active).** Consult the Advisor in exactly these
  cases — no more, no less:
  1. **[VERIFY] mismatch:** the as-built code deviates from the plan's contract → ask the
     Advisor *before* reinterpreting it yourself, never adjust silently.
  2. **A test/gate keeps failing after 2–3 fix attempts** → consult the Advisor with the
     diff + error output instead of iterating further.
  3. **Before declaring a weekend block (Block A/B) done** → the Advisor checks against the
     plan's acceptance criteria + Definition of Done.

  Do NOT consult for: routine edits, locked decisions (they stay locked), or anything the
  plan already specifies exactly.

---

## Phase transitions

A phase is considered "done" when:
- All planned components exist
- Smoke test passes against the relevant environment (demo or local)
- Phase README documents what was built, known limitations, and integration points
- The next phase's concept document is ready in `docs/concepts/`

Phase transitions happen in the **Claude browser interface** (Konzept-Session),
not in Claude Code. Claude Code implements; Claude (browser) plans.

---

## Anti-patterns to flag

If you see any of these, stop and discuss with the human:

- LLM call inside a Gate, VETO, or sizing calculation
- Credentials in any file other than the keyring
- An AI output triggering an order without code-side validation
- A "temporary" hardcoded value that bypasses a check
- A test that hits the live (non-demo) IG account
- Force Trigger usage without checking Daily PNL
- Any direct broker call outside `broker_wrapper/` (always go through the wrapper)
- A subtask marked done without passing `pytest tests/ -v`
- A session ending without a `## Session stopped` block written
- A phase `CLAUDE.md` accumulating >1 session block (rotation rule skipped), or a
  new .md file missing from `docs/INDEX.md`
- Editing a 📕 dated snapshot (concepts, handovers, archives) instead of superseding it
