---
status: snapshot
purpose: P12.5 (Messarm) — execution-ready Plan zwischen Step 8.5 und Step 9. Repariert die vier Befunde, die die Beweiswoche strukturell scheitern lassen (U1/U2/U3 aus dem Ultrareview + U5 neu), schärft den Ausfall-Alarm (Entscheidung B), schaltet den Messarm ein und führt die Beweiswoche als reinen Watch-Auftrag bis zum Phase-12-Handover.
read-when: als Bauauftrag für die ausführende Session; danach als Referenz für die Watch-Woche und die Abnahme
detail: L3
up: ./CLAUDE.md
down:
  - ./PHASE12_PREPROOF_HANDOVER.md                      # Befundlage + Tag-1-Live-Ergebnisse (Vorgänger)
  - ../docs/concepts/phase12_data_foundation_plan.md    # Mutterplan: D1–D20, Steps 0–10, §7 PASS-Kriterien
updated: 2026-08-17
---

# P12.5 — Messarm scharfstellen (Plan)

> **Einordnung (chronologisch):** Phase 12, **nach Step 8.5, vor Step 9**. Kein eigenes
> Verzeichnis, kein eigenes Paket — Code, Tests und Session-Block leben in
> `phase12_data_foundation/` (Nikinger-Entscheidung 2026-08-17). „P12.5" ist ein Label für
> diesen Arbeitsblock, keine neue Phase.
>
> **Adressat:** die ausführende Claude-Code-Session (Sonnet 5). Alles unten ist gegen den
> Repo-Stand `6ecba7b` am **2026-08-17** selbst nachgegrept, nicht aus Vorgänger-Dokumenten
> übernommen. Was **nicht** verifiziert werden konnte, steht ausschließlich in **§8** —
> alles andere ist Fakt und muss nicht neu hergeleitet werden.

---

## §0 BLUF

Der Stack steht und lief am 2026-08-17 einen vollen Handelstag live. **Gemessen wurde
trotzdem nichts.** Vier Code-Befunde und ein ausgeschaltetes Flag trennen den Ist-Zustand
von einer Beweiswoche, die bestehen *kann*:

| # | Ohne Fix passiert | §7-Kriterium |
|---|---|---|
| **U1** | Divergenz-Sampler crasht am ersten Epic jedes Passes | **C tot** |
| **U2** | Messzeilen werden beim **ersten** schlechten Tick als `EXPIRED_UNRESOLVED` abgeschrieben | **E / Kern** |
| **U3** | Ein kurzes Archiv kurzschließt die Bar-Kette, die Zeile läuft still ab | **E / Kern** |
| **U5** | Die letzte Tages-Kohorte (~10 % der Zeilen) bekommt **nie** einen Tracker-Tick | **Kern** (Denominator) |
| **Flag** | `enable_shadow_schedule=False` ⇒ **0** Paper-Zeilen | **Kern** garantierter FAIL |
| **Alarm** | `assess_day` meldet bei genau diesem Ausfall `ok=True` | **G** blind |

**Reihenfolge:** Housekeeping → Fixes (U1/U3/B intern, U2/U5 cross-phase) → Neustart mit
beiden Flags → **falsifizierbarer** Nachweis → Watch-Woche → Handover ⇒ Phase 12 zu.

**Was P12.5 ausdrücklich NICHT tut:** die WI-2-Frage beantworten. Sie ist Phase-11-
Wiederaufnahme und bleibt es.

---

## §1 Rahmen + Arbeitsteilung

| Regel | Stand |
|---|---|
| **Arbeitszeit** | **Unter der Woche, auch bot-berührend** (Nikinger 2026-08-17, überschreibt Plan §1). Die Wochenend-Regel ist aufgehoben. |
| **Bot vor dem Edit stoppen** | Ja. Ein Datei-Edit wirkt nicht auf einen laufenden Prozess, und ein zweiter Scheduler daneben löst die Parallel-Login-Falle aus (`phase1_broker_wrapper/lightstreamer_integration_notes.md`). Gegenprobe: `ps aux \| grep scheduler.run`. |
| **Live / Netz / Kosten** | **Nikinger.** Claude baut, testet offline, committet. Kein `live_test.py`, kein Scheduler-Start, kein IG-Call aus der Session. |
| **Live-DB** | Claude liest nur `mode=ro`. |
| **Cross-Phase-Edits** | Freigabepflichtig. In diesem Plan betroffen: **U2** (`phase10_v3/abstain_lessons/paper.py`) und **U5** (`phase8_scheduler/scripts/wiring.py`) — beide in **Step 2**, hinter einem expliziten Gate. |
| **Advisor** | Nur bei: [VERIFY]-Mismatch, Test rot nach 2–3 Versuchen, vor der Abnahme (Step 5). Nicht für Routine-Edits. |

**Prozess-Ist-Stand bei Planschluss (2026-08-17 18:2x CEST, selbst erhoben):**
- Scheduler `pid 35195`, seit 12:09, argv = `python -m scheduler.run --enable-divergence-sampler` → **ohne** `--enable-shadow-schedule`.
- Recorder `pid 33151`, seit 09:56, argv = `python -m data_foundation.run`.

---

## §2 Gelockte Entscheidungen (E1–E9)

Diese Tabelle ist der Ersatz für Nachdenken. **Nicht neu herleiten, nicht „verbessern".**
Widerspricht der Code einer Zeile ⇒ Advisor / Nikinger, nicht stillschweigend abweichen.

