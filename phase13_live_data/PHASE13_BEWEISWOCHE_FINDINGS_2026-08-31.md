---
status: snapshot
purpose: Source-Delta-Diagnose der Phase-13-Beweiswoche (14-Tage-Fenster, 2026-08-18 bis 2026-08-31).
Empirischer Befund: IG-Quelle liefert im Archiv nur 2 von 13 Handelstagen (17.07. + 18.08.), `instrument_source_availability`
meldet aber `status='ok', history_min_days=30`. Selbst am letzten Tag mit IG-Bars (2026-08-18) divergieren 53.6 %
der vergleichbaren Paper-Trades zwischen IG und yFinance. Folge: Phase-14 D5-Handover ist **technisch freigegeben**
(Tabelle funktioniert), aber **operativ blockiert** durch IG-Substrat-Inkonsistenz, die ein Phase-13-Recorder-Mapping-Problem ist.
read-when: jede Session, die Phase-14 D5-Handover berührt; jede Session, die den Beweiswoche-Track fortsetzt;
jede Plan-Session, die Phase 15/16 strukturiert.
detail: L3
up: ../CLAUDE.md
down:
  - ../CLAUDE.md                                # Phasenkopf, mit Findings-Verweis-Zeile ergänzen
  - ../../docs/concepts/phase13_live_data_plan.md  # 📕 Mutterplan, unangetastet
  - ../../docs/concepts/phase13_c_block_c_replan.md # Block-C-Re-Plan, dessen These hier empirisch bestätigt wird
  - ./scripts/source_delta.py                  # das Diagnose-Tool (Block C3, 7 Tests grün)
  - ../../phase14_discovery/CLAUDE.md           # Phase-14-Phasenkopf (D5-Handover-Status)
  - ../../phase14_discovery/PHASE14_F_DOC_ROTATION_HOOK_STEP2_PLAN.md # Phase-14-Schwester, die in dieser Diagnose-Woche auch lebte
updated: 2026-08-31 (+ §8 Pfad-C-Nachtrag 2026-08-31, Mini-Session 24)
---
# PHASE13_BEWEISWOCHE_FINDINGS_2026-08-31 — Source-Delta-Diagnose

> **Adressat:** die Folgesession, die Phase-14 D5-Handover entscheidet, plus die
> Phase-13-Plan-Session, die den Recorder-Mapping-Bug fixt.
> **Stand:** 2026-08-31 ~10:00 UTC, Mini-Session 23 (Phase-13-Beweiswoche-Auswertung).
> **Methode:** `python3 phase13_live_data/scripts/source_delta.py --days 14` gegen die
> read-only Produktions-DB; Substrat-Cross-Check direkt gegen `bars.sqlite` und
> `trading_bot.sqlite`.

---

## §0 BLUF

| # | Befund | Konsequenz |
|---|---|---|
| **B1** | **IG-Bars im Archiv nur an 2 von 13 Handelstagen** (2026-07-17 + 2026-08-18). 13-Tage-Lücke bis heute. | Phase-13-Recorder-Mapping-Bug oder IG-Spalte wird seit 2026-08-18 nicht mehr befüllt — **Recorder läuft, schreibt aber nicht für IG-Quelle**. |
| **B2** | **53.57 % Divergenzrate** zwischen IG und yFinance am letzten Tag mit Bars (2026-08-18, 30 von 56 vergleichbaren trades). 18/30 = TP↔SL-Gegensatz. | Selbst wenn beide Quellen Bars liefern, sind sie **nicht austauschbar** — Preis-Drift ist real, nicht Latenz-only. |
| **B3** | `instrument_source_availability` für IG: `status='ok', history_min_days=30, origin='derived', last_verified_utc=2026-08-31T06:47Z`. Realität: 2/13 Tage. | Phase-14-Tabelle lügt **strukturell** über die IG-Quelle. Source-Delta-Mechanik fängt das (B1→B2-Kette), aber erst **zur Laufzeit**, nicht im Vorab-`status`. |

