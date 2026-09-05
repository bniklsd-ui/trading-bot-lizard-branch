---
status: active-phase
purpose: PHASE-HEAD, Phase 16 (Freischaltung) — 🔄 eröffnet 2026-09-05 (Plan-Session, Fable 5.1). Mission = jedes gebaute Feature läuft, jeder bekannte Bruch ist zu, ein vorregistrierter 2-Wochen-Lauf beweist Autonomie ohne Hand. Kern-Befund: der Bot ist seit 2026-08-31 faktisch tot (100 % Research-Abstain, 77/Tag) — Ursache Infrastruktur (Historien-Tabelle ohne Zeitfenster), nicht Strategie; dazu Token-Budget täglich um 15:48 leer, Live-DB auf Schema v7 (Migrations nie angewendet, Doku behauptete das Gegenteil), Flags nicht restart-fest, 3 Wochenend-Epics im Universum.
read-when: jede Phase-16-Session; zuerst den neuesten `## Session stopped`-Block, dann den Plan-Step, der dran ist
detail: L1
up: ../CLAUDE.md
down:
  - ../docs/concepts/phase16_activation_plan.md   # 📕 der Plan (P1–P17, L1–L9, Blöcke A–E, AK1–AK16, §9 Drift, §13 Opus-Review)
  - ../phase15_v4/PHASE15_CLOSEOUT_HANDOVER.md    # 📕 Vorgänger-Handover (E1–E3 werden hier geschlossen)
  - ../phase7_reward/PHASE12_RECONCILIATION_TIMING_PLAN.md   # 📕 A6 hängt an Migration 008
  - ../phase5_execution/CLAUDE.md                 # B3-Block → Plan D3
  - ./SESSIONS_ARCHIVE.md                         # 📦 (wird von der ersten Exec-Session angelegt)
updated: 2026-09-05 (Plan-Session)
---

# Phase 16 — Freischaltung

**Mission in einem Satz:** jedes gebaute Feature läuft, jeder bekannte Bruch ist zu, und ein
vorregistrierter 2-Wochen-Lauf beweist Autonomie ohne Hand.

Der Plan ist execution-ready und direkt an Sonnet 5 übergebbar:
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
| L9 | yF-Circuit-Breaker trippt jeden Morgen 09:05 (leerer Frame ≠ Ausfall) — braucht P3-Freigabe | 🟢 |

Dazu aus dem Opus-Review (Plan §13): Bar-Stream-Token-Snapshot (Arm wäre nach der ersten
IG-Token-Rotation tot) und die fehlende Prozess-Supervision (vorregistriert als Grenze, nicht Fix).

## Blöcke

| Block | Inhalt | Gate |
|---|---|---|
| **A** | Haushalt: Step-0-Ritual · Σ-Baseline **1843** · Code↔.md-Sweep · WebUI-Log · Push | keins |
| **B** | Substrat: Schema-Floor im Preflight + Operator-Apply (v9) + Ledger-Restore · Wochenend-Filter + Demotion | nach A |
| **C** | Research-Loop: Historien-Fenster 14 d · Budget 300 k · (Breaker-Semantik, P3-Freigabe offen) | nach B |
| **D** | Freischaltung: Defaults ON + `--no-*` · Bar-Stream-Token-Wrapper · Promotion-Bridge + Compiler · Margin-Headroom nach Live-Probe | nach C |
| **E** | 2-Wochen-Autonomie-Test: Vorregistrierung · `autonomy_report.py` · Runbook · Closeout | nach D + Restart |

**Cross-Phase-Freigabe (Nikinger 2026-09-05):** P1, P2, P4, P5, P7, P8, P9, P15 — nur wo ein Step
sie braucht. **P3 nicht** (Step C5 wartet). P6/P10/P12/P13/P14 unangetastet.

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

## Session stopped — 2026-09-05 (Plan-Session, Fable 5.1 — Phase 16 eröffnet, Plan committet)

