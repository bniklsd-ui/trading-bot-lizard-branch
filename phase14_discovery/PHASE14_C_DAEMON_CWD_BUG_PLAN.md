---
status: snapshot
purpose: Mini-Plan für den Discovery-Daemon-CWD-Path-Bug (Phase 14 Block C2). Der Daemon-Pfad zur ARM-Datei ist relativ und wird falsch aufgelöst, wenn `run_discovery.sh` den CWD nach `phase14_discovery/` setzt — der Daemon ist seit der Scharfschaltung am 2026-08-25 14:12 still, obwohl UI + Arm-File „armed" zeigen. Struktureller Fix in `source_registry/arm.py` (Muster: `run.py:62` macht es bereits richtig), Regressionstest pinnt CWD-Unabhängigkeit, Daemon-Restart zum Aktivieren.
read-when: dieser Bug gebaut/gefixt/verifiziert wird; jede Session, die `DISCOVERY_ARMED` oder den Daemon-Pfad anfasst; vor jedem Operator-Restart des Discovery-Daemons
detail: L3
up: ../CLAUDE.md
down:
  - ./CLAUDE.md                                                  # Phasenkopf, Session-Block-Aufnahme nach Fix
  - ../docs/concepts/phase14_discovery_plan.md                   # 📕 Mutterplan D1–D20 (D11 = „UI schaltet per Datei", unverändert; der Bug ist eine **Impl-Drift** zu D11, kein Plan-Konflikt)
  - ./PHASE14_B1A_PROBE_OUTPUT_2026-08-22.md                     # 📕 Schwester-Snapshot im Phase-14-Verzeichnis
updated: 2026-08-26
---
# P14-C — Discovery-Daemon-Pfad-Bug (Mini-Plan)

> **Einordnung:** Phase 14, **nach Block C (Session 9 abgeschlossen), vor D5-Closeout**.
> Kein eigenes Verzeichnis, kein neues Paket — Code, Tests, Session-Block leben in
> `phase14_discovery/` (gleiche Konvention wie P12.5 in Phase 12). „P14-C" ist ein Label
> für diesen Bugfix, kein neuer Block — er fasst die Lücke zwischen **C2 (Daemon, fertig)**
> und der realen Lauf-Annahme „Daemon liest die Flag-Datei, die der Bediener setzt".
>
> **Adressat:** die ausführende Claude-Code-Session (Sonnet 5) sowie den Operator.
> Alles unten ist gegen den Repo-Stand `11f18c4` am **2026-08-26** selbst nachgemessen
> (nicht aus Vordokumenten übernommen). Was nicht verifiziert werden konnte, steht in
> **§8** — alles andere ist Fakt und muss nicht neu hergeleitet werden.

---

## §0 BLUF

Der Discovery-Daemon (PID 4243, gestartet 2026-08-25 13:42 CEST) hat den
`DISCOVERY_ARMED`-Arm geschluckt, **schläft aber seit 20 Stunden**. Der Bediener sieht
im Dashboard `armed: true`, der Daemon schreibt `armed: false` in
`data/state/discovery_state.json` und macht null Discoveries. **Kein Trading-Impact** —
die Trading-Pipeline liest `instrument_universe`, nicht `instrument_source_availability`
—, aber Phase 14 ist damit operativ **stumm**, und der Beweiswoche-Decision-B aus
Plan §7 P2/P5 wartet auf genau diesen Output.

| # | Ohne Fix passiert | Schaden |
|---|---|---|
| **P1** | Dashboard zeigt `armed: true`, Daemon sieht `armed: false`, 17 stale rows werden nicht abgearbeitet | Phase 14 ist nicht stumm — ist **falsch** stumm |
| **P2** | `--arm-file data/state/DISCOVERY_ARMED` (absolut) würde es sofort lösen, aber das ist **Operateur-Wissen**, nicht die strukturelle Wahrheit | Wer den Daemon startet, muss seinen CWD kennen — **CWD-Falle** |
| **P3** | Eine zweite Quelle (z. B. Capital.com nach B1b) wäre denselben Pfad-Bug ausgesetzt, weil sie durch denselben `arm.py` läuft | Folgeschaden latent, erst beim ersten echten `discover()` sichtbar |

**Reihenfolge:** Befund verifiziert (heute passiert) → D1/D2/D3/D4 gelockt → ein
Code-Commit (Fix + Test, +X/−Y klein) → Daemon-Restart → Verify (erster Cycle sieht
`armed: true` + `stale_count > 0`).

