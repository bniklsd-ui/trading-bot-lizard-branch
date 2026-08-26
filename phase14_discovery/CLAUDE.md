# CLAUDE.md — Phase 14: Discovery-Then-Deterministic (`phase14_discovery/`)

> Zwei Phasen lang war „welche Quelle kann Epic X?" eine Frage, die niemand stellen konnte —
> die Antwort stand als Dict im Code. Phase 14 macht sie zu einer Zeile in der DB.
> **Quelle der Wahrheit ist der Plan + der Code, nicht dieses Dokument.**
> Vollständiger Plan: [`../docs/concepts/phase14_discovery_plan.md`](../docs/concepts/phase14_discovery_plan.md).
> Vorgeschichte: [`../phase13_live_data/PHASE13_CLOSEOUT_HANDOVER.md`](../phase13_live_data/PHASE13_CLOSEOUT_HANDOVER.md) §1.5.
> Spezial-Pläne: [`./PHASE14_C_DAEMON_CWD_BUG_PLAN.md`](./PHASE14_C_DAEMON_CWD_BUG_PLAN.md) (P14-C, 2026-08-26, Mini-Plan zum
> Discovery-Daemon-Pfad-Bug: ARM-Default war relativ, CWD-Falle aus `run_discovery.sh`).

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
## Session stopped — 2026-08-25 (Session 10: Restart-Hygiene — 4 Commits, atomar aus einer Nikinger-Antwort)

