---
status: snapshot
purpose: Supersedes DATA_WEEK_REVIEW_2026-08-07 §3.1/§3.2 root cause. The IG-`/prices` failure was NOT an endpoint outage — it was our own account's historical-data-point allowance, exhausted by the paper tracker at 300 bars per fetch. Documents the live proof, the corrected cause chain, the fix shipped 2026-08-08, and the restart gate (universe reset + H1 re-arm stay blocked until the allowance resets).
read-when: before restarting the scheduler with `enable_paper_trades`, before resetting `instrument_universe`, or when reading DATA_WEEK_REVIEW_2026-08-07 §3 (whose root cause this corrects)
detail: L3
up: ./CLAUDE.md
updated: 2026-08-08
---

# Allowance-Incident — Korrektur zu Datenwoche-Review 3 (2026-08-08, Sa)

> **BLUF:** `DATA_WEEK_REVIEW_2026-08-07.md` §3.1/§3.2 nannte einen **endpoint-spezifischen
> IG-Ausfall** als Ursache. Das ist falsch. Der Live-Check des Nikinger (2026-08-08 06:44 UTC)
> liefert `error.public-api.exceeded-account-historical-data-allowance` — **unser eigenes
> Konto-Kontingent für historische Kursdaten, aufgebraucht durch unseren eigenen Paper-Tracker.**
> IG rechnet `/prices` in **Datenpunkten, nicht in Requests** ab; `_PAPER_BAR_COUNT = 300`
> heißt: **jeder** Tracker-Fetch kostet 300 Punkte.
>
> Das Review war beim *Symptom* richtig (der Endpoint antwortete nicht, `get_market_info`
> schon) und beim *Mechanismus* richtig (die 5-Minuten-Tracker-Kadenz, nicht der
> 30-Minuten-Öffnungs-Intervall). Falsch war die *Ursachenzuschreibung*: keine externe
> Störung, sondern ein Budget, das wir selbst überzogen haben. Alles, was aus „IG ist kaputt,
> wir warten" folgte, gilt nicht mehr.

## 1. Der Beleg

```
$ python -m broker_wrapper.cli --broker ig_demo ohlcv \
      --epic IX.D.DAX.IFMM.IP --resolution MINUTE --count 5
{"ok": false, "ts": "2026-08-08T06:44:05.332Z", "broker": "ig", "method": "get_ohlcv",
 "data": null,
 "error": {"code": "RATE_LIMIT", "retryable": true,
           "message": "403 rate limited: {\"errorCode\":\"error.public-api.exceeded-account-historical-data-allowance\"}"}}
```

`RATE_LIMIT` statt `AUTH_ERROR` ist dabei **korrektes** Verhalten des Adapters — genau die
403-`exceeded-*-allowance`-Sonderbehandlung, die seit dem Vorfall 2026-07-06 inline in
`ig_adapter._request` (`:330-360`) steht. Der Wrapper hat sauber gearbeitet; der Verbrauch
darüber nicht.

## 2. Verbrauchsrechnung (repo-only, keine Netzcalls)

Distinkte `(epic, resolved-Minute)`-Gruppen in `paper_trades` = Untergrenze für
**erfolgreiche** Fetches:

| Tag | erfolgreiche Fetches (≥) | Datenpunkte @300 |
|---|---|---|
| 2026-07-27 | 1 | 300 |
| 2026-08-03 | 32 | 9 600 |
| 2026-08-04 | 33 | 9 900 |
| **Σ** | **66** | **≈19 800** |

Die 218 CRITICAL-Zeilen bereits am Montag (08-03) datieren die Erschöpfung auf **~einen Tag**
H1-Vollbetrieb. Die 4 232 CRITICAL-Zeilen der Woche haben das Kontingent nicht weiter
belastet — ein 403 wird abgewiesen, nicht abgerechnet; sie waren Log-Rauschen, nicht Kosten.

