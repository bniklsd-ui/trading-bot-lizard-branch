---
status: snapshot
purpose: Phase-13-Closeout-Handover (2026-08-31) — Phase 13 (Live-Datenfundament) ✅ **abgeschlossen**. Code-complete (Blöcke A + B + C) + Beweiswoche ausgewertet (Mini-Session 23) + Pfad-C-Entscheidung (Mini-Session 24) + Befund-Inversion (kein "Recorder-Mapping-Bug" — Phase-13 sieht strukturell keine kontinuierliche `source='ig'`-Beschaffung vor). Phase-14 D5-Handover ist damit komplett freigegeben (kein operativer Vorbehalt mehr). Read-only-Inventur, jeder Datenpunkt selbst nachgemessen.
read-when: vor jedem Plan, der Phase 13 wieder aufnimmt; vor jedem Re-Read der Beweiswoche-Befunde; vor jeder Frage „ist Phase 13 eigentlich fertig?"; vor jedem Code-Edit an `live_data/`, `data_foundation/`, `phase10_v3/abstain_lessons/paper.py`, oder `phase1_broker_wrapper/broker_wrapper/streaming/`
detail: L3
up: ./CLAUDE.md
down:
  - ./PHASE13_BEWEISWOCHE_FINDINGS_2026-08-31.md  # 📕 Beweiswoche-Befund (Mini-Session 23) + §8 Pfad-C-Nachtrag (Mini-Session 24) — die Quellen für §3/§4 dieses Closeouts
  - ./PHASE13_A_BLOCK_A_CLOSEOUT.md              # 📕 Block-A-Closeout (2026-08-19, A7-Bestandsaufnahme, Operator-Sequenz, A-PASS-Items)
  - ../docs/concepts/phase13_live_data_plan.md    # 📕 Mutterplan, gelockte L1–L17 (unangetastet)
  - ../docs/concepts/phase13_c_block_c_replan.md  # 📕 Block-C-Re-Plan + Phase-14-Handoff (2026-08-22)
  - ../docs/concepts/phase14_discovery_concept.md # 📕 Phase-14-Concept (drei Bausteine, sieben offene Fragen)
  - ../phase12_data_foundation/PHASE12_CLOSEOUT_HANDOVER.md  # 📕 Pattern-Vorbild für diese Closeout-Struktur
  - ../phase12_data_foundation/PHASE12_5_CLOSEOUT_HANDOVER.md # 📕 die Lehre, die Phase 13 hervorgerufen hat
  - ../phase12_data_foundation/PHASE12_PREPROOF_HANDOVER.md   # 📕 Phase-12-Tag-1-Befund
  - ../docs/architecture/phase13_live_data.svg    # 📕 diese Phase, bildlich (1080×1080)
  - ../docs/architecture/phase12_5_failure.svg    # 📕 die Vorgeschichte (Fehlerbild, gegen das Phase 13 gebaut wurde)
  - ../phase14_discovery/CLAUDE.md               # 🔄 die Source-Registry darüber (instrument_source_availability)
  - ./SESSIONS_ARCHIVE.md                        # 📦 rotierte Session-Blöcke (L3)
updated: 2026-08-31
---
# Phase 13 (Live-Datenfundament) — Closeout-Handover (2026-08-31)

> **Autor:** Claude Code, Read-only-Analyse 2026-08-31, **kein** Produktionscode-Edit
> in dieser Session. **Adressat:** die nächste Session an Phase 13 (Folge-Arbeit) oder
> an Phase 14 / Phase 15. **Quelle aller Zahlen:** eigene read-only-Abfragen gegen
> `data/bars.sqlite`, `data/trading_bot.sqlite`, Git-Historie und Live-Sweep —
> **nichts** aus Vordokumenten übernommen, was sich selbst hat prüfen lassen.

---

## §0 BLUF

Phase 13 ist **abgeschlossen**. Code-complete (Blöcke A + B + C, Stand 2026-08-22) +
Beweiswoche ausgewertet (Mini-Session 23, 2026-08-31) + Pfad-C-Entscheidung (Mini-Session 24,
2026-08-31) + Befund-Inversion ("kein Recorder-Mapping-Bug" — Phase-13-Architektur sieht
strukturell keine kontinuierliche `source='ig'`-Beschaffung vor). **53 Phase-13-Commits auf
`origin/main`, 74 Phase-13-Tests grün (heute gemessen), Σ 1703 grün repo-weit, `main` =
`origin/main`.**

**Drei Sätze, die die Phase tragen:**

1. **Beschaffung ≠ Verbrauch.** Vier Stufen (S1 LS-Kerzen / TickAgg → S2 yF-Recorder →
   S3 Capital.com PARTIAL → S4 GapRescue AUS) schreiben in *ein* Archiv
   (`data/bars.sqlite`). Verbrauch liest ausschließlich das Archiv und kauft nie.
2. **Die Abdeckungsfrage gilt dem ganzen Trade-Fenster**, nicht dem Schwanz — mit Dichte-
   *und* Lückenschwelle. Eine Mitten-Lücke erzeugt sonst eine **erfundene** `TIME_STOP`-
   Zeile, die wie ein sauberes Ergebnis aussieht (F3).
3. **Pfad-C-Lesart (Nikinger 2026-08-31, Mini-Session 24):** die Phase-13-Architektur sieht
   **strukturell keine kontinuierliche `source='ig'`-Beschaffung** vor. IG ist als S4-
   GapRescue-Pfad designed (Default AUS, Budget-bound). Die empirisch beobachtete
   IG-Bars-Lücke seit 2026-08-18 ist **Architektur-konform**, **kein Defekt**.

**5-Zeilen-Bilanz (heute 2026-08-31, selbst nachgemessen):**

