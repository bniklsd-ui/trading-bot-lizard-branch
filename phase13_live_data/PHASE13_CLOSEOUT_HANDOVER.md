---
status: snapshot
purpose: Phase-13-Abschluss (2026-08-22) — Code-complete + live-verifiziert für DE40/FR40 (Block A+B+C); die "discovery-then-deterministic"-Architektur wurde in eine eigene Phase 14 ausgelagert. Was die nächste Session über Phase 13 wissen muss, BEVOR sie einen Plan schreibt.
read-when: vor jedem Plan, der Phase 14 vorbereitet; vor jedem Re-Read der Anforderungen P1–P9 (Beweiswoche); wenn `EPIC_MAP`, `GapRescue` oder `source_delta.py` berührt werden sollen
detail: L3
up: ./CLAUDE.md
down:
  - ./PHASE13_A_BLOCK_A_CLOSEOUT.md                        # 📕 Block-A-Closeout (A7-Bestandsaufnahme, Operator-Sequenz, A-PASS-Items)
  - ../docs/concepts/phase13_live_data_plan.md             # 📕 L1–L17 (gelockt), Blöcke A/B/C, §9-Drift, §8-Fehlgriffe
  - ../docs/concepts/phase13_c_block_c_replan.md           # 📕 Block-C-Re-Plan + Phase-14-Handoff (2026-08-22)
  - ../docs/concepts/phase14_discovery_concept.md          # 📕 Phase-14-Concept (drei Bausteine, sieben offene Fragen)
  - ../phase12_data_foundation/PHASE12_5_CLOSEOUT_HANDOVER.md   # 📕 die Lehre, die Phase 13 hervorgerufen hat
  - ../phase12_data_foundation/PHASE12_PREPROOF_HANDOVER.md     # 📕 Phase-12-Tag-1-Befund
  - ../docs/architecture/phase13_live_data.svg             # 📕 diese Phase, bildlich (1080×1080)
  - ../docs/architecture/phase12_5_failure.svg             # 📕 die Vorgeschichte (Fehlerbild, gegen das Phase 13 gebaut wurde)
updated: 2026-08-22
---

# Phase 13 — Closeout-Handover (2026-08-22)

> **Autor:** Claude Code, Read-only-Analyse 2026-08-22, **kein** Produktionscode-Edit
> in dieser Session. **Adressat:** die nächste Session an Phase 14 (Plan-Vorbereitung) oder
> an Phase 13 (Beweiswoche-Begleitung). **Quelle aller Zahlen:** eigene read-only-Abfragen
> gegen `data/bars.sqlite` und die Git-Historie, **nicht** aus Vordokumenten übernommen.

---

## §0 BLUF

Phase 13 ist **abgeschlossen** im Sinne von „Code-complete + live-verifiziert für den
funktionierenden Teil". Die Beweiswoche gegen P1–P9 läuft als **separater Validierungstrack**
parallel zu Phase 14 — der Code-Stand ist final, der Beweis wird nachgereicht.

**Drei Sätze, die die Phase tragen:**

1. **Beschaffung ≠ Verbrauch.** Vier Stufen (S1 LS-Kerzen / TickAgg → S2 yF-Recorder →
   S3 Capital.com → S4 GapRescue AUS) schreiben in *ein* Archiv. Verbrauch liest
   ausschließlich das Archiv und kauft nie.
2. **Die Abdeckungsfrage gilt dem ganzen Trade-Fenster**, nicht dem Schwanz. Eine
   Mitten-Lücke erzeugt sonst eine **erfundene** `TIME_STOP`-Zeile, die wie ein
   sauberes Ergebnis aussieht (F3).
3. **Die "discovery-then-deterministic"-Architektur ist eine eigene Phase 14.**
   Das hardcoded `EPIC_MAP` und Path C Dukascopy werden dort keine Code-Migration,
   sondern eine Konfigurationszeile.

**Ergebnis-Bilanz (5 Zeilen, Handover-Prompt-Schema):**

