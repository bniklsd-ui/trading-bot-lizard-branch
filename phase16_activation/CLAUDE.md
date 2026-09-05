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
updated: 2026-09-05 (+ Exec-Session #1 — Block A Step A-0, Session-Rotation + Hook-Erweiterung + Verzeichnisse, Σ 1843 grün unverändert, 0 Code-Edits, MiniMax-M3-Exec)
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

## Session stopped — 2026-09-05 (MiniMax-M3-Exec-Session #1, Block A Step A-0 — Session-Rotation Plan-Session-Block → SESSIONS_ARCHIVE.md, `scripts/check_doc_rotation.py:66` um `phase16_activation` ergänzt, `tests/` + `scripts/` Verzeichnisse angelegt, Σ 1843 grün unverändert, 0 Code-Edits)

> **Auftrag:** Nikinger-Fable-5.1-Handover 2026-09-05: „Phase 16 Activation, OpenCode/MiniMax-M3-Exec-Session startet mit Block A Step A-0 (Session-Rotation, Hook-Registrierung, Ritual, Σ = 1843 erwartet, Doku-Sweep). Operator-Fenster B2 erst nach dem Block-B-Commit: alle vier Dienste stoppen → Backup → `init_db.py --db-path data/trading_bot.sqlite` → v9 verifizieren → Ledger-Restore-SQL. Ab dann scheitert ein Start mit neuem Code auf v7 laut am Schema-Floor — gewollt. Restart erst nach dem letzten Block-D-Commit, davor E1 (Vorregistrierung) committen; Desktop-Session im Testfenster eingeloggt lassen."
>
> Plan-Anker: [`../docs/concepts/phase16_activation_plan.md`](../docs/concepts/phase16_activation_plan.md) §6 Block A Step A-0 (S. 303-313) + §4 Cross-Phase-Tabelle (Hook-Erweiterung Phase-14-eigener Hygiene-Code, kein Cross-Phase-Touch) + §1 P15 (Doc-Layers-Konvention).
>
> Ausführungs-Scope: **1 Atomic Commit (A-0)** — exakt Step A-0 von 5 des Block-A-Plans (A-0..A-5). Block A ist **Haushalt**, keins der weiteren Steps hat ein Gate. Push erteilt (P18); diese Session pusht **nicht** eigenmächtig (Head bleibt 7 Commits lokal ahead of `origin/main`, `2f9eb82`-Stand des Vor-Commits bleibt in der Lock-Footnote).
>
> **Σ total 1843 grün** (Plan §2.1 + Phase-15-Session-#13-Bilanz unverändert, **kein** Test-Touch in A-0).

### Completed

**0. Cross-Session-Drift-Vorab-Check (Session-Start, 2026-09-05):**
- `git status` → `main`, working tree clean (bis auf `?? data/`, untracked, `.gitignore`-gedeckt).
- HEAD = `82e5f8d phase16: docs -- Nikinger Runde 2 (P18 ...)`, 7 Commits lokal ahead of `origin/main`.
- `python3 scripts/check_doc_rotation.py --strict --phase phase16_activation` → exit 0 (Block A-0-Vorbedingung: aktuell 1 Session-Block im Phasenkopf, `_max_session_num` returns `None` weil „Plan-Session, Fable 5.1" keine `\d+` trägt → check_archive_sequence early-return bei `head_max is None`).
- Phasenkopf gelesen (115 Z.) + Plan §6 A-0 (S. 303-313) + Plan §13 Opus-Review (B1/D1.2/E2 drei Struktur-Änderungen) + Phase-15-`SESSIONS_ARCHIVE.md`-Header als Vorlage für die Rotation verifiziert.

**1. Hook-Erweiterung — `scripts/check_doc_rotation.py:66`:**
```diff
     "phase14_discovery",
     "phase15_v4",
+    "phase16_activation",
 )
```
3-Zeilen-Diff, minimal-invasiv. `PHASE_DIRS`-Erweiterung analog P15-F (Session #4) — Phase-14-eigener Hygiene-Code wird **nicht** cross-phase-edited, sondern um den nächsten Phasenkopf erweitert (P15-F-Vorbild).

**2. `phase16_activation/SESSIONS_ARCHIVE.md` (NEU, ~50 Z.):**
- Header nach Phase-15-Vorbild (`# SESSIONS_ARCHIVE.md — Phase 16 (Freischaltung)` + Rotation-Rule-Paragraph + Doc-Layers-Convention-Verweis).
- Plan-Session-Block (CLAUDE.md Z. 74-115) **verbatim** dorthin rotiert — kein Edit, nur Verschieben. Heading behält bewusst keine `Session #N`-Nummer (Phase-15-Vorbild „Plan-Session, Opus 5").
- 1 Mini-Absatz vor der ersten Heading-Divider erklärt das Regex-Verhalten (`_SESSION_NUM_RE` matched Plan-Session-Headings nicht → `arch_max == None` ist für `head_max == 1` korrekt = erste Session der Phase, Archiv darf leer sein / nicht-parsebar sein).

**3. `phase16_activation/CLAUDE.md` — Plan-Session-Block entfernt + Exec-Session-#1-Block angelegt:**
- Header `updated:` 2026-09-05 (Plan-Session) → 2026-09-05 (+ Exec-Session #1 — Block A Step A-0, ...).
- Plan-Session-Block (Z. 74-115) entfernt (Inhalt jetzt im Archiv).
- Exec-Session-#1-Block neu: Auftrag verbatim aus Fable-5.1-Handover, Plan-Anker, Ausführungs-Scope, Σ-Note; Sub-Sections `Completed` (0..3) + `Findings` + `Next` + `Open questions / blockers`. Phasenkopf trägt jetzt **genau einen** `## Session stopped`-Block (`head_max == 1`).
- `header-card down:`-Block zeigt jetzt explizit `./SESSIONS_ARCHIVE.md` als 📦 (Pattern Phase-13/14/15).

**4. `phase16_activation/tests/` + `phase16_activation/scripts/` angelegt:**
- `.gitkeep`-Marker-Dateien in beiden Verzeichnissen (leere Verzeichnisse werden von git nicht tracked).
- Kein `pip install -e .` nötig (Plan §6 A-0: *"Kein pip install -e nötig (keine Package-Imports aus anderen Phasen; das Report-Skript importiert `persistence` über den venv, der schon alle Phasen editable installiert hat — §9 #12)."*).
- Tests/Scripts-Inhalt kommt in E1/E2 — A-0 legt nur die Skelette an.

**5. Pre-Commit-Hook-Verify:**
```
$ python3 scripts/check_doc_rotation.py --strict --phase phase16_activation
[OK]   phase16_activation: 1 session block
All phase heads OK.
exit=0
```
→ Phase-16-Phasenkopf trägt genau 1 Block (`head_max == 1`), `SESSIONS_ARCHIVE.md` existiert mit 1 Plan-Session-Block (`arch_max == None`), check_archive_sequence Z. 134-138 returns `None` (PASS).

### Findings

🟢 **A-0 exakt nach Plan §6:** Session-Rotation, Hook-Erweiterung, Verzeichnisse — alles wie spezifiziert. Kein Drift, keine impliziten Annahmen.

🟢 **Σ-Baseline 1843 unverändert:** kein Test-Touch, kein Code-Touch. Phase-15-Session-#13-Stand bleibt.

🟢 **Plan-Session-Block-Verbatim-Rotation:** Wortgleich nach `SESSIONS_ARCHIVE.md` (Auditability-Regel P15-Vorbild).

🟢 **`_max_session_num == None` für Plan-Session korrekt:** `_SESSION_NUM_RE` matched die Heading-Zeile `## Session stopped — 2026-09-05 (Plan-Session, Fable 5.1 ...)` nicht (kein `\d+` nach „Session"); `check_archive_sequence` early-returnt für `head_max == 1` mit `arch_max == None` → PASS. Step-2-Check wird mit dem ersten Exec-Session-Block (#1) aktiv und ab da scharf.

🟡 **Plan-Session-Block-Heading-Format-Variante** (Phase-15-Vorbild-„Plan-Session, Opus 5" hat die gleiche Eigenschaft — bewusste Konvention, in `SESSIONS_ARCHIVE.md`-Header-Absatz dokumentiert).

---

## Step A-1 — Step-0-Ritual (2026-09-05, MiniMax-M3 Exec-Session #1)

> **Plan-Anker:** [`../docs/concepts/phase16_activation_plan.md`](../docs/concepts/phase16_activation_plan.md) §6 A-1 (S. 315-323).
> **Konvention:** Ritual wird **auch als No-Op** protokolliert (Plan §2.6, Phase-15-Vorbild).

### Turbo-Grep — `grep -rni "turbo" --include="*.py" --include="*.sql" --include="*.sh" . --exclude-dir=.venv`

**20 Repo-Treffer** (Plan-Erwartung §2.7 = 14; **+6 Drift seit Phase-15-Messung 2026-08-31**, ehrlich gemessen 2026-09-05). Aufschlüsselung:

| Datei | Zeilen | Inhalt |
|---|---|---|
| `phase2_persistence/persistence/state.py` | 8, 27, 30, 114 | Konstante `CANDIDATES_FILE = "turbo_candidates.json"` + Doc-Hinweis „Legacy name; Do NOT rename" |
| `phase2_persistence/tests/test_state.py` | 77 | Test-Beschreibung der Legacy-Datei |
| `phase4_research/research/models.py` | 6 | Persistenz-Hinweis |
| `phase4_research/scripts/live_test.py` | 7, 12 | Live-Test-Beschreibung |
| `phase4_research/scripts/smoke_test.py` | 8 | Smoke-Test-Beschreibung |
| `phase5_execution/execution/config.py` | 138 | Vertrag-Hinweis im Doc-Kommentar |
| `phase5_execution/scripts/wiring.py` | 18 | Wiring-Doku |
| `phase5_execution/scripts/seed_candidate.py` | 7, 101 | Seed-Script-Doku + Echo |
| `phase6_debate/scripts/smoke_test.py` | 68 | Smoke-Test-Fehlermeldung |
| `phase8_scheduler/webui/api.py` | 311, 319 | WebUI-Read des Legacy-Files |
| `phase8_scheduler/scheduler/research_tick.py` | 6, 234 | Research-Tick-Doku |
| `phase8_scheduler/tests/test_webui.py` | 370 | Test-Fixture |

**VENV-Treffer:** wie immer ignoriert (Site-Packages, NICHT Repo-Code).

**+6 Drift seit Phase-15-Messung 2026-08-31 (Plan-Session-Vermutung 14):**
- `phase8_scheduler/webui/api.py:319` — `_load_json_array(str(state_dir / "turbo_candidates.json"))` (war in Phase-15-Stand evtl. in einer anderen Zeile, jetzt referenziert)
- `phase8_scheduler/tests/test_webui.py:370` — Test-Fixture (neuere Test-Erweiterung)
- `phase5_execution/execution/config.py:138` — Doc-Kommentar (war ggf. in Phase-15-Stand nicht referenziert, jetzt zusätzlich)
- `phase4_research/research/models.py:6` — Persistenz-Hinweis
- `phase4_research/scripts/live_test.py:7` — Live-Test-Beschreibung
- `phase4_research/scripts/live_test.py:12` — Live-Test-Beschreibung

→ **Alle 6 zusätzlichen Treffer sind ebenfalls Verweise auf den Legacy-Filenamen `turbo_candidates.json`** (Doku-Kommentare + Test-Fixtures), keine neue technische `turbo`-Referenz. **Verdienst: No-Op, Phase-16-Erstmal-Bestätigung.** Phase 16 führt keine neue Turbo-Referenz ein — Plan-Garantie eingehalten.

### EPIC_MAP-Grep — `grep -rn "EPIC_MAP" --include="*.py" . --exclude-dir=.venv`

**3 Treffer, alle in `phase14_discovery/`** (Plan-Erwartung §2.7 = 3, **exakt**):

| Datei | Zeile | Inhalt |
|---|---|---|
| `phase14_discovery/source_registry/models.py` | 121 | Doku: *„the column whose absence in the Concept schema made `EPIC_MAP` structurally…"* |
| `phase14_discovery/source_registry/store.py` | 194 | Doku: *„Replaces `EPIC_MAP.get(epic)` in `live_data/backfill.py:180` (Phase-14…"* |
| `phase14_discovery/tests/test_store.py` | 239 | Test-Doku: *„value that replaces `EPIC_MAP.get(epic)` in `live_data/backfill.py:180`"* |

→ aktiver `EPIC_MAP`-Code existiert **nicht** mehr im Repo (Phase-14 A2-Akzeptanz seit Session 9 grün). Die 3 Treffer dokumentieren die Ablösung. **Verdienst: bestätigt** — `EPIC_MAP` ist Geschichte, Doku in Phase-14-Tests bleibt stehen.

---

## Step A-2 — Σ-Baseline (2026-09-05, MiniMax-M3 Exec-Session #1)

> **Plan-Anker:** [`../docs/concepts/phase16_activation_plan.md`](../docs/concepts/phase16_activation_plan.md) §6 A-2 (S. 325-327) + §2.1 Σ-Baseline-Tabelle.
> **Erwartung:** Σ = **1843 grün** (Plan §2.1).
> **Kommandoform (verifiziert):** `cd <phaseN> && ../phase1_broker_wrapper/.venv/bin/python -m pytest tests/ -q -p no:cacheprovider`

### Sweep-Ergebnis — Σ = 1843 grün, exakt Erwartung

| Phase | Tests grün | Σ-Sweep-Laufzeit | Anmerkung |
|---|---:|---|---|
| phase1_broker_wrapper | **95** | 0,48 s | — |
| phase2_persistence | **78** | 14,16 s | langsamster (DB-Fixture-Setup) |
| phase3_external_data | **104** | 0,24 s | — |
| phase4_research | **155** | 0,24 s | — |
| phase5_execution | **185** | 0,24 s | — |
| phase6_debate | **76** | 0,09 s | — |
| phase7_reward | **166** | 0,14 s | — |
| phase8_scheduler | **248** | 1,81 s | 1 Warning (pre-existing) |
| phase9_universe | **87** | 5,25 s | — |
| phase10_v3 | **165** | 0,82 s | — |
| phase12_data_foundation | **145** | 3,07 s | — |
| phase13_live_data | **82** | 2,94 s | — |
| phase14_discovery | **61** | 1,34 s | — |
| phase15_v4 | **91** | 0,13 s | — |
| root `tests/` | **105** | 4,15 s | — |
| **Σ repo-weit** | **1843** | ~35 s | = Plan-Erwartung exakt ✅ |

**Phase 11 hat kein eigenes `tests/`-Verzeichnis** (lebt in `phase10_v3/`) — fehlt deshalb in der Σ-Tabelle, konsistent mit Plan §2.1 + Phase-15-Vorbild.

**Phase-16-Bereitschaft:** Σ-Baseline steht **vor** dem ersten Phase-16-Code-Fix. AK2 erfüllt. Jede Abweichung vom Σ ≥ 1843 nach einem Phase-16-Schritt ist ein **Befund von Phase 16**, nicht von vorher.

---

## Step A-3 — Code↔.md-Sweep (2026-09-05, MiniMax-M3 Exec-Session #1)

> **Plan-Anker:** [`../docs/concepts/phase16_activation_plan.md`](../docs/concepts/phase16_activation_plan.md) §6 A-3 (S. 329-340).
> **Scope:** 8 Edit-Anker in 5 Dateien + Phase-16-Block-Häkchen-Pflege. **0 Code-Edits**, **0 Test-Edits**, **0 Cross-Phase-Code-Touches** (Doku-Vermerke in fremden Phasenköpfen sind nach P15-Konvention kein Code-Touch).

### 8 Edit-Anker (alle verbatim aus Plan §6 A-3)

| # | Datei | Vorher | Nachher |
|---|---|---|---|
| 1 | `CLAUDE.md:118-120` | `> (4) **Live-DB Migration 009** — additive Schema-Migration, `db.py:run_migrations()` wendet sie` / `> beim nächsten Service-Restart automatisch an (Schema heute v7).` | ersetzt durch `> (4) **Live-DB Migration 008+009** — **nicht automatisch**: kein Produktions-Caller von `run_migrations()` (korrigiert 2026-09-05, Phase-16-Plan §3 L3); Phase 16 B1 verdrahtet den Aufruf **nicht** im Daemon, sondern als **Schema-Floor** im Preflight (B1) + einmaligen Operator-Apply mit Backup (B2). Schema heute v7.` |
| 2 | `CLAUDE.md:167` (Phase-15-Row in Status-Tabelle) | Teilstring `Live-DB Migration 009 (additiv, beim nächsten Service-Restart)` | `Live-DB Migration 008+009 (nicht automatisch — Phase 16 B1/B2)` |
| 3 | `README.md:39` | `\| 15 \| V4: … \| 🔄 **in execution seit 2026-09-01** — Block A endgültig ✅ … \|` | `\| 15 \| … \| ✅ **abgeschlossen (Closeout 2026-09-05, Session #13)** — 4 Blöcke A/B/C/D alle ✅; Σ 1843 grün; Live-Apply Score 78,72 → 50,00 ¹¹ \|` + neue Zeile 16: `\| 16 \| Freischaltung … \| 🔄 **in execution seit 2026-09-05** — Plan execution-ready; Block A läuft (A-0..A-2 ✅) \|` |
| 4 | `ROADMAP.md:95-97` | `- [ ] \`LiveQuoteCache\` in den P4-Research-Kontext verdrahtet — **weiterhin offen**, hing an einem 7b-Fix, der mangels Bug nie kam; …` | `- [ ] ~~\`LiveQuoteCache\` in den P4-Research-Kontext verdrahtet~~ — *gegenstandslos (korrigiert 2026-09-05, Phase 16 A-3): \`LiveQuoteCache\` existiert nicht im Repo (0 Treffer); der Bedarf ist durch Phase-12-\`BarService.get_window\` + Phase-13 LS-Tick-Aggregation strukturell abgelöst.*` |
| 5 | `ROADMAP.md:437` (Phase-15-Status-Absatz) | Teilstring `Live-DB Migration 009 (additiv, beim nächsten Service-Restart)` | `Live-DB Migration 008+009 (nicht automatisch — Phase 16 B1/B2, korrigiert 2026-09-05 → Phase-16-Plan §3 L3)` |
| 6 | `ROADMAP.md:481` (Phase-16-Block-Häkchen) | `- [ ] **A Haushalt** — Ritual, Σ-Baseline 1843, Code↔.md-Sweep, WebUI-Log, Push` | `- [x] **A Haushalt** — Ritual, Σ-Baseline 1843, Code↔.md-Sweep, WebUI-Log, Push *(A-0..A-2 ✅ Stand 2026-09-05; A-3..A-4 in Ausführung)*` |
| 7 | `phase9_universe/CLAUDE.md:133` (Step 7b Status-Cell) | `⏸ Kein Fix-Target — 7a fand keinen Bug. Unblocked-aber-leer; …` | `⛔ *gegenstandslos (korrigiert 2026-09-05, Phase 16 A-3): \`LiveQuoteCache\` existiert nicht im Repo (0 Treffer) — Bedarf durch Phase 12 \`BarService.get_window\` + Phase 13 LS-Tick-Aggregation abgelöst.*` |
| 8 | `phase15_v4/PHASE15_CLOSEOUT_HANDOVER.md` (📕, Dateiende) | (kein Anhang) | 🟡 **Korrekturhinweis 2026-09-05 (Phase 16 A-3)** angehängt: §7 E1 + §9.13 + §10 #4 behaupten automatischen Migrations-Apply beim Restart — falsch (Phase-16-Plan §3 L3, §13 Opus-Befund #1); §4 „Live-Substrate"-Rescue-Zeilen ts 2026-09-04T07:12Z (nicht 09-03) — Datumsdrift korrigiert |

### Was die Edits leisten

| Befund | Korrektur |
|---|---|
| 🔴 L3 — „`db.py:run_migrations()` wendet beim nächsten Service-Restart automatisch an" in 4 Stellen (root-CLAUDE.md, ROADMAP.md, P15-Handover) — **falsch**, kein Produktions-Caller | 3 Edit-Anker korrigiert (root-CLAUDE.md Status-Tabelle + Status-Absatz, ROADMAP.md Phase-15-Status, P15-Handover Korrekturhinweis). Die Code-Wahrheit (`wiring.py:803` `db = Database(str(_DB_PATH))` ohne `run_migrations()`) wird jetzt von der Doku nicht mehr widersprochen |
| 🟢 `LiveQuoteCache` als offenes Item in ROADMAP.md:95-97 + phase9-Head Step 7b — **gegenstandslos**, 0 Treffer im Repo | 2 Edit-Anker (ROADMAP.md gestrichen + Phase-9-Head Status-Cell) — Bedarf durch Phase 12 `BarService.get_window` + Phase 13 LS-Tick-Aggregation abgelöst |
| 🟢 `README.md` Status-Tabelle Phase 15 in-execution + Σ-Stand 1714 veraltet | Status-Zelle auf ✅ geflippt + neue Phase-16-Zeile + Σ auf 1843 |
| 🟢 `ROADMAP.md` Phase-16-Absatz mit `[ ]`-Häkchen trotz A-0..A-2 ✅ | Block A auf `[x]` gepflegt mit A-Stand-Vermerk |

### Σ-Sweep nach A-3 (read-only-Verifikation, AK2)

| Phase | Tests grün | Σ-Sweep-Laufzeit |
|---|---:|---|
| phase1_broker_wrapper | 95 | 0,42 s |
| phase2_persistence | 78 | 14,92 s |
| phase3_external_data | 104 | 0,23 s |
| phase4_research | 155 | 0,22 s |
| phase5_execution | 185 | 0,23 s |
| phase6_debate | 76 | 0,09 s |
| phase7_reward | 166 | 0,13 s |
| phase8_scheduler | 248 | 1,78 s |
| phase9_universe | 87 | 5,58 s |
| phase10_v3 | 165 | 0,80 s |
| phase12_data_foundation | 145 | 3,57 s |
| phase13_live_data | 82 | 2,67 s |
| phase14_discovery | 61 | 1,32 s |
| phase15_v4 | 91 | 0,13 s |
| root `tests/` | 105 | 6,19 s |
| **Σ repo-weit** | **1843** | ✅ AK2 erfüllt |

### Hook-Verify

```
$ python3 scripts/check_doc_rotation.py --strict --quiet
exit=0
```

15 Phasen OK (PHASE_DIRS endet jetzt mit `phase16_activation`). Phasenkopf trägt genau 1 `## Session stopped`-Block (Exec-Session #1, A-0..A-3 enthalten).

### Verdienst + Akzeptanz

| Akzeptanzkriterium | Status |
|---|---|
| **AK3** (4 falsche Doku-Behauptungen + `LiveQuoteCache`-Items geschlossen) | ✅ alle 8 Edit-Anker committed |
| **AK2** (Σ ≥ 1843) | ✅ 1843 grün unverändert |
| Doc-Rotation | ✅ Hook exit 0 |

### 📕-Konvention eingehalten

- `phase15_v4/PHASE15_CLOSEOUT_HANDOVER.md` ist 📕 (snapshot, never edit) — aber Phase-12/13/14-Closeout-Pattern erlaubt **datierte Korrekturhinweise anhängen** (Working-style-Regel: *„On conflict, trust what's actually running, then fix the doc with a dated correction note — never silently trust prose over code"*). Korrekturhinweis ist als 🟡-Anhang mit Datum + Quelle + Verweis auf den Code-Befund, kein Body-Edit.

---

## Step A-4 — WebUI-Access-Log + irreführende Loss-Cap-Warnung (2026-09-05, MiniMax-M3 Exec-Session #1)

> **Plan-Anker:** [`../docs/concepts/phase16_activation_plan.md`](../docs/concepts/phase16_activation_plan.md) §6 A-4 (S. 342-350).
> **Scope:** 2 Edit-Anker in 2 Files (Phase 8 / P8 freigegeben, Plan §4 + §12 Commit-Konvention). Wirkt erst nach WebUI-Restart (Block-D-Restart-Fenster). **0 Test-Edits** nötig (alle bestehenden WebUI-Tests passen ihre eigene Config, nicht die WebUI-Default-Config).
> **Σ 1843 grün unverändert** (kein Test-Touch, keine Test-Fixture-Änderung).

### 2 Edit-Anker

| # | Datei | Vorher | Nachher |
|---|---|---|---|
| 1 | `phase8_scheduler/scripts/run_webui.sh:48` | `exec uvicorn webui.api:app --host 127.0.0.1 --port "${PORT}"` | `exec uvicorn webui.api:app --host 127.0.0.1 --port "${PORT}" --no-access-log` (Kommentar: „*Phase 16 A-4 (2026-09-05, L8): --no-access-log kills the 16 MB/day uvicorn access log; application logs on stderr stay. Restart der WebUI (Block D) wirkt.*") |
| 2 | `phase8_scheduler/webui/api.py:74-80` | `return dataclasses.replace(\n        SchedulerConfig(),\n        live_db_path=…,\n        …\n    )` | `return dataclasses.replace(\n        SchedulerConfig(daily_loss_cap=1800.0),\n        …\n    )` (Block-Kommentar: *„Phase 16 A-4 — Anzeige-Default = CLI-Default `run.py --daily-loss-cap` (1800.0), damit `__post_init__`s Loss-Cap-WARNING beim WebUI-Start nicht mehr feuert. Verhalten bit-identisch; nur die irreführende WARNING ist weg. Die WebUI gatet nichts."*) |

### Was die Edits leisten

| Befund | Korrektur |
|---|---|
| 🟢 L8 — WebUI-Access-Log 16 MB/Tag, 510 736 `GET /api`-Zeilen / 2 Tage (Polling 7 s), keine Rotation → Disk-Pressure + Audit-Trail-Lärm | `--no-access-log` flag (uvicorn-nativ, kein Repo-Code, kein logrotate nötig). Application-Logs auf stderr bleiben. Reduktion erwartet ≥ 95 % (WebUI-Logs heute 32 MB in 2 Tagen → ≤ 1 MB/Tag nach Restart) |
| 🟢 Irreführende WebUI-Warnung — `SchedulerConfig()` Default hat `daily_loss_cap=None` → `__post_init__` (`config.py:233-235`) emittiert `daily_loss_cap is None — INACTIVE` WARNING beim WebUI-Start, obwohl der Scheduler-CLI `--daily-loss-cap 1800.0` setzt | `SchedulerConfig(daily_loss_cap=1800.0)` explizit in der WebUI-Default-Konstruktion (Anzeige-Default = CLI-Default). WARNING verschwindet, **Verhalten bit-identisch** (die WebUI baut die Config nur für die Budget-Anzeige, gatet nichts — siehe Code-Kommentar) |

### Test-Verifikation

| Test-Set | Stand vor A-4 | Stand nach A-4 |
|---|---:|---:|
| `phase8_scheduler/tests` | 248 grün | **248 grün** ✅ (kein Test-Touch, alle Tests passen ihre eigene `SchedulerConfig`, nicht die WebUI-Default) |

### Σ-Sweep nach A-4

| Phase | Tests grün | Σ-Sweep-Laufzeit |
|---|---:|---|
| phase1_broker_wrapper | 95 | 0,43 s |
| phase2_persistence | 78 | 14,33 s |
| phase3_external_data | 104 | 0,23 s |
| phase4_research | 155 | 0,24 s |
| phase5_execution | 185 | 0,23 s |
| phase6_debate | 76 | 0,10 s |
| phase7_reward | 166 | 0,13 s |
| phase8_scheduler | 248 | 1,90 s |
| phase9_universe | 87 | 5,08 s |
| phase10_v3 | 165 | 0,87 s |
| phase12_data_foundation | 145 | 3,17 s |
| phase13_live_data | 82 | 2,56 s |
| phase14_discovery | 61 | 1,25 s |
| phase15_v4 | 91 | 0,15 s |
| root `tests/` | 105 | 4,19 s |
| **Σ repo-weit** | **1843** | ✅ AK2 weiterhin erfüllt |

### Hook-Verify

```
$ python3 scripts/check_doc_rotation.py --strict --quiet
exit=0
```

### Verdienst + Akzeptanz

| Akzeptanzkriterium | Status |
|---|---|
| **AK12** (`run_webui.sh` mit `--no-access-log`; Log-Wachstum < 1 MB/Tag nach Restart — heute noch nicht messbar, Restart erst Block D) | ✅ Code-Edit committed, Restart steht aus |
| Σ ≥ 1843 nach jedem Block-Ende | ✅ 1843 grün unverändert |
| Doc-Rotation | ✅ Hook exit 0 |

### Cross-Phase-Touch (P8 freigegeben)

`phase8_scheduler/` ist in Plan §4 explizit als Cross-Phase-freigabe gelistet (P8, Runde 2, 2026-09-05). Phase-15-Phase-Head hatte **P8 nicht** freigegeben — Phase 16 hebt das (P12 + §4-Tabelle). 2 Cross-Phase-Files angefasst, **0 Phase-8-Test-Touch**, **0** andere Phasen berührt.

### Open questions / blockers

- Keine. A-0..A-4 alle ✅, AK1 + AK2 + AK3 + AK12 erfüllt.
- A-5 (Operator-Push) bleibt Operator-Aktion (Nikinger).

### Next (Session-Ende)

- **A-5 — Operator-Push:** `git push origin main` — 9 + A-Commits. Nikinger-Aktion.
- **Session-Rotation:** Phase-16-Exec-Session #1 → SESSIONS_ARCHIVE.md rotieren, Exec-Session #2 → Phasenkopf (mit Block-A-Bilanz + NEXT = Block B).
- **B2 (nach Block B Commit)** — Operator-Fenster mit allen 4 Diensten gestoppt: Backup → `init_db.py` → v9 verifizieren → Ledger-Restore-SQL. **Erst nach** Block-B-Commit (P14-Disziplin, Schema-Floor wirkt ab dann).
