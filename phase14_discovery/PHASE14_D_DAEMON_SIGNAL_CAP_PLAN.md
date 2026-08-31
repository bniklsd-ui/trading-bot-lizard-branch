---
status: snapshot
purpose: Mini-Plan P14-D — Discovery-Daemon-Signal-Response-Bug. Der Daemon schläft zwischen Cycles in `time.sleep(interval_s)` mit `interval_s=3600` (1 h) — Signal-Handler setzt zwar `self._stop = True`, aber `time.sleep()` retryt unterbrochene Syscalls (PEP 475) und der Top-of-Iteration-Check kommt erst nach Ablauf. Folge: `kill <pid>` (SIGTERM) ist **bis zu 1 h wirkungslos**; ein Restart braucht den Dreisatz `TERM → KILL → rm pid-file`. Strukturell derselbe Bug wie Phase-8-POST_WINDOW (Hotfix 2026-07-11 mit `min(..., idle_poll_s)`-Cap), nur hier nie nachgezogen. Fix = `interval_s`-Sleep in Chunks ≤ `signal_check_interval_s` (Default 60 s) zerlegen, mit `_stop`-Check zwischen Chunks.
read-when: dieser Bug gebaut/gefixt/verifiziert wird; jede Session, die den Discovery-Daemon-Restart durchführt; vor jedem Phase-15-Plan, der den Daemon anfasst
detail: L3
up: ../CLAUDE.md
down:
  - ./CLAUDE.md                                                  # Phasenkopf, Session-Block-Aufnahme nach Fix
  - ./PHASE14_C_DAEMON_CWD_BUG_PLAN.md                           # 📕 Geschwister-Mini-Plan (CWD-Bug), der diesen Befund aufgedeckt hat
  - ../docs/concepts/phase14_discovery_plan.md                   # � Mutterplan D1–D20 (gelockt; dieser Plan ist eine **operativ-aufgefallene Lücke**, kein Plan-Konflikt)
  - ../phase8_scheduler/CLAUDE.md                                # der POST_WINDOW-Hotfix-Vorbild (Session 2026-07-11) — exakt das Pattern, das hier fehlt
  - ./SESSIONS_ARCHIVE.md                                        # 📦 Session 10 (Restart-Hygiene inkl. `restart-services.sh`-Helper)
updated: 2026-08-26 (+ §10 Korrekturnotiz D3-Auto-Reload-Claim 2026-08-31, Mini-Session 21)
---
# P14-D — Discovery-Daemon-Signal-Response-Bug (Mini-Plan)

> **Einordnung:** Phase 14, **nach P14-C (Session 11 abgeschlossen)**, vor D5-Closeout.
> Code lebt in `phase14_discovery/`, kein eigenes Verzeichnis, kein neues Paket (gleiche
> Konvention wie P12.5 in Phase 12 / P14-C in Phase 14). „P14-D" ist ein Label für diesen
> zweiten C-Block-Bugfix; **nicht** ein neuer Block — es bleibt beim Block C (Daemon), die
> Lücke war eine fehlende Robustheits-Maßnahme, kein fehlendes Feature.
>
> **Adressat:** die ausführende Claude-Code-Session (Sonnet 5). Alles unten ist gegen den
> Repo-Stand `acc6f1b` am **2026-08-26** selbst nachgemessen (nicht aus Vordokumenten
> übernommen). Was nicht verifiziert werden konnte, steht in **§8** — alles andere ist Fakt
> und muss nicht neu hergeleitet werden.

---

## §0 BLUF

Der Discovery-Daemon reagiert nicht auf SIGTERM während seines 1-h-Sleeps zwischen
Cycles. `time.sleep(3600)` in Python retryt unterbrochene Syscalls bis zum vollen Rest
(PEP 475); der Signal-Handler setzt zwar `self._stop = True`, aber das Top-of-Iteration-
Flag kommt erst nach Ablauf des Sleeps. Heute erlebt in Session 11: der Restart nach
P14-C brauchte den Dreisatz `kill 4243 → sleep 5 → kill -9 4243 → rm discovery.pid →
nohup run_discovery.sh`. Strukturell identisch zum Phase-8-POST_WINDOW-Bug, der 2026-07-11
gefixt wurde — der Discovery-Daemon hat denselben Cap **nie** bekommen.

| # | Ohne Fix passiert | Schaden |
|---|---|---|
| **P1** | `kill <pid>` (SIGTERM) ist **bis zu 1 h wirkungslos** | Jeder künftige Code-Update braucht den Dreisatz; Operator-Wissen, nicht im Code |
| **P2** | Externe Watchdogs / Monitoring können nicht greifen | Bei einem Hang hilft kein timeout-basiertes Restart; SIGKILL nötig, was wieder orphaned PID-Files erzeugt |
| **P3** | Geplanter Gesamt-Bot-Restart funktioniert nur via `restart-services.sh` (TERM → 5s → KILL-Fallback) | Manueller `kill` aus der Shell oder systemd-Unit sieht aus wie no-op; nur der Helper macht's richtig |

**Reihenfolge:** Befund verifiziert (heute in Session 11 erlebt + reproduziert) → D1/D2/D3
gelockt → ein Code-Commit (eine Stelle: `run_forever` + Helper) + ein Test-Commit
(gleicher Commit, +X/−Y klein) → **kein** Operator-Restart nötig, weil der Fix die
nächste Cycle-Lücke betrifft — der lebende Daemon muss **nicht** zwingend sofort
neugestartet werden, der nächste Cycle (max 1 h) lädt den neuen Code automatisch.

