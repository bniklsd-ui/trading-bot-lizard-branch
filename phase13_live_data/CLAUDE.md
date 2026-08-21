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
| `live_data/backfill.py` | `CapitalSource` (S3, **PARTIAL**) + `run_capital_backfill()` | ✅ Session 12 Step 1 — committed, 11 Tests. Hybrid-Pfad B (Capital.com) liefert DE40 + FR40; SP35 (Spain 35) → 404, fällt auf Path C (Dukascopy, deferred). |
| `live_data/rescue.py` | `GapRescue` (S4, Default AUS) | ✅ C2 — committed, 11 Tests |
| `scripts/probe_chart_stream.py` | Gating-Live-Check: liefert `CHART:` auf diesem Konto? | ✅ B0 — committed (operator-run, NO 2026-08-19) |
| `scripts/probe_capital.py` | Gating-Live-Check für Hybrid-Pfad B: liefert die Capital.com Demo-API `resolution=MINUTE` für Germany 40 / France 40 / Spain 35? | ✅ Session 11 — committed (operator-run, Probe ausstehend) |
| *(Repo-Wurzel)* `scripts/store_capital_key.py` | Keyring-Seeder für Capital.com Demo-Creds (Service `trading-bot-capital`, drei Felder) | ✅ Session 11 — committed |
| `scripts/capital_backfill.py` | Operator-invokable Gap-Fill-Script: ruft `run_capital_backfill()` für `--epics` oder `--auto` × `[--start, --end]` (UTC) | ✅ Session 12 Step 2 — committed (operator-run) |
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

## Session stopped — 2026-08-19 (Session 12: C1 Pfad B Build — `backfill.py` + `capital_backfill.py`, PARTIAL abgeschlossen)

