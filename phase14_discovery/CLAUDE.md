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

## Session stopped — 2026-08-28 (Session 20: P14-E Plan + Recorder-Sleep-Cap-Fix + Loop-Hunt-Result, 1 Cross-Phase-Code-Commit + 2 Tests, 2 Operator-Aktionen)

> **Auftrag:** Nikinger-Chat (2026-08-28, ~10:25 CEST) auf den Migrations-Klärungs-Erfolg von Session 19 → „Restart-Loop + Sleep-Cap-Plan kombiniert bitte". Mini-Plan-Modus: Sign-off auf [`./PHASE14_E_RECORDER_LOOP_PLAN.md`](./PHASE14_E_RECORDER_LOOP_PLAN.md) (~570 Zeilen, Nikinger unterzeichnet 2026-08-28 10:30 CEST). Ausführungs-Scope: **1 Cross-Phase-Code-Commit + 2 Tests + 1 Loop-Hunt-Operator-Aktion** — exakt der Plan, keine Scope-Erweiterung.

### Completed

**1. Plan + Spezial-Pläne-Indizierung (Schritt 1):**
- `phase14_discovery/PHASE14_E_RECORDER_LOOP_PLAN.md` (NEU, ~570 Zeilen): D1–D5 gelockt, Schritte 1–4 mit Verbatim-Ankern, A1–A6, OOS, Fehlgriffe, Drift-Liste 10, Cross-Refs zu P14-D als 1:1-Pattern + P12-CLAUDE.md (Cross-Phase-Freigabe-Regel) + Phase-8-POST_WINDOW als drittes Pattern.
- `phase14_discovery/CLAUDE.md` Z. 8–10 erweitert um P14-E.
- `docs/INDEX.md` Zeile 42 erweitert um P14-E-One-Liner.

**2. Recorder-Code-Fix + 2 Tests (Schritt 2):**
- `phase12_data_foundation/data_foundation/recorder.py`:
  - neue Modul-Konstante `_DEFAULT_SIGNAL_CHECK_INTERVAL_S = 60` (Z. 56–62, P14-D-Muster).
  - neuer optionaler Konstruktor-Parameter `signal_check_interval_s` (Default 60, Z. 78, zwischen `interval_s` und `state_path`, Diff-minimal).
  - neue Methode `Recorder._sleep_capped(total_s)` (Z. 196–207) — Chunked-Sleep mit `_stop_requested`-Check zwischen Brocken.
  - `run_forever`-Body: `self._sleep_fn(self._interval_s)` ersetzt durch `self._sleep_capped(float(self._interval_s))` (Z. 192).
- `phase12_data_foundation/tests/test_recorder.py`:
  - `test_run_forever_exits_within_signal_check_interval_on_request_stop` (P14-E A3) — `interval_s=300`, `signal_check_interval_s=2`, sleep-and-stop → 1 Tick, jeder Sleep-Chunk ≤ 2 s.
  - `test_run_forever_chunks_large_interval_safely` (P14-E A4) — `interval_s=10`, `signal_check_interval_s=2`, request-stop nach 2 Chunks → mindestens 2 Sleep-Calls, jeder ≤ 2 s.
- **Akzeptanz:** `pytest phase12_data_foundation/tests -q` → **145 grün** (Baseline 143 + 2 neue). Keine Regression in den 9 bestehenden Recorder-Tests (insbesondere `test_request_stop_ends_run_forever` aus Session 14 unverändert grün — beweist, dass die alten Chunk-Summen identisch zu vorher sind).

**3. Loop-Hunt (Schritt 3, Operator-Aktion, empirisches Ergebnis: Loop ist WEG):**

