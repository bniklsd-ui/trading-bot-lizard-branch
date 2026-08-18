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

## Session stopped — 2026-08-18 (Session 4: Block A2 — der Schnitt in BarService.get_window)

> **Auftrag:** Step A2 (Plan §6, Zeile 604). `BarService.get_window` zu einer reinen
> Archiv-Lesung kürzen — der strukturelle Schnitt, danach kauft der Tracker-Pfad
> per Konstruktion **null** IG-Punkte. L12-Test ist die Akzeptanz.

### Completed

1. **`data_foundation/service.py`** — `get_window` ist jetzt eine **reine Archiv-Lesung**:
   `return [_bar_to_dict(b) for b in self._archive.window(...)]`. Gelöscht: `_MIN_WINDOW_COVERAGE`
   (Zeile 38, mit dem `# ponytail:`-Kommentarblock), `_covers_tail` (Funktion + Aufruf),
   `self._ig_provider` (Attribut + Zuweisung), den Vollfenster-Refetch (`service.py:222-227`)
   und den IG-Top-up-Zweig (`service.py:229-238`). Ebenfalls gelöscht: `_parse_iso` (nur in
   `_covers_tail` verwendet, danach unbenutzt — vor der Löschung gegepptet, keine weiteren
   Aufrufer). `_bar_to_dict` trägt jetzt `"tick_count": getattr(bar, "tick_count", None)`.
   Modul- und Klassen-Docstrings sind komplett umgeschrieben — der alte Text beschrieb den
   Fetch-Pfad, den es nicht mehr gibt.
2. **`data_foundation/models.py`** — `Bar` bekommt `tick_count: int | None = None` **am Ende**
   der Dataclass. Default `None` ist Pflicht, sonst brechen die 24 bestehenden `Bar(...)`-
   Konstruktionen (alle mit keyword args, gegepptet).
3. **`data_foundation/archive.py`** — drei kleine Schema-Anpassungen, damit `tick_count`
   tatsächlich round-trippt: Spalte `tick_count INTEGER` in `_CREATE_BARS` (für frische DBs),
   idempotenter `ALTER TABLE bars ADD COLUMN tick_count INTEGER` in `ensure_schema` (für
   bestehende DBs), Spalte + Platzhalter in `insert_bars`. `Bar(...)`-Projektion in `window()`
   nutzt `row["tick_count"] if "tick_count" in row.keys() else None` — defensiv, falls eine
   DB ohne `ensure_schema` gelesen wird.
4. **`tests/test_service.py`** — umgeschrieben: 6 get_window-Tests, die das gelöschte Verhalten
   pinnten, gelöscht; 6 neue Tests dafür. **L12-Test** (`test_get_window_never_fetches`):
   beide Provider werfen `AssertionError` auf `get_bars`, `get_window` über leeres Archiv
   gibt `[]` zurück und wirft nicht. **`test_get_window_passes_through_tick_count`**:
   Insert mit `tick_count=42`, Read, Wert stimmt. **`test_get_window_tick_count_defaults_to_none_for_old_rows`**:
   Bar ohne `tick_count` → `None` im Dict (alte Zeilen). **`test_bar_service_has_no_ig_provider_attribute`**:
   Struktur-Guard gegen ein stilles Wieder-Aufreißen. **`test_get_window_returns_archive_rows_only`**
   + **`test_get_window_empty_archive_returns_empty`**: das, was `get_window` jetzt **ist**.
5. **`tests/test_step7_integration.py`** — die drei `_covers_tail`-Kommentarzeilen aktualisiert
   (Fenster-Endkapselung statt Schwanz-Check). Der Test selbst war strukturell richtig und
   ist ohne Änderung grün.
6. **Rotation:** Session-3-Block verbatim nach `SESSIONS_ARCHIVE.md` verschoben.

### Verified

- `pytest phase12_data_foundation/tests -q` → **134 passed** (war 135; −7 gelöschte Tests + 6 neue;
  die 12 A1-Tests bleiben unangetastet, die 1 zusätzliche Coverage-Differenz rührt vom
  ersatzlosen Streichen der Refetch-Tests, nicht von A1).
- Voller Regression-Sweep, **alle 12 Suiten grün**, geteiltes Venv (`phase1_broker_wrapper/.venv`):
  | Phase | Tests |
  |---|---|
  | phase1_broker_wrapper | 87 |
  | phase2_persistence | 77 |
  | phase3_external_data | 104 |
  | phase4_research | 155 |
  | phase5_execution | 173 |
  | phase6_debate | 76 |
  | phase7_execution | 138 |
  | phase8_scheduler | 237 (+1 Deprecation-Warning, harmlos) |
  | phase9_universe | 80 |
  | phase10_v3 | 160 |
  | phase12_data_foundation | 134 |
  | meta_m1_harness | 28 |
- `grep -nE "_covers_tail\|_MIN_WINDOW_COVERAGE|_ig_provider" phase12_data_foundation/data_foundation/`:
  **leer** — alle drei Symbole wirklich weg. Verbleibende Treffer in `tests/test_service.py:119,133,284,286,290`
  sind Test-Namen / -Docstrings, die **explizit** vom gelöschten Attribut handeln
  (`test_ig_provider_*` = `BudgetedIGBarProvider`, `test_bar_service_has_no_ig_provider_attribute`
  = der Struktur-Guard).
