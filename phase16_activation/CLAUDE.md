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
updated: 2026-09-08 (+ Plan-Session #21 schließt ab: **`PHASE16_F_EXEC_PLAN.md` NEU** [611 LOC, Blöcke J/H/G/I] — drei Struktur-Defekte des laufenden 2-Wochen-Tests selbst gemessen [J-D1 LS-Bar-Stream schreibt nichts, `archive.py:77` `check_same_thread`-Default, 63 942 `ProgrammingError`, `bars.source='ls'` = 0; J-D2 K1 zählt ohne Fenster, `evaluate_k1` bekommt `from_ts`/`to_ts` von keinem der beiden Aufrufer Z. 870/919 → 7 statt 1 Start; J-D3 K4 unerreichbar, `heartbeat.py:73` misst gegen 00–24 h → `ok=False` an 10 Tagen in Folge]; Nikinger-Entscheidungen: Variante A [Lauf abbrechen, fixen, Prereg v2, Uhr auf Tag 1] + Cross-Phase **P12** freigegeben + Lock **F3 revidiert** [Hook-Step 4 statt neuem Skript] + Pattern C = Referenz entfernen; Σ-Regression-Baseline **1934** vor dem ersten Fix, 16 Suites einzeln gemessen; Step-0-Legacy-Ritual No-Op; 7 Aussagen aus `PHASE16_PARTIAL_CLOSEOUT.md` korrigiert [§1.4]; Exec-Session #20 → Archiv [21. Eintrag]; Push-Freigabe steht aus. — Vorheriger Stand: Exec-Session #19 schließt ab: Doc-Drift-Audit repo-weit nach Nikinger-Push — 6 Audit-Checks: #1 Push-Baseline ✅, #2 Σ-Konsistenz ✅ (Σ 1934), #3 Archiv-Integrität 🟢 (2 F8-B-Reparaturen `ce74ee1` Phase-14 + `23bbd14` Phase-15), #4 ein Block/Phasenkopf ✅, #5 INDEX-Vollständigkeit 🟡 (224 Skill-Internals fehlen — Scope-Drift), #6 Header-Card-Links 🟡 (29 echte fehlende Links aufgedeckt, read-only dokumentiert, Reparatur in Phase-16-F-Subphase Block H); Σ 1924 → 1934 unverändert (Archiv-Reparaturen = Markdown-Only); origin/main = 560d038, 0 Commits pending (Nikinger hat Session-#19-Commits gepusht); Cross-Phase-Freigabe: P14 für Phase-14 + Phase-15-Archive-Touch (`ce74ee1` + `23bbd14`), P16 für diese Rotation]; Exec-Session #20 schließt ab: **Phase-16-F-Subphase-Eröffnung mit `PHASE16_PARTIAL_CLOSEOUT.md` NEU** (310 LOC, Mini-Plan für die 2-Wochen-Test-Periode in 3 Blöcken G/H/I: G = E4-Tagesroutine-Begleitung 9 Tage, H = Audit-Restbefunde-Reparatur 29+1+1 am Wochenende 13.–14. Sept., I = Tag-10-Closeout Mo 2026-09-21 nach 17:30) + 8 Locks F1–F8 + 8 Akzeptanz AK-F1–AK-F7 + 8 Operator-Aktionen Nikinger + 7 Out-of-Scope-Items Phase-17 + 8 Drift-Items; kein Phase-17 (Nikinger-Auftrag „Keine Phase 17, weitere Phase 16 Subphase"); Modul-Tabelle um `PHASE16_PARTIAL_CLOSEOUT.md` ergänzt; Σ 1934 unverändert (docs-only, kein Test-Touch, kein Code-Touch außer der F-Subphase-Eröffnung selbst); 0 Commits pending (Nikinger pusht 560d038 nach dieser Session-#19-Eröffnung); Push-Freigabe-Stand: dieser Commit + 1 = 1 Commits pending nach Commit
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
| `PHASE16_F_EXEC_PLAN.md` | 📕 Exec-Plan der F-Subphase (Blöcke J/H/G/I) — supersedet die H-Mechanik aus `PHASE16_PARTIAL_CLOSEOUT.md` §4 | F |
| `PHASE16_AUTONOMY_PREREGISTRATION_v2.md` | 📕 Prereg v2 (supersedet v1, Grund = die drei J-Defekte) | J5 |
| `PHASE16_CLOSEOUT_HANDOVER.md` + `docs/architecture/phase16_activation.svg` | Closeout nach Tag 10 | I-2 + I-3 |
| *(Cross-Phase)* `phase15_v4/instinct/bridge.py`, `compile.py` | Promotion-Bridge + Prädikat-Compiler | D2 |
| *(Cross-Phase)* `phase1_broker_wrapper/scripts/probe_market_margin.py` | Operator-Live-Probe für B3 | D3.0 |

---
## Session stopped — 2026-09-08 (Opus-5-Plan-Session #21, Phase-16-F-Exec-Plan — `PHASE16_F_EXEC_PLAN.md` NEU [611 LOC, Blöcke J/H/G/I]; **drei Struktur-Defekte des laufenden 2-Wochen-Tests selbst gemessen**, Nikinger-Entscheidung „Lauf abbrechen, fixen, neu vorregistrieren"; Lock F3 revidiert [Hook-Step 4 statt neuem Skript]; Cross-Phase-Freigabe **P12** erteilt; Σ-Regression-Baseline **1934** vor dem ersten Fix)

> **Auftrag:** Nikinger-Chat 2026-09-08 — Plan für die noch offenen und neu offenen Items der
> Phase-16-F-Subphase, ausführungsreif für Sonnet 5. Kein Phase 17 (Lock F1 unverändert).

### Completed

- **`PHASE16_F_EXEC_PLAN.md` NEU** (611 LOC): Blöcke **J** (Live-Reparatur) · **H** (Audit-Restbefunde,
  revidierte Mechanik) · **G** (Tagesroutine) · **I** (Tag-10-Closeout). 13 Locks (J1–J8, H1–H4, F1)
  mit Begründung je Zeile, Schritt-Sequenz mit verbatim-Ankern + heutigen Zeilennummern, Testliste
  (+11 → Σ 1945), 10 Akzeptanzkriterien, vollständige Verify-Liste V-1..V-10, Fehlgriff-Tabelle.
- **`docs/INDEX.md`** +1 Zeile (Phase-16-Cluster, im selben Commit).
- **`phase16_activation/CLAUDE.md`** Modul-Tabelle +2 Zeilen (`PHASE16_F_EXEC_PLAN.md`,
  `PHASE16_AUTONOMY_PREREGISTRATION_v2.md`).
- **Σ-Regression-Baseline genommen (vor dem ersten Fix): 1934 grün**, 16 Suites einzeln gemessen
  2026-09-08. Deckt sich Zeile für Zeile mit `PHASE16_PARTIAL_CLOSEOUT.md` §1.2 — bestätigt, nicht übernommen.
- **Step-0-Legacy-Ritual gelaufen: No-Op.** `grep -rn -i "turbo\|CALL/PUT\|pre_trade_option_check"` →
  4 Treffer, alle bewusst eingefroren und dokumentiert (`ARCHITECTURE.md:76,134,212`, `README.md:28`),
  kein Python-Treffer.

### Findings (alle 2026-09-08 selbst gemessen, Details im Plan §1.3)

- **J-D1** — LS-Bar-Stream schreibt nichts. `data_foundation/archive.py:77` öffnet SQLite mit dem
  `check_same_thread=True`-Default; `live_data/stream.py:498` schreibt aus dem Lightstreamer-Thread.
  **63 942** `sqlite3.ProgrammingError` allein heute, erster um 09:35:25. `bars.source='ls'` = **0**,
  seit es die Tabelle gibt. Log wächst dadurch ≈25 MB/h.
- **J-D2** — K1 misst ohne Fenster. `evaluate_k1` (`autonomy_report.py:542`) hat `from_ts`/`to_ts`;
  **beide** Aufrufer (Z. 870 + 919) übergeben nichts → 7 Alt-Starts seit 2026-08-31 statt der einen
  von heute. Dazu zählt `_START_PATTERNS["webui"]` (Z. 143) einen Start doppelt.
- **J-D3** — K4 unerreichbar. `heartbeat.py:73` prüft die Bar-Dichte gegen 00:00–24:00 UTC; die
  Overnight-Lücke (≈930 min) reißt die 5-Minuten-Gap-Schwelle (Z. 124) an **jedem** Handelstag →
  `ok=False` durchgehend seit 2026-08-24 (10 Tage in Folge). `worst_coverage` ist reine Telemetrie
  und gattert nichts — wer `MIN_WINDOW_RATIO` anfasst, ändert gar nichts.
- **7 Aussagen aus `PHASE16_PARTIAL_CLOSEOUT.md` gegen Code/Live-DB korrigiert** (Plan §1.4) —
  u. a. „endet ohne Traceback" (falsch), das G2-Caps-Pin-Kommando (`/proc/<pid>/cmdline` enthält die
  Caps nicht) und der Pattern-B-`sed` (erzeugt das nicht existierende `docs/CLAUDE.md`).
