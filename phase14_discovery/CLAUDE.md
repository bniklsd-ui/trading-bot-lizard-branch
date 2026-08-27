# CLAUDE.md — Phase 14: Discovery-Then-Deterministic (`phase14_discovery/`)

> Zwei Phasen lang war „welche Quelle kann Epic X?" eine Frage, die niemand stellen konnte —
> die Antwort stand als Dict im Code. Phase 14 macht sie zu einer Zeile in der DB.
> **Quelle der Wahrheit ist der Plan + der Code, nicht dieses Dokument.**
> Vollständiger Plan: [`../docs/concepts/phase14_discovery_plan.md`](../docs/concepts/phase14_discovery_plan.md).
> Vorgeschichte: [`../phase13_live_data/PHASE13_CLOSEOUT_HANDOVER.md`](../phase13_live_data/PHASE13_CLOSEOUT_HANDOVER.md) §1.5.
> Spezial-Pläne: [`./PHASE14_C_DAEMON_CWD_BUG_PLAN.md`](./PHASE14_C_DAEMON_CWD_BUG_PLAN.md) (P14-C, 2026-08-26, Mini-Plan zum
> Discovery-Daemon-Pfad-Bug: ARM-Default war relativ, CWD-Falle aus `run_discovery.sh`);
> [`./PHASE14_D_DAEMON_SIGNAL_CAP_PLAN.md`](./PHASE14_D_DAEMON_SIGNAL_CAP_PLAN.md) (P14-D, 2026-08-26, Mini-Plan zum
> Discovery-Daemon-Signal-Response-Bug: `interval_s=3600`-Sleep verschluckt SIGTERM, analog Phase-8-POST_WINDOW).

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

> Stand: **2026-08-22 — Session 9.** Diese Tabelle wird in Block D gegen den
> As-Built-Stand gefüllt (Testzahlen aus dem finalen Sweep, nicht geschätzt).

| Datei | Zweck | Status |
|---|---|---|
| `source_registry/models.py` | `SourceAvailability`, `SourceProfile`, `Source`-Protocol, `origin`-Vokabular | ✅ A2/A3 (gelockt in Phase-13-Session 4) |
| `source_registry/store.py` | `SourceAvailabilityStore` — der einzige Zugriff auf Migration 007 | ✅ A2 |
| `source_registry/sources.py` | `IGDerivedSource`, `LSStaticSource`, `RegistryYFSource` — alle drei ohne Netz | ✅ A3 |
| `source_registry/arm.py` | Scharf-Flag `data/state/DISCOVERY_ARMED` (Muster `killswitch.py`, sichere Richtung umgedreht) | ✅ C1 (Session 9) |
| `source_registry/run.py` | Der Daemon (Muster `data_foundation/run.py`: PID-File, graceful SIGTERM, `--once`) | ✅ C2 (Session 9) |
| `scripts/run_discovery.sh` | Start-Wrapper (Muster `run_recorder.sh`) | ✅ C4 (Session 9) |
| *(cross-phase)* `phase2_persistence/migrations/007_phase14_source_availability.sql` | die Kreuzungs-Tabelle **+ der einmalige yF-Backfill aus `instrument_universe`** (der Grundbestand kommt aus der Migration, nicht aus einem Resolver-Lauf — `resolve_epic` ruft `set_symbol` in sechs von acht Pfaden nicht) | ✅ A2 |
| *(cross-phase)* `phase9_universe/universe/models.py` | `DS_STALE_SOURCE` ins Vokabular (Live-Blocker B1) | ✅ A1 |
| *(cross-phase)* `phase9_universe/universe/store.py` | yF-Projektion in `set_symbol`, nicht-fatal | ✅ A4 (Session 7) |
| *(cross-phase)* `phase13_live_data/live_data/backfill.py` | `CapitalSource.discover()` (B1b); `EPIC_MAP` raus + Symbol-Lookup rein (B2) | ✅ B1b + B2 (Session 8) |
| *(cross-phase)* `phase13_live_data/scripts/probe_capital.py` | CFD-Filter-Bug Fix: `"CFD"`-Substring → exakt `"INDICES"`; neuer Helper `_pick_index_match` für Testbarkeit | ✅ Cross-Phase-Hygiene (Session 7) |
| *(cross-phase)* `phase13_live_data/scripts/source_delta.py` | drei Fälle statt zwei (`not_available` / `available_but_empty` / `compared`) | ✅ B3 (Session 8) |
| *(cross-phase)* `phase8_scheduler/webui/api.py` + `static/` | `GET /api/discovery`, ARM/DISARM, Warn-Banner | ✅ C3 (Session 9) |
| *(cross-phase)* `phase8_scheduler/scripts/run_scheduler.sh` | Autostart-Hook für `run_discovery.sh` (analog Recorder) | ✅ C4b (Session 9) |

