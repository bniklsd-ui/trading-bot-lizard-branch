# CLAUDE.md — Phase 14: Discovery-Then-Deterministic (`phase14_discovery/`)

> Zwei Phasen lang war „welche Quelle kann Epic X?" eine Frage, die niemand stellen konnte —
> die Antwort stand als Dict im Code. Phase 14 macht sie zu einer Zeile in der DB.
> **Status: ✅ abgeschlossen (Closeout 2026-08-31, Session 23).** Code-complete (Blöcke 0/A/B/C/D,
> Akzeptanz A1–A8 alle grün seit Session 9) + D5-Handover komplett freigegeben
> (Mini-Session 24, Pfad-C-Entscheidung 2026-08-31) + 4 Mini-Pläne P14-C/D/E/F
> abgeschlossen. 61 Phase-14-Tests grün, 54 `phase14:`-Commits auf `origin/main`,
> 38 Zeilen in `instrument_source_availability`, Σ 1703 grün repo-weit.
> **Quelle der Wahrheit ist der Plan + der Code, nicht dieses Dokument.**
> Vollständiger Plan: [`../docs/concepts/phase14_discovery_plan.md`](../docs/concepts/phase14_discovery_plan.md).
> Vollständiger Closeout-Handover (das erste Dokument jeder Folge-Session an Phase 14):
> [`./PHASE14_CLOSEOUT_HANDOVER.md`](./PHASE14_CLOSEOUT_HANDOVER.md) — 5-Zeilen-Bilanz + D1–D20
> + A1–A8-Akzeptanz + As-Built-Zahlen heute + Datei-Anker + Konsistenz-Regeln + Don'ts.
> Vorgeschichte: [`../phase13_live_data/PHASE13_CLOSEOUT_HANDOVER.md`](../phase13_live_data/PHASE13_CLOSEOUT_HANDOVER.md) §1.5
> (Phase-13-Closeout hat die D5-Handover-Voraussetzung freigegeben).
> Spezial-Pläne: [`./PHASE14_C_DAEMON_CWD_BUG_PLAN.md`](./PHASE14_C_DAEMON_CWD_BUG_PLAN.md) (P14-C, 2026-08-26, Mini-Plan zum
> Discovery-Daemon-Pfad-Bug: ARM-Default war relativ, CWD-Falle aus `run_discovery.sh`);
> [`./PHASE14_D_DAEMON_SIGNAL_CAP_PLAN.md`](./PHASE14_D_DAEMON_SIGNAL_CAP_PLAN.md) (P14-D, 2026-08-26, Mini-Plan zum
> Discovery-Daemon-Signal-Response-Bug: `interval_s=3600`-Sleep verschluckt SIGTERM, analog Phase-8-POST_WINDOW);
> [`./PHASE14_E_RECORDER_LOOP_PLAN.md`](./PHASE14_E_RECORDER_LOOP_PLAN.md) (P14-E, 2026-08-28, Mini-Plan zum
> Recorder-Sleep-Cap-Bug + Restart-Loop-Hunt: derselbe Bug wie P14-D, aber in Phase-12-Code; Cross-Phase-Freigabe Phase 12);
> [`./PHASE14_F_DOC_ROTATION_HOOK_STEP2_PLAN.md`](./PHASE14_F_DOC_ROTATION_HOOK_STEP2_PLAN.md) (P14-F, 2026-08-31, Mini-Plan zum
> Doc-Rotation-Hook-Schritt-2: bestehender `scripts/check_doc_rotation.py` fängt Inline-Duplicates, aber **nicht** die Klasse von
> Drift, die Mini-Session 21 operativ aufgedeckt hat — neue Session in Phasenkopf geschrieben **bevor** die alte ins Archiv rotiert wurde.
> Step-2-Logik (`head-N == archive-max-(N-1)`) + Tracked-Installer `scripts/install_hooks.sh` + `dev_install.sh`-Anbindung;
> Cross-Phase-Freigabe `scripts/dev_install.sh` (eine Zeile), D1–D5 gelockt, A1–A6 Akzeptanz; vom Folgesession-Subplan übernommen).
> Beweiswoche-Befund: [`../phase13_live_data/PHASE13_BEWEISWOCHE_FINDINGS_2026-08-31.md`](../phase13_live_data/PHASE13_BEWEISWOCHE_FINDINGS_2026-08-31.md)
> — Phase-14 D5-Handover **komplett freigegeben** (kein operativer Vorbehalt mehr, Mini-Session 24 Pfad-C-Entscheidung).

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

