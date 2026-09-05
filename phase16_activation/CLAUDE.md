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
updated: 2026-09-05 (+ Exec-Session #1 Block A A-0..A-4 endgültig in code, A-5 Push ausstehend; Exec-Session #2 startet Block B)
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
## Session stopped — 2026-09-05 (MiniMax-M3-Exec-Session #2, Block A endgültig in code + Session-Rotation #1→#2, Σ 1843 grün unverändert, 5 atomare Commits, A-5 Push ausstehend)

> **Auftrag:** Nikinger-Chat 2026-09-05: „nächsten Block atomar weiter, danach Session beenden bitte." — bezogen auf die Exec-Session-#1-Block-A-Teilsteps, die nach A-0 (Session-Rotation + Hook + Verzeichnisse, `901c15b`) noch offen waren: A-1 (Ritual) + A-2 (Σ-Baseline) + A-3 (Doku-Sweep) + A-4 (WebUI) + Session-End-Rotation. **Block A endgültig in code** (A-5 = Operator-Push, separat).
>
> Plan-Anker: [`../docs/concepts/phase16_activation_plan.md`](../docs/concepts/phase16_activation_plan.md) §6 Block A Steps A-1..A-4 (S. 315-350) + §4 Cross-Phase-Tabelle + §1 P11/P12/P13/P14/P15.
>
> Ausführungs-Scope: **5 Atomic Commits** (`7f5b516` A-1+A-2 · `19d0ad3` A-3 · `eedd266` A-4 · +2 Session-Rotation) **+ 1 Phasenkopf-Sub-Section-Update pro Step**. Push-Freigabe (P18) erteilt; diese Session pusht **nicht** eigenmächtig (Head = 5 Commits lokal ahead of `origin/main`).
>
> **Σ total 1843 grün** (Plan §2.1 + Phase-15-Session-#13-Stand unverändert durch alle Block-A-Steps).

### Completed

**0. Cross-Session-Drift-Vorab-Check (Session-Start dieser Exec-Folge-Session #2, 2026-09-05):**
- `git log origin/main..HEAD --oneline` → 1 Commit (`901c15b` Block-A-A-0).
- `git status` → working tree clean nach A-0-Commit.
- Hook `check_doc_rotation.py --strict --phase phase16_activation` → exit 0 (Phasenkopf 1 Session-Block, Archiv mit Plan-Session-Block, `_max_session_num==None` korrekt für `head_max==1`).

**1. Block-A-Steps A-1..A-4 in 4 atomaren Commits:**

| Step | Commit | Σ-Delta | Akzeptanz |
|---|---|---|---|
| **A-1+A-2** | `7f5b516` | 0 | AK1 ✅ + AK2 ✅ |
| **A-3** | `19d0ad3` | 0 | AK3 ✅ |
| **A-4** | `eedd266` | 0 | AK12 ✅ (wirkt nach WebUI-Restart) |
| **Session-Rotation** | (dieser Commit) | 0 | Doc-Rotation ✅ |

**2. Σ-Sweep nach Block A (verifiziert nach A-3 und nach A-4):** **1843 grün unverändert.** Phase-1/2/3/4/5/6/7/8/9/10/12/13/14/15/root = 95+78+104+155+185+76+166+248+87+165+145+82+61+91+105 = 1843 ✅ exakt Plan §2.1.

**3. Hook-Verify nach jedem Step:** `python3 scripts/check_doc_rotation.py --strict --quiet` → exit 0 nach A-0..A-4.

**4. Git-Stand am Session-Ende:**
- HEAD = `eedd266` (oder dieser Commit-Commit danach).
- 5 Commits lokal ahead of `origin/main`: `901c15b`, `7f5b516`, `19d0ad3`, `eedd266`, + dieser Session-Rotation-Commit.
- Working tree clean nach diesem Commit (außer untracked `data/`, gitignored).

### Findings

🟢 **Block A endgültig in code** (A-0..A-4 alle ✅), Σ-Baseline 1843 unverändert. A-5 (Operator-Push) ist die einzige offene Phase-16-Aktion vor Block B.

🟢 **Cross-Phase-Touch-Disziplin eingehalten:** Plan §4 Cross-Phase-Tabelle hat die Freigabe-Liste klar gemacht (P1/P2/P3/P4/P5/P7/P8/P9/P15). Block A hat berührt: **P8** (Phase 8 Scheduler, `run_webui.sh` + `webui/api.py`, A-4 — beide additiv, 0 Test-Impact, 248 P8-Tests unverändert grün) + **Doku-Vermerke** in `phase9_universe/CLAUDE.md` (Step 7b Leiche) und `phase15_v4/PHASE15_CLOSEOUT_HANDOVER.md` (🟡-Anhang, datiert, Phase-12/13/14-Closeout-Pattern-konform). P6/P10/P12/P13/P14 unangetastet wie gefordert.

🟢 **Source-of-truth precedence gewahrt:** A-3 hat die 4 dokumentierten Code-Wahrheits-Widersprüche (Plan §3 L3) in der Doku korrigiert. A-4 hat die irreführende WebUI-Warnung behoben, ohne die WebUI-Gating-Logik anzufassen (Code-Kommentar dokumentiert „gatet nichts"). Beide sind additive Korrekturen, keine Lock-Lösung.

🟢 **Hook-Erweiterung (A-0) hat den neuen Phasenkopf sauber integriert** — `_max_session_num == 1` (Exec-Session #1) jetzt im Archiv, Phasenkopf wechselt zu Exec-Session #2 → `_max_session_num == 2`. `_SESSION_NUM_RE` permissiv genug (P15-F-Vorbild), Plan-Session-Block im Archiv bleibt korrekt unnummeriert.

🟡 **A-5 bleibt Operator-Aktion:** Nikinger-Fable-5.1-Handover hat Push erteilt, aber diese Session pusht nicht eigenmächtig (Root-`CLAUDE.md` Working-style: *„Live-/Netz-/kostenpflichtige Läufe bleiben Nikinger-Job"*). 5 Commits ahead of `origin/main` → 7 nach `git push origin main`.

🟡 **B2-Operator-Fenster ist nach Block-B-Commit fällig:** mit B1 (Schema-Floor) committed wirft ein versehentlicher Start mit altem Code auf v7 laut mit `init_db.py`-Anweisung. Das ist **gewollt** (Plan §13 Opus-Befund #1), schützt vor stillem Schema-Stale.

🟢 **`# grep "LiveQuoteCache"` bleibt 0:** nach A-3-Korrektur dokumentiert, dass die Leiche begraben ist. Phase-12/13-Architektur (BarService + LS-Tick-Aggregation) hat den Bedarf strukturell abgelöst.

### Open questions / blockers

- Keine. Block A ✅, AK1+AK2+AK3+AK12 erfüllt. Block B startet in Exec-Session #3 (oder dieser, wenn Nikinger „direkt weiter" sagt).

### Next (für Exec-Session #3 oder Pause-Fortsetzung)

- **Block B — Substrat** (Plan §6 B1..B3, kein Cross-Phase-Gate, startet nach A):
  - **B1** `assert_schema_floor(conn, required=9)` in `phase8_scheduler/scripts/wiring.py` (Anker `wiring.py:1066-1077` Preflight-Block) + 3 Tests in `phase8_scheduler/tests/`: v9 ok, v7 raise mit `init_db.py` im Text, leere Tabelle raise.
  - **B3** `is_weekend_market(epic, name)` in `phase9_universe/universe/models.py` + Discovery-Block (`discovery.py:131` `market_status != "TRADEABLE"`-Check davor) + Promotion-Demotion (`promotion.py:251-262` + neue Loop-Zeile in `promotion.py` active_count-Loop + in `promotion.py` verified→active-Step). 4 Tests in `phase9_universe/tests/`: `test_is_weekend_market` (5 Fälle), `test_discover_filters_weekend_market`, `test_promotion_demotes_active_weekend_epic`, `test_promotion_never_activates_weekend_epic`.
  - **B2 — Operator-Apply** (P13, **erst nach Block-B-Commit**): `bash scripts/restart-services.sh stop` → `cp data/trading_bot.sqlite data/trading_bot.sqlite.bak-20260905-pre-mig009` → `phase1_broker_wrapper/.venv/bin/python phase2_persistence/scripts/init_db.py --db-path data/trading_bot.sqlite` → SQL-Verify (`SELECT MAX(version) FROM _schema_version` → 9 + `PRAGMA table_info(trade_outcomes)` zeigt `last_resolve_attempt_utc`) → Ledger-Restore (`sqlite3 data/bars.sqlite "DELETE FROM source_spend WHERE kind='rescue'"`).
- **A-5 (Operator-Push)** jederzeit möglich, 5 Commits lokal ahead, Fable-5.1-Handover hat erteilt.
- **E1 (Vorregistrierung) — VOR dem Restart nach Block D committen** (Plan §13-Fußnote). Gehört in die Phase-16-Sequenz vor dem Operator-Restart.

**Block-Status nach dieser Session (endgültig):**

| Block | Status |
|---|---|
| A (Haushalt) | ✅ A-0..A-4 endgültig in code (Session #1+#2); A-5 = Operator-Push |
| B (Substrat) | ⏳ startet in Exec-Session #3 |
| C (Research-Loop) | ⏳ nach B |
| D (Freischaltung) | ⏳ nach C |
| E (2-Wochen-Test) | ⏳ nach D + Operator-Restart |

**Push-Status dieser Session:** **0 Commits gepusht**, 4 Commits pending (A-1+A-2 + A-3 + A-4 + Session-Rotation) ahead of `origin/main` (gesamt: 8 Commits lokal ahead nach diesem Commit; 9 + A-5-Push nach Operator-Aktion).