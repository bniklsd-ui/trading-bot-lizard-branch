# CLAUDE.md — Phase 14: Discovery-Then-Deterministic (`phase14_discovery/`)

> Zwei Phasen lang war „welche Quelle kann Epic X?" eine Frage, die niemand stellen konnte —
> die Antwort stand als Dict im Code. Phase 14 macht sie zu einer Zeile in der DB.
> **Quelle der Wahrheit ist der Plan + der Code, nicht dieses Dokument.**
> Vollständiger Plan: [`../docs/concepts/phase14_discovery_plan.md`](../docs/concepts/phase14_discovery_plan.md).
> Vorgeschichte: [`../phase13_live_data/PHASE13_CLOSEOUT_HANDOVER.md`](../phase13_live_data/PHASE13_CLOSEOUT_HANDOVER.md) §1.5.

## Mission (zuerst lesen)

**Was eine Quelle kann, sagt die Quelle — nicht der Konsument.**

1. **Discovery first.** Jede Quelle exponiert ihr Liefer-Spektrum als `SourceProfile`.
2. **Kreuzung second.** `instrument_source_availability` (Migration 007) hält
   IG-Epic × Quelle × Auflösung — inklusive des **quelleneigenen Symbols**.
3. **Determinism last.** Der Konsument liest die Tabelle und wird dadurch *einfacher*.

**Done-Kriterium:** PASS A1–A8 (Plan §7). Die zwei harten davon:
`grep -rn "EPIC_MAP" phase13_live_data/ --include=*.py` ist **leer**, und Discovery gibt
**strukturell** null IG-Punkte aus (Test mit einem Broker, der bei jedem Call wirft).

## Bauprinzip

„So wenig AI wie möglich, so viel AI wie nötig." **Phase 14 fügt NULL neues AI hinzu.**
Quell-Entdeckung, Symbol-Zuordnung, Verfügbarkeits-Bewertung und Scharfschalt-Logik sind
deterministischer Code. Wer hier ein LLM „Quellen bewerten" oder „Symbole raten" lassen
will → **stop**, das ist Code.

## Scope

- **DRIN:** `source_registry/` (Modelle, Store, Quell-Profile, Scharf-Flag, Daemon),
  Migration 007, die Projektions-Naht in `phase9_universe/universe/store.py::set_symbol`,
  der `stale_source`-Vokabular-Fix in `phase9_universe/universe/models.py`, der
  Symbol-Lookup statt `EPIC_MAP` in `phase13_live_data/live_data/backfill.py`, die
  Drei-Fälle-Trennung in `scripts/source_delta.py`, das Scharfschalten in
  `phase8_scheduler/webui/`.
- **DRAUSSEN:** `measurable_universe()` / `data_source_status` umbauen (D3), `prefer` in
  `BarArchive.window` (D7), Dukascopy (D15), `KNOWN_SOURCES` dynamisch (D17), zentrale
  Quell-Verwaltung (Auth/Rate-Limits bleiben je Quelle), `TickerMapper`-Cache,
  Momentum-VETO/Gates/Sizing/P6/P7, `resolve_paper_trade`, die Phase-13-Beweiswoche
  (separater Track, läuft parallel).

## Rahmen

- **Werktags-Arbeit erlaubt, auch bot-berührend.** Vorher den Bot stoppen,
  `ps aux | grep scheduler.run` als Gegenprobe (Parallel-Login-Falle).
- **Live-/Netz-/kostenpflichtige Läufe macht der Nikinger.** Befehl vorbereiten, Kosten
  nennen, vorher fragen. In Phase 14 sind das genau zwei: die Capital.com-`/markets`-Probe
  (B1a, Demo, kostenlos) und die Migration 007 gegen die Produktions-DB (mit Backup).
- **Live-DB nur `mode=ro`.**
- **Cross-Phase-Edits sind für Phase 14 freigegeben** (Nikinger 2026-08-22) für **Phase 2**
  (Migration), **Phase 8** (`webui/`, `run_scheduler.sh`), **Phase 9** (`models.py`,
  `store.py`), **Phase 12** (`budget.py`-Nutzung) und **Phase 13** (`backfill.py`,
  `scripts/`). Ein Touch **außerhalb** dieser Liste ist erneut freigabepflichtig.
- **Ausführungs-Sessions laufen über `claude-minimax`** (Kostengrund, Nikinger 2026-08-18),
  Debugging über `claude`. Ändert **nicht**, welches Modell der Bot selbst ruft.

## Der Kontingent-Deckel (dreifach, Plan §4 D6/D13/D14)

Die Frage „wie verhindern wir, dass Discovery das Kontingent sprengt" ist mit drei Lagen
beantwortet, von wichtig nach unterstützend:

1. **Strukturell.** Discovery ruft **nie** `/prices` und **nie** `search_markets`. Die
   IG-Zeile wird aus `instrument_universe` **abgeleitet** — jede Zeile dort *ist* per
   Definition eine IG-Epic. Der Beweis ist ein Test mit einem Broker-Fake, dessen jede
   Methode wirft (Muster L12 / `test_get_window_never_fetches`), **kein** Zählwert.
2. **Zwei Kontingente, nicht eins.** Das 10 000-Punkte-Kontingent (`/prices`, rollierende
   7 Tage) hat Phase 11 gesprengt; das API-Key-Kontingent (~30 req/min, 403
   `exceeded-api-key-allowance`) hat Phase 9 gesprengt (`discovery.py:183-189`, Pacing
   1,0 s → 2,5 s). Discovery berührt **keins von beiden**, weil sie IG gar nicht ruft.
3. **Deckel für alles, was doch fetcht** — heute nur Capital.com (Demo, kostenlos):
   `max_probe_calls_per_source_per_run=8`, TTL `profile_ttl_days=7` gegen
   `last_verified_utc`, und jede Ausgabe gebucht als `spend_kind='discovery'` im
   existierenden `source_spend`-Ledger (Muster `GapRescue`s `'rescue'`). Sichtbar statt
   unsichtbar.

Dazu kommt der Betriebs-Deckel: der Daemon tut **nichts**, solange
`data/state/DISCOVERY_ARMED` fehlt (D10) — die sichere Richtung jeder Mehrdeutigkeit ist
**nicht scharf**. Unscharf kostet null.

## Modul-Tabelle

> Stand: **nichts gebaut.** Diese Tabelle wird in Block D gegen den As-Built-Stand gefüllt
> (Testzahlen aus dem finalen Sweep, nicht geschätzt).

| Datei | Zweck | Status |
|---|---|---|
| `source_registry/models.py` | `SourceAvailability`, `SourceProfile`, `Source`-Protocol, `origin`-Vokabular | ⬜ A2/A3 |
| `source_registry/store.py` | `SourceAvailabilityStore` — der einzige Zugriff auf Migration 007 | ⬜ A2 |
| `source_registry/sources.py` | `IGDerivedSource`, `LSStaticSource`, `RegistryYFSource` — alle drei ohne Netz | ⬜ A3 |
| `source_registry/arm.py` | Scharf-Flag `data/state/DISCOVERY_ARMED` (Muster `killswitch.py`, sichere Richtung umgedreht) | ⬜ C1 |
| `source_registry/run.py` | Der Daemon (Muster `data_foundation/run.py`: PID-File, graceful SIGTERM, `--once`) | ⬜ C2 |
| `scripts/run_discovery.sh` | Start-Wrapper (Muster `run_recorder.sh`) | ⬜ C4 |
| *(cross-phase)* `phase2_persistence/migrations/007_phase14_source_availability.sql` | die Kreuzungs-Tabelle **+ der einmalige yF-Backfill aus `instrument_universe`** (der Grundbestand kommt aus der Migration, nicht aus einem Resolver-Lauf — `resolve_epic` ruft `set_symbol` in sechs von acht Pfaden nicht) | ⬜ A2 |
| *(cross-phase)* `phase9_universe/universe/models.py` | `DS_STALE_SOURCE` ins Vokabular (Live-Blocker B1) | ⬜ A1 |
| *(cross-phase)* `phase9_universe/universe/store.py` | yF-Projektion in `set_symbol`, nicht-fatal | ⬜ A4 |
| *(cross-phase)* `phase13_live_data/live_data/backfill.py` | `EPIC_MAP` raus, Symbol-Lookup rein; `CapitalSource.discover()` | ⬜ B1/B2 |
| *(cross-phase)* `phase13_live_data/scripts/source_delta.py` | drei Fälle statt zwei (`not_available` / `available_but_empty` / `compared`) | ⬜ B3 |
| *(cross-phase)* `phase8_scheduler/webui/api.py` + `static/` | `GET /api/discovery`, ARM/DISARM, Warn-Banner | ⬜ C3 |

---
 
---

## Session stopped — 2026-08-22 (Session 5: B1a — probe_capital.py erweitert + Operator-Probe startklar)

> **Auftrag:** Nikinger-Frage „was sagt der Plan zu B1a-vs-A4?" → Plan schweigt
> explizit zu dieser Frage (D20 lockt nur A→B; §6 B1 + §9.3 lockt nur B1a→B1b,
> kein Cross-Block-Constraint). Nikinger folgt meiner Empfehlung Option C:
> B1a-Code jetzt, A4 in der Folge-Session, B1b sobald Operator-Output vorliegt.
> B1a-Build: 5-Minuten-Job (`probe_capital.py` um `--markets`-Modus erweitern).