**Daraus folgt für Phase-14 D5-Handover:**
- **Phase-14 ist technisch fertig** — die Tabelle ist da, Discovery läuft, Source-Delta funktioniert wie designed. Architektonisch kann Phase 15 starten.
- **Phase-14 ist operativ blockiert** — solange `instrument_source_availability.ig.status='ok'` aber `instrument_source_availability.ig.history_min_days=30` lügt und der Recorder für IG keine Bars schreibt, ist die Tabelle **unzuverlässig**, und Konsumenten, die `prefer='ig'` lesen, bekommen leere Fenster.
- **D5-Handover: TEILWEISE** — architektonisch freigegeben, mit Pflicht-Vermerk im Phase-14-Phasenkopf, dass die operative Freigabe an die IG-Substrat-Reparatur gekoppelt ist (Phase-13-Initiative, nicht Phase-14-Bug).

---

## §1 Methodik (was wurde gemessen, wie, womit)

**Tool:** `phase13_live_data/scripts/source_delta.py` (Block C3, 7 Tests grün seit Session 14).
Liest für jeden RESOLVED-paper_trade im Fenster die Bars aus `bars.sqlite` pro registrierter
Quelle aus `instrument_source_availability.status='ok', resolution='1m'`, ruft
`resolve_paper_trade()` pro Quelle auf, klassifiziert in drei Fälle:
- `not_available`: keine registrierte Quelle
- `available_but_empty`: mind. eine Quelle registriert, aber mind. eine liefert n_bars=0 im Trade-Fenster
- `compared`: ≥ 2 Quellen mit exit_reason + pnl_points → `agree` oder `diverge` (1e-9-Toleranz auf pnl)

**Lauf-Befehle** (in dieser Session ausgeführt):
```
python3 phase13_live_data/scripts/source_delta.py --days 7   # Mo 25.08. – So 31.08.
python3 phase13_live_data/scripts/source_delta.py --days 14  # Mo 18.08. – So 31.08.
```

**Substrat-Cross-Check (read-only):**
```
sqlite3 data/trading_bot.sqlite "SELECT ... FROM paper_trades/instrument_source_availability"
sqlite3 data/bars.sqlite "SELECT ... FROM bars"
```

Beide gegen `mode=ro` (Phase-13-CLAUDE.md Working-Style).

---

## §2 Empirische Befunde im Detail

### §2.1 Bars-Substrat pro Quelle (Stand 2026-08-31)

| Quelle | Bars total | Tage | Range | Lücken |
|---|---:|---:|---|---|
| `ig` | **2083** | **2** (von 13 möglichen) | 2026-07-17 + 2026-08-18 | **11 Tage** (19.08. – 31.08.) |
| `yf` | 24284 | 11 | 2026-08-17 – 2026-08-28 | Wochenende (Sa/So) |
| `capital` | 962 | 1 | 2026-08-21 | Operator-Live-Verify-Run |

**Befund B1 verschärft:** IG-Bars sind seit **2026-08-18 15:41 UTC** nicht mehr ins Archiv
geschrieben worden — exakt 13 Tage Lücke. Der Recorder (`python -m data_foundation.run`,
PID 7711, alive seit Mini-Session 21) läuft, schreibt aber für `source='ig'` offenbar nichts.

**Per-Epic IG-Verteilung:**
```
IX.D.CAC.IFE.IP   : 452 bars, 2026-08-18 08:10 → 15:41 UTC
IX.D.DAX.IFMM.IP  : 426 bars, 2026-08-18 08:36 → 15:41 UTC
IX.D.DAX.IGN.IP   : 452 bars, 2026-08-18 08:10 → 15:41 UTC
IX.D.IBEX.FWM2.IP : 306 bars, 2026-07-17 11:14 → 16:14 UTC  ← 4 Wochen alt!
IX.D.IBEX.IFM.IP  : 452 bars, 2026-08-18 07:58 → 15:41 UTC
```
Acht IG-Epics in `instrument_source_availability` (DAX/CAC/IBEX/SUN*), aber nur 5 haben
jemals Bars bekommen — drei SUNDAX/SUNDOW/SUNNAS-Epics sind **null-Bars total** (kein
einziger Tag).

### §2.2 instrument_source_availability vs. Realität

Alle 8 IG-Rows (`status='ok', resolution='1m', origin='derived'`):

