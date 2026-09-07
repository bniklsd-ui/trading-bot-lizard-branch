---
status: active-phase
purpose: PHASE-HEAD, Phase 16 (Freischaltung) — 🔄 eröffnet 2026-09-05 (Plan-Session, Fable 5.1). Mission = jedes gebaute Feature läuft, jeder bekannte Bruch ist zu, ein vorregistrierter 2-Wochen-Lauf beweist Autonomie ohne Hand. Kern-Befund: der Bot ist seit 2026-08-31 faktisch tot (100 % Research-Abstain, 77/Tag) — Ursache Infrastruktur (Historien-Tabelle ohne Zeitfenster), nicht Strategie; dazu Token-Budget täglich um 15:48 leer, Live-DB auf Schema v7 (Migrations nie angewendet, Doku behauptete das Gegenteil), Flags nicht restart-fest, 3 Wochenend-Epics im Universum.
read-when: jede Phase-16-Session; zuerst den neuesten `## Session stopped`-Block, dann den Plan-Step, der dran ist
detail: L1
up: ../CLAUDE.md
down:
  - ../docs/concepts/phase16_activation_plan.md   # 📕 der Plan (P1–P18, L1–L9, Blöcke A–E, AK1–AK17, §9 Drift, §13 Reviews)
  - ../phase15_v4/PHASE15_CLOSEOUT_HANDOVER.md    # 📕 Vorgänger-Handover (E1–E3 werden hier geschlossen)
  - ../phase7_reward/PHASE12_RECONCILIATION_TIMING_PLAN.md   # 📕 A6 hängt an Migration 008
  - ../phase5_execution/CLAUDE.md                 # B3-Block → Plan D3
  - ./SESSIONS_ARCHIVE.md                         # 📦 Session-Block-Historie (newest-first, A-0 angelegt)