| Zeile | Stand 2026-08-22 |
|---|---|
| **fertig gestellt** | Blöcke A (Schnitt + Coverage + Stale-Assertion + Sampler-Reparatur + Registry-Hygiene), B (Lightstreamer-Code + TickAggregator-Fallback + Scheduler-Lebenszyklus + Token-Rotation), C (Capital.com Pfad B + GapRescue + source_delta.py) — Code committed auf `main` (40 Commits, Stand `18dafd9`, alle gepusht) |
| **getestet** | 50 Phase-13-Unit-Tests grün (Stand 2026-08-22); 1508 Tests repo-weit, alle Suiten grün |
| **live validiert** | Block A (Strukturtest, `test_get_window_never_fetches` — IG-Provider wirft `AssertionError`, Test grün); Block C Pfad B (962 `source='capital'`-Bars, DAX + FR40, geschrieben in 1 Nikinger-Operator-Lauf 2026-08-22, im Archiv verifiziert) |
| **gepusht und committet** | `main` synchron mit `origin/main` (40 Commits voraus, alle Phase 13, Push-Freigabe vom 2026-08-22 erteilt) |
| **nicht erreicht / offen geblieben** | (a) Beweiswoche P1–P9 (Plan §7) nicht gelaufen — operator-getrieben, separater Track; (b) Block C C1 SP35 (IBEX) PARTIAL by design (Pfad C Dukascopy → Phase 14); (c) Block A Sampler live: A6-Code committet, aber die ersten 5 Beweis-Tage werden zeigen, ob die Sampler-Events gegen F1/F2-Stale-Source wirklich scharf stellen; (d) Module-Tabelle im Phasenkopf stale (39 Tests statt 50) — bewusst in `18dafd9` aufgeschoben |

---

## §1 Was die nächste Session wissen muss, BEVOR sie einen Plan schreibt

### §1.1 Architektur-Bild (in einer Zeile)

```
S1 (LS-Kerzen / TickAgg) ┐
S2 (yF-Recorder)         ├──► BarArchive (data/bars.sqlite) ──► Verbrauch (Tracker, Research, DivergenceSampler, Heartbeat)
S3 (Capital.com PARTIAL)  │         │                              kaufen nie, nur Lesen
S4 (GapRescue, AUS)       ┘         └──► Resolution: coverage_assess → gedeckt | offen | typisiert
```

### §1.2 Wo der Code lebt (Cross-Phase-Edits, die Phase 13 gemacht hat)

- `phase12_data_foundation/data_foundation/`: `service.py` (Schnitt), `coverage.py` (NEU), `archive.py` (`tick_count`+`sources`-Filter), `heartbeat.py` (Sampler-Reparatur), `models.py` (`Bar.tick_count`, `KNOWN_SOURCES`, `DS_STALE_SOURCE`)
- `phase10_v3/abstain_lessons/paper.py`: `window_ok`-Param, Guard in `_resolve_group`, Tracker-Stale-Hook
- `phase8_scheduler/scheduler/runner.py` + `wiring.py` + `config.py` + `run.py`: Bar-Stream-Lebenszyklus, `--enable-bar-stream` CLI-Flag, `window_ok`-Closure
- `phase1_broker_wrapper/broker_wrapper/streaming/`: `ChartCandle` + `subscribe_candles` + `_CandleListener`
- `phase13_live_data/live_data/`: `stream.py` (`LSBarRecorder` dormant, `TickAggregator`+`TickAggregatorRecorder` aktiv), `backfill.py` (`CapitalSource`, EPIC_MAP), `rescue.py` (`GapRescue`)
- `phase13_live_data/scripts/`: `probe_chart_stream.py`, `probe_capital.py`, `capital_backfill.py`, `source_delta.py`

**Konsequenz für Phase 14**: jede Cross-Phase-Änderung braucht weiterhin eine
Cross-Phase-Freigabe vom Nikinger (Phase 12 hat sie 2026-08-17 erteilt, Phase 13
2026-08-18 — Phase 14 muss das wieder einholen).

### §1.3 Was die Locks sind (L1–L17 aus dem Hauptplan, „don't re-litigate")

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
| **L15** | `BarService.get_bars` (Research-Seam) wird in Block A nicht angefasst. | Soll nach Block B neu gemessen werden. |
| **L16** | Phase 13 = Live-Datenfundament, V4 → Phase 14 (jetzt: Phase 15). | Nikinger 2026-08-18, dritte Umnummerierung 2026-08-22. |
| **L17** | Latenzanforderung = datenklassen-spezifisch. Preisreihe live, Begleitgrößen dürfen verspätet sein. | Nikinger 2026-08-18; ordnet S3-Auswahl neu. |

