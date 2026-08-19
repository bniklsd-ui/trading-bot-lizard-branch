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
| `live_data/stream.py` | `LSBarRecorder` (CHART-Pfad, dormant) + `TickAggregator` + `TickAggregatorRecorder` (PRICE-Tick-Aggregation, **S1-Primärpfad nach B0=NO**) | ✅ B2 + B0.5 — committed, 21 Tests |
| `live_data/backfill.py` | `ExternalBackfill` (S3) | 🔄 **Hybrid-Entscheidung 2026-08-19** (Nikinger): B (Capital.com) zuerst, C (Dukascopy) als Fallback wenn B definitiv nicht geht. Probe ausstehend. |
| `live_data/rescue.py` | `GapRescue` (S4, Default AUS) | ✅ C2 — committed, 11 Tests |
| `scripts/probe_chart_stream.py` | Gating-Live-Check: liefert `CHART:` auf diesem Konto? | ✅ B0 — committed (operator-run, NO 2026-08-19) |
| `scripts/source_delta.py` | Doppelauflösung je Quelle, Differenz als Messgröße (P6) | ✅ C3 — committed, 7 Tests |
| `tests/` | gemockt, kein Netz, kein LLM | ✅ 39 Tests grün |
| *(cross-phase)* `data_foundation/coverage.py` | `assess_window` / `WindowCoverage` | ✅ A1 — committed, 12 Tests grün |
| *(cross-phase)* `data_foundation/service.py` | `BarService.get_window` als reine Archiv-Lesung + Stale-Assertion | ✅ A2 + A4 — committed |
| *(cross-phase)* `data_foundation/heartbeat.py` | `DivergenceSampler` rendite-basiert + stale-Check; `assess_day` mit Coverage | ✅ A6 — committed, 143 phase12-Tests |
| *(cross-phase)* `data_foundation/archive.py` | `tick_count`-Spalte, `sources`-Filter | ✅ A2 + A5 — committed |
| *(cross-phase)* `phase1_broker_wrapper/broker_wrapper/streaming/ig_lightstreamer.py` | `subscribe_candles` + `_CandleListener` (S1 — `CHART:`-Kerzen-Abo) | ✅ B1 — committed, 26 P1-Tests |
| *(cross-phase)* `phase8_scheduler/scheduler/runner.py` | `bar_stream`-Param, `_start/_stop/_restart_bar_stream` in preflight + shutdown + _warm_session | ✅ B3 — committed, 244 P8-Tests |
| *(cross-phase)* `phase8_scheduler/scheduler/config.py` + `run.py` | `enable_bar_stream: bool = False`, `--enable-bar-stream` CLI-Flag | ✅ B3 — committed |
| *(cross-phase)* `phase8_scheduler/scripts/wiring.py` | `_mark_stale`-Closure, `window_ok` injiziert, `_PAPER_MAX_FETCH_ATTEMPTS` aktualisiert, bar_stream-Build | ✅ A3 + A6 + B3 — committed |
| *(cross-phase)* `phase10_v3/abstain_lessons/paper.py` | `window_ok`-Param + Guard in `_resolve_group`; Tracker-Stale-Mini-Step | ✅ A3 + A7.5 — committed |
| `PHASE13_A_BLOCK_A_CLOSEOUT.md` | A7 — Bestandsaufnahme, Operator-Sequenz, erreichte PASS-Kriterien | ✅ — committed |

---

## Session stopped — 2026-08-19 (Session 11: C1 — Hybrid-Entscheidung B/C + Probe-Vorbereitung)

