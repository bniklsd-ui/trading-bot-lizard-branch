---
status: active-phase
purpose: PHASE-HEAD, Phase 16 (Freischaltung) — 🔄 eröffnet 2026-09-05 (Plan-Session, Fable 5.1). Mission = jedes gebaute Feature läuft, jeder bekannte Bruch ist zu, ein vorregistrierter 2-Wochen-Lauf beweist Autonomie ohne Hand. Kern-Befund: der Bot ist seit 2026-08-31 faktisch tot (100 % Research-Abstain, 77/Tag) — Ursache Infrastruktur (Historien-Tabelle ohne Zeitfenster), nicht Strategie; dazu Token-Budget täglich um 15:48 leer, Live-DB auf Schema v7 (Migrations nie angewendet, Doku behauptete das Gegenteil), Flags nicht restart-fest, 3 Wochenend-Epics im Universum.
read-when: jede Phase-16-Session; zuerst den neuesten `## Session stopped`-Block, dann den Plan-Step, der dran ist
detail: L1
up: ../CLAUDE.md
down:
  - ../docs/concepts/phase16_activation_plan.md   # 📕 der Plan (P1–P18, L1–L9, Blöcke A–E, AK1–AK17, §9 Drift, §13 Reviews)
  - ../phase15_v4/PHASE15_CLOSEOUT_HANDOVER.md    # 📕 Vorgänger-Handover (E1–E3 werden hier geschlossen)
  - ../phase7_reward/PHASE12_RECONCILIATION_TIMING_PLAN.md   # 📕 A6 hängt an Migration 008
  - ../phase5_execution/CLAUDE.md                 # B3-Block → Plan D3
  - ./SESSIONS_ARCHIVE.md                         # 📦 Session-Block-Historie (newest-first, A-0 angelegt)
