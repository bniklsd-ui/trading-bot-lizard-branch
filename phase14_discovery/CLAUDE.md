# CLAUDE.md — Phase 14: Discovery-Then-Deterministic (`phase14_discovery/`)

> Zwei Phasen lang war „welche Quelle kann Epic X?" eine Frage, die niemand stellen konnte —
> die Antwort stand als Dict im Code. Phase 14 macht sie zu einer Zeile in der DB.
> **Quelle der Wahrheit ist der Plan + der Code, nicht dieses Dokument.**
> Vollständiger Plan: [`../docs/concepts/phase14_discovery_plan.md`](../docs/concepts/phase14_discovery_plan.md).
> Vorgeschichte: [`../phase13_live_data/PHASE13_CLOSEOUT_HANDOVER.md`](../phase13_live_data/PHASE13_CLOSEOUT_HANDOVER.md) §1.5.
> Spezial-Pläne: [`./PHASE14_C_DAEMON_CWD_BUG_PLAN.md`](./PHASE14_C_DAEMON_CWD_BUG_PLAN.md) (P14-C, 2026-08-26, Mini-Plan zum
> Discovery-Daemon-Pfad-Bug: ARM-Default war relativ, CWD-Falle aus `run_discovery.sh`);
> [`./PHASE14_D_DAEMON_SIGNAL_CAP_PLAN.md`](./PHASE14_D_DAEMON_SIGNAL_CAP_PLAN.md) (P14-D, 2026-08-26, Mini-Plan zum
> Discovery-Daemon-Signal-Response-Bug: `interval_s=3600`-Sleep verschluckt SIGTERM, analog Phase-8-POST_WINDOW);
> [`./PHASE14_E_RECORDER_LOOP_PLAN.md`](./PHASE14_E_RECORDER_LOOP_PLAN.md) (P14-E, 2026-08-28, Mini-Plan zum
> Recorder-Sleep-Cap-Bug + Restart-Loop-Hunt: derselbe Bug wie P14-D, aber in Phase-12-Code; Cross-Phase-Freigabe Phase 12).

## Mission (zuerst lesen)

**Was eine Quelle kann, sagt die Quelle — nicht der Konsument.**

1. **Discovery first.** Jede Quelle exponiert ihr Liefer-Spektrum als `SourceProfile`.
2. **Kreuzung second.** `instrument_source_availability` (Migration 007) hält
   IG-Epic × Quelle × Auflösung — inklusive des **quelleneigenen Symbols**.
3. **Determinism last.** Der Konsument liest die Tabelle und wird dadurch *einfacher*.

**Done-Kriterium:** PASS A1–A8 (Plan §7). Die zwei harten davon:
`grep -rn "EPIC_MAP" phase13_live_data/ --include=*.py` ist **leer**, und Discovery gibt
**strukturell** null IG-Punkte aus (Test mit einem Broker, der bei jedem Call wirft).

## Bauprinzip

„So wenig AI wie möglich, so viel AI wie nötig." **Phase 14 fügt NULL neues AI hinzu.**
Quell-Entdeckung, Symbol-Zuordnung, Verfügbarkeits-Bewertung und Scharfschalt-Logik sind
deterministischer Code. Wer hier ein LLM „Quellen bewerten" oder „Symbole raten" lassen
will → **stop**, das ist Code.

## Scope

- **DRIN:** `source_registry/` (Modelle, Store, Quell-Profile, Scharf-Flag, Daemon),
  Migration 007, die Projektions-Naht in `phase9_universe/universe/store.py::set_symbol`,
  der `stale_source`-Vokabular-Fix in `phase9_universe/universe/models.py`, der
  Symbol-Lookup statt `EPIC_MAP` in `phase13_live_data/live_data/backfill.py`, die
  Drei-Fälle-Trennung in `scripts/source_delta.py`, das Scharfschalten in
  `phase8_scheduler/webui/`.
- **DRAUSSEN:** `measurable_universe()` / `data_source_status` umbauen (D3), `prefer` in
  `BarArchive.window` (D7), Dukascopy (D15), `KNOWN_SOURCES` dynamisch (D17), zentrale
  Quell-Verwaltung (Auth/Rate-Limits bleiben je Quelle), `TickerMapper`-Cache,
  Momentum-VETO/Gates/Sizing/P6/P7, `resolve_paper_trade`, die Phase-13-Beweiswoche
  (separater Track, läuft parallel).

