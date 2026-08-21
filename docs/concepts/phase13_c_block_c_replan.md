---
status: snapshot
purpose: Block-C-Re-Plan (Stand 2026-08-22) — Block C ist code-complete (C1 PARTIAL by design, C2/C3 ✅ + live-verifiziert); die "discovery-then-deterministic"-Architektur aus Session 13 wird in eine eigene Phase 14 ausgelagert. V4 rutscht auf Phase 15.
read-when: Block C abgeschlossen ist; Phase 14 vorbereitet wird; jede Session, die an Phase 14 oder 15 anfasst, liest erst diesen Re-Plan + das Phase-14-Concept
detail: L3
up: ../../phase13_live_data/CLAUDE.md
down:
  - ../../phase13_live_data/CLAUDE.md                                   # 🔄 Phase-13-Kopf
  - ../../phase13_live_data/SESSIONS_ARCHIVE.md                         # 📦 Session-13 (Bugfix + Architektur-Insight) liegt hier
  - ../../phase12_data_foundation/PHASE12_5_CLOSEOUT_HANDOVER.md        # 📕 Vorgänger-Closeout
  - ./phase13_live_data_plan.md                                        # 📕 alter Execution-ready Plan (Steps 0–8 + Blöcke A/B/C, bleibt Referenz)
  - ./phase14_discovery_concept.md                                     # 📕 Concept-Skizze für die neue Phase 14
updated: 2026-08-22
---

# Phase 13 — Block C: Re-Plan & Closeout (2026-08-22)

> **Autor:** Claude Code, Planungssession 2026-08-22. **Adressat:** die ausführende Session,
> die Phase 14 vorbereitet (Schritt-0-Reihenfolge, Drift-Check). Alles unten ist selbst
> gegen das Repo nachgemessen — außer, was explizit als Annahme gekennzeichnet ist.
>
> **Anlass:** Block C ist code-complete. Die "discovery-then-deterministic"-Architektur, die
> Session 13 als **Insight** festgehalten hat, ist nach Nikinger-Einschätzung umfangreich genug
> für eine eigene Phase. V4 rutscht entsprechend auf Phase 15. Dieser Re-Plan hält Block C
> sauber zu (statt ihn mit Phase 14 zu vermischen), definiert die Übergabe, und liefert das
> Phase-14-Concept (separater Snapshot, kein full plan).

---

## §0 BLUF

Block C (S3-Fremdquelle + S4-Rettung + Reports) ist **code-complete, live-verifiziert für den
funktionierenden Teil, und schließt hier**. Der einzige Missing-Index (Spain 35 / IBEX) bleibt
bewusst auf yF, weil die strukturelle Antwort — **Discovery-Then-Deterministic** — eine eigene
Phase 14 verdient. Path C Dukascopy ist nach der Architektur nur noch eine Konfiguration, kein
Code-Deployment mehr, und gehört in Phase 14 (nicht in Block C).

| Block-C-Step | Stand 2026-08-22 | Anmerkung |
|---|---|---|
| **C1** — S3-Fremdquelle | **PARTIAL by design** | Capital.com Pfad B: DE40 + FR40 ✅ live-verifiziert (962 Bars am 2026-08-22) · SP35 → 404 → Dukascopy-Pfad wartet auf Phase 14 |
| **C2** — S4 `GapRescue` | ✅ | 11 Tests · Default AUS · eigene `spend_kind='rescue'` (Ledger-eindeutig) |
| **C3** — `source_delta.py` | ✅ | 7 Tests · 962 Bars im Archiv als Live-Substrat bestätigt |
| **Test-Fix** | ✅ (`074d6c9`) | 5-Zeilen-Fix für `test_multiple_days_window`, heute nachgeholt |

**Vier Weichenstellungen dieses Re-Plans** (L1–L4):