> **Auftrag:** Special-Task aus dem Prompt (Nikinger-bestätigt 2026-08-25), schon im
> Session-9-NEXT-Block + „Unverändert offen"-Block vorregistriert. Wochenend-taugliche
> Mini-Session (~15 Min) plus Erweiterung in derselben Nikinger-Antwort („Gerne alles
> genannte, aber was ist das Problem bei phase 8?"). **Vier Atome, eine Session.**
> **Keine Push-Freigabe eigenmächtig** — Working-Style-Regel „Push fragt der Nikinger frei".

### Completed

**Commit 1 — `phase14: scripts -- restart-hygiene (PATH-prepend in dev_install + 4 run_*.sh)`**
(`6644773`, 5 files, +63/-0). NEXT-Punkt 2 des Session-9-NEXT-Blocks: PATH-Prepend-Block
in allen fünf Start-Wrappern. Die einzige venv im Repo ist `phase1_broker_wrapper/.venv`
(in deren `bin/` sowohl `python` als auch `uvicorn` liegen). Nach Reboot funktionieren
alle Start-Wrapper ohne `source <venv>/bin/activate` von Hand.

Fünf Sites, additiv (0 Zeilen gelöscht):
- `scripts/dev_install.sh` (`ROOT=` statt `REPO_ROOT=` — `ROOT` schon da, wiederverwendet)
- `phase8_scheduler/scripts/run_scheduler.sh` (`REPO_ROOT=`)
- `phase8_scheduler/scripts/run_webui.sh` (`REPO_ROOT=`) — **Fix für den explizit
  benannten `uvicorn: not found`-Befund**
- `phase12_data_foundation/scripts/run_recorder.sh` (`REPO_ROOT=`)
- `phase14_discovery/scripts/run_discovery.sh` (`REPO_ROOT=`)

Jeder Block: 5 Zeilen Comment-Header + 6 Zeilen Logik (`REPO_ROOT` aus `BASH_SOURCE`,
`_VENV_BIN` berechnen, Existence-Check, Path-Prepend, `unset _VENV_BIN`). 11 Zeilen
pro Datei, identische Form. `bash -n` OK auf allen 5.

**Commit 2 — `phase8: tests -- hermetic DISCOVERY_ARMED in client-fixture (4 C3-tests grün)`**
(`0a55818`, 1 file, +27/-1). Nikinger-Antwort auf den Phase-8-Befund: die 4 C3-Akzeptanz-
Tests (`test_discovery_unarmed_reports_false`,
`test_discovery_arm_creates_flag_and_subsequent_get_reports_true`,
`test_discovery_disarm_removes_flag`,
`test_discovery_endpoint_fails_soft_without_migration_007`) teilten den Live-Pfad
`data/state/DISCOVERY_ARMED` mit dem Endpoint — alle anderen Fixture-Pfade benutzten
`tmp_path`, **nur** der Arm-Pfad nicht. Plus eine **zweite** Live-Bleed-Stelle, die
erst diese Sitzung entdeckt hat: `webui/api.py:431` liest `data/state/discovery_state.json`
für das Last-Run-Summary-Feld, ebenfalls live. Beide Bleeds adressiert mit
monkeypatch-Pinning von drei Modul-Konstanten auf `tmp_path`:

```python
monkeypatch.setattr(api,   "_DATA_DIR",          tmp_path)              # deckt _ARM_PATH + Zeile 431
monkeypatch.setattr(api,   "_ARM_PATH",          tmp_path / "DISCOVERY_ARMED")
monkeypatch.setattr(arm,   "DEFAULT_ARM_PATH",   tmp_path / "DISCOVERY_ARMED")
```

Zwei Implementierungs-Details im Commit-Kommentar dokumentiert:
- **Module-Shadowing von `source_registry.arm`.** `source_registry/__init__.py:26-32`
  re-exportiert `arm` (die Funktion) als Top-Level-Paketattribut, was `source_registry.arm`
  als Namen schattet. `from source_registry import arm` würde die Funktion binden, nicht
  das Submodul. Workaround: `importlib.import_module("source_registry.arm")` umgeht den
  `__init__`-Shadow und liefert das echte `arm.py`-Modul, wo `DEFAULT_ARM_PATH` definiert ist.
- **Blast-Radius `_DATA_DIR`-Redirect.** `api.py` nutzt `_DATA_DIR` zur Laufzeit nur an
  Zeile 57 (via `_ARM_PATH`, separat gerichtet) und Zeile 431 (das
  `discovery_state.json`-Reading). Die Zeilen 76-79 sind `SchedulerConfig()`-Defaults,
  die nur greifen wenn keine cfg übergeben wird — der Test übergibt immer eine eigene
  cfg, also inert.

**Commit 3 — `phase14+8: scripts -- restart-services.sh (status/stop/start/restart + --dry-run) + run_webui.sh +x`**
(`c97e82a`, 2 files, +266/-0). Nikinger-Antwort: „Gerne alles genannte". NEXT-Punkt 3
war als optional markiert — gebaut mit Disziplin, nicht als `pkill`-Fußkanone.

`scripts/restart-services.sh` (NEU): vier Modi + `--dry-run`:
- `status` — Inventur, exit 0 wenn ≥1 alive (default)
- `stop` — TERM, 5s grace, KILL nur als Fallback nach Grace
- `start` — `nohup` via die kanonischen Wrapper, idempotent (skip wenn alive)
- `restart` — stop + start, sequenziell in Start-Reihenfolge

Sicherheits-Disziplin (Projekt-Kultur eingebaut):
- **Niemals SIGKILL** vor SIGTERM + 5s Grace
- **`data/state/KILL` und `data/state/DISCOVERY_ARMED`** nie angefasst (operator-sticky)
- **Pattern-Match + `/proc/<pid>/cwd`-Check**: ein `python -m scheduler.run` aus
  einem anderen Repo / von einer anderen Maschine wird **nicht** gekillt
- **Sequentielle Starts** mit sleep zwischen Daemons (Parallel-Login-Falle-Konvention)
- **Skript wurde nie echt ausgeführt** — Bot läuft unverändert (4 PIDs alive:
  `data_foundation.run` 4190, `source_registry.run` 4243, `scheduler.run` 4237,
  `uvicorn webui.api:app` 4595). Status-Aufruf listet sie korrekt, restart --dry-run
  zeigt jede Aktion, ohne anzufassen.

Begleitend: `chmod +x phase8_scheduler/scripts/run_webui.sh` (war historisch nur
manuell via `bash ... run_webui.sh` gestartet; Restart-Helper macht es uniform +
+x). Mode-Change 100644 → 100755 im selben Commit.

### Verified

- `bash -n` alle Skripte: **OK** (5 PATH-Prepend + 1 restart-services.sh)
- Mechanik-Direkttest (PATH-Prepend mit `PATH=/usr/bin:/bin`):
  `python → phase1_broker_wrapper/.venv/bin/python`,
  `uvicorn → phase1_broker_wrapper/.venv/bin/uvicorn`. **Prepend funktioniert.**
- Hermetic-fixture-Test (Phase 8): vorher 4 failed, **jetzt 248 passed** in Phase 8.
- Full Sweep nach allen 3 Edits: **Σ 1698 grün, 0 fails** (Phase 8 248 · restliche
  Phasen 1450 unverändert). Σ-Konvergenz auf Session-9-Baseline (1698) erreicht.
- `git diff --name-only` (kumulativ): 5 `.sh` + 1 Test-Datei + 1 NEU `.sh` + 1 mode-change =
  nichts außerhalb der freigegebenen Phase-14-Sites (Phase 8 `scripts/` + `tests/`,
  Phase 12 `scripts/`, Phase 14 `scripts/`, root `scripts/`).
- `restart-services.sh status` (live, idempotent): listet alle 4 alive mit ihren PIDs.
- `restart-services.sh restart --dry-run`: zeigt jede TERM-/KILL-/nohup-Aktion an.

### Findings (zwei, beide produktiv behandelt in dieser Session)

- 🟢 **Phase-8-C3-Test-Bleed → gelöst** (Commit 2). Bleed war an **zwei** Pfaden
  (nicht nur dem Arm-Flag — `discovery_state.json` ist der zweite). Beide im selben
  `_DATA_DIR`-Redirect adressiert. Lesson: bei hermetic-Test-Fixtures immer prüfen,
  ob ein Modul-Konstante-Pfad direkt verwendet wird, zusätzlich zu allen Funktionen,
  die ihn via Attribut lesen.
- 🟢 **Restart-Helper-Fußkanone vermieden** (Commit 3, Bau mit Disziplin). Das Skript
  hat **keinen** `--force`-Flag, **kein** automatisches KILL-File-Clearing, **kein**
  blindes `pkill` — jede Destruktiv-Aktion ist TERM-zuerst mit dokumentierter Grace
  und CWD-Match als Schutz gegen versehentliche Fremdprozess-Kills. `--dry-run`
  previews alles. Der ursprüngliche Skeptizismus („Restart-Helper als Fußkanone") wird
  damit operativ belegt statt postuliert: der Helper ist da, mit klaren Leitplanken,
  für die Fälle in denen ihn jemand bewusst einsetzen will.

### Unverändert offen

- **D5 Closeout-Handover** — wartet auf Phase-13-Beweiswoche (Plan §7 P1–P9).
  Phase ist **strukturell fertig** (A1–A8 grün; **Σ 1698 grün, 0 fails**).
- **Hygiene-Tickets aus Session 4** bleibt leer.
- **Plan-§9-Drift-Listeneintrag #2** erweitern in der nächsten Plan-Session.
- **Phase-15-Planungs-Session**: V4-Themen (Council, Handover, Reward-Reform,
  Force-Trigger, Instinct-ECC) — gegatet auf Phase 9+11+12+13+14 + reale Outcomes.

### NEXT

- **Operator (Nikinger):** Push-Freigabe für die **drei** Commits `6644773` +
  `0a55818` + `c97e82a`. **Working-Style-Regel:** „Push fragt der Nikinger frei,
  nie selbst pushen." Vor Push: nichts mehr zu tun — Working tree clean, alle
  drei Commits sind die angeforderten Korrekturen + Erweiterungen. `restart-services.sh`
  ist gebaut, aber **nicht ausgeführt** — der nächste Reboot wird zeigen, ob die
  Helper-Pfade greifen (Nikkings erster Test nach Push).
- **Ausführende Session (nächste):** keine Phase-14-Code-Pflicht — die Phase ist
  **strukturell fertig** + Σ wieder grün. Wahrscheinliche Tracks je nach Nikinger-
  Entscheidung: (a) Push-Bestätigung + warten auf Beweiswoche; (b) Phase-15-Plan-
  Session (V4); (c) etwas anderes (Phase-13-Beweiswoche-Beobachtung).
- **Phase-14-Aktivität:** Mid-Phase-Status läuft weiter, Phase-13-Beweiswoche läuft
  separat (Plan §7 P1–P9), D5 wartet auf Beweiswoche.
- **Beweiswoche** läuft seit Mo 2026-08-25 (laut Phase-13-Plan §7 operator-getrieben).
  Stand der Session-9-Beobachtung bleibt gültig: Trade #8 BUY DAX.IGN offen,
  5. BUY auf DAX in Folge nach 4 Verlust-Trades (-2530.82 EUR realisiert),
  Token-Budget 38.5% / Weekly-Allowance 48% / Loss-Breaker **nicht** ausgelöst.
  Kein Handlungsbedarf (Safety-Mechanismen innerhalb Caps), Phase-15-Territorium
  (V4: BUY-Serie gegen das Modell stärker gewichten).

---

> **Ältere Session-Blöcke** (verbatim ausgelagert, newest-first): [SESSIONS_ARCHIVE.md](./SESSIONS_ARCHIVE.md) — Rotation per Doc-Layers-Konvention ([docs/DOC_LAYERS_CONVENTION.md](../docs/DOC_LAYERS_CONVENTION.md)).