**Was dieser Mini-Plan ausdrücklich NICHT tut:** Phase 14 schließen (D5 wartet auf die
Phase-13-Beweiswoche, nicht auf diesen Fix), Phase 15 planen (V4 bleibt long-horizon),
den arm.py-Vertrag ändern (nur die Pfad-Konstante, das `is_armed()`-Verhalten bleibt
identisch).

---

## §1 Rahmen + Arbeitsteilung

| Regel | Stand |
|---|---|
| **Arbeitszeit** | Werktags, **ohne** Bot-Stop nötig. Der Fix berührt den Scheduler-, Recorder- und WebUI-Prozess **nicht**. Nur der Discovery-Daemon (PID 4243) wird zum Restart-Zeitpunkt einmal beendet und neu gestartet. |
| **Bot vor dem Restart** | Ja — der Daemon hat ein warmes `UniverseStore`/`SourceAvailabilityStore`-Paar; SIGTERM läuft über `request_stop()` (`run.py:352-353`) und ist graceful (`_clear_pid`, `close()`-Trys, `run.py:355-374`). Vor dem Restart: `ps aux \| grep source_registry.run` als Gegenprobe (Parallel-Login-Falle-Konvention). |
| **Live / Netz / Kosten** | **Nikinger.** Claude baut, testet offline, committet. Kein neuer Live-Lauf — der Fix **wirkt** erst beim nächsten Daemon-Cycle (max 1 h nach Restart). |
| **Live-DB** | Claude liest nur `mode=ro`; der Fix schreibt **nichts** in die DB (er ändert nur die Modul-Konstante + Test). |
| **Cross-Phase-Edits** | **Keine.** Der gesamte Fix lebt in `phase14_discovery/source_registry/arm.py` + `phase14_discovery/tests/test_arm.py`. Die Cross-Phase-Freigabe-Liste aus Phase 14 (Phase 2/8/9/12/13, Plan §4) bleibt unangetastet. |
| **Push** | Nikinger-Freigabe, niemals selbst (`Working-Style`-Regel). Working tree clean nach jedem Commit. |

**Prozess-Ist-Stand bei Planschluss (2026-08-26 07:45 UTC, selbst erhoben):**

| Prozess | PID | argv | CWD |
|---|---|---|---|
| `data_foundation.run` | 4190 | `python -m data_foundation.run` | `/home/trading-bot/trading-bot` (Standard-Start) |
| `source_registry.run` | **4243** | `python -m source_registry.run` | `/home/trading-bot/trading-bot/phase14_discovery` (gesetzt durch `run_discovery.sh:43-44`) |
| `scheduler.run` | 17018 | `python -m scheduler.run --enable-shadow-schedule --enable-divergence-sampler` | repo root |
| `uvicorn webui.api:app` | 4595 | `.../uvicorn webui.api:app --host 127.0.0.1 --port 8000` | repo root |

---

## §2 Gelockte Entscheidungen (D1–D4)

Diese Tabelle ist der Ersatz für Nachdenken. **Nicht neu herleiten, nicht „verbessern".**
Widerspricht der Code einer Zeile ⇒ Advisor / Nikinger, nicht stillschweigend abweichen.

| # | Entscheidung | Begründung |
|---|---|---|
| **D1** | Fix in **`source_registry/arm.py`**, nicht in `run_discovery.sh`. | Der Skript-CDW-Set ist **nicht** falsch — er ist ein Konsumenteneingriff in eine Bibliotheks-Konstante. Strukturelle Wahrheit: `arm.py` ist der Eigentümer der ARM-Pfad-Konstante und muss sie CWD-unabhängig liefern. Die WebUI macht es seit Anbeginn richtig (`api.py:49-50`: `_REPO_ROOT = Path(__file__).resolve().parents[2]`); `run.py:62` ebenfalls (`_REPO_ROOT = Path(__file__).resolve().parents[2]`); **nur** `arm.py:55` weicht ab — Drift durch fehlende Konvention, nicht durch fehlende Implementierung. |
| **D2** | Fix ist **eine** Code-Zeile (Konstante) + **ein** Docstring-Satz, kein neues Argument, keine neue API. | `is_armed()`-Verhalten, `arm()`/`disarm()`-Verträge, `read_state()`-Output bleiben bit-identisch. Konsumenten (`run.py:300`, `api.py:57`, alle Tests) sehen weiterhin einen `str` bzw. `Path`, der jetzt zusätzlich absolut ist. Kein Caller ändert sich. |
| **D3** | Regressionstest pinnt CWD-Unabhängigkeit: `monkeypatch.chdir(...)` + `is_armed(tmp_path / "DISCOVERY_ARMED" with valid content)` → **muss `True` lesen**, wenn der `tmp_path`-Pfad per Monkeypatch auf den Modul-Default zeigt; **muss `False`** bei jedem anderen CWD, wenn die Datei dort fehlt. | Sonst kann ein zukünftiges Refactoring die Konstante wieder relativieren, ohne dass ein Test rot wird — exakt das, was diesen Bug unbemerkt ließ (12 Akzeptanz-Tests in `test_arm.py`, keiner prüft CWD). |
| **D4** | Daemon-Restart nach Commit, **vor** Push (nicht nach). | Der lebende Prozess (PID 4243) hat das **alte** `DEFAULT_ARM_PATH`-Modul-Attribut importiert (Python-Modul-Cache, `run.py:57`). Ein Push allein aktiviert den Fix nicht — erst ein SIGTERM + `nohup run_discovery.sh` lädt den neuen Modul-Code. Der Restart ist die **Verifikation** des Fixes (erster Cycle muss `armed: true` schreiben). |