- **Zwei Offenposten erledigt:** Ledger-Restore (0 Zeilen `kind='rescue'`) und Live-DB-Migration
  008+009 (`_schema_version` = 9).
- Runbook-v2-Pflicht-SQL für die SUN*-Epics war ein **No-Op** (`WHERE status='active'`, alle 5 stehen
  auf `verified`). Prereg formal erfüllt — zufällig; 3 SUN*-Epics zogen heute trotzdem 15 IG-Punkte.

### Nikinger-Entscheidungen (2026-09-08)

1. **Variante A** — Lauf abbrechen, fixen, `PHASE16_AUTONOMY_PREREGISTRATION_v2.md` als datiertes
   Supersede-Doc, Uhr auf Tag 1. (v1 bleibt Byte-identisch, so schreibt v1 es sich selbst vor.)
2. **Cross-Phase P12 freigegeben** für `data_foundation/archive.py` + `heartbeat.py`.
3. **Lock F3 revidiert** — Header-Card-Link-Check wird Step 4 in `scripts/check_doc_rotation.py`,
   kein zweites Skript.
4. **Pattern C** — Referenz auf `PHASE15_A1_A6_STEP_RECORDS.md` entfernen, Datei nicht erfinden.

### Next

- **Exec-Session startet mit Plan §3 Step 0**, dann **Block J** (J0 Bot-Stopp ist Operator-Aktion).
- Block J vor Block H — der Test kann erst neu starten, wenn die drei Defekte weg sind.

### Open questions / blockers

- **V-4 (Plan §6):** ob der zweite `ok=False`-Zweig (`heartbeat.py:142`, `pairs_resolved == 0`)
  zusätzlich feuert, entscheidet sich erst im ersten POST_WINDOW nach dem Restart. Wenn K4 nach J3
  nicht grün wird, ist **das** der erste Verdächtige, nicht der Fenster-Fix.
- Tag-1/Tag-10-Daten stehen erst nach J6 fest; Block I trägt deshalb kein festes Datum.
- Push-Freigabe für diesen Commit steht aus.
