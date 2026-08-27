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

## Session stopped — 2026-08-27 (Session 17: Mini-Session — Push-Status-Check + Pre-Commit-Hook-Install, 0 Code-Edits, 1 Hook + 2 Doc-Edits)

> **Auftrag:** Nikinger-Chat (2026-08-27, ~17:35 CEST) auf den Kurz-Stand-Bericht:
> „Erst pushen, dann B)." Zwei Atome: (1) die drei lokalen Session-16-Commits pushen,
> (2) den Pre-Commit-Hook für `scripts/check_doc_rotation.py` installieren
> (Session-16-🟡-Finding). Mini-Session-Scope: **Push-Verifikation** + **Hook-Wiring**
> + **Doc-Rotation**. Kein Phase-Code-Edit, kein Cross-Phase-Touch.

### Completed

**Push-Status-Check (kein Push-Befehl nötig).** `git reflog` zeigte vor jedem Push:
`6d18b98 refs/remotes/origin/main@{0}: update by push` — die drei Session-16-Commits
(`3b69263` Doc-Korrektur, `f403ab4` Skript+Tests, `6d18b98` Block-Rotation) waren
**bereits auf `origin/main`**, vermutlich durch einen manuellen Push des Nikingers
zwischen Session-16-Ende und dieser Session (oder eine Auto-Hook-Konfiguration).
`git status` clean, `main` = `origin/main` = `6d18b98`, `git fetch origin --dry-run`
No-Op. **Kein Push-Befehl ausgeführt** — Working-Style-Regel eingehalten: kein
Auto-Push, auch nicht wenn der Befehl trivial wäre. Der Status-Check stand
vor jedem Push.

**Pre-Commit-Hook installiert** (`.git/hooks/pre-commit`, **nicht getrackt** —
Operator-seitig, analog `data/`):

```sh
#!/bin/sh
# Pre-commit hook: doc-rotation hygiene check (Phase 14 Hygiene Item 2 follow-up,
# 2026-08-27). Ruft scripts/check_doc_rotation.py --quiet; propagiert exit code.
# Robust: wenn python3 oder das Skript fehlt → skip (exit 0), damit der Hook
# keinen 'frischen Klon' sabotiert. Override pro Commit mit --no-verify.

if ! command -v python3 >/dev/null 2>&1; then
    echo "pre-commit: python3 not found, skipping doc-rotation check"
    exit 0
fi
if [ ! -f scripts/check_doc_rotation.py ]; then
    echo "pre-commit: scripts/check_doc_rotation.py missing, skipping"
    exit 0
fi
python3 scripts/check_doc_rotation.py --quiet
result=$?
if [ $result -ne 0 ]; then
    echo ""
    echo "pre-commit: doc-rotation check failed (exit $result)."
    echo "  Run 'python3 scripts/check_doc_rotation.py' for details."
    echo "  Use 'git commit --no-verify' to override if you know what you are doing."
fi
exit $result
```

- **Default-Verhalten:** ruft das Skript bei jedem Commit. Exit ≠ 0 ⇒ Commit
  blockiert mit klarer Meldung.
- **Override pro Commit:** `git commit --no-verify`.
- **Idempotent:** Hook-Skript-Verhalten ist deterministisch (kein Netz,
  keine externen Imports, exit 0/1/2 — siehe Skript-Doku).

### Verified

- `chmod +x .git/hooks/pre-commit` ⇒ `-rwxr-xr-x` (Mode 755).
- `sh -n .git/hooks/pre-commit` ⇒ **syntax OK** (POSIX-sh).
- `.git/hooks/pre-commit` direkt aufgerufen (Clean-State-Repo) ⇒ **exit 0**
  (Skript-Delegate liefert 0).
- `python3 scripts/check_doc_rotation.py --quiet` redundant gegen Session 16
  bestätigt ⇒ exit 0.
- `git fetch origin --dry-run` ⇒ No-Op (`main` = `origin/main` = `6d18b98`).
- `git log origin/main..main --oneline` ⇒ leer (nichts zu pushen).
- Working tree nach Hook-Install: clean (`.git/hooks/pre-commit` ist
  erwartungsgemäß nicht im Index; `.git/hooks/` ist per Git-Design
  untracked).