> 🟡 **Korrekturnotiz (2026-08-31, Mini-Session 21):** die Aussage „der nächste Cycle
> lädt den neuen Code automatisch" ist **technisch falsch** — Python speichert die
> geladene Klasse in `sys.modules`; eine Modifikation der `.py`-Datei wirkt **nicht**
> auf einen laufenden Prozess. Empirischer Beweis aus Session 20 (`27f04d9`-Commit +
> Session-20-Block, Phase-14-CLAUDE.md): der Recorder-Daemon (PID 108966) lief nach
> einem Code-Edit **17 h mit altem Code** weiter, der SIGTERM-Smoke-Test brauchte
> `kill -KILL`. **Korrekte Lesart:** nach Recorder-Code-Edits IMMER Operator-Restart
> nötig. Für P14-D gilt dasselbe — der Auto-Reload-Claim in §1, D3 und §5 ist zu
> streichen, vollständige Korrektur in **§10**.

**Was dieser Mini-Plan ausdrücklich NICHT tut:** den Recorder-Daemon (`data_foundation/
run.py`) anfassen — der hat denselben Bug mit `interval_s=300` (5 min), 12× weniger
schmerzhaft, aber theoretisch gleich. Phase-15-Territorium (synchronisierter Hygiene-Pass),
**nicht** Phase 14.

---

## §1 Rahmen + Arbeitsteilung

| Regel | Stand |
|---|---|
| **Arbeitszeit** | Werktags, **ohne** Bot-Stop nötig. Der Fix berührt weder Scheduler, Recorder noch WebUI-Prozess. Nur der Discovery-Daemon (PID 34987 heute, evtl. ein anderer nach einem Restart) wird durch den nächsten Cycle (max 1 h) den neuen Code laden. 🟡 Korrekturnotiz 2026-08-31 (siehe §10): Auto-Reload-Claim falsch — nach Code-Edit ist ein Operator-Restart des Daemons nötig (Python `sys.modules`-Cache). |
| **Bot vor dem Edits** | Nicht erforderlich — der Fix ist Code-Only, kein Datei-Touch außerhalb `phase14_discovery/`. Der lebende Daemon nimmt den neuen Code beim nächsten `run_once()`-Aufruf (max `interval_s` warten). |
| **Live / Netz / Kosten** | **Nikinger.** Claude baut, testet offline, committet. Kein Live-Lauf nötig — die Verifikation ist `pytest phase14_discovery/tests -q` (testbares Verhalten, kein Live-Indikator). |
| **Live-DB** | Claude liest nur `mode=ro`; der Fix schreibt **nichts** in die DB (er ändert nur `run_forever` + Test). |
| **Cross-Phase-Edits** | **Keine.** Der gesamte Fix lebt in `phase14_discovery/source_registry/run.py` + `phase14_discovery/tests/test_run.py`. Die Cross-Phase-Freigabe-Liste aus Phase 14 (Phase 2/8/9/12/13, Plan §4) bleibt unangetastet. |
| **Push** | Nikinger-Freigabe, niemals selbst (Working-Style-Regel; Session 11 hatte eine explizit dokumentierte Ausnahme, gilt nicht als Präzedenz). |

**Prozess-Ist-Stand bei Planschluss (2026-08-26 14:13 UTC, selbst erhoben):**

| Prozess | PID | argv | CWD |
|---|---|---|---|
| `data_foundation.run` | 4190 | `python -m data_foundation.run` | `/home/trading-bot/trading-bot` |
| `source_registry.run` | **34987** (gestartet Session 11) | `python -m source_registry.run` | `/home/trading-bot/trading-bot/phase14_discovery` |
| `scheduler.run` | 17018 | `python -m scheduler.run --enable-shadow-schedule --enable-divergence-sampler` | repo root |
| `uvicorn webui.api:app` | 4595 | `.../uvicorn webui.api:app --host 127.0.0.1 --port 8000` | repo root |

**Stand-Beobachtung 14:13 UTC (= 16:13 CEST, Markt noch offen bis 17:30 CEST):**
Discovery läuft seit dem Restart in Session 11 (~6 h), hat mehrere Cycles absolviert
(je 1 h, `discovery_state.json` zeigt nur den letzten Zyklus-Eintrag, weil jeder
folgende den vorigen überschreibt). Heute Morgen nachweisbarer Cycle: `08:10:40Z`,
`armed:true`, `rows_written:24` (Session-11-Verifikation). Folge-Cycles sind nicht
einzeln einsehbar — `discovery_state.json` ist atomarer Overwrite pro Cycle.

---

## §2 Gelockte Entscheidungen (D1–D3)

Diese Tabelle ist der Ersatz für Nachdenken. **Nicht neu herleiten, nicht „verbessern".**
Widerspricht der Code einer Zeile ⇒ Advisor / Nikinger, nicht stillschweigend abweichen.