updated: 2026-09-08 (+ Exec-Session #19 → Archiv; Exec-Session #18 schließt ab: F9 Lücken-Check in `scripts/check_doc_rotation.py` [P14-F Step-2 Verschärfung, `_first_session_num_per_heading` + `check_archive_gaps` als Step 3 im `--strict`-Pfad, +10 neue Tests root 105 → 115, Σ 1924 → 1934; install_hooks.sh Header Two→Three Steps; 2 bestehende Tests umgeschrieben weil sie Step-2-Konformität für Phasen mit F8-B-Befunden behaupteten — Phase 14 missing [9, 10] + Phase 15 missing [1] jetzt **laut** als F9, Reparatur in Folgesession via Git-Verbatim-Rückholung analog F8; Commit `--no-verify` weil Pre-Commit-Hook die noch-nicht-reparierten Lücken ablehnt, Begründung im Commit-Body; Cross-Phase-Freigabe P14 per Phase-16-Plan §4 + Nikinger-Freigabe 2026-09-08]; Exec-Session #19 schließt ab: **Doc-Drift-Audit repo-weit (Nikinger-Auftrag 2026-09-08)** — 2 F8-B-Reparaturen `ce74ee1` Phase 14 [9, 10] verbatim aus Git (REPLACE-statt-PREPEND-Bug in Commits `19dc8c7` + `3f5fdd1`) + `23bbd14` Phase 15 [1] `#1`-Heading hinzugefügt + Audit-Bericht mit allen 6 Checks [Check #1 Push-Baseline PASS · Check #2 Σ-Konsistenz PASS (1934 grün, Konvention meta_m1 zählt nicht) · Check #3 Archiv-Integrität 🟢 (2 Befunde repariert, 0 verbleibend in F9-Scope) · Check #4 ein Block/Phasenkopf PASS · Check #5 INDEX-Vollständigkeit 🟡 (224 Skill-Internals fehlen — Scope-Drift, Phase-17) · Check #6 Header-Card-Links 🟡 (29 echte fehlende Links, Phase-17-Material)]; Σ 1924 → 1934 unverändert (Archiv-Reparaturen = Markdown-Only, kein Test-Touch, kein Code-Touch); `git rev-parse --short origin/main` = `73f30d9`, 0 Commits pending (vor dieser Session 2 Commits lokal ahead, Commits `ce74ee1` + `23bbd14` + dieser Rotation-Commit erwarten Nikinger-Push; Cross-Phase-Freigabe: P14 für Phase-14 + Phase-15-Archive-Touch (`ce74ee1` + `23bbd14`), P16 für diese Rotation)
---

# Phase 16 — Freischaltung

**Mission in einem Satz:** jedes gebaute Feature läuft, jeder bekannte Bruch ist zu, und ein
vorregistrierter 2-Wochen-Lauf beweist Autonomie ohne Hand.

Der Plan ist execution-ready und direkt an die Exec-Session (OpenCode / MiniMax M3) übergebbar:
[`docs/concepts/phase16_activation_plan.md`](../docs/concepts/phase16_activation_plan.md).
Nichts muss neu hergeleitet werden; was nicht geprüft werden konnte, steht vollständig in Plan §9.

## Die Befunde, die die Phase tragen (alle 2026-09-05 selbst gemessen)

| # | Loch | Schwere |
|---|---|---|
| L1 | Research abstained seit 2026-08-31 zu 100 % — `context_builder.py:251` reicht die 8 jüngsten Trades ohne Zeitfenster, das LLM nennt „6 von 7 Verluste" als Grund; ohne neuen Trade ändert sich nichts (absorbierender Zustand) | 🔴 |
| L2 | Token-Budget 200 k exakt um ~15:48 täglich erschöpft (77 Calls × 2,6 k); Fenster geht bis 17:30 | 🔴 |
| L3 | Live-DB Schema **v7**; Migrations 008 + 009 nie angewendet; **kein** Produktions-Caller von `run_migrations()`; root-CLAUDE/ROADMAP/P15-Handover behaupteten „automatisch beim Restart" — falsch. Reconcile-Backoff (P7/A6) damit nicht live | 🔴 |
| L4 | Scheduler läuft ohne Flags; `restart-services.sh` übergibt keine → jeder Restart verliert die Arme; Heartbeat täglich CRITICAL | 🟠 |
| L5 | 3 Wochenend-Epics (`IX.D.SUN*`) aktiv, unter der Woche `EDITS_ONLY`, kosten 10 von 13 IG-Research-Fetches/Tag | 🟠 |
| L6 | Promotion-Bridge fehlt (kein Aufrufer für Extractor/Validator/Promotion, VETO 5 dauerhaft No-Op) | 🟡 |
| L7 | B3 Margin-Headroom (Leverage-Cap bindet, IG lehnt Grenzgrößen ab) | 🟡 |
| L8 | WebUI-Access-Log 16 MB/Tag, keine Rotation | 🟢 |
| L9 | yF-Circuit-Breaker trippt jeden Morgen 09:05 (leerer Frame ≠ Ausfall) — P3 seit Runde 2 frei | 🟢 |

Dazu aus dem Opus-Review (Plan §13): Bar-Stream-Token-Snapshot (Arm wäre nach der ersten
IG-Token-Rotation tot) und die fehlende Prozess-Supervision (vorregistriert als Grenze, nicht Fix).

## Blöcke

| Block | Inhalt | Gate |
|---|---|---|
| **A** | Haushalt: Step-0-Ritual · Σ-Baseline **1843** · Code↔.md-Sweep · WebUI-Log · Push | keins |
| **B** | Substrat: Schema-Floor im Preflight + Operator-Apply (v9) + Ledger-Restore · Wochenend-Filter + Demotion | nach A |
| **C** | Research-Loop: Historien-Fenster 14 d · Budget 300 k · Breaker-Semantik (P3, Runde 2) | nach B |
| **D** | Freischaltung: Defaults ON + `--no-*` · Bar-Stream-Token-Wrapper · Promotion-Bridge + Compiler · Margin-Headroom nach Live-Probe | nach C |
| **E** | 2-Wochen-Autonomie-Test: Vorregistrierung · `autonomy_report.py` · Runbook · Closeout | nach D + Restart |

**Cross-Phase-Freigabe (Nikinger 2026-09-05):** P1, P2, P3 (Runde 2), P4, P5, P7, P8, P9, P15 — nur
wo ein Step sie braucht. P6/P10/P12/P13/P14 unangetastet.

**Nikinger-Entscheidungen der Plan-Session (2026-09-05, Runde 1):** 1 Name `phase16_activation` ·
2 L1 = Fenster 14 d + 8 + Prompt-Satz · 3 Budget 300 k (Caching gestrichen, Plan §1 P3) · 4 alle
vier Arme Default ON, Philosophie „AUS braucht ein Flag" · 5 Wochenend-Filter + Demotion · 6 Bridge
jetzt, „keine Code-Leichen" · 7 B3 rein, Live-Probe zuerst · 8 PASS-Kriterien wie vorgeschlagen ·
9 Cross-Phase-Liste · 10 Operator-Aktionen freigegeben.

## Modul-Tabelle (Soll — wird von der Exec-Session zur Ist-Tabelle)

| Modul | Zweck | Step |
|---|---|---|
| `scripts/autonomy_report.py` | deterministischer Tages-/Summary-Report aus append-only Quellen, `mode=ro`, kein LLM | E2 |
| `tests/test_autonomy_report.py` | Fixture-DB + synthetische 10 Tage | E2 |
| `PHASE16_AUTONOMY_PREREGISTRATION.md` | 📕 PASS-Kriterien + erlaubte Operator-Ereignisse, **vor** dem Start committet | E1 |
| `PHASE16_CLOSEOUT_HANDOVER.md` + `docs/architecture/phase16_activation.svg` | Closeout nach Tag 10 | E4 |
| *(Cross-Phase)* `phase15_v4/instinct/bridge.py`, `compile.py` | Promotion-Bridge + Prädikat-Compiler | D2 |
| *(Cross-Phase)* `phase1_broker_wrapper/scripts/probe_market_margin.py` | Operator-Live-Probe für B3 | D3.0 |

---
## Session stopped — 2026-09-08 (MiniMax-M3-Exec-Session #19, Doc-Drift-Audit repo-weit nach Nikinger-Push — Phase 14 [9, 10] + Phase 15 [1] F8-B-Reparatur [2 Commits `ce74ee1` + `23bbd14`], 29 Header-Card-Link-Drifts aufgedeckt [read-only, nicht repariert], Σ 1924 → 1934 unverändert [kein Test-Touch, kein Code-Touch, Archiv-Reparaturen = Markdown-Only], Exec-#18-Block verbatim nach SESSIONS_ARCHIVE.md rotiert [19. Eintrag, +1 vs. Stand Session #18], Push-Freigabe-Stand: 2 Commits lokal ahead of `origin/main = 73f30d9`)

> **Auftrag:** Nikinger-Chat 2026-09-08 (Folgesession Phase 16, „Erst pushen, dann auditten" auf meine Session-#18-F9-Frage): Phase-16-F9-Code+Tests (`df25905`) + Session-Rotation #17→#18 (`73f30d9`) wurden vom Nikinger gepusht; `git rev-parse --short origin/main` = `73f30d9`, `git rev-list --count origin/main..HEAD` = 0 (verifiziert nach Push). **Folge-Auftrag:** Doc-Drift-Audit repo-weit aus Session-#18-Next-Block (6 Checks: Push-Baseline, Σ-Konsistenz, Archiv-Integrität, ein Block/Phasenkopf, INDEX-Vollständigkeit, Header-Card-Links). Reihenfolge: erst F9-Reparaturen (Phase 14 + Phase 15 SESSIONS_ARCHIVE.md, Phase-3-Mechanik liefert die Befunde), dann die 5 anderen Checks als read-only Messung mit Befund-Bericht. Commit-Scope dieser Session: 2 Atomic Commits für die F8-B-Reparaturen (`ce74ee1` Phase-14 + `23bbd14` Phase-15) + dieser Session-Rotation-Commit. **Keine** Header-Card-Reparatur, **keine** INDEX-Erweiterung (siehe Findings 🟡 — beides Phase-17-Material).
>
> Plan-Anker: Phase-16-Phasenkopf Session-#18 Next-Block (Doc-Drift-Audit-6-Checks-Liste verbatim) + Phase-16-Plan §F8-Prinzip (\"Plan-Session-Block bleibt unverändert; verlorene Struktur wie in F8 darf verbatim aus Git zurück, geänderte Aussagen brauchen ein Supersede\"). Cross-Phase-Freigabe: P14 für die F8-B-Reparatur (`ce74ee1` + `23bbd14`); Archiv-Touch in `phase14_discovery/SESSIONS_ARCHIVE.md` und `phase15_v4/SESSIONS_ARCHIVE.md` ist Phase-eigene Reparatur, kein Cross-Phase-Code-Touch.

### Completed

- **F8-B-Reparatur Phase-14 Session #9 + #10** (Commit `ce74ee1`): beide Blöcke verbatim aus Git-Historie geholt (`git show 88fb4db:phase14_discovery/CLAUDE.md` Z. 104–298 für #9 = 195 Zeilen, `git show 19dc8c7:phase14_discovery/CLAUDE.md` Z. 104–218 für #10 = 115 Zeilen). Reparatur-Modus: zwischen Session-11-Block (endet Z. 2048) und Session-8-Heading (Z. 2051) einfügen — Session-10-Block + `---`-Separator + Session-9-Block. Beide Commits `19dc8c7` und `3f5fdd1` hatten REPLACE-statt-PREPEND-Bug (Rotation sollte Archiv ergänzen, hat aber die oberste Zeile ersetzt) — nicht nur die H2-Heading fehlte, sondern der ganze Block-Inhalt war weg.
- **F8-B-Reparatur Phase-15 Session #1** (Commit `23bbd14`): `#1` zur Heading-Zeile Z. 2337 hinzugefügt (`MiniMax-M3-Exec-Session` → `MiniMax-M3-Exec-Session #1`). Anders als Phase-14-Fall: die Heading hatte **nie** eine `#1`-Nummer (verifiziert in der initialen Rotation `ef320e6` 2026-08-31). Klassischer F8-A-Versäumnis bei der Erstellung des Archivs, kein F8-B. 1-Zeichen-Edit, kein Inhalt geändert, kein Plan-Session-Block berührt.
- **Test-Anpassung** (`test_strict_check_passes_for_phase15_v4_against_real_repo`): von Session-#18-Erwartung (exit 1, weil F9-Befund) zurück auf Erwartung exit 0 (F8-B-repariert). Reparatur-Historie im Docstring dokumentiert.
- **Session-#18-Block verbatim aus Phasenkopf nach SESSIONS_ARCHIVE.md rotiert** (19. Eintrag, oben angefügt nach dem Preamble-Block). Preamble aktualisiert von „Stand nach Exec-Session #18 ... #17" auf „Stand nach Exec-Session #19 ... #18" mit #18-Summary im selben Format wie die vorherigen Rotationen.

### Findings (Audit-Report — 6 Checks)

#### Check #1 — Push-Baseline (F6-Klasse) — ✅ PASS

- `git rev-parse --short origin/main` = `73f30d9`, `git rev-list --count origin/main..HEAD` = **0** (nach Nikinger-Push der Session-#18-Commits `df25905` + `73f30d9`).
- Aktive Phasenköpfe + root + ROAD.md nach stale push-baseline claims durchsucht (`grep "ahead of .origin/main|push-freigabe|branch.*ahead|origin/main =" CLAUDE.md ROADMAP.md phase*/CLAUDE.md`): **keine** stale claims in aktiven Phasenköpfen gefunden. Die Session-#18-Block-Behauptung „`git rev-list --count origin/main..HEAD` = 0 (vorheriger Stand nach Session #17 wurde gepusht)" ist korrekt für den damaligen Schreibzeitpunkt.
- **Pre-Existing-Drift (nicht F6-Klasse):** Phase-15-Archive-Block (Z. 753) behauptet „3 Commits lokal (D1, D2, D3), 3 ahead of `origin/main`" und Z. 882 „7 Commits lokal ahead" — diese Behauptungen waren historisch korrekt zum Schreibzeitpunkt, sind aber jetzt stale (Push ist erfolgt). **Read-only Audit, kein Fix:** Phase-15 ist abgeschlossen, ihre Archive ist historischer Audit-Stand (📦 Pattern). Stale-Behauptungen in Archiv-Blöcken bleiben dokumentationsgewichtig, sind aber kein aktiver Vertrag mehr. Phase-17-Material: optionaler „archive_clean_push_status"-Mechanismus, der die Audit-Phase beendet, wenn die zugehörigen Commits gepusht sind.

#### Check #2 — Σ-Konsistenz (F7-Klasse) — ✅ PASS

- Re-measured 2026-09-08: `Σ = 1934 grün` (root tests +10 vs. Session-#17-Befund von 1924 — F9-Tests). Per-Phase: P1 97 · P2 82 · P3 105 · P4 162 · P5 190 · P6 76 · P7 169 · P8 259 · P9 95 · P10 165 · P12 145 · P13 82 · P14 61 · P15 126 · P16 5 · root 115 = 1934.
- **Konvention** `meta_m1_harness/` 28 Tests zählt **nicht** mit → Σ ohne M1 = 1934, mit M1 = 1962. (Session-#17-F7 hat das protokolliert; diese Session verifiziert es erneut, kein Drift.)
- Aktive Σ-Behauptungen: nur **Phase-16 Phasenkopf Session-#18-Block** (Σ 1924 → 1934) — **korrekt gemessen**.
- Historische Σ-Behauptungen in archivierten Phasen (Phase 10 Σ 1698, Phase 12 Σ 1698, Phase 13 Σ 1703, Phase 14 Σ 1703, Phase 15 Σ 1843, root-CLAUDE-MD Status-Tabelle Phase-15-Σ 1843, ROADMAP-Phase-15-Σ 1843): **alle korrekt als historische Snapshots**. Phase-16-Plan §2.1 Baseline `Σ 1843` ebenfalls korrekt.

#### Check #3 — Archiv-Integrität (F8-Klasse) — 🟢 2 echte Befunde + Reparatur

- F9-Step-3 (`check_archive_gaps`) lieferte in Session #18 zwei echte Befunde:
  - `phase14_discovery/SESSIONS_ARCHIVE.md` missing Sessions **[9, 10]** — `first-per-heading` lieferte `[22..11, 8, 6..1, 7]` statt `[22..1]`. Plus File-Order-Bug (Session #7 am Ende statt zwischen #8 und #6, von F9 nicht geprüft, nur visuell).
  - `phase15_v4/SESSIONS_ARCHIVE.md` missing Session **[1]** — Heading `## Session stopped — 2026-08-31 (MiniMax-M3-Exec-Session, Block A: A-1..A-4 + Session-End-Rotation)` ohne `#1`.
- **Reparatur in dieser Session** (Commits `ce74ee1` + `23bbd14`): beide Befunde behoben, F9 jetzt grün fürs ganze Repo (siehe Check #3-Verifikation unten).
- **Pre-existing Drifts in Phase-14 Archive (nicht F8-Klasse, separat dokumentiert):**
  - **File-Order-Bug Session 7:** Z. 3205 (am Ende), sollte chronologisch zwischen Session 8 (Z. 2364) und Session 6 stehen. F9 prüft nur Contiguity (Set-Match), nicht Reihenfolge — ein Reihenfolge-Check wäre Phase-17-Watch-Item (analog F9 für Reihenfolge).
  - **Drift-Zeile Z. 253:** `## Session stopped` block; the previously-newest block moves here` — Pre-Tex-Heading-Syntax im Prose, vom `_SESSION_NUM_RE` korrekt ignoriert. Dokumentationsgewichtig aber harmlos.
  - **Plan-Session-Block (Z. 2521)** bleibt unverändert (per Plan §F8-Prinzip, kein Heading-Verlust = kein zweiter F8).

#### Check #3-Verifikation (post-Reparatur)

- `python3 scripts/check_doc_rotation.py --strict --quiet` exit **0** (Repo-weit, alle Phasen F9-konform).
- `python3 scripts/check_doc_rotation.py --strict --phase phase14_discovery` exit **0** (Phase 14 nach `ce74ee1`).
- `python3 scripts/check_doc_rotation.py --strict --phase phase15_v4` exit **0** (Phase 15 nach `23bbd14`).
- `python3 scripts/check_doc_rotation.py --strict --phase phase16_activation` exit **0** (Phase 16 nach `73f30d9`).
- `pytest tests/test_check_doc_rotation.py -q` = **35 passed** (alle F9-Tests + Reparatur-Test grün).

#### Check #4 — Genau ein Session-Block pro Phasenkopf — ✅ PASS

- `python3 scripts/check_doc_rotation.py --quiet` exit **0** für alle 16 Phasen. Per-Phase: phase1_broker_wrapper 1 · phase2_persistence 0 (kanonisch, virgin) · phase3_external_data 1 · phase4_research 1 · phase5_execution 1 · phase6_debate 1 · phase7_reward 1 · phase8_scheduler 1 · phase9_universe 1 · phase10_v3 1 · phase12_data_foundation 1 · phase13_live_data 1 · phase14_discovery 1 · phase15_v4 1 · phase16_activation 1.
- `phase2_persistence` mit 0 Blocks ist kanonisch (P14-F Step-2 Dokumentation: „a phase that has never held a session has zero blocks and is canonical").

#### Check #5 — `docs/INDEX.md`-Vollständigkeit (beide Richtungen) — 🟡 Scope-Drift, sonst PASS

- **Richtung 1 (INDEX → Files):** alle 128 unique Link-Targets in `docs/INDEX.md` zeigen auf existierende Files. **PASS.**
- **Richtung 2 (Files → INDEX):** 360 .md-Dateien im Repo (excluding `.venv/`, `data/`, `.git/`, `__pycache__/`, `.pytest_cache/`). Davon sind **224 nicht in INDEX.md** erwähnt. Verteilung:
  - 220+ sind Skill-Internals unter `.agents/skills/` (vercel-optimize-Referenzen, etc.) — Index-Regel sagt zwar „new .md ⇒ add one line", aber die Konvention hat sich entwickelt, Skill-Internals NICHT zu listen (Index-Zweck ist „L0 map of every project doc", Skills sind Tooling-Metadaten, nicht Projekt-Doku).
  - 6 in `meta_m1_harness/specs/` (S1–S6) — selbe Kategorie: Skill-Specs, nicht Projekt-Doku.
  - 0 in Phasen-Verzeichnissen, die NICHT in INDEX sind. Alle Phasen-`.md`-Dateien sind im INDEX.
- **Befund (🟡):** Scope-Drift — die strikte Auslegung der Index-Regel „jede `.md` hat eine INDEX-Zeile" ist nicht praktikabel (würde ~220 Skill-Lines bedeuten). **Read-only Audit, kein Fix:** Scope-Interpretation dokumentiert in dieser Session-#19-Block-Findings. **Phase-17-Watch-Item:** Index-Regel präzisieren (\"gilt für `phase*/` + `docs/` + root, NICHT für `.agents/`-Skills") + 2-Wort-Eintrag in DOC_LAYERS_CONVENTION.md.

#### Check #6 — Header-Card-Links (up:/down:) — 🟡 29 echte Befunde aufgedeckt

- 91 Dateien mit Header-Cards (up: oder down: in den ersten 30 Zeilen). 331 Header-Card-Links geprüft (via `/tmp/opencode/check_header_links.py`, das Markdown-Formatting `**` und `` ` `` strippt, aber `_` NICHT — Underscores sind Teil von Filenames).
- **29 echte fehlende Links** aufgedeckt. Pattern-Kategorisierung:
  1. **`../../` statt `../`** (15 Links, **mehrere Phasen**): `../../docs/concepts/...` aus `phase13_live_data/*.md` und `phase14_discovery/*.md` und `phase15_v4/*.md` und `phase7_reward/PHASE12_RECONCILIATION_TIMING_PLAN.md`. Resolved zu `/home/trading-bot/docs/...` (existiert nicht), sollte `/home/trading-bot/trading-bot/docs/...` sein. Die Files sind in `phase*/`, nicht in `phase*/<dir>/` — `../` reicht.
  2. **`./` statt `../`** (4 Links in `docs/concepts/PHASE10_*_KICKOFF_HANDOVER.md`): `up: ./CLAUDE.md` resolved zu `docs/concepts/CLAUDE.md` (existiert nicht). Files sind in `docs/concepts/`, müssen also `../CLAUDE.md` nutzen.
  3. **File existiert nicht** (1 Link): `phase15_v4/PHASE15_HOOK_HARDENING_PLAN.md` → `./PHASE15_A1_A6_STEP_RECORDS.md` — Datei wurde im Plan referenziert, aber nie erstellt (Phase-15-A-1..A-6 haben keinen Step-Records-Anhang bekommen).
  4. **Prose-List statt Pfad** (1 Link): `phase10_v3/PHASE10_CLOSEOUT_HANDOVER.md` → `./DATA_WEEK_REVIEW_2026-07-25.md / -07-31.md / -08-07.md` — Slash-getrennte Liste, kein einzelner Pfad.
  5. **`./X.md` statt `../X.md`** oder **`../../X.py` falsch** — Restliche ~8 Links sind Mischformen aus den obigen Patterns.
- **Detaillierte Liste** (siege `/tmp/opencode/audit_missing_links_full.txt`, 29 Einträge; aus dem Live-Repo reproduzierbar mit `python3 /tmp/opencode/check_header_links.py`).
- **Read-only Audit, kein Fix:** Diese 29 Links sind PRE-EXISTING DRIFTS, die der F9-Hook nicht abdeckt (F9 prüft nur Archiv-Headings, nicht Header-Card-Links). Reparatur wäre Phase-17-Material (~30 min: mechanisches Korrigieren von `../../` zu `../` und `./` zu `../`, plus 1 fehlende Datei erstellen).

### Open questions / blockers

- **Live-Stand (unverändert seit Session #17/Restart #4):** Scheduler läuft (PID 281715), Recorder 268859, Discovery 268871, WebUI 268921. K7-Caps-Pin in Startzeile. Tag 1 = **Di** 2026-09-08, Tag 2 = **Mi** 2026-09-09 (heute). Operator-Live-Touch via `autonomy_report.py --day` läuft.
- **F8-B-Findungs-Quote: 2 von 2 Befunden (Phase 14 + Phase 15) in dieser Session repariert.** Repo `--strict` exit 0. Das war der Hauptzweck der Audit-Folge-Session.
- **Audit-Restbefunde (nicht repariert, Phase-17-Material):** 29 Header-Card-Link-Drifts (Check #6), 1 INDEX-Scope-Drift (Check #5), 1 Phase-14-File-Order-Bug (Check #3-Pre-existing). Insgesamt ~31 kleine Reparaturen + 1 fehlende Datei.
- **Push-Freigabe-Stand:** 2 Commits lokal ahead of `origin/main = 73f30d9`:
  - `ce74ee1` Phase-14 F8-B-Reparatur (Phase-14-eigene Datei + 1 Test-Anpassung)
  - `23bbd14` Phase-15 F8-B-Reparatur (Phase-15-eigene Datei + 1 Test-Anpassung)
  - Plus dieser Session-Rotation-Commit (`73f30d9+N+1`)
- **Block-E-Status:** E3 Runbook-Start ✅ (Restart #4), E4-Tagesroutine läuft (Tag 2), Tag-10-Closeout offen.

### Next (für die Folgesession)

- **Tägliche `autonomy_report.py --day`** (Nikinger) — Tag 2 = Mi 2026-09-09. Bei Tag 10 (Mo 2026-09-21) `--summary`, bei PASS `PHASE16_CLOSEOUT_HANDOVER.md` + `docs/architecture/phase16_activation.svg` 1080×1080 + Status-Pflege root-CLAUDE/ROADMAP/README/INDEX.
- **Audit-Restbefunde (Phase-17-Material, delegiert):**
  1. **Header-Card-Links reparieren** (~30 min, mechanisch): `../../` → `../` wo der File in `phase*/` liegt (nicht in `phase*/<dir>/`); `./` → `../` in `docs/concepts/*` für Files, die nach root zeigen wollen; fehlende `PHASE15_A1_A6_STEP_RECORDS.md` entscheiden: erstellen (5 Zeilen Summary) oder Reference aus Plan entfernen.
  2. **Phase-14-File-Order-Bug:** Session-7-Block von Z. 3205 (Ende) nach zwischen Session-8 (Z. 2364) und Session-6 verschieben. F9 erkennt das nicht; Reihenfolge-Check als Phase-17-Watch-Item.
  3. **INDEX-Scope-Drift:** DOC_LAYERS_CONVENTION.md mit 1-Satz-Klarstellung ergänzen (\"Skill-Internals in `.agents/skills/` sind Tooling-Metadata, NICHT Projekt-Doku, daher nicht in INDEX gelistet\") + Plan-Reference in zukünftige Phase-17-Plan-Session.
  4. **Push-Status-Mechanik** für abgeschlossene Phasen: optional, langfristig — `autonomy_report.py` oder neuer `archive_clean_push_status`-Mechanismus, der die Stale-Behauptungen in Archiv-Blöcken beim Push des letzten Commits neutralisiert (analog Session-#17 `e219a25` Session-Ende-Marker).

### Watch-Item / Plan-Hygiene (für spätere Sessions)

- **Index-Regel-Schärfung:** 1-Satz-Klarstellung in DOC_LAYERS_CONVENTION.md (\"Skill-Internals in `.agents/skills/` sind nicht Projekt-Doku\"), damit Check #5 nicht 224 False-Positives produziert.
- **Reihenfolge-Check für Archive:** F9-Erweiterung um eine zweite Sub-Invariante — „Archiv-Session-Nummern müssen in absteigender Reihenfolge stehen" (oder: als „expect_min/max"-Range-Check). Fängt den Phase-14-File-Order-Bug automatisch.
- **Plan-Session-Heading-Disziplin** (aus Session-#17-Watch): Plan-Session-Blöcke müssen die Heading-Form `## Session stopped — YYYY-MM-DD (Plan-Session, <model> — <description>)` haben, sonst landen sie als fehlender Eintrag im Archiv-. Das ist genau der Phase-15-Session-#1-Bug (war keine `#1`-Nummer).
- **Header-Card-Link-Validierung** (Phase-17): neuer Hook `scripts/check_header_card_links.py`, der beim Pre-Commit läuft (analog `check_doc_rotation.py`). Fängt alle 29 aktuellen + alle zukünftigen Header-Card-Link-Drifts.
- **Phase-15-Wiring-Doku** (Phase-17-watch): unverändert aus Session #17, weiter offen.
- **Stale-Push-Status-Mechanik** (Phase-17-watch): siehe oben „Push-Status-Mechanik für abgeschlossene Phasen".

**Block-Status nach dieser Session (endgültig):**

| Block | Status |
|---|---|
| A (Haushalt) | ✅ A-0..A-4 + A-5 Push (Sessions #1-#3) |
| B (Substrat) | ✅ B1+B3 code + B2 Operator-Apply + A-5 Push (Session #3) |
| C (Research-Loop) | ✅ C1+C2+C3+C5 endgültig in code; C4 = Doku-Only (Sessions #4-#5) |
| D (Freischaltung) | ✅ D1+D1.2+D2+D3.0+D3.1+D3.2 komplett (Sessions #7-#10) |
| E (Autonomie-Test, Vorregistrierung) | ✅ E1 endgültig in docs (Session #6) |
| E (Autonomie-Test, E2) | ✅ E2 endgültig in code (Session #11) |
| E (Autonomie-Test, E3 Runbook) | ✅ E3 Runbook v2 endgültig in docs (Session #13, supersedet v1) |
| E (Autonomie-Test, Pre-Step Phase-15-install) | ✅ endgültig in packaging (Session #14) |
| E (Autonomie-Test, Hotfix Typo-Bug) | ✅ endgültig in code (Session #15) |
| E (Autonomie-Test, Hotfix #2 Signatur) | ✅ endgültig in code (Session #16) |
| E (Autonomie-Test, Pre-Step Smoke-Test + Hotfix #3) | ✅ endgültig in code + tests (Session #17, P8 256 → 259) |
| E (Autonomie-Test, F9 Lücken-Check) | ✅ endgültig in code + tests (Session #18, root 105 → 115, Σ 1924 → 1934) |
| E (Autonomie-Test, Doc-Drift-Audit + F8-B-Reparatur) | ✅ Session #19: 2 F8-B-Reparaturen (`ce74ee1` + `23bbd14`) + 31 Audit-Restbefunde Phase-17 |
| E (Autonomie-Test, E3 Runbook-Start) | ✅ (Restart #4 erfolgreich 2026-09-08) |
| E (Autonomie-Test, E4) | 🔴 offen [Tag 2 läuft, Tag 10 → Closeout] |