```
epic                 | status | origin   | history_min_days | last_verified_utc
IX.D.CAC.IFE.IP      | ok     | derived  | 30               | 2026-08-31T06:47:10.291Z
IX.D.DAX.IFMM.IP     | ok     | derived  | 30               | 2026-08-31T06:47:10.291Z
IX.D.DAX.IGN.IP      | ok     | derived  | 30               | 2026-08-31T06:47:10.291Z
IX.D.IBEX.FWM2.IP    | ok     | derived  | 30               | 2026-08-31T06:47:10.291Z
IX.D.IBEX.IFM.IP     | ok     | derived  | 30               | 2026-08-31T06:47:10.291Z
IX.D.SUNDAX.IGN.IP   | ok     | derived  | 30               | 2026-08-31T06:47:10.291Z
IX.D.SUNDOW.IAE.IP   | ok     | derived  | 30               | 2026-08-31T06:47:10.291Z
IX.D.SUNNAS.IAE.IP   | ok     | derived  | 30               | 2026-08-31T06:47:10.291Z
```

Realität: **5 Epics haben je 1 Tag Bars, 3 SUN-Epics haben 0 Bars, 0 Epics haben 30 Tage Bars.**

**`last_verified_utc` ist nicht aussagekräftig** — das Feld wird vom Discovery-Daemon auf
"`instrument_universe hat diese Zeile`" gesetzt (= trivial wahr), **nicht** auf
"`bars.sqlite hat Bars für diese Quelle in den letzten 7 Tagen`". Der Discovery-Cycle
vom 2026-08-31 06:47 UTC hat die `derived`-Zeilen aus `instrument_universe` re-importiert
(= ja, IG-Epic existiert), ohne tatsächlich Bars zu prüfen.

**Befund B3:** Phase-14-Tabelle ist **kein** Substrat-Validitäts-Lieferant. Sie ist ein
**Verfügbarkeits-Index** (was ist prinzipiell möglich), kein **Aktualitäts-Index** (was
ist tatsächlich da). Die zwei sind strukturell verschieden.

### §2.3 Source-Delta-Ergebnis 14-Tage-Fenster (2026-08-18..2026-08-31)

```
total=332  agree=26  diverge=30  not_available=0  available_but_empty=276
divergence_rate=53.57%   (= 30 / (26+30))
```

**Per-Tag-Verteilung (nur `compared`):**
```
2026-08-18 : 70 trades total, 56 compared, 26 agree, 30 diverge, rate=53.6%
2026-08-19..2026-08-31 : 0 compared (alle available_but_empty wegen IG-Lücke)
```

**Befund B2 (Divergenz-Pattern, n=30 divergente trades):**
```
IG=SL     → yF=TP        : 10 trades  (Gegensatz)
IG=TP     → yF=SL        :  8 trades  (Gegensatz gespiegelt)
IG=SL     → yF=TIME_STOP :  5 trades  (vorzeitig abgebrochen)
IG=TP     → yF=TIME_STOP :  3 trades
IG=TIME_STOP → yF=TIME_STOP :  4 trades  (gleicher exit, aber pnl-Drift)
```

**18 von 30 divergenten trades (60 %) zeigen TP↔SL-Gegensatz** — IG und yFinance
sehen für den gleichen Trade **gegenteilige Exit-Gründe**. Das ist nicht Latenz
(sonst wäre es nur ein paar Minuten Verzögerung), das ist **echte Preis-Drift**
zwischen den Quellen im 1-Minuten-Fenster.

**Stichprobe (erste 5 divergent rows):**
```
paper_id=7b0b4652 epic=DAX.IFMM created=2026-08-18T07:05
  IG: n_bars=210 reason=TP  pnl=+45.0
  yF: n_bars=300 reason=SL  pnl=-30.0

paper_id=d94ae75e epic=DAX.IFMM created=2026-08-18T07:05
  IG: n_bars=210 reason=SL  pnl=-30.0
  yF: n_bars=300 reason=TP  pnl=+45.0
```

Auffällig: **IG hat 210/236 Bars, yF hat 300 Bars** für den gleichen Trade. Die Quellen
haben unterschiedlich viele Bars im Fenster. yF liefert konsistent 300 = (240 max_hold +
60 padding), IG liefert nur 210-236 — also hört IG früher auf (offenbar XETRA-Markt-Close
gegen 17:30 UTC, aber unsere Trade-Resolution rechnet 240+60 Min weiter und IG-Bars
enden bei 15:41 UTC).

