---
status: snapshot
purpose: Execution-ready Plan für Phase 13 (Live-Datenfundament) — der strukturelle Schnitt nach dem Scheitern von P12.5 plus ein vierstufiges Beschaffungssystem mit IG-Lightstreamer als Live-Stufe. Gelockte Entscheidungen L1–L16, Blöcke A/B/C mit Datei:Zeile-Ankern, Testliste, Abnahme.
read-when: vor jedem Bauschritt an Phase 13; die ausführende Session liest §2 (gelockt), §6 (Sequenz), §9 (Drift-Liste) vollständig, bevor sie eine Zeile ändert
detail: L3
up: ../../phase12_data_foundation/PHASE12_5_CLOSEOUT_HANDOVER.md
down:
  - ../../phase12_data_foundation/PHASE12_5_CLOSEOUT_HANDOVER.md   # 📕 warum P12.5 scheiterte (Vorgänger)
  - ./phase12_data_foundation_plan.md                              # 📕 Phase-12-Plan: D1–D20, Anforderungen A–G
  - ../../phase1_broker_wrapper/lightstreamer_integration_notes.md # 📗 LS-Chronik + Parallel-Login-Falle
updated: 2026-08-18
---

# Phase 13 — Live-Datenfundament: Execution-Ready Plan (2026-08-18)

> **Autor:** Claude Code, Planungssession 2026-08-18. **Adressat:** die ausführende Session
> (Sonnet 5). Alles unten ist gegen den Repo-Stand `c38cb9f` selbst nachgemessen — außer, was
> in **§9** steht. §9 ist vollständig: was dort nicht steht, gilt als geprüft.
>
> **Vorgänger:** [`PHASE12_5_CLOSEOUT_HANDOVER.md`](../../phase12_data_foundation/PHASE12_5_CLOSEOUT_HANDOVER.md).
> Dieser Plan **ersetzt** dessen §4-Optionsliste: Option B ist gebaut als Block A, Option C
> (Stream) ist nicht mehr gegatet, sondern Block B.

---

## §0 BLUF

Drei Datenwochen und zwei Fundament-Anläufe sind an derselben Stelle gestorben: **der
Verbrauchspfad besorgt sich seine Daten selbst.** Phase 13 trennt beides endgültig.

**Beschaffung** ist ein vierstufiges System, das nach Kosten und Latenz gestaffelt ist und
jede Bar in *ein* Archiv schreibt. **Verbrauch** liest ausschließlich dieses Archiv und
kauft nie. Die Frage, die ein Konsument stellt, ändert sich von „ist das Archiv jetzt
aktuell?" zu „**deckt das Archiv das Fenster genau dieses Trades dicht genug ab?**" — und
die Antwort „nein" ist kein Kaufauslöser, sondern ein typisierter Status.

| Stufe | Quelle | Kosten | Latenz | Rolle |
|---|---|---|---|---|
| **S1** | IG **Lightstreamer** `CHART:{epic}:1MINUTE` (Fallback: Tick-Aggregation) | **0** (anderes Kontingent) | Echtzeit | der **Schwanz**: deckt „jetzt", und zwar aus **derselben Preisreihe wie der Einstieg** |
| **S2** | yFinance-Recorder (existiert, läuft) | 0 | ~15 Min | der **Rumpf**: Backfill, Neustart-Erholung, Off-Hours, 7 Tage Historie |
| **S3** | unabhängige Fremdquelle (Auswahl: §6 Block C1) | 0 | Minuten–Stunden | **Gegenprobe + Tiefen-Backfill**: eine zweite Meinung, die nicht IG und nicht Yahoo ist |
| **S4** | IG REST `/prices` (`get_historical_ohlcv`, **Bereichs-API**) | 1 Pkt/Bar, gedeckelt | sofort | **Rettung**: nur für gealterte Restlücken, lückengroß, gedrosselt, Frische-geprüft, Default AUS |

**Erste Akzeptanzbedingung, strukturell statt hoffnungsvoll:** ein Test, in dem der
Tracker-Pfad gegen einen IG-Provider läuft, der bei **jedem** Call `AssertionError` wirft.
Grün heißt: Ausgeben ist nicht unwahrscheinlich, sondern unmöglich (Lehre aus
Closeout §3 — 123 grüne Tests konnten den Kostenfehler nicht sehen, weil keiner Kosten prüfte).

**Drei neue Befunde dieser Session** (§4) formen den Plan mit: IG liefert für eine
Forward-Epic seit einem Monat tote Historie und meldet dabei `ok=True`; der Divergenz-Sampler
ist gegen genau diesen Fall strukturell blind; und eine Lücke *mitten* im Trade-Fenster
erzeugt heute eine **erfundene** `TIME_STOP`-Auflösung, die wie ein sauberes Ergebnis aussieht.

---

## §1 Rahmen, Arbeitsteilung, Gates

**Bindend übernommen aus Phase 12** (`phase12_data_foundation/CLAUDE.md`, Abschnitt „Rahmen",
Nikinger-Entscheidung 2026-08-17):

- **Werktags-Arbeit ist erlaubt, auch bot-berührend.** Vorher den Bot stoppen
  (`ps aux | grep scheduler.run` als Gegenprobe — Parallel-Login-Falle), danach gezielt neu
  starten. Ein Datei-Edit wirkt ohnehin nicht auf einen laufenden Prozess.
- **Live-, Netz- und kostenpflichtige Läufe macht der Nikinger.** Claude bereitet den Befehl
  vor, nennt die Kosten, fragt vorher.
