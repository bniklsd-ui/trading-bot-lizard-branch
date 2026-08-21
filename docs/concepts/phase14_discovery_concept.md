---
status: concept
purpose: Concept-Skizze für Phase 14 (Discovery-Then-Deterministic) — die Architektur, die Block C abschließt als "Quellen sind nicht hardcoded, sondern dynamisch + kreuzreferenziert". Vollständiger execution-ready Plan folgt in einer eigenen Planungssession; hier nur das Bild, das die Phase rechtfertigt und die Block-C-Trennung trägt.
read-when: Phase 14 vorbereitet wird; jede Session, die `EPIC_MAP` oder eine neue Quelle anfasst, liest erst dieses Concept
detail: L3
up: ../../phase13_live_data/CLAUDE.md
down:
  - ./phase13_c_block_c_replan.md                                       # 📕 Block-C-Closure, der Phase 14 lostritt
  - ./phase13_live_data_plan.md                                         # 📕 Phase-13-Hauptplan (L1–L16, Blöcke A/B/C, Decision-Wurzeln)
  - ./phase12_data_foundation_plan.md                                   # 📕 Phase-12-Plan (data_foundation/Schicht, die Phase 14 erweitert)
  - ../../phase12_data_foundation/PHASE12_5_CLOSEOUT_HANDOVER.md        # 📕 Warum "nicht im Konsumentenpfad kaufen" — die Lehre hinter Phase 14
updated: 2026-08-22
---

# Phase 14 — Discovery-Then-Deterministic (Concept-Skizze, 2026-08-22)

> **Wichtig:** Das hier ist **kein** execution-ready Plan. Es ist die Concept-Skizze, die
> Nikinger 2026-08-22 aus dem Architektur-Insight der Session 13 als „rechtfertigt eine
> eigene Phase" klassifiziert hat. Der vollständige Plan (Decisions D1–D?, Steps 0–?,
> Drift-Liste, Akzeptanz) wird in einer eigenen Planungssession geschrieben, sobald die
> Beweiswoche genug Zahlen für die Quell-Auswahl liefert.
>
> **Autor:** Claude Code, Planungssession 2026-08-22. **Adressat:** die nächste
> Planungssession, die den execution-ready Plan schreibt.

---

## §0 BLUF

**Heute**: Jede neue Quelle braucht einen Code-Deploy. Capital.com hat ein hardcoded
`EPIC_MAP = {"IX.D.DAX.IFMM.IP": "DE40", "IX.D.CAC.IFE.IP": "FR40"}` in
`live_data/backfill.py:67-72` — für jedes weitere Symbol muss jemand von Hand nachpflegen
(typische Drift-Quelle, vgl. P12.5-Folgekosten).

**Phase 14**: Jede Quelle **exponiert selbst**, was sie liefern kann
(Epics × Auflösung × Historientiefe × Frische). Eine DB-Tabelle hält die Kreuzung. Die
Konsumenten lesen die Tabelle, nicht den Code. Hinzufügen einer Quelle = DB-Eintrag + eine
`Source.discover()`-Methode, **kein** Konsumenten-Refactor.

**Dadurch absorbiert** Phase 14 implizit zwei Block-C-Altlasten:
- **Path C Dukascopy** (für SP35/IBEX): nach der Architektur nur eine Quell-Registry-Zeile.
- **Hardcoded `EPIC_MAP`**: verschwindet, sobald `run_capital_backfill` die Tabelle liest.

V4 (Council, Handover, Reward-Reform, Force-Trigger, Instinct-ECC) rutscht entsprechend
auf Phase 15.

---

## §1 Mission

> **„Was eine Quelle kann, sagt die Quelle — nicht der Konsument."**

Ein Konsument, der Daten für Epic X braucht, fragt das Archiv (oder die
Discovery-Tabelle): „welche Quellen können das?". Das ersetzt jede hartcodierte Annahme
„Capital.com liefert DE40+FR40" durch eine dynamische, vom Anbieter selbst gepflegte
Tatsache.

Drei Sätze, die die Phase tragen:

1. **Discovery first.** Jede Quelle hat eine `discover() -> SourceProfile`-Methode, die ihr
   eigenes Liefer-Spektrum preisgibt.
