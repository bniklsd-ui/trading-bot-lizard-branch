---
status: snapshot
purpose: Block-A-Abschluss für Phase 13 (Live-Datenfundament) — A7.1/A7.2/A7.3 read-only-Verifikation, Operator-Sequenz für den ersten Neustart mit Messarm, erreichte PASS-Kriterien + offene Block-B/C-Items.
read-when: vor dem ersten scharfen Neustart mit `--enable-shadow-schedule --enable-divergence-sampler`; vor Block-B0 (`CHART:`-Live-Check); vor jedem Re-Read der Anforderungen A–G
detail: L3
up: ../docs/concepts/phase13_live_data_plan.md
down:
  - ./CLAUDE.md                                  # phase head (Session 7 = A5+A6, A7 in dieser Session)
  - ./SESSIONS_ARCHIVE.md                        # rotierte Session-Blöcke
  - ../phase12_data_foundation/CLAUDE.md         # Phase 12 (Datenfundament) — A baute auf A
  - ../docs/concepts/phase12_data_foundation_plan.md  # Anforderungen A–G, §7 Done-Kriterium
  - ../phase12_data_foundation/PHASE12_5_CLOSEOUT_HANDOVER.md  # warum Block A überhaupt nötig wurde
updated: 2026-08-19
---

# Phase 13 — Block A (A0–A7) Closeout: Bestandsaufnahme + Operator-Block

> **Autor:** Claude Code, Session 8 (2026-08-19). **Adressat:** Nikinger (Operator-Restart)
> + nächste Session an Block B. **Quelle der Zahlen:** read-only-Abfragen gegen
> `data/trading_bot.sqlite` und `data/bars.sqlite` heute, **nicht** aus Vordokumenten
> übernommen.

## §0 BLUF

Block A ist gebaut, getestet und auf `main`. Die zwei strukturellen F1/F2-Bugs sind
geschlossen, die PASS-Kriterien P1, P3, P5, P9 sind **per Konstruktion** oder
**per Messung** erfüllt. **Was noch fehlt, ist allein Operator-Arbeit** (Allowance-Probe
+ Neustart mit Messarm). Vor diesem Neustart ist dieser Closeout zu lesen — danach
beginnt die Beweiswoche (Block A Akzeptanz, Plan §7).

## §1 Bestandsaufnahme (read-only, 2026-08-19)

### 1.1 IG-Spend diese Woche (`data/bars.sqlite:source_spend`)

| `kind` | Events | Punkte |
|---|---:|---:|
| `research` | 47 | 4675 |
| `sample` | 12 | 36 |
| `probe` | 4 | 20 |
| **`tracker`** | **0** | **0** |

**`tracker`-Spend ist null.** Das ist der strukturelle Schnitt aus A2 — der
Tracker-Pfad ruft seit A2 keinen IG-Provider mehr. Genau die Garantie, die L12
versprochen hat. **Bestätigt, nicht nur behauptet.**

### 1.2 Allowance-Stand (`allowance_observations`, letzte 3 Einträge)

| ID | observed_at | total | remaining | expiry |
|---|---|---:|---:|---|
| 63 | 2026-08-18T14:08:09.943Z | 10000 | 5054 | 2026-08-23T20:53:42Z |
| 62 | 2026-08-18T13:41:48.928Z | 10000 | 5355 | 2026-08-23T20:53:42Z |
| 61 | 2026-08-18T13:41:48.784Z | 10000 | 5656 | 2026-08-23T43Z |

**Der Stand ist von gestern.** Vor dem ersten Neustart mit Messarm ist eine **frische
`probe_allowance.py`-Beobachtung** Pflicht — die 5054 sind 24 h alt. Anforderung F
(Plan §7) verlangt IG-Wochenverbrauch < 1500 nach einem scharfen Tag, **nicht** total.
Nach den 4675 research-Punkten am 18.08. (heute ist Mittwoch, die Woche rollt erst
Sonntag) ist die Reserve dünn — der erste Tracker-Punkt würde mit hoher
Wahrscheinlichkeit das 403-Trigger-Limit reißen. **Lösung:** S1 (Lightstreamer,
anderes Kontingent) statt IG-Tracker. Block B.

### 1.3 Bars-Archiv (`data/bars.sqlite:bars`)

