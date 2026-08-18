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

## Session stopped — 2026-08-18 (Session 5: Block A3 — window_ok-Guard im Tracker)

> **Auftrag:** Step A3 (Plan §6, Zeile 647). Cross-Phase-Naht: `window_ok`-Param
> in `PaperTradeTracker.__init__`, Guard in `_resolve_group` **vor** `resolve_paper_trade`,
> `wiring.py:_build_paper_tracker` baut die Closure mit `assess_window` und injiziert sie.
> **Mitten-Loch-Test (F3)** ist der wichtigste Test des Blocks. Nach A2 muss F3 enden —
> sonst landen weiterhin erfundene `TIME_STOP`-Zeilen im Messsubstrat.

### Completed

1. **`phase10_v3/abstain_lessons/paper.py`** — drei additive Eingriffe, alle
   `keyword-only`-Param am Ende der Liste, keine Signaturbrechung:
   - `__init__` bekommt `window_ok: Callable[[str, Sequence[Mapping[str,Any]], str, str], bool] | None = None`
     als letzten Parameter.
   - `self.window_ok = window_ok` (Default `None` = bit-identisch zum Alt-Verhalten).
   - `_resolve_group` setzt den Guard **vor** `resolve_paper_trade(trade, bars)` **innerhalb**
     des `try`-Blocks: `if self.window_ok is not None and not self.window_ok(...): self._charge_failed_attempt([trade], now); continue`.
     Docstring erklärt F3 und warum der Guard die U2-Mechanik wiederverwendet (Cap greift
     statt sofortigem Write-off).
2. **`phase8_scheduler/scripts/wiring.py`** — die `window_ok`-Closure sitzt in
   `_build_paper_tracker` direkt nach `bar_fetch`. Lazy `from data_foundation.coverage import
   assess_window` (Phasen-Isolation). Bei `verdict.covered is False` wird ein
   `window_uncovered`-Event an `research_health.jsonl` emittiert (`record_event`, exakt
   das vorhandene Observability-Pattern — keine neue Pipe). `PaperTradeTracker(...)` bekommt
   `window_ok=window_ok` als neuen keyword-arg. `bar_fetch`-Docstring zeigt jetzt explizit
   auf A2: „bar_service.get_window is a pure archive read — no IG fetch, no chain".
