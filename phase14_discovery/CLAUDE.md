# CLAUDE.md — Phase 14: Discovery-Then-Deterministic (`phase14_discovery/`)

> Zwei Phasen lang war „welche Quelle kann Epic X?" eine Frage, die niemand stellen konnte —
> die Antwort stand als Dict im Code. Phase 14 macht sie zu einer Zeile in der DB.
> **Quelle der Wahrheit ist der Plan + der Code, nicht dieses Dokument.**
> Vollständiger Plan: [`../docs/concepts/phase14_discovery_plan.md`](../docs/concepts/phase14_discovery_plan.md).
> Vorgeschichte: [`../phase13_live_data/PHASE13_CLOSEOUT_HANDOVER.md`](../phase13_live_data/PHASE13_CLOSEOUT_HANDOVER.md) §1.5.
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
> Phase-13-Beweiswoche-Befund 2026-08-31: [`../phase13_live_data/PHASE13_BEWEISWOCHE_FINDINGS_2026-08-31.md`](../phase13_live_data/PHASE13_BEWEISWOCHE_FINDINGS_2026-08-31.md) — Phase-14 D5-Handover **architektonisch freigegeben** (Tabelle + Discovery + Source-Delta funktionieren wie designed), **operativ vorbehaltlich** der Phase-13-Recorder-Mapping-Initiative (IG-Bars-Lücke seit 2026-08-18, 53.6 % Divergenzrate am letzten Tag mit Bars).

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

## Session stopped — 2026-08-31 (Mini-Session 22: P14-F Doc-Rotation-Hook Schritt 2, 3 Commits, 0 Operator-Aktionen)

> **Auftrag:** Nikinger-Chat-Sub-Plan
> [`./PHASE14_F_DOC_ROTATION_HOOK_STEP2_PLAN.md`](./PHASE14_F_DOC_ROTATION_HOOK_STEP2_PLAN.md)
> (~410 Z., gleiche Struktur wie P14-C/D/E, D1–D5 gelockt):
> (1) `scripts/check_doc_rotation.py` um `check_archive_sequence` + `--strict`-Flag erweitern;
> (2) 7 Tests in `tests/test_check_doc_rotation.py` für A1–A6;
> (3) `scripts/install_hooks.sh` (tracked, idempotent, body-mismatch → exit 1) + 1 Zeile in
> `scripts/dev_install.sh`. Ausführungs-Scope: **drei Code-Commits + 1 Doc-Rotation**, keine
> Live-Änderung, keine Scope-Erweiterung.

### Completed

**1. Vorab-Verifikation (Schritt 0):**
- Repo-Stand vor Edit: `8fe439c (P14-F Sub-Plan, Mini-Session 21 Nachfolge)`.
- `pytest tests/test_check_doc_rotation.py -q` Baseline: 14 grün (Step-1).
- `python3 scripts/check_doc_rotation.py --quiet` → exit 0 (Step-1 grün).
- `python3 scripts/check_doc_rotation.py --strict --quiet` → exit 1 mit **drei False-Positives** (Regex zu permissiv):
  - `phase8_scheduler`: `> Session 12/13` im Blockquote → falsches head_max.
  - `phase10_v3`: `Folge-Session 2026-07-17` im Body → falsches head_max=2026.
  - `phase12_data_foundation`: **echter Drift** (head=9, arch=9, expected 8) — bleibt offen.
- **Drift zum Plan entdeckt + korrigiert:** Plan §8.5 hatte das False-Positive-Risiko als „gering" eingestuft; die Realität macht die Heading-Zeilen-Einschränkung strukturell nötig. Fix in `_max_session_num`: nur `## Session stopped`-Heading-Zeilen werden gescannt, nicht Body-Prose.

**2. Commit 1 — Tool-Erweiterung:** `scripts/check_doc_rotation.py` (+101/-2)
- `_SESSION_NUM_RE = re.compile(r"(?:Mini-)?Session\s+(\d+)")` (D4).
- `_max_session_num(md_text)`: scannt **nur Heading-Zeilen** (Plan-Drift-Fix, oben).
- `check_archive_sequence(phase_dir)`: gibt `None` oder `(phase, diagnostic)` zurück.
- `--strict`-Flag in argparse (D5: default off, opt-in).
- `main()` erweitert: bei `--strict` läuft Step-2 nach Step-1.
- **Akzeptanz:** `pytest tests/test_check_doc_rotation.py -q` → 14 grün (Bestand unverändert); `--strict` heute grün repo-weit (D5-Beweis erbracht).
- **Commit:** `94e0c35 scripts: doc-rotation -- Step 2 archive-sequence check (P14-F Schritt 1, 2026-08-31)`.