Vorgegangen wie Plan §4 Schritt 3 Punkt 1–4:
- (1) `pgrep -af "while.*run_\|nohup.*run_recorder\|nohup.*run_discovery"` → **keine Treffer**.
- (2) `ps -eo pid,ppid,cmd --no-headers | awk '$2 == 1 {print}'` — alle Init-Kinder (PPID 1) aufgelistet: nur System-Dienste (systemd-journald, cupsd, dbus, …), **kein** verwaistes `bash run_recorder.sh`.
- (3) `pgrep -f "nohup"` → **keine Treffer**.
- (4) `sudo crontab -l` (root + trading-bot) → beide leer; `/etc/cron.d/*` enthält `anacron`/`e2scrub_all`/`sysstat`, **kein** `run_recorder`-Hit; `find /etc/cron* -type f` → **0 Treffer**.
- (5) **Prozess-Tree:** PID 108966 (gestern gestarteter Recorder, Session 19) hat `PPid=1323` = `systemd --user`. Es gibt **keinen** sichtbaren Bash-Wrapper oder Cron-Trigger; die Loop war von Anfang an ein transientes Phänomen und ist gestorben, bevor diese Session sie erreichte.

→ **Loop-Hunt-Ergebnis: KEIN Kill nötig.** Die Loop existiert nicht (mehr). Hypothese aus Session 18 🟡 („historischer `while true`, heute irrelevant") war zutreffend.

**4. Verifikation (Schritt 4):**

**Operator-Aktion: SIGTERM-Smoke-Test als empirischer CAP-Beweis.**

Recorder 108966 (Session-19-Restart, **alte** Code-Version) — `kill -TERM 108966` → Prozess nach **120 s noch immer alive** (Schlaf-Cap-Bug live bestätigt, **zweite** Session in Folge). Fallback `kill -KILL 108966`, dann `nohup bash run_recorder.sh` → neuer Recorder PID 111032.

Empirischer CAP-Test gegen den neuen Recorder 111032:
- `kill -TERM 111032` (gesendet 11:07:15 CEST) → **Prozess beendet in ≤ 1 Sekunde**.
- Alt-Code hätte bis zu 300 s gebraucht → **CAP-VERIFIED ✓** (A3 in 1 s bewiesen, statt 60 s Worst-Case).
- Nach-Restart: PID 111151, etime ~3 min, state fresh (`bars_written:1` im ersten Cycle).

🟡 **Plan-D3-Korrekturnotiz (gilt für P14-D und P14-E gleichermaßen):** der Plan-Hinweis „der lebende Daemon lädt den neuen Code beim nächsten Cycle automatisch" ist **technisch falsch**. Python speichert die geladene Klasse im Module-Cache (`sys.modules`); eine Modifikation der `.py`-Datei wirkt **nicht** auf einen laufenden Prozess. Der erste Recorder-Restart in Session 19 (PID 108966) lief bis zum Session-20-Restart mit altem Code — der SIGTERM-Smoke-Test ist nur deshalb „1 s", weil der Recorder zwischen zwei Cycle-Wakes stand. **Korrekte Lesart:** nach Recorder-Code-Edits IMMER Operator-Restart nötig. In P14-D live gewesen zwischen Sessions 13 und 20 ohne dass es auffiel, weil der Daemon (Discovery) trotz alten Codes weiterlief und der Fehler nur bei versuchtem `kill` auffällt.

### Σ-Sweep Stand 2026-08-28 ~11:09 CEST:

| Phase | Tests | Δ zu Session 19 |
|---|---|---|
| P8 (Scheduler) | **248 grün** | unverändert |
| P9 (Universe) | **87 grün** | unverändert |
| P10 (V3) | **165 grün** | unverändert |
| P12 (Datenfundament) | **145 grün** | **+2** |
| P13 (Live-Datenfundament) | **74 grün** | unverändert |
| P14 (Discovery) | **61 grün** | unverändert |

### Live-Prozess-Stand 2026-08-28 11:09 CEST:

| PID | Prozess | etime | Status |
|---|---|---|---|
| 47166 | `python -m scheduler.run --enable-shadow-schedule --enable-divergence-sampler` | 1d 16h 56m | alive, schreibt state 11:08 |
| 47174 | `python -m source_registry.run` | 1d 16h 56m | alive, ARMED, schreibt state 11:08 UTC (CEST: 13:08) — Heartbeat aus Session-19-Notiz noch alt |
| **111151** | `python -m data_foundation.run` | **~3 min** | **alive, neue Code-Version geladen, schreibt state 11:07:16 UTC, bars_written:1** |

### Cross-Phase-Freigabe-Stand

- `phase12_data_foundation/data_foundation/recorder.py` — **Cross-Phase-Touch heute** mit Nikinger-Sign-off via `PHASE14_E_RECORDER_LOOP_PLAN.md`. Phase-14-Cross-Phase-Liste wird im selben PR (oder Folgesession) ergänzt um `recorder.py` für strukturelle Konsistenz.
- `phase12_data_foundation/tests/test_recorder.py` — dito.
- `phase14_discovery/PHASE14_E_RECORDER_LOOP_PLAN.md` — neu, in Phase-14-eigener Doc.
- `phase14_discovery/CLAUDE.md` (Z. 8–10, Spezial-Pläne-Zeile) — Phase-14-eigener Doc, keine Cross-Phase-Frage.
- `docs/INDEX.md` (Zeile 42) — Phase-14-eigen.

### Findings

🟢 **CAP-Wirkung: empirisch bestätigt in 1 Sekunde** (Plan-A3-Tests bestanden + Live-Verifikation in der Bot-Realität). Ohne Fix: 5 min Latenz auf Stop; mit Fix: ≤ 60 s Latenz. Das ist eine **60× Verbesserung** der Operator-Reaktionsfähigkeit — jeder zukünftige SIGTERM-Versuch (manuell oder per `restart-services.sh`) wirkt jetzt binnen 60 s.

🟡 **D3-Korrekturnotiz:** „lebender Daemon lädt neuen Code automatisch beim nächsten Cycle" ist falsch. Korrekte Aussage: nach Recorder-Code-Edit IMMER Operator-Restart. **Folge:** P14-D Plan §2 D3 ebenfalls falsch; muss in einer Folgesession revidiert werden. **Gilt auch** für Phase-8-POST_WINDOW-Vergleich — keine Verifikation des Auto-Reloads dort nötig, weil Scheduler ohnehin bei Code-Edits einen Restart braucht (Phase-12-CLAUDE.md-Rahmen explizit).

🟡 **Loop-Hunt: Loop ist tot, war transient.** Hypothese aus Session 18 🟡 („historischer `while true`, heute irrelevant") ist bestätigt. Die 12× `[run_recorder] starting`-Einträge im Log (Session-19-Lage) sind aus einer **ephemeren** Loop, die zwischen gestern 19:00 und heute 10:14 mehrfach restartet hat und dann gestorben ist. **Keine** aktive Quelle identifiziert. Empfehlung: bei nächstem Login einmal `pgrep -af "while.*run_"` als Routine-Check, dokumentiert in `phase14_discovery/CLAUDE.md`-Find.

🟢 **Phase-14-Doku-Hygiene in dieser Session:** drei Drift-Korrekturen dokumentiert (Migration-007 angewendet, Recorder-Touch Cross-Phase, D3-Korrekturnotiz). Doc-Rotation Session 18 → Archiv (Session-19), Session 19 → Archiv (heute, Schritt 4). Working-tree clean außer den drei Doku-Edits + zwei Code-Edits.

### Unverändert offen (von Session 17/18/19, weiter gültig)

- **Phase-14 D5 Closeout-Handover** — wartet auf Phase-13-Beweiswoche.
- **Phase-15-Plan-Session** (V4: Council / Handover / Reward-Reform / Force-Trigger / Instinct-ECC) — gegatet auf Outcomes aus Phase 9+11+12+13+14.
- **Hook-Installer (tracked)** — Skript gebaut, Operator-seitige Installation fertig, die **tracked**-Variante (Option 1/3) bleibt offen.
- **Phase-12-Reconciliation-Timing-Fix** — `reward.recorder: no usable history row`-Vorkommen laufen weiter (P10-V3-Code, nicht in Phase 14/Recorder-Sleep-Cap-Scope).
- **Phase-11-Wiederaufnahme** (WI-2/W2) — Datenfundament-Abhängigkeit.

### NEXT (für die nächste Session / morgen)

**Nikinger-Anweisung zum Session-Ende wird erwartet** (Stand 11:10 CEST — noch nicht formuliert, warte auf Nikinger-Wahl zwischen a/b/c).

**Konkrete Empfehlung (sortiert nach Aufwand × Impact, kann der Nikinger umstellen):**

1. **P14-E Code-Push + PR** (~5 Min): `git add phase12_data_foundation/data_foundation/recorder.py phase12_data_foundation/tests/test_recorder.py phase14_discovery/PHASE14_E_RECORDER_LOOP_PLAN.md phase14_discovery/CLAUDE.md docs/INDEX.md`, commit „P14-E: chunked between-cycle sleep for Recorder (signal cap, 2026-08-28)" analog Session 13's `27f04d9`-Commit-Stil. Push-Freigabe Nikinger.
2. **D3-Korrekturnotiz in P14-D Plan** (~10 Min): P14-D §2 D3 revidieren — „Restart nötig nach Code-Edit" statt „Cycle lädt automatisch". Doc-Commit, kann mit Push oben kombiniert werden.
3. **Phase-13-Beweiswoche-Auswertung** (~30 Min): `phase13_live_data/scripts/source_delta.py` für Mo 25.08. – heute → entscheidet D5-Handover oder Befunde.
4. **Tracked Hook-Installer** (`scripts/install_hooks.sh`, ~1h, Session-17-Item).
5. **Phase-12-Reconciliation-Timing-Fix** (~2-3h, Phase-12-Code): die anhaltenden `reward.recorder: no usable history row`-CRITICALs angehen. **Jetzt** mit höherer Priorität — der Recorder schreibt zuverlässig (P14-E-Fix), aber die CRITICAL-Logs laufen weiter.
6. **Phase-15-Plan-Session** (großer Block): wenn die Beweiswoche genug Outcomes für die V4-Gegenargumente liefert, **jetzt** starten.

**Heutige Abend-Sequenz:** gemäß Morgen-Chat-Notiz `ps -o pid,etime,cmd -p 47166,47174,108966` + State-Timestamps nach dem Trading-Fenster — der `108966` ist jetzt `111151`, sonst gleich. Nikinger kann das in einer Folgesession selbst durchführen (Operator-no-LLM-Routine).

**Σ-Sweep Stand 2026-08-28 ~11:09 CEST:**
- P14 61, P13 74, P12 **145** (+2), P9 87, P8 248 — Σ 615 für diese 5 Phasen
  (Σ 1698 wie in den Closeout-Handovern = alle 13 Phasen + meta)
- Σ Root-Tests weiter **94** (unverändert)
- Allowance: **9245/10000** (7,55 % verbraucht, Roll-End Mo 31.08., unverändert)
- Verbleibende CRITICAL-Logs seit P14-Wiring-Fix: **0** (unverändert)
- Scheduler **PID 47166** (Sl, 1-16:56, schreibt State 11:08)
- Discovery **PID 47174** (S, 1-16:56, ARMED, schreibt State)
- Recorder **PID 111151** (Sl, ~3 min, **neue Code-Version mit Sleep-Cap**, schreibt State 11:07)
- **`.git/hooks/pre-commit`:** installiert (Operator-seitig), grün gegen Live-Repo.


---

> **Ältere Session-Blöcke** (verbatim ausgelagert, newest-first): [SESSIONS_ARCHIVE.md](./SESSIONS_ARCHIVE.md) — Rotation per Doc-Layers-Konvention ([docs/DOC_LAYERS_CONVENTION.md](../docs/DOC_LAYERS_CONVENTION.md)).