3. **`_PAPER_MAX_FETCH_ATTEMPTS`-Kommentarblock** komplett umgeschrieben — der alte Text
   („BarService.get_window's own budget-aware chain does X") ist seit A2 falsch. Drei
   Abschnitte: aktueller A3-Stand (Cap greift für raised fetch / leere Bars / ungedecktes
   Fenster), Pre-A3-Historie als „kept for the audit trail", A2-Notiz über die
   get_window-Verwandlung. **Korrigiert, nicht gelöscht** (Plan §6 A3 verbatim).
4. **`tests/test_paper_engine.py`** — vier neue Tests, exakt die Plan-Liste:
   - `test_window_ok_none_default_is_bit_identical` — selbe Bars wie der bestehende
     Auflösungs-Test, ohne `window_ok`-Param ⇒ gleiche Resolution. Regressions-Schutz.
   - `test_window_ok_false_charges_attempt_and_does_not_call_resolve` — Guard sagt nein,
     Trade bleibt OPEN, `exit_reason` NULL (beweist, dass `resolve_paper_trade` nie gerufen
     wurde — sie ist der einzige Writer dieses Felds), `_fetch_attempts == 1`.
   - `test_window_ok_false_eventually_expires_at_cap` — 12 Ticks → `EXPIRED_UNRESOLVED`,
     `exit_reason` NULL (kein fabrizierter TIME_STOP).
   - **`test_window_ok_mitten_loch_blocks_fabricated_time_stop`** (F3-Test) — der wichtigste
     Test des Blocks. Macht zuerst eine **Precondition-Probe** ohne Guard: derselbe Bar-Satz
     (09:00–09:01, 20-Min-Loch 09:02–09:21, 09:22–10:00) **produziert** ein
     `RESOLVED/TIME_STOP` (Sanity, dass die Lücke genau F3 ist). Dann mit Guard: `OPEN`,
     `exit_reason=NULL`, `_fetch_attempts == 1`. Rotiert vor dem zweiten Tick den Trade
     (`DELETE FROM paper_trades`) — sonst kollidieren die zwei Pfade im selben Store.
5. **Rotation:** Session-4-Block verbatim nach `SESSIONS_ARCHIVE.md` verschoben.

### Verified

- `pytest phase10_v3/tests -q` → **164 passed** (war 160; +4 neue Tests).
- `pytest phase10_v3/tests/test_paper_engine.py -q` → **56 passed** (52 + 4).
- Voller Regression-Sweep, **alle 12 Suiten grün**: 87 · 77 · 104 · 155 · 173 · 76 · 138 · 237 · 80 · 164 · 134 · 28.
- `py_compile` auf `wiring.py`, `paper.py`, `test_paper_engine.py`, `coverage.py` — alle clean.
- `git diff --stat HEAD` → **+237 / −9** (net +228). A3 ist **rein additiv** — keine Löschungen,
  nur `window_ok` als neuer Parameter + neuer Closure-Body + 4 neue Tests.
- Der F3-Test hat **beide** Hälften verifiziert: pre-A3-Code fabriziert die TIME_STOP-Zeile
  (Sanity-Zweig), A3 blockiert sie (Hauptzweig). Das ist der Beweis, dass der Guard genau
  den F3-Pfad schließt — nicht „etwas anderes".

### Note

- **Cross-Phase-Edits** an `phase10_v3/abstain_lessons/paper.py` (4 cm) + `phase8_scheduler/scripts/wiring.py`
  (54 cm) + 1 Test in `phase10_v3/tests/` — alles gemäß Plan §1 / Nikinger-Freigabe
  2026-08-18. **Kein** Eingriff in `phase12_data_foundation/` (nur `assess_window` **konsumiert**,
  kein neuer Code-Pfad dort).
- **Wiring.py hat keinen Test** (dokumentierte Konvention, operator-run). Der `window_ok`-
  End-to-End-Pfad ist nur über die `phase10_v3`-Tests sichtbar — die `py_compile`-Probe
  ist hier das Maximum an statischer Verifikation. Cross-Phase-Regression (alle 12 Suiten
  grün) ist der zweite Schutz.
- **Dataclass-Tests brechen nicht:** `Bar(...)`-Aufrufer in `test_paper_engine.py` weiter
  ohne `tick_count` (Default `None`), keine Migration.
- **A2 + A3 zusammen** schließen die zwei strukturellen Lücken: A2 macht den Tracker-Pfad
  kauf-unfähig, A3 macht ihn **lückentolerant** — eine Lücke im Fenster ist heute ein
  typisierter Status (Retry-Cap, dann `EXPIRED_UNRESOLVED`), nie mehr eine fabrizierte
  Auflösung. Das ist die schärfste Form von L1/L3 zusammen.

### Next

- **A4** (Plan §6, Zeile 698): Stale-History-Assertion in `BudgetedIGBarProvider.get_bars`.
  Nach der Bar-Liste builden, **vor** `record_spend` prüfen; `stale` ⇒ `record_spend` +
  `return None` + `event="stale_history"`. Neuer `stale_tolerance_min=120` Konstruktor-Param.
  Neuer `DS_STALE_SOURCE` in `KNOWN_DATA_SOURCE_STATUSES`. Test: 301 32-Tage-alte Bars
  landen nicht im Archiv, ein `stale_history`-Event wird emittiert.
- **A5** (Plan §6, Zeile 736): `BarArchive.window` bekommt `sources: tuple[str, ...] | None`
  Filter-Argument (L10). A5-Teilarbeit (Spalte + INSERT + Projection) ist **bereits** in A2
  gelandet — A5 ergänzt nur den Filter und die `KNOWN_SOURCES`/`prefer`-Default-Pflege.
- **A6** (Plan §6, Zeile 757): Heartbeat-Reparatur (F1/F2) + Niveau-→Rendite-Vergleich
  (A6.0). Zweiter Sampler-Callback `mark_stale_fn`, `sample_epic`-Signatur erweitert.
  Wichtigster Substep: der Divergenz-Sampler ist heute blind gegen F1 (toter IG-Historical
  mit `ok=True`); A6 repariert das strukturell.
- **A7** (Plan §6, Zeile 847): Registry-Hygiene + Operator-Sequenz. `IX.D.IBEX.FWM2.IP`
  bleibt `ok` bis A6 läuft; die 14 RESOLVED/yf-Zeilen vom 18.08. sind in der ersten
  Auswertung **getrennt** auszuweisen (nicht löschen).
- **Offen bis Block B0:** ob `CHART:{epic}:1MINUTE` liefert (Plan §9.2).
- **Offen bis Block C1:** welche Fremdquelle S3 wird (Plan §6 C1).
- **`main` liegt jetzt 8 Commits vor `origin/main`** (inkl. dieses Commits) — Push bleibt
  bewusste Einzelfreigabe des Nikinger.

### Open questions / blockers

- **Kein technischer Blocker.** Bot steht sicher, Recorder sammelt kostenlos weiter.
- **A4 will denselben `stale_tolerance_min`-Knopf** wie der Sampler in A6 — getrennte
  Defaults, aber bewusst **nicht** derselbe Parameter (Plan §6 A6.1: „Schreibpfad vs.
  Diagnose, eine Lockerung am einen Ort soll nicht still am anderen mitgemacht werden").
- **A6 ist der einzige A*-Block-Step, der die Sampler-API ändert** (`sample_epic` bekommt
  zwei Callbacks). Aufrufer in `wiring.py:946` und `test_heartbeat.py` müssen mitziehen —
  mein Auftrag, vor A6 zu prüfen.