2. **Kreuzung second.** Ein Konsument sieht nicht „alle Quellen", sondern „für Epic X die
   Untermenge, die liefern kann".
3. **Determinism last.** Erst danach läuft der Backfill / Resolve / Lookup — der Code wird
   einfacher, nicht komplizierter, weil die Auswahl bereits getroffen ist.

---

## §2 Drei Bausteine (aus Session 13 Architektur-Insight)

### §2.1 Quell-Profil

Eine Schnittstelle, die jede Quelle implementiert:

```python
# Pseudocode, KEIN fertiger Code
@dataclass(frozen=True)
class SourceProfile:
    source: str                       # "ig", "yf", "ls", "capital", …
    available_epics: set[str]         # {"IX.D.DAX.IFMM.IP", "IX.D.CAC.IFE.IP", …}
    resolutions: set[str]             # {"1m", "5m", "1h", "1d"}
    history_min_days: int             # Capital.com 30, yF 7, IG /prices 30+, …
    latency_min: int                  # IG-LS echtzeit, yF 15, Capital.com 1, …
    last_verified_utc: str            # wann wurde discover() zuletzt aufgerufen
    notes: str | None                 # z. B. ToS-Hinweis (Dukascopy)

class Source:
    def name(self) -> str: ...
    def discover(self) -> SourceProfile: ...   # kann Aufruf sein (IG-search_markets, Capital.com /markets)
                                                # oder gecachte Methode, die ein Profil aus der DB liest
    def fetch_window(self, epic, start, end, resolution) -> list[Bar]: ...
```

**Heute vs. Phase 14:**

| Heute | Phase 14 |
|---|---|
| `CapitalSource` (in `backfill.py`) kennt nur DE40/FR40 (hardcoded `EPIC_MAP`). | `CapitalSource.discover()` ruft `GET /markets?searchTerm=` und baut das Profil dynamisch. |
| `yFinance` hat `TickerMapper` in Phase 3 — Mapping IG → yFinance-Symbol steht im Code. | `yFinanceSource.discover()` würde die Mapping-Logik in ein Profil gießen, **nicht** aber den Mapper abschaffen (das ist ein Research-Layer-Detail, nicht Quell-Profil). |
| IG-Adapter hat `search_markets()` (Phase 9). | `IGSource.discover()` würde ihn aufrufen und die IG-Tradeable-Epics ins Profil schreiben. |

### §2.2 Kreuzungs-Tabelle

```sql
-- Phase-2-Migration 007 (Nummer heute noch zu vergeben, siehe Drift-Liste)
CREATE TABLE instrument_source_availability (
    epic                TEXT NOT NULL,
    source              TEXT NOT NULL,
    resolution          TEXT NOT NULL,
    history_min_days    INTEGER NOT NULL,
    latency_min         INTEGER NOT NULL,
    last_verified_utc   TEXT NOT NULL,
    notes               TEXT,
    PRIMARY KEY (epic, source, resolution),
    FOREIGN KEY (epic) REFERENCES instrument_universe(epic)  -- die Phase-9-Tabelle
);
```

**Drei Schreib-Pfade:**

1. **Initial-Discovery nach Phase-14-Build:** einmaliger Lauf, der für alle `active`-Epics
   aus `instrument_universe` jedes registrierte `Source.discover()` ruft und die Tabelle füllt.
2. **Periodisch (z. B. wöchentlich):** Re-Discovery, damit `last_verified_utc` aktuell
   bleibt. Quellen können verschwinden (ToS-Änderung), neue Symbole kommen dazu.
3. **Operator-Override:** manueller Eintrag, wenn eine Quelle für eine bestimmte Epic
   entdeckt wurde, aber die automatische Discovery sie nicht findet (z. B. yF-Edge-Cases).

### §2.3 Konsumenten-Umstellung

Drei Konsumenten, die heute hardcoded sind und morgen die Tabelle lesen:

| Konsument | Heute | Phase 14 |
|---|---|---|
| `run_capital_backfill` | liest `EPIC_MAP` | liest `instrument_source_availability` für `source='capital'` |
| `BarArchive.window` (mit `prefer=`) | Rangfolge im Code | entweder a) `prefer` entfällt zugunsten der Tabellenauswahl, oder b) `prefer` wird zum reinen Tie-Breaker |
| Beweiswoche-Coverage-Report (`source_delta.py` P6) | listet Quellen starr | liest die Tabelle, kann „diese Quelle kann das prinzipiell nicht" sauber ausweisen |

