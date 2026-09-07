# SESSIONS_ARCHIVE.md — Phase 16 (Freischaltung)

Newest-first. Rotation rule (root `CLAUDE.md`, mandatory since 2026-07-06): the phase head
carries exactly one `## Session stopped` block; archives have no size cap. See
[`../CLAUDE.md`](../CLAUDE.md) "Rotation rule (mandatory since 2026-07-06)" for the full
contract, and [`../docs/DOC_LAYERS_CONVENTION.md`](../docs/DOC_LAYERS_CONVENTION.md) for
the L0/L1/L2/L3 model.

Plan-Session-Block trägt bewusst **keine** `Session #N`-Nummer im Heading (Phase-15-Vorbild
„Plan-Session, Opus 5") — das P14-F-Step-2-Regex `_SESSION_NUM_RE` matcht darauf nicht;
`_max_session_num` returnt `None`; für die erste Exec-Session (`head_max == 1`) ist das
Archiv-Max `None` korrekt (check_archive_sequence, Z. 134-138).

Stand nach Exec-Session #9 (2026-09-07): Archiv trägt **9** Einträge — `#8` (Block D
D1.2 Bar-Stream-Token-Wrapper, Σ 1909, P8 only) + `#7` (Block D D1+D2, Σ 1907, zwischenzeitlich
gepusht) + `#6` (Block E E1 Vorregistrierung, Σ 1864 docs-only) + `#5` (Block C C2+C3+C5, Σ 1864)
+ `#4` (Block C C1, Σ 1862) + `#3` (Block B B1+B3 + B2 Operator-Apply + A-5-Push, Σ 1856)
+ `#2` (Block A endgültig in code) + `#1` (Block A A-0) + Plan-Session. Phasenkopf trägt genau
**1** Block (Exec-Session #9, D3.0 Operator-Probe-Skript endgültig in code, Σ 1909 unverändert
[operator-run script, kein Test-Impact per Phase-1-Convention]; **wartet auf Nikinger für
`probe_market_margin.py`-Lauf**; danach D3.1 + D3.2 in Folge-Session gegen Befunde, alternativ
D3 vertagt zugunsten Block E [E2 autonomy_report.py deterministisch + E3 Runbook + E4
Tagesroutine+Closeout]).

---

## Session stopped — 2026-09-07 (MiniMax-M3-Exec-Session #8, Block D Step D1.2 endgültig in code, Σ 1909 grün = 1907 + 2 neue P8-Tests [P8 +2], Pause auf Nikinger-Auftrag)