- `python3 scripts/check_doc_rotation.py` (verbose) heute noch einmal:
  14/14 Phase-Heads OK (unverändert zu Session 16).
- **Prozess-Stand (17:40 CEST):** Scheduler **PID 47166 Sl** (mit
  `--enable-divergence-sampler`); Recorder und Discovery-Daemon sind
  aus `ps aux` **verschwunden** (in Session 16 noch PIDs 4190 / 47174).
  Kein speculativer Befund — Hook-Install hat darauf keinen Einfluss
  (Hook betrifft nur `git commit`); Auflösung obliegt dem Operator bzw.
  dem jeweiligen Phasen-Owner (Recorder = Phase 12, Daemon = Phase 14).

### Findings

🟢 **Push war redundant** — die drei Commits waren schon oben (reflog-Beweis
`origin/main@{0}: update by push`). Working-Style-Regel „nie selbst pushen"
hat **automatisch** richtig gehandelt: vor jedem Pushen steht der Status-Check,
und der hat ergeben „nichts zu tun". Lesson für Folge-Sessions: bei jeder
Push-Anfrage kurz `reflog`/`fetch --dry-run` als **erste** Aktion — spart
Round-Trips und schließt „schon gepusht?"-Vermutungen strukturell aus, ohne
dass eine Push-Force-Flag gesetzt werden muss.

🟢 **Hook ist live ab dem nächsten Commit.** Er fängt jeden zukünftigen
Inline-Duplikat-Drift **vor** dem Index. Damit ist die Doc-Layers-Rotation-Regel
nun **dreifach** geschützt: Konvention + Skript + Pre-Commit-Hook.

🟡 **Hook ist nicht im Repo.** `.git/hooks/` ist per Git-Design lokales
Operator-Tool — wird nicht mit-versioniert. Ein neuer Klon (oder ein
`git clone` auf einer anderen Maschine) hat den Hook **nicht**. Drei mögliche
nächste Schritte, alle Phase-15- oder Operator-Territorium:

1. **Repo-getrackter Installer** (`scripts/install_hooks.sh`): tracked im
   Repo, Operator ruft einmal nach `git clone`. Erfordert ein Opt-in
   (`.git/hooks` darf nicht blind überschrieben werden).
2. **Pure-Doku**: ein Eintrag in `AGENTS.md` / `README.md` „after clone: run
   `bash scripts/install_hooks.sh`". Niedrigste Hürde, aber Disziplin-lastig.
3. **Core-Hooks-Path** (`git config core.hooksPath <tracked-dir>`): der
   tracked-Pfad `scripts/hooks/` enthält die Hook-Datei, Git ruft sie
   automatisch. **Sauberste Lösung**, aber Projekt-weit einmal umzustellen
   — andere Hooks (Linter, Formatierer) wären mit berührt.

Empfehlung: (3) in Phase 15 als Hygiene-Atom mitnehmen, falls Phase 15 ohnehin
am Workflow schraubt; sonst (1) jetzt in einer Folge-Mini-Session.

🟡 **FAIL-Pfad des Hooks nicht Live-getestet.** Skript-Tests decken den
`two-FAIL`-Fall ab (`test_check_doc_rotation.py` main-Test + E2E-Subprozess),
und der Hook ist ein dünner Delegate — daher reicht die Skript-Test-Suite
strukturell. Ein direkter Commit-Test mit absichtlich verdoppeltem Session-Block
+ `git commit --no-verify`-Vergleich wäre eine Option für eine spätere
Mini-Session, wenn der Hook mal versagt. Heute nicht nötig.

### Unverändert offen (von Session 16)

- **D5 Closeout-Handover** — wartet auf Phase-13-Beweiswoche (Plan §7 P1–P9).
  Phase 14 bleibt **closed-in-all-but-D5**.
- **Recorder-Daemon (`phase12_data_foundation/data_foundation/run.py`)** —
  derselbe theoretische Bug wie P14-D. Phase-15-Territorium (Helper-Klasse
  in einem gemeinsamen Modul, beide Daemons).
