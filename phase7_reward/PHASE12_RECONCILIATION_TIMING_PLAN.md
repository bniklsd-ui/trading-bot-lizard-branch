---
status: snapshot
purpose: Mini-Plan für die laufenden `reward.recorder: no usable history row`-CRITICALs.
Hintergrund: der `RewardSink.reconcile_open_trades()`-Retry-Pfad
(`phase8_scheduler/scheduler/reconcile.py` läuft alle 5 Min im Scheduler-Cycle)
hämmert `get_trade_history` für dieselben Deals ohne Backoff. Bei IG-Settlement-
Lag entstehen so **mehrere Dutzend CRITICAL-Logs pro Tag für denselben deal_id**,
obwohl die Auflösung am Ende immer glückt (Trade wechselt OPEN → CLOSED).
Fix = exponential-Backoff (Konstante pro deal_id, in `trade_outcomes`) +
strukturelle Trennung „first-time fail" vs. „persistent fail" (>24 h).
read-when: jede Session, die das Timing-Thema anfasst; jede Plan-Session, die den
Phase-7/Phase-8-Reconcile-Pfad erweitert; jede P15-V4-Plan-Session, die Reward-Loop
betrachtet.
detail: L3
up: ../CLAUDE.md
down:
  - ./CLAUDE.md                                                    # Phasenkopf, mit Plan-Verweis in Spezial-Pläne-Zeile
  - ../../phase13_live_data/PHASE13_BEWEISWOCHE_FINDINGS_2026-08-31.md # Vor-Findings (Phase-13-Beweiswoche-Auswertung 2026-08-31)
  - ../../phase7_reward/CLAUDE.md                                   # Phase-7-Phasenkopf, dessen pnl_resolver die Wurzel-Logik hat
  - ../../phase7_reward/reward/recorder.py                          # der reward.recorder-Logger-Prefix, Z. 276 (CRITICAL-Wurzel)
  - ../../phase7_reward/reward/pnl_resolver.py                       # der PnLUnavailable-Raiser, Z. 212 (no usable history row)
  - ../../phase8_scheduler/scheduler/reconcile.py                     # der alle-5-Min-Reconcile-Pass, Z. 137 (reconcile_open_trades-Aufruf)
  - ../../phase2_persistence/persistence/migrations.py                # für die geplante trade_outcomes-Erweiterung
  - ../../phase2_persistence/migrations/003_phase12_reconcile_backoff.sql # 📕 NEU — die Backoff-Spalte (D2)
updated: 2026-08-31
---
# PHASE12_RECONCILIATION_TIMING_PLAN — Backoff für `RewardSink.reconcile_open_trades`

> **Drin:** (1) `trade_outcomes.last_resolve_attempt_utc` Spalte + Migration 003;
> (2) exponential-Backoff (15 min → 30 min → 1 h → 4 h → 24 h cap) in `RewardSink._on_trade_closed`
> (in-cycle) und `reconcile_open_trades` (cold-retry); (3) „persistent-fail"-Alarm (>24 h ohne
> Auflösung) als WARNING-Lift (heute silent → morgen operator-flagged); (4) Tests.
>
> **Nicht drin:** Schema-Änderung an `reward_pts`/`trade_lessons`, Logic für was beim
> „persistent-fail" passiert (Trade bleibt OPEN, Score fehlt — bewusst nicht auto-close),
> Phase-15-Planung (das hier ist die Vorbereitung; P15-V4 entscheidet, ob persistent-fail
> ein VETO-Ersatz bekommt).
>
> **Adressat:** die ausführende Claude-Code-Session (Sonnet 5). Alles unten ist
> gegen den Repo-Stand `fdca387` am **2026-08-31 ~07:50 UTC** selbst nachgemessen.
> Was nicht verifiziert werden konnte, steht in **§8** — alles andere ist Fakt und muss
> nicht neu hergeleitet werden.

---

## §0 BLUF

| # | Befund | Konsequenz |
|---|---|---|
| **B1** | **17 CRITICAL-Logs für 4 verschiedene deal_ids in 3 Tagen** (2026-08-25/26/27), alle endeten mit erfolgreicher Auflösung (Trade OPEN → CLOSED). Last-Log 2026-08-27 11:34 UTC (= ~4 Tage her, seitdem Ruhe). | **CRITICAL ist Spam, kein Datenverlust.** Die Reconciliation funktioniert strukturell — sie löst jeden Trade auf, aber spamt dabei 3-7 CRITICALs pro Deal. |
| **B2** | `reconcile_open_trades` läuft im Scheduler-Cycle (alle 5 Min, `phase8_scheduler/scheduler/reconcile.py:137`) und ruft für jeden OPEN-Trade `pnl_resolver.resolve()` → `get_trade_history` (Branch 3). **Kein Backoff, kein „tried recently"-Skip.** | Bei IG-Settlement-Lag (typisch 30 min bis 2 h, demos nachweislich bis 24 h) wird dieselbe `get_trade_history`-Abfrage alle 5 Min wiederholt. |
| **B3** | `pnl_resolver.py:212` (`PnLUnavailable`) hat **denselben Wortlaut** für zwei strukturell verschiedene Fälle: (a) „Trade ist noch nicht gesettelt" (normal, retry hilft) und (b) „Trade wird nie gesettelt" (z. B. ein Deal, der der bei IG aus dem History-Fenster fällt oder ein Phantom-Trade ist). Heute werden beide gleich behandelt (Retry). | Operator sieht nicht, welche OPEN-Trades „normaler Lag" sind und welche „echt kaputt". **Kein operator-flagged alarm** bei persistent fail. |