## Rahmen

- **Werktags-Arbeit erlaubt, auch bot-berührend.** Vorher den Bot stoppen,
  `ps aux | grep scheduler.run` als Gegenprobe (Parallel-Login-Falle).
- **Live-/Netz-/kostenpflichtige Läufe macht der Nikinger.** Befehl vorbereiten, Kosten
  nennen, vorher fragen. In Phase 14 sind das genau zwei: die Capital.com-`/markets`-Probe
  (B1a, Demo, kostenlos) und die Migration 007 gegen die Produktions-DB (mit Backup).
- **Live-DB nur `mode=ro`.**
- **Cross-Phase-Edits sind für Phase 14 freigegeben** (Nikinger 2026-08-22) für **Phase 2**
  (Migration), **Phase 8** (`webui/`, `run_scheduler.sh`), **Phase 9** (`models.py`,
  `store.py`), **Phase 12** (`budget.py`-Nutzung) und **Phase 13** (`backfill.py`,
  `scripts/`). Ein Touch **außerhalb** dieser Liste ist erneut freigabepflichtig.
- **Ausführungs-Sessions laufen über `claude-minimax`** (Kostengrund, Nikinger 2026-08-18),
  Debugging über `claude`. Ändert **nicht**, welches Modell der Bot selbst ruft.

## Der Kontingent-Deckel (dreifach, Plan §4 D6/D13/D14)

Die Frage „wie verhindern wir, dass Discovery das Kontingent sprengt" ist mit drei Lagen
beantwortet, von wichtig nach unterstützend:

1. **Strukturell.** Discovery ruft **nie** `/prices` und **nie** `search_markets`. Die
   IG-Zeile wird aus `instrument_universe` **abgeleitet** — jede Zeile dort *ist* per
   Definition eine IG-Epic. Der Beweis ist ein Test mit einem Broker-Fake, dessen jede
   Methode wirft (Muster L12 / `test_get_window_never_fetches`), **kein** Zählwert.
2. **Zwei Kontingente, nicht eins.** Das 10 000-Punkte-Kontingent (`/prices`, rollierende
   7 Tage) hat Phase 11 gesprengt; das API-Key-Kontingent (~30 req/min, 403
   `exceeded-api-key-allowance`) hat Phase 9 gesprengt (`discovery.py:183-189`, Pacing
   1,0 s → 2,5 s). Discovery berührt **keins von beiden**, weil sie IG gar nicht ruft.
3. **Deckel für alles, was doch fetcht** — heute nur Capital.com (Demo, kostenlos):
   `max_probe_calls_per_source_per_run=8`, TTL `profile_ttl_days=7` gegen
   `last_verified_utc`, und jede Ausgabe gebucht als `spend_kind='discovery'` im
   existierenden `source_spend`-Ledger (Muster `GapRescue`s `'rescue'`). Sichtbar statt
   unsichtbar.

Dazu kommt der Betriebs-Deckel: der Daemon tut **nichts**, solange
`data/state/DISCOVERY_ARMED` fehlt (D10) — die sichere Richtung jeder Mehrdeutigkeit ist
**nicht scharf**. Unscharf kostet null.

## Modul-Tabelle

> **Stand: 2026-08-31 — Mini-Session 21.** Block-D-Schließung: Tabelle gegen den
> As-Built-Stand gefüllt (Testzahlen aus dem finalen Sweep dieser Session, nicht
> geschätzt — `pytest phase14_discovery/tests --collect-only -q` reproduziert die
> Einzelzahlen, Σ = 61 für Phase 14). Cross-Phase-Tests stehen bei der Eigentümer-
> Phase (P2/P8/P9/P13), nicht hier — die Spalte zeigt den Beitrag, den Phase 14
> an der jeweiligen Suite hat (Phase-13-Backfill z. B. wird in P13 getestet, nicht
> hier).