- **Phase-15-Planungs-Session**: V4-Themen (Council, Handover, Reward-Reform,
  Force-Trigger, Instinct-ECC) — gegatet auf Phase 9+11+12+13+14 + reale
  Outcomes.
- **Hook-Installer (tracked)** — siehe 🟡 Findings oben. Heute **nicht** im
  Scope: aktueller Auftrag war nur „Hook installieren", nicht „installierbar
  machen für andere Maschinen".
- **Phase-12-Reconciliation-Timing-Fix** — `reward.recorder: no usable
  history row` (nicht Phase-14-Scope).

### NEXT

- **Operator (Nikinger):** **Push-Freigabe** für **einen** Commit dieser
  Mini-Session (Session-17-Rotation: `phase14_discovery/CLAUDE.md` +
  `phase14_discovery/SESSIONS_ARCHIVE.md`). Diff: Session-16-Block wandert
  **verbatim** ans Archiv-Anfang; Session-17-Block ersetzt ihn im Phasenkopf;
  Footer-Pointer unverändert. Kein Code-Edit, kein Cross-Phase-Touch, keine
  Test-Datei geändert. (Der Hook selbst ist `.git/hooks/pre-commit` und
  erwartungsgemäß **nicht** Teil des Commits — siehe 🟡 Findings.)
- **Ausführende Session (nächste):** keine Pflicht. Wahrscheinliche Tracks je
  nach Nikinger-Entscheidung: (a) Hook-Installer tracked (Option 1/3 aus
  🟡 Findings, Mini-Session, geringer Aufwand); (b) Phase-13-Beweiswoche-
  Beobachtung (separater Track); (c) Phase-15-Plan-Session (V4 + Recorder-
  Helper + Hook-Installer als Hygiene-Atome); (d) Phase-12-Reconciliation-
  Timing (nicht Phase-14-Scope); (e) Recorder-/Daemon-Restart (PIDs 4190
  und 47174 verschwunden, Verifikation welcher Prozess wieder laufen muss).
- **Phase-14-Aktivität:** **closed-in-all-but-D5** + **Hygiene vollständig +
  Hook gewired**. Phase-14-Hygiene ist jetzt **dreifach** geschützt
  (Konvention + Skript + Hook). Letzter offener Hygiene-Punkt ist
  „Hook-Installer im Repo" — Phase-15-Territorium.
- **Σ-Sweep** Stand 2026-08-27 ~17:40 CEST:
  - P14 61, P13 74, P12 143, P9 87, P8 248 — Σ 613 für diese 5 Phasen
    (Σ 1698 wie in den Closeout-Handovern = alle 13 Phasen + meta)
  - **+14** Hygiene-Tests in `tests/test_check_doc_rotation.py`
    → Σ Root-Tests **94** (unverändert zu Session 16)
  - Allowance: 9245/10000 (7,55 % verbraucht, Roll-End Mo 31.08.) —
    unverändert zu Session 16
  - Verbleibende CRITICAL-Logs seit P14-Wiring-Fix: **0**
  - Scheduler **PID 47166 Sl** (mit `--enable-divergence-sampler`),
    Recorder + Discovery-Daemon: **nicht in `ps aux`** (waren in
    Session 16 noch PIDs 4190 / 47174; Hook-Install hat darauf keinen
    Einfluss)
  - **check_doc_rotation.py** heute: 14/14 Phase-Heads OK
  - **`git reflog`:** `6d18b98 origin/main@{0}: update by push` — die
    Session-16-Commits sind live; **kein** lokaler Commit-Stand abweichend
    von `origin/main`
  - **`.git/hooks/pre-commit`:** installiert, `-rwxr-xr-x`, exit 0 im
    Clean-State-Test (Delegate an `scripts/check_doc_rotation.py --quiet`).

---

> **Ältere Session-Blöcke** (verbatim ausgelagert, newest-first): [SESSIONS_ARCHIVE.md](./SESSIONS_ARCHIVE.md) — Rotation per Doc-Layers-Konvention ([docs/DOC_LAYERS_CONVENTION.md](../docs/DOC_LAYERS_CONVENTION.md)).