| # | Entscheidung | Begründung (kurz) |
|---|---|---|
| **E1** | **U1 wird kanonisch in `service.py:119` gefixt**, nicht in `heartbeat.py:175`. | `BudgetedIGBarProvider` ist die *eine* Stelle, an der IGs Rohformat ins System kommt. Der Fix dort heilt zugleich den lexikalischen Vergleich in `heartbeat.py:174` (`window_start = ig_bar.ts` gegen ISO-Archivzeilen). `_write_through` normalisiert bereits selbst — `normalize_bar_ts` ist idempotent, es bricht nichts doppelt. |
| **E2** | **Der „Never raises"-Vertrag von `BudgetedIGBarProvider` bleibt** (`service.py:61-62`). `normalize_bar_ts` wirft `ArchiveError` ⇒ die Bar-Liste wird gewrappt, Fehler ⇒ `_emit(reason="bad_timestamp")` + `return None`. | Ein Provider, der wirft, killt die Kette — genau der Schaden, den U1 anrichtet. Der Fix darf ihn nicht an anderer Stelle wieder einbauen. |
| **E3** | **U3 wird als Deckungs-Schwelle am Archiv-Kurzschluss gefixt** (`service.py:207`), **nicht** als Start-Zeit-Vergleich. | Ein strikter `bars[0].ts_utc <= start_utc`-Check schlägt **immer** fehl: der Tracker fragt `now−300min` an, der Handel beginnt erst 09:00. Das wäre ein permanenter Cache-Miss ⇒ Dauer-Fetch. `coverage_ratio` existiert bereits (`archive.py`) und trennt gesund (~0,80) von kaputt (~0,03) sauber. |
| **E4** | **Die Schwelle kommt NICHT an `service.py:217`** (den IG-Top-up). | Symmetrie wäre hier falsch: ein teilweise, aber ausreichend gedecktes Archiv würde jeden Tick einen ~301-Punkte-IG-Fetch auslösen. Bei `:207` fällt der Pfad zuerst auf **yF (gratis)** durch, das backfillt, und der bestehende Tail-Check bei `:217` lehnt den IG-Zweig danach korrekt ab. |
| **E5** | **U2 wird in `_resolve_group` gefixt** (`paper.py:588`), nicht in `wiring.py`s `bar_fetch`. | `resolve_paper_trade` gibt `None` an **beiden** Rückgabestellen (`paper.py:248` und `:275/276`) mit derselben Bedeutung: *„zu wenig Daten"*, nie *„kein Ergebnis"*. Ein Write-off auf `None` ist damit der Bug selbst. Beide Aufrufer (Debatten-Pfad + H1-Timer) laufen durch diese eine Stelle. |
| **E6** | **Der Zähler heißt ab jetzt „fehlgeschlagene Auflösungsversuche", nicht „fehlgeschlagene Fetches".** Docstring `paper.py:552-566` **und** der Kommentar `wiring.py:468-480` werden im selben Commit korrigiert. | Der falsche Kommentar ist selbst einer der vier Befunde. Ein Fix, der ihn stehen lässt, produziert den nächsten Fehlschluss. |
| **E7** | **U5 wird als Deadline-Marge im Wiring gefixt** (`wiring.py:799`), nicht in `paper.py`. | `open_scheduled_pairs`' Deadline-Guard ist korrekt; falsch ist der **übergebene Wert**. `window_close` selbst lässt der letzten Kohorte null Tracker-Ticks. Das Wiring besitzt die Policy, `paper.py` bleibt deterministisch. |
| **E8** | **Entscheidung B: `assess_day` wertet `shadow_enabled=False` als Problem + `ok=False`** — bedingungslos, kein neuer Parameter. | Der Daemon kann nicht lügen (`wiring.py:950` liest `config.enable_shadow_schedule`). `data_health.py --shadow-enabled` ist eine Operator-Behauptung; vergisst jemand das Flag, ist Exit 1 die **richtige** Antwort. Fail-loud ist genau die Fehlerklasse, um die es hier geht. |
| **E9** | **U4 (TickerMapper-Refresh) und Entscheidung C (SUN*-Epics vs. `max_active`) sind DRAUSSEN.** | Nikinger-Entscheidung 2026-08-17. U4 ist reine Kostenfrage, heilt beim Neustart, und der Pool ist mit 5 stabilen Epics real nicht betroffen. **Un-Defer-Trigger** für U4: taucht `EpicNotMappedError` in den Watch-Wochen-Logs auf. C bleibt bei der Handover-Empfehlung „(c) jetzt, (a) nach Step 9". |

---

## §3 Die Befunde mit verifizierten Ankern

> Alle Zeilennummern **selbst gegrept am 2026-08-17**, Stand `6ecba7b`. Trotzdem gilt §8.1:
> vor dem Edit einmal per Grep auf den zitierten **Verbatim-String** gegenprüfen — der ist
> der eigentliche Anker, die Zahl nur die Abkürzung.

### U1 — `DivergenceSampler` crasht an echten IG-Timestamps

```
service.py:117-127   PriceBar(ts=b.get("timestamp", ""), …)      ← :119, IG-Rohformat ungefiltert
models.py:70-97      normalize_bar_ts()                          ← kann "yyyy/MM/dd HH:mm:ss" UND ISO
heartbeat.py:167     self._last_sample_date[epic] = today        ← Drossel VOR dem Fetch gesetzt
heartbeat.py:174     window_start = ig_bar.ts                    ← lexikalischer Vergleich gegen ISO
heartbeat.py:175     window_end = _iso(_parse(ig_bar.ts) + …)    ← ValueError hier
heartbeat.py:204-209 _parse() → datetime.fromisoformat           ← kann IGs Format nicht
wiring.py:930f       for rec in …measurable_universe(): sample_epic(...)  ← kein except ⇒ Schleife stirbt
```

**Live belegt** (`data/state/research_health.jsonl`, 2026-08-17): Pass 1 sampelte genau ein
Epic (`IX.D.DAX.IFMM.IP`), Pass 2 genau eines (`IX.D.DAX.IGN.IP`) — jeweils das nächste in
der Liste. Ein funktionierender Sampler hätte im ersten Pass alle 5 abgearbeitet. Der
IG-Fetch **gelingt** (6 Punkte gebucht, `source_spend.kind='sample'`), der Crash liegt danach.

**Warum die Tests das nie fingen:** `_FakeBudgetedIG.get_bars` (`tests/test_heartbeat.py:174`)
liefert `f"{self.day}T09:00:00.000Z"` — **ISO**, ein Format, das aus dieser Quelle in
Produktion nie kommt. Die fehlende Fixture *ist* der Defekt.