### §1.4 Drei nachgemessene Befunde (F1/F2/F3, die Lehre hinter den Locks)

| Befund | Wirkung | Gelockt durch |
|---|---|---|
| **F1** — `IX.D.IBEX.FWM2.IP` trägt 301 IG-Bars mit `ts_utc` 2026-07-17, `fetched_at` 2026-08-18. IG liefert tote Historie mit `ok=True`. | Sampler war strukturell blind (F2). Stale-Source-Status wurde ergänzt. | L8 + A4 + A6 |
| **F2** — `DivergenceSampler` ankerte das Vergleichsfenster am IG-Bar-TS, kein yF-Fenster wenn IG-TS veraltet ⇒ stiller `return`. | 0 Events bei 12 Samples. Sampler jetzt rendite-basiert. | A6 (compute_return_divergence statt compute_divergence_pct) |
| **F3** — `resolve_paper_trade` filtert nur `ts >= created_utc` und prüft SL unbedingt vor Time-Stop. Mitten-Lücke ⇒ erfundene `TIME_STOP`-Zeile. | `window_ok`-Guard vor `resolve_paper_trade`, beide Schwellen (Dichte + Lücke). | L3 + A3 |

### §1.5 Drei Schnittstellen, die Phase 14 erbt

| Schnittstelle | Heute | Phase 14 (geplant) |
|---|---|---|
| **`EPIC_MAP = {"IX.D.DAX.IFMM.IP": "DE40", "IX.D.CAC.IFE.IP": "FR40"}`** in `phase13_live_data/live_data/backfill.py:67-72` | hardcoded, 2 Keys | `instrument_source_availability`-Tabelle; Map verschwindet |
| **Path C Dukascopy** (für SP35 / IBEX) | offen, ToS-Klausel von Nikinger ausgelegt (privater Single-User-Store) | `dukascopy.Source()` als Quell-Registry-Zeile, kein Backfill-Code |
| **Auto-Gap-Fill-Scheduler** (Cron-Logik, tägliche Lücken ≥ 60 min schließen) | nicht implementiert | Operator-Trigger nach Phase-14-Tabelle, **nicht** in Phase 13 nachholen |

---

## §2 As-Built-Zahlen (heute 2026-08-22, read-only gegen `data/bars.sqlite`)

### §2.1 Substrat

| `source` | Bars | Epics | Anmerkung |
|---|---:|---|---|
| `yf` | 11 654 | mehrere | Recorder läuft, kostenlos |
| `ig` | 2 230 | mehrere | historisch, vor dem Schnitt |
| `capital` | 962 | `IX.D.CAC.IFE.IP` (481), `IX.D.DAX.IFMM.IP` (481) | Pfad B live-verifiziert 2026-08-22 |
| `ls` | 0 | — | B0 = NO, Code dormant; TickAgg-Pfad im Scheduler noch nicht live |

**Total: 14 846 Bars** in `data/bars.sqlite`. Das ist das **Substrat**, gegen das Phase 14
seine `instrument_source_availability`-Tabelle füllen wird.

### §2.2 `source_spend`-Ledger (Top 5 nach ts_utc, IG)

| ts_utc | source | points | kind |
|---|---|---:|---|
| 2026-08-18 14:08:09 | ig | 301 | research |
| 2026-08-18 13:41:48 | ig | 301 | research |
| 2026-08-18 13:41:48 | ig | 301 | research |
| 2026-08-18 13:41:48 | ig | 301 | research |
| 2026-08-18 13:41:48 | ig | 301 | research |

**Beobachtung:** kein einziger `tracker`-Eintrag. L12 (strukturelle Kostenzusicherung)
hält den Auflöse-Pfad kauf-frei. Research-Spend ist 2026-08-18 noch hoch (P12.5-Rest),
aber **nicht** der Tracker-Pfad.

### §2.3 Bars-Schema