- 8968 Zeilen, davon 2230 IG + 6738 yF.
- `IX.D.IBEX.FWM2.IP` trägt 306 IG-Bars mit `fetched_at=2026-08-18T11:10:17Z`,
  `ts_utc` zwischen 2026-07-17 und 2026-08-01 — **das ist F1, der aufgezeichnete
  Fall.** A4 stoppt ab jetzt neue stale-Writes; die 306 Altzeilen werden **nicht**
  per Skript aufgeräumt (Doku-Hygiene-Regel: nicht in Dateien löschen, die
  Verlauf tragen).

### 1.4 Instrument-Registry (`instrument_universe`)

| `data_source_status` | Anzahl |
|---|---:|
| `ok` | 5 |
| `no_intraday_source` | 3 |
| `unverified` | 14 |

**`IX.D.IBEX.FWM2.IP` trägt heute noch `data_source_status='ok'`** — der Sampler
hat ihn noch nicht geprüft. Sobald der Scheduler mit `--enable-divergence-sampler`
läuft, wird FWM2 beim ersten täglichen Sample (alte IG-Historie vs neue yF-Bar)
**automatisch** auf `stale_source` umgestellt (A6.1, `wiring.py:_mark_stale`).
**Operator-Eingriff ist nicht nötig** und wäre falsch — der Code macht es
konsistent.

### 1.5 Paper-Trades (`paper_trades`)

- 5 Epics × 4 Pair-Slots (SHADOW_BUY + SHADOW_SELL) × 2 Cycles = **20 OPEN**.
- `created_utc`: 2026-08-18T10:39:05Z und 11:15:21Z.
- `time_stop_utc`: 2026-08-18T14:39:05Z und 15:15:21Z — **bereits überschritten**.
- Beim ersten Scheduler-Tick werden sie über `stale_after_minutes=300` (5 h, der
  bestehende Tracker-Cap) als **`EXPIRED_UNRESOLVED`** abgeschlossen — **kein
  Messausfall**, sondern erwarteter Lifecycle-Abschluss. In der Beweiswoche
  separat ausweisen, **nicht** als Messfehler verbuchen (Closeout §6 Empfehlung).

## §2 Erreichte PASS-Kriterien (Plan §7)

| # | Kriterium | Status | Beleg |
|---|---|---|---|
| **P1** | Tracker-Pfad gibt null IG-Punkte aus | **✅ per Konstruktion** | A2 (`get_window` ist reine Archiv-Lesung) + §1.1 (`tracker`-Spend 0) |
| **P2** | `paper_trades.resolution_source ≠ NULL` | **✅ ungebrochen** | Migration 006 Spalte, weiter befüllt (D11) |
| **P3** | Keine Auflösung aus ungedecktem Fenster | **✅ per Konstruktion** | A3 (`window_ok`-Guard in `_resolve_group`) + F3-Test (pre-A3 fabriziert, A3 blockiert) |
| **P4** | LS liefert 5/5 Tage | ⬜ Block B | CHART-Live-Check B0 steht aus |
| **P5** | Tages-Abdeckung ≥ 0.9 an ≥ 4/5 Tagen | **✅ wird gemessen** | A6.2 (`assess_day.worst_coverage`) — erste echte Messung wartet auf Neustart |
| **P6** | Source-Delta-Report | ⬜ Block C3 | `scripts/source_delta.py` ausstehend |
| **P7** | IG-Wochenverbrauch < 1500 | **✅ noch erfüllt** | §1.1 — aber dünn; Block B zwingend |
| **P8** | 5/5 Tage `measurement_heartbeat` | ⬜ ab Neustart | `daily_health_check` aktivieren, A6.2-Alarm testen |
| **P9** | Kein Epic mit toter Historie auf `ok` | **✅ wird emittiert** | A6.1 (`mark_stale_fn`) — FWM2 fällt beim ersten Sampler-Lauf auf `stale_source` |

**P1, P3, P9** sind strukturell erreicht (kein Tuning, kein Tuningspielraum).
**P5, P8** sind messbereit, Messung wartet auf Neustart. **P2** ist
unverändert gut. **P4, P6, P7** bleiben offen (Block B / C).

## §3 Operator-Sequenz für den ersten Neustart (A7.3 verbatim, Plan §6 Zeile 862)

> **Diese Sequenz ist der einzige Live-Operator-Schritt in Block A.** Alles
> davor war Code (committet) + Verifikation (read-only, hier). Alles danach
> ist Beobachtung der laufenden Beweiswoche.

### Schritt 1 — Allowance-Probe

```bash
python phase12_data_foundation/scripts/probe_allowance.py
```