**Hypothese zur Erklärung:** IG-Bars sind echte Intraday-XETRA-Close-Snapshots (echt um
15:30 UTC Close), yF ist delayed/yF-Bar-Intraday-konstruiert und liefert auch nach
Markt-Close Bars (Phantom-Bars). Damit ist **die Substrat-Qualität pro Quelle
fundamental verschieden**, und ein Konsument, der `prefer='ig'` oder `prefer='yf'` liest,
muss die Quelle-spezifische Coverage kennen.

---

## §3 Was funktioniert (Bestätigung von Block C3)

**Source-Delta-Mechanik arbeitet wie designed** (Block C3, 7 Tests grün seit Phase-13-Session 14):
- ✅ Korrekte Klassifikation in drei Fälle
- ✅ Korrekter Vergleich (exit_reason + pnl_points, 1e-9-Toleranz)
- ✅ Saubere JSON-Ausgabe (machine-readable)
- ✅ Lauffähig in beiden Modi (--day, --days)
- ✅ Fail-soft gegen fehlende Tabellen / fehlende Bars
- ✅ `mode=ro` (Produktions-DB-Schutz)
- ✅ Live-Verify in Mini-Session 23 empirisch erbracht (332 trades in 14 Tagen)

**Das ist die strukturelle Antwort auf P12.5:** nicht mehr "ist das Archiv aktuell?" sondern
"deckt das Archiv das Trade-Fenster dicht genug ab, mit Substrat-Vergleich?". Block C3 macht
die Beschaffungslücke **sichtbar** — sie fixt sie nicht (Beschaffung ist Phase-13-Block-C2-Recurring-
Aufgabe, nicht Phase-14-Territorium), aber sie macht sie **messbar**.

---

## §4 Was nicht funktioniert (Phase-14-Drift, B3)

**`instrument_source_availability.history_min_days` ist eine Behauptung, keine Messung.**

Die Tabelle wurde von Phase-14 so designed, dass die Quell-Profile (`derived`, `recorded`,
`registry`) die Verfügbarkeit **deklarieren**, aber die Tabelle tut nichts, um die
**tatsächliche** Substrat-Coverage gegen die Deklaration zu prüfen. Konkret:
- 8 IG-Rows mit `status='ok', history_min_days=30` (Versprechen: 30 Tage Historie)
- Realität: 0 von 8 Rows haben 30 Tage Bars im Archiv
- Realität: 3 von 8 Rows haben 0 Bars überhaupt
- Realität: 5 von 8 Rows haben je 1 Tag Bars

**Konsequenz für Konsumenten:** wenn ein Konsument `instrument_source_availability` liest und
`prefer='ig'` setzt (= nimm die IG-Zeile), bekommt er eine Zeile mit `status='ok'` zurück und
**keinen Hinweis**, dass die IG-Spalte im Archiv leer ist. Erst der Source-Delta-Lauf zeigt
die Lücke (276/332 trades `available_but_empty`).

**Dieser Drift ist genau das, was Phase-15 lösen muss** — die V4-Reihe hat schon einen
"Vor-der-Tabelle-stehende-Validierungs-Schicht"-Vorschlag, der jetzt empirisch verstärkt
wird. Konkret: ein `instrument_source_availability.last_actual_bar_utc` + ein Cross-Check
"wenn `last_actual_bar_utc < now - 24h` UND `status='ok'`, dann logge WARNING und setze
`status='stale'`". Das ist **kein Phase-14-Territorium** (Phase-14 ist die Tabelle selbst,
nicht die Validierung), sondern Phase-15 (V4: Sophisticated/Optional).

**Aber:** Phase-14 kann den Drift **frühzeitig signalisieren**. Die Tabelle hat bereits ein
`last_verified_utc`-Feld — die Frage ist, ob dieses Feld "Discovery hat die Zeile aus
instrument_universe abgeleitet" (heute) oder "Recorder hat für diese Zeile Bars
geschrieben" (Ziel) bedeutet. Heute ist es das erste.

---

## §5 Empfohlene Entscheidungen (für Phase-14 D5 + Phase-15-Plan)

### §5.1 Phase-14 D5-Handover

**Vorschlag (Nikinger-bestätigung ausstehend):** **TEILWEISE freigeben**.

- **Architektonische Freigabe:** ✅ Phase-14 ist fertig — die Tabelle existiert, Discovery
  arbeitet, Source-Delta funktioniert, D1–D20 alle gelockt. Phase 15 kann starten.
