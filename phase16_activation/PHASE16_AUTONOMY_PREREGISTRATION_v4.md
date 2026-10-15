---
status: snapshot (aktive Vorregistrierung — 2-Tage-Brückenfenster nach v3)
purpose: Vorregistrierung des 2-Tage-Beobachtungsfensters Do 2026-10-15 09:00 → Fr 2026-10-16
  17:30 (Berlin). Liefert frische, unverzerrte Messdaten für den v3-Closeout und den nächsten
  Plan (Wochenende 17./18.10.). Erbt alle Werte + Kriterien aus v3; neu sind nur das Fenster
  und vier Fix-Fragen Q1–Q4 zu den Befunden der Session #37.
read-when: Closeout v3 / Plan-Session am Wochenende; Audit, ob die Fragen vor dem Fenster
  festgelegt wurden (Commit-Zeit < 2026-10-15 09:00).
detail: L3
up: ./CLAUDE.md
down:
  - ./PHASE16_AUTONOMY_PREREGISTRATION_v3.md  # Werte, K1–K9, P17-Ereignisse, Watch-Items W1–W8 — gelten unverändert
  - ./PHASE16_E3_RUNBOOK_v4.md                # Restart-Ritual
  - ../phase7_reward/CLAUDE.md                # 🟡 Backoff-Korrektur 2026-10-15 (Q1)
---
# Phase 16 — Vorregistrierung v4: 2-Tage-Brückenfenster (2026-10-15/16)

## BLUF

- **Fenster:** Do **2026-10-15 09:00** → Fr **2026-10-16 17:30** (Berlin), 2 Handelstage.
- **Auftrag:** Nikinger 2026-10-15 ~07:50: „2 Tage Testperiode, ab heute Marktöffnung bis morgen
  Marktschluss, damit Closeout und neuer Plan übers Wochenende geschrieben werden können."
- **Kein neuer Autonomie-Test.** v3 (10 Tage, 09-29 → 10-13) ist beendet. Dieses Fenster misst,
  ob die Session-#37-Fixes live tragen, mit Daten, die **nicht** durch den blockierten AEX-Slot
  (10-09…10-14) oder den LLM-Guthaben-Ausfall (10-09) verzerrt sind.
- **Code-Stand:** HEAD `75b070f` (Backoff-Anker-Fix). Scheduler-Restart 2026-10-15 07:42:26
  (MainPID 670575) **vor** dem Fenster → zählt nicht als Operator-Restart in K1.

## Vorregistrierte Werte

Alle Werte aus v3 §„Vorregistrierte Werte" gelten unverändert (demo, max_trades 5,
daily_loss_cap 1800, Token-Budget 300 000, vier Arme ON, Rescue AUS, Promotion-Bridge ON,
Cycle 5 min, `max_parallel_positions` 1). Einzige Abweichung: **Tage = 2**.

## Kriterien

| # | aus v3 | Bewertung in diesem Fenster |
|---|---|---|
| K1, K2, K5, K6, K7, K8, K9 | unverändert | PASS/FAIL je Tag wie in v3 |
| K3 (≥ 5 Trades) | 10-Tage-Kriterium | **nur berichtet** (Rohzahl), nicht PASS-bewertet |
| K4 (Heartbeat ≥ 8/10) | 10-Tage-Kriterium | **nur berichtet** (x/2), nicht PASS-bewertet |

Report: `phase16_activation/scripts/autonomy_report.py --from 2026-10-15 --to 2026-10-16 --summary`
(Operator führt aus). Profit bleibt **kein** Kriterium (v3 „ehrliche Ausschlüsse").

## Fix-Fragen Q1–Q4 (neu, vor dem Fenster festgelegt)

| # | Frage | Messquelle | Erwartung |
|---|---|---|---|
| **Q1** | Bucht der Recorder broker-geschlossene Trades jetzt zeitnah? (Backoff-Fix `75b070f`) | `trade_outcomes`: `updated_at − close_ts` je CLOSED-Trade mit `open_ts` im Fenster; `run_scheduler.log` `P&L unresolved`-Zeilen je deal_id | ≤ 1 h 15 min bei Close < 4 h nach Open. Erster gelöster Versuch = **erste echte IG-Settlement-Messung** (bisher unbekannt, die 24 h waren der Backoff-Boden). > 4 h = FAIL Q1 |
| **Q2** | Ist der Slot frei — keine Blockade durch Geister-Positionen? | `abstain_records` `reason_gate_constraints` mit `max_parallel_positions` vs. tatsächlich offene Position (`execution_state.json` / `trade_outcomes` OPEN) | jede Slot-Abstain-Zeile fällt in eine Zeit mit echter offener Position. Abstain ohne echte Position = FAIL Q2 |
| **Q3** | Ist die LLM-Strecke verfügbar? | `run_scheduler.log` `credit balance is too low` / `HTTP/1.1 4xx` auf `api.anthropic.com` | 0 Guthaben-Fehler; sonst Zeitpunkt + Anzahl berichten, betroffene Ticks aus Abstain-Statistik herausrechnen |
| **Q4** | Wie oft bleibt eine Position nach Restart unüberwacht? (bekannter Defekt, Phase-17-Kandidat) | `run_scheduler.log` `starting scheduler daemon` während eine Position OPEN ist | **Watch, kein PASS:** jedes Vorkommen dokumentieren (deal_id, Dauer bis zum Close) |

**Watch-Items zusätzlich zu v3 W1–W8:**
- **W9** `instinct.bridge … InstinctValidator.validate() missing 1` — Anzahl CRITICAL im Fenster (bekannter Defekt, Phase-17-Kandidat).
- **W10** Daily-Loss-Breaker-Sicht: bei jedem Stop-out Zeitraum, in dem `profit_loss IS NULL` war (Breaker blind) — Eingangsmaterial für den Phase-17-Kandidaten „Breaker ohne Blindfenster".

## Erlaubte Ereignisse

- v3 §„Erlaubte Operator-Ereignisse (P17)" gilt unverändert.
- **Lesezugriff durch `eurofyx-fleet`** (Nikinger-FYI 2026-10-15: Fleet liest im selben Zeitraum
  über die Projekte, u. a. Prompts für das Standardisierungssystem) ist **kein** Operator-Ereignis,
  solange er rein lesend bleibt — keine Dienste, kein `data/state/KILL`, kein `DISCOVERY_ARMED`,
  keine DB-Writes (gleiche Regel, die Fleet sich in S6 selbst gesetzt hat). Ein Schreibzugriff wäre ein
  Befund für den Closeout.
- **Vor** dem Fenster liegende Eingriffe zählen nicht: manueller AEX-Close id 26 (2026-10-14 ~19:00),
  Scheduler-Restart 07:42:26.

## Aktiv-Block

| Feld | Wert |
|---|---|
| Start | 2026-10-15 09:00 Berlin (Marktöffnung); Dienste laufen seit Restart 07:42:26 |
| Ende | 2026-10-16 17:30 Berlin (Marktschluss) |
| Code | HEAD `75b070f` |
| Offene Position bei Start | keine (`execution_state.json` OPEN/PENDING leer, 07:36) — id 26 in `trade_outcomes` noch OPEN ohne P&L (Buchung erwartet ~19:12, Backoff-24-h-Stufe; zählt nicht für Q1, da Open vor dem Fenster) |
| Vorregistriert | Session #37 (Opus 5.5), Commit vor 09:00 |
