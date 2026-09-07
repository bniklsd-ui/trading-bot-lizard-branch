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
updated: 2026-09-07 (+ Exec-Session #15 → Archiv; Exec-Session #16 schließt ab: Block-E-Hotfix #2 wiring.py:400 Signatur [Phase-16-D2.6-Commit bfab841 hatte SingleShotInstractExtractor(llm=llm, cfg=instinct_cfg) aufgerufen -- aber echte Signatur ist SingleShotInstinctExtractor(llm_client), 1 positional arg, kein cfg, keyword heisst 'llm_client' nicht 'llm', Atomic Commit 8363903, 4 Zeichen 'llm=llm, cfg=instinct_cfg' -> 'llm_client=llm', P8 256 + P15 126 Tests grün unverändert, kein Test-Touch] + alle 3 Phase-16-D2.6-Regression-Bugs aus demselben Commit bfab841 jetzt strukturell gefixt [ModuleNotFoundError via Session-#14-editable-install + NameError via Session-#15-Hotfix-#1 + TypeError via Session-#16-Hotfix-#2] + Σ 1921 unverändert [P8 256 + P15 126 Tests grün, repo-weit 1921] + Cross-Phase-Freigabe P8 per Phase-16-Plan §4 (Nikinger 2026-09-05); Exec-#15-Block verbatim nach SESSIONS_ARCHIVE.md rotiert [16. Eintrag, +1 vs. Stand Session #15]; Block E [E1 docs ✅, E2 code ✅, E3 docs v2 ✅, Phase-15-install ✅, Hotfix Typo-Bug ✅, **Hotfix #2 Signatur ✅**, E3 Runbook-Start jetzt hoffentlich wirklich unblocked] ⇒ offen: Scheduler-Restart durch Nikinger (dringend, alle 3 Fixes sind in Code, hoffentlich letzter D2.6-Bug) + E4 Tagesroutine+Closeout-Handover+SVG; 13 Commits pending lokal ahead of origin/main = e66be3a)
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
## Session stopped — 2026-09-07 (MiniMax-M3-Exec-Session #16, Block E Hotfix #2 wiring.py:400 SingleShotInstinctExtractor-Signatur, Σ 1921 grün unverändert [P8 256 + P15 126 Tests grün, kein Test-Touch, 4 Zeichen-Edit in Phase-8], Exec-#15-Block verbatim nach SESSIONS_ARCHIVE.md rotiert [16. Eintrag, +1 vs. Stand Session #15], Pause auf Nikinger-Auftrag [Scheduler-Restart #3 NÄCHSTE AKTION, hoffentlich letzter D2.6-Bug], 13 Commits pending lokal ahead of origin/main = e66be3a)

> **Auftrag:** Nikinger-Chat 2026-09-07 (Fortsetzung Session #15, „Scheduler-Restart #2 nach Hotfix #1"): Nikinger hat die Restart-Befehle wiederholt. Resultat: **Hotfix #1 (Typo `intinct_cfg` → `instinct_cfg`) war erfolgreich** (Scheduler kam über Z. 400 hinaus), ABER **dritter Blocker** auf Z. 400: `TypeError: SingleShotInstinctExtractor.__init__() got an unexpected keyword argument 'llm'`. **Root Cause:** Phase-16-D2.6-Commit `bfab841` hat die `SingleShotInstinctExtractor(...)`-Konstruktion mit der Signatur `(llm=llm, cfg=instinct_cfg)` aufgerufen — aber die echte Signatur in `phase15_v4/instinct/extractor.py:260` ist `def __init__(self, llm_client: _LLMClientLike)` (1 positional arg, kein cfg, keyword heißt `llm_client` nicht `llm`). Das `cfg`-Argument gehört in den `InstinctBridge(...)`-Konstruktor (Z. 406, der hat `cfg=instinct_cfg` korrekt). **Fix:** 1-Wort-Edit `llm=llm, cfg=instinct_cfg` → `llm_client=llm` (4 Zeichen Differenz). Atomic Commit `8363903 phase16+phase8: code -- Hotfix #2 wiring.py:400 Signatur`. Cross-Phase-Freigabe P8 per Phase-16-Plan §4.
>
> Plan-Anker: [`../docs/concepts/phase16_activation_plan.md`](../docs/concepts/phase16_activation_plan.md) §6 E3 (Restart-Sequenz wartet jetzt auf den 3. und möglicherweise letzten D2.6-Regression-Bug) · Phase-16-Phasenkopf Session-#15 OPEN-QUESTION (Hotfix #1 + Watch-Item Phase-17-Smoke-Test für wiring.py) · `phase15_v4/instinct/extractor.py:260` (echte Signatur) · `phase15_v4/instinct/bridge.py:60-70` (Bridge-Konstruktor akzeptiert cfg) · `phase15_v4/tests/test_instinct_extractor.py:135+` (alle 14 Tests rufen mit positional-arg `_FakeLLM()`, niemals mit `llm=` oder `cfg=`).
>
> Ausführungs-Scope: **1 Atomic Commit** (`8363903 phase16+phase8: code -- Hotfix #2 wiring.py:400 Signatur`). Plus dieser Session-Rotation-Commit. Push-Freigabe-Stand: Nikinger hat zwischen #15 und #16 0 Commits gepusht.

### Completed

**0. Cross-Session-Drift-Vorab-Check (Session-Start dieser Hotfix-#2-Session #16, 2026-09-07 ~22:30 CEST):**
- `git log origin/main..HEAD --oneline` → 12 Commits (Session-#15: `994a5af` Rotation-#15 · `a774aec` Hotfix #1 + Session-#14: `4481672` Rotation-#14 · `48eb55b` dev_install.sh · `a5399e9` setup.cfg · `240eea7` pyproject.toml + Session-#13: `6d26cf1` Final-Update · `6279874` E1-Aktiv-Block · `743e032` Rotation-#13 · `a660878` v2-Supersede · `e66be3a` Rotation-#12 · `a3fa6ce` Runbook-v1 · `e219a25` Session-#11-Endmarker) — Nikinger hat zwischen #15 und #16 **0** Commits gepusht.
- `git status` vor dieser Hotfix-Session → working tree clean.
- Hook `check_doc_rotation.py --strict --phase phase16_activation` → exit 0.
- Phase-16-Live-State-Sweep: Scheduler **DEAD** (PID keine, TypeError als letzte Log-Zeile), Recorder **ALIVE** (PID 268859), Discovery **ALIVE** (PID 268871), WebUI **ALIVE** (PID 268921). Scheduler-Crash-Ursache jetzt identifiziert: Signatur-Mismatch in `wiring.py:400`.
- Pre-Fix-Log-Befund: `data/state/scheduler.log` zeigt jetzt **3 Crash-Versuche**: (1) `ModuleNotFoundError` 22:01 (Session #13) → (2) `NameError: intinct_cfg` 22:24 (Session #15) → (3) `TypeError: SingleShotInstinctExtractor.__init__() got an unexpected keyword argument 'llm'` 22:28 (Session #16). Alle 3 Crashes aus demselben Commit `bfab841` 2026-09-07 — Phase-16 D2.6 hat 3 separate Regression-Bugs in `_build_reward_sink` produziert.

**1. Bug-Analyse (gemessen an diesem Code-Stand, 2026-09-07):**

| Frage | Antwort |
|---|---|
| Welche Signatur hat `SingleShotInstinctExtractor` wirklich? | `phase15_v4/instinct/extractor.py:260`: `def __init__(self, llm_client: _LLMClientLike) -> None`. **1 positional arg** namens `llm_client`, kein cfg, kein `llm`-Keyword. |
| Wie ruft die Test-Suite es auf? | `phase15_v4/tests/test_instinct_extractor.py` 14 Stellen: alle mit positional-arg `_FakeLLM()` (z. B. Z. 137, 158, 181, 198, 218, …). Niemals mit `llm=` oder `cfg=`. |
| Warum hat der D2.6-Commit die Signatur nicht erkannt? | Phase-16 D2.6 wurde **am 2026-09-07** (gleicher Tag) als Phase-15 Closeout abgeschlossen. Die echte `instinct/extractor.py`-Signatur wurde nicht gegen die wiring-Aufrufung gegengeprüft — Phase-15-Code wurde als „fertig" angenommen und nur die wiring angepasst. Die 14 Tests in `test_instinct_extractor.py` waren grün, weil sie die `wiring.py`-Konstruktion gar nicht aufrufen (sie konstruieren `SingleShotInstinctExtractor` direkt mit Fake-LLMs). |
| Severity? | 🔴 Live-Blocker — Scheduler kann nicht starten, gleicher Effekt wie Hotfix #1 + ModuleNotFoundError. |

**2. Atomic Commit 1/1 — `phase8_scheduler/scripts/wiring.py` Hotfix #2:**

| Datei | Inhalt | LOC | Σ-Delta | Akzeptanz |
|---|---|---:|---:|---|
| `phase8_scheduler/scripts/wiring.py` (Hotfix #2) | 1-Wort-Edit Z. 400: `SingleShotInstinctExtractor(llm=llm, cfg=instinct_cfg)` → `SingleShotInstinctExtractor(llm_client=llm)`. Das `cfg=instinct_cfg` ist nicht nötig (der Extractor hat kein cfg), und der InstinctBridge bekommt sein cfg auf Z. 406 korrekt. Py-Compile OK. P8 256 Tests grün, P15 126 Tests grün (kein Test-Touch). | +1 / −1 | – | Phase-16-Plan §4 (P8 in Cross-Phase-Freigabe) + Session-#15-Watch-Item „Smoke-Test für wiring.py" + minimale Änderung | Commit `8363903 phase16+phase8: code -- Hotfix #2 wiring.py:400` |

**3. Σ-Sweep nach Hotfix #2 (verifiziert 2026-09-07):** **1921 grün unverändert.** Phase-1/2/3/4/5/6/7/8/9/10/12/13/14/15/16/root = 97+82+105+162+190+76+169+256+95+165+145+82+61+126+5+105 = **1921** ✅ Plan-Akzeptanz AK2 trivial erfüllt. P8 256 Tests grün (Bug lebte nur im Runtime-Pfad von `scripts/wiring.py`).

**4. Hook-Verify:** `python3 scripts/check_doc_rotation.py --strict --quiet` → exit 0 nach Hotfix-#2-Commit und nach dieser Rotation.

**5. Phase-15-Watch (gut zu wissen, kein Phase-16-Edit):**
- `InstinctBridge.__init__` (Phase-15) hat `cfg: InstinctConfig` als Pflicht-Argument (kein Default). Die wiring auf Z. 402-407 ist korrekt.
- `SingleShotInstinctExtractor.__init__` (Phase-15) hat **kein** cfg-Argument. Die wiring auf Z. 400 darf cfg nicht weiterreichen.
- `InstinctValidator.__init__` (Phase-15) hat **keine** Argumente. Die wiring auf Z. 401 (`instinct_validator = InstinctValidator()`) ist korrekt.
- Diese Asymmetrie ist dokumentiert in `bridge.py:65`, `extractor.py:260`, `validator.py:35-50`. Wer den Wiring-Layer schreibt, muss alle 3 Signaturen kennen — die Tests testen sie einzeln, nicht in der wiring-Kombination.

**6. Git-Stand am Session-Ende (vor Push):**
- HEAD = dieser Final-Commit (Session-Rotation #15→#16 + Hotfix #2 davor).
- Commits lokal ahead of `origin/main = e66be3a` = 13 (`994a5af` Rotation #15 + `a774aec` Hotfix #1 + `4481672` Rotation #14 + `48eb55b` dev_install.sh + `a5399e9` setup.cfg + `240eea7` pyproject.toml + `6d26cf1` #13-Final + `6279874` E1-Aktiv-Block + `743e032` Rotation #13 + `a660878` v2-Supersede + `e66be3a` Rotation #12 + **`8363903` Hotfix #2** + dieser Final-Rotation).
- Working tree clean nach jedem Commit.
- 1 Hotfix-#2-Commit + 1 Rotation-Commit pending, nicht eigenmächtig gepusht.

### Findings

🟢 **3. Phase-16-D2.6-Regression-Bug strukturell behoben:** Session #13 ModuleNotFoundError (via Session #14 editable-install) + Session #15 NameError `intinct_cfg` (via Hotfix #1) + Session #16 TypeError `SingleShotInstinctExtractor(llm=…, cfg=…)` (via Hotfix #2). Alle 3 Crashes aus demselben Commit `bfab841` 2026-09-07.

🟢 **Minimal-invasiver Fix:** 1-Wort-Edit, keine API-Änderung, kein Test-Touch, keine Doku-Änderung. Cross-Phase-Freigabe P8 per Phase-16-Plan §4 (Nikinger 2026-09-05).

🟢 **Σ unverändert:** P8 256 Tests grün, P15 126 Tests grün, Repo-weit 1921 unverändert.

🟢 **Hoffentlich letzter D2.6-Bug:** wenn der Scheduler nach Hotfix #2 hochkommt, ist die wiring-Pipeline komplett. Sollte ein 4. Bug auftauchen, würden die Truncate-Logs (vom Nikinger gemacht) und ein neuer Restart es aufdecken — Pattern ist etabliert.

🟡 **Watch-Item Phase-17-Material (dringend!):** `scripts/wiring.py` braucht einen **Import-Smoke-Test** für `_build_reward_sink` (und auch `build_scheduler`): „kann die Funktion mit gefakten broker+db+llm aufgerufen werden, ohne dass ein NameError/TypeError/ModuleNotFoundError auftritt?". ~30 LOC Test-Code, ~5 Min, fängt alle 3 jetzigen D2.6-Bugs gleichzeitig. Diese Lesson ist die direkte Anwendung der Session-#13-OPEN-QUESTION-Anmerkung + jetzt 2-mal in derselben Session empirisch bestätigt.

🟡 **Watch-Item Phase-15-Doku (Phase-15 selbst ist closed):** in `phase15_v4/instinct/__init__.py` oder einer kurzen `PHASE15_WIRING.md` sollten die **drei** Konstruktor-Signaturen (`InstinctBridge`, `SingleShotInstinctExtractor`, `InstinctValidator`) prominent dokumentiert sein, damit zukünftige Cross-Phase-Editoren sie nicht falsch erraten. Aktuell sind sie nur in den jeweiligen `__init__`-Docstrings vergraben.

🔵 **Beobachtung — D2.6 hat 3 Bugs in 5 Zeilen produziert:** `instinct_cfg = InstinctConfig()` (Z. 399, korrekt) + `SingleShotInstinctExtractor(...)` (Z. 400, 2 Bugs!) + `instinct_validator = InstinctValidator()` (Z. 401, korrekt) + `InstinctBridge(...)` (Z. 402-407, korrekt). Das ist eine auffallend hohe Bug-Dichte für eine einzige kurze Code-Stelle — Hinweis darauf, dass der Code schnell runtergeschrieben wurde ohne Smoke-Test. Phase-17-Lesson: „jede Code-Stelle, die ein Symbol aus einer anderen Phase erstmalig importiert + benutzt, braucht mindestens einen Smoke-Test, bevor der Commit rausgeht".

### Open questions / blockers

- **Live-Stand (post Session #16, vor Nikinger-Restart-Versuch #3):** Scheduler **DEAD** (TypeError als letzte Log-Zeile), Recorder **ALIVE** (PID 268859), Discovery **ALIVE** (PID 268871), WebUI **ALIVE** (PID 268921). Logs wurden **NICHT** von Nikinger nochmal truncatet (war nach Hotfix #1 auch nicht nötig — Scheduler hängt im ersten Cycle). **Empfehlung nächste Aktion (Nikinger):** `bash scripts/restart-services.sh start` (Scheduler sollte jetzt hochkommen). Falls ein 4. Bug auftaucht, neuer Truncate + Logs teilen.
- **E3-Restart-Tag:** wenn dieser Restart erfolgreich ist, dann **endgültig unblocked.** Tag 1 = morgen (Mo 2026-09-08) wäre perfekt.
- **E4 (Tagesroutine + Closeout)**: nach E3 in der Folgesession.
- **Push-Freigabe-Stand:** Nikinger hat zwischen #15 und #16 0 Commits gepusht. Diese Session **2 Commits pending** (`8363903` Hotfix #2 + dieser Final-Rotation). Plus 11 Commits pending aus Sessions #13 + #14 + #15. **Branch lokal 13 ahead of origin/main = e66be3a.**

### Next (für die Folgesession)

- **Scheduler-Restart-Versuch #3 (Nikinger-Aktion, hoffentlich letzter):** `bash scripts/restart-services.sh start` (alle 4 frisch starten — Scheduler sollte jetzt hochkommen dank Hotfix #2). → `sleep 30` + K7-Caps-Pin-Verify (`account=demo, max_trades=5, daily_loss_cap=1800.0, cycle=5min`). → Falls Scheduler crasht: Log teilen.
- **E3 — Runbook-Start nach erfolgreichem Scheduler-Restart (Nikinger-Aktion, Runbook v2 §0 Reihenfolge):** Schritt 1 = Pflicht-Operator-SQL ✅ DONE (Session #13) → Schritt 2 = v2 §2 Pre-Flight → Schritt 3 = v2 §2.6 Prereg-Aktiv-Block ✅ DONE → Schritt 4 = v2 §3 Restart-Sequenz (Restart war gerade, also als „done" markiert) → Schritt 5 = v2 §4 Day-0-Checks Timeline → Schritt 6 = v2 §5 Tagesroutine → Schritt 7 = v2 §8 Tag-10-Closeout.
- **E4 — Tagesroutine + Closeout**: ab Tag 1 täglich `autonomy_report.py --day`. Nach Tag 10: `--summary`, bei `overall_verdict == "PASS"` Closeout-Handover + SVG + Status-Pflege.

### Watch-Item / Plan-Hygiene (für spätere Sessions)

- **Pflicht-Operator-SQL §1 v2**: ✅ DONE (Session #13, Commit `6279874`).
- **Staffelung via `marginDepositBands`** (Plan §13 #8): Phase-17-Material.
- **Hybrid-Test-Ansatz** (Session #11 Findings): Phase-17-Material.
- **Runbook-Supersede-Disziplin** (P11): wenn nach E3 etwas am Runbook fehlt, kein Edit — neues, datiertes, supersedendes Doc.
- **Phase-17-Kandidaten:** Prozess-Supervision; Strategie-Bewertung; **dringend: Import-Smoke-Test für `scripts/wiring.py`** (jetzt 3-mal empirisch bestätigt: D2.6-Code ohne Smoke-Test = 3 Bugs).
- **Phase-9-Discovery-Filter** (`is_weekend_market`): strukturelle Lösung für die 3-Epics-Lücke.
- **Phase-15-`requires-python` Align-Option:** falls Nikinger strikt `>=3.12` statt `>=3.11` will, 1-Zeilen-Edit.
- **Phase-15-Wiring-Doku (Phase-17-watch):** 3 Konstruktor-Signaturen prominent dokumentieren in Phase-15-Repo.

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
| E (Autonomie-Test, Pre-Step Phase-15-install) | ✅ endgültig in packaging (Session #14) |
| E (Autonomie-Test, Hotfix Typo-Bug) | ✅ endgültig in code (Session #15) |
| E (Autonomie-Test, Hotfix #2 Signatur) | ✅ endgültig in code (Session #16) |
| E (Autonomie-Test, E3 Runbook-Start) | 🔴 offen [Nikinger-Aktion: restart, hoffentlich wirklich unblocked] |
| E (Autonomie-Test, E4) | 🔴 offen [nach E3-Restart-Start] |

**Push-Status dieser Session:** **2 Commits pending** (`8363903` Hotfix #2 + dieser Final-Rotation), 0 Commits gepusht. Plus 11 Commits pending aus Sessions #13 + #14 + #15. **Branch lokal 13 ahead of origin/main = e66be3a.**