**Cross-Phase-Freigabe-Status:** keine Änderung — alle Edits sind innerhalb von
`phase14_discovery/`, kein Touch außerhalb.

---

## §3 Der Befund mit verifizierten Ankern

> Alle Zeilennummern **selbst gegrept am 2026-08-26**, Stand `11f18c4` (`b9327ca` auf
> origin/main). Vor jedem Edit: einmal per Grep auf den zitierten **Verbatim-String**
> gegenprüfen — der ist der eigentliche Anker, die Zahl nur die Abkürzung.

### §3.1 Die Pfad-Drift

```
arm.py:55     DEFAULT_ARM_PATH = Path("data") / "state" / "DISCOVERY_ARMED"           ← RELATIV, Bug-Quelle
run.py:62     _REPO_ROOT = Path(__file__).resolve().parents[2]                       ← richtig (Muster)
run.py:63-66  _DEFAULT_PID_PATH / _DEFAULT_STATE_PATH / _DEFAULT_UNIVERSE_DB_PATH /
              _DEFAULT_BARS_DB_PATH = _REPO_ROOT / "data" / ...                      ← richtig (4x)
api.py:49-50  _REPO_ROOT = Path(__file__).resolve().parents[2]                       ← richtig
api.py:57     _ARM_PATH = _DATA_DIR / "state" / "DISCOVERY_ARMED"                    ← richtig (absolut)
api.py:11-13  DB read-only via mode=ro (UI-Konsens: WebUI schreibt nur Dateien, D11) ← unverändert
```

**Drift-Befund:** sechs Stellen konstruieren den ARM-Pfad. **Eine** (arm.py:55) tut es
relativ. `run.py` hat den Fix für seine **eigenen** vier Default-Pfade
(konsistent), aber **importiert** die ARM-Pfad-Konstante aus `arm.py` und benutzt sie
als `--arm-file`-Default (`run.py:300`) — die Drift **infiziert** damit auch den
Daemon-CLI, nicht nur die Library-Funktion `is_armed()`.

### §3.2 Wie der CWD zuschlägt

```
run_discovery.sh:43-44  PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
                       cd "$PROJECT_DIR"                                              ← CWD = phase14_discovery/
arm.py:55              DEFAULT_ARM_PATH = Path("data") / "state" / "DISCOVERY_ARMED" ← RELATIV
                       ⇒ Auflösung im Daemon-Prozess:
                          /home/trading-bot/trading-bot/phase14_discovery/data/state/DISCOVERY_ARMED
                       ⇒ Datei existiert dort NICHT (existiert nur auf Repo-Root-Ebene)
                       ⇒ is_armed() returnt IMMER False
```

**Reproduktion, eine Zeile:**

```bash
cd /home/trading-bot/trading-bot/phase14_discovery && \
    /home/trading-bot/trading-bot/phase1_broker_wrapper/.venv/bin/python \
        -c "from source_registry.arm import is_armed, DEFAULT_ARM_PATH; \
            print('exists?', DEFAULT_ARM_PATH.exists()); \
            print('is_armed():', is_armed(str(DEFAULT_ARM_PATH)))"
# exists? False
# is_armed(): False
```