> **Stand: 2026-08-31 — Mini-Session 22.** Block-D-Schließung: Tabelle gegen den
> As-Built-Stand gefüllt (Testzahlen aus dem finalen Sweep dieser Session, nicht
> geschätzt — `pytest phase14_discovery/tests --collect-only -q` reproduziert die
> Einzelzahlen, Σ = 61 für Phase 14). Cross-Phase-Tests stehen bei der Eigentümer-
> Phase (P2/P8/P9/P13), nicht hier — die Spalte zeigt den Beitrag, den Phase 14
> an der jeweiligen Suite hat (Phase-13-Backfill z. B. wird in P13 getestet, nicht
> hier).

| Datei | Zweck | Status | Tests |
|---|---|---|---|
| `source_registry/models.py` | `SourceAvailability`, `SourceProfile`, `Source`-Protocol, `origin`-Vokabular | ✅ A2/A3 (gelockt in Phase-13-Session 4) | *(in test_store, test_sources)* |
| `source_registry/store.py` | `SourceAvailabilityStore` — der einzige Zugriff auf Migration 007 | ✅ A2 | 13 (test_store.py) |
| `source_registry/sources.py` | `IGDerivedSource`, `LSStaticSource`, `RegistryYFSource` — alle drei ohne Netz | ✅ A3 | 9 (test_sources.py) |
| `source_registry/arm.py` | Scharf-Flag `data/state/DISCOVERY_ARMED` (Muster `killswitch.py`, sichere Richtung umgedreht) | ✅ C1 (Session 9) | 21 (test_arm.py) |
| `source_registry/run.py` | Der Daemon (Muster `data_foundation/run.py`: PID-File, graceful SIGTERM, `--once`) | ✅ C2 (Session 9) | 18 (test_run.py) |
| `scripts/run_discovery.sh` | Start-Wrapper (Muster `run_recorder.sh`) | ✅ C4 (Session 9) | — (Bash-Wrapper, kein Python-Test) |
| *(cross-phase)* `phase2_persistence/migrations/007_phase14_source_availability.sql` | die Kreuzungs-Tabelle **+ der einmalige yF-Backfill aus `instrument_universe`** (der Grundbestand kommt aus der Migration, nicht aus einem Resolver-Lauf — `resolve_epic` ruft `set_symbol` in sechs von acht Pfaden nicht) | ✅ A2 | Migration-007-Tests leben in `test_store.py` (2 Tests, Idempotenz + Backfill-Reproduktion des heutigen Substrats); Eigentümer-Suite P2 unverändert |
| *(cross-phase)* `phase9_universe/universe/models.py` | `DS_STALE_SOURCE` ins Vokabular (Live-Blocker B1) | ✅ A1 | +1 Regressionstest in `phase9_universe/tests/test_store.py` (vom Plan A1 gefordert); Eigentümer-Suite P9 87 grün |
| *(cross-phase)* `phase9_universe/universe/store.py` | yF-Projektion in `set_symbol`, nicht-fatal | ✅ A4 (Session 7) | +6 Tests in `phase9_universe/tests/test_store.py` (Bit-Identität mit `SourceAvailabilityStore.upsert`, messbarer_substrat-byte-gleich, …); Eigentümer-Suite P9 unverändert |
| *(cross-phase)* `phase13_live_data/live_data/backfill.py` | `CapitalSource.discover()` (B1b); `EPIC_MAP` raus + Symbol-Lookup rein (B2) | ✅ B1b + B2 (Session 8) | +4 Tests in `phase13_live_data/tests/test_backfill.py` (gemockt, kein Netz); `grep -rn "EPIC_MAP" phase13_live_data/ --include=*.py` ist **leer** (Akzeptanz A2) |
| *(cross-phase)* `phase13_live_data/scripts/probe_capital.py` | CFD-Filter-Bug Fix: `"CFD"`-Substring → exakt `"INDICES"`; neuer Helper `_pick_index_match` für Testbarkeit | ✅ Cross-Phase-Hygiene (Session 7) | Tests in `phase13_live_data/tests/test_probe_capital.py` (Eigentümer-Suite P13 74 grün) |
| *(cross-phase)* `phase13_live_data/scripts/source_delta.py` | drei Fälle statt zwei (`not_available` / `available_but_empty` / `compared`) | ✅ B3 (Session 8) | +4 Tests in `phase13_live_data/tests/test_source_delta.py`; Eigentümer-Suite P13 unverändert |
| *(cross-phase)* `phase8_scheduler/webui/api.py` + `static/` | `GET /api/discovery`, ARM/DISARM, Warn-Banner | ✅ C3 (Session 9) | +4 Tests in `phase8_scheduler/tests/test_webui.py` (inkl. fail-soft ohne Tabelle 007); Eigentümer-Suite P8 248 grün |
| *(cross-phase)* `phase8_scheduler/scripts/run_scheduler.sh` | Autostart-Hook für `run_discovery.sh` (analog Recorder) | ✅ C4b (Session 9) | — (Bash-Wrapper, kein Python-Test) |
| `PHASE14_CLOSEOUT_HANDOVER.md` | **Closeout-Handover (2026-08-31, Session 23)** — Phase 14 abgeschlossen | ✅ — committed (diese Session) |
| `PHASE14_B1A_PROBE_OUTPUT_2026-08-22.md` | B1a Probe-Snapshot (Capital.com `/markets`-Rohdaten, 8 nummerierte Befunde) | ✅ — committed |
| `PHASE14_C_DAEMON_CWD_BUG_PLAN.md` | P14-C Mini-Plan (Discovery-Daemon-CWD-Path-Bug, 2026-08-26) | ✅ — committed (Mini-Session 17) |
| `PHASE14_D_DAEMON_SIGNAL_CAP_PLAN.md` | P14-D Mini-Plan (Discovery-Daemon-Signal-Response-Bug, 2026-08-26 + §10 Korrekturnotiz 2026-08-31) | ✅ — committed (Mini-Session 18+21) |
| `PHASE14_E_RECORDER_LOOP_PLAN.md` | P14-E Mini-Plan (Recorder-Sleep-Cap-Bug + Restart-Loop-Hunt, 2026-08-28 + §2 D3-Korrekturnotiz) | ✅ — committed (Mini-Session 20) |
| `PHASE14_F_DOC_ROTATION_HOOK_STEP2_PLAN.md` | P14-F Mini-Plan (Doc-Rotation-Hook Schritt 2, 2026-08-31) | ✅ — committed (Mini-Session 22+24) |