```
epic TEXT, resolution TEXT, ts_utc TEXT, open REAL, high REAL, low REAL,
close REAL, volume REAL, source TEXT, fetched_at TEXT, tick_count INTEGER
```

`tick_count` wurde in Block A2+A5 ergänzt; `ensure_schema()` migriert eine
Pre-Phase-13-DB idempotent (Phase 12 D4). Production-DB hat die Spalte seit
Commit `c8c39e6` (2026-08-19).

### §2.4 Capital.com-Live-Lauf 2026-08-22 (verbatim aus Nikinger-Operator-Run)

```
"bars_written_total": 962,
"results": {
  "IX.D.DAX.IFMM.IP": 481,
  "IX.D.CAC.IFE.IP": 481
}
```

Fenster: 2026-08-21T08:00:00Z – 2026-08-21T16:00:00Z (UTC), Demo-Konto, kostenlos.
Session-13-Bugfix (`ensure_schema()` vor `insert_bars`) hält live. Siehe
Phase-13-Kopf für den vollständigen Live-Verified-Block.

---

## §3 Was bewiesen ist vs. was nicht (Test vs. Live vs. Produktion)

| Artefakt | Beweis-Art | Beleg |
|---|---|---|
| **L12: Tracker-Pfad gibt 0 IG-Punkte aus** | **Strukturell, Test** | `phase12_data_foundation/tests/test_service.py::test_get_window_never_fetches` — beide Provider werfen `AssertionError` auf `get_bars`, `get_window` gibt `[]` zurück, wirft nicht. |
| **F3: Mitten-Loch erzeugt keine erfundene `TIME_STOP` mehr** | **Strukturell, Test** | `phase10_v3/tests/test_paper_engine.py::test_window_ok_mitten_loch_blocks_fabricated_time_stop` — derselbe Bar-Satz, ohne Guard `RESOLVED/TIME_STOP`, mit Guard `OPEN/exit_reason=NULL`. |
| **F1/F2: Stale-Source-Status + renditebasierter Vergleich** | **Code, Test** | `phase12_data_foundation/tests/test_heartbeat.py` (A6-Tests, +7). **Nicht live:** die ersten 5 Beweiswochen-Tage werden zeigen, ob der Sampler auch gegen echte Stale-Source-Events scharf stellt. |
| **B0: `CHART:`-Pfad liefert auf diesem Konto** | **Live, negativer Befund** | `probe_chart_stream.py` 2026-08-19 = NO. Folge: TickAggregatorRecorder ist der aktive S1-Pfad. |
| **C1 Pfad B: Capital.com DE40+FR40 live** | **Live, positiv** | 962 Bars im Archiv, exakt Erwartung (Session 13). |
| **C1 Pfad C: Dukascopy** | **Nicht live** | bewusst deferred; ToS-Auslegung gilt (Nikinger 2026-08-19). |
| **Beweiswoche P1–P9** | **Nicht gelaufen** | operator-getrieben, separater Track. |
| **`tick_count`-Round-Trip (A2+A5)** | **Test, Schema-validiert** | `test_get_window_passes_through_tick_count` + `PRAGMA table_info`-Probe. |

---

## §4 Beweiswoche (Phase 13, separat) — was sie zeigen muss

**Setup** (Plan §7 + Re-Plan §4):
- Operator-Freigabe für den ersten Neustart mit Messarm (A7-Operator-Sequenz im
  `PHASE13_A_BLOCK_A_CLOSEOUT.md`).
- Täglich: `python phase12_data_foundation/scripts/data_health.py` (Exit 0 erwartet).
- Wöchentlich: `python phase13_live_data/scripts/source_delta.py --days 5`.

**PASS-Kriterien (P1–P9, Plan §7, neu zu messen gegen den heutigen Substrat-Stand):**

