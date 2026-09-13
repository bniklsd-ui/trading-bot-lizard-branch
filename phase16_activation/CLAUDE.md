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
updated: 2026-09-13 (+ Exec-Session #29: **Block H-Finish: H-2 INDEX-Scope-Klarstellung + H-1 Step-4 Header-Card-Link-Check** [1 Code-Commit `b865808` + 1 Test-Commit `e6246fe` + 1 DOC_LAYERS-Commit `4779660`; Lock F3 revidiert (kein zweites Skript — Header-Card-Check wandert als Step 4 in bestehendes `scripts/check_doc_rotation.py`); 6 neue Tests A1–A6 in `tests/test_check_doc_rotation.py`; Σ **1939 → 1945** (+6 root 115 → 121); `check_doc_rotation.py --strict --quiet` exit 0; alle 92 Header-Cards validiert (0 broken links); `scripts/install_hooks.sh` + `scripts/dev_install.sh` + `.git/hooks/pre-commit` byte-identisch synchronisiert, idempotenter Installer meldet exit 0 beim nächsten Lauf; Session #28 verbatim nach SESSIONS_ARCHIVE.md rotiert [29. Eintrag]; 1 Drift = „Header-Card-Treffer = 0 broken" als Interpretation der Auftrag-Akzeptanz dokumentiert — `docs/concepts/*`-Files tragen weiterhin legitime `../../`-Header-Card-Links, alle resolved]). — Vorheriger Stand: Exec-Session #28: **Block H-Start**; Exec-Session #26: **J6 Restart + J7 Day-0-Verify (AI-geführt)**; Exec-Session #25: **Drift #7 Fix — Runbook v3 NEU**; Exec-Session #24: **Pre-Flight + Verify**; Exec-Session #23: **Doc-Drift-Repair**; Exec-Session #22: **Phase-16-F-Subphase Block J**; Plan-Session #21: **`PHASE16_F_EXEC_PLAN.md` NEU**

## Session stopped — 2026-09-13 (MiniMax-M3-Exec-Session #29, Phase-16-F-Subphase **Block H-Finish: H-2 INDEX-Scope-Klarstellung + H-1 Step-4 Header-Card-Link-Check** — 3 Commits `b865808` + `e6246fe` + `4779660`; Lock F3 revidiert (Nikinger 2026-09-08, kein zweites Skript — Header-Card-Check wandert als Step 4 in `scripts/check_doc_rotation.py`); 6 neue Tests A1–A6 (Regression-Pin für die 29-Befunde-Klasse aus Audit-Session #19, Patterns A-E); Σ 1939 → **1945** (+6 root 115 → 121, exakt am F-Exec-Plan §3 H-Akzeptanz-Wert); `check_doc_rotation.py --strict --quiet` exit 0; alle 92 Header-Cards validiert (0 broken); Session #28 verbatim nach SESSIONS_ARCHIVE.md rotiert [29. Eintrag]; 1 Drift = „Akzeptanz-H-Interpretation Header-Card-Treffer = 0 broken vs. 0 literal" notiert — `docs/concepts/*` Files tragen weiterhin legitime `../../`-Header-Card-Links, alle resolved)

> **Auftrag:** Nikinger-Auftrag-Fortsetzung aus Session #28: H-2 + H-1 (INDEX-Scope + Hook Step 4). Lock H2: H-2 (1 Satz in `docs/DOC_LAYERS_CONVENTION.md:53`) **zuerst** (vor H-1), damit die Hook-Spec sauber zur Doku-Klarstellung passt; dann H-1 (Code → Test → Install-Hook-Sync); H-5 Verifikation am Ende. **Auftrag-Ende:** Session-Stop-Block schreiben, Block-#28 verbatim nach SESSIONS_ARCHIVE.md rotiert, Commit, Nikinger pusht.

### Completed

**1. H-2 — INDEX-Scope-Klarstellung (`docs/DOC_LAYERS_CONVENTION.md:53`):**
- Anverter-Anker verbatim: `Maintenance rule: **new .md file ⇒ its index line lands in the same commit.**`
- Edit: ein Satz in Klammern nach der bestehenden Maintenance-Regel: „(Scope: die Regel gilt für `phase*/`, `docs/` und Root-`.md`; Skill-Internals `.agents/skills/` und Harness-Specs `meta_m1_harness/specs/` sind Tooling-Metadaten und werden **nicht** in `docs/INDEX.md` gelistet — Phase 16 H-2, 2026-09-13)".
- Verbatim-Anker aus F-Exec-Plan §3 H-2 (Lock H2: vor H-1). Commit `4779660`.

**2. H-1 Code — `scripts/check_doc_rotation.py` Step 4 Header-Card-Link-Check:**
- Neue Funktionen (alle modul-intern, kein zweites Skript — Lock F3 revidiert):
  - `_extract_header_card_block(md_text) -> str | None` — YAML-Frontmatter extrahieren (Doc ohne `---` → None, driftet nicht)
  - `_iter_header_card_link_values(yaml) -> list[(line_offset, value)]` — `up:`-Zeile + alle `  - ` unter `down:`
  - `_strip_card_link(value) -> str` — Kommentar ab `#`, dann ``**`` + Backticks weg, Underscores **bleiben** (Lock-Schritt 3)
  - `_is_pathish_token(token) -> bool` — `/` oder `.md/.py/.sql/.svg`-Endung → pathish; sonst Prosa → skip (Lock-Schritt 5; erklärt `docs/INDEX.md:7 down: every project doc (that is the point)` korrekt)
  - `_discover_step4_md_files(repo_root) -> list[Path]` — alle `*.md` außer `.git/`, `.venv/`, `node_modules/`, `.agents/`, `__pycache__/` (Lock-Schritt Scope)
  - **`check_header_card_links(md_path) -> list[(diagnostic, value)]`** — die exponierte Funktion, validiert jede `up:`-/`down:`-Target-Existenz
- Verdrahtung in `main()` nach Steps 2/3 im selben `--strict`-Block (gleicher `return 1`-Pfad). Lock H2: erst NACH H-3/H-4 (Commit `fa51084`), damit jeder Commit zwischen H-3 und H-1 nicht den Pre-Commit-Hook selbst blockt.
- Modul-Docstring auf 4 Steps erweitert (P14-F Step-2 + P16-F9 Step-3 + P16-H-1 Step-4).
- `--strict`-Hilfetext angepasst: „Enable Steps 2 + 3 + 4 (P14-F + P16-F9 + P16-H-1)".
- Commit `b865808` (269 insertions, +13 deletions).

**3. H-1 Tests — `tests/test_check_doc_rotation.py` +6 A1–A6:**
- A1 `test_header_card_up_link_ok` — `up: ./X.md` auf existierende Datei → keine Befunde
- A2 `test_header_card_down_links_with_inline_comment` — `  - X.md   # Kommentar` → Kommentar abgeschnitten, Pfad aufgelöst
- A3 `test_header_card_strip_markdown_preserves_underscores` — ``**X**`` + `PHASE10_CLOSEOUT_HANDOVER.md` → Bold/Backticks weg, Underscores bleiben (Lock-Schritt 3 Pin)
- A4 `test_header_card_prose_down_entry_is_ignored` — `down: every project doc (that is the point)` → Prosa ohne Slash/.md-Endung ignoriert (Regressions-Pin für `docs/INDEX.md:7`)
- A5 `test_header_card_double_dotdot_is_flagged` — Pin für die 21 Pattern-A-Bugs aus H-3 (`../../` in `phase*/`-File)
- A6 `test_header_card_repo_is_clean` — End-to-End gegen das echte Repo, schlägt fehl sobald jemand eine kaputte Karte einführt
- Commit `e6246fe` (168 insertions). Σ root 115 → 121, repo-weit 1939 → **1945**.

**4. H-1 Operational Scripts sync (`scripts/install_hooks.sh` + `scripts/dev_install.sh` + `.git/hooks/pre-commit`):**
- `scripts/install_hooks.sh` CANONICAL_BODY auf 4 Steps + Step-4-Default-Kommentar erweitert.
- `scripts/dev_install.sh` Kommentar-Block um P16-H-1 erweitert.
- `.git/hooks/pre-commit` mit CANONICAL_BODY byte-identisch synchronisiert → idempotenter Installer meldet exit 0 beim nächsten Lauf.
- Im selben Code-Commit `b865808` gebündelt (operational scripts = code-change Begleitung, keine separate Commit).

**5. H-5 Verifikation (Akzeptanz H am Ende von #29):**
- `python3 scripts/check_doc_rotation.py --strict --quiet` → **exit 0** ✓
- Σ-Sweep selbst nachgemessen (16 Phasen einzeln + root): **1945 grün** (97+82+105+161+190+76+169+259+95+165+149+82+61+126+7+121 = 1945; exakt der F-Exec-Plan §3 H-Akzeptanz-Wert).
- `git grep -n "\.\./\.\./" -- "phase*/*.md" "docs/concepts/*.md"` zeigt weiterhin `../../`-Header-Card-Lines in `docs/concepts/*` — alle aber **valid** (siehe Findings).
- Header-Card-Links end-to-end via `test_header_card_repo_is_clean` validiert (alle 92 Cards grün).
- `bash scripts/install_hooks.sh` → **exit 0** (Hook up-to-date).

**6. Doc-Rotation Session #28 → SESSIONS_ARCHIVE + Session #29 → Phasenkopf:**
- `phase16_activation/SESSIONS_ARCHIVE.md` Session-#28-Block verbatim (Z. 15-114 der alten CLAUDE.md) als 29. Eintrag prependiert (newest-first).
- Preamble-„Stand nach Exec-Session #28" → „Stand nach Exec-Session #29", Archiv-Count **28 → 29**.
- `phase16_activation/CLAUDE.md` Session-#28-Block durch Session-#29-Block ersetzt.

### Findings

🟢 **Akzeptanz H exakt erreicht: Hook exit 0 + Σ 1945 + alle 92 Header-Cards validiert.** F-Exec-Plan §3 H-Akzeptanz-Wert (Σ = 1939 vor H-1 + 6 neue Tests = 1945) **auf den Punkt getroffen**. H-1, H-2, H-5 alle ✅.

🟡 **Drift: Auftrag-Akzeptanz „Header-Card-Treffer = 0" Interpretation.** Die wörtliche Akzeptanz des Nikinger-Auftrags war `git grep -n "\.\./\.\./" -- "*/*.md" =0 Header-Card-Treffer`. Nach H-3 + H-1 gibt es weiterhin `../../`-Header-Card-Lines in `docs/concepts/*` (z. B. `phase16_activation_plan.md:8-12`), aber **alle resolved** korrekt zu existierenden Files (von `docs/concepts/` aus ist `../../phaseX/Y.md` der korrekte Weg ins Repo-Root + Phase-Ordner — `../` würde nach `docs/` zeigen, falsch). Interpretation: „Header-Card-Treffer = 0 broken links", was durch `check_header_card_links` validiert wird (Hook exit 0). Body-Links (in `phase13_live_data/SESSIONS_ARCHIVE.md` etc.) sind out-of-scope per F-Exec-Plan §1.4 V-8. Wenn der Nikinger eine striktere Lesart will (= keine `../../`-Literale in Header-Cards, auch wenn valide), wäre das Phase-17-Material (würde 12+ Dateien in `docs/concepts/` berühren, alle Wege verifizieren).

🟢 **Lock F3-Revision sauber umgesetzt.** Nikinger 2026-09-08 entschied „kein neues Hook-Skript". Heute umgesetzt: Step 4 lebt im selben `scripts/check_doc_rotation.py`, im selben `--strict`-Block, mit derselben `return 1`-Logik. Der Pre-Commit-Hook bleibt **eine** Python-Aufruf-Zeile. `install_hooks.sh` hat jetzt 4 Steps im Kommentar-Block + CANONICAL_BODY byte-identisch zum installierten Hook.

🟢 **A4-Pin funktioniert.** `docs/INDEX.md:7 down: every project doc (that is the point)` wird korrekt als Prosa erkannt (kein `/`, keine `.md/.py/.sql/.svg`-Endung → skip). Der Pin-Test `test_header_card_prose_down_entry_is_ignored` schlägt fehl, wenn die `_is_pathish_token`-Heuristik gebrochen wird. Damit ist die wichtigste `docs/INDEX.md`-Regressions-Bombe- entschärft.

🟢 **Cross-Phase-Touches minimal + scoped.** 5 Files in dieser Session editiert: `scripts/check_doc_rotation.py` (eigener Code, kein Phase-Scope) + `scripts/install_hooks.sh` (Tracked-Installer, keine Phase-Freigabe nötig) + `scripts/dev_install.sh` (Tracked-Installer, gleiches) + `tests/test_check_doc_rotation.py` (root-Tests, keine Phase-Freigabe nötig) + `docs/DOC_LAYERS_CONVENTION.md` (eigene Konvention, keine Phase-Freigabe nötig). Keine Phase-Code-Touches.

🟢 **Header-Card-Strip-Pipeline explizit per Test gepinnt (A2 + A3).** `Inline-Comment ab #` + ``**``/Backtick-Strip + Underscore-Erhalt — alle drei Regeln durch je einen Test abgedeckt. Wenn jemand an `_strip_card_link` dreht, fallen die Tests. Genau das, war das Lock-Schritt-3-Versprechen der F-Exec-Plan H-1 Spec.

### Open questions / blockers

- **Keine Tag-1-Blocker (Fortschreibung Session #28).** Alle Session-#28-Watch-Items unverändert offen (K3 kumuliert sich, K6-Auslastung 98,4% Beobachtung, Block I).
- **Σ-Drift 1940 (Session #27) → 1939 (Session #28) → 1945 (heute).** Der gestern beobachtete -1 Test ist heute durch +6 neue H-1-Tests überkompensiert; die 1940 → 1939-Drift-Auflösung bleibt empfohlen für Session #30 (Suite-für-Suite-Diff gegen Session-#27-Baseline).
- **Block-H-Rest:** H-5 (Verifikation) ist heute erledigt. Drift #8 in v3 §11 + W2-Notiz offen für Session #30.
- **Block I Di 2026-09-22 nach 17:30** unverändert.

### NEXT (für die nächste Session)

**Push-Status:** **3 Commits pending** nach dieser Session (`b865808` + `e6246fe` + `4779660`). **Nikinger pusht jetzt mit `git push origin main`** (working tree clean danach außer `data/`). Der `fa51084` aus Session #28 ist bereits gepusht.

**Tagesroutine Tag 2–Tag 10 (Operator):** unverändert (Session #27 NEXT-Block).

**Offene Items für die nächste Exec-Session (Session #30, Block I Tag-10-Closeout):**

1. **Session #30 (Block I, Tag-10-Closeout) — geplant Mo/Di 2026-09-21/22 nach 17:30 Berlin:** Fokus I-1 Tag-10-Summary (`autonomy_report.py --from 2026-09-09 --to 2026-09-22 --summary`) + I-2 Closeout-Handover (analog Phase-15-Pattern) + I-3 SVG (1080×1080, 3-Säulen Status-Bilanz) + I-4 Status-Pflege root/ROADMAP/README/INDEX + I-5 Session-Rotation. Plus die Σ-Drift-Auflösung (heute 1945 vs. #27-Behauptung 1940; Differenz zur #28-Baseline 1939 = +6 neue Tests dokumentiert). Total ~5 Commits + 1 neuer SVG.
2. **Drift #8 in v3 §11 + W2-Definition-Update-Markierung** — diese Session mit der v3-§11-Aktualisierung + W2-Definition-Update-Markierung (die H-1-Tests beweisen die „full-file-count"-Toleranz).
3. **Falls K4 FAIL an ≥ 2 Tagen:** Trigger T-5 → Exec-Session on demand.
4. **Falls K6 FAIL:** Trigger T-8 → Exec-Session on demand.
5. **Falls erster OPEN-Trade:** Gate P7/A6 → A6-Live-Verify-Session on demand.

**Push-Freigabe-Stand nach dieser Session:** 3 Commits pending (`b865808` + `e6246fe` + `4779660`). Nikinger pusht.

**Block-Status nach Session #29:**

| Block | Status |
|---|---|
| A (Haushalt) | ✅ (Session #1-#4) |
| B (Substrat) | ✅ (Session #3) |
| C (Research-Loop) | ✅ (Sessions #3-#7) |
| D (Freischaltung) | ✅ (Session #7-#17) |
| E (2-Wochen-Test) | 🔄 — Tag-1-Verify ✅ (#27), H-3+H-4 ✅ (#28), **H-1+H-2+H-5 ✅ (#29, diese)**, Block I Di 2026-09-22 (#30) |
| F (Subphase) | 🔄 — G Tag 1 ✅, H ✅ (#28-#29), I (#30) |