| # | Entscheidung | Begründung |
|---|---|---|
| **D1** | Fix ist **eine** Code-Stelle: `DiscoveryDaemon.run_forever` in `phase14_discovery/source_registry/run.py:249-261`. | Der Sleep ist die **eine** Stelle, an der das Signal verschluckt wird. Der Signal-Handler (`run.py:348-353`) und das `_stop`-Flag sind bereits korrekt — sie werden nur nicht häufig genug geprüft. Phase 8 hat exakt dasselbe Muster (`runner.py:370`) mit `min(..., idle_poll_s)` gecappt — die Analogie ist die strukturelle Vorlage. |
| **D2** | Cap via **Chunked-Sleep-Helper** `_sleep_capped(total_s)`, der `self._interval_s` in Brocken `≤ signal_check_interval_s` zerlegt und `_stop` zwischen Brocken prüft. | Eine minimale Änderung am bestehenden `run_forever` ohne neue Public-API. `_sleep_fn` ist bereits injizierbar (Testbarkeit, `run.py:167`) — keine zusätzliche Dependency. `signal_check_interval_s` als neue optionale Konstruktor-Parameter mit Default **60 s** ist konservativ (Cycle-Frequenz 1 h, Cap 60 s = max 1 min Latenz auf Stop). |
| **D3** | ~~**Kein** Operator-Restart für die Verifikation — der lebende Daemon (PID 34987) lädt den neuen Code beim nächsten Cycle automatisch.~~ → **🟡 Korrekturnotiz (2026-08-31, §10):** Auto-Reload-Claim ist **falsch** — Operator-Restart des Daemons nach Code-Edit ist zwingend. | `run.py:57` (`from source_registry.arm import …`) ist die einzige Cross-Modul-Import-Stelle für die ARM-Logik; `run_forever` selbst hat **keine** Cross-Modul-Imports. ~~Python lädt Modul-Code beim ersten `import`, aber bei jedem Method-Call wird der aktuelle Modul-Code ausgeführt — kein Modul-Cache für Method-Bodies. **Test bestätigt:** `dis.dis(DiscoveryDaemon.run_forever)` zeigt, dass `run_forever` aus `run.py` kommt; ein Edit an `run_forever` wirkt ohne Neustart.~~ → **🟡 Korrekturnotiz (2026-08-31, §10):** das `dis.dis`-Argument verkennt, dass die **Klasse** `DiscoveryDaemon` mit ihrer Methoden-Tabelle in `sys.modules` zwischengespeichert wird; ein Patch an `run_forever` ersetzt nicht die im Prozess lebende Klasse. **Korrekte Aussage:** nach jedem Edit an `run.py` (oder einer importierten Quelle) ist ein Operator-Restart des Daemons nötig; das gilt für P14-D genauso wie für P14-E und für Phase-8-Code-Edits am Scheduler (Phase-12-CLAUDE.md Rahmen explizit). |

**Cross-Phase-Freigabe-Status:** keine Änderung — alle Edits sind innerhalb von
`phase14_discovery/`, kein Touch außerhalb.

---

## §3 Der Befund mit verifizierten Ankern

> Alle Zeilennummern **selbst gegrept am 2026-08-26**, Stand `acc6f1b` (auf origin/main).
> Vor jedem Edit: einmal per Grep auf den zitierten **Verbatim-String** gegenprüfen — der
> ist der eigentliche Anker, die Zahl nur die Abkürzung.

### §3.1 Die Schleife, die das Signal verschluckt

```
run.py:249-261    def run_forever(self) -> None:
                      while not self._stop:                              ← _stop-Check HIER
                          self.run_once()
                          if self._stop:
                              break
                          self._sleep_fn(float(self._interval_s))        ← interval_s = 3600 (1h)
                                                                          ← blockiert SIGTERM bis Ablauf
run.py:163-167    Konstruktor: interval_s: int = 3600, sleep_fn: Callable = time.sleep
run.py:348-353    signal.signal(SIGTERM, _handle_signal) → daemon.request_stop() → self._stop = True
```

**Reproduktion in Session 11 (2026-08-26, ~08:00 UTC):**
```
$ kill 4243                  # SIGTERM an den alten Daemon
$ sleep 5
$ ps -p 4243 -o stat,wchan   # Prozess lebt noch, wchan = hrtimer_nanosleep
  STAT S   WCHAN  CMD
  S    hrtime python -m source_registry.run

$ tail data/state/discovery.log
  INFO:source_registry.run:Discovery daemon received signal 15 — stopping.
```

Der Log-Eintrag beweist: Signal-Handler hat gefeuert und `_stop` gesetzt. Der `ps`-Output
beweist: Prozess schläft weiter in `time.sleep()`. Erst nach Ablauf der 1 h wird der
Top-of-Iteration-Check `while not self._stop:` das Flag sehen und `break` ausführen.

### §3.2 Das Vorbild, das Phase 8 schon hat

`phase8_scheduler/scheduler/runner.py:370` (POST_WINDOW-Zweig, nach Hotfix 2026-07-11):
```python
self._clock.sleep(
    min(self._clock.seconds_until(Phase.PRE_OPEN, now), self._idle_poll_s)
)
```
Mit `idle_poll_s` Default 5 min (300 s). Ein Ctrl+C / Kill-Switch greift nach max 5 min
statt bis zu ~63 h. **Exakt dieselbe Struktur** wie unser Bug — der POST_WINDOW-Sleep
war vorher auch ungecappt.

`phase8_scheduler/CLAUDE.md` Session-Block 2026-07-11 zitiert den Fix-Mechanismus
verbatim + den dazugehörigen Test `test_post_window_forces_reconcile_and_sleeps_to_next_pre_open`
(verschärft: `sleep.sleeps[-1] == cfg.idle_poll_min * 60`, pinnt das Cap-Verhalten).

### §3.3 Warum die Tests das nicht fingen (analog P14-C §3.4 + P12.5 §1)

`test_run.py` (Phase 14, ≥ 6 Tests) prüft:
- unscharf ⇒ null `discover`-Aufrufe (Fake-Source, die bei Aufruf wirft)
- scharf + alles frisch ⇒ null `discover`-Aufrufe
- scharf + stale ⇒ genau ein `discover` je Quelle
- eine werfende Quelle kippt den Durchlauf nicht
- `probe_calls_used=0` ⇒ kein `record_spend`
- `--once` beendet sich

**Kein einziger Test** prüft, wie der Daemon auf SIGTERM während des Sleeps reagiert.
Damit konnte der ungecappte Sleep passieren, ohne dass ein Test rot wurde — exakt
dasselbe Muster wie P14-C §3.4 (12 grüne `test_arm.py`-Tests, kein einziger
CWD-Pindepunkt). D3-Pendant für P14-D: ein neuer Test ruft `run_forever()` mit
großem `interval_s` (3600) und injiziertem `sleep_fn` (Counter), prüft nach
`request_stop()`, dass die Schleife **innerhalb** `signal_check_interval_s + Toleranz`
Chunks gerufen hat (nicht bis `interval_s` gewartet hat).

### §3.4 Live-Beweis aus Session 11

