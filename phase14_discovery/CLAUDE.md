# CLAUDE.md — Phase 14: Discovery-Then-Deterministic (`phase14_discovery/`)

> Zwei Phasen lang war „welche Quelle kann Epic X?" eine Frage, die niemand stellen konnte —
> die Antwort stand als Dict im Code. Phase 14 macht sie zu einer Zeile in der DB.
> **Quelle der Wahrheit ist der Plan + der Code, nicht dieses Dokument.**
> Vollständiger Plan: [`../docs/concepts/phase14_discovery_plan.md`](../docs/concepts/phase14_discovery_plan.md).
> Vorgeschichte: [`../phase13_live_data/PHASE13_CLOSEOUT_HANDOVER.md`](../phase13_live_data/PHASE13_CLOSEOUT_HANDOVER.md) §1.5.

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
## Session stopped — 2026-08-22 (Session 9: Block C — Daemon + Web-UI-Scharfschalten + Start-Wrapper)

> **Auftrag:** Nikinger-Freigabe 2026-08-22 (Special-Task im Prompt: Push der 4 ungepushten
> Session-8-Commits war erteilt) + die Anschluss-Frage aus dem Session-8-NEXT-Block:
> „Soll ich C1 starten, oder ist der Push jetzt dran?". Nikinger-Entscheidung im Chat
> der Planungs-Session: **Loslegen, alle 4 C1–C4 atomar, Smoke-Test + Sweep am Ende**.
> Fünf Commits: drei Code+Tests (C1, C2, C3), zwei Scripts (C4a, C4b). **39 neue Tests**
> (Phase-14: 22 → 57 = +35; Phase-8: 244 → 248 = +4). **Sweep Σ 1659 → 1698.** Push der
> vier B2/B3-Commits **zu Beginn der Session** ausgeführt (`31b5f87..a22b54d`), Branch
> seither `up to date with 'origin/main'`. Akzeptanz **A2 + A5 + A6 grün**;
> A1 + A3 + A4 + A7 waren bereits grün, A8 mit dem Sweep.

### Completed

**Commit 1 — `phase14: code+tests -- C1 arm.py (file-flag, safe-default False per D10)`**
(`275deb2`, 3 files, +433/-0). `phase14_discovery/source_registry/arm.py` NEU: vier
Funktionen (`is_armed`, `arm`, `disarm`, `read_state`) + Modul-Konstante
`DEFAULT_ARM_PATH = data/state/DISCOVERY_ARMED`. **Verbatim-Muster** aus
`scheduler/killswitch.py` (atomar `.tmp` + `os.replace`, fail-soft, wirft nie) — mit
einem **bewusst umgedrehten Detail** (Plan D10): die sichere Richtung ist `False`,
nicht `True`. Das steht im Modul-Docstring, weil das genau die Sorte Fehler ist, die
ein unaufmerksamer Clone-Kopiervorgang mitnimmt. `is_armed` validiert strikt auf JSON
`True` (`armed='true'` String, `armed=1` Int, `armed=null` lesen alle als False). 18
neue Tests (`test_arm.py`): 9 negative cases für `is_armed`, Round-Trip arm/disarm,
atomic-write-Beweis (`tmp`-Siblings nach `arm()` == `[flag]`), Parent-Dir-`mkdir -p`,
Modul-Konstante gegen UI-Sync gepinnt.