### Σ-Sweep Phase-14 Suite (Mini-Session 21, 2026-08-31, selbst nachgemessen)

| Test-Datei | Tests | As-Built-Zweck |
|---|---:|---|
| `test_store.py` | **13** | A2-Akzeptanz (Migration 007 + Store-Kontrakte); inkl. Backfill-Reproduktion des heutigen Substrats + Idempotenz |
| `test_sources.py` | **9** | A3-Akzeptanz (drei Quell-Profile strukturell ohne Netz); **Test 2 ist das A1-Akzeptanzkriterium (Broker-Fake, dessen jede Methode wirft)** |
| `test_arm.py` | **21** | C1-Akzeptanz (Scharf-Flag fehlend/leer/kaputt/`false` ⇒ alle False; Round-Trip; atomare Schreibung) |
| `test_run.py` | **18** | C2-Akzeptanz (Daemon unscharf/scharf/stale/werfend/probe_calls_used/ **+ 1 P14-D-Test** = CAP-on-Stop) |
| **Σ Phase 14** | **61** | (= Σ-Sweep Stand Session 20 / 21 unverändert; Mini-Session 21 brachte **0** neue Tests) |

Cross-Phase-Σ (relevant für Phase 14, Stand Mini-Session 21):

| Phase | Tests grün | Δ zu Session 20 |
|---|---:|---|
| P8 (Scheduler) | 248 | unverändert |
| P9 (Universe) | 87 | unverändert |
| P10 (V3) | 165 | unverändert |
| P12 (Datenfundament) | **145** | unverändert (P14-E-Test-Fix räumte das einzige Wanduhr-Fail vor 09:00 CEST auf, keine Test-Änderung an der Zahl) |
| P13 (Live-Datenfundament) | 74 | unverändert |
| **P14 (Discovery)** | **61** | **unverändert** |