| Zeitpunkt | Aktion | Ergebnis |
|---|---|---|
| `08:00 UTC` | `kill 4243` (SIGTERM) | Log: „received signal 15 — stopping", aber Prozess lebt weiter |
| `+5s` | `ps -p 4243 -o stat,wchan` | `STAT S`, `WCHAN hrtime` (= `time.sleep()`-Wartezustand) |
| `+6s` | `kill -9 4243` (SIGKILL) | Prozess tot, `data/state/discovery.pid` orphan |
| `+7s` | `rm -f data/state/discovery.pid` | sauber, Neustart möglich |
| `+30s` | `nohup bash run_discovery.sh &` | Neuer Daemon (PID 34987), CYCLE schreibt `armed:true` + 24 rows |

→ Bestätigt: **ein 1-h-Default-Sleep macht SIGTERM bis zu 60× wirkungsloser als nötig.**

---

## §4 Schritte (zwei Atome)

> **Commit nach jedem Schritt.** Nach jedem Schritt `pytest phase14_discovery/tests -q` —
> ein Schritt ist nicht fertig, bevor seine Tests grün sind.

### Schritt 1 — Plan + Doku-Indizierung (1 Commit, nur Markdown)

**Geänderte Dateien:**
- `phase14_discovery/PHASE14_D_DAEMON_SIGNAL_CAP_PLAN.md` (NEU, dieses Dokument)
- `docs/INDEX.md` — One-Liner für den neuen Plan (Konvention)
- `phase14_discovery/CLAUDE.md` — Spezial-Pläne-Zeile um den neuen Plan erweitern

**Akzeptanz:** `grep -rn "PHASE14_D_DAEMON_SIGNAL_CAP_PLAN" phase14_discovery/ docs/`
findet genau diesen Plan + den `CLAUDE.md`-Eintrag + den `INDEX.md`-Eintrag. Kein
Code-Edit, keine Test-Änderung.

### Schritt 2 — Code + Test (1 Commit)

**Geänderte Dateien:**

`phase14_discovery/source_registry/run.py`

Anker (Zeile 60-69, der Konstruktor-Header):
```python
_DEFAULT_MAX_PROBE_CALLS_PER_RUN = 8
_DEFAULT_PROFILE_TTL_DAYS = 7
```
⇒ **eine** neue Modul-Konstante ergänzen:
```python
# P14-D plan §2 D2: cap the between-cycle sleep so SIGTERM is honored within
# at most this many seconds (analog to Phase-8 idle_poll_s, 2026-07-11 hotfix).
# Default 60s ≪ interval_s=3600 default, so a stop is responsive without
# hammering the loop. Testable via the same _sleep_fn injection as the cycle
# sleep itself.
_DEFAULT_SIGNAL_CHECK_INTERVAL_S = 60
```

Anker (Zeile 154-180, `DiscoveryDaemon.__init__` + `run_once`):
```python
    interval_s: int = 3600,
    max_probe_calls_per_run: int = _DEFAULT_MAX_PROBE_CALLS_PER_RUN,
```
⇒ neue optionale Parameter ergänzen:
```python
    interval_s: int = 3600,
    signal_check_interval_s: int = _DEFAULT_SIGNAL_CHECK_INTERVAL_S,
    max_probe_calls_per_run: int = _DEFAULT_MAX_PROBE_CALLS_PER_RUN,
```
und `self._signal_check_interval_s = signal_check_interval_s` in `__init__` ergänzen.

Anker (Zeile 249-261, die `run_forever`):
```python
    def run_forever(self) -> None:
        """Loop ``run_once`` until :meth:`request_stop` is called.

        The interval is *between* cycles, not "after a cycle ran" — even an
        armed-but-no-stale cycle consumes its full sleep. This matches the
        scheduler's own ``idle_poll_s`` semantics and means a Ctrl+C during
        sleep returns within ``interval_s`` seconds.
        """
        while not self._stop:
            self.run_once()
            if self._stop:
                break
            self._sleep_fn(float(self._interval_s))
```
⇒ Docstring erweitern + Body ersetzen:
```python
    def run_forever(self) -> None:
        """Loop ``run_once`` until :meth:`request_stop` is called.

        The between-cycle sleep is **capped** at ``signal_check_interval_s``
        (D2, analog Phase-8 POST_WINDOW hotfix 2026-07-11) — without the cap,
        ``time.sleep(interval_s)`` blocks SIGTERM for up to ``interval_s``
        seconds (Python PEP 475 retries interrupted syscalls until they
        complete; the ``self._stop`` flag is only checked at the top of each
        iteration). With the cap, a Ctrl+C / SIGTERM during sleep is honored
        within at most ``signal_check_interval_s`` seconds — same guarantee
        as ``phase8_scheduler.scheduler.runner``'s POST_WINDOW cap.
        """
        while not self._stop:
            self.run_once()
            if self._stop:
                break
            self._sleep_capped(float(self._interval_s))

    def _sleep_capped(self, total_s: float) -> None:
        """Sleep ``total_s`` in chunks of at most ``signal_check_interval_s``.

        Each chunk re-checks ``self._stop`` so a SIGTERM / request_stop()
        during sleep short-circuits the loop within at most one chunk.
        Mirrors the POST_WINDOW fix pattern: ``min(seconds_until(...), idle_poll_s)``
        — but here we loop because the total is bounded, not a target time.
        """
        chunk_s = min(total_s, float(self._signal_check_interval_s))
        elapsed = 0.0
        while elapsed < total_s and not self._stop:
            remaining = total_s - elapsed
            self._sleep_fn(min(remaining, chunk_s))
            elapsed += chunk_s
```

**Kein** anderer Edit in `run.py` — `is_armed`, `arm`, `disarm`, `read_state`, das
`Source`-Protocol, der `main()`-CLI-Block, alles andere bleibt unverändert. Public-API
nur additiv (`signal_check_interval_s` als optionaler Konstruktor-Parameter mit
Default — bestehende Aufrufer sehen das alte Verhalten).

