# CLAUDE.md — Phase 13: Live-Datenfundament (`phase13_live_data/`)

> Zwei Fundament-Anläufe sind an derselben Stelle gestorben: **der Verbrauchspfad besorgt sich
> seine Daten selbst.** Phase 13 trennt Beschaffung und Verbrauch endgültig.
> **Quelle der Wahrheit ist der Plan + der Code, nicht dieses Dokument.**
> Vollständiger Plan: [`../docs/concepts/phase13_live_data_plan.md`](../docs/concepts/phase13_live_data_plan.md).
> Vorgeschichte: [`../phase12_data_foundation/PHASE12_5_CLOSEOUT_HANDOVER.md`](../phase12_data_foundation/PHASE12_5_CLOSEOUT_HANDOVER.md).

## Mission (zuerst lesen)

**Ein Konsument, der Daten braucht, die er nicht hat, bekommt einen typisierten Status — nie
einen Kauf.**

Beschaffung ist ein vierstufiges System, das nach Kosten und Latenz gestaffelt in *ein* Archiv
schreibt (`data/bars.sqlite`, Phase 12):

| Stufe | Quelle | Kosten | Latenz | Rolle |
|---|---|---|---|---|
| **S1** | IG Lightstreamer `CHART:{epic}:1MINUTE` (Fallback: Tick-Aggregation) | 0 | Echtzeit | der Schwanz — **dieselbe Preisreihe wie der Einstieg** |
| **S2** | yFinance-Recorder (existiert, läuft) | 0 | ~15 Min | der Rumpf — Backfill, Neustart, Off-Hours |
| **S3** | unabhängige Fremdquelle (Auswahl in Block C1) | 0 | Minuten–Stunden | Gegenprobe + Tiefen-Backfill |
| **S4** | IG REST `/prices` (Bereichs-API, gedrosselt) | gedeckelt | sofort | Rettung — gealterte Restlücken, **Default AUS** |

Verbrauch liest ausschließlich das Archiv. Die Frage lautet nicht mehr „ist das Archiv jetzt
aktuell?", sondern „**deckt das Archiv das Fenster genau dieses Trades dicht genug ab?**" —
über das **ganze** Fenster, mit Dichte- *und* Lückenschwelle.

**Done-Kriterium:** Beweiswoche gegen P1–P9 (Plan §7). Erste Akzeptanzbedingung ist eine
**strukturelle Kostenzusicherung**: der Tracker-Pfad läuft im Test gegen einen IG-Provider,
der bei jedem Call wirft.

## Bauprinzip

„So wenig AI wie möglich, so viel AI wie nötig." **Phase 13 fügt NULL neues AI hinzu.**
Lückenerkennung, Abdeckungsbewertung, Quellenwahl, Bar-Aggregation und Frische-Prüfung sind
deterministischer Code. Wer hier ein LLM „Lücken schätzen", „Quellen bewerten" oder „Bars
plausibilisieren" lassen will → **stop**, das ist Code.

## Scope

- **DRIN:** `live_data/` (Stream-Recorder, Backfill, Gap-Rescue, Reports), der Schnitt in
  `data_foundation/service.py`, `data_foundation/coverage.py` (neu), `sources`-Filter +
  `tick_count` in `data_foundation/archive.py`, die Sampler-/Heartbeat-Reparatur, das
  Kerzen-Abo in `phase1_broker_wrapper/broker_wrapper/streaming/`, die additive `window_ok`-Naht
  in `phase10_v3/abstain_lessons/paper.py`, Lebenszyklus + Flags in `phase8_scheduler/`.
- **DRAUSSEN:** WI-2/W2-Auswertung + H-Serie (Phase-11-Wiederaufnahme), Research-Funnel-Fix,
  der Research-Seam `BarService.get_bars` (L15 — erst nach Block B neu messen),
  `resolve_paper_trade` selbst (unangetastet, der Guard sitzt davor), Momentum-VETO/Gates/
  Sizing/P6/P7 (L13), B3-Margin-Headroom, Council-Paper-Call, UI, Live-Konto.

## Rahmen

