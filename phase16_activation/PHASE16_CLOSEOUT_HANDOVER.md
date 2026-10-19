---
status: archive
purpose: Phase-16-Closeout-Handover — Teilbilanz (6/9 Löcher live zu + L7 per Live-Probe, Bot handelt wieder, aber kein Autonomie-Lauf PASS), offene Entscheidungen für die Folge-Plan-Session
read-when: Cold-Reader-Einstieg nach Phase 16 — vor jedem anderen Phase-16-Doc und vor dem Entwurf des nächsten Plans
detail: L3
up: ./CLAUDE.md
down:
  - ../docs/architecture/phase16_activation.svg       # 📕 Closeout-Bild 1080×1080
  - ../docs/concepts/phase16_activation_plan.md       # 📕 Plan (P1–P18, L1–L9, AK1–AK17)
  - ./PHASE16_PARTIAL_CLOSEOUT.md                     # 📕 §7 = Kandidatenliste „für die nächste Phase"
  - ./PHASE16_AUTONOMY_PREREGISTRATION_v3.md          # 📕 Kriterien K1–K9 (gelten weiter)
  - ./PHASE16_AUTONOMY_PREREGISTRATION_v4.md          # 📕 Brückenfenster Q1–Q4
  - ./PHASE16_LLM_SWITCH_PLAN.md                      # 📕 ungebauter K6-Plan
  - ./SESSIONS_ARCHIVE.md                             # 📦 Session-Historie #1–#37
superseded: —
---

# Phase 16 — Closeout-Handover (2026-10-16, Opus-5.5-Session #38)

> Alle Zahlen hier hat diese Session **selbst gemessen**: Tests je Suite getrennt, `git`,
> Live-DB `mode=ro`, Logs, `autonomy_report.py` offline. Wo ein Wert nur abgeleitet ist, steht das dabei.

## §0 BLUF

Phase 16 ist **mit Teilbilanz abgeschlossen**.
- **Erreicht:** 6 von 9 Löchern sind live zu, L7 (Margin-Cap) ist per Code und Live-Probe belegt. Der Bot handelt wieder (17 Trades seit 09-28, vorher 100 % Research-Abstain). Die Dienste überleben einen Reboot.
- **Nicht erreicht:** Der Kern-Beweis **AK15** fehlt. Kein vorregistrierter Autonomie-Lauf hat PASS erreicht.
- **Was den PASS verhindert:** vier benannte Defekte (§4). Drei liegen außerhalb von Phase 16 (P5/P7/P8/P15) und warten auf eine Cross-Phase-Freigabe.

| Ergebnis | Stand (gemessen 2026-10-16) |
|---|---|
| **fertig gestellt** | Plan-Blöcke A–D · F-Subphase (J1–J8, H) · R-Subphase R0–R6 (u. a. systemd-Autostart) · Backoff-Fix `75b070f` · E1/E2 (Prereg v1–v4, `autonomy_report.py`) |
| **getestet** | **Σ 1964 grün** (16 Suites, Zählweise wie Plan) = +121 seit Baseline 1843; + `meta_m1_harness` 28 = 1992; 0 rot, 0 skip |
| **live validiert (Demo)** | L1 · L3 · L4 · L5 · L8 · L9 (+ L7 nur Probe) · Autostart (Reboot 2026-10-12) · A6 nach Quell-Definition (§2, Gate P7 = Entscheidung E6) · Q1–Q4 (Brückenfenster) |
| **gepusht und committet** | 94 Commits seit 2026-09-05; `origin/main = HEAD = be15cf9` vor dem Closeout-Commit; der Closeout-Commit liegt lokal, Push auf Freigabe |
| **nicht erreicht / offen** | **AK15** (2-Wochen-PASS) · **L2** Token-Budget (K6) · **L6** Promotion-Bridge live tot · Monitor-Orphan · Breaker-Blindfenster · LLM-Subphase nur Plan |

## §1 Was nur offline bewiesen ist