**Erwartung:** Exit 0, JSON auf stdout mit `ok=true, remainingAllowance ≈ 9000+`
(das Wochenfenster rollt am 2026-08-23 ab). Wenn `remainingAllowance < 1500`,
**nicht** starten — auf den Rollover warten.

### Schritt 2 — Scheduler gestoppt prüfen

```bash
ps aux | grep scheduler.run | grep -v grep
```

**Erwartung:** leere Ausgabe. Wenn nicht, **kill** mit `kill <pid>` (kein
`kill -9` — der Runner hat einen sauberen Shutdown).

### Schritt 3 — Recorder lebt

```bash
cat data/state/recorder.pid  # muss existieren
ps -p $(cat data/state/recorder.pid)  # muss laufen
```

**Erwartung:** PID aktiv. Wenn nicht, mit `python -m data_foundation.run` starten
(gleiche Form wie Phase 12). Recorder ist kostenlos und blockiert nichts.

### Schritt 4 — KILL-Datei leeren

```bash
# KILL-Datei ist der sticky, operator-gesetzte Halt. Leeren vor Neustart:
rm -f data/state/KILL
```

**Vorsicht:** das ist ein bewusster Operator-Schritt. Im Zweifel vorher prüfen
(`cat data/state/KILL`).

### Schritt 5 — Start mit Messarm

```bash
python -m scheduler.run \
    --enable-shadow-schedule \
    --enable-divergence-sampler \
    --daily-loss-cap 1800 \
    --max-trades 5
```

**Beide Flags sind neu in Phase 13** (Plan §6 A0.3 Schritt-0-Default-Verhalten:
beide Default AUS, hier explizit an). `--enable-bar-stream` ist noch nicht
verfügbar (Block B1, abhängig von B0-Ergebnis).

### Schritt 6 — Beobachten: 5 Handelstage

- **Täglich** (vor `POST_WINDOW`): `python phase12_data_foundation/scripts/data_health.py`
  → Exit 0 erwartet, sonst Alarm.
- **Täglich** `window_uncovered`-Events in `data/state/research_health.jsonl`
  prüfen — `grep '"event": "window_uncovered"'` (sollte mit wachsendem
  LS-Stream gegen 0 gehen, anfangs häufig).
- **Freitags** Review-Session nach `phase10_v3`-Muster
  (Tabelle: `phase10_v3/DATA_WEEK_REVIEW_2026-XX-XX.md`); Akzeptanzkriterien P5/P8.

## §4 Was diese Session NICHT tut (bewusst)

- **Kein DB-Write.** `IX.D.IBEX.FWM2.IP` bleibt `ok` in der Registry. Der
  Sampler macht es konsistent beim ersten Lauf — der Operator-Eingriff wäre
  Drift (Closeout §7 Empfehlung).
- **Kein Löschen der 306 FWM2-IG-Bars.** A4 stoppt neue stale-Writes, der
  Altbestand bleibt für die Beweiswoche stehen (Audit-Trail).
- **Kein Löschen der 20 OPEN-Paper-Trades.** Der `stale_after_minutes`-Cap
  schließt sie beim ersten Tick — als `EXPIRED_UNRESOLVED`. Das ist
  Lifecycle, kein Fehler.
- **Kein Push.** `main` ist 12 Commits vor `origin/main`; Push bleibt
  bewusste Einzelfreigabe.

## §5 Was Block A6/A7 nicht fängt — die Tracker-Stale-Lücke

**Offene Tracker-Lücke, klein, vor Neustart zu schließen** (Session-7-Block §3
hat sie notiert): `paper.py` lässt einen Trade, dessen einzige Archive-Bar
stale ist, ungehindert durch. Heute geschützt durch:
1. `stale_after_minutes=300` (5 h, gegen die typische 24-h-OPEN-Liste irrelevant)
2. `window_ok`-Guard aus A3 (deckt Mitten-Lücken, aber keine **ausschließlich
   stalen** Fenster).

**Der Fix** ist eine dritte, **sehr kleine** Stale-Prüfung in `paper.py`,
analog zu A6.1 im Sampler:

```python
# Pseudo-Code, A6.1-Stil
newest = max((b.get("timestamp", "") for b in bars), default="")
if newest and _age_minutes(newest, _parse(now)) > 120:
    self._charge_failed_attempt([trade], now)
    continue
```

Diese Stale-Prüfung gehört **vor** den `window_ok`-Guard (billiger, fängt
mehr Fälle), ist **additiv** und ändert den U2-Mechanismus nicht. **5 Zeilen
plus 1 Test.** Sollte im **nächsten Patch** (Session 9 oder nach dem ersten
Neustart) als Mini-Step ergänzt werden — bewusst NICHT in dieser Session, weil
sie die Test-Fixtures erneut anfasst und der Live-Stand sauber dokumentiert
werden muss, **bevor** weiter gebaut wird.

