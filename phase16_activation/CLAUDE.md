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

### Open questions / blockers

- Keine. A-0 ist die saubere Brücke zwischen Plan-Session und Exec-Session; nächster Step (A-1 Ritual) ist unabhängig und read-only.

### Next (für die nächste Session oder Pause-Fortsetzung)

- **A-1 — Step-0-Ritual:** `grep -rni "turbo" --include="*.py" --include="*.sql" --include="*.sh" . --exclude-dir=.venv` + `grep -rn "EPIC_MAP" --include="*.py" . --exclude-dir=.venv` — Erwartung 14 + 3 wie Plan §2.7 (5. Mal No-Op-Bestätigung). Ergebnis in diesen Phasenkopf-Block.
- **A-2 — Σ-Baseline:** Sweep nach Plan §2.1, Erwartung Σ = **1843** grün. Abweichung = Befund von *vor* Phase 16, dokumentieren.
- **A-3 — Code↔.md-Sweep (4 falsche Behauptungen + Leichen):** root-CLAUDE.md:119-120, root-CLAUDE.md Status-Tabelle Z. 167, README.md:39, ROADMAP.md:99, ROADMAP.md:441, phase9_universe/CLAUDE.md:133, phase15_v4/PHASE15_CLOSEOUT_HANDOVER.md (📕, 🟡-Anhang), ROADMAP.md Phase-16-Häkchen-Pflege. Erste Code-Touches im Plan-Scope: 0 (alles Doku).
- **A-4 — WebUI-Access-Log (L8):** `run_webui.sh` `--no-access-log` + `webui/api.py:75` `SchedulerConfig(daily_loss_cap=1800.0)` mit Kommentar. Wirkt erst nach WebUI-Restart.
- **A-5 — Operator-Push:** `git push origin main` — 7 + A-Commits. Stand vor A-5: 7 lokal ahead; nach A-5 dann 7 + Anzahl-A-Commits ahead. Nikinger-Aktion.
- **B2 (nach Block B Commit)** — Operator-Fenster mit allen 4 Diensten gestoppt: Backup → `init_db.py` → v9 verifizieren → Ledger-Restore-SQL. **Erst nach** Block-B-Commit (P14-Disziplin, Schema-Floor wirkt ab dann).