- **Operative Freigabe:** ⏸️ Vorbehaltlich — die IG-Spalte der Tabelle ist unzuverlässig,
  bis Phase-13 die Recorder-Mapping-Initiative abgeschlossen hat (Phase-13-Code, nicht
  Phase-14-Code).

**Im Phase-14-Phasenkopf wäre zu vermerken:**
> "D5-Closeout-Handover — architektonisch freigegeben; operativ vorbehaltlich der
> Phase-13-Recorder-Mapping-Initiative. Beweiswoche-Befund 2026-08-31 zeigt IG-Substrat-
> Inkonsistenz (`history_min_days=30` Lüge, 13-Tage-Lücke seit 2026-08-18); Phase-14-Tabelle
> funktioniert wie designed, aber die Validitäts-Lücke ist Phase-15-Territorium."

### §5.2 Phase-13 Folge-Initiative (Recorder-Mapping-Bug)

Der Phase-13-Recorder läuft (PID 7711, Mini-Session 21 verifiziert), schreibt aber seit
2026-08-18 15:41 UTC **keine IG-Bars mehr**. Hypothesen (zu prüfen in der Phase-13-Folge-Session):
1. IG-Stream disconnected seit 2026-08-18 Abend (Tagesende-Close-Verhalten, nie
   wieder-verbunden am nächsten Morgen)
2. IG-Spalte in `bars` wird vom Recorder gar nicht befüllt (Source-Filter-Bug — Recorder
   schreibt nur LS, yF, capital, aber IG nicht)
3. IG-Lightstreamer-Pfad ist seit B0.5 tot (Tick-Aggregation statt CHART), und die
   Tick-Aggregation schreibt nicht in `bars` (separater Stream ohne Bar-Service-Wiring)

Diese Hypothesen sind alle Phase-13-Territorium und sollten in einer eigenen Mini-Session
verifiziert/gefixt werden. Nicht in diesem Doc.

### §5.3 Phase-15-Plan-Session (V4 — Council / Handover / Reward-Reform / Force-Trigger / Instinct-ECC)

**Aufnahme in Phase-15-Plan (Empfehlung):** die V4-Reihe hat schon einen
"Quellen-Vertrauens-Modell"-Vorschlag. Mit dem heutigen Befund wird dieser Vorschlag
**empirisch verstärkt**:
- Konkrete Forderung: jede `status='ok'`-Zeile in `instrument_source_availability` braucht
  eine **tatsächliche** Substrat-Coverage-Messung (z. B. `bars.count(* WHERE epic=? AND source=? AND ts_utc >= now - 7d)`) als Hintergrund-Task.
- Konkrete Forderung: bei `last_actual_bar_utc < now - 24h` automatische Status-Degradation
  auf `stale` oder `empty` (heute gibt es diese Status-Werte schon im Vokabular von
  Phase 9 — `DS_STALE_SOURCE`, siehe P14-CLAUDE.md §"Live-Blocker B1")
- Konkrete Forderung: Konsumenten, die `prefer='ig'` lesen, bekommen einen
  **klaren Status**, der das Trade-Fenster mit der tatsächlichen Substrat-Lage abgleicht.

**Diese Forderungen sind Phase-15-Plan-Session-Territorium**, nicht Phase-14-Code. Der
heutige Befund ist die Begründung, nicht die Implementation.

---

## §6 Empfehlung an den Nikinger (zur Abstimmung)

1. **Findings-Notiz akzeptieren** ✅ — diese Notiz (`PHASE13_BEWEISWOCHE_FINDINGS_2026-08-31.md`)
   ist die offizielle Beweiswoche-Auswertung; im Phase-13- und Phase-14-Phasenkopf mit
   Verweis-Zeile einhängen.
2. **D5-Handover-Status:** **TEILWEISE freigeben** (architektonisch ja, operativ nein) — Phase-14
   ist strukturell fertig, aber die IG-Substrat-Lüge muss vor dem nächsten Beweis-Lauf
   gefixt werden.
3. **Phase-13-Folge-Session (Recorder-Mapping-Bug):** priorisieren in der nächste Session,
   1-2 Stunden (Recorder-Initiative, Hypothesen aus §5.2 verifizieren, ggf. Recorder-Fix).
4. **Phase-15-Plan-Session:** jetzt vorbereiten (das heutige Befund-Material geht direkt in
   den V4-Plan als empirische Begründung der Quellen-Vertrauens-Forderung).

