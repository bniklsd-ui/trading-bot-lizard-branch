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
updated: 2026-09-07 (+ Exec-Session #11 → Archiv; Exec-Session #12 schließt Block E Step E3 endgültig in docs: `phase16_activation/PHASE16_E3_RUNBOOK.md` NEU [363 LOC, locked-nach-Commit analog Prereg-Disziplin, Korrekturen nur als neues datiertes Supersede] + INDEX.md-Zeile; E3 ist ein Plan-verbatim-Konsolidat von Plan §6 E3 S. 797-808 + §11 Operator-Aktionen #5/#6/#7 + Session-#11-Watch-Items in 9 Sektionen [BLUF / §1 Pre-Flight 6 Schritte / §2 Restart-Sequenz verbatim / §3 Day-0-Checks Timeline 5min-30min-4h-24h mit SQL-Smokes / §4 Tagesroutine 1-min-Tagesabschluss + 5 Nicht-Tun-Punkte / §5 Trigger-Bedingungen T-1..T-12 mit T-12 Sofort-Stop kill -TERM bei Nicht-Demo-Trade / §6 Watch-Items W1-W6 verbatim aus Prereg / §7 Tag-10-Closeout / §8 was-das-Runbook-nicht-macht / §9 Cross-Refs]; keine Cross-Phase-Touches; Phasenkopf trägt Exec-#12 mit Verweis auf Runbook §1 Pre-Flight §1.4 K1-Log-Truncate (löst Session-#11-Watch-Item ein, ohne Code-Change); Σ 1921 unverändert docs-only; Block E [E1 docs ✅, E2 code ✅, E3 docs ✅] ⇒ offen nur E3 Runbook-Start [Nikinger-Aktion] + E4 Tagesroutine+Closeout-Handover+SVG)
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
## Session stopped — 2026-09-07 (MiniMax-M3-Exec-Session #12, Block E Step E3 Runbook endgültig in docs, Σ 1921 grün unverändert [docs-only], Exec-#11-Block verbatim nach SESSIONS_ARCHIVE.md rotiert [12. Eintrag, +1 vs. Stand Session #11], Pause auf Nikinger-Auftrag)

> **Auftrag:** Nikinger-Chat 2026-09-07 (Phase-16-Exec-Folge, „letzten sesion → Next step, atomically, then ask nikinger"): Session-#11-Empfehlung war E3 (Operator-Restart, Nikinger-Job, Plan §6 E3 S. 797-808) — nicht mechanisch von der Exec-Session ausführbar. Als atomischer Pre-E3-Deliverable jetzt **Block E Step E3 Runbook endgültig in docs**: `phase16_activation/PHASE16_E3_RUNBOOK.md` NEU [363 LOC, locked-nach-Commit analog Prereg-Disziplin, Korrekturen nur als neues datiertes Supersede]. Konsolidiert Plan §6 E3 S. 797-808 + §11 Operator-Aktionen #5/#6/#7 + Session-#11-Watch-Items (K1-Timestamp-Truncate, Hybrid-Test, Staffelung) in 9 Sektionen [BLUF · §1 Pre-Flight 6 Schritte · §2 Restart-Sequenz verbatim · §3 Day-0-Checks Timeline 5min/30min/4h/24h mit SQL-Smokes · §4 Tagesroutine 1-min-Tagesabschluss + 5 Nicht-Tun-Punkte · §5 Trigger-Bedingungen T-1..T-12 · §6 Watch-Items W1-W6 · §7 Tag-10-Closeout · §8 was-das-Runbook-nicht-macht]. Block E [E1 docs ✅, E2 code ✅, E3 docs ✅] ⇒ offen nur E3 Runbook-Start [Nikinger-Aktion] + E4 Tagesroutine+Closeout-Handover+SVG.
>
> Plan-Anker: [`../docs/concepts/phase16_activation_plan.md`](../docs/concepts/phase16_activation_plan.md) §6 E3 S. 797-808 (4 Bash-Zeilen `restart-services.sh status/start` + `cat /proc/.../cmdline` + `grep "starting scheduler daemon"` verbatim übernommen in §2) · §11 Operator-Aktionen #5/#6/#7 (Restart · täglicher `--day`-Report · Tag-10-Closeout → §4/§7) · §7 AK4 (Schema-Floor 9 in §1.2) · §7 AK5 (Default-Profile in §1.2-§2 erwartet; `--enable-*`-Flags entfernt per D1) · §7 AK13 (Aktiv-Block-Eintragung in §1.6) · §7 AK14 (Autonomy-Report-Use in §4 + §7) · §7 AK15 (7 PASS-Kriterien + ihre append-only Messquellen → §4 + §6) · §8 Fehlgriffe-Tabelle (T-1..T-12 mappen die häufigsten Symptome auf Exec-Session-Pfad) · §10 Out-of-Scope (Strategie-Bewertung, Auto-Restart, Fehlgriff-Diagnose → §8 explizit ausgeschlossen) · §1 P11 (Prereg-Disziplin übertragen: Runbook locked-nach-Commit, Korrekturen nur als Supersede) · §1 P15 (neue .md-Datei ⇒ INDEX.md-Zeile im selben Commit) · Session-#11-Watch-Item K1 timestamp-Filter (Truncate-Anweisung in §1.4 verbatim übernommen, löst das Watch-Item ein, kein Code-Change nötig).
>
> Ausführungs-Scope: **2 Atomic Commits** (`a3fa6ce` phase16: docs -- E3 Runbook + INDEX.md-Zeile · dieser Final-Commit Session-Rotation #11→#12). Push-Freigabe-Stand: Nikinger hat zwischen #11 und jetzt 0 Commits gepusht (last push war Session #11 ⇒ `e9c8aa7..11f315b`, `origin/main = e219a25` nach dem 2026-09-07 Push-Freigabe-Status-Update-Commit `e219a25` von Session #11). Diese Session pusht die **eigenen** 2 Commits **nicht** eigenmächtig.

### Completed

**0. Cross-Session-Drift-Vorab-Check (Session-Start dieser Exec-Folge-Session #12, 2026-09-07):**
- `git log origin/main..HEAD --oneline` → leer (HEAD = `e219a25` = origin/main; Cross-Session-Pattern bestätigt).
- `git status` → working tree clean bis auf untracked `data/` (gitignored).
- Hook `check_doc_rotation.py --strict --phase phase16_activation` → exit 0 (vor dieser Rotation: Phasenkopf 1 Block Exec-#11, Archiv 11 Blocks).
- §6 E3 Source-Pin-Bestätigung verbatim an aktuellen Stand:
  - `scripts/restart-services.sh` Z. 47-67 (Service-Registry) + Z. 213-247 (cmd_start, sequenziell Recorder→Discovery→Scheduler→WebUI mit 2 s Settle-Sleep) + Z. 197-209 (cmd_stop, SIGTERM + 5 s grace → SIGKILL) — exakt die Reihenfolge, die das Runbook §2 referenziert.
  - `phase8_scheduler/scripts/run_scheduler.sh:64` echo `[run_scheduler] starting daemon from ${PROJECT_DIR} (keyring must be unlocked)...` (no ts) → gefolgt von `scheduler/run.py:206-212` `logger.info("starting scheduler daemon (account=%s, max_trades=%d, daily_loss_cap=%s, cycle=%dmin).")` **mit** Timestamp-Prefix (default `basicConfig` Format `asctime levelname name: message`) — Runbook §2 verweist auf die zweite Zeile für die K7-Caps-Pin-Verifikation.
  - `phase12_data_foundation/scripts/run_recorder.sh:37` `[run_recorder] starting recorder from <path>...` (no ts).
  - `phase14_discovery/scripts/run_discovery.sh:46` `[run_discovery] starting daemon from <path> (unarmed ⇒ noop)...` (no ts).
  - `phase8_scheduler/scripts/run_webui.sh:47` `[run_webui] dashboard on http://127.0.0.1:8000 (read-only DB, localhost-only)...` (no ts).
  - `phase1_broker_wrapper/credentials.py` `get_credential(name)` (keyring-via-D-Bus, kein `.env`-Touch, Hard Rule 1).
  - `phase2_persistence/persistence/db.py` `Database.__init__` + `run_migrations()` (Schema-Floor-9-Verify via `_schema_version` + `PRAGMA user_version`).
  - Session-#11-Watch-Item K1 timestamp-Filter: bestätigt dass 3 von 4 Wrapper-Logs untimestamped Start-Lines schreiben → Runbook §1.4 mit Truncate-Anweisung als Pre-Flight-Schritt eingebaut.

**1. Block-E Step E3 in 1 atomaren Docs-Commit:**

| Datei | Inhalt | LOC | Σ-Delta | Akzeptanz |
|---|---|---:|---:|---|
| `phase16_activation/PHASE16_E3_RUNBOOK.md` (NEU) | 9 Sektionen. **§0 BLUF** (1 Satz). **§1 Pre-Flight** (6 Schritte, ≤ 5 min): §1.1 Liveness (`bash scripts/restart-services.sh status` → 4 Dienste tot seit B2); §1.2 Schema-Floor 9 (2 SQL-Smokes gegen `_schema_version` + `PRAGMA user_version`); §1.3 Keyring (Python-Snippet mit `get_credential` + 8-Zeichen-Fingerprint, Hard Rule 1); §1.4 K1-Log-Truncate (`truncate -s 0` für 3 untimestamped Logs, run_scheduler NICHT — löst Session-#11-Watch-Item ohne Code-Change); §1.5 DB-Health (Bars-Group + trade_outcomes-Count, keine `database is locked`); §1.6 Akten-Vermerk Prereg-Aktiv-Block (Eintragung, kein Edit, vor dem ersten Start). **§2 Restart-Sequenz** (Plan §6 E3 S. 799-808 verbatim + K7-Caps-Pin-Zeile `starting scheduler daemon (account=demo, max_trades=5, daily_loss_cap=1800.0, cycle=5min).`). **§3 Day-0-Checks Timeline** (t0+5min/30min/4h/24h mit 5-6 SQL-Smokes je Zeitfenster gegen `bars.source GROUP BY` / `trade_outcomes` OPEN-PENDING / `paper_trades` / `source_spend kind='sample'` / `instrument_universe` SUN*-Filter = 0 / Heartbeat ok / kein PreflightError). **§4 Tagesroutine** (1-min-Tagesabschluss mit `autonomy_report.py --day` + 5 Nicht-Tun-Punkte aus Prereg: kein manueller Restart außer Backoff-KILL-Clear / kein Trade-Eingriff Force-Trigger Hard Rule 5 / kein Hotfix-Commit auf Caps-Arms / keine DB-Repair außerhalb Runbook / kein Browser-Refresh). **§5 Trigger-Bedingungen** (T-1..T-12: Dienst tot nach Restart / Schema-Floor verletzt / SUN*-Regression / `bars.source='ls'` 0 nach 24 h / Heartbeat false ≥ 2 Tage / WebUI down / KILL ohne Auto-Backoff / Token-Budget vor 17:30 / Margen-Reject-Häufung / Reboot / Desktop-Session verloren / **T-12 Trade mit nicht-Demo-Account = SOFORT-STOP** mit `kill -TERM $(pgrep -f scheduler.run)` als Notbremse, Hard Rule 4). **§6 Watch-Items** (W1-W6 verbatim aus Prereg). **§7 Tag-10-Closeout** (`autonomy_report.py --from/--to/--summary` + Exec-Session rufen wenn `overall_verdict == "PASS"`; FAIL = Exec-Session, kein Operator-Workaround). **§8 was-das-Runbook-nicht-macht** (Strategie-Bewertung ausgeschlossen, keine Code-Änderungen, keine Prozess-Supervision, keine Fehlgriff-Diagnose = Exec-Session-Pfad). **§9 Cross-Refs** (Prereg + Plan §6/§7/§8/§10/§11/§13 + `restart-services.sh` + `autonomy_report.py` + Phase-15-Vorgänger). | 363 | – | Plan §1 P11 (locked-nach-Commit) + §1 P15 (INDEX.md-Zeile im selben Commit) + AK13 (Aktiv-Block-Pfad §1.6) + Session-#11-Watch-Item K1 (§1.4 löst es ein) |
| `docs/INDEX.md` (+1 Zeile) | Phase-16-Cluster: `phase16_activation/PHASE16_E3_RUNBOOK.md` (📕 E3 Operator-Runbook). Per Plan §1 P15 „neue .md-Zeile im selben Commit". | 1 | – | Plan §1 P15 |

**2. Σ-Sweep nach E3-Runbook-Abschluss (verifiziert 2026-09-07):** **1921 grün unverändert.** Phase-1/2/3/4/5/6/7/8/9/10/12/13/14/15/16/root = 97+82+105+162+190+76+169+256+95+165+145+82+61+126+5+105 = **1921** ✅ Plan-Akzeptanz AK2 trivial erfüllt (Σ ≥ Vorblock-Stand 1921 + 0 Tests). Kein Test-File, kein Code-Touch ⇒ Σ bit-identisch.

**3. Hook-Verify:** `python3 scripts/check_doc_rotation.py --strict --quiet` → exit 0 nach Code-Commit (`a3fa6ce`) und nach dieser Rotation.

**4. Runbook-Selbsttest (Markdown-Lint + Cross-Ref-Auflösung):** `python3 -c "import re; doc=open('phase16_activation/PHASE16_E3_RUNBOOK.md').read(); print('Sections:', len(re.findall(r'^## ', doc, re.M))); print('Cross-Refs:', len(re.findall(r'\.\./', doc))); print('Bash-Blocks:', doc.count('\`\`\`bash'))"` → Sections=9 (inkl. Header-Karte + §0 BLUF), Cross-Refs=10, Bash-Blocks=8. Alle Anchor-Dateien aus §9 (`PHASE16_AUTONOMY_PREREGISTRATION.md`, `phase16_activation_plan.md`, `restart-services.sh`, `autonomy_report.py`, `test_autonomy_report.py`, `phase15_v4/PHASE15_CLOSEOUT_HANDOVER.md`, `phase16_activation/SESSIONS_ARCHIVE.md`) existieren (`ls` verified). Keine toten Links.

**5. Git-Stand am Session-Ende (vor Push):**
- HEAD = dieser Final-Commit (Session-Rotation #11→#12).
- Commits lokal ahead of `origin/main = e219a25` = 2 (`a3fa6ce` E3-Runbook-Docs + dieser Rotation-Commit).
- Working tree clean nach jedem Commit.
- 2 Commits pending nicht eigenmächtig gepusht (Nikinger-Push-Freigabe erwartet, analog Session-#11-Verhalten: Nikinger pusht zwischen Folgesessions inzwischen unregelmäßig).

### Findings

🟢 **Runbook ist Plan-§6-E3-Konsolidat, nicht -Erweiterung:** die 4 Bash-Zeilen aus Plan §6 E3 S. 799-808 stehen verbatim in §2 (`restart-services.sh status/start` + `cat /proc/.../cmdline` + `grep "starting scheduler daemon"`). Day-0-Checks aus Plan §6 E3 Z. 806-808 sind in §3 als 24-h-Zeitfenster mit expliziten SQL-Smokes ausgeschrieben (5 min Liveness, 30 min Substrat, 4 h Heartbeat/Preflight, 24 h Tagesabschluss mit `autonomy_report.py --day`). Plan §11 Operator-Aktionen #5/#6/#7 sind 1:1 in §1-§4-§7 abgebildet.

🟢 **Session-#11-Watch-Item K1-Timestamp-Filter eingelöst:** §1.4 enthält die Truncate-Anweisung (`truncate -s 0 data/state/run_recorder.log data/state/run_discovery.log data/state/run_webui.log`) als Pre-Flight-Schritt 4 — `run_scheduler.log` bleibt unangetastet weil die `scheduler.run:206-212` `logger.info`-Zeile Timestamp-Prefix hat (default `basicConfig` Format), `autonomy_report.py` filtert dort präzise. Watch-Item von Session #11 explizit „löst das Watch-Item ein, kein Code-Change nötig" — exakt wie damals angekündigt.

🟢 **Prereg-Disziplin übertragen (locked-nach-Commit):** der Header-Doc-Kommentar (Zeile 4-7) sagt explizit: „committed **vor** dem ersten Service-Start; danach nicht geändert. Korrekturen nur als neues, datiertes, supersedendes Dokument mit Grund — niemals ein Edit hier". Gleiche Konvention wie `PHASE16_AUTONOMY_PREREGISTRATION.md` und `meta_m1_harness/META_M1_PREREGISTRATION.md` (M1-Vorregistrierungs-Disziplin, Plan §1 P11).

🟢 **T-12 Notbremse explizit ausgeschrieben:** §5 Trigger-Bedingungen T-12 — „Trade mit nicht-Demo-Account = Sofort Exec-Session + `kill -TERM $(pgrep -f scheduler.run)` als Notbremse". Hard Rule 4 (root-CLAUDE.md: „Never test against real money first") ist die einzige Bedingung, unter der der Operator einen laufenden Prozess eigenmächtig killt — alles andere (T-1..T-11) ist Exec-Session-Pfad. So wird die einzige asynchrone Gefahr (versehentlicher Live-Trade durch Bug) mit einem mechanisch eindeutigen 1-Zeilen-Befehl gestoppt, bevor die Exec-Session eintrifft.

🟢 **5 Nicht-Tun-Punkte aus Prereg explizit im Runbook:** §4 listet sie als Operator-Verhaltensregeln (kein manueller Restart außer Backoff-KILL-Clear / kein Trade-Eingriff / kein Hotfix-Commit auf Caps-Arms / keine DB-Repair außerhalb Runbook / kein Browser-Refresh). Das verhindert die häufigste Form von Operator-Drift, die ein 2-Wochen-Fenster zerschießen würde — die Prereg-Operator-Regel „nichts anfassen außer täglichem `--day`-Report" wird in mechanisch ausführbare Sätze übersetzt.

🟢 **Doppelte Sicherheitsnetze in §5:** T-1 (Dienst tot nach Restart) verbietet explizit den manuellen Operator-Restart („Exec-Session, **nicht** manuell restarten (das ist FAIL Kriterium 1)"). T-7 (KILL-Datei ohne Auto-Backoff) sagt „Nicht anfassen". T-10 (Reboot getriggert) sagt „Exec-Session, FAIL Kriterium 1". T-11 (Desktop-Session verloren) sagt „Nicht neu einloggen ohne Exec-Session-Rücksprache (Keyring-Relogin = FAIL Kriterium 1)". Der Runbook-Leser hat eine klare Trennlinie: alles, was nicht in der Liste steht, ist Exec-Session.

🟢 **Cross-Refs vollständig aufgelöst:** §9 listet 7 Anchor-Dateien (Prereg + Plan §6/§7/§8/§10/§11/§13 + `restart-services.sh` + `autonomy_report.py` + `test_autonomy_report.py` + Phase-15-Vorgänger), `ls`-verifiziert. Der Operator kann vom Runbook zum Plan und zurück navigieren, ohne den Repo-Inhalt zu kennen.

🟢 **Hard Rule 1 (Credentials) explizit in §1.3 beachtet:** der Keyring-Snippet druckt nur die ersten 8 Zeichen (`(get_credential(...) or '')[:8] + '...'`), kein Volltext, kein `.env`-Touch. Hard Rule 2 (VETOs) ist im Runbook nicht relevant — Runbook ist Operator-Pfad, nicht Order-Pfad. Hard Rule 3 (AI → Order) ist nicht relevant — E2-Script ist read-only, E3-Runbook ist Operator-Aktion. Hard Rule 4 (Demo-only) ist in T-12 als Sofort-Stop-Pfad verankert. Hard Rule 5 (Force-Trigger respektiert Daily PNL) ist in §4 als „kein Trade-Eingriff" abgedeckt (daily_loss_cap=1800 sperrt den Force-Trigger strukturell bei PNL < 0).

🟢 **Plan §1 P12 eingehalten:** E3-Runbook ist phase-intern, **kein** Cross-Phase-Code-Touch. Phase-16 self-contained. Keine `wiring.py`-, keine `recorder.py`-, keine `sizing.py`-Änderung.

🟡 **Watch-Item §8 „Fehlgriff-Diagnose = Exec-Session-Pfad":** das Runbook mappt Symptome (Tabelle in §5) auf Trigger, nicht auf Root-Cause. Das ist eine bewusste Reduktion — die Plan-§8-Fehlgriffe-Tabelle (z. B. „Heartbeat nach D1 weiter CRITICAL 'measurement arm off' → Bot nicht neu gestartet (`sys.modules`-Cache) — `/proc/<pid>/cmdline` + Startzeit prüfen") braucht Code-Verständnis und gehört in die Exec-Session. Der Runbook-Leser kommt mit Linux-Grundwissen + 1 min Lesezeit aus.

🟡 **Watch-Item Phase-16-Sub-Tag-Verlust:** das `updated:`-Stamp im Header trägt jetzt nur noch das Datum, nicht die Tageszeit. Bei mehreren Sessions am selben Tag ist die Reihenfolge nur über `git log` rekonstruierbar. Akzeptabel weil Session-#11 dieselbe Konvention hat.

### Open questions / blockers

- **Block E Schritt E3 ✅ (docs-Teil)** — Runbook endgültig in docs, locked-nach-Commit. Kein inhaltlicher Blocker.
- **E3 (Operator-Restart-Ausführung)** wartet auf **Nikinger-Aktion**. Plan §11 Operator-Aktion #5 + Runbook §1-§3. **Empfehlung an Nikinger:** Restart an einem Dienstag oder Mittwoch (Donnerstag/Freitag vermeiden wegen Schluss-Preisen und sauberen 10-Handelstagen ohne Wochenend-Lücke). Vor Restart das Runbook §1 Pre-Flight durchgehen (≤ 5 min).
- **E4 (Tagesroutine + Closeout)**: wird nach E3 in der Folgesession gestartet; benötigt die ersten `autonomy_report.py --day`-Outputs (Runbook §4 + §7). Closeout-Handover nach Tag 10 → `phase16_activation/PHASE16_CLOSEOUT_HANDOVER.md` (Plan-§-HANDOVER_PROMPT.md-Template) + `docs/architecture/phase16_activation.svg` 1080×1080 + Status-Pflege root-CLAUDE/ROADMAP/README/INDEX + Session-Rotation.
- **Live-DB Schema v7 → v9 Akten-Vermerk** (B2, Sessions #3) — heute nicht Phase-16-Edit, weiter offen.
- **Push-Freigabe-Stand:** Nikinger hat zwischen #11 und jetzt 0 Commits gepusht (letzter Push war `e219a25` = Stand Session #11). Diese Session 2 Commits pending (`a3fa6ce` + Rotation). **Push-Freigabe erwartet**, analog Session-#11-Verhalten (Nikinger pusht zwischen Folgesessions inzwischen unregelmäßig — manche Sessions werden sofort gepusht, andere erst auf Anfrage).

### Next (für die Folgesession)

- **E3 — Runbook-Start + Day-0-Checks** (Nikinger-Job, Plan §6 E3 S. 797-808 + Runbook §1-§3): Runbook §1 Pre-Flight (6 Schritte, ≤ 5 min) → §2 Restart-Sequenz (Plan §6 E3 verbatim) → §3 Day-0-Checks Timeline (t0+5min Liveness / t0+30min Substrat / t0+4h Heartbeat-Preflight / t0+24h Tagesabschluss). Tag-Wahl: Dienstag oder Mittwoch empfohlen (Donnerstag/Freitag vermeiden wegen Wochenend-Lücke). Vor dem ersten Start: Prereg-Aktiv-Block-Eintragung (Runbook §1.6) + Folge-Commit `phase16: docs -- E1-Aktiv-Block-Eintragung` mit Zeitstempel (AK13).
- **E4 — Tagesroutine + Closeout**: ab Tag 1 täglich `autonomy_report.py --day` (Runbook §4, ≤ 1 min/Tag). Nach Tag 10: `--summary` (Runbook §7), wenn `overall_verdict == "PASS"` Closeout-Handover `phase16_activation/PHASE16_CLOSEOUT_HANDOVER.md` nach `docs/HANDOVER_PROMPT.md` (BLUF, Bilanz, Bild `docs/architecture/phase16_activation.svg` 1080×1080, offene Entscheidungen), Status-Pflege root-CLAUDE/ROADMAP/README/INDEX, Session-Rotation.
- **PHASE16_CLOSEOUT_HANDOVER.md + docs/architecture/phase16_activation.svg** nach Tag 10 (Phase-16-Abschluss, Runbook §7).

### Watch-Item / Plan-Hygiene (für spätere Sessions)

- **K1 timestamp-Filter (s. Session #11 Findings 🟡):** durch Runbook §1.4 Pre-Flight-Schritt 4 (Truncate der 3 untimestamped Logs) eingelöst — kein Code-Change nötig. Falls später eine Session das Runbook editiert (statt Supersede), ist §1.4 die erste Stelle, die geprüft werden muss.
- **Staffelung via `marginDepositBands`** (Plan §13 #8 Beobachtung): nicht in dieser Session zu lösen, dokumentiert. Falls IG empirisch Trades > Schwellen ablehnt, ist `marginDepositBands`-Parsing die saubere Lösung (Option A im vorigen Phasenkopf). Bleibt Phase-17-Material. Runbook §5 T-9 hat den Margen-Reject-Trigger bereits als Exec-Session-Pfad — die Diagnose + Fix bleibt Phase-17.
- **Hybrid-Test-Ansatz** (Session #11 Findings 🟡): CLI-Bridge (`main()` + Exit-Codes 0/1/2) ist im Test nicht direkt gecovered. Plan §7 AK14 verlangt das nicht; Phase-17-Material wenn CI-Run gewünscht.
- **Runbook-Supersede-Disziplin** (P11): wenn nach E3 etwas am Runbook fehlt (z. B. ein neuer Trigger-Bedingung), wird **kein** Edit am bestehenden Runbook gemacht — neues, datiertes, supersedendes Doc (z. B. `PHASE16_E3_RUNBOOK_v2.md`) mit Begründung. Die Prereg-Disziplin gilt symmetrisch für beide Vorregistrierungs-Docs.
- **Phase-17-Kandidaten aus dem Runbook herausgelesen** (für die nächste Strategie-Phase, nicht Phase-16): Prozess-Supervision (systemd-User-Unit + Auto-Restart nach Reboot + Keyring ohne Login, Runbook §8 + Plan §10 / Opus-Review §13 #5); Strategie-Bewertung (Watch-Items W1 BUY-Bias, W2 DAX-Only → Win-Rate / Sharpe / P&L, Runbook §8 explizit ausgeschlossen); CLI-Bridge-Test-Hardening (Hybrid-Test-Ansatz oben).

**Block-Status nach dieser Session (endgültig):**

| Block | Status |
|---|---|
| A (Haushalt) | ✅ A-0..A-4 + A-5 Push (Sessions #1-#3) |
| B (Substrat) | ✅ B1+B3 code + B2 Operator-Apply + A-5 Push (Session #3) |
| C (Research-Loop) | ✅ C1+C2+C3+C5 endgültig in code; C4 = Doku-Only (Sessions #4-#5) |
| D (Freischaltung) | ✅ D1+D1.2+D2+D3.0+D3.1+D3.2 komplett (Sessions #7-#10) |
| E (Autonomie-Test, Vorregistrierung) | ✅ E1 endgültig in docs (Session #6) |
| E (Autonomie-Test, E2) | ✅ E2 endgültig in code (Session #11) |
| **E (Autonomie-Test, E3)** | ✅ **E3 Runbook endgültig in docs** (Session #12); E3 Runbook-Start [Nikinger] + E4 Tagesroutine+Closeout offen |

**Push-Status dieser Session:** **2 Commits pending** (`a3fa6ce` E3-Runbook-Docs + dieser Rotation-Commit), 0 Commits gepusht. **Nikinger-Push-Freigabe erwartet**, analog Session-#11-Verhalten (manche Sessions werden sofort gepusht, andere erst auf Anfrage). Branch lokal ahead of `origin/main = e219a25`.
