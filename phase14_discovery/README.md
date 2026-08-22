# phase14_discovery — Discovery-Then-Deterministic

**Mid-Phase-Stand 2026-08-22 (Session 9):** Blöcke 0 + A + B + C code-complete,
Akzeptanz **A1–A8 alle grün** (Sweep Σ 1698), Phase-Final-Closeout (**D5**) nach
Phase-13-Beweiswoche (Plan §7 P1–P9) — Beweiswoche läuft separat, operiert von
Nikinger.

> Phase 14 turns "which source can serve epic X?" from a hardcoded dict in the
> code into a row in the database. Each source exposes its own delivery spectrum
> as a `SourceProfile`; the cross-product IG-Epic × Source × Resolution lives
> in `instrument_source_availability` (Migration 007); consumers read the table
> instead of the code — and `EPIC_MAP` disappears.

Mission (one line): **was eine Quelle kann, sagt die Quelle — nicht der
Konsument.**

Full execution-ready plan (locked decisions **D1–D20**, Block 0/A/B/C/D step
sequence with verbatim anchors, acceptance **A1–A8**, complete drift list):
[`docs/concepts/phase14_discovery_plan.md`](../docs/concepts/phase14_discovery_plan.md).
Phase head / session log: [`CLAUDE.md`](./CLAUDE.md).

---

## Was Phase 14 heute kann (Bedien-Anleitung)

**Standard-Verhalten:** der Discovery-Daemon läuft **immer mit** (Phase-8
`run_scheduler.sh` startet ihn via `nohup …/run_discovery.sh`), tut aber
**nichts**, solange `data/state/DISCOVERY_ARMED` fehlt (Plan D10 — safe
default `False`). Das ist **kein Bug**, das ist die Sicherheitsrichtung.

**ARM (scharfschalten):** Web-UI öffnen (lokal auf
`phase8_scheduler/scripts/run_webui.sh` oder wie im Phase-8-Setup), das neue
amber Banner „SOURCE DISCOVERY NOT ARMED" ist sichtbar (Status-Card), Buttons
„ARM DISCOVERY" / „DISARM DISCOVERY" liegen in der dritten Button-Row.
Klick auf **ARM DISCOVERY** → `data/state/DISCOVERY_ARMED` wird geschrieben
→ der nächste Daemon-Tick (Default 3600 s, also bis zu 1 h) prüft die Tabelle
und schreibt ggf. Availability-Zeilen. Sichtbar im UI: das Banner verschwindet,
das Banner zeigt jetzt „armed by=dashboard ts=…".

**DISARM (scharf raus):** Button **DISARM DISCOVERY** → Datei weg → Daemon
schläft wieder. Banner kommt zurück.

**Operator-Quick-Aktionen ohne UI:**

```bash
# ARM von Hand:
echo '{"armed": true, "by": "operator:manual", "ts": "'"$(date -u +%FT%T.%3NZ)"'"}' \
    > data/state/DISCOVERY_ARMED

# DISARM von Hand:
rm data/state/DISCOVERY_ARMED

# Einmal-Cycle ohne Daemon-Restart (Operator-Diagnose):
phase1_broker_wrapper/.venv/bin/python -m source_registry.run --once

# Letzten Cycle-Stand lesen:
cat data/state/discovery_state.json   # ts_utc, armed, stale_count, rows_written, errors

# Live-Status über die API:
curl -s localhost:<webui-port>/api/discovery | jq
```

**Fail-Safe:** der Daemon bucht nie etwas ins Budget- oder Allowance-Ledger
außer `probe_calls_used > 0` ist. Die drei Default-Sources (IGDerived,
LSStatic, RegistryYF) sind **net-free** (`probe_calls_used == 0`) — also keine
Ledger-Einträge im Normalbetrieb. Erst wenn Capital.com als Discovery-Source
hinzukommt (Phase-13-B1b-Wiring), wird `spend_kind='discovery'` ins
`source_spend`-Ledger geschrieben.

**Discovery berührt IG strukturell nicht:** kein `/prices`-Call, kein
`search_markets`. Die IG-Zeile wird aus `instrument_universe` **abgeleitet**
(D6, Beweis: Broker-Fake, dessen jede Methode `AssertionError` wirft, `discover()`
läuft trotzdem durch).

---

## Package: `source_registry` (Stand Session 9)

| Module | Responsibility | Status |
|---|---|---|
| `models.py` | `SourceAvailability` + `SourceProfile` dataclasses + `Source` Protocol + `origin`-Vokabular | ✅ A2/A3 |
| `store.py` | `SourceAvailabilityStore` — der einzige Zugriff auf Migration 007 (eigene `sqlite3`-Connection, Phasen-Isolation) | ✅ A2 |
| `sources.py` | `IGDerivedSource` (D6: jede Epic ⇒ abgeleitete Zeile, **null IG-Punkte**), `LSStaticSource`, `RegistryYFSource` — alle drei ohne Netz | ✅ A3 |
| `arm.py` | Scharf-Flag `data/state/DISCOVERY_ARMED` (Muster `killswitch.py`, sichere Richtung umgedreht: fail-soft + `False` als Default) | ✅ C1 |
| `run.py` | Daemon (Muster `data_foundation/run.py`: PID-File, `SIGTERM`/`SIGINT` → graceful, `--once`) | ✅ C2 |
| `__init__.py` | Public-Surface-Exports (Arm-Symbole + Models + Sources + Store) | ✅ Block 0 + C1 |
| `scripts/run_discovery.sh` | Start-Wrapper (Muster `run_recorder.sh`) | ✅ C4 |

Plus Cross-Phase-Edits (in der freigegebenen Liste, Nikinger 2026-08-22):