**Push-Freigabe:** diese Notiz + 1 Phasenkopf-Update (Phase 13 + Phase 14) sind 2-3 Commits,
pushbar nach Nikinger-Sign-off.

---

## §7 Cross-Refs

- **Block-C-Re-Plan** [`../../docs/concepts/phase13_c_block_c_replan.md`](../../docs/concepts/phase13_c_block_c_replan.md)
  §0 "drei neu nachgemessene Befunde tragen die Phase: IG liefert für eine Forward-Epic seit
  einem Monat tote Historie mit ok=True" — **empirisch vollständig bestätigt**.
- **Phase-13-CLAUDE.md** Modul-Tabelle `source_delta.py`-Zeile — Status "✅ C3 — committed,
  7 Tests — final (Block C geschlossen 2026-08-22)" bleibt gültig; **das Tool funktioniert,
  die Phase-13-Substrat-Schicht darunter ist es, die den Drift zeigt**.
- **Phase-14-CLAUDE.md** Modul-Tabelle `instrument_source_availability`-Zeile — "✅ A2" bleibt
  gültig (Tabelle ist da); **neu hinzuzufügen: Findings-Vermerk 2026-08-31**.
- **Mini-Session-21-Findings (Phase-14-CLAUDE.md Z. 235)** — "🟡 Doc-Rotation-Hygiene: ...
  für die nächste Session: Doc-Rotation als Pre-Commit-Hook-Schritt 2" — **erledigt in
  Mini-Session 22** (P14-F Schritt 1+2+3, Commits 94e0c35/d32e93a/8fe439c/8db5a1c).
- **Mini-Session-21-Findings (Phase-14-CLAUDE.md Z. 235)** — "Hook-Installer (tracked) —
  Skript gebaut, Operator-seitige Installation fertig, die **tracked**-Variante (Option 1/3)
  bleibt offen" — **erledigt in Mini-Session 22** (Commit 8fe439c, `scripts/install_hooks.sh`).

---

## §8 Nachtrag 2026-08-31 (Mini-Session 24, Nikinger-Entscheidung Pfad C)

> **Operator-Entscheidung:** Nikinger hat nach Vorlage der drei Pfade A/B/C in
> Mini-Session 24 Pfad C gewählt. Pfad A/B bleiben offen — Pfad A als P15-V4-Kandidat
> (siehe §8.2), Pfad B als Phase-14-Schema-Migration (aufgehoben solange C gilt).

### §8.1 "by design"-Vermerk (Pfad C)

Die in dieser Notiz dokumentierten Befunde B1/B2/B3 bleiben **empirisch korrekt**,
bekommen aber eine **andere Lesart**:

- **B1 (IG-Bars-Lücke 2/13 Tage)** ist **kein Defekt**, sondern **Architektur-konform**:
  die Phase-13-Architektur sieht **strukturell keine kontinuierliche `source='ig'`-Beschaffung**
  vor. IG ist als **S4-Rettungspfad** (GapRescue, `phase13_live_data/live_data/rescue.py`,
  Default AUS per Phase-13-CLAUDE.md, Budget-bound 10 000 IG-Punkte/Woche) designed.
  Die heutigen 2 IG-Tage (17.07. + 18.08.) stammen aus Operator-gefahrenen
  GapRescue-Einmal-Runs (vermutlich B1a-Probe + Block-C-Live-Verify), nicht aus
  einer Pipeline.
- **B2 (53.6 % Divergenzrate am 2026-08-18)** ist weiter ein **echter Befund** — aber
  eingeschränkt auf den einen Tag mit IG-Bars; ab 2026-08-19 systematisch nicht
  messbar (keine IG-Bars, kein Vergleich). **Nicht** ein Beweis für eine
  kontinuierliche Drift; **ein** Stichproben-Befund an einem Operator-Run-Tag.
- **B3 (`last_verified_utc` reflektiert Discovery-Ableitung, nicht Substrat)** bleibt
  ein **struktureller Drift in der Tabelle** — der Discovery-Process aktualisiert das
  Feld aus `instrument_universe` (= trivial wahr), nicht aus `bars.sqlite` (= echte
  Substrat-Validität). **Aber:** solange Pfad C gilt und IG als "GapRescue-Pfad"
  verstanden wird, ist die Tabelle semantisch korrekt (sie zeigt
  "Discovery hat diese Epic bestätigt", nicht "diese Quelle liefert heute Bars").