### U2 — Der Retry-Cap ist wirkungslos

```
wiring.py:514-517    bar_fetch → bar_service.get_window(...)     ← durchgehend fail-soft, liefert []
paper.py:544-549     except um bar_fetch → _charge_failed_attempt ← feuert nie, es wirft ja nichts
paper.py:586-590     outcome is None → self.store.mark_expired()  ← Write-off beim ERSTEN Miss
paper.py:552-579     _charge_failed_attempt (Cap-Logik, intakt)
wiring.py:468-480    Kommentar behauptet ausdrücklich das Gegenteil  ← falsch, E6
wiring.py:481        _PAPER_MAX_FETCH_ATTEMPTS = 12
wiring.py:559        stale_after_minutes = exec_cfg.max_hold_minutes + 60   (= 300)
```

**Die Zahlen passen exakt:** 12 Versuche × 5-Min-Kadenz = 60 Min Toleranz; eine Zeile ist bei
`t+240` fällig und der Stale-Cut greift bei `t+300`. Der Cap ist also korrekt dimensioniert —
er wird nur nie erreicht.

### U3 — `_covers_tail` prüft nur das Fensterende

```
service.py:202-228   BarService.get_window
service.py:207       if _covers_tail(archived, end_utc, minutes): return …   ← der Kurzschluss
service.py:217       if not _covers_tail(...) and self._ig_provider …        ← IG-Top-up (E4: NICHT anfassen)
service.py:254-261   _covers_tail → nur bars[-1].ts_utc >= end−1 Intervall
```

Ein frisches, aber kurzes Archiv (Recorder-Neustart, erster Tag, Lücke) erfüllt den
Tail-Check und kurzschließt ⇒ `resolve_paper_trade` findet keine Bar bis `time_stop_utc` ⇒
`None` ⇒ (mit U2) sofortiger Write-off.

**Rechnung zur Schwelle** (Fenster = `now−300min … now`, Auflösung 1m):

| Lage | vorhandene / erwartete Minuten | ratio |
|---|---|---|
| gesund (Handel ab 09:00, Fälligkeit 13:00) | 240 / 300 | **0,80** |
| Recorder erst ab 09:56 (Tag 1, real) | 184 / 300 | **0,61** |
| Recorder-Lücke 30 Min | 210 / 300 | **0,70** |
| kurzes Archiv (U3-Fall) | 10 / 300 | **0,03** |

⇒ **Schwelle 0.5** trennt sicher, mit Marge nach beiden Seiten. Selbstheilend: fällt der Pfad
durch, holt yF (gratis) die Bars, schreibt sie durch, und der nächste Aufruf trifft wieder
das Archiv.

### U5 — Die letzte Tages-Kohorte bekommt nie einen Tick (**NEU, 2026-08-17**)

```
runner.py:399        self._run_paper_tracker()          ← steht im WINDOW-Zweig
runner.py:401-407    POST_WINDOW-Zweig: warm_session + reconcile + health_check + sleep — KEIN Tracker-Tick
paper.py:442-445     deadline-Guard: now + max_hold > deadline ⇒ ganzer Tick übersprungen
wiring.py:798-800    deadline = heute window_close (17:30), unverändert übergeben
phase5_execution/execution/config.py:102   max_hold_minutes = 240
```

**Ablauf:** Kohorten öffnen alle 30 Min ab 09:00, solange `now + 240min ≤ 17:30` ⇒ letzte
Öffnung **13:30**, deren `time_stop_utc` = **17:30** = `window_close`. Der Tracker tickt nur
im WINDOW; um 17:30 kippt die Phase auf POST_WINDOW. Die 13:30-Kohorte bekommt **keinen
einzigen** Tick. Am nächsten Morgen ist sie älter als `stale_after_minutes` (300) und wird
**ohne Fetch** stale-expired (`paper.py:532-535`).

**Größenordnung:** 10 Kohorten/Tag (09:00–13:30 im 30-Min-Takt), davon 1 systematisch tot
⇒ **~10 %** der Messzeilen. Kein Datenqualitätsproblem, ein Fahrplanfehler — die Freitags-
Review würde es sonst als Ersteres lesen.

---

## §4 Schritt-Sequenz

> Jeder Step endet mit **grünem `pytest`** (per-Phase separat, Memory `reference_running_phase_tests`,
> geteilter Venv `phase1_broker_wrapper/.venv`) **+ einem atomaren Commit**. Kein Step gilt als
> fertig ohne grüne Tests.

---

### Step 1 — Housekeeping (docs-/read-only, kein Gate)

**1a — Legacy-Grep-Ritual.**
```bash
grep -rn -i "turbo\|CALL/PUT\|pre_trade_option_check\|expected hold" --include="*.py" --include="*.md" .
```
**Erwartung: dokumentierter No-Op.** Einziger aktiver Treffer ist der eingefrorene
`turbo_candidates.json` (P2/P5-Gate-2-Contract, **nicht umbenennen**); alles andere sind
Doku-Zeilen, die die historische Bereinigung *bestätigen*. Präzedenz:
`phase8_scheduler/SESSIONS_ARCHIVE.md:1185`, `phase10_v3/CLAUDE.md:99-100`. Ergebnis in einer
Zeile im Session-Block festhalten — **auch wenn es ein No-Op ist** (das ist der Punkt des Rituals).

**1b — `.md` ↔ Code-Verify.** Prüfen und bei Abweichung **den Code gewinnen lassen** + die
Doku mit datiertem Vermerk korrigieren:
- Root-`CLAUDE.md` Phasen-Tabelle Zeile 12 · `ROADMAP.md` Phase-12-Block · `docs/INDEX.md`
  Phase-12-Einträge · `phase12_data_foundation/CLAUDE.md` Kopf · `README.md`.