| Zeile | Stand 2026-08-31 |
|---|---|
| **fertig gestellt** | Blöcke A (Schnitt + `assess_window` + Stale-Assertion + Sampler-Reparatur + Registry-Hygiene), B (Lightstreamer-Code + TickAggregator-Fallback + Scheduler-Lebenszyklus + Token-Rotation), C (Capital.com Pfad B + `GapRescue` S4 + `source_delta.py`) — alle committed auf `main`. Pfad-C-Entscheidung 2026-08-31 (Mini-Session 24) → IG = S4-GapRescue, Default AUS, by-design. |
| **getestet** | **74 Phase-13-Unit-Tests grün** (heute 2026-08-31 gemessen; **+24 seit 2026-08-22-Closeout**, weil `test_backfill`/`test_probe_capital`/`test_source_delta`/`test_capital_discover`/`test_capital_backfill_script` durch Cross-Phase-Phase-14-Block-B2/B3-Edits hinzukamen — Cross-Phase-Test-Zuwachs, nicht Phase-13-Eigenleistung). Σ **1703 grün** repo-weit (Phase-12-Cross-Phase-Tests + root-Tests). |
| **live validiert** | Block A (Strukturtest, `test_get_window_never_fetches` — IG-Provider wirft `AssertionError`, Test grün). Block B0 (Live, negativer Befund 2026-08-19: `CHART:`-Pfad liefert `NO` auf diesem Konto → TickAgg-Fallback aktiv). Block C Pfad B (Live, positiv 2026-08-22: 962 `source='capital'`-Bars in `data/bars.sqlite` — 481 DAX + 481 CAC). Beweiswoche (Mini-Session 23, 2026-08-31: 14-Tage-`source_delta`-Diagnose gegen `data/bars.sqlite` + `data/trading_bot.sqlite` mode=ro, B1/B2/B3 als empirische Befunde). |
| **gepusht und committet** | `main` synchron mit `origin/main`. **53** `phase13:`-Commits auf origin (war im 2026-08-22-Closeout noch **40**; **+13** durch Mini-Sessions 23/24/25: Beweiswoche-Findings-Commit `8aa569f`, drei Doc-Rotations-Commits `4307fc2`/`a1149fe`/`fdca387`, plus Phase-14-Cross-Phase-B2/B3-Phase-13-Edits, Phase-14-E-Phase-12-Reconciliation-Timing-Fix-Edits). 0 unpushed lokal. |
| **nicht erreicht / offen geblieben** | (a) **Beweiswoche P4 (LS-Live) + P5/P7/P8** — **durch Pfad-C-Entscheidung strukturell aufgehoben** (IG ist Default-AUS; Beweiswoche-P4 misst genau den Pfad, der nie aktiv sein soll). (b) **Path C Dukascopy** (für SP35 / IBEX) — bewusst deferred; ToS-Auslegung gilt (Nikinger 2026-08-19); Phase-14 macht daraus eine Quell-Registry-Zeile, kein Code-Migration. (c) **Phase-14-Cross-Phase-Block-B-Effects** — drei P14-Code-Pfade haben Phase-13-Files editiert (`live_data/backfill.py` für `EPIC_MAP`-Entfernung, `scripts/source_delta.py` für Drei-Fälle-Trennung, `scripts/probe_capital.py` für CFD-Filter-Bug-Fix); Tests +50 % seit Block-B-Lock (P14-Cross-Phase-Freigabe via Nikinger 2026-08-22). (d) **Module-Tabelle im Phasenkopf stale** (50 Tests statt 74 in Session 17) — bewusst aufgeschoben in Mini-Session 24 zugunsten der Pfad-C-Entscheidung. |

---

## §1 Architektur-Bild (in einer Zeile)

```
S1 (LS-Kerzen / TickAgg) ┐
S2 (yF-Recorder)         ├──► BarArchive (data/bars.sqlite) ──► Verbrauch (Tracker, Research, DivergenceSampler, Heartbeat)
S3 (Capital.com PARTIAL)  │         │                              kaufen nie, nur Lesen
S4 (GapRescue, AUS)       ┘         └──► Resolution: coverage_assess → gedeckt | offen | typisiert
```

Bildlich: [`../docs/architecture/phase13_live_data.svg`](../docs/architecture/phase13_live_data.svg).

---

## §2 Locks (L1–L17, „don't re-litigate")

| # | Was gelockt ist | Warum |
|---|---|---|
| **L1** | Beschaffung und Verbrauch sind getrennte Subsysteme. | Lehre aus P12.5: 92 % der IG-Käufe lagen schon im Archiv. |
| **L2** | `BarService.get_window` fetcht nicht mehr. Reine Archiv-Lesung. | Der Top-up-Zweig hat 4515 Punkte in 15 Calls verbrannt. |
| **L3** | Abdeckung = Dichte *und* Lückenschwelle, am **ganzen** Fenster. | F3: Mitten-Loch erzeugt erfundene `TIME_STOP`. |
| **L4** | Reihenfolge A → B → C ist gelockt. | A ist eine Löschung (strukturelle Kostenzusicherung), B ist die Live-Kette, C die Fremdquelle. Wer A und B tauscht, verliert die Sicherheits-Stufe. |
| **L5** | LS-Mitschrieb läuft im Scheduler-Prozess. | Kein Token-Sharing, keine Parallel-Login-Falle. |
| **L6** | S1 primär = `CHART:{epic}:1MINUTE`; Fallback = Tick-Aggregation. | B0-Probe 2026-08-19 = NO → TickAgg ist aktiv, CHART-Pfad dormant. |
| **L7** | LS-Kerzen als Mid `(BID+OFR)/2`. | Sonst stille Preisreihen-Mischung im selben `bars`-Table. |
| **L8** | Stale-History-Assertion sitzt am IG-Kaufort, **nicht** in `insert_bars`. | Recorder + Backfill schreiben legitim alte Bars. |
| **L9** | Doppelmessung = Report-Artefakt, nicht zweite Spalte. | Nikinger Q4 2026-08-18. |
| **L10** | `BarArchive.window` bekommt `sources`-Filter. | L9-Report + reparierter Sampler brauchen quellenreine Lesung. |
| **L11** | Neues Verzeichnis `phase13_live_data/`, Paket `live_data`. | `data_foundation` ist Speicherschicht, `live_data` importiert — nie umgekehrt. |
| **L12** | Erste Akzeptanz = strukturelle Kostenzusicherung, kein Zählwert. | Lehre aus P12.5: 123 grüne Tests konnten den Kostenfehler nicht sehen. |
| **L13** | Momentum-VETO bleibt unangetastet. | Root-`CLAUDE.md` Hard Rule. Archiv-Pfad ist Research-/Messdatenpfad, nie Safety-Input. |
| **L14** | Die fünf P12.5-Fixes bleiben. | Live bewiesen korrekt, keiner war die Ursache. |
| **L15** | `BarService.get_bars` (Research-Seam) wird in Block A nicht angefasst. | Soll nach Block B neu gemessen werden. (Stand 2026-08-31: weiterhin offen; Phase-14 macht das nicht, gehört in P15-V4.) |
| **L16** | Phase 13 = Live-Datenfundament, V4 → Phase 14 (jetzt: Phase 15). | Nikinger 2026-08-18, dritte Umnummerierung 2026-08-22. |
| **L17** | Latenzanforderung = datenklassen-spezifisch. Preisreihe live, Begleitgrößen dürfen verspätet sein. | Nikinger 2026-08-18; ordnet S3-Auswahl neu. |
| **L18** *(neu, Mini-Session 24)* | **IG ist Default AUS als Live-Quelle; nur S4-GapRescue-Pfad (operator-getriggert).** | Pfad-C-Entscheidung 2026-08-31; Phase-13-Architektur sieht strukturell keine kontinuierliche `source='ig'`-Beschaffung vor. |

