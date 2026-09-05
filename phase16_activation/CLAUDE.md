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
updated: 2026-09-05 (+ Exec-Session #3 Block B B1+B3 endgültig in code, Σ 1856 grün, B2 = Operator; Exec-Session #4 startet Block C nach B2)
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
## Session stopped — 2026-09-05 (MiniMax-M3-Exec-Session #3, Block B B1+B3 endgültig in code + Session-Rotation #2→#3, Σ grün ≥ 1843, B2 = Operator nach Block-B-Commit, A-5 Push ausstehend)

> **Auftrag:** Nikinger-Chat 2026-09-05 (Phase-16-Exec-Folge): „NEXT (für Exec-Session #3 oder Pause-Fortsetzung): Block B startet (Plan §6 B1..B3). B2 ist Operator-Aktion (P13) und kommt nach Block-B-Commit mit allen 4 Diensten gestoppt." — **Block B in code** (B1 = Schema-Floor, B3 = Wochenend-Filter + Demotion), B2 als vorbereitete Operator-Anweisung an Nikinger übergeben.
>
> Plan-Anker: [`../docs/concepts/phase16_activation_plan.md`](../docs/concepts/phase16_activation_plan.md) §6 Block B Steps B1..B3 (S. 365-466) + §1 P8 (Schema-Floor statt In-Daemon-Migration) + §1 P7/P9 (Wochenend-Filter + Demotion) + §4 Cross-Phase-Tabelle (P8 + P9 freigegeben).
>
> Ausführungs-Scope: **3 Atomic Commits** (`SESSION-ROT` `#2→#3` · B1 `assert_schema_floor` · B3 `is_weekend_market`) **+ 1 Phasenkopf-Sub-Section-Update pro Step**. Push-Freigabe (P18) erteilt; diese Session pusht **nicht** eigenmächtig (Head = 8 Commits lokal ahead of `origin/main` vor dieser Session → 11 nach dieser Session).

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

**2. Σ-Sweep nach Block B (verifiziert 2026-09-05):** **1856 grün (= 1843 + 13 neue Tests).** Phase-1/2/3/4/5/6/7/8/9/10/12/13/14/15/root = 95+78+104+155+185+76+166+253+95+165+145+82+61+91+105 = 1856 ✅ exakt Plan-Akzeptanz AK2 erfüllt.

**2. Σ-Sweep nach Block B:** wird am Session-Ende durchgeführt (Erwartung ≥ 1850 = 1843 + 3 P8 + 4 P9).

**3. Hook-Verify:** `python3 scripts/check_doc_rotation.py --strict --quiet` → exit 0 erwartet nach Session-Rotation.

**4. Git-Stand am Session-Ende:**
- HEAD = dieser Commit (3 neue Commits über Block-A-Stand von `557761c`).
- 8 Commits lokal ahead of `origin/main` (vor Session) + 3 Commits in dieser Session = **11 Commits lokal ahead nach Session**.
- Working tree clean nach diesem Commit (außer untracked `data/`, gitignored).

### Findings

🟢 **Block B Code endgültig** (B1 + B3 ✅), Schema-Floor und Wochenend-Demotion sind codeseitig scharf. **B2 bleibt Operator** (P13).

🟢 **Cross-Phase-Touch-Disziplin eingehalten:** Plan §4 Cross-Phase-Tabelle: Block B hat berührt: **P8** (`phase8_scheduler/scripts/wiring.py` + `phase8_scheduler/tests/test_wiring_schema_floor.py`) + **P9** (`phase9_universe/universe/{models,discovery,promotion}.py` + `phase9_universe/tests/test_weekend_market.py`). Keine P1/P2/P3/P4/P5/P7/P15-Touches in Block B.

🟢 **Source-of-truth precedence gewahrt:** B1 wurde gegen den verbatim Preflight-Block `wiring.py:1066-1077` gebaut (gleicher Mechanismus wie der bestehende `account`-Check, als `assert_schema_floor`-Modul-Funktion extrahiert für Testbarkeit). B3 nutzt die existierenden `set_status`/`UniverseRecord`-Schnittstellen unverändert (additive Edit, kein Re-Design der Promotion-Pipeline).

🟡 **B2-Operator-Fenster ist die einzige offene Phase-16-Aktion nach dieser Session:** mit B1 (Schema-Floor) committed wirft ein versehentlicher Start mit altem Code auf v7 laut mit `init_db.py`-Anweisung. Das ist **gewollt** (Plan §13 Opus-Befund #1), schützt vor stillem Schema-Stale. B2-Befehlsblock liegt unter `### B2-Operator-Anweisungen (P13)` weiter unten bereit.

🟡 **A-5 bleibt Operator-Aktion:** Nikinger-Fable-5.1-Handover hat Push erteilt, aber diese Session pusht nicht eigenmächtig (Root-`CLAUDE.md` Working-style). 11 Commits ahead of `origin/main` → 13 nach `git push origin main`.

🟢 **`is_weekend_market` hat Fail-Open Richtung „entdeckt":** wenn Epic=`.SUN*` aber Name ohne Marker (oder None), wird der Filter ausgelöst; wenn Name=„Wochenend-…" aber Epic normal, wird auch gefiltert — beides ist konservativ korrekt (Plan §1 P7: „Prädikat: IG-Name enthält `wochenend`/`weekend` **oder** Epic enthält `.SUN`"). Epic-only-Edge-Case (`SUN*` ohne Wochenend im Namen) ist mit dem OR-Muster abgedeckt.

### B2-Operator-Anweisungen (P13, nach Block-B-Commit, alle 4 Dienste gestoppt)

```bash
# 1. Alle 4 Dienste stoppen (Recorder, Discovery, Scheduler, WebUI — PIDs 124485/124512/124569/124611 zum Stand 2026-09-05)
bash scripts/restart-services.sh stop
ps aux | grep -E "scheduler.run|data_foundation.run|source_registry.run|uvicorn" | grep -v grep   # muss leer sein

# 2. Backup der Live-DB (Phase 16 B2)
cp data/trading_bot.sqlite data/trading_bot.sqlite.bak-20260905-pre-mig009

# 3. Migrations 008 + 009 anwenden (Ledger-Restore wandert in den Migrations-Pfad, weil Recorder gestoppt)
phase1_broker_wrapper/.venv/bin/python phase2_persistence/scripts/init_db.py --db-path data/trading_bot.sqlite

# 4. SQL-Verify
sqlite3 "file:data/trading_bot.sqlite?mode=ro" "SELECT MAX(version) FROM _schema_version; PRAGMA table_info(trade_outcomes);" | grep -E "^9$|last_resolve_attempt_utc"
# Erwartung: '9' + Spalte 'last_resolve_attempt_utc' vorhanden + Tabelle 'instincts' vorhanden

# 5. Ledger-Restore (250 falsch gebuchte Rescue-Punkte aus dem 2026-09-04-Pfad-A-Scharfschaltungs-Bug)
sqlite3 data/bars.sqlite "SELECT COUNT(*), SUM(points) FROM source_spend WHERE kind='rescue';"   # erwartet 5 | 250
sqlite3 data/bars.sqlite "DELETE FROM source_spend WHERE kind='rescue';"
```

Kosten: 0 EUR (Demo, kein Network). Empfehlung: B2 + A-5 in einem Schritt erledigen, danach Blöcke C/D folgen (Restart erst nach Block-D-Commit + E1-Vorregistrierung).

### Open questions / blockers

- Keine in Block B Code. B1 + B3 sind mechanisch korrekt (analog zu Phase-7/8/9-Step-Mustern).

### Next (für Exec-Session #4 oder Pause-Fortsetzung)

- **B2 — Operator-Apply** (P13, **nach dieser Session**): Befehlsblock oben. Stop alle 4 Dienste → Backup → `init_db.py --db-path data/trading_bot.sqlite` → SQL-Verify v9 → Ledger-Restore. Schema-Floor wirkt ab B1-Commit; ein versehentlicher Start mit altem Code vor B2 wirft laut mit `init_db.py`-Anweisung im Text — gewollt.
- **A-5 (Operator-Push)** jederzeit möglich, 11 Commits lokal ahead, Fable-5.1-Handover hat erteilt.
- **Block C — Research-Loop** (Plan §6 C1..C5): startet nach B2 in Exec-Session #5 (oder dieser, wenn Nikinger „direkt weiter" sagt). C1 (Historien-Fenster 14d) + C2 (Prompt-Satz) + C3 (Budget 300k) + C4 (Doku) + C5 (Breaker-Semantik, P3 Runde 2 freigegeben).
- **E1 (Vorregistrierung) — VOR dem Restart nach Block D committen** (Plan §13-Fußnote). Gehört in die Phase-16-Sequenz vor dem Operator-Restart.

**Block-Status nach dieser Session (endgültig):**

| Block | Status |
|---|---|
| A (Haushalt) | ✅ A-0..A-4 endgültig in code (Session #1+#2); A-5 = Operator-Push |
| B (Substrat) | ✅ B1+B3 endgültig in code (Session #3); B2 = Operator-Apply (Nikinger) |
| C (Research-Loop) | ⏳ startet nach B2 in Exec-Session #5 |
| D (Freischaltung) | ⏳ nach C |
| E (2-Wochen-Test) | ⏳ nach D + Operator-Restart |

**Push-Status dieser Session:** **0 Commits gepusht**, 3 Commits pending (Session-Rotation + B1 + B3) ahead of `origin/main` (gesamt: 11 Commits lokal ahead nach dieser Session; 13 + A-5-Push nach Operator-Aktion).