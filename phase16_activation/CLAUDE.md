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
updated: 2026-09-08 (+ Exec-Session #20 → Archiv; Exec-Session #19 schließt ab: Doc-Drift-Audit repo-weit nach Nikinger-Push — 6 Audit-Checks: #1 Push-Baseline ✅, #2 Σ-Konsistenz ✅ (Σ 1934), #3 Archiv-Integrität 🟢 (2 F8-B-Reparaturen `ce74ee1` Phase-14 + `23bbd14` Phase-15), #4 ein Block/Phasenkopf ✅, #5 INDEX-Vollständigkeit 🟡 (224 Skill-Internals fehlen — Scope-Drift), #6 Header-Card-Links 🟡 (29 echte fehlende Links aufgedeckt, read-only dokumentiert, Reparatur in Phase-16-F-Subphase Block H); Σ 1924 → 1934 unverändert (Archiv-Reparaturen = Markdown-Only); origin/main = 560d038, 0 Commits pending (Nikinger hat Session-#19-Commits gepusht); Cross-Phase-Freigabe: P14 für Phase-14 + Phase-15-Archive-Touch (`ce74ee1` + `23bbd14`), P16 für diese Rotation]; Exec-Session #20 schließt ab: **Phase-16-F-Subphase-Eröffnung mit `PHASE16_PARTIAL_CLOSEOUT.md` NEU** (310 LOC, Mini-Plan für die 2-Wochen-Test-Periode in 3 Blöcken G/H/I: G = E4-Tagesroutine-Begleitung 9 Tage, H = Audit-Restbefunde-Reparatur 29+1+1 am Wochenende 13.–14. Sept., I = Tag-10-Closeout Mo 2026-09-21 nach 17:30) + 8 Locks F1–F8 + 8 Akzeptanz AK-F1–AK-F7 + 8 Operator-Aktionen Nikinger + 7 Out-of-Scope-Items Phase-17 + 8 Drift-Items; kein Phase-17 (Nikinger-Auftrag „Keine Phase 17, weitere Phase 16 Subphase"); Modul-Tabelle um `PHASE16_PARTIAL_CLOSEOUT.md` ergänzt; Σ 1934 unverändert (docs-only, kein Test-Touch, kein Code-Touch außer der F-Subphase-Eröffnung selbst); 0 Commits pending (Nikinger pusht 560d038 nach dieser Session-#19-Eröffnung); Push-Freigabe-Stand: dieser Commit + 1 = 1 Commits pending nach Commit
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
| `PHASE16_PARTIAL_CLOSEOUT.md` | 📕 Partial Closeout zur 2-Wochen-Test-Halbzeit (Phase-16-F-Subphase: Blöcke G/H/I — E4-Begleitung + Audit-Restbefunde-Reparatur + Tag-10-Closeout) | F |
| `PHASE16_CLOSEOUT_HANDOVER.md` + `docs/architecture/phase16_activation.svg` | Closeout nach Tag 10 | I-2 + I-3 |
| *(Cross-Phase)* `phase15_v4/instinct/bridge.py`, `compile.py` | Promotion-Bridge + Prädikat-Compiler | D2 |
| *(Cross-Phase)* `phase1_broker_wrapper/scripts/probe_market_margin.py` | Operator-Live-Probe für B3 | D3.0 |

---
## Session stopped — 2026-09-08 (MiniMax-M3-Exec-Session #20, Phase-16-F-Subphase-Eröffnung — `PHASE16_PARTIAL_CLOSEOUT.md` NEU [310 LOC, Mini-Plan für die 2-Wochen-Test-Periode in 3 Blöcken G/H/I: G = E4-Tagesroutine-Begleitung 9 Tage, H = Audit-Restbefunde-Reparatur 29+1+1 am Wochenende 13.–14. Sept., I = Tag-10-Closeout Mo 2026-09-21 nach 17:30], 8 Locks F1–F8 [F1: Phase-16-F als Subphase, kein Phase-17; F2: F9-Mechanik zentral; F3: H-1-Hook analog F9 vor H-3-Reparatur; F4: Sammel-Commit für 29+1+1; F5: Block-G-Vorrang, Code-Edits außerhalb Trade-Fenster; F6: read-only für aktive Phasen; F7: Tag-10-Closeout Mo-Abend; F8: Phase-15 `requires-python`-Align offen für Phase-17], 8 Akzeptanzkriterien AK-F1–AK-F7, 8 Operator-Aktionen Nikinger, 7 Out-of-Scope-Items für Phase-17, 8 Drift-Items, Cross-Phase-Touch 6 Phasen + root, Σ 1934 unverändert, Exec-#19-Block verbatim nach SESSIONS_ARCHIVE.md rotiert [20. Eintrag, +1 vs. Stand Session #19], Push-Freigabe-Stand: 0 Commits pending nach Nikinger-Push `560d038`)

> **Auftrag:** Nikinger-Chat 2026-09-08 (Folgesession Phase 16, auf meine Audit-Bericht-Frage „Wie verfahren mit den 31 Audit-Restbefunden? Was sind nicht-geblockte offene Items?"): **„Ich schlage vor, eine Plan Session kümmert sich darum einen Mini Plan zu schreiben, der in der Zeit des 2 Wochen Tests die noch zu tuenden offenen Items strukturiert (inklusive deines Empfohlenes Weges der Audit Lösung) angeht. Keine Phase 17, weitere Phase 16 Subphase. Schreibe z.B ein Part Closeout, dann commit und push + Danach session beenden."** — 4 Punkte explizit: (1) **Plan-Session-Format** mit Mini-Plan, (2) **Strukturierung der offenen Items für die 2-Wochen-Test-Periode**, (3) **Phase-16-F als Subphase** (kein Phase-17, keine neue Nummer), (4) **„z.B. ein Partial Closeout"** als Dokumentenformat (analog `PHASE15_CLOSEOUT_HANDOVER.md` aber mid-phase statt full-close). Mein Vorschlag aus der vorherigen Antwort (Phase-17-Plan-Session mit Blöcken A-F) wurde explizit abgelehnt durch „Keine Phase 17" → umgesetzt als Phase-16-F-Subphase mit 3 Blöcken G/H/I + 7 Locks F1-F8 (F1 supersedet die Phase-17-Plan-Empfehlung).
>
> Plan-Anker: Phase-16-Phasenkopf Session-#19-Findings (6 Audit-Checks, 31 Restbefunde, 2 davon repariert) + Phase-16-Plan §1 P1 (Phase-16-als-Ganzes-Philosophie, F1 als Subphase-Erweiterung) + Phase-15-CLOSEOUT-HANDOVER als Pattern-Vorbild (763 LOC, §0 BLUF + 5-Zeilen-Bilanz, §1 SVG, §2 Locks, §3 Akzeptanz, §4 As-Built, §5 Test vs. Live, §6 Delta, §7 Offene Entscheidungen, §8 Datei-Anker, §9 Konsistenz, §10 Don'ts, §11 Was-diese-Session-gemacht-hat) + Phase-13/14-Closeouts als Pattern-Vorbilder. Cross-Phase-Touch: 6 Phasen in Block H (P7/P10/P13/P14/P15 + root docs/concepts/), alle gemäß Phase-16-Plan §4 Cross-Phase-Freigabe-Liste + Nikinger-Auftrag 2026-09-08.
>
> Ausführungs-Scope: **1 Atomic Commit** (`phase16: docs -- PHASE16_PARTIAL_CLOSEOUT.md NEU (Phase-16-F-Subphase-Eröffnung mit Mini-Plan Blöcke G/H/I + 8 Locks F1-F8 + 8 Akzeptanz AK-F1-F7 + 8 Operator-Aktionen + 7 Out-of-Scope-Items + 8 Drift-Items, Modul-Tabelle um PHASE16_PARTIAL_CLOSEOUT.md ergänzt, Session-Rotation #19→#20)`) + dieser Session-Rotation-Commit. Push-Freigabe-Stand: 0 Commits pending (Session-#19-Commits `ce74ee1` + `23bbd14` + `560d038` wurden vom Nikinger gepusht, `git rev-parse --short origin/main` = `560d038`, `git rev-list --count origin/main..HEAD` = 0 — verifiziert nach Push).

### Completed

- **`PHASE16_PARTIAL_CLOSEOUT.md` NEU** (310 LOC, ~13 KB) im Verzeichnis `phase16_activation/`. Struktur:
  - YAML-Header (status: partial, L3-Snapshot-Pattern, purpose + read-when + 4 down-Links + updated 2026-09-08)
  - §0 BLUF (5 Bullet-Points: Status, Σ, Audit-Recap, 3 Stränge, Phase-17-ausgeschlossen)
  - §1 Status-Quintessenz (4 Sub-Sections: Block-Tabelle A-F, Σ-Endstand 1934, Live-Stand E4-Tag-1, Audit-Recap 6-Checks-Tabelle)
  - §2 Audit-Befunde im Detail (29 Header-Card-Link-Drifts in 5 Pattern-Kategorien + 1 INDEX-Scope-Drift + 1 Phase-14-Order-Bug)
  - §3 8 Locks F1-F8 mit Begründung je Zeile
  - §4 Schritt-Sequenz mit 3 Blöcken G/H/I (G = E4-Begleitung 9 Tage, H = Audit-Restbefunde-Reparatur am Wochenende 13.–14. Sept., I = Tag-10-Closeout Mo 2026-09-21 nach 17:30)
  - §5 8 Akzeptanzkriterien AK-F1 bis AK-F7 mit Beleg-Quelle
  - §6 8 Operator-Aktionen tabelliert mit Kosten + Wann
  - §7 7 Out-of-Scope-Items für Phase-17 explizit delegiert (Strategie-Bewertung, Prozess-Supervision, Smoke-Test-Pattern auf Geschwister-`_build_*`, Phase-15-Wiring-Doku, Phase-15-`requires-python`-Align, Force-Trigger, Live-Account, Phase-9 `is_weekend_market`)
  - §8 8 Drift-Items dokumentiert (D-F1 bis D-F8)
  - §9 Was-diese-Session-gemacht-hat
  - §10 Cross-Phase-Touch-Disziplin (6 Phasen in Block H + Block I root/ROADMAP/README/INDEX)
  - §11 Σ-Impact (1934 → ~1944 nach Block H + Tests, Block I docs-only)
- **Modul-Tabelle im Phasenkopf** ergänzt um `PHASE16_PARTIAL_CLOSEOUT.md` (Step **F**, Partial Closeout zur 2-Wochen-Test-Halbzeit). Reihenfolge der Tabelle aktualisiert: E2 → E2-Tests → E1 → **F (NEU)** → I-2+I-3 → D2 → D3.0.
- **YAML-Header-Card `updated:` Stamp** auf `2026-09-08` aktualisiert mit Session-#20-Summary (PHASE16_PARTIAL_CLOSOUT.md NEU + Modul-Tabelle-Ergänzung + Session-Rotation #19→#20 + Push-Freigabe-Stand 0 Commits pending).
- **Session-#19-Block verbatim aus Phasenkopf nach SESSIONS_ARCHIVE.md rotiert** (20. Eintrag, oben angefügt nach dem Preamble-Block, _erster-Eintrag_ in der Archiv-Liste). Preamble aktualisiert von „Stand nach Exec-Session #18 ... #17" auf „Stand nach Exec-Session #20 ... #19" mit #19-Summary (Doc-Drift-Audit, 6 Checks, 2 F8-B-Reparaturen, 31 Restbefunde Phase-17).

### Findings

- **🟢 Phase-16-F-Subphase eröffnet ohne Phase-17-Plan-Session.** Nikinger-Auftrag 2026-09-08 („Keine Phase 17, weitere Phase 16 Subphase") supersedet die Empfehlung aus Session-#20-Antwort (Phase-17-Plan-Session mit Blöcken A-F). F1-Lock dokumentiert die Begründung (Phase 16 ist als großes Ganzes bereits geplant, Restarbeit passt in F als Subphase).
- **🟢 31 Audit-Restbefunde strukturiert in Block H + 2 Sammel-Reparaturen** (Phase 14 [9, 10] + Phase 15 [1]) **bereits in Session #19 repariert** (`ce74ee1` + `23bbd14`). F-Subphase erbt einen sauberen Repo-Stand: `check_doc_rotation.py --strict --quiet` exit 0.
- **🟢 Block G (E4-Begleitung) hat Vorrang** vor Block H (Audit-Reparatur). F5-Lock + Phase-16-Plan-§11 Operator-Trigger: Code-Edits in Block H nur **außerhalb** der Trade-Fenster (Mo-Fr 09:00–17:30). Empfehlung im Partial Closeout: Wochenende Sa/So 2026-09-13/14 für Block H (1 zusammenhängender Block, keine Markt-Unterbrechung).
- **🟢 H-1-Hook-Vor-Reparatur-Strategie** (F3-Lock) analog zu Session-#18-F9-Strategie: Hook bauen → Befunde auto-detected → Reparatur mit Hook-Beweis. Eliminiert die Klasse zukünftiger Header-Card-Drifts **vor** der aktuellen Sammel-Reparatur, statt nur die aktuellen 29 zu fixen und die Klasse offen zu lassen.
- **🟢 F-Subphase erbt saubere Phase-17-Vorbereitung.** Die 7 Out-of-Scope-Items + 8 Drift-Items sind explizit für Phase-17 delegiert (Strategie-Bewertung, Prozess-Supervision, Smoke-Test-Pattern auf Geschwister-`_build_*`, Phase-15-Wiring-Doku, Phase-15-`requires-python`-Align, Force-Trigger, Live-Account, Phase-9 `is_weekend_market` + Stale-Push-Status-Mechanik + Index-Regel-Schärfung). Phase-17-Plan-Session kann auf dieser Vorlage aufbauen.
- **🟢 Live-Stand unverändert:** Scheduler PID 281715 (K7-Caps-Pin), Recorder 268859, Discovery 268871, WebUI 268921 — alle 4 durchgehend seit Restart #4 (Di 2026-09-08 09:30:49). Tag 1 (Di 2026-09-08) abgeschlossen, Tag 2 (Mi 2026-09-09) startet morgen früh.

### Open questions / blockers

- **Live-Stand:** wie oben (alle 4 Dienste laufen, Tag 1 → Tag 2 morgen).
- **H-3-Pattern-C-Entscheidung** (Nikinger-Wahl): `phase15_v4/PHASE15_A1_A6_STEP_RECORDS.md` entweder **erstellen** (5-Zeilen-Summary mit Commit-Verweisen auf A-1..A-6-Step-Commits) ODER **Reference entfernen** aus `PHASE15_HOOK_HARDENING_PLAN.md`. Beides 1-Zeilen-Commit. Entscheidung im Block-H-Wochenende (13.–14. Sept.).
- **Push-Freigabe-Stand:** 0 Commits pending (Nikinger hat `560d038` + Vorgänger bereits gepusht). Diese Session produziert 1 Commit (`phase16: docs -- PHASE16_PARTIAL_CLOSEOUT.md NEU + Session-Rotation #19→#20`).
- **Block-E-Status:** E3 Runbook-Start ✅ (Restart #4 läuft), E4-Tagesroutine startet Tag 2 (Mi 2026-09-09), Tag-10-Closeout offen (Block I, Mo 2026-09-21 nach 17:30).
- **Keine** Blocker für den F-Subphase-Start. Alle 8 Locks F1-F8 sind mit dem Phase-16-Plan und dem Nikinger-Auftrag konsistent.

### Next (für die Folgesession, Block G + H + I nach Zeitplan)

- **Tag 2 (Mi 2026-09-09) morgens** — Block-G-Aktion G1 (Nikinger): `python3 phase16_activation/scripts/autonomy_report.py --day 2026-09-09` + G2 (K7-Caps-Pin-Verify). Kein Code-Touch.
- **Wochenende 13.–14. Sept.** — Block-H-Session: H-1-Hook bauen (2 Commits), H-2 Convention-Klarstellung (1 Commit), H-3 Sammel-Reparatur (1 Commit, mechanisch), H-4 Phase-14-Order-Fix (1 Commit), H-5 Verifikation (Hook-Beweis). Total ~5 Commits, alle außerhalb Trade-Fenster.
- **Mo 2026-09-21 nach 17:30** — Block-I-Session: I-1 Summary (Nikinger-Aktion), I-2 Closeout-Handover + I-3 SVG + I-4 Status-Pflege + I-5 Rotation. ~5 Commits + 1 neuer SVG.
- **Optional parallel zu Block G** (außerhalb Trade-Fenster): H-3-Pattern-C-Entscheidung (PHASE15_A1_A6_STEP_RECORDS.md) kann jederzeit gefällt werden.

### Watch-Item / Plan-Hygiene (für Phase-17-Material)

- **Index-Regel-Schärfung in DOC_LAYERS_CONVENTION.md** (geplant in Block H-2): Skill-Internals in `.agents/skills/` + Harness-Specs in `meta_m1_harness/specs/` sind Tooling-Metadaten, **nicht** Projekt-Doku, und werden nicht in `docs/INDEX.md` gelistet. 1-Satz-Klarstellung.
- **Reihenfolge-Check für Archive** (Phase-17-Watch-Item, nicht in Block H): F9-Erweiterung um Sub-Invariante „Archiv-Session-Nummern müssen in absteigender Reihenfolge stehen" — würde den Phase-14-File-Order-Bug (Session 7 am Ende) auto-detected. Block-H-4-Fix behebt den aktuellen Fall, aber ein Reihenfolge-Check wäre preventive.
- **Header-Card-Link-Validierung als Pre-Commit-Hook** (Block H-1, analog F9): `--strict`-Default nach Hook-Beweis. Fängt alle 29 aktuellen + alle zukünftigen Header-Card-Link-Drifts.
- **Stale-Push-Status-Mechanik** (Phase-17-Watch-Item, nicht in Block H): die 8 Drift-Items D-F4 + die 224 INDEX-Scope-Missing-Items können in Phase-17 systematisch aufgeräumt werden.
- **Phase-15-`requires-python`-Align** (Phase-17-Watch-Item, nicht in Block H): F8-Lock, Nikinger-Entscheidung. 1-Zeilen-Edit in `phase15_v4/pyproject.toml`.
- **Plan-Session-Heading-Disziplin** (Phase-17-Watch-Item, nicht in Block H): Standard-Form `## Session stopped — YYYY-MM-DD (Plan-Session, <model> — <description>)` mit klarer Distinktion zu Exec-Sessions (`MiniMax-M3-Exec-Session #N, …`).
- **Smoke-Test-Pattern auf Geschwister-`_build_*`** (Phase-17-Watch-Item, unverändert aus Session #18-F9-Watch): `_build_paper_tracker`, `_build_paper_engine`, `_build_context_recorder`, `_build_data_foundation`, `_build_research`, `_build_universe_from_db`, `_build_abstain_sink` — gleiche Exposition wie der gefixte `_build_reward_sink`.

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
| **F (Phase-16-F-Subphase: Partial Closeout + Mini-Plan Blöcke G/H/I)** | ✅ **diese Session #20** — `PHASE16_PARTIAL_CLOSEOUT.md` NEU mit 3 Blöcken (G laufend, H Wochenende 13.–14. Sept., I Mo 2026-09-21 nach 17:30) + 8 Locks F1-F8 |
| E (Autonomie-Test, E3 Runbook-Start) | ✅ (Restart #4 erfolgreich 2026-09-08) |
| E (Autonomie-Test, E4) | 🔴 offen [Tag 2 morgen, Tag 10 → Closeout Mo 2026-09-21] |
| E (Autonomie-Test, H Audit-Restbefunde-Reparatur) | 🔴 offen [Wochenende 13.–14. Sept. 2026, 5 Commits geplant] |
| E (Autonomie-Test, I Tag-10-Closeout) | 🔴 offen [Mo 2026-09-21 nach 17:30] |