- Konkret zu prüfen: behauptet noch irgendwo etwas „Step 9 läuft" / „Messarm an" / einen
  Test-Zählstand ≠ dem heute gemessenen?
- Die INDEX-Zeile **für diesen Plan** hat die Planungssession bereits gesetzt (direkt nach
  dem Pre-Proof-Handover, chronologisch korrekt) — nur gegenprüfen, nicht doppeln. **Jedes
  weitere** neue `.md` aus P12.5 (Review-Doc, Closeout) braucht seine Zeile im **selben**
  Commit, in dem es entsteht.

**1c — Regression-Baseline VOR jedem Fix.** Alle Phasen einzeln, Zählstände notieren:
```bash
for p in phase1_broker_wrapper phase2_persistence phase3_external_data phase4_research \
         phase5_execution phase6_debate phase7_reward phase8_scheduler phase9_universe \
         phase10_v3 phase12_data_foundation meta_m1_harness tests; do
  echo "== $p"; phase1_broker_wrapper/.venv/bin/python -m pytest "$p" -q 2>&1 | tail -1
done
```
**Heute bereits gemessen und damit Fakt: `phase12_data_foundation` = 117 passed.** Der Rest
laut Session-5-Stand (P1 87 · P2 77 · P3 104 · P4 155 · P5 173 · P6 76 · P7 138 · P8 237 ·
P9 80 · P10 159 · meta 28 · root 80) — **das sind Erwartungswerte, keine Fakten** (§8.2).
Abweichungen dokumentieren, nicht wegdiskutieren.

**Akzeptanz Step 1:** Grep-Ergebnis dokumentiert · alle fünf Statusdokumente stimmen mit dem
Code überein · Baseline-Tabelle im Session-Block · INDEX-Zeile gesetzt · ein Commit
`phase12: P12.5 Step 1 — housekeeping + baseline`.

---

### Step 2 — Fixes in `data_foundation/` (phasen-intern, **kein** Freigabe-Gate)

> Drei der fünf Änderungen liegen vollständig in Phase-12-eigenem Code. Bot vorher stoppen
> ist hier **nicht** nötig (der laufende Prozess liest die Datei nicht neu) — aber der
> Neustart in Step 4 ist Pflicht, sonst wirkt nichts davon.

#### 2a — U1: `service.py:119`

**Datei:** `phase12_data_foundation/data_foundation/service.py`
**Anker (verbatim):** `                ts=b.get("timestamp", ""),`

`normalize_bar_ts` ist bereits importiert (`service.py:25`). Die Listen-Konstruktion
(`:117-127`) wird gewrappt, damit E2 (Never-raises) hält:

```python
try:
    bars = [
        PriceBar(
            ts=normalize_bar_ts(b.get("timestamp", "")),
            ...
        )
        for b in raw_bars
    ]
except ArchiveError:
    self._emit(epic, False, reason="bad_timestamp")
    return None
```
`ArchiveError` aus `data_foundation.exceptions` importieren (Modul-Top, wie `models`).

**Tests** (`tests/test_service.py`, neu):
1. `test_ig_provider_normalizes_ig_raw_timestamps` — Fake-Broker liefert
   `{"timestamp": "2026/08/17 14:15:00", ...}`; Assertion: der zurückgegebene `PriceBar.ts`
   ist `"2026-08-17T14:15:00.000Z"`.
2. `test_ig_provider_returns_none_on_unparseable_timestamp` — `{"timestamp": "not a date"}`
   ⇒ `get_bars(...) is None`, **kein** Raise, ein `bar_fetch`-Event mit
   `reason == "bad_timestamp"`.

**Tests** (`tests/test_heartbeat.py`, geändert — das ist der eigentliche Regressionsschutz):
3. `_FakeBudgetedIG.get_bars` (`:174`) auf das **IG-Rohformat** umstellen und den Sampler
   end-to-end laufen lassen: `sample_epic` darf nicht werfen, muss die yF-Archivbar desselben
   Fensters finden und ein `quote_divergence`-Event erzeugen.
   → **Achtung:** Diese Fixture-Änderung trifft mehrere bestehende Sampler-Tests
   (`:178`, `:191`, `:214`, `:224`, `:247` …). Sie **müssen** danach grün sein — genau das ist
   der Beweis, dass E1 den lexikalischen Vergleich in `heartbeat.py:174` mitgeheilt hat.
   Wird ein Test dabei rot, ist das ein **echter Befund**, kein Fixture-Problem: dann
   Advisor, nicht Fixture zurückdrehen.

#### 2b — U3: `service.py:207`

**Anker (verbatim):** `        if _covers_tail(archived, end_utc, minutes):`

Neue Modul-Konstante neben `_RESOLUTION_MINUTES` (`service.py:31`):
```python
# ponytail: fixed threshold, calibrated against the observed spread (0.80 healthy vs. 0.03
# for the short-archive case this guards, P12.5 plan §3/U3). Ceiling: coverage_ratio counts
# naive wall-clock minutes, so it never reaches 1.0 across a pre-market span. Upgrade path if
# it ever misfires: a trading-calendar-aware expected-minutes count in BarArchive.
_MIN_WINDOW_COVERAGE = 0.5
```
Bedingung erweitern:
```python
if (_covers_tail(archived, end_utc, minutes)
        and self._archive.coverage_ratio(epic, resolution, start_utc, end_utc) >= _MIN_WINDOW_COVERAGE):
```
**`service.py:217` bleibt unverändert** (E4).

**Tests** (`tests/test_service.py`, neu):
4. `test_get_window_refetches_when_archive_window_is_too_short` — Archiv enthält nur die
   letzten 10 Minuten eines 300-Minuten-Fensters; Assertion: die Provider-Kette **wird**
   gerufen (bisher nicht).
5. `test_get_window_uses_archive_when_coverage_is_adequate` — Archiv deckt 240 von 300
   Minuten (der reale Gesund-Fall); Assertion: die Kette wird **nicht** gerufen (kein
   Dauer-Fetch, das ist die Kosten-Regression).