| Datei | Zweck | Status | Tests |
|---|---|---|---|
| `source_registry/models.py` | `SourceAvailability`, `SourceProfile`, `Source`-Protocol, `origin`-Vokabular | ✅ A2/A3 (gelockt in Phase-13-Session 4) | *(in test_store, test_sources)* |
| `source_registry/store.py` | `SourceAvailabilityStore` — der einzige Zugriff auf Migration 007 | ✅ A2 | 13 (test_store.py) |
| `source_registry/sources.py` | `IGDerivedSource`, `LSStaticSource`, `RegistryYFSource` — alle drei ohne Netz | ✅ A3 | 9 (test_sources.py) |
| `source_registry/arm.py` | Scharf-Flag `data/state/DISCOVERY_ARMED` (Muster `killswitch.py`, sichere Richtung umgedreht) | ✅ C1 (Session 9) | 21 (test_arm.py) |
| `source_registry/run.py` | Der Daemon (Muster `data_foundation/run.py`: PID-File, graceful SIGTERM, `--once`) | ✅ C2 (Session 9) | 18 (test_run.py) |
| `scripts/run_discovery.sh` | Start-Wrapper (Muster `run_recorder.sh`) | ✅ C4 (Session 9) | — (Bash-Wrapper, kein Python-Test) |
| *(cross-phase)* `phase2_persistence/migrations/007_phase14_source_availability.sql` | die Kreuzungs-Tabelle **+ der einmalige yF-Backfill aus `instrument_universe`** (der Grundbestand kommt aus der Migration, nicht aus einem Resolver-Lauf — `resolve_epic` ruft `set_symbol` in sechs von acht Pfaden nicht) | ✅ A2 | Migration-007-Tests leben in `test_store.py` (2 Tests, Idempotenz + Backfill-Reproduktion des heutigen Substrats); Eigentümer-Suite P2 unverändert |
| *(cross-phase)* `phase9_universe/universe/models.py` | `DS_STALE_SOURCE` ins Vokabular (Live-Blocker B1) | ✅ A1 | +1 Regressionstest in `phase9_universe/tests/test_store.py` (vom Plan A1 gefordert); Eigentümer-Suite P9 87 grün |
| *(cross-phase)* `phase9_universe/universe/store.py` | yF-Projektion in `set_symbol`, nicht-fatal | ✅ A4 (Session 7) | +6 Tests in `phase9_universe/tests/test_store.py` (Bit-Identität mit `SourceAvailabilityStore.upsert`, messbarer_substrat-byte-gleich, …); Eigentümer-Suite P9 unverändert |
| *(cross-phase)* `phase13_live_data/live_data/backfill.py` | `CapitalSource.discover()` (B1b); `EPIC_MAP` raus + Symbol-Lookup rein (B2) | ✅ B1b + B2 (Session 8) | +4 Tests in `phase13_live_data/tests/test_backfill.py` (gemockt, kein Netz); `grep -rn "EPIC_MAP" phase13_live_data/ --include=*.py` ist **leer** (Akzeptanz A2) |
| *(cross-phase)* `phase13_live_data/scripts/probe_capital.py` | CFD-Filter-Bug Fix: `"CFD"`-Substring → exakt `"INDICES"`; neuer Helper `_pick_index_match` für Testbarkeit | ✅ Cross-Phase-Hygiene (Session 7) | Tests in `phase13_live_data/tests/test_probe_capital.py` (Eigentümer-Suite P13 74 grün) |
| *(cross-phase)* `phase13_live_data/scripts/source_delta.py` | drei Fälle statt zwei (`not_available` / `available_but_empty` / `compared`) | ✅ B3 (Session 8) | +4 Tests in `phase13_live_data/tests/test_source_delta.py`; Eigentümer-Suite P13 unverändert |
| *(cross-phase)* `phase8_scheduler/webui/api.py` + `static/` | `GET /api/discovery`, ARM/DISARM, Warn-Banner | ✅ C3 (Session 9) | +4 Tests in `phase8_scheduler/tests/test_webui.py` (inkl. fail-soft ohne Tabelle 007); Eigentümer-Suite P8 248 grün |
| *(cross-phase)* `phase8_scheduler/scripts/run_scheduler.sh` | Autostart-Hook für `run_discovery.sh` (analog Recorder) | ✅ C4b (Session 9) | — (Bash-Wrapper, kein Python-Test) |

### Σ-Sweep Phase-14 Suite (Mini-Session 21, 2026-08-31, selbst nachgemessen)

