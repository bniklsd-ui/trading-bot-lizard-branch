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
| *(cross-phase)* `data_foundation/coverage.py` | `assess_window` / `WindowCoverage` | ⬜ Block A1 |

---

## Session stopped — 2026-08-18 (Session 3: Block A1 — assess_window + WindowCoverage)

> **Auftrag:** Step A1 (Plan §6 A1, §5.1). Reine Funktion, kein I/O, kein Cross-Phase-Import.

### Completed

1. **`data_foundation/coverage.py` (NEU, 99 Zeilen)** — `WindowCoverage` (frozen dataclass:
   `covered`, `present`, `expected`, `ratio`, `largest_gap_min`, `reason`) und
   `assess_window(timestamps, start_utc, end_utc, resolution_minutes, *, min_ratio, max_gap_min)`
   strikt nach §5.1-Signatur. Reason-Priorität `empty > gap > sparse` (§5.1).
   Konstanten `MIN_WINDOW_RATIO=0.90` / `MAX_WINDOW_GAP_MIN=5` sind die gelockten v1-Knöpfe
   (Plan §9.14: Block A misst die reale Verteilung, justiert danach). `_parse` aus
   `archive.py:222-227` **lokal** dupliziert (Phasen-Isolation, Plan §6 A1). Ränder fließen in
   die Gap-Rechnung ein — sonst wären Tests 4/5 (Loch am Fensteranfang/-ende) blind.
2. **`tests/test_coverage.py` (NEU, 12 Tests)** — die 9 Pflicht-Tests aus §6 A1 wortgleich:
   volles Fenster, leer, **Mitten-Loch** (F3-Fang, ratio > min_ratio trotzdem reason='gap'),
   Rand-Lücken, gleichmäßig dünn, `gap` > `sparse`, `expected==0` ohne `ZeroDivisionError`,
   Duplikate zählen einmal. Plus 3 defensive: Timestamps außerhalb des Fensters ignoriert,
   Defaults halten die Modul-Konstanten, `WindowCoverage` ist `frozen`.
3. **`phase12_data_foundation/README.md`** — Modul-Tabelle um `coverage.py` ergänzt (Verweis auf
   Phase 13 §6 A1). Sonst nichts geändert.
4. **Rotation:** Session-2-Block verbatim nach `SESSIONS_ARCHIVE.md` verschoben.

### Verified

- `pytest phase12_data_foundation/tests -q` → **135 passed** (Baseline 123 + 12 hinzu, 0 Regressionen).
  Phase-12-Suite allein, geteiltes Venv `phase1_broker_wrapper/.venv`.
- Akzeptanz A1 wortgleich erfüllt: *"die neun Tests grün; `assess_window` hat null Aufrufer"*.
- `grep -n "_covers_tail\|MIN_WINDOW_COVERAGE\|_ig_provider" phase12_data_foundation/`: alle drei
  noch vorhanden — A1 fasst sie nicht an, **A2** löscht sie (L2).
- `assess_window` hat 0 Produktions-Aufrufer (gegrept); Verdrahtung kommt in A2
  (`BarService.get_window`-Body-Ersatz) und A3 (Tracker-Naht in `paper.py`).

### Next

- **Step A2** (Plan §6, Zeile 604): `BarService.get_window` zu einer reinen Archiv-Lesung kürzen
  (Verbatim-Anker-Tabelle in §6 A2 prüfen, Zeilen können sich verschoben haben). L12-Test
  `test_get_window_never_fetches` (IG-Provider wirft `AssertionError`) ist die **strukturelle
  Kostenzusicherung** — der Kernpunkt von L12. **Pause für Nikinger-Bestätigung** vor Cross-
  Phase-Edits in A3 (das ist die nächste Stufe, die `paper.py` und `wiring.py` berührt).

### Note

- Netto-Diff: +2 neue Dateien + 1 README-Zeile + 1 Session-Block-Tausch. Kein Eingriff in
  laufende Komponenten. `data_foundation` ist cross-phase-Paket (Phase 12), `live_data`
  importiert es (L11) — der neue Modul liegt also **in** Phase 12, **benutzt von** Phase 13.
- Die zwei bisherigen Live-Unbekannten aus A0.0 sind gelöst (Modell-ID `MiniMax-M3[1m]`,
  Bearer-Header, Subscription-Key-Tausch), siehe Session-2-Block.

### Open questions / blockers

- **Kein technischer Blocker für A2.** Bot steht sicher, Recorder sammelt kostenlos weiter.
- **A2 ist der Lösch-Step** (L2): danach kauft der Tracker-Pfad **per Konstruktion** keine
  IG-Punkte mehr — der strukturelle Schnitt, den Closeout §1 empfohlen hat. Genau da, **nicht
  jetzt**, ist der Moment, das mit dem Nikinger kurz zu bestätigen, bevor A3 (die Cross-
  Phase-Naht) anläuft.
- **`main` liegt jetzt 6 Commits vor `origin/main`** (inkl. dieses Commits) — Push bleibt
  bewusste Einzelfreigabe des Nikinger.