#### 2c — Entscheidung B: `heartbeat.py`

**Anker (verbatim):** `    if shadow_enabled and pairs_resolved == 0 and pairs_typed_expired == 0:` (`:105`)

Direkt davor eine dritte Bedingung, dazu die `assess_day`-Docstring (`:58-63`) nachziehen
(sie zählt heute explizit „genau zwei Bedingungen" auf):
```python
if not shadow_enabled:
    problems.append(
        "measurement arm off: enable_shadow_schedule is False — no shadow pairs can be "
        "opened, so this day measures nothing (Phase-12 §7 Kern cannot pass)"
    )
    ok = False
```

**Tests** (`tests/test_heartbeat.py`, neu):
6. `test_assess_day_flags_measurement_arm_off` — `shadow_enabled=False`, Bars vorhanden,
   messbare Epics vorhanden ⇒ `ok is False` und `"measurement arm off"` in einem Problem-String.
   **Das ist die exakte Tag-1-Situation, die live `ok=True` meldete.**
7. Bestehende `assess_day`-Tests durchsehen: jeder, der mit `shadow_enabled=False` ein
   `ok=True` erwartet, kodiert ab jetzt das falsche Verhalten und wird angepasst — mit einer
   Zeile Kommentar, warum.

**Akzeptanz Step 2:** `pytest phase12_data_foundation/tests -q` grün, **117 → ~123**.
Ein Commit `phase12: P12.5 Step 2 — U1/U3 + heartbeat flags a dead measurement arm`.

---

### Step 3 — Cross-Phase-Fixes (**Freigabe-Gate: Nikinger fragen, bevor editiert wird**)

> Zwei Dateien außerhalb `data_foundation/`. Beide Änderungen sind klein und additiv, beide
> berühren **keinen** Gate-, VETO- oder Order-Pfad. Vor dem Edit: **Bot stoppen** (§1) — nicht
> weil die Datei sonst nicht schreibbar wäre, sondern damit Edit und Neustart eine Einheit
> bilden und kein halb-gepatchter Prozess weiterläuft.

#### 3a — U2: `phase10_v3/abstain_lessons/paper.py:588`

**Anker (verbatim):** `                if outcome is None:`

```python
if outcome is None:
    # Both of resolve_paper_trade's None-returns mean "not enough bar data yet", never
    # "no outcome" -- so this is a failed resolution attempt, subject to the same cap as
    # a raised fetch error, not an immediate write-off (P12.5 plan §3/U2).
    self._charge_failed_attempt([trade], now)
    continue
```

Dazu **im selben Commit** (E6):
- `_charge_failed_attempt`-Docstring (`paper.py:552-566`): „failed fetch" → „failed
  resolution attempt (a raised fetch error **or** a fetch that came back without enough
  bars)". Der Satz „a successful `_resolve_group` always terminates it" ist ab jetzt falsch
  und muss weg.
- `wiring.py:468-480`: der Absatz behauptet, ein erschöpftes Budget zeige sich „as a
  short/failed get_window result … subject to this same cap". Das war **nicht** wahr und ist
  es erst durch diesen Fix. Korrigieren + datiert vermerken.

**Tests** (`phase10_v3/tests/`, in der Datei mit den bestehenden Tracker-Guards):
8. `test_tick_charges_attempt_instead_of_expiring_on_empty_bars` — `bar_fetch` liefert `[]`;
   nach **einem** Tick: Trade weiterhin `OPEN`, Attempt-Zähler 1. **Das ist der falsifizierbare
   Kern des Fixes.**
9. `test_tick_expires_after_the_attempt_cap` — 12 Ticks mit leerem `bar_fetch` ⇒ danach
   `EXPIRED_UNRESOLVED`. (Cap-Verhalten bleibt, nur der Auslöser ändert sich.)
10. `test_tick_still_resolves_normally_when_bars_are_sufficient` — Regressionsschutz: der
    gesunde Pfad ist unverändert.

#### 3b — U5: `phase8_scheduler/scripts/wiring.py:799`

**Anker (verbatim):** `            deadline = now.replace(hour=close_hour, minute=close_minute, second=0, microsecond=0)`

```python
# P12.5/U5: window_close itself leaves the last cohort zero tracker ticks -- the tracker
# only runs in the WINDOW phase (runner.py:399), and a pair whose time-stop IS
# window_close goes due exactly when the phase flips to POST_WINDOW. It then dies on the
# stale cut next morning without a single fetch (~10% of the day's measurement rows).
# Two cycle intervals of margin give that cohort two real chances.
deadline = now.replace(
    hour=close_hour, minute=close_minute, second=0, microsecond=0
) - timedelta(minutes=2 * config.cycle_interval_min)
```
**Bei Ausführung verifizieren (§8.3):** heißt das Feld wirklich `cycle_interval_min`, und ist
`timedelta` in `wiring.py` bereits importiert? (Bei `:516` wird `timedelta` benutzt ⇒ sehr
wahrscheinlich ja, trotzdem gegenprüfen.) Der Docstring der Closure (`wiring.py:785-788`)
erklärt die Deadline und muss die Marge mit aufnehmen.

**Test:** `wiring.py` hat konventionsgemäß **keine** pytest-Suite (dokumentiert:
`phase12_data_foundation/tests/test_run.py:3`). Verifikation daher:
- `python -m py_compile phase8_scheduler/scripts/wiring.py` sauber, **und**
- ein AST-Guard nach dem Vorbild von `tests/test_resolver_wiring.py` (existiert bereits,
  parst `wiring.py` und prüft einen Call im isolierten Funktionskörper):
11. `test_shadow_deadline_has_margin` in `phase12_data_foundation/tests/` — parst
    `wiring.py`, isoliert den `shadow_pair_scheduler`-Body, assertet, dass die
    `deadline`-Zuweisung eine Subtraktion enthält. Ein datei-weiter Grep würde eine
    verschobene/tote Zeile nicht fangen — dieselbe Lücke, die Step 8.5 aufdeckte.

**Akzeptanz Step 3:** `pytest phase10_v3/tests -q` grün (159 → ~162) ·
`pytest phase12_data_foundation/tests -q` grün (~123 → ~124) · `py_compile` sauber ·
**volle Regression** wie in 1c, alle Zählstände dokumentiert. Ein Commit
`phase12: P12.5 Step 3 — U2 retry-cap actually fires + U5 shadow deadline margin`.

---

### Step 4 — Neustart mit dem Messarm (**Nikinger, live**)

> Claudes Arbeit endet bei *committed + grün*. Dieser Step ist Operator-Arbeit. Der Plan
> liefert die Sequenz, nicht die Ausführung.

**Erst stoppen, dann starten** — ein zweiter Scheduler neben dem laufenden öffnet zwei
IG-Logins parallel und die zerschießen sich gegenseitig die Session-Tokens. Der Fehler sähe
dann aus wie „die Fixes wirken nicht".

1. Laufenden Scheduler stoppen (Kill-Switch im Dashboard oder `kill 35195`; POST_WINDOW
   greift seit dem 2026-07-11-Hotfix binnen ≤ 5 Min).
2. **Gegenprobe:** `ps aux | grep scheduler.run` ⇒ **keine Zeile mehr.**
3. ```bash
   bash phase8_scheduler/scripts/run_scheduler.sh --enable-divergence-sampler --enable-shadow-schedule
   ```
   Beide Flags sind verbatim gegen `phase8_scheduler/scheduler/run.py` geprüft (12
   `add_argument`-Blöcke, §8.4 nennt die Gegenprobe). Der Recorder wird vom Skript
   mitgestartet und darf weiterlaufen — seine PID-Datei verweigert das Duplikat selbst.
   **Ein drittes Flag ist nicht nötig:** `enable_paper_trades` ist bereits Default `True`
   (`config.py:177`), ebenso `enable_bar_service` (`:156`) und
   `enable_measurement_heartbeat` (`:198`).
4. Der Universe-Refresher läuft im Preflight sofort (`runner.py:285`), nicht erst nach der
   240-Min-Drossel — der Resolver-Log mit den `ResolverReport`-Zählern kommt binnen Minuten.

---

### Step 5 — Der falsifizierbare Nachweis (**am Starttag, nicht am Freitag**)

> Dies ist der **vierte** Vorfall derselben Fehlerklasse (`enable_ig_bars` → `SymbolResolver`
> → `enable_shadow_schedule` → jetzt). Grüne Tests beweisen davon **nichts**. Der Nachweis
> besteht aus drei Artefakten, alle drei müssen vorliegen, bevor irgendwo „läuft" steht.

**(a) Echte argv.**
```bash
ps aux | grep scheduler.run
```
⇒ muss **beide** Flags zeigen. Ausgabe in den Session-Block kopieren, nicht paraphrasieren.

**(b) Config-Default zurückgelesen** — der Prozess hat gelesen, was wir glauben:
```bash
grep -n "enable_shadow_schedule\|enable_paper_trades" phase8_scheduler/scheduler/config.py
```

**(c) Eine Zeile echte Live-Daten** (~30 Min nach dem Start, read-only):
```bash
phase1_broker_wrapper/.venv/bin/python -c "
import sqlite3, datetime
c = sqlite3.connect('file:data/trading_bot.sqlite?mode=ro', uri=True)
today = datetime.datetime.now(datetime.timezone.utc).strftime('%Y-%m-%d')
print(c.execute(
  \"SELECT variant, COUNT(*) FROM paper_trades \"
  \"WHERE variant IN ('SHADOW_BUY','SHADOW_SELL') AND created_utc >= ? GROUP BY 1\",
  (today,)).fetchall())"
```
⇒ **Soll: zwei Zeilen, > 0.** Die letzten Paper-Zeilen überhaupt stammen vom **2026-08-07**
(heute verifiziert) — jede Zeile mit heutigem Datum ist damit netto neu und nicht mit
Altbestand verwechselbar.

**(d) Der Alarm-Positivtest** — der Alarm muss auch *anschlagen* können:
```bash
phase1_broker_wrapper/.venv/bin/python phase12_data_foundation/scripts/data_health.py \
  --day <heute> --shadow-enabled
```
Bei null Pairs muss das jetzt `ok=False` / Exit `1` liefern. Liefert es `ok=True`, ist
Entscheidung B nicht wirksam geworden — dann **stoppen und nachsehen**, nicht die Woche starten.

**Wenn (c) leer bleibt:** nicht warten, nicht hoffen. Erst prüfen ob `measurable_universe()`
noch 5 Epics liefert, dann ob `shadow_pair_scheduler` gebaut wurde
(`wiring.py:775-776` verlangt **beide** Config-Flags), dann den Logauszug lesen.

---

### Step 6 — Beweiswoche als Watch-Auftrag (5 Handelstage)

> **Nikinger-Vorgabe:** die Woche läuft, aber **nur mit Watch-Auftrag**. Keine Feature-Arbeit,
> kein „schnell noch"-Fix, kein Nachjustieren an Schwellen, während gemessen wird. Wer
> mittendrin an der Messapparatur dreht, hat am Freitag keine Woche, sondern fünf Fragmente.

**Täglich, ein Befehl** (read-only, kein Netz, werktags erlaubt):
```bash
phase1_broker_wrapper/.venv/bin/python phase12_data_foundation/scripts/data_health.py \
  --day <letzter Handelstag> --shadow-enabled
```
Exit `0` erwartet. Ausgabe (die 6 Zählwerte) in eine Zeile pro Tag im Session-Block.

**Watch-Liste — was einen Abbruch rechtfertigt (und was ausdrücklich nicht):**

| Beobachtung | Reaktion |
|---|---|
| Exit `1` an einem Tag | Ursache notieren, **weiterlaufen lassen**. Ein einzelner typisierter Ausfalltag ist ein Messergebnis, kein Abbruchgrund. |
| Exit `1` an **zwei aufeinanderfolgenden** Tagen | **Stopp.** Root-Cause-Session. Dieselbe Notbremsen-Logik wie 2026-08-11 — nicht auf wackligem Fundament weiterbauen. |
| `pairs_opened = 0` an einem Handelstag | **Sofort** prüfen (das ist der Tag-1-Fehler in Wiederholung), nicht bis Freitag warten. |
| `EpicNotMappedError` im Log | U4 un-defern (E9), **nach** der Woche. |
| IG-Verbrauch > 1 000 Punkte bis Mittwoch | Prognose in `data_health.py` lesen; Soll für die Woche ist **< 1 500** (§7/F). Heute: 136. |
| `quote_divergence`-Events = 0 | **Kein** Problem, sofern der Sampler nachweislich lief (Kriterium C zählt die Ausführung, nicht den Fund). |
| Einzelne `EXPIRED_UNRESOLVED` | Erwartet. Erst der **Anteil** ist die Kennzahl, und den liest die Freitags-Review. |

**Freitags: Review-Session.** Ergebnisdoc `phase12_data_foundation/PROOF_WEEK_REVIEW_<date>.md`,
Muster `phase10_v3/DATA_WEEK_REVIEW_*.md`. Abnahme gegen §7 des Mutterplans:

| Anf. | Beweis in der Woche | Anmerkung für diese Woche |
|---|---|---|
| **A** | kein neuer Parallel-Speicher; Grep-Abnahmen aus Step 7 bleiben wahr | — |
| **B** | ≥ 1 Instrument erreicht `ok`/typisierten Status **ohne Code-Edit** | — |
| **C** | Sampler lief täglich; `quote_divergence`-Events existieren (leere Tage zählen als Ausführungsbeweis) | **war bis U1 tot** — hier zeigt sich, ob der Fix greift |
| **D** | jedes nicht-messbare Epic trägt typisierten Status; kein `NULL`-Fallback; SUN*-Epics erzeugen null Paper-Zeilen | Tag-1 bereits erfüllt |
| **E** | jede aufgelöste `paper_trades`-Zeile hat `resolution_source ≠ NULL`; `abstain_report.py --paper` gruppiert danach | **Spalte ist noch nie in echt gefüllt worden** |
| **F** | Budget-Prognose vs. Realverbrauch, Soll < 1 500, **kein** 403, `remaining_estimate` monoton plausibel | zzgl. **neu**: Anteil Archiv-Treffer vs. Fetch (U3-Schwelle im Feld, §8.5) |
| **G** | 5/5 Tage `measurement_heartbeat`; jeder Problemtag am **selben Tag** CRITICAL | Entscheidung B ist Teil des Beweises |
| **Kern** | ≥ 4 von 5 Handelstagen mit aufgelösten Shadow-Pairs **pro `ok`-Epic**; null Quarantäne-Kaskaden durch Budget | s. Warnung unten |

> ⚠️ **Warnung für die Review, ins Ergebnisdoc übernehmen:** die 5 messbaren Epics sind nur
> **3 verschiedene yF-Ticker** — `IX.D.DAX.IFMM.IP` und `IX.D.DAX.IGN.IP` teilen sich `^GDAXI`,
> `IX.D.IBEX.IFM.IP` und `IX.D.IBEX.FWM2.IP` teilen sich `^IBEX`, dazu `IX.D.CAC.IFE.IP` =
> `^FCHI` (heute aus der Live-DB erhoben). §7 „Kern" ist **per Epic** formuliert und damit
> erfüllbar — aber Auflösungs- und Divergenz-Statistik über diese Paare sind **korreliert,
> nicht unabhängig**. Nicht als fünf unabhängige Stichproben lesen.

**PASS ⇒** Phase-12-Kern abgenommen; Step 10 (Lightstreamer) freigeschaltet; Phase 11 (WI-2)
kann wiederaufgenommen werden.
**FAIL ⇒** Root-Cause-Session, kein Weiterbau.

---

### Step 7 — Handover ⇒ Phase 12 zu

`phase12_data_foundation/PHASE12_CLOSEOUT_HANDOVER.md` nach Vorlage
`docs/HANDOVER_PROMPT.md`. Pflichtinhalt, weil die Vorlage genau das erzwingt:
- **Ergebnis + eine Zeile „nicht erreicht / offen geblieben"** (ein Closeout ohne die zweite
  Zeile ist eine Werbebroschüre).