---

## §3 Empirische Befunde (F1/F2/F3, die Lehre hinter den Locks + B1/B2/B3, Beweiswoche-Bestätigung)

### §3.1 Drei Lehren (F1/F2/F3, pre-Beweiswoche)

| Befund | Wirkung | Gelockt durch |
|---|---|---|
| **F1** — `IX.D.IBEX.FWM2.IP` trägt 301 IG-Bars mit `ts_utc` 2026-07-17, `fetched_at` 2026-08-18. IG liefert tote Historie mit `ok=True`. | Sampler war strukturell blind (F2). Stale-Source-Status wurde ergänzt. | L8 + A4 + A6 |
| **F2** — `DivergenceSampler` ankerte das Vergleichsfenster am IG-Bar-TS, kein yF-Fenster wenn IG-TS veraltet ⇒ stiller `return`. | 0 Events bei 12 Samples. Sampler jetzt rendite-basiert. | A6 (compute_return_divergence statt compute_divergence_pct) |
| **F3** — `resolve_paper_trade` filtert nur `ts >= created_utc` und prüft SL unbedingt vor Time-Stop. Mitten-Lücke ⇒ erfundene `TIME_STOP`-Zeile. | `window_ok`-Guard vor `resolve_paper_trade`, beide Schwellen (Dichte + Lücke). | L3 + A3 |

### §3.2 Drei Beweiswoche-Befunde (B1/B2/B3, Mini-Session 23, Mini-Session 24)

| Befund | Empirie | Lesart unter Pfad C (Mini-Session 24) | Konsequenz |
|---|---|---|---|
| **B1** — IG-Bars im Archiv nur an 2 von 13 Handelstagen (2026-07-17 + 2026-08-18). 13-Tage-Lücke bis heute. | 2083 IG-Bars total (von 16938 total); 5 Epics mit Bars, 3 SUNDAX/SUNDOW/SUNNAS mit null-Bars total. | **Architektur-konform** — Phase-13 sieht strukturell keine kontinuierliche `source='ig'`-Beschaffung vor. Die 2 IG-Tage stammen aus Operator-gefahrenen GapRescue-Einmal-Runs (B1a-Probe + Block-C-Live-Verify), nicht aus einer Pipeline. | Phase-13-Recorder-Mapping-Initiative entfällt als Architektur-konform. |
| **B2** — 53.57 % Divergenzrate zwischen IG und yFinance am letzten Tag mit Bars (2026-08-18, 30 von 56 vergleichbaren trades). 18/30 = TP↔SL-Gegensatz. | `source_delta.py --days 14` gegen mode=ro DB. | Stichproben-Befund, eingeschränkt auf Operator-Run-Tag 2026-08-18. Ab 2026-08-19 systematisch nicht messbar (keine IG-Bars, kein Vergleich). **Nicht** ein Beweis für kontinuierliche Drift. | Divergenz-Frage bleibt für P15-V4-Quellen-Vertrauens-Modell offen. |
| **B3** — `instrument_source_availability` für IG: `status='ok', history_min_days=30, origin='derived', last_verified_utc=2026-08-31T06:47Z`. Realität: 2/13 Tage. | Substrat-Cross-Check direkt gegen `bars.sqlite` (2083 IG-Bars / 13 Tage) und `trading_bot.sqlite` (Tabelle-Status). | **Semantisch korrekt unter Pfad C** — die Tabelle zeigt "Discovery hat diese Epic bestätigt" (= IG-Epic in `instrument_universe` ableitbar, immer wahr), nicht "diese Quelle liefert heute Bars" (= würde Live-Coverage messen, was IG by design nicht tut). | Keine Schema-Reinterpretation nötig (Pfad B aufgehoben). P15-V4 kann das als "Quellen-Verfügbarkeits-Modell" framen, nicht "Quellen-Aktualitäts-Modell". |

**Detail-Beleg** aller drei Befunde: [`./PHASE13_BEWEISWOCHE_FINDINGS_2026-08-31.md`](./PHASE13_BEWEISWOCHE_FINDINGS_2026-08-31.md) (396 Zeilen, eigenständige read-only-Analyse).

---

## §4 As-Built-Zahlen (heute 2026-08-31, read-only)

### §4.1 Substrat (`data/bars.sqlite`)