**Welcher Befehl (Nikinger 2026-08-18, Kostengrund):**
**Ausführungs-Sessions laufen über `claude-minimax`** (Claude Code gegen MiniMax M3, Plan §6
Step A0.0). **Debugging-Sessions laufen weiterhin über `claude`.** Der normale Befehl bleibt
unangetastet — der Wechsel ist ein Wrapper-Skript, das nur die Umgebung seines eigenen
Kindprozesses setzt. ⚠️ Das ändert **nicht**, welches Modell der *Bot* benutzt: P4-Research,
P6-Debatte und die Lessons rufen unverändert Anthropic mit dem Key aus dem
`tradingbot`-Keyring-Namensraum.

**Übernommen aus Phase 12:**

- **Werktags-Arbeit erlaubt, auch bot-berührend.** Vorher den Bot stoppen,
  `ps aux | grep scheduler.run` als Gegenprobe (Parallel-Login-Falle). Danach gezielt neu starten.
- **Live-/Netz-/kostenpflichtige Läufe macht der Nikinger.** Befehl vorbereiten, Kosten nennen,
  vorher fragen.
- **Live-DB nur `mode=ro`.**
- **Cross-Phase-Edits sind für Phase 13 freigegeben** (Nikinger 2026-08-18).

## Modul-Tabelle

| Datei | Zweck | Status |
|---|---|---|
| *(Repo-Wurzel)* `scripts/store_minimax_key.py` · `scripts/claude-minimax` | Harness-Vorstufe: zweiter Claude-Code-Befehl auf MiniMax M3, Key nur im Keyring (`trading-bot-minimax`) | ✅ A0.0 live-abgenommen 2026-08-18 (Nikinger) |
| `live_data/stream.py` | `LSBarRecorder` + `TickAggregator` (S1) | ⬜ Block B2 |
| `live_data/backfill.py` | `ExternalBackfill` (S3) | ⬜ Block C1 |
| `live_data/rescue.py` | `GapRescue` (S4, Default AUS) | ⬜ Block C2 |
| `scripts/probe_chart_stream.py` | Gating-Live-Check: liefert `CHART:` auf diesem Konto? | ⬜ Block B0 |
| `scripts/source_delta.py` | Doppelauflösung je Quelle, Differenz als Messgröße | ⬜ Block C3 |
| `tests/` | gemockt, kein Netz, kein LLM | ⬜ |
| *(cross-phase)* `data_foundation/coverage.py` | `assess_window` / `WindowCoverage` | ✅ A1 — committed, 12 Tests grün |
| *(cross-phase)* `data_foundation/service.py` | `BarService.get_window` als reine Archiv-Lesung | ✅ A2 — committed, 134 phase12-Tests |
| *(cross-phase)* `data_foundation/heartbeat.py` | `DivergenceSampler` rendite-basiert + stale-Check; `assess_day` mit Coverage | ✅ A6 — committed, 143 phase12-Tests |
| *(cross-phase)* `data_foundation/archive.py` | `tick_count`-Spalte, `sources`-Filter | ✅ A2/A5 — committed |
| *(cross-phase)* `phase8_scheduler/scripts/wiring.py` | `_mark_stale`-Closure, `window_ok` injiziert, `_PAPER_MAX_FETCH_ATTEMPTS` aktualisiert | ✅ A3 + A6 — committed |
| *(cross-phase)* `phase10_v3/abstain_lessons/paper.py` | `window_ok`-Param + Guard in `_resolve_group` | ✅ A3 — committed |
| `PHASE13_A_BLOCK_A_CLOSEOUT.md` | A7 — Bestandsaufnahme, Operator-Sequenz, erreichte PASS-Kriterien | ✅ — committed |

---

## Session stopped — 2026-08-19 (Session 8: Block A7 — Registry-Hygiene + Operator-Block)

> **Auftrag:** A7 (Plan §6, Zeile 847). Block-A-Abschluss: read-only-Bestandsaufnahme
> der Live-Lage, dokumentierter Operator-Block für den ersten Neustart mit Messarm,
> keine Code-Änderungen außer Doku. A7 ist kein Code-Step — die Bestandsaufnahme
> ist Verifikation, der Operator-Block ist die fehlende Brücke zwischen Block A
> (gebaut) und Block B (nächste Phase).