- Was nur **offline** bewiesen ist, explizit als solches benannt.
- Delta gegen die Anforderungen **A–G** aus `PHASE11_DEFERRAL_HANDOVER.md`.
- Die vier Kandidaten für danach aus Mutterplan §6, mit Empfehlung **1 → 2 → 4, 3 nebenher**:
  Funnel-Reason-Split (`REASON_LLM_ABSTAIN` durchreichen) → Promotion lernt
  `data_source_status` → Phase 11 / WI-2 wiederaufnehmen, `market_context` aus dem
  BarService nebenher.
- **Die Nummerierung des Danach entscheidet der Nikinger**, nicht die Session.

**Doku-Sync im selben Commit** (Rotationsregel!): Session-Block in
`phase12_data_foundation/CLAUDE.md` ersetzen, den bisherigen **verbatim** nach
`SESSIONS_ARCHIVE.md` (newest-first) verschieben; Root-`CLAUDE.md` Zeile 12; `ROADMAP.md`;
`docs/INDEX.md` (+ Zeile für das Review-Doc **und** das Closeout-Doc); `README.md`.
**Memory aktualisieren:** `project_phase12_data_foundation_plan.md` und
`feedback_verify_flags_are_on.md` — letzteres um den vierten Vorfall **und** darum, dass der
Nachweis diesmal *vor* dem Weiterarbeiten erbracht wurde.