| # | Entscheidung | Begründung |
|---|---|---|
| **L1** | **Block C ist final.** Code-Stand bleibt, keine weiteren C1-Pfade, keine Dukascopy-Code, keine Auto-Scheduler-Logik. | Alles, was noch als C-Code auf der Liste stand (Dukascopy, Auto-Gap-Fill, dynamische EPIC_MAP), fällt unter Phase 14. |
| **L2** | **"Discovery-Then-Deterministic" wird Phase 14, nicht Block-C-Erweiterung.** | Nikinger 2026-08-22: „recht umfangreich, eigene Phase recht". Eine Entdeckungs-Pipeline mit Quell-Profilen, Kreuzungs-Tabelle, DB-Schema (`instrument_source_availability` o. ä.), Konsumenten-Umstellung ist eine eigene Migrations-Linie — der Aufwand übersteigt die Scope-Disziplin eines Block-C-Closures. |
| **L3** | **V4 rutscht auf Phase 15.** | Nikinger-Entscheidung 2026-08-22, Präzedenzfälle 2026-08-01, 2026-08-11, 2026-08-18. Nummerierungs-Kaskade (Root-`CLAUDE.md`, `ROADMAP.md`, `docs/INDEX.md`) ist in **diesem** Commit ausgeführt; die ausführende Session findet sie vor. |
| **L4** | **Beweiswoche läuft weiter, P1–P9 bleiben gültig**, mit der Klarstellung dass `source_delta.py` jetzt 962 reale `source='capital'`-Bars als Substrat hat. | Block C hat die Werkzeuge geliefert; die Beweiswoche ist die operator-getriebene Validierung. P6 (Quellen-Delta-Report) ist mit Live-Substrat sofort sinnvoll. |

---

## §1 Was Block C geleistet hat — die drei Schritte einzeln

### §1.1 C1 — Capital.com Pfad B (PARTIAL, by design)

**Gebaut** (Session 11 + 12, Commits `b6a344f` … `369fb62` … `c8c39e6`):
- `phase13_live_data/live_data/backfill.py` — `CapitalSource` (authenticate + fetch_window)
  + `run_capital_backfill()`, vier quellenunabhängige Regeln aus Plan §6 C1.0 (Window-Check,
  keine synthetischen Bars, Backoff-Pflicht, später Rendite-Vergleich statt Niveau-Vergleich).
- `phase13_live_data/scripts/capital_backfill.py` — Operator-invokable mit `--epics` /
  `--auto` × `[--start, --end]` (UTC), Keyring-Service `trading-bot-capital`.
- `KNOWN_SOURCES` (`models.py:22`) erweitert um `SOURCE_CAPITAL`; `prefer`-Default in
  `archive.py:144` jetzt `('ig', 'capital', 'ls', 'yf')` — Capital.com rangiert vor
  LS/yFinance, weil Broker-CFD-Reihe näher an IG ist als Kassaindex.
- 11 Tests in `phase13_live_data/tests/test_backfill.py` (gemockt, kein Netz).

**Live-Verified 2026-08-22** (Commit `f8134ca` ist die Session-13-Doku; die Verifikation
stammt aus dem Nikinger-Operator-Run danach):
- 962 Bars geschrieben (481 DAX + 481 CAC) · exakt der Session-13-Erwartungsspanne
  (`~480/Epic`, `~960` total).
- `data/bars.sqlite`-Probe (`mode=ro`): `SELECT source, COUNT(*) FROM bars GROUP BY source`
  → `('capital', 962)`, `('ig', 2230)`, `('yf', 11654)`.

**Was NICHT in C1 gebaut wurde — und warum das richtig ist:**

| Item | Warum raus aus C1 |
|---|---|
| **Spain 35 (IBEX) via Dukascopy** (Plan §6 C1 Pfad C) | ToS-Klausel „may not be used to construct a database of any kind"; Nikinger-Auslegung erlaubt es für den privaten Single-User-Store, aber das ist keine Code-Deploy-Entscheidung, sondern eine Architektur-Entscheidung. **Gehört in Phase 14** (Discovery-Architektur macht aus dem Quell-Anbinden eine Konfigurations-Zeile). |
| **Hardcoded `EPIC_MAP = {"IX.D.DAX.IFMM.IP": "DE40", "IX.D.CAC.IFE.IP": "FR40"}`** in `backfill.py:67-72` | Session-13-Architektur-Insight: genau die Stelle, an der Plan/Code-Drift entsteht. **Gehört in Phase 14** (dynamische Discovery). |
| **Auto-Gap-Fill-Scheduler** (Cron-Logik, tägliche Lücken ≥ 60 min schließen) | Operator-getrieben für jetzt; eine Automatisierung gehört in Phase 14 als Folge-Schritt nach der Discovery-Tabelle. |