Vom Repo-Root aus dieselben zwei Zeilen: `exists? True` / `is_armed(): True` (heute
gemessen, identisch zur WebUI-Anzeige `armed: true`).

### §3.3 Was die Indikatoren zeigen (heute gemessen, 2026-08-26 07:45 UTC)

| Quelle | Wert | Interpretation |
|---|---|---|
| `data/state/DISCOVERY_ARMED` (Datei) | `{"armed": true, "by": "dashboard", "ts": "2026-08-25T12:12:38.984889+00:00"}`, 84 bytes, mtime 2026-08-25 14:12:38 CEST | Bediener hat gestern scharf gestellt |
| `data/state/discovery_state.json` (Daemon-Write) | `{"ts_utc": "2026-08-26T07:42:20.689Z", "armed": false, "stale_count": 0, "rows_written": 0, "errors": []}`, mtime 09:42 lokal | Letzter Daemon-Cycle las die Flag-Datei als **nicht armed** |
| `GET /api/discovery` (WebUI, akut gepolt) | `{"armed": true, "armed_ts": "2026-08-25T12:12:38.984889+00:00", "last_run_utc": "2026-08-26T07:42:20.689Z", "last_rows_written": 0, "rows_total": 22, "rows_by_source": {"yf": 22}, "stale_rows": 17}` | UI zeigt armed, meldet aber **17 stale rows** ohne Verarbeitung |
| `instrument_source_availability` (DB) | 22 Zeilen, davon 17 mit `last_verified_utc` ≤ 2026-08-17 (älter als die 7-Tage-TTL), 5 mit Update 2026-08-25 15:22 (= Set-Symbol-Projektion, nicht Discovery) | Daten sind da, aber 17 Zeilen formal stale und nicht durch Discovery erneuert |
| Scheduler (PID 17018, `--enable-divergence-sampler`) | 4 saubere Cycles heute 09:21–09:41, 0 Crashes | A1-`stale_source`-Fix hält; Beweiswoche läuft |

**Fazit:** das Problem ist **nicht** „Daemon hat den ARM verpasst", sondern **„Daemon
liest strukturell am falschen Ort"** — derselbe CWD-Falle-Mechanismus würde bei jedem
Modul-Cache-Refresh wieder zuschlagen.

### §3.4 Warum die Tests das nicht fingen (analog P12.5 §1, „Testlücke")

`test_arm.py` (12 Tests, alle grün) prüft die `is_armed()`-Logik gegen **explizite
Pfade**: jeder Test konstruiert eine eigene Datei in `tmp_path` und übergibt den Pfad
als `is_armed(str(tmp_path / "DISCOVERY_ARMED"))`. **Kein einziger Test** ruft
`is_armed()` mit `DEFAULT_ARM_PATH` auf. Damit konnte die Drift von „relativ" zu
„absolut" passieren, ohne dass ein Test rot wurde — exakt das Muster aus P12.5 §1
„123 grüne Tests konnten den Kostenfehler nicht sehen". D3 ist die Antwort: ein neuer
Test ruft `is_armed()` über den **Modul-Default** und prüft das Resultat unabhängig
vom aktuellen CWD.

---

## §4 Schritte (zwei Atome)

> **Commit nach jedem Schritt.** Nach jedem Schritt `pytest phase14_discovery/tests -q` —
> ein Schritt ist nicht fertig, bevor seine Tests grün sind.

### Schritt 1 — Plan + Doku-Indizierung (1 Commit, nur Markdown)

**Geänderte Dateien:**
- `phase14_discovery/PHASE14_C_DAEMON_CWD_BUG_PLAN.md` (NEU, dieses Dokument)
- `docs/INDEX.md` — One-Liner für den neuen Plan (Konvention, jedes neue `.md` ⇒ eine
  Zeile dazu im selben Commit)
- `phase14_discovery/CLAUDE.md` — `down:`-Link-Liste um den neuen Plan erweitert

**Akzeptanz:** `grep -rn "PHASE14_C_DAEMON_CWD_BUG_PLAN" phase14_discovery/ docs/`
findet genau diesen Plan + den `down:`-Eintrag + den `INDEX.md`-Eintrag. Kein
Code-Edit, keine Test-Änderung.

### Schritt 2 — Code + Test (1 Commit)

**Geänderte Dateien:**

`phase14_discovery/source_registry/arm.py`