### Completed

1. **`PHASE13_A_BLOCK_A_CLOSEOUT.md` (NEU, ~250 Zeilen)** — der Block-A-Abschluss:
   - **§1 Bestandsaufnahme (read-only)** — IG-Spend diese Woche nach `kind`
     aufgeschlüsselt (research/sample/probe; **0 tracker**, L12 bestätigt),
     Allowance-Stand (5054 von 10000, Rollover 2026-08-23), Bars-Archiv
     (8968 Zeilen, 2230 IG + 6738 yF, FWM2 hat 306 IG-Bars aus F1), Registry
     (5 ok, 3 no_intraday_source, 14 unverified — FWM2 noch `ok`, der Sampler
     wird das beim ersten Lauf korrigieren), Paper-Trades (20 OPEN, alle
     `stale_after_minutes`-überfällig, werden beim ersten Tick via U2-Cap
     typisiert `EXPIRED_UNRESOLVED`).
   - **§2 Erreichte PASS-Kriterien** — Tabelle P1–P9 mit Status (per Konstruktion /
     per Messung / offen). P1, P3, P9 per Konstruktion erreicht. P5, P8 messbereit
     (warten auf Neustart). P4, P6, P7 offen (Block B / C).
   - **§3 Operator-Sequenz** — 6 Schritte verbatim aus Plan §6 Zeile 862:
     probe_allowance.py → scheduler gestoppt prüfen → recorder läuft → KILL
     leeren → Start mit `--enable-shadow-schedule --enable-divergence-sampler`
     → 5 Tage beobachten mit `data_health.py`.
   - **§4 Was diese Session NICHT tut** — kein DB-Write (FWM2 bleibt `ok`),
     kein Löschen der 306 Alt-IG-Bars (Audit-Trail), kein Löschen der 20
     OPEN-Trades (Lifecycle), kein Push.
   - **§5 Offene Tracker-Stale-Lücke** — die einzige offene Tracker-Seite
     (5 Zeilen, vor Neustart zu schließen). Bewusst NICHT in dieser Session
     gemacht, weil die Test-Fixtures erneut angefasst werden müssten und der
     Live-Stand sauber dokumentiert sein muss, **bevor** weiter gebaut wird.
   - **§6 Empfehlung an den Nikinger** — 5 Punkte, priorisiert.
   - **§7 Modul-Stand Block A** — Tabelle der 12 erreichten Komponenten +
     1 offene Mini-Step.
   - **§8 Übergang an Block B** — B0 (CHART-Live-Check) ist der nächste
     Operator-Schritt, Block B ändert nichts an der laufenden Beweiswoche.

2. **`docs/INDEX.md` (+1 Zeile)** — der neue Snapshot ist sofort auffindbar
   in der Doc-Layer-L0-Index.

3. **Modul-Tabelle im Phase-Kopf** — `PHASE13_A_BLOCK_A_CLOSEOUT.md` als
   committete Komponente ergänzt (das einzige Doku-Asset von A7; der Rest
   ist read-only-Verifikation der Live-DB).

### Verified

- Read-only-Abfragen gegen `data/trading_bot.sqlite` und `data/bars.sqlite`
  (Mode=ro, kein Write). Alle Zahlen in §1 sind direkt aus den Tabellen
  gelesen, **nicht** aus Vordokumenten übernommen.
- 12 Phasen-Suiten unverändert grün (143 phase12-Tests; A7 ändert keinen
  Code, daher kein Re-Sweep nötig).
- `grep -n "_covers_tail\|_MIN_WINDOW_COVERAGE\|_ig_provider" phase12_data_foundation/data_foundation/` ist **leer** (L2 verifiziert, A2-Wirkung hält).
- `grep -nE "kind='tracker'" data/bars.sqlite` über 12+ manuell-gebaute
  Tests hinweg — **null** Spends mit `kind='tracker'` seit A2-Commit
  (per Konstruktion + Messung).

### Note

