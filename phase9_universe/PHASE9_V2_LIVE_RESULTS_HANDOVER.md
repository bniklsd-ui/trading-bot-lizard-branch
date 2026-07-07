---
status: snapshot
purpose: Dated results snapshot of the first multi-day V2 live run (started 2026-07-06 15:52) — what V2a/V2b already proved, what is still open
read-when: assessing V2 progress, planning the run's follow-up, or onboarding the meta-phase session
detail: L3
up: ./CLAUDE.md
updated: 2026-07-07
---
# Phase 9 (V2) — Live-Run Results & Handover (Stand 2026-07-07 ~11:00, Lauf läuft weiter)

> 📕 Dated snapshot — nicht weiterpflegen; Folgebefunde gehören in neue Session-Blöcke /
> einen Folge-Snapshot. Der Lauf (gestartet 2026-07-06 15:52, geplant ~2–3 Tage) läuft beim
> Schreiben dieses Files **noch** — Zahlen sind der Stand von heute Vormittag.
> **Zweck des Laufs (Nikinger):** eine Test-Baseline erzeugen, die zukünftige Phasen
> erhalten und verbessern müssen.

## TL;DR

**V2a (autonome Epic-Research) funktioniert end-to-end und verändert das Bot-Verhalten
messbar.** Die Universum-Warnung ist weg, die DB-Pipeline hat über Nacht 15 Instrumente
durch discover→verify→activate geschleust (8 active am Cap + 7 verified in Wartestellung,
**0 quarantined**), alle 15 mit code-bewiesenem `point_value` über **Pricing-Pfad 1
(`ig_fields`)** — der Pfad, den erst das P1-Hardening (Pip-Feld-Passthrough) freigeschaltet
hat. Research hat erstmals ein **DB-Instrument (CAC) gepickt und debattiert**. Noch nicht
bewiesen: ein echter Trade unter dem V2-Universum, und der Neustart-Pickup der 8 Aktiven.

## Belege (Log `logs/scheduler_5a_variety_.log` + DB read-only + `research_health.jsonl`)

| Frage | Befund |
|---|---|
| Universum-Warnung beim Start? | **Weg.** 0 Treffer `universe_from_records` im ganzen Lauf (vorher jeder Start). |
| DB-Pipeline-Durchsatz | **8 active / 7 verified / 0 quarantined / 0 discovered** (15 Instrumente; Cap `max_active=8` exakt getroffen; STXE via neuem `seed_curated`-Wiring, Rest `research_promoted`). |
| Pricing | Alle 15 `point_value_source='ig_fields'` (Pfad 1) — deterministisch code-bewiesen, kein carried-over Wert (D6 erfüllt). |
| C3-Fix wirksam? | **Ja.** yFinance war heute Vormittag hart down (`possibly delisted` für ^GDAXI/^FCHI/^IBEX, 30 Fehler, 3-Attempt-Retry griff) — trotzdem 0 Quarantänen; alle Rows tragen `data_degraded=1` statt eingefroren zu sein. Vor dem Fix hätte genau dieses yf-Wetter das Universum wieder stundenlang eingefroren (der 2026-07-06-Befund). |
| Verändert V2 das Research? | **Ja, sichtbar.** 2026-07-07 10:27: erster Pick + Bull/Bear/Judge-Debatte über **CAC** (DB-Universum) — Judge-Abstain mit sauberer Begründung (Widerstandszone, schwaches Momentum). Vorher DAX-only-Muster. |
| Entscheidungs-Verteilung | 41 WINDOW-Research-Zyklen: 40 LLM-Abstains (on merit, Lessons sichtbar im Reasoning: Verluststrecken-Vorsicht) + 1 Pick→Debatte→Abstain. **0 Trades bisher in diesem Lauf.** |
| Mechanik-Stabilität | 0 ERROR/CRITICAL außer den yf-Fetches; kein AUTH_ERROR, kein RATE_LIMIT, kein Backoff-Trip; `consecutive_failures=0`; Tages-Rollover 06→07 sauber. |
| Observability | `research_health.jsonl` liefert pro Zyklus per-Epic-Health (DAX `full`, CAC `degraded/missing volume`) — die v1.6-Diagnose-Kette trägt. |

## Was noch zu beweisen ist (in Prioritätsreihenfolge)

1. **Neustart-Pickup (der letzte V2a-Beweispunkt):** der laufende Prozess baut sein
   Research-Universum **einmal beim Start** (Wiring) — er sieht weiterhin 2 Epics, obwohl
   die DB längst 8 active hält. Der **nächste Daemon-Start** muss `context built: 8
   tradeable epic(s)` zeigen. Erst dann ist discover→activate→**research-nutzt-es**
   geschlossen.
2. **Ein echter open→close-Trade unter dem V2-Universum** (Baseline-Ziel des Laufs).
   Bisher 0 Trades — die Abstains sind inhaltlich begründet, kein Mechanik-Problem.
3. **Variety-These (v1.5-Carry-over):** mit 8 statt 2–4 Epics nach dem Neustart — sinkt
   die Abstain-Quote? (`research_health.jsonl` hergeben die Zeitreihe.)
4. **V2b-i im Scharfbetrieb:** `--enable-ig-bars`-Beobachtungslauf (`bar_fetch`-Events)
   steht unverändert aus — gerade heute attraktiv, weil yFinance auf der VM notorisch
   flakt (IG-primär würde den Brain-Context von Yahoo entkoppeln).
5. **Step 7b-Trigger prüfen:** mit 8+ aktiven Epics ist die H2-Bedingung (~10+
   LS-Subscriptions) fast erreicht → LS-Multi-Epic-Diagnose bei Gelegenheit re-runnen.

## Watch-Items (klein, nicht blockierend — bewusst NICHT am laufenden System gefixt)

- **`fail_count`-Reset-Lücke:** Step-1-Verify-PASS resettet `fail_count` nicht
  (`reset_fail_count` wird nur im Step-3-Recovery-Pfad genutzt). Folge: DAX ist active
  mit `fail_count=3` = exakt `demote_after_fails` — ein einziger IG-Wackler (z. B.
  `get_ohlcv` um 09:00:00 beim Marktöffnen) kann das Kern-Instrument unverdient
  quarantinieren. Fix-Kandidat: `reset_fail_count=True` beim Übergang →`verified`
  (Ein-Zeiler + Test), nach dem Lauf.
- **yFinance-Zuverlässigkeit der VM:** intermittierend ganztags (gestern Abend ok, heute
  Vormittag down) — mit C3 nur noch Signalverlust, aber die V2b-Kette (IG-primär) ist die
  strukturelle Antwort.
- **Mid-Run-Propagation:** Universum-Änderungen erreichen Research erst per Neustart
  (Design-Entscheidung des Step-5-Wirings, kein Bug — aber dokumentierenswert; evtl.
  V3-Thema „Universe-Rebuild pro Refresh").

## Kontext für die nächste Session

- Lauf weiterlaufen lassen (~2–3 Tage, Baseline). Danach: Neustart → Beweispunkt 1.
- **Nächste Phase (Nikinger-Spoiler, 2026-07-07):** eine **Meta-Phase** — Experiment,
  auf ein Open-Source-Harness umzusteigen (aktuell vielversprechendster Kandidat:
  **opencode**) für Unabhängigkeit. Betrifft nicht den Bot, sondern **wie am Bot
  gearbeitet wird**; ehrliche Dokumentation im Projekt ist Teil des Experiments.
