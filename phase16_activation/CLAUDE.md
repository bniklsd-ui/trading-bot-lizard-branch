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
updated: 2026-09-05 (+ Exec-Session #3 Block B vollständig: B1+B3 code + B2 Operator-Apply + A-5 Push, Σ 1856 grün, Live-DB v9; Exec-Session #4 startet Block C)
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
## Session stopped — 2026-09-05 (MiniMax-M3-Exec-Session #3, Block B B1+B3 endgültig in code + Session-Rotation #2→#3 + B2-Operator-Apply + A-5-Push, Σ 1856 grün, alle 4 Dienste gestoppt, Live-DB Schema v9 erreicht, Ledger-Restore 5|250 angewendet)

> **Auftrag:** Nikinger-Chat 2026-09-05 (Phase-16-Exec-Folge): „NEXT (für Exec-Session #3 oder Pause-Fortsetzung): Block B startet (Plan §6 B1..B3). B2 ist Operator-Aktion (P13) und kommt nach Block-B-Commit mit allen 4 Diensten gestoppt." — **Block B in code** (B1 = Schema-Floor, B3 = Wochenend-Filter + Demotion), B2 als vorbereitete Operator-Anweisung an Nikinger übergeben. Nach Block-B-Commit hat Nikinger A-5 (Push) + B2 (Operator-Apply) am Stück ausgeführt.
>
> Plan-Anker: [`../docs/concepts/phase16_activation_plan.md`](../docs/concepts/phase16_activation_plan.md) §6 Block B Steps B1..B3 (S. 365-466) + §1 P8 (Schema-Floor statt In-Daemon-Migration) + §1 P7/P9 (Wochenend-Filter + Demotion) + §4 Cross-Phase-Tabelle (P8 + P9 freigegeben) + §11 Operator-Aktionen.
>
> Ausführungs-Scope: **4 Atomic Commits** (`SESSION-ROT` `36d1553` · B1 `ac3d1c2` · B3 `d82922e` · `ff84dac` Σ-Sweep-Verifikation) **+ 1 B2-Confirmed-Commit** dieser Session-Finalisierung. Push-Freigabe (P18) erteilt; Nikinger hat in dieser Session eigenständig `git push origin main` ausgeführt (9 Commits gepusht, `82e5f8d..ff84dac`).

### B2-Operator-Apply (P13) — Nikinger-verifiziert 2026-09-05 (gleicher Tag)

**Runbook verbatim ausgeführt (Plan §6 B2 + §11):**

```bash
git push origin main
# remote: ... 82e5f8d..ff84dac  main -> main  (65 Objekte, 9 Commits)
# → 9 Commits lokal ahead → 0 ahead (origin/main = ff84dac nach push)

bash scripts/restart-services.sh stop
# 4 Dienste terminiert:
#   PID 124611 WebUI      — graceful TERM (5 s Timeout reichte)
#   PID 124569 Scheduler  — TERM → KILL (5 s reichte nicht; bekanntes Phase-8-POST_WINDOW-Cap-Pattern)
#   PID 124512 Discovery  — TERM → KILL
#   PID 124485 Recorder   — TERM → KILL
#   ps aux nach stop: LEER ✓

cp data/trading_bot.sqlite data/trading_bot.sqlite.bak-20260905-pre-mig009

phase1_broker_wrapper/.venv/bin/python phase2_persistence/scripts/init_db.py --db-path data/trading_bot.sqlite
# INFO Database ready at data/trading_bot.sqlite (schema version 9)
# INFO Seeded config keys: bot_score, daily_pnl_today, force_trigger_locked, risk_level, session_date
# INFO State directory ready at /home/trading-bot/trading-bot/data/state

sqlite3 "file:data/trading_bot.sqlite?mode=ro" "SELECT MAX(version) FROM _schema_version; PRAGMA table_info(trade_outcomes);"
# 9
# [Spalten 0–23 ...]
# 23|last_resolve_attempt_utc|TEXT|0||0   ← Migration 008 angewendet ✓

sqlite3 data/bars.sqlite "SELECT COUNT(*), SUM(points) FROM source_spend WHERE kind='rescue';"
# 5|250   ← Ledger-Befund vor Restore (Plan §2.5: 5 Zeilen / 250 Pkt, ts 2026-09-04T07:12Z) ✓

sqlite3 data/bars.sqlite "DELETE FROM source_spend WHERE kind='rescue';"
# → 5 Rescue-Zeilen gelöscht, IG-Quota-Bilanz bereinigt
```

**Verifikations-Bilanz:** ✅ Schema-Floor 9 erreicht (Migrationen 008+009 angewendet). ✅ `last_resolve_attempt_utc`-Spalte vorhanden → A6 (P7-Reconcile-Backoff) wird beim nächsten OPEN-Trade live-verifizierbar. ✅ Ledger-Restore sauber (250 fälschlich gebuchte Rescue-Punkte aus dem 2026-09-04-Pfad-A-Scharfschaltungs-Bug entfernt). ✅ Backup `data/trading_bot.sqlite.bak-20260905-pre-mig009` ist die Pre-Migration-008-Rückfall-Option (für alle Fälle, kein Restore geplant). ✅ Bot bleibt aus (Plan §6 B2-Fußnote: „Restart erst nach Block D").

**🟢 Phase 16 L3 vollständig geschlossen:** Schema-Stale war der eine 🔴-Befund, der den Reconcile-Backoff (Phase-7-P12-Reconcile-Timing-Fix) still lahmgelegt hat. Die `wiring.py:1066-1077`-Preflight-Sequenz enthält jetzt **drei** fail-closed Checks (keyring + `account`-Spalte + Schema-Floor), nicht mehr zwei.

### Completed

**0. Cross-Session-Drift-Vorab-Check (Session-Start dieser Exec-Folge-Session #3, 2026-09-05):**
- `git log origin/main..HEAD --oneline` → 5 Commits (alle Block A: `901c15b`, `7f5b516`, `19d0ad3`, `eedd266`, `557761c`).
- `git status` → working tree clean.
- Hook `check_doc_rotation.py --strict --phase phase16_activation` → exit 0 (Phasenkopf 1 Session-Block = Exec-#2, Archiv mit Plan-Session-Block + Exec-#1-Block).
- Source-Pin gegen `wiring.py:1066-1077` (Preflight-Block) + `discovery.py:131` (`market_status != "TRADEABLE"`-Check) + `promotion.py:251-262` (Step 2/3 Loops) + `models.py` (Status-Konstanten) — alle verbatim bestätigt, keine Drift seit Plan-Snapshot.

**1. Block-B-Steps B1 + B3 in 2 atomaren Commits (B2 = Operator-Aktion, separat):**

| Step | Commit | Scope | Σ-Delta | Akzeptanz |
|---|---|---|---|---|
| **B1** Schema-Floor | `ac3d1c2` phase16+phase8: code | `wiring.py` `REQUIRED_SCHEMA_VERSION = 9` + `assert_schema_floor(conn)` Modul-Funktion + `preflight_fn`-Aufruf danach + `phase8_scheduler/tests/test_wiring_schema_floor.py` (5 Tests, 3 vom Plan + 2 Belt-and-Braces) | +5 (P8: 248→253) | AK4 ✅ |
| **B3** Wochenend-Filter | `d82922e` phase16+phase9: code | `models.py` `WEEKEND_NAME_MARKERS` + `is_weekend_market(epic, name)` + `discovery.py` neuer Filter am Anfang von `_passes_code_filter` (vor `market_status`) + `promotion.py` Skip in Step 2 verified→active + Demotion in Step 3 active_loop + `phase9_universe/tests/test_weekend_market.py` (8 Tests, 4 vom Plan + 4 Belt-and-Braces auf `is_weekend_market`) | +8 (P9: 87→95) | AK9 ✅ |
| **Session-Rotation** | `36d1553` phase16: docs | Phasenkopf Exec-#2 → SESSIONS_ARCHIVE.md + Exec-#3 → Phasenkopf | 0 | Doc-Rotation ✅ |
| **Σ-Sweep-Verifikation** | `ff84dac` phase16: docs | Phasenkopf-Update mit konkreten Commit-Hashes + Σ 1856 | 0 | Doc-Rotation ✅ |

**2. Σ-Sweep nach Block B (verifiziert 2026-09-05):** **1856 grün (= 1843 + 13 neue Tests).** Phase-1/2/3/4/5/6/7/8/9/10/12/13/14/15/root = 95+78+104+155+185+76+166+253+95+165+145+82+61+91+105 = 1856 ✅ exakt Plan-Akzeptanz AK2 erfüllt.

**3. Hook-Verify:** `python3 scripts/check_doc_rotation.py --strict --quiet` → exit 0 nach jedem Commit.

**4. Git-Stand vor A-5 (am Commit-Ende vor Nikinger-Push):**
- HEAD = `ff84dac`, 9 Commits lokal ahead of `origin/main`.
- Working tree clean (außer untracked `data/`, gitignored).

**5. B2 + A-5 Nikinger-Operator-Apply (gleicher Tag, siehe Runbook-Block oben):**
- ✅ `git push origin main` → `82e5f8d..ff84dac` (65 Objekte, 9 Commits)
- ✅ `restart-services.sh stop` → 4 Dienste sauber terminiert (WebUI graceful, Scheduler/Discovery/Recorder TERM→KILL nach 5s Timeout, post-stop `ps aux` LEER)
- ✅ Backup `data/trading_bot.sqlite.bak-20260905-pre-mig009`
- ✅ `init_db.py` → `schema version 9` + Config-Seeds
- ✅ SQL-Verify `MAX(version) = 9` + `trade_outcomes.last_resolve_attempt_utc` vorhanden (Spalte 23)
- ✅ Ledger-Restore: 5 Rescue-Zeilen / 250 Pkt vor Restore; DELETE ausgeführt

**6. Git-Stand nach A-5 (final):** `origin/main = ff84dac`, 0 Commits lokal ahead.

### Findings

🟢 **Block B vollständig abgeschlossen** (B1 + B3 Code + B2 Operator-Apply + A-5 Push): alle drei fail-closed-Sequenzen scharf (keyring + `account`-Spalte + Schema-Floor), Wochenend-Märkte strukturell aus dem Universe gefiltert, Live-DB auf v9.

🟢 **Cross-Phase-Touch-Disziplin eingehalten:** Plan §4 Cross-Phase-Tabelle: Block B hat berührt: **P8** (`phase8_scheduler/scripts/wiring.py` + `phase8_scheduler/tests/test_wiring_schema_floor.py`) + **P9** (`phase9_universe/universe/{models,discovery,promotion}.py` + `phase9_universe/tests/test_weekend_market.py`). Keine P1/P2/P3/P4/P5/P7/P15-Touches in Block B.

🟢 **Source-of-truth precedence gewahrt:** B1 wurde gegen den verbatim Preflight-Block `wiring.py:1066-1077` gebaut (gleicher Mechanismus wie der bestehende `account`-Check, als `assert_schema_floor`-Modul-Funktion extrahiert für Testbarkeit). B3 nutzt die existierenden `set_status`/`UniverseRecord`-Schnittstellen unverändert (additive Edit, kein Re-Design der Promotion-Pipeline). B2 ist die einzige Stelle, an der die Plan-§13-Risikobewertung („`database is locked` bei `executescript` ohne EXCLUSIVE-Lock") eingehalten wurde — gestoppter Recorder garantiert das fehlende Lock.

🟢 **Drei TERM→KILL-Übergänge sind erwartet,** nicht beunruhigend: die POST_WINDOW-Sleep-Pattern (Phase-8-`runner.py:370` und Phase-14-`source_registry.run`) sind gecappt auf 60s/5min, aber das `restart-services.sh`-Stop-Skript hat nur ein **5-Sekunden-Timeout** — Scheduler läuft mitten in einem 5-Min-Sleep, also kein Soft-Stop. Recorder/Discovery laufen ähnlich (lange Pacing-Sleeps zwischen IG/yF-Probes). Ein zukünftiger Phase-17-Vorschlag wäre, das Stop-Skript-Time-Out auf den Idle-Poll-Cap zu erhöhen, aber das ist nicht Phase-16-Scope.

🟢 **`is_weekend_market` hat Fail-Open Richtung „entdeckt":** wenn Epic=`.SUN*` aber Name ohne Marker (oder None), wird der Filter ausgelöst; wenn Name=„Wochenend-…" aber Epic normal, wird auch gefiltert — beides ist konservativ korrekt (Plan §1 P7: „Prädikat: IG-Name enthält `wochenend`/`weekend` **oder** Epic enthält `.SUN`"). Epic-only-Edge-Case (`SUN*` ohne Wochenend im Namen) ist mit dem OR-Muster abgedeckt.

🟢 **AK4 live-verifiziert:** `wiring.py:803` baut `db = Database(str(_DB_PATH))` ohne `run_migrations()` (kein Lock-Risiko mehr), `wiring.py:1083` ruft `assert_schema_floor(db.conn)` nach dem `account`-Check. Ein versehentlicher Start mit altem Code (Pre-B1) auf v7 würde laut am Schema-Fail scheitern — ab heute aber: v9 erreicht, also kein Lock-Out.

🟡 **A-6 (Reconcile-Backoff Live-Verify) wartet auf nächsten OPEN-Trade** (Phase-7-P12-Reconcile-Timing-Plan): die `last_resolve_attempt_utc`-Spalte ist live, der Backoff-Code läuft ab dem nächsten Trade. Beweis-Kriterium: ≤ 5 CRITICALs in 24 h statt 6+ in 52 min (Replay-verifiziert Mini-Session 26, Pre-Test bestätigt 2026-07-04).

🟡 **Bot bleibt aus** (Plan §6 B2-Fußnote: „Restart erst nach Block D"). Der `restart-services.sh start` ist blockiert bis Phase-D-Commit + E1-Vorregistrierung.

### Open questions / blockers

- Keine. Block B ✅ vollständig. B1 + B3 mechanisch korrekt, B2-Ausführung verifiziert.

### Next (für Exec-Session #4 oder Pause-Fortsetzung)

- **Block C — Research-Loop** (Plan §6 C1..C5): startet jetzt (nach B2) in Exec-Session #4. C1 (Historien-Fenster 14d in P4) + C2 (Prompt-Satz in P4) + C3 (Budget 300k in P8) + C4 (Doku, kein Code) + C5 (Breaker-Semantik in P3, Runde 2 freigegeben).
- **E1 (Vorregistrierung) — VOR dem Restart nach Block D committen** (Plan §13-Fußnote). Gehört in die Phase-16-Sequenz vor dem Operator-Restart.
- **Optional:** wenn Nikinger „direkt weiter mit Block C" sagt → ich starte in derselben Session nach einer Mini-Session-Rotation (Exec-#3 → Archiv, Exec-#4 → Phasenkopf).

**Block-Status nach dieser Session (endgültig):**

| Block | Status |
|---|---|
| A (Haushalt) | ✅ A-0..A-4 endgültig in code (Session #1+#2); A-5 = Operator-Push |
| B (Substrat) | ✅ B1+B3 endgültig in code + B2 Operator-Apply + A-5 Push (Session #3) |
| C (Research-Loop) | ⏳ startet jetzt in Exec-Session #4 (auf Nikinger-Auftrag) |
| D (Freischaltung) | ⏳ nach C |
| E (2-Wochen-Test) | ⏳ nach D + Operator-Restart |

**Push-Status dieser Session:** **9 Commits gepusht von Nikinger** (`ff84dac` = `origin/main`), 0 Commits pending, 0 Commits lokal ahead.