Anker (Zeile 1-2): die Modul-Docstring-Reihenfolge bleibt.
Anker (Zeile 49-55, der heutige Block):
```python
# Default path matches the Web-UI constant (`_ARM_PATH` in `phase8_scheduler/webui/api.py`)
# and the daemon's default. Kept here as a single source of truth — modules that need it
# import this constant; never duplicate the literal in another file.
DEFAULT_ARM_PATH = Path("data") / "state" / "DISCOVERY_ARMED"
```
⇒ ersetzen durch (D1-Muster: `run.py:62`):
```python
# Module resolves the canonical repo root via ``Path(__file__).resolve().parents[2]`` —
# the same pattern ``run.py:62`` and ``webui/api.py:49`` already use for their own
# absolute default paths. ``run_discovery.sh`` cds into ``phase14_discovery/`` before
# ``exec python -m source_registry.run``; a relative path here would resolve to
# ``phase14_discovery/data/state/DISCOVERY_ARMED`` (does not exist) and the daemon
# would silently stay unarmed despite the operator having set the file. Fixed
# 2026-08-26 (P14-C plan §3.1) — D1/D2.
_REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_ARM_PATH = _REPO_ROOT / "data" / "state" / "DISCOVERY_ARMED"
```

**Kein** anderer Edit in `arm.py` — `is_armed()`/`arm()`/`disarm()`/`read_state()`
bleiben bit-identisch (`str(DEFAULT_ARM_PATH)` weiterhin zulässig; `Path`-Objekte
akzeptieren beide String- und Path-Vergleiche).

`phase14_discovery/tests/test_arm.py`

Neue Tests am Ende der Datei (Reihenfolge: nach den 12 bestehenden, vor
`@pytest.fixture`-Helfern):

```python
# ---------------------------------------------------------------------------
# P14-C (Daemon-CWD-Path-Bug): CWD-independence of DEFAULT_ARM_PATH.
# Reproduces the production setup: run_discovery.sh cds into phase14_discovery/
# before exec'ing the daemon. Without the absolute path, is_armed() resolves
# the file under the wrong directory and silently returns False.
# ---------------------------------------------------------------------------


def test_default_arm_path_is_absolute() -> None:
    """DEFAULT_ARM_PATH must not depend on the caller's CWD (D1/D2)."""
    assert DEFAULT_ARM_PATH.is_absolute()


def test_is_armed_uses_default_path_independent_of_cwd(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    """``is_armed()`` with the module default must read the file at its absolute
    location, even when the caller's CWD is a subdirectory of the repo (the
    production scenario after ``run_discovery.sh`` cds into ``phase14_discovery/``).

    Strategy: monkeypatch the module-level default to point at ``tmp_path``, drop
    a valid arm payload there, chdir into a subdirectory, then call ``is_armed()``
    with ``str(DEFAULT_ARM_PATH)``. The function must still see the file because
    it resolves the default as an absolute path; a relative default would now
    resolve against the chdir'd CWD and miss the file.
    """
    arm_file = tmp_path / "DISCOVERY_ARMED"
    arm_file.parent.mkdir(parents=True, exist_ok=True)
    arm_file.write_text('{"armed": true, "by": "test", "ts": "2026-08-26T00:00:00+00:00"}',
                        encoding="utf-8")
    monkeypatch.setattr("source_registry.arm.DEFAULT_ARM_PATH", arm_file)
    # Reproduce the production CWD (cd into phase14_discovery/ before exec).
    sub = arm_file.parent / "phase14_discovery" / "source_registry"
    sub.mkdir(parents=True, exist_ok=True)
    monkeypatch.chdir(sub)
    assert is_armed(str(DEFAULT_ARM_PATH)) is True


def test_is_armed_default_false_when_no_flag_file(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    """Without a flag file at the module default, even from a non-repo CWD,
    ``is_armed()`` must return False (safe direction, D10)."""
    monkeypatch.setattr("source_registry.arm.DEFAULT_ARM_PATH",
                        tmp_path / "nonexistent" / "DISCOVERY_ARMED")
    monkeypatch.chdir(tmp_path / "phase14_discovery")
    assert is_armed(str(DEFAULT_ARM_PATH)) is False
```

**Akzeptanz Schritt 2:** `pytest phase14_discovery/tests -q` → vorher 22 (oder aktuelle
Phase-14-Zahl), nachher +3 = 25 grün. Σ-Sweep über alle 14 Suiten unverändert (kein
Cross-Phase-Edit).

### Schritt 3 — Daemon-Restart (Operator, Nikinger)

Nicht in einem Commit — ein bewusster Operator-Schritt nach Push-Freigabe. Skript:

```bash
# 1. SIGTERM an den alten Daemon (graceful — run.py:352-353 → request_stop())
kill 4243
# 2. Warten auf sauberen Exit (max 5 s, dann SIGKILL als Fallback)
sleep 5
# 3. PID-File weg? Sollte sein (run.py:361).
ls -la /home/trading-bot/trading-bot/data/state/discovery.pid  # erwartet: No such file
# 4. Neustart via den kanonischen Wrapper
nohup bash /home/trading-bot/trading-bot/phase14_discovery/scripts/run_discovery.sh \
    >> /home/trading-bot/trading-bot/data/state/discovery.log 2>&1 &
# 5. Verify (siehe §5 Akzeptanz)
```

Alternative, falls der Nikinger die Restart-Helper aus Session 10 mag:

```bash
bash /home/trading-bot/trading-bot/scripts/restart-services.sh restart --dry-run   # erst Preview
bash /home/trading-bot/trading-bot/scripts/restart-services.sh restart             # dann echt
```

Der Helper berührt `data/state/DISCOVERY_ARMED` nicht (sticky) und startet die
Daemons in Start-Reihenfolge (data_foundation → source_registry → scheduler → uvicorn)
mit Sleep dazwischen (Parallel-Login-Falle-Konvention).

**Akzeptanz Schritt 3:** siehe §5.

---

## §5 Akzeptanz (PASS-Kriterien)

| # | Kriterium | Wie belegt |
|---|---|---|
| **A1** | `DEFAULT_ARM_PATH.is_absolute() is True` | `test_arm.py::test_default_arm_path_is_absolute` |
| **A2** | `is_armed()` mit Modul-Default findet die Flag-Datei **unabhängig vom CWD** | `test_arm.py::test_is_armed_uses_default_path_independent_of_cwd` |
| **A3** | Fehlende Flag-Datei bleibt fail-soft (`False`), auch aus Subdir-CWD | `test_arm.py::test_is_armed_default_false_when_no_flag_file` |
| **A4** | Daemon-Cycle nach Restart schreibt `armed: true` (nicht `false`) in `discovery_state.json` | `cat data/state/discovery_state.json` direkt nach Restart + erstem Cycle (max `interval_s` = 3600, in der Praxis ~10 s für den ersten Cycle) |
| **A5** | `stale_count > 0` (17 erwartet) und `rows_written > 0` (für die yF-Projektion — alle 5 aktiven Epics + 12 weitere) | selbe Datei wie A4, ein Cycle später |
| **A6** | Σ-Sweep über alle 14 Suiten unverändert | `pytest` je Phase separat, Tabelle in Session-Block |

**Nicht Teil der Akzeptanz** (bewusst): Capital.com-Discovery (B1b — wartet auf
Operator-Probe), Dukascopy (D15 des Mutterplans, P15-Territorium), `enable_ig_bars`
(Phase-9-Flag, nicht Phase-14). Alles unverändert.

---

## §6 Out of Scope

- **`run_discovery.sh`-CWD-Logik anfassen.** Das Skript `cd`'t in `phase14_discovery/`
  aus einem **anderen** Grund: das `pyproject.toml` definiert `source_registry` als
  Paket-Root (`packages.find include=["source_registry*"]`), und der editable Install
  macht `python -m source_registry.run` von überall aus lauffähig — der CWD-Wechsel ist
  **kosmetisch-konsistent** mit den Geschwistern `run_recorder.sh` und `run_scheduler.sh`,
  nicht die Ursache des Bugs. Es zu entfernen würde Cross-Phase-Drift einführen.
- **WebUI-Pfad (`api.py:57`) anfassen.** Schon korrekt absolut; eine Änderung wäre
  Drift zum `arm.py`-Default, nicht Verbesserung.
- **`run.py:300` (`--arm-file default=str(DEFAULT_ARM_PATH)`).** Übernimmt den
  absoluten Pfad automatisch aus `arm.py` nach D1. Kein separater Edit.
- **`is_armed()`/`arm()`/`disarm()`/`read_state()` API.** Unverändert.
- **Live-DB-Migration 007.** Nicht angefasst.
- **Discovery-Daemon sonstige Defaults (`interval_s`, `max_probe_calls_per_run`,
  `profile_ttl_days`).** Unverändert.
- **Phase-14-D5-Closeout-Handover.** Wartet weiter auf Phase-13-Beweiswoche, nicht
  auf diesen Fix.

---