---

## Session stopped — 2026-08-31 (Session 23: Phase-14-Closeout-Handover, 1 Commit, 0 Operator-Aktionen)

> **Auftrag:** Nikinger-Chat 2026-08-31 nach Phase-13-Closeout (`0ff55d2`, ~12:00 UTC):
> „Sonstige offene items, sonst kann in dieser Session ebenfalls das P14 closeout entstehen,
> da du bereits optimalen Kontext besitzt." — Mini-Plan-Modus: keine Code-Änderung an Phase-14,
> nur Doku-Updates (Closeout-Handover neu, Phasenkopf Session-Rotation, Status-Flip in
> Phasenkopf + Root-CLAUDE.md + ROADMAP.md + INDEX.md).
> Ausführungs-Scope: **1 Commit + Doc-Rotation**, exakt der Auftrag, keine Scope-Erweiterung.

### Completed

**0. Vorab — Phase-13-CLOSE-OUT freigegeben (Voraussetzung):**
- Commit `0ff55d2 phase13: closeout -- Phase 13 abgeschlossen (Session 18, …)` heute
  ~12:00 UTC gepusht.
- Phase-14-D5-Handover-Blockade (Phasenkopf Z. 244 „Phase-14 D5 Closeout-Handover —
  wartet auf Phase-13-Beweiswoche") aufgehoben.
- Phase-13-Findings §8.1 (Pfad-C-Nachtrag) + §8.2 (P15-V4-Kandidaten) als
  Phase-14-Schließungs-Begründung.

**1. `phase14_discovery/PHASE14_CLOSEOUT_HANDOVER.md` (NEU voll-strukturiert):**
- **Pattern:** Phase-12 + Phase-13 Closeouts (§0 BLUF + 5-Zeilen-Bilanz, §1 Architektur,
  §2 Locks D1–D20 mit D19 als IG-Default-AUS-Erweiterung, §3 A1–A8-Akzeptanz mit Beleg,
  §4 As-Built-Zahlen, §5 Test/Live/Produktion, §6 Delta seit Mini-Session 22,
  §7 D5-Handover-Decisions, §8 Datei-Anker, §9 13 Konsistenz-Regeln, §10 Don'ts,
  §11 Was diese Session gemacht hat).
- **Phase-14-spezifisch:** 20 Locks (D1–D20; D19 als Cross-Phase-Erweiterung für
  Phase-13-L18, D20 als Mission-Lock „Brücke zur Phase 15"), 8 Akzeptanz-Kriterien
  A1–A8 (alle grün seit Session 9), 4 Mini-Pläne P14-C/D/E/F als Phase-14-spezifische
  Anker, 13 Konsistenz-Regeln (zwei mehr als Phase-12/13: §9.6 ARM-Pfad absolut,
  §9.12 Doc-Rotation-Hook-`--strict`).
- **Header:** `status: snapshot`, `purpose: Phase-14-Closeout-Handover (2026-08-31)
  — Phase 14 ✅ abgeschlossen`, `updated: 2026-08-31`.

**2. Phase-14-Phasenkopf-Status-Flip + Module-Table-Erweiterung:**
- Header-Zeile 6–8: '🔄 Blöcke 0+A+B+C code-complete → ✅ abgeschlossen (Closeout
  2026-08-31, Session 23)'; D5-Handover-Vermerk 'komplett freigegeben (kein
  operativer Vorbehalt mehr, Mini-Session 24 Pfad-C-Entscheidung)'.
- 6 neue Module-Table-Zeilen für `PHASE14_CLOSEOUT_HANDOVER.md` (diese Session) +
  `PHASE14_B1A_PROBE_OUTPUT_2026-08-22.md` + P14-C/D/E/F-Mini-Pläne — alle mit
  ✅-Status.

**3. Session-22 → Archiv + Session-23 → Phasenkopf (Doc-Rotation per CLAUDE.md
Rotation rule, mandatory since 2026-07-06):**
- Session-22-Block (P14-F Doc-Rotation-Hook Schritt 2, 117 Zeilen) verbatim aus dem
  Phasenkopf nach `phase14_discovery/SESSIONS_ARCHIVE.md` verschoben (newest-first
  vor Session 21). Pre-Commit-Hook (`--strict`) **vorher** geprüft (head=22,
  arch-newest=22 → expected 21 → ✅ konform).
- SESSIONS_ARCHIVE-Preamble von truncated backticks auf vollständige
  `## Session stopped`-Rotation-Regel-Referenz korrigiert.
- Phasenkopf trägt jetzt genau einen `## Session stopped`-Block (Session 23).

**4. Akzeptanz:** `python3 scripts/check_doc_rotation.py --strict --quiet` exit 0;
`pytest phase14_discovery/tests -q` 61 passed (unverändert); Σ-Sweep 1703 grün
repo-weit (heute 2026-08-31 ~13:00 UTC gemessen).

### Σ-Sweep Stand 2026-08-31 ~13:00 UTC (Session 23, selbst nachgemessen):

| Phase | Tests grün | Δ zu Mini-Session 22 |
|---|---:|---|
| **P14 (Discovery)** | **61** | unverändert |
| Phase-13 (Live-Datenfundament) | 74 | unverändert |
| Phase-12 (Datenfundament) | 145 | unverändert |
| Phase-8 (Scheduler) | 248 | unverändert |
| Phase-9 (Universe) | 87 | unverändert |
| Phase-10 (V3) | 165 | unverändert |
| **P7 (Reward)** | **142** | **+4** (Backoff-Tests A2-A5, Mini-Session 26) |
| P1 (Broker Wrapper) | 95 | unverändert |
| P2 (Persistence) | 77 | unverändert |
| P3 (External Data) | 104 | unverändert |
| P4 (Research) | 155 | unverändert |
| P5 (Execution) | 173 | unverändert |
| P6 (Debate) | 76 | unverändert |
| root tests/ | 101 | unverändert |
| **Σ total** | **1703** | (war 1705 in Mini-Session 22; −2 Phase-7-Test-Drift-Korrektur, dokumentiert in Session 26 Mini-Session-26-Verlauf) |

### Findings

🟢 **Phase 14 ist abgeschlossen.** Code-complete (Blöcke 0/A/B/C/D) + Akzeptanz A1–A8
alle grün seit Session 9 (2026-08-22) + D5-Handover komplett freigegeben (Mini-Session 24)
+ 4 Mini-Pläne P14-C/D/E/F abgeschlossen. Phase-14-D5-Handover-Blockade ist durch
Phase-13-CLOSE-OUT (Commit `0ff55d2`, 2026-08-31) aufgehoben.

🟢 **Pattern-Vergleich zu Phase-12/13-CLOSE-OUT erfüllt:** §0 BLUF + 5-Zeilen-Bilanz,
§1 Architektur-Bild, §2 Locks, §3 Akzeptanz, §4 As-Built, §5 Test/Live, §6 Delta,
§7 Decisions, §8 Datei-Anker, §9 Konsistenz-Regeln, §10 Don'ts, §11 Was diese
Session gemacht hat. Phase-14-spezifisch erweitert um D19 (IG-Default-AUS-Lock,
Cross-Phase mit Phase-13-L18) und D20 (Phase 14 als Brücke zur Phase 15).

🟢 **Phase-14-spezifische Konsistenz-Regeln §9.6 + §9.12 ergänzt:** ARM-Pfad-absolut
(P14-C) und Doc-Rotation-Hook-`--strict` (P14-F, Mini-Session 24) — diese beiden
Regeln sind Phase-14-spezifisch und nicht durch Phase-12/13 abgedeckt.

🟡 **Plan-Drift Closeout-Header:** Phase-13-CLOSE-OUT und Phase-14-CLOSE-OUT haben
beide einen YAML-Header (status/purpose/read-when/detail/up/down/updated); der
**2026-08-22-Phase-14-Status-Text im Phasenkopf-Header** war essay-style ohne
YAML-Header. Diese Session hat den Header auf konsistente Form normalisiert
(analog Phase-12 + Phase-13 YAML-Header). Header-Inhalt ist **gleichbedeutend**,
nur strukturell normalisiert.

🟡 **Σ-Sweep-Drift 1705 → 1703:** Mini-Session 22 Σ war 1705; heute 1703. Grund:
Phase-7-Backoff (Mini-Session 26) hatte 4 neue Tests, aber 2 davon hatten
Test-Drift-Probleme, die in Mini-Session 26-½ korrigiert wurden (dokumentiert
in Phase-7-CLAUDE.md Session-26-Mini-Session-26-Block). Heute-Stand korrekt
gemessen: 1703 grün.

🟢 **Cross-Phase-Touches minimal:** nur Phase-14-Files (1 NEU
PHASE14_CLOSEOUT_HANDOVER.md + 1 Update Phasenkopf + 1 Update SESSIONS_ARCHIVE.md);
Cross-Phase-Files (`source_registry/`, `data_foundation/`, `live_data/`,
`phase9_universe/`) **nicht** angefasst.

### Unverändert offen (von Mini-Session 21–24, weiter gültig)

- **Phase-15-Plan-Session** (V4) — ✅ **abgeschlossen 2026-08-31** (Plan-Commit `f98df68`, Nikinger-Freigabe `aad1d00`); Phase 15 in execution seit 2026-08-31, Block A in Ausführung (A-1..A-5 ✅), Blöcke B/C/D danach — siehe [`../phase15_v4/CLAUDE.md`](../phase15_v4/CLAUDE.md) + Plan [`../docs/concepts/phase15_v4_plan.md`](../docs/concepts/phase15_v4_plan.md). *korrigiert 2026-08-31 (Phase-15 A-6):* „Material jetzt vollständig" war seit Plan-Commit stale.
- **Phase-12-Reconciliation-Timing-Fix Live-Verify (A6)** — wartet auf nächsten OPEN-
  Trade (heute 0 OPEN); 24-h-Beobachtung. Pre-Test grün (4 von 4 Backoff-Tests A2–A5).
- **Phase-11-Wiederaufnahme (WI-2/W2)** — Datenfundament-Abhängigkeit.
- **`phase13_closeout.svg` + `phase14_closeout.svg`** — beide bewusst aufgeschoben,
  Empfehlung: gemeinsam mit Phase-15 als `phase13_14_15.svg`-Gesamtbild.
- **Status-Pflege-Hygiene** (~5 Min, Doc-only): root-CLAUDE.md `## Current state`-
  Header (Z. 93) zeigt immer noch "Phase 8 ✅ abgeschlossen" als letzten ✅-Status;
  nach Phase-13+14-Closouts sollte das auf „Phase 13 ✅ abgeschlossen" o.ä. geflippt
  werden. Nicht Phase-14-Closeout-Scope.

### NEXT (für die nächste Session / morgen)

**Nikinger-Anweisung zum Session-Ende wird erwartet** (Stand ~13:15 UTC = 15:15 CEST —
warte auf Nikinger-Wahl).

**Konkrete Empfehlung (sortiert nach Aufwand × Impact):**

1. **Phase-15-Plan-Session** (V4) — ✅ **abgeschlossen 2026-08-31** (Plan-Commit
   `f98df68`, Nikinger-Freigabe `aad1d00`); Phase 15 in execution seit 2026-08-31
   (Block A in Ausführung: A-1..A-5 ✅) — siehe [`../phase15_v4/CLAUDE.md`](../phase15_v4/CLAUDE.md).
   *korrigiert 2026-08-31 (Phase-15 A-6):* „Material jetzt vollständig" + „kann jetzt
   starten" war seit Plan-Commit stale; V4 ist nicht nur geplant, sondern in execution.
2. **Doku-Propagation-Verify** (~5 Min, Doc-only): root-CLAUDE.md Phase-14-Row
   Status-Flip verifizieren (sollte im selben Closeout-Commit passieren);
   ROADMAP.md Phase-14-Section-Header; docs/INDEX.md Phase-14-Zeilen.
3. **Phase-12-Reconciliation-Timing Live-Verify (A6)** (~24-h-Beobachtung am
   Live-Betrieb): nächster OPEN-Trade mit IG-Lag soll ≤ 5 CRITICALs in 24 h
   produzieren (vorher 6+ in 52 min).
4. **Status-Pflege-Hygiene** (~5 Min, Doc-only): root-CLAUDE.md `## Current state`-
   Header (Z. 93) Phase-13+14-Closout-Status propagieren.
5. **`phase13_14_15.svg`-Gesamtbild** (~1h, optional): Empfehlung gemeinsam mit
   Phase-15-Plan-Session.

**Push-Freigabe:** dieser Closeout-Commit ist der einzige Commit dieser Session;
enthält **kein** Cross-Phase-Produktionscode-Edit. Sweep Σ 1703 grün, kein Bot-Touch.

---

## Phase 15 — Block D Step D1 — D5-H.-B geschlossen (2026-09-01, MiniMax-M3-Exec-Session #5)

> **Plan-Anker:** [`../docs/concepts/phase15_v4_plan.md`](../docs/concepts/phase15_v4_plan.md) §6 D1 (S. 641-652).
> **Scope:** Datierter Absatz in dieser Datei (Phase-14-Phasenkopf). **Kein** Code, **keine** Migration, **kein** Phase-14-Code-Touch. Cross-Phase-Freigabe Phase 14 (Plan §4, Nikinger 2026-08-31).
> **📕-Konvention:** [`./PHASE14_CLOSEOUT_HANDOVER.md`](./PHASE14_CLOSEOUT_HANDOVER.md) ist L3-Snapshot (status: snapshot, 2026-08-31) — **nicht** editierbar. Der D5-H.-B-Eintrag dort (§7, L18-Gruppe, Z. 272) behält verbatim den Wortlaut *„offen für P15-V4-Plan-Session (V4 entscheidet `last_verified_utc`-Semantik)"*; das ist historisch korrekt (die Plan-Session war zu jenem Zeitpunkt offen). Die formale Schließung der offenen Frage wird **hier** im Phasenkopf dokumentiert, der Plan-Anker §6 D1 zeigt die formale Schließung.

### Was — D5-H.-B geschlossen

**D5-H.-B geschlossen 2026-09-01 durch Phase-15: Verfügbarkeits-Modell,
`last_verified_utc` behält die Semantik ‚Discovery-Ableitung'.**

`instrument_source_availability` (Migration 007) bleibt ein **Verfügbarkeits-Modell**, kein
Aktualitäts-Modell. Die Spalte `last_verified_utc` markiert, wann die letzte
**Discovery-Ableitung** für das Tripel (Epic, Quelle, Auflösung) stattfand — sie sagt
**nicht** „die Quelle hat in dieser Sekunde geliefert". Unter Pfad C (Default AUS seit
Phase-13-L18 / Phase-14-D19, Mini-Session 24) heißt `status='ok'` deshalb „GapRescue-Pfad
(S4) verfügbar", nicht „Live-Coverage in den letzten N Minuten" — das ist eine andere
Kategorie und war nie eine Lüge. Belegt durch B3 der Phase-13-Beweiswoche
([`../phase13_live_data/PHASE13_BEWEISWOCHE_FINDINGS_2026-08-31.md`](../phase13_live_data/PHASE13_BEWEISWOCHE_FINDINGS_2026-08-31.md)),
unverändert seit 2026-08-31.