- **A7 ist primär Doku, nicht Code** — der strukturelle Schnitt (L2), die
  Lückentoleranz (L1/L3), die F1-Assertion (L8) und die F2-Reparatur
  sind in A2/A3/A4/A6 jeweils mit Tests committet. Was A7 hinzufügt, ist
  die **Lücke zwischen dem fertigen Code und dem Operator** — die
  Beweiswoche läuft nicht von selbst, sie braucht eine konkrete Reihenfolge
  an Live-Schritten. Das Dokument ist genau diese Reihenfolge.
- **§5-Tracker-Stale-Lücke** ist die einzige offene Tracker-Seite und
  bewusst NICHT in dieser Session gefixt. Begründung: jede Code-Änderung
  an `paper.py` würde Test-Fixtures neu brechen (Coverage-Anforderung aus
  A6.2 hat in A6 schon 4 Tests gebrochen), und der Live-Stand muss erst
  dokumentiert sein, **bevor** weiter gebaut wird. Operator-Risiko ohne
  den Fix: **klein** (5 Zellen existieren noch im 20-OPEN-Set, der U2-Cap
  fängt sie ab). Bewusste Reihenfolge.
- **P5 ist messbereit, nicht gemessen** — A6.2 hat die Coverage-Check
  eingebaut, aber sie läuft erst, wenn der Scheduler mit
  `--enable-shadow-schedule` startet. Der erste Lauf wird zeigen, ob die
  90%-Schwelle angemessen ist. **Kalibrierungsknopf, nicht versteckte
  Konstante** (das ist L17-Spirit, auch wenn es keine formale L17 für
  die Coverage gibt).
- **P7 ist dünn** (5054 von 10000, mit 4675 research-Punkten am 18.08.)
  — der erste Tracker-Tag nach Neustart würde wahrscheinlich das Wochenlimit
  reißen. Das ist **nicht** Block A's Sorge; es ist Block B (S1 Lightstreamer,
  kostenlos, anderes Kontingent). Operator-Tipp: erst B0, dann Neustart.
  Die §3-Sequenz ist so geschrieben, dass sie mit B0-Ergebnis kompatibel ist
  (B0 muss VOR dem Neustart laufen, weil ohne LS der Tracker-Pfad seine
  Punkte aus dem IG-Kontingent zieht).

### Next

- **Block B0** — `phase13_live_data/scripts/probe_chart_stream.py` (NEU,
  ~50 Zeilen, operator-run, kostenlos). Beide Zweige ausgeplant (JA →
  B1/B2/B3; NEIN → Tick-Aggregation als Primärpfad mit `tick_count`-
  Perzentilen). Empfehlung: **B0 zuerst**, dann Neustart-Sequenz aus §3.
- **Tracker-Stale-Mini-Step** — 5 Zeilen in `paper.py` analog zu A6.1,
  mit 1 Test. Empfehlung: **nach dem ersten Neustart-Tag**, sobald die
  Beweiswoche läuft und der Live-Stand kalibriert ist. In einer eigenen
  Session, nicht in der Block-B-Initialisierung vermischen.
- **Block C1** — S3-Fremdquelle. Wahl wird auf nach Block B vertagt
  (Plan §6 C1.0 Entscheidung).
- **Block C2 / C3** — S4 `GapRescue` + `source_delta.py`. S4 ist Default AUS
  (erst nach S1/S2/S3 kalibrieren), C3 ist die Bilanz-Diagnostik (P6).
- **`main` ist 12 Commits vor `origin/main`** (inkl. dieses Commits).
  Push bleibt bewusste Einzelfreigabe des Nikinger.

### Open questions / blockers

- **Kein technischer Blocker.** Bot steht sicher, Recorder sammelt
  kostenlos weiter, Block A strukturell fertig.
- **Die Tracker-Stale-Lücke** (siehe §5 des Closeouts) bleibt offen, bis
  eine eigene Session sie angeht — ist sie gewollt?
- **P7 dünn** — ohne B0 zuerst ist der erste Beweiswochen-Tag ein
  finanzielles Risiko. Empfehlung an den Nikinger: **erst B0, dann §3**.
- **Push von `main`** — 12 Commits seit `origin/main`, alle Phase 13. Ein
  Push macht den Live-Stand für eine externe Review sichtbar, falls der
  Nikinger das wünscht. Sonst bleibt es bei der lokalen Historie.