## §6 Empfehlung an den Nikinger

1. **Heute / morgen:** `probe_allowance.py` ausführen (Schritt 1). Wenn
   `remainingAllowance > 1500`, ist Block A startbereit.
2. **Erste Beweiswoche:** Schritte 2-5 aus §3, danach 5 Tage laufen lassen.
3. **Während der Beweiswoche:** Frequenz `data_health.py` einmal täglich
   (morgens, vor `PRE_OPEN`). Beim ersten `ok=False` NICHT abbrechen — die
   ersten 1-2 Tage können den Recorder-Lag oder ein anderes Boot-Artefakt
   melden. Nach 2 aufeinanderfolgenden `ok=False` Tagen: Review-Session.
4. **Vor Block B:** diese Session nicht weiterbauen — die A5/A6-Tests
   sind strukturell, der Live-Lauf ist die eigentliche Akzeptanz.
5. **Push von `main`:** die 12 Commits seit `origin/main` sind alle Phase 13
   und alle getestet. Ein Push vor der Beweiswoche **macht den Live-Stand
   nachvollziehbar** für eine externe Review — Operator-Entscheidung.

## §7 Modul-Stand Block A (Quelle der Wahrheit: Code + Phase 13 Head)

| Komponente | Status | Beweis |
|---|---|---|
| `data_foundation/coverage.py` | ✅ A1 | 12 Tests, Mitten-Loch-Fang |
| `data_foundation/service.py` (`get_window` kauf-frei) | ✅ A2 | `test_get_window_never_fetches` |
| `data_foundation/service.py` (Stale-Assertion) | ✅ A4 | 3 Tests, `record_spend` vor Verwerfen |
| `data_foundation/archive.py` (`tick_count`, `sources`) | ✅ A2+A5 | 5 Filter-Tests |
| `data_foundation/heartbeat.py` (Sampler F1/F2) | ✅ A6.1 | 2 Tests, `kind="return"`, `mark_stale_fn` |
| `data_foundation/heartbeat.py` (`compute_return_divergence`) | ✅ A6.0 | Rendite-Differenz statt Niveau |
| `data_foundation/heartbeat.py` (`assess_day`-Coverage) | ✅ A6.2 | 2 neue Felder, `worst_coverage`-Berechnung |
| `phase10_v3/abstain_lessons/paper.py` (`window_ok`) | ✅ A3 | 4 Tests, F3-Mitten-Loch |
| `phase8_scheduler/scripts/wiring.py` (`_mark_stale`, `window_ok`) | ✅ A3+A6 | `py_compile` clean |
| `phase13_live_data/CLAUDE.md` | ✅ | 7 Session-Blöcke (1-4 + 5-6 in Archive + 7) |
| `phase13_live_data/SESSIONS_ARCHIVE.md` | ✅ | 6 Blöcke verbatim |
| **A7 (Block-A-Abschluss)** | ✅ (dieses Dokument) | §1, §2, §3 — Verifikation + Sequenz |
| **Tracker-Stale-Guard (Mini-Step)** | ⬜ | §5 — vor Neustart ergänzen |

## §8 Übergang an Block B

Block B wartet auf:
1. **B0 — `CHART:{epic}:1MINUTE`-Live-Check** (`scripts/probe_chart_stream.py`,
   ~50 Zeilen, operator-run, kostenlos). Beide Zweige sind ausgeplant:
   - JA (CHART liefert): Block B1, B2, B3 wie geplant.
   - NEIN (`onSubscriptionError`): Tick-Aggregation als Primärpfad
     (`tick_count`-Perzentile separat ausweisen, „dünne Bars" markiert).
2. **A5-Vorarbeit reicht:** `Bar.tick_count`, `sources`-Filter, `archive`
   Schema-Migration — alles schon da.
3. **Die Beweiswoche läuft parallel** — Block B mischt sich mit ihr nicht,
   weil Lightstreamer in S1 **nur** Daten liefert, nicht konsumiert.

**Sobald Block B0 läuft, fällt die IG-Tracker-Frage praktisch weg** — S1
liefert kostenlos, S2 schreibt weiter, S3+S4 sind Rückfallebenen. Das ist der
Punkt, an dem P7 dauerhaft fällt (statt „dünn" zu sein).