| Test-Datei | Tests | As-Built-Zweck |
|---|---:|---|
| `test_store.py` | **13** | A2-Akzeptanz (Migration 007 + Store-Kontrakte); inkl. Backfill-Reproduktion des heutigen Substrats + Idempotenz |
| `test_sources.py` | **9** | A3-Akzeptanz (drei Quell-Profile strukturell ohne Netz); **Test 2 ist das A1-Akzeptanzkriterium (Broker-Fake, dessen jede Methode wirft)** |
| `test_arm.py` | **21** | C1-Akzeptanz (Scharf-Flag fehlend/leer/kaputt/`false` ⇒ alle False; Round-Trip; atomare Schreibung) |
| `test_run.py` | **18** | C2-Akzeptanz (Daemon unscharf/scharf/stale/werfend/probe_calls_used/ **+ 1 P14-D-Test** = CAP-on-Stop) |
| **Σ Phase 14** | **61** | (= Σ-Sweep Stand Session 20 / 21 unverändert; Mini-Session 21 brachte **0** neue Tests) |

Cross-Phase-Σ (relevant für Phase 14, Stand Mini-Session 21):

| Phase | Tests grün | Δ zu Session 20 |
|---|---:|---|
| P8 (Scheduler) | 248 | unverändert |
| P9 (Universe) | 87 | unverändert |
| P10 (V3) | 165 | unverändert |
| P12 (Datenfundament) | **145** | unverändert (P14-E-Test-Fix räumte das einzige Wanduhr-Fail vor 09:00 CEST auf, keine Test-Änderung an der Zahl) |
| P13 (Live-Datenfundament) | 74 | unverändert |
| **P14 (Discovery)** | **61** | **unverändert** |

---

## Session stopped — 2026-08-31 (Mini-Session 21: VM-Migrations-Check + Doku-Hygiene + P14-E-Test-Fix + D3-Korrekturnotiz, 3 Commits, 1 Operator-Aktion)

> **Auftrag:** Nikinger-Chat (2026-08-31, ~07:50 CEST) auf Phase-14-Wiederaufnahme
> nach VM-Migrations-Bedenken (Stichwort: Keyring) → „Fange mit deinen genannten
> ersten Schritt an". Scope: **drei Mini-Session-21-Commits** (Doku + Test) + **eine
> Operator-Aktion** (Daemons per `restart-services.sh start` reaktivieren, weil sie
> zwischen 2026-08-29 11:27 UTC (letzter Discovery-Cycle) und heute stillschweigend
> nicht mehr liefen) — exakt der Plan, keine Scope-Erweiterung.

### Completed

**1. VM-Migrations- und Keyring-Check (Schritt 0, vor jedem Phase-14-Edit):**
- **Keyring (SecretService via gnome-keyring-daemon):** ✅ 11 Einträge lesbar (Login-Collection unlocked), inkl. `tradingbot/ig_demo_{username,password,api_key,account_id}`, `trading-bot-capital/{api_key,identifier,password}`, `openrouter/api_key`, `trading-bot-minimax/minimax_api_key`. Phase-1 `check_credentials` returns `True` für alle 4 IG-Demo-Keys; Werte lesbar (`Dem***` len=12, `eb3***` len=41). **Kein** Keyring-Migrations-Schaden.
- **DB-Substrate:** ✅ `trading_bot.sqlite` (`_schema_version=7`, Migration 007 angewendet) + `bars.sqlite` (6.6 MB, Archiv intakt); `instrument_universe=22`, `instrument_source_availability=38` (8 ig + 8 ls + 22 yF).
- **WebUI:** ✅ PID 3304 alive, port 8000; `/api/discovery` returns `armed:true, rows_total:38, stale_rows:14`.
- **Drei Daemons (Scheduler, Discovery, Recorder):** 🟡 **DEAD** zum Session-Start. Letzter Discovery-Cycle war 2026-08-29 11:27 UTC; die PIDs aus Session 20 (47166/47174/111151) sind weg. Mögliche Ursache: Reboot während Offline-Intervall, oder Operator-seitiger Stop ohne Re-Start. **Schritt-2-Operator-Aktion unten.**

**2. Operator-Aktion (Restart-Hygiene):** `bash scripts/restart-services.sh start` →
- Recorder **PID 7711** — alive, Heartbeat `2026-08-31T05:54:47Z` (fresh).
- Discovery **PID 7725** — alive, ARMED, Heartbeat `2026-08-31T05:54:49Z`.
- Scheduler **PID 7735** — alive, Preflight-Pass (kein Keyring-Error im Log).
- WebUI **PID 3304** — already alive, skip (Refuse-Double-Start).