### §1.2 C2 — `GapRescue` (S4-Rettung, Default AUS)

**Gebaut** (Session 9, Commit `fd6755f`): `phase13_live_data/live_data/rescue.py` (~190 Zeilen).
- Direkter IG-REST-Call (Bereichs-API `from`/`to`) am Chain-Provider vorbei.
- Gedrosselt: `max_calls_per_epic_per_day=1`, `min_gap_age_min=60`, `max_points_per_call=60`.
- Stale-Assertion am Kaufort (L8 wiederverwendet, vierte unabhängige Stale-Konstante
  *bewusst* vermieden — `GapRescue` nutzt `BudgetedIGBarProvider.stale_tolerance_min`).
- Eigener `spend_kind='rescue'` — Ledger-Eintrag auffindbar (Failure-Handover §5.1 war der
  Anlass: geteilter Provider taggte Tracker-Top-ups fälschlich als `research`).
- `RescueReport` mit `skipped_reason` immer zurück (kein `None`, nie raise).
- 11 Tests in `phase13_live_data/tests/test_rescue.py` (gemockt).

**Was NICHT in C2 gebaut wurde:** das **Anschalten** (`enable_gap_rescue=True` in der
Scheduler-Config). Das ist Operator-Step, nicht Bauschritt — und gehört zur Beweiswoche.

### §1.3 C3 — `scripts/source_delta.py` (P6 PASS-Kriterium)