**Commit 2 — `phase14: code+tests -- C2 run.py daemon (PID, --once, fail-soft if unarmed)`**
(`94bbd0c`, 2 files, +869/-0). `phase14_discovery/source_registry/run.py` NEU:
`DiscoveryDaemon`-Klasse + `main()`-CLI. PID-File-Guarded (Muster
`data_foundation/run.py:39-53`), `SIGTERM`/`SIGINT` → `graceful stop`, `--once`-Modus.
Schleife: `is_armed` ⇒ **nein: skip, Debug-Tick, nichts weiter**; sonst
`stale_rows(ttl_days)` ⇒ nichts stale ⇒ skip; sonst je Source `discover(epics,
max_probe_calls=8)` mit fail-soft (`SourceProfile.errors` sammelt Exceptions, wirft
nicht — Plan §8.5). `probe_calls_used > 0 AND budget != None` ⇒
`record_spend(cum, kind='discovery')` in `source_spend` (Plan D13, freigegebener
Cross-Phase-Touch zu Phase 12's `SourceBudget`). State-File
`data/state/discovery_state.json` (atomic `.tmp` + `os.replace`, Format spiegelt
`recorder_state.json`). CycleResult ist `frozen`. `_build_default_sources` baut die
drei net-free Phase-14-Sources (ig/ls/yf); Capital.com ist **bewusst nicht** im
Default-Set — es lebt in Phase-13 `backfill.py` und würde Phase-13-Module in den
Daemon ziehen. 17 neue Tests (`test_run.py`): unarmed-skip, armed+no-stale-skip,
armed+stale-call-each-source-once, raising-source-tolerated, zero-probe-no-spend,
nonzero-probe-records-spend, state-file-shape, `CycleResult`-frozen,
`run_forever`-calls-`run_once`-until-stop, stop-before-first-cycle, `main --once` smoke,
PID-already-running-exit-0, `default_sources`-AreNetFree. **Lazy Cross-Phase-Imports
nur in `main()`** — Tests üben den Daemon mit duck-typed Stores, kein Phase-12-Wiring.

**Commit 3 — `phase14: webui -- C3 /api/discovery + amber banner + ARM/DISARM
(cross-phase Phase 8)`** (`af837c1`, 5 files, +226/-1). Cross-Phase Phase 8
(freigegeben): drei Endpoints in `webui/api.py`, Banner + Buttons in der
Static-Bundle, Amber-CSS-Variante. **api.py:** Modul-Konstante `_ARM_PATH` (mirror von
`source_registry.arm.DEFAULT_ARM_PATH`, kein Cross-Phase-Import at module load).
`GET /api/discovery` mit `{armed, armed_by, armed_ts, last_run_utc, last_rows_written,
last_errors, rows_total, rows_by_source, stale_rows}` — **fail-soft auf jedem Bein**
(missing flag / missing state.json / missing migration 007 / missing DB ⇒ sichere
Defaults, kein 500). Lazy imports von `source_registry.arm` im Endpoint-Body. `POST
/api/discovery/arm` (`by='dashboard'`), `POST /api/discovery/disarm`. 503 wenn
`source_registry` nicht importierbar (Dashboard-Headline bleibt unberührt). **Frontend:**
`#discovery-banner` (amber Variante des `#kill-banner`), Buttons `ARM DISCOVERY` /
`DISARM DISCOVERY` in einer dritten `btn-row`. JS: `renderDiscovery(d)` toggelt
Banner + Button-Disabled-State (ARM disabled wenn armed, DISARM disabled wenn not
armed — die sichere Default-False-Richtung). 7s-Poll erweitert um `/api/discovery`.
**CSS:** `.discovery-banner` (amber tint), `.btn--discovery-arm`/`.btn--discovery-disarm`,
generisches `.btn[disabled]`. 4 neue Tests (`test_webui.py`): unarmed-false,
arm-roundtrip, disarm-removes, **fail-soft ohne Migration 007** (Akzeptanz C3-Test).

**Commit 4 — `phase14: scripts -- C4 run_discovery.sh (start wrapper, autostart-safe)`**
(`7aa86bd`, 1 file, +34/-0). `phase14_discovery/scripts/run_discovery.sh` NEU, dünn,
analog `phase12_data_foundation/scripts/run_recorder.sh`: `set -euo pipefail`,
`PROJECT_DIR + cd`, `exec python -m source_registry.run "$@"`. Header dokumentiert
die **safe-default-False-Semantik** (D10: autostarten ist unbedenklich, der Daemon
ist ohne Flag ein No-Op).

**Commit 5 — `phase14: scripts -- C4b run_scheduler.sh hooks up the Discovery daemon`**
(`170ed72`, 1 file, +10/-0). Cross-Phase Phase 8: `phase8_scheduler/scripts/run_scheduler.sh`
bekommt einen analogen `nohup`-Block für `run_discovery.sh` (analog zum Recorder-Block
aus Zeile 38-39, jetzt Zeile 41-42). Header-Comment erweitert um den Phase-14-Kontext
(mit Verweis auf die D10-Safe-Default-Argumentation). PID-Doppelstart-Schutz sitzt im
Daemon (`source_registry.run`), nicht hier — Muster Recorder.

**Push der 4 B2/B3-Commits zu Beginn** (`31b5f87..a22b54d`). Branch danach `up to date
with 'origin/main'`, 0 Commits dahinter.

**Smoke-Test** (`phase5_execution/scripts/smoke_test.py --broker ig_demo`) — einmal
gelaufen auf Nikinger-Freigabe (nicht Phase-14-Stoff, gleiche Logik wie Session 8 für
B2/B3). Ergebnis sauber: `NO_TRADE -- time_window: 20:07 outside trade window
09:00-17:30 Europe/Berlin` (heute Samstag 20:07, kein Trade-Fenster; Phase 5 baut
den Cycle sauber auf, alle Gates + VETOs laufen, OrderDecliner blockt, kein
Live-Touch). **Beweis:** die Phase-13-/Phase-14-Bibliothek ist unter dem Phase-5-Bot
konsumierbar — kein Import- oder Wiring-Bruch aus C1/C2/C3/C4.

### Verified

- Regression-Sweep aller 14 Suiten + root `tests/` (Stand nach den fünf Commits,
  ohne diesen Docs-Edit):
  | Suite | Vor Session 9 | Nach | Δ |
  |---|---:|---:|---:|
  | phase1_broker_wrapper | 95 | 95 | 0 |
  | phase2_persistence | 77 | 77 | 0 |
  | phase3_external_data | 104 | 104 | 0 |
  | phase4_research | 155 | 155 | 0 |
  | phase5_execution | 173 | 173 | 0 |
  | phase6_debate | 76 | 76 | 0 |
  | phase7_reward | 138 | 138 | 0 |
  | phase8_scheduler | 244 | 248 | **+4 (C3)** |
  | phase9_universe | 87 | 87 | 0 |
  | phase10_v3 | 165 | 165 | 0 |
  | phase12_data_foundation | 143 | 143 | 0 |
  | phase13_live_data | 74 | 74 | 0 |
  | phase14_discovery | 22 | 57 | **+35 (C1: 18, C2: 17)** |
  | meta_m1_harness | 28 | 28 | 0 |
  | root `tests/` | 80 | 80 | 0 |
  | **Σ** | **1659** | **1698** | **+39** |
  *(Cross-check: C1=18, C2=17, C3=4 = 39 neue Tests, keine Lücke. C4 hat keinen
  Testbeitrag — bash-Wrapper, durch `bash -n`-Syntaxcheck + Operator-Run validiert.)*
- `grep -rn "EPIC_MAP" phase13_live_data/ --include=*.py` → **leer** (Exit 1, kein
  Treffer). **Akzeptanz A2 grün.**
- Akzeptanz A5 grün: `test_run.py::test_run_once_unarmed_does_nothing` — der
  `FakeSource` mit `raise_in_discover=True` bleibt **unangerührt**, weil der
  arm-Check vor jeder DB- und Netz-Aktion liegt.
- Akzeptanz A6 grün: `test_webui.py::test_discovery_endpoint_fails_soft_without_migration_007`
  + `test_discovery_unarmed_reports_false` — die UI meldet `armed: false` und
  `rows_total: null`, nicht 500.
- Akzeptanz A8 grün: Sweep-Tabelle oben, Σ 1698, kein roter Test, keine
  uncommitteten Änderungen.
- Working tree clean vor Commit-Kette (außer `data/`-Ordner, gitignored).
- **Cross-Phase-Edits nur innerhalb der freigegebenen Liste** (Nikinger 2026-08-22):
  Phase 8 (`webui/api.py` + `static/` für C3, `run_scheduler.sh` für C4b), Phase 12
  (`SourceBudget` als lazy import in C2). Kein Touch außerhalb.
- `git log --oneline -7` zeigt die saubere Kette: 4× B2/B3 (alt) + 5× C1–C4b (neu).

### Findings (drei)

- **C3-Akzeptanz-Test-Strenge.** Der `test_discovery_endpoint_fails_soft_without_migration_007`
  pinnt **drei** `None`-Werte (`rows_total`, `rows_by_source`, `stale_rows`). Das ist
  mehr als der Plan §6 C3-Akzeptanztest verlangt (nur `rows_total: null`); die zwei
  zusätzlichen Asserts sind die offensichtliche Erweiterung desselben fail-soft-Vertrags
  und kosten nichts, dokumentieren aber laut, dass die ganze Availability-Query als
  Block failt, nicht nur die Summe. Beibehalten.
- **C2 `main()`-Imports.** Die Cross-Phase-Imports (`UniverseStore`,
  `SourceAvailabilityStore`, `SourceBudget`) leben **innerhalb** von `main()`, nicht
  am Modul-Top. Das ist Repo-Konvention (`api.py:18-20` zitiert das gleiche Muster)
  und bedeutet konkret: `import source_registry.run` triggert keine
  Phase-12-/`UniverseStore`-Lade-Arbeit. Tests, die `DiscoveryDaemon` direkt
  konstruieren, sehen Phase 12 nicht — sie arbeiten mit duck-typed Stores. Die
  drei Cross-Phase-Imports im `main()`-Body haben jeweils einen `try/except`-Mantel
  (`budget = SourceBudget(...)` als best-effort, `None` on failure — kein Hard-Fail
  der CLI wenn das Budget nicht initialisierbar ist, weil default-Sources eh nie
  buchen).
- **`is_armed` strict-type.** Drei Tests mehr als der Plan (String, Int, Null —
  alle False) sind verteidigende Auslegung des `armed is True`-Checks. Die Alternative
  wäre `if data.get("armed"):` gewesen, was `"yes"` / `1` / nicht-leere Strings als
  arm liest — falsche Richtung. Der strikte `is True` ist die ehrliche Lektüre des
  Vertrags. Test-Kommentar dokumentiert das.

### Unverändert offen

- **Block D** (Closeout) — die einzige Akzeptanz-Lücke. Konkret: D1 (Modul-Tabelle
  in `phase14_discovery/CLAUDE.md` gegen den As-Built-Stand füllen — Testzahlen aus
  dem **finalen** Sweep, nicht geschätzt; **ist in dieser Session bereits passiert**,
  Stand-Notiz aktualisiert), D2 (finaler Regression-Sweep, je Phase separat, Tabelle
  in den Session-Block — **genauso bereits passiert**, Tabelle im Verified-Abschnitt
  oben), D3 (`## Session stopped` schreiben + Rotationsregel — **passiert gerade**),
  D4 (root-`CLAUDE.md` + `ROADMAP.md` + `docs/INDEX.md`: Phase-14-Zeile auf den
  erreichten Stand; **nicht in dieser Session — Block-D-Topic**), D5
  (Closeout-Handover **nur**, wenn die Phase geschlossen wird — gesonderte Entscheidung).
- **Hygiene-Tickets aus Session 4**, weiter zurückgestellt: `*.sqlite.bak-*` in
  `.gitignore`, `ROADMAP.md:427`-Aktualisierung.
- **Plan-§9-Drift-Listeneintrag #2** erweitern in der nächsten Plan-Session.
- **Phase-15-Planungs-Session**: V4-Themen (Council, Handover, Reward-Reform,
  Force-Trigger, Instinct-ECC) — gegatet auf Phase 9+11+12+13+14 + reale Outcomes.

### NEXT

- **Operator (Nikinger):** Push-Freigabe für die 5 Commits
  (`275deb2`, `94bbd0c`, `af837c1`, `7aa86bd`, `170ed72`) + diesen Docs-Commit.
  Stand jetzt: 5 Commits vor `origin/main`.
- **Ausführende Session (nächste):** **Block D — Closeout.** Konkret:
  - root-`CLAUDE.md`: Phase-14-Zeile auf „Block C done, Beweiswoche + Block D ausstehend"
    (statt „Plan committet, Bau nicht begonnen")
  - `ROADMAP.md` Phase-14-Block auf den erreichten Stand
  - `docs/INDEX.md`: Phase-14-Status-Update (Bullet-Liste, eine Zeile)
  - **Entscheidung A**: Soll die Phase hier geschlossen werden (mit Closeout-Handover,
    D5), oder soll Block D nur die Doku-Updates machen und die Phase erst nach der
    Beweiswoche (Phase 13 Plan §7 P1–P9) final schließen? Mein Vorschlag:
    **erst Beweiswoche abwarten** — Phase 14 hat strukturell geliefert, aber der
    Beweis-Track ist Phase 13 und läuft parallel. D5 (= Closeout-Handover) ist deshalb
    die letzte Session der Phase, nicht diese.
- **Beweiswoche läuft separat weiter** (Phase 13 Plan §7 P1–P9). C1–C4 berühren die
  laufende Beweiswoche nicht — kein Konsumentenpfad schreibt in
  `instrument_source_availability` während der Beweiswoche; die einzigen Schreiber
  sind (a) A4-Projektion in `UniverseStore.set_symbol`, die auf den nächsten
  Resolver-Tick wartet, und (b) der C2-Daemon, der ohne `arm`-Flag ein No-Op ist.

---

> **Ältere Session-Blöcke** (verbatim ausgelagert, newest-first): [SESSIONS_ARCHIVE.md](./SESSIONS_ARCHIVE.md) — Rotation per Doc-Layers-Konvention ([docs/DOC_LAYERS_CONVENTION.md](../docs/DOC_LAYERS_CONVENTION.md)).