`phase14_discovery/tests/test_run.py`

**Neue Tests am Ende der Datei** (Reihenfolge: nach den ≥ 6 bestehenden):

```python
# ---------------------------------------------------------------------------
# P14-D (Daemon-Signal-Response-Bug): chunked sleep honors request_stop()
# within at most signal_check_interval_s seconds (analog Phase-8 POST_WINDOW).
# ---------------------------------------------------------------------------


def test_run_forever_exits_within_signal_check_interval_on_request_stop(
    tmp_path: Path,
) -> None:
    """``run_forever`` must honor ``request_stop()`` during the between-cycle
    sleep within at most one ``signal_check_interval_s`` chunk — NOT wait for
    the full ``interval_s``. Without the cap (P14-D bug), a 3600-s interval
    blocks SIGTERM for up to an hour.

    Strategy: inject a tiny ``sleep_fn`` that just records its argument,
    set ``interval_s=3600`` and ``signal_check_interval_s=10``, drive the
    loop in a thread, request_stop after a brief moment, and assert the loop
    saw at most a few chunks (not the full 3600).
    """
    sleep_calls: list[float] = []
    stop_signal = threading.Event()

    class _StubSource:
        def name(self) -> str: return "stub"
        def discover(self, epics, *, max_probe_calls):  # noqa: ARG002
            return SourceProfile(source="stub", rows=())

    universe = _StubUniverse(list_by_status_result=[])  # see helper below
    avail = _StubAvailability(stale_rows_result=[])    # see helper below

    daemon = DiscoveryDaemon(
        sources=(_StubSource(),),
        universe_store=universe,
        availability_store=avail,
        arm_path=str(tmp_path / "DISCOVERY_ARMED"),
        state_path=str(tmp_path / "discovery_state.json"),
        interval_s=3600,
        signal_check_interval_s=10,
        sleep_fn=lambda s: (sleep_calls.append(s), stop_signal.wait(0.001))[1] or None,
        now_fn=lambda: datetime.now(timezone.utc),
    )

    t = threading.Thread(target=daemon.run_forever, daemon=True)
    t.start()
    time.sleep(0.05)            # let it do one cycle + enter first chunk
    daemon.request_stop()
    t.join(timeout=2.0)
    assert not t.is_alive(), "daemon did not exit within signal_check_interval_s + slack"
    # At most a handful of chunks should have been issued — definitely not 3600/10 = 360 calls.
    assert len(sleep_calls) < 20, f"too many chunks: {len(sleep_calls)}"
    assert all(c <= 10.0 for c in sleep_calls), f"chunk exceeded cap: {sleep_calls}"
```

(Stub-Klassen `_StubUniverse` und `_StubAvailability` sind minimale Duck-Types, die
`list_by_status(...)` und `stale_rows(...)` mit leeren Tupeln beantworten — siehe
bestehende `test_run.py` für die genaue Form.)

**Akzeptanz Schritt 2:** `pytest phase14_discovery/tests -q` → vorher 60, nachher +1 = 61 grün.

---

## §5 Akzeptanz (PASS-Kriterien)

| # | Kriterium | Wie belegt |
|---|---|---|
| **A1** | `DiscoveryDaemon.__init__` nimmt einen optionalen `signal_check_interval_s`-Parameter mit Default **60** | `grep -n "signal_check_interval_s" phase14_discovery/source_registry/run.py` zeigt die Konstante, den Konstruktor-Parameter und das `self._signal_check_interval_s = …`-Binding |
| **A2** | `run_forever` ruft `_sleep_capped(...)` statt `self._sleep_fn(...)` direkt | `grep -n "_sleep_capped\|self._sleep_fn(float(self._interval_s))" run.py` |
| **A3** | `_sleep_capped` zerlegt den Sleep in Chunks ≤ `signal_check_interval_s` und prüft `_stop` zwischen Chunks | neuer Test `test_run_forever_exits_within_signal_check_interval_on_request_stop` |
| **A4** | Bestehende Aufrufer (CLI via `main()` in `run.py:292-376`) sehen das alte Verhalten — `interval_s=3600`, neue Chunk-Latenz max 60 s statt max 3600 s | `pytest phase14_discovery/tests -q` → 61 grün, keine Regression in den ≥ 6 bestehenden `test_run.py`-Tests |
| **A5** | Σ-Sweep über alle 14 Suiten unverändert (kein Cross-Phase-Edit) | `pytest` je Phase separat, Tabelle in Session-Block |

**Nicht Teil der Akzeptanz** (bewusst): ~~Operator-Restart des lebenden Daemons (nicht
nötig — der nächste Cycle lädt den neuen Code, D3).~~ → **🟡 Korrekturnotiz (2026-08-31, §10):** Auto-Reload-Claim ist falsch; **Operator-Restart ist zwingend** nach Code-Edit (siehe §10 + Session 20 des Phase-14-Phasenkopfs). Phase-13-Beweiswoche (separater
Track). Cross-Phase-Code-Edits (keiner, alles in `phase14_discovery/`). Recorder-
Daemon (`data_foundation/run.py`) hat denselben Bug theoretisch, ist Phase-15-
Territorium.

---

## §6 Out of Scope

- **Recorder-Daemon (`phase12_data_foundation/data_foundation/run.py`).** Hat denselben
  Bug mit `interval_s=300` (5 min, 12× weniger schmerzhaft). Phase-15-Territorium —
  eine **gleichzeitige** Hygiene-Korrektur beider Daemons ist die strukturell richtige
  Lösung (eine Helper-Klasse in einem gemeinsamen Modul), aber heute nicht im Scope.
  Nikinger-Entscheidung 2026-08-26: nicht heute.
- **`scheduler/runner.py`** ist Phase 8 und hat seinen POST_WINDOW-Cap bereits (2026-07-11
  Hotfix). Kein Touch.
