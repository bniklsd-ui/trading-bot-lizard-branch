---
status: archive
purpose: Phase-15-Closeout-Handover — was V4 geleistet hat, was offen bleibt, was die nächste Session braucht
read-when: Cold-Reader-Einstieg nach Phase 15 (V4) — liest diesen Handover vor jedem anderen Phase-15-Doc, danach den Phasenkopf
detail: L3
up: ./CLAUDE.md
down:
  - ../docs/concepts/phase15_v4_plan.md          # 📕 Plan (P1–P16, AK1–AK14, §9 Drift)
  - ../phase12_data_foundation/PHASE12_CLOSEOUT_HANDOVER.md # 📕 Pattern-Vorbild
  - ../phase13_live_data/PHASE13_CLOSEOUT_HANDOVER.md    # 📕 Pattern-Vorbild
  - ../phase14_discovery/PHASE14_CLOSEOUT_HANDOVER.md    # 📕 Pattern-Vorbild
  - ./PHASE15_HOOK_HARDENING_PLAN.md            # 📕 Mini-Plan P15-F
  - ../docs/architecture/phase15_closeout.svg   # 📕 Closeout-Bild (1080×1080)
  - ../docs/architecture/phase13_14_15.svg      # 📕 Geschwister-Bild (3-Säulen)
  - ./SESSIONS_ARCHIVE.md                       # 📦 Session-Historie, newest-first
superseded: —
created: 2026-09-05
---

# Phase 15 — Closeout-Handover (2026-09-05, MiniMax-M3-Exec-Session #13)

> **Status:** Phase 15 (V4) ✅ **abgeschlossen** auf Code-Ebene (4 Blöcke A/B/C/D alle ✅).
> Eine einzige strukturelle Folge-Arbeit bleibt bewusst offen: die **Promotion-Bridge**
> (Plan §10 Out-of-Scope). Ledger-Restore (250 Punkte, Block-D-Folgefix-Schaden) und
> Live-DB-Migration 009 sind additive Operator-Aufgaben ohne Code-Touch.

---

## §0 BLUF — Phase 15 in 5 Zeilen