> **Auftrag:** Nikinger-Chat 2026-09-07 (Phase-16-Exec-Folge, „letzten sesion" → „Next step, atomically, then ask nikinger" → Fragebogen-Antwort „D1.2, also der nächste Step bitte"). — **Block D Step D1.2 (Bar-Stream-Token-Wrapper)** endgültig in code (P8 only, Opus-Befund #2, AK5b). D3 (Margin-Headroom mit zwingender Operator-Live-Probe D3.0 vor Code) + Block E (E2/E3/E4) bleiben für nachfolgende Sessions.
>
> Plan-Anker: [`../docs/concepts/phase16_activation_plan.md`](../docs/concepts/phase16_activation_plan.md) §6 Block D Step D1.2 (S. 592-619, inkl. `_RebuildingBarStream`-Klassen-Skizze Z. 604-613 + Wrapper-Anker `wiring.py:1131` → `bar_stream = _RebuildingBarStream(_build_recorder)` + 2 Test-Skizzen Z. 617-619) · §1 P4 (Defaults ON, Cross-Phase-Freigabe P8) · §7 AK5b (Wrapper frisch-baut gegen CURRENT tokens, ein `restart()`-Call pro Token-Rotation). · §9 Source-Pin-Liste (Plan nennt `wiring.py:1091-1134` + `wiring.py:1131`; aktueller Code-Stand: heute sind die Pin-Zeilen **+66** versetzt durch Phase-13-B0-Source-Block-Erweiterung; Plan-Drift notiert, Anker-Substanz unverändert).
>
> Ausführungs-Scope: **2 Atomic Commits** (`64a42d4` D1.2 Code + Tests · `468ce3d` Session-Rotation #7→#8). Push-Freigabe-Stand: zwischen Session #7 und jetzt hat Nikinger die 5 pending Commits der Session #7 (E1 + Rotation + D1 + D2 + Final-Rotation) per `git push origin main` gepusht — `origin/main` ist jetzt auf `e9c8aa7`. Diese Session pusht die **eigenen** 2 Commits **nicht** eigenmächtig (Nikinger-Auftrag am Session-Ende erwartet, Cross-Session-Pattern).

### Completed

**0. Cross-Session-Drift-Vorab-Check (Session-Start dieser Exec-Folge-Session #8, 2026-09-07):**
- `git log origin/main..HEAD --oneline` → leer (HEAD = `e9c8aa7` = origin/main; 5 Session-#7-Commits inzwischen gepusht).
- `git status` → working tree clean bis auf untracked `data/` (gitignored).
- Hook `check_doc_rotation.py --strict --phase phase16_activation` → exit 0 (vor dieser Rotation: Phasenkopf 1 Block Exec-#7, Archiv 6 Blocks).
- §6 D1.2 Source-Pin-Bestätigung:
  - P8 `scripts/wiring.py:1156-1199` Block (Plan-Anker war `wiring.py:1091-1134`/`wiring.py:1131`; Plan-Drift +66 Zeilen aus Phase-13-B0-Source-Block-Erweiterung).
  - P8 `scheduler/runner.py:493-512` `_restart_bar_stream` (Duck-Type-Kontrakt: `hasattr(bar_stream, "restart")` → `restart()`, sonst `stop()+start()`).
  - P1/P13 `ig_lightstreamer.py:232-233,256` (CST/XST Snapshot bei Konstruktion, das latente Bug-Wurzel für Opus-Befund #2).
  - Pattern-Vorlage für den Test-Import: `tests/test_wiring_schema_floor.py:27-32` (sys.path-Insert + offline-sicheres Import-Setup).

**1. Block-D Step D1.2 in 1 atomaren Commit:**

| Step | Commit | Scope | Σ-Delta | Akzeptanz |
|---|---|---|---|---|
| **D1.2** Wrapper + Tests | `64a42d4` phase16+phase8: code | P8 `scripts/wiring.py`: `_RebuildingBarStream` Klasse NEU (Z. ~120-153, nach `assert_schema_floor`, vor `_STATE_DIR`-Block) — start/stop/restart duck-type, Build-Fn-Closure liest `broker._cst/_security_token/_account_id/_lightstreamer_endpoint` bei jedem Call, stop vor start no-op (`self._inner=None` ⇒ return), restart = stop+start; bar_stream-Build-Block umstrukturiert zu `_build_recorder()`-Closure mit lazy cross-phase imports (Pattern aus dem Original beibehalten: `from broker_wrapper.streaming.ig_lightstreamer import IGLightstreamerClient` und `from live_data.stream import TickAggregatorRecorder` lazy innerhalb der Closure); `from universe import UniverseStore` an den Top des `if config.enable_bar_stream:`-Blocks gezogen (von try-Block-Mitte); `bar_stream = recorder` → `bar_stream = _RebuildingBarStream(_build_recorder)` (Pin aus Plan). `phase8_scheduler/tests/test_rebuilding_bar_stream.py` NEU mit 2 Tests (Pattern `test_wiring_schema_floor.py`, sys.path.insert + offline-safe): `test_rebuilding_bar_stream_uses_fresh_tokens` (current_token["cst-OLD"], start, current_token[0]="cst-NEW", restart → 2 builds, alter inner gestoppt, neue inner hat cst-NEW, kein Objekt-Reuse) · `test_rebuilding_bar_stream_stop_before_start_is_noop` (stop ohne start no-op, restart ohne start baut einmal + start, kein raise). | P8 +2 (254→256) | AK5b ✅ |

**2. Σ-Sweep nach D1.2 (verifiziert 2026-09-07):** **1909 grün = 1907 + 2 neue P8-Tests.** Phase-1/2/3/4/5/6/7/8/9/10/12/13/14/15/root = 95+82+105+162+185+76+169+256+95+165+145+82+61+126+105 = **1909** ✅ Plan-Akzeptanz AK2 erfüllt. P15-Sweep mit `PYTHONPATH=.../phase15_v4`. Σ-Erhöhung rein P8 (+2), alle anderen Phasen bit-identisch.

**3. Hook-Verify:** `python3 scripts/check_doc_rotation.py --strict --quiet` → exit 0 nach jedem Commit (nach Code-Commit + nach Rotation-Commit, beide verifiziert).

**4. Git-Stand am Session-Ende (vor Push):**
- HEAD = `468ce3d` (Session-Rotation #7→#8).
- Commits lokal ahead of `origin/main` = 2 (D1.2 Code + Rotation-Commit) — **Nikinger-Push-Freigabe ausstehend** (analog den vorherigen Sessions, eigenmächtiges Pushen bleibt aus; Fable-5.1 + Root-`CLAUDE.md` Working-style-Regel).
- Working tree clean nach jedem Commit.

### Findings

🟢 **D1.2 vollständig:** Wrapper-Klasse 24 LOC + Build-Block-Restrukturierung 48 LOC + 2 Tests 89 LOC + Doc-Kommentar 7 LOC, alles in **einem** atomaren Commit (D1.2 ist klein genug für einen Commit; Splitting an Klasse/Block/Tests wäre künstlich granular gewesen).

🟢 **Wrapper-Disziplin:** `start()` baut immer frisch aus dem Closure; `stop()` ist No-op auf `None` und setzt `self._inner = None` (defensiv, schützt vor Re-Use nach Restart); `restart()` ist die saubere Sequenz `stop() + start()`. Runner-`hasattr(bar_stream, "restart")` greift direkt auf `wrapper.restart()` (kein Fallback-Pfad `stop()+start()` auf demselben Objekt nötig — der Wrapper abstrahiert das genau weg, was der Runner tun würde).

🟢 **Hard Rule 3 unangetastet:** reine Mechanik-Schicht im Wiring-Pfad, kein VETO-Aufruf, keine AI-Verzweigung, keine Order-Trigger-Funktion. `preflight_fn` (Z. 1127-1144) bleibt unverändert. Keyring-Read bleibt nur in preflight_fn.

🟢 **`from universe import UniverseStore`-Verschiebung ist orthogonal:** Lazy-Konvention eingehalten (Import im Function-Body), aber weil `UniverseStore` in beiden nested-Closures (`_epics_in_measurable` + `_build_recorder`) gebraucht wird, ist der Top-of-`if`-Block-Import effizienter als doppelter Lazy-Import. Eine Zeile Diff-Bilanz: `-1` Import-Statement tiefer im Block, `+1` Import-Statement am Top des `if`-Blocks.

🟢 **Test-Pattern dem Schema-Floor-Test nachempfunden:** `test_wiring_schema_floor.py:27-32` ist die Vorlage (sys.path-Insert + offline-safes Import-Setup, weil `scripts.wiring` kein installiertes Paket ist). Tests sind pure-fakes (kein Netz, kein Keyring, kein LLM, kein Live-`data/`-Write).

🟢 **`_FakeInner`-Test-Helper ausreichend:** duck-typed mit `start()`/`stop()` (Z. 31-37 des Test-Files) + `token`-Konstruktor-Argument für die Mutation-Assertion. Für die `_FakeInner`-Instanz wird kein `restart()` implementiert — bewusst, weil der Plan-Test den **Wrapper** testet, nicht den inner-Recorder (das wäre redundant mit dem bestehenden `test_bar_stream_*`-Block in `test_runner.py:917-994`, der `restart`-Calls gegen den Recorder prüft; das Pattern bleibt unangetastet).

🟢 **Cross-Phase-Touch-Disziplin:** D1.2 berührt ausschließlich **P8** (`scripts/wiring.py` + 1 neues Test-File). Keine P1/P2/P3/P4/P5/P7/P9/P15-Touches. P1/P13-Code (`ig_lightstreamer.py`) bleibt **unangetastet** (Opus-Befund #2 wurde absichtlich als P8-Wrapper gelöst, nicht als P1/P13-Inplace-Fix — Plan §6 D1.2 schreibt das explizit vor).

🟢 **Plan-Drift +66 Zeilen dokumentiert:** Plan-Anker `wiring.py:1091-1134` und `wiring.py:1131` (Substanz-Anker: Wrapper-Klasse-Slot und `bar_stream = recorder`-Pin) zeigen im aktuellen Code-Stand auf Z. ~120-153 (Wrapper-Slot) und Z. ~1244 (`bar_stream = recorder`-Pin). Beide Pin-Substanzen (class location + assignment-line) sind unverändert, der Drift ist reine Insertion aus den Phase-13-B0-Source-Kommentaren (Z. 1146-1156 + 33 Zeilen Quelltext-Erweiterung). Im Commit-Message dokumentiert.

### Open questions / blockers

- Keine inhaltlichen Phase-16-Blocker. D1 + D1.2 + D2 ✅ strukturell vollständig.
- **D3 (Margin-Headroom) bleibt offen** — zwingende Operator-Live-Probe D3.0 (`phase1_broker_wrapper/scripts/probe_market_margin.py` für 3 Epics, Demo) *vor* dem Code (Plan §6 D3, L7, P1/P5, AK11). Braucht entweder: (a) ich liefere dir Runbook-Anleitung für die Probe, du führst sie aus, ich baue den Sizing-Code in Folge-Session gegen deine Befunde, oder (b) wir vertagen D3 auf nach Block E.
- **Block E Rest (E2/E3/E4)** bleibt offen — blockiert auf D-Komplettierung (D3) + Operator-Restart. E2 = `scripts/autonomy_report.py` + 5 Tests (deterministisch, read-only, mode=ro), E3 = Runbook Start + Day-0-Checks (Operator), E4 = Tagesroutine + Closeout-Handover nach Tag 10.
- **Live-DB Schema v7 → v9 Akten-Verifikation** (B2, schon gelaufen nach Sessions #3-Exec-Logbuch) — heute nicht Phase-16-Edit, bleibt Operator-Akten-Vermerk.
- **Push-Freigabe-Sequenz:** Nikinger hat zwischenzeitlich die 5 Commits der Session #7 (E1 + Rotation + D1 + D2 + Final-Rotation) gepusht, **origin/main = `e9c8aa7`**. Diese Session hat 2 Commits pending (`64a42d4` + `468ce3d`); Push-Freigabe erwartet (analog Nikinger-Verhalten der letzten Sessions).

### Next (für die Folgesession)

- **D3** = Margin-Headroom B3 (L7, P1/P5, AK11) — **erst** Operator-Live-Probe `phase1_broker_wrapper/scripts/probe_market_margin.py` für 3 Epics (Demo), **dann** Code in `phase5_execution/execution/sizing.py` (Sizing-Grenzfall 27 100 / 24 500 / mf 5 ⇒ 21,0; `mf=None` ⇒ heutiger Cap). ~3 Tests. Zwei Wege:
  - **(a) Vorbereitet:** ich liefere das Runbook + Probe-Skript-Bauanleitung, du führst die Probe aus, ich baue den Code in Folge-Session gegen deine Befunde.
  - **(b) Vertagt:** D3 nach Block E (E2/E3/E4 vorziehen). Operativ sauber, weil D3 keinerlei Voraussetzung für E2-E4 ist.
- **Block E — 2-Wochen-Test** (nach D-Komplettierung + Operator-Restart, oder auch direkt wenn D3 vertagt wird):
  - **E2** = `scripts/autonomy_report.py` (deterministisch, read-only, mode=ro) + 5 Tests (Tagesbericht + Summary PASS/FAIL).
  - **E3** = Runbook Start (Operator, restart-services.sh start + Day-0-Checks).
  - **E4** = Tagesroutine (täglich `--day`-Report) + Closeout-Handover nach Tag 10.

**Block-Status nach dieser Session (endgültig):**

| Block | Status |
|---|---|
| A (Haushalt) | ✅ A-0..A-4 + A-5 Push (Sessions #1-#3) |
| B (Substrat) | ✅ B1+B3 code + B2 Operator-Apply + A-5 Push (Session #3) |
| C (Research-Loop) | ✅ C1+C2+C3+C5 endgültig in code; C4 = Doku-Only (Sessions #4-#5) |
| D (Freischaltung) | ✅ **D1+D1.2+D2 endgültig in code** (Sessions #7+#8); **D3 ⏳** (Folge-Session) |
| E (Autonomie-Test, Vorregistrierung) | ✅ E1 endgültig in docs (Session #6) |
| E (Autonomie-Test, Rest) | ⏳ E2/E3/E4 nach D-Komplettierung + Operator-Restart |

**Push-Status dieser Session:** **0 Commits gepusht** (in dieser Session), 2 Commits pending (D1.2 Code + Final-Rotation) ahead of `origin/main` (= `e9c8aa7`). **Nikinger-Push-Freigabe erwartet**, analog den vorherigen Sessions.

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

---

## Session stopped — 2026-09-07 (MiniMax-M3-Exec-Session #6, Block E Step E1 Vorregistrierung endgültig in docs, Σ 1864 grün unverändert [docs-only], Pause auf Nikinger-Auftrag)

> **Auftrag:** Nikinger-Chat 2026-09-05 (Phase-16-Exec-Folge, „letzten sesion") am 2026-09-07 fortgesetzt: „Next step, atomically, then ask nikinger." — **Block E Step E1** (Plan §6 E1, P11) endgültig in docs. Block D (D1/D1.2/D2/D3) + Block E (E2/E3/E4) bleiben für nachfolgende Sessions.
>
> Plan-Anker: [`../docs/concepts/phase16_activation_plan.md`](../docs/concepts/phase16_activation_plan.md) §6 Block E Step E1 (S. 760–769) · §1 P11 + P17 + P4/P5 + P6 + P7 · §7 AK13 + AK15 + AK16 · §11 Operator-Aktionen #5/#6/#7 · §13 Opus-Review #5/#6/#8/#9.
>
> Ausführungs-Scope: **2 Atomic Commits** (`af99a2c` E1 Vorregistrierung + INDEX-Zeile · `dc505b2` Session-Rotation #5→#6). Push-Freigabe (P18) gilt weiterhin; diese Session pusht **nicht** eigenmächtig.

### Completed

**0. Cross-Session-Drift-Vorab-Check (Session-Start dieser Exec-Folge-Session #6, 2026-09-07):**
- `git log origin/main..HEAD --oneline` → leer (HEAD = `b2a64df` = origin/main; 7 Session-#5-Commits sind inzwischen gepusht).
- `git status` → working tree clean bis auf untracked `data/`.
- Hook `check_doc_rotation.py --strict --phase phase16_activation` → exit 0 (vor dieser Rotation: Phasenkopf 1 Block Exec-#5, Archiv 4 Blocks).
- §6 E1-Verbatim-Bestätigung: 9 Konfig-Werte, 7 PASS-Kriterien mit append-only Messquellen, 4 erlaubte Operator-Ereignisse (P17), 6 Watch-Items, Operator-Regel, Aktiv-Block.

**1. Block-E Step E1 in 1 atomaren Commit:**

| Step | Commit | Scope | Σ-Delta | Akzeptanz |
|---|---|---|---|---|
| **E1** Vorregistrierung | `af99a2c` phase16: docs | **NEU** `phase16_activation/PHASE16_AUTONOMY_PREREGISTRATION.md` (9 vorregistrierte Werte + 7 PASS-Kriterien AK15 mit append-only Messquellen + 4 erlaubte Operator-Ereignisse P17 + 6 Watch-Items + Operator-Regel + Aktiv-Block vom Operator vor E3-Restart) + INDEX-Zeile in `docs/INDEX.md`. | 0 (docs-only) | AK13 (Commit-Zeit < Start-Zeile ist die Nikinger-Pflicht bei E3) + AK15-Framework (Kriterien vorregistriert, Messquellen ausschließlich append-only, Opus-Review §13 #6 eingehalten: keine `*_state.json`, stattdessen `*.log` + `.jsonl` + SQLite-Tabellen) |

**2. Σ-Sweep nach E1 (verifiziert 2026-09-07):** **1864 grün unverändert**. AK2 (Σ ≥ Vorblock) trivial erfüllt.

**3. Hook-Verify:** `python3 scripts/check_doc_rotation.py --strict --quiet` → exit 0 nach Commit + nach Rotation.

**4. Git-Stand am Session-Ende:**
- HEAD = `dc505b2`.
- Commits lokal ahead of `origin/main` = 0 (E1 ist die erste Session nach dem letzten Push) + 2 (diese Session) = **2 Commits ahead**.
- Working tree clean nach jedem Commit (außer untracked `data/`, gitignored).

### Findings

🟢 **E1 erfüllt P11 wörtlich:** Vorregistrierung committet **vor** dem E3-Restart (AK13: Commit-Zeit < Start-Zeile strukturell erfüllbar). Nach dem Start **kein** Edit mehr an den 9 Werten oder 7 Kriterien — Korrekturen nur als neues, datiertes, supersedendes Dokument (M1-Disziplin).

🟢 **Aktiv-Block = Eintragung, kein Edit:** explizit als „Eintragung am E3-Tag **vor** der ersten Start-Zeile" definiert. **Vor** dem Test, **nicht** „nach dem Lauf geschrieben" — P11-Spirit gewahrt.

🟢 **append-only Quellen konsequent:** AK15 misst ausschließlich aus `*.log` + `*.jsonl` + SQLite-Tabellen. `*_state.json` ausgeschlossen (Opus-Review §13 #6). WebUI-Aliveness ehrlich als Operator-Sichtung vorregistriert.

🟢 **PASS-Kriterien messen Autonomie, nicht Profit:** Kriterium 3 zählt nur ≥ 5 autonome CLOSED-Trades (nicht Win-Rate, nicht P&L). P&L explizit ausgeschlossen.

🟡 **Kriterium 7 (Caps unverändert):** pinnt Start-Log-Zeile auf exakte Strings. Mitigation: `daily_loss_cap=1800.0` mit `.0`-Suffix (Python-Float-Default-Repr); beim E3-Runbook-Schritt nachmessen + ggf. Pin-Muster schärfen — bewusst NICHT jetzt (würde M1-Disziplin verletzen).

🟡 **Kriterium 2 (3+1-Regel):** WebUI-Operator-Sichtung ist Selbstverpflichtung, kein technisches PASS. Bewusst so vorregistriert: WebUI-Aliveness ist nicht anders belegbar (Opus-Review §13 #6).

🟡 **Watch-Item W6:** n≈10–20 ≪ `instinct_n_min = 50` → VETO 5 No-Op, per Plan §13 #8 erwartet (Bridge lebt, unter Schwelle). Beim Closeout wird die tatsächliche n-Zahl als Befund geführt.

🟢 **Cross-Phase-Disziplin:** E1 berührt **keinen** Cross-Phase-Code (nur Phase-16-Doc + INDEX-Eintrag). P1/P2/P3/P4/P5/P7/P8/P9/P15 alle unangetastet.

### Open questions / blockers

- Keine. E1 ✅ vollständig. AK13 hängt jetzt nur noch an der **Reihenfolge der Operator-Aktionen** beim E3-Restart (zuerst D1+D2 fertig bauen, dann E3-Restart, dann Vorregistrierung bleibt unangetastet).

### Next (für die Folgesession)

- **Block D — Freischaltung** (Plan §6 D1..D3, nach E1 freigegeben):
  - **D1** = Defaults flippen + `--no-*`-Schalter (P4/P5/P8/P15, AK5) · ~5 Tests
  - **D1.2** = Bar-Stream-Token-Wrapper (P8, Opus-Befund #2, AK5b) · 2 Tests
  - **D2** = Promotion-Bridge + Prädikat-Compiler (P2/P7/P8/P15, AK10) · ~10 Tests
  - **D3** = Margin-Headroom (P1/P5, AK11) · erst Operator-Live-Probe, dann Code · ~3 Tests
- **Block E — 2-Wochen-Test** (nach D + Operator-Restart):
  - **E2** = `scripts/autonomy_report.py` (deterministisch, read-only, mode=ro) + 5 Tests
  - **E3** = Runbook Start (Operator, restart-services.sh start + Day-0-Checks)
  - **E4** = Tagesroutine + Closeout-Handover

**Block-Status nach dieser Session (endgültig):**

| Block | Status |
|---|---|
| A (Haushalt) | ✅ A-0..A-4 + A-5 Push (Sessions #1-#3) |
| B (Substrat) | ✅ B1+B3 code + B2 Operator-Apply + A-5 Push (Session #3) |
| C (Research-Loop) | ✅ C1+C2+C3+C5 endgültig in code; C4 = Doku-Only (Sessions #4-#5) |
| **E (Autonomie-Test, Vorregistrierung)** | ✅ **E1 endgültig in docs** (diese Session) |
| D (Freischaltung) | ⏳ nach E1 (Vorregistrierung) — kann jetzt starten |
| E (Autonomie-Test, Rest) | ⏳ E2/E3/E4 nach D + Operator-Restart |

**Push-Status dieser Session:** **0 Commits gepusht**, 2 Commits pending (E1 + Final-Rotation) ahead of `origin/main`.

---

## Session stopped — 2026-09-05 (MiniMax-M3-Exec-Session #5, Block C Steps C2+C3+C5 endgültig in code, Σ 1864 grün = 1862 + 2 neue Tests (1× P4 + 1× P3), Pause auf Nikinger-Auftrag)

> **Auftrag:** Nikinger-Chat 2026-09-05 (Phase-16-Exec-Folge): „Block C noch offen: C2 + C3 + C5. E1 (Vorregistrierung) muss vor Block-D-Operator-Restart committet sein — kann jederzeit in einer Mini-Session passieren." — **Block C vollständig abgeschlossen** (Plan §6 C2 + C3 + C5: C2 = Prompt-Satz, C3 = Budget 300k, C5 = Breaker-Semantik); E1 + Block D + Block E bleiben offen für nachfolgende Sessions.
>
> Plan-Anker: [`../docs/concepts/phase16_activation_plan.md`](../docs/concepts/phase16_activation_plan.md) §6 Block C Steps C2 (S. 502-512) + C3 (S. 515-522) + C5 (S. 531-555) · §1 P2 (Prompt-Satz) + P3 (Budget-Flip + Caching gestrichen mit Begründung) + §1 P18 (P3 Runde 2 freigegeben) · §4 Cross-Phase-Tabelle (P4 + P8 + P3 freigegeben) · §7 AK7+AK8+AK17.
>
> Ausführungs-Scope: **3 Atomic Commits** (`ac39ee4` C2+C3 kombiniert · `c9a34e0` C5 · dieser Final-Commit Σ-Sweep+Rotation). Push-Freigabe (P18 / Fable-5.1-Handover) gilt weiterhin; diese Session pusht **nicht** eigenmächtig (Nikinger entscheidet am Session-Ende).

### Completed

**0. Cross-Session-Drift-Vorab-Check (Session-Start dieser Exec-Folge-Session #5, 2026-09-05):**
- `git log origin/main..HEAD --oneline` → 4 Commits (`a329180` Exec-#4-Σ-Verifikation, `acc941f` C1, `e26ff06` Session-Rotation #3→#4, `6ee2620` B2-Confirmed).
- `git status` → working tree clean.
- Hook `check_doc_rotation.py --strict --phase phase16_activation` → exit 0 (vor Mini-Rotation: Phasenkopf 1 Block Exec-#4, Archiv 3 Blocks).
- §9 Source-Pins verbatim bestätigt: `phase4_research/research/prompt.py:46` ABSTAIN-Anker + `scheduler/config.py:134` + `scheduler/run.py:62` + `external_data/fetcher.py:407-411` (jetzt 411-419 nach C5).
- §9 Greps ausgeführt: kein P4-Pin auf „When in doubt" / „Recent trades (newest" außerhalb der C1-Test-Datei (Plan §9 #2 bestätigt); alle P8-`200_000`-Pins identifiziert (`config.py:134`, `run.py:62`, `live_test.py:60`, `test_run.py:20,52`, `test_config.py:39`, `test_webui.py:338-339,348` — 7 Stellen, jetzt alle auf 300_000 migriert); P3-Circuit-Tests-Liste: `test_circuit_opens_after_repeated_get_history_failures` (umbenannt-Pfad via `always_rate_limit`-Fixture), `test_circuit_success_after_failures_resets` (bleibt unverändert), `test_default_circuit_is_constructed_when_omitted` (bleibt unverändert).

**1. Block-C Steps C2+C3+C5 in 2 atomaren Commits:**

| Step | Commit | Scope | Σ-Delta | Akzeptanz |
|---|---|---|---|---|
| **C2** Prompt-Satz „context, not a veto" + **C3** Budget 200k → 300k | `ac39ee4` phase16+phase4+phase8: code | **C2:** `phase4_research/research/prompt.py` neuer System-Prompt-Satz nach ABSTAIN-Zeile („Recent trades are context for lessons and sizing, NOT a veto…") + 1 Substring-Pin-Test `test_system_prompt_names_history_as_context_not_veto` in `tests/test_prompt.py`. **C3:** `scheduler/config.py` Default `daily_token_budget: 200_000 → 300_000` + Doc-String (Begründung „exhausted daily at ~15:48") + CLI-Default in `scheduler/run.py:62` + Help-Text-Update + `live_test.py:60` (Operator-Tool) + 5 Test-Pins (`test_run.py:20,52`, `test_config.py:39`, `test_webui.py:338-339,348`) inkl. Prozent-Pin 0.6 (war 0.9, 100\*1800/300000). | P4 +1 (161→162), P8 ±0 (253, default flip + Test-Parität) | AK7 ✅ (C2-Satz im System-Prompt) + AK8 ✅ (Budget 300k in Config + CLI + alle Test-Pins) |
| **C5** Breaker-Semantik | `c9a34e0` phase16+phase3: code | `external_data/fetcher.py` neuer zweigliedriger `except` (RateLimitError record_failure + raise; DataUnavailableError raise-only) — leerer Frame ist Datenurteil, kein Ausfall. `tests/test_circuit.py` lokaler `YFRateLimitError` (Mirror `test_fetcher.py`-Pattern) + neue `always_rate_limit`-Fixture + bestehender `test_circuit_opens_after_repeated_get_history_failures` umgebaut auf Rate-Limit-Pfad (Circuit-Öffnung weiter gepinnt) + neuer `test_empty_frame_does_not_open_circuit` (4× empty-frame ⇒ circuit bleibt zu, 5. Call versucht erneut Netz). | P3 +1 (104→105) | AK17 ✅ (empty frame öffnet Circuit nicht; RateLimitError öffnet weiter) |

**2. Σ-Sweep nach Block C (verifiziert 2026-09-05):** **1864 grün (= 1862 + 2 neue Tests).** Phase-1/2/3/4/5/6/7/8/9/10/12/13/14/15/root = 95+78+105+162+185+76+166+253+95+165+145+82+61+91+105 = **1864** ✅ exakt Plan-Akzeptanz AK2 erfüllt. P15-Sweep mit `PYTHONPATH=.../phase15_v4` (Phase-eigenes `instinct`-Package, Pre-existing Quirk aus Phase 15) — 91 unverändert.

**3. Hook-Verify:** `python3 scripts/check_doc_rotation.py --strict --quiet` → exit 0 nach jedem Commit.

**4. Git-Stand am Session-Ende:**
- HEAD = dieser Final-Commit.
- Commits lokal ahead of `origin/main` = 4 (vorherige, alle Block B/C) + 3 (diese Session: `ac39ee4` C2+C3, `c9a34e0` C5, dieser Final-Commit) = **7 Commits ahead**.
- Working tree clean nach jedem Commit (außer untracked `data/`, gitignored).

### Findings

🟢 **Block C vollständig abgeschlossen** (C1 + C2 + C3 + C5 ✅): L1 (Window) + L2 (Budget) + L9 (Breaker) strukturell zu. **Cross-Phase-Touch-Disziplin eingehalten:** Block C Steps C2+C3+C5 berühren **P4** (C2 = prompt.py + test_prompt.py) + **P8** (C3 = config.py + run.py + 3 Test-Dateien + live_test.py) + **P3** (C5 = fetcher.py + test_circuit.py). Keine P1/P2/P5/P7/P9/P15-Touches.

🟢 **C2 = semantischer Begleiter zu C1:** C1 hat das Zeitfenster gesetzt (mechanisch), C2 benennt die Rolle im System-Prompt. Zusammen verhindern sie, dass eine Pechsträhne nach dem 7. Trade wieder zu einem absorbierenden „5–6 von 7 Verluste → ABSTAIN"-Zustand führt. Substring-Pin ist minimal (zwei Substrings, keine Prompt-Regression möglich).

🟢 **C3 = rein numerischer Flip, Test-Parität gehalten:** P8 253 unverändert. Alle Stellen explizit migriert (Plan §9 #3 grep-verifiziert: 7 Stellen mit `200_000` → `300_000`, übrige Treffer nur in Kommentaren wie „was 200000"). Doc-String dokumentiert explizit, **warum kein `cache_system=True`** (Plan §1 P3: Meter zählt Cache-Reads voll + Sonnet-4.6-Prefix-Mindestlänge 1024 Tokens, System-Prompt ~250 → erwartet 0 Saving). Nikinger-Antwort Runde 2 bestätigt.

🟢 **C5 = minimal-invasiver Eingriff, fail-open Semantik bewahrt:** `DataUnavailableError` re-raised unverändert (Caller sieht weiterhin leeren Frame), `RateLimitError` öffnet Circuit weiterhin. Vorher locked-out 09:05-Phase pro Ticker für 15 min bei Yahoo-Datenleck, jetzt versucht jeder Cycle erneut (3 interne Retries à ~1 s — akzeptabel). Test `test_circuit_opens_after_repeated_get_history_failures` umgebaut: nicht gelöscht (würde Coverage der Circuit-Öffnungs-Mechanik verlieren), sondern auf `always_rate_limit`-Fixture migriert (RateLimitError ist der einzige verbleibende Auslöser).

🟡 **P15-Σ-Quirk dokumentiert:** `phase15_v4/tests/test_instinct_*.py` brauchen `PYTHONPATH=/home/trading-bot/trading-bot/phase15_v4` (Phase-eigenes `instinct`-Package, nicht im venv editable installiert). 4 Errors bei normalem `pytest`-Aufruf sind erwartet (Pre-existing, identisch zum Stand vor dieser Session) — Phase-15-Σ bleibt 91.

🟡 **C4 (Research-Ökonomie Doku-Only, Plan §6 C4) wurde in dieser Session NICHT separat committet:** die Begründung „Quotes im User-Prompt variieren jede Runde ⇒ Dedupe nicht möglich → YAGNI mit Begründung" ist im Phasenkopf (Findings oben, Block-Tabelle unten) bereits dokumentiert. Falls Nikinger einen expliziten Doku-Commit fordert, kann das nachgeholt werden — Code-Touch = 0.

🟡 **Bot bleibt aus:** B2 (Schema-Apply) ist gelaufen, A-5 (Push) ist gelaufen, aber der Bot wurde noch nicht neu gestartet (Plan §6 B2-Fußnote: „Restart erst nach Block D"). C1+C2+C3+C5 wirken beim nächsten Restart sofort (C3 = CLI-Default, C1/C2 = Research-Kontext-Aufbau, C5 = yF-Breaker-Semantik). E1 (Vorregistrierung) zwingend vor Block-D-Operator-Restart.

### Open questions / blockers

- Keine. Block C ✅ vollständig (C1 + C2 + C3 + C5). L1/L2/L9 strukturell zu. Bot bleibt aus bis Block D + Operator-Restart.

### Next (für die Folgesession)

- **E1 (Vorregistrierung)** (Plan §6 E1, P11): `phase16_activation/PHASE16_AUTONOMY_PREREGISTRATION.md` (📕, NEU) — Start-/Enddatum (10 Handelstage), Konfiguration (Demo, max_trades 5, daily_loss_cap 1800, Budget 300k, alle vier Arme ON, Universe ohne Wochenend), PASS-Kriterien AK15 (§7 E2) mit je einer append-only Messquelle, erlaubte Operator-Ereignisse (P17: Backoff-KILL einmal, Reboot = Intervention), Watch-Items. **Muss vor Block-D-Operator-Restart committet sein.**
- **Block D — Freischaltung** (Plan §6 D1..D3): D1 = Defaults flippen + `--no-*`-Schalter (P4/P5/P8/P15) · D1.2 = Bar-Stream-Token-Wrapper (P8, Opus-Befund #2) · D2 = Promotion-Bridge + Prädikat-Compiler (P2/P7/P8/P15) · D3 = Margin-Headroom (P1/P5, Operator-Probe D3.0 zuerst).
- **Block E — 2-Wochen-Autonomie-Test** (Plan §6 E1..E4): nach D + Operator-Restart. E2 = `scripts/autonomy_report.py` (deterministisch, read-only, mode=ro) + Tests · E3 = Runbook Start (Operator) · E4 = Tagesroutine + Closeout-Handover.

**Block-Status nach dieser Session (endgültig):**

| Block | Status |
|---|---|
| A (Haushalt) | ✅ A-0..A-4 + A-5 Push (Sessions #1-#3) |
| B (Substrat) | ✅ B1+B3 code + B2 Operator-Apply + A-5 Push (Session #3) |
| C (Research-Loop) | ✅ **C1+C2+C3+C5 endgültig in code**; C4 = Doku-Only, im Phasenkopf dokumentiert |
| D (Freischaltung) | ⏳ nach E1 (Vorregistrierung) |
| E (2-Wochen-Test) | ⏳ nach D + Operator-Restart |

**Push-Status dieser Session:** **0 Commits gepusht**, 3 Commits pending (C2+C3 + C5 + Final-Sweep) ahead of `origin/main` (gesamt: **7 Commits lokal ahead nach dieser Session**, Fable-5.1-Push-Freigabe gilt weiterhin).

---

## Session stopped — 2026-09-05 (MiniMax-M3-Exec-Session #4, Block C Step C1 endgültig in code, Σ 1862 grün = 1856 + 6 neue P4-Tests, Pause auf Nikinger-Auftrag)

> **Auftrag:** Nikinger-Chat 2026-09-05 (Phase-16-Exec-Folge, Mini-Rotation nach B2-Confirmed): „Block C, aber nur erster Step, danach Session beenden." — **Block C Step C1** (Plan §6 C1, L1-Fix: Historien-Fenster 14d als Post-Filter im P4-Research-Context). C2..C5 + E1 bleiben für nachfolgende Sessions.
>
> Plan-Anker: [`../docs/concepts/phase16_activation_plan.md`](../docs/concepts/phase16_activation_plan.md) §6 Block C Step C1 (S. 470-499) + §1 P2 (Fenster 14d + max 8 Trades + Prompt-Satz) + §1 P4 (P4 Post-Filter, kein SQL-Touch) + §4 Cross-Phase-Tabelle (P4 freigegeben) + §7 AK7.
>
> Ausführungs-Scope: **3 Atomic Commits** (`e26ff06` Session-Rotation · `acc941f` C1 Code+Tests · Final-Commit). Push-Freigabe (P18) gilt weiterhin; diese Session pusht **nicht** eigenmächtig.

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
- HEAD = `a329180` (Final-Commit).
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

---

---
## Session stopped — 2026-09-05 (MiniMax-M3-Exec-Session #3, Block B B1+B3 endgültig in code + Session-Rotation #2→#3 + B2-Operator-Apply + A-5-Push, Σ 1856 grün, alle 4 Dienste gestoppt, Live-DB Schema v9 erreicht, Ledger-Restore 5|250 angewendet)

> **Auftrag:** Nikinger-Chat 2026-09-05 (Phase-16-Exec-Folge): „NEXT (für Exec-Session #3 oder Pause-Fortsetzung): Block B startet (Plan §6 B1..B3). B2 ist Operator-Aktion (P13) und kommt nach Block-B-Commit mit allen 4 Diensten gestoppt." — **Block B in code** (B1 = Schema-Floor, B3 = Wochenend-Filter + Demotion), B2 als vorbereitete Operator-Anweisung an Nikinger übergeben. Nach Block-B-Commit hat Nikinger A-5 (Push) + B2 (Operator-Apply) am Stück ausgeführt.
>
> Plan-Anker: [`../docs/concepts/phase16_activation_plan.md`](../docs/concepts/phase16_activation_plan.md) §6 Block B Steps B1..B3 (S. 365-466) + §1 P8 (Schema-Floor statt In-Daemon-Migration) + §1 P7/P9 (Wochenend-Filter + Demotion) + §4 Cross-Phase-Tabelle (P8 + P9 freigegeben) + §11 Operator-Aktionen.
>
> Ausführungs-Scope: **4 Atomic Commits** (`SESSION-ROT` `36d1553` · B1 `ac3d1c2` · B3 `d82922e` · `ff84dac` Σ-Sweep-Verifikation) **+ 1 B2-Confirmed-Commit** `6ee2620` dieser Session-Finalisierung. Push-Freigabe (P18) erteilt; Nikinger hat in dieser Session eigenständig `git push origin main` ausgeführt (9 Commits gepusht, `82e5f8d..ff84dac`).

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

**Verifikations-Bilanz:** ✅ Schema-Floor 9 erreicht (Migrationen 008+009 angewendet). ✅ `last_resolve_attempt_utc`-Spalte vorhanden → A6 (P7-Reconcile-Backoff) wird beim nächsten OPEN-Trade live-verifizierbar. ✅ Ledger-Restore sauber (250 fälschlich gebuchte Rescue-Punkte aus dem 2026-09-04-Pfad-A-Scharfschaltungs-Bug entfernt). ✅ Backup `data/trading_bot.sqlite.bak-20260905-pre-mig009` ist die Pre-Migration-008-Rückfall-Option. ✅ Bot bleibt aus (Plan §6 B2-Fußnote: „Restart erst nach Block D").

**🟢 Phase 16 L3 vollständig geschlossen:** Schema-Stale war der eine 🔴-Befund, der den Reconcile-Backoff (Phase-7-P12-Reconcile-Timing-Fix) still lahmgelegt hat. Die `wiring.py:1066-1077`-Preflight-Sequenz enthält jetzt **drei** fail-closed Checks (keyring + `account`-Spalte + Schema-Floor), nicht mehr zwei.

### Completed

**0. Cross-Session-Drift-Vorab-Check (Session-Start dieser Exec-Folge-Session #3, 2026-09-05):**
- `git log origin/main..HEAD --oneline` → 5 Commits (alle Block A: `901c15b`, `7f5b516`, `19d0ad3`, `eedd266`, `557761c`).
- `git status` → working tree clean.
- Hook `check_doc_rotation.py --strict --phase phase16_activation` → exit 0.
- Source-Pin gegen `wiring.py:1066-1077` + `discovery.py:131` + `promotion.py:251-262` + `models.py` — alle verbatim bestätigt.

**1. Block-B-Steps B1 + B3 in 2 atomaren Commits (B2 = Operator-Aktion, separat):**

| Step | Commit | Scope | Σ-Delta | Akzeptanz |
|---|---|---|---|---|
| **B1** Schema-Floor | `ac3d1c2` phase16+phase8: code | `wiring.py` `REQUIRED_SCHEMA_VERSION = 9` + `assert_schema_floor(conn)` Modul-Funktion + `preflight_fn`-Aufruf danach + `phase8_scheduler/tests/test_wiring_schema_floor.py` (5 Tests) | +5 (P8: 248→253) | AK4 ✅ |
| **B3** Wochenend-Filter | `d82922e` phase16+phase9: code | `models.py` `WEEKEND_NAME_MARKERS` + `is_weekend_market(epic, name)` + `discovery.py` Filter + `promotion.py` Skip + Demotion + `phase9_universe/tests/test_weekend_market.py` (8 Tests) | +8 (P9: 87→95) | AK9 ✅ |
| **Session-Rotation** | `36d1553` phase16: docs | Phasenkopf Exec-#2 → SESSIONS_ARCHIVE.md + Exec-#3 → Phasenkopf | 0 | Doc-Rotation ✅ |
| **Σ-Sweep-Verifikation** | `ff84dac` phase16: docs | Phasenkopf-Update mit konkreten Commit-Hashes + Σ 1856 | 0 | Doc-Rotation ✅ |

**2. Σ-Sweep nach Block B (verifiziert 2026-09-05):** **1856 grün (= 1843 + 13 neue Tests).** Phase-1/2/3/4/5/6/7/8/9/10/12/13/14/15/root = 95+78+104+155+185+76+166+253+95+165+145+82+61+91+105 = 1856 ✅ AK2 erfüllt.

**3. Hook-Verify:** `python3 scripts/check_doc_rotation.py --strict --quiet` → exit 0 nach jedem Commit.

**4. Git-Stand vor A-5:** HEAD = `ff84dac`, 9 Commits lokal ahead of `origin/main`.

**5. B2 + A-5 Nikinger-Operator-Apply:** ✅ push (9 Commits) · ✅ stop (4 Dienste) · ✅ Backup · ✅ init_db.py v9 · ✅ SQL-Verify · ✅ Ledger-Restore.

**6. Git-Stand nach A-5:** `origin/main = ff84dac`, 0 Commits lokal ahead.

### Findings

🟢 **Block B vollständig abgeschlossen** (B1 + B3 Code + B2 Operator-Apply + A-5 Push): alle drei fail-closed-Sequenzen scharf, Wochenend-Märkte strukturell aus dem Universe gefiltert, Live-DB auf v9.

🟢 **Cross-Phase-Touch-Disziplin eingehalten:** Block B berührt: **P8** + **P9**. Keine P1/P2/P3/P4/P5/P7/P15-Touches.

🟢 **Source-of-truth precedence gewahrt:** B1 = gleicher Mechanismus wie `account`-Check; B3 = additive Edits auf bestehende Schnittstellen.

🟢 **Drei TERM→KILL-Übergänge sind erwartet** (POST_WINDOW-Sleep-Cap-Pattern).

🟢 **`is_weekend_market` Fail-Open Richtung „entdeckt":** beide Filter triggern unabhängig.

🟢 **AK4 live-verifiziert:** drei fail-closed Checks jetzt scharf; v9 erreicht.

🟡 **A-6 (Reconcile-Backoff Live-Verify) wartet auf nächsten OPEN-Trade.**

🟡 **Bot bleibt aus** (Plan §6 B2-Fußnote).

### Open questions / blockers

- Keine. Block B ✅ vollständig.

### Next (für Exec-Session #4)

- **Block C — Research-Loop** (Plan §6 C1..C5): startet in Exec-Session #4.
- **E1 (Vorregistrierung) — VOR dem Restart nach Block D committen**.

**Block-Status nach dieser Session:**

| Block | Status |
|---|---|
| A (Haushalt) | ✅ A-0..A-4 endgültig in code (Session #1+#2); A-5 = Operator-Push |
| B (Substrat) | ✅ B1+B3 code + B2 Operator-Apply + A-5 Push (Session #3) |
| C (Research-Loop) | ⏳ startet in Exec-Session #4 |
| D (Freischaltung) | ⏳ nach C |
| E (2-Wochen-Test) | ⏳ nach D + Operator-Restart |

**Push-Status dieser Session:** **9 Commits gepusht von Nikinger** (`ff84dac` = `origin/main`), 0 Commits pending.

---

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
| D (Freischaltung) | ⏳ nach D + Operator-Restart |
| E (2-Wochen-Test) | ⏳ nach D + Operator-Restart |

**Push-Status dieser Session:** **0 Commits gepusht**, 4 Commits pending (A-1+A-2 + A-3 + A-4 + Session-Rotation) ahead of `origin/main` (gesamt: 8 Commits lokal ahead nach diesem Commit; 9 + A-5-Push nach Operator-Aktion).

---

## Session stopped — 2026-09-05 (MiniMax-M3-Exec-Session #1, Block A Step A-0 — Session-Rotation Plan-Session-Block → SESSIONS_ARCHIVE.md, `scripts/check_doc_rotation.py:66` um `phase16_activation` ergänzt, `tests/` + `scripts/` Verzeichnisse angelegt, Σ 1843 grün unverändert, 0 Code-Edits)

> **Auftrag:** Nikinger-Fable-5.1-Handover 2026-09-05: „Phase 16 Activation, OpenCode/MiniMax-M3-Exec-Session startet mit Block A Step A-0 (Session-Rotation, Hook-Registrierung, Ritual, Σ = 1843 erwartet, Doku-Sweep). Operator-Fenster B2 erst nach dem Block-B-Commit: alle vier Dienste stoppen → Backup → `init_db.py --db-path data/trading_bot.sqlite` → v9 verifizieren → Ledger-Restore-SQL. Ab dann scheitert ein Start mit neuem Code auf v7 laut am Schema-Floor — gewollt. Restart erst nach dem letzten Block-D-Commit, davor E1 (Vorregistrierung) committen; Desktop-Session im Testfenster eingeloggt lassen."
>
> Plan-Anker: [`../docs/concepts/phase16_activation_plan.md`](../docs/concepts/phase16_activation_plan.md) §6 Block A Step A-0 (S. 303-313) + §4 Cross-Phase-Tabelle (Hook-Erweiterung Phase-14-eigener Hygiene-Code, kein Cross-Phase-Touch) + §1 P15 (Doc-Layers-Konvention).
>
> Ausführungs-Scope: **5 Atomic Commits (A-0+A-1+A-2+A-3+A-4+Session-Rotation)** — exakt Block A in code (A-0..A-4 von 5 des Block-A-Plans; A-5 = Operator-Push, separat). Block A ist **Haushalt**, keins der weiteren Steps hat ein Gate. Push erteilt (P18); diese Session pusht **nicht** eigenmächtig (Head ist nach Block A 5 Commits lokal ahead of `origin/main`, `901c15b`-Stand des Vor-A-0-Commits in der Lock-Footnote dokumentiert).
>
> **Σ total 1843 grün** (Plan §2.1 + Phase-15-Session-#13-Bilanz unverändert, **kein** Test-Touch in Block A).

### Completed

**0. Cross-Session-Drift-Vorab-Check (Session-Start, 2026-09-05):**
- `git status` → `main`, working tree clean (bis auf `?? data/`, untracked, `.gitignore`-gedeckt).
- HEAD = `82e5f8d phase16: docs -- Nikinger Runde 2 (P18 ...)`, 7 Commits lokal ahead of `origin/main`.
- `python3 scripts/check_doc_rotation.py --strict --phase phase16_activation` → exit 0 (Block A-0-Vorbedingung: aktuell 1 Session-Block im Phasenkopf, `_max_session_num` returns `None` weil „Plan-Session, Fable 5.1" keine `\d+` trägt → check_archive_sequence early-return bei `head_max is None`).
- Phasenkopf gelesen (115 Z.) + Plan §6 A-0 (S. 303-313) + Plan §13 Opus-Review (B1/D1.2/E2 drei Struktur-Änderungen) + Phase-15-`SESSIONS_ARCHIVE.md`-Header als Vorlage für die Rotation verifiziert.

**1. Block A — alle 5 Steps in 5 atomaren Commits (`901c15b`, `7f5b516`, `19d0ad3`, `eedd266` + dieser Session-Rotation-Commit):**

| Step | Commit | Scope | Σ-Delta | Akzeptanz |
|---|---|---|---|---|
| **A-0** Session-Rotation + Hook + Verzeichnisse | `901c15b` | docs-only: `check_doc_rotation.py:66` +1, `SESSIONS_ARCHIVE.md` NEU, `CLAUDE.md` Exec-#1-Block, `tests/`+`scripts/`/`-Skeleton | 0 | AK1 ✅ |
| **A-1+A-2** Ritual + Σ-Baseline | `7f5b516` | docs-only: phasenkopf sub-sections, turbo=20 (Plan-Erwartung 14+6 Drift seit Phase-15, alle Legacy-Dateinamen, kein Befund), EPIC_MAP=3 exakt, Σ=**1843** exakt | 0 | AK2 ✅ |
| **A-3** Code↔.md-Sweep (4 falsche Behauptungen + Leichen) | `19d0ad3` | docs-only: 8 Edit-Anker in 5 Dateien + ROADMAP.md Phase-16-Block-Häkchen auf `[x]` | 0 | AK3 ✅ |
| **A-4** WebUI-Access-Log + irreführende Loss-Cap-Warnung | `eedd266` | code (P8 freigegeben): `run_webui.sh` `--no-access-log` + `webui/api.py:75` `SchedulerConfig(daily_loss_cap=1800.0)` mit Kommentar | 0 | AK12 ✅ |
| **Session-Rotation** | (dieser Commit) | phasenkopf Exec-#1 → SESSIONS_ARCHIVE.md, Exec-#2 → phasenkopf, ROADMAP.md Block A endgültig ✅ | 0 | — |

**2. Σ-Baseline (A-2, nachgemessen 2026-09-05, Plan §2.1):**

| Phase | grün | | Phase | grün |
|---|---:|---|---|---:|
| phase1_broker_wrapper | 95 | | phase9_universe | 87 |
| phase2_persistence | 78 | | phase10_v3 | 165 |
| phase3_external_data | 104 | | phase12_data_foundation | 145 |
| phase4_research | 155 | | phase13_live_data | 82 |
| phase5_execution | 185 | | phase14_discovery | 61 |
| phase6_debate | 76 | | phase15_v4 | 91 |
| phase7_reward | 166 | | root `tests/`` | 105 |
| phase8_scheduler | 248 | | **Σ** | **1843** |

### Findings

🟢 **Block A endgültig in code (A-0..A-4 ✅):** alle 5 atomaren Commits in der erwarteten Reihenfolge; Σ-Baseline 1843 unverändert; Hook-Verify exit 0 nach jedem Step; Plan-Garantie „Phase 16 führt keine neue Turbo-Referenz ein" eingehalten.

🟢 **A-3 Drift-Sweep hat die zwei Doku-Lügen + zwei Leichen geschlossen** (Plan §13 Opus-Befund #1 = `run_migrations()`-Behauptung in 4 Stellen korrigiert; Plan-Session-Vermerk „LiveQuoteCache nie gebaut (0 Treffer)" in 2 Stellen als *gegenstandslos* markiert). Code-Wahrheit (`wiring.py:803` ohne `run_migrations()`) wird jetzt von der Doku nicht mehr widersprochen.

🟢 **A-4 ist die erste Cross-Phase-Code-Touch der Phase 16** (P8 freigegeben in Plan §4 / P12). Phase-8-Tests 248 unverändert grün — die WebUI-Default-Config-Korrektur hat null Test-Impact (alle Tests passen ihre eigene `SchedulerConfig`).

🟡 **A-5 (Operator-Push) bleibt offen:** 5 Commits lokal ahead of `origin/main` nach Block A; Nikinger entscheidet am Session-Ende. Fable-5.1-Handover hat Push für alle Commits erteilt, aber diese Session pusht **nicht** eigenmächtig (P13 / Root-`CLAUDE.md` Working-style).

🟡 **WebUI-Log-Wachstum < 1 MB/Tag erst nach WebUI-Restart messbar** (Block D Restart-Fenster). AK12 ist mit dem Code-Edit committed, das messbare Kriterium kommt mit dem Restart.

🟢 **Plan-Session-Block + Exec-Session-#1-Block + Plan-Session-Block jetzt sauber gestapelt** (newest-first im Archiv; Phasenkopf trägt genau 1 Block = Exec-Session #2). `_max_session_num` Archiv-Wert: `1` (aus Exec-Session #1 Heading) — `head_max = 1` nachher (Exec-Session #2 → `2`). Beim ersten Check nach diesem Commit: `arch_max == 1`, `head_max == 2`, `expected == 1` → `1 == 1` ✅ PASS.

### Open questions / blockers

- Keine in Block A. Plan-Sub-Session-`## Session stopped` Block hat keinen Status-Block, daher wird Plan-Session-Block (bottom) **nie** von der Doc-Rotation verdrängt — bewusste Konvention (Phase-15-Vorbild).
- Block-B-Gate (B1 = `assert_schema_floor`-Funktion, 3 Tests + B3 = Wochenend-Filter+Demotion, 4 Tests) ist unabhängig von Block A, startet in Exec-Session #2.

### Next (für Exec-Session #2)

- **Block B — Substrat** (Plan §6 B1..B3, kein Cross-Phase-Gate, Phase 16 startet nach A):
  - **B1** `assert_schema_floor(conn, required=9)` in `phase8_scheduler/scripts/wiring.py` + 3 Tests in `phase8_scheduler/tests/` (`v9 ok`, `v7 raise mit init_db.py im Text`, `leere Tabelle raise`). Quelle: `wiring.py:1066-1077` Preflight-Block.
  - **B3** Wochenend-Instrumente: `is_weekend_market(epic, name)` in `phase9_universe/universe/models.py` + Discovery-Block (`discovery.py:131`) + Promotion-Demotion (`promotion.py:251-262` + neue Loop-Zeile). 4 Tests in `phase9_universe/tests/`.
- **B2 — Operator-Apply** (P13, **erst nach Block-B-Commit**): alle 4 Dienste stoppen → Backup → `init_db.py --db-path data/trading_bot.sqlite` → SQL-Verify v9 → Ledger-Restore (Plan §6 B2). Schema-Floor wirkt ab B1-Commit; ein versehentlicher Start mit altem Code vor B2 wirft laut mit `init_db.py`-Anweisung im Text — gewollt.

---

## Session stopped — 2026-09-05 (Plan-Session, Fable 5.1 — Phase 16 eröffnet, Plan committet)

> **Auftrag:** Nikinger-Chat 2026-09-05: „Phase 16 sollte mind. alle Löcher, die der Bot noch hat,
> stopfen, sodass alle Funktionen freigeschaltet werden, und nach Phase 16 ein ausgiebiger Test
> von z. B. 2 Wochen komplett autonom." Plan bis Ausführungsreife, Fragen gebündelt vorab,
> Advisor-Ersatz per Agent (Opus vor dem Festlegen, Sonnet-Cold-Read vor „fertig").

### Completed
- **Recherche read-only** (Live-DB `mode=ro`, Logs, `/proc`, git): 9 Löcher L1–L9 verifiziert
  (Plan §3), Σ-Baseline **1843** selbst gemessen (Plan §2.1), 7 Commits lokal ahead (`2f9eb82`).
- **Nikinger-Fragerunde** (10 Entscheidungen, alle gelockt → Plan §1 P1–P17).
- **Opus-Plan-Agent-Review** (Plan §13): 3 Struktur-Änderungen übernommen — B1 = Schema-Floor
  statt In-Daemon-Migration (gelockte Preflight-Entscheidung `wiring.py:1070` + Lock-Risiko),
  D1.2 = Bar-Stream-Token-Wrapper (latenter Bug seit Phase 13 B3), E2 = append-only Messquellen;
  C3b Caching gestrichen (Meter zählt Cache-Reads voll + Präfix < 1024); Ledger-Restore nach B2;
  P17 erlaubte Operator-Ereignisse vorregistriert. Ein Dissens (Compiler) dokumentiert.
- **Sonnet-Cold-Read** (Anker-Verifikation): 8 Anker-Korrekturen + `InstinctValidation.decision` verifiziert + D2.6-Einfügepunkt (`wiring.py:832`) festgelegt — Plan §13.
- **Nikinger Runde 2** (Plan P18): Push ✅ · P3 für C5 freigegeben · Allein-Entscheidungen bestätigt · **Exec-Modell = OpenCode / MiniMax M3** für alle Blöcke.
- `docs/concepts/phase16_activation_plan.md` (📕, NEU) · dieser Phasenkopf (NEU) · `docs/INDEX.md`
  2 Zeilen · `ROADMAP.md` Phase-16-Abschnitt · root `CLAUDE.md` Status-Absatz + Tabellenzeile.
- **0 Code-Edits, 0 Bot-Touch** (Bot lief die ganze Session, PID 124569 seit 09-03).

### Findings
- 🔴 **L3 ist die eine Doku-Lüge, die Code-Wahrheit widerlegt:** „`db.py:run_migrations()` wendet
  beim nächsten Service-Restart automatisch an" steht in root-CLAUDE.md:108, ROADMAP.md:441 und
  im P15-Handover (§7 E1, §9.13, §10 #4) — kein Produktions-Caller existiert. Korrektur = Plan A-3.
- 🟡 **Zwei Stellen, an denen die Plan-Session allein entschieden hat** (**in Runde 2 bestätigt**): (a) `InstinctConfig.enable_instinct_promotion` → Default True (P5, supersedet
  P15-P10, Begründung: VETO 5 kann nur vetoen); (b) Caching **nicht** bauen trotz „können wir
  testen" (P3, zwei verifizierte Fakten machen den Test ergebnislos).
- 🟢 C5 (L9): P3-Freigabe in Runde 2 erteilt — Step ist regulär.
- 🟢 `LiveQuoteCache` existiert nicht (0 Treffer) — ROADMAP 9b + phase9-Head führen eine Leiche (A-3).

### Next
- **Exec-Session (OpenCode / MiniMax M3, Einstieg über `AGENTS.md`):** Plan §6 **Block A, Step A-0** — diesen Block per
  Rotationsregel nach `SESSIONS_ARCHIVE.md` (neu anlegen) rotieren, `check_doc_rotation.py:66` um
  `phase16_activation` ergänzen, dann A-1 (Ritual), A-2 (Σ = 1843 erwartet), A-3 (Sweep).
- ~~Push~~ erledigt in der Plan-Session (Runde 2).
- **Operator im B2-Fenster** (alle vier Dienste gestoppt): Backup → `init_db.py --db-path
  data/trading_bot.sqlite` → Verify v9 → Ledger-Restore SQL (Plan §6 B2).

### Open questions / blockers
- Keine. Runde 2 hat alle drei Punkte geklärt (Plan P18).