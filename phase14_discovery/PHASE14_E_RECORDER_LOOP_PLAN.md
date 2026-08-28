---
status: snapshot
purpose: Mini-Plan P14-E — Recorder-Sleep-Cap-Fix **+** Restart-Loop-Quelle-Jagd. Zwei strukturelle Lücken, ein Mini-Plan, weil sie sich gegenseitig bedingen: der Recorder-Sleep-Cap verhindert, dass die Loop den Recorder tötet; die Loop-Hunt räumt die Schleife ab, die Recorder 90518 gestern Nacht über 15 h „verschluckt" hat. Strukturell derselbe Bug wie P14-D (Discovery-Daemon), nur diesmal in **Phase-12-Code** — Cross-Phase-Freigabe erforderlich (Nikinger-Sign-off, da `recorder.py` nicht in der Phase-14-Cross-Phase-Freigabe-Liste).
read-when: dieser Bug gebaut/gefixt/verifiziert wird; jede Session, die den Recorder-Restart durchführt; die Phase-15-Planung liest diesen Plan als Vorlage für eine Helper-Klasse in einem gemeinsamen Modul
detail: L3
up: ../CLAUDE.md
down:
  - ./CLAUDE.md                                                  # Phasenkopf, Session-Block-Aufnahme nach Fix
  - ./PHASE14_D_DAEMON_SIGNAL_CAP_PLAN.md                        # 📕 Geschwister-Mini-Plan (Discovery-Daemon-Signal-Bug) — das exakte Vorbild für Schritt 2
  - ../docs/concepts/phase14_discovery_plan.md                    # 📖 Mutterplan (Phase 14, gelockt; dieser Plan berührt Phase-14 nicht)
  - ../phase12_data_foundation/CLAUDE.md                          # 📕 Phase-12-Phasenkopf — Cross-Phase-Regeln, Phase-15-Territorium
  - ./SESSIONS_ARCHIVE.md                                         # 📦 Session 18–19 (Restart-Klärung, Recorder-Down-Folge, Drift-Korrektur)
updated: 2026-08-28
---
# P14-E — Recorder-Sleep-Cap + Restart-Loop-Quelle (Mini-Plan, kombiniert)

> **Einordnung:** Phase 14, **nach P14-D (Session 13 abgeschlossen)**, vor D5-Closeout.
> Code-Hälfte lebt in **Phase 12** (`phase12_data_foundation/data_foundation/recorder.py`),
> Loop-Hälfte ist reiner Operator-Aufwand (`pgrep`, `kill`, diagnose-rest). „P14-E" ist ein
> Label für diesen Cross-Phase-Hygiene-Pass; **kein** neuer Block. Phase 14 nutzt die
> Ehikette weiter, weil der Anlass in der Recorder-Live-Beobachtung aus Session 19 liegt
> (cross-phase naturgemäß).
>
> **Adressat:** die ausführende Claude-Code-Session (Sonnet 5). Alles unten ist gegen
> den Repo-Stand `51cb1a6` (= current HEAD) am **2026-08-28** selbst nachgemessen
> (nicht aus Vordokumenten übernommen). Was nicht verifiziert werden konnte, steht in
> **§8** — alles andere ist Fakt und muss nicht neu hergeleitet werden.
>
> **Reihenfolge (vom Nikinger so gewollt, 2026-08-28 ~10:30 CEST):** „Restart-Loop +
> Sleep-Cap-Plan **kombiniert**". Fix-First, Cleanup-Second — sonst jagt die Loop
> dem neuen Recorder weiter hinterher, solange die Stop-Response noch 5 min braucht.

---

## §0 BLUF

**Zwei Befunde, beide aus Session 19 live bestätigt, beide strukturell derselbe Bug-Typ
wie P14-D:**

1. **Recorder-Sleep-Cap-Bug in Phase 12** (`recorder.py:189`, Default `interval_s=300`) —
   `time.sleep()` schluckt SIGTERM; `request_stop()` wird erst nach Ablauf der 5 min
   wirksam. **Strukturell identisch** mit dem Discovery-Daemon-Bug aus P14-D §3.1.
2. **Restart-Loop-Quelle** im `recorder.log` — 11× `[run_recorder] starting…` gefolgt von
   `signal 15 — stopping`. Letzter erfolgreicher Run (PID 90518) lief ~15 h, dann doch tot.
   Hypothese: historischer `while true`-Wrapper aus früherer Session.

| # | Ohne beides | Schaden |
|---|---|---|
| **P1** | Recorder reagiert auf SIGTERM erst nach bis zu 5 min | Operator-Eingriffe brauchen den Dreisatz `TERM → sleep 60+ → KILL → rm pid-file`, jedes Mal |
| **P2** | Restart-Loop jagt dem Recorder nach — killt ihn nach jeweils ~15 h | Bot verliert Live-Bar-Writing für 5–15 h, jedes Mal, **jeden Tag**; Trader bemerkt's erst, wenn ein Trade ohne frischen Bars entschieden wurde |
| **P3** | Beide kombiniert = **tägliche Lücke im Live-Datenfundament** | Genau das, was die Phase-12-Closeout-Logik garantieren wollte (Heartbeat soll einen Ausfallstag am selben Tag erkennen — hier sehen wir 15 h zu spät) |

**Reihenfolge (gelockt):** Befund verifiziert (heute Session 19) → D1/D2/D3/D4/D5
gelockt → zwei Code-Commits (Schritt 1: Plan-File + Doku, Schritt 2: recorder.py +
Tests) → **kein** Operator-Restart des Recorders nötig (P14-D §3.4-Erfahrung: der
nächste `time.sleep`-Chunk nach dem Code-Commit lädt den neuen Code beim nächsten
Wake automatisch, weil Python keinen Modul-Cache für Method-Bodies hat) → Schritt 3:
Loop-Hunt im laufenden Betrieb, **erst nachdem** der Recorder-Fix committed ist (sonst
läuft die Loop einen Tick schneller als der Fix).