| # | Kriterium | Heute beweisbar? |
|---|---|---|
| **P1** | Tracker-Pfad gibt 0 IG-Punkte aus | ✅ L12-Test grün; P1-Beweis wartet auf Beweiswoche-Live (`source_spend` über die Woche) |
| **P2** | Jede aufgelöste `paper_trades`-Zeile hat `resolution_source ≠ NULL` | ⏳ Beweiswoche |
| **P3** | Keine Auflösung aus ungedecktem Fenster | ✅ L3-Code + Mitten-Loch-Test; Live-Beweis wartet auf Beweiswoche |
| **P4** | LS liefert an 5/5 Handelstagen für jede `ok`-Epic | ❌ `ls`-Quelle hat 0 Bars; TickAgg-Pfad wartet auf ersten Lauf |
| **P5** | Tages-Abdeckung ≥ `MIN_WINDOW_RATIO` an ≥ 4/5 Tagen | ⏳ Beweiswoche |
| **P6** | Quellen-Delta-Report beziffert „Quelle dreht das Ergebnis" | ✅ `source_delta.py` existiert, 7 Tests, Live-Substrat jetzt 962 `capital`-Bars |
| **P7** | IG-Wochenverbrauch < 1500, kein 403 | ⏳ Beweiswoche; Ledger bereits frei von `tracker`-Spend |
| **P8** | 5/5 Tage `measurement_heartbeat`, Problemtag am selben Tag CRITICAL | ⏳ Beweiswoche |
| **P9** | Kein Epic mit toter Historie steht auf `ok` | ✅ F1-Code + Stale-Assertion; Live-Beweis wartet auf ersten Stale-Event |

**Was das für die nächste Session bedeutet:** Beweiswoche kann **parallel** zur
Phase-14-Planung laufen — die zwei Tracks stören einander nicht. Die
Phase-14-Planning-Session braucht keine Beweiswoche-Ergebnisse, um ihren Plan zu
schreiben; sie braucht sie nur, um D2–D? (Quell-Profile-TTL, Caching-Strategie)
zu kalibrieren.

---

## §5 Offene Entscheidungen (mit Empfehlung, nicht als Fragen ins Leere)

| # | Entscheidung | Optionen | Empfehlung | Was daraus folgt |
|---|---|---|---|---|
| **E1** | **Phase-14-Plan-Reihenfolge** | (a) Decisions D1–D? zuerst, dann Schema; (b) Quell-Profile-Mock zuerst (testbar ohne DB), dann Schema; (c) Schema zuerst, dann Profile | **(b) Mock zuerst** | Der Mock ist offline testbar, liefert die Schnittstelle, an der die Tabelle entlangläuft. Schema-Migration ist erst nötig, wenn der Mock-Contract fest ist. Vermeidet die Migration-zurück-Rolle. |
| **E2** | **Profil-Cache-TTL** | (a) täglich (1× pro Handelstag); (b) wöchentlich; (c) on-demand mit manueller Invalidierung | **(b) wöchentlich** | Täglich kostet ohne Mehrwert (Quell-Liefer-Spektrum ändert sich nicht täglich). On-demand ist operator-fehler-anfällig. Wöchentlich matched den Beweiswoche-Turnus. |
| **E3** | **Dukascopy-Code in Phase 14** | (a) Ja, mit Phase-14-Tabelle; (b) Nein, Dukascopy-ToS zu heikel; (c) Mock-only (Tabelle kennt Dukascopy, aber kein echter `dukascopy.Source()`) | **(c) Mock-only zuerst** | Die Tabelle kennt die Zeile, der `fetch`-Pfad wirft `NotImplementedError("Dukascopy-Backfill deferred")`. Phase 14 schließt die Architektur; der echte Dukascopy-Backfill ist ein eigener Folge-Track. |
| **E4** | **Phase-14-Cross-Phase-Freigabe** | (a) jetzt einholen, bevor Plan-Session startet; (b) erst beim ersten Code-Edit; (c) im Plan dokumentieren, vor dem ersten Edit einholen | **(a) jetzt** | Die Plan-Session braucht die Liste der Cross-Phase-Touches (Phase 2 / 3 / 9 / 13), um den Plan überhaupt schreiben zu können. Nikinger weiß dann schon, was kommt. |
| **E5** | **Phase 13 Status in Root-CLAUDE.md** | (a) „abgeschlossen"; (b) „abgeschlossen (Beweiswoche separat)"; (c) „🔄 code-complete, Beweiswoche läuft" | **(b)** | Beweiswoche ist ein realer Validierungstrack, nicht ein Phase-13-Reopen. Die Wortwahl vermeidet die „ist das wirklich fertig?"-Verwirrung. (Aus dieser Session aufgeschoben — Modul-Tabelle-Fix + Root-Update folgen in einer eigenen Doc-Session.) |
| **E6** | **Module-Tabelle-Korrektur im Phasenkopf** | (a) jetzt, im selben Status-Commit; (b) eigener Doc-Commit; (c) gar nicht, der Re-Plan ist die kanonische Aussage | **(a)** | Eine Review-Stelle, ein Commit, eine Frage „stimmt das Modul-Listing?" — alles andere macht es schlimmer. (Aus dieser Session aufgeschoben.) |
| **E7** | **Soll die Beweiswoche die Phase-14-Plan-Session blockieren?** | (a) Ja, erst P1–P9 grün, dann Phase 14; (b) Nein, parallel | **(b) parallel** | Phase 14 ist Architektur, Beweiswoche ist Validierung. Die Plan-Session braucht die Beweiswoche nur für E2 (TTL), und das ist eine Optimierung, kein Blocker. |

