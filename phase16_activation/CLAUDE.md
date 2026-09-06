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
updated: 2026-09-05 (+ Exec-Session #3 → Archiv; Exec-Session #4 startet Block C Step C1; Phasenkopf trägt Exec-#4)
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
## Session stopped — 2026-09-05 (MiniMax-M3-Exec-Session #4, Block C Step C1 endgültig in code, Σ 1862 grün = 1856 + 6 neue P4-Tests, Pause auf Nikinger-Auftrag)

> **Auftrag:** Nikinger-Chat 2026-09-05 (Phase-16-Exec-Folge, Mini-Rotation nach B2-Confirmed): „Block C, aber nur erster Step, danach Session beenden." — **Block C Step C1** (Plan §6 C1, L1-Fix: Historien-Fenster 14d als Post-Filter im P4-Research-Context). C2..C5 + E1 bleiben für nachfolgende Sessions.
>
> Plan-Anker: [`../docs/concepts/phase16_activation_plan.md`](../docs/concepts/phase16_activation_plan.md) §6 Block C Step C1 (S. 470-499) + §1 P2 (Fenster 14d + max 8 Trades + Prompt-Satz) + §1 P4 (P4 Post-Filter, kein SQL-Touch) + §4 Cross-Phase-Tabelle (P4 freigegeben) + §7 AK7.
>
> Ausführungs-Scope: **3 Atomic Commits** (`e26ff06` Session-Rotation · `acc941f` C1 Code+Tests · dieser Final-Commit). Push-Freigabe (P18) gilt weiterhin; diese Session pusht **nicht** eigenmächtig.

### Completed

**0. Cross-Session-Drift-Vorab-Check (Session-Start dieser Exec-Folge-Session #4, 2026-09-05):**
- `git log origin/main..HEAD --oneline` → 1 Commit (`6ee2620` B2-Confirmed-Vermerk aus der vorherigen Session).
- `git status` → working tree clean.
- Hook `check_doc_rotation.py --strict --phase phase16_activation` → exit 0 (vor Mini-Rotation: Phasenkopf 1 Block, Archiv 3 Blocks).
- Source-Pin gegen `models.py:681` (`recent_trades_quarantine_before`) + `context_builder.py:251-256` (Anker für `_drop_older_than`) + `prompt.py:121-132` (`_render_trades`) — alle verbatim bestätigt.

**1. Block-C Step C1 in 2 atomaren Commits + 1 Session-Rotation-Commit:**

| Step | Commit | Scope | Σ-Delta | Akzeptanz |
|---|---|---|---|---|
| **C1** Historien-Fenster 14d | `acc941f` phase16+phase4: code | `research/models.py` `ResearchConfig.recent_trades_max_age_days: int \| None = 14` + `ResearchContext.recent_trades_max_age_days: int \| None = None` (Default `None` = bit-identisch) + `research/context_builder.py` neue Modul-Funktion `_drop_older_than(trades, max_age_days, *, now_fn=None)` (close_ts→open_ts Fallback, fail-open auf unparsbar, now_fn injizierbar) + Anwendung direkt nach `db.get_recent_trades_for_prompt(8, …)` + `research/prompt.py` `_render_trades(trades, *, max_age_days=None)` rendert Header „Recent trades (last N days, newest first):" + 6 Tests in `phase4_research/tests/test_recent_trades_window.py` (4 vom Plan + 2 Belt-and-Braces für den Header) | +6 (P4: 155→161) | AK7 ✅ |
| **Session-Rotation** | `e26ff06` phase16: docs | Phasenkopf Exec-#3 → SESSIONS_ARCHIVE.md + Exec-#4 → Phasenkopf (mit Heading-Body-Regex-False-Positive-Fix „Session 5" → "Folgesession") | 0 | Doc-Rotation ✅ |

**2. Σ-Sweep nach C1 (verifiziert 2026-09-05):** **1862 grün (= 1856 + 6 neue P4-Tests).** Phase-1/2/3/4/5/6/7/8/9/10/12/13/14/15/root = 95+78+104+161+185+76+166+253+95+165+145+82+61+91+105 = 1862 ✅ exakt Plan-Akzeptanz AK2 erfüllt.

**3. Hook-Verify:** `python3 scripts/check_doc_rotation.py --strict --quiet` → exit 0 nach jedem Commit.

**4. Git-Stand am Session-Ende:**
- HEAD = dieser Final-Commit.
- Commits lokal ahead of `origin/main` = 1 (vorheriger B2-Confirmed) + 3 (diese Session) = **4 Commits ahead**.
- Working tree clean nach jedem Commit (außer untracked `data/`, gitignored).

### Findings

🟢 **C1 ist der deterministische Fix für L1:** ohne Zeitfenster altert die Tabelle „8 jüngste Trades" nur, wenn ein neuer Trade die Reihenfolge ändert — und nach dem 7. Verlust war das ein absorbierender Zustand (77 Calls/Tag für 5 Tage). 14-Tage-Fenster als Post-Filter lässt den LLM weiterhin die letzten 8 **oder weniger** Trades sehen, aber abgeschnitten am 14-Tage-Cutoff. Plus Prompt-Satz (C2, später) macht die Historie-Rolle explizit („context for lessons and sizing, NOT a veto").

🟢 **Fail-Open Semantik korrekt:** `_drop_older_than` parst `close_ts` (Fallback `open_ts`) mit `datetime.fromisoformat`, ersetzt vorher `Z` → `+00:00`. Bei unparsbarem Timestamp → **behalten** (LLM sieht mehr, nie weniger — defensiv).

🟢 **`now` injizierbar:** über `now_fn`-Parameter testbar; Default `datetime.now(timezone.utc)`.

🟡 **`recent_trades_max_age_days=None` muss bit-identisch zum Pre-P16-Verhalten sein** (Plan §1 P2: „None = off"). Test `test_window_none_is_bit_identical` pinnt das.

🟡 **Pre-LLM-Limit auf 8 bleibt:** die `_drop_older_than`-Funktion filtert NACH `db.get_recent_trades_for_prompt(8, …)` (siehe `context_builder.py:251`). Es ist also „8 jüngste aus DB → dann 14-Tage-Filter" — bei 8×20 Tage alten Trades bleibt 0 im Kontext (das ist **gewollt**: leerer recent-trades-Block ist ehrlicher als „6 von 7 Verluste"-Narrativ).

🟢 **Cross-Phase-Touch-Disziplin:** Block C Step C1 berührt **nur P4** (`research/{models,context_builder,prompt}.py` + Tests). Keine P1/P2/P3/P5/P7/P8/P9/P15-Touches. P4 war schon in Plan §4 freigegeben.

🟢 **Header-Render aus Config:** `"Recent trades (last {config.recent_trades_max_age_days} days, newest first):"` — Zahl kommt aus der Config, nicht hardcoden. Bei `None` → fällt auf `"Recent trades (newest first):"` zurück (Pre-P16-String).

### Open questions / blockers

- Keine. C1 ist mechanisch korrekt und orthogonal zu C2..C5 (C2 = Prompt-Satz in derselben `prompt.py`, C3 = Budget 300k in P8, C5 = Breaker-Semantik in P3, alle unabhängig).

### Next (für die Folgesession)

- **Block C Step C2** (Plan §6 C2): Prompt-Satz `"- Recent trades are context for lessons and sizing, NOT a veto: a losing streak by itself is never a reason to abstain — judge the setup in front of you.\n"` in `research/prompt.py` nach `"- When in doubt, ABSTAIN. A skipped session is cheap; a bad trade is not.\n"`. 1 Test (`test_system_prompt_names_history_as_context_not_veto`).
- **Block C Step C3** (Plan §6 C3): Budget 200k → 300k in `scheduler/config.py:134` + `scheduler/run.py:57` CLI-Default. Tests in `phase8_scheduler/tests/test_run.py:20,52`, `test_config.py:39`, `test_webui.py:338-348` (Prozent-Pin 0.6). **Kein** `cache_system=True` (P3-Begründung).
- **Block C Step C5** (Plan §6 C5, P3 Runde 2 freigegeben): Breaker-Semantik in `external_data/fetcher.py:407-411` — leerer Frame öffnet Circuit nicht (nur `RateLimitError`). Test `test_empty_frame_does_not_open_circuit`.
- **E1 (Vorregistrierung)** muss vor Block-D-Operator-Restart committet sein.

**Block-Status nach dieser Session (endgültig):**

| Block | Status |
|---|---|
| A (Haushalt) | ✅ A-0..A-4 + A-5 Push (frühere Sessions) |
| B (Substrat) | ✅ B1+B3 code + B2 Operator-Apply + A-5 Push (vorherige Session) |
| C (Research-Loop) | 🔄 C1 endgültig in code; C2+C3+C5 offen |
| D (Freischaltung) | ⏳ nach C |
| E (2-Wochen-Test) | ⏳ nach D + Operator-Restart |

**Push-Status dieser Session:** **0 Commits gepusht**, 2 Commits pending (Session-Rotation + C1) ahead of `origin/main` (gesamt: 3 Commits lokal ahead nach dieser Session).