# Phase 8 → v1.7 Hotfix — Initial-Plan (das „Was")

> **Audience:** die spätere Claude-Code-Session, die aus diesem „Was" den detaillierten
> Ausführungsplan (das „Wie") baut — und danach die Implementierungs-Session selbst.
> **Author:** Claude Code, 2026-07-02 (dieselbe Repo-Umgebung, Code = Source of Truth).
> **Was diese Datei ist:** ein bewusst **kleiner** v1.7-Plan (kein Vergleich zum Umfang von
> v1.5/v1.6) — Richtung + Steps + offene Fragen, im selben Zwei-Stufen-Modell wie
> `phase8_v1.6_hotfix_plan.md`: diese Datei ist das „Was", eine spätere Session baut daraus
> das „Wie" und implementiert.

---

## 0. Kontext — der historische erste autonome Trade

Am 2026-07-02 hat der Phase-8-Scheduler zum ersten Mal überhaupt einen **echten, autonom
generierten, net-new Trade** platziert — der harte, bisher unbewiesene Kern der Phase-8-Mission
(root `CLAUDE.md`: „autonome, unbeaufsichtigte Erzeugung echter Demo-Trades"):

- **DAX BUY**, `deal_id=DIAAAAXW7U4AWAP`, size 19.5, `open_level=25617.0`.
- Entstanden aus einem **echten P4-Research-Pick** (conf 62) → **echter P6-Bull/Bear/Judge-
  Debatte** → Entscheidung **TRADE** (nicht ABSTAIN wie in allen vorherigen Zyklen des Tages).
- Order **ACCEPTED** um 16:58:32; vom Broker per SL/TP geschlossen um 17:07:21
  (`execution.monitor: … gone from broker — closed by broker SL/TP`).
- P&L-Auflösung folgt dem bereits aus Phase 7 bekannten, dokumentierten Muster: IG bucht die
  Transaktionshistorie erst nach Settlement → der erste Resolve-Versuch (17:07:21) und ein
  Retry (17:12:21) meldeten „IG lag — retry later"; die `Reconciler`-Pass (Modul 9/10) läuft
  periodisch weiter und wird die P&L auflösen, sobald IG nachzieht — **kein neuer Bug**, das ist
  exakt der in Phase 7 bewiesene, idempotente Retry-Pfad.

**Kurz danach meldete Nikinger die Webui als „kaputt"**: der Trade-Zähler und die Realized-P&L-
Karte zeigten falsche/veraltete Werte, zusätzlich waren die Score-/Confidence-/Lessons-Karten
leer. Zwei parallele Untersuchungen (Code + Live-DB + Live-Log, read-only, noch kein Fix) haben
die Ursache **präzise und mit niedrigem Risiko** eingegrenzt — **kein** Zusammenhang mit dem am
selben Tag gemergten `provenance`-Spalten-Fix (siehe §1), **kein** Sicherheitsproblem (DB,
Broker- und Daily-Loss-Breaker-Pfad sind bestätigt korrekt und unberührt).

**Nikinger-Bestätigung (nach Live-Beobachtung):** der Trade-Zähler hat sich selbst korrigiert
(0/5 → 1/5), sobald der Scheduler-Zyklus fertig durchgelaufen ist — „einige Elemente sind
einfach extrem verzögert". Das deckt sich exakt mit der unten dokumentierten Diagnose.

---

## 1. Befund (Root Cause, code-verifiziert 2026-07-02)

**Der eigentliche Fund ist überraschend klein und webui-only.** `scheduler/state.py`s eigener
Docstring (Design Point 3, bereits vor v1.7 dokumentiert) legt offen, dass
`SchedulerState.realized_pnl_today` **bewusst** ein *best-effort*-Snapshot ist, **nicht** die
Quelle der Wahrheit für den Loss-Breaker: `record_cycle` faltet P&L nur zum Zyklus-Zeitpunkt
ein, und ein `CLOSED_BY_BROKER`-Close liefert an dieser Stelle strukturell `profit_loss=None`
(die echte P&L löst sich **später**, asynchron, über den bereits existierenden
`Reconciler`/P7-`reconcile_open_trades`-Pass auf, sobald IGs Historie settled — bewiesenes
Phase-7-Verhalten). **Der sicherheitskritische Daily-Loss-Breaker liest deshalb bereits direkt
aus der DB** (`scripts/wiring.py:301-308`, eine getestete
`SELECT COALESCE(SUM(profit_loss),0.0) FROM trade_outcomes WHERE session_date=? …`-Closure —
exaktes Prädikat beim Implementieren gegenprüfen).

**Die Webui hat diese Unterscheidung nie bekommen:** `/api/status` (`webui/api.py:145,147`)
reicht das lagging `state.trades_today`/`state.realized_pnl_today`-Snapshot direkt an das
Dashboard durch, als wäre es Live-Wahrheit — während `/api/trades` (`webui/api.py:223-232`) auf
demselben Dashboard bereits korrekt direkt aus der DB liest. Das Dashboard wurde deshalb intern
inkonsistent, sobald der Lebenszyklus eines echten Trades lang genug dauerte (~9 Minuten,
IG-Settlement-Lag), um diese Lücke sichtbar zu machen — zum ersten Mal überhaupt, weil es der
erste echte autonome Trade überhaupt war. `trades_today` hat sich selbst korrigiert, sobald der
Zyklus fertig durchlief und `record_cycle`/`save` ausgeführt wurde (von Nikinger live bestätigt:
0/5 → 1/5). `realized_pnl_today` bleibt dagegen **strukturell** falsch für jeden
`CLOSED_BY_BROKER`-Trade, weil der Fold-Pfad den später aufgelösten Wert nie empfängt — das ist
der eigentliche, nicht selbstheilende Bug.

**Die leeren Score-/Confidence-/Lessons-Karten sind ein separater, korrekter Nicht-Bug:** der
Operator-Lauf `archive_verification_trades.py --commit` (heute, unabhängig von diesem Vorfall)
hat die einzigen `reward_pts`/`trade_lessons`-Zeilen kaskadierend auf null gelöscht — echter
Leerzustand, keine Störung.

**Ausgeschlossen (beide unabhängigen Untersuchungen stimmen überein, hohe Konfidenz):** die am
selben Tag gemergte `provenance`-Spalte (Migration 003) als Ursache. Es gibt **keinen** Code-Pfad
irgendwo im Repo (Webui, Persistence, Scheduler), der `trade_outcomes` positional/ordinal liest —
jeder Read ist named-column/dict-basiert (`sqlite3.Row` oder `dict(row)`). Eine spätere Session
sollte diese Hypothese **nicht** erneut verfolgen.

---

## 2. Steps (bewusst klein — das ist ein echtes „kleines v1.7", kein Multi-Step-Epic)

**Step 1 — der eigentliche Fix (P8-only, `webui/api.py`).** `/api/status`s `trades_today` +
`realized_pnl_today` DB-gespeist machen, statt aus dem State-Snapshot — Wiederverwendung des
bereits bewiesenen Query-Musters aus `scripts/wiring.py`s `realized_pnl_today`-Closure, gespiegelt
an `/api/trades`s bereits direktem DB-Read. `scheduler/state.py`/`safety.py`/`reconcile.py`
bleiben **unberührt** (ihr aktuelles Verhalten ist korrekt und dokumentiert; andere Konsumenten —
Day-Rollover, Backoff, Restart-Sicherheit — hängen unverändert am Snapshot). **Keine**
Client-Änderung (`app.js`) erwartet — es rendert nur, was `/api/status` liefert.

**Step 2 — optional, kosmetisch, niedrigste Priorität (explizit unter Zeitdruck streichbar).**
Freundlichere Score-/Confidence-/Lessons-Leerzustand-Meldung, die „archiviert" von „nie Daten
gehabt" unterscheidet — kein funktionaler Bug, bei Zeitdruck überspringen.

**Step 3 — Operator-Live-Verifikation.** Einen weiteren echten Trade-Zyklus end-to-end in der
Webui beobachten, bestätigen dass beide Karten korrekt aktualisieren und mit der Trades-Tabelle
konsistent bleiben.

**Step 4 — Doku-Flip.** `phase8_scheduler/CLAUDE.md` + Root-`CLAUDE.md` nach Verifikation
aktualisieren.

---

## 3. Offene Fragen für die „Wie"-Session

1. **Exaktes SQL-Prädikat** für `/api/status`s DB-gespeisten Trade-Count/P&L — soll `trades_today`
   auch `OPEN`-Trades zählen (damit der Zähler auch mitten im Zyklus live-akkurat ist, wie es
   `/api/trades` bereits zeigt), oder ist die UI-Semantik „Trades heute" bewusst anders (nur
   Closes zählen)? `wiring.py`s `realized_pnl_today`-Prädikat exakt spiegeln, oder unterscheidet
   sich die UI-Semantik?
2. **Sauberer Read-Helper vs. Inline-SQL:** einen leichten, wiederverwendbaren, getesteten Read
   in `persistence/db.py` (P2) ergänzen (P2-`CLAUDE.md`-Konvention: „P2 stays a dumb
   parameterised store") statt Ad-hoc-SQL direkt in `webui/api.py` — `webui/api.py` macht
   bereits an anderer Stelle Inline-SQL (Präzedenz existiert für beide Wege) — in der
   „Wie"-Session entscheiden.
3. **Zählt dieser Trade als v1.6-Step-4s „5a Varietäts-Run"-Beweis** (net-new autonomer
   open→close) oder braucht 5a noch einen saubereren/längeren/Mehr-Trade-Lauf? **Das ist
   Nikingers Entscheidung**, nicht in diesem Dokument vorwegzunehmen.
4. Ist **Step 2** (Leerzustand-Copy) überhaupt Teil des ersten v1.7-Cuts, oder unbegrenzt
   zurückgestellt?

---

## 4. Cross-Phase-Register (antizipiert)

Voraussichtlich **rein P8** (`webui/api.py`, evtl. ein kleiner neuer P2-Read-Helper je nach
offener Frage 2) — **kein** P4/P5/P6/P7-Logik-/Schema-Touch erwartet, anders als v1.5/v1.6. Vor
Baubeginn in der „Wie"-Session bestätigen.

**Regression-Hinweis:** nur gemockte `pytest` (Webui hat eine eigene Testsuite in
`phase8_scheduler/tests/test_webui.py` — dort erweitern, kein neues Muster erfinden); Live-/
Netz-Verifikation bleibt Nikingers Job (Projekt-Konvention).

---

*Ende des Plans (Was). Die „Wie"-Session baut daraus den file-für-file-Ausführungsplan.*