| Thema | Offline-Beleg | Warum nicht live |
|---|---|---|
| Promotion-Bridge + Compiler + VETO 5 | P15/P7/P5-Tests grün | Live scheitert jeder Lauf vor der Promotion (§4.2). 29 `instincts` stehen auf `proposed`, 0 `validated`/`promoted`. VETO 5 läuft also weiter mit leerer Regelliste. |
| Margin-Cap (D3) | Sizing-Tests, Live-**Probe** 09-07 (DAX 5, IBEX/AEX 10) | Kein Log beweist, dass der Cap in einem Live-Trade gebunden hat. |
| K9 (≤ 10 Auto-Restarts/Tag) | Prereg v3 definiert ihn | `autonomy_report.py` bewertet nur K1–K8 (Drift). `NRestarts` setzt sich bei Unit-Start und Boot zurück, daher ist K9 für v3 nachträglich nicht messbar. v4 wurde manuell gemessen: 0. |
| K2-Discovery-Signal | Report meldet „3/3" | `evaluate_k2` (`autonomy_report.py:660,663`) zählt für Discovery dieselben Scheduler-Health-Events. Der vorregistrierte Beleg (`instrument_source_availability.last_verified_utc` wächst je Tag) wird **nicht** gelesen. Die Tabelle wird in-place überschrieben, heute haben 24 Zeilen `last_verified_utc` = 2026-10-16. |
| K2-WebUI | konstant `"operator-gesichtet"` (`autonomy_report.py:656`) | ✅ **Sichtung durch den Nikinger am 2026-10-17** (Dashboard ok, Daten aktuell). Das liegt nach dem v4-Fenster. Die Unit läuft aber seit 10-12 21:10 ohne Restart (`NRestarts=0`), deckt v4 also per Ableitung ab. Für v3 gibt es keine Sichtung. |

## §2 Autonomie-Läufe — Ergebnis je Kriterium

