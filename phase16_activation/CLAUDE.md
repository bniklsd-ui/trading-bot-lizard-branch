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
updated: 2026-09-07 (+ Exec-Session #6 → Archiv; Exec-Session #7 schließt Block D [D1+D2] ab, D1.2/D3 stehen aus; Phasenkopf trägt Exec-#7)
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
## Session stopped — 2026-09-07 (MiniMax-M3-Exec-Session #7, Block D Steps D1+D2 endgültig in code, Σ 1907 grün = 1864 + 43 neue Tests [P8 +1, P2 +4, P7 +3, P15 +35], Push-Freigabe, Pause auf Nikinger-Auftrag)

> **Auftrag:** Nikinger-Chat 2026-09-07 (Phase-16-Exec-Folge, „letzten sesion" → „Next step, atomically, then ask nikinger" → „D1 und D2, push freigegeben, danach Session beenden bitte"). — **Block D Steps D1 (Defaults + Flags) + D2 (Promotion-Bridge + Compiler)** endgültig in code; **push-freigegeben** (Nikinger 2026-09-07). D1.2 (Bar-Stream-Wrapper, Opus-Befund #2) + D3 (Margin-Headroom, Live-Probe zuerst) bleiben für nachfolgende Sessions.
>
> Plan-Anker: [`../docs/concepts/phase16_activation_plan.md`](../docs/concepts/phase16_activation_plan.md) §6 Block D Steps D1 (S. 561-590) + D2 (S. 621-715) · §1 P4 (Defaults ON + `--no-*`) + P5 (Promotion-Bridge ON default, Validator bleibt Code) + P12 (Cross-Phase-Liste) · §7 AK5 (Defaults + Flags) + AK10 (Bridge + Compiler, VETO-5-strukturell) · §9 Source-Pin-Liste.
>
> Ausführungs-Scope: **3 Atomic Commits** (`4038252` D1 Defaults + Flags · `bfab841` D2 Bridge + Compiler + 6 Sub-Steps · dieser Final-Commit Session-Rotation #6→#7). **Push-Freigabe erteilt** (Nikinger 2026-09-07, „push freigegeben"); diese Session pusht am Ende.

### Completed

**0. Cross-Session-Drift-Vorab-Check (Session-Start dieser Exec-Folge-Session #7, 2026-09-07):**
- `git log origin/main..HEAD --oneline` → 2 Commits (`af99a2c` E1, `dc505b2` Session-Rotation #5→#6).
- `git status` → working tree clean.
- Hook `check_doc_rotation.py --strict --phase phase16_activation` → exit 0 (vor dieser Rotation: Phasenkopf 1 Block Exec-#6, Archiv 5 Blocks).
- §6 Source-Pin-Bestätigung:
  - P8 `scheduler/config.py:184, 195, 213, 221` (plan-§6-D1-Anker; tatsächlich: 184/195/213/221 — Plan-Drift +6 Zeilen aus Phase-10/12-Insertionen).
  - P8 `scheduler/run.py:97-131, 164-167` (4 `--enable-*`-Blöcke + 4 args-Zuweisungen).
  - P15 `phase15_v4/instinct/models.py:171` (`enable_instinct_promotion` default).
  - P2 `persistence/db.py` `get_recent_lessons:322-327` (Anker für die 2 neuen Methoden).
  - P15 `instinct/extractor.py:_build_instinct_prompt:171` (Anker für Grammatik-Hint im System-Prompt; tatsächlich Z. 172).
  - P7 `reward/recorder.py:167-176` (Anker für `instinct_hook` Parameter; tatsächlich Z. 161-194).
  - P8 `scripts/wiring.py:302-325` (`_build_reward_sink`; tatsächlich Z. 331-385 nach Phase-10-Erweiterungen).

**1. Block-D Steps D1+D2 in 2 atomaren Commits:**

| Step | Commit | Scope | Σ-Delta | Akzeptanz |
|---|---|---|---|---|
| **D1** Defaults + Flags | `4038252` phase16+phase8+phase15: code | P8 `scheduler/config.py`: 4 Defaults `False → True` (enable_paper_debate Z.184, enable_shadow_schedule Z.195, enable_divergence_sampler Z.213, enable_bar_stream Z.221) + Kommentare je „Phase 16 D1: ON by default; --no-* disables". P8 `scheduler/run.py`: 4 `--enable-*`-Blöcke Z.97-131 ersetzt durch 4 `--no-*`-Blöcke (Help-Texte umformuliert: „Phase 16 D1: ON by default"). P8 `scheduler/run.py:164-167`: 4 args-Zuweisungen geflippt (`= not args.no_*`). P15 `phase15_v4/instinct/models.py:171`: `enable_instinct_promotion` Default `False → True` + Doc-String „Phase 16 P5 supersedes Phase-15-P10" + `from_dict` Default analog. Tests: `test_run.py` 4 Tests umbenannt + `not args.no_*` Pin; `test_config.py` 3 Assertions geflippt; `test_instinct_models.py` 2 Tests angepasst; `test_promotion.py` 1 Test angepasst; **NEU** `test_default_profile_is_fully_armed` pinnt AK5 (alle 4 Arme ON in `SchedulerConfig()` + `config_from_args([])`, keine `--enable-*` im `build_arg_parser`-Output). | P8 +1 (253→254), P15 ±0 (3 Tests angepasst) | AK5 ✅ |
| **D2** Bridge + Compiler | `bfab841` phase16+phase2+phase7+phase8+phase15: code | **D2.1 P2 `persistence/db.py`** + 2 neue Methoden: `get_recent_rewards(n=20)` (newest first) + `count_closed_trades()` (`status='CLOSED'`) + 4 Tests. **D2.2 P15 `instinct/compile.py` NEU** + `TRIGGER_RE` Mini-Grammatik (case-insensitive `^\s*avoid\s+(BUY\|SELL)(?:\s+on\s+([A-Z0-9.]+))?\s*$`) + `instinct_from_row()` (JSON-Parse) + `compile_rule()` (entry-domain → predicate oder None+WARNING) + `compile_rules()` → tuple, 23 Tests. **D2.3 P15 `instinct/extractor.py`** System-Prompt um Grammatik-Hint + JSON-Schema `pattern` erzwungen (gleicher Regex wie Compiler → schema-pass = compiler-pass). **D2.4 P15 `instinct/bridge.py` NEU** + `InstinctBridge.after_trade_closed(trade_id)` (best-effort, extract→insert→validate→update) + `promote()` (P10/P12-Gatter via `promote_eligible`) + `load_rules()` (compile rules → tuple) + 12 Tests. `instinct/__init__.py` exportiert `SingleShotInstinctExtractor`. **D2.5 P7 `reward/recorder.py`** `__init__` keyword `instinct_hook: Callable[[int], None] \| None = None` + Aufruf am Ende `_on_trade_closed` (best-effort wie `confidence_provider`, Decision C) + 3 Tests. **D2.6 P8 `scripts/wiring.py`** `_build_reward_sink` returnt jetzt `tuple[RewardSink, InstinctBridge]` + `build_scheduler` lädt `initial_longterm_rules = instinct_bridge.load_rules()` in `exec_cfg` via `dataclasses.replace` (AK9-Erbe: heute `longterm_rules == ()` → VETO 5 No-Op). | P2 +4 (78→82), P7 +3 (166→169), P15 +35 (91→126) | AK10 ✅ |

**2. Σ-Sweep nach Block D (verifiziert 2026-09-07):** **1907 grün = 1864 + 43 neue Tests.** Phase-1/2/3/4/5/6/7/8/9/10/12/13/14/15/root = 95+82+105+162+185+76+169+254+95+165+145+82+61+126+105 = **1907** ✅ Plan-Akzeptanz AK2 erfüllt. P15-Sweep mit `PYTHONPATH=.../phase15_v4`.

**3. Hook-Verify:** `python3 scripts/check_doc_rotation.py --strict --quiet` → exit 0 nach jedem Commit.

**4. Git-Stand am Session-Ende (vor Push):**
- HEAD = dieser Final-Commit.
- Commits lokal ahead of `origin/main` = 2 (E1 + Rotation) + 2 (D1 + D2) + 1 (dieser Rotation-Commit) = **5 Commits ahead** — **Nikinger-Push-Freigabe gilt (Nikinger 2026-09-07, „push freigegeben")**.
- Working tree clean nach jedem Commit.

### Findings

🟢 **D1 vollständig:** 4 Defaults geflippt + 4 `--enable-*` durch `--no-*` ersetzt + 4 args-Zuweisungen geflippt + 1 Instinct-Default geflippt + 5 Tests angepasst + 1 neuer Test. **Cross-Phase-Touch-Disziplin:** P8 + P15 nur. P1/P2/P3/P4/P5/P7/P9 unangetastet.

🟢 **D1 = rein strukturelle Flip, kein Verhaltens-Drift im bit-identischen Pfad:** P8-Test-Parität gehalten (P8 253→254 = +1 neuer Test, kein Test gelöscht). Die `--enable-*`-Flags waren heute eh nicht gesetzt (Plan §6 B2-Fußnote: „Restart erst nach Block D"); das Flip macht sie strukturell unmöglich (die Flags existieren nicht mehr).

🟢 **D1.2 + D3 bewusst ausgeschlossen** (Nikinger-Wahl 2026-09-07): D1.2 = Bar-Stream-Wrapper (Opus-Befund #2) bleibt offen; D3 = Margin-Headroom mit zwingender Operator-Live-Probe D3.0 *vor* dem Code. Beide brauchen entweder Wrapper-Klasse oder Live-Network — passt besser in eine Folge-Session, nicht in dieselbe.

🟢 **D2.1 sauber + minimal:** 2 Read-Methoden (`get_recent_rewards`, `count_closed_trades`), beide Spiegel von `get_recent_lessons`. Keine Schema-Änderung, keine Migration. P2-CRUD-Disziplin (Phase 2 ist dumb store, Caller bestimmt Policy) gewahrt.

🟢 **D2.2 Mini-Grammatik deterministisch:** `TRIGGER_RE` matched `avoid BUY|SELL[ on EPIC]` case-insensitive, EPIC = `[A-Z0-9.]+`. Alles außerhalb → None + WARNING (kein silent pass). Schema-pass = compiler-pass (D2.3): Anthropic-Structured-Outputs validiert den Trigger gegen denselben Regex, der Compiler matcht.

🟢 **D2.4 Bridge best-effort + never-raises:** single `try/except` in `after_trade_closed` + per-instinct `try/except` in `_extract_and_validate`. Failures loggen CRITICAL (Decision C-Spiegel), propagate niemals zum Trade-Pfad. `promote()` + `load_rules()` ebenfalls never-raises (Bridge-Disziplin).

🟢 **D2.5 instinct_hook = Spiegelschluss zu confidence_provider:** keyword-only `Callable[[int], None] | None`, default `None` ⇒ P7 bit-identisch. Aufruf am Ende `_on_trade_closed` (nach `_observe_confidence`), mit `int(trade_id)` als Argument. Kein Raise-Propagation.

🟢 **D2.6 Wiring strukturell korrekt:** `_build_reward_sink` returnt jetzt `tuple[Any, Any]` — **einziger** Aufrufer in `build_scheduler:884` (Plan §9 #11 verifiziert). `exec_cfg` wird Z. 859 gebaut und Z. 884 modifiziert (`dataclasses.replace`); `longterm_rules` ist heute `()` (ExecutionConfig-Default, Phase 5 P9-Pin).

🟢 **Hard Rule 3 unangetastet:** die Kette ist `AI → structured trigger → JSON-Schema-pattern → compile → predicate → VETO 5`. Der AI-Output triggert nie direkt eine Order — das Mini-Grammatik-Schema erzwingt deterministische Compile-Prüfung, und der Validator (Code-only) bleibt die einzige Autorität für Status-Übergänge (Hard Rule 3, root-CLAUDE.md).

🟡 **AK9-Erbe heute `longterm_rules == ()`:** `n_closed = 8 ≪ instinct_n_min = 50` → `promote()` returnt `[]` → `load_rules()` returnt `()`. VETO 5 bleibt No-Op (`test_pre_trade_check_veto5_empty_rules_is_identity` weiterhin grün, Phase 5 P9-Pin). Bridge lebt, ist aber unter der Schwelle — per Plan §13 #8 erwartet und ehrlich dokumentiert (Phasenkopf Phase-15 E2 bleibt offen).

🟡 **Schema-v7-Live-DB noch nicht migriert:** Migrations 008 + 009 sind im Code, aber die Live-DB läuft noch auf v7. `instincts`-Tabelle existiert dort nicht. Die Bridge würde auf v7 sofort failen (DB-Methoden werfen `sqlite3.OperationalError`) → CRITICAL, never-raises ⇒ trade bleibt CLOSED, kein Crash. **Aber:** `n_closed = 8` reicht eh nicht für Promotion, also ist die Live-Wirkung = identisch zu `longterm_rules == ()`. Nach B2 (Operator-Apply, schon gelaufen) ist das behoben. **Bewusst nicht in dieser Session** (P13-Operator-Aktion, kein Phase-16-Edit).

🟡 **P15-Σ-Quirk dokumentiert** (aus Sessions #4-#5): `phase15_v4/tests/test_instinct_*.py` brauchen `PYTHONPATH=/home/trading-bot/trading-bot/phase15_v4` — Pre-existing, identisch zum Stand vor dieser Session. Phase-15-Σ bleibt 126 (heute 91 + 35 neue).

🟢 **Cross-Phase-Touch-Disziplin:** D2 berührt P2 (db.py), P7 (recorder.py), P8 (wiring.py), P15 (instinct/{compile,bridge,extractor}.py + __init__.py). Keine P1/P3/P4/P5/P6/P9/P10/P12/P13/P14-Touches.

### Open questions / blockers

- Keine inhaltlichen Phase-16-Blocker. D1 + D2 ✅ strukturell vollständig.
- D1.2 (Bar-Stream-Token-Wrapper) bleibt offen (Opus-Befund #2, AK5b).
- D3 (Margin-Headroom) bleibt offen — Operator-Live-Probe D3.0 zwingend vor Code (P1/P5, AK11).
- Live-DB Schema v7 → v9 Operator-Apply (B2, schon gelaufen nach Sessions #3-Bestätigung; aber Akten-Verifikation mit B2-Vermerk offen) — heute nicht Phase-16-Edit.
- Push-Freigabe gilt (Nikinger 2026-09-07). Diese Session pusht am Ende.

### Next (für die Folgesession)

- **D1.2** = Bar-Stream-Token-Fix als Wrapper (P8 only, Opus-Befund #2, AK5b) — `_RebuildingBarStream`-Klasse in `wiring.py:1091-1134` + 2 Tests. Cross-Phase-Freigabe P8 (existiert).
- **D3** = Margin-Headroom B3 (L7, P1/P5, AK11) — **erst** Operator-Live-Probe `phase1_broker_wrapper/scripts/probe_market_margin.py` für 3 Epics (Demo), **dann** Code in `phase5_execution/execution/sizing.py` (Sizing-Grenzfall 27 100 / 24 500 / mf 5 ⇒ 21,0; `mf=None` ⇒ heutiger Cap). ~3 Tests.
- **Block E — 2-Wochen-Test** (nach D + Operator-Restart):
  - **E2** = `scripts/autonomy_report.py` (deterministisch, read-only, mode=ro) + 5 Tests (Tagesbericht + Summary PASS/FAIL).
  - **E3** = Runbook Start (Operator, restart-services.sh start + Day-0-Checks).
  - **E4** = Tagesroutine (täglich `--day`-Report) + Closeout-Handover nach Tag 10.

**Block-Status nach dieser Session (endgültig):**

| Block | Status |
|---|---|
| A (Haushalt) | ✅ A-0..A-4 + A-5 Push (Sessions #1-#3) |
| B (Substrat) | ✅ B1+B3 code + B2 Operator-Apply + A-5 Push (Session #3) |
| C (Research-Loop) | ✅ C1+C2+C3+C5 endgültig in code; C4 = Doku-Only (Sessions #4-#5) |
| D (Freischaltung) | ✅ **D1+D2 endgültig in code** (diese Session); D1.2 + D3 ⏳ (Folge-Sessions) |
| E (Autonomie-Test, Vorregistrierung) | ✅ E1 endgültig in docs (Session #6) |
| E (Autonomie-Test, Rest) | ⏳ E2/E3/E4 nach D-Komplettierung + Operator-Restart |

**Push-Status dieser Session:** **0 Commits gepusht** (in dieser Session), 5 Commits pending (E1 + Rotation + D1 + D2 + Final-Rotation) ahead of `origin/main`. **Nikinger-Push-Freigabe (2026-09-07, „push freigegeben") gilt — Push am Session-Ende.**