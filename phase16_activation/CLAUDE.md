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
updated: 2026-09-05 (+ Exec-Session #4 → Archiv; Exec-Session #5 startet D + E; Phasenkopf trägt Exec-#5)
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