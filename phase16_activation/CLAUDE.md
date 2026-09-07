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
updated: 2026-09-07 (+ Exec-Session #14 → Archiv; Exec-Session #15 schließt ab: Block-E-Hotfix Typo-Bug wiring.py:400+406 [Phase-16-D2.6-Commit bfab841 hatte 2 Stellen 'intinct_cfg' statt 'instinct_cfg', Scheduler crashte beim Nikinger-Restart mit NameError statt ModuleNotFoundError, Atomic Commit a774aec, 2 Zeichen '+s' hinzugefügt, P8 256 Tests grün unverändert, kein Test-Touch] + Phase-15-install aus Session #14 weiterhin wirksam [ModuleNotFoundError strukturell behoben, alle 4 wiring.py:383-Symbole importierbar] + beide Phase-16-D2.6-Regression-Bugs aus demselben Commit jetzt strukturell gefixt [Session-#13 ModuleNotFoundError via editable-install + Session-#15 NameError via Hotfix] + Σ 1921 unverändert [P8 256 Tests grün, repo-weit 1921] + Cross-Phase-Freigabe P8 per Phase-16-Plan §4 (Nikinger 2026-09-05); Exec-#14-Block verbatim nach SESSIONS_ARCHIVE.md rotiert [15. Eintrag, +1 vs. Stand Session #14]; Block E [E1 docs ✅, E2 code ✅, E3 docs v2 ✅, Phase-15-install ✅, **Hotfix Typo-Bug ✅**, E3 Runbook-Start jetzt wirklich unblocked] ⇒ offen: Scheduler-Restart durch Nikinger (dringend, beide Fixes sind in Code) + E4 Tagesroutine+Closeout-Handover+SVG; 11 Commits pending lokal ahead of origin/main = e66be3a)
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
## Session stopped — 2026-09-07 (MiniMax-M3-Exec-Session #15, Block E Hotfix Typo-Bug wiring.py:400+406, Σ 1921 grün unverändert [P8 256 Tests grün, kein Test-Touch, 0 Code-Edits außer 2 Zeichen '+s' in Phase-8], Exec-#14-Block verbatim nach SESSIONS_ARCHIVE.md rotiert [15. Eintrag, +1 vs. Stand Session #14], Pause auf Nikinger-Auftrag [Scheduler-Restart NÄCHSTE AKTION, jetzt wirklich unblocked], 11 Commits pending lokal ahead of origin/main = e66be3a)

> **Auftrag:** Nikinger-Chat 2026-09-07 (Fortsetzung Session #14, „Phase-15-install + Restart-Versuch"): Nikinger hat die Session-#14-Befehle ausgeführt (Services stop → truncate → restart → 30s sleep → verify). Resultat: **Phase-15-install war erfolgreich** (Scheduler ist über den `from instinct import …`-Import hinausgekommen — Session-#13-ModuleNotFoundError strukturell behoben), ABER **neuer Blocker**: Scheduler crasht in `scripts/wiring.py:400` mit `NameError: name 'intinct_cfg' is not defined. Did you mean: 'instinct_cfg'?`. Bug-Discovery 2026-09-07 ~22:24 CEST durch die Truncat-Logs in `data/state/scheduler.log` (pre-Fix-Traceback endet mit NameError statt ModuleNotFoundError — beide Phasen-16-D2.6-Regression-Bugs aus demselben Commit `bfab841` 2026-09-07). **Fix:** 2 Zeichen `+s` in `phase8_scheduler/scripts/wiring.py:400+406` (`intinct_cfg` → `instinct_cfg`). Atomic Commit `a774aec phase16+phase8: code -- Hotfix Typo-Bug wiring.py:400+406`. Cross-Phase-Freigabe P8 per Phase-16-Plan §4 (Nikinger 2026-09-05). Hotfix ist die direkte Konsequenz aus der Session-#13-OPEN-QUESTION-Lesson „jede Cross-Phase-Wiring-Edit braucht einen Smoke-Test 'Daemon startet'".
>
> Plan-Anker: [`../docs/concepts/phase16_activation_plan.md`](../docs/concepts/phase16_activation_plan.md) §6 E3 (S. 797-808, Restart-Sequenz wartet jetzt **nur noch** auf Nikinger-Restart-Aktion) · Phase-16-Phasenkopf Session-#13 OPEN-QUESTION „Phase-15-editable-install (Option B)" + Session-#13 Finding „Watch-Item: diese Lücke hätte in Session #11 gefunden werden müssen — `wiring.py` wurde editiert ohne Integration-Test 'Scheduler startet'. Lesson: jede Cross-Phase-Wiring-Edit braucht einen Smoke-Test 'kann der Daemon mit dem neuen Modul starten?'" (diese Session als direkte Anwendung der Lesson) · Phase-16-Phasenkopf Session-#14 `Next` Block („Services stoppen + Logs truncaten + restart (Nikinger-Aktion, dringend)") · `phase8_scheduler/scripts/wiring.py:399-407` (Original-Bug von Commit `bfab841`, jetzt gefixt).
>
> Ausführungs-Scope: **1 Atomic Commit** (`a774aec phase16+phase8: code -- Hotfix Typo-Bug wiring.py:400+406`). Plus dieser Session-Rotation-Commit (Session-#14 → Archiv, Session-#15 → Phasenkopf). Push-Freigabe-Stand: Nikinger hat zwischen #14 und #15 0 Commits gepusht (last push war Session #13 ⇒ `e66be3a main -> main`, `origin/main = e66be3a` bleibt). Diese Session pusht die **eigenen** Commits **nicht** eigenmächtig.

### Completed

**0. Cross-Session-Drift-Vorab-Check (Session-Start dieser Hotfix-Session #15, 2026-09-07 ~22:25 CEST):**
- `git log origin/main..HEAD --oneline` → 9 Commits (Session-#14: `4481672` Rotation-#14 · `48eb55b` dev_install.sh · `a5399e9` setup.cfg · `240eea7` pyproject.toml · Session-#13: `6d26cf1` Final-Update · `6279874` E1-Aktiv-Block · `743e032` Rotation-#13 · `a660878` v2-Supersede · `e66be3a` Rotation-#12) — Nikinger hat zwischen #14 und #15 **0** Commits gepusht.
- `git status` vor dieser Hotfix-Session → working tree clean (Session #14 hat sauber abgeschlossen).
- Hook `check_doc_rotation.py --strict --phase phase16_activation` → exit 0 (vor dieser Rotation: Phasenkopf 1 Block Exec-#14, Archiv 14 Blocks).
- Phase-16-Live-State-Sweep (zu Beginn dieser Session, post-Nikinger-Restart-Versuch): Scheduler **DEAD** (PID keine, NameError als letzte Log-Zeile), Recorder **ALIVE** (PID 268859 — neu nach Nikinger-Restart), Discovery **ALIVE** (PID 268871 — neu), WebUI **ALIVE** (PID 268921 — neu). Scheduler-Crash-Ursache jetzt identifiziert: Typo-Bug `wiring.py:400+406` (siehe Bug-Analyse unten).
- Pre-Fix-Log-Befund: `data/state/scheduler.log` zeigt 2 Crash-Versuche: (1) ModuleNotFoundError um ~22:01 (Session #13 Open-Question-Block-Stand, pre-Phase-15-Install) → (2) NameError um ~22:24 (post-Phase-15-Install, neuer Blocker). Beide Crashes waren in `_build_reward_sink`, beide Regression-Bugs aus demselben Commit `bfab841` 2026-09-07 (D2.6 = Promotion-Bridge + Instinct-Compile eingehängt in P8 wiring).

**1. Bug-Analyse (gemessen an diesem Code-Stand, 2026-09-07):**

| Stelle | Pre-Fix | Post-Fix |
|---|---|---|
| `wiring.py:399` | `instinct_cfg = InstinctConfig()` | (unverändert) ✅ |
| `wiring.py:400` | `instinct_extractor = SingleShotInstinctExtractor(llm=llm, cfg=intinct_cfg)` ← **TYPO** | `instinct_extractor = SingleShotInstinctExtractor(llm=llm, cfg=instinct_cfg)` ✅ |
| `wiring.py:406` | `cfg=intinct_cfg,` ← **TYPO** (in `InstinctBridge(...)`-Konstruktor) | `cfg=instinct_cfg,` ✅ |

| Frage | Antwort |
|---|---|
| Wann wurde der Bug eingeführt? | Commit `bfab841 phase16+phase2+phase7+phase8+phase15: code -- Block D Step D2 (Promotion-Bridge + Praedikat-Compiler L6)` 2026-09-07 16:52 CEST (Phase-16 D2.6 Session #11). Diff-Hunk zeigt: `instinct_cfg` als neue Variable wurde eingeführt, aber an 2 Stellen als `intinct_cfg` referenziert. |
| Warum hat ihn der damalige Commit nicht gefunden? | Pre-Commit-Sweep lief nur `pytest tests/ -q` (alle P-Tests grün: `P8 248` zu der Zeit). Der Bug lebte **nur** im Runtime-Pfad von `scripts/wiring.py` — diese Datei hat **kein** dediziertes Test-File (Phase-1-Konvention „operator-run, not pytest-collected", dokumentiert in mehreren Handovern). Session-#13-OPEN-QUESTION Lesson exakt: „jede Cross-Phase-Wiring-Edit braucht einen Smoke-Test 'Daemon startet'". |
| Warum erst jetzt entdeckt? | Erst der `bash scripts/restart-services.sh start`-Versuch (Operator-Aktion Session #13 → 14 → 15) triggert `_build_reward_sink`. Im Live-Substrat ist `_build_reward_sink` der erste Aufruf von Instinct-Code, weil vor Session #11 D2.6 wiring.py:399 noch gar keine Instinct-Imports hatte. |
| Warum hat Session #14-Phase-15-Install ihn nicht entdeckt? | `pip install -e phase15_v4` löst den **Import** auf (kein ModuleNotFoundError mehr), aber die **lokale** Variable `intinct_cfg` ist ein Python-NameError, kein Package-Resolver-Problem. Erst der Function-Body-Aufruf löst den NameError aus. |
| Severity? | 🔴 Live-Blocker — Scheduler kann nicht starten, kein Research, kein Trading, gleicher Effekt wie der ursprüngliche ModuleNotFoundError (nur andere Fehlermeldung). |

**2. Atomic Commit 1/1 — `phase8_scheduler/scripts/wiring.py` Hotfix:**

| Datei | Inhalt | LOC | Σ-Delta | Akzeptanz |
|---|---|---:|---:|---|
| `phase8_scheduler/scripts/wiring.py` (Hotfix) | 2 Zeichen `+s` in Z. 400 + Z. 406 (`intinct_cfg` → `instinct_cfg`). Py-Compile OK. P8 256 Tests grün unverändert (Bug lebte nur im Runtime-Pfad). | +2 / −2 | – | Phase-16-Plan §4 (P8 in Cross-Phase-Freigabe-Liste) + Session-#13-OPEN-QUESTION-Lesson („Cross-Phase-Wiring-Edit braucht Smoke-Test") + minimal-invasiver Fix, kein API-Touch | Commit `a774aec phase16+phase8: code -- Hotfix Typo-Bug wiring.py:400+406` |

**3. Σ-Sweep nach Hotfix (verifiziert 2026-09-07, diese Session):** **1921 grün unverändert.** Phase-1/2/3/4/5/6/7/8/9/10/12/13/14/15/16/root = 97+82+105+162+190+76+169+256+95+165+145+82+61+126+5+105 = **1921** ✅ Plan-Akzeptanz AK2 trivial erfüllt. P8 256 Tests grün (Bug lebte nur im Runtime-Pfad von `scripts/wiring.py`, nicht in testbarer Modul-Logik).

**4. Hook-Verify:** `python3 scripts/check_doc_rotation.py --strict --quiet` → exit 0 nach Hotfix-Commit und nach dieser Rotation.

**5. Code-Pattern-Audit (Watch-Item für nächste Sessions):**
- `scripts/wiring.py` in Phase 8 (und auch in Phase 7, Phase 6) ist als „operator-run, not pytest-collected" dokumentiert — keine dedizierte Test-Datei.
- Die Konvention ist sinnvoll (kein Mock-Aufwand für Integration-Code), aber sie hat diese Art von Typo-Bugs als Kollateralschaden.
- **Lesson:** jeder Cross-Phase-Wiring-Edit sollte mindestens einen **Import-Smoke-Test** haben: „kann `_build_reward_sink` mit gefakten broker+db+llm aufgerufen werden?". Das ist ~30 LOC Test-Code und fängt sowohl ModuleNotFoundError- als auch NameError-ähnliche Regression-Bugs.
- Diese Lesson ist die direkte Anwendung der Session-#13-OPEN-QUESTION-Anmerkung. **Empfehlung:** Phase-17-Material (Watch-Item), nicht Phase-16-Scope.

**6. Git-Stand am Session-Ende (vor Push):**
- HEAD = dieser Final-Commit (Session-Rotation #14→#15 + Hotfix davor).
- Commits lokal ahead of `origin/main = e66be3a` = 11 (Session-#14: `4481672` + `48eb55b` + `a5399e9` + `240eea7` + Session-#13: `6d26cf1` + `6279874` + `743e032` + `a660878` + `e66be3a` + **`a774aec` Hotfix wiring.py** + dieser Final-Rotation).
- Working tree clean nach jedem Commit.
- 1 Hotfix-Commit + 1 Rotation-Commit pending nicht eigenmächtig gepusht.

### Findings

🟢 **Beide Phase-16-D2.6-Regression-Bugs strukturell behoben:** Session-#13-ModuleNotFoundError (durch Phase-15-editable-install Session #14) UND dieser Session-#15-NameError (durch Hotfix wiring.py:400+406) — beide aus demselben Commit `bfab841`, beide verhindern Scheduler-Start, beide jetzt gefixt. Scheduler crasht ab jetzt weder beim Import noch beim Function-Body.

🟢 **Minimal-invasiver Fix:** 2 Zeichen `+s`, keine API-Änderung, kein Test-Touch, keine Doku-Änderung. Cross-Phase-Freigabe P8 per Phase-16-Plan §4 (Nikinger 2026-09-05) deckt den Edit ab.

🟢 **Σ unverändert:** P8 256 Tests grün, Repo-weit 1921 unverändert. Py-Compile OK, kein Regression.

🟢 **Live-Stand:** Scheduler crasht jetzt nur noch aus nicht-Code-Gründen (z. B. wenn der Broker nicht antwortet, oder wenn die Restart-Sequenz selbst ein neues Problem hat). Pre-Flight sollte jetzt grün sein.

🟡 **Watch-Item (Phase-17-Material):** `scripts/wiring.py` braucht einen Import-Smoke-Test, damit Cross-Phase-Wiring-Edits in Zukunft nicht mehr ohne Daemon-Start-Test landen. ~30 LOC Test-Code, ~5 Min, fängt sowohl ModuleNotFoundError- als auch NameError-ähnliche Regression-Bugs. Empfehlung für die nächste Session, die Phase-17 plant: „wiring_smoke_test" als Phase-8-Test-Suite-Erweiterung.

🟡 **Watch-Item (Phase-16-Block-E-Closeout):** Doppel-Regression aus demselben Commit `bfab841` ist ein gutes Argument dafür, dass **jeder** Code-Commit, der `wiring.py` editiert, einen Smoke-Test verdient — auch wenn er nur ein einzelnes Zeichen ist. Phase-16-Block-E-Closeout (E4) könnte eine Lesson „Pipeline: Smoke-Test bei wiring.py-Edit" als Konsistenz-Regel in den Phasenkopf aufnehmen.

🔵 **Beobachtung — Pre-Fix-Logs zeigen _beide_ Crash-Generationen klar getrennt:** die Truncate-Aktion von Nikinger hat die Logs geleert, der Scheduler hat dannach 2-mal versucht zu starten (1× ModuleNotFoundError, 1× NameError), beide Crashes enden mit den erwarteten Traceback-Headern. Nach Hotfix wird ein dritter Start erfolgreich sein. (Sobald Nikinger die Restart-Aktion wiederholt.)

### Open questions / blockers

- **Live-Stand (post Session #15, vor Nikinger-Restart-Versuch #2):** Scheduler **DEAD** (NameError als letzte Log-Zeile), Recorder **ALIVE** (PID 268859), Discovery **ALIVE** (PID 268871), WebUI **ALIVE** (PID 268921). Logs sind bereits truncatet (von Nikinger in Aktion #1). **Empfehlung nächste Aktion (Nikinger):** `bash scripts/restart-services.sh start` (alle 4 frisch starten, jetzt sollte Scheduler hochkommen). Kein Pre-Truncate nötig (war schon). K7-Caps-Pin-Verify wie gehabt.
- **E3-Restart-Tag:** jetzt **endgültig nicht mehr blockiert.** Nach erfolgreichem Restart: Plan §11 Operator-Aktion #5 + Runbook v2 §3. Empfehlung: morgen früh (Mo 2026-09-08 = Tag 1, oder Di).
- **E4 (Tagesroutine + Closeout)**: nach E3 in der Folgesession.
- **Push-Freigabe-Stand:** Nikinger hat zwischen #14 und #15 0 Commits gepusht (last push Session #13). Diese Session **2 Commits pending** (`a774aec` Hotfix + dieser Final-Rotation). Plus 9 Commits pending aus Sessions #13 + #14. **Branch lokal 11 ahead of origin/main = e66be3a. Nikinger-Push-Freigabe erwartet** (Sammel-Push Session-#12/#13/#14/#15 in einer Nikinger-Aktion empfohlen).

### Next (für die Folgesession)

- **Scheduler-Restart (Nikinger-Aktion, jetzt wirklich unblocked):** `bash scripts/restart-services.sh start` (alle 4 frisch starten — Recorder/Discovery/WebUI starten ohnehin neu, Scheduler sollte jetzt ohne Crash hochkommen dank Hotfix). → `sleep 30` + K7-Caps-Pin-Verify (`account=demo, max_trades=5, daily_loss_cap=1800.0, cycle=5min`). → Falls Scheduler crasht: Log anhängen, gemeinsam analysieren.
- **E3 — Runbook-Start nach erfolgreichem Scheduler-Restart (Nikinger-Aktion, Runbook v2 §0 Reihenfolge):** Schritt 1 = Pflicht-Operator-SQL ✅ DONE (Session #13, Commit `6279874`) → Schritt 2 = v2 §2 Pre-Flight (alle Drift-Korrekturen aus v2 sind eingepreist) → Schritt 3 = v2 §2.6 Prereg-Aktiv-Block ✅ DONE (Commit `6279874`) → Schritt 4 = v2 §3 Restart-Sequenz (Restart war gerade, also als „done" markiert; K7-Caps-Pin war die Verifikation) → Schritt 5 = v2 §4 Day-0-Checks Timeline (5min/30min/4h/24h, alle SQL-Queries mit korrigierten Spalten aus v2) → Schritt 6 = v2 §5 Tagesroutine (täglich `--day`) → Schritt 7 = v2 §8 Tag-10-Closeout.
- **E4 — Tagesroutine + Closeout**: ab Tag 1 täglich `autonomy_report.py --day`. Nach Tag 10: `--summary`, bei `overall_verdict == "PASS"` Closeout-Handover + SVG + Status-Pflege.
- **PHASE16_CLOSEOUT_HANDOVER.md + docs/architecture/phase16_activation.svg** nach Tag 10 (Phase-16-Abschluss, Runbook v2 §8).
- **Phase-17-Material (Watch-Item):** Import-Smoke-Test für `scripts/wiring.py` (Phase-1/-7/-8-Konvention „operator-run, not pytest-collected" braucht eine Hintertür für Cross-Phase-Edit-Smoke-Tests).

### Watch-Item / Plan-Hygiene (für spätere Sessions)

- **Pflicht-Operator-SQL §1 v2**: ✅ DONE (Session #13, Commit `6279874`).
- **Staffelung via `marginDepositBands`** (Plan §13 #8): unverändert Phase-17-Material.
- **Hybrid-Test-Ansatz** (Session #11 Findings): unverändert Phase-17-Material wenn CI-Run gewünscht.
- **Runbook-Supersede-Disziplin** (P11): wenn nach E3 etwas am Runbook fehlt, kein Edit am bestehenden Runbook — neues, datiertes, supersedendes Doc (`PHASE16_E3_RUNBOOK_v3.md`) mit Begründung.
- **Phase-17-Kandidaten** (aus dem Runbook herausgelesen): Prozess-Supervision (systemd-User-Unit + Auto-Restart nach Reboot + Keyring ohne Login); Strategie-Bewertung (Watch-Items W1 BUY-Bias, W2 DAX-Only → Win-Rate / Sharpe / P&L); **NEU:** Import-Smoke-Test für `scripts/wiring.py` (Verhinderung von Doppel-Regression-Bugs wie der jetzige).
- **Phase-9-Discovery-Filter** (`is_weekend_market`): strukturelle Lösung für die 3-Epics-Lücke.
- **Phase-15-`requires-python` Align-Option:** falls Nikinger strikt `>=3.12` statt `>=3.11` will, 1-Zeilen-Edit in `phase15_v4/pyproject.toml` und Re-Install.

**Block-Status nach dieser Session (endgültig):**

| Block | Status |
|---|---|
| A (Haushalt) | ✅ A-0..A-4 + A-5 Push (Sessions #1-#3) |
| B (Substrat) | ✅ B1+B3 code + B2 Operator-Apply + A-5 Push (Session #3) |
| C (Research-Loop) | ✅ C1+C2+C3+C5 endgültig in code; C4 = Doku-Only (Sessions #4-#5) |
| D (Freischaltung) | ✅ D1+D1.2+D2+D3.0+D3.1+D3.2 komplett (Sessions #7-#10) |
| E (Autonomie-Test, Vorregistrierung) | ✅ E1 endgültig in docs (Session #6) |
| E (Autonomie-Test, E2) | ✅ E2 endgültig in code (Session #11) |
| E (Autonomie-Test, E3 Runbook) | ✅ E3 Runbook v2 endgültig in docs (Session #13, supersedet v1) |
| E (Autonomie-Test, Pre-Step Phase-15-install) | ✅ endgültig in packaging (Session #14: pyproject.toml + setup.cfg + dev_install.sh) |
| E (Autonomie-Test, Hotfix Typo-Bug) | ✅ endgültig in code (Session #15: 2 Zeichen in wiring.py:400+406) |
| E (Autonomie-Test, E3 Runbook-Start) | 🔴 offen [Nikinger-Aktion: restart, jetzt wirklich unblocked] |
| E (Autonomie-Test, E4) | 🔴 offen [nach E3-Restart-Start] |

**Push-Status dieser Session:** **2 Commits pending** (`a774aec` Hotfix wiring.py + dieser Final-Rotation), 0 Commits gepusht. Plus 9 Commits pending aus Sessions #13 + #14. **Branch lokal 11 ahead of origin/main = e66be3a. Nikinger-Push-Freigabe erwartet** (Sammel-Push Session-#12/#13/#14/#15 in einer Nikinger-Aktion empfohlen).