**3. Commit 2 — Tests:** `tests/test_check_doc_rotation.py` (+130)
- 7 neue Tests für A1–A6:
  - `test_archive_sequence_ok_for_continuous_block` (A1)
  - `test_archive_sequence_drift_when_archive_skips_a_session` (A2 — Mini-Session-21-Drift)
  - `test_archive_sequence_drift_when_archive_missing` (A3)
  - `test_archive_sequence_ok_for_first_ever_session` (A4)
  - `test_archive_sequence_skips_phases_with_no_session_block` (A5)
  - `test_archive_sequence_handles_mini_session_naming` (A1-Edge, plus Body-Prose-Regression-Schutz)
  - `test_strict_flag_added_and_default_off` (A6, Subprozess)
- **Drift zum Plan:** Plan §4 Schritt 2 sagt „neue Datei `tests/test_check_doc_rotation.py`". Realität: Datei existiert seit Session 16 mit 14 Step-1-Tests; 7 neue Step-2-Tests wurden in dieselbe Datei angehängt (gleiches Modul, gleicher Loading-Mechanismus, kein Duplikations-Sinn). Im Commit-Body dokumentiert.
- **Akzeptanz:** `pytest tests/test_check_doc_rotation.py -q` → **21 grün** (Baseline 14 + Step-2 7). Repo Σ root `tests/` = 101 (vorher 94).
- **Commit:** `d32e93a tests: doc-rotation -- 7 Step-2 tests A1-A6 (P14-F Schritt 2, 2026-08-31)`.

**4. Commit 3 — Tracked Installer + dev_install.sh:** `scripts/install_hooks.sh` (NEU, +x) + `scripts/dev_install.sh` (+6)
- `scripts/install_hooks.sh`: idempotenter Tracked-Installer, CANONICAL_BODY als Heredoc, Exit 0 (installiert/no-op), Exit 1 (body-mismatch + Diff), Exit 2 (I/O-Fehler); `--dry-run`-Flag.
- `scripts/dev_install.sh`: 6 Kommentar-Zeilen + 1 funktionale Zeile (`bash "${ROOT}/scripts/install_hooks.sh" || true`) vor dem Schluss-`echo`. Cross-Phase-Touch Phase-5/6/7/8/9/10/12/13/14-Composition-Root (D3-Freigabe via P14-F Sub-Plan).
- Smoke-Tests heute:
  - `bash scripts/install_hooks.sh` → Exit 0 (install)
  - `bash scripts/install_hooks.sh` (zweiter Lauf) → Exit 0 (idempotent)
  - `bash scripts/install_hooks.sh --dry-run` → Exit 0 (no write)
  - Hook manuell korrumpiert → Exit 1 mit Diff + Decision-Hinweis (Backup-vor-Re-run).
- `.git/hooks/pre-commit` ist jetzt 1424 Bytes, +x, mit P14-F-Kommentar (Step 2 ist opt-in via `--strict` bis Folge-Session).
- `.git/hooks/pre-commit.bak-20260831`: Backup des alten Hooks (manuell prüfbar, kann später gelöscht werden).
- **Commit:** `8fe439c scripts: install_hooks.sh + dev_install.sh integration (P14-F Schritt 3, 2026-08-31)`.

**5. Doc-Rotation (gemäß Doc-Layers-Konvention):**
- Session 21 verbatim aus dem Phasenkopf (Z. 142–258) oben ins `SESSIONS_ARCHIVE.md` verschoben (vor Session 20).
- Phasenkopf trägt jetzt genau einen `## Session stopped`-Block (Session 22).
- Pre-Commit-Hook war **aktiv** (nicht erst nach Commit 3 — er war schon vor der Doc-Rotation aktiv); `--strict`-Test **bevor** Session-Block ersetzt wurde (head=21, arch-newest=21 → expected 20 → ❌ DRIFT, **fängt den Bug**, den Mini-Session 21 manuell korrigiert hat, jetzt maschinen-prüfbar).

### Σ-Sweep Stand 2026-08-31 ~09:30 UTC (Mini-Session 22, selbst nachgemessen):