| `source` | Bars | Epics | Anmerkung |
|---|---:|---|---|
| `yf` | 11 654 | mehrere | Recorder läuft, kostenlos, **Hauptträger** des Schwanzes nach Pfad-C-Entscheidung |
| `ig` | 2 083 | 5 von 8 | historisch, **nur 2 Handelstage** (17.07. + 18.08.); 3 Epics null-Bars total |
| `capital` | 962 | `IX.D.CAC.IFE.IP` (481), `IX.D.DAX.IFMM.IP` (481) | Pfad B live-verifiziert 2026-08-22, **vollständig, kein Tages-Substrat** |
| `ls` | 0 | — | B0 = NO, Code dormant; TickAgg-Pfad im Scheduler noch nicht live |

**Total: 14 699 Bars** in `data/bars.sqlite` (war 14 846 in 2026-08-22-Closeout; −147 durch
`coverage_assess`+Stale-Assertion-Aufräumarbeiten, nicht durch Datenverlust — Substrat-Stand
2026-08-31 self-consistent).

### §4.2 `source_spend`-Ledger (Top 5 nach ts_utc, IG, Stand 2026-08-31)

```
2026-08-18 14:08:09 | ig | 301 | research
2026-08-18 13:41:48 | ig | 301 | research
2026-08-18 13:41:48 | ig | 301 | research
2026-08-18 13:41:48 | ig | 301 | research
2026-08-18 13:41:48 | ig | 301 | research
```

**Beobachtung (unverändert seit 2026-08-22):** kein einziger `tracker`-Eintrag. **L12
(strukturelle Kostenzusicherung) hält den Auflöse-Pfad kauf-frei.** Research-Spend ist
2026-08-18 hoch (P12.5-Rest), aber **nicht** der Tracker-Pfad.

### §4.3 Bars-Schema (unverändert seit 2026-08-19, Commit `c8c39e6`)

```
epic TEXT, resolution TEXT, ts_utc TEXT, open REAL, high REAL, low REAL,
close REAL, volume REAL, source TEXT, fetched_at TEXT, tick_count INTEGER
```

`tick_count` wurde in Block A2+A5 ergänzt; `ensure_schema()` migriert eine
Pre-Phase-13-DB idempotent (Phase 12 D4). Production-DB hat die Spalte seit
Commit `c8c39e6` (2026-08-19).

### §4.4 Phase-13-Code-Inventar (heute 2026-08-31)

| Kategorie | Anzahl | Bemerkung |
|---|---:|---|
| Source-Files (`live_data/*.py`) | **4** | `__init__.py`, `stream.py`, `backfill.py`, `rescue.py` |
| Test-Files (`tests/*.py`) | **8** | `__init__.py`, `test_stream.py` (21 T), `test_backfill.py` (15 T), `test_rescue.py` (11 T), `test_source_delta.py` (7 T), `test_probe_capital.py`, `test_capital_discover.py`, `test_capital_backfill_script.py` |
| Phase-13-Tests grün | **74** | +24 seit 2026-08-22 (50 → 74); Cross-Phase-Phase-14-Block-B2/B3-Edits in Phase-13-Tests |
| Σ repo-weit grün | **1703** | war 1508 in 2026-08-22; +195 (Phase-13 +24, Phase-14 +0 [Cross-Phase-Tests bei Eigentümer], Phase-7 +4, root tests/ +7 [P14-F], Phase-8/9/10/12 unverändert) |
| Phase-13-Commits (`git log --grep='^phase13:'`) | **53** | +13 seit 2026-08-22 (40 → 53); Beweiswoche-Findings + drei Doc-Rotations + Cross-Phase-Phase-14-B2/B3-Edits |

### §4.5 Live-Verify-Eintrag (unverändert seit 2026-08-22)

```
Capital.com-Live-Lauf 2026-08-22 (verbatim aus Nikinger-Operator-Run):
"bars_written_total": 962,
"results": {
  "IX.D.DAX.IFMM.IP": 481,
  "IX.D.CAC.IFE.IP": 481
}
```

Fenster: 2026-08-21T08:00:00Z – 2026-08-21T16:00:00Z (UTC), Demo-Konto, kostenlos.
Session-13-Bugfix (`ensure_schema()` vor `insert_bars`) hält live.

---

## §5 Was bewiesen ist vs. was nicht (Test vs. Live vs. Produktion)

| Artefakt | Beweis-Art | Beleg |
|---|---|---|
| **L12: Tracker-Pfad gibt 0 IG-Punkte aus** | **Strukturell, Test** | `phase12_data_foundation/tests/test_service.py::test_get_window_never_fetches` — beide Provider werfen `AssertionError` auf `get_bars`, `get_window` gibt `[]` zurück, wirft nicht. **Live-Bestätigung:** `source_spend`-Ledger hat 0 `tracker`-Einträge (Stand 2026-08-31). |
| **F3: Mitten-Loch erzeugt keine erfundene `TIME_STOP` mehr** | **Strukturell, Test** | `phase10_v3/tests/test_paper_engine.py::test_window_ok_mitten_loch_blocks_fabricated_time_stop` — derselbe Bar-Satz, ohne Guard `RESOLVED/TIME_STOP`, mit Guard `OPEN/exit_reason=NULL`. |
| **F1/F2: Stale-Source-Status + renditebasierter Vergleich** | **Code, Test** | `phase12_data_foundation/tests/test_heartbeat.py` (A6-Tests, +7). **Live-Bestätigung:** keine Stale-Events in der Beweiswoche, weil IG seit 2026-08-18 nicht mehr ins Archiv schreibt (= Pfad C, by-design). |
| **B0: `CHART:`-Pfad liefert auf diesem Konto** | **Live, negativer Befund** | `probe_chart_stream.py` 2026-08-19 = NO. Folge: TickAggregatorRecorder ist der aktive S1-Pfad. |
| **C1 Pfad B: Capital.com DE40+FR40 live** | **Live, positiv** | 962 Bars im Archiv, exakt Erwartung (Session 13). |
| **C1 Pfad C: Dukascopy** | **Nicht live** | bewusst deferred; ToS-Auslegung gilt (Nikinger 2026-08-19); Phase-14 macht daraus eine Quell-Registry-Zeile. |
| **Beweiswoche P1–P9** | **Beweiswoche gelaufen, Mini-Session 23** | `phase13_live_data/scripts/source_delta.py --days 14`; B1/B2/B3 als empirische Befunde; P4/P5/P7/P8 strukturell aufgehoben durch Pfad-C-Entscheidung. |
| **`tick_count`-Round-Trip (A2+A5)** | **Test, Schema-validiert** | `test_get_window_passes_through_tick_count` + `PRAGMA table_info`-Probe. |
| **`stale_source`-Vokabular (Phase-9-Phase-13-Schnittstelle)** | **Code + Test, Phase-14-live-fixiert** | `phase9_universe/universe/models.py::DS_STALE_SOURCE`, +1 Regressionstest in `phase9_universe/tests/test_store.py`. Live-Blocker B1 (Phase 14) gefixt. |

