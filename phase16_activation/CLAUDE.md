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
updated: 2026-09-07 (+ Exec-Session #7 → Archiv; Exec-Session #8 schließt Block D Step D1.2 [Bar-Stream-Token-Wrapper, AK5b, P8 only] ab, D3 steht aus; Phasenkopf trägt Exec-#8)
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
## Session stopped — 2026-09-07 (MiniMax-M3-Exec-Session #8, Block D Step D1.2 endgültig in code, Σ 1909 grün = 1907 + 2 neue P8-Tests [P8 +2], Pause auf Nikinger-Auftrag)

> **Auftrag:** Nikinger-Chat 2026-09-07 (Phase-16-Exec-Folge, „letzten sesion" → „Next step, atomically, then ask nikinger" → Fragebogen-Antwort „D1.2, also der nächste Step bitte"). — **Block D Step D1.2 (Bar-Stream-Token-Wrapper)** endgültig in code (P8 only, Opus-Befund #2, AK5b). D3 (Margin-Headroom mit zwingender Operator-Live-Probe D3.0 vor Code) + Block E (E2/E3/E4) bleiben für nachfolgende Sessions.
>
> Plan-Anker: [`../docs/concepts/phase16_activation_plan.md`](../docs/concepts/phase16_activation_plan.md) §6 Block D Step D1.2 (S. 592-619, inkl. `_RebuildingBarStream`-Klassen-Skizze Z. 604-613 + Wrapper-Anker `wiring.py:1131` → `bar_stream = _RebuildingBarStream(_build_recorder)` + 2 Test-Skizzen Z. 617-619) · §1 P4 (Defaults ON, Cross-Phase-Freigabe P8) · §7 AK5b (Wrapper frisch-baut gegen CURRENT tokens, ein `restart()`-Call pro Token-Rotation). · §9 Source-Pin-Liste (Plan nennt `wiring.py:1091-1134` + `wiring.py:1131`; aktueller Code-Stand: heute sind die Pin-Zeilen **+66** versetzt durch Phase-13-B0-Source-Block-Erweiterung; Plan-Drift notiert, Anker-Substanz unverändert).
>
> Ausführungs-Scope: **2 Atomic Commits** (`64a42d4` D1.2 Code + Tests · dieser Final-Commit Session-Rotation #7→#8). Push-Freigabe-Stand: zwischen Session #7 und jetzt hat Nikinger die 5 pending Commits der Session #7 (E1 + Rotation + D1 + D2 + Final-Rotation) per `git push origin main` gepusht — `origin/main` ist jetzt auf `e9c8aa7`. Diese Session pusht die **eigenen** 2 Commits **nicht** eigenmächtig (Nikinger-Auftrag am Session-Ende erwartet, Cross-Session-Pattern).

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
- HEAD = dieser Final-Commit (Session-Rotation #7→#8).
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
- **D3 (Margin-Headroom) bleibt offen** — zwingende Operator-Live-Probe D3.0 (`phase1_broker_wrapper/scripts/probe_market_margin.py` für 3 Epics, Demo) *vor* dem Code (Plan §6 D3, L7, P1/P5, AK11). Braucht entweder: (a) ich liefere dir Runbook-Anleitung für die Probe, du führst sie aus, ich baue den Sizing-Code in Folge-Session, oder (b) wir vertagen D3 auf nach Block E.
- **Block E Rest (E2/E3/E4)** bleibt offen — blockiert auf D-Komplettierung (D3) + Operator-Restart. E2 = `scripts/autonomy_report.py` + 5 Tests (deterministisch, read-only, mode=ro), E3 = Runbook Start + Day-0-Checks (Operator), E4 = Tagesroutine + Closeout-Handover nach Tag 10.
- **Live-DB Schema v7 → v9 Akten-Verifikation** (B2, schon gelaufen nach Sessions #3-Exec-Logbuch) — heute nicht Phase-16-Edit, bleibt Operator-Akten-Vermerk.
- **Push-Freigabe-Sequenz:** Nikinger hat zwischenzeitlich die 5 Commits der Session #7 (E1 + Rotation + D1 + D2 + Final-Rotation) gepusht, **origin/main = `e9c8aa7`**. Diese Session hat 2 Commits pending (`64a42d4` + Final-Rotation); Push-Freigabe erwartet (analog Nikinger-Verhalten der letzten Sessions).

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