---

## Session stopped — 2026-08-27 (Session 15: Mini-Session — Plan-§11-Korrekturnotiz + Advisor-Tool-Restpostand-Notiz, dokumentationsdominiert, 0 Code-Edits)

> **Auftrag:** Nikinger-Chat-Handover (Do 2026-08-27, ~10:00 CEST). Priorität für
> die Folge-Session war die Auflösung der **Dokumentations-Items** aus dem
> Session-14-Morgen-Add: (1) Plan-§9-Drift-Listeneintrag #2 erweitern —
> vierfach relevant (B5 + P14-C + P14-D + Doc-Rotation-Drift aus Session 12);
> (2) Advisor-Tool-Fehler-Doku als Phase-8-Restpostand; (3) ggf. weitere
> §9-Drift-Einträge. Mini-Session-Scope: keine Code-Edits, keine Cross-Phase-
> Touches, eine atomare Doc-Einheit.

### Completed

**Plan §11 Korrekturnotiz** ([`../docs/concepts/phase14_discovery_plan.md`](../docs/concepts/phase14_discovery_plan.md)):
vier Post-Execution-Drifts als neue Sektion nach §10 dokumentiert. Konvention
folgt dem Phase-12-Praezedens (inline-Footnote in §4 + Header-Blockquote) —
*erweitert* um eine **Post-Execution-Sektion**, weil die vier Befunde alle erst
nach der Ausführung sichtbar wurden und keine D1–D20 ändern:

- **§11.1 B5** — `backfill.py:414-416` verwirft `insert_bars`-Rückgabewert.
  Code-Bug, war als „latent" markiert — **Korrekturnotiz 2026-08-27 (Session
  16)**: Fix bereits live in Commit `4681d68` (2026-08-22, Block 0.3 mit
  B3/B4/B5 gebündelt). Heute `backfill.py:649` mit korrektem
  `written += archive.insert_bars(...)` + Inline-Kommentar;
  Regressionstest `test_run_capital_backfill_counts_only_genuinely_new_rows`
  pinnt das Verhalten. **Status: ✅ gefixt + getestet.**
- **§11.2 P14-C-Befund** — Modul-Konstanten-Konvention `parents[2]` fehlte an
  einer von sechs Stellen (`arm.py:55`). **Impl-Drift zu D11**, nicht Plan-
  Konflikt. Fix bereits auf `origin/main` (Session 11, Fix-Commit `4e44b73`
  — *nicht* `2769763`, das war der Mini-Plan-Doc-Commit).
- **§11.3 P14-D-Befund** — Sleep-Cap-Konvention für Daemon-Loops fehlte in
  `run_forever`. **Impl-Drift zum Phase-8-POST_WINDOW-Hotfix** (2026-07-11).
  Fix bereits auf `origin/main` (Session 13+14, Commit `27f04d9`). Recorder-
  Daemon (Phase 12) hat denselben Bug — **Phase-15-Territorium**.
- **§11.4 Doc-Rotation-Drift** — Inline-Duplikat eines Session-Blocks im
  Phasenkopf (entdeckt + aufgeräumt in Session 13). Lehre: Pre-Commit-Hook
  oder Editor-Checklist diskutieren.

