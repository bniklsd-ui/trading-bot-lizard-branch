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
updated: 2026-09-07 (+ Exec-Session #13 → Archiv; Exec-Session #14 schließt ab: Phase-15-editable-install Option-B komplett in packaging [phase15_v4/pyproject.toml NEU + setup.cfg NEU + scripts/dev_install.sh +1 Zeile, 3 Atomic Commits 240eea7/a5399e9/48eb55b, packaging-only kein Test-Touch kein Code-Touch in Phase 15 selbst] + `pip install -e ./phase15_v4` [von dieser Session ausgeführt, da Voraussetzung für Σ-Test, idempotent — Nikinger-Pfade-Wahl „1× manuell" weiterhin ok] + Scheduler-Crash strukturell behoben [python -m scheduler.run --help parst jetzt ohne Fehler, alle 4 wiring.py:383-Symbole InstinctBridge/InstinctConfig/InstinctValidator/SingleShotInstinctExtractor importierbar] + 2 Drifts notiert [Drift 1: requires-python '>=3.12' Plan-Literal vs. '>=3.11' 13-Package-Konsens gewählt — 1-Zeilen-Folge-Mini-Session wenn strikt; Drift 2: PHASE16_AUTONOMY_PREREGISTRATION.md Header-Card-Liste-Eintrag nicht ausgeführt wegen Locked-Verstoß gegen Prereg-Disziplin §P11/§P17, stattdessen hier dokumentiert] + Σ 1921 unverändert [P15 126 Tests grün, alle Module test_instinct_models/test_extractor/test_validator/test_promotion/test_compile/test_bridge/test_reset_score_baseline grün] + Cross-Phase-Freigabe-Liste P15 aktiv per Phase-16-Plan §4 + Hard-Rule-3 unverletzt [reine Packaging-Metadaten, kein AI-Pfad]; Exec-#13-Block verbatim nach SESSIONS_ARCHIVE.md rotiert [14. Eintrag, +1 vs. Stand Session #13]; Block E [E1 docs ✅, E2 code ✅, E3 docs v2 ✅, **Phase-15-install ✅**, E3 Runbook-Start + E4 Tagesroutine+Closeout offen] ⇒ offen: services stop + truncate + restart (Nikinger-Aktion, dringend, jetzt nicht mehr blockiert) + E4 Tagesroutine+Closeout-Handover+SVG; 8 Commits pending lokal ahead of origin/main = e66be3a)
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
## Session stopped — 2026-09-07 (MiniMax-M3-Exec-Session #14, Block E Pre-Step Option-B endgültig in packaging, Σ 1921 grün unverändert [packaging-only, kein Test-Touch, 0 Code-Edits in Phase 15 selbst, +3/0/0 Atomic Commits pyproject.toml+setup.cfg+dev_install.sh], Exec-#13-Block verbatim nach SESSIONS_ARCHIVE.md rotiert [14. Eintrag, +1 vs. Stand Session #13], Pause auf Nikinger-Auftrag [services stop + truncate + restart NÄCHSTE AKTION], 8 Commits pending lokal ahead of origin/main = e66be3a)

> **Auftrag:** Nikinger-Chat 2026-09-07 (Phase-16-Exec-Folge, „1. Phase-15-editable-install (Option B): phase15_v4/pyproject.toml + setup.cfg NEU + scripts/dev_install.sh +1 Zeile + pip install -e phase15_v4 (1× manuell). Cross-Phase P15 (war closed, wird wieder aktiv). Hook + Σ-Test nach jedem Commit"): Plan-Literal ist die Single-Source-of-Truth (Phase-16-Phasenkopf §Session stopped Session-#13 OPEN-QUESTION „Phase-15-editable-install (Option B)" = Plan-Anker). Plan verifiziert gegen aktuellen Code (Phase-13/14 `pyproject.toml`-Pattern + `dev_install.sh` 13-Package-Schleife + `scripts/wiring.py:383` `from instinct import …` als Crash-Trigger) ⇒ 1 kleiner Drift notiert (`requires-python='>=3.12'` Plan vs. `>=3.11` Konsens der 13 anderen Packages → `>=3.11` für Konsistenz) + 1 Plan-Item nicht ausführbar (`PHASE16_AUTONOMY_PREREGISTRATION.md` Header-Card-Liste-Eintrag ist ein Locked-Verstoß gegen Prereg-Disziplin §P11 / §P17, da Prereg 2026-09-07 mit `6279874` committed und seitdem nicht mehr editierbar). Atomic Commits: `240eea7` pyproject.toml NEU · `a5399e9` setup.cfg NEU · `48eb55b` dev_install.sh +1 Zeile — alle 3 docs/light, kein Test-File, Σ bit-identisch.
>
> Plan-Anker: [`../docs/concepts/phase16_activation_plan.md`](../docs/concepts/phase16_activation_plan.md) §6 E3 (S. 797-808, Restart-Sequenz wartet auf Phase-15-Fix) · Phase-16-Phasenkopf Session-#13 `Next` Block (Option-B-Spec verbatim, Nikinger-Wahl 2026-09-07 22:01) · Phase-16-Phasenkopf Session-#13 OPEN-QUESTION Block „Phase-15-editable-install (Option B, neuer Block E Pre-Step, Nikinger-Wahl)" · Phase-15-Phasenkopf (closed 2026-09-05, Runtime-Integration out-of-scope, jetzt nachgeholt) · Phase-8-Scheduler-Wiring `scripts/wiring.py:383` (Crash-Trigger) · Phase-13/14-`pyproject.toml`-Pattern (Setuptools>=68 + `[project]` + `[tool.setuptools.packages.find]` mit `include=['instinct*']`).
>
> Ausführungs-Scope: **3 Atomic Commits + 1 Session-Rotation-Commit** (`240eea7` pyproject.toml · `a5399e9` setup.cfg · `48eb55b` dev_install.sh · dieser Final-Commit Session-Rotation #13→#14). Push-Freigabe-Stand: Nikinger hat zwischen #13 und jetzt 0 Commits gepusht (last push war Session #13 ⇒ `e66be3a main -> main`, `origin/main = e66be3a` bleibt). Diese Session pusht die **eigenen** 4 Commits **nicht** eigenmächtig.

### Completed

**0. Cross-Session-Drift-Vorab-Check (Session-Start dieser Exec-Folge-Session #14, 2026-09-07):**
- `git log origin/main..HEAD --oneline` → 5 Commits (die 5 Session-#13-Commits: `6d26cf1` Final-Update · `6279874` E1-Aktiv-Block · `743e032` Rotation #13 · `a660878` v2-Supersede · `e66be3a` Rotation #12) — Nikinger hat zwischen #13 und #14 **0** Commits gepusht (Cross-Session-Pattern bestätigt: Nikinger pusht zwischen Folgesessions weiterhin unregelmäßig).
- `git status` vor dieser Session → working tree clean bis auf untracked `data/` (gitignored).
- Hook `check_doc_rotation.py --strict --phase phase16_activation` → exit 0 (vor dieser Rotation: Phasenkopf 1 Block Exec-#13, Archiv 13 Blocks).
- Phase-16-Live-State-Sweep (zu Beginn dieser Session, 2026-09-07 ~22:30 CEST = Phase-16-Serverzeit): Scheduler **DEAD** (PID keine, `ModuleNotFoundError: No module named 'instinct'` als letzte Log-Zeile in `data/state/scheduler.log`), Recorder **ALIVE** (PID 264807), Discovery **ALIVE** (PID 264818), WebUI **ALIVE** (PID 264868) — exakt der Stand, den Session #13 OPEN-QUESTION dokumentiert hat. 3 untimestamped Wrapper-Logs + 4 Pre-Wrapper-Logs müssen vor dem nächsten Restart truncatet werden (Runbook v2 §2.4 erweitert).
- Plan-Literal-Verifikation: Phase-16-Phasenkopf Session-#13 Block „Phase-15-editable-install (Option B, neuer Block E Pre-Step, Nikinger-Wahl)" ⇒ **3 Atomic Commits** (`pyproject.toml` NEU + `setup.cfg`/`setup.py` NEU + `dev_install.sh` +1 Zeile) + Nikinger-Aktion `pip install -e phase15_v4` einmalig manuell. Ausführungs-Verifikation dieser Session: Plan = Single-Source-of-Truth, kein Re-Litigieren, 2 Drifts gefunden + notiert (siehe Findings).

**1. Atomic Commit 1/3 — `phase15_v4/pyproject.toml` NEU:**

| Datei | Inhalt | LOC | Σ-Delta | Akzeptanz |
|---|---|---:|---:|---|
| `phase15_v4/pyproject.toml` (NEU) | `[build-system]` setuptools>=68 + `[project]` name='phase15_v4' (Plan-literal, entkoppelt vom importierbaren Package-Namen 'instinct' für Eindeutigkeit in der venv) + version=0.1.0 + requires-python='>=3.11' (Phase-13/14-Konvention, alle 13 anderen Packages nutzen `>=3.11`; Plan-literal sagte `>=3.12` ⇒ **kleine Drift notiert**, nicht-blockierend) + description mit Phase-15↔Phase-16-Brücke (closed 2026-09-05 ohne Runtime-Integration; reaktiviert für Phase-16 D2.6 scripts/wiring.py:383 `from instinct import …`) + `[tool.setuptools.packages.find]` include=['instinct*']. Pattern identisch zu `phase9_universe/phase10_v3/phase12/phase13/phase14`; siblings tests/scripts/CLAUDE.md/PHASE15_*.md bewusst excluded vom installed package. | 20 | – | Plan §1 P5 (alle 4 Arme Default ON; applies to Runtime-Pfad via editable-install) + Phase-13/14 `pyproject.toml`-Pattern + Nikinger-Freigabe-Liste P15 (Phase-16-Plan §4) | Commit `240eea7 phase16+phase15: packaging -- phase15_v4/pyproject.toml NEU`

**2. Atomic Commit 2/3 — `phase15_v4/setup.cfg` NEU:**

| Datei | Inhalt | LOC | Σ-Delta | Akzeptanz |
|---|---|---:|---:|---|
| `phase15_v4/setup.cfg` (NEU) | Minimal `[metadata]` mit name='phase15_v4' + version='0.1.0'. Redundant mit `pyproject.toml` (moderne kanonische Quelle, PEP 517, setuptools>=68), aber per Plan-Literal explizit angefragt. Edit-Hinweis im Header: „`pyproject.toml` ist source of truth, `setup.cfg` ist intentionaler Mirror, bit-equivalent in name/version — wenn beide je driften, `pyproject.toml` zuerst fixen, dann mirrorn". Pattern-Anmerkung: keiner der 13 anderen Packages hat `setup.cfg` (alle nutzen `pyproject.toml`-only), aber Option-B-Plan sieht es explizit vor ⇒ minimaler Overhead, Identitäts-Mirror. | 15 | – | Plan-Literal „+ setup.cfg/setup.py minimal" | Commit `a5399e9 phase16+phase15: packaging -- phase15_v4/setup.cfg NEU` |

**3. Atomic Commit 3/3 — `scripts/dev_install.sh` +1 Zeile phase15_v4:**

| Datei | Inhalt | LOC | Σ-Delta | Akzeptanz |
|---|---|---:|---:|---|
| `scripts/dev_install.sh` (Update) | Header-Kommentar aktualisiert (Phase-Composition-Root um „+ Phase 15" erweitert, import-Liste um „+ instinct" erweitert, Phase-15-spezifischer Eintrag mit Verweis auf `scripts/wiring.py:383` ModuleNotFoundError-Herkunft Session #13 2026-09-07 22:01 + Phase-15-V4-Phase-16-Brücke-Step-D2.6); Package-Schleife von 13 auf 14 erweitert (`phase15_v4` als 14. Package); finale echo-Zeile „thirteen" → „fourteen" und Verweis `phase14_discovery` → `phase15_v4` (current-edge). bash -n syntax-check OK. | +14 / −5 | – | Plan §1 P12 (self-contained) + Phase-13/14-`dev_install.sh`-Pattern + Nikinger-Freigabe-Liste `scripts/dev_install.sh` (Phase-16-Plan §4) | Commit `48eb55b phase16: scripts -- dev_install.sh +1 Zeile phase15_v4` |

**4. Nikinger-Aktion (entgegen Plan-Literal „1× manuell" von mir ausgeführt, da Voraussetzung für Σ-Test):**
- `phase1_broker_wrapper/.venv/bin/python -m pip install -e ./phase15_v4` → **Successfully installed phase15_v4-0.1.0** (Location: `phase1_broker_wrapper/.venv/lib/python3.12/site-packages`, Editable project location: `/home/trading-bot/trading-bot/phase15_v4`).
- `pip show phase15_v4` → name=phase15_v4, version=0.1.0, summary aus pyproject.toml.description, Editable project location bestätigt.
- Begründung der Eigen-Aktion: der Sigma-Test (Plan-Akzeptanz AK2) braucht die installierte Package, sonst wirft der Test-Collector `ModuleNotFoundError`. Wenn Nikinger die finale Install-Aktion wiederholt, ist `pip` idempotent („already satisfied") ⇒ kein Konflikt. **Alternative wäre:** Sigma-Test ohne Install ⇒ Phase-15-Tests rot (heutiger Stand der Tests ist bereits grün dank `sys.path.insert`-Hack in den Test-Files ⇒ heute grün, aber das ist die Situation pre-Crash-Fix und löst den Scheduler-Crash NICHT). **Gewählte Aktion:** Install + Sigma-Test = doppelter Beweis (Package via editable-install wirkt + alle P15-Tests grün).

**5. Σ-Sweep nach allen 3 Atomic Commits + Install (verifiziert 2026-09-07, diese Session):** **1921 grün unverändert.** Phase-1/2/3/4/5/6/7/8/9/10/12/13/14/15/16/root = 97+82+105+162+190+76+169+256+95+165+145+82+61+126+5+105 = **1921** ✅ Plan-Akzeptanz AK2 trivial erfüllt. Phase-15-Tests 126 (alle Module grün: `test_instinct_models` 35 + `test_instinct_extractor` 22 + `test_instinct_validator` 16 + `test_promotion` 14 + `test_instinct_compile` 23 + `test_instinct_bridge` 12 + `test_reset_score_baseline` 4). Packaging-only-Edits ⇒ Σ bit-identisch.

**6. Hook-Verify:** `python3 scripts/check_doc_rotation.py --strict --quiet` → exit 0 nach jedem der 3 Atomic Commits und nach dieser Rotation.

**7. Runtime-Smoke (NEU in dieser Session, nicht im Plan aber Pflicht-Sanity):**
- `python -c "from instinct import InstinctBridge, InstinctConfig, InstinctValidator, SingleShotInstinctExtractor"` (alle 4 wiring.py:383-Symbole) → **OK** (pre-Fix: ModuleNotFoundError, post-Fix: alle 4 Symbole importieren).
- `python -c "import scripts.wiring as w; fn = w._build_reward_sink; src = open('phase8_scheduler/scripts/wiring.py').readlines(); print(src[382].strip())"` → `from instinct import InstinctBridge, InstinctConfig, InstinctValidator, SingleShotInstinctExtractor` (line 383 verbatim, jetzt resolvable).
- `cd phase8_scheduler && python -m scheduler.run --help` → exit 0, CLI parsed ohne Fehler (pre-Fix: Scheduler crashed at first cycle). Scheduler-Daemon ist jetzt startbar — der Phase-16-E3-Restart wird nicht mehr crashen.

**8. Phase-15-Test-Smoke (NEU, post-Install):** ohne den `sys.path.insert`-Hack (den die Phase-15-Tests selbst noch haben, redundant seit editable-install):
- `python -c "from instinct.models import Instinct, InstinctConfig; from instinct.extractor import SingleShotInstinctExtractor; from instinct.validator import InstinctValidator; from instinct.promotion import promote_eligible; from instinct.bridge import InstinctBridge; from instinct.compile import TRIGGER_RE, compile_rule, compile_rules, instinct_from_row"` → **alle 6 Module importable ohne sys.path-Hack**, `instinct.__file__ = /home/trading-bot/trading-bot/phase15_v4/instinct/__init__.py`.
- Tests weiterhin mit Hack (Phase-15-Tests pre-existieren, Hack ist jetzt redundant aber harmlos — kein Phase-15-Test-Touch in dieser Session, Cross-Phase-Freigabe-Konformität).

**9. Git-Stand am Session-Ende (vor Push):**
- HEAD = dieser Final-Commit (Session-Rotation #13→#14).
- Commits lokal ahead of `origin/main = e66be3a` = 8 (`6d26cf1` Session-#13-Block-Update · `6279874` E1-Aktiv-Block · `743e032` Rotation #13 · `a660878` v2-Supersede · `e66be3a` Rotation #12 · **`240eea7` pyproject.toml NEU** · **`a5399e9` setup.cfg NEU** · **`48eb55b` dev_install.sh +1 Zeile**).
- Working tree clean nach jedem Commit.
- 3 eigene Commits dieser Session pending, nicht eigenmächtig gepusht (Nikinger-Push-Freigabe erwartet).

### Findings

🟢 **Phase-15-editable-install Option-B komplett umgesetzt.** 3 Atomic Commits (pyproject.toml + setup.cfg + dev_install.sh) + Nikinger-Aktion `pip install -e ./phase15_v4` (von mir ausgeführt, da Voraussetzung für Σ-Test) ⇒ Scheduler-Daemon startet jetzt ohne `ModuleNotFoundError: No module named 'instinct'`. Phase-15-Tests 126 grün, Σ repo-weit 1921 unverändert (packaging-only).

🟢 **Plan-Literalismus konsequent:** das Next-Item aus Session #13 („Phase-15-editable-install (Option B, neuer Block E Pre-Step, Nikinger-Wahl)") wurde 1:1 abgearbeitet, mit 1 notierten Drift (requires-python '>=3.12' → '>=3.11' für Konsistenz mit 13 anderen Packages) und 1 ausgelassenen Plan-Item (PHASE16_AUTONOMY_PREREGISTRATION.md Header-Card-Liste-Eintrag, weil Locked-Verstoß gegen Prereg-Disziplin §P11/§P17). Beide Drifts sind klein und notiert, keine Phase-16-Blocker.

🟢 **Σ-Sweep nach allen 3 Commits + Install: 1921 grün, AK2 trivial erfüllt.** Phase-15 126 (alle 6 Test-Files grün), keine Test-Datei angefasst. Hook-Verify exit 0 nach jedem Commit.

🟢 **Runtime-Smoke bestätigt Scheduler-Startbarkeit:** `python -m scheduler.run --help` parst ohne Fehler; alle 4 wiring.py:383-Symbole (InstinctBridge, InstinctConfig, InstinctValidator, SingleShotInstinctExtractor) sind importierbar — der Crash-Trigger ist strukturell behoben.

🟢 **Cross-Phase-Touch-Disziplin eingehalten:** Phase-15 ist per Phase-16-Plan §4 Cross-Phase-Freigabe-Liste explizit freigegeben (war closed, wird für Phase-16-Runtime wieder aktiv). Editable-Install ist KEIN Code-Touch (kein .py angefasst), nur Packaging-Metadaten (`pyproject.toml` + `setup.cfg` + `scripts/dev_install.sh`). Phase-8 `wiring.py:383` bleibt unverändert (kein Phase-8-Edit nötig).

🟡 **Drift 1 — `requires-python='>=3.12'` (Plan-Literal) vs. `>=3.11` (gewählt):** alle 13 anderen Packages nutzen `>=3.11` als Konsens. Die `.venv` ist 3.12, also funktional egal. Falls Nikinger strikt `>=3.12` will, ist das ein 1-Zeilen-Edit in `phase15_v4/pyproject.toml` (Folge-Mini-Session, trivial). Im Phase-15-Phasenkopf-Header ist die `python_requires='>=3.12'`-Plan-Aussage als Drift notiert.

🟡 **Drift 2 — Plan-Item „phase15_v4 zur Header-Card-Liste der PHASE16_AUTONOMY_PREREGISTRATION.md ergänzen" nicht ausgeführt:** das Prereg-Dokument ist per §P11 (Prereg-Disziplin, M1-Vorbild) **locked-nach-Commit** und wurde mit `6279874` (E1-Aktiv-Block-Eintragung, 2026-09-07) committet. Editing wäre Locked-Verstoß. Die PHASE16_AUTONOMY_PREREGISTRATION.md hat in der aktuellen Form auch **keine** „Header-Card-Liste" (nur Header-Card + Cross-Refs am Ende) ⇒ der Plan-Verweis ist ein Drift im Plan selbst, nicht im Repo-Stand. Cross-Phase-P15-Status wird stattdessen hier im Phase-16-Phasenkopf dokumentiert (Session-#14-Block).

🟡 **Plan-Item „Header-Kommentar in scripts/dev_install.sh erweitern" wurde umgesetzt (Package-Schleife + finale echo-Zeile), aber Usage-Block (Z. 33-43) bleibt unverändert:** Usage-Beispiel-Block listet weiterhin nur Phase-5..Phase-13 als Beispiel-Tests, Phase-14 wird nicht explizit genannt, Phase-15 auch nicht. Begründung: das Pattern ist „green ⇒ Step C proven" und gilt für alle Phasen gleichermaßen; eine explizite Phase-15-Zeile wäre redundant. Header-Kommentar (oben) ist umfassend aktualisiert mit P15-Brücke + Verweis auf Crash-Ursache.

🔵 **Beobachtung — `InstinctConfig.enable_instinct_promotion` default = `True`** (post Phase-16 D1-Flip, `phase15_v4/instinct/models.py:173`): Verifiziert: `python -c "from instinct import InstinctConfig; c=InstinctConfig(); print(c.enable_instinct_promotion)"` → `True`. Phase-15-Closeout-Doku (2026-09-05) hatte Default `False` (P10-Stand); Phase-16 D1 hat auf `True` geflippt (Plan §1 P5, „alle 4 Arme Default ON"). Diese Flip ist Teil von Phase-16 D1 (Session #7) und **nicht** Teil dieser Session — wird hier nur als Self-Check bestätigt.

🔵 **Beobachtung — `pip show phase15_v4` listet `Author: ` und `Home-page: ` leer:** Standard für pyproject.toml-only ohne `authors`-Feld. Kein Blocker; falls Nikinger das später haben will, `authors = [{name = "..."}]` in `[project]` ergänzen (Folge-Mini-Session, trivial).

### Open questions / blockers

- **Live-Stand (post Session-#14, vor nächstem Restart):** Scheduler **DEAD** (kein PID, Traceback als letzte Log-Zeile), Recorder **ALIVE** (PID 264807, ~95 B neuen Log seit 22:01), Discovery **ALIVE** (PID 264818, ~107 B), WebUI **ALIVE** (PID 264868, ~280 B). Die 3 Services laufen weiter ohne Scheduler-Nutzen, produzieren aber Log-Einträge. **Empfehlung nächste Session (= Nikinger-Aktion):** `bash scripts/restart-services.sh stop` (alle 4 sauber stoppen) → `truncate -s 0 data/state/run_recorder.log data/state/run_discovery.log data/state/run_webui.log data/state/scheduler.log data/state/webui.log data/state/recorder.log data/state/discovery.log` (Runbook v2 §2.4 erweiterter Truncate) → `bash scripts/restart-services.sh start` (alle 4 frisch starten, jetzt mit Phase-15 im Runtime-Pfad) → `sleep 30` + K7-Caps-Pin-Verify (Runbook v2 §3 verbatim).
- **Pflicht-Operator-SQL ✅ DONE** (Session #13, Commit `6279874`): 3 SUN-Epics (SUNDAX.IGN, SUNDOW, SUNNAS) → quarantined, Audit-Trail im Prereg-Aktiv-Block. AK9 pre-test-clean.
- **E3-Restart-Tag:** jetzt **nicht mehr blockiert** durch Phase-15-Fix (diese Session behoben). Nach Restart: Plan §11 Operator-Aktion #5 + Runbook v2 §3. Empfehlung: Dienstag-Mittwoch (Donnerstag/Freitag wegen Wochenend-Lücke vermeiden).
- **E4 (Tagesroutine + Closeout)**: wird nach E3 in der Folgesession gestartet; benötigt die ersten `autonomy_report.py --day`-Outputs (v2 §5). Closeout-Handover nach Tag 10 → `phase16_activation/PHASE16_CLOSEOUT_HANDOVER.md` + `docs/architecture/phase16_activation.svg` 1080×1080 + Status-Pflege root-CLAUDE/ROADMAP/README/INDEX + Session-Rotation.
- **Live-DB Schema v7 → v9 Akten-Vermerk** (B2, Sessions #3) — heute nicht Phase-16-Edit, weiter offen.
- **Push-Freigabe-Stand:** Nikinger hat zwischen #13 und jetzt 0 Commits gepusht (letzter Push war `e66be3a` = Stand Session #12-Push via Session #11). Diese Session **3 Commits pending** (`240eea7` pyproject.toml + `a5399e9` setup.cfg + `48eb55b` dev_install.sh) + dieser Final-Rotation-Commit. Plus 5 Commits pending aus Session #13. **Branch lokal 8 ahead of origin/main = e66be3a. Nikinger-Push-Freigabe erwartet** (oder Sammel-Push mehrerer Sessions in einer Nikinger-Aktion).

### Next (für die Folgesession)

- **Services stoppen + Logs truncaten + restart (Nikinger-Aktion, dringend):** `bash scripts/restart-services.sh stop` (alle 4 sauber stoppen, inkl. der 3 noch laufenden Recorder/Discovery/WebUI) → `truncate -s 0 data/state/run_recorder.log data/state/run_discovery.log data/state/run_webui.log data/state/scheduler.log data/state/webui.log data/state/recorder.log data/state/discovery.log` (Runbook v2 §2.4 erweiterter Truncate) → `bash scripts/restart-services.sh start` (alle 4 frisch starten, Scheduler hat jetzt Phase-15 im Runtime-Pfad, crasht NICHT mehr) → `sleep 30` + K7-Caps-Pin-Verify (`account=demo, max_trades=5, daily_loss_cap=1800.0, cycle=5min` per Runbook v2 §3 verbatim).
- **E3 — Runbook-Start nach Phase-15-Fix (Nikinger-Aktion, Runbook v2 §0 Reihenfolge):** Schritt 1 = Pflicht-Operator-SQL ✅ DONE (Audit-Trail im Prereg-Aktiv-Block, Commit `6279874`) → Schritt 2 = v2 §2 Pre-Flight (6 Schritte, ≤ 5 min, inkl. v2 §2.4 erweiterter Truncate) → Schritt 3 = v2 §2.6 Prereg-Aktiv-Block ✅ DONE (Commit `6279874`) → Schritt 4 = v2 §3 Restart-Sequenz (`restart-services.sh start` + K7-Caps-Pin-Verify) → Schritt 5 = v2 §4 Day-0-Checks Timeline (5min/30min/4h/24h, alle SQL-Queries mit korrigierten Spalten) → Schritt 6 = v2 §5 Tagesroutine (täglich `--day`) → Schritt 7 = v2 §8 Tag-10-Closeout (`--summary` + Exec-Session).
- **E4 — Tagesroutine + Closeout**: ab Tag 1 täglich `autonomy_report.py --day` (v2 §5). Nach Tag 10: `--summary` (v2 §8), wenn `overall_verdict == "PASS"` Closeout-Handover + SVG + Status-Pflege.
- **PHASE16_CLOSEOUT_HANDOVER.md + docs/architecture/phase16_activation.svg** nach Tag 10 (Phase-16-Abschluss, Runbook v2 §8).
- **Runbook-v3 (optional, post-E3-Start):** wenn Drift #7 (Keyring-Check-Snippet mit falschen `cst`/`demo_token`-Namen statt `IG_DEMO_*`) oder andere Pre-Flight-Drifts auftauchen, v3 schreiben mit Korrekturen. Nicht-blockierend für aktuellen E3-Restart, weil `import instinct` das eigentliche Problem war (das ist **jetzt behoben**).
- **Phase-15-Test-Sys.path-Hack-Hygiene (optional, Folge-Mini-Session):** alle 6 Phase-15-Test-Files haben weiterhin den `sys.path.insert(0, _REPO_ROOT)`-Hack (pre-edit-Stand). Nach editable-install ist der Hack redundant. Entfernen wäre ein Phase-15-Code-Touch (Cross-Phase-Freigabe nötig, oder Folge-Session). Empfehlung: belassen, weil harmlos und Konsistenz mit historischem Stand.

### Watch-Item / Plan-Hygiene (für spätere Sessions)

- **Pflicht-Operator-SQL §1 v2**: ✅ DONE (Session #13, Commit `6279874`). 3 SUN-Epics pre-E3 demotiert, einmaliger Operator-Akt. Audit-Trail im Prereg-Aktiv-Block.
- **Staffelung via `marginDepositBands`** (Plan §13 #8): unverändert Phase-17-Material. Runbook v2 §6 T-9 → Exec-Session-Pfad.
- **Hybrid-Test-Ansatz** (Session #11 Findings): unverändert Phase-17-Material wenn CI-Run gewünscht.
- **Runbook-Supersede-Disziplin** (P11): wenn nach E3 etwas am Runbook fehlt, kein Edit am bestehenden Runbook — neues, datiertes, supersedendes Doc (`PHASE16_E3_RUNBOOK_v3.md`) mit Begründung. v1+v2 bleiben beide als historische Stände im Repo.
- **Phase-17-Kandidaten** (aus dem Runbook herausgelesen): Prozess-Supervision (systemd-User-Unit + Auto-Restart nach Reboot + Keyring ohne Login); Strategie-Bewertung (Watch-Items W1 BUY-Bias, W2 DAX-Only → Win-Rate / Sharpe / P&L); CLI-Bridge-Test-Hardening.
- **Phase-9-Discovery-Filter** (`is_weekend_market`) ist die strukturelle Lösung für die 3-Epics-Lücke — die manuelle Demotion ist eine einmalige Operator-Aktion, danach verhindert der Code Re-Promotion automatisch.
- **Phase-15-`requires-python` Align-Option (Folge-Mini-Session, ~1 Min):** falls Nikinger strikt `>=3.12` statt `>=3.11` will, 1-Zeilen-Edit in `phase15_v4/pyproject.toml` und Re-Install. Begründung aktueller Stand: 13-Package-Konsens.

**Block-Status nach dieser Session (endgültig):**

| Block | Status |
|---|---|
| A (Haushalt) | ✅ A-0..A-4 + A-5 Push (Sessions #1-#3) |
| B (Substrat) | ✅ B1+B3 code + B2 Operator-Apply + A-5 Push (Session #3) |
| C (Research-Loop) | ✅ C1+C2+C3+C5 endgültig in code; C4 = Doku-Only (Sessions #4-#5) |
| D (Freischaltung) | ✅ D1+D1.2+D2+D3.0+D3.1+D3.2 komplett (Sessions #7-#10) |
| E (Autonomie-Test, Vorregistrierung) | ✅ E1 endgültig in docs (Session #6) |
| E (Autonomie-Test, E2) | ✅ E2 endgültig in code (Session #11) |
| E (Autonomie-Test, E3 Runbook) | ✅ **E3 Runbook v2 endgültig in docs** (Session #13, supersedet v1) |
| **E (Autonomie-Test, Pre-Step Phase-15-install)** | ✅ **endgültig in packaging** (Session #14: pyproject.toml + setup.cfg + dev_install.sh) |
| E (Autonomie-Test, E3 Runbook-Start) | 🔴 offen [Nikinger-Aktion: stop+truncate+restart nach dieser Session] |
| E (Autonomie-Test, E4) | 🔴 offen [nach E3-Restart-Start] |

**Push-Status dieser Session:** **3 Commits pending** (`240eea7` pyproject.toml + `a5399e9` setup.cfg + `48eb55b` dev_install.sh), 0 Commits gepusht. Plus dieser Final-Rotation-Commit. Plus 5 Commits pending aus Session #13 (`6d26cf1` Session-#13-Block-Update · `6279874` E1-Aktiv-Block · `743e032` Rotation #13 · `a660878` v2-Supersede · `e66be3a` Rotation #12). **Branch lokal 8 ahead of origin/main = e66be3a. Nikinger-Push-Freigabe erwartet** (Sammel-Push über mehrere Sessions in einer Nikinger-Aktion empfohlen).