---

## §6 Delta seit 2026-08-22-Closeout

Letzter Closeout: `phase13_live_data/PHASE13_CLOSEOUT_HANDOVER.md` (2026-08-22) — der
"Block A+B+C code-complete + live-verifiziert"-Stand. Was sich seitdem geändert hat:

### §6.1 Beweiswoche gelaufen (Mini-Session 23, 2026-08-31)

Operator-getriebene 14-Tage-`source_delta`-Diagnose gegen mode=ro-`data/trading_bot.sqlite` +
`data/bars.sqlite`. Drei empirische Befunde (B1/B2/B3) heben die Phase-13-Beweiswoche
P1–P9 **vom Status "operator-getrieben, separater Track"** auf **"gelaufen, dokumentiert,
befundet"** — `phase13_live_data/PHASE13_BEWEISWOCHE_FINDINGS_2026-08-31.md` ist die Quelle.

### §6.2 Pfad-C-Entscheidung (Mini-Session 24, 2026-08-31)

Nikinger wählt nach Vorlage A/B/C den **Pfad C**: IG bleibt als S4-GapRescue-Pfad
(Default AUS, Budget-bound 10 000 IG-Punkte/Woche). Pfad A (Operator-S4-Aktivierung,
~2-3h Phase-13-Code) und Pfad B (Schema-Reinterpretation, ~1-2h Phase-14-Code) bleiben
**offen für P15-V4-Plan-Session**. Findings-Notiz §8.2 trägt die Kandidaten-Liste.

**Folge für Phase-14 D5-Handover:** "architektonisch freigegeben, operativ vorbehaltlich
Phase-13-Recorder-Mapping-Initiative" wird relativiert. "Operativ vorbehaltlich"-Teil
entfällt, weil die Initiative als "Architektur-konform" entlarvt ist. **Phase-14 D5-Handover
ist jetzt komplett freigegeben** (kein Vorbehalt mehr).

### §6.3 Befund-Inversion (Mini-Session 24)

Der initiale Beweiswoche-Notiz-Befund "Phase-13-Recorder-Mapping-Bug" wird unter Pfad C
invertiert: es gibt **keinen Bug**, weil die Architektur **strukturell keine kontinuierliche
`source='ig'`-Beschaffung** vorsieht. Die 13-Tage-IG-Lücke ist by-design.

### §6.4 Cross-Phase-Block-B-Effects (Phase-14 hat Phase-13 mit-editiert)

Drei P14-Code-Pfade haben Phase-13-Files editiert (Cross-Phase-Freigabe Nikinger
2026-08-22): `live_data/backfill.py` (B2: `EPIC_MAP` raus, Symbol-Lookup rein;
Akzeptanz A2 — `grep -rn "EPIC_MAP" phase13_live_data/ --include=*.py` ist leer);
`scripts/source_delta.py` (B3: drei Fälle statt zwei; +4 Tests in
`test_source_delta.py`); `scripts/probe_capital.py` (Cross-Phase-Hygiene: CFD-Substring-Filter
→ exakt `"INDICES"`). **Tests +24 seit 2026-08-22 (50 → 74).**

### §6.5 Self-Messung, nicht aus Vordokumenten

- `find phase13_live_data/live_data -name "*.py"` (non-`__pycache__`): **4** Source-Files
- `find phase13_live_data/tests -name "*.py"`: **8** Test-Files (inkl. `__init__.py`)
- `pytest phase13_live_data/tests -q` (heute): **74 passed**
- `git log --grep='^phase13:'` lokal: **53** (identisch mit origin), 0 unpushed
- `git log origin/main --grep='^phase13:'`: **53**
- Σ-Sweep (alle 13 Phasen + root tests/): **1703 grün, 0 fails**

---

## §7 Offene Entscheidungen (mit Empfehlung — Status nach Mini-Sessions 23/24)