Plan-Header mit `down:`-Links auf die zwei Schwester-Mini-Pläne (P14-C,
P14-D) ergänzt, `updated:` auf 2026-08-27 gesetzt. **Snapshot-Status
unverändert** — §11 ist additiv, kein Eingriff in bestehende Inhalte.

**Advisor-Tool-Restpostand (Phase 8):** der Eintrag in
[`../phase8_scheduler/CLAUDE.md`](../phase8_scheduler/CLAUDE.md) Zeile 414
„Advisor-Tool war diese Session **nicht erreichbar** (ein Aufruf, sofortiger
Fehler, keine weiteren Details in der Tool-Antwort) — exakte Fehlermeldung
geht an den Nikinger zur eigenen Recherche" **bleibt sachlich korrekt**.
Keine Aktion nötig — der Tool-Status hat sich seit 2026-07-25 nicht
geändert (keine neue Session hat das Tool benutzt; Phase 14 lief ohne
Advisor-Session, alle P14-C/D-Punkte wurden per Code-Selbstprüfung + Live-
Verify abgenommen). **Closed Loop:** diese Mini-Session bestätigt nur, dass
der Eintrag sufficient ist. Kein Repo-Fix, kein neuer Plan — Werkzeug-
Verfügbarkeit ist Operator-Infrastruktur, nicht Phase-14-Scope.

**Rotation Session 14 → SESSIONS_ARCHIVE.md** (Doc-Layers-Konvention):
Session-14-Block (inkl. Morgen-Add-Paragraph) wandert **verbatim** an den
Anfang des Archivs; Phasenkopf trägt jetzt nur noch den neuen Session-15-
Block. Footer-Pointer bleibt. Σ-Sweep-Stand 2026-08-27 ~10:50 CEST unten
im Block dokumentiert.

### Verified

- `pytest phase14_discovery/tests -q` → **61 passed** (unverändert).
- `pytest phase13_live_data/tests -q` → **74 passed** (unverändert).
- `pytest phase12_data_foundation/tests -q` → **143 passed** (unverändert).
- `pytest phase9_universe/tests -q` → **87 passed** (unverändert).
- `pytest phase8_scheduler/tests -q` → **248 passed, 1 warning** (unverändert).
- Plan-Sektion §11 strukturell sauber: §11.1–§11.5 unter `## §11`-
  Header, keine Duplikation mit §9 Drift-Liste, Verbatim-Anker
  zeigen auf den heutigen Repo-Stand (Sessions 11/13/14, Commits
  `2769763` / `27f04d9` / `22cc688`).
- Working tree: nur Markdown-Änderungen, kein Code-Touch, kein
  Cross-Phase-Edit. Push = Nikinger-Freigabe (Working-Style-Regel,
  unverändert seit Session 11).

### Findings

🟢 **Alle vier Drifts sind bereits gefixt + live-verifiziert** — §11 ist
**deskriptiv**, nicht **präskriptiv**. Phase 14 ist **closed-in-all-but-D5**
geblieben; diese Session ändert daran nichts. Das ist das gewünschte
Ergebnis: die Korrekturnotiz dokumentiert eine **abgeschlossene**
Beweis-Kette, nicht offene Arbeit.

> **Korrekturnotiz 2026-08-27 (Mini-Session 16):** die ursprüngliche
> Erstfassung von §11 behauptete für §11.1 B5 „latent bis zum nächsten
> Cross-Phase-Touch" und für §11.2 P14-C den Doc-Commit `2769763` als
> Fix-Anker. Beides war falsch: B5 ist seit `4681d68` (2026-08-22,
> Block 0.3) gefixt + getestet; der P14-C-Fix lebt in `4e44b73` (nicht
> `2769763`, das war der Mini-Plan-Doc). Inhaltliche Aussage bleibt
> richtig (alle vier Drifts sind gefixt), Anker wurden präzisiert.