**Was Phase 14 NICHT anfasst:**
- `resolve_paper_trade` (unverändert, der Guard sitzt davor)
- Momentum-VETO, Gates, Sizing, P6-Debatte, P7-Brain (Phase-13-L13, gilt weiter)
- Der eigentliche `fetch_window`-Code pro Quelle (bleibt deterministisch, semantisch
  unverändert)

---

## §3 Was Phase 14 leistet (Outcome)

| Outcome | Wie belegt |
|---|---|
| **Eine neue Quelle hinzufügen ist eine Konfiguration, kein Deploy.** | Commit-Größe für „Dukascopy-Quelle anbinden" ≤ 50 Zeilen, kein Konsumenten-Touch. |
| **`run_capital_backfill` ohne `EPIC_MAP`.** | `grep -n "EPIC_MAP" phase13_live_data/` ist **leer**. |
| **Coverage-Metrik pro Quelle-Epic-Paar aus der Tabelle, nicht aus `prefer`-Rangfolge.** | `source_delta.py` P6 zeigt „war prinzipiell nicht abrufbar" getrennt von „war abrufbar und hat divergiert". |
| **Dukascopy-ToS-Klausel explizit dokumentiert, nicht im Code versteckt.** | `notes`-Spalte in der Tabelle hält den Vermerk; das `SourceProfile.notes`-Feld ist verpflichtend. |
| **Backfill-Lücken werden erklärbar.** | „Lücke von 09:00 bis 09:15 für IX.D.IBEX.FWM2.IP: keine Quelle in `instrument_source_availability` mit `latency_min ≤ 15` für `resolution='1m'`." — vorher war es „Lücke, warum auch immer". |

---

## §4 Was Phase 14 *nicht* macht (Scope-Disziplin)

- **Quell-Authentifizierung**: jede Quelle authentifiziert sich heute selbst (Phase-1-Muster
  mit Keyring-Namensräumen). Phase 14 fasst das **nicht** an — sie geht davon aus, dass die
  Quell-Instanzen ihre Credentials schon kennen.
- **Quell-Rate-Limits / Backoff / Retry**: bleibt in jeder `Source`-Klasse. Phase 14 macht
  keine **zentrale** Quell-Verwaltung; sie macht nur **Sichtbarkeit** des Liefer-Spektrums.
- **Quell-Ranking nach „Qualität"** (z. B. „IG vor yF weil Broker-Original"): explizit
  out-of-scope. Die Tabelle ist eine **Fakten**-Tabelle (was kann wer), keine
  **Präferenz**-Tabelle. Wenn zwei Quellen dasselbe können, entscheidet der Konsument
  deterministisch nach seiner eigenen Regel.
- **Migration bestehender Konsumenten-Caches** (z. B. yFinance `TickerMapper`-Cache):
  out-of-scope. Die Tabelle **parallel** zum Cache; eine spätere Phase räumt den Cache
  auf, sobald alle Konsumenten die Tabelle lesen.
- **V4 (Council, Handover, Reward-Reform, Force-Trigger, Instinct-ECC)**: Phase 15.

---

## §5 Beziehung zu Phase 13 (Block C) und Phase 15 (V4)

```
Phase 13 (Live-Datenfundament)         Phase 14 (Discovery)             Phase 15 (V4)
─────────────────────────────          ─────────────────────            ──────────────
Block A: Schnitt ✅                    Quell-Profile                    Council Skill
Block B: Live/LS ✅                    Kreuzungs-Tabelle                Bull/Bear-Handover
Block C: Backfill+Rescue+Reports ✅    Konsumenten lesen Tabelle        Reward-Reform
                                                                          Force-Trigger
                                                                          Instinct-ECC
```

Phase 14 ist **die** Brücke zwischen dem Datenfundament (Phase 13) und der AI-Sophistication
(Phase 15). V4 setzt voraus, dass die Daten-Infrastruktur **konfigurierbar** ist, nicht nur
**vorhanden**. Genau das liefert Phase 14.

---

## §6 Offene Fragen (für die Planungssession, nicht für jetzt)