**Die exakte Obergrenze steht hier bewusst nicht.** `totalAllowance` und `allowanceExpiry`
kommen aus dem `allowance`-Objekt, das IG in **jeder erfolgreichen** `/prices`-Antwort
mitschickt (`ig_adapter.py:436-439`) — der Tracker hat es bislang weggeworfen. Ab dem Fix
unten wird es einmal pro Prozess geloggt. Bis dahin gilt: Größenordnung ~20 000 Punkte
verbraucht, echter Deckel unbekannt.

**Nicht der Verursacher:** die Phase-9-Promotion-Probe. `scripts/verify_instrument.py:78-79`
nutzt `MINUTE_5` × **3 Bars** = 3 Punkte je Epic und Runde (~400/Tag bei 22 Epics) — 100×
billiger pro Call als der Tracker. Phase 9 ist **Opfer** der Erschöpfung, nicht Mitverursacher.

## 3. Die korrigierte Ursachenkette

```
_PAPER_BAR_COUNT = 300 Punkte/Fetch  ×  ~33 Fetches/Tag (H1-Volumen, 8+ Epics)
   ↓
Konto-Kontingent für historische Kursdaten binnen ~1 Tag erschöpft  (08-03)
   ↓
jeder weitere get_ohlcv → 403 → Trade bleibt OPEN → Rückstand wächst monoton
   ↓                                    ↓
Tracker: 218→1564 CRITICAL/Tag     check_ig_side sieht `ig_ohlcv_available: false`
                                        ↓
                     18/22 Epics quarantined (inkl. DAX/CAC/IBEX/AEX/STXE-Kern),
                     restliche 4 bei fail_count=2/3
```

Der Kaskadenschaden am `instrument_universe` bleibt exakt wie im Review beschrieben — nur die
Ursache am Kopf der Kette ändert sich. **Die Phase-9-Lücke ist dadurch schwerwiegender als
gedacht:** `check_ig_side` liest einen **kontoweiten Budget-Ausfall** als
**Instrumenten-Untauglichkeit**. Das wiederholt sich bei der nächsten Erschöpfung, auch mit
dem Fix unten. Ausdrücklich **nicht** in dieser Session gefixt (Phase-9-Code, außerhalb des
Phase-10/11-Scopes) — Befund + Entscheidungsvorlage für den Nikinger.

## 4. Der zweite Befund: eine Datenintegritäts-Falle, unabhängig vom Kontingent

Auch bei **gesundem** Endpoint wäre ein Neustart nicht sicher gewesen.

`resolve_paper_trade` (`abstain_lessons/paper.py`) filtert Bars ausschließlich über
`timestamp >= created_utc` und prüft den SL-Treffer **zuerst und bedingungslos**, *vor* dem
`ts >= time_stop_utc`-Ausstieg. Für einen am 08-04 angelegten Trade passiert damit **jede**
Bar eines späteren Fetches den Filter. Der erste Tick nach einem Neustart hätte einen
unbekannten Anteil der **390** liegengebliebenen `OPEN`-Zeilen mit **erfundenem**
`exit_level`/`pnl_points`/`r_multiple` als `RESOLVED` geschrieben — in genau die
`paper_trades`-Tabelle, aus der WI-2/W2 beantwortet werden soll.

Das feuert auch **ohne** `--enable-shadow-schedule`: `_run_paper_tracker` tickt allein an
`enable_paper_trades`.

## 5. Der Fix (2026-08-08, Bot gestoppt, Wochenende)

Zwei Dateien, additiv, keine Gate-/VETO-/Order-Pfade berührt.

**`phase10_v3/abstain_lessons/paper.py` — `PaperTradeTracker`:**

| Neu | Wirkung |
|---|---|
| `stale_after_minutes` | Ein Trade älter als der Schnitt wird **ohne Fetch** auf `EXPIRED_UNRESOLVED` gesetzt. Zuerst Korrektheits-, dann Budgetschutz (§4). |
| `budget_ok` | **Einmal** pro Tick geprüft, vor jedem Fetch → ein erschöpftes Budget kostet null Calls für den ganzen Tick, nicht einen pro Epic. Gleiche Callable-Form wie das bestehende `reflect_cap_check` — bewusst, nicht zufällig. |

