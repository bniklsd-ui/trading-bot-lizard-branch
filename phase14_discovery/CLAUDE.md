# CLAUDE.md — Phase 14: Discovery-Then-Deterministic (`phase14_discovery/`)

> Zwei Phasen lang war „welche Quelle kann Epic X?" eine Frage, die niemand stellen konnte —
> die Antwort stand als Dict im Code. Phase 14 macht sie zu einer Zeile in der DB.
> **Quelle der Wahrheit ist der Plan + der Code, nicht dieses Dokument.**
> Vollständiger Plan: [`../docs/concepts/phase14_discovery_plan.md`](../docs/concepts/phase14_discovery_plan.md).
> Vorgeschichte: [`../phase13_live_data/PHASE13_CLOSEOUT_HANDOVER.md`](../phase13_live_data/PHASE13_CLOSEOUT_HANDOVER.md) §1.5.
> Spezial-Pläne: [`./PHASE14_C_DAEMON_CWD_BUG_PLAN.md`](./PHASE14_C_DAEMON_CWD_BUG_PLAN.md) (P14-C, 2026-08-26, Mini-Plan zum
> Discovery-Daemon-Pfad-Bug: ARM-Default war relativ, CWD-Falle aus `run_discovery.sh`);
> [`./PHASE14_D_DAEMON_SIGNAL_CAP_PLAN.md`](./PHASE14_D_DAEMON_SIGNAL_CAP_PLAN.md) (P14-D, 2026-08-26, Mini-Plan zum
> Discovery-Daemon-Signal-Response-Bug: `interval_s=3600`-Sleep verschluckt SIGTERM, analog Phase-8-POST_WINDOW).

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

> Stand: **2026-08-22 — Session 9.** Diese Tabelle wird in Block D gegen den
> As-Built-Stand gefüllt (Testzahlen aus dem finalen Sweep, nicht geschätzt).

| Datei | Zweck | Status |
|---|---|---|
| `source_registry/models.py` | `SourceAvailability`, `SourceProfile`, `Source`-Protocol, `origin`-Vokabular | ✅ A2/A3 (gelockt in Phase-13-Session 4) |
| `source_registry/store.py` | `SourceAvailabilityStore` — der einzige Zugriff auf Migration 007 | ✅ A2 |
| `source_registry/sources.py` | `IGDerivedSource`, `LSStaticSource`, `RegistryYFSource` — alle drei ohne Netz | ✅ A3 |
| `source_registry/arm.py` | Scharf-Flag `data/state/DISCOVERY_ARMED` (Muster `killswitch.py`, sichere Richtung umgedreht) | ✅ C1 (Session 9) |
| `source_registry/run.py` | Der Daemon (Muster `data_foundation/run.py`: PID-File, graceful SIGTERM, `--once`) | ✅ C2 (Session 9) |
| `scripts/run_discovery.sh` | Start-Wrapper (Muster `run_recorder.sh`) | ✅ C4 (Session 9) |
| *(cross-phase)* `phase2_persistence/migrations/007_phase14_source_availability.sql` | die Kreuzungs-Tabelle **+ der einmalige yF-Backfill aus `instrument_universe`** (der Grundbestand kommt aus der Migration, nicht aus einem Resolver-Lauf — `resolve_epic` ruft `set_symbol` in sechs von acht Pfaden nicht) | ✅ A2 |
| *(cross-phase)* `phase9_universe/universe/models.py` | `DS_STALE_SOURCE` ins Vokabular (Live-Blocker B1) | ✅ A1 |
| *(cross-phase)* `phase9_universe/universe/store.py` | yF-Projektion in `set_symbol`, nicht-fatal | ✅ A4 (Session 7) |
| *(cross-phase)* `phase13_live_data/live_data/backfill.py` | `CapitalSource.discover()` (B1b); `EPIC_MAP` raus + Symbol-Lookup rein (B2) | ✅ B1b + B2 (Session 8) |
| *(cross-phase)* `phase13_live_data/scripts/probe_capital.py` | CFD-Filter-Bug Fix: `"CFD"`-Substring → exakt `"INDICES"`; neuer Helper `_pick_index_match` für Testbarkeit | ✅ Cross-Phase-Hygiene (Session 7) |
| *(cross-phase)* `phase13_live_data/scripts/source_delta.py` | drei Fälle statt zwei (`not_available` / `available_but_empty` / `compared`) | ✅ B3 (Session 8) |
| *(cross-phase)* `phase8_scheduler/webui/api.py` + `static/` | `GET /api/discovery`, ARM/DISARM, Warn-Banner | ✅ C3 (Session 9) |
| *(cross-phase)* `phase8_scheduler/scripts/run_scheduler.sh` | Autostart-Hook für `run_discovery.sh` (analog Recorder) | ✅ C4b (Session 9) |