**Gebaut** (Session 9, Commit `50a417e`): `phase13_live_data/scripts/source_delta.py` (~253
Zeilen).
- Read-only Diagnostic (`mode=ro` gegen `trading_bot.sqlite` + `bars.sqlite`).
- Löst jeden resolved Trade je Quelle (`yf`, `ls`, `capital`) getrennt auf, weist die
  Differenz aus (P6 = „Anteil der Zeilen, bei denen die Quelle das Ergebnis dreht").
- CLI: `--day` oder `--days N` (mutually exclusive), `--quiet`.
- Exit-Codes: 0 OK (auch bei Divergenz — Divergenz ist Daten, kein Fehler), 1 READ ERROR.
- 7 Tests in `phase13_live_data/tests/test_source_delta.py` (eine war pre-existing
  date-drift, Fix in Commit `074d6c9`).

**Live-Substrat**: der capital_backfill-Lauf hat `bars.source='capital'` erstmals in relevanter
Menge ins Archiv gebracht — `source_delta.py` kann ab sofort `--sources capital` (oder den
Default) sinnvoll vergleichen.

---

## §2 Warum Block C jetzt schließt (drei strukturelle Gründe)

1. **C1 ist PARTIAL, und die Lücke ist architektonisch**, nicht mechanisch. Spain 35 fehlt,
   weil Capital.com es nicht liefert. Dukascopy würde es liefern, aber ToS + die
   hardcoded-EPIC_MAP-Architektur machen aus dem Schließen eine Code-Migration. Diese
   Architektur-Frage ist **Phase 14**, nicht „ein weiterer Backfill-Pfad".
2. **Der "Discovery"-Insight ist keine Schnittstellen-Erweiterung** — er ist ein
   **Schema-Bruch**. Heute: `EPIC_MAP` lebt im Code, jedes neue Symbol ist ein PR. Nach
   Phase 14: `instrument_source_availability` in der DB, jedes neue Symbol ist eine Zeile.
   Der Migrations-Pfad ist: Tabelle anlegen, Backfill einmalig laufen lassen (kann er selbst),
   Konsumenten umstellen, EPIC_MAP entfernen. Das ist drei Commits über mindestens zwei
   Sessions — keine Sache für einen Block-C-Closure.
3. **Beweiswoche ist die nächste Pflicht**, nicht weitere Quellen. P1–P9 sind die Akzeptanz;
   ihre Belege hängen an `data_health.py` (täglich) und `source_delta.py` (wochenweise).
   Erst wenn diese Zahlen vorliegen, lässt sich seriös entscheiden, ob S3 (Fremdquelle) den
   Aufwand wert ist, und wenn ja, welche. Genau diese Messen-vor-Entscheiden-Reihenfolge
   ist die Lehre aus P12.5 (Failure-Handover §3: „drei Datenwochen an drei Infrastruktur-
   Ausfällen gescheitert").

---

## §3 Was Phase 14 leisten wird (Concept-Skizze, nicht der Plan)

> Die **vollständige** Skizze (L1–L?, Steps 0–?, Drift-Liste, Akzeptanz) liegt in
> [`./phase14_discovery_concept.md`](./phase14_discovery_concept.md). Hier nur das Bild, das
> den Block-C-Closure rechtfertigt.

**Mission:** jede Quelle (IG, yFinance, LS, Capital.com, später Dukascopy) **exponiert
selbst**, was sie liefern kann (Epics, Historientiefe, Auflösung, Frische). Konsumenten
fragen das Archiv nach „was kann für Epic X?", nicht „kann diese Quelle das?". Das hardcoded
`EPIC_MAP` verschwindet.

**Drei Bausteine** (aus Session 13, Architektur-Insight):

1. **Discovery-Schritt pro Quelle** — z. B. Capital.com `GET /markets?searchTerm=`,
   IG `search_markets()`, yFinance `Ticker()`. Output: ein Quell-Profil je Quelle.
2. **Kreuzungs-Tabelle** in der DB (`instrument_source_availability` o. ä., Phase-2-Migration).
   Jede IG-Tradeable-Epic × {welche Quellen liefern was für sie}. Wird aus den
   Quell-Profilen abgeleitet, **nicht** von Hand gepflegt.
3. **Konsumenten-Umstellung**: `run_capital_backfill` liest die Tabelle, nicht `EPIC_MAP`.
   `BarArchive.window(sources=…)` wird quellenbewusst statt rang-bewusst. `prefer` wird
   entweder abgeschafft (die Tabelle weiß, was sie will) oder zum reinen Tie-Breaker.

**Was Phase 14 mit Path C Dukascopy macht:** nach der Architektur ist
`dukascopy.Source()` ein Hinzufügen in der Quell-Registry — kein neuer Backfill-Code, keine
neuen Tests im Kernpfad, nur eine Discovery-Config und ein Konsument, der die Tabelle liest.
**Damit absorbiert Phase 14 implizit Path C**, ohne dass Dukascopy-Code in Phase 13 gebaut
werden muss.

---

## §4 Akzeptanz Block C (heute, 2026-08-22)

| # | Kriterium | Beleg |
|---|---|---|
| **B1** | Capital.com Pfad B ist **live production-ready** für DE40 + FR40. | Nikinger-Operator-Lauf 2026-08-22: 962 Bars im Archiv (`data/bars.sqlite`, `mode=ro`-Probe), `bars_written_total: 962` exakt im Erwartungsbereich. |
| **B2** | S4 `GapRescue` existiert, ist getestet, ist **Default AUS**. | `live_data/rescue.py` vorhanden, 11 Tests grün, kein Scheduler-Config-Eintrag der es anschaltet. |
| **B3** | `source_delta.py` ist P6-Werkzeug und hat ein **reales Substrat** (962 `source='capital'`-Bars). | Archiv-Probe zeigt 962 Capital-Zeilen. |
| **B4** | Keine uncommitteten Änderungen, keine roten Tests. | Working tree clean, alle 13 Phasen + root-Tests grün (1508 passed, Commit `074d6c9`). |
| **B5** | Die einzige offene Stelle (`test_multiple_days_window`) ist gefixt. | Commit `074d6c9`, 50 phase13-Tests grün. |

**B1 + B5 = Block C done** in dem Sinne, den der Plan in §6 C4 vorgegeben hat. Was bleibt
ist operator-getrieben (Beweiswoche) und architektur-getrieben (Phase 14).

---

## §5 Schritt-Sequenz für die Phase-14-Vorbereitungs-Session

> Diese Sequenz gehört **nicht mehr in den Block-C-Plan**. Sie steht hier nur, damit die
> Phase-14-Planning-Session einen sauberen Einstieg hat.

| Schritt | Datei / Aktion | Akzeptanz |
|---|---|---|
| **0.0** | `git pull` + `ps aux \| grep scheduler.run` (Gegenprobe) + Regression-Sweep (Block-A0.2-Muster). | Working tree sauber, alle Suiten grün. |
| **0.1** | Concept-Snapshot komplett lesen: [`phase14_discovery_concept.md`](./phase14_discovery_concept.md) (L1–L?, Drift, Akzeptanz). | Fragen gesammelt, mit Nikinger gebündelt geklärt. |
| **0.2** | Quell-Profil-Schema skizzieren: `instrument_source_availability(epic, source, resolution, history_min, latency_min, last_verified_utc)`. | Eine Tabelle, eine Column-Liste; mit Phase-2-Migrations-Nummer abgeglichen (heute max 006). |
| **1.0** | `docs/concepts/phase14_discovery_plan.md` schreiben — Decisions D1–D?, Steps 0–?, Drift-Liste, Akzeptanz. | Plan committed. |
| **1.1** | `phase10_v3`/`phase13_live_data`/`phase12_data_foundation` Cross-Phase-Edit-Freigabe (Nikinger) **vor** jedem Code-Schritt einholen. | Cross-Phase-Touches in der Plan-Tabelle markiert. |

`docs/INDEX.md` und `ROADMAP.md` sind bereits in **diesem** Commit aktualisiert (Phase 14
neu, V4 → Phase 15) — die Phase-14-Planning-Session findet das vor.

---

## §6 Drift-Liste (was die Phase-14-Planning-Session selbst nachmessen muss)

> Was hier **nicht** steht, hat die Block-C-Planungssession 2026-08-22 selbst gegen das Repo
> verifiziert und ist als Fakt formuliert. Alles, was Phase 14 berührt, liegt im Concept
> (Drift-Liste dort).

1. **Aktueller Stand `EPIC_MAP`** in `live_data/backfill.py` — heute ein Dict mit 2 Keys;
   Annahme: stabil, weil Session 12 abgeschlossen und seitdem keine Edits an der Datei.
   Vorhandene Tests pinnen das fest.
2. **Capital.com URL-Wechsel** (Demo-URL `demo-api-capital.backend-capital.com`) — heute
   stabil; Phase 14 muss vor jeder Quell-Anbindung die aktuelle URL gegen das Swagger-File
   verifizieren.
3. **`models.py:22` `KNOWN_SOURCES`** heute `{SOURCE_IG, SOURCE_YF, SOURCE_LS, SOURCE_CAPITAL}`
   — vier Strings, alphabetisch nicht relevant, aber als frozenset im `__init__.py`
   durchsuchbar. Phase 14 fügt **keine** Quelle via Code-Edit hinzu, sondern via DB-Eintrag;
   das ist der ganze Sinn der Architektur.
4. **Migrations-Nummerierung** in `phase2_persistence/migrations/`: heute `001…006`. Phase 14
   braucht vermutlich `007` für `instrument_source_availability`. Vor dem ersten Edit
   greppen.
5. **`source_spend`-Ledger-Verträglichkeit**: heute führt `GapRescue` einen eigenen
   `spend_kind='rescue'`, der Ledger ist eindeutig. Phase 14 darf das nicht still ändern.

---

## §7 Was Phase 13 *nicht* macht (unverändert, hier nur zur Bestätigung)

Reproduziert aus dem Hauptplan `phase13_live_data_plan.md` §10, weil der Block-C-Stand
diese Liste beerbt:

- **WI-2/W2-Auswertung + H-Serie** — Phase-11-Wiederaufnahme nach bestandener Beweiswoche.
- **Research-Funnel-Fix** (0-Kandidaten) — eigenes Thema, entkoppelt über Shadow-Schedule.
- **`BarService.get_bars`-Research-Seam** — L15 (Hauptplan), erst nach Block B neu messen.
- **`resolve_paper_trade`** — unangetastet, der Guard sitzt davor.
- **Momentum-VETO, Gates, Sizing, P6, P7** — L13 (Hauptplan).
- **B3 Margin-Headroom, Council-Paper-Call-Aktivierung, UI, Live-Konto, `lesson_embeddings`** —
  Phase 14+ / Phase 15, nicht Block C.
- **Ein Revert der fünf P12.5-Fixes** — L14 (Hauptplan).