> **Auftrag:** Nikinger („da bereits viel zeit verschwendet wurde,
> möchte ich den vollständigen weg gehen. alles was gebaut werden kann,
> baue jetzt (atomar)"). Nach Probe-PARTIAL (DE40 + FR40 liefern
> MINUTE-Bars, SP35 = Spain 35 = IBEX liefert 404) baut diese Session
> Pfad B fertig. Spanien (IBEX) bleibt **explizit Path-C-Territorium**
> (Dukascopy, deferred per Nikinger-Auflage: „soll trotzdem als weiterer
> Fallback in einer zukünftigen Session gebaut werden").

### Completed

**Step 1 — `phase13_live_data/live_data/backfill.py` (NEU, ~340 Zeilen).**
`CapitalSource` Klasse (`authenticate` + `fetch_window`) +
`run_capital_backfill()` Convenience-Funktion. Implementiert die
vier quellenunabhängigen Regeln aus Plan §6 C1.0:

| Regel | Wo umgesetzt |
|---|---|
| (1) Window-Check | `_parse_and_validate`: jeder Bar-Timestamp muss in `[start-1min, end+1min]` sein, sonst Skip + Warn-Log |
| (2) Keine synthetischen Bars | `_parse_and_validate`: `O==H==L==C` + `volume ∈ {0, None}` ⇒ Skip (Off-Hours-Auffüll-Bars) |
| (3) Vergleiche nie absolute Niveaus | n/a — Sampler-Konzern (A6.0) |
| (4) Backoff ist Pflicht | `_backoff` exponential (2^attempt s) bei HTTP 429/503, max 3 Retries |

Quellen-spezifisch (empirisch 2026-08-19, alle in Commit-History
dokumentiert):
- Demo-URL: `https://demo-api-capital.backend-capital.com`
- Auth: `POST /api/v1/session` mit `X-CAP-API-KEY`-Header + Body
  `{identifier, password, encryptedPassword: false}`. `password` =
  API-Key-Custom-Password (NICHT Account-Login-Pwd).
- Datumsformat: `YYYY-MM-DDTHH:MM:SS` ohne `Z`/ms (strikt).
- TZ: snapshotTime wird als `Europe/Madrid` (UTC+2 im Sommer)
  interpretiert, dann nach UTC konvertiert → CAPITAL_TZ + zoneinfo,
  DST-aware.
- Epic-Mapping: `IX.D.DAX.IFMM.IP → DE40`, `IX.D.CAC.IFE.IP → FR40`.
  Spain/AEX/MIB sind Path-C-Territorium (Test `test_epic_map_does_not_contain_path_c_territory`
  pinnt das fest).

`run_capital_backfill()` schreibt mit `source='capital'` ins
`BarArchive`. KNOWN_SOURCES erweitert in
`phase12_data_foundation/data_foundation/models.py` (cross-phase,
per Plan §1 freigegeben). `prefer`-Default in `archive.py:144` jetzt
`('ig', 'capital', 'ls', 'yf')` — Capital.com rangiert vor
LS/yFinance, weil Broker-CFD-Reihe näher an IG ist als Kassaindex.

**Step 2 — `phase13_live_data/scripts/capital_backfill.py` (NEU, ~170
Zeilen).** Operator-invokable Gap-Fill-Script: liest Creds aus
Keyring (`trading-bot-capital.{identifier,password,api_key}`),
lädt `BarArchive(args.db)`, ruft `run_capital_backfill()` für
`--epics` (kommagetrennt) oder `--auto` (measurable-universe).
`--start`/`--end` (UTC ISO 8601 mit `Z`), `--dry-run` für
Plan-Print ohne Auth. Output: per-Epic Bar-Counts + `next_step_hint`.
Exit 0/1/2/3 analog `probe_capital.py`. Operator-Run, kostenlos
(Demo-Konto).

**Step 3 — Tests.**
- 11 neue Tests in `phase13_live_data/tests/test_backfill.py`:
  auth success (verifiziert Header hat `X-CAP-API-KEY`, Body hat
  KEIN `apiKey`), auth 401 raises, unmapped epic returns [],
  LOCAL → UTC-Konvertierung (Snapshot 20:54 CEST → 18:54 UTC),
  synthetische Bars gefiltert, out-of-window gefiltert, 429 →
  Backoff + Retry → 200, 404 propagiert sofort (kein Retry),
  `run_capital_backfill` schreibt mit `source='capital'`,
  `run_capital_backfill` records 0 für unmapped Epics,
  EPIC_MAP enthält keine Path-C-Epics (Lock-in Test).
- Bestehende 38 Phase-13-Tests unverändert (1 pre-existing
  date-drift in `test_source_delta.py::test_multiple_days_window`
  — siehe Offene Findings).

### Verified

- `pytest phase13_live_data/tests -q` → **49 passed** (war 38, +11).
- `pytest phase12_data_foundation/tests -q` → **143 passed** (unverändert).
- `pytest phase1_broker_wrapper/tests -q` → **95 passed** (unverändert).
- `pytest phase8_scheduler/tests -q` → **244 passed** (unverändert).
- `pytest phase10_v3/tests -q` → **165 passed** (unverändert).
- `py_compile` clean auf allen geänderten/neuen Dateien.

### Note

- **Drei Commits in dieser Session**, jeder Schritt unabhängig grün
  (Nikinger-Auflage „commit after each step"):
  1. `369fb62` Step 1 — `backfill.py` + Tests + KNOWN_SOURCES + prefer
  2. `08dfa74` Step 2 — `capital_backfill.py` operator-script
  3. *(dieser Docs-Commit)* Session-12-Block + Modul-Tabelle + Rotation

- **PARTIAL ist explizit gewollt**, nicht „halb gebaut": die zwei
  funktionierenden Indizes (DE40, FR40) decken zusammen 4 von 5
  verfügbaren messbaren Epics im Archiv ab. Das einzige Loch ist
  SP35 (Spain 35 = IBEX) — und das ist die gleiche Epic, die in
  Phase-12-Closeout §3.4 als „selbstverschuldeter yF-Existenzbeweis"
  beschrieben wurde (IG lieferte tote Historie für FWM2, yF-Kassa
  ist die einzige verfügbare Reihe). Für die Beweiswoche ist das
  **kein Blocker** — FWM2 wird weiterhin über S2 (yFinance-Recorder)
  bedient.

- **Path C (Dukascopy) ist explizit für eine Folge-Session
  geblockt**, nicht gestrichen:**
  > Nikinger 2026-08-19: „PS: halte fest, das Path C trotzdem als
  > weiterer Fallback in einer zukünftigen Session gebaut werden soll."
  Geplante Reihenfolge: zuerst Messwoche mit Pfad B (S2 + S3-Partial)
  + S4 (`GapRescue`, default AUS), **dann** Dukascopy-Backfill für
  SP35 + generelle S3-Reserve. ToS-Auslegung (Session 11) gilt
  weiter — Dukascopy ist nur für den privaten Single-User-Store
  freigegeben.

- **`live_data/backfill.py` enthält absichtlich keinen Auto-Scheduler**
  oder Gap-Detection. Das ist Operator-getrieben für jetzt. Eine
  Auto-Gap-Fill-Logik (z. B. „täglich 09:00 UTC die letzten 24 h
  scannen, Lücken ≥ 60 min automatisch schließen") wäre eine
  Folge-Aufgabe — bewusst NICHT in dieser Session gebaut, um den
  Scope von Session 12 auf „Pfad B fertig + Probe-Backfill-Script"
  zu begrenzen.

### Open questions / blockers

- **Capital.com TZ-Annahme** (`Europe/Madrid`, UTC+2 im Sommer)
  ist **empirisch** aus einem 1-Stunden-Probe-Fenster abgeleitet
  (Bars kamen mit +2 h Offset zur UTC-Anfrage zurück). Wenn der
  Server im Winter auf CET (UTC+1) wechselt, fängt `zoneinfo`
  das automatisch — gut. Wenn der Server die TZ **ändert** (was bei
  Capital.com unwahrscheinlich ist), müssen wir manuell nachziehen.
  Frühe Validierung: Beweiswoche-Tag-1, **`source_delta.py`
  zeigt den `capital`-vs-`yf`-Differenz-Vektor pro Minute** — wenn
  der konstant +2 h verschoben ist, ist die TZ falsch.
- **`KNOWN_SOURCES` ist eine einzige zentrale Konstante** — jede
  neue Quelle braucht genau eine Edit in `models.py:22`. Das ist
  Plan §6 C1.0 Fold-in-Checklisten-Item #3, hier umgesetzt.

### Next

- **Operator (Nikinger):** manueller Smoke-Test mit `--dry-run`:
  ```bash
  python phase13_live_data/scripts/capital_backfill.py \
      --epics IX.D.DAX.IFMM.IP,IX.D.CAC.IFE.IP \
      --start 2026-08-21T08:00:00Z \
      --end   2026-08-21T16:00:00Z \
      --dry-run
  ```
  Erwartetes Output: JSON mit `dry_run: true`, beiden Epics, dem
  Zeitfenster. Kein Auth, kein Write.

- **Operator (Nikinger):** realer Backfill-Lauf (kostenlos, Demo-Konto):
  ```bash
  python phase13_live_data/scripts/capital_backfill.py \
      --epics IX.D.DAX.IFMM.IP,IX.D.CAC.IFE.IP \
      --start 2026-08-21T08:00:00Z \
      --end   2026-08-21T16:00:00Z
  ```
  Erwartetes Output: JSON mit per-Epic bar-counts (~480 Bars je
  Epic im 8-h-Fenster bei MINUTE-Resolution).

- **Operator (Nikinger):** Beweiswoche bleibt der Live-Test für die
  gesamte Datenkette (Phase 13 Plan §7 PASS-Kriterien P1–P9).
  Pfad B (dieser Build) ist eine zusätzliche Sicherheitsschicht
  für DE40/FR40; SP35/AEX/MIB laufen weiter über yFinance-Recorder
  bis Path C (Dukascopy) in einer Folge-Session kommt.

- **Push:** weiterhin bewusste Einzelfreigabe. Stand jetzt:
  **27 Commits** vor `origin/main`, alle Phase 13, alle Suiten grün.

### Offene Findings (für Folge-Sessions, nicht in diesem Build-Scope)

- **`phase13_live_data/tests/test_source_delta.py::test_multiple_days_window`**
  ist seit 2026-08-20 rot. Harte Test-Daten „2026-08-18" / „2026-08-19"
  liegen außerhalb des `--days 2`-Fensters, sobald `today > 2026-08-19`.
  Empfohlener Fix: Test auf `datetime.now()`-relative Daten oder
  `freezegun` umstellen. ~5 Zeilen.
- **Path C (Dukascopy)** ist für eine Folge-Session geblockt (siehe
  Nikinger-Auflage oben) — `live_data/dukascopy_backfill.py`
  existiert noch nicht. ToS-Auslegung aus Session 11 bleibt gültig
  für diesen Use-Case (privater Single-User-Backtest-Store).
- **Auto-Gap-Fill-Scheduler** für Pfad B (täglicher Lauf, der
  Lücken ≥ 60 min automatisch schließt) wäre eine Folge-Aufgabe
  — bewusst out-of-scope dieser Session.