Der Schnitt ist **Wanduhr**, nicht `bar_count × bar_minutes`: IG liefert die letzten N
*existierenden* Bars, die über die Übernachtlücke zurückreichen. Wert:
`exec_cfg.max_hold_minutes + 60`, aus der **gleichen** Config wie die Trade-Geometrie
gezogen — eine zweite hartcodierte Kopie dieser Zahl ist genau die Drift-Klasse, die Befund
B1 verursacht hat.

**`phase8_scheduler/scripts/wiring.py` — `_build_paper_tracker`:**
- `bar_fetch` trippt bei `RATE_LIMIT` einen Cooldown (`_PAPER_BUDGET_COOLDOWN_MIN = 60`) und
  zusätzlich unterhalb eines Reserve-Floors (`_PAPER_ALLOWANCE_FLOOR = 2000`, **Platzhalter
  bis ein `totalAllowance` beobachtet ist** — der Floor existiert, damit die Phase-9-Probe
  weiterläuft und die Kaskade aus §3 nicht erneut zündet).
- `env.error` wird nicht mehr verschluckt. Vorher trugen 4 232 CRITICAL-Zeilen den echten
  IG-Fehlercode **nirgends**; die gesamte Diagnose lief über
  `instrument_universe.checks_json`.
- `allowance` wird einmal pro Prozess auf INFO geloggt (`totalAllowance` = Deckel,
  `allowanceExpiry` = Reset-Zeitpunkt).

**Zur Abnahme-Eigenschaft, ohne Schönfärberei:** die letzte Session forderte „ein
wiederholter `get_ohlcv`-Fehler muss künftiges Call-Volumen **senken**". `stale_after_minutes`
allein **begrenzt** nur (aus monotonem Wachstum wird ein Plateau); erst `budget_ok` **senkt**
tatsächlich, auf null während des Cooldowns. Zusammen ist die Eigenschaft erfüllt.