- **Live-DB nur `mode=ro`.**
- **Cross-Phase-Edits sind für Phase 13 freigegeben** (Nikinger 2026-08-18: „Cross Phase edits
  sind okay"). Betroffen: `phase1_broker_wrapper/` (Streaming), `phase8_scheduler/`
  (Config/CLI/Runner/Wiring), `phase10_v3/abstain_lessons/paper.py` (eine additive Naht),
  `phase12_data_foundation/data_foundation/` (Speicherschicht).
- **Bauprinzip:** Phase 13 fügt **null** neue AI hinzu. Wer hier ein LLM „Lücken schätzen",
  „Quellen bewerten" oder „Bars plausibilisieren" lassen will → stop, das ist Code.
- **Betriebszustand jetzt (2026-08-18, selbst nachgemessen):** Scheduler **gestoppt**.
  Recorder läuft (`pid 33151`, `python -m data_foundation.run`, reiner yFinance-Prozess,
  kostenlos). IG-Fenster: **4731 / 10 000** verbraucht, IG-eigene Restmeldung **5054** (14:08),
  Fenster rollt gegen **2026-08-25** ab. `main` liegt **4 Commits vor `origin/main`**
  (nicht gepusht).

**Gate für den Wiederanlauf mit IG-berührendem Messarm** (Closeout §6 C1, unverändert
bindend): erst wenn (a) Block A auf `main` ist **und** (b) eine frische
`remainingAllowance`-Beobachtung vorliegt (`scripts/probe_allowance.py`, 5 Punkte).
Nach Block A ist der Tracker-Pfad per Konstruktion bei 0 Punkten — das Gate ist danach
Formsache, aber es bleibt.

---

## §2 Gelockte Entscheidungen (L1–L16)

> Gelockt heißt gelockt: nicht mid-implementation re-litigieren. Widerspricht neue Evidenz
> einer Zeile → Befund an den Nikinger, **nie** still abweichen.

| # | Entscheidung | Begründung / Anker |
|---|---|---|
| **L1** | **Beschaffung und Verbrauch sind getrennte Subsysteme.** Beschaffung = vier Stufen S1–S4, die ins Archiv schreiben. Verbrauch = Archiv-Lesen. Kein Konsumentenpfad löst je einen externen Fetch aus. | Closeout §1: „das Problem ist nicht, dass zu teuer gekauft wird — das Problem ist, dass überhaupt gekauft wird". 1638 von 1782 gekauften IG-Bars (92 %) lagen bereits im Archiv. |
| **L2** | **`BarService.get_window` fetcht nicht mehr.** Es wird eine reine Archiv-Lesung. Der explizite IG-Top-up-Zweig (`service.py:229-238`) und der Vollfenster-Refetch (`service.py:222-227`) **entfallen ersatzlos**; `_covers_tail`, `_MIN_WINDOW_COVERAGE` und `self._ig_provider` werden gelöscht. | Netto eine Löschung, kein Umbau. Der Zweig kostete am 18.08. 4515 von 4731 Punkten in 15 Calls. |
| **L3** | **Die Abdeckungsfrage gilt dem ganzen Trade-Fenster, nicht dem Schwanz.** Neue Prüfung `assess_window(timestamps, start, end, res_min, *, min_ratio, max_gap_min) -> WindowCoverage` — **zwei** Schwellen: Dichte *und* größte zusammenhängende Lücke. | `resolve_paper_trade` (`paper.py:246`) filtert nur `timestamp >= created_utc` und prüft den SL-Treffer **unbedingt vor** dem Time-Stop-Ausstieg (`paper.py:261-271`). Eine Lücke **mitten** im Fenster verschluckt den SL-Treffer und liefert eine erfundene `TIME_STOP`-Zeile, die wie ein sauberes Ergebnis aussieht. Eine reine Schwanz-Prüfung kann das nicht sehen; eine reine Quote auch nicht (300-Min-Fenster mit 20-Min-Loch = Quote 0,93). |
| **L4** | **Reihenfolge: Block A (Schnitt) → Block B (Live/LS) → Block C (S3/S4 + Reports).** | **Selbst gelockt.** Die Nikinger-Antwort vom 2026-08-18 beantwortete den *Umfang* („mehrstufig, gerne mehr Stufen"), **nicht** die Reihenfolge. Begründung: Block A ist eine Löschung, macht sofort einen sicheren Neustart möglich (0 Punkte auf dem Tracker-Pfad), während Block B noch gebaut wird — und Block B wird dann gegen **gemessene** Abdeckungszahlen aus Block A gebaut statt gegen eine Vermutung. Wer diese Zeile aufmacht, verschiebt den Neustart um die volle Bauzeit von B. |
| **L5** | **Der LS-Mitschrieb läuft im Scheduler-Prozess** (die eine warme IG-Session). Er stirbt mit dem Bot; der yF-Recorder deckt die Bot-aus-Zeiten weiter ab. | Nikinger 2026-08-18. Löst die im Phase-12-Plan §6 Step 10 offen gelassene Kernfrage: kein Token-Sharing über Datei/IPC (neue Sicherheitsfläche), keine Parallel-Login-Falle. Für die Messung folgenlos — gemessen wird nur, wenn der Bot läuft. |
| **L6** | **S1 primär = `CHART:{epic}:1MINUTE`-Kerzen; Fallback = Tick-Aggregation aus dem bestehenden `PRICE`-Abo.** Beide schreiben `source='ls'` und füllen die neue Spalte `bars.tick_count`. Der Fallback ist **nicht** gleichwertig und wird nie so etikettiert. | CHART liefert serverseitig fertige OHLC + `CONS_TICK_COUNT`. Tick-Aggregation unterschätzt bei dünnem Tickfluss High/Low — also genau das SL/TP-Treffersignal. Step 7a maß 21/2/15/7 Updates über den Diagnosefenster-Zeitraum (`lightstreamer_integration_notes.md`), also mindestens eine Epic mit sehr dünnem Fluss. `tick_count` macht die Qualität pro Bar messbar statt behauptet. |
| **L7** | **LS-Kerzen werden als Mid geführt:** `(BID_x + OFR_x) / 2` je O/H/L/C. | `ig_adapter.py:891-907` (`_parse_bar`): „IG returns OHLC as nested {bid, ask} per field; **use mid**". Das Archiv enthält bereits IG-REST-Bars in Mid. Eine LS-Bar in Bid neben einer REST-Bar in Mid wäre eine stille Preisreihen-Mischung im selben `bars`-Table. |
| **L8** | **Die Stale-History-Assertion sitzt am IG-Kaufort, NICHT in `insert_bars`.** | `BarArchive.insert_bars` (`archive.py:92`) ist auch der Schreibpfad des Recorders **und** der künftigen Backfill-Stufe S3 — die schreiben legitim alte Bars (yF 7 Tage, S3 potenziell Monate). Eine pauschale „`ts_utc` muss nahe `fetched_at` liegen"-Regel dort bricht den Backfill, und das Symptom wäre „das Archiv füllt sich nicht mehr" mit dem Recorder als erstem Verdächtigen. |
| **L9** | **Doppelmessung (Nikinger Q4) ist ein Report-Artefakt, keine zweite Spalte.** `scripts/source_delta.py` löst dieselben Trades ein zweites Mal quellenrein auf und weist die Differenz aus. `paper_trades.resolution_source` bleibt unverändert. | Nikinger 2026-08-18 („Beides messen, Differenz = eigene Messgröße"). Eine zweite Spalte hieße Migration 007 + `to_row`/`from_row`-Positionslogik + zwei Wahrheiten pro Zeile. Der Report braucht nichts davon: das Archiv trägt beide Quellen zur selben Minute bereits. |
| **L10** | **`BarArchive.window` bekommt ein `sources`-Filterargument** (`sources: tuple[str, ...] | None = None`), zusätzlich zum bestehenden `prefer`. | `prefer` **rankt** nur und kollabiert auf eine Zeile je `ts_utc` — eine quellenreine Lesung ist damit unmöglich. Der `DivergenceSampler` umgeht das heute mit einer Nachfilterung im Aufrufer (`heartbeat.py:186-191`, inkl. Kommentar, warum). L9s Report und der reparierte Sampler brauchen beide dasselbe: einmal richtig im Store, nicht zweimal daneben. |
| **L11** | **Neues Verzeichnis `phase13_live_data/`, Paket `live_data`.** `data_foundation` (Phase 12) bleibt die **Speicherschicht** (Archiv, Budget, Service, Coverage) und wird cross-phase editiert. `live_data` importiert `data_foundation`, **nie umgekehrt**. | Repo-Konvention (eine Phase = ein Verzeichnis) + Abhängigkeitsrichtung vorwärts. `assess_window` liegt deshalb in `data_foundation/coverage.py`, nicht in `live_data` — sonst würde Phase 12 auf Phase 13 zeigen. |
| **L12** | **Erste Akzeptanzbedingung ist eine strukturelle Kostenzusicherung**, kein Zählwert: der Tracker-Pfad läuft im Test gegen einen IG-Provider, dessen `get_bars` `AssertionError` wirft. | Closeout §8.2. Ein Test, der „≤ N Punkte" prüft, misst eine Zahl, die morgen anders parametrisiert ist. Ein Test, der überhaupt keinen Call zulässt, prüft die Struktur. |
| **L13** | **Der Momentum-VETO bleibt unangetastet** (Phase-12 D16 gilt weiter): er sourct direkt aus P1-IG-Echtzeit-Bars, nie aus BarService/Archiv/LS/yF. Ebenso unberührt: Gates, Sizing, P6, P7. | Root-`CLAUDE.md` Hard Rules. Der Archiv-Pfad ist Research-/Messdatenpfad, nie Safety-Input. |
| **L14** | **Die fünf P12.5-Fixes bleiben** (U1, U2, U3, U5, Entscheidung B — Commits `83d5ef3`, `ff5741c`). Kein Revert. | Closeout §8.4: alle live bewiesen korrekt, keiner war die Ursache. **Ausnahme, die kein Revert ist:** `_MIN_WINDOW_COVERAGE`/U3 verschwindet mit `get_window`s Fetch-Zweig, weil der Zweig verschwindet — das ist L2, keine Rücknahme. |
| **L15** | **Der Research-Seam (`BarService.get_bars`, `service.py:195-209`) wird in Block A NICHT angefasst.** Er trägt dasselbe Muster (`coverage_ratio >= 1.0` gegen ein Fenster, das bei `now` endet, praktisch nie bestehbar), ist heute aber billig: gemessen 10 Calls × 5 Punkte = 50 Punkte am 18.08. Er wird nach Block B **neu gemessen** — mit laufendem LS sollte das Archiv die Prüfung von selbst bestehen. Erst dann wird entschieden. | Closeout §4 „Geltungsbereich": der Research-Seam **will** legitim frische Daten (der Tracker nicht), die Löschung ist dort nicht die richtige Antwort. Explizit als „nicht in diesem Schnitt enthalten" festgehalten statt stillschweigend mitgenommen. |
| **L16** | **Phase 13 = Live-Datenfundament; das alte „V4" (Council, Handover, Reward-Reform, Force-Trigger, Instinct-ECC) rutscht auf Phase 14.** | Nikinger 2026-08-18. Präzedenzfälle: 2026-08-01 und 2026-08-11. Die Doku-Kaskade (Root-`CLAUDE.md`, `ROADMAP.md`, `README.md`, `ARCHITECTURE.md`, `docs/INDEX.md`) ist in **diesem** Commit mit dem Plan bereits ausgeführt — die ausführende Session findet sie vor und muss sie nicht nachziehen. |
| **L17** | **Latenzanforderung ist datenklassen-spezifisch, nicht global.** **Die Preisreihe (OHLC) muss live sein** — sie ist das Auflösungssignal für SL/TP und der Grund, warum S1 existiert. **Begleitgrößen (Volumen und Ähnliches) dürfen verspätet oder ganz abwesend sein.** Eine Quelle, die nur Begleitgrößen nachliefert, erfüllt die Anforderung; eine Quelle, die die Preisreihe verspätet liefert, ersetzt S1 **nicht**. | Nikinger 2026-08-18: „solange grundlegende Daten live kommen (z. B. Lightstreamer) und nur z. B. Volumendaten verspätet wären, wäre das zumutbar". Schärft, wofür S2/S3 zuständig sein dürfen: Rumpf, Backfill und Gegenprobe — nie der Auflösungspfad in Echtzeit. Macht zugleich die S3-Wahl unkritischer, weil ihr Verzug per Definition nur Begleitgrößen und nachträgliches Lückenfüllen betrifft. |

---

## §3 Zielarchitektur

```
   BESCHAFFUNG (schreibt)                                  VERBRAUCH (liest, kauft nie)
   ─────────────────────────                               ────────────────────────────
   S1  LS-Kerzen  CHART:{epic}:1MINUTE      ┐
       im Scheduler-Prozess (L5)            │
       source='ls', tick_count, Mid (L7)    │
                                            │
   S2  Recorder (eigener Prozess, yF)       │              PaperTradeTracker
       alle 300 s, source='yf'              ├──►  ┌──────────────────┐  ──► get_window()
                                            │     │ data/bars.sqlite │       = reine Lesung
   S3  Fremdquelle (Block C1)               │     │   BarArchive     │
       lückengetrieben, source=<neu>        │     │  bars(…, source, │  ──► assess_window()
                                            │     │   tick_count)    │       je Trade-Fenster
   S4  IG-Rettung  get_historical_ohlcv     │     │  source_spend    │       ├─ gedeckt  → auflösen
       Bereichs-API, lückengroß, gedrosselt,│     │  allowance_obs.  │       └─ Lücke    → Retry,
       Frische-Assertion (L8), Default AUS  ┘     └──────────────────┘            dann typisiert ab
                                                          │
                                                          ├──► Research get_bars() (L15: unverändert)
                                                          ├──► DivergenceSampler (repariert, §6 A6)
                                                          └──► scripts/source_delta.py (L9)

   UNBERÜHRT:  Momentum-VETO ← P1-IG-Echtzeit-Bars direkt (L13)
```

**Der eine Satz, der die Phase trägt:** *Ein Konsument, der Daten braucht, die er nicht hat,
bekommt einen typisierten Status — nie einen Kauf.*

---

## §4 Neue Befunde dieser Session (nachgemessen, nicht übernommen)

Alle drei am 2026-08-18 gegen `data/bars.sqlite`, `data/trading_bot.sqlite` (`mode=ro`),
`data/state/research_health.jsonl` und den Quelltext geprüft. Keiner steht in einem
Vordokument.

### F1 — IG liefert für eine Forward-Epic seit einem Monat tote Historie und meldet `ok=True`

`IX.D.IBEX.FWM2.IP` („Spanien 35 (2€)", Forward-Kontrakt): im Archiv liegen **301** IG-Bars
mit `resolution='1m'`, deren `ts_utc` von `2026-07-17T11:14:00.000Z` bis
`2026-07-17T16:14:00.000Z` reicht — und deren `fetched_at` bei **allen 301**
`2026-08-18T11:10:17.019Z` lautet. IG antwortete am 18.08. mit einer **einen Monat alten**
Kursreihe, Statuscode ok, Envelope ok, `bars` nicht leer.

Am 18.08. hatte genau diese Epic mit **8** `bar_fetch/ig/ok=True`-Events die **meisten von
allen** (CAC/DAX/IBEX-Kassa je 3) — und **null** verwertbare Bars für diesen Tag. Der
Archiv-PK (`INSERT OR IGNORE`) hat jede Wiederholung stillschweigend geschluckt.

Dasselbe Muster, kleiner: `IX.D.AEX.FWM1.IP` (5 Bars, `ts` 2026-07-17, `fetched_at`
2026-08-17) und FWM2s 5m-Sample (identisch). Über das ganze Archiv gibt es **exakt drei**
solcher `(epic, source, fetched-Tag ≠ ts-Tag)`-Gruppen — selten, aber real, und **beide**
betroffenen Epics sind `FWM*`-Forward-Epics.

**Zwei Folgen:**
1. Der Closeout §7 nannte FWM2 den „Existenzbeweis" für rein-yF-Auflösung (14/14 Trades ohne
   IG-Punkt). Das ist **korrigiert**: FWM2 löste ohne IG auf, weil IGs Daten für sie
   **unbrauchbar** waren, nicht weil yF genügte. Sie ist der teuerste Blindgänger des Tages,
   nicht der Beweis.
2. `IX.D.IBEX.FWM2.IP` trägt heute `data_source_status='ok'` und `yf_ticker='^IBEX'` — also
   den **Kassa**-Index als Datenquelle für einen **Forward**-Kontrakt. Ihre 14 `RESOLVED/yf`-
   Zeilen vom 18.08. sind gegen eine andere Preisreihe aufgelöst als ihr Einstieg.

### F2 — Der Divergenz-Sampler kann genau F1 nicht melden

`DivergenceSampler.sample_epic` (`heartbeat.py:184-193`) ankert das Vergleichsfenster am
**IG-Bar-Zeitstempel**:

```python
window_start = ig_bar.ts
window_end = _iso(_parse(ig_bar.ts) + timedelta(minutes=5))
archived = self.archive.window(epic, "1m", window_start, window_end, prefer=("yf",))
yf_bars = [b for b in archived if b.source == "yf"]
if not yf_bars:
    return  # Recorder hasn't covered this window yet — nothing to compare
```

Ist `ig_bar.ts` einen Monat alt, findet der Archivgriff keine yF-Bar und die Funktion kehrt
**still** zurück. Der eine Alarm, der „IG und yF widersprechen sich" fangen soll, ist gegen
den schlimmsten Fall (IG serviert tote Historie) strukturell blind — er scheitert **zur
Stille**, nicht zum Alarm. Bestätigung im Log: **0** `quote_divergence`-Events insgesamt bei
**12** bezahlten Samples.

### F3 — Eine Lücke *mitten* im Trade-Fenster erzeugt eine erfundene `TIME_STOP`-Zeile

`resolve_paper_trade` (`paper.py:234-278`) iteriert die vorhandenen Bars ab `created_utc`.
Fehlen die Minuten, in denen der SL berührt wurde, läuft die Schleife bis zur ersten Bar mit
`ts >= time_stop_utc` und gibt `PaperExitReason.TIME_STOP` mit
`last_close_at_or_before_stop` zurück. Das Ergebnis ist **nicht** von einem echten
Time-Stop unterscheidbar — weder in der DB (`exit_reason='TIME_STOP'`, `status='RESOLVED'`)
noch im Heartbeat, der `TIME_STOP` als „typisiertes Ergebnis" **positiv** zählt
(`heartbeat.py:85-89`). Eine Datenlücke wird so zu einer sauber aussehenden Messzeile.

Das ist die eigentliche Begründung für L3: eine Schwanz-Prüfung sieht diesen Fall nie, und
`resolve_paper_trade` selbst darf nicht geändert werden (es ist die reine, getestete
Auflösungsfunktion — der Guard gehört davor).

---

## §5 Contracts (exakte Namen)

Alles hier ist **neu oder geändert**. Namen sind bindend — die ausführende Session erfindet
keine eigenen.

### 5.1 `phase12_data_foundation/data_foundation/coverage.py` (NEU)

```python
@dataclass(frozen=True)
class WindowCoverage:
    covered: bool
    present: int              # vorhandene distinkte Bar-Minuten im Fenster
    expected: int             # naiv erwartete Bar-Anzahl (Wanduhr, keine Session-Kalender)
    ratio: float              # present / expected, auf 1.0 gedeckelt
    largest_gap_min: int      # größte zusammenhängende Lücke in Minuten
    reason: str | None        # None wenn covered; sonst 'empty' | 'sparse' | 'gap'

MIN_WINDOW_RATIO: float = 0.90      # v1, Kalibrierungsknopf — Block A misst die reale Verteilung
MAX_WINDOW_GAP_MIN: int = 5         # v1, dito

def assess_window(
    timestamps: Sequence[str],
    start_utc: str,
    end_utc: str,
    resolution_minutes: int,
    *,
    min_ratio: float = MIN_WINDOW_RATIO,
    max_gap_min: int = MAX_WINDOW_GAP_MIN,
) -> WindowCoverage: ...
```

`timestamps` ist bewusst eine Folge **ISO-Strings**, keine Bar-Objekte: die beiden Aufrufer
haben verschiedene Shapes (`service.py` hält `Bar`-Objekte mit `.ts_utc`, der Tracker hält
Dicts mit `["timestamp"]`). Eine formfreie Signatur spart eine Adapterschicht.

`reason`-Semantik: `'empty'` = keine Bar im Fenster · `'sparse'` = `ratio < min_ratio` ·
`'gap'` = `largest_gap_min > max_gap_min` (auch bei guter Quote). Bei mehreren zutreffenden
Gründen gewinnt der spezifischste in dieser Reihenfolge: `empty` → `gap` → `sparse`.

### 5.2 `data_foundation/archive.py` (GEÄNDERT)

```python
def window(
    self, epic: str, resolution: str, start_utc: str, end_utc: str,
    *,
    prefer: tuple[str, ...] = ("ig", "ls", "yf"),
    sources: tuple[str, ...] | None = None,      # NEU (L10) — None = alle Quellen
) -> list[Bar]: ...
```

`sources` filtert **vor** der `prefer`-Rangfolge (`WHERE source IN (...)`). Damit ist eine
quellenreine Lesung möglich, ohne den Aufrufer nachfiltern zu lassen.

`ensure_schema()` bekommt zusätzlich einen **idempotenten, geführten** Spaltenanbau:

```python
cols = {r[1] for r in self.conn.execute("PRAGMA table_info(bars)").fetchall()}
if "tick_count" not in cols:
    self.conn.execute("ALTER TABLE bars ADD COLUMN tick_count INTEGER")
```

Kein P2-Migrationslauf — `bars.sqlite` ist eine eigene Datei (Phase-12 D4) und
`ensure_schema` ist ihr einziger DDL-Ort. `Bar` bekommt `tick_count: int | None = None`
**ans Ende** des Dataclass (Default nötig, sonst brechen alle bestehenden Konstruktionen).

### 5.3 `data_foundation/service.py` (GELÖSCHT + GEÄNDERT)

Nach dem Schnitt:

```python
def get_window(self, epic: str, resolution: str, start_utc: str, end_utc: str) -> list[dict[str, Any]]:
    """Reine Archiv-Lesung. Fetcht nie (L1/L2) — Beschaffung ist ein eigenes Subsystem."""
    return [_bar_to_dict(b) for b in self._archive.window(epic, resolution, start_utc, end_utc)]
```

**Gelöscht:** `_covers_tail` (ganze Funktion), `_MIN_WINDOW_COVERAGE` (Konstante inkl.
ponytail-Kommentar), `self._ig_provider` (Attribut + Zuweisung im `__init__`), der
Vollfenster-Refetch und der IG-Top-up-Zweig.

`_bar_to_dict` bekommt `"tick_count": bar.tick_count` **zusätzlich** (der Tracker liest es
nicht, aber `source_delta.py` und der Coverage-Report lesen dieselben Dicts).

### 5.4 `phase10_v3/abstain_lessons/paper.py` (ADDITIVE NAHT)

```python
class PaperTradeTracker:
    def __init__(
        self, ..., 
        window_ok: Callable[[str, Sequence[Mapping[str, Any]], str, str], bool] | None = None,
    ) -> None: ...
```

Argumentfolge **verbindlich**: `(epic, bars, created_utc, time_stop_utc)`. Die Epic wird
explizit durchgereicht und **nicht** aus der ersten Bar geraten — man würde sie aus genau den
Daten lesen, die man gerade als lückenhaft eingestuft hat.

Default `None` = bit-identisch. Aufruf in `_resolve_group`, **vor** `resolve_paper_trade`:

```python
if self.window_ok is not None and not self.window_ok(
    trade.epic, bars, trade.created_utc, trade.time_stop_utc
):
    self._charge_failed_attempt([trade], now)
    continue
```

Damit erbt der Fall die bereits gebaute U2-Mechanik: nicht gedeckt ⇒ ein gezählter
Fehlversuch ⇒ nächster Tick versucht erneut ⇒ nach `max_fetch_attempts` (12) typisiert
`EXPIRED_UNRESOLVED`. Bei 240 Min Haltedauer gegen Minuten-Latenz kostet das Warten null
Messqualität (Closeout §4 Option B).

`resolve_paper_trade` selbst wird **nicht** angefasst.

### 5.5 `phase1_broker_wrapper/broker_wrapper/streaming/` (ADDITIV)

`base.py` — neben `PriceTick`:

```python
@dataclass
class ChartCandle:
    epic: str
    ts_utc: str          # Kerzenbeginn, ISO 8601 UTC ms 'Z' (aus UTM)
    open: float          # Mid (L7)
    high: float
    low: float
    close: float
    tick_count: int | None
    complete: bool       # CONS_END == "1"

CandleCallback = Callable[[ChartCandle], None]
```

`ig_lightstreamer.py` — **additiv**, die `StreamClient`-ABC bleibt unangetastet (sonst müsste
`PollingStreamClient` mitziehen, das für Kerzen keinen Sinn ergibt):

```python
_CHART_FIELDS = ["UTM", "CONS_END", "CONS_TICK_COUNT",
                 "BID_OPEN", "BID_HIGH", "BID_LOW", "BID_CLOSE",
                 "OFR_OPEN", "OFR_HIGH", "OFR_LOW", "OFR_CLOSE"]

class IGLightstreamerClient(StreamClient):
    def subscribe_candles(self, epic: str, callback: CandleCallback, *, scale: str = "1MINUTE") -> None: ...
    def unsubscribe_candles(self, epic: str) -> None: ...
    def _do_subscribe_chart(self, epic: str, scale: str) -> None: ...   # Subscription("MERGE", [f"CHART:{epic}:{scale}"], _CHART_FIELDS)

class _CandleListener(SubscriptionListener): ...
```

Getrenntes `self._chart_subs: dict[str, Subscription]` neben `self._subs` — `stop()` räumt
beide.

### 5.6 `phase13_live_data/live_data/` (NEU)

```python
# stream.py
class LSBarRecorder:
    """S1 — schreibt fertige LS-Kerzen write-through ins Archiv (source='ls')."""
    def __init__(self, stream: Any, archive: Any, epics_fn: Callable[[], list[str]], *,
                 resolution: str = "1m", health_sink: Callable[[dict], None] | None = None,
                 now_fn: Callable[[], datetime] = ...) -> None: ...
    def start(self) -> None          # stream.start() + je Epic subscribe_candles
    def stop(self) -> None
    def restart(self) -> None        # nach Token-Rotation (§6 B3)
    def resync_epics(self) -> None   # aus dem universe_refresher-Slot
    def on_candle(self, candle: ChartCandle) -> None   # fail-soft, schreibt nur bei complete=True

class TickAggregator:
    """L6-Fallback — PRICE-Ticks → 1-Min-OHLC (Mid), nur wenn CHART nicht verfügbar."""
    def on_tick(self, tick: PriceTick) -> None: ...
    def close_minute(self, minute_start_utc: str) -> ChartCandle | None: ...

# rescue.py  (Block C, Default AUS)
@dataclass
class RescueReport:
    epic: str; gaps_found: int; bars_written: int; points_spent: int; skipped_reason: str | None

class GapRescue:
    """S4 — gealterte Restlücken über die IG-Bereichs-API, gedrosselt und frische-geprüft."""
    max_calls_per_epic_per_day: int = 1
    min_gap_age_min: int = 60
    max_points_per_call: int = 60
    stale_tolerance_min: int = 120     # L8 — die Assertion aus F1 sitzt HIER
    def rescue_epic(self, epic: str, day_start_utc: str, day_end_utc: str) -> RescueReport: ...

# backfill.py (Block C1 — Quelle wird dort gewählt)
class ExternalBackfill: ...
```

---

## §6 Schritt-Sequenz

> Pro Step: **Dateien → exakte Namen → Verbatim-Anker (Zeile = Abkürzung, String = Wahrheit)
> → Tests → Akzeptanz.** Reihenfolge verbindlich. Jeder Step endet mit grünem
> `pytest <phase>/tests -q` **je Phase separat** (Memory `reference_running_phase_tests`,
> geteiltes Venv `phase1_broker_wrapper/.venv`) + atomarem Commit + Session-Block-Update.
>
> ⚠ **Zeilennummern verschieben sich zwischen Steps.** Immer den Verbatim-String greppen,
> nie blind die Zeile ansteuern.

---

### BLOCK A — Der Schnitt (macht einen sicheren Neustart möglich)

#### Step A0 — Haushalt, Baseline, Gerüst

**A0.0 — `claude-minimax`: ein zweiter Claude-Code-Befehl auf MiniMax M3.**

> **Nikinger-Entscheidung 2026-08-18, Kostengrund.** **Steht bewusst vor allem anderen**, weil
> jeder Schritt danach über den neuen Befehl laufen soll. **Kein Phase-13-Scope** — das ist
> Harness-Arbeit (Meta-Strang-Klasse, vgl. M1), sie steht hier nur, weil sie die Voraussetzung
> für die Ausführung ist.

**Die Regel, wer worauf läuft** (gehört in den Phasen-Kopf, nicht nur hierher):
**Ausführungs-Sessions → `claude-minimax`. Debugging-Sessions → weiterhin `claude`.**
Der normale Befehl wird **nicht angefasst** — keine Änderung an `~/.claude/settings.json`,
kein Export in einer Dotfile, keine Umgebungsvariable, die eine bestehende Session sieht.

**Drei heute verifizierte Fakten, die den Bau formen:**
1. `~/.local/bin/claude` ist ein **Symlink auf ein ELF-Binary**
   (`~/.local/share/claude/versions/2.1.233`). Ein zweiter Symlink wäre also schlicht wieder
   `claude` — es braucht ein **Wrapper-Skript**, das die Umgebung setzt und dann `exec claude`.
2. `~/.local/bin` liegt auf `PATH` (Position 2) — der Wrapper ist dort sofort aufrufbar.
3. 🔴 **`keyring` ist im System-`python3` NICHT importierbar**, nur im Projekt-venv
   (`phase1_broker_wrapper/.venv/bin/python`, Backend `keyring.backends.SecretService.Keyring`).
   Ein Wrapper mit nacktem `python3 -c "import keyring"` scheitert sofort. Absoluter
   Interpreterpfad, nicht `python3`.

**Zwei Dateien, beide im Repo (versioniert und reviewbar), Symlink nur beim Operator:**

*(a) `scripts/store_minimax_key.py`* — Keyring-Seeder, **exakte Kopie des Musters** von
`meta_m1_harness/bakeoff/store_bakeoff_key.py` (`getpass`, keine Shell-History, keine Datei,
`--status`/`--delete`, idempotentes Löschen). **Eigener Namensraum**, damit nichts mit den
Bot-Credentials kollidiert:

```python
SERVICE_NAME = "trading-bot-minimax"
USERNAME     = "minimax_api_key"
```

Das ist der vierte getrennte Keyring-Namensraum im Projekt (`tradingbot` = Live-Bot,
`trading-bot-bakeoff-runner` = M1, `trading-bot-bakeoff-void` = neutralisierter Fork). Hard
Rule 1 gilt unverändert: **der Schlüssel landet in keiner Datei, in keiner Dotfile, in keiner
Shell-History.**

*(b) `scripts/claude-minimax`* — der Wrapper (`chmod +x`), Operator verlinkt ihn:
`ln -s ~/trading-bot/scripts/claude-minimax ~/.local/bin/claude-minimax`

```bash
#!/usr/bin/env bash
# Claude Code gegen MiniMax statt Anthropic. Lässt `claude` unangetastet.
set -euo pipefail
VENV_PY="$HOME/trading-bot/phase1_broker_wrapper/.venv/bin/python"   # keyring lebt NUR hier
KEY="$("$VENV_PY" - <<'PY'
import sys, keyring
v = keyring.get_password("trading-bot-minimax", "minimax_api_key")
if not v:
    sys.exit("minimax key not in keyring — run: python scripts/store_minimax_key.py")
print(v)
PY
)"
export ANTHROPIC_BASE_URL="${MINIMAX_BASE_URL:-https://api.minimax.io/anthropic}"
export ANTHROPIC_AUTH_TOKEN="$KEY"
export ANTHROPIC_MODEL="${MINIMAX_MODEL:-MiniMax-M3}"
# Ohne diese beiden fragt Claude Code seine Hintergrund-Calls weiter unter einem
# claude-*-Namen an, den MiniMax nicht kennt — s. Stolperstein 2 unten.
export ANTHROPIC_DEFAULT_HAIKU_MODEL="$ANTHROPIC_MODEL"
export ANTHROPIC_SMALL_FAST_MODEL="$ANTHROPIC_MODEL"
unset ANTHROPIC_API_KEY        # ein vorhandener Anthropic-Key darf nicht still gewinnen
exec claude "$@"
```

**Der Nachweis, dass es wirklich auf MiniMax läuft — nicht optional** (Memory
`feedback_verify_flags_are_on`: viermal derselbe Fehlermodus, „läuft ohne Fehler" beweist
nichts). Zwei Stufen, beide vom Nikinger:
1. **Vor Claude Code**, ein nackter `curl` gegen den Endpunkt mit dem Keyring-Schlüssel und
   einem Ein-Token-Prompt. Prüft Endpunkt + Auth-Header + Modellname als Tripel, **bevor** ein
   Agent im Spiel ist. Schlägt er fehl, liegt es nie an Claude Code.
2. **Nach dem ersten `claude-minimax`-Lauf:** die **Verbrauchsanzeige bei MiniMax** ansehen.
   Nur der Zähler des Anbieters ist der Beweis — dieselbe Disziplin wie beim
   IG-`remainingAllowance`. Steht dort 0, lief es woanders.

**Was sich dadurch NICHT ändert** (bitte nicht verwechseln): der **Bot** ruft weiter Anthropic
auf — P4-Research, P6-Debatte, P7-/Abstain-Lessons nutzen unverändert den Key aus dem
`tradingbot`-Namensraum und werden in `data/state/llm_usage.json` gemessen. `claude-minimax`
wechselt, **wer den Coding-Agenten fährt**, nicht **welches Modell der Bot benutzt**.

**Drei Stolpersteine, jeder mit Symptom und erstem Verdächtigen:**
1. *„Die erste Anfrage geht durch, dann kommt ein 404 auf ein Modell, das ich nie gewählt habe."*
   → Claude Code macht Hintergrund-Calls (Titel, Zusammenfassung) mit einem Haiku-Klasse-Modell.
   Ohne `ANTHROPIC_DEFAULT_HAIKU_MODEL`/`ANTHROPIC_SMALL_FAST_MODEL` fragt es dafür weiter einen
   `claude-*`-Namen an. Deshalb stehen beide im Wrapper.
2. *„Tool-Calls schlagen sporadisch fehl, mal geht's, mal nicht."* → 🔴 **Bekannt und der
   ernsteste Einwand gegen diesen Weg:** MiniMax' `/anthropic`-Endpunkt ist ein **Shim über ihre
   native OpenAI-kompatible API**, und für genau diese Kombination sind sporadische
   Tool-Calling-Fehler berichtet (der Schlüssel des Wrapper-Objekts wechselt zwischen `result`,
   `arguments` und dem Tool-Namen). Claude Code **ist** Tool-Calling. Wenn das auftritt: nicht
   den Plan verdächtigen, den Shim. Ausweichpfad wäre MiniMax' OpenAI-kompatibler Endpunkt über
   den bereits gebauten, smoke-getesteten `OpenAICompatLLMClient` (M1 Step 10) — aber der fährt
   den Bot, nicht Claude Code, also ist das **kein** Ersatz, sondern nur ein Beleg, dass die
   Sprechweise im Projekt schon existiert. Realistischer Ausweg: für die betroffene Session auf
   `claude` zurück.
3. *„Der Wrapper findet den Schlüssel nicht, obwohl er gesetzt ist."* → Fakt 3 oben: falscher
   Interpreter. Gegenprobe:
   `phase1_broker_wrapper/.venv/bin/python scripts/store_minimax_key.py --status`.

**Bei Ausführung zu verifizieren** (steht auch in §9.18): die exakte Basis-URL (Quellen
nennen sowohl `.../anthropic` als auch `.../anthropic/v1`; Claude Code hängt seinen Pfad selbst
an, also entscheidet nur der Live-Test), ob MiniMax den **Bearer**-Header
(`ANTHROPIC_AUTH_TOKEN`) oder `x-api-key` (`ANTHROPIC_API_KEY`) erwartet, und die genaue
Modell-ID des M3-Tarifs.

**Rollback ist ein Befehl:** `rm ~/.local/bin/claude-minimax`. `claude` war nie berührt.

**Akzeptanz A0.0:** `claude-minimax --version` läuft · der `curl`-Vorabtest liefert eine
Antwort mit einem MiniMax-Modellnamen · nach einem echten Lauf zeigt **MiniMax' eigene
Verbrauchsanzeige** Verbrauch · `claude` ohne Wrapper verhält sich unverändert (Gegenprobe:
`env | grep ANTHROPIC` in einer normalen Shell ist leer).

---

**A0.1 Legacy-/Turbo-Grep (Ritual) — bereits von dieser Planungssession ausgeführt, Ergebnis
dokumentiert, NICHT wiederholen:**

```
grep -rniE "\b(turbo_research|strike|otm|issuer)\b" --include="*.py" .   (ohne .venv)
```
→ **3 Treffer, alle harmlos, dokumentierter No-Op:** `phase9_universe/universe/promotion.py:121`,
`:277` und `phase9_universe/tests/test_promotion.py:343` benutzen „strike" im Sinne von
*Fehlversuch* (`fail_count`), nicht im Optionssinn. `turbo_candidates` = 19 Treffer, der
eingefrorene P5-Gate-2-Contract-Name — **nicht umbenennen**. Ergebnis identisch zu den
Ritualen vom 2026-06-27 und 2026-07-10. Phase 13 führt keine neue Turbo-Referenz ein.

**A0.2 Regression-Baseline VOR dem ersten Fix.** Vollständig, je Phase separat, in **eine**
Tabelle in den Session-Block. Die Planungssession hat heute nur zwei Suiten gemessen
(`phase12_data_foundation` **123**, `phase10_v3` **160**, beide grün, 2026-08-18) — die
übrigen sind aus Vordokumenten und gelten als **ungeprüft** (§9.8). Baseline aufnehmen für:
`phase1_broker_wrapper`, `phase2_persistence`, `phase3_external_data`, `phase4_research`,
`phase5_execution`, `phase6_debate`, `phase7_reward`, `phase8_scheduler`, `phase9_universe`,
`phase10_v3`, `phase12_data_foundation`, `meta_m1_harness`, root `tests/`.

**A0.3 Phasen-Gerüst.** `phase13_live_data/CLAUDE.md` **existiert bereits** (Phasen-Kopf +
Session-Block 1, mit dem Plan committet) — **nicht** neu anlegen, nur den Session-Block nach
der Rotationsregel fortschreiben. Neu zu erstellen: `README.md`, `pyproject.toml`,
`requirements.txt`, `live_data/__init__.py` (leer), `tests/__init__.py`. Editable-Install in
`scripts/dev_install.sh` **anhängen** (Kette erweitern, Muster: der `phase12_data_foundation`-
Eintrag). Jede neue `.md` bekommt ihre `docs/INDEX.md`-Zeile im **selben** Commit.

**A0.4 Nummerierung** — **bereits erledigt** (L16, Commit dieses Plans). Die ausführende
Session prüft nur per Grep, dass kein „Phase 13 (V4)" mehr steht, und meldet Abweichungen.

**Akzeptanz A0:** Baseline-Tabelle im Session-Block; `python -c "import live_data"` läuft;
`docs/INDEX.md` kennt jede neue Datei; Grep auf „Phase 13 (V4)" leer.

---

#### Step A1 — `assess_window` + `WindowCoverage`

**Datei:** `phase12_data_foundation/data_foundation/coverage.py` (NEU, ~70 Zeilen).
Contract: §5.1. Reine Funktion, keine I/O, kein Import außerhalb stdlib +
`data_foundation.exceptions`.

Implementierungshinweise:
- `expected` = `max(0, int((end - start).total_seconds() // 60 // resolution_minutes))` —
  dieselbe naive Wanduhr-Rechnung wie `BarArchive.coverage_ratio` (`archive.py:179-187`).
  **Nicht** neu erfinden: Trade-Fenster liegen dank der U5-Deadline-Marge innerhalb der
  Handelszeit, dort ist naiv korrekt.
- `largest_gap_min`: über die sortierten, distinkten Zeitstempel die größte Differenz
  zweier aufeinanderfolgender Marken; zusätzlich die Ränder gegen `start_utc`/`end_utc`
  prüfen (eine Lücke am Fensteranfang ist genauso tödlich wie eine in der Mitte).
- Zeitstempel werden **lexikalisch** verglichen, wo es geht — Repo-Konvention
  (`paper.py:240`-Docstring). Für die Gap-Rechnung ist ein `datetime`-Parse nötig; dafür
  `_parse` aus `archive.py`-Muster lokal duplizieren (Phasen-Isolation, kein Import).

**Tests** (`phase12_data_foundation/tests/test_coverage.py`, NEU, ≥ 9):
1. volles Fenster → `covered=True`, `ratio==1.0`, `largest_gap_min==0`
2. leeres Fenster → `covered=False`, `reason=='empty'`
3. **Loch in der Mitte** (20 Min fehlen bei 300-Min-Fenster) → `covered=False`,
   `reason=='gap'`, obwohl `ratio > min_ratio` ← **das ist der Test, der F3 fängt**
4. Loch am Fensteranfang → `reason=='gap'`
5. Loch am Fensterende → `reason=='gap'`
6. gleichmäßig dünn (jede zweite Minute fehlt) → `reason=='sparse'`
7. `gap` schlägt `sparse`, wenn beides zutrifft
8. `expected == 0` (Start == Ende) → `covered=False`, kein `ZeroDivisionError`
9. Duplikate im Input (dieselbe Minute zweimal) zählen einmal

**Akzeptanz A1:** die neun Tests grün; `assess_window` hat null Aufrufer (wird in A2/A3
verdrahtet).

---

#### Step A2 — Der Schnitt in `BarService.get_window`

**Datei:** `phase12_data_foundation/data_foundation/service.py`. Contract: §5.3.

**Anker (verbatim, Zeilen Stand 2026-08-18):**

| Zeile | Verbatim-String | Aktion |
|---|---|---|
| 38 | `_MIN_WINDOW_COVERAGE = 0.5` | löschen (inkl. des `# ponytail:`-Kommentarblocks :34-37) |
| 182 | `        self._ig_provider = dict(providers).get("ig")` | löschen |
| 213 | `    def get_window(` | Body ersetzen (§5.3) |
| 218 | `        if (_covers_tail(archived, end_utc, minutes)` | löschen (bis :220) |
| 222 | `        count = max(1, int((_parse_iso(end_utc) - _parse_iso(start_utc)).total_seconds() // 60 // minutes) + 1)` | löschen (bis :227) |
| 229 | `        if not _covers_tail(archived, end_utc, minutes) and self._ig_provider is not None:` | löschen (bis :238, inkl. Kommentarblock) |
| 266 | `def _covers_tail(bars: Sequence[Any], end_utc: str, resolution_minutes: int) -> bool:` | ganze Funktion löschen (bis :273) |
| 276 | `def _bar_to_dict(bar: Any) -> dict[str, Any]:` | `"tick_count": bar.tick_count` ergänzen |

Der Klassen-Docstring (`service.py:1-16`) und der `BarService`-Docstring (`:157-166`)
beschreiben beide den alten Fetch-Pfad — **beide anpassen**, sonst steht die Löschung neben
ihrer eigenen Widerlegung. Ebenso der Modul-Docstring-Satz über den „paper tracker's raw
`broker.get_ohlcv`"-Ersatz.

**Wichtig:** `_parse_iso` (`:52`) wird danach evtl. unbenutzt — **erst greppen**, dann
löschen. `minutes`/`_RESOLUTION_MINUTES` bleiben (der Research-Seam nutzt sie, L15).

**Tests** (`phase12_data_foundation/tests/test_service.py`, umgeschrieben):
- Die bestehenden `get_window`-Tests, die einen Refetch **erwarten**, werden ersetzt — sie
  pinnen das gelöschte Verhalten. Neu:
- `test_get_window_never_fetches`: `BarService` mit einem Chain-Provider **und** einem
  IG-Provider, deren `get_bars` `AssertionError("no fetch allowed")` wirft; `get_window`
  über ein leeres Archiv gibt `[]` zurück und wirft nicht. ← **L12, die strukturelle
  Kostenzusicherung**
- `test_get_window_returns_archive_rows_only`
- `test_get_window_passes_through_tick_count`
- `test_bar_service_has_no_ig_provider_attribute` (Struktur-Guard gegen ein stilles
  Wieder-Aufreißen)

**Akzeptanz A2:** `grep -n "_covers_tail\|_MIN_WINDOW_COVERAGE\|_ig_provider" phase12_data_foundation/`
ist **leer**; `phase12_data_foundation` grün; die Nettobilanz des Diffs ist negativ
(Löschung > Ergänzung).

---

#### Step A3 — Tracker-Naht: Abdeckung je Trade

**Dateien:** `phase10_v3/abstain_lessons/paper.py` (§5.4) + `phase8_scheduler/scripts/wiring.py`.

**Anker (verbatim):**

| Datei:Zeile | Verbatim-String | Aktion |
|---|---|---|
| `paper.py:469` | `    def __init__(` (der `PaperTradeTracker`-Konstruktor) | `window_ok`-Param **ans Ende** der keyword-only-Liste |
| `paper.py:585` | `    def _resolve_group(` | Guard vor `resolve_paper_trade` einfügen |
| `paper.py:591` | `                outcome = resolve_paper_trade(trade, bars)` | Guard **davor**, innerhalb des `try` |
| `wiring.py:520` | `    def bar_fetch(epic: str) -> list[dict[str, Any]]:` | Docstring/Kommentar korrigieren: liest nur noch das Archiv |
| `wiring.py:523` | `        return bar_service.get_window(epic, "1m", start, _utc_iso(now))` | unverändert lassen (Shape bleibt) |
| `wiring.py:490` | `def _build_paper_tracker(config: SchedulerConfig, exec_cfg: Any, bar_service: Any) -> Any:` | `window_ok`-Closure bauen + injizieren |

Die `window_ok`-Closure in `_build_paper_tracker`:

```python
def window_ok(epic: str, bars, created_utc: str, time_stop_utc: str) -> bool:
    from data_foundation.coverage import assess_window   # lazy, Phasen-Isolation
    verdict = assess_window([b.get("timestamp", "") for b in bars], created_utc, time_stop_utc, 1)
    if not verdict.covered:
        record_event(str(_OBSERVABILITY_PATH), {
            "event": "window_uncovered", "epic": epic, "reason": verdict.reason,
            "ratio": verdict.ratio, "largest_gap_min": verdict.largest_gap_min,
        })
    return verdict.covered
```

Die Signatur ist in §5.4 gelockt: `(epic, bars, created_utc, time_stop_utc)`.

Der **Kommentarblock** `wiring.py:468-487` (über `_PAPER_MAX_FETCH_ATTEMPTS`) beschreibt den
alten Zustand („BarService.get_window's own budget-aware chain does…") — korrigieren, nicht
löschen: der Cap gilt jetzt zusätzlich für „Fenster noch nicht gedeckt".

**Tests:**
- `phase10_v3/tests/` (+4): `window_ok=None` ⇒ bit-identisch zum Alt-Verhalten ·
  `window_ok` gibt `False` ⇒ `_charge_failed_attempt` läuft, `resolve_paper_trade` wird
  **nicht** gerufen · nach `max_fetch_attempts` ⇒ `EXPIRED_UNRESOLVED` · **Mitten-Loch-Test:**
  ein Bar-Set, das ohne Guard eine `TIME_STOP`-Auflösung erzeugen würde, produziert mit
  Guard **keine** Auflösung ← **der wichtigste Test des ganzen Blocks (F3)**
- `phase12_data_foundation/tests/test_service.py`: unverändert grün

**Akzeptanz A3:** der Mitten-Loch-Test rot ohne den Guard, grün mit; `phase10_v3` grün;
`wiring.py` per `py_compile` sauber (kein eigenes Testfile — dokumentierte
„operator-run"-Konvention).

---

#### Step A4 — Stale-History-Assertion + typisierter Status (F1)

**Dateien:** `data_foundation/models.py`, `data_foundation/service.py`.

- `models.py`: neuer Status `DS_STALE_SOURCE = "stale_source"` in
  `KNOWN_DATA_SOURCE_STATUSES` (Anker: `KNOWN_DATA_SOURCE_STATUSES: frozenset[str] = frozenset(`,
  `models.py:30`). Ein Epic mit diesem Status fällt aus `measurable_universe()` (die Abfrage
  filtert auf `data_source_status='ok'`, keine Änderung nötig).
- `service.py`, `BudgetedIGBarProvider.get_bars`: **nach** dem Bauen der `PriceBar`-Liste
  (Anker: `        self._budget.record_spend(len(bars), self._spend_kind)`, `service.py:139`)
  eine Frische-Prüfung **vor** `record_spend`:

```python
newest = max(b.ts for b in bars)
if _age_minutes(newest, self._now_fn()) > self._stale_tolerance_min:
    self._emit(epic, False, reason="stale_history")
    return None          # der Spend ist trotzdem gebucht — IG hat ihn berechnet
```

⚠ **Reihenfolge zählt:** IG hat die Punkte auch dann berechnet, wenn die Daten unbrauchbar
sind. `record_spend` läuft **vor** dem Verwerfen, sonst lügt das Ledger nach unten. Das ist
kontraintuitiv und gehört als Kommentar an die Stelle.

`stale_tolerance_min` = neuer Konstruktor-Param, Default `120`.

**Registry-Konsequenz:** wer den `stale_history`-Event sieht, setzt den Status — das macht
**nicht** dieser Provider (er kennt die Registry nicht, D-Muster wie beim Sampler), sondern
die Sampler-Closure in A6.

**Tests** (`test_service.py`, +3): Bars mit `ts` innerhalb der Toleranz ⇒ normal ·
Bars älter als die Toleranz ⇒ `None` + `reason='stale_history'` · der Spend ist trotzdem
gebucht.

**Akzeptanz A4:** ein synthetischer FWM2-Fall (301 Bars mit `ts` = heute − 32 Tage) landet
**nicht** im Archiv und erzeugt einen typisierten Event.

---

#### Step A5 — `BarArchive`: `sources`-Filter + `tick_count`

**Datei:** `data_foundation/archive.py`. Contract: §5.2.

**Anker:** `        prefer: tuple[str, ...] = ("ig", "ls", "yf"),` (`archive.py:138`) —
`sources`-Param direkt darunter; `    def ensure_schema(self) -> None:` (`archive.py:82`) —
geführter ALTER am Ende; `_CREATE_BARS` (`archive.py:24`) — `tick_count INTEGER` ergänzen
(für frische DBs); `insert_bars`' INSERT (`archive.py:116-118`) — Spalte + Platzhalter.

⚠ `bars`' PRIMARY KEY bleibt `(epic, resolution, ts_utc, source)` — `tick_count` gehört
**nicht** hinein.

**Tests** (`test_archive.py`, +5): `sources=("yf",)` liefert nur yF-Zeilen ·
`sources=None` unverändert · `sources` + `prefer` zusammen · `ensure_schema` auf einer
DB **ohne** `tick_count` fügt die Spalte hinzu und ist beim zweiten Lauf ein No-Op ·
`insert_bars` schreibt `tick_count=None` ohne Fehler.

**Akzeptanz A5:** `ensure_schema` gegen eine **Kopie** der echten `bars.sqlite`
(nach `/tmp`, nie in-place) läuft durch und die 6504 bestehenden Zeilen bleiben lesbar.

---

#### Step A6 — Heartbeat: Abdeckungs-Alarm + Sampler-Reparatur (F1/F2)

**Datei:** `data_foundation/heartbeat.py` + die Sampler-Closure in `wiring.py:920-948`.

**A6.0 — der latente Niveau-Vergleich (Befund aus der S3-Recherche, 2026-08-18).**
`check_divergence` (`observability.py:130-140`) und `compute_divergence_pct` (`:123-127`)
vergleichen **absolute Kursniveaus** mit Schwelle `0.5 %`. Das ist strukturell falsch, sobald
zwei verschiedene Produkte verglichen werden — und genau das tut der Sampler heute: IGs
**CFD**-Mid gegen yFinances **Kassa**-Index. Der Abstand zwischen beiden ist eine Basis
(Finanzierung, Dividenden, Spread), kein Fehler. Empirisch gemessen an einem einzigen Tag über
drei Quellen: die AEX lag bei einem Anbieter **0,35 %**, bei einem anderen **2,1 %** über dem
Kassaschluss — beides dauerhafte, instrumentspezifische Offsets.

**Warum das ein latenter Bug ist, kein theoretischer:** überschreitet die Basis eines Epics je
0,5 %, setzt der Sampler nach zwei Läufen `data_source_status='mismatch'` und wirft das Epic aus
`measurable_universe()` — eine **selbstverschuldete Quarantäne-Kaskade** an einem Instrument,
mit dem nichts falsch ist. Dass das bisher nicht passiert ist (0 `quote_divergence`-Events),
ist eine Eigenschaft der aktuellen Paarungen, keine Garantie.

**Locked:** der Vergleich wechselt von Niveau auf **Veränderung**. `check_divergence`
(`observability.py:130`) und `compute_divergence_pct` (`:123`) bleiben **unangetastet** — der
Sampler (`heartbeat.py:195-197`) ist ihr einziger Produktions-Aufrufer (heute gegrept, außer
Tests kein weiterer), aber es sind Phase-8-Dateien und die Löschung brächte nichts. Der Sampler
bekommt
stattdessen `compute_return_divergence(ig_bars, yf_bars) -> float` in `heartbeat.py`: prozentuale
Bar-zu-Bar-Rendite beider Reihen über dasselbe Fenster, verglichen wird die **Differenz der
Renditen**. Eine konstante Basis fällt dabei heraus, eine echte Entkopplung nicht.
⚠ Das braucht ≥ 2 überlappende Bars je Quelle — bei nur einer Bar ist keine Rendite definiert:
dann typisierter Event `divergence_no_comparator` (s. A6.1), **nicht** stillschweigend 0.

**A6.1 `DivergenceSampler.sample_epic` — zwei Löcher schließen.** Anker:

| Zeile | Verbatim-String | Aktion |
|---|---|---|
| 179 | `        ig_bars = self.budgeted_ig.get_bars(epic, resolution="5m", count=3)` | direkt danach: Frische-Prüfung auf `ig_bars[-1].ts` |
| 186 | `        archived = self.archive.window(epic, "1m", window_start, window_end, prefer=("yf",))` | auf `sources=("yf",)` umstellen (L10) |
| 191 | `        yf_bars = [b for b in archived if b.source == "yf"]` | entfällt (der Store filtert jetzt) |
| 192 | `        if not yf_bars:` | **nicht mehr still**: typisierten Event `divergence_no_comparator` emittieren, dann `return` |

Neue Frische-Prüfung, direkt nach dem Fetch:

```python
if _age_minutes(ig_bar.ts, self.now_fn()) > self.stale_tolerance_min:
    self._emit({"event": "stale_source", "epic": epic, "provider": "ig",
                "bar_ts": ig_bar.ts, "age_min": ...})
    mark_stale_fn(epic)      # → data_source_status='stale_source'
    return
```

⚠ Das ist ein **zweiter** Callback neben `mark_mismatch_fn`. Signatur von `sample_epic` wird
verbindlich:

```python
def sample_epic(self, epic: str, mark_mismatch_fn: Callable[[str], Any],
                mark_stale_fn: Callable[[str], Any]) -> None: ...
```

`DivergenceSampler` bekommt zusätzlich das Feld `stale_tolerance_min: int = 120`.
⚠ **Das ist ein eigener Knopf, nicht derselbe wie A4s** `BudgetedIGBarProvider.stale_tolerance_min`
— gleicher Default, getrennt einstellbar. Begründung: der Provider schützt den *Schreibpfad*
(nichts Totes ins Archiv), der Sampler die *Diagnose* (wann ist eine Quelle als tot zu melden).
Sie zu koppeln hieße, eine Lockerung am einen Ort still am anderen mitzumachen. `GapRescue`
(§5.6) trägt aus demselben Grund seinen eigenen.

**Die beiden Aufrufer, die mitziehen müssen — namentlich:**
1. `phase8_scheduler/scripts/wiring.py:946`, verbatim
   `                    divergence_sampler.sample_epic(rec.epic, _mark_mismatch)`
   — braucht eine zweite Closure `_mark_stale` nach dem Muster von `_mark_mismatch`
   (`wiring.py:920-943`), die `data_source_status=DS_STALE_SOURCE` setzt und `logger.critical`
   loggt.
2. `phase12_data_foundation/tests/test_heartbeat.py` — jeder `sample_epic`-Aufruf.

**A6.2 `assess_day` — Abdeckung statt Bar-Zählung.** Anker:
`    bars_today = archive.bars_written_since(start, end)` (`heartbeat.py:72`).
`bars_today > 0` ist ein zu schwaches Signal (F3: 496 yF-Bars pro Epic am 18.08. und trotzdem
löchrige Fenster). Ergänzen: je `measurable_universe()`-Epic die Tages-Abdeckung über das
Handelsfenster via `assess_window`; neue `HealthVerdict`-Felder `worst_coverage: float` und
`epics_below_threshold: list[str]`; `ok=False`, sobald ein `ok`-Epic unter `MIN_WINDOW_RATIO`
liegt. Die `wiring.py`-Closure (`:967-977`) reicht die neuen Felder in den Event durch.

**Tests** (`test_heartbeat.py`, +7): stale IG-Bar ⇒ `mark_stale_fn` gerufen, **kein**
Vergleich · fehlender yF-Komparator ⇒ Event statt Stille · `sources`-Filter wird benutzt
(kein Nachfiltern im Aufrufer) · `assess_day` mit einem löchrigen Epic ⇒ `ok=False` ·
`assess_day` mit vollständiger Abdeckung ⇒ `ok=True` · `worst_coverage` korrekt · die drei
bestehenden `ok=False`-Bedingungen unverändert.

**Akzeptanz A6:** ein synthetischer 18.08.-Nachbau (FWM2 mit einen Monat alter IG-Bar)
erzeugt `stale_source` + Statuswechsel; der bestehende Alarmtest aus P12.5 Step 5 (d-i)
bleibt grün.

---

#### Step A7 — Registry-Hygiene + Operator-Sequenz

**A7.1 Bestandsaufnahme, read-only.** `IX.D.IBEX.FWM2.IP` trägt heute
`data_source_status='ok'` mit `yf_ticker='^IBEX'` (Kassa-Index für einen Forward-Kontrakt,
F1). Nach A6 setzt der erste Sampler-Lauf den Status selbst auf `stale_source`. Die
ausführende Session **greift nicht per Hand in die DB ein** — sie dokumentiert nur, dass die
14 `RESOLVED/yf`-Zeilen dieser Epic vom 18.08. in der ersten Auswertung **getrennt**
auszuweisen sind (nicht löschen: sie sind ehrliche Daten mit bekanntem Etikett).

**A7.2 Die 20 am 18.08. offen gebliebenen Shadow-Zeilen** laufen beim nächsten Start über den
Staleness-Guard typisiert ab. Das ist **kein Messausfall** und darf in der ersten Auswertung
nicht als einer verbucht werden (Closeout §6).

**A7.3 Operator-Sequenz (Nikinger, gegatet):**
1. `python phase12_data_foundation/scripts/probe_allowance.py` (5 Punkte) — frische
   `remainingAllowance`-Beobachtung.
2. `ps aux | grep scheduler.run` — muss leer sein.
3. Neustart **mit** Messarm: `--enable-shadow-schedule --enable-divergence-sampler`.
4. Nach dem ersten Handelstag: `python phase12_data_foundation/scripts/data_health.py`
   und die Punktebilanz. **Erwartung: Tracker-Anteil exakt 0.**

**Akzeptanz Block A:** ein voller Handelstag mit scharfem Messarm und **null** Punkten auf
`spend_kind` in `{tracker}` bzw. null 301-Punkt-Cluster im Ledger; `window_uncovered`-Events
existieren und sind auswertbar; alle Suiten grün.

---

### BLOCK B — Live (Lightstreamer)

#### Step B0 — Gating-Live-Check (Operator, kostenlos)

**Das ist die größte unverifizierte Annahme des Plans.** IG hat `MARKET:`/`L1:` am
2026-05-08 abgeschaltet (`ig_lightstreamer.py:11-12`); ob `CHART:` davon betroffen war, ist
**nicht** belegt — die Feldliste in §5.5 stammt aus Drittbibliotheken und IG-Labs-Forenposts,
labs.ig.com selbst antwortete beim Abruf mit HTTP 403.

**Skript:** `phase13_live_data/scripts/probe_chart_stream.py` (die ausführende Session baut es
in B0, bevor irgendetwas anderes gebaut wird). Es abonniert `CHART:IX.D.DAX.IFMM.IP:1MINUTE`
mit den Feldern aus §5.5, druckt jede Update-Zeile roh und beendet sich nach N Kerzen oder
Timeout. **Kosten: 0** (Streaming-Kontingent, nicht Historien-Punkte —
[IG-Doku](https://www.ig.com/en/trading-platforms/trading-apis/how-to-use-ig-api): 10 000
Historienpunkte/Woche gelten für REST, Streaming hat ~40 gleichzeitige Subscriptions je
Verbindung). Vorbild: `phase1_broker_wrapper/scripts/test_lightstreamer.py`.

**Verzweigung — beide Zweige sind ausgeplant, die Session stallt nicht:**
- **JA (CHART liefert):** B1/B2 wie beschrieben. `CONS_TICK_COUNT` füllt `bars.tick_count`.
- **NEIN (`onSubscriptionError` oder keine Updates):** `TickAggregator` (§5.6) wird der
  Primärpfad. `tick_count` = Anzahl aggregierter Ticks. **Zusätzlich verbindlich:** der
  Session-Block hält fest, dass LS-Bars in diesem Modus High/Low unterschätzen können, und
  die Beweiswoche weist `tick_count`-Perzentile aus. Ein LS-Bar mit `tick_count <= 2` gilt
  in `source_delta.py` als „dünn" und wird getrennt ausgewiesen.

⚠ **Parallel-Login-Falle:** dieser Probe-Lauf ist ein IG-authentifizierender Prozess. Der
Scheduler muss dabei **stehen** (`reference_ig_parallel_login_trap`).

#### Step B1 — P1-Streaming: Kerzen-Abo

**Dateien:** `phase1_broker_wrapper/broker_wrapper/streaming/base.py`,
`.../ig_lightstreamer.py`, `.../__init__.py` (Export). Contract: §5.5.

**Anker:** `_FIELDS = ["BIDPRICE1", "ASKPRICE1", "TIMESTAMP"]` (`ig_lightstreamer.py:41`) —
`_CHART_FIELDS` daneben; `    def _do_subscribe(self, epic: str) -> None:`
(`ig_lightstreamer.py:190`) — `_do_subscribe_chart` daneben; `        self._subs: dict[str, Subscription] = {}`
(`:128`) — `self._chart_subs` daneben; `    def stop(self) -> None:` (`:149`) — beide
Dicts räumen; `@dataclass\nclass PriceTick:` (`base.py:24-25`) — `ChartCandle` daneben.

`StreamClient` (die ABC, `base.py:35`) bleibt **unangetastet** — `subscribe_candles` ist
IG-spezifisch und duck-typed, `PollingStreamClient` zieht nicht mit.

`UTM` ist Unix-ms → `_utm_to_iso` (`ig_lightstreamer.py:44`) existiert und wird
wiederverwendet, nicht neu geschrieben.

**Tests** (`phase1_broker_wrapper/tests/test_lightstreamer.py`, +8, alle gemockt): Item-String
exakt `CHART:{epic}:1MINUTE` · Feldliste exakt · `MERGE`-Modus · Mid-Rechnung aus BID/OFR
(L7) · `CONS_END != "1"` ⇒ **kein** Callback · `CONS_END == "1"` ⇒ Callback mit
`complete=True` · fehlendes/nicht-numerisches Feld ⇒ kein Crash, kein Callback ·
`stop()` räumt Preis- **und** Kerzen-Abos.

#### Step B2 — `LSBarRecorder`

**Datei:** `phase13_live_data/live_data/stream.py` (NEU). Contract: §5.6.

`on_candle` schreibt **nur** bei `complete=True` genau eine `Bar` mit `source='ls'`,
`tick_count=candle.tick_count`, `fetched_at=now`. Fail-soft wie `Recorder.tick`
(`recorder.py:104-147`) — eine Epic darf nie den Stream töten. Kein Broker-Import, kein LLM.

**Tests** (`phase13_live_data/tests/test_stream.py`, ≥ 8): unvollständige Kerze ⇒ kein Write ·
vollständige Kerze ⇒ genau eine Archivzeile mit `source='ls'` · Archiv-Fehler ⇒ geloggt, nicht
geworfen · `resync_epics` abonniert neue, kündigt entfallene · `restart` baut Abos neu auf ·
`stop` ist idempotent · doppelte Kerze zur selben Minute ⇒ ein Row (PK) · `tick_count` landet
in der Zeile.

#### Step B3 — Lebenszyklus + Token-Rotation

**Dateien:** `phase8_scheduler/scheduler/runner.py`, `scripts/wiring.py`,
`scheduler/config.py`, `scheduler/run.py`.

**Der Kern dieses Steps ist die Token-Rotation.** `_warm_session` (`runner.py:432`) ruft
`self._broker.connect()`, sobald die Session weg ist — **jeder** dieser Re-Logins rotiert
CST/XST und macht einen LS-Client, der auf dem alten Paar aufgebaut wurde, wertlos
(`lightstreamer_integration_notes.md`, „Parallel-login auth trap": IG rotiert
`X-SECURITY-TOKEN` bei jedem `POST /session`).

**Anker + Aktion:**

| Datei:Zeile | Verbatim-String | Aktion |
|---|---|---|
| `runner.py:432` | `    def _warm_session(self) -> None:` | am Ende des Re-Login-Zweigs `self._restart_bar_stream()` |
| `runner.py:441` | `        env = self._broker.connect()` | der Restart gehört **nach** der ok-Prüfung |
| `runner.py:219` | `    def __init__(` | `bar_stream: Any | None = None` (keyword-only, ans Ende) |
| `runner.py:285` | `        self._run_universe_refresher()` | in `preflight()`, **danach** `self._start_bar_stream()` |
| `runner.py:413` | `    def shutdown(self, state: SchedulerState) -> None:` | `self._stop_bar_stream()` als eigener guarded Block |
| `wiring.py:998` | `    return SchedulerRunner(` | `bar_stream=bar_stream,` ergänzen |
| `config.py:207` | `    enable_divergence_sampler: bool = False` | `enable_bar_stream: bool = False` daneben |
| `run.py:130` | `    parser.add_argument("--verbose", action="store_true", help="DEBUG logging to stderr.")` | `--enable-bar-stream` davor (Muster: `--enable-divergence-sampler`) |
| `run.py:157` | `        enable_divergence_sampler=args.enable_divergence_sampler,` | `enable_bar_stream=args.enable_bar_stream,` daneben |

Den Restart **in** `_warm_session` zu setzen (statt an jedem Aufrufer) ist bewusst: es gibt
mehrere Aufrufer (`preflight`, WINDOW, POST_WINDOW, `shutdown`), und ein Guard pro Aufrufer
ist genau der zweite Bug.

`_start_bar_stream`/`_stop_bar_stream`/`_restart_bar_stream` sind fail-soft (`logger.critical`,
nie werfend) — Muster: `_run_universe_refresher` (`runner.py:484-497`).

**Tests** (`phase8_scheduler/tests/test_runner.py`, +6): `bar_stream=None` ⇒ bit-identisch ·
`preflight` startet den Stream **nach** `broker.connect()` · ein Re-Login in `_warm_session`
löst genau einen `restart()` aus · ein No-Op-`_warm_session` (bereits verbunden) löst **keinen**
aus · `shutdown` stoppt den Stream auch, wenn der Reconcile vorher warf · eine werfende
`stream.start()` killt den Daemon nicht.
`phase8_scheduler/tests/test_run.py`: +1 für das CLI-Arm.

#### Step B4 — Recorder-Abstimmung

Mit laufendem S1 ist S2 kein Primärlieferant mehr, sondern Backfill. Der Recorder bleibt
**unverändert** (er läuft, er ist kostenlos, er deckt Bot-aus-Zeiten). Einzige Anpassung:
sein `count` (Default 30, `recorder.py:74`) darf bleiben — `INSERT OR IGNORE` macht Overlap
gratis. **Explizit kein Step:** den Recorder abzuschalten, sobald LS läuft. Er ist die
Rückfallebene, deren Fehlen Phase 12 gekostet hat.

**Akzeptanz Block B:** ein Handelstag mit `--enable-bar-stream`; im Archiv existieren
`source='ls'`-Zeilen für jede `measurable_universe()`-Epic; die Tages-Abdeckung je Epic
(A6.2) liegt über `MIN_WINDOW_RATIO`; `window_uncovered`-Events gehen gegenüber Block A
messbar zurück; **null** zusätzliche IG-Historienpunkte.

---

### BLOCK C — Stufe 3, Stufe 4, Reports

#### Step C1 — S3: unabhängige Fremdquelle

**Datei:** `phase13_live_data/live_data/backfill.py` (NEU).

**Auswahlkriterien (bindend):** kostenlos oder < 10 €/Monat · 1-Minuten-Granularität ·
Abdeckung der europäischen Indizes (DAX, CAC, **IBEX**, AEX, FTSE, MIB, STOXX50) · per
`requests` erreichbar (Repo-Konvention, **nicht** httpx/urllib) · dokumentierte API oder
ausdrücklich erlaubter Bulk-Download, **kein** HTML-Scraping und **nichts**, wofür eine
Zugangssperre umgangen werden müsste · Publikationsverzug bekannt und < 2 h. Eine kleine,
gepflegte pip-Abhängigkeit ist erlaubt (Memory `feedback_util_deps_venv`) — Paketname +
letztes Release im Session-Block festhalten.

#### C1.0 — Marktlage 2026-08-18 (recherchiert, nicht geraten)

**Befund: keine kostenlose Quelle erfüllt alle Kriterien gleichzeitig.** Vier Kandidaten
geprüft, jeder mit genau einer disqualifizierenden Eigenschaft:

| Kandidat | Abdeckung | Verzug | Aufwand | Was dagegen spricht |
|---|---|---|---|---|
| **Dukascopy** Datafeed | ✅ **alle**, inkl. IBEX + MIB (je 1440 Bars am 17.08. verifiziert) | ~90 s nach Stundenschluss (Tick-Dateien) | `requests` + stdlib `lzma`/`struct`, keine neue Abhängigkeit | 🔴 **ToS verbietet den Fall wörtlich:** „The WEBSITE and the information contained therein **may not be used to construct a database of any kind**." Unser Archiv *ist* eine Datenbank. Nikinger-Entscheidung, keine Ingenieursfrage. |
| **Deriv** WebSocket | DAX, CAC, AEX, FTSE, ESTX50 — ❌ **kein IBEX, kein MIB** | ~1 Min | WebSocket-only, kein REST → bricht die `requests`-Regel (`websockets` v16 liegt bereits im venv; Präzedenzfall Lightstreamer) | IBEX ist **2 von 5** messbaren Epics. Taugt damit nicht zum Lückenfüllen. |
| **Capital.com** Demo-API | ⚠️ **ungeprüft** — Germany 40 / France 40 / Spain 35 sind handelbare Produkte, aber keine Epic verifiziert | ⚠️ ungeprüft | ✅ reines `requests`/REST, Muster wie der IG-Adapter (API-Key → Session → CST/XST), 10 req/s | Unbewiesen. Und es ist eine **Broker**-API wie IG — ein Auth-Ausfall kann Primärquelle und Gegenprobe gleichzeitig treffen. |
| **Bezahlt** (DB Non-Display) | ✅ | Echtzeit | Lizenzvertrag | **313 €/Monat** allein für „DAX Indices" (Tier 3, Entry, netto, Preisliste v9_1 gültig ab 2025-01-01); keine Privatpersonen-Ermäßigung; IBEX wäre eine separate BME-Lizenz. |

**Börsen-direkt und offene Behördendaten sind geprüft und tot** — hier vollständig, damit es
niemand ein zweites Mal recherchiert:
- **Deutsche-Börse-Public-Data-Set** (1-Min-Xetra-Daten): **offline** — beide S3-Buckets
  antworten anonym mit `AccessDenied`, das AWS-Registry-YAML trägt `Deprecated: True`,
  `registered-data.deutsche-boerse.com` löst nicht mehr auf. Zwei weitere Kill-Shots, falls es
  je zurückkommt: die Lizenz war **Non-Commercial** (nicht CC BY, wie ursprünglich vermutet),
  und es enthielt nur **Einzelinstrumente, nie Indexstände**.
- **ETF-Proxy** (DAX-ETF statt DAX): moot, weil genau dieses Datenset die Quelle gewesen wäre —
  und ohnehin die schwächere Idee: ein ETF bringt eigene Tracking-Differenz, eigenen Spread und
  eigene Liquiditätslücken **zusätzlich** zur Indexbewegung, die man verifizieren will.
- **Euronext MiFID-II-Trades-Files** (CAC/AEX/MIB-Handelsplätze): existieren wirklich, sind
  gratis und lizenzsauber — aber **15 Min verzögert**, **instrumentbezogen ohne Indexstände**,
  und ohne stabile Download-URL (Web-Download-Dienst, kein `requests`-Vertrag).
- **BME / IBEX:** kein freies Intraday-Produkt gefunden. ⚠️ Unbestätigt, Tendenz negativ.
- **Warum die MiFID-II-Gratispflicht das grundsätzlich nicht lösen kann:** sie gilt für
  **Handelsplatzdaten zu Finanzinstrumenten**, nicht für proprietär *berechnete* Indexstände.
  DAX, CAC 40 und IBEX 35 sind lizenzierte Indexprodukte ihrer jeweiligen Börse — genau
  deshalb existiert die 313-€-Position. Den Index aus Konstituenten nachzurechnen bräuchte
  Konstituentenliste, Free-Float-Faktoren und Divisor, alle selbst lizenzpflichtig. **Nicht.**

**ENTSCHIEDEN (Nikinger 2026-08-18): die Wahl wird auf nach Block B vertagt.** Grund: erst
Block B liefert die **gemessene** Lückenrate. Ist sie mit laufendem LS klein, ist S3s Grenznutzen
klein und S4 reicht als Rückfallebene; ist sie groß, rechtfertigt sie die Kosten der jeweils
unangenehmen Eigenschaft. Genau diese Reihenfolge — erst messen, dann entscheiden — ist die
Lehre aus P12.5.

**L17 entschärft diese Entscheidung zusätzlich:** live sein muss die **Preisreihe**, und die
liefert S1. Was S3 beisteuert, sind Begleitgrößen und nachträgliches Lückenfüllen — beides darf
verspätet sein. Damit ist der Publikationsverzug eines Kandidaten **kein** Ausschlusskriterium
mehr, sondern nur noch Abdeckung, Lizenz und Zugriffsweg. Das ordnet das Feld neu: Dukascopys
~90 Minuten sind unter L17 unproblematisch, seine ToS-Klausel bleibt der einzige Einwand.

**Wenn doch früher entschieden werden soll:** Capital.com, gegatet auf einen
kostenlosen Live-Check (liefert die Demo-API `resolution=MINUTE` für Germany 40 / France 40 /
**Spain 35**, und wie weit zurück?). Es ist die einzige Option ohne ToS-Kollision und ohne neue
Abhängigkeit — und als Broker-CFD-Preisreihe liegt sie **näher an IGs eigener Reihe** als der
yF-Kassaindex, was sie zugleich zur besseren Gegenprobe und zum brauchbareren Lückenfüller für
SL/TP-Auflösung macht.

**Betriebsmodell:** lückengetrieben, nicht zeitgetrieben. Ein Tages-Pass fragt das Archiv nach
Lücken älter als `min_gap_age_min`, holt genau diese Spannen, schreibt mit eigenem
`source`-Tag (⇒ `KNOWN_SOURCES` in `models.py:22` erweitern **und** `BarArchive.window`s
`prefer`-Default um die neue Quelle ergänzen — sonst rankt sie stumm hinter yF).

⚠ **`prefer` ist heute `("ig", "ls", "yf")`** (`archive.py:138`). Eine neue Quelle, die nicht
in `prefer` steht, bekommt `default_rank` und verliert jeden Gleichstand. Das ist ein stiller
Fehler, der wie „die neue Quelle liefert nichts" aussieht.

**Vier Regeln für jede externe Quelle — quellenunabhängig, aus der Recherche vom 2026-08-18,
jede empirisch belegt:**
1. **Antwortfenster nach dem Fetch prüfen.** Mindestens eine untersuchte API beantwortet ein
   Fenster jenseits ihrer Historientiefe mit **aktuellen** Bars und **ohne** Fehler — ein
   naiver Lückenfüller archiviert dann falsch datierte Daten und merkt nichts. Jede Antwort:
   `assert` alle Zeitstempel liegen im angefragten Fenster, sonst verwerfen + typisierter Event.
2. **Keine synthetischen Bars übernehmen.** Mindestens ein untersuchter Anbieter füllt
   Nicht-Handelsminuten mit dem letzten Kurs auf (gemessen: ein Samstag lieferte 1440 von 1440
   Bars mit `O==H==L==C` und Volumen 0). Filter: `O==H==L==C` **und** `volume in (0, None)`
   **und** Minute außerhalb der Handelszeit ⇒ nicht schreiben.
3. **Vergleiche nie über absolute Niveaus** (s. A6.0) — jede Fremdquelle ist ein anderes Produkt
   mit eigener Basis.
4. **Backoff ist Pflicht, nicht Kür.** Bei den geprüften Gratis-Endpunkten traten `429` und
   wiederholte `503` innerhalb weniger Dutzend Anfragen auf, auf URLs, die Sekunden vorher `200`
   lieferten.

**Fold-in-Checkliste, sobald die Quelle gewählt ist** — der Name muss an **allen vier** Stellen
landen, sonst driftet der Plan gegen den Code:
- [ ] §0-Stufentabelle: „unabhängige Fremdquelle" → der Name
- [ ] dieser Step (C1) selbst
- [ ] `data_foundation/models.py:22` — `KNOWN_SOURCES` erweitern
- [ ] `data_foundation/archive.py:138` — `prefer`-Default erweitern (**die am leichtesten
      vergessene**, s. §8)

**Tests** (`phase13_live_data/tests/test_backfill.py`, ≥ 6, **alle gemockt, kein Netz**):
Lückenerkennung · exakte Spannenanfrage · Zeitzonen-/Format-Normalisierung über
`normalize_bar_ts` · leere Antwort ⇒ fail-soft · unbekannte Quelle ⇒ `ArchiveError` ·
Dedup gegen bestehende Zeilen.

#### Step C2 — S4: `GapRescue` (die Handover-Fixes als Rückfallebene)

**Datei:** `phase13_live_data/live_data/rescue.py` (NEU). Contract: §5.6. **Default AUS**
(`enable_gap_rescue: bool = False`).

Setzt die drei Bausteine aus Failure-Handover §5 um — aber als **letzte** Stufe, nicht als
Hauptpfad:
1. **Eigener `spend_kind="rescue"`** — der Ledger wird eindeutig (Failure-Handover §5.1: der
   geteilte Provider taggte Tracker-Top-ups fälschlich als `research`, die Kostenexplosion war
   im Ledger nicht auffindbar).
2. **Lückengroße Anfrage** statt Vollfenster — und zwar über
   `broker.get_historical_ohlcv(epic, from_dt, to_dt, resolution)`
   (`ig_adapter.py:449-451`, **Bereichs-API mit `from`/`to`**). Damit ist der Einwand des
   Failure-Handovers §5.2 („Chain-Provider ist count-basiert") gegenstandslos: die
   Rettungsstufe geht am Chain-Provider vorbei direkt an den Adapter.
   ⚠ `get_historical_ohlcv` bucht **keinen** Spend — `GapRescue` muss ihn selbst gegen
   `SourceBudget` buchen und vorher `can_spend` fragen.
3. **Drossel** `max_calls_per_epic_per_day` nach dem Muster von `DivergenceSampler`s
   `_last_sample_date` (`heartbeat.py:156`).

Plus die Frische-Assertion aus L8/A4 (`stale_tolerance_min`) — hier gehört sie hin, nicht in
`insert_bars`.

**Tests** (`test_rescue.py`, ≥ 8): Lücke < `min_gap_age_min` ⇒ kein Call · Drossel greift beim
zweiten Aufruf desselben Tages · `can_spend=False` ⇒ kein Call · Punkte werden gebucht ·
stale Antwort ⇒ kein Write + typisierter Event · Lückengröße = angefragte Spanne ·
`RescueReport` korrekt · Default-AUS heißt: ohne Flag existiert das Objekt gar nicht.

#### Step C3 — `scripts/source_delta.py` (Nikinger Q4)

**Datei:** `phase13_live_data/scripts/source_delta.py` (NEU, read-only, `mode=ro`).

Für jede in einem Zeitraum aufgelöste `paper_trades`-Zeile: das Trade-Fenster **je Quelle
getrennt** aus dem Archiv lesen (`BarArchive.window(..., sources=("ls",))` bzw. `("yf",)`,
L10), `resolve_paper_trade` **unverändert** ein zweites Mal aufrufen und ausgeben:
Übereinstimmung ja/nein · `exit_reason` je Quelle · `pnl_points`-Differenz · Anteil der
Zeilen, bei denen die Quelle das Ergebnis dreht · `tick_count`-Perzentile der LS-Bars.

Das ist der „Differenz = eigene Messgröße"-Auftrag. Kein Pipeline-Eingriff, keine
Schema-Änderung, keine zweite Wahrheit pro Zeile (L9).

**Tests** (`test_source_delta.py`, ≥ 4, gegen eine temporäre DB): Übereinstimmung ·
Nicht-Übereinstimmung · fehlende Quelle ⇒ Zeile als „nicht vergleichbar" ausgewiesen,
nicht als Übereinstimmung · exit code ≠ 0 nur bei Lesefehler, nie bei Divergenz.

#### Step C4 — Beweiswoche + Abnahme

Täglich `data_health.py` (Exit 0 erwartet). Freitags eine Review-Session nach dem
`phase10_v3`-Muster, Ergebnisdoc
`phase13_live_data/PROOF_WEEK_REVIEW_<date>.md`. PASS-Kriterien: §7.

---

## §7 Abnahme (PASS-Kriterien)

| # | Kriterium | Wie belegt |
|---|---|---|
| **P1** | **Der Verbrauchspfad gibt null IG-Punkte aus.** | `source_spend` enthält für die Woche **keinen** Eintrag mit `kind='tracker'` und keinen 301-Punkt-Cluster; der L12-Test ist grün. |
| **P2** | Jede in der Woche aufgelöste `paper_trades`-Zeile hat `resolution_source ≠ NULL`. | SQL über die Woche. |
| **P3** | **Keine Auflösung aus einem ungedeckten Fenster.** Jede `TIME_STOP`-Zeile stammt aus einem Fenster, das `assess_window` als gedeckt einstuft. | `source_delta.py` + `window_uncovered`-Events; ein Gegenbeispiel = FAIL. |
| **P4** | LS liefert: `source='ls'`-Zeilen an 5/5 Handelstagen für jede `measurable_universe()`-Epic. | Archiv-Query. |
| **P5** | Tages-Abdeckung je `ok`-Epic ≥ `MIN_WINDOW_RATIO` an ≥ 4/5 Tagen. | `assess_day`-Verdikte. |
| **P6** | Der Quellen-Delta-Report existiert und beziffert, in wie viel Prozent der Fälle die Quelle das Ergebnis dreht. | `source_delta.py`-Ausgabe im Review-Doc. **Kein Zielwert** — die Zahl ist das Ergebnis, nicht die Hürde. |
| **P7** | IG-Wochenverbrauch < 1 500 Punkte (Phase-12 Anforderung F, unverändert), **kein** 403. | Ledger + `allowance_observations`. |
| **P8** | 5/5 Tage `measurement_heartbeat`; jeder Problemtag am **selben** Tag CRITICAL. | Event-Log. |
| **P9** | Kein Epic mit toter Historie steht auf `ok`. | Registry-Query; FWM2 muss `stale_source` tragen. |

**FAIL ⇒ Root-Cause-Session, kein Weiterbau.** Dieselbe Notbremsen-Logik wie 2026-08-11 und
2026-08-18.

---

## §8 Fehlgriffe, die wie andere Fehler aussehen

> Jede Zeile: **Symptom** → **erster Verdächtiger**. Billiger als die Debug-Session danach.

| Symptom | Erster Verdächtiger |
|---|---|
| „Das Archiv füllt sich nicht mehr, der Recorder ist tot." | Eine Frische-Assertion, die versehentlich in `BarArchive.insert_bars` gelandet ist statt am IG-Kaufort (L8). Der Recorder schreibt legitim bis zu 7 Tage alte yF-Bars; S3 noch ältere. `recorder_state.json` prüfen: `bars_written` > 0 bei `errors: []` ⇒ Recorder lebt, der Guard frisst. |
| „Nach dem Schnitt lösen plötzlich viel weniger Trades auf." | **Kein Bug — das ist das Feature.** Vorher wurden Fenster mit Löchern zu erfundenen `TIME_STOP`s (F3). Gegenprobe: `window_uncovered`-Events zählen. Erst wenn die Rate auch mit laufendem LS hoch bleibt, ist `MIN_WINDOW_RATIO`/`MAX_WINDOW_GAP_MIN` zu streng kalibriert — das sind Knöpfe, keine Konstanten. |
| „LS abonniert, aber es kommen keine Kerzen." | Reihenfolge in `subscribe_candles`: die SDK-`Subscription` muss **nach** `client.connect()` registriert werden, sonst hängt sie im Leeren (`_do_subscribe`s `active`-Prüfung, `ig_lightstreamer.py:169-171`, macht das für Preise bereits richtig — der Kerzenpfad muss dasselbe Muster spiegeln, nicht ein eigenes). Zweiter Verdächtiger: `setDataAdapter` — Preise brauchen `"Pricing"`, für CHART ist der Adapter **unbestätigt** (§9.2). |
| „LS lief, dann kam stundenlang nichts mehr." | Token-Rotation: `_warm_session` hat re-eingeloggt und der LS-Client hängt an toten CST/XST (B3). Gegenprobe: im Log ein `broker connect` **ohne** ein nachfolgendes Stream-Restart-Log. |
| „Der Divergenz-Sampler meldet nie etwas, alles ist gut." | Genau das war F2. `if not yf_bars: return` — Abwesenheit von Events ist **kein** Beweis von Übereinstimmung. Nach A6 muss es `divergence_no_comparator`-Events geben, wenn nichts verglichen werden konnte. |
| „Plötzlich fallen Epics reihenweise auf `mismatch` und verschwinden aus `measurable_universe()`." | Ein **Niveau**-Vergleich statt eines Rendite-Vergleichs (A6.0). Zwei verschiedene Produkte (CFD vs. Kassa vs. Fremdquelle) tragen eine dauerhafte Basis — gemessen bis 2,1 % — die kein Fehler ist. Gegenprobe: ist der gemeldete `pct` über Tage **konstant**, ist es die Basis; schwankt er, ist es echte Entkopplung. |
| „Die neue Fremdquelle liefert Bars mit Zeitstempeln, die niemand angefragt hat." | Kein Bug bei uns: mindestens eine geprüfte externe API antwortet auf ein Fenster außerhalb ihrer Historientiefe mit **aktuellen** Bars und **ohne** Fehler (C1, empirisch belegt). Deshalb ist die Fensterprüfung nach dem Fetch Pflicht, nicht Kür. |
| „Seit LS läuft, ist das Volumen überall `NULL` — die Volumen-Verarbeitung ist kaputt." | Wahrscheinlich nicht kaputt, sondern **verdrängt**. `BarArchive.window` kollabiert per `prefer` auf **eine** Zeile je `ts_utc`, und `ls` rankt vor `yf` (`archive.py:138`). Trägt die LS-Kerze keinen Volumenwert, verdeckt sie die yF-Zeile derselben Minute, die einen hätte. Das ist die direkte Folge von L17 und **kein** Fehler im Volumenpfad. Gegenprobe: `SELECT source, COUNT(*) FROM bars WHERE ts_utc = '<Minute>'` — liegen beide Zeilen da, ist es die Rangfolge. |
| „Die neue S3-Quelle schreibt, aber ihre Bars tauchen nie in einer Auflösung auf." | `prefer` in `BarArchive.window` (`archive.py:138`) kennt sie nicht ⇒ `default_rank` ⇒ sie verliert jeden Gleichstand gegen yF (C1). |
| „`ensure_schema` wirft `duplicate column name: tick_count`." | Der geführte `PRAGMA table_info`-Check fehlt oder läuft nach dem ALTER (A5). `CREATE TABLE IF NOT EXISTS` schützt nicht vor einem nackten ALTER. |
| „Nach dem Neustart sind 20 Paper-Zeilen `EXPIRED_UNRESOLVED`." | Erwartet. Die am 18.08. beim Stopp offenen Zeilen (A7.2). Kein Messausfall. |
| „Der Ledger zeigt weniger Punkte als IG selbst." | Ein `return None` vor `record_spend` in `BudgetedIGBarProvider` (A4). IG berechnet den Call auch, wenn wir die Daten verwerfen — `record_spend` muss **vor** dem Verwerfen laufen. |
| „`resolve_paper_trade` ist kaputt, es kommt `None` zurück." | Wahrscheinlich nicht die Funktion, sondern der neue `window_ok`-Guard davor (A3), der die Bars gar nicht erst durchlässt. `window_uncovered`-Event für dieselbe Epic/Minute suchen. |

---

## §9 Bei Ausführung verifizieren (Drift-Liste — vollständig)

> Diese Liste ist **abschließend**: was hier nicht steht, hat diese Planungssession am
> 2026-08-18 selbst gegen Code oder Live-DB geprüft und ist als Fakt formuliert. Nichts hier
> stammt ungeprüft aus einem Vorgänger-Handover.

1. **Alle Datei:Zeile-Anker** (Stand `c38cb9f`, 2026-08-18) vor dem Edit per Grep auf den
   **Verbatim-String** re-verifizieren. Steps verschieben einander die Zeilen.
2. **`CHART:{epic}:1MINUTE` existiert auf diesem Konto** — Feldnamen, `setDataAdapter`-Wert,
   und ob `CONS_END`/`CONS_TICK_COUNT` tatsächlich geliefert werden. Quelle der Feldliste:
   Drittbibliotheken + IG-Labs-Forum, **nicht** die Primärdoku (labs.ig.com gab 403).
   **Step B0 ist genau dieser Check und gatet Block B.**
3. **Tickdichte je Epic**, falls der Fallback greift: reichen die `PRICE`-Updates für
   brauchbare 1-Min-OHLC? Step 7a maß 21/2/15/7 Updates (DAX/STXE/CAC/IBEX) — die 2 für STXE
   ist das Warnsignal.
4. **Überlebt die LS-Session einen REST-Re-Login?** B3 baut den Restart defensiv ein (er
   schadet nie). Ob er **nötig** ist, ist unbestätigt — beim ersten Langlauf beobachten.
5. **`ig_adapter.get_historical_ohlcv`-Verhalten live:** akzeptiert IG `from`/`to` für
   `MINUTE`-Auflösung über kurze Spannen, und was steht dann im `allowance`-Objekt?
   Code-seitig verifiziert (`ig_adapter.py:449-477`), **live ungeprüft**.
6. **Zählt `get_historical_ohlcv` gegen dasselbe 10 000er-Kontingent wie `get_ohlcv`?**
   Annahme: ja (beides `/prices/{epic}`). Erst nach einem Realaufruf bestätigt.
7. **Migrationsnummer:** Phase 13 braucht **keine** P2-Migration (`bars.sqlite` ist eine
   eigene Datei, `ensure_schema` ist ihr DDL-Ort). Falls C1/C3 doch eine Spalte in
   `trading_bot.sqlite` braucht: nächste freie Nummer erst greppen (Stand heute 001–006).
8. **Test-Baselines der übrigen Phasen.** Heute selbst gemessen und damit Fakt:
   `phase12_data_foundation` **123**, `phase10_v3` **160** (beide grün, 2026-08-18). Alle
   anderen Zählstände in diesem Repo stammen aus Vordokumenten und sind **ungeprüft** —
   A0.2 misst sie neu.
9. **`scheduler/run.py`-Flag-Liste** vor dem Anbau greppen (bestätigt vorhanden: 13
   `add_argument`-Aufrufe, u. a. `--enable-shadow-schedule`, `--enable-divergence-sampler`,
   `--no-bar-service`, `--no-measurement-heartbeat`).
10. **Aktueller Registry-Stand** vor Block A frisch lesen, nicht aus diesem Plan übernehmen.
    Stand 2026-08-18: 8 `active` (5 × `ok`, 3 × `no_intraday_source`), 14 `verified` mit
    `unverified`, 0 `quarantined`.
11. **`bars.sqlite`-Größe** vor dem `ALTER TABLE`: heute 6504 Zeilen / 1,5 MB — ein ALTER
    darauf ist Millisekunden. Bei deutlich gewachsener Datei vorher Kopie ziehen.
12. **`live_data`-Paketname frei?** `pip list | grep live` vor dem `pyproject.toml`.
13. **Ob der `universe_refresher`-Slot der richtige Ort für `resync_epics` ist** — er läuft
    heute in `preflight` und periodisch (`runner.py:285`, `:517-522`). Passt vom Takt, ist
    aber nicht live erprobt.
14. **Die reale Basis je Epic** (A6.0): wie groß ist der dauerhafte Abstand IG-CFD ↔ yF-Kassa
    tatsächlich, pro Instrument? Heute unbekannt — 0 `quote_divergence`-Events beweisen nur,
    dass sie unter 0,5 % liegt, nicht wie weit darunter. Block A misst sie; erst danach ist
    eine Rendite-Schwelle seriös zu wählen. **Bis dahin keine Schwelle raten.**
15. **Die S3-Quelle selbst** (§6 C1) — zum Zeitpunkt dieses Plans **nicht entschieden**. Die
    Recherche vom 2026-08-18 ergab: keine kostenlose Quelle ist zugleich vollständig (IBEX 35
    und MIB eingeschlossen) *und* frisch *und* lizenzrechtlich unbedenklich. Die Wahl ist eine
    Nikinger-Entscheidung, kein Rechercheergebnis — sie steht bis Block C aus und blockiert
    Block A und B nicht. Marktlage + die vier geprüften Kandidaten: §6 C1.0.
16. **Capital.com-Abdeckung**, falls dieser Weg gewählt wird: liefert die Demo-API
    `resolution=MINUTE` für Germany 40 / France 40 / **Spain 35**, und wie weit zurück? Ein
    kostenloser Operator-Lauf entscheidet das. Bis dahin ist jede Aussage über Capital.com
    in diesem Plan **unbestätigt**.
17. **Ob BME ein freies verzögertes MiFID-II-Datenprodukt für den spanischen Markt
    veröffentlicht**, wie Euronext es tut. Unbestätigt, Tendenz negativ — aber der wertvollste
    verbleibende Unbekannte, weil IBEX 2 von 5 messbaren Epics stellt und von keiner geprüften
    Gratisquelle außer Dukascopy abgedeckt wird.
18. **`claude-minimax` (A0.0), drei Punkte — alle nur live entscheidbar:**
    a. **Die exakte Basis-URL.** Quellen nennen sowohl `https://api.minimax.io/anthropic` als
       auch `.../anthropic/v1`; Claude Code hängt seinen eigenen Pfad an, also produziert genau
       eine der beiden ein doppeltes `/v1`. Symptom bei falscher Wahl: 404 auf **jede** Anfrage,
       nicht nur auf manche.
    b. **Bearer oder `x-api-key`** — `ANTHROPIC_AUTH_TOKEN` vs. `ANTHROPIC_API_KEY`. Der Wrapper
       setzt Bearer; schlägt die Auth mit 401 fehl, ist das der erste Tausch, den man probiert.
    c. **Die genaue Modell-ID des M3-Tarifs** (`MiniMax-M3` ist die dokumentierte Schreibweise,
       im Tarif des Nikinger aber nicht überprüft).
19. **Ob die LS-Kerze überhaupt ein Volumen trägt** (L17): `CHART:`-Feldliste kennt `LTV`
    (last traded volume) und `TTV` (total traded volume), aber bei einem CFD auf einen Index
    kann beides strukturell 0 oder leer sein. Teil des B0-Live-Checks — **einfach mit
    abfragen**, es kostet nichts extra. Ergebnis entscheidet, ob die `prefer`-Verdrängung aus
    §8 real wird oder nur theoretisch ist. Falls sie real wird und Volumen je gebraucht wird:
    die Antwort ist **nicht**, `prefer` umzustellen (das würde den Preis verschlechtern, um
    eine Begleitgröße zu retten), sondern eine quellenübergreifende Lesung —
    `BarArchive.window(..., sources=("yf",))` liefert die yF-Zeile weiterhin gezielt (L10).

---

## §10 Explizit NICHT in Phase 13

- **WI-2/W2-Auswertung** und die H-Serie — Phase-11-Wiederaufnahme nach bestandener
  Beweiswoche. Phase 13 baut das Instrument, sie liest es nicht ab.
- **Research-Funnel-Fix** (0-Kandidaten-Problem, W1/W5) — eigenes Thema, bewusst über den
  Shadow-Schedule entkoppelt.
- **Der Research-Seam `BarService.get_bars`** — L15, erst nach Block B neu messen.
- **`resolve_paper_trade` selbst** — die reine Funktion bleibt unangetastet; der Guard sitzt
  davor.
- **Momentum-VETO, Gates, Sizing, P6, P7** — L13.
- **B3 Margin-Headroom**, Council-Paper-Call-Aktivierung, UI, Live-Konto,
  `lesson_embeddings`, neue bezahlte Provider über das C1-Budget hinaus.
- **Lightstreamer für Live-Quotes im Research-Kontext** (P9 Step 7b) — bleibt geparkt;
  S1 hier ist Archiv-Mitschrieb, ein anderer Zweck.
- **Ein Revert der fünf P12.5-Fixes** — L14.

---

## §11 Drop-Order & Risiken

**Drop-Order bei Zeit-/Budgetdruck (zuerst weglassen):** C2 (`GapRescue`, ohnehin Default AUS)
→ C1 (S3-Fremdquelle) → C3 (`source_delta.py`) → B (LS) → **nie:** Block A. Block A allein
stoppt die Blutung und ist die Voraussetzung für jeden sicheren Neustart.

**Risiken:**
- **CHART nicht verfügbar** (§9.2) ⇒ Tick-Aggregation, schlechtere High/Low-Treue. Gemindert
  durch `tick_count` + getrennte Ausweisung; **nicht** wegdefiniert.
- **LS stirbt mit dem Bot** (L5) ⇒ Lücken in Bot-aus-Zeiten. Gemindert durch S2 (läuft
  weiter) und S3/S4 (Backfill). Das ist der bewusst gezahlte Preis für „keine zweite
  IG-Session".
- **Zu strenge Abdeckungsschwellen** ⇒ wenige Auflösungen, Messung verhungert. Gemindert:
  Block A **misst** die reale Verteilung, bevor die Schwellen fixiert werden; beide sind
  benannte Knöpfe (§5.1), keine versteckten Konstanten.
- **SQLite-Nebenläufigkeit**: jetzt drei Schreiber auf `bars.sqlite` (Recorder-Prozess,
  Scheduler-BarService, LS-Callback-Thread im selben Prozess). Kurze Transaktionen,
  `INSERT OR IGNORE`; bei beobachtetem `database is locked` ⇒ `busy_timeout` setzen
  (erlaubt, kein Redesign). ⚠ **Neu gegenüber Phase 12:** der LS-Callback läuft in einem
  SDK-Thread — `BarArchive`s `sqlite3.Connection` ist nicht threadsicher. Entweder eine
  eigene Connection im Recorder-Thread oder `check_same_thread=False` + Lock. **In B2
  entscheiden und im Session-Block begründen.**
- **Ein vierter `source`-Wert** (C1) berührt `KNOWN_SOURCES`, `prefer` und jeden Report.
  §8 hat die stille Variante als eigene Zeile.