🟡 **Doc-Rotation-Hygiene ohne maschinelle Prüfung** — §11.4 hält fest,
dass die Doc-Layers-Konvention (genau ein `## Session stopped`-Block im
Phasenkopf) **nicht** automatisch geprüft wird. Empfehlung: einen
`scripts/check_doc_rotation.py` mit `grep -c` + Exit-Code als optionaler
Pre-Commit-Hook. **Nicht in dieser Session umgesetzt** — neue Datei +
neues Skript wäre eine Eigenleistung über Mini-Session-Scope.

### Unverändert offen (von Session 14)

- **D5 Closeout-Handover** — wartet auf Phase-13-Beweiswoche (Plan §7 P1–P9).
  Phase 14 bleibt **closed-in-all-but-D5**.
- **Hygiene-Tickets aus Session 4** bleibt leer.
- **Recorder-Daemon (`phase12_data_foundation/data_foundation/run.py`)** —
  derselbe theoretische Bug wie P14-D. Phase-15-Territorium (Helper-Klasse
  in einem gemeinsamen Modul, beide Daemons).
- **Phase-15-Planungs-Session**: V4-Themen (Council, Handover, Reward-Reform,
  Force-Trigger, Instinct-ECC) — gegatet auf Phase 9+11+12+13+14 + reale
  Outcomes.
- **B5-Fix (Phase-13-Code, 1 Zeile)** — ✅ bereits gefixt (`4681d68`,
  2026-08-22, Block 0.3) + Regressionstest
  (`test_run_capital_backfill_counts_only_genuinely_new_rows`).
- **Doc-Rotation-Hygiene-Hook** — Vorschlag, kein Phase-14-Scope.

### NEXT

- **Operator (Nikinger):** **Push-Freigabe** für den Docs-Commit (2 Markdown-
  Dateien, 2 Markdown-Files via Rotation). Diff ist dokumentationsdominiert,
  kein Code-Touch, kein Bot-Stop nötig. Default-Working-Style-Regel „nie
  selbst pushen" gilt weiterhin — diese Session ist **nicht** als Override-
  Variante deklariert; falls Du pushen willst, Frage-Tool wie üblich.
- **Ausführende Session (nächste):** keine Pflicht. Phase 14 bleibt
  **closed-in-all-but-D5**. Wahrscheinliche Tracks je nach Nikinger-
  Entscheidung: (a) Phase-13-Beweiswoche-Beobachtung (läuft seit Mo
  2026-08-25, separater Track); (b) Phase-15-Plan-Session (V4) — könnte
  den Recorder-Sleep-Cap-Helper als Hygiene-Atom mitnehmen (B5
  ist bereits gefixt, fällt weg); (c) Mini-Session für den
  Doc-Rotation-Hygiene-Hook (gering, aber lohnend);
  (d) Phase-12-Reconciliation-Timing-Fix für die
  `reward.recorder: no usable history row`-Vorkommen (nicht Phase-14-Scope).
- **Phase-14-Aktivität:** **closed-in-all-but-D5** — strukturell +
  operativ fertig. §11 dokumentiert Post-Execution-Drifts deskriptiv,
  ändert nichts am Phase-Status.
- **Σ-Sweep** Stand 2026-08-27 ~10:50 CEST:
  - P14 61, P13 74, P12 143, P9 87, P8 248 — Σ 613 für diese 5 Phasen
    (Σ 1698 wie in den Closeout-Handovern = alle 13 Phasen + meta)
  - Allowance (aus Session 14): 9245/10000 (7.55 % verbraucht, Mo 31.08. Roll-End)
  - Verbleibende CRITICAL-Logs seit P14-Wiring-Fix: **0** (Bestätigung
    aus Session 14 hält)
  - Recorder (Phase 12): läuft weiter (PID 4190 Sl), Daemon
    (Phase 14): läuft (PID 47174 Sl, mit P14-D-Fix), Scheduler: PID 47166

---

> **Ältere Session-Blöcke** (verbatim ausgelagert, newest-first): [SESSIONS_ARCHIVE.md](./SESSIONS_ARCHIVE.md) — Rotation per Doc-Layers-Konvention ([docs/DOC_LAYERS_CONVENTION.md](../docs/DOC_LAYERS_CONVENTION.md)).