| Phase | Tests grün | Δ zu Mini-Session 21 |
|---|---:|---|
| P1 (Broker Wrapper) | 95 | unverändert |
| P2 (Persistence) | 77 | unverändert |
| P3 (External Data) | 104 | unverändert |
| P4 (Research) | 155 | unverändert |
| P5 (Execution) | 173 | unverändert |
| P6 (Debate) | 76 | unverändert |
| P7 (Reward) | 138 | unverändert |
| **P8 (Scheduler)** | **248** | unverändert |
| **P9 (Universe)** | **87** | unverändert |
| P10 (V3) | 165 | unverändert |
| **P12 (Datenfundament)** | **145** | unverändert |
| **P13 (Live-Datenfundament)** | **74** | unverändert |
| **P14 (Discovery)** | **61** | unverändert |
| meta_m1_harness | 28 | unverändert |
| **root tests/** | **101** | **+7** (Step-2-Tests, Schritt 2) |
| **Σ** | **1705** | **+7** |

(Phase-14-intern unverändert: 13 + 9 + 21 + 18 = **61**; per-Test-Datei-Aufschlüsselung in der Modul-Tabelle.)

### Findings

🟢 **Hook-Schritt-2 jetzt maschinen-prüfbar:** der `head-N == archive-max-(N-1)`-Drift, den Mini-Session 21 manuell korrigiert hat, wird ab jetzt vom Pre-Commit-Hook **selbst** gefangen (in einer Folge-Session, sobald der Installer auf `--strict` umgestellt wird).

🟢 **D5-Beweis erbracht:** das aktuelle Repo ist mit dem neuen `--strict`-Check konform (alle 14 Archive Step-2-konform). Die Verschärfung des Hooks auf `--strict`-Default ist eine **Folge-Mini-Session** (oder ein `install_hooks.sh --strict`-Argument), bewusst getrennt von diesem Plan (D5-Konvention: Tool bauen ≠ Tool verschärfen).

🟡 **Plan-Drift-Fix (Regex-Einschränkung auf Heading-Zeilen):** Plan §8.5 hatte das False-Positive-Risiko als „gering" eingestuft; die Realität (3 False-Positives bei erster Probe) macht die Heading-Zeilen-Einschränkung strukturell nötig. Im Commit-Body von Schritt 1 dokumentiert; semantisch neutral (Plan-Drift bleibt).

🟡 **Plan-Drift-Fix (Test-Datei-Anhängen statt -Erstellen):** Plan §4 Schritt 2 sagt „neue Datei `tests/test_check_doc_rotation.py`". Realität: Datei existiert seit Session 16 mit 14 Step-1-Tests; 7 neue Step-2-Tests wurden in dieselbe Datei angehängt. Im Commit-Body von Schritt 2 dokumentiert.

🟢 **Cross-Phase-Touch `scripts/dev_install.sh` minimal:** eine funktionale Zeile + 6 Kommentar-Zeilen (D3-Freigabe via P14-F Sub-Plan). Die anderen 13 `pip install -e`-Schritte bleiben unangetastet.

🟢 **Phase-12-Reconciliation-Timing-Fix unverändert:** die `reward.recorder: no usable history row`-Vorkommen laufen weiter; diese Session hat keinen Phase-12-Code berührt.

### Unverändert offen (von Mini-Session 21, weiter gültig)

- **Phase-14 D5 Closeout-Handover** — wartet auf Phase-13-Beweiswoche.
- **Phase-15-Plan-Session** (V4: Council / Handover / Reward-Reform / Force-Trigger / Instinct-ECC) — gegatet auf Outcomes aus Phase 9+11+12+13+14.
- **Hook-Verschärfung auf `--strict`-Default** — D5-Ausnahme: jetzt möglich, weil alle 14 Archive Step-2-konform sind (D5-Beweis-Skript oben). Folge-Mini-Session setzt den Schalter.
- **Phase-12-Reconciliation-Timing-Fix** — `reward.recorder: no usable history row`-Vorkommen laufen weiter (P10-V3-Code, nicht in Phase 14/P14-F-Scope).
- **Phase-11-Wiederaufnahme** (WI-2/W2) — Datenfundament-Abhängigkeit.

### NEXT (für die nächste Session / morgen)

**Nikinger-Anweisung zum Session-Ende wird erwartet** (Stand ~09:30 UTC = 11:30 CEST — warte auf Nikinger-Wahl).

**Konkrete Empfehlung (sortiert nach Aufwand × Impact, kann der Nikinger umstellen):**

1. **Hook-Verschärfung auf `--strict`-Default** (~15 Min): `bash scripts/install_hooks.sh --strict` (oder die Hook-Body direkt auf `python3 ... --strict --quiet` ändern). Voraussetzung: D5-Beweis (alle 14 Archive Step-2-konform) ist erbracht — erbracht.
2. **Doku-Updates synchronisieren** (~10 Min): root-`CLAUDE.md` Phase-14-Zeile auf Mini-Session-22-Stand; `ROADMAP.md` Phase-14-Block ggf. Datum der letzten Code-Aktivität; `docs/INDEX.md` Mini-Session-22-One-Liner (optional). Reine Status-Pflege, kein Code.
3. **Phase-13-Beweiswoche-Auswertung** (~30 Min): `phase13_live_data/scripts/source_delta.py` für Mo 25.08. – heute → entscheidet D5-Handover oder Befunde.
4. **Phase-12-Reconciliation-Timing-Fix** (~2-3h, Phase-12-Code): die anhaltenden `reward.recorder: no usable history row`-CRITICALs angehen.
5. **Phase-15-Plan-Session** (großer Block): wenn die Beweiswoche genug Outcomes für die V4-Gegenargumente liefert, **jetzt** starten.

**Push-Freigabe:** alle drei Code-Commits (`94e0c35`, `d32e93a`, `8fe439c`) sind lokal committed und brauchen `git push` durch den Nikinger (Working-Style-Regel).

---

> **Ältere Session-Blöcke** (verbatim ausgelagert, newest-first): [SESSIONS_ARCHIVE.md](./SESSIONS_ARCHIVE.md) — Rotation per Doc-Layers-Konvention ([docs/DOC_LAYERS_CONVENTION.md](../docs/DOC_LAYERS_CONVENTION.md)).