**3. Commit 1 — P14-D §10 Korrekturnotiz (Doc-only):** `phase14_discovery/PHASE14_D_DAEMON_SIGNAL_CAP_PLAN.md`
- neuer §10-Abschnitt „D3-Auto-Reload-Claim ist falsch" (~110 Zeilen, analog Mutterplan §11.3 + P14-E §2 D3-Korrekturnotiz): D3 war die Annahme, ein laufender Daemon lade Code-Edits beim nächsten Cycle automatisch. **Falsch** — Python speichert die geladene Klasse in `sys.modules`; ein `.py`-Edit wirkt **nicht** auf einen laufenden Prozess.
- Inline-Korrektur-Marker an den vier verstreuten Stellen (§0 BLUF, §1 Rahmen, §2 D3-Zeile, §5 Akzeptanz): ~~gestrichen~~, mit 🟡-Hinweis auf §10.
- `updated:` im Header von `2026-08-26` → `2026-08-26 (+ §10 Korrekturnotiz D3-Auto-Reload-Claim 2026-08-31, Mini-Session 21)`.
- Empirischer Beweis (in §10.3 zitiert): Session-20-PID 108966 (Recorder, alter Code) reagierte auf SIGTERM erst nach 120 s; PID 111032 (Recorder, neuer Code, nach Neustart) reagierte in ≤ 1 s.
- **Commit:** `362f4b9 phase14: docs -- P14-D §10 Korrekturnotiz (D3 Auto-Reload-Claim falsch, 2026-08-31, Mini-Session 21)` (+105/-5).

**5. Commit 2 — P14-E Test-Fix (Cross-Phase Phase-12, Code+Test):** `phase12_data_foundation/tests/test_recorder.py`
- die zwei in Session 20 neu hinzugekommenen P14-E-Tests (`test_run_forever_exits_within_signal_check_interval_on_request_stop`, `test_run_forever_chunks_large_interval_safely`) bauen den Recorder direkt auf (ohne den `_recorder`-Fixture-Helper, der bereits `market_open=True` als Default hat) und erben damit die Default-`market_open_fn=_default_market_open`, die die Wanduhr liest.
- Konsequenz: vor XETRA-Markteröffnung (09:00 Europe/Berlin) macht `tick()` `skipped_off_hours=True` und ruft `get_bars()` nicht auf — der Test schlägt fehl mit `assert 0 == 1`. Heute Morgen um 07:52 CEST (= 1:08 vor Marktöffnung) **empirisch reproduziert**.
- Fix: `market_open_fn=lambda: True` in beiden Recorder-Konstruktor-Aufrufen. Pattern identisch zum bestehenden `test_request_stop_ends_run_forever`, der den `_recorder`-Helper mit `market_open=True` (Default) verwendet.
- Cross-Phase-Touch Phase-12-Test: bereits in Session 20 von Nikinger via `PHASE14_E_RECORDER_LOOP_PLAN.md` sign-off freigegeben. Mini-Session 21 ist eine Korrektur an demselben Touch, kein neuer Cross-Phase-Edit.
- **Akzeptanz:** `pytest phase12_data_foundation/tests -q` → **145 grün** (Baseline 143 + P14-E 2); alle 11 test_recorder-Tests PASSED, inkl. `test_off_hours_is_a_no_op_no_fetch` (das mit `market_open=False` explizit den Off-Hours-Pfad prüft).
- **Commit:** `98cac57 phase12: test -- Recorder market_open_fn in P14-E tests (deterministic, Mini-Session 21)` (+2).

**6. Commit 3 — Phase-14-CLAUDE.md Modul-Tabelle (Block-D-Schließung, Doc-only):** `phase14_discovery/CLAUDE.md`
- `Stand: 2026-08-22 — Session 9` → `Stand: 2026-08-31 — Mini-Session 21` (Block-D-Schließung, Doku-Hygiene).
- Neue Spalte `Tests` mit der jeweiligen `test_<modul>.py`-Zahl (13 + 9 + 21 + 18 = 61 für Phase 14).
- Cross-Phase-Zeilen erklären explizit, dass die Tests bei der Eigentümer-Phase leben (P2/P8/P9/P13), nicht hier.
- Neue Sub-Tabelle „Σ-Sweep Phase-14 Suite" mit der per-Test-Datei-Aufschlüsselung.
- Neue Cross-Phase-Σ-Tabelle mit den für Phase 14 relevanten Suiten (P8 248, P9 87, P10 165, P12 145, P13 74, P14 61); Delta zu Session 20 überall „unverändert" — Mini-Session 21 brachte 0 neue Tests.
- **Commit:** `b16aea8 phase14: docs -- Modul-Tabelle auf As-Built-Stand (Block-D-Schließung, Mini-Session 21)` (+45/-19).