**Daraus folgt:**

1. **Backoff einführen** — eine `last_resolve_attempt_utc`-Spalte pro Trade, exponential-Backoff
   (15 min → 30 min → 1 h → 4 h → 24 h cap). Reduziert 17 CRITICALs auf 4-5 (einer pro Backoff-Stufe).
2. **„persistent fail"-Detection** — wenn `last_resolve_attempt_utc - open_ts > 24 h`, dann WARNING
   statt CRITICAL (heute silent → morgen operator-flagged via WebUI-Endpoint / manuelles Log-Scan).
3. **Idempotenz** — der Backoff ändert nichts am Retry-Erfolg; trades, die IG nach 5 h postet, werden
   weiterhin beim ersten Backoff-Slot nach Settlement erkannt und aufgelöst.

**Phase-12-Label-Hinweis:** der historische Label „Phase-12-Reconciliation-Timing-Fix" wurde in
mehreren Session-Blöcken verwendet, obwohl die Wurzel-Logik in `phase7_reward/reward/recorder.py`
und `phase8_scheduler/scheduler/reconcile.py` lebt (nicht Phase 12). Der Name bleibt für
Konsistenz mit den offenen-Items-Listen in den Phasenköpfen; der **Code** ist Phase-7/Phase-8
(`reward_sink` ist Phase-7-Eigentum, der Reconcile-Pass ist Phase-8-Eigentum, beide brauchen
Cross-Phase-Freigabe).

---

## §1 Rahmen + Arbeitsteilung

| Regel | Stand |
|---|---|
| **Arbeitszeit** | Werktags, **ohne** Bot-Stop nötig. `RewardSink._on_trade_closed` und `reconcile_open_trades` laufen im Scheduler (PID 10358, alive), aber das Hot-Patch-Risiko ist überschaubar: ein Code-Bug hier crasht den Scheduler nicht (beide Pfade sind `try/except`-geguarded mit `logger.critical`, Decision J). Der Bot **muss** trotzdem nach dem Edit per `restart-services.sh restart scheduler` neu gestartet werden (Python `sys.modules`-Cache, siehe P14-D §10-Korrekturnotiz). |
| **Bot vor dem Edit** | **Restart-Hygiene zwingend** (`restart-services.sh restart scheduler`, ~5 s Downtime). Kein Doppel-Login-Risiko, da `kill -TERM → SIGTERM-grace → exit 0` gewohnt (POST_WINDOW-Sleep-Cap-Fix, P14-D/P14-E-Pattern). |
| **Live / Netz / Kosten** | **Nichts.** Tests sind `mode=ro`-Tests mit gemocktem Broker; die Migration ist lokal (kein IG-Call); die Backoff-Logik nutzt `db.update_open_trade_attempt(...)` — eine lokale Schreib-Operation auf der SQLite-DB. |
| **Live-DB** | Wird vom Code geschrieben (Update der neuen `last_resolve_attempt_utc`-Spalte). **Vor** dem ersten Code-Commit: frisches DB-Backup (`cp data/trading_bot.sqlite data/state/diagnostics/trading_bot.sqlite.pre-phase12-timing-fix`). |
| **Cross-Phase-Edits** | Phase 7 + Phase 8 (Eigentümer des Reward-Loop + Reconcile-Pass) + Phase 2 (Migration 003). **Cross-Phase-Freigabe-Liste aus Phase 14 (Phase 2/8/9/12/13) deckt Phase 2 + Phase 8 ab — Phase 7 fehlt in der Liste** → Phase-7-Touch braucht eine Mini-Plan-Sign-off (Nikinger-Freigabe via diesem Plan). Phase-12 ist hier **nicht** berührt (Recorder-Code ist in Phase 12, aber unverändert). |
| **Push** | Nikinger-Freigabe nach allen Akzeptanzpunkten + Operator-Restart verifiziert. |

**Prozess-Ist-Stand bei Planschluss (2026-08-31 ~07:50 UTC, selbst erhoben):**