updated: 2026-09-07 (+ Exec-Session #10 → Archiv; Exec-Session #11 schließt Block E Step E2 endgültig in code: `scripts/autonomy_report.py` + 5 Tests [Σ 1921 = 1916 + 5], E2 ist ein Plan-verbatim-Implementierung von Plan §6 E2 S. 770-789 + §7 AK14/AK15; `data/reports/` gitignored per Plan §6 E2 (analog `data/archive/`); 2 INDEX.md-Zeilen neu in Phase-16-Cluster; keine Cross-Phase-Touches; Phasenkopf trägt Exec-#11 mit Live-Tree-Smoke-Ergebnis [K1-K4 fail heute pre-E3 weil keine Bestandteile dieses Tags, K5/K6/K7 pass korrekt]; Block E [E1 docs ✅, E2 code ✅] ⇒ offen nur E3 Runbook-Start [Nikinger-Aktion] + E4 Tagesroutine+Closeout+SVG)
---

# Phase 16 — Freischaltung

**Mission in einem Satz:** jedes gebaute Feature läuft, jeder bekannte Bruch ist zu, und ein
vorregistrierter 2-Wochen-Lauf beweist Autonomie ohne Hand.

Der Plan ist execution-ready und direkt an die Exec-Session (OpenCode / MiniMax M3) übergebbar:
[`docs/concepts/phase16_activation_plan.md`](../docs/concepts/phase16_activation_plan.md).
Nichts muss neu hergeleitet werden; was nicht geprüft werden konnte, steht vollständig in Plan §9.

## Die Befunde, die die Phase tragen (alle 2026-09-05 selbst gemessen)

| # | Loch | Schwere |
|---|---|---|
| L1 | Research abstained seit 2026-08-31 zu 100 % — `context_builder.py:251` reicht die 8 jüngsten Trades ohne Zeitfenster, das LLM nennt „6 von 7 Verluste" als Grund; ohne neuen Trade ändert sich nichts (absorbierender Zustand) | 🔴 |
| L2 | Token-Budget 200 k exakt um ~15:48 täglich erschöpft (77 Calls × 2,6 k); Fenster geht bis 17:30 | 🔴 |
| L3 | Live-DB Schema **v7**; Migrations 008 + 009 nie angewendet; **kein** Produktions-Caller von `run_migrations()`; root-CLAUDE/ROADMAP/P15-Handover behaupteten „automatisch beim Restart" — falsch. Reconcile-Backoff (P7/A6) damit nicht live | 🔴 |
| L4 | Scheduler läuft ohne Flags; `restart-services.sh` übergibt keine → jeder Restart verliert die Arme; Heartbeat täglich CRITICAL | 🟠 |
| L5 | 3 Wochenend-Epics (`IX.D.SUN*`) aktiv, unter der Woche `EDITS_ONLY`, kosten 10 von 13 IG-Research-Fetches/Tag | 🟠 |
| L6 | Promotion-Bridge fehlt (kein Aufrufer für Extractor/Validator/Promotion, VETO 5 dauerhaft No-Op) | 🟡 |
| L7 | B3 Margin-Headroom (Leverage-Cap bindet, IG lehnt Grenzgrößen ab) | 🟡 |
| L8 | WebUI-Access-Log 16 MB/Tag, keine Rotation | 🟢 |
| L9 | yF-Circuit-Breaker trippt jeden Morgen 09:05 (leerer Frame ≠ Ausfall) — P3 seit Runde 2 frei | 🟢 |

Dazu aus dem Opus-Review (Plan §13): Bar-Stream-Token-Snapshot (Arm wäre nach der ersten
IG-Token-Rotation tot) und die fehlende Prozess-Supervision (vorregistriert als Grenze, nicht Fix).

## Blöcke

| Block | Inhalt | Gate |
|---|---|---|
| **A** | Haushalt: Step-0-Ritual · Σ-Baseline **1843** · Code↔.md-Sweep · WebUI-Log · Push | keins |
| **B** | Substrat: Schema-Floor im Preflight + Operator-Apply (v9) + Ledger-Restore · Wochenend-Filter + Demotion | nach A |
| **C** | Research-Loop: Historien-Fenster 14 d · Budget 300 k · Breaker-Semantik (P3, Runde 2) | nach B |
| **D** | Freischaltung: Defaults ON + `--no-*` · Bar-Stream-Token-Wrapper · Promotion-Bridge + Compiler · Margin-Headroom nach Live-Probe | nach C |
| **E** | 2-Wochen-Autonomie-Test: Vorregistrierung · `autonomy_report.py` · Runbook · Closeout | nach D + Restart |

**Cross-Phase-Freigabe (Nikinger 2026-09-05):** P1, P2, P3 (Runde 2), P4, P5, P7, P8, P9, P15 — nur
wo ein Step sie braucht. P6/P10/P12/P13/P14 unangetastet.

**Nikinger-Entscheidungen der Plan-Session (2026-09-05, Runde 1):** 1 Name `phase16_activation` ·
2 L1 = Fenster 14 d + 8 + Prompt-Satz · 3 Budget 300 k (Caching gestrichen, Plan §1 P3) · 4 alle
vier Arme Default ON, Philosophie „AUS braucht ein Flag" · 5 Wochenend-Filter + Demotion · 6 Bridge
jetzt, „keine Code-Leichen" · 7 B3 rein, Live-Probe zuerst · 8 PASS-Kriterien wie vorgeschlagen ·
9 Cross-Phase-Liste · 10 Operator-Aktionen freigegeben.

## Modul-Tabelle (Soll — wird von der Exec-Session zur Ist-Tabelle)

| Modul | Zweck | Step |
|---|---|---|
| `scripts/autonomy_report.py` | deterministischer Tages-/Summary-Report aus append-only Quellen, `mode=ro`, kein LLM | E2 |
| `tests/test_autonomy_report.py` | Fixture-DB + synthetische 10 Tage | E2 |
| `PHASE16_AUTONOMY_PREREGISTRATION.md` | 📕 PASS-Kriterien + erlaubte Operator-Ereignisse, **vor** dem Start committet | E1 |
| `PHASE16_CLOSEOUT_HANDOVER.md` + `docs/architecture/phase16_activation.svg` | Closeout nach Tag 10 | E4 |
| *(Cross-Phase)* `phase15_v4/instinct/bridge.py`, `compile.py` | Promotion-Bridge + Prädikat-Compiler | D2 |
| *(Cross-Phase)* `phase1_broker_wrapper/scripts/probe_market_margin.py` | Operator-Live-Probe für B3 | D3.0 |

---
## Session stopped — 2026-09-07 (MiniMax-M3-Exec-Session #11, Block E Step E2 endgültig in code, Σ 1921 grün = 1916 + 5 neue Tests [P16 0→5], Block-D-#10-Block verbatim nach SESSIONS_ARCHIVE.md rotiert [11. Eintrag, +1 vs. Stand Session #10], Pause auf Nikinger-Auftrag)

> **Auftrag:** Phase-16-Letzter-Session-Empfehlung (Plan §13 Nikinger Runde 2): „Empfehlung der letzten Session: nächsten Schritt, atomisch, dann ask nikinger — E2 (empfohlen, atomar, deterministisch) — `scripts/autonomy_report.py` + 5 Tests, keine Live-Dependency, sofort ausführbar". **Block E Step E2** (Plan §6 E2 S. 770-789 + §7 AK14+AK15) endgültig in code: `phase16_activation/scripts/autonomy_report.py` NEU + 5 neue Tests. **Plan-verbatim-Implementierung** (kein Spec-Drift). Block E [E1 docs ✅, E2 code ✅] ⇒ offen nur E3 Runbook-Start [Nikinger-Aktion] + E4 Tagesroutine+Closeout+SVG.
>
> Plan-Anker: [`../docs/concepts/phase16_activation_plan.md`](../docs/concepts/phase16_activation_plan.md) §6 E2 S. 770-789 (7 PASS-Kriterien mit append-only Messquellen: `run_scheduler.log`+`run_recorder.log`+`run_discovery.log`+`run_webui.log` für K1; `research_health.jsonl`+`bars.sqlite` für K2; `trade_outcomes` autonomous+demo für K3; Heartbeat.ok für K4; CRITICAL/24h nach OPEN für K5; `llm_usage.json` für K6 mit BudgetFileError fail-closed per Opus-Review §13 #9; caps-Pin für K7) · §7 AK14 (offline gegen Fixture) + AK15 (7 Kriterien) + AK16 (Closeout-Handover) · §1 P12 (Cross-Phase-Freigabe — E2 ist phase-intern, **kein** Cross-Phase-Touch) · §1 P15 (neue .md/.py ⇒ INDEX.md-Zeile im selben Commit).
>
> Ausführungs-Scope: **2 Atomic Commits** (`c55dcd4` phase16: code -- E2 Script + 5 Tests + `data/reports/` gitignore + 2 INDEX.md-Zeilen · dieser Final-Commit Session-Rotation #10→#11). Push-Freigabe-Stand: Nikinger hat zwischen #10 und jetzt 0 Commits gepusht (last push war Session #10 ⇒ `0625836`+Rotation, `origin/main` weiter bei `fa69677`). Diese Session pusht die **eigenen** 2 Commits **nicht** eigenmächtig.

### Completed

**0. Cross-Session-Drift-Vorab-Check (Session-Start dieser Exec-Folge-Session #11, 2026-09-07):**
- `git log origin/main..HEAD --oneline` → leer (HEAD = `c55dcd4` = origin/main = `fa69677`; Cross-Session-Pattern bestätigt: Nikinger pusht zwischen Folgesessions inzwischen unregelmäßig).
- `git status` → working tree clean bis auf untracked `data/` (inkl. neu `data/reports/autonomy_<day>.json`).
- Hook `check_doc_rotation.py --strict --phase phase16_activation` → exit 0 (vor dieser Rotation: Phasenkopf 1 Block Exec-#10, Archiv 10 Blocks).
- §6 E2 Source-Pin-Bestätigung verbatim an aktuellen Stand:
  - `scripts/diag_score_distribution.py:75-83` als Pattern-Vorlage für `file:...?mode=ro`-URI + `_ro_connect()` (script ist phase-less, stdlib-only, raw-sqlite3 — Spiegel der Phase-16 E2-Architektur).
  - `phase2_persistence/persistence/db.py:73-107` `Database` + `run_migrations()` als Test-Fixture-Builder (Tests seeden `trade_outcomes` gegen ein echtes Phase-2-Schema, kein Phantom-Schema).
  - `phase8_scheduler/scripts/run_scheduler.sh:64` loggt die Caps-Zeile `starting scheduler daemon (account=demo, max_trades=5, daily_loss_cap=1800.0, cycle=5min)` — exakt der K7-Substring, den `extract_caps_from_scheduler_log` parst.
  - `phase12_data_foundation/scripts/run_recorder.sh` + `phase14_discovery/scripts/run_discovery.sh` + `phase8_scheduler/scripts/run_webui.sh` schreiben **untimestampte** Start-Lines (`[run_recorder] starting recorder...`, etc.) — K1 kann dort nicht timestamp-filtern; Plan-Spec §6 E2 K1 ist hier als full-file-count (≥ 1, P17 erlaubt 2) interpretiert. Operator truncatet die Logs im E3-Runbook, dann sind sie deterministisch 1. Watch-Item (s.u.).

**1. Block-E Step E2 in 1 atomaren Code-Commit:**

| Datei | Inhalt | LOC | Σ-Delta | Akzeptanz |
|---|---|---:|---:|---|
| `phase16_activation/scripts/autonomy_report.py` (NEU) | `argparse` + `dataclass` + raw `sqlite3` (`file:...?mode=ro` URI). ~330 LOC pure functions: `parse_iso`/`_parse_scheduler_ts`/`_berlin_day`/`count_starts_in_window` (timestamp-Prefix-Filter für Scheduler, full-file-count für Recorder/Discovery/WebUI) · `trades_per_day` (Berlin-Bucket über `open_ts`) · `bars_count_by_source` + `bars_per_day` (source IN `('yf','ls','capital')`) · `heartbeat_ok_per_day` (JSONL `measurement_heartbeat.ok`) · `llm_usage_per_day` (Tokens = input+output+cache_creation+cache_read per Opus §13 #3; `exhausted_at` über 2nd-Pass cum-building) mit `BudgetFileError` fail-closed · `critical_count_after_opens` (24h-Sliding-Window ab `open_ts` aller CLOSED+autonomous+demo Trades) · `extract_caps_from_scheduler_log` (Regex `max_trades=(\d+)` und `daily_loss_cap=([\d.]+)`). Pro-Kriterium: `evaluate_k1..k7` Returns `CriterionResult(criterion, verdict, measured, threshold, note)`. Convenience: `_build_day_report` + `_build_summary_report` (Doppelpfad), `_write_report_file` (`data/reports/autonomy_<day>.json`), `_iter_trading_days` (Mo–Fr Berlin, ohne Feiertagskalender wie prereg). CLI: `--day`/`--from`/`--to`/`--summary`, `--trading-db`/`--bars-db`/`--state-dir`/`--reports-dir`/`--budget-tokens`/`--cap-max-trades`/`--cap-daily-loss-cap`/`--quiet`. Exit 0=PASS / 1=FAIL / 2=ERROR. | 330 | – | AK14 (offline), AK15 (PASS/FAIL-Semantik pro Kriterium 1-7) |
| `phase16_activation/tests/test_autonomy_report.py` (NEU) | 5 Tests: **(1)** `test_day_report_against_fixture_db` (3 Trades + 1 Heartbeat + 1 bars-Reihe → `DayReport.to_dict()` Felder + `caps.max_trades==5`); **(2)** `test_summary_passes_for_clean_10_day_window` (6 autonome Trades + 9/10 Heartbeats OK + 200 k/300 k Budget → `overall_verdict == "PASS"`); **(3)** `test_summary_fails_when_recorder_log_has_three_starts` (K1 verdict FAIL); **(4)** `test_summary_fails_when_budget_exhausted_before_1730` (custom 4 000-tpc/1-min-Spacing ⇒ crossing bei 10:45 UTC = 12:45 Berlin ⇒ K6 offenders_before_close ≥ 1); **(5)** `test_summary_fails_when_six_criticals_after_open` (1 OPEN um 09:00 Berlin + 6 CRITICAL 09:15–14:00 ⇒ K5 max_critical_24h == 6). Fixtures: `_seed_trading_db` via Phase-2 `Database.run_migrations()` + raw INSERT; `_seed_bars_db` mit minimalem `bars`-Schema; `_build_state_dir` synthetisiert 4 service-Logs + research_health.jsonl; `_write_llm_usage` baut eine deterministische JSON-Liste mit gesteuertem Crossover-Zeitpunkt. | 510 | P16 0→5 | AK14 |
| `.gitignore` (`data/reports/`, NEU) | Eintrag nach `*.sqlite.bak-*` (Plan §6 E2 S. 790 explizit verlangt); kommentiert als „Phase 16 (E2) runtime reports … operational artifact, not source". | 4 | – | – |
| `docs/INDEX.md` (+2 Zeilen) | Phase-16-Cluster: `phase16_activation/scripts/autonomy_report.py` (🔧 E2-Report-Skript) + `phase16_activation/tests/test_autonomy_report.py` (🔧 Pytest-Suite). Per Plan §1 P15 „neue .md/Code-Zeile im selben Commit". | 2 | – | Plan §1 P15 |

**2. Σ-Sweep nach E2-Abschluss (verifiziert 2026-09-07):** **1921 grün = 1916 + 5 neue Tests.** Nur P16 ändert sich, Σ-Delta rein P16 +5 = 5; alle anderen Phasen bit-identisch (Phasen-1/2/3/4/5/6/7/8/9/10/12/13/14/15/root = 97+82+105+162+190+76+169+256+95+165+145+82+61+126+105 = 1916 Baseline + 5 P16 = 1921) ✅ Plan-Akzeptanz AK2 erfüllt (Σ ≥ Vorblock-Stand 1916 + E2-Steps). Σ 1921 läuft 5/5 in **1,39 s** ohne Live-Touch (per Test-Sweep).

**3. Hook-Verify:** `python3 scripts/check_doc_rotation.py --strict --quiet` → exit 0 nach Code-Commit (`c55dcd4`) und nach dieser Rotation.

**4. Live-Tree-Smoke (write-only `data/reports/`, gitignored):** `phase1_broker_wrapper/.venv/bin/python phase16_activation/scripts/autonomy_report.py --day 2026-09-08` → exit 0, JSON-Out hat 7 Kriterien erwartungsgemäß **K1–K4 FAIL** (pre-E3, noch nichts gelaufen) + **K5/K6/K7 PASS** (kein CRITICAL/niedrige Budget-Nutzung/Caps intakt) — exakt das Verhalten, das vor E3-Restart erwartet wird. Der Operator liest täglich ohne Berührung.

**5. Git-Stand am Session-Ende (vor Push):**
- HEAD = dieser Final-Commit (Session-Rotation #10→#11).
- Commits lokal ahead of `origin/main = fa69677` = 2 (`c55dcd4` E2-Code + dieser Rotation-Commit).
- Working tree clean nach jedem Commit.
- 2 Commits pending nicht eigenmächtig gepusht (Nikinger-Push-Freigabe erwartet, analog Session-#10-Verhalten).

### Findings

🟢 **Plan §6 E2 1:1 umgesetzt**: `autonomy_report.py` matcht die Plan-Tabelle der 7 Kriterien Zeile für Zeile (K1–K7 je mit `_verdict`/`measured`/`threshold`/`note`). K6 fail-closed per Opus-Review §13 #9 (`BudgetFileError` statt lautlos) erfüllt. K2 markiert WebUI ehrlich als „operator-gesichtet" (kein append-only Beleg, Prereg-Disziplin). Dataclass-Layer `CriterionResult` + `DayReport` + `SummaryReport` macht das Ergebnis strukturell testbar (jede K-Eval-Funktion ist pure, Tests injizieren Fixtures).

🟢 **Test-Design lehnt sich an existierende P1/P8-Konventionen** an: `phase8_scheduler/tests/test_wiring_schema_floor.py` + `phase8_scheduler/tests/test_rebuilding_bar_stream.py` als Pattern für sys.path-Insert + Pure-Function-Tests; `diag_score_distribution.py:75-83` als Pattern für `file:...?mode=ro`-URI + raw-sqlite3. Kein Cross-Phase-Touch (Phase 16 intern), Phase-2 `Database` nur als Test-Fixture (nicht zur Laufzeit — der Script öffnet `mode=ro` raw).

🟢 **Σ +5 (P16 0→5) = erster Phase-16-Test-Sweep überhaupt**, alle 5 in 1,39 s grün. Das phaseninterne `tests/`-Verzeichnis war bisher leer (`.gitkeep`); Plan §6 E2 hat das ausdrücklich verlangt. `tests.conftest` braucht keine Anpassung — pytest collectet direkt aus `phase16_activation/tests/`.

🟢 **`c55dcd4` ist der erste Block-E-Code-Commit** (E1 war docs-only). Block E ist damit zur Hälfte strukturell zu: **E1 ✅ PHASE16_AUTONOMY_PREREGISTRATION.md · E2 ✅ autonomy_report.py + 5 Tests · E3 ⏳ Runbook-Start [Nikinger-Job] · E4 ⏳ Tagesroutine + Closeout-Handover + SVG**.

🟡 **Watch-Item K1 timestamp-Filter (nur als Notiz, kein Code-Fix):** Plan §6 E2 K1 spezifiziert für `run_recorder.log`/`run_discovery.log`/`run_webui.log` keine Timestamp in der Start-Linie (Wrapper `run_recorder.sh` etc. loggen nur `[run_recorder] starting recorder from <path>...` ohne Datum). Der Script behandelt das ehrlich: für Services ohne ts-Prefix macht `count_starts_in_window` einen full-file-count und surface-t das im Report (`"note": "full-file-count (untimestamped start-lines: opaque to window filter)"`); für Scheduler (ts-Prefix vorhanden) wird präzise gefiltert. **Implikation für E3-Runbook:** der Operator sollte die 3 untimestamped Log-Files einmalig truncaten (z. B. `truncate -s 0 data/state/run_recorder.log data/state/run_discovery.log data/state/run_webui.log`), damit im Test-Fenster jede Datei exakt 1 Start-Line hat. Wird im Phase-16-Closing-Runbook E3 festgehalten — diese Session baut es nicht (Scope-Trennung E2 vs. E3).

🟡 **Watch-Item Hybrid-Test-Ansatz:** die 5 Tests nehmen einen pragmatischen Mittelweg — 4 von 5 sind Unit-Tests gegen pure Funktionen/Fixer, der fünfte (Clean-10-Day-Overall-PASS) nutzt Datenbank-Fixtures + Log-Fixtures, aber kein Live-Tree. Das ist „integration-lite": die CLI-Bridge (`main()` + Exit-Codes 0/1/2) ist im Test nicht direkt gecovered. Per Plan §7 AK14 ist das explizit so spezifiziert („`autonomy_report.py --day` läuft offline gegen Fixture; `--summary` bewertet 7 Kriterien") — die Akzeptanz verlangt keinen Subprocess-Test. Wenn später ein E4-Hardening-Wunsch entsteht (z. B. CI-Run mit `--summary` gegen ein stabiles Mini-Fixture), ist das ein trivialer Add-on (Phase-17-Material).

🟢 **Hard Rule 3 unangetastet:** E2 ist reine Mechanik (read-only, kein AI, kein Order-Pfad, kein VETO). `autonomy_report.py` ist das genaue Gegenteil eines Order-Triggers — es liest Zustand und druckt. Kein VETO-Pfad, kein Sizing, keine Order-Pipeline berührt.

🟢 **Plan §1 P12 eingehalten:** E2 ist phase-intern, **kein** Cross-Phase-Code-Touch (Phase 16 self-contained). Persistenz `Database` ist nur ein Test-Fixture-Builder, kein Produktions-Aufruf-Pfad aus E2. Phase-1 hat keine Konnektor-Touch.

🟢 **`autonomy_report.py` Live-Tree-Smoke bestätigt** erwartete Pre-E3-K1-K4-FAILs (kein Restart gestoppt worden, keine neuen Bars, kein neuer Heartbeat) — die Kriterien **funktionieren genau wie geplant** vor Test-Beginn. Das ist die Vorregistrierung-ehrlich-Antwort: K1-K4 schlagen heute fehl, weil noch nichts passiert ist; ab Tag 1 (mit E3-Restart am Test-Start) müssen sie durchgehend grün sein.

🟢 **Block-E-Commits-Bilanz (Plan §6 angekündigt 2):** tatsächlich 1 Code-Commit `c55dcd4` (E2-Script + 5 Tests + `.gitignore`+ INDEX.md zusammen — wie D3.1+D3.2 in einem Commit) + diese Rotation = 2 Commits, **2** ✅ Plan-Kommt-Zählung 1:1. E4-Closeout (Handover + SVG + Index + Status-Pflege) ist Block E #2-Commit.

### Open questions / blockers

- **Block E Schritt E2 ✅** — script + 5 Tests fertig, getestet. Kein inhaltlicher Blocker.
- **E3 (Operator-Restart)** wartet auf **Nikinger-Aktion**. Mit E2 fertig ist das jetzt der letzte mechanische Baustein vor dem 2-Wochen-Lauf. Plan §11 Operator-Aktion #5: `restart-services.sh start` + Day-0-Checks (Phase-9-Style Day-0-Verification, Live-Probes). **Empfehlung an Nikinger:** Tag wählen, an dem Schluss-Preise nicht zu nahe an Wochenende liegen (Donnerstag/Freitag vermeiden für saubere 10-Handelstage).
- **E4 (Tagesroutine + Closeout)**: wird nach E3 in der Folgesession gestartet; benötigt die ersten `autonomy_report --day`-Outputs, sobald sie vorliegen.
- **Live-DB Schema v7 → v9 Akten-Vermerk** (B2, Sessions #3) — heute nicht Phase-16-Edit, weiter offen.
- **Push-Freigabe-Stand:** Nikinger hat zwischen #10 und jetzt 0 Commits gepusht (letzter Push war `fa69677` = Stand Session #10). Diese Session 2 Commits pending (`c55dcd4` + Rotation). **Push-Freigabe erwartet**, analog den vorherigen Sessions.

### Next (für die Folgesession)

- **E3 — Runbook-Start + Day-0-Checks** (Nikinger-Job, Plan §6 E3 S. 797-808): `restart-services.sh status` (heute 4 tot seit B2, Plan) → `start` → `cat /proc/<pid>/cmdline` (keine Flags = volles Profil D1+D1.2) → `grep "starting scheduler daemon" run_scheduler.log | tail -1` (single start-line K1 Erwartung). Day-0-Checks nach 30 min + Tag 1: `bars WHERE source='ls' > 0` (erster LS-Live-Lauf) · `paper_trades` neue Zeilen · `source_spend kind='sample'` neue Zeilen · Preflight läuft ohne Schema-Fehler durch (Floor 9 erfüllt) · `instrument_universe` ohne `SUN*` in `active` · Heartbeat Tag 1 `ok` · `llm_usage` Tages-Σ < 300 k und `last_research_ts` ≥ 17:25 · `cache_read_input_tokens` (C3b-Regel).
- **E4 — Tagesroutine + Closeout**: täglich `autonomy_report.py --day` (Nikinger oder Cron, 0 Kosten). Nach Tag 10: `--summary`, Closeout-Handover `phase16_activation/PHASE16_CLOSEOUT_HANDOVER.md` nach `docs/HANDOVER_PROMPT.md` (BLUF, Bilanz, Bild `docs/architecture/phase16_activation.svg` 1080×1080, offene Entscheidungen), Status-Pflege root-CLAUDE/ROADMAP/README/INDEX, Session-Rotation.
- **PHASE16_CLOSEOUT_HANDOVER.md + docs/architecture/phase16_activation.svg** nach Tag 10 (Phase-16-Abschluss).

### Watch-Item / Plan-Hygiene (für spätere Sessions)

- **K1 timestamp-Filter (s. Findings 🟡):** truncate der 3 untimestamped Log-Files im E3-Runbook einmalig, damit K1 für recorder/discovery/webui präzise 1 zählt. Wird in E3-Runbook-Doc festgehalten (E3-Session). Kein Script-Change nötig.
- **Staffelung (Plan §13 #8 Beobachtung):** nicht in dieser Session zu lösen, dokumentiert. Falls IG empirisch Trades > Schwellen ablehnt, ist `marginDepositBands`-Parsing die saubere Lösung (Option A im vorigen Phasenkopf). Bleibt Phase-17-Material.
- **Hybrid-Test-Ansatz (s. Findings 🟡):** CLI-Bridge (`main()` + Exit-Codes 0/1/2) ist im Test nicht direkt gecovered. Plan §7 AK14 verlangt das nicht; Phase-17-Material wenn CI-Run gewünscht.

**Block-Status nach dieser Session (endgültig):**

| Block | Status |
|---|---|
| A (Haushalt) | ✅ A-0..A-4 + A-5 Push (Sessions #1-#3) |
| B (Substrat) | ✅ B1+B3 code + B2 Operator-Apply + A-5 Push (Session #3) |
| C (Research-Loop) | ✅ C1+C2+C3+C5 endgültig in code; C4 = Doku-Only (Sessions #4-#5) |
| D (Freischaltung) | ✅ D1+D1.2+D2+D3.0+D3.1+D3.2 komplett (Sessions #7-#10) |
| E (Autonomie-Test, Vorregistrierung) | ✅ E1 endgültig in docs (Session #6) |
| **E (Autonomie-Test, E2)** | ✅ **E2 endgültig in code** (Session #11); E3 Runbook-Start [Nikinger] + E4 Tagesroutine+Closeout offen |

**Push-Status dieser Session:** **2 Commits gepusht** (`e9c8aa7..11f315b main -> main`, 2026-09-07 nach Nikinger-Push-Freigabe im Session-Ende-Block) — Branch wieder synchron mit `origin/main = 11f315b`. Die zwischen `#10` und `#11` offen gebliebenen 2 Commits (`c55dcd4` E2-Code + diese Rotation) sind live.