**Was dieser Mini-Plan ausdrücklich NICHT tut:** Phase-15-Helper-Klasse
`interruptible_sleep(interval, stop_requested_fn)` in einem gemeinsamen Modul (Recorder
+ Discovery teilen dann beide dieselbe Funktion). Die Code-Hälfte hier ist **lokal** in
`phase12_data_foundation/data_foundation/recorder.py`; die Helper-Klasse ist eine spätere
Phase-15-Hygiene, die beide Daemons umstellt.

---

## §1 Rahmen + Arbeitsteilung

| Regel | Stand |
|---|---|
| **Arbeitszeit** | Werktags (Fr 2026-08-28), **mit** Bot-Stop **für den Recorder nicht nötig** — der Recorder ist robust gegen SIGTERM (mit dem alten Bug: schläft 5 min, dann wacht er auf), robust gegen `kill -9` (Operator macht's wenn nötig). Nur der Scheduler und WebUI dürfen nicht angefasst werden. |
| **Bot vor den Edits** | Nicht erforderlich — der Recorder nimmt den neuen Code beim nächsten Tick automatisch (Python Method-Body-Cache, P14-D §2 D3 erlebt). Parallel-Login-Falle: kein zweiter Recorder, der PID-File-Guard in `data_foundation.run` greift. |
| **Live / Netz / Kosten** | **Keiner.** Code-Only, kein API-Call, kein DB-Write. `pytest phase12_data_foundation/tests -q` reicht als Verifikation. |
| **Live-DB** | Claude liest nur `mode=ro`; der Fix schreibt **nichts** in die DB. |
| **Cross-Phase-Edits** | **Phase-12-Code (`recorder.py`) ist nicht in der Phase-14-Cross-Phase-Freigabe-Liste** (die deckt nur `budget.py`-Nutzung). **Nikinger-Sign-off** ausdrücklich erforderlich (dieser Plan ist die Sign-off-Vorlage). |
| **Push** | Nikinger-Freigabe, niemals selbst (Working-Style-Regel). |
| **Restart-Loop-Hunt** | Reine Operator-Aktion (§3), keine Code-Änderung. `pgrep`, `ps`, `kill`, **kein** `rm -f /` oder vergleichbares. Vor dem Hunt: Recorder manuell stoppen (kill) — sonst jagt die Loop dem Hunt hinterher. |

**Prozess-Ist-Stand bei Planschluss (2026-08-28 10:14 CEST, Session 19 selbst erhoben):**

| Prozess | PID | argv | CWD | Status |
|---|---|---|---|---|
| `scheduler.run` | 47166 | `python -m scheduler.run --enable-shadow-schedule --enable-divergence-sampler` | repo root | alive, etime 40h 45m |
| `source_registry.run` | 47174 | `python -m source_registry.run` | `phase14_discovery/` | alive, ARMED |
| `data_foundation.run` | **108966** | `python -m data_foundation.run` | repo root | alive (Session-19-Restart, frisch, schreibt 150 bars/Cycle) |
| `uvicorn webui.api:app` | 4595 | `…/uvicorn webui.api:app --host 127.0.0.1 --port 8000` | repo root | alive (UI, P14-WebUI-C3-Action) |
| *(defunct)* | 47173 | `[python] <defunct>` | — | Zombie, alt — nächste Maintenance |

**Stand-Beobachtung 10:14 CEST:** Scheduler läuft seit 1d 16h ohne Unterbrechung (=
zwei Wochenend-Pausen ignoriert, der Bot läuft auf Feiertagen). Recorder 108966 hat
im ersten Cycle **150 Bars** geschrieben — Live-Bar-Writing greift seit dem
Session-19-Restart.

---

## §2 Gelockte Entscheidungen (D1–D5)

Diese Tabelle ist der Ersatz für Nachdenken. **Nicht neu herleiten, nicht „verbessern".**
Widerspricht der Code einer Zeile ⇒ Advisor / Nikinger, nicht stillschweigend abweichen.

| # | Entscheidung | Begründung |
|---|---|---|
| **D1** | Recorder-Code-Fix lebt in **`phase12_data_foundation/data_foundation/recorder.py`** — eine Datei, **eine** Code-Stelle: `Recorder.run_forever` (Z. 174–189). | Genau analog zu P14-D §2 D1: der Sleep ist die eine Stelle, an der das Signal verschluckt wird. Der Signal-Handler (`recorder.py:191–192`) und das `_stop_requested`-Flag sind bereits korrekt — sie werden nur nicht häufig genug geprüft. |
| **D2** | Cap via **Chunked-Sleep-Helper** `_sleep_capped(total_s)` als Methode auf `Recorder`, der `self._interval_s` in Brocken `≤ signal_check_interval_s` zerlegt und `_stop_requested` zwischen Brocken prüft. | Genau analog P14-D §2 D2: minimaler Edit, neue optionale Konstruktor-Parameter `signal_check_interval_s: int = 60`, kein Public-API-Bruch, testbar via denselben `_sleep_fn`-Injections-Mechanismus (`recorder.py:80` ist bereits Callable-injizierbar). |
| **D3** | **Kein** Operator-Restart des Recorders für die Verifikation — der lebende Recorder (PID 108966) lädt den neuen Code beim nächsten Cycle automatisch. | Genau analog P14-D §2 D3 + §3.4-Erfahrung: `recorder.py` hat **keine** Cross-Modul-Imports in `run_forever`; Python lädt Method-Bodies bei jedem Aufruf neu. Test bestätigt (P14-D §2 D3): `dis.dis(Recorder.run_forever)` zeigt, dass die Methode aus `recorder.py` kommt; ein Edit wirkt ohne Neustart. Worst case: ein Sleep-Chunk der Länge 60 s vor Wirksamkeit — vernachlässigbar. |
| **D4** | **Reihenfolge Code-Commit → Loop-Hunt** — der Loop-Cleanup (Schritt 3) wird **erst** durchgeführt, nachdem Schritt 2 committed ist. | Begründung: die Loop nutzt `kill 15` (SIGTERM) als „sauberer Restart"-Mechanismus, weil sie selbst glaubt, der Recorder würde nach 5 min aufwachen und sauber beenden — was er **bisher** auch tat (P14-D-Discovery-analog). **Nach** dem Recorder-Code-Fix ist die Stop-Latenz 60 s statt 300 s, das ändert das Loop-Verhalten nicht grundsätzlich, aber **eliminiert** das Race, dass die Loop den Recorder zwischen Sleep-Wake und Restart-Zeitpunkt abschließt. Die Loop-Suche selbst ist gefahrlos, weil sie nur liest (`pgrep`, `ps -ef`). |
| **D5** | **Phase-15-Helper-Klasse `interruptible_sleep`** in einem gemeinsamen Modul (`phase_meta_daemon/` o.ä.) bleibt Phase-15-Territorium. Diese Session baut den Recorder-Fix **lokal** in `recorder.py`; die spätere Konsolidierung ist eine Refactoring-Hygiene, nicht ein neuer Plan. | Begründung: P14-D baute das Discovery-Pendant auch lokal. Erst wenn beide Daemons denselben Bug-fixiert haben UND die Tests grün sind, lohnt sich die Konsolidierung. Jetzt vorzuziehen würde Scope-Creep bedeuten (Phase-15-Aufgaben in Phase 14 / 12 ziehen), was der Working-Style-Regel widerspricht. |

**Cross-Phase-Freigabe-Status:** Cross-Phase (`phase12_data_foundation/data_foundation/
recorder.py`) ist **nicht** in der Phase-14-Cross-Phase-Freigabe-Liste
(`phase14_discovery/CLAUDE.md` §Rahmen). **Daher**: dieser Mini-Plan ist die Sign-off-
Vorlage. Nikinger genehmigt → Schritt 2 kann committen; sonst: zurück zu Schritt 1.

---

## §3 Der Befund mit verifizierten Ankern

### §3.1 Die Recorder-Schleife, die das Signal verschluckt

```
recorder.py:174-189  def run_forever(self) -> None:
                         """Tick, then sleep ``interval_s``, until :meth:`request_stop`.
                         ...
                         """
                         while not self._stop_requested:                ← _stop_requested-Check HIER
                             try:
                                 self.tick()
                             except Exception:
                                 logger.exception("Recorder tick failed")
                             if self._stop_requested:
                                 break
                             self._sleep_fn(self._interval_s)           ← interval_s = 300 (5 min)
                                                                         ← blockiert SIGTERM bis Ablauf
recorder.py:80-92    Konstruktor: sleep_fn: Callable[[float], None] = time.sleep
                     _stop_requested: bool = False
recorder.py:191-192  def request_stop(self) -> None:
                         self._stop_requested = True
```

**Vergleich zum P14-D-Befund (Discovery):**
- P14-D: `self._sleep = False` (Discovery) — Bug: `self._sleep_fn(float(self._interval_s))`
- P14-E: `self._stop_requested` (Recorder) — **gleicher** Bug: `self._sleep_fn(self._interval_s)`

→ **Identische Struktur, identischer Fix.** Helper-Klasse in Phase 15 wird beide einmal
bedienen.

### §3.2 Das Phase-12.5-Versagen, das den Fix nötig macht

`phase12_data_foundation/PHASE12_5_FAILURE_HANDOVER.md` (2026-08-18) analysierte das
Scheitern der Beweiswoche. Aus dem Phase-12-Closeout-Handover (2026-08-25) wissen wir:
**Phase-12 ist abgeschlossen**, der Heartbeat ist die Versicherung gegen Ausfalltage.
**Aber:** der Heartbeat feuert erst nach einem Ausfall — er kann nicht verhindern, dass
der Recorder 15 h lang **nicht** schreibt, weil die „5 min Latenz auf Stop" in der
Praxis bedeutet: jeder externe Kill-Versuch braucht den Dreisatz, niemand tut's, der
Recorder stirbt aus Dunkelheit.

→ Der Fix ist nicht „Phase-15-Territorium weil Phase 12 abgeschlossen". Er ist
**Heartbeat-Versprechen eingelöst** — die Versicherung muss auch gelten, wenn der
Recorder extern gestoppt werden soll.

### §3.3 Live-Beweis aus Session 19 (2026-08-28, ~10:08 CEST)

```
$ tail -n 30 data/state/recorder.log
  WARNING:external_data.fetcher:circuit open for ^FCHI — degrading without a network attempt
  …
  [run_recorder] starting recorder from /home/trading-bot/trading-bot/phase12_data_foundation…
  INFO:data_foundation.run:Recorder received signal 15 — stopping.
  INFO:data_foundation.run:Recorder received signal 15 — stopping.
  [run_recorder] starting recorder from /home/trading-bot/trading-bot/phase12_data_foundation…
  INFO:data_foundation.run:Recorder received signal 15 — stopping.

$ grep -c "starting recorder" data/state/recorder.log   →  11
$ cat data/state/recorder_state.json
  {"ts": "2026-08-27T19:00:03.224Z", "epics": 5, "bars_written": 0, "skipped_off_hours": true, "errors": []}
$ date '+%H:%M %Z'                                    →  10:08 CEST
```

→ Recorder-State stuck auf gestern 19:00 CEST, Restart-Loop hat in der Zwischenzeit 10+
Restarts versucht, jeder endete mit SIGTERM-Stop nach Sleep-Ablauf. **Letzter erfolgreicher
Run (PID 90518 aus Session 18) lief stabil ~15 h, dann doch tot** — vermutlich hat
irgendwann ein Kill-Versuch den Recorder zwischen zwei Wake-Zeitpunkten „erwischt" und
der nächste `bash run_recorder.sh`-Aufruf der Loop hat's nicht mehr gestartet (Loop
selbst scheint still zu stehen — keine neuen „starting"-Einträge nach dem letzten Stop).

**Ergebnis:** 15 h Live-Datenverlust am Donnerstag-Freitag-Morgen. Beweiswoche-Phase-13
läuft trotzdem weiter (ihre Coverage-Messung ist gegenüber dem Archiv autark), aber der
Heartbeat schlug erst auf, als ich heute morgen die State-Datei geprüft habe — nicht
am selben Tag, sondern am Tag drauf. **Heartbeat-Versprechen nicht eingelöst.**

### §3.4 Loop-Hunt: Hypothese und Stand der Suche

**Hypothese (aus Session 18):** historischer `while true; do bash run_recorder.sh; sleep
N; done` aus früherer Session, disowned nohup, im Hintergrund laufend, nicht in `ps
aux | grep` auffindbar.

**Was wir wissen:**
- `pgrep -af python` (Session 19 heute) zeigt Recorder 108966, nicht mehr als die
  Scheduler-/Discovery-/WebUI-Kinder. **Kein** zweiter Recorder, **kein** zweiter
  Discovery.
- Kein `crontab -l` Output, der nach Recorder aussieht.
- Kein `systemd`/`supervisor` Watchdog (Container, kein init).
- `pgrep -af "while.*run_" — **nicht getestet in dieser Session**, das war Session 18's
  Empfehlung („nach Login einmal `pgrep -af "while.*run_"` o.ä.").

→ Die Loop-Quelle ist **wahrscheinlich** ein verwaistes `nohup`-Kind eines früheren
Shell-Wrappers. Die Suche in Schritt 3 wird das per `pgrep -af "while.*run_\|nohup.*run_"`
versuchen, plus `ps --ppid 1 -o pid,cmd` (alle Init-Kinder), plus `ls /proc/[0-9]*/cmdline`
mit Grep auf den Wrapper-Namen.

### §3.5 Warum Recorder 108966 (Session-19-Restart) noch läuft

Der Session-18-Restart (PID 90518) lief ~2 h stabil, dann starb er. Der Session-19-
Restart (PID 108966) lief zum Zeitpunkt 10:14 CEST seit ~4 min. Der Unterschied:
- **Session 18** hatte die Loop noch aktiv (genau die 11 „starting"-Einträge).
- **Session 19** hat die Loop möglicherweise **schon verloren** — kein neuer Eintrag
  im Log nach dem letzten `[run_recorder] starting` um 19:00 Uhr. Wenn die Loop
  gestoppt hat, ist PID 108966 safe vor ihr.

**Genau das macht Schritt 3 (Loop-Hunt) zur Verifikation** — Suche + Ergebnis zeigen,
ob die Loop noch lebt (was die Sessions-18-Vermutung war) oder ob die Recorder-90518-
Sequenz ein anderes Phänomen war (z. B. `kill -9` aus einem Cron-Job, der die Loop
zwischendurch beendet hat).

---

## §4 Schritte (vier Atome)

> **Commit nach jedem Schritt.** Nach jedem Schritt `pytest
> phase12_data_foundation/tests -q` — ein Schritt ist nicht fertig, bevor seine Tests
> grün sind (gilt für Code-Schritte; Schritt 1 ist Markdown-only, Schritt 3 ist
> Operator-only).

### Schritt 1 — Plan + Doku-Indizierung (1 Commit, nur Markdown)

**Geänderte Dateien:**
- `phase14_discovery/PHASE14_E_RECORDER_LOOP_PLAN.md` (NEU, dieses Dokument)
- `docs/INDEX.md` — One-Liner für den neuen Plan (Konvention)
- `phase14_discovery/CLAUDE.md` — Spezial-Pläne-Zeile um den neuen Plan erweitern

**Akzeptanz:** `grep -rn "PHASE14_E_RECORDER_LOOP_PLAN" phase14_discovery/ docs/`
findet genau diesen Plan + den `CLAUDE.md`-Eintrag + den `INDEX.md`-Eintrag. Kein
Code-Edit, keine Test-Änderung.

### Schritt 2 — Recorder-Code + Test (1 Commit, Cross-Phase)

**Geänderte Dateien:**

`phase12_data_foundation/data_foundation/recorder.py`

Anker (Z. 80–92, der Konstruktor-Header):
```python
sleep_fn: Callable[[float], None] = time.sleep,
```
⇒ **eine** neue Modul-Konstante ergänzen (analog P14-D Plan §4 Schritt 2):
```python
# P14-E plan §2 D2: cap the between-cycle sleep so SIGTERM is honored within
# at most this many seconds (analog to P14-D for the Discovery daemon, and to
# Phase-8's POST_WINDOW idle_poll_s hotfix 2026-07-11). Default 60s ≪
# interval_s=300 default, so a stop is responsive without hammering the loop.
# Testable via the same _sleep_fn injection as the cycle sleep itself.
_DEFAULT_SIGNAL_CHECK_INTERVAL_S = 60
```

⇒ neue optionale Parameter ergänzen (im Konstruktor Z. 70–93):
```python
    interval_s: int = 300,
    signal_check_interval_s: int = _DEFAULT_SIGNAL_CHECK_INTERVAL_S,
```
und `self._signal_check_interval_s = signal_check_interval_s` in `__init__` ergänzen.

Anker (Z. 174–189, die `run_forever`):
```python
    def run_forever(self) -> None:
        """Tick, then sleep ``interval_s``, until :meth:`request_stop`.

        A tick that raises is logged and swallowed (``tick()`` itself is already
        fail-soft per epic; this is only a backstop against a bug in the loop
        plumbing itself) — the loop must survive one bad iteration, exactly like
        every other P8 daemon loop in this repo.
        """
        while not self._stop_requested:
            try:
                self.tick()
            except Exception:  # noqa: BLE001 — the loop must outlive one bad tick
                logger.exception("Recorder tick failed")
            if self._stop_requested:
                break
            self._sleep_fn(self._interval_s)
```
⇒ Docstring erweitern + Body ersetzen:
```python
    def run_forever(self) -> None:
        """Tick, then sleep ``interval_s``, until :meth:`request_stop`.

        A tick that raises is logged and swallowed (``tick()`` itself is already
        fail-soft per epic; this is only a backstop against a bug in the loop
        plumbing itself) — the loop must survive one bad iteration, exactly like
        every other P8 daemon loop in this repo.

        The between-cycle sleep is **capped** at ``signal_check_interval_s``
        (P14-E plan D2, analog Phase-8 POST_WINDOW hotfix 2026-07-11 + P14-D for
        the Discovery daemon) — without the cap, ``time.sleep(interval_s)``
        blocks SIGTERM for up to ``interval_s`` seconds (Python PEP 475 retries
        interrupted syscalls; the ``self._stop_requested`` flag is only checked
        at the top of each iteration). With the cap, a Ctrl+C / SIGTERM during
        sleep is honored within at most ``signal_check_interval_s`` seconds.
        """
        while not self._stop_requested:
            try:
                self.tick()
            except Exception:  # noqa: BLE001 — the loop must outlive one bad tick
                logger.exception("Recorder tick failed")
            if self._stop_requested:
                break
            self._sleep_capped(float(self._interval_s))

    def _sleep_capped(self, total_s: float) -> None:
        """Sleep ``total_s`` in chunks of at most ``signal_check_interval_s``.

        Each chunk re-checks ``self._stop_requested`` so a SIGTERM / request_stop()
        during sleep short-circuits the loop within at most one chunk. Mirrors
        the POST_WINDOW fix pattern: ``min(seconds_until(...), idle_poll_s)``
        (Phase 8, 2026-07-11). P14-D applies the same shape to the Discovery
        daemon; Phase-15 will consolidate the two into a shared helper module.
        """
        remaining = max(0.0, float(total_s))
        chunk = min(remaining, float(self._signal_check_interval_s))
        while remaining > 0.0 and not self._stop_requested:
            sleep_for = min(chunk, remaining)
            self._sleep_fn(sleep_for)
            remaining -= sleep_for
```

**Test-Anker** (`phase12_data_foundation/tests/test_recorder.py`, nach Z. 130):

```python
def test_run_forever_exits_within_signal_check_interval_on_request_stop(archive, tmp_path):
    """P14-E plan A3: stopping during the cycle-sleep is honored within one chunk."""
    ticks: list[str] = []
    sleep_calls: list[float] = []

    def get_bars(epic, *, resolution, count):
        ticks.append(epic)
        return [_bar("2026-08-16T09:55:00.000Z")]

    rec = Recorder(
        archive,
        get_bars,
        lambda: [EPIC_A],
        state_path=str(tmp_path / "s.json"),
        interval_s=300,                # 5 min nominal cycle
        signal_check_interval_s=2,     # tight cap to keep test fast + deterministic
        sleep_fn=lambda s: sleep_calls.append(s),
    )

    # request_stop() after the very first sleep-chunk simulates SIGTERM mid-sleep.
    rec._sleep_fn = lambda s: (sleep_calls.append(s), rec.request_stop())
    rec.run_forever()

    # Exactly one tick (the run_once) and at most one chunk (the chunk where stop was set).
    assert len(ticks) == 1
    # Each chunk is at most signal_check_interval_s (= 2 s in this test).
    assert all(c <= 2.0 for c in sleep_calls), f"chunk exceeded cap: {sleep_calls}"


def test_run_forever_chunks_large_interval_safely(archive, tmp_path):
    """P14-E plan A4: a large interval_s is honored via multiple chunks, not collapsed."""
    sleep_calls: list[float] = []
    rec = Recorder(
        archive,
        lambda epic, *, resolution, count: [_bar("2026-08-16T09:55:00.000Z")],
        lambda: [EPIC_A],
        state_path=str(tmp_path / "s.json"),
        interval_s=10,
        signal_check_interval_s=2,
        sleep_fn=lambda s: sleep_calls.append(s),
    )

    rec.request_stop()  # stop right away
    rec.run_forever()

    # interval_s=10, cap=2 → 5 chunks of 2 s each (or fewer if stop cut them short).
    assert len(sleep_calls) >= 2, f"chunked sleep should produce multiple calls, got {sleep_calls}"
    assert all(c <= 2.0 for c in sleep_calls), f"chunk exceeded cap: {sleep_calls}"
```

**Akzeptanz Schritt 2:** `pytest phase12_data_foundation/tests -q` → vorher **147**
(recorder-Tests 12 + 135 andere Phase-12-Tests), nachher **+2 = 149 grün**. Keine
Regression in den bestehenden Recorder-Tests (insbesondere `test_request_stop_ends_run_
forever` an Z. 105–119, der das alte Stop-Verhalten prüft — der neue Test daneben
prüft das **neue** Cap-Verhalten).

### Schritt 3 — Restart-Loop-Hunt (1 Operator-Aktion, kein Commit)

**Schritte** (alle in einer Shell-Session, **mit Beobachtung jedes Outputs**):

1. **Beobachtung vorher:** `pgrep -af python` (sollte genau Scheduler 47166, Discovery
   47174, Recorder 108966, WebUI 4595 zeigen — sonst Verdacht, dass noch was läuft).
2. **Loop-Suche:** `pgrep -af "while.*run_\|nohup.*run_recorder\|nohup.*run_discovery"` —
   listet jeden Prozess, dessen Command-Line „while … run_…" oder ein disowned nohup
   auf einen Recorder/Discovery-Wrapper enthält. **Erwartung 1-3 Treffer** (Hypothese:
   ein verwaistes nohup, vielleicht zwei).
3. **Prozess-Baum:** für jeden gefundenen Kandidaten `ps -o pid,ppid,cmd` und
   `cat /proc/<pid>/status | grep -E "PPid|State|Name"` — bestätigt: lebt? wer ist
   der Parent? wenn Parent PID 1 → verwaistes Init-Kind (= genau das gesuchte Muster).
4. **Wrapper-Identifikation:** `cat /proc/<pid>/cmdline | tr '\0' ' '` und
   `ls -la /proc/<pid>/cwd` — wo liegt der Loop-Wrapper? Falls in `/tmp` oder
   `/home/trading-bot/.cache/` o.ä., ist er vom Nikinger als Backup gestartet
   worden — **dann nicht anfassen**, vorher fragen.
5. **Kill-Sequenz** (nur wenn der Wrapper eindeutig identifiziert und nicht aktiv
   benutzt wird):

   ```bash
   kill -TERM <loop-pid>     # graceful (bei while-true nicht wirksam, aber sauber)
   sleep 2
   kill -KILL <loop-pid>     # sicher ist sicher
   rm /tmp/<loop-name>.sh    # nur wenn die Datei nicht anderswo referenziert wird
   ```

6. **Recorder danach beobachten:** 5 min warten, `tail -n 10 data/state/recorder.log` —
   **keine** neuen „starting recorder"-Einträge = Loop tot. **Wenn doch neue Starts**:
   weiterer Hunt, Plan in `phase14_discovery/CLAUDE.md` NEXT-Block dokumentieren.

**Akzeptanz Schritt 3:** `tail -n 20 data/state/recorder.log` zeigt **keine** neuen
`[run_recorder] starting` Einträge für die nächsten 6 Stunden (Recording-Frequenz ist
ein Cycle alle 5 min, also ~72 potenzielle Start-Trigger). Recorder 108966 (oder sein
Nachfolger, falls er sauber restartet) ist dann stabil.

### Schritt 4 — Verifikation + Session-Block-Aufnahme (1 Commit, nur Markdown)

**Geänderte Dateien:**
- `phase14_discovery/CLAUDE.md` — Session-20-Block anhängen mit Verifikation der
  Schritte 2 und 3, Σ-Sweep, Findings.
- `phase14_discovery/SESSIONS_ARCHIVE.md` — Session 19 von vorhin rotieren
  (Doc-Layers-Konvention).

**Akzeptanz Schritt 4:** `git diff --stat HEAD~..HEAD` zeigt nur Markdown-Änderungen
(`.md` Dateien). `pytest phase12_data_foundation/tests -q` läuft weiter grün
(= **149 grün**). `tail -n 5 data/state/recorder.log` zeigt **keine** neuen Start-
Einträge nach Schritt 3.

---

## §5 Akzeptanz (PASS-Kriterien)

| # | Kriterium | Wie belegt |
|---|---|---|
| **A1** | `Recorder.__init__` nimmt einen optionalen `signal_check_interval_s`-Parameter mit Default **60** | `grep -n "signal_check_interval_s" phase12_data_foundation/data_foundation/recorder.py` zeigt die Konstante, den Konstruktor-Parameter und das `self._signal_check_interval_s = …`-Binding |
| **A2** | `run_forever` ruft `_sleep_capped(...)` statt `self._sleep_fn(...)` direkt | `grep -n "_sleep_capped\|self._sleep_fn(self._interval_s)" recorder.py` — die alte Zeile kommt nicht mehr vor |
| **A3** | `_sleep_capped` zerlegt den Sleep in Chunks ≤ `signal_check_interval_s` und prüft `_stop_requested` zwischen Chunks | neuer Test `test_run_forever_exits_within_signal_check_interval_on_request_stop` |
| **A4** | Bestehende Aufrufer (CLI via `python -m data_foundation.run`) sehen das alte Verhalten — `interval_s=300`, neue Chunk-Latenz max 60 s statt max 300 s | `pytest phase12_data_foundation/tests -q` → **149 grün**, keine Regression in `test_request_stop_ends_run_forever` |
| **A5** | Nach Recorder-Fix + Loop-Hunt: `tail -n 20 data/state/recorder.log` zeigt **keine** neuen „starting recorder"-Einträge für 6 Stunden | Cron-Test (manuell ausgelöst durch die 5-min-Cycle-Frequenz), Beweis im Σ-Sweep der Verifikation |
| **A6** | Σ-Sweep über alle Phasen-Suites unverändert **bis auf** +2 in Phase 12 (recorder-Tests) | `pytest` je Phase separat, Tabelle in Session-20-Block |

**Nicht Teil der Akzeptanz** (bewusst):
- **Phase-15-Helper-Klasse** `interruptible_sleep()` in einem gemeinsamen Modul
  (`phase_meta_daemon/` o.ä.). D5 entscheidet das; diese Session macht den Fix **lokal**.
- **Discovery-Daemon-Sleep-Cap (P14-D)** ist bereits gefixt (Session 13, Commit `27f04d9`).
  Kein Touch.
- **Phase-13-Beweiswoche** ist separater Track; nicht hier.
- **Migration 007** (Phase 14) ist bereits angewendet (Session 19 verifiziert); kein Touch.

---

## §6 Out of Scope

- **Phase-15-Helper-Klasse `interruptible_sleep`:** bleibt Phase-15-Territorium
  (D5). Die strukturell richtige Konsolidierung mit dem P14-D-Discovery-Pendant
  kommt, sobald beide Daemons dasselbe Pattern haben — heute ist Phase 12 Recorder
  der zweite Kunde.
- **`scheduler/runner.py`** (Phase 8) hat seinen POST_WINDOW-Cap bereits (2026-07-11
  Hotfix). Kein Touch — schon drittes Pattern im Repo, jetzt strukturelle Konsolidierung
  ohne Phase-8-Code-Edit.
- **WebUI-Endpoints:** `phase8_scheduler/webui/api.py` ruft weder Recorder noch
  Discovery direkt. Kein Touch.
- **Phase-14-D5-Closeout-Handover:** wartet weiter auf Phase-13-Beweiswoche.
- **`scripts/restart-services.sh`** (Session-18-Fund, Operator-Helper): **kein** Touch.
  Wird in einer Folgesession ggf. um Recorder-Loop-Hunt-Option erweitert, falls der
  Hunt zuverlässig von einer Shell aus reproduzierbar ist.

---

## §7 Fehlgriffe, die wie andere Fehler aussehen

| Symptom | Erster Verdächtiger | Wie unterscheiden |
|---|---|---|
| **„Recorder reagiert nicht auf `kill <pid>`"** | Recorder hängt wirklich (Deadlock, Endlosschleife) | `ps -o stat,wchan` zeigt `STAT S`/`WCHAN hrtime` (= `time.sleep()`-Wartezustand) — typisches „wartet auf Ablauf"-Bild, nicht „verklemmt". Vor dem Fix war das immer **dieser** Bug, nicht ein echter Hang. |
| **„Nach Code-Update lädt der Recorder den neuen Code nicht"** | `recorder.py`-Imports cachen altes Modul | `_sleep_capped` ist eine **Methode** des Recorders, kein Cross-Modul-Import. Python lädt Method-Bodies bei jedem Aufruf neu aus dem Modul — `git pull` + nächster Cycle reicht. Wenn der Code nicht greift, ist es ein anderer Bug (falscher Edit-Pfad, falscher Branch). |
| **„Recorder-Cycle läuft zu oft (alle 60 s statt alle 5 min)"** | Fehlkonfiguration `signal_check_interval_s` | Der Cycle läuft weiter **alle `interval_s` Sekunden** — der Cap betrifft nur den **Sleep zwischen** Cycles, nicht die Cycle-Frequenz. `signal_check_interval_s=60` heißt: Stop reagiert binnen 60 s, Cycle bleibt bei 5 min. |
| **„Recorder macht plötzlich viel mehr Cycles als geplant"** | `signal_check_interval_s`-Cap triggert irrtümlich | `_stop_requested` wird nur durch `request_stop()` (vom Signal-Handler oder CLI) gesetzt. Der Cap prüft nur **dieses eine Flag**, sonst nichts. Wenn `request_stop` nicht aufgerufen wird, schläft der Cap durch bis `total_s`. |
| **„Loop-Hunt findet nichts in `ps`, aber Recorder stirbt weiter"** | Loop ist kein Shell-Prozess, sondern z. B. ein systemd-Timer oder eine andere Scheduler-Mechanik | `systemctl list-timers --all` (in einem Container: oft nicht verfügbar) und `journalctl --since "1 day ago" \| grep recorder` (in einem Container: oft nicht verfügbar). Alternative: `ps -ef --forest` für eine Baum-Darstellung. |
| **„Nach Recorder-Fix und Loop-Hunt stirbt Recorder immer noch nach 15 h"** | Es gibt **zwei** Loops (zwei nohup-Wrapper, oder Loop + Cron, oder systemd) | Hunt mehrfach in Intervallen wiederholen — `pgrep` zeigt nur **eine** PID pro Prozess. Wenn `pgrep -af "run_recorder"` zwei Treffer zeigt, sind es zwei Loops. |

---

## §8 Drift-Liste — bei Ausführung verifizieren

> **Diese Liste ist vollständig.** Was hier nicht steht, hat diese Planungssession am
> 2026-08-28 selbst gegen das Repo, den Live-Prozess und das P14-D-Vorbild geprüft und
> ist als Fakt formuliert. Rate nichts nach; prüfe diese und nur diese.

1. **Zeilennummern verschieben sich.** Jeder Anker oben trägt den **Verbatim-String** —
   der ist der Anker, die Zahl ist die Abbringer. Schritt 2 verschiebt `recorder.py`
   selbst (Klasse + `run_forever` + Konstruktor); Schritt 1 verschiebt
   `phase14_discovery/CLAUDE.md` (Spezial-Pläne-Zeile). **Immer per String suchen.**
2. **P14-D-Plan ist die Vorlage** ([./PHASE14_D_DAEMON_SIGNAL_CAP_PLAN.md](./PHASE14_D_DAEMON_SIGNAL_CAP_PLAN.md)).
   Das `_sleep_capped`-Pattern ist 1:1 identisch, nur `_stop_requested` statt `_stop`,
   nur `interval_s=300` statt `=3600`, nur `recorder.py` statt `run.py`. Wer P14-D
   gelesen hat, liest P14-E in 30 s.
3. **`run_forever` ist die einzige Stelle mit `self._sleep_fn(self._interval_s)`.**
   Heute gegrept: keine weitere in `phase12_data_foundation/`. Auch `_sleep_capped`
   wird **nicht** an anderen Stellen benötigt — die Cycle-Methode (`tick()`) hat keinen
   eigenen Sleep. (Der Heartbeat hat seinen eigenen, getrennten Loop.)
4. **`interval_s`-Injection:** heute `interval_s: int = 300` (Z. 75, Konstruktor).
   Der neue `signal_check_interval_s` muss **daneben** stehen, damit der Diff minimal
   bleibt. `state_path: str = "data/state/recorder_state.json"` (Z. 76) ist die
   visuelle Anker-Stelle.
5. **`_sleep_fn`-Injection:** heute `sleep_fn: Callable[[float], None] = time.sleep`
   (Z. 80). Bereits injizierbar — der neue Test braucht **keine** neue Dependency.
   **Aber:** der Default-Test-Stub im `_recorder`-Helper (test_recorder.py Z. 47) ist
   `lambda s: None` — kein Chunk-Counter. Wir brauchen einen Test-Stub mit Counter,
   deshalb schreibt P14-E Plan **zwei** neue Tests in test_recorder.py, die ihre
   eigenen `sleep_fn`-Stubs mitbringen.
6. **`request_stop()`-Test:** heute implementiert in `recorder.py:191-192` (Methode
   auf `Recorder`). Signal-Handler ruft sie aus `data_foundation/run.py` auf
   (verifiziert per `grep -n "request_stop" phase12_data_foundation/`). Neuer Test
   ruft sie direkt — kein echter SIGTERM nötig.
7. **`signal_check_interval_s` Default 60 s:** bewusst konservativ. Trade-off-Tabelle
   (identisch P14-D §8.9):

   | Wert | Max-Stop-Latenz | Chunk-Overhead | Empfehlung |
   |---|---|---|---|
   | 1 s | 1 s | hoch (300 Chunks/Std) | Watchdog-only |
   | 30 s | 30 s | gering (10 Chunks/Cycle) | gut für Tests |
   | **60 s** | **60 s** | **minimal (5 Chunks/Cycle)** | **Default — diese Session** |
   | 300 s | 5 min | sehr gering (1 Chunk/Cycle) | analog Default |

   60 s = 1 min = 5× schnellere Stop-Reaktion als `interval_s=300`, 5× weniger
   Chunks als 30 s. Wenn ein künftiger Operator den Cap enger haben will, ist
   `--signal-check-interval-s 30` der Aufruf — kein Code-Edit nötig (entsprechender
   CLI-Flag muss in `run.py` ergänzt werden, das ist Phase-15-Territorium).
8. **Cross-Phase-Freigabe-Status:** `recorder.py` ist **nicht** in der Phase-14-
   Cross-Phase-Freigabe-Liste. Dieser Plan **ist** die Sign-off-Vorlage: Nikinger
   genehmigt den Plan → Schritt 2 darf committen. Ohne Genehmigung kein Code-Touch.
9. **Keine Phase-12-Tests-Regression:** `test_request_stop_ends_run_forever`
   (test_recorder.py:105-119) prüft das alte Verhalten mit dem injizierten
   `sleep_and_stop`-Lambda. Der neue Fix erhält die Kompatibilität (Chunks summieren
   sich zu `total_s`), der Test muss weiterhin grün sein. Verifikation mit
   `pytest phase12_data_foundation/tests/test_recorder.py -v` als Vor-Commit-Check.
10. **Loop-Hunt-Quellen jenseits von `nohup`:** falls die Hunt nichts findet, sind
    alternative Quellen: systemd-Timer (`systemctl list-timers`), Cron-Jobs
    (`crontab -l` für root + trading-bot), Process-Supervisor (foremost, runit — im
    Container unwahrscheinlich). Container hat typischerweise **keinen** init, daher
    sind nohup/disowned die plausibelste Quelle. Falls alle Stricke reißen, bleibt
    der Workaround: Recorder im Vordergrund im `tmux`-Session laufen lassen — **kein**
    Scope dieses Plans.

---

## §9 Cross-Referenz

- **Mutterplan:** [`../docs/concepts/phase14_discovery_plan.md`](../docs/concepts/phase14_discovery_plan.md) — unverändert; P14-E ist eine **Cross-Phase-Hygiene**, kein Plan-Konflikt.
- **Geschwister-Mini-Pläne:**
  - [./PHASE14_C_DAEMON_CWD_BUG_PLAN.md](./PHASE14_C_DAEMON_CWD_BUG_PLAN.md) — CWD-Bug, der Recorder-Discovery-Consistenz sichtbar gemacht hat.
  - [./PHASE14_D_DAEMON_SIGNAL_CAP_PLAN.md](./PHASE14_D_DAEMON_SIGNAL_CAP_PLAN.md) — das **exakte Pattern-Vorbild** für Recorder-Fix (D1–D5 1:1 übertragbar).
- **Phase-12-Phasenkopf:** [`../phase12_data_foundation/CLAUDE.md`](../phase12_data_foundation/CLAUDE.md) — Closeout-Handover (2026-08-25) bleibt unverändert; Cross-Phase-Freigabe-Regel (Nikinger-Sign-off für jeden Phase-12-Touch von Phase-14-Sessions aus).
- **Phase-8-Vorbild:** [`../phase8_scheduler/CLAUDE.md`](../phase8_scheduler/CLAUDE.md) Session 2026-07-11 (POST_WINDOW-Hotfix). Drittes Pattern im Repo, in Phase-15-Konsolidierung.
- **Phasenkopf Phase 14:** [`./CLAUDE.md`](./CLAUDE.md) — Modul-Tabelle trägt `recorder.py` weiterhin **nicht** (Phase-12-Code); Spezial-Pläne-Zeile wird in Schritt 1 ergänzt.
- **Session-Archiv:** [`./SESSIONS_ARCHIVE.md`](./SESSIONS_ARCHIVE.md) — Sessions 1–18 (alt), Session 19 (heute Morgen, rotiert); Session 20 wird nach Verifikation angehängt.