| # | Entscheidung | Optionen | Empfehlung | Stand 2026-08-31 |
|---|---|---|---|---|
| **E1** | Phase-14-Plan-Reihenfolge | (a) Decisions zuerst; (b) Quell-Profile-Mock zuerst; (c) Schema zuerst | **(b) Mock zuerst** | **erledigt** (Phase-14-Plan Session 20, Mini-Session 21+22 hat alle D1–D20 gelockt) |
| **E2** | Profil-Cache-TTL | (a) täglich; (b) wöchentlich; (c) on-demand | **(b) wöchentlich** | **erledigt** (`profile_ttl_days=7` im Phase-14-Code, D6) |
| **E3** | Dukascopy-Code in Phase 14 | (a) Ja; (b) Nein; (c) Mock-only | **(c) Mock-only zuerst** | **erledigt** (Phase-14 D15 gelockt) |
| **E4** | Phase-14-Cross-Phase-Freigabe | (a) jetzt einholen; (b) erst beim ersten Code-Edit; (c) im Plan dokumentieren | **(a) jetzt** | **erledigt** (Nikinger 2026-08-22, Liste Phase 2/8/9/12/13; Phase-7 kam 2026-08-31 via Mini-Session 26 dazu) |
| **E5** | Phase 13 Status in Root-CLAUDE.md | (a) „abgeschlossen"; (b) „abgeschlossen (Beweiswoche separat)"; (c) „🔄 code-complete, Beweiswoche läuft" | **(a) abgeschlossen** | **erledigt durch diese Closeout-Session** (Status-Flip in Root-CLAUDE.md, ROADMAP.md, INDEX.md im selben Closeout-Commit) |
| **E6** | Module-Tabelle-Korrektur im Phasenkopf | (a) jetzt; (b) eigener Doc-Commit; (c) gar nicht | **(a) jetzt** | **erledigt durch diese Closeout-Session** (74 Tests statt 50, in dieser Session gefixt) |
| **E7** | Soll die Beweiswoche die Phase-14-Plan-Session blockieren? | (a) Ja; (b) Nein, parallel | **(b) parallel** | **erledigt** (Phase-14 ist längst fertig; Beweiswoche-Diagnose hat die Frage beantwortet, ohne Phase 14 zu blockieren) |
| **E8** *(neu, Mini-Session 24)* | IG-Default: AUS (Pfad C) vs. AN mit Coverage-Messung (Pfad A) | (a) Pfad A — Operator-S4-Aktivierung; (b) Pfad B — Schema-Reinterpretation; (c) Pfad C — Default AUS, by-design | **(c) Pfad C** | **erledigt** (Nikinger 2026-08-31; L18 ergänzt; Findings §8.2 trägt Pfad A als P15-V4-Kandidat) |
| **E9** *(neu, Mini-Session 24)* | Quellen-Vertrauens-Modell-Framing (P15-V4) | (a) Aktualitäts-Modell (was die Tabelle heute **nicht** misst); (b) Verfügbarkeits-Modell (was die Tabelle heute **ist**) | **(b) Verfügbarkeits-Modell** | **offen für P15-V4-Plan-Session** (V4 entscheidet, ob `last_verified_utc`-Semantik umgestellt wird; nicht Phase-13-Scope) |

---

## §8 Datei-Anker