## §7 Fehlgriffe, die wie andere Fehler aussehen

| Symptom | Erster Verdächtiger | Wie unterscheiden |
|---|---|---|
| **„Daemon sieht armed=false trotz Dashboard-true"** | DISCOVERY_ARMED wurde versehentlich geleert | `cat data/state/DISCOVERY_ARMED` zeigt `{"armed": true, …}` ⇒ nicht das. Dann Bug dieser Plan-Datei (CWD) — `monkeypatch.chdir(phase14_discovery)` reproduziert. |
| **„Discovery schreibt nichts, allowance sieht trotzdem frisch aus"** | Universe-Refresh hat die Projektionen schon gemacht | `last_verified_utc` der 5 `active`-Epics = `2026-08-25T15:22:20` (Set-Symbol-Projektion, `phase9_universe/universe/store.py`); die 17 stale Zeilen sind die `verified`-Epics — Discovery muss sie erneuern. |
| **„Test grün, aber Live-Bug bleibt"** | Daemon hat noch das alte Modul im Cache | `ps aux \| grep source_registry.run` zeigt eine PID mit Startzeit **vor** dem Fix-Commit ⇒ Restart nötig (D4). |
| **„Nach dem Restart: armed=true, aber stale_count bleibt 0"** | TTL-Schwelle falsch konfiguriert (D14 des Mutterplans) | `stale_rows` rechnet lexikografisch über `last_verified_utc < cutoff_iso`. `cutoff_iso = now - 7d`. Die 17 Zeilen aus 2026-08-17 sind älter als `now - 7d = 2026-08-19`. ⇒ Echte Stale. Wenn der Daemon `stale_count=0` schreibt, hat er die `cutoff_iso`-Berechnung nicht ausgeführt — neuer Bug, melden. |
| **„Restart-Skript löscht DISCOVERY_ARMED"** | `restart-services.sh` hat einen `--clear`-Flag, den der Bediener gesetzt hat | Skript hat **keinen** solchen Flag (Session 10 Commit `c97e82a`, §3: „`data/state/KILL` und `data/state/DISCOVERY_ARMED` nie angefasst"). Wenn es doch passiert: manueller Re-Arm via `echo '{"armed": true, "by": "operator", "ts": "..."}' > data/state/DISCOVERY_ARMED`. |
| **„`is_armed()` aus einem Test klappt, aber im Daemon-Prozess nicht"** | `monkeypatch` hat den Test-Pfad überschrieben, aber nicht den Daemon-Pfad | `run.py:300` liest `str(DEFAULT_ARM_PATH)` **bei Prozessstart**. Wenn der Daemon vor dem Fix gestartet wurde, ist `DEFAULT_ARM_PATH` im Prozess-Speicher der **alte** relative String. Restart löst es (D4). |

---

## §8 Drift-Liste — bei Ausführung verifizieren

> **Diese Liste ist vollständig.** Was hier nicht steht, hat diese Planungssession am
> 2026-08-26 selbst gegen das Repo, den Live-Prozess und einen CWD-Wechsel geprüft und
> ist als Fakt formuliert. Rate nichts nach; prüfe diese und nur diese.

1. **Zeilennummern verschieben sich.** Jeder Anker oben trägt den **Verbatim-String** —
   der ist der Anker, die Zahl ist die Abkürzung. Schritt 2 verschiebt `arm.py` selbst;
   Schritt 1 verschiebt `phase14_discovery/CLAUDE.md` (Header + `down:`-Liste).
   **Immer per String suchen.**
2. **`run.py:62` ist das Vorbild.** Es benutzt `Path(__file__).resolve().parents[2]` für
   `_REPO_ROOT` und konstruiert **alle vier** seiner Modul-Defaults daraus
   (`_DEFAULT_PID_PATH`, `_DEFAULT_STATE_PATH`, `_DEFAULT_UNIVERSE_DB_PATH`,
   `_DEFAULT_BARS_DB_PATH`). Das ist der Pattern-Standard; arm.py weicht davon ab. Heute
   gegrept: keine weitere Stelle in `phase14_discovery/source_registry/` verwendet
   einen relativen Default-Pfad.
3. **`api.py:50` benutzt eine andere Schreibweise:** `_DATA_DIR = _REPO_ROOT / "data"`,
   nicht `_REPO_ROOT / "data" / "state" / "DISCOVERY_ARMED"`. Das ist
   **konsistent** (Data-dir-Wurzel separat), keine Drift — beide Stellen landen am
   selben Pfad, solange `_REPO_ROOT` identisch berechnet wird. Der Fix in `arm.py` muss
   **denselben** `parents[2]`-Trick verwenden, sonst landet man auf einer anderen
   Repo-Root.