> **Auftrag:** Nikinger („vermerke eine hybrid entscheidung: erst option B.
> nur wenn das definitiv nicht geht, dann option C"). Plan §6 C1.0
> ENTSCHIEDEN „auf nach Block B vertagt" wird hiermit **doppelt
> überschrieben**: (a) Vertagung aufgehoben (die Entscheidung fällt jetzt),
> (b) Hybrid-Wahl B-first/C-fallback statt einzelnem Kandidaten. Die
> Begründung — „Archiv ist für mich privat, sonst keine Berührung mit
> dem Internet" — wiegt die Dukascopy-ToS-Klausel
> („may not be used to construct a database of any kind") **für diesen
> Use-Case** auf: die einzige Datenbank, die das Archiv bildet, ist
> ein lokales SQLite-File im `data/`-Pfad des Nikinger-VMs, ohne
> externen Read/Write, ohne API, ohne Veröffentlichung. Die ToS-Klausel
> zielt auf redistributable, abfragbare Drittdaten-Dienste, nicht auf
> einen privaten Backtest-Store eines einzelnen Traders. **Nikinger-
> Entscheidung, dokumentiert; nicht selbst ausgelegt.**

### Completed

**C1-Hybrid-Entscheidung (gelockt, Nikinger-Override von L17-Plan §6 C1.0):**

| Pfad | Quelle | Wann |
|---|---|---|
| **B (primär)** | **Capital.com** Demo-API — Germany 40 / France 40 / **Spain 35**, `resolution=MINUTE`, REST via `requests` (Repo-Konvention). Plan §6 C1.0 „wenn früher entschieden werden soll"-Pfad. | Nikinger-Operator-Live-Check via `scripts/probe_capital.py` (kostenlos, ~80 Zeilen, analog zu `probe_chart_stream.py`). |
| **C (fallback)** | **Dukascopy** Datafeed — vollständige Abdeckung inkl. IBEX + MIB, ~90 s Verzug, stdlib `lzma`+`struct`. | Nur wenn B **definitiv** nicht geht — d.h. Probe-Exit AUTH oder NO bei allen drei Indizes. Nicht bei „liefert nur 1 von 3". |

**Begründung ToS-Klausel-Aufhebung für Dukascopy (Pfad C):**
- Dukascopy ToS: „may not be used to construct a database of any kind"
- Nikinger-Argument: das `data/bars.sqlite` ist ein **lokales,
  privates** Archiv auf dem Nikinger-VM, ohne externen Zugriff,
  ohne API-Endpoint, ohne Datenfreigabe. Der „database"-Begriff in
  der ToS zielt auf redistributable / multi-user Drittdaten-Dienste,
  nicht auf einen Single-User-Backtest-Store.
- **Risiko bleibt Nikinger-getragen.** Nicht von Claude ausgelegt —
  wenn Nikinger die ToS-Auslegung revidiert, fällt Pfad C weg und
  nur Pfad B + A (überspringen) bleiben.

**Begründung B-first statt direkt C:**
- B ist ToS-sauber (kein Cloud-Konflikt, Broker-API wie IG → andere
  Auth-Klasse aber Lizenz ok).
- B liefert als Broker-CFD-Preisreihe eine **bessere Gegenprobe**
  zu IG-CFD als Dukascopys Index-Kassa (näher an der eigenen Reihe).
- C hat die umfassendere Abdeckung (alle Indizes, lange Historie),
  ist aber nur Fallback wegen Lizenz-Eigenheit.

### `scripts/probe_capital.py` — Operator-Live-Check (kostenlos)

- Auth: POST `https://api-capital.backend-capital.com/api/v1/session`
  mit `identifier` + `password` + `apiKey` (aus Keyring-Namensraum
  `trading-bot-capital`, neuer Seeder analog zu `store_minimax_key.py`).
- Sucht drei Epics: **Germany 40** (DAX-äquivalenter CFD),
  **France 40** (CAC), **Spain 35** (IBEX). Bei jedem: `resolution=
  MINUTE`, kleines Zeitfenster (~15 Min).
- Exit-Codes analog `probe_chart_stream.py`: `0 YES` / `1 NO` /
  `2 PARTIAL` / `3 AUTH`.
- **Output:** stderr = menschliche Erzählung, stdout = JSON-`Envelope`-
  ähnliches Objekt (maschinenlesbar). Repo-Konvention
  (siehe `scripts/probe_chart_stream.py`).
- **Nicht in dieser Session gebaut** — siehe „Next".

### Was diese Session **nicht** tut (bewusst)

- Kein Code-Change außer Doku (Doku-Commit folgt; Probe-Build = nächster Schritt).
- Kein DB-Write. `live_data/backfill.py` bleibt ⬜ bis nach Probe.
- Kein Push (weiterhin Operator-Einzelfreigabe).
- Kein Override der Dukascopy-ToS in der Breite — der Override gilt
  **nur für diesen Use-Case** (privater Backtest-Store eines einzelnen
  Traders, keine externe Berührung). Sollte das Archiv jemals eine
  API, ein Web-UI oder Drittnutzer bekommen, fällt der Pfad C weg.

### Next

- **Step 2 (diese Session):** `scripts/probe_capital.py` bauen (~80
  Zeilen, operator-run, kostenlos, kognitive Spiegelung von
  `probe_chart_stream.py`) — kein Netz, kein LLM in Tests.
- **Step 3 (Nikinger-Aktion):** Keyring-Seeder
  `scripts/store_capital_key.py` + `python phase13_live_data/scripts/probe_capital.py`.
- **Step 4 (Nikinger-Decision):** Probe-Exit interpretieren:
  - `0 YES` oder `2 PARTIAL` (≥ 1/3 Indizes) → Capital.com-Backfill
    bauen (`live_data/backfill.py` nach §6 C1, vier Regeln + Fold-in).
  - `3 AUTH` → Keyring prüfen, Re-Seed, Re-Probe.
  - `1 NO` bei allen drei → **Pfad C (Dukascopy)** fällt zu, vor
    jedem Code-Build kurze Nikinger-Bestätigung der ToS-Auslegung.
- **Parallel:** Beweiswoche läuft weiter (Phase 13 Block A + S1 via
  `TickAggregatorRecorder` aktiv), kein Konflikt mit C1.
- **Push:** weiterhin bewusste Einzelfreigabe. Stand jetzt: **23 Commits**
  vor `origin/main`, alle Phase 13, alle Suiten grün.