### Completed

**`phase13_live_data/scripts/probe_capital.py`** — zwei neue Flags, +79 Zeilen:

| Flag | Wirkung |
|---|---|
| `--markets` (bool) | B1a-Modus: nach Auth pro Term ein GET `/api/v1/markets?searchTerm=…`, **roh** ausgegeben (keine Filterung, kein Prices-Probe) |
| `--terms` (str) | Suchterme für `--markets` (Default fällt auf `--indices` zurück → backward-compat mit den existierenden Defaults `Germany 40,France 40,Spain 35`) |

Existierender Prices-Probe-Flow **unverändert** — Auth-Pfad ist geteilt (CST +
X-SECURITY-TOKEN einmal holen, dann Verzweigung). Die Pre-Session-Antwort vom
2026-08-22 („`--markets --terms Germany 40,France 40,Spain 35` ⇒ unrecognized
arguments") ist damit behoben: das Argument existiert jetzt.

Output-Format pro Term im `--markets`-Modus:

```json
{
  "term": "Germany 40",
  "http_status": 200,
  "url": "https://demo-api-capital.backend-capital.com/api/v1/markets?searchTerm=Germany+40",
  "content_type": "application/json",
  "raw_text_snippet": "..." (erste 500 Zeichen),
  "raw_body": { ... die tatsächliche API-Antwort ... }
}
```

Dazu `purpose` + `next_step_hint` als Hilfetext für den Operator — erklärt, **was**
in `raw_body` zu suchen ist (Feldnamen für Source-Symbol, das aktuell `DE40`/`FR40`
in `EPIC_MAP` heißt, und alles was zur IG-Epic zurückmappt).

### Operator-Befehl (Demo, kostenlos, am Wochenende möglich)

```bash
phase1_broker_wrapper/.venv/bin/python phase13_live_data/scripts/probe_capital.py \
    --markets --terms "Germany 40,France 40,Spain 35"
```

Output (JSON auf stdout, stderr = narrative) im nächsten Chat pasten. Ich
baue danach `CapitalSource.discover()` (B1b) gegen die beobachtete Form.

### Verified (heute nachgemessen, 2026-08-22)

| Suite | Vor B1a | Nach B1a | Δ |
|---|---:|---:|---:|
| phase13_live_data | 53 | 53 | 0 (B1a ist Script-Erweiterung, keine Test-Änderung) |
| **Summe (Regression)** | **1634** | **1634** | **0** |

Working tree clean (außer dem Hygiene-Findling aus Session 4), `ps aux | grep
scheduler.run` leer, kein Live-DB-Write. Cross-Phase-Edit: ein gezielter Patch
in `phase13_live_data/scripts/probe_capital.py` (Phase 13 ist freigegeben für
Phase-14-Cross-Phase-Edits, Nikinger 2026-08-22). Kein Build, kein
Commit-Push für die anderen Session-5-Edits — das wäre Session-Arbeit.

### Cross-Phase-Anmerkungen für die nächsten Schritte

- **A4 folgt nach dem Operator-Output** (oder parallel, falls du die Probe
  erst am Wochenende machst). A4 braucht **keinen** B1a-Output — die
  yF-Projektion in `set_symbol` ist orthogonal zur Capital.com-Discovery-Form.
- **Falls die Probe einen überraschenden Status liefert** (z.B. 403 oder ein
  Swagger-Drift): Block B fällt auf `origin='operator'` zurück (Plan §6 B1
  „Kein Raten"-Klausel: 2 Paare DE40+FR40 als Seed-Script), Block B2
  (`EPIC_MAP` raus) bleibt machbar. Kein B-Block bricht.
- **B1b + die +4 B1b-Tests** kommen in der Folge-Session nach der Probe.

### Next

- **Operator (Nikinger):** Probe-Run oben ausführen, Output im nächsten Chat
  pasten. Push-Freigabe für 3 Commits (`fd9e7f8` A3-Code, `888ee01`
  Session-4-Docs, `69cfc31` B1a). 3 Commits vor `origin/main`.
- **Ausführende Session (nächste):** Plan §6 **Block A4** — yF-Projektion in
  `UniverseStore.set_symbol`. Sechs Tests gegen die Doppelschreiber-These
  (Plan §6 A4 Test 6). Falls B1a-Output schon da: **danach** B1b
  (`CapitalSource.discover()` gegen beobachtete Form).
- **Unverändert offen:**
  - Operator-Run der B1a-Probe (das hier, am Wochenende möglich).
  - Optional: `.gitignore`-Pattern für `*.sqlite.bak-*` (1 Zeile, s. Session-4).
  - Optional: `ROADMAP.md:427` Korrektur-Eintrag (zweiter Roll-over).