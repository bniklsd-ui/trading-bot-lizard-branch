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
updated: 2026-09-08 (+ Exec-Session #22 schließt ab: **Phase-16-F-Subphase Block J — die drei Struktur-Defekte des laufenden 2-Wochen-Tests alle drei gefixt**, alle 5 Commits lokal ahead, Σ 1934 → **1940** [+6 neue Tests, 1 archive + 2 autonomy_report + 3 heartbeat]; Nikinger-Sonderauftrag 2026-09-08 „J0 ist deine Aktion" → Bot-Stopp-Reihenfolge Scheduler → Recorder → Discovery → WebUI + `ps`-Gegenprobe; 5 Atomic Commits: `669dde9` J1 BarArchive threadsicher (Cross-Phase P12, `check_same_thread=False` + `threading.Lock`) · `3969f8c` J2+J8 K1 misst im Fenster + WebUI-Start zählt einmal · `cae9669` J3+J5 Heartbeat-Coverage misst Handelssitzung Berlin 09:00–17:30 + 30-min-Recorder-Lag-Toleranz (Cross-Phase P12) · `6890ac4` J5/J6 Prereg v2 NEU (v1 byte-identisch eingefroren) + `docs/INDEX.md`-Supersede-Markierung · dieser Rotation-Commit #21→#22 mit Verbatim-Archiv-Verschiebung; Σ-Regression-Sweep 16 Suites einzeln nachgemessen, Akzeptanz J „Σ = 1934 + 6 = 1940" exakt getroffen; Push-Freigabe für 6 Commits steht aus (Nikinger-Sonderauftrag „Push-Freigabe für 7119bcc" + 5 Folge-Commits im selben Push); Nikinger-Aktionen heute+morgen: J4 (Log-Truncate 4 Wrapper-Logs morgen), J6 (Restart morgen vor 09:00 Berlin, damit Tag 1 voller Handelstag), Aktiv-Block-Eintrag in Prereg v2 vor erster Start-Zeile; G1/G2-Tagesroutine startet nach J6; offene Verifikationen AK-J1/J2/J3/J4 (alle vier hängen am ersten Markt-Tag nach J6, kein Live-Verify vor dem Restart). — Vorheriger Stand: Plan-Session #21 schließt ab: **`PHASE16_F_EXEC_PLAN.md` NEU` [611 LOC, Blöcke J/H/G/I] — drei Struktur-Defekte des laufenden 2-Wochen-Tests selbst gemessen [J-D1 LS-Bar-Stream schreibt nichts, `archive.py:77` `check_same_thread`-Default, 63 942 `ProgrammingError`, `bars.source='ls'` = 0; J-D2 K1 zählt ohne Fenster, `evaluate_k1` bekommt `from_ts`/`to_ts` von keinem der beiden Aufrufer Z. 870/919 → 7 statt 1 Start; J-D3 K4 unerreichbar, `heartbeat.py:73` misst gegen 00–24 h → `ok=False` an 10 Tagen in Folge]; Nikinger-Entscheidungen: Variante A [Lauf abbrechen, fixen, Prereg v2, Uhr auf Tag 1] + Cross-Phase **P12** freigegeben + Lock **F3 revidiert** [Hook-Step 4 statt neuem Skript] + Pattern C = Referenz entfernen; Σ-Regression-Baseline **1934** vor dem ersten Fix, 16 Suites einzeln gemessen; Step-0-Legacy-Ritual No-Op; 7 Aussagen aus `PHASE16_PARTIAL_CLOSEOUT.md` korrigiert [§1.4]; Exec-Session #20 → Archiv [21. Eintrag]; Push-Freigabe steht aus. — Vorheriger Stand: Exec-Session #19 schließt ab: Doc-Drift-Audit repo-weit nach Nikinger-Push — 6 Audit-Checks: #1 Push-Baseline ✅, #2 Σ-Konsistenz ✅ (Σ 1934), #3 Archiv-Integrität 🟢 (2 F8-B-Reparaturen `ce74ee1` Phase-14 + `23bbd14` Phase-15), #4 ein Block/Phasenkopf ✅, #5 INDEX-Vollständigkeit 🟡 (224 Skill-Internals fehlen — Scope-Drift), #6 Header-Card-Links 🟡 (29 echte fehlende Links aufgedeckt, read-only dokumentiert, Reparatur in Phase-16-F-Subphase Block H); Σ 1924 → 1934 unverändert (Archiv-Reparaturen = Markdown-Only); origin/main = 560d038, 0 Commits pending (Nikinger hat Session-#19-Commits gepusht); Cross-Phase-Freigabe: P14 für Phase-14 + Phase-15-Archive-Touch (`ce74ee1` + `23bbd14`), P16 für diese Rotation]; Exec-Session #20 schließt ab: **Phase-16-F-Subphase-Eröffnung mit `PHASE16_PARTIAL_CLOSEOUT.md` NEU** (310 LOC, Mini-Plan für die 2-Wochen-Test-Periode in 3 Blöcken G/H/I: G = E4-Tagesroutine-Begleitung 9 Tage, H = Audit-Restbefunde-Reparatur 29+1+1 am Wochenende 13.–14. Sept., I = Tag-10-Closeout Mo 2026-09-21 nach 17:30) + 8 Locks F1–F8 + 8 Akzeptanz AK-F1–AK-F7 + 8 Operator-Aktionen Nikinger + 7 Out-of-Scope-Items Phase-17 + 8 Drift-Items; kein Phase-17 (Nikinger-Auftrag „Keine Phase 17, weitere Phase 16 Subphase"); Modul-Tabelle um `PHASE16_PARTIAL_CLOSEOUT.md` ergänzt; Σ 1934 unverändert (docs-only, kein Test-Touch, kein Code-Touch außer der F-Subphase-Eröffnung selbst); 0 Commits pending (Nikinger pusht 560d038 nach dieser Session-#19-Eröffnung); Push-Freigabe-Stand: dieser Commit + 1 = 1 Commits pending nach Commit
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
| `PHASE16_PARTIAL_CLOSEOUT.md` | 📕 Partial Closeout zur 2-Wochen-Test-Halbzeit (Phase-16-F-Subphase: Blöcke G/H/I — E4-Begleitung + Audit-Restbefunde-Reparatur + Tag-10-Closeout) | F |
| `PHASE16_F_EXEC_PLAN.md` | 📕 Exec-Plan der F-Subphase (Blöcke J/H/G/I) — supersedet die H-Mechanik aus `PHASE16_PARTIAL_CLOSEOUT.md` §4 | F |
| `PHASE16_AUTONOMY_PREREGISTRATION_v2.md` | 📕 Prereg v2 (supersedet v1, Grund = die drei J-Defekte) | J5 |
| `PHASE16_CLOSEOUT_HANDOVER.md` + `docs/architecture/phase16_activation.svg` | Closeout nach Tag 10 | I-2 + I-3 |
| *(Cross-Phase)* `phase15_v4/instinct/bridge.py`, `compile.py` | Promotion-Bridge + Prädikat-Compiler | D2 |
| *(Cross-Phase)* `phase1_broker_wrapper/scripts/probe_market_margin.py` | Operator-Live-Probe für B3 | D3.0 |

---
## Session stopped — 2026-09-08 (MiniMax-M3-Exec-Session #22, Phase-16-F-Subphase Block J — die drei Struktur-Defekte des laufenden 2-Wochen-Tests **alle drei gefixt**, alle 5 Commits lokal ahead, Σ 1934 → **1940** [+6 neue Tests, 1 archive + 2 autonomy_report + 3 heartbeat]; Nikinger-Sonderauftrag 2026-09-08 „J0 ist deine Aktion" → Bot-Stopp-Reihenfolge Scheduler → Recorder → Discovery → WebUI + `ps`-Gegenprobe)

> **Auftrag:** Nikinger-Chat 2026-09-08 (Folgesession Plan-Session #21): „Push-Freigabe für
> 7119bcc. J0 (Bot stoppen) ist deine Aktion — Reihenfolge Scheduler → Recorder → Discovery →
> WebUI, danach ps als Gegenprobe (Parallel-Login-Falle). J6 (Restart) morgens vor 09:00,
> damit Tag 1 ein voller Handelstag ist. Ab dann G1/G2 täglich — das Caps-Pin-Kommando im
> Plan ist korrigiert, das aus dem Partial Closeout liest `/proc/<pid>/cmdline` und findet
> dort keine Caps." Ausführungsreif aus `PHASE16_F_EXEC_PLAN.md` (Plan-Session #21, Opus 5).

### Completed

- **J0 — Bot stoppen** in der vorgeschriebenen Reihenfolge Scheduler → Recorder → Discovery →
  WebUI mit `kill -TERM` + `ps`-Gegenprobe (Operator-Aktion Nikinger war „deine Aktion" laut
  Sonderauftrag). Recorder + Discovery + WebUI stoppten sofort (P14-D-Plan-Konform: signal
  check_interval_s ≤ 60 s); Scheduler brauchte ~3 min (cycle_interval_s = 300 s, einmal
  `time.sleep()` durchlaufen, dann `request_stop()` greift). Stop-Reihenfolge wichtig für
  Parallel-Login-Falle (Phase-1-Lightstreamer-Notes): wenn der Scheduler noch lebt während der
  Recorder startet, könnten beide parallel IG-Sessions aufmachen. **Ergebnis:** `ps` nach J0 =
  leer, keine PID-Files, keine Zombies, alle 4 Stop-Meldungen sauber geloggt (`scheduler.run:
  scheduler daemon stopped cleanly` / `Recorder received signal 15 — stopping` /
  `Discovery daemon received signal 15 — stopping` / `Finished server process`).
- **J1 — `BarArchive` threadsicher** (Commit `669dde9`, Cross-Phase P12):
  `phase12_data_foundation/data_foundation/archive.py:77` `sqlite3.connect(...)` → jetzt mit
  `check_same_thread=False`; `__init__` bekommt `self._lock = threading.Lock()`; alle 7
  DB-Methoden (`close`, `ensure_schema`, `insert_bars`, `window`, `latest_ts`,
  `bars_written_since`) tragen jetzt `with self._lock:` um ihre DB-Zugriffe. `coverage_ratio`
  absichtlich **ohne** Lock — sie ruft nur `window()` (das bereits locked) + pure-Python-Arithmetik
  (kein shared state). 1 Regression-Pin-Test `test_insert_bars_from_other_thread` (Phase 12
  root 145 → 146).
- **J2 + J8 — K1 misst im Fenster + WebUI-Doppelzählung weg** (Commit `3969f8c`):
  `phase16_activation/scripts/autonomy_report.py` drei Änderungen:
  (1) `_START_PATTERNS["webui"]` (Z. 143) matcht jetzt nur noch das Wrapper-Pattern
  `[run_webui] dashboard on` (vorher zwei Muster, uvicorn-Duplikat dabei) — J8.
  (2) Neuer Helper `_berlin_day_bounds(day)` als Inverse zu `_berlin_day`, gibt
  tz-aware UTC `[start, end)` für ein Berlin-Datum zurück, end-exclusive. Phase-16 hat
  `zoneinfo` schon importiert, kein neuer Import nötig.
  (3) `_build_day_report` (Z. 870) + `_build_summary_report` (Z. 919) übergeben jetzt
  Berlin-Tagesgrenzen an `evaluate_k1`; vorher wurde die ganze run_scheduler.log-Datei gezählt
  (= 7 historic Starts seit 2026-08-31, K1 FAIL auf Tag 1). 2 Regression-Pin-Tests
  (Phase 16 root 5 → 7).
- **J3 + J5 — Heartbeat-Coverage auf die Handelssitzung + Recorder-Lag-Toleranz** (Commit
  `cae9669`, Cross-Phase P12): `phase12_data_foundation/data_foundation/heartbeat.py` drei
  Änderungen:
  (1) `import zoneinfo` ergänzt + Modulkonstante `RECORDER_LAG_TOLERANCE_MIN = 30`.
  (2) Neuer Helper `_session_bounds_iso(day_utc)` neben `_day_bounds_iso` — Berlin 09:00–17:30
  via `zoneinfo.ZoneInfo("Europe/Berlin")`, end um die 30-min-Lag-Toleranz zurückgenommen
  (gemessen 18 min am 2026-09-08 08:48 UTC). Session-Zeiten 09:00/17:30 als Konstanten
  gespiegelt, **nicht** importiert (Phase 12 importiert nicht aus Phase 8).
  (3) `assess_day` benutzt jetzt ein zweites Paar `cov_start, cov_end` für die Coverage-Schleife
  statt `start, end` (00:00–24:00); die Bars-Today- und Paper-Trade-Zähler bleiben auf
  `_day_bounds_iso`, weil das Tages-Aggregate sind. 3 Regression-Pin-Tests (Phase 12 root 146 → 149).
- **J5 — `PHASE16_AUTONOMY_PREREGISTRATION_v2.md` NEU** (Commit `6890ac4`, 235 LOC) +
  `docs/INDEX.md` (v1-Markierung superseded + v2-Zeile). v1 ist **byte-identisch eingefroren**
  (vorher md5 = nachher md5, per Lock J6 + die v1-Einleitung „Korrekturen sind nur als neues,
  datiertes, supersedendes Dokument möglich"). v2 ist die aktive Vorregistrierung mit einem
  neuen `## Warum v2`-Block, der die drei J-Defekte + Fixes (Commits `669dde9`/`3969f8c`/`cae9669`)
  dokumentiert; v1-Wortlaut der PASS-Kriterien 1–7 unverändert (Kriterien waren richtig,
  Substrat war kaputt). Aktiv-Block ist neu und wartet auf die Operator-Eintragung am E3-Tag.
- **Session-Rotation #21 → #22**: Opus-5-Plan-Session #21-Block (alt) **verbatim** nach
  `SESSIONS_ARCHIVE.md` rotiert (jetzt 22. Eintrag, +1 vs. Stand Session #21); Phasenkopf
  trägt genau diesen #22-J-Exec-Block.

### Findings (alle 2026-09-08 während J-Exec gemessen)

- **Σ-Regression-Sweep nach Block J**: 16 Suites einzeln gemessen, **Σ 1940** grün
  (Phase 1 97 · Phase 2 82 · Phase 3 105 · Phase 4 162 · Phase 5 190 · Phase 6 76 ·
  Phase 7 169 · Phase 8 259 · Phase 9 95 · Phase 10 165 · Phase 12 **149** [+4] ·
  Phase 13 82 · Phase 14 61 · Phase 15 126 · Phase 16 **7** [+2] · root 115). Plan-Akzeptanz J
  „Σ = 1934 + 6 neue Tests = 1940" exakt getroffen (1 archive + 2 autonomy_report + 3 heartbeat).
- **P12-Archivierung gegengeprüft**: die `_session_bounds_iso`-Konstante `RECORDER_LAG_TOLERANCE_MIN`
  ist tatsächlich die einzige Stellschraube (Plan §3 J5 / §7 Fehlgriffe „K4 bleibt `ok=False` nach
  J3, `worst_coverage` aber nahe 1,0"): die Konstante wird per `grep -n` ein einziges Mal
  in `heartbeat.py:73` (Doc-Comment) + `:107` (Verwendung) referenziert.
- **Race-Condition-Smoke (manuell)**: `test_insert_bars_from_other_thread` schreibt aus einem
  `threading.Thread`, Haupt-Thread liest über `window()`. Ohne J1 hätte das den
  `sqlite3.ProgrammingError` aus dem Live-Log reproduziert; mit J1 ist es grün + die Bar
  ist lesbar (Roundtrip).
- **`_session_bounds_iso` vs `_day_bounds_iso`**: `bars_today` (`bars_written_since(start, end)`)
  zählt weiterhin alle Bars des Berlin-Tages 00:00–24:00 — das ist eine Tages-Aggregat-Frage
  („wie viele Bars hat der Recorder heute geschrieben?"), die unabhängig von Coverage ist. Nur
  die Coverage-Schleife nutzt das Session-Fenster.

### Akzeptanz J (Plan §3)

- **AK-J1** `bars.source='ls'` > 0 nach dem ersten Handelstag — **unverifiziert**, wartet auf
  J6-Restart (Bot ist seit 11:40 down). Verifizier-Befehl nach J6 + 10 min Markt-Öffnung:
  `sqlite3 "file:data/bars.sqlite?mode=ro" "select count(*) from bars where source='ls'"` → > 0.
- **AK-J2** 0 `ProgrammingError` im neuen `run_scheduler.log` — **unverifiziert**, gleiche
  Wartezeit. Verifizier-Befehl: `grep -c ProgrammingError data/state/run_scheduler.log` → 0
  nach erstem POST_WINDOW.
- **AK-J3** K1 = 1 Start je Dienst im Tagesreport — Test `test_k1_ignores_starts_before_window`
  grün, drei Alt-Starts + ein In-Window-Start ergeben max_starts = 1. Live-Verify wartet auf
  J6 + Day-0-Verify.
- **AK-J4** `measurement_heartbeat.ok == true` am ersten POST_WINDOW — **unverifiziert**, wartet.
- **AK-J5** Prereg v2 committet **vor** der ersten Start-Zeile des neuen Laufs — ✅ dieser Commit
  `6890ac4` ist im Repo, J6 (Restart) ist morgen.
- **AK-Σ** Σ = 1940 ✅ (1934 + 6 neue Tests, exakt nach Plan-Akzeptanz J).

### Nikinger-Aktionen (heute + morgen)

- **Push-Freigabe für 5 Commits lokal ahead** (`7119bcc` + `669dde9` + `3969f8c` + `cae9669` +
  `6890ac4` + dieser Rotation = 6 Commits). Nikinger-Sonderauftrag sagte „Push-Freigabe für
  7119bcc" — die 5 Folge-Commits hängen am selben thematischen Strang (J-Block + Prereg v2)
  und sollten im selben Push mit raus, sonst zerreißt es den Audit-Stand.
- **J4 — Log-Hygiene (morgen, Nikinger-Aktion)**: 4 Wrapper-Logs truncaten mit Backup-Kopie
  daneben, siehe Plan §3 J4 + Runbook-v2 §2.4. Vor J6.
- **J6 — Restart morgen vor 09:00 Berlin** (Nikinger-Aktion) per `PHASE16_E3_RUNBOOK_v2.md` §3
  verbatim. Danach Day-0-Verify (J7, Exec-Session on demand).
- **J6 — Aktiv-Block-Eintrag in Prereg v2** (Nikinger-Aktion, **vor** der ersten Start-Zeile
  im Log): Start-Zeitstempel aus `run_scheduler.log` erste Zeile, Commit
  `phase16: docs -- E1-Aktiv-Block-Eintragung`, Commit-Zeit < Start-Zeile (AK13-Bedingung).

### Open questions / blockers

- **V-4 (Plan §6, aus #21-Block übernommen):** ob der zweite `ok=False`-Zweig
  (`heartbeat.py:142`, `pairs_resolved == 0`) zusätzlich feuert, entscheidet sich erst im
  ersten POST_WINDOW nach J6. Wenn K4 nach J3 nicht grün wird, ist **das** der erste
  Verdächtige, nicht der Fenster-Fix — die `worst_coverage`-Telemetrie im Event zeigt, ob
  J3 allein gewirkt hat.
- **Block H** (Audit-Restbefunde-Reparatur 29+1+1) wartet auf das nächste Wochenende
  (13.–14. Sept. 2026); bleibt **außerhalb** des Trade-Fensters (Lock F5). H-1-Hook-Step-4
  in `scripts/check_doc_rotation.py` (Lock F3 revidiert, kein zweites Skript).
- **Block G** (Tagesroutine G1 + G2) startet mit dem J6-Restart morgen früh. G1 =
  `autonomy_report.py --day YYYY-MM-DD`, G2 = korrigiertes Caps-Pin-Kommando:
  `grep "starting scheduler daemon" data/state/run_scheduler.log | tail -1`
  (nicht `/proc/<pid>/cmdline` — enthält die Caps nicht).