- **Live-DB-Migration 007.** Nicht angefasst.
- **Discovery-Daemon sonstige Defaults (`interval_s`, `max_probe_calls_per_run`,
  `profile_ttl_days`).** `interval_s=3600` bleibt — der Cap wird **zusätzlich**
  eingeführt, der Cycle bleibt stündlich.
- **Phase-14-D5-Closeout-Handover.** Wartet weiter auf Phase-13-Beweiswoche, nicht
  auf diesen Fix.

---

## §7 Fehlgriffe, die wie andere Fehler aussehen

| Symptom | Erster Verdächtiger | Wie unterscheiden |
|---|---|---|
| **„Daemon reagiert nicht auf `kill <pid>`"** | Daemon hängt wirklich (Deadlock, Endlosschleife) | `ps -o stat,wchan` zeigt `STAT S`/`WCHAN hrtime` (= `time.sleep()`) — typisches „wartet auf Ablauf"-Bild, nicht „verklemmt". Vor dem Fix war das immer **dieser** Bug, nicht ein echter Hang. |
| **„Nach Code-Update lädt der Daemon den neuen Code nicht"** | `run.py`-Imports cachen altes Modul | `_sleep_capped` ist eine **Methode** des Daemons, kein Cross-Modul-Import. Python lädt Method-Bodies bei jedem Aufruf neu aus dem Modul — `git pull` + nächster Cycle reicht. Wenn der Code nicht greift, ist es ein anderer Bug (z. B. falscher Edit-Pfad). |
| **„Daemon-Cycle läuft zu oft (alle 60 s statt alle 1 h)"** | Fehlkonfiguration `signal_check_interval_s` | Der Cycle läuft weiter **alle `interval_s` Sekunden** — der Cap betrifft nur den **Sleep zwischen** Cycles, nicht die Cycle-Frequenz. `signal_check_interval_s=60` heißt: Stop reagiert binnen 60 s, Cycle bleibt bei 1 h. |
| **„Discovery macht plötzlich viel mehr Discoveries als geplant"** | `signal_check_interval_s`-Cap triggert irrtümlich | `_stop` wird nur durch `request_stop()` (vom Signal-Handler oder CLI) gesetzt. Der Cap prüft nur **dieses eine Flag**, sonst nichts. Wenn `request_stop` nicht aufgerufen wird, schläft der Cap durch bis `total_s`. |
| **„Watchdog kann den Daemon immer noch nicht restarten"** | Cap ist zu groß | `signal_check_interval_s` ist ein Default (60 s) — der Watchdog kann den Cap beim Start auf 1 s setzen (`--signal-check-interval-s 1`), dann greift SIGTERM binnen 1 s. Aber: das **muss der Watchdog-Autor** wissen — wir liefern den Hook, der Watchdog nutzt ihn. |

---

## §8 Drift-Liste — bei Ausführung verifizieren

> **Diese Liste ist vollständig.** Was hier nicht steht, hat diese Planungssession am
> 2026-08-26 selbst gegen das Repo, den Live-Prozess und das Phase-8-Vorbild geprüft und
> ist als Fakt formuliert. Rate nichts nach; prüfe diese und nur diese.

1. **Zeilennummern verschieben sich.** Jeder Anker oben trägt den **Verbatim-String** —
   der ist der Anker, die Zahl ist die Abkürzung. Schritt 2 verschiebt `run.py` selbst
   (Klasse + `run_forever`); Schritt 1 verschiebt `phase14_discovery/CLAUDE.md` (Spezial-
   Pläne-Zeile). **Immer per String suchen.**
2. **Phase-8-POST_WINDOW-Hotfix** ist die Vorlage (`phase8_scheduler/CLAUDE.md` Session
   2026-07-11). Der dortige Fix-Snippet (`min(..., idle_poll_s)`) ist ein **anderer
   Pattern** als unser hier vorgeschlagener `_sleep_capped`-Helper — dort ist es ein
   **einzelner Sleep bis zum Zielzeitpunkt**, hier ist es ein **kumulierter Sleep bis
   zur Gesamt-Dauer**. Beide Patterns lösen dasselbe Symptom (unresponsives SIGTERM
   bei langem Sleep), aber die Schleifen-Form ist unterschiedlich. Unser Pattern
   (Chunked-Loop) ist hier angemessen, weil `run_forever` keine Zielzeit hat, sondern
   eine Periode.
3. **`run_forever` ist die einzige Stelle mit `self._sleep_fn(float(self._interval_s))`.**
   Heute gegrept: keine weitere. Auch `_sleep_capped` wird **nicht** an anderen Stellen
   benötigt — der Cycle-Worker (`run_once`) hat keinen eigenen Sleep.
4. **`interval_s`-Injection in `__init__`:** heute `interval_s: int = 3600` (Zeile 163).
   Der neue `signal_check_interval_s` muss **daneben** stehen (nicht zwischen anderen
   Parametern), damit der Diff minimal bleibt. `max_probe_calls_per_run` (Zeile 164)
   ist die visuelle Anker-Stelle.
5. **`_sleep_fn`-Injection:** heute `sleep_fn: Callable[[float], None] = time.sleep`
   (Zeile 167). Bereits injizierbar — der neue Test braucht **keine** neue Dependency,
   er nutzt denselben Mechanismus.
6. **`request_stop()`-Test:** heute implementiert in `run.py:182-184` (Methode auf
   `DiscoveryDaemon`). Signal-Handler in `run.py:348-353` ruft sie auf. Test ruft sie
   direkt auf — kein echter SIGTERM nötig (verifiziert via `grep` der Method-Signatur
   in `run.py`).