**7. Doc-Rotation (gemäß Doc-Layers-Konvention):**
- Session 20 verbatim von `phase14_discovery/CLAUDE.md` (Z. 137–253) ins `SESSIONS_ARCHIVE.md` (oben, vor Session 19) verschoben.
- Phasenkopf trägt jetzt genau einen `## Session stopped`-Block (Session 21).
- Pre-Commit-Hook (`scripts/check_doc_rotation.py`) war beim Commit-2 nicht aktiv (Doc-Commit, kein Trigger); für Commit 3 + Doc-Rotation separat grün geprüft.

### Σ-Sweep Stand 2026-08-31 ~06:00 UTC (Mini-Session 21, selbst nachgemessen):

| Phase | Tests grün | Δ zu Session 20 |
|---|---:|---|
| P1 (Broker Wrapper) | 95 | unverändert |
| P2 (Persistence) | 77 | unverändert |
| P3 (External Data) | 104 | unverändert |
| P4 (Research) | 155 | unverändert |
| P5 (Execution) | 173 | unverändert |
| P6 (Debate) | 76 | unverändert |
| P7 (Reward) | 138 | unverändert |
| **P8 (Scheduler)** | **248** | unverändert |
| **P9 (Universe)** | **87** | unverändert |
| P10 (V3) | 165 | unverändert |
| **P12 (Datenfundament)** | **145** | **unverändert** (P14-E-Test-Fix räumte das einzige Wanduhr-Fail vor 09:00 CEST auf, **keine** Test-Zahl-Änderung — 145 war schon der Session-20-Stand) |
| **P13 (Live-Datenfundament)** | **74** | unverändert |
| **P14 (Discovery)** | **61** | unverändert |
| meta_m1_harness | 28 | unverändert |
| root tests/ | 94 | unverändert |
| **Σ** | **1698** | unverändert |

(Phase-14-intern: 13 + 9 + 21 + 18 = **61**; per-Test-Datei-Aufschlüsselung in der Modul-Tabelle.)

### Live-Prozess-Stand 2026-08-31 ~06:00 UTC (Mini-Session 21):

| PID | Prozess | etime | Status |
|---|---|---|---|
| **7711** | `python -m data_foundation.run` | ~5 min | **alive (Restart in dieser Session)**, schreibt `recorder_state.json` 05:54:47Z |
| **7725** | `python -m source_registry.run` | ~5 min | **alive (Restart)**, ARMED, `discovery_state.json` 05:54:49Z |
| **7735** | `python -m scheduler.run --enable-shadow-schedule --enable-divergence-sampler` | ~5 min | **alive (Restart)**, Preflight ✓ |
| 3304 | `uvicorn webui.api:app` | 1h 15m | alive (war schon alive vor Mini-Session 21, kein Restart nötig) |

### Findings

🟢 **VM-Migration war unspektakulär:** Keyring, DBs, WebUI, Git-Stand, Pre-Commit-Hook alle grün. Die einzige „Schäden" waren die drei gestoppten Daemons, was ein Operator-seitiger Restart-Hygiene-Punkt ist, **kein** Migrations-Defekt.

🟢 **P14-E-Test-Wanduhr-Anfälligkeit gefixt:** deterministisch zu jeder Wanduhr-Zeit. Pattern identisch zum älteren `test_request_stop_ends_run_forever` (der den Helper verwendet); Minimal-Diff (2 Zeilen).