> **Auftrag:** Nikinger-Chat 2026-09-05: „Phase 16 sollte mind. alle Löcher, die der Bot noch hat,
> stopfen, sodass alle Funktionen freigeschaltet werden, und nach Phase 16 ein ausgiebiger Test
> von z. B. 2 Wochen komplett autonom." Plan bis Ausführungsreife, Fragen gebündelt vorab,
> Advisor-Ersatz per Agent (Opus vor dem Festlegen, Sonnet-Cold-Read vor „fertig").

### Completed
- **Recherche read-only** (Live-DB `mode=ro`, Logs, `/proc`, git): 9 Löcher L1–L9 verifiziert
  (Plan §3), Σ-Baseline **1843** selbst gemessen (Plan §2.1), 7 Commits lokal ahead (`2f9eb82`).
- **Nikinger-Fragerunde** (10 Entscheidungen, alle gelockt → Plan §1 P1–P17).
- **Opus-Plan-Agent-Review** (Plan §13): 3 Struktur-Änderungen übernommen — B1 = Schema-Floor
  statt In-Daemon-Migration (gelockte Preflight-Entscheidung `wiring.py:1070` + Lock-Risiko),
  D1.2 = Bar-Stream-Token-Wrapper (latenter Bug seit Phase 13 B3), E2 = append-only Messquellen;
  C3b Caching gestrichen (Meter zählt Cache-Reads voll + Präfix < 1024); Ledger-Restore nach B2;
  P17 erlaubte Operator-Ereignisse vorregistriert. Ein Dissens (Compiler) dokumentiert.
- **Sonnet-Cold-Read** (Anker-Verifikation) — Ergebnis siehe Findings.
- `docs/concepts/phase16_activation_plan.md` (📕, NEU) · dieser Phasenkopf (NEU) · `docs/INDEX.md`
  2 Zeilen · `ROADMAP.md` Phase-16-Abschnitt · root `CLAUDE.md` Status-Absatz + Tabellenzeile.
- **0 Code-Edits, 0 Bot-Touch** (Bot lief die ganze Session, PID 124569 seit 09-03).

### Findings
- 🔴 **L3 ist die eine Doku-Lüge, die Code-Wahrheit widerlegt:** „`db.py:run_migrations()` wendet
  beim nächsten Service-Restart automatisch an" steht in root-CLAUDE.md:108, ROADMAP.md:441 und
  im P15-Handover (§7 E1, §9.13, §10 #4) — kein Produktions-Caller existiert. Korrektur = Plan A-3.
- 🟡 **Zwei Stellen, an denen die Plan-Session allein entschieden hat** (Nikinger kann in Runde 2
  überstimmen): (a) `InstinctConfig.enable_instinct_promotion` → Default True (P5, supersedet
  P15-P10, Begründung: VETO 5 kann nur vetoen); (b) Caching **nicht** bauen trotz „können wir
  testen" (P3, zwei verifizierte Fakten machen den Test ergebnislos).
- 🟡 **C5 (L9) braucht eine P3-Freigabe**, die nicht in der Liste war — der Step ist im Plan, wartet.
- 🟢 `LiveQuoteCache` existiert nicht (0 Treffer) — ROADMAP 9b + phase9-Head führen eine Leiche (A-3).

### Next
- **Exec-Session (Sonnet 5 / `claude-minimax`):** Plan §6 **Block A, Step A-0** — diesen Block per
  Rotationsregel nach `SESSIONS_ARCHIVE.md` (neu anlegen) rotieren, `check_doc_rotation.py:66` um
  `phase16_activation` ergänzen, dann A-1 (Ritual), A-2 (Σ = 1843 erwartet), A-3 (Sweep).
- **Operator sofort möglich (freigegeben):** `git push origin main` (7 + Plan-Commit).
- **Operator im B2-Fenster** (alle vier Dienste gestoppt): Backup → `init_db.py --db-path
  data/trading_bot.sqlite` → Verify v9 → Ledger-Restore SQL (Plan §6 B2).

### Open questions / blockers
- P3-Freigabe für C5 (fetcher.py Breaker-Semantik) — ja/nein.
- Bestätigung P5 (Promotion-Default True) und P3 (kein Caching) — sonst Runde 2.
- Push-Freigabe für den Plan-Commit dieser Session.