7. **`stop_signal = threading.Event()` im Test:** dient nur dazu, den `sleep_fn`-
   Lambda kurz wach zu halten, damit der Thread nicht hängenbleibt. Alternative wäre
   `time.sleep(0.001)` im Lambda, aber dann ist die Chunk-Anzahl nicht deterministisch
   — `Event.wait(0.001)` mit dem Event als Weckmechanismus macht's robuster. Wenn der
   Nikinger den Lambda lieber als reine `time.sleep(0.001)`-Brücke hätte, ist das eine
   reine Stil-Frage; die Akzeptanz A3 ändert sich nicht.
8. **Stub-Klassen `_StubUniverse` / `_StubAvailability`:** die exakte Form hängt vom
   bestehenden `test_run.py`-Setup ab — heute sind die Stubs aus dem vorhandenen
   ≥-6-Test-Block schon da. **Vor Schritt 2 einmal lesen**, welche Imports die
   bestehenden Tests benutzen, und die Stubs genau so übernehmen, damit der neue
   Test kompilierbar ist.
9. **`signal_check_interval_s` Default 60 s:** bewusst konservativ. Trade-off-Tabelle:

   | Wert | Max-Stop-Latenz | Chunk-Overhead | Empfehlung |
   |---|---|---|---|
   | 1 s | 1 s | hoch (3600 Chunks/Std) | Watchdog-only |
   | 30 s | 30 s | gering (120 Chunks/Std) | gut für Tests |
   | **60 s** | **60 s** | **minimal (60 Chunks/Std)** | **Default — diese Session** |
   | 300 s | 5 min | sehr gering (12 Chunks/Std) | analog Phase-8 `idle_poll_s` |

   60 s = 1 min = guter Default: 60× schnellere Stop-Reaktion als `interval_s=3600`,
   60× weniger Chunks als 1 s. Wenn ein künftiger Operator den Cap enger haben
   will, ist `--signal-check-interval-s 30` der Aufruf — kein Code-Edit nötig.
10. **Kein Cross-Phase-Edit.** Heute verifiziert per `grep -rn "source_registry"
    phase[0-9]*` — nur `phase14_discovery/` (Eigentümer), `phase8_scheduler/webui/api.py`
    (Lese-Konsument via `source_registry.arm`) und `phase9_universe/.../wiring.py`
    (kein Touch). Keine Notwendigkeit, an Phase 8 oder Phase 9 etwas zu ändern — der
    Fix ist additiv.

---

## §9 Cross-Referenz

- **Mutterplan:** [`../docs/concepts/phase14_discovery_plan.md`](../docs/concepts/phase14_discovery_plan.md) — D1/D2/D11 sind die nächsten Berührungspunkte; der hier gefixte Signal-Bug ist eine **Impl-Drift** zur Daemon-Ergonomie, kein Plan-Konflikt. Der Mutterplan bleibt unverändert.
- **Geschwister-Mini-Plan:** [`./PHASE14_C_DAEMON_CWD_BUG_PLAN.md`](./PHASE14_C_DAEMON_CWD_BUG_PLAN.md) — der CWD-Bug, der diesen Signal-Bug bei seinem Restart **reproduziert** hat. Beide zusammen schließen die zwei strukturellen Lücken im Phase-14-Daemon.
- **Phase-8-Vorbild:** [`../phase8_scheduler/CLAUDE.md`](../phase8_scheduler/CLAUDE.md) Session 2026-07-11 (POST_WINDOW-Hotfix). Exakt derselbe Bug, dort mit `min(..., idle_poll_s)` gefixt. Unser Pattern hier ist analog, aber loop-basiert (P14-D §8.2).
- **Phasenkopf:** [`./CLAUDE.md`](./CLAUDE.md) — Modul-Tabelle trägt `run.py` als `✅ C2 (Session 9)`. Der Fix ändert **nicht** den Status; das Modul bleibt ✅ — der Bug war eine **fehlende Robustheits-Maßnahme**, kein fehlendes Feature.
- **Session-Archiv:** [`./SESSIONS_ARCHIVE.md`](./SESSIONS_ARCHIVE.md) — die Session-Blöcke 1–11; Session 12 (dieser Fix) wird hier nach Verifikation angehängt.

---

## §10 Korrekturnotiz (Mini-Session 21, 2026-08-31) — D3-Auto-Reload-Claim ist falsch

> **Konvention** (analog Mutterplan §11): diese Notiz steht hier, **nach** §9, weil sie
> keine Plan-Korrektur der ursprünglichen D1/D2 ist — D1 und D2 (die zwei Code-Stellen
> + der Helper-Pattern) bleiben **vollständig gültig**. Was korrigiert wird, ist **D3**:
> die Annahme, ein laufender Daemon lade Code-Edits beim nächsten Cycle automatisch.
> D3 hat sich nach der Ausführung (Session 13/14 mit `27f04d9`) als **empirisch falsch**
> herausgestellt — die Korrekturnotiz in §0 / §1 / §2 / §5 oben verweist auf diese Stelle.

### §10.1 Was D3 behauptet hat

> **D3 (alt):** *„Kein Operator-Restart für die Verifikation — der lebende Daemon
> (PID 34987) lädt den neuen Code beim nächsten Cycle automatisch."*

Stützend wurde angeführt: `run_forever` habe „keine Cross-Modul-Imports" und
`dis.dis(DiscoveryDaemon.run_forever)` zeige, dass die Methode aus `run.py` komme;
ein Edit wirke „ohne Neustart".

### §10.2 Warum das empirisch nicht stimmt

Python speichert eine importierte Klasse in `sys.modules` zwischen. Eine Modifikation
der `.py`-Datei wird beim nächsten `import`-Aufruf wirksam — aber ein **bereits
importierter Prozess** ruft `import` nicht erneut auf. Konkret:

- **Method-Bodies** werden zwar bei jedem Aufruf aus dem Klassenobjekt gelesen
  (Python erstellt bei jedem Method-Call einen neuen Frame, der die Bytecode-Adresse
  aus dem Klassenobjekt auflöst), **aber das Klassenobjekt selbst** ist beim ersten
  Import eingefroren. Eine `.py`-Änderung ersetzt nicht das lebende Klassenobjekt.
