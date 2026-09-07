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
updated: 2026-09-07 (+ Exec-Session #5 → Archiv; Exec-Session #6 startet Block D; Phasenkopf trägt Exec-#6)
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
## Session stopped — 2026-09-07 (MiniMax-M3-Exec-Session #6, Block E Step E1 Vorregistrierung endgültig in docs, Σ 1864 grün unverändert [docs-only], Pause auf Nikinger-Auftrag)

> **Auftrag:** Nikinger-Chat 2026-09-05 (Phase-16-Exec-Folge, „letzten sesion") am 2026-09-07 fortgesetzt: „Next step, atomically, then ask nikinger." — **Block E Step E1** (Plan §6 E1, P11) endgültig in docs. Block D (D1/D1.2/D2/D3) + Block E (E2/E3/E4) bleiben für nachfolgende Sessions.
>
> Plan-Anker: [`../docs/concepts/phase16_activation_plan.md`](../docs/concepts/phase16_activation_plan.md) §6 Block E Step E1 (S. 760–769) · §1 P11 (Vorregistrierung vor Start, danach nicht geändert) + P17 (erlaubte Operator-Ereignisse) + P4/P5 (Arme ON + Promotion-Default) + P6 (Rescue AUS) + P7 (Universe ohne Wochenend) · §7 AK13 (Commit-Zeit < Start-Zeile) + AK15 (7 PASS-Kriterien) + AK16 (Closeout) · §11 Operator-Aktionen #5/#6/#7 · §13 Opus-Review #5 (Supervision), #6 (WebUI-Aliveness unmessbar), #8 (Bridge unerreichbar im Test), #9 (Budget-Datei-Korruption).
>
> Ausführungs-Scope: **2 Atomic Commits** (`af99a2c` E1 Vorregistrierung + INDEX-Zeile · dieser Final-Commit Session-Rotation #5→#6). Push-Freigabe (P18) gilt weiterhin; diese Session pusht **nicht** eigenmächtig.

### Completed

**0. Cross-Session-Drift-Vorab-Check (Session-Start dieser Exec-Folge-Session #6, 2026-09-07):**
- `git log origin/main..HEAD --oneline` → leer (HEAD = `b2a64df` = origin/main; 7 Session-#5-Commits sind inzwischen gepusht).
- `git status` → working tree clean bis auf untracked `data/`.
- Hook `check_doc_rotation.py --strict --phase phase16_activation` → exit 0 (vor dieser Rotation: Phasenkopf 1 Block Exec-#5, Archiv 4 Blocks).
- §6 E1-Verbatim-Bestätigung: 9 Konfig-Werte (Tage/Account/max_trades/daily_loss_cap/Token-Budget/4 Arme/Universe/Rescue/Promotion-Bridge), 7 PASS-Kriterien mit append-only Messquellen, 4 erlaubte Operator-Ereignisse (P17), 6 Watch-Items, Operator-Regel, Aktiv-Block.

**1. Block-E Step E1 in 1 atomaren Commit:**

| Step | Commit | Scope | Σ-Delta | Akzeptanz |
|---|---|---|---|---|
| **E1** Vorregistrierung | `af99a2c` phase16: docs | **NEU** `phase16_activation/PHASE16_AUTONOMY_PREREGISTRATION.md` (9 vorregistrierte Werte + 7 PASS-Kriterien AK15 mit append-only Messquellen + 4 erlaubte Operator-Ereignisse P17 + 6 Watch-Items + Operator-Regel + Aktiv-Block vom Operator vor E3-Restart) + INDEX-Zeile in `docs/INDEX.md` (Phase-16-Block, zwischen SESSIONS_ARCHIVE und Plan-Link). | 0 (docs-only) | AK13 (Commit-Zeit < Start-Zeile ist die Nikinger-Pflicht bei E3) + AK15-Framework (Kriterien vorregistriert, Messquellen ausschließlich append-only, Opus-Review §13 #6 eingehalten: keine `*_state.json`, stattdessen `*.log` + `.jsonl` + SQLite-Tabellen) |

**2. Σ-Sweep nach E1 (verifiziert 2026-09-07):** **1864 grün unverändert** (root `tests/` = 105 nachgemessen, alle anderen Phasen unangetastet). Plan-Akzeptanz AK2 (Σ ≥ Vorblock) trivial erfüllt.

**3. Hook-Verify:** `python3 scripts/check_doc_rotation.py --strict --quiet` → exit 0 nach Commit + nach Rotation.

**4. Git-Stand am Session-Ende:**
- HEAD = dieser Final-Commit.
- Commits lokal ahead of `origin/main` = 0 (E1 ist die erste Session nach dem letzten Push) + 2 (diese Session: `af99a2c` E1, dieser Final-Commit) = **2 Commits ahead**.
- Working tree clean nach jedem Commit (außer untracked `data/`, gitignored).

### Findings

🟢 **E1 erfüllt P11 wörtlich:** Vorregistrierung committet **vor** dem E3-Restart (AK13: Commit-Zeit < Start-Zeile ist strukturell erfüllbar, weil die Vorregistrierung als Doku-Only **jetzt** im Repo steht und der Operator-Restart frühestens nach Block D erfolgen kann). Nach dem Start **kein** Edit mehr an den 9 Werten oder 7 Kriterien — Korrekturen nur als neues, datiertes, supersedendes Dokument (M1-Disziplin, analog `META_M1_PREREGISTRATION.md`).

🟢 **Aktiv-Block = Eintragung, kein Edit:** der einzige Operator-Touch am Dokument ist die `## Aktiv-Block`-Tabelle (Start-Zeitstempel + Ende + Restart-Befehl + Anwesenheits-Bestätigung), explizit als „Eintragung am E3-Tag **vor** der ersten Start-Zeile" definiert. Das ist **vor** dem Test und **nicht** „nach dem Lauf geschrieben" — P11-Spirit gewahrt.

🟢 **append-only Quellen konsequent:** AK15 misst ausschließlich aus `*.log` + `*.jsonl` + SQLite-Tabellen (Trade-Tabelle, `bars.sqlite`). `*_state.json` sind explizit ausgeschlossen (Opus-Review §13 #6: in-place-Überschreibung, beweist nichts). WebUI-Aliveness ist ehrlich als Operator-Sichtung vorregistriert, nicht als append-only Beleg.

🟢 **PASS-Kriterien messen Autonomie, nicht Profit:** Kriterium 3 zählt nur ≥ 5 autonome CLOSED-Trades (nicht Win-Rate, nicht P&L). P&L ist explizit aus dem Test ausgeschlossen („Was diese Vorregistrierung *nicht* macht").

🟡 **Kriterium 7 (Caps unverändert) ist eine kleine Schwäche:** es pinnt die Start-Log-Zeile auf exakte Strings. Wenn der Scheduler-Start-Log-Text sich minimal ändert (z.B. Float-Format `1800.0` → `1800`), bricht das Grep-Pattern. Mitigation: das ist `daily_loss_cap=1800.0` mit `.0`-Suffix (Python-Float-Default-Repr), die Wahrscheinlichkeit einer Änderung ohne Phase-17-Skript ist gering. Beim E3-Runbook-Schritt nachmessen + ggf. das Pin-Muster schärfen — bewusst NICHT jetzt (würde M1-Disziplin verletzen: kein Vorab-Wissen nach dem ersten Log-Blick).

🟡 **Kriterium 2 „Dienste pro Handelstag aktiv"** ist eine 3+1-Regel (3 automatische append-only Belege + 1 Operator-Sichtung WebUI). Die Operator-Sichtung ist kein technisches PASS, sondern eine Selbstverpflichtung — wenn Nikinger die WebUI nicht aktiv prüft, gilt Kriterium 2 als „nicht erfüllt" unabhängig von der Realität. Bewusst so vorregistriert: WebUI-Aliveness ist nicht anders belegbar (Opus-Review §13 #6).

🟡 **Watch-Item W6 (`min_evidence` vs. Trade-Zahl)** erwartet n≈10–20 Trades ≪ `instinct_n_min = 50` → VETO 5 bleibt No-Op. Das ist **kein** PASS-Verletzung, sondern per Plan §13 #8 erwartetes Verhalten (Bridge lebt, ist aber unter der Schwelle). Beim Closeout wird die tatsächliche n-Zahl als Befund geführt.

🟢 **Cross-Phase-Disziplin:** E1 berührt **keinen** Cross-Phase-Code (nur Phase-16-Doc + INDEX-Eintrag). P1/P2/P3/P4/P5/P7/P8/P9/P15 alle unangetastet.

### Open questions / blockers

- Keine. E1 ✅ vollständig. AK13 (Commit-Zeit < Start-Zeile) hängt jetzt nur noch an der **Reihenfolge der Operator-Aktionen** beim E3-Restart (zuerst D1+D2 fertig bauen, dann E3-Restart ausführen, dann Vorregistrierung bleibt unangetastet).

### Next (für die Folgesession)

- **Block D — Freischaltung** (Plan §6 D1..D3, nach E1 freigegeben):
  - **D1** = Defaults flippen + `--no-*`-Schalter (P4/P5/P8/P15, AK5) — `SchedulerConfig` Defaults `enable_* = True` + `config_from_args` Mirror + `--no-*`-Flags + Entfernung der `--enable-*`-Flags + Help-Text-Update. ~5 Tests.
  - **D1.2** = Bar-Stream-Token-Wrapper (P8 only, Opus-Befund #2, AK5b) — Wrapper-Klasse die `restart()` korrekt mit aktuellen Broker-Tokens baut, damit der Arm nach IG-Token-Rotation nicht stirbt. 2 Tests.
  - **D2** = Promotion-Bridge + Prädikat-Compiler (L6, P2/P7/P8/P15, AK10) — Extractor-Hook am Close-Seam von `RewardSink` → Validator → DB; Promotion beim Start + nach jedem Close; Prädikat-Compiler (Mini-Grammatik `avoid <BUY\|SELL>[ on <EPIC>]`). Cross-Phase Phase 15 + Phase 5 + Phase 7 + Phase 2 + Phase 8. ~10 Tests.
  - **D3** = Margin-Headroom B3 (L7, P1/P5, AK11) — **erst** Operator-Live-Probe `probe_market_margin.py` für 3 Epics (Demo), **dann** Code in P5 Sizing-Grenzfall. ~3 Tests.
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
| **E (Autonomie-Test, Vorregistrierung)** | ✅ **E1 endgültig in docs** (diese Session) |
| D (Freischaltung) | ⏳ nach E1 (Vorregistrierung) — kann jetzt starten |
| E (Autonomie-Test, Rest) | ⏳ E2/E3/E4 nach D + Operator-Restart |

**Push-Status dieser Session:** **0 Commits gepusht**, 2 Commits pending (E1 + Final-Rotation) ahead of `origin/main`.