---

## §5 Test-Bilanz

| Suite | vorher | nachher (erwartet) | neu |
|---|---|---|---|
| `phase12_data_foundation` | **117** (heute gemessen) | ~124 | 2 Provider · 2 `get_window` · 1 `assess_day` · 1 AST-Guard, + angepasste Sampler-Fixtures |
| `phase10_v3` | 159 (Erwartung, §8.2) | ~162 | 3 Tracker-Tests |
| alle übrigen | Baseline aus 1c | **unverändert** | — |

Ändert sich eine Zahl außerhalb dieser Tabelle, ist das ein Befund und gehört in den
Session-Block — nicht stillschweigend übernehmen.

---

## §6 Risiken

- **Die U3-Schwelle ist ein Kalibrierknopf, keine Wahrheit.** 0.5 ist gegen die gemessene
  Spreizung (0,80 / 0,61 / 0,03) gewählt, nicht hergeleitet. Zu hoch ⇒ Dauer-Fetch (Kosten,
  sichtbar an F); zu niedrig ⇒ U3 lebt weiter (sichtbar an E). Beides fällt in der Woche auf,
  **wenn** F den Archiv-/Fetch-Split ausweist (§8.5).
- **U2 verlängert die Lebensdauer fälliger Zeilen** von einem Tick auf bis zu 12. Der
  Stale-Cut (300 Min) bleibt der harte Deckel — die Zahlen passen exakt (§3/U2), aber es ist
  eine reale Verhaltensänderung im Paper-Pfad.