- `git diff --stat HEAD` → **net −57 Zeilen** (170 Löschungen, 113 Ergänzungen) — der Schnitt
  ist netto eine Löschung, wie L2 verlangt.
- `get_window`-Aufrufer in `phase8_scheduler/scripts/wiring.py` (Zeilen 191, 195, 209, 245, 523)
  bleiben binär-kompatibel: Signatur `get_window(epic, resolution, start_utc, end_utc)` ist
  unverändert. Die dortigen Kommentare über „BarService.get_window's own budget-aware chain"
  (Zeilen 478, 480, 483) sind jetzt **stale** — das ist A3s Job (Plan §6 A3, dort verbatim
  genannt: „Der Kommentarblock über `_PAPER_MAX_FETCH_ATTEMPTS` … beschreibt den alten
  Zustand — korrigieren, nicht löschen").

### Note

- **A5-Teilarbeit in A2:** der `tick_count`-Round-Trip brauchte Spalte + INSERT + Projection.
  Das ist die **kleinste Ecke** von A5 (Plan §6 A5), ohne die A2s `_bar_to_dict` keinen
  sinnvollen Test hätte. A5 selbst bleibt offen (drei weitere Dinge: `sources`-Filter,
  `_CREATE_BARS` ist hier schon dabei, `KNOWN_SOURCES`/`prefer`-Default — kein Bruch, nur
  Vorgriff auf den reinen Datenträger).
- Netto-Diff: −57 Zeilen Service-Code (überwiegend Löschungen), 6 Tests umgeschrieben, 1
  Dataclass-Feld, 5 Schema-Zeilen. Kein Eingriff in laufende Komponenten. Bot steht weiterhin,
  Recorder sammelt kostenlos weiter.
- **Was A2 leistet, was A2 nicht leistet:** A2 macht den Tracker-Pfad **strukturell**
  kauf-unfähig — der IG-Provider wird nicht mehr aufgerufen, egal welche Parametrisierung
  jemand morgen wählt. Das beantwortet L12 (P1, P7). A2 macht **nicht** aus einem leeren
  Archiv eine Auflösung — das ist A3s Job (das `window_ok`-Guard vor `resolve_paper_trade`,
  das genau F3 fängt: Mitten-Loch → erfundene `TIME_STOP`).

### Next

- **Pause für Nikinger-Bestätigung** (geplant war das bereits im Session-3-Block): A2 ist
  der strukturelle Schnitt, der **per Konstruktion** den IG-Verbrauch auf dem Tracker-Pfad
  stoppt. A3 fügt die `window_ok`-Naht in `paper.py` und `wiring.py` ein (cross-phase) —
  danach würde eine `TIME_STOP`-Auflösung aus einem ungedeckten Fenster **nicht mehr**
  entstehen (F3). Beide Schritte greifen ineinander; A3 ohne A2 ließe den alten Code
  zynisch weiterleben, A2 ohne A3 ließe weiterhin erfundene `TIME_STOP`-Zeilen zu.
- **Bestätigungs-Punkt:** Soll A3 jetzt direkt starten, oder erst ein Trockenlauf des
  Schnitts (z. B. ein kurzer Commit + Smoke auf main, damit vor dem ersten echten
  Scharfschalten klar ist, dass der Build sauber ist)?
- **A3 konkret** (Plan §6, Zeile 647): `phase10_v3/abstain_lessons/paper.py` bekommt einen
  `window_ok`-Param am Konstruktor **und** den Guard in `_resolve_group` **vor**
  `resolve_paper_trade`. `wiring.py:_build_paper_tracker` baut die Closure, die
  `assess_window` aufruft, und injiziert sie. Der Mitten-Loch-Test (F3) ist der wichtigste
  Test des ganzen Blocks.
- **A4–A7** folgen A3 in der Reihenfolge L4. A4 ist die Stale-History-Assertion in
  `BudgetedIGBarProvider` (L8, F1). A5 die `sources`-Filter-Erweiterung (L10). A6 die
  Heartbeat-/Sampler-Reparatur (F1/F2 + Niveau-Vergleich → Rendite-Vergleich, A6.0). A7
  der Operator-Block mit dem Allowance-Probe und der erwarteten 0-Punkte-Bilanz.
- **Offen bis Block B0:** ob `CHART:{epic}:1MINUTE` liefert (Plan §9.2). Beide Zweige sind
  ausgeplant.
- **Offen bis Block C1:** welche Fremdquelle S3 wird (Plan §6 C1).
- **`main` liegt jetzt 7 Commits vor `origin/main`** (inkl. dieses Commits) — Push bleibt
  bewusste Einzelfreigabe des Nikinger.

### Open questions / blockers

- **Kein technischer Blocker.** Bot steht sicher, Recorder sammelt kostenlos weiter.
- **A3 ist cross-phase** (`paper.py` in `phase10_v3`, `wiring.py` in `phase8_scheduler`,
  `coverage.py` in `phase12_data_foundation`) — Plan §1 hat es freigegeben (Nikinger
  2026-08-18), aber der Übergang ist der richtige Moment für eine kurze Bestätigung, weil
  A2 ab jetzt **Produktionswirkung** hat (jeder laufende Tracker sieht ein anderes
  `get_window`).
- **Der F2-Anker** (`heartbeat.py:184-193`) ist nach A6 zu reparieren — bewusst **nicht**
  in A2 mitgenommen, weil A2 ein reiner Lese-Schnitt ist.