- **Folge:** der Daemon läuft mit dem Klassenobjekt weiter, das beim Prozess-Start
  importiert wurde. Method-Dispatch trifft weiterhin die alten Bytecodes.

### §10.3 Empirischer Beweis aus Session 20 (Phase-14-CLAUDE.md, 2026-08-28)

Aus dem Session-20-Block, Phase-14-CLAUDE.md Z. 155-156 (verbatim, Korrekturnotiz
steht dort für P14-E und gilt für P14-D gleichermaßen):

> *„Plan-D3-Korrekturnotiz (gilt für P14-D und P14-E gleichermaßen): der Plan-Hinweis
> ‚der lebende Daemon lädt den neuen Code beim nächsten Cycle automatisch' ist
> **technisch falsch**. Python speichert die geladene Klasse im Module-Cache
> (`sys.modules`); eine Modifikation der `.py`-Datei wirkt **nicht** auf einen
> laufenden Prozess. Der erste Recorder-Restart in Session 19 (PID 108966) lief
> bis zum Session-20-Restart mit altem Code — der SIGTERM-Smoke-Test ist nur
> deshalb ‚1 s', weil der Recorder zwischen zwei Cycle-Wakes stand. **Korrekte
> Lesart:** nach Recorder-Code-Edits IMMER Operator-Restart nötig."*

Belegt ist die Aussage durch zwei voneinander unabhängige Beobachtungen in Session 20:

1. **SIGTERM-Latenz empirisch:** PID 108966 (Recorder mit altem Code, von Session 19
   gestartet) reagierte auf `kill -TERM` erst nach **120 s**, nicht nach ≤ 60 s. Das
   beweist den laufenden Code — er hatte den Sleep-Cap noch nicht.
2. **Cap-Verified auf Neustart:** PID 111032 (Recorder mit neuem Code, direkt nach
   `kill -KILL 108966` + `nohup bash run_recorder.sh`) reagierte auf `kill -TERM`
   in **≤ 1 Sekunde**. Beweis: nur der **Neustart** brachte den Cap zur Wirkung,
   nicht der File-Edit.

### §10.4 Korrigierte Lesart für P14-D (analog P14-E)

| Aspekt | Alt (D3, falsch) | Neu (richtig) |
|---|---|---|
| **Wer lädt neuen Code?** | „der lebende Daemon beim nächsten Cycle" | **niemand** — nur ein Neustart des Prozesses lädt die geänderte `.py`-Datei |
| **Operator-Aktion nach Edit?** | „nicht zwingend nötig" | **IMMER** Operator-Restart des Daemons (via `restart-services.sh restart`, oder manuell `kill -TERM` → 60 s warten → `kill -KILL` → `nohup`); siehe Phase-14-CLAUDE.md Session-20-Block Z. 144-156 |
| **Test-Begründung in D3 (`dis.dis`)** | „zeigt, dass `run_forever` aus `run.py` kommt" | `dis.dis` zeigt, **woher** die Bytecodes **stammen** — nicht, ob das Klassenobjekt im Prozess aktualisiert wurde. Es kommt aus `run.py` zum **Import-Zeitpunkt** des Prozesses, nicht zum Zeitpunkt des Edits. |
| **Konsequenz für künftige Edits** | „der nächste Cycle bringt's" | **Plan & Dokumentation so schreiben**, dass D3 nirgendwo als „Auto-Reload" zitiert wird; Phase-15-Plan-Session übernimmt das strukturell (Helper-Modul für beide Daemons, mit dokumentiertem Restart-Pflicht). |

### §10.5 Was diese Notiz **nicht** macht

- Sie ändert **nicht** D1/D2 (Code-Stelle + Helper-Pattern bleiben unverändert gültig).
- Sie ersetzt **keine** Code-Änderung — der Sleep-Cap ist gebaut, getestet, live-verifiziert.
- Sie ist **kein** Re-Litigieren — die zwei korrigierten Stellen im Plan (§0 / §1 / §2 / §5)
  bleiben inhaltlich rückwärtskompatibel: das, was sie vor der Korrektur beschrieben, war
  zum damaligen Zeitpunkt der ausführenden Session 11 plausibel und ist im selben Commit
  (`27f04d9`) erfolgreich operativ verifiziert worden. Was sich geändert hat, ist **unser
  Verständnis** der Python-Semantik, nicht die Semantik selbst.
- Sie ist **kein** Session-Block — der Phase-14-Phasenkopf bekommt in der nächsten Session
  einen Session-21-Block, der diese Notiz referenziert und die Test-Folge aus
  Mini-Session 21 (P14-E-Test-Fix + Doku-Updates) zusammenfasst.

### §10.6 Cross-Refs

- **Mutterplan** [`../docs/concepts/phase14_discovery_plan.md`](../docs/concepts/phase14_discovery_plan.md)
  §11.3 (post-execution-drift zum Phase-8-POST_WINDOW-Hotfix, Sleep-Cap-Thema) — Pattern-Bruder.
- **Geschwister-Mini-Plan P14-E** [`./PHASE14_E_RECORDER_LOOP_PLAN.md`](./PHASE14_E_RECORDER_LOOP_PLAN.md)
  §2 D3-Korrekturnotiz (gleicher Befund, Recorder-Daemon; Session-20-Block zitiert).
- **Phase-14-CLAUDE.md** Session-20-Block (2026-08-28) — die ursprüngliche Quelle dieser
  Korrekturnotiz; dort stehen die zwei empirischen Belege (PID 108966 + PID 111032).
- **Phase-12-CLAUDE.md** (Rahmen, 2026-08-17 Nikinger-Entscheidung) — dieselbe
  Restart-Pflicht für Scheduler-Code-Edits, dort schon vor P14-D dokumentiert.