- **yF-Intermittenz** (bekannt für `^FCHI`/`^IBEX`, Diagnose 2026-07-02) trifft **2 der 3**
  Ticker im messbaren Pool. Circuit/Retry existieren; das Restrisiko sind Archivlücken, und
  darauf gibt der Tracker jetzt typisiert auf statt zu raten.
- **SQLite-Nebenläufigkeit** (Recorder + Scheduler an `bars.sqlite`): getrennte Dateien,
  kurze Transaktionen, `INSERT OR IGNORE`. Bei beobachtetem `database is locked` ⇒
  `busy_timeout` setzen (im Mutterplan erlaubt, kein Redesign).

---

## §7 Explizit NICHT in P12.5

- **U4** (TickerMapper-Refresh) und **Entscheidung C** (SUN*-Epics vs. `max_active`) — E9.
- **Step 10** (Lightstreamer-Mitschrieb) — gatet auf Step-9-PASS, eigene Design-Session.
- **WI-2/W2-Auswertung** und jede weitere H-Serie — Phase-11-Wiederaufnahme.
- **Funnel-Reason-Split**, `market_context`-Befüllung, B3-Margin-Headroom,
  Council-Paper-Call, UI, Live-Konto — alle im Closeout als *Vorschlag*, keiner als *Arbeit*.
- **Momentum-VETO** bleibt unangetastet (D16): sourct immer direkt aus P1-IG-Echtzeit-Bars,
  nie aus BarService/Archiv/yF.

---

## §8 Bei Ausführung verifizieren (Drift-Liste — NICHT als gesichert behandeln)

> Alles außerhalb dieser Liste wurde am 2026-08-17 gegen `6ecba7b` selbst gegrept und ist Fakt.

1. **Alle Datei:Zeile-Anker** per Grep auf den zitierten **Verbatim-String** gegenprüfen,
   bevor darauf editiert wird. Die Strings sind der Anker, die Zahlen die Abkürzung — Step 2
   und 3 verschieben einander gegenseitig die Zeilen.
2. **Die Test-Zählstände außer P12** (P1 87 · P2 77 · P3 104 · P4 155 · P5 173 · P6 76 ·
   P7 138 · P8 237 · P9 80 · P10 159 · meta 28 · root 80) stammen aus dem Session-5-Block und
   sind **nicht** heute nachgemessen. Nur `phase12_data_foundation = 117` ist heute verifiziert.
3. **`SchedulerConfig.cycle_interval_min`** — Feldname für Step 3b. Der Plan nimmt
   `cycle_interval_min` an (die Phasen-Doku nennt „`cycle_interval_min = 5`"), im Runner
   existiert außerdem ein abgeleitetes `_cycle_interval_s`. Vor dem Edit greppen; ebenso, ob
   `timedelta` in `wiring.py` importiert ist.
4. **Die exakte Flag-Schreibweise** `--enable-shadow-schedule` / `--enable-divergence-sampler`
   gegen die 12 `add_argument`-Blöcke in `phase8_scheduler/scheduler/run.py` — der Handover
   nennt `:105` und `:115`, das wurde **nicht** zeilengenau nachgeprüft. Ein Tippfehler hier
   sieht exakt aus wie „der Fix wirkt nicht".
5. **`data_health.py` weist den Archiv-/Fetch-Split heute nicht aus.** §6/F braucht ihn, um
   eine fehlkalibrierte U3-Schwelle **in** der Woche zu sehen statt am Freitag. Die Daten
   liegen bereits vor (`bar_fetch`-Events im Observability-Log, `source_spend` nach `kind`).
   **Entscheidung der ausführenden Session:** entweder eine Zeile in `data_health.py`
   ergänzen (klein, phasen-intern, kein Gate) oder den Split am Freitag manuell aus dem Log
   ziehen. Empfehlung: **die Zeile ergänzen**, in Step 2.
6. **`abstain_report.py --paper` gruppiert nach `resolution_source`** — Kriterium E verlangt
   das. Die Spalte existiert seit Migration 006, war aber **nie mit echten Daten befüllt**.
   Vor der Freitags-Review einmal gegen echte Zeilen laufen lassen, nicht erst währenddessen.
7. **Aktueller DB-Stand** vor Step 4 frisch lesen, nicht aus diesem Plan übernehmen.
   Stand 2026-08-17: `paper_trades` = 110 `RESOLVED` / 505 `EXPIRED_UNRESOLVED`, letzte Zeile
   `2026-08-07T11:15:26Z`; Registry = 5 `active`/`ok`, 3 `active`/`no_intraday_source`,
   13 `verified`/`unverified`, 1 `quarantined`; Archiv = 1 891 Bars; Spend = 136 Punkte
   (probe 20 / research 110 / sample 6).