🟢 **P14-D Plan §10 Korrekturnotiz:** schließt die letzte Lücke aus Session 20 („Folge: P14-D Plan §2 D3 ebenfalls falsch; muss in einer Folgesession revidiert werden"). Auto-Reload-Claim ist jetzt **vier Mal** im Plan mit 🟡-Marker gestrichen + vollständig in §10 erklärt; Cross-Refs zum Mutterplan §11.3 + P14-E-Plan §2 D3 + Phase-12-CLAUDE.md Rahmen.

🟢 **Block-D-Schließung der Modul-Tabelle:** Tabelle hat jetzt `Tests`-Spalte + Σ-Sweep-Tabelle; Plan-Vorgabe „Testzahlen aus dem finalen Sweep, nicht geschätzt" ist erfüllt. As-Built-Stand 2026-08-31.

🟡 **Doc-Rotation-Hygiene:** Pre-Commit-Hook (Session 17) hat Session-21-Doc-Rotation **nicht** automatisch geprüft (er checkt nur den Phasenkopf-Block, nicht die Archiv-Bewegung selbst). Die Rotation wurde manuell verifiziert (`grep -c '^## Session stopped' phase14_discovery/CLAUDE.md == 1` ✓ + SESSIONS_ARCHIVE.md hat Session 20 + 19 + 18 + …). Für die nächste Session: Doc-Rotation als Pre-Commit-Hook-Schritt 2 (auch die „vorher ins Archiv" verifizieren) — out-of-scope heute.

### Unverändert offen (von Session 17/18/19/20, weiter gültig)

- **Phase-14 D5 Closeout-Handover** — wartet auf Phase-13-Beweiswoche.
- **Phase-15-Plan-Session** (V4: Council / Handover / Reward-Reform / Force-Trigger / Instinct-ECC) — gegatet auf Outcomes aus Phase 9+11+12+13+14.
- **Hook-Installer (tracked)** — Skript gebaut, Operator-seitige Installation fertig, die **tracked**-Variante (Option 1/3) bleibt offen. **Heute mit höherer Priorität:** Doc-Rotation-Hook-Schritt-2 (siehe Findings).
- **Phase-12-Reconciliation-Timing-Fix** — `reward.recorder: no usable history row`-Vorkommen laufen weiter (P10-V3-Code, nicht in Phase 14/Recorder-Sleep-Cap-Scope). **Jetzt** mit höherer Priorität — der Recorder schreibt zuverlässig (P14-E-Fix), aber die CRITICAL-Logs laufen weiter.
- **Phase-11-Wiederaufnahme** (WI-2/W2) — Datenfundament-Abhängigkeit.

### NEXT (für die nächste Session / morgen)

**Nikinger-Anweisung zum Session-Ende wird erwartet** (Stand ~06:00 UTC = 08:00 CEST — noch nicht formuliert, warte auf Nikinger-Wahl).

**Konkrete Empfehlung (sortiert nach Aufwand × Impact, kann der Nikinger umstellen):**

1. **Doku-Updates synchronisieren** (~10 Min): root-`CLAUDE.md` Phase-14-Zeile auf Mini-Session-21-Stand; `ROADMAP.md` Phase-14-Block ggf. Datum der letzten Code-Aktivität; `docs/INDEX.md` Mini-Session-21-One-Liner (optional). Reine Status-Pflege, kein Code.
2. **Phase-13-Beweiswoche-Auswertung** (~30 Min): `phase13_live_data/scripts/source_delta.py` für Mo 25.08. – heute → entscheidet D5-Handover oder Befunde.
3. **Tracked Hook-Installer mit Doc-Rotation-Schritt-2** (~1h): das Session-17-Skript (`scripts/install_hooks.sh`) um den „vorher ins Archiv"-Check erweitern, dann tracked-Commit.
4. **Phase-12-Reconciliation-Timing-Fix** (~2-3h, Phase-12-Code): die anhaltenden `reward.recorder: no usable history row`-CRITICALs angehen. **Jetzt** mit höherer Priorität — der Recorder schreibt zuverlässig (P14-E-Fix), aber die CRITICAL-Logs laufen weiter.
5. **Phase-15-Plan-Session** (großer Block): wenn die Beweiswoche genug Outcomes für die V4-Gegenargumente liefert, **jetzt** starten.

**Heutige Abend-Sequenz:** gemäß P14-D §10-Korrekturnotiz ist nach Recorder-Code-Edits IMMER Operator-Restart nötig. Wenn der Phase-12-Reconciliation-Timing-Fix (#4) heute Abend live geht, sind `restart-services.sh restart` (oder die per-Daemon-Wrapper mit `kill -TERM → 60s → kill -KILL`) die einzigen gangbaren Pfade.


---

> **Ältere Session-Blöcke** (verbatim ausgelagert, newest-first): [SESSIONS_ARCHIVE.md](./SESSIONS_ARCHIVE.md) — Rotation per Doc-Layers-Konvention ([docs/DOC_LAYERS_CONVENTION.md](../docs/DOC_LAYERS_CONVENTION.md)).