---

## §6 Was Phase 13 *nicht* macht (Out-of-Scope, Verweis auf Plan §10)

Reproduziert aus dem Hauptplan, hier mit Verweis auf den aktuellen Stand:

- **WI-2/W2-Auswertung + H-Serie** — Phase-11-Wiederaufnahme nach bestandener Beweiswoche.
- **Research-Funnel-Fix** (0-Kandidaten-Problem, W1/W5) — eigenes Thema, entkoppelt über Shadow-Schedule.
- **`BarService.get_bars`-Research-Seam** — L15 (Hauptplan), erst nach Block B neu messen.
- **`resolve_paper_trade` selbst** — unangetastet, der Guard sitzt davor (L3, A3).
- **Momentum-VETO, Gates, Sizing, P6, P7** — L13 (Hauptplan).
- **B3 Margin-Headroom, Council-Paper-Call-Aktivierung, UI, Live-Konto, `lesson_embeddings`** — Phase 14+ / Phase 15, nicht Phase 13.
- **Lightstreamer für Live-Quotes im Research-Kontext** (P9 Step 7b) — bleibt geparkt; S1 hier ist Archiv-Mitschrieb, ein anderer Zweck.
- **Ein Revert der fünf P12.5-Fixes** — L14 (Hauptplan).
- **Status-Updates in Root-`CLAUDE.md`, `ROADMAP.md`, Phasenkopf-Modul-Tabelle, Session-15-Block** — bewusst aufgeschoben aus dieser Session (nur Doku-Files: Handover + SVG + INDEX-Eintrag).

---

## §7 Was diese Session gemacht hat — und was nicht

**Diese Session (2026-08-22, 15. Session auf Phase 13, diesmal Read-only):**
- As-Built gegen Code, Tests, Git-Historie und `data/bars.sqlite` (mode=ro) selbst nachgemessen.
- Phase-13-Status ehrlich: Code-complete + live-verifiziert für DE40/FR40, Beweiswoche offen.
- Drei Schnittstellen benannt, die Phase 14 erbt (EPIC_MAP, Path C, Auto-Gap-Fill).
- Sieben offene Entscheidungen mit Empfehlung formuliert (E1–E7).
- Cross-Phase-Berührungspunkte für die Phase-14-Plan-Session zusammengetragen.

**Was diese Session bewusst NICHT gemacht hat** (bleibt für eine Status-Session):
- Root-`CLAUDE.md` Phase-13-Row auf „abgeschlossen" — wartet auf die Status-Commits, in
  denen Modul-Tabelle + Phase-Status zusammenfließen.
- `ROADMAP.md` Phase-13-Section auf „abgeschlossen" — gleicher Grund.
- `phase13_live_data/CLAUDE.md` Modul-Tabelle 4× Korrekturen (Test-Count 39→50,
  Block-C-Zeilen auf „PARTIAL, final") — Session-15-Block begleitet das.
- `phase13_live_data/CLAUDE.md` Session-15-Block (Phase-13-Closout-Handover) +
  Rotation Session 14 → `SESSIONS_ARCHIVE.md` — gehört in die Status-Commits.

**Push-Freigabe:** erteilt 2026-08-22 (40 Commits synchron, Stand `18dafd9`).