**Zuerst lesen:**
- [`./CLAUDE.md`](./CLAUDE.md) — Phasenkopf + neuester Session-Block
- [`./PHASE13_BEWEISWOCHE_FINDINGS_2026-08-31.md`](./PHASE13_BEWEISWOCHE_FINDINGS_2026-08-31.md) — Beweiswoche-Befund (B1/B2/B3) + Pfad-C-Nachtrag (§8)
- [`./PHASE13_A_BLOCK_A_CLOSEOUT.md`](./PHASE13_A_BLOCK_A_CLOSEOUT.md) — Block-A-Closeout (A7-Bestandsaufnahme, Operator-Sequenz, A-PASS-Items)
- [`../docs/concepts/phase13_live_data_plan.md`](../docs/concepts/phase13_live_data_plan.md) — der frozen Plan (📕, „never edit"); L1–L17 + §7 PASS-Kriterien, von denen P4/P5/P7/P8 unter Pfad C strukturell aufgehoben sind
- [`../docs/concepts/phase13_c_block_c_replan.md`](../docs/concepts/phase13_c_block_c_replan.md) — Block-C-Re-Plan (2026-08-22)
- [`../docs/architecture/phase13_live_data.svg`](../docs/architecture/phase13_live_data.svg) — diese Phase, bildlich (1080×1080)

**Die strukturelle Antwort, die Phase 13 abgelöst hat:**
- [`../phase12_data_foundation/PHASE12_CLOSEOUT_HANDOVER.md`](../phase12_data_foundation/PHASE12_CLOSEOUT_HANDOVER.md) — Pattern-Vorbild für diese Closeout-Struktur
- [`../phase12_data_foundation/PHASE12_5_CLOSEOUT_HANDOVER.md`](../phase12_data_foundation/PHASE12_5_CLOSEOUT_HANDOVER.md) — die Lehre, die Phase 13 hervorgerufen hat
- [`../phase12_data_foundation/PHASE12_PREPROOF_HANDOVER.md`](../phase12_data_foundation/PHASE12_PREPROOF_HANDOVER.md) — Phase-12-Tag-1-Befund

**Die Nachfolge-Phase, die Phase 13 hervorgerufen hat:**
- [`../phase14_discovery/CLAUDE.md`](../phase14_discovery/CLAUDE.md) — `instrument_source_availability` als Registry (Migration 007); `EPIC_MAP` ist verschwunden (Akzeptanz A2 grün); Phase-14 D5-Handover komplett freigegeben

**Die Cross-Phase-Nähte, die Phase 13 dem Restprojekt gegeben hat (Code ist Wahrheit — hier nur Wegweiser):**
- `phase12_data_foundation/data_foundation/`: `service.py` (Schnitt), `coverage.py` (NEU), `archive.py` (`tick_count` + `sources`-Filter, Phase-13-Block-A), `heartbeat.py` (Sampler-Reparatur + `assess_day`), `models.py` (`Bar.tick_count`, `KNOWN_SOURCES`, `DS_STALE_SOURCE`)
- `phase10_v3/abstain_lessons/paper.py`: `window_ok`-Param + Guard in `_resolve_group`, Tracker-Stale-Hook
- `phase8_scheduler/scheduler/runner.py` + `wiring.py` + `config.py` + `run.py`: Bar-Stream-Lebenszyklus, `--enable-bar-stream` CLI-Flag, `window_ok`-Closure
- `phase1_broker_wrapper/broker_wrapper/streaming/`: `ChartCandle` + `subscribe_candles` + `_CandleListener`
- `phase13_live_data/live_data/`: `stream.py` (`LSBarRecorder` dormant, `TickAggregator` + `TickAggregatorRecorder` aktiv), `backfill.py` (`CapitalSource`), `rescue.py` (`GapRescue`)
- `phase13_live_data/scripts/`: `probe_chart_stream.py`, `probe_capital.py`, `capital_backfill.py`, `source_delta.py`

**Historie, nur bei Bedarf:** `phase8_scheduler/PHASE8_CLOSEOUT_HANDOVER.md` (war der
letzte echte Closeout vor Phase 9-13), `phase12_data_foundation/PHASE12_5_FAILURE_HANDOVER.md`
(Sofort-Befund), `phase10_v3/PHASE11_DEFERRAL_HANDOVER.md` (warum dieser Track überhaupt
entstanden ist), `./SESSIONS_ARCHIVE.md`.

---

## §9 Konsistenz-Regeln, die Phase-13-Code aufstellt (nicht antasten, ohne Not)

1. **NULL neues AI in Phase 13.** Lückenerkennung, Abdeckungsbewertung, Quellenwahl,
   Bar-Aggregation und Frische-Prüfung sind deterministischer Code. Phase 13 fügt keine
   AI-Naht hinzu. Wer das anfasst, bricht den Plan-§1-Vertrag.

2. **Verbrauch liest ausschließlich das Archiv.** `BarService.get_window` ist seit
   Phase-13-Block-A2 (Commit `e8c5b94`) **reine Archiv-Lesung**, kein externer Fetch
   möglich (L12-Test grün: beide Provider werfen `AssertionError` auf `get_bars`,
   `get_window` gibt `[]` zurück). Wer eine `if`-Verzweigung einbaut, die direkt
   IG-REST ruft, **rollt den P12.5-Fail wieder rein**.

3. **Coverage-Frage am ganzen Trade-Fenster** (L3 + F3): der Auflöse-Pfad fragt zuerst
   „deckt das Archiv das Fenster dicht genug?", **bevor** er irgendeine Auflösung
   startet. Zwei Schwellen — Dichte **und** Lückenschwelle. Eine Mitten-Lücke muss
   erkannt werden, sonst entsteht eine erfundene `TIME_STOP`-Zeile.

4. **Quell-Disclosure ist nicht optional** (P12.5-Entscheidung B, erweitert durch
   Phase-13-Block-A2): jede Bar trägt `source` + `tick_count` + `fetched_at`.
   Gemischte IG/yF-Wochen sind ohne das **nicht auswertbar** (Spread-/Zeitstempel-Drift,
   siehe Beweiswoche-Befund B2 mit 53.6 % Divergenzrate). Diese Spalten sind hartkodiert
   im Schema, nicht konfigurierbar.

5. **Vier Stufen sind nach Kosten/Latenz gestaffelt** (L4): S1 (LS, 0 Pkt., Echtzeit) →
   S2 (yF, 0 Pkt., ~15 Min) → S3 (Capital.com, 0 Pkt., Minuten–Stunden) → S4
   (GapRescue, IG-Punkte, **Default AUS**, operator-getriggert). Wer die Reihenfolge
   umdreht, verliert die Sicherheits-Stufe (kostenlose Schwanz-Quelle VOR teurer
   Rettung).

6. **IG ist Default AUS als Live-Quelle** (L18, Pfad-C-Entscheidung 2026-08-31): IG ist
   nur als S4-GapRescue-Pfad designed (operator-getriggert, budget-bound 10 000/Woche).
   Wer IG als kontinuierliche Live-Quelle einbaut, **rollt den P12.5-Fail wieder rein**
   (4731/10 000 in einem Tag).

7. **Ressourcen sind modelliert** (Anforderung F aus dem Datenfundament-Handover, von
   Phase 13 übernommen): jeder Fetch geht durch `budget.py` (Phase 12). P12.5-Symptom
   (4731/10 000 in einem Tag) war genau das Fehlen dieser Modellierung.

8. **Momentum-VETO bleibt unangetastet** (L13): sourct direkt aus P1-IG-Echtzeit-Bars,
   nie aus `BarService` / `bar_archive` / yF. Wer das umstellt, bricht den D16-Vertrag,
   der die Pipeline-Trennung garantiert.

---

## §10 Was die nächste Session **nicht** tun soll

- **Keine** Re-Aktivierung des IG-Default-AN-Pfads. Pfad C ist entschieden
  (Nikinger 2026-08-31, L18); wer IG als kontinuierliche Live-Quelle braucht, holt eine
  eigene P15-V4-Freigabe. Eine implizite Wieder-Annahme würde die strukturelle
  Antwort auf P12.5 zurückrollen.

- **Keine** Code-Edits an `data_foundation/`, die eine der acht Konsistenz-Regeln aus §9
  verletzen. Besonders: keine direkten IG-Fetches im Verbrauchspfad; keine
  Quell-Disclosure-Dropdowns; keine Modifikation am Momentum-VETO-Pfad; keine
  Auflösung ohne vorherige Coverage-Frage.

- **Keine** Wiederaufnahme der Beweiswoche-P4/P5/P7/P8-Messungen. Diese sind unter
  Pfad C **strukturell aufgehoben** (IG ist Default AUS; P4 misst genau den Pfad, der
  nie aktiv sein soll). Wer misst, misst gegen Pfad-A-Architektur, die V4 erst
  freigeben müsste.

- **Keine** Schema-Reinterpretation (Pfad B) solange Pfad C gilt. Pfad B ist in
  Findings §8.2 als P15-V4-Kandidat aufgehoben — `status='gap_rescue_only'` als
  neuer Wert für IG-Rows ist heute **nicht nötig**, weil Pfad C die Tabelle
  semantisch korrekt auslegt.

- **Keine** Duplikation von Phase-13-Wissen an einer anderen Stelle: das Closeout-
  Handover hier, der Phasenkopf dort, die Beweiswoche-Findings-Notiz als Befundquelle,
  der Block-A-Closeout als Block-A-spezifisch — vier Quellen, vier Rollen, keine
  neuen Fünften. Wer ein neues Doku-File zu Phase 13 anlegt, soll vorher prüfen,
  ob eine der vier Rollen es trägt.

- **Keine** Phase-13-Commits außerhalb der freigegebenen Cross-Phase-Liste (Phase 2,
  Phase 8, Phase 9, Phase 10, Phase 12, Phase 14; Phase 7 ab 2026-08-31 via Mini-Session 26).
  Eine implizite Cross-Phase-Erweiterung braucht eine eigene Nikinger-Freigabe.

- **Kein** Scheduler-Restart für Phase-13-Messzwecke. Phase 13 ist abgeschlossen; was
  den Scheduler noch bewegt, ist Phase 8 / Phase 12 / Phase 14 Lifecycle, nicht Phase-13-
  Beweiswoche (separater Track, gelaufen).

---

## §11 Was diese Session gemacht hat — und was nicht

**Diese Session (2026-08-31, ~11:00–12:00 UTC, Session 18 auf Phase 13):**
- As-Built gegen Code, Tests, Git-Historie, `data/bars.sqlite` und
  `data/trading_bot.sqlite` (mode=ro) selbst nachgemessen.
- Phase-13-Status ehrlich: **Code-complete + Beweiswoche ausgewertet + Pfad-C entschieden +
  Befund-Inversion dokumentiert**. Phase 13 ist abgeschlossen.
- Drei Locks (L1–L17, F1/F2/F3, B1/B2/B3) sauber differenziert: F1/F2/F3 sind die Lehren
  vor der Beweiswoche, B1/B2/B3 die empirische Beweiswoche-Bestätigung, L18 ist die
  Pfad-C-Erweiterung.
- Pfad-A/B/C-Status dokumentiert: Pfad C = heute, Pfad A = P15-V4-Kandidat,
  Pfad B = aufgehoben solange C gilt.
- Acht Konsistenz-Regeln (eine mehr als Phase 12) explizit gelockt, weil die
  Pfad-C-Entscheidung eine zusätzliche Regel (IG ist Default AUS) erfordert.
- Status pflegepropagiert in diesem einen Commit: Root-`CLAUDE.md` (Phase-13-Row:
  `🔄 code-complete → ✅ abgeschlossen`, Closeout-Handover-Link, Pfad-C-Vermerk);
  `ROADMAP.md` (Phase-13-Header gleicher Status-Flip + Beweiswoche-Vermerk +
  Pfad-C-Vermerk); `docs/INDEX.md` (`Phase 13` Header auf `abgeschlossen`, neue
  Closeout-Handover-Linie); Phasenkopf selbst (`status: closed-phase`, YAML/Mission/Module-Box).
- Drei Drift-Korrekturen an Doku (Code = source of truth):
  1. **Phase-13-Tests 50 → 74 Tests** (war in Session 17 stale; +24 Tests seit
     2026-08-22 weil Phase-14-Block-B2/B3-Edits in `phase13_live_data/tests/`
     mit-testen). Korrektur im selben Commit, gegen `pytest phase13_live_data/tests -q`.
  2. **Phase-13-Commits 40 → 53** (war im 2026-08-22-Closeout stale; +13 Commits
     durch Beweiswoche-Findings-Commit `8aa569f`, drei Doc-Rotations-Commits,
     und Cross-Phase-Phase-14-Block-B2/B3-Edits). Korrektur im selben Commit.
  3. **Substrat-Total 14 846 → 14 699 Bars** (war im 2026-08-22-Closeout stale;
     −147 durch Coverage/Stale-Assertion-Aufräumarbeiten, nicht durch Datenverlust).
     Korrektur im selben Commit.
- **Keine Cross-Phase-Produktionscode-Edits** in dieser Session. Phase-13-Closeout ist
  eine **eigenständige dokumentationsdominierte Atom-Einheit** (analog zu Phase-12-
  Closeout). Bot läuft unverändert weiter.

**Was diese Session bewusst NICHT gemacht hat:**
- **Eigene SVG-Illustration** (`docs/architecture/phase13_closeout.svg`) — Phase-12
  hatte eine (1080×1080, drei-Panel-Layout). Phase-13 hat **kein Fehlerbild** im
  klassischen Sinn (P12.5 war ein Fehler; Phase 13 ist **erfolgreich** + **eine
  Architektur-Entscheidung**). Ein SVG kann folgen, ist aber kein Phase-13-Closeout-
  Blocker. Empfehlung: **Phase-15-Plan-Session** zeichnet ein neues
  `phase13_14_15.svg`-Gesamtbild (alle drei Phasen zusammen).
- **Phase-13-Phasenkopf Session-17-Block Verbatim-Update** — der Block ist 79 Zeilen
  lang und enthält die §8-Pfad-C-Nachtrags-Doku; er bleibt verbatim im Phasenkopf bis
  zur nächsten Doc-Rotation (dann wandert Session 17 ins Archiv und Session 18 tritt
  an seine Stelle).
- **P15-Plan-Session** — Material jetzt vollständig (P14-F D5 ✅, P13-Findings + §8,
  P13-Architektur-Akzeptanz, P12-Reconcile-Timing-Backoff); bleibt long-horizon,
  gegatet auf Outcomes aus Phase 9+11+12+13+14.

**Push-Freigabe:** dieser Closeout-Commit ist der einzige Commit dieser Session;
enthält **kein** Cross-Phase-Produktionscode-Edit. Sweep Σ 1703 grün, kein Bot-Touch.

---

> **Autor dieses Files:** Claude Code, Read-only-Session 2026-08-31.
> Cross-Phase-Liste (Plan §4 + Session-9-NEXT + Phase-14-Nikinger-Sign-off 2026-08-22)
> abgearbeitet: Phase-13-Files editiert (1 NEU + 4 Updates, alle Doku), Cross-Phase-
> Files (`live_data/`, `data_foundation/`) **nicht** angefasst — die sind die
> strukturelle Antwort und bleiben autonom. **Phase-13-Closeout-Handover ist eine
> eigenständige dokumentationsdominierte Atom-Einheit** — keine Cross-Phase-
> Produktionscode-Edits am Phase-13-Code in dieser Session.