| Datei | Status |
|---|---|
| `phase7_reward/reward/recorder.py` | tracked, 408 Zeilen, `_on_trade_closed` Z. 245-280 (CRITICAL-Raiser) |
| `phase7_reward/reward/pnl_resolver.py` | tracked, 234 Zeilen, `PnLUnavailable` Z. 212 |
| `phase8_scheduler/scheduler/reconcile.py` | tracked, 154 Zeilen, Z. 137 ruft `reconcile_open_trades()` |
| `phase2_persistence/persistence/db.py` | tracked, `_TRADE_COLUMNS` als Whitelist für `INSERT` |
| `phase2_persistence/migrations/` | tracked, Schema-Runner scannt NUR diesen Ordner (Phase-7-CLAUDE §1.7) |
| `trade_outcomes` heute | 8 CLOSED, 0 OPEN, 8 reward_pts, 8 trade_lessons (alle resolved) |
| `data/state/scheduler.log` | 17 CRITICALs „no usable history row", letzte 2026-08-27 11:34 UTC |

---

#### §2 Gelockte Entscheidungen (D1–D5)

Diese Tabelle ist der Ersatz für Nachdenken. **Nicht neu herleiten, nicht „verbessern".**
Widerspricht der Code einer Zeile ⇒ Advisor / Nikinger, nicht stillschweigend abweichen.