**Verifiziert:** `pytest phase10_v3/tests` **141 passed** (138 + 3 neue: stale-expiry ohne
Fetch, frischer Trade weiterhin auflösbar, Budget-Stand-down überspringt den ganzen Tick).
`pytest phase8_scheduler/tests` **229 passed**. `wiring.py` per `py_compile` (kein
pytest-Testfile, dokumentierte „operator-run"-Konvention).

**Gegen die reale DB gerechnet** (read-only), Stichtag Mo 2026-08-10 07:05 UTC:

| | |
|---|---|
| `OPEN`-Zeilen | 390 |
| davon fällig | 390 |
| Stale-Schnitt | 2026-08-10T02:05:00.000Z |
| → expired, **0 Fetches** | **390** |
| → würden gefetcht | **0** |

Der gesamte Rückstand entlädt sich beim ersten Tick ohne einen einzigen API-Call.

## 6. Restart-Gate (Nikinger)

**Nicht in dieser Session erledigt, bewusst:** Universe-Reset und H1-Scharfschaltung.
Beide hängen an einem **beobachteten** `remainingAllowance`, nicht an einem Datum. Ein Reset
der 18 Epics auf `fail_count=0` gegen ein noch erschöpftes Kontingent quarantäniert alle 22
binnen drei Verify-Runden erneut — er wäre nicht nur wirkungslos, sondern schädlich.

1. Denselben Einzeiler **einmal täglich** laufen lassen, bis `"ok": true` kommt:
   ```bash
   phase1_broker_wrapper/.venv/bin/python -m broker_wrapper.cli \
     --broker ig_demo ohlcv --epic IX.D.DAX.IFMM.IP --resolution MINUTE --count 5
   ```
2. Dann das `allowance`-Objekt aus der Antwort hierher zurückspielen — `totalAllowance`
   dimensioniert das Budget, `allowanceExpiry` datiert den Reset.
3. **Erst dann** Universe-Reset (Präzedenzfall 2026-07-06, `phase9_universe/CLAUDE.md`) und
   H1-Scharfschaltung.

## 7. Offene Punkte

- **H1s Volumen ist auch nach dem Fix nicht budgetiert.** Der Fix verhindert die *Eskalation*
  und die *Datenkorruption*; er senkt den Grundverbrauch von ~33 Fetches × 300 Punkten pro Tag
  nicht. Vor einer echten Messwoche braucht es einen der beiden Hebel:
  (a) billigere Bars (`MINUTE_5` × 60 = ⅕ der Kosten) oder (b) weniger Volumen (weniger Epics
  oder weniger Paare/Tag). **(a) ist ungetestet und wird nicht blind geschaltet** —
  `resolve_paper_trade` löst einen Same-Bar-SL+TP-Treffer bedingungslos zu **SL** auf; bei
  30-Pkt-SL/45-Pkt-TP genügt eine Bar mit ~75 Punkten Spanne. Auf 1-Min-Bars selten, auf
  5-Min-DAX-Bars nicht selten. Gröbere Bars könnten also Budget kaufen, indem sie den
  SL-Anteil systematisch aufblähen — genau die Zahl, die in Review §2 schon einmal falsch
  gelesen wurde.
- **Der Offline-Test dazu ist nicht möglich.** Die Roh-Bars werden nirgends persistiert:
  `paper_trades` speichert nur Auflösungen, `data/cache/` enthält ausschließlich
  yFinance-**Tages**bars, und alle 1 082 `market_regime_snapshots` sind `quote_only` mit
  `degraded=1` und `atr_points IS NULL`. Stattdessen als **budgetierter Live-Test** nach dem
  Reset: ein `get_ohlcv(MINUTE, 300)` und ein `get_ohlcv(MINUTE_5, 60)` auf demselben Epic im
  selben Fenster, Auflösungen vergleichen — Gesamtkosten 360 Punkte, einmalig.
- **Phase-9 `check_ig_side`** (§3, Ende) — Designbefund, außerhalb des Scopes, wartet auf eine
  Nikinger-Entscheidung.
- **Mess-Substrat für WI-2 — gesichert, solange es billig war:** die 390 Zeilen, die beim
  nächsten Tick auf `EXPIRED_UNRESOLVED` kippen, wären danach nicht mehr von echten
  Geometrie-Expiries zu unterscheiden (ein reiner Datumsfilter fängt auch legitime mit ein).
  Ihre `paper_id`s sind deshalb **vor** dem ersten Tick gesichert:
  [`OUTAGE_EXPIRED_PAPER_IDS_2026-08-08.json`](./OUTAGE_EXPIRED_PAPER_IDS_2026-08-08.json)
  (390 IDs, 22 Epics, read-only erzeugt). **Kein** Schema-Zusatz, keine Migration — eine
  datierte Datei genügt, und der Zeitpunkt, sie kostenlos zu erzeugen, war jetzt.
  Die 115 bereits durch denselben Vorfall expirierten Zeilen aus 08-04 sind **nicht** darin
  enthalten — für die bleibt nur die Datumsabgrenzung.

- **Der Floor `_PAPER_ALLOWANCE_FLOOR = 2000` ist ein Ausfallrisiko, nicht nur eine
  Ungenauigkeit:** liegt das echte `totalAllowance` bei oder unter 2000, ist `budget_ok()`
  praktisch dauerhaft `False` und der Tracker löst **gar nichts** mehr auf — das einzige
  Signal wäre eine CRITICAL-Zeile im Log. Nach dem ersten erfolgreichen Fetch das geloggte
  `allowance`-Objekt prüfen und den Wert ggf. senken. Als Warnung auch inline im Code
  vermerkt.
- **B5-Restfehlerrate** (10/68 Reflect-Versuche über der 300-Zeichen-Grenze) unverändert
  offen, s. Review §4.