---

## Session stopped — 2026-08-27 (Session 16: Mini-Session — Phase-14-nahe Hygiene [Doc-Rotation-Hook], Code+Tests+Doc-Korrektur)

> **Auftrag:** Nikinger-Antwort auf den Session-15-NEXT-Block: „Die Phase 14
> Nahe Hygiene bitte." Zwei Items auf der Liste: (1) B5-Fix
> (`backfill.py:414-416` `insert_bars`-Return-Verwurf) und (2)
> Doc-Rotation-Hygiene-Hook (`scripts/check_doc_rotation.py`).
> **Erste Entdeckung:** B5 ist **bereits gefixt** (Commit `4681d68`,
> 2026-08-22, Block 0.3 mit B3/B4/B5 gebündelt, Inline-Kommentar in
> `backfill.py:645-648` zeigt explizit auf B5, Regressionstest
> `test_run_capital_backfill_counts_only_genuinely_new_rows` pinnt das
> Verhalten). **Item 1 fällt weg** — kein Code-Edit nötig. Stattdessen:
> Doc-Korrektur für die Session-15-Erstfassung (die §11.1 + §11.2 mit
> falschen Ankern geschrieben hatte). Item 2 (Doc-Rotation-Hook) wird
> gebaut. Mini-Session-Scope: **drei Atome** — Doc-Korrektur (Phase-14-
> plan.md + CLAUDE.md + INDEX.md) + Skript+Tests (scripts/ + tests/) +
> Session-Block-Rotation. Working-Style „Push fragt der Nikinger frei".

### Completed

**Doc-Korrektur (Commit `3b69263`)** — Working-Style-Regel „Code > Doc"
angewendet. Die Session-15-Erstfassung hatte **zwei** Anker-Drift
erzeugt:

- **§11.1 B5:** behauptete „latent bis zum nächsten Cross-Phase-Touch" —
  **falsch**. Der Fix lebt seit `4681d68` (2026-08-22), Inline-Kommentar
  in `backfill.py:645-648` (explizit „Phase-14 finding B5"), Regressionstest
  `test_run_capital_backfill_counts_only_genuinely_new_rows`
  (`test_capital_backfill_script.py:169-200`) pinnt das Verhalten.
  §11.1 wurde komplett umgeschrieben mit Korrekturnotiz-Header (2026-08-27,
  Mini-Session 15+16); Code-Snippet zeigt jetzt `backfill.py:644-649` (heute).
- **§11.2 P14-C-Befund:** verwies auf Commit `2769763` als Fix-Anker — **falsch**.
  `2769763` ist der Mini-Plan-Doc-Commit. Der Fix lebt in `4e44b73`
  (2026-08-26, Session 11, Code+Tests). Inhaltliche Aussage bleibt richtig
  (Fix ist live); Anker präzisiert + Korrekturnotiz-Block angehängt.

  CLAUDE.md-Session-15-Block: Findings-Sektion „Drei der vier Drifts
  sind gefixt" → „Alle vier Drifts sind gefixt"; Unverändert-offen-Liste
  B5-Fix-Eintrag „latent" → „✅ bereits gefixt"; NEXT-Block Track (b)
  „B5-Fix als Hygiene-Atom mitnehmen" gestrichen. docs/INDEX.md
  Plan-Entry mit §11-Korrekturnotiz-Marker erweitert.

**Doc-Rotation-Hygiene-Hook (Commit `f403ab4`)** — strukturelle Antwort
auf den Session-12-Befund (§11.4 Korrekturnotiz: „die Doc-Layers-Rotation-
Regel war dokumentiert, aber nicht maschinen-prüfbar. Inline-Duplikate
von Session-Blöcken rutschten durchs Review"). Skript macht es prüfbar:

`scripts/check_doc_rotation.py` (~115 Zeilen, kein Netz, keine externen
Imports, exit codes 0/1/2):
- `count_session_blocks(md_text)` — reine Zähl-Funktion. Ignoriert
  Inline-Matches im Footer-Block (Quote-Paragraph, kein H2).
- `check_phase(phase_dir)` — `(count, label)`; `0` für fehlende `CLAUDE.md`.
- `main()` — iteriert über `PHASE_DIRS` (14 aktive/geschlossene Phasen
  + `meta_m1_harness`), sammelt Verstöße, `exit 1` wenn `count > 1`.
- CLI: `--phase NAME` (repeatable, Restrict), `--quiet` (OK-Zeilen
  unterdrücken, Failures weiter gedruckt).
- Regel: „at most one", nicht „exactly one" — virgin Phases (z. B.
  `phase2_persistence`, kein Archiv, kein History) bleiben mit 0 OK.

`tests/test_check_doc_rotation.py` (14 Tests, alle grün):
- 5 Pure-Tests (count_session_blocks: leer / no-heading / one /
  two-inline-duplicate / inline-match-im-Footer-ignoriert).
- 3 check_phase-Tests (fehlt / 0 / 1).
- 3 main-Tests mit `tmp_path` + `monkeypatch` (zero-OK / one-OK /
  two-FAIL) + `--quiet`-Suppress-Test.
- 2 End-to-End-Tests gegen das Live-Repo (`main()` + Subprocess-Aufruf).

Convention: phase-less Skript, geladen via
`importlib.util.spec_from_file_location` (gleiches Muster wie
`test_verify_instrument.py` / `test_resolve_epics.py` — root `scripts/`
ist absichtlich **kein** Package, weil die Phasen bereits auf
`scripts.wiring` kollidieren würden).

**Rotation Session 15 → SESSIONS_ARCHIVE.md** (Doc-Layers-Konvention):
Session-15-Block (inkl. der inzwischen angebrachten §11.1/§11.2-
Korrekturnotiz-Header) wandert **verbatim** an den Anfang des Archivs;
Phasenkopf trägt jetzt nur noch den Session-16-Block. Footer-Pointer
bleibt. Σ-Sweep-Stand 2026-08-27 ~13:30 CEST unten im Block dokumentiert.

### Verified

- `pytest phase14_discovery/tests -q` → **61 passed** (unverändert).
- `pytest phase13_live_data/tests -q` → **74 passed** (unverändert).
- `pytest phase12_data_foundation/tests -q` → **143 passed** (unverändert).
- `pytest phase9_universe/tests -q` → **87 passed** (unverändert).
- `pytest phase8_scheduler/tests -q` → **248 passed, 1 warning** (unverändert).
- `pytest tests/test_check_doc_rotation.py -v` → **14 passed** (NEU).
- `pytest tests -q` → **94 passed** (war 80, **+14** neue Hygiene-Tests).
- `python3 scripts/check_doc_rotation.py --quiet` → **exit 0**.
- `python3 scripts/check_doc_rotation.py` (verbose) → alle 14 Phase-Heads
  OK: 1× virgin (phase2_persistence), 13× canonical (1 Block).
  **Null** Drift im Live-Repo.
- `grep "^## Session stopped" phase14_discovery/CLAUDE.md` → **1**
  (canonical), `.count_session_blocks(...) == 1`.
- Working tree nach Commits `3b69263` + `f403ab4`: clean (außer `data/`
  untracked, gitignored). **Drei** Commits in dieser Session geplant
  (Doc-Korrektur + Skript+Tests + Session-Block-Rotation, alle lokal;
  Push = Nikinger-Freigabe).

### Findings

🟢 **Item 1 (B5-Fix) erledigt durch Entdeckung** — der Fix existierte
seit 2026-08-22 (`4681d68`), ich hatte es in Session 15 nur nicht
bemerkt. Die Doc-Korrektur in dieser Session macht den Drift sichtbar
und bringt das Doc in Übereinstimmung mit dem Code. **Lesson:**
bei zukünftigen „latent"-Aussagen erst `grep`/`git log` checken, dann
schreiben.

🟢 **Item 2 (Doc-Rotation-Hook) gebaut + getestet + grün gegen Live-Repo**
— strukturelle Antwort auf §11.4. Heute fängt jeder zukünftige
Inline-Duplikat-Drift das Skript + den End-to-End-Test, **bevor** er
committed werden kann. Die Regel ist jetzt **doppelt** geschützt:
maschinen-prüfbar (Skript) + dokumentiert (Doc-Layers-Konvention).

🟡 **„at most one" statt „exactly one"** — bewusste Lockerung der Regel
im Skript, weil Phase 2 (Persistence) legitimerweise 0 Session-Blöcke hat
(„no archive — no history"). Die strikte „exactly one"-Lesart hätte
einen Fehlalarm geworfen. **Regel-Drift im Skript korrekt:** das Skript
konsumiert die Regel, nicht definiert sie — `docs/DOC_LAYERS_CONVENTION.md`
sagt „exactly one session block" im Rotation-Kontext (nach dem ersten
Append); Phase 2 hat nie appended.

🟡 **Pre-Commit-Hook nicht gewired** — das Skript ist gebaut + grün,
aber **nicht** als Pre-Commit-Hook in `.git/hooks/pre-commit` o. ä.
installiert. Empfehlung: beim Phase-15-Setup (oder einer kleinen
Folge-Session) einen `pre-commit`-Hook installieren, der das Skript
aufruft. **Bewusst nicht in dieser Session** — Hook-Installation ist
Operator-Sache (Nikinger-Call), nicht Phase-14-Scope.

### Unverändert offen (von Session 15)

- **D5 Closeout-Handover** — wartet auf Phase-13-Beweiswoche (Plan §7 P1–P9).
  Phase 14 bleibt **closed-in-all-but-D5**.
- **Hygiene-Tickets aus Session 4** bleibt leer.
- **Recorder-Daemon (`phase12_data_foundation/data_foundation/run.py`)** —
  derselbe theoretische Bug wie P14-D. Phase-15-Territorium (Helper-Klasse
  in einem gemeinsamen Modul, beide Daemons).
- **Phase-15-Planungs-Session**: V4-Themen (Council, Handover, Reward-Reform,
  Force-Trigger, Instinct-ECC) — gegatet auf Phase 9+11+12+13+14 + reale
  Outcomes.
- **Doc-Rotation-Hook als Pre-Commit-Hook** — Skript gebaut, Hook-Installation
  offen (siehe 🟡 Findings oben).

### NEXT

- **Operator (Nikinger):** **Push-Freigabe** für **drei** Commits dieser
  Mini-Session: `3b69263` (Doc-Korrektur, 3 Files +59/−29) +
  `f403ab4` (Skript + Tests, 2 Files +365) + den Session-16-Block-Rotation-
  Commit (2 Files, +X/−Y klein). Diff ist dokumentationsdominiert +
  1 Hygiene-Skript mit voller Test-Suite; kein Cross-Phase-Edit (das
  Skript lebt unter `scripts/` + `tests/`, beide root-level, kein
  Phase-Package angefasst). Default-Working-Style-Regel „nie selbst
  pushen" gilt weiterhin — diese Session ist **nicht** als Override-
  Variante deklariert; falls Du pushen willst, Frage-Tool wie üblich.
- **Ausführende Session (nächste):** keine Pflicht. Phase 14 bleibt
  **closed-in-all-but-D5** + **Phase-14-Hygiene jetzt vollständig**
  (alle vier Items aus dem Session-15-NEXT-Block abgearbeitet oder als
  nicht-nötig geschlossen). Wahrscheinliche Tracks je nach Nikinger-
  Entscheidung: (a) Phase-13-Beweiswoche-Beobachtung (läuft seit Mo
  2026-08-25, separater Track); (b) Phase-15-Plan-Session (V4 — könnte
  den Recorder-Sleep-Cap-Helper als Hygiene-Atom mitnehmen);
  (c) Mini-Session für den Doc-Rotation-Pre-Commit-Hook-Install (gering);
  (d) Phase-12-Reconciliation-Timing-Fix für die
  `reward.recorder: no usable history row`-Vorkommen (nicht Phase-14-Scope).
- **Phase-14-Aktivität:** **closed-in-all-but-D5** + **Hygiene vollständig**
  — §11 dokumentiert Post-Execution-Drifts deskriptiv; Doc-Korrektur
  in dieser Session hat §11.1/§11.2-Anker präzisiert; Doc-Rotation-Hook
  ist die strukturelle Antwort auf §11.4. Phase-14 ist jetzt **doppelt**
  abgesichert (Doc-Konvention + maschinen-prüfbar).
- **Σ-Sweep** Stand 2026-08-27 ~13:30 CEST:
  - P14 61, P13 74, P12 143, P9 87, P8 248 — Σ 613 für diese 5 Phasen
    (Σ 1698 wie in den Closeout-Handovern = alle 13 Phasen + meta)
  - **+14** neue Hygiene-Tests in `tests/test_check_doc_rotation.py`
    → Σ Root-Tests jetzt **94** (war 80)
  - Allowance (aus Session 14): 9245/10000 (7.55 % verbraucht, Mo 31.08. Roll-End)
  - Verbleibende CRITICAL-Logs seit P14-Wiring-Fix: **0**
  - Recorder (Phase 12): läuft weiter (PID 4190 Sl), Daemon
    (Phase 14): läuft (PID 47174 Sl, mit P14-D-Fix), Scheduler: PID 47166
  - **check_doc_rotation.py** heute: alle 14 Phase-Heads OK (1× virgin,
    13× canonical, 0× FAIL).

---

> **Ältere Session-Blöcke** (verbatim ausgelagert, newest-first): [SESSIONS_ARCHIVE.md](./SESSIONS_ARCHIVE.md) — Rotation per Doc-Layers-Konvention ([docs/DOC_LAYERS_CONVENTION.md](../docs/DOC_LAYERS_CONVENTION.md)).