| # | Frage | Wer entscheidet |
|---|---|---|
| Q1 | **Migrations-Nummer 007 — ist sie frei?** | Phase-14-Planning-Session (grep auf `phase2_persistence/migrations/`). |
| Q2 | **`Source.discover()`-Aufruf-Frequenz** (wöchentlich, täglich, on-demand)? | Nikinger (Kosten vs. Aktualität). |
| Q3 | **Bleibt `prefer` in `BarArchive.window`?** | Nikinger + Plan-Diskussion. Mein Vorschlag: `prefer` wird zum **Tie-Breaker** unter mehreren tabellentauglichen Quellen, nicht zur primären Auswahl. |
| Q4 | **Reihenfolge: Schema zuerst, oder erst eine Quell-Discovery-Mock, dann Schema?** | Planungssession. Mein Vorschlag: erst Mock (kann in der Plan-Session entstehen), dann Migration. |
| Q5 | **Wann genau wandert Dukascopy aus „deferred" auf „TODO"?** | Nach Phase 14 Schritt 1.0 (Tabelle steht) — dann ist Dukascopy eine Quell-Registry-Zeile, kein Phase-13-Code mehr. |
| Q6 | **Gehört die `instrument_universe`-Tabelle (Phase 9) erweitert, oder bleibt sie IG-only?** | Planungssession. Mein Vorschlag: bleiben — die Kreuzungs-Tabelle zeigt, **welche IG-Epics welche Quellen haben**, sie **erweitert** die IG-Liste nicht. |
| Q7 | **Cost-Model**: jede `discover()`-Methode kostet einen API-Call. Wann cachen wir Profile? | Planungssession. Vorschlag: TTL-basiert (z. B. 7 Tage), mit manueller Invalidierung. |

---

## §7 Was die Phase-14-Planungssession als erstes tut

Sie liest **diese Reihenfolge**, bevor sie eine Zeile Code anfasst:

1. **Block-C-Re-Plan** [`./phase13_c_block_c_replan.md`](./phase13_c_block_c_replan.md)
   — die Übergabe, die Warum-Frage.
2. **Phase-13-Hauptplan** [`./phase13_live_data_plan.md`](./phase13_live_data_plan.md) —
   L1–L16 (insb. L1/L2/L10/L11/L13/L17), §3 Architektur-Bild, §6 Block-C-Steps als
   Vor-Bild, §10 Out-of-Scope.
3. **Phase-12.5-Closeout** [`../../phase12_data_foundation/PHASE12_5_CLOSEOUT_HANDOVER.md`](../../phase12_data_foundation/PHASE12_5_CLOSEOUT_HANDOVER.md)
   — die Lehre hinter „nicht im Konsumentenpfad kaufen".
4. **Phase-13-Session-13-Block** (im `phase13_live_data/CLAUDE.md`-Kopf oder im Archive) —
   der genaue Wortlaut des Architektur-Insights.
5. **Live-DB-Stand** (`data/bars.sqlite`, `data/trading_bot.sqlite`, `mode=ro`) — was
   `instrument_source_availability` mit welchem Substrat füllen müsste.

Erst danach: `git pull` + Regression-Sweep + Schritt 0.0 (siehe Block-C-Re-Plan §5).

---

## §8 Concept-Stand, klar abgegrenzt vom execution-ready Plan

| Was dieses Concept **ist** | Was es **nicht** ist |
|---|---|
| Begründung der Phase (Nikinger-Einschätzung „recht umfangreich"). | L1–L?-Decisions, gelockt. |
| Drei Bausteine skizziert (Quell-Profil, Kreuzungs-Tabelle, Konsumenten-Umstellung). | Konkrete Funktions-/Typnamen mit Verbatim-Ankern. |
| Outcome-Tabelle, Scope-Disziplin-Tabelle, Verhältnis zu Phase 13 + 15. | Test-Liste, Akzeptanzkriterien, Drift-Liste, Fehlgriff-Tabelle. |
| Sieben offene Fragen, deren Antworten der Plan braucht. | Antworten. |

Die Planungssession füllt das alles aus, schreibt `docs/concepts/phase14_discovery_plan.md`,
bekommt Decisions gelockt, und committed den Plan — eine eigenständige Sitzung, nicht Teil
dieser hier.