| Lauf | Fenster | Ende | K1 | K2 | K3 | K4 | K5 | K6 | K7 | K8 | K9 |
|---|---|---|---|---|---|---|---|---|---|---|---|
| v1 | ab 09-07 | tot Tag 1 (LS-Stream, K1/K4-Messfehler) | — | — | — | — | — | — | — | — | — |
| v2 | 09-09 → | tot Tag 9 (Reboot ohne Autostart, Drift #12/#13) | — | — | — | — | — | — | — | — | — |
| **v3** | 09-30 → 10-13 | 10 Tage durch | ❌ | ◐ | ✅ 13 | ✅ 10/10 | ❌ 17 | ❌ 2 Tage | ✅ | ✅ | n/m |
| **v4** | 10-15 → 10-16 | Brücke, K3/K4 nur berichtet | ✅ | ✅* | (2) | (1/2) | ✅ 5 | ❌ 2 Tage | ✅ | ✅ | ✅ 0 |

◐ = 3/3 automatisch (Discovery nur Proxy), WebUI im Fenster ungesichtet · ✅* = WebUI am 10-17 gesichtet, deckt v4 per Ableitung ab (§1) · n/m = nicht messbar.
v3-Report: `autonomy_report.py --from 2026-09-30 --to 2026-10-13 --summary` (Session #38, Ausgabe nach `/tmp`, nicht nach `data/reports/`).
Die Zahlen sind mit dem v4-Report `data/reports/autonomy_2026-10-15_to_2026-10-16.json` reproduzierbar.

**Lesart der FAILs (v3):**
- **K1:** Der FAIL hält. Unabhängig vom fehlenden `NRestarts`-Abzug brechen zwei Operator-Ereignisse K1 nach Prereg-Regel: der R-Fix-Restart 09-30 06:37 und der Reboot 10-12 21:09 (P17b = FAIL K1). Zwei weitere Scheduler-Starts haben **keine bekannte Ursache**: 10-08 22:26 (Stopp zwischen 15:43 und 16:59) und 10-11 19:02 (Sonntag).
- **K5:** Das Kriterium zählt **alle** CRITICALs, die Prereg v3 nennt es „(A6)". Der Script-Wert für v3 ist max 17, also FAIL.
  - Die **Quell-Definition von A6** (`phase7_reward/PHASE12_RECONCILIATION_TIMING_PLAN.md:366`) zählt dagegen nur die „CRITICALs des neuen deal_id". Nachgezählt per `grep` auf die deal_id in `run_scheduler.log`: **max 2 je Trade** über alle 15 Trades ab id 14 (id 27 = 2, sonst 0–1). → Das Ziel von A6, den Reconcile-Backoff, hat der Bot live erreicht.
  - Der Rest von K5 stammt aus `instinct.bridge` (Defekt §4.2) und `abstain_lessons.paper` (`get_price not ok`). Die Per-Trade-Werte stehen im Report-JSON; die 24-h-Fenster überlappen (drei Trades am 10-07).
  - **Widerspruch, offen gelassen:** nach registrierter Lesart (K5 = alle CRITICALs) ist A6 FAIL, nach Quell-Lesart PASS. Ob Gate P7 damit offen ist, entscheidet der Nikinger (E6).
- **K6:** Das Budget war an 10-12 und 10-13 vor 17:30 leer. Beide Tage lagen im **blockierten Slot** (AEX-Orphan, §4.3) und hatten die meisten Calls (149/142 gegen 84–130 an freien Tagen). K6-v3 ist also teilweise ein Symptom des Monitor-Defekts. v4 riss K6 aber auch **ohne** Blockade (92 Calls/303 910 Tokens, 138/301 031). K6 bleibt damit ein eigenes Problem.

**Kein Kriterium, aber Substrat für die Strategie-Frage:** Phase-16-Trades id 12–28: 17 CLOSED, 9 Gewinner, Σ **−654,72 EUR**. Davon v3 13 Trades/−2 232,75 EUR und v4 2/+1 593,71 EUR. Die Watch-Items **W1 und W2 sind gekippt**: 5 SELL-Trades (id 21–25) und Epics AEX/IBEX/MIB/CAC neben DAX.

## §3 Delta seit dem letzten Handover

Der letzte Handover ist `phase15_v4/PHASE15_CLOSEOUT_HANDOVER.md` (09-05), danach kam der Partial Closeout (09-08).

| Abschnitt | Sessions | Kern | Anker |
|---|---|---|---|
| Plan-Blöcke A–D | #1–#10 | L1–L9-Fixes, Schema v9 per Operator-Apply, Arme Default ON, Bridge, Margin-Cap | Plan §6, `SESSIONS_ARCHIVE.md` |
| E1/E2 + F-Subphase | #11–#32 | Prereg v1 → v2, J-Fixes (LS-Thread, K1-Fenster, K4-Sitzungsfenster), Header-Card-Hook | `PHASE16_F_EXEC_PLAN.md` |
| R-Subphase | #33–#35 | Drift #12/#13, K8 Liveness, Log-Archivierung, 4 systemd-User-Units, yF-Retry-Fix, Prereg v3 | `PHASE16_R_EXEC_PLAN.md`, `systemd/` |
| LLM-Subphase | #36 | **nur Plan + Brief**, kein Code | `PHASE16_LLM_SWITCH_PLAN.md` |
| Status-Check + Brücke | #37 | Backoff-Fix `75b070f` (P7), Prereg v4, Q1–Q4 gemessen | Phasenkopf → Archiv-Block #37 |
| Closeout | #38 | v3 erstmals ausgewertet, A6 nach deal_id gezählt, Bridge-Ursache im Code belegt | dieses Dokument |

## §4 Was den PASS verhindert (Fix-Kandidaten, nach Wirkung sortiert)

Mit „Kandidat" sind die Einträge aus `PHASE16_PARTIAL_CLOSEOUT.md` §7 gemeint (dort „für die nächste Phase" markiert). Diese Session hat sie gegen den Code geprüft.

1. **Token-Budget (L2/K6).** Research läuft pro 5-min-Tick unbedingt und macht ≈ 94 % des Verbrauchs aus (R6-Messung). 300k reichen an Handelstagen nicht. → Entscheidung E2.
2. **Promotion-Bridge live tot (L6).** Zwei Defekte hintereinander:
   - **Code-belegt:** `phase15_v4/instinct/bridge.py:146` ruft `self.validator.validate(instinct)`. Die Signatur ist aber `validate(self, instinct, trades)` (`validator.py:97`), also `TypeError` je Instinct. Der Test-Fake `tests/test_instinct_bridge.py:128` hat nur **ein** Argument und hat die Naht deshalb grün gehalten.
   - **Inferiert, nicht live verifiziert:** Seit 10-15 scheitert schon der Extractor (`JSONDecodeError` bei char 962–988, trade_id 26/27/28). Er läuft über den Lesson-Client mit `lesson_max_tokens = 400` (`phase7_reward/reward/models.py:379`, verdrahtet `phase8_scheduler/scripts/wiring.py:390-400`). Die Länge passt zu einem Token-Abbruch.
   - **Lehre für den Plan:** Contract-Tests an Phasen-Nähten, kein Fake mit abweichender Signatur.
3. **Monitor-Orphan nach Restart.** `reconcile_startup` lässt eine Position mit Status `present` stehen (`phase5_execution/execution/order.py:68`, „the monitor handles it"). Nach einem Restart startet aber niemand einen Monitor dafür. Beleg: AEX id 26 blieb 6 Tage offen, `max_hold` wurde nie angewendet, und `max_parallel_positions=1` blockierte vom 10-09 bis 10-14 jeden Trade. Cross-Phase P5/P8.
4. **Breaker-Blindfenster.** `safety.py:24-36` summiert nur gebuchte P&L. Ein Stop-out ist bis zum IG-Settlement unsichtbar, gemessen 1 h 06 bis 1 h 54 (seit `75b070f`, vorher 24 h). Dieselbe Annahme trägt den Daily-PNL-Lock (Hard Rule 5). Vorschlag: ungelöste broker-geschlossene Zeilen mit `−initial_risk` zählen. Cross-Phase P7/P8.
5. **Report-Skript-Drift.** K9 fehlt, das Discovery-Signal ist nur ein Proxy, K5 trennt nicht nach Logger. Jede Änderung an Kriterien braucht eine **neue Vorregistrierung vor** dem Lauf (P11).

**Weitere Kandidaten** (je eine Zeile; früher ausdrücklich für Closeout oder Plan markiert):
- Backoff-Anker auf `_pending_close[...].closed_at` statt `open_ts`. Das ist der Upgrade-Pfad aus dem `ponytail:`-Kommentar in `phase7_reward/reward/recorder.py`. Ohne ihn lag id 27 bei 1 h 54 statt ~1 h 15; ob es helfen würde, hängt von der unbekannten IG-Settle-Zeit ab (Session #37).
- `close_ts` ist bei Cold-Reconstruct der Zeitpunkt des letzten Fehlversuchs (`updated_at`), nicht der echte Close. `hold_duration_min` fällt dadurch zu lang aus (id 26). Datenbefund, kein Geldpfad.
- Smoke-Test-Muster auf die Geschwister-`_build_*` in `wiring.py` übertragen (Partial Closeout §7).
- `requires-python` in Phase 15 angleichen, `>=3.12` vs. `>=3.11` (D-F1).
- **WebUI-Layout** (Nikinger-Wunsch 2026-10-17): Gesamt-Umsatz (Σ P&L aller Trades) oben anzeigen, TRADES als lange Liste in eine Seitenspalte, LESSONS bis zum unteren Rand vergrößern, damit 16:9 genutzt wird. Ort: `phase8_scheduler/webui/static/` + `api.py` (`/api/trades` liefert die Daten schon). Die Summe rechnet der Code, kein LLM. Cross-Phase P8, vor dem Bau einen Design-Skill nutzen.
- ✅ „Prozess-Supervision" aus Partial Closeout §7 ist **erledigt**: R5-systemd-Units, Autostart am 10-12 live bewiesen. Nicht neu planen.

**Unbekannt geblieben:** die Ursache des Scheduler-Stopps am 10-08 (15:43–16:59) · die Ursache des Starts am 10-11 19:02 · die genaue IG-Settle-Zeit (Intervall 42 min bis 1 h 54) · die Ursache der 16× `PaperEngine get_price not ok`.

## §5 Offene Entscheidungen (Nikinger)

**E1 — Rahmen und Nummer der Folgearbeit** *(projektweit sichtbar, wird hier nicht entschieden)*
- (a) **Phase 17** mit eigenem Verzeichnis und Plan. Folge: saubere Trennung, ROADMAP bekommt eine neue Zeile, und der Kandidaten-Text („für die nächste Phase", Nikinger 10-14/15) passt wörtlich.
- (b) **Weitere Phase-16-Subphase** (Suffix wie F/R/LLM). Folge: kein Nummernsprung. Phase 16 bliebe dann aber faktisch offen, was diesem Closeout widerspricht. Der Lock „Phase 17 ausgeschlossen" vom 09-08 galt der damaligen F-Subphase.
- **Empfehlung: (a).** Phase 16 ist hiermit geschlossen. Eine vierte Subphase würde den Schirm endgültig verwässern.

**E2 — Token-Budget (K6)**
- (a) LLM-Switch-Plan ausführen (günstigeres Modell). Folge: Cross-Phase P4/5/7/8/15, Smoke-Pflicht, Modellwechsel mitten in der Messreihe.
- (b) Research-Kadenz im Code senken (Change-Detector bzw. Research nur bei Marktänderung). Folge: weniger AI, passt zum Bauprinzip, P4/P8-Touch, Wirkung auf die Trade-Frequenz unbekannt.
- (c) Cap erhöhen. Folge: kostet nur Geld, löst nichts strukturell.
- (d) K6 umformulieren („Research-Pause nach Cap akzeptiert"). Folge: nur per neuer Prereg.
- **Empfehlung: (b) zuerst, (a) als zweite Stufe.** Erst die Calls pro Tag messen, die ein Change-Detector spart. Die v3-Daten zeigen, dass blockierte Tage teurer sind, Fix §4.3 senkt den Verbrauch also mit.

**E3 — Nächster Autonomie-Lauf**
- (a) Erst §4.1–4.4 fixen, dann einen neu vorregistrierten 10-Tage-Lauf (v5) mit messbarem K9 und echtem Discovery-Signal. Folge: realistisch ≥ 3 Wochen bis zum Ergebnis.
- (b) v3 als „Autonomie mit benannten Ausnahmen" akzeptieren und zur Strategie-Arbeit wechseln. Folge: AK15 bleibt formal unerfüllt, und die Defekte §4.2–4.4 laufen weiter.
- **Empfehlung: (a).** §4.3 und §4.4 berühren Geldpfade (Hard Rule 2/5) und gehören vor jede Strategie-Arbeit.

**E4 — K5-Rauschen**
- (a) Kriterium belassen, Quellen beheben: Bridge-Fix, `PaperEngine get_price`-CRITICAL prüfen (ist CRITICAL die richtige Stufe?).
- (b) K5 per neuer Prereg auf die A6-Quell-Definition (CRITICALs der deal_id) einschränken.
- **Empfehlung: (a).** Das Kriterium nicht lockern, sondern die Ursachen beheben.

**E5 — Promotion-Bridge bis zum Fix**
- (a) An lassen. Folge: Extractor-Calls kosten Tokens, schreiben nur `proposed`-Zeilen und promoten nichts (n < 50).
- (b) `enable_instinct_promotion=False` bis zum Fix. Folge: sauberere Logs, Abweichung von P5.
- **Empfehlung: (a)**, Fix in der Folgephase. Ohne Validator-Fix kann nichts promotet werden.

**E6 — Gate P7 / A6 aus Phase 15**
- (a) Als erfüllt werten (Quell-Definition, deal-bezogen max 2). Folge: der letzte Phase-15-Folgepunkt ist geschlossen, und der Status-Text in root und ROADMAP wird angepasst.
- (b) Offen lassen, bis K5 nach registrierter Lesart PASS zeigt. Folge: das hängt am Bridge-Fix und am Paper-Rauschen.
- **Empfehlung: (a).** A6 wurde für den Reconcile-Backoff geschrieben; K5 hat den Begriff später breiter benutzt.

**E7 — `LLM_UNAVAILABLE` als eigener Abstain-Grund** (Fleet-Vorschlag, Session #37)
- (a) Einführen und laut melden. Folge: Guthaben-Ausfälle wie am 10-09 (338× `credit balance`) werden als eigene Klasse sichtbar, statt in `research_empty` zu verschwinden. P4/P8-Touch, neuer Enum-Wert in P10.
- (b) Nicht einführen. Folge: der Ausfall bleibt nur im Log sichtbar.
- **Empfehlung: (a)**, klein und deterministisch. Gehört in denselben Block wie E2.

**E8 — Cross-Phase-Freigaben** für die Folgephase: P5 + P8 (§4.3), P7 + P8 (§4.4), P15 + P7 (§4.2), P4 + P8 (E2 b).

## §6 Offene Operator-Aktionen (Nikinger)

| # | Aktion | Befehl / Ort |
|---|---|---|
| 1 | ✅ ~~K2-WebUI-Sichtung~~ — erledigt 2026-10-17 (Nikinger: „webui ist okay") | http://127.0.0.1:8000 |
| 2 | Push des Closeout-Commits | `git push -u origin main` |
| 3 | Optional: v3-Report persistent ablegen | `phase1_broker_wrapper/.venv/bin/python phase16_activation/scripts/autonomy_report.py --from 2026-09-30 --to 2026-10-13 --summary` |

## §7 Regeln, die weiter gelten (nicht ohne Not antasten)

- Vorregistrierungen v1–v4, die Plan-Docs und der Partial Closeout sind 📕-Snapshots. Nicht editieren, nur superseden.
- `RescueConfig.enable_gap_rescue` bleibt `False` (P6). Demo-only (Hard Rule 4). Ein Force-Trigger existiert nicht.
- Phase 13 nur mit eigener Freigabe anfassen (bei R2 erteilt, gilt nicht fort).
- Tests je Suite **getrennt** laufen lassen. Σ-Konvention: 16 Suites ohne `meta_m1_harness`.
- Der Bot läuft weiter (4 systemd-Units aktiv, `NRestarts=0`). Bot-berührende Edits nur nach P14-Ritual (Stop → Edit → Restart).

## §8 Datei-Anker

- Phasenkopf + Session-Block #38: [`CLAUDE.md`](./CLAUDE.md) · Historie: [`SESSIONS_ARCHIVE.md`](./SESSIONS_ARCHIVE.md)
- Bild: [`../docs/architecture/phase16_activation.svg`](../docs/architecture/phase16_activation.svg)
- Kriterien: [`PHASE16_AUTONOMY_PREREGISTRATION_v3.md`](./PHASE16_AUTONOMY_PREREGISTRATION_v3.md) · Brücke: [`…_v4.md`](./PHASE16_AUTONOMY_PREREGISTRATION_v4.md) · Runbook: [`PHASE16_E3_RUNBOOK_v4.md`](./PHASE16_E3_RUNBOOK_v4.md)
- Report-Skript: [`scripts/autonomy_report.py`](./scripts/autonomy_report.py) · Units: [`systemd/`](./systemd/) + `../scripts/install_units.sh`
- K6-Plan: [`PHASE16_LLM_SWITCH_PLAN.md`](./PHASE16_LLM_SWITCH_PLAN.md) · Kandidaten: [`PHASE16_PARTIAL_CLOSEOUT.md`](./PHASE16_PARTIAL_CLOSEOUT.md) §7
- Defekt-Stellen: `phase15_v4/instinct/bridge.py:146` · `phase15_v4/instinct/validator.py:97` · `phase5_execution/execution/order.py:68` · `phase8_scheduler/scheduler/safety.py:24-36` · `phase7_reward/reward/recorder.py` (`_next_retry_in_s`)

---

> 🟡 **Korrekturhinweis 2026-10-19 (Phase-17 A-3):** §4 „Unbekannt geblieben" — Scheduler-Stopp 10-08 (15:43–16:59) und Start 10-11 19:02 sind **VM-Host-Reboots**, nicht scheduler- oder systemd-eigene Ereignisse. Belegt im Journal (`journalctl --user --list-boots`): Boot-Ende 10-08 16:38:49 → Boot-Start 16:59:39 (Δ 21 min); Boot-Ende 10-11 15:40:58 mit Scheduler SIGKILL 15:40:57 (`status=9/KILL`, T10/Plan D13 = Stop-Timeout nach dem laufenden 300-s-Cycle-Sleep) → nächster Boot 10-12 21:08; Scheduler-Start 10-11 19:02 = grafischer Login. Nikinger 2026-10-17 (Plan-Session F9/F12): „Reboots vom VM-Host ausgelöst". Folge für Prereg v5 (Phase-17 Plan E-2): K1 zählt **Operator-Starts**, ein VM-Host-Reboot ist FAIL K1 mit dokumentierter Ursache „VM-Host" — kein stiller Vorfall mehr. §5 E1–E8 entschieden → [`docs/concepts/phase17_testbed_plan.md`](../docs/concepts/phase17_testbed_plan.md) §1 (T3/T5/T7/T10/T22/T23), E1 = Phase-17-Nummer, E6 = Gate P7/A6 gilt als erfüllt (T11, K6 bleibt als Phase-17-Delegation offen — D-2).