| # | Entscheidung | Begründung |
|---|---|---|
| **D1** | **Backoff-Granularität**: exponential mit Stufen 15 min → 30 min → 1 h → 4 h → 24 h cap. Auswahl basiert auf IG-Settlement-Beobachtungen (Demos: 30 min typisch, bis 24 h worst-case; Contract 1.2-Footnote). | 15 min deckt den Normalfall (IG bucht ≤ 30 min nach Close). 30 min → 1 h → 4 h escalieren langsam. 24 h cap verhindert, dass sehr alte OPEN-Trades für immer im 5-min-Cycle hängen. |
| **D2** | **Neue Spalte** `trade_outcomes.last_resolve_attempt_utc TEXT` (ISO-8601, tz-aware UTC) als nullable; Migration 003 (`003_phase12_reconcile_backoff.sql`). **Idempotent**: `UPDATE` schreibt nur, wenn Retry tatsächlich stattgefunden hat (= `pnl_resolver.resolve()` gerufen wurde). | Eine einzige Spalte genügt — sie ist die Quelle für „wann habe ich das letzte Mal versucht?"; die nächste Retry-Wartezeit wird beim Versuch berechnet. Kein Backoff-State-Tabelle nötig. |
| **D3** | **Backoff-Skip-Logik** lebt in `RewardSink.reconcile_open_trades` (Phase-7-Code), nicht im Scheduler. Begründung: der `reconcile_open_trades` ist der einzige Aufrufer, der den OPEN-Status sieht; der Scheduler entscheidet nur „läuft Reconcile?" — die Backoff-Frage ist eine Reward-Sink-Eigenschaft. | Klare Ownership (Phase-7 = Reward-Loop), keine zusätzliche Coupling zwischen Scheduler und Reward-Sink. Phase-8-Tests bleiben unverändert. |
| **D4** | **„persistent fail"-Detection**: wenn `now - last_resolve_attempt_utc > 24 h` UND Trade-Status noch OPEN, **WARNING statt CRITICAL**. Implementierung: neuer Log-Level-Pfad in `RewardSink._on_trade_closed` (logger.warning statt logger.critical bei `_check_backoff_and_skip → False && now - open_ts > 24h`). | WARNING erscheint in WebUI-Tail (`/api/last_cycle` zeigt die letzten Log-Zeilen), CRITICAL nicht. Operator kann so die „wirklich kranken" OPEN-Trades scannen. |
| **D5** | **Reihenfolge der Spalten-Migration**: `last_resolve_attempt_utc` **vor** `pnl_resolver.resolve()`-Aufruf in `_on_trade_closed` und in `reconcile_open_trades` schreiben (= „Claim" auf den Slot), **nach** dem erfolgreichen `resolve()` nicht ändern (kein Timestamp-Reset). | Pre-claim verhindert, dass zwei zwei concurrent Reconcile-Calls gleichzeitig denselben Backoff-Slot holen. Idempotenz durch `INSERT`-Whitelist (Phase-2 `_TRADE_COLUMNS`) ohne Migration der Read-Pfade. |

**Cross-Phase-Freigabe-Status:**

- **`phase7_reward/reward/recorder.py`** — Phase-7-Eigentum (Reward-Loop). Cross-Phase-Freigabe für
  Phase 7 ist **neu** in diesem Mini-Plan (Nikinger-Sign-off via P12-Recon-Plan).
- **`phase7_reward/reward/pnl_resolver.py`** — unverändert (Backoff-Skip-Logik lebt im Recorder,
  nicht im Resolver).
- **`phase8_scheduler/scheduler/reconcile.py`** — **unverändert** (Phase 8 ist freigegeben via
  Phase-14-Cross-Phase-Liste).
- **`phase2_persistence/migrations/003_phase12_reconcile_backoff.sql`** — Phase-2-Migration,
  freigegeben via Phase-14-Cross-Phase-Liste (Phase 2 ist enthalten).
- **`phase2_persistence/persistence/db.py`** — `_TRADE_COLUMNS` muss die neue Spalte aufnehmen
  (sonst INSERT scheitert). Phase-2-Touch freigegeben.

---

#### §3 Der Befund mit verifizierten Ankern

### §3.1 Die CRITICAL-Quelle

```
phase7_reward/reward/recorder.py:245-279    def _on_trade_closed(self, closed: ClosedTrade):
                                            : ...
                                            : 271   try:
phase7_reward/reward/recorder.py:272-274        close_level, profit_loss, r_multiple = pnl_resolver.resolve(
                                                   closed, self.broker, ctx, self.cfg)
                                            : 275   except Exception as exc:  # includes PnLUnavailable
                                            : 276       logger.critical(
                                            : 277           "reward: P&L unresolved for deal_id=%s: %s — trade stays OPEN, retry later",
                                            : 278           deal_id, exc,
                                            : 279       )
```

**Log-Prefix** ist `reward.recorder` (Python-Logger-Name = `__name__` = `reward.recorder`),
nicht `phase12`. Der historische Name „Phase-12-Reconciliation-Timing-Fix" in den
Session-Blöcken ist **ein Mislabling** aus früheren Sessions, wo der `reward.recorder`-Prefix
versehentlich der Phase 12 zugeordnet wurde (Recorder-Lives-there). **Korrekte
Phasen-Zuordnung:** Phase 7 (Reward-Loop-Eigentum) + Phase 8 (Reconcile-Pass-Eigentum) + Phase 2
(DB-Schema-Eigentum).

### §3.2 Die Wurzel-Exception

```
phase7_reward/reward/pnl_resolver.py:196-215  candidates: list[dict[str, Any]] = []
                                            : for tx in transactions:
                                            :     ...
                                            :     if own_open_instant is not None:
                                            :         if tx_close_instant < own_open_instant:
                                            :             continue
                                            :     candidates.append(tx)
                                            :
                                            : if not candidates:
                                            :     raise PnLUnavailable(
                                            :         f"no usable history row for deal_id={...} "
                                            :         f"(size={size}); IG lag — retry later"
                                            :     )
```

`PnLUnavailable` wird ausschließlich in Branch 3 (history-Match) geworfen, **niemals** in
Branch 1 (`closed.profit_loss`) oder Branch 2 (`closed.close_level`+Richtung). Letztere sind
lag-frei aus dem Close-Confirm (P7-Step 13c, 2026-06-26 live-verifiziert) — sie schlagen
**nie** „no usable history row" fehl. Der Fehler tritt also **nur** bei cold-reconcile-Pfaden auf
(d. h. entweder (a) Close-Confirm-Timeout oder (b) Restart zwischen Open und Close).

### §3.3 Der 5-Min-Cycle-Hammer

```
phase8_scheduler/scheduler/reconcile.py:114-149    def tick(self, state: SchedulerState) -> ReconcileReport:
                                                    :     # ...
                                                    : 137   resolved = self._reward_sink.reconcile_open_trades()
                                                    : # ...
                                                    : 149   if resolved:
                                                    :         logger.info("reconcile: resolved %d open trade(s): %s", ...)
```

`Reconcile.tick()` läuft in jedem Scheduler-Cycle (Standard 5 min, `scheduler/config.py`
`cycle_interval_min: int = 5`). Es ruft `reconcile_open_trades(None)` (= alle OPEN-Trades). Für
jeden OPEN-Trade wird `RewardSink._on_trade_closed` aufgerufen → `pnl_resolver.resolve()` →
`get_trade_history`. **Kein Backoff**: ein 30-min-IG-Lag erzeugt ~6 CRITICALs pro Trade.

**Empirischer Beweis** (heute nachgemessen, `data/state/scheduler.log`):

```
DIAAAAYCHTSTGA3: 13:49 → 14:05  (16 min, 2 retries)
DIAAAAYCN87PCAT: 14:02 → 14:08 → 14:23 → 14:38 → 14:54  (52 min, 5 retries)
DIAAAAYCPU28MA4: 16:07 → 16:12 → 16:28 → 16:44 → 16:59  (52 min, 5 retries)
DIAAAAYCT67N8AU: 10:42 → 10:47 → 11:02 → 11:18 → 11:34  (52 min, 5 retries)
```

= 17 CRITICALs in 3 Tagen, alle glücken am Ende (current DB state: 0 OPEN deals).

### §3.4 Heutiges OPEN-Trade-Volumen

```
sqlite> SELECT COUNT(*) FROM trade_outcomes WHERE status='OPEN';
0
```

Alle 4 betroffenen Deals sind zwischenzeitlich aufgelöst — der „Fix" reinigt also nicht eine
**laufende** Inkonsistenz, sondern reduziert die **historische CRITICAL-Frequenz** (= „leiserer
Betrieb"). Die Akzeptanz wird empirisch per **Replay-Test** gemessen (siehe §5 A2).

---

#### §4 Schritte (drei Atome, in fester Reihenfolge)

> **Commit nach jedem Schritt.** Nach jedem Schritt `pytest phase7_reward/tests
> phase8_scheduler/tests -q` — Phase 7 + Phase 8 sind die einzigen Suiten, die Tests ändern.

### Schritt 1 — DB-Migration + Spalte + Whitelist (1 Commit, 2 Dateien)

**Geänderte Dateien:**

`phase2_persistence/migrations/003_phase12_reconcile_backoff.sql` (NEU):

```sql
-- 003_phase12_reconcile_backoff.sql (Phase 7+8 backoff, 2026-08-31)
-- Erweitert trade_outcomes um last_resolve_attempt_utc (ISO-8601, tz-aware UTC)
-- für die RewardSink-Backoff-Logik. Migration ist idempotent (siehe Migration-Runner).
ALTER TABLE trade_outcomes ADD COLUMN last_resolve_attempt_utc TEXT;
```

`phase2_persistence/persistence/db.py` (+1 Zeile in `_TRADE_COLUMNS`):

```python
_TRADE_COLUMNS: tuple[str, ...] = (
    # ... existing columns ...
    "last_resolve_attempt_utc",  # P12-Reconcile-Timing: Backoff-Logik, ISO-8601 UTC
)
```

**Akzeptanz Schritt 1:** frische Test-DB (`init_db.py`) erreicht Schema-Version 3; Migration
auf bestehende DB ist idempotent (`ADD COLUMN` wirft beim zweiten Lauf, aber der
Migration-Runner scannt `_schema_version` und wendet nur unapplied Versionen an).

### Schritt 2 — Backoff-Logik in RewardSink (1 Commit, `phase7_reward/reward/recorder.py`)

**Neue Helper-Klasse** (oben, nach `import`-Block):

```python
# P12-Reconcile-Timing: exponential backoff for unresolved trade P&L retries.
# D1: 15 min → 30 min → 1 h → 4 h → 24 h cap. D4: WARNING statt CRITICAL nach 24 h.
_RETRY_BACKOFF_STEPS_S = (15 * 60, 30 * 60, 60 * 60, 4 * 60 * 60, 24 * 60 * 60)


def _next_retry_in_s(last_attempt_iso: str | None, open_ts_iso: str | None) -> int:
    """Return seconds until next retry is allowed.

    ``0`` means „proceed immediately" (first attempt or no prior attempt).
    Otherwise: pick the largest step whose duration has passed since the last
    attempt. Caps at 24 h (D1).
    """
    if last_attempt_iso is None:
        return 0
    last = _parse_iso(last_attempt_iso)
    if last is None:
        return 0
    elapsed = (datetime.now(timezone.utc) - last).total_seconds()
    for step in _RETRY_BACKOFF_STEPS_S:
        if elapsed < step:
            return int(step - elapsed)
    return 0  # past 24 h cap → allow next retry (caller decides severity)
```

**Modifikation** in `_on_trade_closed` (Z. 245):

```python
def _on_trade_closed(self, closed: ClosedTrade) -> None:
    deal_id = closed.deal_id
    row = self.db.get_trade_by_deal_id(deal_id)
    if row is None:
        logger.critical(
            "reward: no open record for deal_id=%s — cannot record close", deal_id
        )
        return

    # P12-Reconcile-Timing: backoff-skip if recent attempt was within the next-step window.
    last_attempt = row.get("last_resolve_attempt_utc")
    open_ts_iso = row.get("open_ts")
    retry_in_s = _next_retry_in_s(last_attempt, open_ts_iso)
    if retry_in_s > 0:
        logger.debug("reward: deal_id=%s backoff-skip (retry in %ds)", deal_id, retry_in_s)
        return

    # P12-Reconcile-Timing: claim the slot BEFORE calling resolve() (D5 — pre-claim).
    self.db.update_trade_resolve_attempt(deal_id, datetime.now(timezone.utc).isoformat())

    # ... existing logic: idempotency check, resolve(), persist ...
```

**Modifikation** in der `except`-Branch (Z. 275-279): Log-Level abhängig von D4 —

```python
except Exception as exc:  # noqa: BLE001 - includes PnLUnavailable
    # P12-Reconcile-Timing: WARNING statt CRITICAL nach 24 h ohne Auflösung.
    age_h = _parse_iso(open_ts_iso)
    severity = logger.critical
    if age_h is not None:
        hours_open = (datetime.now(timezone.utc) - age_h).total_seconds() / 3600
        if hours_open > 24:
            severity = logger.warning
            severity(
                "reward: P&L unresolved for deal_id=%s (%.1fh open): %s — "
                "persistent fail, investigate",
                deal_id, hours_open, exc,
            )
        else:
            severity(
                "reward: P&L unresolved for deal_id=%s: %s — trade stays OPEN, retry later",
                deal_id, exc,
            )
    else:
        severity(
            "reward: P&L unresolved for deal_id=%s: %s — trade stays OPEN, retry later",
            deal_id, exc,
        )
```

**Neue DB-Methode** in `phase2_persistence/persistence/db.py` (Whitelist + Schema):

```python
def update_trade_resolve_attempt(self, deal_id: str, iso_utc: str) -> None:
    """P12-Reconcile-Timing: stamp last_resolve_attempt_utc for backoff skip."""
    self._conn.execute(
        "UPDATE trade_outcomes SET last_resolve_attempt_utc = ?, "
        "updated_at = ? WHERE deal_id = ?",
        (iso_utc, iso_utc, deal_id),
    )
    self._conn.commit()
```

**Akzeptanz Schritt 2:** bestehende 138 P7-Tests grün + 4 neue Tests in
`tests/test_recorder.py` (Backoff-Skip-Lifecycle, persistent-fail WARNING, idempotenter
pre-claim, slot-claim überlebt Prozess-Restart).

### Schritt 3 — Live-Verifikation + Akzeptanz (1 Commit, optionale README-Notiz)

**Aktion:** Operator-Restart des Scheduler (`bash scripts/restart-services.sh restart scheduler`).
Live-Beobachtung: nächster OPEN-Trade mit `PnLUnavailable` produziert **maximal einen CRITICAL pro
Backoff-Stufe** (= 5 CRITICALs max, statt 6+ ohne Backoff). Nach 24 h ohne Auflösung: WARNING.

**Akzeptanz Schritt 3:**
- `bash scripts/restart-services.sh status` zeigt Scheduler `alive`.
- `pytest phase7_reward/tests phase8_scheduler/tests -q` ≥ 142 grün (138 + 4 neu).
- README-Notiz in `phase7_reward/README.md` (Backoff-Sektion, ~20 Zeilen, kein API-Change).

---

#### §5 Akzeptanz (PASS-Kriterien A1–A6)

| # | Kriterium | Wie belegt |
|---|---|---|
| **A1** | `last_resolve_attempt_utc`-Spalte existiert nach Migration auf Schema-Version 3 | `pytest phase2_persistence/tests -q` (Schema-Version-Asserts); `sqlite3 data/trading_bot.sqlite ".schema trade_outcomes"` zeigt die Spalte |
| **A2** | Replay-Test: 17 historische CRITICALs aus 2026-08-25/26/27 hätten mit Backoff nur 4-5 produziert (einer pro Backoff-Stufe). | `tests/test_recorder.py::test_backoff_replay_reduces_critical_count` — synthetisches Replay-Skript simuliert die 4 Deals mit denselben Open-Timestamps, mockt `pnl_resolver.resolve` so dass es immer `PnLUnavailable` wirft, und assertiert: ohne Backoff = 17 CRITICALs, mit Backoff = ≤ 5. |
| **A3** | Backoff-Skip verhindert CRITICAL-Repeat innerhalb der Backoff-Window | `tests/test_recorder.py::test_backoff_skip_within_window` — setzt `last_resolve_attempt_utc = now - 5 min`, ruft `_on_trade_closed` erneut, assertiert: kein CRITICAL-Log, kein `update_trade_resolve_attempt`-Call (pre-claim nicht ausgelöst) |
| **A4** | Persistent-fail-WARNING nach >24 h ohne Auflösung | `tests/test_recorder.py::test_persistent_fail_warning` — `open_ts = now - 25 h`, mockt `pnl_resolver.resolve` → `PnLUnavailable`, assertiert: WARNING geloggt, kein CRITICAL |
| **A5** | Pre-claim-Idempotenz: zwei concurrent `_on_trade_closed`-Calls lassen nur einen den resolve() ausführen | `tests/test_recorder.py::test_preclaim_idempotent_concurrent` — setzt `last_resolve_attempt_utc = now`, ruft zweimal `_on_trade_closed` parallel, assertiert: nur ein `update_trade_resolve_attempt`-Call + nur ein `resolve`-Call |
| **A6** | Live-Verifikation: nach Scheduler-Restart produziert der nächste OPEN-Trade mit IG-Lag ≤ 5 CRITICALs in 24 h (statt 6+ ohne Backoff) | Operator-Run nach dem Code-Commit; manuelles Log-Scanning `data/state/scheduler.log` auf neue CRITICALs des neuen deal_id |

**Nicht Teil der Akzeptanz** (bewusst):
- Die Frage, was beim **persistent-fail** (= Trade > 24 h OPEN) operativ passiert: (Trade bleibt
  OPEN, kein auto-close — bewusst, weil wir nicht wissen, ob IG jemals settled; V4-Plan-Session
  entscheidet, ob persistent-fail ein VETO-äquivalenter Stop wird).
- Schema-Validation-Rollback-Test (zu teuer, out-of-scope für ein einzelnes Timing-Fix).
- WebUI-Endpoint für „persistent-fail OPEN trades" (Operator kann via Log-Scan arbeiten; P15-V4
  kann den Endpoint nachziehen).

---

#### §6 Out of Scope

- **Phase-15-Planung** (V4: Council, Handover, Reward-Reform, Force-Trigger, Instinct-ECC). Hier
  ist Vorbereitung — der persistent-fail-WARNING ist Material für P15-V4-Diskussion; nicht der
  Fix selbst.
- **Schema-Validation-Rollback-Test** (zu teuer für ein einzelnes Timing-Fix; Phase-12-Pattern ist
  „ADD COLUMN"-only).
- **Schema-Migration auf Phase-12-Recorder** (Recorder ist in Phase 12, aber nicht berührt — der
  Recorder schreibt Bars, der RewardSink resolved P&L; diese sind entkoppelt).
- **Auto-Close bei persistent-fail** (Trade bleibt OPEN; auto-close wäre eine P5-Order-Operation
  und braucht eine separate Cross-Phase-Freigabe + Plan-Session).
- **WebUI-Endpoint** „aktuelle persistent-fail OPEN-Trades" (Operator-Scan via Log reicht für jetzt;
  WebUI ist read-mostly und nicht der primäre Operator-Weg für diese Diagnose).
- **Phase-13-Beweiswoche-Auswertung** (separater Track, läuft seit Mo 2026-08-25, ist close-out-fähig
  mit Pfad-C-Entscheidung 2026-08-31).
- **Live-Code-Touch außerhalb Phase 7 + Phase 2** (Phase-8-Reconcile-Pfad bleibt unverändert; D3
  bündelt die Backoff-Skip-Logik im RewardSink, nicht im Scheduler).

---

#### §7 Fehlgriffe, die wie andere Fehler aussehen

| Symptom | Erster Verdächtiger | Wie unterscheiden |
|---|---|---|
| **„NCRITICALs kommen weiter, alle paar Minuten, derselbe deal_id"** | Echter Backoff-Bug (z. B. `last_resolve_attempt_utc` wird nicht korrekt geschrieben) | `sqlite3 data/trading_bot.sqlite "SELECT deal_id, last_resolve_attempt_utc FROM trade_outcomes WHERE status='OPEN'"` zeigt die Spalten-Inhalte. Wenn `last_resolve_attempt_utc` für den CRITICAL-deal_id innerhalb der Backoff-Window steht → Backoff funktioniert, der Scheduler ruft nicht `_on_trade_closed` (würde im DEBUG-Log landen). |
| **„Trade bleibt für immer OPEN, kein WARNING nach 24 h"** | Pre-claim bug: `_on_trade_closed` wird nicht aufgerufen, weil `reconcile_open_trades` den Trade nicht listet | `tests/test_recorder.py::test_persistent_fail_warning` (A4) zeigt das Verhalten lokal. Wenn lokal OK, aber live kaputt: `data/state/scheduler.log` zeigt, ob `reconcile_open_trades` aufgerufen wird (jeder Aufruf logged die Deal-Liste). |
| **„Migration 003 wirft beim zweiten Lauf"** | Phase-2-Migration-Runner scannt `_schema_version`, idempotente Migrations | Migration-Runner ist seit Phase-7-CLAUDE §1.7 dokumentiert; `tests/test_schema_migrations.py` bestätigt Idempotenz. Wenn der Test grün ist, ist die Migration OK; wenn nicht, ist es ein Phase-2-Bug, nicht Phase-7. |
| **„Aktuelle OPEN-Trades (vor diesem Fix) lösen sich nach dem Fix nicht auf"** | Backoff-Skip überspringt Trades mit `last_resolve_attempt_utc = None`? | D1: `_next_retry_in_s` returnt `0` für `last_attempt_iso=None` → erste Attempts laufen sofort durch. Nach dem ersten Attempt wird `last_resolve_attempt_utc` gesetzt → Backoff greift ab dann. Vor diesem Fix gibt es keine OPEN-Trades (siehe §3.4), also kein Live-Risiko. |
| **„A6 Live-Verifikation: weiter CRITICALs > 5 / 24 h für einen neuen deal_id"** | Backoff-Window zu kurz für IG-Lag, oder Pre-claim bug | 24 h empirisch beobachten; falls > 5, D1-Stufen härter setzen (z. B. 30 min → 1 h → 4 h → 8 h → 24 h cap). Folge-Session-Plan, nicht dieser-Fix. |

---

#### §8 Drift-Liste — bei Ausführung verifizieren

> **Diese Liste ist vollständig.** Was hier nicht steht, hat diese Planungssession am
> 2026-08-31 selbst gegen das Repo geprüft und ist als Fakt formuliert. Rate nichts nach;
> prüfe diese und nur diese.

1. **Zeilennummern verschieben sich.** Jeder Anker oben trägt den **Verbatim-String** — der ist
   der Anker, die Zahl die Abkürzung. Schritt 1 ändert `db.py` (`_TRADE_COLUMNS`); Schritt 2 ändert
   `recorder.py` (Z. 245-280-Bereich) + fügt `update_trade_resolve_attempt` zu `db.py` hinzu.
   **Immer per String suchen.**
2. **`PnLUnavailable`-Wortlaut bleibt unverändert.** Der Backoff lebt im Recorder, nicht im
   Resolver. `pnl_resolver.py:212` wird **nicht** angefasst. Der Wortlaut
   „no usable history row for deal_id=... IG lag — retry later" bleibt für Kompatibilität
   mit bestehenden Log-Scannern.
3. **`_TRADE_COLUMNS` muss erweitert werden.** Phase-2-Whitelist (P2-CLAUDE.md §3) — sonst
   scheitert das nächste `insert_trade` mit `unknown column last_resolve_attempt_utc`. Schritt 1
   deckt das ab.
4. **Phase-7-Cross-Phase-Freigabe.** Phase 7 ist **nicht** in der Phase-14-Cross-Phase-Liste.
   Nikinger-Sign-off via diesem Mini-Plan ist die Freigabe; ohne Sign-off **kein** Commit
   auf `phase7_reward/reward/recorder.py`.
5. **`get_trade_history(days=30)`-Limit.** Branch 3 fragt immer `days=30` (Default in
   `pnl_resolver.py`); sehr alte OPEN-Trades (>30 Tage) lösen sich nie auf. Mit Backoff ist das
   weniger ein Problem (weniger CRITICALs), aber die „persistent fail"-Frage bleibt für V4.
6. **Backoff-Stufen sind Konstanten, nicht konfigurierbar.** D1 nennt die Stufen explizit; eine
   `RewardConfig.backoff_steps_s = (...)-Tuple` ist overkill für die aktuelle IG-Settlement-Realität.
   Wenn P15-V4 mehr Flexibilität braucht, wird sie nachgezogen.
7. **Migration 003 ist nur `ADD COLUMN`.** Kein `UPDATE existing rows` — bestehende OPEN-Trades
   (heute 0) bekommen `last_resolve_attempt_utc = NULL`, was `_next_retry_in_s` korrekt als „sofort
   retry" interpretiert. Bei zukünftigen OPEN-Trades wird das Feld ab dem ersten Attempt gesetzt.
8. **Phase-8-Tests bleiben unverändert.** `tests/test_reconcile.py` mockt den `RewardSink`-Aufruf;
   kein Backoff-Wissen nötig. Falls Phase-8-Tests brechen, ist es ein Coupling-Bug.
9. **Der Scheduler muss nach dem Code-Edit neu gestartet werden** (Python `sys.modules`-Cache, P14-D
   §10-Korrekturnotiz). Operator-Restart ist **zwingender Teil von** Schritt 3, kein Optional.
10. **Heute keine OPEN-Trades** (siehe §3.4) — der Fix wird rein präventiv wirksam. Die Akzeptanz
    A2 (Replay-Test) misst die Verbesserung gegen den historischen 17-CRITICAL-Datensatz.

---

#### §9 Cross-Refs

- **Phase-7-CLAUDE.md** — `pnl_resolver.py` Step 9 + `recorder.py` Step 8 + `decision J` (fail-closed
  writes). Backoff-Skip ist **additiv** zu Decision J, kein Konflikt.
- **Phase-8-CLAUDE.md** — `reconcile.py` ist Contract F (composition, nicht reimplementation). Der
  Backoff lebt im RewardSink (D3); Phase-8-Composition bleibt unverändert.
- **Phase-2-CLAUDE.md** — `_TRADE_COLUMNS` Whitelist (§3, Konzept §3/§12). Migration 003 ist
  ADD COLUMN, das Standard-Migration-Pattern.
- **P14-F-Plan** — orthogonal (Doc-Rotation-Hook); keine Code-Überschneidung.
- **Phase-13-Findings-Notiz** [`../phase13_live_data/PHASE13_BEWEISWOCHE_FINDINGS_2026-08-31.md`]
  §5.2 — erwähnt „Phase-12-Reconciliation-Timing-Fix" als laufend; dieser Plan ist die Antwort.
- **Mini-Session-21-Findings** (Phase-14-CLAUDE.md) — Recorder-Code-Edit braucht Operator-Restart
  (P14-D §10-Korrekturnotiz); dasselbe Pattern gilt für diesen Plan (Scheduler-Restart nach
  Recorder-Code-Edit).
- **P15-V4-Plan-Material** — persistent-fail OPEN-Trades sind V4-Diskussions-Material (Quellen-
  Vertrauens-Modell + Reward-Reform). Dieser Plan liefert das Substrat (WARNING-Log); V4
  entscheidet die Folgeschritte.

---

**Stand:** 2026-08-31 ~07:50 UTC, Mini-Session 25 (Plan-Vorbereitung Session).
**Nächste Aktion:** Nikinger-Sign-off für Phase-7-Cross-Phase-Freigabe (D2), dann
Schritt 1 (Migration + Whitelist) ausführen.