**Konsequenz für Phase-14 D5-Handover (Mini-Session 23):** die Entscheidung "architektonisch
freigegeben, operativ vorbehaltlich Phase-13-Recorder-Mapping-Initiative" wird
**relativiert** — der "operativ vorbehaltlich"-Teil entfällt, weil die Initiative als
"Architektur-konform" entlarvt ist. **Phase-14 D5-Handover ist jetzt komplett
freigegeben** (kein Vorbehalt).

### §8.2 P15-V4-Kandidatenliste (offen, nicht in Mini-Session-24-Scope)

Drei Items wandern explizit in die **P15-V4-Plan-Session** (V4 = Council, Handover,
Reward-Reform, Force-Trigger, Instinct-ECC):

1. **Pfad A — Operator-S4-Aktivierung** (~2-3h Phase-13-Code):
   - Wenn eine echte IG-Coverage für Divergenz-Vergleich gebraucht wird:
     GapRescue-Skript als Operator-Tool mit Schedule (z. B. täglich 17:30 UTC).
   - IG-Budget-Kontingent ist 10 000/Woche — `enable_divergence_sampler` verbraucht
     ~120/Woche (~1.2 %); ein täglicher 1-Tages-Backfill der 8 IG-Epics verbraucht
     weitere ~560/Woche (~5.6 %); beides zusammen **innerhalb der 10 000/Woche**.
   - Frage: ist die zus-liche Coverage den Budget-Preis wert? **V4-Entscheidung.**

2. **Pfad B — Schema-Reinterpretation** (~1-2h Phase-14-Code, **aufgehoben solange C gilt**):
   - Neuer `status='gap_rescue_only'`-Wert in `instrument_source_availability`,
     IG-Rows umklassifiziert. Semantisch sauberer, aber **Pfad C hat sich als
     ausreichend erwiesen** — V4 kann entscheiden, ob das später nochmal relevant wird.

3. **P15-Quellen-Vertrauens-Modell** (siehe Findings §5.3, jetzt mit Befund-Inversion
   neu gerahmt):
   - Die ursprüngliche V4-Forderung war "jede `status='ok'`-Zeile braucht eine
     **tatsächliche** Substrat-Coverage-Messung, sonst automatische Degradation auf
     `stale`/`empty`". Mit Pfad C wird das **weniger dringend**: `status='ok'` heißt
     "GapRescue-Pfad verfügbar", was eine andere Kategorie ist als "Live-Coverage".
     **V4 kann das** als "Quellen-Verfügbarkeits-Modell" (was die Tabelle heute ist)
     **statt Quellen-Aktualitäts-Modell** (was der ursprüngliche Vorschlag war)
     framen. Konkrete Frage: soll V4 die `last_verified_utc`-Semantik von
     "Discovery-Ableitung" auf "Bars-Substrat-Validierung" umstellen? **V4-Entscheidung.**

### §8.3 Update-Liste (für die nächste Session / P15-Plan)

- **Pfad C ist umgesetzt** durch diesen Nachtrag — keine Code-Änderung, nur Doku.
- **P15-Plan-Session-Material** ist um drei konkrete Items (§8.3) erweitert — die
  V4-Plan-Session kann direkt mit der Quellen-Vertrauens-Diskussion starten.
- **Phase-13 ist close-out-fähig** mit Pfad C + diesem Nachtrag — eine eigenständige
  Closeout-Session ist jetzt **möglich** (siehe auch Phase-12-Closeout als Pattern).

---

**>Updated:** 2026-08-31 (Mini-Session 24, Pfad-C-Entscheidung, §8 Nachtrag angehängt;
  Header `updated:` von `2026-08-31` auf `2026-08-31 (+ §8 Pfad-C-Nachtrag 2026-08-31, Mini-Session 24)`).

---

> **Stand:** 2026-08-31 ~10:00 UTC, Mini-Session 23 (Phase-13-Beweiswoche-Auswertung).
> **Nächste Aktion:** Findings-Notiz in Phase-13- und Phase-14-Phasenkopf referenzieren,
> dann Phase-13-Recorder-Initiative (Hypothesen-Test) als nächste Session.