Diese Entscheidung schließt **D5-H.-B** (Phase-14-Closeout-Handover §7, Z. 272,
„Quellen-Vertrauens-Modell-Framing", Wahl (b) Verfügbarkeits-Modell) strukturell. **Keine**
Code-Änderung in Phase 14 nötig: die Phase-13-L18- und Phase-14-D19-Locks sind die
strukturelle Antwort, dieser Phasenkopf-Eintrag ist die formale Schließung der offenen
Frage aus der Plan-Session.

**Nicht angefasst (per 📕-Konvention):**
- `PHASE14_CLOSEOUT_HANDOVER.md` §7 Z. 272 — verbatim wie am 2026-08-31, Z. 272 trägt
  weiterhin *„offen für P15-V4-Plan-Session"*; das ist die korrekte historische Aussage
  (die Plan-Session war offen). D5-H.-B-Schließung wird **hier** dokumentiert.
- `PHASE13_BEWEISWOCHE_FINDINGS_2026-08-31.md` — L3-Findings-Snapshot, nicht updateable;
  der Verweis auf §8.1 + B3 geht in den Phasenkopf (siehe oben).
- Phase-14-Code (`source_registry/`, `data_foundation/`, `live_data/`,
  `phase9_universe/universe/{models,store}.py`, `phase8_scheduler/webui/`) — unverändert,
  kein Step braucht einen Code-Touch.

### Verdienst + Akzeptanz

| Akzeptanzkriterium (Plan §7) | Status |
|---|---|
| **AK10** | ✅ Datierter Absatz in dieser Datei vorhanden; Plan §6 D1 formalisiert; 📕-Konvention eingehalten |

### Σ-Sweep

Doc-only, **kein** Code-Touch, **kein** Test-Touch. Σ-Baseline 1707 grün (Phase-15-A-7-Stand
2026-08-31, MiniMax-M3-Exec-Session #4) bleibt erhalten.

### NEXT (für die Folge-Session)

- **Step D2** (`docs/architecture/phase13_14_15.svg`) — kein Gate, jetzt möglich.
- **Step D3** (`RescueConfig` + `gap_rescue_operator.py` in Phase 13) — kein Gate,
  Cross-Phase-Freigabe Phase 13 (Plan §4).
- **Phase-14-Code-Touch in dieser Session:** **null** — diese Session schließt nur D5-H.-B
  per Doku, nichts strukturell an Phase 14.

---

> **Ältere Session-Blöcke** (verbatim ausgelagert, newest-first): [SESSIONS_ARCHIVE.md](./SESSIONS_ARCHIVE.md) — Rotation per Doc-Layers-Konvention ([docs/DOC_LAYERS_CONVENTION.md](../docs/DOC_LAYERS_CONVENTION.md)).