4. **Live-Prozess-Pfad** (`/proc/4243/cwd`) — heute gemessen: `phase14_discovery/`.
   Bestätigt die Hypothese, dass `run_discovery.sh` den CWD umsetzt. Nicht garantiert,
   dass das nach jedem Restart identisch ist — wer den Daemon von Hand aus dem Repo-Root
   startet, würde keinen Bug sehen (aber dafür hat er den falschen Operator-Workflow).
5. **`arm.py:55`-Import im Mutterplan:** `docs/concepts/phase14_discovery_plan.md`
   §6 C3 verweist auf `phase8_scheduler/webui/api.py:431` für `discovery_state.json` —
   das ist eine **andere** Datei (UI-Read). Der `arm.py:55`-String erscheint im
   Mutterplan nicht explizit (nur §5.4 „Default-Pfad: `data/state/DISCOVERY_ARMED`"),
   deshalb ist die Drift **nicht** ein Vordokument-Konflikt — der Mutterplan sagt nur
   „der Pfad", nicht „wie er aufgelöst wird".
6. **`test_arm.py`-Imports:** heute `from source_registry.arm import (DEFAULT_ARM_PATH,
   arm, disarm, is_armed, read_state)`. `DEFAULT_ARM_PATH` ist bereits importiert; die
   neuen Tests brauchen keine zusätzlichen Imports. `monkeypatch.setattr(...)` zielt auf
   den **Modul-Namen im Test-Prozess**, nicht auf den Daemon — die Tests pinnen das
   Verhalten der Library, nicht der Live-Anwendung.
7. **`is_armed(str(...))` vs `is_armed(Path(...))`:** das aktuelle `is_armed()`
   nimmt `str` (`arm.py:58`), `Path(arm_path)` (Zeile 68) konvertiert. Tests reichen
   Strings rein — bleibt kompatibel.
8. **`webui/api.py:431`** liest `data/state/discovery_state.json` (das **vom Daemon
   geschriebene** State-File). Nach Fix + Restart wird diese Datei `"armed": true`
   enthalten — die UI zeigt dann `armed: true` UND `last_rows_written > 0` UND
   `stale_rows` schrumpft. Visuell verifizierbar ohne Code.
9. **Push-Reihenfolge:** Commit `Plan + INDEX + CLAUDE.md.down` zuerst, Commit
   `arm.py + test_arm.py` zweitens, dann **Push-Freigabe** für beide (Nikinger),
   dann **Daemon-Restart** (Nikinger, manuell oder via `restart-services.sh`). Der
   Restart **vor** dem Push wäre ein Live-Change auf einem ungepushten Commit —
   vermeiden.
10. **Session-10-Restart-Hygiene:** Commit `c97e82a` (Session 10) hat `run_discovery.sh`
    mit PATH-Prepend ausgestattet, nicht aber mit einem CWD-Reset. Die `cd "$PROJECT_DIR"`-
    Zeile 44 bleibt unverändert (siehe §6, „nicht die Ursache").

---

## §9 Cross-Referenz

- **Mutterplan:** [`../docs/concepts/phase14_discovery_plan.md`](../docs/concepts/phase14_discovery_plan.md) — D1/D2/D11 sind die nächsten Berührungspunkte; der hier gefixte Pfad-Bug ist eine **Impl-Drift** zu D11 („UI schaltet per Datei"), nicht ein Plan-Konflikt. Der Mutterplan bleibt unverändert.
- **Phasenkopf:** [`./CLAUDE.md`](./CLAUDE.md) — Modul-Tabelle trägt den Arm-Stand „✅ C1 (Session 9)". Der Fix ändert **nicht** den Status; das Modul bleibt ✅ — der Bug war eine unentdeckte Lücke im C1-Modul.
- **Geschwister-Snapshot:** [`./PHASE14_B1A_PROBE_OUTPUT_2026-08-22.md`](./PHASE14_B1A_PROBE_OUTPUT_2026-08-22.md) — anderes Sub-Thema, gleiche Doku-Konvention.
- **Session-Archiv:** [`./SESSIONS_ARCHIVE.md`](./SESSIONS_ARCHIVE.md) — die Session-Blöcke 1–10; Session 11 (dieser Fix) wird hier nach Verifikation angehängt.
