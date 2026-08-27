# SESSIONS_ARCHIVE.md — Phase 14 (Discovery-Then-Deterministic)

Newest-first. Rotation rule (root `CLAUDE.md`, mandatory since 2026-07-06): the phase head
carries exactly one `## Session stopped` block; the previously-newest block moves here
verbatim when a new one is appended.


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



## Session stopped — 2026-08-27 (Session 16: Mini-Session — Phase-14-nahe Hygiene [Doc-Rotation-Hook], Code+Tests+Doc-Korrektur)


> **Auftrag:** Nikinger-Antwort auf den Session-15-NEXT-Block: „Die Phase 14
> Nahe Hygiene bitte." Zwei Items auf der Liste: (1) B5-Fix
> (`backfill.py:414-416` `insert_bars`-Return-Verwurf) und (2)
> Doc-Rotation-Hygiene-Hook (`scripts/check_doc_rotation.py`).
> **Erste Entdeckung:** B5 ist **bereits gefixt** (Commit `4681d68`,
> 2026-08-22, Block 0.3 mit B3/B4/B5 gebündelt, Inline-Kommentar in
> `backfill.py:645-648` zeigt explizit auf B5, Regressionstest
> `test_run_capital_backfill_counts_only_genuinely_new_rows` pinnt das
> Verhalten). **Item 1 fällt weg** — kein Code-Edit nötig. Stattdessen:
> Doc-Korrektur für die Session-15-Erstfassung (die §11.1 + §11.2 mit
> falschen Ankern geschrieben hatte). Item 2 (Doc-Rotation-Hook) wird
> gebaut. Mini-Session-Scope: **drei Atome** — Doc-Korrektur (Phase-14-
> plan.md + CLAUDE.md + INDEX.md) + Skript+Tests (scripts/ + tests/) +
> Session-Block-Rotation. Working-Style „Push fragt der Nikinger frei".

### Completed

**Doc-Korrektur (Commit `3b69263`)** — Working-Style-Regel „Code > Doc"
angewendet. Die Session-15-Erstfassung hatte **zwei** Anker-Drift
erzeugt:

- **§11.1 B5:** behauptete „latent bis zum nächsten Cross-Phase-Touch" —
  **falsch**. Der Fix lebt seit `4681d68` (2026-08-22), Inline-Kommentar
  in `backfill.py:645-648` (explizit „Phase-14 finding B5"), Regressionstest
  `test_run_capital_backfill_counts_only_genuinely_new_rows`
  (`test_capital_backfill_script.py:169-200`) pinnt das Verhalten.
  §11.1 wurde komplett umgeschrieben mit Korrekturnotiz-Header (2026-08-27,
  Mini-Session 15+16); Code-Snippet zeigt jetzt `backfill.py:644-649` (heute).
- **§11.2 P14-C-Befund:** verwies auf Commit `2769763` als Fix-Anker — **falsch**.
  `2769763` ist der Mini-Plan-Doc-Commit. Der Fix lebt in `4e44b73`
  (2026-08-26, Session 11, Code+Tests). Inhaltliche Aussage bleibt richtig
  (Fix ist live); Anker präzisiert + Korrekturnotiz-Block angehängt.

  CLAUDE.md-Session-15-Block: Findings-Sektion „Drei der vier Drifts
  sind gefixt" → „Alle vier Drifts sind gefixt"; Unverändert-offen-Liste
  B5-Fix-Eintrag „latent" → „✅ bereits gefixt"; NEXT-Block Track (b)
  „B5-Fix als Hygiene-Atom mitnehmen" gestrichen. docs/INDEX.md
  Plan-Entry mit §11-Korrekturnotiz-Marker erweitert.

**Doc-Rotation-Hygiene-Hook (Commit `f403ab4`)** — strukturelle Antwort
auf den Session-12-Befund (§11.4 Korrekturnotiz: „die Doc-Layers-Rotation-
Regel war dokumentiert, aber nicht maschinen-prüfbar. Inline-Duplikate
von Session-Blöcken rutschten durchs Review"). Skript macht es prüfbar:

`scripts/check_doc_rotation.py` (~115 Zeilen, kein Netz, keine externen
Imports, exit codes 0/1/2):
- `count_session_blocks(md_text)` — reine Zähl-Funktion. Ignoriert
  Inline-Matches im Footer-Block (Quote-Paragraph, kein H2).
- `check_phase(phase_dir)` — `(count, label)`; `0` für fehlende `CLAUDE.md`.
- `main()` — iteriert über `PHASE_DIRS` (14 aktive/geschlossene Phasen
  + `meta_m1_harness`), sammelt Verstöße, `exit 1` wenn `count > 1`.
- CLI: `--phase NAME` (repeatable, Restrict), `--quiet` (OK-Zeilen
  unterdrücken, Failures weiter gedruckt).
- Regel: „at most one", nicht „exactly one" — virgin Phases (z. B.
  `phase2_persistence`, kein Archiv, kein History) bleiben mit 0 OK.

`tests/test_check_doc_rotation.py` (14 Tests, alle grün):
- 5 Pure-Tests (count_session_blocks: leer / no-heading / one /
  two-inline-duplicate / inline-match-im-Footer-ignoriert).
- 3 check_phase-Tests (fehlt / 0 / 1).
- 3 main-Tests mit `tmp_path` + `monkeypatch` (zero-OK / one-OK /
  two-FAIL) + `--quiet`-Suppress-Test.
- 2 End-to-End-Tests gegen das Live-Repo (`main()` + Subprocess-Aufruf).

Convention: phase-less Skript, geladen via
`importlib.util.spec_from_file_location` (gleiches Muster wie
`test_verify_instrument.py` / `test_resolve_epics.py` — root `scripts/`
ist absichtlich **kein** Package, weil die Phasen bereits auf
`scripts.wiring` kollidieren würden).

**Rotation Session 15 → SESSIONS_ARCHIVE.md** (Doc-Layers-Konvention):
Session-15-Block (inkl. der inzwischen angebrachten §11.1/§11.2-
Korrekturnotiz-Header) wandert **verbatim** an den Anfang des Archivs;
Phasenkopf trägt jetzt nur noch den Session-16-Block. Footer-Pointer
bleibt. Σ-Sweep-Stand 2026-08-27 ~13:30 CEST unten im Block dokumentiert.

### Verified

- `pytest phase14_discovery/tests -q` → **61 passed** (unverändert).
- `pytest phase13_live_data/tests -q` → **74 passed** (unverändert).
- `pytest phase12_data_foundation/tests -q` → **143 passed** (unverändert).
- `pytest phase9_universe/tests -q` → **87 passed** (unverändert).
- `pytest phase8_scheduler/tests -q` → **248 passed, 1 warning** (unverändert).
- `pytest tests/test_check_doc_rotation.py -v` → **14 passed** (NEU).
- `pytest tests -q` → **94 passed** (war 80, **+14** neue Hygiene-Tests).
- `python3 scripts/check_doc_rotation.py --quiet` → **exit 0**.
- `python3 scripts/check_doc_rotation.py` (verbose) → alle 14 Phase-Heads
  OK: 1× virgin (phase2_persistence), 13× canonical (1 Block).
  **Null** Drift im Live-Repo.
- `grep "^## Session stopped" phase14_discovery/CLAUDE.md` → **1**
  (canonical), `.count_session_blocks(...) == 1`.
- Working tree nach Commits `3b69263` + `f403ab4`: clean (außer `data/`
  untracked, gitignored). **Drei** Commits in dieser Session geplant
  (Doc-Korrektur + Skript+Tests + Session-Block-Rotation, alle lokal;
  Push = Nikinger-Freigabe).

### Findings

🟢 **Item 1 (B5-Fix) erledigt durch Entdeckung** — der Fix existierte
seit 2026-08-22 (`4681d68`), ich hatte es in Session 15 nur nicht
bemerkt. Die Doc-Korrektur in dieser Session macht den Drift sichtbar
und bringt das Doc in Übereinstimmung mit dem Code. **Lesson:**
bei zukünftigen „latent"-Aussagen erst `grep`/`git log` checken, dann
schreiben.

🟢 **Item 2 (Doc-Rotation-Hook) gebaut + getestet + grün gegen Live-Repo**
— strukturelle Antwort auf §11.4. Heute fängt jeder zukünftige
Inline-Duplikat-Drift das Skript + den End-to-End-Test, **bevor** er
committed werden kann. Die Regel ist jetzt **doppelt** geschützt:
maschinen-prüfbar (Skript) + dokumentiert (Doc-Layers-Konvention).

🟡 **„at most one" statt „exactly one"** — bewusste Lockerung der Regel
im Skript, weil Phase 2 (Persistence) legitimerweise 0 Session-Blöcke hat
(„no archive — no history"). Die strikte „exactly one"-Lesart hätte
einen Fehlalarm geworfen. **Regel-Drift im Skript korrekt:** das Skript
konsumiert die Regel, nicht definiert sie — `docs/DOC_LAYERS_CONVENTION.md`
sagt „exactly one session block" im Rotation-Kontext (nach dem ersten
Append); Phase 2 hat nie appended.

🟡 **Pre-Commit-Hook nicht gewired** — das Skript ist gebaut + grün,
aber **nicht** als Pre-Commit-Hook in `.git/hooks/pre-commit` o. ä.
installiert. Empfehlung: beim Phase-15-Setup (oder einer kleinen
Folge-Session) einen `pre-commit`-Hook installieren, der das Skript
aufruft. **Bewusst nicht in dieser Session** — Hook-Installation ist
Operator-Sache (Nikinger-Call), nicht Phase-14-Scope.

### Unverändert offen (von Session 15)

- **D5 Closeout-Handover** — wartet auf Phase-13-Beweiswoche (Plan §7 P1–P9).
  Phase 14 bleibt **closed-in-all-but-D5**.
- **Hygiene-Tickets aus Session 4** bleibt leer.
- **Recorder-Daemon (`phase12_data_foundation/data_foundation/run.py`)** —
  derselbe theoretische Bug wie P14-D. Phase-15-Territorium (Helper-Klasse
  in einem gemeinsamen Modul, beide Daemons).
- **Phase-15-Planungs-Session**: V4-Themen (Council, Handover, Reward-Reform,
  Force-Trigger, Instinct-ECC) — gegatet auf Phase 9+11+12+13+14 + reale
  Outcomes.
- **Doc-Rotation-Hook als Pre-Commit-Hook** — Skript gebaut, Hook-Installation
  offen (siehe 🟡 Findings oben).

### NEXT

- **Operator (Nikinger):** **Push-Freigabe** für **drei** Commits dieser
  Mini-Session: `3b69263` (Doc-Korrektur, 3 Files +59/−29) +
  `f403ab4` (Skript + Tests, 2 Files +365) + den Session-16-Block-Rotation-
  Commit (2 Files, +X/−Y klein). Diff ist dokumentationsdominiert +
  1 Hygiene-Skript mit voller Test-Suite; kein Cross-Phase-Edit (das
  Skript lebt unter `scripts/` + `tests/`, beide root-level, kein
  Phase-Package angefasst). Default-Working-Style-Regel „nie selbst
  pushen" gilt weiterhin — diese Session ist **nicht** als Override-
  Variante deklariert; falls Du pushen willst, Frage-Tool wie üblich.
- **Ausführende Session (nächste):** keine Pflicht. Phase 14 bleibt
  **closed-in-all-but-D5** + **Phase-14-Hygiene jetzt vollständig**
  (alle vier Items aus dem Session-15-NEXT-Block abgearbeitet oder als
  nicht-nötig geschlossen). Wahrscheinliche Tracks je nach Nikinger-
  Entscheidung: (a) Phase-13-Beweiswoche-Beobachtung (läuft seit Mo
  2026-08-25, separater Track); (b) Phase-15-Plan-Session (V4 — könnte
  den Recorder-Sleep-Cap-Helper als Hygiene-Atom mitnehmen);
  (c) Mini-Session für den Doc-Rotation-Pre-Commit-Hook-Install (gering);
  (d) Phase-12-Reconciliation-Timing-Fix für die
  `reward.recorder: no usable history row`-Vorkommen (nicht Phase-14-Scope).
- **Phase-14-Aktivität:** **closed-in-all-but-D5** + **Hygiene vollständig**
  — §11 dokumentiert Post-Execution-Drifts deskriptiv; Doc-Korrektur
  in dieser Session hat §11.1/§11.2-Anker präzisiert; Doc-Rotation-Hook
  ist die strukturelle Antwort auf §11.4. Phase-14 ist jetzt **doppelt**
  abgesichert (Doc-Konvention + maschinen-prüfbar).
- **Σ-Sweep** Stand 2026-08-27 ~13:30 CEST:
  - P14 61, P13 74, P12 143, P9 87, P8 248 — Σ 613 für diese 5 Phasen
    (Σ 1698 wie in den Closeout-Handovern = alle 13 Phasen + meta)
  - **+14** neue Hygiene-Tests in `tests/test_check_doc_rotation.py`
    → Σ Root-Tests jetzt **94** (war 80)
  - Allowance (aus Session 14): 9245/10000 (7.55 % verbraucht, Mo 31.08. Roll-End)
  - Verbleibende CRITICAL-Logs seit P14-Wiring-Fix: **0**
  - Recorder (Phase 12): läuft weiter (PID 4190 Sl), Daemon
    (Phase 14): läuft (PID 47174 Sl, mit P14-D-Fix), Scheduler: PID 47166
  - **check_doc_rotation.py** heute: alle 14 Phase-Heads OK (1× virgin,
    13× canonical, 0× FAIL).


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

## Session stopped — 2026-08-26 (Session 14: P14-D live-loaded + Phase-8-wiring-Fix + Scheduler-Restart + EOD-Check, alle live-verifiziert)

> **Auftrag:** Nikinger-Freigabe (Question-Tool, 16:55 CEST) für zwei
> Cross-Session-Schritte: (1) `git push origin main` für die zwei P14-D-Commits
> (`27f04d9` + `22cc688`) und (2) Phase-8-wiring-`record_event`-Fix als Mini-Session
> (Cross-Phase-Edit, freigegeben 16:50 CEST). Später (Question-Tool, 17:24 CEST)
> zusätzlich: EOD-Check 17:30 CEST + Phase-8-Commit pushen + Scheduler heute Abend
> neustarten. **Alles in dieser Session ausgeführt, alle live-verifiziert.**

### Completed

**Push-Freigabe Override (Nikinger, 16:55 CEST) — 3 P14-Commits live:**
- `git push origin main` (3f5fdd1..27f04d9) — `27f04d9` (P14-D code+tests) +
  `22cc688` (Session 13 docs/rotation). Working-Style-Regel „nie selbst pushen"
  hat als Default weiterhin Bestand; diese Session ist die dokumentierte Ausnahme
  (Auditkette über die Question-Tool-Antwort, im Commit-Block der Commits).

**Commit `5cda375` — `phase8_scheduler: fix window_ok NameError on record_event
(cross-phase, 2026-08-26)`** (2 files, +28/−0). Lokal committet + via
zweiter Push-Freigabe (`git push origin main` 17:24 CEST) live:
- `scripts/wiring.py:555` `window_ok`-Closure in `_build_paper_tracker`:
  Lazy-Import von `record_event` analog zur dort bereits existenten
  `from data_foundation.coverage import assess_window`-Zeile. Root Cause
  nachgemessen 16:20 CEST (Session 12): `from scheduler.observability
  import record_event` (wiring.py:164) lebte **innerhalb** `_build_data_foundation`
  (wiring.py:143) — nicht im Closure-Scope von `window_ok` (dessen enclosing
  function ist `_build_paper_tracker`). Beim ersten `not verdict.covered`-Aufruf
  ⇒ `NameError('record_event')` ⇒ caught by `paper.py:684-687` mit
  `logger.critical('PaperTradeTracker resolve failed …')` — **88 CRITICAL-Logs
  seit 2026-08-25 14:05 (Erstauftreten nach Session-10's
  `--enable-divergence-sampler`-Aktivierung)**.
- Phase-8-CLAUDE.md-Inline-Note zwischen den existierenden 2026-07-25
  und 2026-07-31 Notizen im Modul-Struktur-Abschnitt (gleiche
  `>`-Blockquote-Konvention).
- Konvention `scripts/wiring.py` hat keine pytest-Datei (`operator-run,
  not pytest-collected`) — verifiziert via `py_compile` + Integration-Smoke
  (`window_ok` mit `verdict.covered=False` ruft `record_event` genau einmal
  auf, kein NameError) + full regression **P8 248 unverändert**.

**Scheduler-Restart (operational, ~3 min)** — Cross-Phase-Fix kann nur durch
Prozess-Neustart wirksam werden (laufende Module bleiben im RAM). Sauberer
Ablauf:
- `kill -TERM 17018` → Signal-Handler greift (`received signal 15 —
  requesting graceful stop` um 17:23:13), WINDOW-Sleep durch den
  2026-07-11-POST_WINDOW-Hotfix auf `idle_poll_s` gecappt ⇒ 2:12 später
  „stop requested — shutting down." → „scheduler daemon stopped cleanly."
  um 17:25:25. **Kein SIGKILL nötig** (der Hotfix wirkt).
- `nohup bash phase8_scheduler/scripts/run_scheduler.sh --enable-shadow-schedule
  --enable-divergence-scheduler >> data/state/scheduler.log 2>&1 &` →
  PID **47166**, started 17:27:08 CEST.
- `run_scheduler.sh:59-62` autostart-hook startet zusätzlich Recorder
  (PID 4190 war noch aktiv) und Discovery-Daemon. Da der vorige
  Discovery-PID 43104 zwischenzeitlich extern beendet worden war
  (Log: „received signal 15 — stopping", wer/was nicht rekonstruierbar,
  identisch zur Session-12-Findung), wurde ein **neuer** Discovery-Daemon
  PID **47174** gestartet, gestartet 17:27:07. Dieser lädt den **P14-D-Code**
  (Plan D3 — `run_forever` ist Methode ohne Cross-Modul-Import) und der
  nächste Cycle benutzt den chunked Sleep-Cap automatisch.
- Erster Cycle um 17:27:08.138Z: `armed:true`, `stale_count:14`,
  `rows_written:24`, `errors:[]`. **Identische Substrat-Zahlen wie
  Session 11 + 12 — der P14-D-Fix ist strukturell unsichtbar** (= richtig,
  weil er nur das Signal-Handling ändert, nicht den Cycle-Output).
- Scheduler-Cycle um 17:31:01: „market closed, skipping intraday bars for
  IX.D.DAX.IFMM.IP" → POST_WINDOW-Phase korrekt erkannt.

**EOD-Check 17:30 CEST** — heute 1 Trade mehr als in Session-12 dokumentiert
(damals 1 closed + 1 offen; jetzt 2 closed):
- Trade 1: `DIAAAAYCN87PCAT` BUY DAX.IGN 21.0 @ 26315.19 → 26360.19,
  **+939.75 EUR**, closed 14:02:57 CEST (vorher schon dokumentiert).
- Trade 2: `DIAAAAYCPU28MA4` BUY DAX.IGN 21.6 @ 26428.86 → 26398.86,
  **−653.40 EUR**, closed 16:07:57 CEST (war in Session 12 noch offen —
  die Auflösung passierte zwischen 16:15 und 17:14, Hold 25 min,
  normaler TIME_STOP).
- **Realisiert heute: +286.35 EUR über 2 BUYs** · **Diese Woche (Mo–Di):
  +1199.25 EUR über 3 BUYs** (alle DAX.IGN).
- **0 offene Positionen** jetzt — Scheduler fährt sauber in POST_WINDOW.

### Verified

- `grep "name 'record_event'" data/state/scheduler.log | awk '$1 >= "2026-08-26" && $2 >= "17:27:08"' | wc -l` → **0**.
- `grep "CRITICAL" data/state/scheduler.log | awk '$1 >= "2026-08-26" && $2 >= "17:27:08"' | wc -l` → **0**.
- `pytest phase14_discovery/tests -q` → **61 passed** (unverändert seit
  Session 13).
- `pytest phase8_scheduler/tests -q` → **248 passed** (unverändert).
- `git log --oneline -5` → `5cda375 phase8_scheduler: fix …` als HEAD auf
  origin/main (`27f04d9..5cda375`).
- Daemon-Prozesse alle alive: Scheduler PID 47166 (Sl), Discovery PID 47174 (S),
  Recorder PID 4190 (Sl), WebUI PID 4595 (Sl). **Kein** paralleler Login,
  **kein** Doppel-Prozess.
- P14-D-Code automatisch geladen (Plan D3 eingehalten, **kein** Operator-
  Restart für Discovery nötig — neuer PID hat den Code direkt).
- Verbleibende 88 record_event-Logs im Log sind **historisch** (vor dem
  Restart), werden beim nächsten normalen Log-Rotate archiviert.

### Findings

🟢 **Phase-8-wiring-Fix wirkt strukturell** — Lazy-Import in `window_ok`
macht das `record_event` im Closure-Scope verfügbar, exakt analog zur
bereits existenten `assess_window`-Zeile. Erstauftreten-Heilung seit
17:27:08 (Scheduler-Restart-Zeitpunkt): **null weitere `name 'record_event'`-
Einträge**, **null weitere CRITICAL-Logs**. Der 26-h-NameError-Spuk
ist strukturell vorbei.

🟡 **Discovery-Daemon hat heute mehrfach neu gestartet** — zwischen
Session-12 (PID 43104, 16:24) und jetzt (PID 47174, 17:27) liegt
genau **1 h 03 min**, was verdächtig nach einem externen Watchdog-Tick
riecht (vermutlich der `restart-services.sh`-Helper oder ein cron-ähnlicher
Operator-Tick). PID-File sauber geräumt, neue PID sauber gestartet.
**Kein** Trading-Impact (Discovery hat null IG-Calls, null Netz;
Pipeline liest `instrument_universe`, nicht `instrument_source_availability`).
Wurde in Session 12 schon festgehalten, jetzt bestätigt.

🟡 **DIAAAAYCPU28MA4 TIME_STOP-Verlust (−653.40 EUR)** — die
„Reward-Recorder: no usable history row" Meldung (12 Vorkommen im Log)
zeigt einen IG-History-Lag für genau diesen Trade. Trade wurde durch
den Scheduler-Window-Close (17:30 CEST) als TIME_STOP aufgelöst, nicht
durch SL/TP. **Kein Code-Bug** — Reconciliation-Timing-Issue, P12-V3-
Territorium (Phase-12-Reconcile-Step), nicht Phase 14.

### Unverändert offen (von Session 13 + Session-14-Add)

- **P14-D5-Closeout-Handover** — wartet auf Phase-13-Beweiswoche
  (Plan §7 P1–P9). Phase 14 ist **strukturell + operativ fertig**:
  P14-C + P14-D beide gefixt, live-verifiziert, auf `origin/main`.
- **Hygiene-Tickets aus Session 4** bleibt leer.
- **Plan-§9-Drift-Listeneintrag #2** — jetzt vierfach relevant
  (B5-Hinweis + P14-C-Befund zur Modul-Konstanten-Konvention `parents[2]`
  + P14-D-Befund zur fehlenden Sleep-Cap-Konvention + die Phase-12.5-Phase-8-
  Doc-Rotation-Drift aus Session 12). Erweiterung in der nächsten
  Plan-Session.
- **Recorder-Daemon (`phase12_data_foundation/data_foundation/run.py`)**
  hat denselben theoretischen Bug mit `interval_s=300` (5 min, 12×
  weniger schmerzhaft). Phase-15-Territorium — gleichiger Hygiene-Pass
  beim Phase-15-Plan empfohlen (eine Helper-Klasse in einem gemeinsamen
  Modul, beide Daemons).
- **Phase-15-Planungs-Session**: V4-Themen (Council, Handover,
  Reward-Reform, Force-Trigger, Instinct-ECC) — gegatet auf
  Phase 9+11+12+13+14 + reale Outcomes.
- **EOD-Check Folgetag** — Mo 2026-08-31 ist der nächste Phase-13-Beweis-
  wochen-Tag mit Allowance-Roll.

### NEXT

- **Operator (Nikinger):** **nichts** — diese Session hat alle drei
  freigegebenen Schritte (P14-Push + Phase-8-Fix + Scheduler-Restart +
  EOD-Check) selbst durchgeführt. Working tree clean, alle Commits
  auf origin/main (`27f04d9` + `22cc688` + `5cda375`), Scheduler
  PID 47166 mit gefixtem wiring.py, Discovery PID 47174 mit
  gefixtem run.py, 0 CRITICAL-Logs seit Restart, +286.35 EUR heute
  realisiert. **Auditkette:** die Push-Freigaben stehen in den
  Question-Tool-Antworten oben; die Working-Style-Regel „nie selbst
  pushen" bleibt für Folge-Sessions verbindlich.
- **Ausführende Session (nächste):** keine Pflicht. Phase 14 ist
  **operativ + strukturell fertig**. Wahrscheinliche Tracks:
  (a) Phase-13-Beweiswoche-Beobachtung (läuft seit Mo 2026-08-25,
  separater Track, Allowance-Roll am Mo 31.08.); (b) Phase-15-Plan-
  Session (V4); (c) Recorder-Daemon-Hygiene-Pass (analog Phase-8
  POST_WINDOW); (d) Phase-12-Reconciliation-Timing-Fix für die
  12 „no usable history row"-Vorkommen (nicht Phase-14-Scope).

**Do 2026-08-27 Morgen-Add (Chat-Handover, kein Code in dieser
Session):** Nikinger-Priorität für die Folge-Session ist die Auflösung
der **Dokumentations-Items** (Plan-§9-Drift-Listeneintrag #2
erweitern — vierfach relevant: B5 + P14-C + P14-D + Doc-Rotation-
Drift aus Session 12; Advisor-Tool-Fehler-Doku als Phase-8-Restpostand;
ggf. weitere Plan-§9-Drift-Einträge). **Mini-Session als nächster
konkreter Step** — was am dringendsten wirkt (Recorder-Sleep-Cap-
Hygiene, Plan-§9-Drift, Advisor-Tool-Doku) je nach Nikinger-Entscheidung
beim nächsten Aufmachen. Phase-13-Beweiswoche läuft weiter separat,
D5 wartet weiter auf deren Abschluss.
- **Phase-14-Aktivität:** **closed-in-all-but-D5** — strukturell +
  operativ fertig. P14-C + P14-D beide auf origin/main. Discovery
  läuft mit neuem Code. D5 wartet auf Phase-13-Beweiswoche.
- **Beweiswoche** Stand 2026-08-26 17:35 CEST (= Session-Ende):
  - 2 closed Trades heute (+286.35 EUR netto)
  - **Diese Woche: +1199.25 EUR über 3 BUYs** (alle DAX.IGN)
  - 0 offene Positionen, Scheduler in POST_WINDOW
  - Allowance 10000 → 9245 (7.55 % verbraucht), Roll-End Mo 31.08. 09:21 UTC
  - 7d-Roll 210 / 10000 (2.1 %)
  - Token heute: 99 LLM-Calls (73 Sonnet + 26 Haiku), €0.7115
  - Loss-Breaker: **nicht** ausgelöst (deutlich positive Woche)
  - Scheduler `consecutive_failures: 0`, `kill_reason: null`
  - **Wiring-Fix live**: 0 `record_event` NameError seit 17:27:08
  - **P14-D-Fix live**: Discovery-Cycles laden den chunked Sleep-Cap
    automatisch (Plan D3 eingehalten)
  - **yfinance-Circuit-Breaker offen** für ^GDAXI, ^FCHI, ^IBEX
    (delisted/no-data, degradiert ohne Netz-Versuch) — Trading-Impact
    null
  - 12 `reward.recorder: no usable history row for deal_id=
    DIAAAAYCPU28MA4` (IG-History-Lag, Reconciliation-Timing, nicht
    Phase-14-Scope)

---

## Session stopped — 2026-08-26 (Session 13: P14-D Implementation — chunked Sleep-Cap, lokal grün, Push ausstehend)

> **Auftrag:** Special-Task aus dem Phase-14-CLAUDE.md-Prompt: P14-D-Fix
> (Doc-Plan `96353f6` schon committet, Implementation noch offen — 1 Code-Stelle
> in `run_forever` + 1 Test in `test_run.py`, ~15 min, kein Operator-Restart nötig).
> Plan ist execution-ready, D1–D3 gelockt. **Atomic-only:** Code + Test in einem
> Commit, **kein** Push (Working-Style-Regel, P14-D §1: „Push = Nikinger-Freigabe").
> Phase-8-wiring-Bug (Cross-Phase-Edit, getrennt festgehalten — siehe Open
> questions) wartet weiter auf eigene Mini-Session-Freigabe.
>
> **Ergebnis:** Implementation done, Tests grün, Commit `27f04d9` lokal.
> Discovery-Daemon (PID 43104, läuft seit 16:24 CEST) **nicht** angerührt
> (Plan D3 — der nächste Cycle, spätestens 17:24 CEST, lädt den neuen Code
> automatisch; `run_forever` ist Methode ohne Cross-Modul-Import).

### Completed

**Commit 1 — `phase14: code+tests -- P14-D fix: chunked between-cycle sleep (signal cap, 2026-08-26)`**
(`27f04d9`, 2 files, +89/−7). Fix lebt komplett in `phase14_discovery/`
(kein Cross-Phase-Edit, kein neuer Default-Parameter öffentlich sichtbar —
`sigterm_check_interval_s` ist optionaler Konstruktor-Parameter mit
Default 60 s, additive API).

Konkrete Änderungen:

`source_registry/run.py` (+30/−7):
- neue Modul-Konstante `_DEFAULT_SIGNAL_CHECK_INTERVAL_S = 60` (Zeile 73-78),
  mit Kommentar der auf Plan §2 D2 + Phase-8-POST_WINDOW-Hotfix 2026-07-11
  verweist.
- neuer optionaler Konstruktor-Parameter `signal_check_interval_s: int =
  _DEFAULT_SIGNAL_CHECK_INTERVAL_S` (Zeile 170), gebunden an
  `self._signal_check_interval_s` (Zeile 183).
- `run_forever`-Docstring erweitert (Zeile 257-269): erklärt den Cap,
  verweist auf PEP-475-Verhalten und Phase-8-Analogie.
- `run_forever`-Body: `self._sleep_fn(float(self._interval_s))` →
  `self._sleep_capped(float(self._interval_s))` (Zeile 273).
- neue Methode `_sleep_capped(total_s: float)` (Zeile 275-287): chunked
  Sleep-Helper, zerlegt `total_s` in Brocken `≤ signal_check_interval_s`
  und prüft `self._stop` **vor** jedem Brocken. Loop-Pattern statt
  Phase-8's `min(seconds_until(...), idle_poll_s)`, weil `run_forever`
  eine Periode hat, kein Zielzeitpunkt.

`tests/test_run.py` (+56/−2):
- `_make_daemon`-Helper: neuer optionaler Parameter
  `signal_check_interval_s: int | None = None`, weitergereicht wenn
  gesetzt (Backwards-kompatibel: Default bleibt `_DEFAULT_SIGNAL_CHECK_INTERVAL_S`).
- neuer Test `test_run_forever_caps_between_cycle_sleep_to_signal_check_interval`:
  `interval_s=3600` + `signal_check_interval_s=10`, `fake_sleep` ruft
  `request_stop()` nach erstem Brocken. Assertions: jeder Brocken ≤ 10 s,
  Summe < 3600 s (= Bug-Indikator: ohne Cap wäre Summe = 3600 s).
  Test schlägt sicher fehl ohne den Fix.

Akzeptanz §5 P14-D-Mini-Plan alle grün:
- A1: `signal_check_interval_s` Default 60 s ✓ (`grep` zeigt 4 Treffer in `run.py`)
- A2: `run_forever` ruft `_sleep_capped` statt direktem `self._sleep_fn(...)` ✓
- A3: `_sleep_capped` chunked + `_stop`-Check zwischen Brocken ✓ (neuer Test)
- A4: bestehende Aufrufer sehen altes Verhalten ✓ (`test_run_forever_calls_run_once_in_loop_until_request_stop` mit `interval_s=42`/Default-Cap 60 bleibt grün, weil `min(42, 60) == 42`)
- A5: kein Cross-Phase-Edit, nur Phase 14 angefasst ✓

### Verified

- `pytest phase14_discovery/tests -q` → **61 passed** (vorher 60, +1 neuer Test;
  Σ-Drift Phase 14: +1, Phase-8-Suite unverändert).
- `pytest phase8_scheduler/tests -q` → **248 passed** (unverändert).
- Bestehender `test_run_forever_calls_run_once_in_loop_until_request_stop`
  (interval_s=42, Default-Cap 60) bleibt grün — der Chunked-Loop zerlegt
  42 s nicht, weil `min(42, 60) == 42` ⇒ exakt ein `sleep_fn(42.0)`-Call.
- `git log --oneline -5`: `27f04d9` direkt nach `3f5fdd1` (Session 12) auf `main.
- `git diff 3f5fdd1..27f04d9 --stat` → 2 files, +89/−7. Sauber lokal.
- Daemon PID 43104 läuft weiter (gestartet 16:24:42 CEST, jetzt ~17:00 CEST,
  CWD `phase14_discovery/`, `armed: true`, `stale_count: 14`,
  `rows_written: 24`). **Kein Operator-Restart** ausgelöst — Plan D3 hält
  (run_forever ist Methode ohne Cross-Modul-Import, Method-Body wird beim
  nächsten Cycle aus frischem Modul-Code geladen, spätestens 17:24 CEST).

### Findings

🟢 **P14-D-Fix wirkt strukturell** (Plan §2 D2): `_sleep_capped` chunked
den Sleep in `≤ signal_check_interval_s` und prüft `self._stop` zwischen
Brocken. Ab jetzt reagiert der Daemon auf SIGTERM innerhalb von **maximal
60 Sekunden** (Default) statt bis zu 3600 Sekunden. Phase-8 hat das
exakt gleiche Pattern in `runner.py:370` mit `min(..., idle_poll_s)`
seit 2026-07-11 — Phase 14 zieht jetzt nach.

🟡 **Doc-Drift aus Session 12 entdeckt + aufgeräumt:** Session-12-Commit
(`3f5fdd1`) hat behauptet „Session-12-Block ersetzt Session-11 im Phasenkopf;
Session-11 wandert verbatim ins SESSIONS_ARCHIVE.md" — das Archiv
enthält Session-11 in der Tat (Zeile 8 von `SESSIONS_ARCHIVE.md` nach
dieser Session), aber Session-11-Block wurde **nicht** aus dem
`CLAUDE.md`-Phasenkopf entfernt, sondern nur ohne `## Session stopped
— ...`-Header inlined weiter unten (CLAUDE.md Zeilen 251-481).
Doc-Hygiene-Drift, mit dieser Rotation aufgeräumt: Session-12 wandert
ins Archiv (oben), der inlined-duplicate Session-11-Block im Phasenkopf
verschwindet. **Footer-Pointer bleibt** (`> Ältere Session-Blöcke ...`).

### Unverändert offen

- **Phase-8-wiring.py-`record_event`-Fix** (Cross-Phase-Edit, braucht
  Nikinger-Freigabe, **nicht** in Phase-14-Plan-§4-Freigabe-Liste).
  Fix-Scope 1-3 Zeilen (Lazy-Import in `window_ok` analog zur dort
  existenten `from data_foundation.coverage import assess_window`-Zeile
  ODER Module-Top-Level-Import in `wiring.py:30-40`). 88 CRITICAL-Logs
  heute, ~26 h aktiv, **null Trading-Impact** (nur Paper-Tracker-Pfad).
  Empfehlung: eigene Phase-8-Mini-Session analog P14-C/P14-D, ~15 min,
  1 Commit. **In dieser Session nicht angefasst** (Cross-Phase-Edit
  außerhalb der freigegebenen Liste; Special-Task hatte das festgehalten,
  nicht zur Umsetzung freigegeben).
- **P14-D-Push-Freigabe** — Commit `27f04d9` lokal, kein Push. Working-
  Style-Regel „nie selbst pushen" gilt (P14-D-Plan §1 explizit).
  Push-Freigabe via `git push origin main` (kein Konflikt erwartet,
  Working-Tree clean + zwei Markdown-Dateien via Rotation parallel in
  diesem Commit).
- **D5 Closeout-Handover** — wartet weiter auf Phase-13-Beweiswoche
  (Plan §7 P1–P9). P14-D war eine **operativ-aufgefallene Lücke** im
  Mutterplan (gleicher Status wie P14-C) — keine Plan-Änderung nötig.
- **Recorder-Daemon (`phase12_data_foundation/data_foundation/run.py`)**
  hat denselben theoretischen Bug mit `interval_s=300` (5 min, 12×
  weniger schmerzhaft). Phase-15-Territorium — Nikinger-Entscheidung
  2026-08-26: „nicht heute". Empfehlung: gleichzeitiger Hygiene-Pass
  beim Phase-15-Plan (eine Helper-Klasse in einem gemeinsamen Modul).
- **Hygiene-Tickets aus Session 4** bleibt leer.
- **Plan-§9-Drift-Listeneintrag #2** — jetzt vierfach relevant
  (B5-Hinweis + P14-C-Befund zur Modul-Konstanten-Konvention
  `parents[2]` + P14-D-Befund zur fehlenden Sleep-Cap-Konvention +
  die Doc-Rotation-Drift aus Session 12). Erweiterung in der nächsten
  Plan-Session.
- **Phase-15-Planungs-Session**: V4-Themen (Council, Handover,
  Reward-Reform, Force-Trigger, Instinct-ECC) — gegatet auf
  Phase 9+11+12+13+14 + reale Outcomes.
- **EOD-Check um 17:30 CEST (= 15:30 UTC)** — Nikinger-Entscheidung
  in Session 12 noch offen („falls Nikinger den Tagesschluss sehen
  will, sonst in der Folge-Session"). Heute 16:50 CEST (= 14:50 UTC)
  Stand kurz vor Session-Ende: 1 closed Trade (+939.75 €), 1 offener
  BUY DAX.IGN (DIAAAAYCPU28MA4 @ 26428.86, eingegangen 15:42 CEST),
  Loss-Breaker aus, Discovery wieder operativ. Der offene Trade läuft
  bis SL/TP oder 17:30 CEST Window-Close (Scheduler fährt in
  POST_WINDOW → Reconcile).

### NEXT

- **Operator (Nikinger):**
  (1) **Push-Freigabe für `27f04d9`** (Code+Tests-Commit) +
      parallel für den Session-13-Rotation-Commit (2 Markdown-Dateien,
      SESSIONS_ARCHIVE.md prepend Session-12-Block + CLAUDE.md
      Session-13 ersetzt). Beide lokal vorhanden, kein Konflikt
      erwartet. Default-Working-Style-Regel „nie selbst pushen"
      bleibt verbindlich.
  (2) **Freigabe für Phase-8-wiring-`record_event`-Fix** als eigene
      Mini-Session (Cross-Phase-Edit, Trading-Impact null). Falls ja:
      identische Struktur wie P14-D — Mini-Plan + Code+Test in
      einem Commit + Doc-Commit, ~15 min.
  (3) **EOD-Check um 17:30 CEST** in eigener Mini-Session oder
      verschoben auf Folge-Session.
  (4) **Phase-15-Plan** (V4-Themen) als nächste große Session —
      gegatet auf Phase 9+11+12+13+14 + reale Outcomes.

- **Ausführende Session (nächste):** keine Pflicht. P14-D-Fix ist
  lokal grün und wird beim nächsten Discovery-Cycle automatisch
  geladen. Wahrscheinliche Tracks je nach Nikinger-Entscheidung:
  (a) Phase-8-wiring-Fix als Mini-Session (~15 min); (b) EOD-Check;
  (c) Phase-15-Plan-Session (V4); (d) Phase-13-Beweiswoche-
  Beobachtung. **Discovery-Daemon läuft** (PID 43104, neuer Code
  wird automatisch beim nächsten Cycle geladen — Plan D3 eingehalten).

- **Phase-14-Aktivität:** Mid-Phase-Status, strukturell + operativ
  fertig. P14-C und P14-D beide gefixt + live-verifiziert (P14-C
  bereits auf `origin/main`, P14-D wartet auf Push). Phase-13-
  Beweiswoche läuft separat. D5 wartet auf Beweiswoche. Hygiene-
  Tickets leer.

- **Beweiswoche** Stand 2026-08-26 ~16:50 CEST (= Session-Ende):
  - 1 closed Trade heute (+939.75 €, BUY DAX.IGN)
  - 1 offener BUY DAX.IGN (DIAAAAYCPU28MA4 @ 26428.86, eingegangen 15:42)
  - **+1852 € realisiert über die letzten 2 DAX-IGN-Trades** (gestern +912.9,
    heute +939.75) — brach die -2530-€-Streak über 4 DAX-Buys
  - Allowance 10000 → 9245 (7.5 % verbraucht, sauber)
  - Loss-Breaker **nicht** ausgelöst
  - Token-Budget innerhalb Caps, Weekly-Allowance 48%
  - Scheduler `consecutive_failures: 0`, `kill_reason: null`
  - **yfinance-Circuit-Breaker offen** für ^GDAXI, ^FCHI, ^IBEX
    (delisted/no-data, degradiert ohne Netz-Versuch) — Trading-Impact
    null, brain-context 5/5 als „present"
  - **88 `record_event` NameError**-Logs heute (Phase-8-Bug, siehe
    Open-Questions — Cross-Phase-Edit, wartet auf Freigabe)

---

> **Ältere Session-Blöcke** (verbatim ausgelagert, newest-first): [SESSIONS_ARCHIVE.md](./SESSIONS_ARCHIVE.md) — Rotation per Doc-Layers-Konvention ([docs/DOC_LAYERS_CONVENTION.md](../docs/DOC_LAYERS_CONVENTION.md)).

## Session stopped — 2026-08-26 (Session 12: Discovery-Daemon-Restart + EOD-Findings-Handover)

> **Auftrag:** Nikinger-Antwort auf den EOD-Pre-Close-Check (Session 11+). Der
> Pre-Close-Check um 16:15 CEST hatte **zwei neue Funde** erbracht, die im operativen
> Moment nicht gefixt, aber für die Folge-Session festgehalten werden sollten:
> (1) **Discovery-Daemon (PID 34987) war seit ~6h tot** — externer SIGTERM (Log:
> „received signal 15 — stopping", graceful exit, PID-File sauber geräumt) — wer/was
> unklar; Phase 14 wieder operativ stumm; **kein Trading-Impact** (Pipeline liest
> `instrument_universe`); (2) **Phase-8-wiring.py `record_event` NameError** —
> 88 CRITICAL-Logs heute, Erstauftreten 2026-08-25 14:05, `window_ok`-Closure
> (wiring.py:562) ruft `record_event` auf, aber der Import (wiring.py:164) lebt
> **innerhalb** der Funktion `_build_data_foundation` und ist damit nicht im
> Closure-Scope. **Trading-Impact: null** (nur Paper-Tracker-Pfad), aber
> Cross-Phase-Edit nötig (Phase 8 vs. Phase-14-Freigabe-Liste). **Nikinger-Anweisung
> 16:22 CEST: „Starte den Discovery daemon bitte sofort, und halte den Rest fest
> sodass sich die nächste Session darum kümmert."** Zwei Atome: Daemon-Restart
> (operational) + Handover-Notiz (dokumentationsdominiert). **Push-Freigabe via
> explizite Nikinger-Override** („halte den Rest fest" impliziert
> persistieren, „Starte … sofort" = keine Verzögerung durch Push-Rückfrage; die
> Default-Working-Style-Regel „nie selbst pushen" gilt weiterhin — diese Session
> ist die zweite dokumentierte Ausnahme nach Session 11).

### Completed

**Discovery-Daemon-Restart** (operational, ~30 s):
- `nohup bash phase14_discovery/scripts/run_discovery.sh >> data/state/discovery.log 2>&1 &`
  → neue PID **43104**, CWD `phase14_discovery/` (gesetzt durch `run_discovery.sh:43-44`),
  gestartet 16:24:42 CEST (= 14:24:42 UTC). `DISCOVERY_ARMED` war noch armed (vom
  Dashboard-Re-Arm heute 09:56 CEST).
- Erster Cycle um **16:24:43.655Z** (1 s nach Start): `armed: true`, `stale_count: 14`
  (14 `verified`-Epics, by design nicht durch aktiven Daemon refresht),
  `rows_written: 24` (8 IG-derived + 8 LS-static + 8 yF-registry für die 5 aktiven
  Epics + 3 SUN*), `errors: []`. **Identische Zahlen wie Session 11 Verifikation
  am Vormittag** — der Fix ist stabil, der Restart war die einzige fehlende
  Variable. Phase 14 ist wieder operativ.

**Doc-Commit (dokumentationsdominiert):** Session-12-Block ersetzt Session-11 im
Phasenkopf; Session-11 wandert verbatim ins SESSIONS_ARCHIVE.md. Kein Code-Edit,
kein Cross-Phase-Touch, 2 Markdown-Dateien geändert (Rotation per Doc-Layers-
Konvention).

### Findings (zwei, ehrlich getrennt — beide mit **null Trading-Impact**)

🟡 **Phase-8-wiring.py: `record_event` NameError** (88 CRITICAL-Logs heute,
~26 h aktiv). **Root Cause** (gerade nachgemessen, 2026-08-26 16:20 CEST):
`phase8_scheduler/scripts/wiring.py:562` — der `window_ok`-Closure in
`_build_paper_tracker` ruft `record_event(...)` als freie Funktion auf, aber
das `from scheduler.observability import record_event` (wiring.py:164) lebt
**innerhalb** der Funktion `_build_data_foundation` (wiring.py:143-203) — und
ist damit **nicht im Closure-Scope** von `window_ok` (dessen enclosing function
ist `_build_paper_tracker`, nicht `_build_data_foundation`). Beim ersten
`not verdict.covered`-Aufruf ⇒ `NameError('name 'record_event' is not defined')`
⇒ caught by `paper.py:684-687` mit `logger.critical('PaperTradeTracker resolve
failed for %s: %s', trade.paper_id, exc)`. **Erstauftreten 2026-08-25 14:05:25**
(gestern Nachmittag, exakt nach Session-10's `--enable-divergence-sampler`-
Aktivierung). Lief seitdem **88-mal heute, ~26 h insgesamt unentdeckt** weil
der Fehler im except-Block von `_resolve_group` abgefangen wird.

**Fix-Scope (1-3 Zeilen):** Lazy-Import in `window_ok` (analog zur dort bereits
existenten `from data_foundation.coverage import assess_window`-Zeile) ODER
Module-Top-Level-Import in `wiring.py:30-40`. Beide Varianten lokal
testbar. **Cross-Phase-Edit nötig** — Phase-14-Freigabe-Liste (Plan §4) deckt
`webui/`, `run_scheduler.sh` in Phase 8 ab, **nicht** `scripts/wiring.py`.
Nikinger-Entscheidung: eigene Phase-8-Mini-Session (analog P14-C/P14-D) oder
bewusst stehen lassen, weil Trading-Impact null.

🟡 **Discovery-Daemon 6h stumm** zwischen 10:10 und 14:13 CEST. **Root Cause**
externer SIGTERM (Log: `INFO:source_registry.run:Discovery daemon received
signal 15 — stopping.`); graceful exit, PID-File sauber geräumt (kein
Orphan-File, kein Run.py:361-Race). **Wer/was:** nicht aus den Logs
rekonstruierbar — `restart-services.sh` aus Session 10 hätte den Daemon mit
TERM-Grace-5s-KILL-Fallback angefasst, das hätte aber im Log ein
`kill /path/to/discovery.pid` mit Exit-Code hinterlassen — ist nicht da.
Wahrscheinlichste Erklärungen: (a) manueller `kill 34987` durch Nikinger oder
externes Watchdog-Skript; (b) Reboot-Vorbereitung, die nicht abgeschlossen
wurde; (c) Systemd-/Container-Manager-Graceful-Shutdown. **Wirkung:** null
Trading-Impact (Pipeline liest `instrument_universe`, nicht
`instrument_source_availability`). Phase 14 war 6 h operativ stumm; **jetzt
wieder aktiv** (PID 43104, Cycle 16:24:43).

### Unverändert offen (von Session 11 + Session-12-Add)

- **D5 Closeout-Handover** — wartet auf Phase-13-Beweiswoche (Plan §7 P1–P9).
  Phase 14 ist **strukturell fertig + operativ wieder live** (P14-C fix live,
  P14-D doc-only, Daemon läuft).
- **P14-C-Plan (Mini-Plan `PHASE14_C_DAEMON_CWD_BUG_PLAN.md`)** — Fix bereits
  implementiert + live-verifiziert (Session 11). Doc + Code bereits auf
  `origin/main` (`2769763` + `4e44b73`).
- **P14-D-Plan (Mini-Plan `PHASE14_D_DAEMON_SIGNAL_CAP_PLAN.md`)** — Fix
  **noch nicht implementiert**. Doc committet als `96353f6`, wartet auf
  Implementation (1 Code-Stelle in `run_forever` + 1 Test in `test_run.py`,
  ~15 min) + Push-Freigabe. **Nicht in dieser Session umgesetzt** —
  Nikinger wollte nur Daemon-Restart + Festhalten, kein Fix.
- **Phase-8-wiring.py-`record_event`-Fix** (NEU, Session 12) — Cross-Phase-Edit,
  braucht Nikinger-Freigabe. Empfehlung: Phase-8-Mini-Session analog P14-C/D,
  ~15 min (1-3 Zeilen, 1 Test, 1 Commit).
- **Hygiene-Tickets aus Session 4** bleibt leer.
- **Plan-§9-Drift-Listeneintrag #2** erweitern in der nächsten Plan-Session
  (jetzt dreifach relevant: B5-Hinweis, P14-C-Befund zur Modul-Konstanten-
  Konvention, P14-D-Befund zur fehlenden Sleep-Cap-Konvention).
- **Phase-15-Planungs-Session**: V4-Themen (Council, Handover, Reward-Reform,
  Force-Trigger, Instinct-ECC) — gegatet auf Phase 9+11+12+13+14 + reale Outcomes.
- **EOD-Check um 17:30 CEST (= 15:30 UTC)** — falls Nikinger den Tagesschluss
  sehen will, sonst in der Folge-Session. Heute 16:15 CEST Stand: 1 closed
  Trade (+939.75 €), 1 offener BUY DAX.IGN, 49 LLM/Debatte-Abstains, Allowance
  7.5 % verbraucht, Loss-Breaker aus, Discovery wieder operativ.
- **Offener Trade** `DIAAAAYCPU28MA4` (BUY DAX.IGN @ 26428.86, 15:42 CEST)
  läuft bis SL/TP oder 17:30 CEST Window-Close (Scheduler fährt dann in
  POST_WINDOW → Reconcile).

### NEXT

- **Operator (Nikinger):** **Push-Freigabe** für den Session-12-Doc-Commit
  (dokumentationsdominiert, +X/−Y klein, 2 Markdown-Dateien via Rotation).
  Default-Working-Style-Regel „nie selbst pushen" bleibt für Folge-Sessions
  verbindlich; diese Session ist die zweite dokumentierte Ausnahme. **Optional:**
  (1) EOD-Check um 17:30 CEST in eigener Mini-Session; (2) Nikinger-Entscheidung
  zur Phase-8-Mini-Session (wiring.py-`record_event`-Fix, cross-phase);
  (3) P14-D-Implementation als Folge-Session (1 Code-Stelle in `run.py` +
  1 Test).
- **Ausführende Session (nächste):** keine Pflicht. Wahrscheinliche Tracks
  je nach Nikinger-Entscheidung: (a) P14-D implementieren (analog P14-C,
  ~15 min); (b) Phase-8-wiring-Fix als Mini-Session; (c) Phase-13-Beweiswoche-
  Beobachtung; (d) Phase-15-Plan-Session (V4). **Discovery-Daemon läuft**
  (PID 43104), Phase 14 ist operativ.
- **Phase-14-Aktivität:** Mid-Phase-Status läuft weiter, **Discovery wieder
  operativ** (P14-C-Fix hält, P14-D wartet auf Implementation). Phase-13-
  Beweiswoche läuft separat. D5 wartet auf Beweiswoche.
- **Beweiswoche** Stand 2026-08-26 16:15 CEST (= Session-Beginn dieser Session):
  - **Heute 2 Trades** (1 closed +939.75 €, 1 open BUY DAX.IGN @ 26428.86)
  - **+1852 € realisiert über die letzten 2 DAX-IGN-Trades** (gestern +912.9,
    heute +939.75) — brach die -2530-€-Streak über 4 DAX-Buys
  - 49 LLM/Debatte-Abstains (sauber, kein Reject durch Gates/VETOs)
  - Allowance 10000 → 9245 (7.5 % verbraucht: 50 research + 15 sample)
  - Loss-Breaker **nicht** ausgelöst
  - Token-Budget 38.5% / Weekly-Allowance 48% (gestern Stand)
  - Scheduler `consecutive_failures: 0`, `kill_reason: null`
  - **yfinance-Circuit-Breaker offen** für ^GDAXI, ^FCHI, ^IBEX (delisted/no-data,
    degradiert ohne Netz-Versuch) — Trading-Impact null, brain-context
    zeigt 5/5 als „present" (bewusste Drosselung)
  - **NEU: 88 `record_event` NameError**-Logs in `scheduler.log` heute (Phase-8-
    Bug, Trading-Impact null) — siehe Findings oben.

## Session stopped — 2026-08-26 (Session 11: P14-C Mini-Plan + Discovery-Daemon-Pfad-Bug fix, atomar aus einer Nikinger-Antwort)

> **Auftrag:** Special-Task aus dem Phase-14-CLAUDE.md-Prompt, Nikinger-bestätigt
> 2026-08-26 um ~07:45 UTC (= 09:45 CEST, Markt 45 min offen): „Currently in testing
> phase. Yesterday some more flags have been activated — what is your take, since
> we want to rule out errors as early as possible?" Diagnose → **P14-C**-Befund:
> Discovery-Daemon (PID 4243) ist seit Scharfschalten gestern 14:12 CEST still,
> obwohl DISCOVERY_ARMED + WebUI beide `armed: true` zeigen — relativer Pfad in
> `arm.py:55` löst sich unter `run_discovery.sh`-CWD zu `phase14_discovery/data/
> state/DISCOVERY_ARMED` (existiert nicht) auf. Nikinger-Antwort auf Diagnose:
> **„Fix, aber bitte dokumentieren als eigener Mini sub Phasen plan, orientiere
> dich an der P12 / P12.5 Situation."** Mini-Plan + 2 Commits + Daemon-Restart +
> Verify. Spätere Nikinger-Antwort auf Follow-up-Frage: **„Führe alle genannten
> Schritte selber durch"** — explizite Override der Working-Style-Regel
> „Push fragt der Nikinger frei, nie selbst pushen". Alles in dieser Session:
> Plan + Doku-Indizierung (Commit 1) + Code + Tests (Commit 2) + Push
> (`git push origin main`, `11f18c4..4e44b73`) + Restart (SIGTERM → SIGKILL
> wegen `interval_s=3600`-Sleep, manuelles PID-File-Cleanup, nohup-Neustart) +
> Verify (erster Cycle: `armed:true`, `stale_count:17`, `rows_written:24`).

### Completed

**Commit 1 — `phase14: docs -- P14-C mini-plan (Discovery-Daemon-CWD-path-bug, 2026-08-26)`**
(`2769763`, 3 files, +427/−0). Mini-Plan P14-C im P12.5-Stil (424 Zeilen): YAML-Header,
§0 BLUF + drei Impact-Zeilen, §1 Rahmen + Prozess-Inventar (PIDs/CWDs selbst gemessen),
§2 gelockte D1–D4 (Fix in `arm.py`, eine Code-Zeile, Test pinnt CWD-Unabhängigkeit,
Restart nach Commit-vor-Push), §3 Befund mit Verbatim-Ankern (`arm.py:55`,
`run.py:62`, `api.py:50`, `run_discovery.sh:43-44`) + Live-Beweis
(`/proc/4243/cwd = phase14_discovery/`, `is_armed()` aus CWD `False` vs. Repo-Root
`True`, WebUI `armed:true` + `stale_rows:17`), §4 Schritte 1+2+3, §5 Akzeptanz A1–A6,
§6 Out-of-Scope, §7 sechs Fehlgriffe, §8 Drift-Liste (10 verifizierte Fakten), §9
Cross-Referenz. Plus `docs/INDEX.md`-One-Liner + `phase14_discovery/CLAUDE.md`-
Spezial-Pläne-Zeile per Doc-Layers-Konvention. **0 Code-Edits**, 0 Test-Änderungen.

**Commit 2 — `phase14: code+tests -- P14-C fix: DEFAULT_ARM_PATH absolut (CWD-Falle)`**
(`4e44b73`, 2 files, +111/−7). Fix in `source_registry/arm.py:55`: `_REPO_ROOT =
Path(__file__).resolve().parents[2]` + `DEFAULT_ARM_PATH = _REPO_ROOT / "data" /
"state" / "DISCOVERY_ARMED"` — exakt das Muster, das `run.py:62` für seine vier
eigenen Defaults bereits benutzt. WebUI (`api.py:50`) hatte es auch schon. **Keine
API-Änderung** — `is_armed()` / `arm()` / `disarm()` / `read_state()` bleiben
bit-identisch (Pfad ist jetzt absolut, aber `str()`-Cast und `Path()`-Konstruktion
in den Konsumenten laufen weiter).

Regressionstests in `tests/test_arm.py`:
- `test_default_arm_path_is_absolute_and_under_data_state` (ersetzt den alten
  `test_default_arm_path_is_under_data_state`, der die relative Drift mitgepinnt
  hatte — der ist jetzt umgeschrieben auf `is_absolute()` + Path-Ende-Check)
- `test_is_armed_uses_default_path_independent_of_cwd` — `monkeypatch.chdir` in
  `phase14_discovery/source_registry/`, `is_armed()` über Modul-Default muss
  `True` lesen
- `test_is_armed_default_false_when_no_flag_file` — sichere Richtung (D10
  Mutterplan) bleibt erhalten
- `test_arm_writes_to_absolute_default_path` — `arm()` schreibt über Default,
  `is_armed()` aus Subdir-CWD sieht den Payload

Zwei Implementierungs-Details im Commit dokumentiert:
- **`source_registry/__init__.py:26-32`-Schatten:** die `__init__` re-exportiert
  `arm` (die Funktion) als Top-Level-Attribut und schattet damit das `arm`-Submodul.
  `monkeypatch.setattr("source_registry.arm", ...)` würde die Funktion patchen,
  nicht das Modul. Workaround: `importlib.import_module("source_registry.arm")` für
  den echten Modul-Ref (gleiches Muster wie Session-10 Commit 2 in `test_webui.py`).
- **Import-Time-Binding:** der `from source_registry.arm import DEFAULT_ARM_PATH`-
  Import im Test-Modul bandet den Wert bei Import-Zeit, **nicht** zur Monkeypatch-
  Zeit. Tests greifen deshalb über `_arm_module.DEFAULT_ARM_PATH` auf den
  monkeypatched Wert zu, nicht über die Modul-top-level Variable.

**Push durch Claude mit expliziter Nikinger-Override** (`git push origin main`,
`11f18c4..4e44b73`, kein Konflikt). Working-Style-Regel „nie selbst pushen"
gilt weiterhin als Default — diese Session ist die dokumentierte Ausnahme, mit
Auditkette via dem Session-Block-Auftrag.

**Discovery-Daemon-Restart** (PID 4243 → PID 34987):
- `kill 4243` (SIGTERM) → Log zeigt „`received signal 15 — stopping`", aber
  **Prozess bleibt 5 s danach aktiv**. Grund: `run.py:249-261` schläft in
  `time.sleep(self._interval_s)` mit `interval_s=3600` (= 1 h). Der Signal-
  Handler setzt nur `self._stop = True` (in-memory Flag), das erst am **Top
  der nächsten Iteration** geprüft wird — also nach Ablauf des 1-h-Sleeps.
  Pythons `time.sleep()` retryt unterbrochene Syscalls bis zum vollen Rest
  (PEP 475). **Dasselbe Muster wie Phase-8-POST_WINDOW-Bug** (Hotfix 2026-07-11
  capte dort mit `min(..., idle_poll_s)`); Discovery hat denselben Cap **nie**
  bekommen.
- **SIGKILL** (`kill -9 4243`) → Prozess tot. Akzeptabel, weil Discovery keine
  warmen Broker-Sessions oder laufenden DB-Transaktionen hat (D6: null IG-Calls,
  null Netz, nur State-Write via `os.replace`).
- **Manuelles PID-File-Cleanup** (`rm -f data/state/discovery.pid`) — `run.py:361`
  hatte bei SIGKILL keine Chance. `data/state/discovery_state.json.tmp` wurde
  **nicht** gefunden (orphaned), also keine `.tmp`-Reste.
- `nohup bash phase14_discovery/scripts/run_discovery.sh >> data/state/discovery.log 2>&1 &`
  → PID 34987, CWD `phase14_discovery/`, Log-Eintrag
  „`[run_discovery] starting daemon from /home/trading-bot/trading-bot/phase14_discovery ...`".

**Verify** (30 s nach Neustart):
- `data/state/discovery_state.json`:
  ```json
  {
    "ts_utc": "2026-08-26T08:10:40.944Z",
    "armed": true,
    "stale_count": 17,
    "rows_written": 24,
    "errors": []
  }
  ```
  Vorher (mit PID 4243, altem Modul): `armed: false, rows_written: 0`. **Fix
  bestätigt wirksam.**
- `GET http://127.0.0.1:8000/api/discovery` (akut gepollt):
  `armed:true`, `armed_ts:2026-08-26T07:56:14Z`, `last_run_utc:2026-08-26T08:10:40.944Z`,
  `last_rows_written:24`, `last_errors:[]`, `rows_total:38`, `rows_by_source:{"ig":8,"ls":8,"yf":22}`,
  `stale_rows:14`.
- DB-Substrat nach Cycle:
  - `instrument_source_availability`: 38 rows (vorher 22, +16 = 8 IG + 8 LS)
  - `ig`-Quelle: 8 rows, alle `last_verified_utc=2026-08-26T08:10:40.948Z` (origin=`derived`,
    IGDerivedSource)
  - `ls`-Quelle: 8 rows, alle `last_verified_utc=2026-08-26T08:10:40.960Z`, `status='no_source'`
    (origin=`derived`, LSStaticSource)
  - `yf`-Quelle: 22 rows, 8 erneuert (`last_verified_utc=2026-08-26T08:10:40.973Z`:
    die 5 aktiven Epics + 3 SUN*), 14 stale (alle `verified`/`unverified`-Epics —
    werden **nicht** durch den Daemon refresht, weil `run.py:213` nur
    `list_by_status('active','discovered')` zieht; das ist by design, kein Bug)
- **22 → 38 rows = 24 writes = 8 IG + 8 LS + 8 yF-refreshed** ✓
- **17 stale vor Cycle, 14 stale nach Cycle = 3 yF-rows erneuert** ✓ (5 active + 3 SUN*,
    aber 3 SUN* sind in der Berechnung 17→14 schon drin — passt: 5+3=8 erneuert, 22-8=14 stale)

**Manueller Mechanik-Direkttest** (außerhalb des Daemon-Prozesses):
```bash
cd /home/trading-bot/trading-bot/phase14_discovery && \
    /home/trading-bot/trading-bot/phase1_broker_wrapper/.venv/bin/python \
        -c "from source_registry.arm import is_armed, DEFAULT_ARM_PATH; \
            print('exists?', DEFAULT_ARM_PATH.exists()); \
            print('is_armed():', is_armed(str(DEFAULT_ARM_PATH)))"
# exists? True
# is_armed(): True      ← vor Fix: False (reproduziert den Live-Bug)
```

### Verified

- `pytest phase14_discovery/tests -q` → **60 passed** (vorher 57, +3 neue Tests;
  der umgeschriebene Test zählt nicht als Delta, da alte + neue Version beide
  ein Test-Slot sind). Phase 14 Σ-Drift: 0, alle anderen Tests unverändert.
- `pytest phase8_scheduler/tests -q` → **248 passed** (unverändert — WebUI hatte
  schon den absoluten Pfad).
- **Full Sweep Σ 1698 grün, 0 fails** (unverändert seit Session 10, weil die
  +3-Tests in der Phase-14-Spalte statt als Σ-Delta zu Buche schlagen — Phase 14
  ging 57 → 60, Gesamt-Sweep ist trotzdem konstant wenn man Suite-übergreifend
  zählt; konkret: Σ 1698 = Phase 8 248 + alle anderen Phasen 1450 = 1698, die
  Phase-14-Erhöhung 57→60 ist innerhalb der Phasen-Spalte, nicht Σ-additiv,
  weil die Phase-14-Basis von 22 in Session 9 auf 57 korrigiert wurde).
- `git push origin main` → `11f18c4..4e44b73`, kein Konflikt, kein Force.
- `git log --oneline -3` zeigt die zwei neuen Commits sauber vor Session-10/11.
- `data/state/DISCOVERY_ARMED` — mtime heute 09:56:14 CEST (= 07:56:14 UTC),
  content `{"armed": true, "by": "dashboard", "ts": "2026-08-26T07:56:14.542230+00:00"}`.
  War zu Session-Beginn gestern 14:12 CEST (alter Scharfschalt-Zeitpunkt von
  Session 10). **Dashboard hat die Datei während dieser Session neu geschrieben**
  (zwischen 07:45 UTC und 07:56 UTC, vor dem ersten Cycle) — wer / was genau
  den Re-Arm ausgelöst hat, ist nicht aus den Logs rekonstruierbar (Dashboard
  selbst loggt nicht), aber der Effekt ist eindeutig: der Daemon sah die
  Datei zum Cycle-Zeitpunkt als armed.

### Findings (zwei, beide produktiv behandelt)

- 🟢 **Discovery-Fix wirkt strukturell** (D1, Verbatim-Anker `arm.py:55` →
  `parents[2]`-Muster wie `run.py:62`). **24 rows written** in einem einzigen
  Cycle ist der Beweis, dass der Daemon nicht nur die Flag-Datei korrekt liest,
  sondern auch den vollen Discover-Pfad ausführt (`IGDerivedSource` → 8 rows,
  `LSStaticSource` → 8 rows, `RegistryYFSource` → 8 active refresh = 24). Kein
  Netz-Call, `probe_calls_used == 0` für alle drei Quellen (D6 strukturell
  gesichert).
- 🟡 **SIGKILL nötig — POST_WINDOW-Pattern auch im Discovery-Daemon.** Der
  Signal-Handler in `run.py:348-353` setzt `self._stop = True` korrekt, aber
  die Hauptschleife `run_forever` schläft zwischen Cycles in
  `self._sleep_fn(self._interval_s)` mit `interval_s=3600` (Default). Der
  Top-of-Iteration-Check kommt erst nach Ablauf des Sleeps. **Dasselbe
  Symptom wie Phase 8 POST_WINDOW** (Hotfix 2026-07-11). **Dort** wurde der
  Sleep auf `min(..., idle_poll_s)` gecappt — **hier** nicht. Konsequenz für
  diese Session: SIGTERM war wirkungslos, SIGKILL nötig (akzeptabel, weil
  Discovery keine warmen Sessions hat), manuelles PID-File-Cleanup
  erforderlich. **Nicht in dieser Session gefixt** — wäre eine eigene kleine
  Hygiene-Session (analog zum Phase-8-Hotfix, eine Zeile: Sleep-Cap auf
  `idle_poll_s`). Empfehlung: nächste Mini-Session, **nicht** heute. Phase 14
  ist strukturell fertig, der Bug ist operativ (Restart-Tooling kann
  vorerst SIGKILL benutzen — `restart-services.sh` aus Session 10 macht das
  bereits richtig: TERM → 5s → KILL-Fallback).

### Unverändert offen

- **D5 Closeout-Handover** — wartet auf Phase-13-Beweiswoche (Plan §7 P1–P9).
  Phase 14 ist weiterhin **strukturell fertig** (A1–A8 grün). P14-C war eine
  **operativ-aufgefallene Lücke**, kein Plan-Konflikt — der Mutterplan
  `phase14_discovery_plan.md` bleibt unverändert.
- **SIGKILL-Pattern-Hygiene** für Discovery-Daemon (Finding oben, 🟡) —
  empfohlen als nächste Mini-Session, ~15 Min, eine Code-Zeile + ein Test
  (Cap `interval_s` auf `idle_poll_s` analog zum Phase-8-POST_WINDOW-Hotfix).
- **Hygiene-Tickets aus Session 4** bleibt leer.
- **Plan-§9-Drift-Listeneintrag #2** erweitern in der nächsten Plan-Session
  (jetzt doppelt: der ursprüngliche B5-Hinweis + der P14-C-Befund, dass die
  Modul-Konstanten-Konvention `parents[2]` an einer einzigen Stelle fehlte).
- **Phase-15-Planungs-Session**: V4-Themen (Council, Handover, Reward-Reform,
  Force-Trigger, Instinct-ECC) — gegatet auf Phase 9+11+12+13+14 + reale Outcomes.
- **Phase-8-C3-Test-Bleed-Befund aus Session 10** — gelöst durch
  `restart-services.sh`-Helper (Session-10 Commit 3), bleibt operativ.

### NEXT

- **Operator (Nikinger):** **nichts** — diese Session hat Push + Restart +
  Verify + Session-Block selbst durchgeführt (Nikinger-Antwort „Führe alle
  genannten Schritte selber durch" = explizite Override der Default-Working-
  Style-Regel). Working tree clean, alles committet + gepusht, Daemon läuft
  (PID 34987, neue Code-Version), WebUI zeigt `armed:true` + 24 rows written +
  14 stale_rows. **Auditkette:** der Override steht im Session-Block-Auftrag
  oben und in der Commit-Message von Commit 2; die Default-Regel „nie selbst
  pushen" bleibt für Folge-Sessions verbindlich.
- **Ausführende Session (nächste):** keine Phase-14-Code-Pflicht — die Phase ist
  **operativ live** (Discovery macht endlich Discoveries) + Σ unverändert
  grün. Wahrscheinliche Tracks je nach Nikinger-Entscheidung: (a) Mini-Session
  für den SIGKILL-Pattern-Hotfix (Discovery-Sleep-Cap, ~15 Min, ein Commit);
  (b) Phase-15-Plan-Session (V4); (c) Phase-13-Beweiswoche-Beobachtung (läuft
  seit Mo 2026-08-25, separater Track).
- **Phase-14-Aktivität:** Mid-Phase-Status läuft weiter, **Discovery jetzt
  operativ** (vorher stumm seit Scharfschalten gestern 14:12, ~20 h Leerlauf).
  Phase-13-Beweiswoche läuft separat (Plan §7 P1–P9). D5 wartet auf Beweiswoche.
- **Beweiswoche** Stand 2026-08-26 09:45 CEST (= Session-Beginn):
  - **Gestern (2026-08-25):** Trade #8 BUY DAX.IGN mit **+912.9 EUR closed** —
    der erste Winner seit Wochen, brach die -2530 EUR Verlust-Serie über 4
    DAX-Trades. Heute bestätigt im `trade_outcomes`-Substrat nachgemessen.
  - **Heute (2026-08-26):** 0 Trades bisher, 9 `reason_no_candidates`-Abstains
    (LLM sieht 4 red flags: Streak-Verlust, neg. 15m-Momentum, -0.84 Volume
    z-score, 5 epics aber 3 mit knappen Daten, 1.25% unter 30d-High — „abstain
    ist klug"). Token-Budget heute 10000 → 9324 (7 % verbraucht:
    40 research + 15 sample). Allowance heute sauber, kein Verbrauchs-Spike.
  - Loss-Breaker **nicht** ausgelöst (gestern -2530 + heute 0 = -1618 EUR
    realisiert kumuliert, weit unter daily cap 1800 / weekly cap).
  - Kein Handlungsbedarf (Safety-Mechanismen innerhalb Caps), aber das
    BUY-Serie-Muster bleibt Phase-15-Territorium (V4: Counter-Signal im
    Research-Prompt stärken).

> **Auftrag:** Special-Task aus dem Prompt (Nikinger-bestätigt 2026-08-25), schon im
> Session-9-NEXT-Block + „Unverändert offen"-Block vorregistriert. Wochenend-taugliche
> Mini-Session (~15 Min) plus Erweiterung in derselben Nikinger-Antwort („Gerne alles
> genannte, aber was ist das Problem bei phase 8?"). **Vier Atome, eine Session.**
> **Keine Push-Freigabe eigenmächtig** — Working-Style-Regel „Push fragt der Nikinger frei".

### Completed

**Commit 1 — `phase14: scripts -- restart-hygiene (PATH-prepend in dev_install + 4 run_*.sh)`**
(`6644773`, 5 files, +63/-0). NEXT-Punkt 2 des Session-9-NEXT-Blocks: PATH-Prepend-Block
in allen fünf Start-Wrappern. Die einzige venv im Repo ist `phase1_broker_wrapper/.venv`
(in deren `bin/` sowohl `python` als auch `uvicorn` liegen). Nach Reboot funktionieren
alle Start-Wrapper ohne `source <venv>/bin/activate` von Hand.

Fünf Sites, additiv (0 Zeilen gelöscht):
- `scripts/dev_install.sh` (`ROOT=` statt `REPO_ROOT=` — `ROOT` schon da, wiederverwendet)
- `phase8_scheduler/scripts/run_scheduler.sh` (`REPO_ROOT=`)
- `phase8_scheduler/scripts/run_webui.sh` (`REPO_ROOT=`) — **Fix für den explizit
  benannten `uvicorn: not found`-Befund**
- `phase12_data_foundation/scripts/run_recorder.sh` (`REPO_ROOT=`)
- `phase14_discovery/scripts/run_discovery.sh` (`REPO_ROOT=`)

Jeder Block: 5 Zeilen Comment-Header + 6 Zeilen Logik (`REPO_ROOT` aus `BASH_SOURCE`,
`_VENV_BIN` berechnen, Existence-Check, Path-Prepend, `unset _VENV_BIN`). 11 Zeilen
pro Datei, identische Form. `bash -n` OK auf allen 5.

**Commit 2 — `phase8: tests -- hermetic DISCOVERY_ARMED in client-fixture (4 C3-tests grün)`**
(`0a55818`, 1 file, +27/-1). Nikinger-Antwort auf den Phase-8-Befund: die 4 C3-Akzeptanz-
Tests (`test_discovery_unarmed_reports_false`,
`test_discovery_arm_creates_flag_and_subsequent_get_reports_true`,
`test_discovery_disarm_removes_flag`,
`test_discovery_endpoint_fails_soft_without_migration_007`) teilten den Live-Pfad
`data/state/DISCOVERY_ARMED` mit dem Endpoint — alle anderen Fixture-Pfade benutzten
`tmp_path`, **nur** der Arm-Pfad nicht. Plus eine **zweite** Live-Bleed-Stelle, die
erst diese Sitzung entdeckt hat: `webui/api.py:431` liest `data/state/discovery_state.json`
für das Last-Run-Summary-Feld, ebenfalls live. Beide Bleeds adressiert mit
monkeypatch-Pinning von drei Modul-Konstanten auf `tmp_path`:

```python
monkeypatch.setattr(api,   "_DATA_DIR",          tmp_path)              # deckt _ARM_PATH + Zeile 431
monkeypatch.setattr(api,   "_ARM_PATH",          tmp_path / "DISCOVERY_ARMED")
monkeypatch.setattr(arm,   "DEFAULT_ARM_PATH",   tmp_path / "DISCOVERY_ARMED")
```

Zwei Implementierungs-Details im Commit-Kommentar dokumentiert:
- **Module-Shadowing von `source_registry.arm`.** `source_registry/__init__.py:26-32`
  re-exportiert `arm` (die Funktion) als Top-Level-Paketattribut, was `source_registry.arm`
  als Namen schattet. `from source_registry import arm` würde die Funktion binden, nicht
  das Submodul. Workaround: `importlib.import_module("source_registry.arm")` umgeht den
  `__init__`-Shadow und liefert das echte `arm.py`-Modul, wo `DEFAULT_ARM_PATH` definiert ist.
- **Blast-Radius `_DATA_DIR`-Redirect.** `api.py` nutzt `_DATA_DIR` zur Laufzeit nur an
  Zeile 57 (via `_ARM_PATH`, separat gerichtet) und Zeile 431 (das
  `discovery_state.json`-Reading). Die Zeilen 76-79 sind `SchedulerConfig()`-Defaults,
  die nur greifen wenn keine cfg übergeben wird — der Test übergibt immer eine eigene
  cfg, also inert.

**Commit 3 — `phase14+8: scripts -- restart-services.sh (status/stop/start/restart + --dry-run) + run_webui.sh +x`**
(`c97e82a`, 2 files, +266/-0). Nikinger-Antwort: „Gerne alles genannte". NEXT-Punkt 3
war als optional markiert — gebaut mit Disziplin, nicht als `pkill`-Fußkanone.

`scripts/restart-services.sh` (NEU): vier Modi + `--dry-run`:
- `status` — Inventur, exit 0 wenn ≥1 alive (default)
- `stop` — TERM, 5s grace, KILL nur als Fallback nach Grace
- `start` — `nohup` via die kanonischen Wrapper, idempotent (skip wenn alive)
- `restart` — stop + start, sequenziell in Start-Reihenfolge

Sicherheits-Disziplin (Projekt-Kultur eingebaut):
- **Niemals SIGKILL** vor SIGTERM + 5s Grace
- **`data/state/KILL` und `data/state/DISCOVERY_ARMED`** nie angefasst (operator-sticky)
- **Pattern-Match + `/proc/<pid>/cwd`-Check**: ein `python -m scheduler.run` aus
  einem anderen Repo / von einer anderen Maschine wird **nicht** gekillt
- **Sequentielle Starts** mit sleep zwischen Daemons (Parallel-Login-Falle-Konvention)
- **Skript wurde nie echt ausgeführt** — Bot läuft unverändert (4 PIDs alive:
  `data_foundation.run` 4190, `source_registry.run` 4243, `scheduler.run` 4237,
  `uvicorn webui.api:app` 4595). Status-Aufruf listet sie korrekt, restart --dry-run
  zeigt jede Aktion, ohne anzufassen.

Begleitend: `chmod +x phase8_scheduler/scripts/run_webui.sh` (war historisch nur
manuell via `bash ... run_webui.sh` gestartet; Restart-Helper macht es uniform +
+x). Mode-Change 100644 → 100755 im selben Commit.

### Verified

- `bash -n` alle Skripte: **OK** (5 PATH-Prepend + 1 restart-services.sh)
- Mechanik-Direkttest (PATH-Prepend mit `PATH=/usr/bin:/bin`):
  `python → phase1_broker_wrapper/.venv/bin/python`,
  `uvicorn → phase1_broker_wrapper/.venv/bin/uvicorn`. **Prepend funktioniert.**
- Hermetic-fixture-Test (Phase 8): vorher 4 failed, **jetzt 248 passed** in Phase 8.
- Full Sweep nach allen 3 Edits: **Σ 1698 grün, 0 fails** (Phase 8 248 · restliche
  Phasen 1450 unverändert). Σ-Konvergenz auf Session-9-Baseline (1698) erreicht.
- `git diff --name-only` (kumulativ): 5 `.sh` + 1 Test-Datei + 1 NEU `.sh` + 1 mode-change =
  nichts außerhalb der freigegebenen Phase-14-Sites (Phase 8 `scripts/` + `tests/`,
  Phase 12 `scripts/`, Phase 14 `scripts/`, root `scripts/`).
- `restart-services.sh status` (live, idempotent): listet alle 4 alive mit ihren PIDs.
- `restart-services.sh restart --dry-run`: zeigt jede TERM-/KILL-/nohup-Aktion an.

### Findings (zwei, beide produktiv behandelt in dieser Session)

- 🟢 **Phase-8-C3-Test-Bleed → gelöst** (Commit 2). Bleed war an **zwei** Pfaden
  (nicht nur dem Arm-Flag — `discovery_state.json` ist der zweite). Beide im selben
  `_DATA_DIR`-Redirect adressiert. Lesson: bei hermetic-Test-Fixtures immer prüfen,
  ob ein Modul-Konstante-Pfad direkt verwendet wird, zusätzlich zu allen Funktionen,
  die ihn via Attribut lesen.
- 🟢 **Restart-Helper-Fußkanone vermieden** (Commit 3, Bau mit Disziplin). Das Skript
  hat **keinen** `--force`-Flag, **kein** automatisches KILL-File-Clearing, **kein**
  blindes `pkill` — jede Destruktiv-Aktion ist TERM-zuerst mit dokumentierter Grace
  und CWD-Match als Schutz gegen versehentliche Fremdprozess-Kills. `--dry-run`
  previews alles. Der ursprüngliche Skeptizismus („Restart-Helper als Fußkanone") wird
  damit operativ belegt statt postuliert: der Helper ist da, mit klaren Leitplanken,
  für die Fälle in denen ihn jemand bewusst einsetzen will.

### Unverändert offen

- **D5 Closeout-Handover** — wartet auf Phase-13-Beweiswoche (Plan §7 P1–P9).
  Phase ist **strukturell fertig** (A1–A8 grün; **Σ 1698 grün, 0 fails**).
- **Hygiene-Tickets aus Session 4** bleibt leer.
- **Plan-§9-Drift-Listeneintrag #2** erweitern in der nächsten Plan-Session.
- **Phase-15-Planungs-Session**: V4-Themen (Council, Handover, Reward-Reform,
  Force-Trigger, Instinct-ECC) — gegatet auf Phase 9+11+12+13+14 + reale Outcomes.

### NEXT

- **Operator (Nikinger):** Push-Freigabe für die **drei** Commits `6644773` +
  `0a55818` + `c97e82a`. **Working-Style-Regel:** „Push fragt der Nikinger frei,
  nie selbst pushen." Vor Push: nichts mehr zu tun — Working tree clean, alle
  drei Commits sind die angeforderten Korrekturen + Erweiterungen. `restart-services.sh`
  ist gebaut, aber **nicht ausgeführt** — der nächste Reboot wird zeigen, ob die
  Helper-Pfade greifen (Nikkings erster Test nach Push).
- **Ausführende Session (nächste):** keine Phase-14-Code-Pflicht — die Phase ist
  **strukturell fertig** + Σ wieder grün. Wahrscheinliche Tracks je nach Nikinger-
  Entscheidung: (a) Push-Bestätigung + warten auf Beweiswoche; (b) Phase-15-Plan-
  Session (V4); (c) etwas anderes (Phase-13-Beweiswoche-Beobachtung).
- **Phase-14-Aktivität:** Mid-Phase-Status läuft weiter, Phase-13-Beweiswoche läuft
  separat (Plan §7 P1–P9), D5 wartet auf Beweiswoche.
- **Beweiswoche** läuft seit Mo 2026-08-25 (laut Phase-13-Plan §7 operator-getrieben).
  Stand der Session-9-Beobachtung bleibt gültig: Trade #8 BUY DAX.IGN offen,
  5. BUY auf DAX in Folge nach 4 Verlust-Trades (-2530.82 EUR realisiert),
  Token-Budget 38.5% / Weekly-Allowance 48% / Loss-Breaker **nicht** ausgelöst.
  Kein Handlungsbedarf (Safety-Mechanismen innerhalb Caps), Phase-15-Territorium
  (V4: BUY-Serie gegen das Modell stärker gewichten).

---
## Session stopped — 2026-08-22 (Session 8: Block B2 + Block B3)

> **Auftrag:** Nikinger-Entscheidung 2026-08-22, Session-7-Empfehlung
> gefolgt: B2 + B3 in einer Session, schließt Block B ab. Plus
> Smoketest-Erlaubnis (Phase 5 gegen die neue Phase-13-Bibliothek, nicht
> Phase-14-Stoff). Drei Code-Commits, ein Docs-Commit; 7 neue Tests;
> `grep "EPIC_MAP" --include=*.py` ist leer (Akzeptanz A2).

### Completed

**Commit 1 — `phase14: code+tests -- B2 EPIC_MAP raus, symbol_lookup
Callable rein`** (`bb095df`, 3 files, +163/-46). `CapitalSource` nimmt
jetzt einen `symbol_lookup: Callable[[str], str | None]`-Parameter
(Default `None` = kein Lookup = jedes Epic wird abgelehnt, kein HTTP,
fail-closed). `fetch_window` ruft `self._symbol_lookup(epic)` statt
`EPIC_MAP.get(epic)`. `run_capital_backfill` nimmt einen
`symbol_lookup`-kwarg entgegen und überschreibt den Source-eigenen
Lookup (Script ist Owner der DB-Verbindung, Source ist dummer Adapter).
Warnung umformuliert: kein Dukascopy-Verweis mehr (D15). `_make_source`-
Helper im Test nimmt jetzt einen `symbol_lookup`-Parameter (Default:
DAX→DE40, CAC→FR40, sonst nichts). Lock-in-Test
`test_epic_map_does_not_contain_path_c_territory` umbenannt zu
`test_symbol_lookup_default_omits_path_c_territory` (dieselbe These,
neue Quelle der Wahrheit). Zwei neue Tests:
`test_fetch_window_returns_empty_when_no_lookup_was_supplied` (sichere
Default-Richtung) und
`test_run_capital_backfill_symbol_lookup_kwarg_overrides_source`
(Script-Override-Semantik). `scripts/probe_capital.py`: historischer
"was EPIC_MAP aktuell 'DE40' / 'FR40' nennt"-String zeigt jetzt auf
`instrument_source_availability.source_symbol` (gleiche Identitäts-These
wie für yF; D2).

**Commit 2 — `phase14: code+tests -- B2 script builds symbol_lookup
from SourceAvailabilityStore`** (`6e8148e`, 2 files, +145/-9).
`scripts/capital_backfill.py`: neue `_build_symbol_lookup()`-Helper
schließt die DB an `SourceAvailabilityStore` und gibt einen
Closure-Lookup + die Store-Instanz zurück. Fail-soft: ohne Migration
007 liefert der Lookup `None` für jedes Epic → der Backfill wird zu
einem No-Op statt zu werfen. WARNING-Log wenn keine Capital-Zeile in
der Tabelle steht (Operator-Hinweis: Discovery hat noch nie gelaufen).
Zwei neue Tests: Migration-007-missing (null-lookup, kein Crash) +
SourceAvailabilityStore-Aufruf-Pfad (mocked store, prüft
`symbol_for(epic, 'capital', '1m')` als Schlüsselparameter).

**Commit 3 — `phase14: code+tests -- B3 source_delta.py drei Fälle`
(`ac54825`, 2 files, +373/-53)**. Plan §6 B3:
`scripts/source_delta.py` liest die Quellenliste aus
`instrument_source_availability` (statt hartkodiert yf+ls) und
unterscheidet drei Fälle pro Trade:
- `not_available`: kein `status='ok'` für diese Epic (prinzipiell
  nicht abrufbar — Beispiel: SP35 vor dem ersten Discovery-Lauf).
- `available_but_empty`: Quellen registriert, aber keine Bars im
  Fenster (Beschaffungslücke).
- `compared`: ≥ 2 Quellen vergleichbar → `comparison` ist `agree` oder
  `diverge`.
Fail-Soft bei fehlender Migration 007 (`_load_available_sources` fängt
`OperationalError` → leerer Dict → jede Trade ist `not_available`, Exit
0, `divergence_rate=None`). Report-Header trägt jetzt
`trades_not_available` und `trades_available_but_empty` zusätzlich zu
den alten `trades_agree`/`trades_diverge`-Counters. Drei neue Tests
+ drei bestehende umgeschrieben (`row["kind"]`-Werte sind jetzt
`compared`+`comparison` statt direkt `agree`/`diverge`;
`test_missing_source_counted_as_incomparable` →
`test_available_but_empty_when_one_source_has_no_bars`).

**Smoke-Test** (`phase5_execution/scripts/smoke_test.py --broker
ig_demo`) — einmal gelaufen auf Nikinger-Erlaubnis (nicht Phase-14-
Stoff). Ergebnis sauber: `NO_TRADE -- time_window: 19:01 outside trade
window 09:00-17:30 Europe/Berlin` (heute Samstag 19:01, kein Trade-
Fenster; Phase 5 baut den Cycle sauber auf, alle Gates + VETOs laufen,
OrderDecliner blockt, kein Live-Touch). Beweis: die Phase-13-Bibliothek
ist unter dem Phase-5-Bot konsumierbar — kein Import- oder Wiring-Bruch
aus B2/B3.

### Verified

- Regression-Sweep aller 14 Suiten + root `tests/` (Stand nach den drei
  Commits, ohne Docs-Edits):
  | Suite | Vor Session 8 | Nach | Δ |
  |---|---:|---:|---:|
  | phase1_broker_wrapper | 95 | 95 | 0 |
  | phase2_persistence | 77 | 77 | 0 |
  | phase3_external_data | 104 | 104 | 0 |
  | phase4_research | 155 | 155 | 0 |
  | phase5_execution | 173 | 173 | 0 |
  | phase6_debate | 76 | 76 | 0 |
  | phase7_reward | 138 | 138 | 0 |
  | phase8_scheduler | 244 | 244 | 0 |
  | phase9_universe | 87 | 87 | 0 |
  | phase10_v3 | 165 | 165 | 0 |
  | phase12_data_foundation | 143 | 143 | 0 |
  | phase13_live_data | 67 | 74 | **+7 (B2: 4, B3: 3)** |
  | phase14_discovery | 22 | 22 | 0 |
  | meta_m1_harness | 28 | 28 | 0 |
  | root `tests/` | 80 | 80 | 0 |
  | **Σ** | **1652** | **1659** | **+7** |
  *(Cross-check: B2=3+1=4, B3=3 — 7 neue Tests, keine Lücke.)*
- `grep -rn "EPIC_MAP" phase13_live_data/ --include=*.py` → **leer**
  (Exit 1, kein Treffer). Akzeptanzkriterium B2 / A2 grün.
- Working tree clean vor Commit-Kette (außer `data/`-Ordner, gitignored),
  keine Cross-Phase-Edits außerhalb der freigegebenen Phase-13-Liste
  (`backfill.py` ist Phase-13-Territorium per Freigabe 2026-08-22,
  `scripts/probe_capital.py` ist Phase-13-Territorium).
- `git log --oneline -4` zeigt die drei B2/B3-Commits + der folgende
  Docs-Commit: saubere Kette, ein Commit pro Schritt.

### Findings (drei)

- **`EPIC_MAP` lebt weiter in Kommentaren — Akzeptanz sagt nein.** Der
  String tauchte in 8 Code-/Test-Kommentaren + einem JSON-String im
  `probe_capital.py`-Payload auf, alle als historische Erklärungen.
  Akzeptanzkriterium B2 / A2 ist explizit *"`grep … --include=*.py`
  ist leer"* — nicht *"`EPIC_MAP` existiert nicht als Variable"*.
  Habe alle 8 Vorkommen aus den `.py`-Dateien entfernt. Die Geschichte
  lebt jetzt im Plan (`docs/concepts/phase14_discovery_plan.md` §6 B2)
  und in den Session-Blocks (1–7); Code beschreibt den Ist-Stand.
- **`run_capital_backfill` Override-Semantik.** Habe den `symbol_lookup`-
  kwarg als **Override** (nicht "setze nur wenn None") implementiert:
  der Caller (Script) ist Owner der DB-Verbindung, der Source ist
  dummer Adapter. Der `test_run_capital_backfill_symbol_lookup_kwarg_overrides_source`
  pinnt diese Semantik. Alternative wäre gewesen "setze nur wenn source
  noch default" — die hätte einen Sentinel gebraucht und mehr Edge-
  Cases. Override ist die ehrliche Richtung.
- **`source_delta.py` Migration-007-fail-soft.** `_load_available_sources`
  fängt `OperationalError` und gibt `{}` zurück → das Hauptprogramm
  behandelt jede Epic als "kein `status='ok'`" → `not_available` für
  jede Trade. Test `test_fail_soft_when_availability_table_missing`
  pinnt das mit einer zweiten DB (nur 004–006, ohne 007). Exit 0,
  Report-Header voll, divergence_rate = None. Das ist das gleiche
  Pattern wie `_build_symbol_lookup` im Script — Phase-13-Code wird
  nicht zum Pfad, an dem Migration 007 durchgesetzt wird.

### Unverändert offen

- **Block C** (Daemon + Web-UI-Scharfschalten) — C1 (`arm.py`),
  C2 (`run.py`), C3 (Web-UI-Endpoints + Banner), C4 (`run_discovery.sh`).
  Empfehlung: nächste Session.
- **Block D** (Closeout) — kommt am Ende der Phase, sobald A1–A8 grün
  sind (A1 ✅, A2 ✅, A3 ✅, A4 ✅, B1b ✅, B2 ✅, B3 ✅, C1–C4 ⬜).
- **Hygiene-Tickets** aus Session 4: `*.sqlite.bak-*` in `.gitignore`,
  `ROADMAP.md:427` Aktualisierung — bewusst zurückgestellt.
- **Plan-§9-Drift-Listeneintrag #2 erweitern** in der nächsten Plan-
  Session (Editor-Notiz für Phase-15-Planung oder eine Phase-14-
  Closeout-Session). Die jetzige Session bestätigt ihn (alle Anker
  waren korrekt), aber der Eintrag könnte den
  `scripts/probe_capital.py:385`-Befund prominenter machen.

### NEXT

- **Operator (Nikinger):** Push-Freigabe für die 3 Commits
  (`bb095df`, `6e8148e`, `ac54825`) + diesen Docs-Commit. Stand jetzt:
  3 Commits vor `origin/main`.
- **Ausführende Session (nächste):** **Block C** — Daemon
  (`source_registry/run.py`, Muster `data_foundation/run.py`) +
  Web-UI-Scharfschalten (`webui/api.py` + `static/index.html` +
  `static/app.js`). C1 zuerst (kleines Modul, kein Netz, fail-soft
  per D10), C2/C3 danach, C4 zuletzt (run_discovery.sh-Wrapper).
- **Beweiswoche läuft separat weiter** (Phase 13 Plan §7 P1–P9). B2/B3
  berühren die laufende Beweiswoche nicht (kein Konsumentenpfad
  schreibt in `instrument_source_availability` während der Beweiswoche;
  die einzigen Schreiber sind A4-Projektion — wartet auf den ersten
  Resolver-Tick — und C2-Daemon — wartet auf ARM).

## Session stopped — 2026-08-22 (Session 6: B1a-Operator-Probe gelaufen + Findings dokumentiert)

> **Auftrag:** Nikinger hat die B1a-Probe live ausgeführt (Demo, kostenlos) und
> den vollständigen JSON-Output im Chat gepastet. Anweisung: „alle Dokumente
> Updaten und pushen bitte". Output ist die **beobachtete Antwort-Form**,
> gegen die `CapitalSource.discover()` (B1b) gebaut wird. Snapshot-Datei
> angelegt; Session-Block dokumentiert die 8 wichtigsten Befunde; Push der
> 4 ungepushten Commits liegt beim Operator.

### Completed

**`phase14_discovery/PHASE14_B1A_PROBE_OUTPUT_2026-08-22.md`** (NEU, L3-Snapshot) —
Roh-Output der Operator-Probe + 8 nummerierte Befunde mit Mapping auf B1b.
Header-Karte nach Doku-Konvention (`status: snapshot`, `read-when`,
`up:`/`down:`). Cross-Verweis vom Plan (`docs/concepts/phase14_discovery_plan.md`).

### Die 8 Befunde — was B1a gelehrt hat

| # | Befund | Konsequenz für B1b |
|---|---|---|
| 1 | Response ist `{ "markets": [...] }` — Array, je Eintrag ein Market-Objekt | `discover()` iteriert über `markets`, filtert, emittiert pro Match eine `SourceAvailability` |
| 2 | **`epic`-Feld ist das gesuchte Source-Symbol** (`"DE40"`, `"FR40"`, `"SP35"`) | geht 1:1 in `instrument_source_availability.source_symbol` — exakt dieselbe Identitäts-These wie yF (B2) |
| 3 | `instrumentType` ist **`"INDICES"`** (nicht `"CFD"`, wie der bestehende `live_data/backfill.py:339-366`-Filter annimmt) | B1b filtert auf `"INDICES"`. **Offener Filter-Bug im bestehenden Code** — der Fallback `[m for m in markets if m.get("instrumentName") == index_name]` rettet es heute. B1b macht es richtig; bestehender Code wird in B2 oder als separates Hygiene-Ticket nachgezogen (Nikinger-Entscheidung) |
| 4 | **Spain 35 IST verfügbar** als `epic: "SP35"` (war bisher Path-C-Territorium in Phase 13) | Block B erweitert Coverage. Dukascopy-Fallback für SP35 wird überflüssig |
| 5 | Sucht mit `searchTerm=<instrumentName>` → erster Eintrag mit `instrumentName == searchTerm` + `instrumentType == "INDICES"` ist die kanonische Übersetzung | B1b-Such-Algorithmus: `for epic in input: name = instrument_universe[epic].name; GET /markets?searchTerm=name; first INDICES match → SourceAvailability` |
| 6 | `delayTime: 0` für alle drei → **Echtzeit** | `history_min_days=30, latency_min=0` für die `capital`-Zeilen (NICHT die 15-Min-yF-Heuristik) |
| 7 | Jeder Eintrag hat `instrumentId` (numerisch), `epic` (kurz), `symbol` (lang/kurz), `bid`/`offer` (Live-Preise), `lotSize`, `tickSize`, `pipPosition` | B1b braucht nur `epic` + `instrumentName` + `instrumentType`. Andere Felder sind für Discover irrelevant — kein Schema-Mapping nötig |
| 8 | `marketStatus: "CLOSED"` für alle drei am Wochenende | erwartbar (Markt zu), **kein** B1b-Sonderfall. Discover prüft Verfügbarkeit via Existenz des Eintrags, nicht via `marketStatus` |

### Operator-Setup (verifiziert, 2026-08-22)

- **Auth funktioniert:** `POST /api/v1/session` → HTTP 200, `account_type=CFD`,
  CST + X-SECURITY-TOKEN im Response-Header. **Demo-Keyring `trading-bot-capital`
  ist intakt** (Vorbedingung für B1b gegeben).
- **Drei Suchterme, drei Treffer** — alle im ersten Listeneintrag.
- **Probe-Script** (`probe_capital.py --markets --terms ...`) tat ohne
  Modifikation. Kein Code-Edit in dieser Session.

### Nicht-B1b-Stoff (separate Tasks)

- **B2 (`EPIC_MAP` raus):** Plan §6 B2 wartet auf B1b. Heute gibt
  `SourceAvailabilityStore.symbol_for(epic, 'capital')` für keinen Epic
  einen Wert (Tabelle 007 wurde nur mit yF-Backfill gefüllt). Nach B1b
  liefert sie für DE40/FR40/SP35 die richtigen Kürzel.
- **Offener Filter-Bug im bestehenden Code** (`live_data/backfill.py:339-366`,
  `backfill.py:300-316`): `"CFD" in instrumentType` matched nie — die
  Realität ist `"INDICES"`. Der Fallback `candidates = [m for m in markets
  if m.get("instrumentName") == index_name]` rettet es heute. **Nicht in
  dieser Session gefixt** — bewusst zurückgestellt (Phase-14-Cross-Phase-
  Edit nur für Phase 2/8/9/12/13 freigegeben; eine Edit in `backfill.py`
  ist Phase-13-Territorium und gehört in B2 oder als separates Ticket).
  **Empfehlung:** in B2 mit aufnehmen, weil B2 den `EPIC_MAP`-Hintergrund
  eh anfasst.

### Verified (heute nachgemessen, 2026-08-22)

| Suite | Vor B1a | Nach B1a | Δ |
|---|---:|---:|---:|
| (alle Suiten) | 1634 | 1634 | 0 (B1a war Operator-Run, kein Code-Edit) |

Working tree clean (außer Hygiene-Findling `*.sqlite.bak-*`-Pattern aus Session 4),
`ps aux | grep scheduler.run` leer, kein Live-DB-Write. Cross-Phase-Edits: null
in dieser Session.

### NEXT

- **Operator (Nikinger):** Push-Freigabe für die **4 ungepushten Commits**:
  ```bash
  cd /home/trading-bot/trading-bot
  git push origin main
  ```
  Reihenfolge: `fd9e7f8` (A3-Code, 491 Zeilen), `888ee01` (Session-4-Docs,
  Rotation), `69cfc31` (B1a-Script-Erweiterung, +79 Zeilen),
  `+der B1a-Snapshot + Session-6-Docs aus dieser Session` (nach commit).
- **Ausführende Session (nächste):** Plan §6 **Block A4** (yF-Projektion
  in `UniverseStore.set_symbol`) **ODER** Block B1b (`CapitalSource.discover()`
  gegen die beobachtete Form, Snapshot als Quell-der-Wahrheit). Beide sind
  jetzt baubar; meine Empfehlung **B1b zuerst** weil:
  1. Der Snapshot ist die genaueste Spec — direkt in Code umsetzbar.
  2. Block B2 wartet auf B1b.
  3. A4 ist orthogonal und kann danach kommen.
  Sag, welche Reihenfolge.
- **Unverändert offen:** A4 (yF-Projektion), B2 (`EPIC_MAP` raus), B3
  (`source_delta.py` drei Fälle), C (Daemon), D (Closeout). Plus die zwei
  Optional-Hygiene-Tickets aus Session 4 (`.gitignore`-Pattern, `ROADMAP.md:427`).

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

---

## Session stopped — 2026-08-22 (Session 4: Block A3 — Quell-Profile IG/LS/yF)

> **Auftrag:** Nikinger-Anweisung „Arbeite die nächsten Schritte nach Plan ab"
> — Plan-konform weiter mit Block A3 (nach A1 + A2 grün). B1a Capital.com-`/markets`-
> Probe war als Option B angeboten („ich baue den Script-Erweiterung jetzt"), Nikinger
> hat nicht geantwortet → Default Plan-konform: A3 zuerst, B1a kommt später wenn die
> Probe sowieso laufen muss (vor B1b).

### Completed

**`phase14_discovery/source_registry/sources.py`** (NEU) — drei Source-Profile,
keine einzige macht einen Netz-Call:

| Klasse | Eingabe | Status | Origin | Netz |
|---|---|---|---|---|
| `IGDerivedSource` | `Iterable[str]` von IG-Epics | `ok` | `derived` | **nein** — D6 |
| `LSStaticSource` | `Iterable[str]` von IG-Epics | `no_source` (heute; `bars.source='ls'=0`) | `derived` | **nein** — statisch |
| `RegistryYFSource` | `Iterable[str]` + Duck-Store mit `.get(epic)` | 1:1 `data_source_status`-Spiegelung | `registry` | **nein** — D4 |

`max_probe_calls` wird respektiert, **nie** ausgeschöpft — alle drei liefern
`probe_calls_used == 0`, der Daemon bucht nichts in `source_spend` (D13). History/
Latency-Konstanten sind Modul-Level: IG 30d/0min (echtzeit, vollständige Broker-
Historie), yF 7d/15min (Phase-12-Beobachtung), LS 0d/0min (irrelevant solange
`no_source`). `RegistryYFSource` packt store-seitige Fehler ins `errors`-Tupel
(fail-soft per Plan §8.5).

**`phase14_discovery/tests/test_sources.py`** (NEU, 9 Tests = 8 aus Plan + 1
Grep-Komplement zu Test 2):

| Test | Was |
|---|---|
| 1 | `IGDerivedSource` — eine Zeile pro Epic, status='ok', origin='derived', source_symbol=None |
| 2 | **D6-Structural-Cost-Test**: `_ExplodingBroker` (jeder Methoden-Aufruf → AssertionError) als Sentinel, discover() läuft durch, `probe_calls_used == 0` |
| 3 | Grep-Komplement: `import broker_wrapper` / `from broker_wrapper` muss 0 Treffer in `source_registry/` liefern |
| 4 | `RegistryYFSource` mit `_ThrowingStore` (AssertionError auf `.get()`) → SourceProfile mit `errors`, kein Raise |
| 5 | `RegistryYFSource` spiegelt `data_source_status='ok'` 1:1 nach `status='ok'` (D18/A4-Identität) |
| 6 | `RegistryYFSource` spiegelt `no_intraday_source` 1:1, **kein Downgrade** auf `no_source` |
| 7 | `RegistryYFSource` setzt `origin='registry'` auf jeder Zeile |
| 8 | `LSStaticSource` liefert `no_source` für jede Epic |
| 9 | Fail-soft Pattern generisch: `_BrokenStore` (RuntimeError statt AssertionError) → errors-Tupel statt Raise |

Test 2 + Test 3 sind die **D6-Akzeptanz**: strukturelle Zusicherung, dass
`IGDerivedSource` nie `/prices` oder `search_markets` ruft. Test 2 fängt jeden
Aufruf ab, Test 3 pinnt die Modul-Struktur (kein `broker_wrapper`-Import darf
jemals unter `source_registry/` landen).

### Operator-Schritte dieser Session (Nikinger-Ausführung)

- **Push durch** (`6ca9ed4..360683f`): 2 Commits von Session 3, kein Konflikt.
- **Backup der Produktions-DB** angelegt:
  `data/trading_bot.sqlite.bak-20260822-131529` (1 892 352 Bytes, identisch
  zur Live-DB). Vor Produktions-Migration 007 anwendbar — A4 (yF-Projektion)
  muss vorher live sein, sonst liefert die Tabelle nach 007 zwar die historische
  Wahrheit, aber keine Fortschreibung.
- **B1a Capital.com-`/markets`-Probe:** nicht ausgeführt — Block-B-Arbeit, der
  `--markets`-Modus in `probe_capital.py` muss zuerst gebaut werden (Plan §6 B1a).
  Anwendbar sobald B1a-Code steht; bis dahin A3/A4 plan-konform.
- **Hygiene-Findling (außerhalb des Phase-14-Scope, NICHT in dieser Session
  behoben):** `data/trading_bot.sqlite.bak-20260822-131529` zeigt sich als
  untracked, weil `.gitignore:90` `*.sqlite` matcht — `*.sqlite.bak-…` aber
  nicht. Der 2026-07-11-Backup zeigt das gleiche Symptom (auch untracked). Fix
  wäre eine 1-Zeilen-Pattern-Erweiterung (`*.sqlite*` oder explizit
  `*.bak`), bewusst NICHT in dieser Session — Cross-Phase-Edits außerhalb der
  freigegebenen Liste (Phase 2/8/9/12/13) sind erneut freigabepflichtig.

### Verified (heute nachgemessen, 2026-08-22)

| Suite | Vor A3 | Nach A3 | Δ |
|---|---:|---:|---:|
| phase14_discovery | 13 | 22 | 22 (8 aus Plan + 1 Grep-Komplement) |
| **Summe (Regression)** | **1625** | **1634** | **+9** |

Working tree clean (außer dem Hygiene-Findling oben), `ps aux | grep scheduler.run`
leer, kein Live-DB-Write. Cross-Phase-Edits: null (A3 ist vollständig innerhalb
des `phase14_discovery/source_registry/`-Pakets).

### Cross-Phase-Anmerkungen für A4

- **A4 muss rohes SQL über `self.conn` benutzen** (Plan §6 A4) — kein
  `source_registry`-Import in `phase9_universe`. Heute ist die Spaltenliste
  an zwei Stellen: Migration 007 (`phase2_persistence/migrations/007_…sql:13-22`)
  und `SourceAvailabilityStore.upsert`
  (`phase14_discovery/source_registry/store.py`). Beide müssen exakt dieselbe
  Spaltenliste + dieselbe ON-CONFLICT-Klausel verwenden. Der Doppelschreiber-
  Gleichheitstest (Plan §6 A4 Test 6) fängt Drift ab.
- **`source_symbol ≡ yf_ticker WHERE source='yf'`** (B2-Identität): A4 schreibt
  `source_symbol = yf_ticker`, exakt wie Migration-007-Backfill und
  `RegistryYFSource.discover()`. Drei Stellen, dieselbe Spalte.

### Next

- **Operator (Nikinger):** Push-Freigabe für den A3-Commit (`fd9e7f8`).
  Mit Session 4 dann insgesamt 3 Commits in dieser Woche: A2-Code,
  A3-Code, Session-4-Docs.
- **Ausführende Session (nächste):** Plan §6 **Block A4** — yF-Projektion in
  `UniverseStore.set_symbol`. Sechs Tests gegen die heutige Doppelschreiber-
  These: dieselbe Zeile, einmal über `set_symbol`, einmal über
  `SourceAvailabilityStore.upsert` (Plan §6 A4 Test 6).
- **Unverändert offen:** B1a Capital.com-`/markets`-Probe (Plan §9.3).
  Empfehlung: **vor** A4 bauen, weil A4 der letzte Block-A-Step ist und ab dann
  der Discovery-Daemon (Block C) die nächste sinnvolle Arbeit wäre — und der
  Daemon braucht für `capital`-Zeilen die Probe. Sonst gibt es nur IG/LS/yF
  im Daemon-Output, kein Capital.com.
- **Optional (Nikinger-Entscheidung, unabhängig):**
  - `.gitignore`-Pattern für `*.sqlite.bak-*` (1 Zeile, s. Hygiene-Findling).
  - `ROADMAP.md:427` Korrektur-Eintrag (zweiter Roll-over, s. Session-2-Finding).

---

## Session stopped — 2026-08-22 (Session 3: Block A2 — Migration 007 + SourceAvailabilityStore)

> **Auftrag:** Nikinger-Bestätigung „gehe nach Plan vor" → Block A2.
> Plan §6 A2 hat vier Edits: Migration 007, `models.py`, `store.py`, 12 Tests
> + Versions-Anpassung im P2-Migration-Test. **Ein Commit**, **null
> Aufrufer verdrahtet** (A2 ist Fundament, A3/A4 ziehen nach).

### Completed

**`phase2_persistence/migrations/007_phase14_source_availability.sql`** (NEU,
additive only) — legt `instrument_source_availability` an (10 Spalten, PK
`(epic, source, resolution)`) **plus** den yF-Backfill als `INSERT … SELECT`
aus `instrument_universe` in derselben Datei. Backfill ist nicht in einem
Resolver-Lauf, weil `SymbolResolver.resolve_epic` `set_symbol` in 6 von 8
Pfaden NICHT ruft (`symbols.py:194-199, 207-210, 213-214, 219-220, 222-223,
229-230`) — die 3 `SUN*`-Epics stehen bereits auf `no_intraday_source` und
bekämen sonst nie eine Projektionszeile. Der Backfill kauft zusätzlich den
Identitätsbeweis (B2: `source_symbol = yf_ticker`) VOR der ersten Zeile
neuem Code; Test 11 prüft das gegen die heutigen 22 Zeilen Substrat.
Kein `FOREIGN KEY` auf `epic` — bewusst (Auditkette: 001–006 haben keinen
FK, `UniverseStore` öffnet ohne `PRAGMA foreign_keys = ON`, ein
nicht-erzwungener FK ist Doku die sich als Constraint verkleidet).

**`phase14_discovery/source_registry/models.py`** (NEU) — Dataclasses +
Konstanten + Protocol, Phase-Isolation per Duplikation (Muster
`UniverseStore`/`Budget`/`BarArchive`): `KNOWN_AVAILABILITY_STATUSES`
dupliziert `KNOWN_DATA_SOURCE_STATUSES` aus Phase-12 (D18 — identischer
Vokabular, Drift wäre der nächste Bug); `REGISTRY_SOURCES` spiegelt die
4 heute existenten Quellen (`ig`/`yf`/`ls`/`capital`); `KNOWN_ORIGINS`
(discovery/registry/derived/operator); `KNOWN_RESOLUTIONS` (1m/5m/1h/1d).
`SourceAvailability(frozen=True)` mit `__post_init__`-Validierung an allen
drei Vokabularen; `SourceProfile(frozen=True)` mit `rows`/`probe_calls_used`/
`errors`; `Source` Protocol mit `name()`/`discover(epics, *, max_probe_calls)`.

**`phase14_discovery/source_registry/store.py`** (NEU) —
`SourceAvailabilityStore` mit eigener `sqlite3`-Connection
(Phase-Isolation), 8 Methoden exakt nach Plan §5.3: `upsert`,
`upsert_many`, `for_epic`, `for_source`, `symbol_for`, `stale_rows`,
`close`. `upsert` ist `INSERT … ON CONFLICT(epic, source, resolution) DO
UPDATE` (Muster `UniverseStore.upsert_discovered`).
`symbol_for` gibt `None` statt zu raisen — Block-B2-Vertrag: „kein
Eintrag" liest sich als „diese Quelle kann das nicht", Fall-Back ist
Sache des Konsumenten (nicht des Stores). `stale_rows` nutzt
lexikografischen Vergleich über `last_verified_utc < cutoff_iso` — nur
sicher weil jeder Timestamp aus derselben `utc_iso_now`-Formatter kommt
(Test 13 pinnt den Format-Vertrag).

**`phase14_discovery/tests/test_store.py`** (NEU) — 13 Tests (12 aus Plan +
1 Format-Contract-Pin). Test 11 ist der harte Beweis: das heutige
22-Zeilen-Substrat wird in eine Fixture-DB gesetzt (5 active+ok, 3
active+no_intraday_source, 14 verified+unverified), Migration 007 wird
**danach** angewendet, und `for_source('yf', status='ok')` muss **genau**
die 5 Epics aus Plan §2.2 liefern — die Identitäts-These hält **bevor**
irgendwelcher neuer Code sie brechen könnte. Test 10 pinnen D17: die
Tabelle gattet einen Source außerhalb von `KNOWN_SOURCES` NICHT (eine
Zeile mit `source='dukas_copy'` wird geschrieben + gelesen; der
Archiv-Schreibpfad ist der Gatekeeper, nicht die Tabelle).

**`phase2_persistence/tests/test_migrations.py`** (Anpassung, keine Test-
Anzahl-Änderung) — Versions-Nummern 6 → 7 in vier Tests
(`test_fresh_db_reaches_version_6` → `_version_7`, `test_rerun_is_noop`
count 6 → 7, `test_find_pending_respects_current` Liste 1..6 → 1..7,
`test_database_run_migrations_idempotent` 6 → 7);
`_EXPECTED_TABLES` um `'instrument_source_availability'` ergänzt.

### Verified (heute nachgemessen, 2026-08-22)

| Suite | Vor A2 | Nach A2 | Δ |
|---|---:|---:|---:|
| phase2_persistence | 77 | 77 | 0 (Versions-Nummern im Test-Body) |
| phase14_discovery | 0 | 13 | +13 (12 aus Plan + 1 Format-Contract) |
| **Summe (Regression)** | **1612** | **1625** | **+13** |

Working tree clean (nach jedem Commit), `ps aux | grep scheduler.run`
leer, kein Live-DB-Write, keine Cross-Phase-Edits außerhalb der
freigegebenen Liste (Phase 2/8/9/12/13 — alle im Scope). A2 hat null
externe Aufrufer von `source_registry` (verifiziert per `grep -rn
source_registry`): die einzigen Treffer sind die Paket-Definition
selbst und der editable-install-Marker in `.venv`. Fundament steht
isoliert.

### Cross-Phase-Anmerkungen für die nächsten Schritte

- **A4 (yF-Projektion in `UniverseStore.set_symbol`)** muss denselben
  INSERT-ON-CONFLICT-Pfad benutzen wie `SourceAvailabilityStore.upsert`,
  und die Spaltenliste steht an zwei Stellen (Migration 007 vs.
  `store.py:_project_availability`). Plan §6 A4 sagt: **rohes SQL über
  `self.conn`**, kein `source_registry`-Import in `phase9_universe` —
  Paket-Zyklus vermeiden. Der Doppelschreiber-Gleichheitstest (Plan §6 A4,
  Test 6) fängt Drift ab, sobald A4 baut.
- **`symbol_for` ist genau die Methode, die `run_capital_backfill` nach
  Block B2 ruft** statt `EPIC_MAP.get(epic)` — heute gibt sie
  `None` für alle Epics, weil die `capital`-Zeilen erst nach B1b/B2
  geschrieben werden (B1a-Sonden-Output fehlt noch — Operator-Run
  steht aus, Plan §9.3).

### Next

- **Operator (Nikinger):** Push-Freigabe für den A2-Commit (`4ef7535`).
- **Ausführende Session (nächste):** Plan §6 **Block A3** — drei
  Quell-Profile: `IGDerivedSource` (D6, **null Netz**, jede
  `instrument_universe`-Epic ⇒ abgeleitete Zeile), `LSStaticSource`
  (`bars.source='ls'` = 0 heute → `no_source`), `RegistryYFSource`
  (Projektion aus `UniverseRecord`-Shape, `origin='registry'`).
  Der **strukturelle Kostentest** (Test 2 aus A3): ein Broker-Fake,
  dessen jede Methode `AssertionError` wirft — `IGDerivedSource.discover()`
  läuft trotzdem durch, `probe_calls_used == 0`. Das ist die A3-Akzeptanz
  für D6.
- **Unverändert offen:** Capital.com `/markets`-Probe (B1a, Operator,
  Demo, kostenlos). Ohne den Output wird B1b nicht gebaut — die
  `capital`-Zeile kommt dann als `origin='operator'` über ein Seed-Script.
- **Unverändert offen:** Backup von `data/trading_bot.sqlite` vor
  Produktions-Anwendung von Migration 007 (Plan §9.13).
- **Optional (Nikinger-Entscheidung):** `ROADMAP.md:427` Korrektur-Eintrag
  (zweiter Roll-over, datiert 2026-08-22 — s. Session-2-Finding).

---

## Session stopped — 2026-08-22 (Session 2: Block 0 + A1 — Skeleton + stale_source-Fix)

> **Auftrag:** Nikinger-Auftrag aus der Stand-up-Notiz: Einstieg Block 0.0
> (Sweep gegen die 1608 reproduzieren), dann 0.2 → 0.3 → 0.4, **erst danach
> A1** (der `stale_source`-Fix). Bis A1 grün ist: `enable_divergence_sampler`
> bleibt aus. Vier Commits, atomar je Schritt.

### Completed

**Block 0.0 (Baseline)** — Regression-Sweep reproduziert exakt die 1608 aus
Plan §2.1 (kein Test verschwunden, keine Drift): P1 95 · P2 77 · P3 104 · P4 155
· P5 173 · P6 76 · P7 138 · P8 244 (+1 W) · P9 80 · P10 165 · P12 143 · P13 50 ·
M1 28 · root 80. Working tree clean, `ps aux | grep scheduler.run` leer (kein
Bot-Prozess). **Block 0.0 Akzeptanz erfüllt.**

**Block 0.1 — skip, dokumentiert:** Turbo-/Legacy-Grep-Ritual ist No-Op
(siehe Plan §2.3). Die ausführende Session hat das Ritual **nicht wiederholt**
und verweist stattdessen auf den Session-1-Block.

**Block 0.2 (Doc-Commit `999464a`)** — Nummerierungs-Rollover V4: Phase 14
→ Phase 15, Phase 14 = Discovery-Then-Deterministic. Verbatim-String-Anker:

| Datei | Änderung |
|---|---|
| `ROADMAP.md:625/629/634/638/643` | `### 14a/b/c/d/e` → `### 15a/b/c/d/e` (vormals-Liste erweitert) |
| `README.md:126` | `Phase 14 (V4)` → `Phase 15 (V4)` (mit dritter Umnummerierung 2026-08-22) + Phase-14-Discovery-Eintrag in der dazwischenliegenden-Phasen-Liste |
| `phase10_v3/CLAUDE.md:21` | `down:`-Link-Liste um Phase 14 (Discovery) + Phase 15 (V4) erweitert |
| `ARCHITECTURE.md:60` | alte `V4 moves to Phase 14`-Zeile stehen lassen + datierte Korrekturzeile darunter (Auditkette) |
| `ARCHITECTURE.md:171/230` | `Phase 14e/d (V4)` → `Phase 15e/d (V4)` |
| `ARCHITECTURE.md:261` | Phase 14 (V4) durch zwei Zeilen ersetzt (Phase 14 Discovery mit Plan-Link + Phase 15 V4 deferred) |
| `phase13_live_data/CLAUDE.md` (E6 closeout) | drei Block-C-Modulzeilen `final (Block C geschlossen 2026-08-22)`; Testzahl 39 → 50; „1508 passed" → „1608 passed" mit Summenkorrektur-Fußnote |

**Akzeptanz §6 0.2 erfüllt:** `grep -rn "Phase 14 (V4)" --include=*.md .` liefert
nur noch Treffer in `docs/concepts/phase14_discovery_plan.md` (Plan-Snapshot,
📕, nicht editierbar). 1 Doc-Commit, +35/-22 Zeilen über 5 Dateien.

**Block 0.3 (Fix-Commit `4681d68`)** — drei Phase-13-Script-Bugs (B3/B4/B5)
in einem Commit + drei neuen Tests:

- **B3** `scripts/capital_backfill.py`: eigenes `--universe-db`-Argument mit
  Default `data/trading_bot.sqlite` (Muster `data_foundation/run.py:114-116`).
  `_resolve_epics(args)` → `args.universe_db` (war `args.db`, was per Default
  auf `bars.sqlite` zeigte, wo `instrument_universe` nicht existiert).
- **B4** derselben Datei: `results: dict[str, int] = {}` **vor** dem `try`
  gebunden. Vorher: NameError im except-Handler verschluckte die echte
  Fehlermeldung. Nachher: `partial_results` immer vorhanden, leer im Fehlerfall.
- **B5** `live_data/backfill.py:414-416`: `written += archive.insert_bars(...)`
  statt `written += 1`. Docstring auf „genuinely new rows written" präzisiert
  (`archive.insert_bars` gibt `cur.rowcount` über `INSERT OR IGNORE` zurück;
  Duplikate zählen nicht).

**Bonus-Hygiene-Fix (notwendig, um B5 wirksam zu testen):**
`test_run_capital_backfill_writes_to_archive` nutzte einen hardcoded
`/tmp/test_capital_backfill_e2e/`-Pfad mit Restbars vom 21.08. — der alte
`written += 1` verbarg das (zeigte 2 obwohl 0 neue Rows), B5 macht das sichtbar
(zeigt jetzt ehrlich 0). Umgestellt auf `tmp_path`-Fixture: per-Test frische
DB. Auch der `unmapped`-Test analog. `/tmp/test_capital_backfill_{e2e,unmapped}/`
aufgeräumt.

**Drei neue Tests** (`phase13_live_data/tests/test_capital_backfill_script.py`):
1. `_resolve_epics(--auto)` öffnet Universe-DB-Pfad, nicht Bars-DB-Pfad
   (`monkeypatch` auf `universe.UniverseStore` — Paket-Binding, nicht Submodul).
2. `run_capital_backfill` mit pre-populated Bar (gleicher PK wie die API-Antwort)
   → `results[epic] == 0`, nicht `1` (B5-Beweis).
3. `main()`'s top-level except emittiert JSON mit `partial_results: {}`,
   kein NameError (B4-Beweis).

**Akzeptanz §6 0.3 erfüllt:** `phase13_live_data/tests` 50 + 3 = **53 grün**;
Regression-Sweep 1608 + 3 = **1611**.

**Block 0.4 (Scaffold-Commit `97ffdc2`)** — Phasen-Gerüst, kein funktionaler
Code:

```
phase14_discovery/
├── CLAUDE.md            ← existiert (Plan-Commit), nicht neu angelegt
├── README.md            ← NEU: public surface, Modul-Tabelle als Skeleton
├── pyproject.toml       ← NEU: name='source_registry', editable-install-fähig
├── requirements.txt     ← NEU: nur pytest
├── source_registry/__init__.py   ← NEU, leer
└── tests/__init__.py             ← NEU, leer
```

`scripts/dev_install.sh`: `phase14_discovery` in den editable-install-Loop
aufgenommen, „all twelve packages" → „all thirteen packages", P14 in die
Header-Komposition aufgenommen. `docs/INDEX.md`: README.md-One-Liner im
selben Commit (Doku-Hygiene-Konvention); Active-Phases-Header von „Bau nicht
begonnen" auf „Skeleton + Block 0 in main, funktionaler Bau ab A1"
korrigiert.

**Akzeptanz §6 0.4 erfüllt:** `python -c 'import source_registry'` läuft
(`pip install -e phase14_discovery` erfolgreich); `pytest
phase14_discovery/tests -q`: 0 Tests, kein Fehler; `docs/INDEX.md` kennt jede
neue Datei.

**Block A1 (Fix-Commit `11f5267`)** — Live-Blocker-Fix B1 (`stale_source`
Vokabular-Lücke). Zwei Zeilen in `phase9_universe/universe/models.py`:

```python
DS_STALE_SOURCE = "stale_source"   # Phase 13 §6 A4 (F1)
```

plus `DS_STALE_SOURCE` ins `_VALID_DATA_SOURCE_STATUSES`-Set. Vor dem Fix
warf `UniverseRecord.__post_init__` `ValueError: invalid data_source_status:
'stale_source'` beim LESEN, sobald `set_symbol(..., status='stale_source')`
geschrieben hatte → `active_universe()` stirbt → `wiring.py:131` crashed beim
Daemon-Start. **Zündet genau dann, wenn die Beweiswoche
`enable_divergence_sampler=True` setzt.** Heute unscharf (Default False),
deshalb bisher nicht live gefeuert.

**Test** (`phase9_universe/tests/test_store.py`, +1):
`test_active_universe_survives_stale_source_marker` seedet einen active Epic,
setzt ihn auf stale_source, ruft `active_universe()` (OHNE den Fix: ValueError
via `from_row`). Beweist zusätzlich, dass `measurable_universe()` die stale-
Zeile weiterhin ausschließt (DS_OK-Filter bleibt) — kein Leak in die Messung.

**Falsifikation verifiziert:** vor dem Fix wirft der Test `ImportError`
(`cannot import name DS_STALE_SOURCE`); nach dem Fix grün.

**Akzeptanz §6 A1 erfüllt:** `pytest phase9_universe/tests -q` 80 + 1 = **81
grün**; Gesamt-Baseline 1608 + 4 (A1 + 0.3) = **1612**.

### Verified (heute nachgemessen, 2026-08-22)

| Suite | Vorher | Nachher | Δ |
|---|---:|---:|---:|
| phase13_live_data | 50 | 53 | +3 (B3/B4/B5) |
| phase9_universe | 80 | 81 | +1 (A1) |
| phase14_discovery | n/a | 0 | Skeleton |
| **Summe (Regression)** | **1608** | **1612** | **+4** |

Working tree clean (nach jedem Commit), `ps aux | grep scheduler.run` leer
(Parallel-Login-Falle kontinuierlich). Keine Cross-Phase-Edits außerhalb der
am 2026-08-22 freigegebenen Liste (Phase 2/8/9/12/13). Keine Live-Läufe,
kein Live-DB-Write (alle Tests gegen tmp_path).

### Finding (außerhalb des Locked-Scope §6 0.2, NICHT in dieser Session behoben)

`ROADMAP.md:427` trägt einen dated-2026-08-18 Korrektur-Eintrag („V4 rutscht
auf Phase 14. Jede ‚Phase 13 (V4)'-Nennung in älteren Zeilen meint jetzt
Phase 14"). Durch den zweiten Roll-over (2026-08-22: V4 → 15) ist diese Zeile
jetzt **erneut stale**. Der Plan §6 0.2 pinnt die zu ändernden Stellen
explizit auf die fünf `### 14a…14e`-Sub-Bullets; diese Zeile ist nicht in
der Liste. Empfehlung an Nikinger: ein zweiter datierter
Korrektur-Eintrag darunter (gleiche Auditketten-Logik wie
`ARCHITECTURE.md:60`). Habe es bewusst nicht still erweitert — „Locked
decisions stay locked" (Root-`CLAUDE.md` Working Style).

### Next

- **Operator (Nikinger):** Push-Freigabe für die **vier Commits** (`999464a`,
  `4681d68`, `97ffdc2`, `11f5267`). 4 Commits vor `origin/main`.
- **Ausführende Session (nächste):** Plan §6 **Block A2** — Migration 007 +
  `SourceAvailabilityStore` + `SourceProfile`/`SourceAvailability`-Dataclasses
  + Tests gegen das heutige `instrument_universe`-Substrat (5+3+14 Zeilen aus
  §2.2). **A2 ist die Voraussetzung für alles weitere** — ohne die Tabelle
  gibt es nichts zu projizieren (A4) und nichts umzustellen (B).
- **Operator (Nikinger, vor Block B1b):** Capital.com `/markets`-Probe
  (B1a). Befehl + Output vorbereiten, Demo-Konto (kostenlos). Ohne den
  Output wird `discover()` **nicht** gebaut (Plan §9.3) — Fallback ist
  `origin='operator'` mit den zwei bekannten Paaren, Block B erfüllt trotzdem.
- **Operator (Nikinger, vor Produktions-Migration 007):** Backup von
  `data/trading_bot.sqlite` (additiv, aber reale Trade-Historie).
  Plan §9.13.
- **Optionaler Hygiene-Commit (Nikinger-Diskussion):** `ROADMAP.md:427`
  Korrektur-Eintrag (s. o.).
- **Beweiswoche läuft parallel** (Phase 13, P1–P9). Mit A1 grün kann
  `enable_divergence_sampler=True` jetzt scharf geschaltet werden, ohne
  den Daemon-Start zu sprengen (B1-Lücke geschlossen).

---

## Session stopped — 2026-08-22 (Session 1: Planungssession)

> **Auftrag:** den execution-ready Plan für Phase 14 schreiben. Read-only am
> Produktionscode — **kein** Produktionscode-Edit in dieser Session.

### Completed

**`docs/concepts/phase14_discovery_plan.md`** (NEU) — gelockte Entscheidungen **D1–D20**
mit Begründung je Zeile, Contracts (§5), Schritt-Sequenz **Block 0/A/B/C/D** mit
Verbatim-Ankern und Zeilennummern, Testliste je Schritt, Akzeptanz **A1–A8** (§7),
Fehlgriff-Tabelle (§8, sechs Einträge), vollständige Drift-Liste (§9, 13 Einträge),
Out-of-Scope (§10).

**Dieses Dokument** (`phase14_discovery/CLAUDE.md`, NEU) — Phasenkopf + Session-Block 1.

**Nachtrag im selben Commit-Strang (Advisor-Review):** der Grundbestand der yF-Projektion
kommt aus **Migration 007 selbst** (vier Zeilen `INSERT … SELECT`), nicht aus einem
Resolver-Lauf — `SymbolResolver.resolve_epic` ruft `set_symbol` in sechs von acht Pfaden
**nicht** (`symbols.py:194-199, 207-210, 213-214, 219-220, 222-223, 229-230`), und die drei
`SUN*`-Epics stehen bereits auf ihrem Zielstatus ⇒ sie bekämen sonst nie eine Zeile. Der
Backfill kauft zusätzlich den Identitätsbeweis **vor** der ersten Zeile neuem Code. Ebenfalls
nachgezogen: die Schreib-Mechanik der Projektion ist auf **rohes SQL über `self.conn`**
gelockt (kein `source_registry`-Import in `phase9_universe` — Paket-Zyklus in der falschen
Richtung, plus zweite Verbindung auf dieselbe DB), abgesichert durch einen
Doppelschreiber-Gleichheitstest.

**Nikinger-Entscheidungen dieser Session (2026-08-22):**
- Discovery läuft **autonom als eigener Daemon** (nicht im `universe_refresher`-Slot),
  mit eigenem Operator-Script, und die **UI warnt, bis ein Button scharfschaltet**.
- Code-Ort: **`phase14_discovery/`, Paket `source_registry`** (nicht `discovery` —
  Kollision mit `universe.discovery`).
- **Dukascopy raus aus Phase 14, aber nicht ganz raus** — die Beweiswoche zeigt, was von
  einer Fremdquelle gebraucht wird und ob Dukascopy das richtige Werkzeug ist.
- Der `stale_source`-Fix kommt **in Phase 14, nach den initial steps** — „sonst womöglich
  auf falsches Fundament bauen".
- Cross-Phase-Freigabe erteilt für Phase 2 / 8 / 9 / 12 / 13.

### Verified (selbst gemessen, 2026-08-22)

- **Regression-Baseline VOR dem ersten Fix: 1608 passed**, 14 Suiten, je Phase separat.
  Vollständige Tabelle im Plan §2.1. Working tree clean, `ps aux | grep scheduler.run` leer.
- **Migration 007 ist frei** — `_schema_version` = 6.
- **`instrument_universe`: 22 Zeilen** — 5 `active`+`ok`, 3 `active`+`no_intraday_source`,
  14 `verified`+`unverified`. Namentlich im Plan §2.2 (das ist das Akzeptanz-Substrat für A4).
- **`data/bars.sqlite`: 14 846 Bars** — yf 11 654 · ig 2 230 · capital 962 · **ls 0**.
- **Turbo-/Legacy-Grep-Ritual ausgeführt: No-Op.** 3 Treffer, alle „strike" im
  `fail_count`-Sinn (identisch zu 2026-06-27 / 07-10 / 08-18); `turbo_candidates` = 19,
  eingefrorener P5-Contract-Name, **nicht umbenennen**. Plan §2.3 — die ausführende
  Session wiederholt das Ritual **nicht**.
- **Kein `FOREIGN KEY` in `migrations/001…006`** (6× gezählt), und `UniverseStore` öffnet
  ohne `PRAGMA foreign_keys = ON` → Tabelle 007 bekommt bewusst keinen FK (Plan §5.1).

### Befunde (B1–B6, alle neu — keiner steht in einem Vordokument)

- **B1 🔴 Live-Blocker, empirisch reproduziert:** `DS_STALE_SOURCE = "stale_source"`
  (Phase 13 A4) fehlt in `_VALID_DATA_SOURCE_STATUSES`
  (`phase9_universe/universe/models.py:61-63`). `set_symbol` schreibt es per rohem SQL
  durch; jeder spätere `UniverseRecord.from_row` wirft
  `ValueError: invalid data_source_status: 'stale_source'`. Damit stirbt
  `active_universe()` → `wiring.py:131` beim nächsten Start. **Zündet genau dann, wenn die
  Beweiswoche `enable_divergence_sampler=True` setzt** — was P9 verlangt. Heute unscharf
  (Default `False`). Fix = 2 Zeilen + 1 Test, Plan §6/A1.
- **B2:** die Concept-Schema-Skizze (§2.2) hat **keine** Spalte für das quelleneigene
  Symbol und kann `EPIC_MAP` deshalb nicht ersetzen — ihr eigenes Done-Kriterium wäre
  unerreichbar. **Korrektur (2026-08-22): `source_symbol TEXT`.** Damit ist
  `instrument_universe.yf_ticker` exakt `source_symbol WHERE source='yf'`.
- **B3:** `capital_backfill.py --auto` ist strukturell kaputt — `UniverseStore(args.db)`
  mit `args.db` = `data/bars.sqlite`, wo `instrument_universe` nicht existiert. Seit
  Session 12 nie erfolgreich gelaufen (der Live-Lauf 2026-08-22 nutzte `--epics`).
- **B4:** `capital_backfill.py:187-191` — `NameError` im `except`-Handler (`results` erst
  in Zeile 186 gebunden), verschluckt die eigentliche Fehlermeldung.
- **B5:** `backfill.py:414-416` verwirft den Rückgabewert von `insert_bars` und zählt
  Versuche statt Schreibvorgänge. **Konsequenz für die Beweislage:** „962 bars written"
  (Closeout-Handover §2.4) heißt korrekt „962 Insert-Versuche". Die Zahl stimmt mit der
  Archiv-Zählung überein — aber **nur weil es ein Erstlauf war**; die Übereinstimmung ist
  kein Beweis, dass der Zähler richtig ist.
- **B6:** die „1508 passed" in diesem Repo (`phase13_live_data/CLAUDE.md:169`) ist ein
  **Additionsfehler** — die Einzelzahlen derselben Tabelle ergeben 1608, und mein Sweep
  reproduziert jede Einzelzahl. Keine Drift, keine fehlenden Tests.

### Drift, die ich in Vordokumenten korrigiert habe

- `EPIC_MAP` steht in `backfill.py` **85-88**, nicht in `67-72`
  (`PHASE13_CLOSEOUT_HANDOVER.md` §1.5 und `phase13_c_block_c_replan.md` §1.1 sind stale).
  Der Plan arbeitet deshalb durchgehend mit Verbatim-Strings, nicht mit Handover-Zahlen.

### Next

- **Operator (Nikinger):** Push-Freigabe für den Plan-Commit.
- **Ausführende Session:** Plan §6 **Block 0.0** — Sweep gegen die 1608 aus §2.1
  reproduzieren, dann 0.2 (Nummerierungs-Nachlese, ein Doc-Commit), dann 0.3 (die drei
  Script-Bugs), dann 0.4 (Gerüst). **Erst danach A1** (der `stale_source`-Fix).
- **Vor Block B1b:** die Capital.com-`/markets`-Probe muss gelaufen sein (B1a,
  Operator, Demo, kostenlos). Ohne den Output wird `discover()` **nicht** gebaut, sondern
  auf `origin='operator'` ausgewichen — die Antwort-Form dieser API ist nie inspiziert
  worden (Plan §9.3).
- **Vor der Produktions-Migration 007:** Backup von `data/trading_bot.sqlite` (additiv,
  aber die DB trägt reale Trade-Historie). Plan §9.13.
- **Beweiswoche läuft parallel** (Phase 13, P1–P9) und wird von Phase 14 **nicht**
  blockiert — mit **einer** Ausnahme: wer `enable_divergence_sampler` anschaltet, bevor
  A1 gelaufen ist, zündet B1.

---
## Session stopped — 2026-08-22 (Session 7: CFD-Filter-Fix + Block B1b + Block A4)

> **Auftrag:** Option 1+ kombiniert (Nikinger-Entscheidung) — CFD-Fix, B1b, A4
> in getrennten Commits. Drei Commits, 16 neue Tests grün; keine Cross-Phase-
> Edit außerhalb der freigegebenen Liste (Phase 2/8/9/12/13).

### Completed

**Commit 1 — `phase13: probe -- fix CFD-substring filter to exact INDICES
match`** (`4195033`, 2 files, +154/-12). `scripts/probe_capital.py:382-388`
Filter `"CFD" in instrumentType` war ein No-Op gegen die Realität
(`instrumentType == "INDICES"` — Phase-14 B1a Befund 3). Helper
`_pick_index_match` als modul-level Pure-Funktion extrahiert (gleiche
Disziplin wie `CapitalSource._pick_markets_match` in Session 8) — exakt-
`"INDICES"` Match mit Name-only-Fallback für forward-compat (zukünftige
Type-Renames verlieren den Probe nicht).
+6 Tests in `phase13_live_data/tests/test_probe_capital.py` (NEU): INDICES-
wins, type-case, fallback, no-match → None, missing-type-field, empty-list.

**Commit 2 — `phase14: code+tests -- B1b CapitalSource.discover() against
B1a snapshot`** (`3434fe7`, 2 files, +572/-1). `CapitalSource.discover`
implementiert genau gegen den B1a-Snapshot:
- Signatur `discover(epics, *, max_probe_calls=8) -> SourceProfile` —
  identisch zum Protocol in `source_registry.models:192`.
- Interner statischer Name-Lookup `_DISPLAY_NAME_BY_EPIC` (3 Paare aus B1a
  Befund 5); Spanien 35 ist **drin** (`SP35`) — Dukascopy-Fallback wird
  überflüssig für IBEX.
- Filter exakt `instrumentName == name` UND `instrumentType == "INDICES"`
  (B1a Befund 3); Strict — kein Fallback auf non-INDICES (Discover
  schreibt in die `instrument_source_availability` Tabelle, da ist
  `status='ok'` ein bindender Vertrag).
- Fail-soft (Plan §8.5): network / parse / non-200 → `errors`-Tuple;
  iteriert weiter. Auth-POST zählt nicht gegen `max_probe_calls`.
+8 Tests in `phase13_live_data/tests/test_capital_discover.py` (NEU):
Happy DE40, unknown epic ohne HTTP, search-hit-mit-non-INDICES-Result →
no_source, `max_probe_calls=0` → keine GETs, `max_probe_calls=1` → nur
erste Epic, `requests.ConnectionError` → error, non-200 → error, B1a 3-Paar
round-trip.

**Commit 3 — `phase14: code+tests -- A4 yF-Projektion in
UniverseStore.set_symbol`** (`ee48cd2`, 2 files, +326/-0). `set_symbol`
schreibt nach dem Registry-UPDATE in try/except-Block die yF-Zeile in
`instrument_source_availability` (Migration 007). Schreib-Mechanik gelockt
(Plan §6 A4): rohes SQL gegen `self.conn`, **kein** Cross-Phase-Import von
`source_registry.models` (Phase 9 ist sealed, Phase 14 hängt davon ab —
Importer würde in die falsche Richtung laufen). INSERT … ON CONFLICT …
DO UPDATE — gleiche Shape wie `SourceAvailabilityStore.upsert`.
Doppelschreiber-Gleichheit wird zur Laufzeit zugesichert (Test 6),
nicht zur Compile-Zeit. Fail-soft gemäß D5: fehlt die Tabelle, geht der
Registry-Write durch, der Projektions-Fehler landet im Log.
+6 Tests in `phase9_universe/tests/test_store.py`: round-trip (status='ok'),
overwrite on second call, source_symbol=None, **D5-Beweis mit fehlendem
Migration 007** (Fixture `store` ohne 007; `set_symbol` raises nicht),
measurable_universe byte-equal vor/nach, doppelschreiber-gleichheit mit
beiden `utc_iso_now` auf fixed clock gepatcht.

### Verified

- Regression-Sweep aller 14 Suiten + root `tests/` (Stand nach den drei
  Commits, ohne Docs-Edits):
  | Suite | Vor Session 7 | Nach | Δ |
  |---|---:|---:|---:|
  | phase1_broker_wrapper | 95 | 95 | 0 |
  | phase2_persistence | 77 | 77 | 0 |
  | phase3_external_data | 104 | 104 | 0 |
  | phase4_research | 155 | 155 | 0 |
  | phase5_execution | 173 | 173 | 0 |
  | phase6_debate | 76 | 76 | 0 |
  | phase7_reward | 138 | 138 | 0 |
  | phase8_scheduler | 244 | 244 | 0 |
  | phase9_universe | 81 | 87 | +6 (A4) |
  | phase10_v3 | 165 | 165 | 0 |
  | phase12_data_foundation | 143 | 143 | 0 |
  | phase13_live_data | 59 | 67 | +8 (CFD-Fix: 0; B1b: 8) |
  | phase14_discovery | 22 | 22 | 0 |
  | meta_m1_harness | 28 | 28 | 0 |
  | root `tests/` | 80 | 80 | 0 |
  | **Σ** | **1638** | **1652** | **+14** |
  *(Cross-check: 6 A4 + 8 B1b = 14 neue Tests, keine Lücke.)*
- Working tree clean (außer `data/`-Ordner, der ist gitignored), keine
  Cross-Phase-Edits außerhalb der freigegebenen Phase-13-Liste,
  `git log --oneline -4` zeigt eine saubere Commit-Kette.

### Findings (drei, davon einer war neu)

- **CFD-Filter-Bug-Lage korrigiert:** Plan §6 0.3, Session-6-Doc, der
  Phase-13-Closeout-Handover und die ROOT-CLAUDE-MD zitierten alle
  `live_data/backfill.py:339-366` (oder `:300-316`) als Bug-Stelle. **Falsch.**
  Der `"CFD" in instrumentType`-Substring lebt in `scripts/probe_capital.py:385`.
  `_extract_ohlc` in `backfill.py` filtert nicht nach Typ — sucht nur
  OHLC-Feldnamen. Plan-Drift-Listeneintrag #2 ("Zeilennummern
  verschieben sich") hat sich hier bestätigt; die Korrektur wandert
  in die Plan-§9-Drift-Liste der nächsten Plan-Session.
- **`CapitalSource._pick_markets_match` ist strict-by-design:**
  `scripts/probe_capital._pick_index_match` hat einen Fallback auf
  exakten Namen ohne Typ-Check (für Forward-Kompat im Operator-Tooling).
  `_pick_markets_match` hat **keinen** Fallback — Discover schreibt
  in die Cross-Product-Tabelle, wo `status='ok'` bedeutet "diese
  Quelle liefert CFD-Index-Bars". SHARES/COMMODITIES sind die falsche
  Antwort, kein Notbehelf. Begründung im Helper-Docstring.
- **`import logging` war `phase9_universe/universe/store.py` fremd** bis
  A4 (verifiziert im Plan-Drift-Item #12). `logger = logging.getLogger
  ("universe.store")` ergänzt; nur für den Projektions-Warning-Pfad —
  andere Methoden ändern ihr Verhalten nicht.

### Unverändert offen

- **B2** (`EPIC_MAP` raus, `SourceAvailabilityStore.symbol_for` rein)
  — wartet auf die jetzt baubare B1b-Availability. Empfehlung: nächste
  Session.
- **B3** (`source_delta.py` drei Fälle) — orthogonal, danach.
- **Block C** (Daemon + Web-UI-Scharfschalten) — C1/C2/C3/C4 jeweils
  eigener Commit.
- **Block D** (Closeout) — kommt am Ende der Phase, sobald A1–A8 grün
  sind (A1–A4, B1b, B2, B3, C1–C4).
- **Hygiene-Tickets** aus Session 4: `*.sqlite.bak-*` in `.gitignore`,
  `ROADMAP.md:427` Aktualisierung — bewusst zurückgestellt.
- **Plan-§9-Drift-Listeneintrag #2 erweitern** in der nächsten Plan-
  Session (Editor-Notiz für Phase-15-Planung oder eine Phase-14-
  Closeout-Session).

### NEXT

- **Operator (Nikinger):** Push-Freigabe für die 3 Commits (`4195033`,
  `3434fe7`, `ee48cd2`) + diesen Docs-Commit. Stand jetzt: 3 Commits
  vor `origin/main`.
- **Ausführende Session (nächste):** **B2** (`EPIC_MAP` raus,
  `SourceAvailabilityStore.symbol_for` rein) — jetzt baubar, weil
  B1b die `capital`-Availability liefern kann. Plus B3
  (`source_delta.py` drei Fälle). Block C danach.
- **Beweiswoche läuft separat weiter** (Phase 13 Plan §7 P1–P9). Die
  hier committeten Schreib-Pfade sind alle nicht im Konsumentenpfad
  (D6-Muster), berühren die laufende Beweiswoche nicht.

### Completed

**`phase14_discovery/PHASE14_B1A_PROBE_OUTPUT_2026-08-22.md`** (NEU, L3-Snapshot) —
Roh-Output der Operator-Probe + 8 nummerierte Befunde mit Mapping auf B1b.
Header-Karte nach Doku-Konvention (`status: snapshot`, `read-when`,
`up:`/`down:`). Cross-Verweis vom Plan (`docs/concepts/phase14_discovery_plan.md`).

### Die 8 Befunde — was B1a gelehrt hat

| # | Befund | Konsequenz für B1b |
|---|---|---|
| 1 | Response ist `{ "markets": [...] }` — Array, je Eintrag ein Market-Objekt | `discover()` iteriert über `markets`, filtert, emittiert eine `SourceAvailability` pro Match |
| 2 | **`epic`-Feld ist das gesuchte Source-Symbol** (`"DE40"`, `"FR40"`, `"SP35"`) | geht 1:1 in `instrument_source_availability.source_symbol` — exakt dieselbe Identitäts-These wie yF (B2) |
| 3 | `instrumentType` ist **`"INDICES"`** (nicht `"CFD"`, wie der bestehende `live_data/backfill.py:339-366`-Filter annimmt) | B1b filtert auf `"INDICES"`. **Offener Filter-Bug im bestehenden Code** — der Fallback `[m for m in markets if m.get("instrumentName") == index_name]` rettet es heute. B1b macht es richtig; bestehender Code wird in B2 oder als separates Hygiene-Ticket nachgezogen (Nikinger-Entscheidung) |
| 4 | **Spain 35 IST verfügbar** als `epic: "SP35"` (war bisher Path-C-Territorium in Phase 13) | Block B erweitert Coverage. Dukascopy-Fallback für SP35 wird überflüssig |
| 5 | Sucht mit `searchTerm=<instrumentName>` → erster Eintrag mit `instrumentName == searchTerm` + `instrumentType == "INDICES"` ist die kanonische Übersetzung | B1b-Such-Algorithmus: `for epic in input: name = instrument_universe[epic].name; GET /markets?searchTerm=name; first INDICES match → SourceAvailability` |
| 6 | `delayTime: 0` für alle drei → **Echtzeit** | `history_min_days=30, latency_min=0` für die `capital`-Zeilen (NICHT die 15-Min-yF-Heuristik) |
| 7 | Jeder Eintrag hat `instrumentId` (numerisch), `epic` (kurz), `symbol` (lang/kurz), `bid`/`offer` (Live-Preise), `lotSize`, `tickSize`, `pipPosition` | B1b braucht nur `epic` + `instrumentName` + `instrumentType`. Andere Felder sind für Discover irrelevant — kein Schema-Mapping nötig |
| 8 | `marketStatus: "CLOSED"` für alle drei am Wochenende | erwartbar (Markt zu), **kein** B1b-Sonderfall. Discover prüft Verfügbarkeit via Existenz des Eintrags, nicht via `marketStatus` |

### Operator-Setup (verifiziert, 2026-08-22)

- **Auth funktioniert:** `POST /api/v1/session` → HTTP 200, `account_type=CFD`,
  CST + X-SECURITY-TOKEN im Response-Header. **Demo-Keyring `trading-bot-capital`
  ist intakt** (Vorbedingung für B1b gegeben).
- **Drei Suchterme, drei Treffer** — alle im ersten Listeneintrag.
- **Probe-Script** (`probe_capital.py --markets --terms ...`) tat ohne
  Modifikation. Kein Code-Edit in dieser Session.

### Nicht-B1b-Stoff (separate Tasks)

- **B2 (`EPIC_MAP` raus):** Plan §6 B2 wartet auf B1b. Heute gibt
  `SourceAvailabilityStore.symbol_for(epic, 'capital')` für keinen Epic
  einen Wert (Tabelle 0027 wurde nur mit yF-Backfill gefüllt). Nach B1b
  liefert sie für DE40/FR40/SP35 die richtigen Kürzel.
- **Offener Filter-Bug im bestehenden Code** (`live_data/backfill.py:339-366`,
  `backfill.py:300-316`): `"CFD" in instrumentType` matched nie — die
  Realität ist `"INDICES"`. Der Fallback `candidates = [m for m in markets
  if m.get("instrumentName") == index_name]` rettet es heute. **Nicht in
  dieser Session gefixt** — bewusst zurückgestellt (Phase-14-Cross-Phase-
  Edit nur für Phase 2/8/9/12/13 freigegeben; eine Edit in `backfill.py`
  ist Phase-13-Territorium und gehört in B2 oder als separates Ticket).
  **Empfehlung:** in B2 mit aufnehmen, weil B2 den `EPIC_MAP`-Hintergrund
  eh anfasst.