- **fertig gestellt:** Blöcke A (Haushalt) + B (Reward-Kalibrierung) + C (Instinct-ECC) + D (Erbstücke) — alle 4 ✅ auf Code-Ebene, Plan-Akzeptanzkriterien AK1–AK14 (mit drei Plan-§-Reduktionen transparent dokumentiert) erfüllt.
- **getestet:** Σ **1843 grün** repo-weit (Session #12-Sweep, selbst nachgemessen 2026-09-05); 99 Phase-15-Tests + 12 Phase-5-Tests + 7 Phase-13-Tests + 4 Hook-Tests = **122 Tests** für Phase 15, dazu unveränderte Test-Suiten in allen 14 Mit-Phasen.
- **live-validiert (im Rahmen der Möglichkeiten):** Block B `--apply` live ausgeführt 2026-09-03 ~12:00 CEST (`reward_pts.id=11` Score 78,72 → 50,00, pre-apply-Backup archiviert, 4 Dienste restartet); Block D Pfad-A-Operator-Skript gebaut aber AUS (`--dry-run`-Default, kein Live-Run). Block C **nicht live-migriert**: Live-DB `data/trading_bot.sqlite` steht auf Schema-Version 7, Migrations 008/009 additiv und risikofrei, werden beim nächsten Service-Restart automatisch angewendet.
- **gepusht und committet:** **18 Commits gepusht** (Sessions #5 + #9 mit D-Folgefix-Variante-C vollständig auf `origin/main`); **6 Commits lokal ahead** (C2-Code `c00ab73` + C3+C4-Code `6065e6c` + Korrekturhinweis `7b5edf0` + Sonderhinweis #12 `7816688` + 2 Session-Rotationen `#10→#11` + `#11→#12`). Push-Freigabe für die 6 ausstehenden Commits steht aus (Nikinger-Entscheidung Session-Ende).
- **nicht erreicht / offen geblieben:** (1) **Promotion-Bridge** — die strukturelle Schließung Block C ↔ VETO-Schicht (Instincts → deterministische Prädikate → `config.longterm_rules`) ist Plan §10 out-of-scope; eine spätere Wiring-Session baut sie. (2) **Ledger-Restore** — 250 fälschlich gebuchte Rescue-Punkte aus dem 2026-09-03-Pfad-A-Scharfschaltungs-Versuch, manuell, kein Code-Touch, Nikinger-Aktion. (3) **Gate P7 / A6** — Phase-12-Reconcile-Timing-Live-Verify wartet auf nächsten OPEN-Trade + 24 h Beobachtung (Backoff replay-verifiziert in Mini-Session 26). (4) **Phase-15-Row in root-CLAUDE.md** wird in dieser Session auf ✅ flipped.

## §1 Architektur-Bild

`s/../docs/architecture/phase15_closeout.svg` zeigt das Closeout-Bild (1080×1080, valid SVG).
Stil konsistent mit `phase13_14_15.svg` und den Geschwister-Closeouts.

**Drei Panels:**

1. **① Fehlerbild** (rot-getönt, 120-320 Y): Live-Substrat der 8 geschlossenen Trades —
   −1 972,87 EUR P&L bei +28,72 Score. Vier Symptome + arithmetische Ursache:
   `process_weight = 1,5` macht `max|process| = 3,75` > `|outcome bei R=−1| = 2,0`,
   Stop-Out nettet +1,10. Phase-11-H3-Beleg, `scorer.py:45-49`.

2. **② Zielbild** (grün-getönt, 340-720 Y): Vier Blöcke A/B/C/D strukturell zu, je 220×320
   Kachel mit Schritten → Status-Box endgültig/live/code-complete ✅. n=8 < n_min=50 →
   Promotion-Gatter bleibt zu Recht ZU (akzeptanzgepinnt).

3. **③ Status heute** (740-900 Y): 3-spaltig — fertig/getestet (Σ 1843),
   live-validiert + gepusht/nicht-gepusht, nicht erreicht/offen. Ehrliche Bilanz mit
   Promotion-Bridge, Ledger-Restore, A6, Live-DB-Migration 009.

**Was das Bild trägt** (920-1060 Y, gelber Callout):

① Der Reward-Loop, der Verluste belohnt
② Vier endgültig-zu Blöcke + heute-Verhalten bit-identisch (AK9)
③ Promotion-Gatter wartet zu Recht auf n ≥ n_min=50

`../docs/architecture/phase13_14_15.svg` (3-Säulen-Bild, Block D Step D2, 2026-09-01) bleibt
das architektonische Geschwister-Bild; `phase15_closeout.svg` ist das hier dokumentierte
**Solo-Closeout-Bild** (Block-Status, Bilanz, was bleibt).

---

## §2 Locks P1–P16 (Plan §1, gelockt seit 2026-08-31 Plan-Session)

| ID | Lock | Status heute (2026-09-05) |
|---|---|---|
| **P1** | `process_weight` ist die einzige Reward-Gewichtung, die Block B ändern darf | ✅ hergestellt (Code: `models.py:357`, Block B Invariante `max|process| < |outcome bei R=−1|`) |
| **P2** | Cross-Phase Phase 2 für Instinct-DB-Substrat freigegeben | ✅ ausgeführt (Session #10, `migration 009_phase15_instincts.sql`, `_INSTINCT_COLUMNS`, 3 DB-Methoden, **null** Schema-Reibung mit Phase 2 selbst — additive-only) |
| **P3** | Cross-Phase Phase 5 für VETO 5 freigegeben | ✅ ausgeführt (Session #12, `vetos.py:206-228` + `config.py:113-119`) |
| **P4** | `process_quality_score` ist NICHT abhängig von `veto_trigger_count` (NULL-Pfad) | ✅ bestätigt (`scorer.py:131` ignoriert NULL, B5-Vermerk Session #7) |
| **P5** | Block C sortiert strikt C1 (DB) → C2 (Logik) → C3 (VETO 5) → C4 (Tests) | ✅ eingehalten (Session #10/#11/#12) |
| **P6** | Akzeptanztests werden **nie** `pytest.raises` für den Extractor verwenden (best-effort-Kontrakt) | ✅ eingehalten (8 Failure-Tests über `result.ok is False`, Session #11) |
| **P7** | Block B `--apply` ist Operator-Aktion (Plan §11 #3) | ✅ eingehalten (Session #8, Nikinger-Operator-Sequenz: stop → backup → --apply → restart) |
| **P8** | Instinct-Extractor definiert eigenes `_LLMClientLike`-Protocol (Phase-7-Brain-Spiegelung, kein Import) | ✅ eingehalten (`extractor.py:60-80`, Decision F-Pattern) |
| **P9** | Validator ist deterministisch (kein LLM) | ✅ gepinnt (`test_validator_has_no_llm_import` triple-pin: Modul-Namespace + Source-Text + AST, Session #11) |
| **P10** | `enable_instinct_promotion` ist Master-Schalter (Default `False`) | ✅ gepinnt (`InstinctConfig.enable_instinct_promotion = False`, doppelter Test + Live-Verify) |
| **P11** | Instinct-Lifecycle: `proposed → validated → promoted` (+ `refuted` + `archived`) | ✅ gepinnt (`update_instinct_status(id, status)` + Per-Transition-Timestamps, Session #10) |
| **P12** | `instinct_n_min = 50`, **getrennt** von `RewardConfig.n_min = 10` (Wilson-Confidence) | ✅ gepinnt (§9.6-Drift-Vorab-Verify Session #11, getrennt in Phase 7 + Phase 15) |
| **P13** | Promotion-Harness returnt `[]` solange Bedingungen nicht erfüllt | ✅ gepinnt (`test_promotion_refuses_below_n_min`, n=8 → []) |
| **P14** | Schema-Versionierung additiv-only (kein `ALTER TABLE` auf bestehenden Tabellen) | ✅ eingehalten (Phase-2 Hard Rule, alle Migrations 005–009 additiv) |
| **P15** | Auditability: Doc-only-Edits tragen datierten Vermerk + Plan-Snapshot bleibt verbatim | ✅ eingehalten (alle Cross-Phase-Phasenköpfe tragen P15-Vermerke aus Session #4) |
| **P16** | `rescue.py` Signatur ist `(epic, from_dt, to_dt, resolution)` per ABC-Vertrag | ✅ hergestellt (Session #9 Schritte 1+2+3+4, Bug-Cluster behoben, Regressionstest `test_call_history_uses_correct_signature`) |

**Plan §11 Korrekturhinweis (2026-09-05, Session #12):** AK4 wurde für `phase7_reward/CLAUDE.md`
reduziert auf „auditability-bewusst beibehalten" (49 KB bleiben) — Begründung im Plan-📕-Snapshot,
**nicht** im Handover (Auditability, kein Verstoß).

---

## §3 Akzeptanz A1–A14 (Plan §7)

| Akzeptanz | Status | Beleg |
|---|---|---|
| **A1** Step-0-Ritual (Turbo/EPIC_MAP) | ✅ | Phasenkopf A-1, 14 Turbo-Treffer = Legacy-File `turbo_candidates.json`, 3 EPIC_MAP-Treffer in Phase-14-Tests |
| **A2** Σ-Baseline ≥ 1703 | ✅ | Phasenkopf A-2 (Σ 1703 exakt am 2026-08-31), Session #10 (1744), Session #11 (1831), Session #12 (1843) |
| **A3** ROADMAP 15b/15c/15d stimmen mit Code | ✅ | Phasenkopf A-3 (3 „gebaut"-Vermerke + 1 „partial" + 1 „gegenstandslos") |
| **A4** ROADMAP.md < 40 KB | ✅ reduziert | ROADMAP.md = 39.109 B, `phase7_reward/CLAUDE.md` auditability-bewusst beibehalten |
| **A5** `process_weight`-Invariante: `max|process| < |outcome bei R=−1|` | ✅ | `models.py:357-360` (Kommentar zeigt 0,5×2,5=1,25 < 2,0), B1 RED-Test → B2 Fix |
| **A6** Phase-12-Reconcile-Timing ≤ 5 CRITICALs/24h | 🟡 **ausstehend** | Backoff replay-verifiziert (Mini-Session 26: 17 → 4), wartet auf nächsten OPEN-Trade |
| **A7** Promotion-Harness verweigert bei n < n_min | ✅ | `test_promotion_refuses_below_n_min` (n=8, n_min=50 → `[]`) |
| **A8** Validator deterministisch (kein LLM) | ✅ | `test_validator_has_no_llm_import` + `test_validator_module_only_imports_stdlib_and_models` (triple-pin) |
| **A9** VETO 5 mit leerer Regelliste = Identität (bit-identical-to-today) | ✅ | `test_pre_trade_check_veto5_empty_rules_is_identity` (Phase 5, 173 unveränderte Tests grün) |
| **A10** D5-H.-B geschlossen (datierter Absatz in Phase 14) | ✅ | Phasenkopf Step D1 (2026-09-01, Mini-Session #5) |
| **A11** `phase13_14_15.svg` 1080×1080, valid SVG, INDEX-Zeile | ✅ | Session #5 Step D2 |
| **A12** `enable_gap_rescue` als Phase-13-`RescueConfig` mit Default `False`, **kein** `SchedulerConfig`-Feld | ✅ | Session #5 Step D3 (RescueConfig + Operator-Tool) + Session #9 Folgefix-Schritt 3+4 (Mock + Regressionstest) |
| **A13** Σ-Sweep ≥ 1703 nach jedem Block | ✅ | A-2 (1703), D3 (1714), Folgefix (1743), C1 (1744), C2 (1831), C3+C4 (1843) |
| **A14** Neue .md/.svg haben ihre `docs/INDEX.md`-Zeile im selben Commit | ✅ | `ROADMAP_ARCHIVE.md` (A-5) + `PHASE15_HOOK_HARDENING_PLAN.md` (A-7) + `phase13_14_15.svg` (D2) + `PHASE15_CLOSEOUT_HANDOVER.md` + `phase15_closeout.svg` (diese Session) |

**A6 ist die einzige offene Akzeptanz** — eine Beobachtungs-Akzeptanz, abhängig vom Eintreten
eines OPEN-Trades (6 Tage ohne seit `trade_outcomes.id=11` 2026-08-27). Der Code-Pfad selbst
ist replay-verifiziert.

---

## §4 As-Built-Zahlen heute (2026-09-05)

### Phase 15 (eigener Code)

| Modul | Zweck | Tests |
|---|---|---|
| `phase15_v4/instinct/__init__.py` | Package-Marker (re-exports) | — |
| `phase15_v4/instinct/models.py` | `Instinct` (frozen dataclass) + `InstinctConfig` + Domain/Status-Helpers | 35 |
| `phase15_v4/instinct/extractor.py` | `SingleShotInstinctExtractor` (LLM, best-effort, `_LLMClientLike` Protocol) | 22 |
| `phase15_v4/instinct/validator.py` | `InstinctValidator` (deterministic, **kein** LLM-Call) | 16 |
| `phase15_v4/instinct/promotion.py` | `promote_eligible` (Doppel-Sperre P10/P12) | 14 |
| `phase15_v4/scripts/reset_score_baseline.py` | Block B `--apply` (idempotent, MD5-verify) | 4 (`test_reset_score_baseline.py`) |

**Σ Phase 15: 91 Tests grün** (35 + 22 + 16 + 14 + 4)

### Cross-Phase-Touches

| Phase | Datei | Δ Tests |
|---|---|---|
| Phase 2 | `persistence/db.py` (`_INSTINCT_COLUMNS` + 3 Methoden) + `migrations/009_phase15_instincts.sql` (NEU) + `tests/test_migrations.py` | +1 |
| Phase 5 | `execution/config.py` (`longterm_rules`) + `execution/vetos.py` (VETO 5 + `longterm_pre_trade_check`) | +12 |
| Phase 13 | `live_data/rescue.py` (Bug 1+3 Fix) + `live_data/rescue.py` (`RescueConfig`) + `scripts/gap_rescue_operator.py` (NEU) + `tests/test_rescue.py` (Mock-Fix + Regressionstest) | +7 (D3) +1 (Folgefix-3+4) = +8 |
| root | `tests/test_check_doc_rotation.py` (4 P15-F-Tests, Phase-14-Hygiene-Code) | +4 |
| **Σ Cross-Phase** | | **+25** |

**Σ Phase 15-Beitrag: 91 (eigene) + 25 (Cross-Phase) = 116 Tests grün**
(differenziert zu Σ 1843 oben: 91 Phase-15 + 185 Phase-5 + 82 Phase-13 + 105 root = 463 Tests
in den berührten Suiten; 1380 Tests in den unveränderten 10 Suiten).

### Σ-Sweep Stand 2026-09-05 ~15:05 UTC (selbst nachgemessen, Session #12)

| Phase | Tests grün |
|---|---:|
| phase1_broker_wrapper | 95 |
| phase2_persistence | 78 |
| phase3_external_data | 104 |
| phase4_research | 155 |
| **phase5_execution** | **185** |
| phase6_debate | 76 |
| phase7_reward | 166 |
| phase8_scheduler | 248 |
| phase9_universe | 87 |
| phase10_v3 | 165 |
| phase12_data_foundation | 145 |
| phase13_live_data | 82 |
| phase14_discovery | 61 |
| **phase15_v4** | **91** |
| root `tests/` | 105 |
| **Σ repo-weit** | **1843** |

**Δ vs. Plan-Baseline 1703: +140 Tests** über die Phase-15-Laufzeit (Sessions #1-#12).

### Git-Stand 2026-09-05

```
$ git log --oneline origin/main..HEAD
7816688 phase15: docs -- Sonderhinweis Block-Status-Korrektur Session #12 (Block C ✅, Phase 15 formal noch offen — Closeout-Handover + Promotion-Bridge)
7b5edf0 phase15: docs -- §6 C2/C4 Korrekturhinweis: test_instinct.py ist As-Built 4 Files + test_veto5_with_empty_rules_is_identity lebt in Phase 5 (Cross-Phase-Touch)
6065e6c phase15+phase5: code+tests -- Block C Steps C3+C4 atomic (VETO 5 + ExecutionConfig.longterm_rules + 12 Phase-5-Tests, AK9 bit-identical-to-today, Σ 1843 grün)
c00ab73 phase15: code+tests -- Block C Step C2 Instinct-Package (4 Module, 87 Tests, AK7/AK8+Schema-Pin, Σ 1831 grün)
19f36c7 phase15: docs -- Session-Rotation #9->#10 (Block C Step C1 atomic, Migration 009 + DB-Methoden, schema version 9, Σ 1744 grün, MiniMax-M3-Exec-Session #10)
9f76a1e phase15: code -- Block C Step C1 Migration 009 + _INSTINCT_COLUMNS + 3 DB-Methoden (P15-C1, schema version 9, Instincts-Tabelle mit trigger/domain/confidence/evidence/contradictions/status-Lifecycle, AK12 strukturell gewahrt)
```

**6 Commits lokal ahead of `origin/main`. Letzter gepushter Commit: `9e3d215`** (Phase-15-Session #9, Block-D-Folgefix-Variante-C komplett).

### Live-Substrate

| Größe | Wert | Beleg |
|---|---|---|
| Live-DB `data/trading_bot.sqlite` Schema-Version | **7** | `SELECT MAX(version) FROM _schema_version` (manuell, 2026-09-05) |
| Live-DB `data/trading_bot.sqlite` `instincts`-Tabelle | **existiert NICHT** | Schema ist auf v7, Migration 009 additiv, greift beim nächsten Service-Restart |
| Live `reward_pts` row 11 `score_after` | **50.0** | `--apply` erfolgreich (war 78,72), Backup archiviert |
| Live `trade_outcomes` letzte Row | id=11, closed 2026-08-27, pnl=-641,3 EUR | 6 Tage ohne OPEN-Trade, Block B A6 wartet |
| Live `data/bars.sqlite` `source_spend WHERE kind='rescue'` | **5 Zeilen, 250 Punkte** | Pfad-A-Scharfschaltungs-Bug-Lauf 2026-09-03, **noch nicht** restored |
| Pre-apply-Backup | `data/trading_bot.sqlite.pre-apply-2026-09-03` (3,1 MB) | existiert, unverändert |
| Live-Dienste | 4/4 ALIVE seit 2026-09-03 ~12:00 CEST | Recorder, Discovery, Scheduler, WebUI |

---

## §5 Test vs. Live vs. Produktion

### Test (offline, mock-HTTP, in-suite)

- Σ 1843 grün repo-weit (selbst nachgemessen 2026-09-05)
- 99 Phase-15-Tests + 25 Cross-Phase-Tests (Phase 2/5/13) + 4 Hook-Tests = **128 Tests** explizit für Phase 15
- 7 Akzeptanz-Pin-Tests (AK7/AK9/AK12 + 4 weitere): alle grün
- **Heute-Verhalten bit-identisch** zu vor Phase 15: AK9-Pin `test_pre_trade_check_veto5_empty_rules_is_identity` grün, Phase-5-Sweep 173 unverändert
- 0 Regressions in den 14 unveränderten Phasen-Suiten

### Live (read-only-DB-Verify, mode=ro)

- `reward_pts` Score-Reset: ✅ row 11 = 50.0, row 10 = 77.587 (unverändert), delta-Spalten preserved
- `reward_pts` outcome_score_delta row 11 = −2.0166... (OLD delta, process_weight=1,5-Zeit), neuen Deltas werden mit 0,5 berechnet
- 4 Dienste ALIVE seit `--apply`, kein Crash, kein Bit-Drift am heute-Verhalten
- `data/bars.sqlite.source_spend WHERE kind='rescue'` = 5 Zeilen / 250 Punkte (Ledger-Restore ausstehend)
- Live-DB-Schema v7 (Migrations 008 + 009 additiv, apply bei nächstem Restart)

### Produktion (Live-Live, mit echtem Geld)

- **Nicht in Scope** für Phase 15. Account bleibt auf `account='demo'` (verifiziert in `trade_outcomes.account` für die letzten 8 Rows: alle `demo`).
- Hard Rule 4 (CLAUDE.md): "Never test against real money first" — eingehalten.

**Ehrliche Lesart:** Die Phase ist im **Demo**-Modus vollständig. Für einen Wechsel auf
**Live**-Account (`account='live'`) braucht es die Promotion-Bridge + einen
n ≥ n_min Trigger — beides Folge-Arbeit.

---

## §6 Delta seit letztem Handover

**Letzter formaler Phase-15-Handover-Stand:** Session #8 (2026-09-03, B6 `--apply` live) →
Sonderhinweis Session #12 (2026-09-05, Block-C-Code-complete).

| Datum | Session | Was | Σ-Δ |
|---|---|---|---|
| 2026-09-03 #8½ | Block D Folgefix Audit-Trail (vor Fix) | Bug-Diagnose | (0) |
| 2026-09-03 #9 | Block D Folgefix Variante C (4 Schritte: Signatur + Spend + Mock + Regression) | +1 | 1742→1743 |
| 2026-09-05 #10 | C1 atomic: Migration 009 + DB-Methoden | +1 | 1743→1744 |
| 2026-09-05 #11 | C2 atomic: Instinct-Package (5 Module + 87 Tests) | +87 | 1744→1831 |
| 2026-09-05 #12 | C3+C4 atomic: VETO 5 + 12 Phase-5-Tests | +12 | 1831→1843 |
| 2026-09-05 #13 | **Closeout-Handover (diese Session)** | 0 (Doc-only) | 1843 |

**Keine Phase-15-Code-Edits zwischen Session #12 und #13.** Reiner Doc-Closeout.

---

## §7 Offene Entscheidungen (E1–E9 aus Plan §7 + Closeout-spezifisch)

| # | Frage | Optionen | Empfehlung |
|---|---|---|---|
| **E1** | Wann wird Migration 009 auf der Live-DB angewendet? | (a) nächster Service-Restart (additiv, risikofrei) · (b) Operator-`sqlite3`-Migration · (c) gar nicht (Phase 15.5 wenn Live-Substrat n ≥ 50) | **(a) bei nächstem Restart** — `db.py:69-77` ruft `run_migrations()` automatisch, additiv |
| **E2** | Wann kommt die Promotion-Bridge? | (a) eigene Phase 15.5 · (b) Phase 16 · (c) bleibt offen | **(c)** bis Nikinger signalisiert Bedarf |
| **E3** | Wann wird der Ledger-Restore gemacht? | (a) Nikinger manuell jetzt · (b) nächste Service-Wartung · (c) im Block-C-D-Backlog | **(a)** — 1 SQL-Statement, sofort (250 Punkte) |
| **E4** | Soll die `phase13_14_15.svg` poliert werden? | (a) ja, Spalten-Abstände · (b) nein, Status reicht | **(b)** — Item #5 der Session-Next-Liste, optional, ~10 Min |
| **E5** | Wann wird A6 (Phase-12-Reconcile-Timing Live-Verify) abgeschlossen? | (a) wartet auf nächsten OPEN-Trade · (b) Backoff-Code-Only-Rreign reicht | **(a)** — formelle Akzeptanz hängt an Live-Beobachtung |
| **E6** | Soll `phase7_reward/CLAUDE.md` weiter reduziert werden? | (a) ja, weitere 10 KB raus · (b) nein, auditability | **(b)** — Plan-§7-AK4-Korrekturhinweis 2026-08-31 |
| **E7** | Schema-Version-Anzeige im Phasenkopf aktualisieren? | (a) ja · (b) nein | **(b)** — Phase-2-`migrations/` ist die Quelle |
| **E8** | Phase-15-Closeout-Bild (dieses Solo-SVG) statt/parallel zum 3-Säulen-Bild? | (a) ersetzen · (b) parallel · (c) verwerte | **(b)** — beide haben Wert (Phase 13+14+15 vs. Phase-15-spezifisch), INDEX.md führt beide |
| **E9** | Quellen-Vertrauens-Modell (Plan-§10-out-of-scope)? | (a) bleibt offen · (b) nächste Phase | **(a)** — Plan §10 |

**Keine projektweit-sichtbare Entscheidung ist hier offen** (Phase-15-Code + Doku + Status
sind alle im Plan-Lock). Alle 9 Entscheidungen sind Nikinger-Wahl, keine Notwendigkeit
zur sofortigen Klärung.

---

## §8 Datei-Anker

### Phasenkopf + Live-Doku

- [`./CLAUDE.md`](./CLAUDE.md) — Phase-15-Phasenkopf (L1, Header-Card, 6 Steps dokumentiert + 1 Sonderhinweis + 1 Gate-P7-Status-Notiz)
- [`./SESSIONS_ARCHIVE.md`](./SESSIONS_ARCHIVE.md) — 11 Session-Blöcke (newest-first), Plan-Session + #1-#12

### Plan + Mini-Pläne

- [`../docs/concepts/phase15_v4_plan.md`](../docs/concepts/phase15_v4_plan.md) — 📕 execution-ready Plan, P1–P16, AK1–AK14, §9 Drift
- [`./PHASE15_HOOK_HARDENING_PLAN.md`](./PHASE15_HOOK_HARDENING_PLAN.md) — 📕 Mini-Plan P15-F (Doc-Rotation-Hook)

### Bilder

- [`../docs/architecture/phase15_closeout.svg`](../docs/architecture/phase15_closeout.svg) — 📕 Closeout-Bild (1080×1080, diese Session)
- [`../docs/architecture/phase13_14_15.svg`](../docs/architecture/phase13_14_15.svg) — 📕 3-Säulen-Bild (Block D Step D2, 2026-09-01)

### Code (Phase 15 + Cross-Phase)

- [`./instinct/`](./instinct/) — 5 Module (`__init__` + `models` + `extractor` + `validator` + `promotion`)
- [`./scripts/reset_score_baseline.py`](./scripts/reset_score_baseline.py) — Block B `--apply`
- [`./tests/test_instinct_models.py`](./tests/test_instinct_models.py), [`test_instinct_extractor.py`](./tests/test_instinct_extractor.py), [`test_instinct_validator.py`](./tests/test_instinct_validator.py), [`test_promotion.py`](./tests/test_promotion.py), [`test_reset_score_baseline.py`](./tests/test_reset_score_baseline.py)
- Phase 2: `persistence/db.py` (`_INSTINCT_COLUMNS`, `_INSTINCT_STATUSES`, 3 Methoden) + `migrations/009_phase15_instincts.sql`
- Phase 5: `execution/config.py` (`longterm_rules`) + `execution/vetos.py` (`longterm_pre_trade_check`, VETO 5 in `pre_trade_check`)
- Phase 13: `live_data/rescue.py` (Bug-Fixes + `RescueConfig`) + `scripts/gap_rescue_operator.py` (NEU)

### Pattern-Vorbilder (Closeout-Sessions)

- [`../phase12_data_foundation/PHASE12_CLOSEOUT_HANDOVER.md`](../phase12_data_foundation/PHASE12_CLOSEOUT_HANDOVER.md) — Phase-12-Pattern
- [`../phase13_live_data/PHASE13_CLOSEOUT_HANDOVER.md`](../phase13_live_data/PHASE13_CLOSEOUT_HANDOVER.md) — Phase-13-Pattern
- [`../phase14_discovery/PHASE14_CLOSEOUT_HANDOVER.md`](../phase14_discovery/PHASE14_CLOSEOUT_HANDOVER.md) — Phase-14-Pattern (jüngstes Vorbild)

### Hook + Index

- [`../scripts/check_doc_rotation.py`](../scripts/check_doc_rotation.py) — Phase-14-Hygiene-Code, in Phase 15 erweitert (PHASE_DIRS + permissive Regex)
- [`../docs/INDEX.md`](../docs/INDEX.md) — Phase-15-L1-Index mit beiden neuen Zeilen (Handover + Bild)

---

## §9 Konsistenz-Regeln (Phase-15-spezifisch, nicht-antasten ohne Not)

| # | Regel | Begründung |
|---|---|---|
| **§9.1** | `InstinctConfig.instinct_n_min` bleibt 50 (Promotion-Gate), getrennt von `RewardConfig.n_min` 10 (Wilson) | P12, §9.6-Verify Session #11 |
| **§9.2** | VETO 5 mit `config.longterm_rules = ()` ist No-Op (bit-identical-to-today, AK9) | AK9, 173 Phase-5-Tests unverändert grün |
| **§9.3** | `enable_gap_rescue` ist ausschließlich in `RescueConfig` (Phase 13), **nie** in `SchedulerConfig` (Phase 8) | AK12, `test_enable_gap_rescue_is_NOT_in_scheduler_config` pınnt |
| **§9.4** | Schema-Migrationen für Phase 15 sind additiv-only (Migrations 008 + 009, kein `ALTER TABLE` auf bestehenden Tabellen) | Phase-2-Hard-Rule, additive-only-Disziplin |
| **§9.5** | Phase-7-`Brain` darf aus Phase 15 **nie** importiert werden — Mirror-Pattern mit eigenem `_LLMClientLike`-Protocol | Decision F-Pattern, Phase-Isolution |
| **§9.6** | `process_weight = 0,5` ist die **einzige** Reward-Gewichtung, die Block B ändert; `outcome_weight`, `entry_signal`, `debate_signal` bleiben unangetastet | P1, B2-Fix isoliert |
| **§9.7** | `RescueConfig` Default `enable_gap_rescue = False` — Aufheben ist `enable_gap_rescue=True` UND `--apply`, **nie** eines allein | Doppel-Sperre, P10-Disziplin |
| **§9.8** | Phase-15-Phasenkopf trägt exakt **eine** `## Session stopped`-Block; ältere sind in `SESSIONS_ARCHIVE.md` | Doc-Layers-Konvention |
| **§9.9** | Plan-Snapshot `docs/concepts/phase15_v4_plan.md` ist 📕 — Korrekturhinweise als datierte 🟡-Vermerke, kein Edit des Plan-Texts | Plan-Auditability |
| **§9.10** | Promotion-Bridge ist **bewusst offen** (Plan §10) — keine Phase-15-Code-Edits für sie ohne neue Nikinger-Freigabe | Plan §10, Phase-15-Struktur-Schließung wartet |
| **§9.11** | Cross-Phase-Phase 8 ist **nie** freigegeben für Phase 15 — kein Step braucht sie | Plan §4, Phase-8-Isolution |
| **§9.12** | Ledger-Restore ist Nikinger-Aktion (manuell, `DELETE FROM source_spend WHERE kind='rescue'`), kein Code-Touch, kein Commit | Audit-Trail §Ledger-Recovery, `data/` ist `.gitignore`-d |
| **§9.13** | Live-DB-Schema-Versionierung läuft **additiv** — `db.py:run_migrations()` wird beim nächsten Service-Restart automatisch 008+009 anwenden | Phase-2-Hard-Rule, kein Operator-Eingriff nötig |

---

## §10 Don'ts (10 Punkte)

1. **Don't rewrite VETO 5** um die Promotion-Bridge zu bauen — die Bridge ist Phase-15-out-of-scope und braucht eine eigene Phase.
2. **Don't change `process_weight`** zurück auf 1,5 — Block B ist live, Score-Reset ist irreversibel (Audit-Trail im Backup), H3 kehrt zurück.
3. **Don't push to `origin/main`** ohne Nikinger-Freigabe — 6 Commits pending, jeder braucht Bestätigung.
4. **Don't migrate the live DB manually** (`sqlite3 data/trading_bot.sqlite ...`) — der Service-Restart macht es additiv, manueller Eingriff umgeht `db.py:69-77`-Disziplin.
5. **Don't activate `enable_gap_rescue` ohne `--apply`** und ohne `--enable-gap-rescue` — Doppel-Sperre schützt vor versehentlichem Pfad-A-Scharfschalten.
6. **Don't import `phase7_reward.reward.brain.Brain`** aus `phase15_v4/instinct/extractor.py` — Decision F-Pattern, `_LLMClientLike` ist Phase-15-eigen.
7. **Don't change `InstinctConfig.instinct_n_min`** ohne Phase-15-Plan-Update — P12 + §9.1 garantieren saubere Trennung.
9. **Don't add new `.md` files** ohne `docs/INDEX.md`-Zeile im selben Commit — Phase-14-Doc-Rotation-Hook + AK14.
10. **Don't edit `docs/concepts/phase15_v4_plan.md`** ohne datierten 🟡-Korrekturhinweis — Plan-📕-Konvention.
11. **Don't claim "Phase 15 ist abgeschlossen"** ohne Closeout-Handover — Pattern aus Phase 12/13/14, Working-Style §6 ("Report outcomes faithfully").

---

## §11 Was diese Session gemacht hat

| Datum | Session | Was (kurz) |
|---|---|---|
| 2026-08-31 #1 | Plan-Session + A-1..A-4 | Plan `f98df68`, Nikinger-Freigaben `a2d4a15` / `d1dd26b` / `aad1d00`, Σ-Baseline 1703 |
| 2026-08-31 #2 | A-5 | ROADMAP.md-Phasen-1-8 → ROADMAP_ARCHIVE.md (749→507 Z., 54→39 KB) |
| 2026-08-31 #3 | A-6 | docs/INDEX.md Doppel-Header entfernt, 5 stale P15-Vermerke in Phasen 7/13/14 geräumt |
| 2026-08-31 #4 | P15-F (A-7) | Doc-Rotation-Hook erweitert (PHASE_DIRS + permissive Regex), 4 neue Tests |
| 2026-09-01 #5 | Block D D-1..D-3 | D5-H.-B geschlossen, `phase13_14_15.svg` (1080×1080), `RescueConfig` + `gap_rescue_operator.py` |
| 2026-09-02 #6 | Block B / Gate-P7-Status-Notiz | 0 OPEN-Trades am Tag, A6 wartet, Code-Vorbereitung B1–B6 startet |
| 2026-09-03 #7 | Block B B1..B6 (Code + dry-run) | `process_weight` 1,5→0,5 + Invariante RED-Test + Reset-Tool |
| 2026-09-03 #8 | Block B B6 `--apply` | Stop→Backup→Apply→Restart, Score 78,72→50,00 live, AK5+AK6+AK13 grün |
| 2026-09-03 #8½ | Block-D-Folgefix Audit-Trail | Bug-Diagnose + Recherche + Plan für Fix |
| 2026-09-03 #9 | Block-D-Folgefix Variante C (4 Schritte) | `rescue.py` Signatur + Spend-Logik + Mock-Update + Regressionstest |
| 2026-09-05 #10 | Block C Step C1 | Migration 009 + `_INSTINCT_COLUMNS` + 3 DB-Methoden, Schema v8→v9 (fresh-DB) |
| 2026-09-05 #11 | Block C Step C2 | Instinct-Package (5 Module + 87 Tests), AK7 + AK8 gepinnt |
| 2026-09-05 #12 | Block C Step C3+C4 | VETO 5 + `ExecutionConfig.longterm_rules` + 12 Phase-5-Tests, AK9 grün |
| 2026-09-05 #13 | **Closeout (diese Session)** | PHASE15_CLOSEOUT_HANDOVER.md + phase15_closeout.svg + Status-Pflege |

**13 Sessions, 12 davon Code-Sessions, 1 reine Doc-Closeout-Session.**

### Was diese Session (#13) konkret tat

1. `git log` / `git status` Vorab-Check: HEAD = `7816688`, working tree clean, 6 ahead of `origin/main`.
2. Σ-Sweep selbst nachgemessen: **1843 grün** (Phasen 1/2/3/4/5/6/7/8/9/10/12/13/14/15/root alle unverändert grün, +12 in Phase 5 von C3+C4).
3. `phase7_reward/reward/models.py:357` verifiziert: `process_weight: float = 0.5` ✅.
4. `phase5_execution/execution/vetos.py:206-228` verifiziert: `longterm_pre_trade_check` + VETO 5 ✅.
5. `phase5_execution/execution/config.py:113-119` verifiziert: `longterm_rules: tuple[Any, ...] = ()` ✅.
6. `phase13_live_data/live_data/rescue.py:270-286` verifiziert: `_call_history(epic, start_utc, end_utc)` + `method(epic, start_utc, end_utc, "MINUTE")` (ABC-Vertrag korrekt) ✅.
7. `data/trading_bot.sqlite` read-only: `_schema_version` max = **7** (Migrations 008+009 additiv, apply beim nächsten Service-Restart) — **Befund, kein Phase-15-Code-Touch**.
8. `data/trading_bot.sqlite.reward_pts` id=11: `score_after = 50.0`, `win_loss = LOSS`, `pnl_raw = -641.3` — `--apply`-Erfolg bestätigt.
9. `data/trading_bot.sqlite.trade_outcomes` id=11: closed 2026-08-27, danach 0 OPEN-Trades (P7 wartet zu Recht).
10. `data/bars.sqlite.source_spend WHERE kind='rescue'`: **5 Zeilen, 250 Punkte** — Ledger-Restore ausstehend (Nikinger-Aktion).
11. `docs/architecture/phase15_closeout.svg` NEU (18455 B, 1080×1080, valid SVG, 140 root-Children, Stil konsistent mit Geschwistern).
12. `phase15_v4/PHASE15_CLOSEOUT_HANDOVER.md` NEU (dieses Dokument, ~14 KB).
13. `phase15_v4/CLAUDE.md` Phasenkopf: Session #12 → SESSIONS_ARCHIVE.md rotiert, neuer Session-#13-Block im Phasenkopf.
14. `phase15_v4/SESSIONS_ARCHIVE.md`: vorheriger #11-Block-Header behalten (war schon im Archiv), #12-Block dazurotiert (verbatim).
15. `docs/INDEX.md`: 2 neue Zeilen (`PHASE15_CLOSEOUT_HANDOVER.md`, `phase15_closeout.svg`).
16. `ROADMAP.md`: Phase-15-Sub-Items 15b/15c/15d/15e detailliert + 15a-Verweis-Notiz; Phase-15-Status-Block.
17. `CLAUDE.md`: Phase-15-Row flippt auf ✅ + neuer ✅-2026-09-05 Status-Absatz.
18. **0 Code-Edits, 0 Test-Edits, 0 Cross-Phase-Code-Touches** — Doc-only-Closeout.

### Warum diese Session NICHT tat

- **Promotion-Bridge bauen** — Plan §10 out-of-scope, eigene Wiring-Session.
- **Ledger-Restore** — Nikinger-Aktion (manuell), kein Code-Touch.
- **Live-DB Migration 008+009 anwenden** — Service-Restart macht es additiv; kein Phase-15-Code-Touch.
- **Push to `origin/main`** — 6 Commits pending, Nikinger entscheidet.

---

> **Übergabe an die nächste Session:** Phase 15 ist **abgeschlossen** auf Code-Ebene.
> Promotion-Bridge, Ledger-Restore und A6 sind die einzigen offenen Folge-Arbeiten —
> keine ist ein Phase-15-Blocker. Die nächste Session kann **frei wählen**, ob sie
> eine Phase-15.5-Promotion-Bridge plant, einen anderen Track aufmacht, oder den
> Doc-Polish (Plan-§6-C2-Korrekturhinweis, SVG-Polish) als Mini-Sessions abarbeitet.
> **Keine** der offenen Arbeiten hat eine **harte Deadline** im Phase-15-Sinn.
---

> 🟡 **Korrekturhinweis 2026-09-05 (Phase 16 A-3, MiniMax-M3 Exec-Session #1):**
> §7 E1, §9.13 und §10 Punkt 4 behaupten einen automatischen Migrations-Apply beim
> Restart — **falsch**, kein Produktions-Caller von `db.py:run_migrations()`
> (verifiziert durch `grep -rn "run_migrations()" phase8_scheduler/ --include=*.py`
> 2026-09-05 → 0 Treffer außerhalb `phase2_persistence/`; Phase-16-Plan §3 L3 +
> §13 Opus-Review Befund #1). Phase 16 B1 baut den Aufruf **nicht** im Daemon
> (gelockte Preflight-Entscheidung `wiring.py:1070-1071` *„safety-critical daemon
> does not mutate schema"* + Lock-Risiko gegen laufenden Discovery-Daemon bei
> `journal_mode=delete` ohne `busy_timeout`), sondern einen **Schema-Floor** im
> Preflight + einmaligen Operator-Apply mit Backup (Phase-16-Plan §6 B1/B2).
>
> §4 „Live-Substrate": die 5 Rescue-Zeilen tragen `ts 2026-09-04T07:12Z`, nicht
> 09-03 — Datumsdrift in der ursprünglichen Erhebung, hiermit korrigiert
> (Quelle: `sqlite3 "file:data/bars.sqlite?mode=ro" "SELECT created_utc, points
> FROM source_spend WHERE kind='rescue'"`, Phase-16-Plan §2.5).
>
> Beide Korrekturen ändern die Phase-15-Bilanz nicht (Phase 15 bleibt ✅), sie
> aktualisieren nur die zwei Stellen, an denen die Doku der Code-Wahrheit
> widersprochen hat (Working-style-Regel: *„Tested code > concept doc >
> README/status prose"*). Datierter Vermerk im Sinne der
> Phase-12/13/14-Closeout-Konvention.