| File | Was | Status |
|---|---|---|
| `phase2_persistence/migrations/007_phase14_source_availability.sql` | Die Kreuzungs-Tabelle + einmaliger yF-Backfill aus `instrument_universe` (Migration 007) | ✅ A2 |
| `phase9_universe/universe/models.py` | `DS_STALE_SOURCE` ins Vokabular (Live-Blocker B1, Fix A1) | ✅ A1 |
| `phase9_universe/universe/store.py` | yF-Projektion in `set_symbol`, nicht-fatal | ✅ A4 |
| `phase13_live_data/live_data/backfill.py` | `CapitalSource.discover()` (B1b); `EPIC_MAP` raus + `symbol_lookup`-Callable rein (B2) | ✅ B1b + B2 |
| `phase13_live_data/scripts/probe_capital.py` | CFD-Filter-Bug Fix: `"CFD"`-Substring → exakt `"INDICES"` | ✅ Cross-Phase-Hygiene Session 7 |
| `phase13_live_data/scripts/source_delta.py` | Drei Fälle statt zwei (`not_available` / `available_but_empty` / `compared`) | ✅ B3 |
| `phase8_scheduler/webui/api.py` + `static/` | `GET /api/discovery`, ARM/DISARM, amber Warn-Banner | ✅ C3 |
| `phase8_scheduler/scripts/run_scheduler.sh` | Autostart-Hook für `run_discovery.sh` (analog Recorder-Block) | ✅ C4b |

---

## Akzeptanz-Status (Plan §7)

| # | Kriterium | Status | Beleg |
|---|---|---|---|
| **A1** | Discovery gibt **strukturell** null IG-Punkte aus | ✅ | `test_sources.py` Broker-Fake (jede Methode wirft), `discover()` durchläuft, `probe_calls_used == 0` |
| **A2** | `grep -rn "EPIC_MAP" phase13_live_data/ --include=*.py` ist **leer** | ✅ | Exit 1, kein Treffer (mehrfach verifiziert in Session 8 + 9) |
| **A3** | `measurable_universe()` vor/nach Phase 14 identisch | ✅ | `test_store.py` + Read-only-Probe gegen Produktions-DB (5× `(yf, ok)` + 3× `(yf, no_intraday_source)`, §2.2 des Plans) |
| **A4** | yF-Projektion reproduziert heutiges Registry-Substrat exakt | ✅ | Migration-007-Backfill (5+3 Epics), `set_symbol`-Fortschreibung |
| **A5** | Daemon tut unscharf **nichts** | ✅ | `test_run_once_unarmed_does_nothing` (Fake-Source wirft, kein `discover`-Call, `armed=False` im state-File) |
| **A6** | UI warnt bis scharfgestellt, schaltet per Datei | ✅ | `test_discovery_unarmed_reports_false` + `test_discovery_endpoint_fails_soft_without_migration_007` |
| **A7** | `source_delta.py` unterscheidet „nicht abrufbar" von „divergiert" | ✅ | Drei Tests pro Fall (not_available / available_but_empty / compared) |
| **A8** | Kein roter Test, keine uncommitteten Änderungen | ✅ | Sweep Σ 1698 (Baseline 1659 + 39 aus Block B/C, 0 Regressions) |

**Sweep-Stand Session 9** (Σ 1698, alle Suiten grün, separat gelaufen wegen
der `tests.conftest`-Namenskollision):

```
phase1_broker_wrapper:    95   phase9_universe:          87
phase2_persistence:       77   phase10_v3:              165
phase3_external_data:    104   phase12_data_foundation: 143
phase4_research:         155   phase13_live_data:        74
phase5_execution:        173   phase14_discovery:        57
phase6_debate:            76   meta_m1_harness:          28
phase7_reward:           138   root tests/:              80
phase8_scheduler:        248
```

---

## Was noch ausstehend ist

- **Phase-13-Beweiswoche** (Phase-13 Plan §7 P1–P9) läuft separat, operator-getrieben.
  Block C (C1–C4) berührt sie nicht — kein Konsumentenpfad schreibt in
  `instrument_source_availability` während der Beweiswoche; die einzigen
  Schreiber sind (a) A4-Projektion in `UniverseStore.set_symbol`, die auf den
  nächsten Resolver-Tick wartet, und (b) der C2-Daemon, der ohne `arm`-Flag
  ein No-Op ist.
- **D5 Closeout-Handover** wird die letzte Phase-14-Session, **nach** der
  Beweiswoche. Bis dahin Mid-Phase-Status hier.
- **Plan-§9-Drift-Listeneintrag #2 erweitern** in der nächsten Plan-Session.
- **Phase-15-Planungs-Session:** V4-Themen (Council, Handover, Reward-Reform,
  Force-Trigger, Instinct-ECC) — gegatet auf Phase 9+11+12+13+14 + reale Outcomes.

---

**Bauprinzip:** zero new AI. Source discovery, symbol mapping, availability
evaluation, scharfschalt logic — deterministic code, see root `CLAUDE.md`.
Whoever reaches for an LLM call here → **stop**, that is code.

**Dreifacher Kontingent-Deckel:**
1. **strukturell** — Discovery ruft nie `/prices`, nie `search_markets` (D6);
   IG-Zeile wird abgeleitet, testbar mit einem Broker-Fake, dessen jede
   Methode wirft.
2. **zwei getrennte Kontingente** — 10 000-Punkte-Wochenfenster (`/prices`) und
   API-Key-Allowance (30 req/min) werden beide nicht berührt, weil IG gar nicht
   gerufen wird.
3. **Ledger-`spend_kind='discovery'`** — jeder Fetch, der doch Netz kostet (heute
   nur Capital.com), wird im existierenden `source_spend`-Ledger gebucht.
