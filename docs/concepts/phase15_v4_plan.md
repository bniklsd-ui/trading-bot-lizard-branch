---
status: snapshot
purpose: Execution-ready Plan für Phase 15 (V4 — Reward-Kalibrierung + Instinct-ECC + Quellen-Vertrauens-Lock), geschrieben 2026-08-31 in der Plan-Session gegen den laufenden Code; direkt an Sonnet 5 übergebbar
read-when: vor jedem Phase-15-Schritt; danach nur noch als Snapshot beim Auditieren
detail: L3
up: ../../CLAUDE.md
down:
  - ../../phase15_v4/CLAUDE.md                                   # Phasenkopf — trägt den Plan-Session-Session-stopped-Block; Step A-0 liest ihn
  - ../../phase13_live_data/PHASE13_BEWEISWOCHE_FINDINGS_2026-08-31.md   # §8.2 P15-V4-Kandidaten
  - ../../phase14_discovery/PHASE14_CLOSEOUT_HANDOVER.md         # §7 D5-H.-B / D5-H.-C, §9 Konsistenz-Regeln
  - ../../phase10_v3/PHASE11_DEFERRAL_HANDOVER.md                # H3 ist offen; Block B ist H3
  - ./phase7_reward_concept.md                                   # §7b Instinct-Schema (vorgegeben, nicht neu erfinden)
updated: 2026-08-31
---

# Phase 15 (V4) — Execution-ready Plan (2026-08-31)

> **Adressat:** die ausführende Session (Sonnet 5). Dieser Plan ist so geschrieben, dass
> nichts neu hergeleitet werden muss. Jede Zahl in §2/§3 ist in der Plan-Session selbst
> gegen Code oder Live-DB gemessen, mit Datum und Zeilennummer. Was **nicht** geprüft
> werden konnte, steht vollständig in **§9** — was dort nicht steht, gilt als geprüft.

---

## §0 BLUF

Phase 15 ist **nicht** die fünf ROADMAP-Häkchen. Drei davon sind gegen den Code falsch:
**15b ist gebaut**, **15c ist zu ~80 % gebaut**, **15d bewacht ein Feature, das es nicht gibt.**

Was stattdessen zu tun ist, in einem Satz: **der Lern-Score des Bots belohnt Verluste.**
Live gemessen — 8 geschlossene Trades, **−1 972,87 EUR** realisiert, Score **von 50 auf
78,72 gestiegen**. Der Prozess-Anteil ist mit `process_weight = 1.5` **stärker** als der
Outcome-Anteil und damit ein konstanter positiver Offset. Der Code weiß das seit
2026-07-31 (`scorer.py:45-49`, dort als „Phase-11 H3, nicht hier adressiert" vermerkt);
diese Plan-Session hat es zum ersten Mal **am Live-Substrat gemessen** und quantifiziert.

Drei Blöcke, in dieser Reihenfolge:

| Block | Inhalt | Gate |
|---|---|---|
| **A** | Haushalt: Step-0-Ritual, Σ-Baseline, ROADMAP-Wahrheit (15b/15c/15d), Doc-Rotation | keins |
| **B** | Reward-Kalibrierung (= Phase-11 **H3**) + Score-Reset auf 50 | **Gate P7: „Phase-12-Reconcile-Timing Live-Verify" muss abgeschlossen sein** |
| **C** | Instinct-ECC: Extraktion + Validierung, Promotion hinter Flag | nach B |
| **D** | Erbstücke: Quellen-Vertrauens-Lock, `phase13_14_15.svg`, Pfad A (Operator-S4) | nach A |

**Nicht in Phase 15:** 15a Council-Integration (Nikinger-Entscheidung 2026-08-31,
Runde 1), 15d als Code (moot-by-absence), Auto-Gap-Fill-Scheduler + Dukascopy-echt
(Nikinger-Entscheidung, Runde 2).

---

## §1 Gelockte Entscheidungen (P1–P16) — „don't re-litigate"

Jede Zeile trägt ihre Begründung. Wer eine davon gutgemeint aufmacht, macht Arbeit rückgängig,
die auf einer Messung beruht, nicht auf einer Meinung.

| # | Was gelockt ist | Warum |
|---|---|---|
| **P1** | **Der Prozess-Anteil muss schwächer sein als der Outcome-Anteil.** Invariante: für `r_multiple ≤ −1.0` ist `total_delta < 0` — für **jede** Kombination der drei Prozess-Signale. | Das ist die eigentliche Design-Absicht („weak process signal, not a multiplier", `scorer.py:44`), die die Zahlen heute verletzen: max\|process\| = 1.5 × 2.5 = **3.75** > \|outcome bei R=−1\| = **2.0**. Ein Verlust hebt den Score. Live belegt: Trades 10 + 11, je +1,10. |
| **P2** | Umgesetzt wird P1 über **`process_weight` allein** (1.5 → **0.5**). Keine Struktur-Änderung an `scorer.py`s drei Termen. | Kleinster Diff, der die Invariante erfüllt: max\|process\| = 0.5 × 2.5 = 1.25; bei R=−1 → −2.0 + 1.25 = **−0.75 < 0** ✓. Die Semantik-Frage „ist ein Stop-Out ein clean exit?" (H3) bleibt bewusst **offen** — sie ist nicht nötig, um die Invariante herzustellen, und eine Semantik-Änderung wäre eine Design-Entscheidung ohne Datenbasis (n=8). |
| **P3** | `tight_spread_pct` bleibt **unverändert bei 0.05** — mit einem dokumentierten `ponytail:`-Kalibrierungs-Kommentar und der gemessenen Verteilung. | Der Schwellwert liegt ~11× über dem realen Spread (§3 B2), der Bonus feuert also immer. Aber: es gibt **nur 13 Spread-Beobachtungen im ganzen Repo** (8 Trades + 5 Snapshots). Einen Schwellwert auf n=13 zu fitten ist Rauschen-Fitting. P2 löst den Schaden bereits vollständig; die Neukalibrierung wartet auf Daten. **Der Knopf bleibt sichtbar stehen.** |
| **P4** | `veto_trigger_count` / `gate_fail_count` werden **nicht befüllt**, sondern als gegenstandslos dokumentiert (wie 15d). | Ein Trade, der eine `reward_pts`-Zeile bekommt, hat per Definition alle 5 Gates und alle 4 VETOs passiert. Belegt: **0 von 1902** `abstain_records` haben `stage='veto'` oder `'gate'` (§2.4). Code, der garantiert zweimal Null schreibt, ist kein Code. |
| **P5** | Score-Reset auf 50,0 über **einen** `UPDATE` auf die **neueste** `reward_pts`-Zeile. Alle `outcome_score_delta`/`process_score_delta` der 8 Zeilen bleiben **unangetastet**. | Nikinger-Entscheidung 2026-08-31 (Runde 2). Die Deltas sind die eigentliche Messhistorie und bleiben; nur der Akkumulator wird re-basiert. `get_current_score()` liest genau diese eine Zelle (`db.py:280-284`). **Bekannte, bewusste Inkonsistenz:** Zeile 11 sagt danach `−2.017 + 3.15` aber `score_after = 50.0`. Das Script protokolliert das, der Phasenkopf trägt es. |
| **P6** | Der Reset ist ein **einmaliges Script**, keine Migration, kein Feature. | Einmalige Korrektur einer Historie. Eine Migration würde es auf jeder frischen DB wiederholen, wo es nichts zu korrigieren gibt. |
| **P7** | Block B und der Reset laufen **erst nach abgeschlossenem „Phase-12-Reconcile-Timing Live-Verify"** (in `phase7_reward/CLAUDE.md` „A6" genannt). | Nikinger-Entscheidung 2026-08-31 (Runde 1). Das „Phase-12-Reconcile-Timing Live-Verify" beobachtet 24 h `phase7_reward/reward/recorder.py`-Verhalten am laufenden Bot; `scorer.py` ist dessen direkte Abhängigkeit und der Reset schreibt in dieselbe DB. Ein Edit mitten im Fenster macht die Messung wertlos. |
| **P8** | Instinct-Schema = **wörtlich** Concept §7b: `trigger` / `domain` ∈ {entry,exit,sizing,timing} / `confidence` / `evidence_trade_ids[]` / `contradictions_trade_ids[]`. | `docs/concepts/phase7_reward_concept.md:573-575`. Das Schema ist seit 2026-06-16 spezifiziert. Neu erfinden = Drift ohne Gewinn. |
| **P9** | Der Instinct-Extraktor spiegelt **exakt** `phase7_reward/reward/brain.py`: `_LLMClientLike`-Protokoll, `ask_candidate(system, user, json_schema)`, best-effort, wirft **nie**. | Gleiche Familie, gleiche Datei-Nachbarschaft, gleicher Fehler-Vertrag. Ein zweiter LLM-Stack wäre Decision F aus Phase 7 rückgängig gemacht. |
| **P10** | **Promotion ist per Default AUS** und erreicht die VETO-Schicht nur über deterministischen Code. `longterm_pre_trade_check()` ist eine gewöhnliche Funktion in `vetos.py`, kein AI-Call. | ROADMAP 15e Leitplanke + CLAUDE.md Hard Rule 2 + Hard Rule 3. Die AI schlägt vor, der Code entscheidet. |
| **P11** | Der Hook-Punkt ist **`pre_trade_check()`** in `phase5_execution/execution/vetos.py:197`, als **VETO 5** nach `veto_position_conflict`. Nicht in `executor.py`, nicht pro Aufrufer. | Ein gemeinsamer Choke-Point statt vier Kopien, die auseinanderdriften. `pre_trade_check` ist bereits genau das für VETO 1–4; `executor.py:332` ruft es einmal auf. |
| **P12** | `n_min` für Instinct-Promotion = **50 geschlossene Trades**, als eigenes Feld `instinct_n_min` in `RewardConfig`, **nicht** das bestehende `n_min = 10`. | `n_min = 10` gehört der Wilson-Confidence (`models.py:347`) und hat eine andere Bedeutung; Wiederverwendung koppelt zwei unabhängige Schwellen. 50 ist ein bewusst gesetzter, dokumentierter Startwert („deutlich über" der Confidence-Schwelle, Concept §7b) — ein Kalibrierungs-Knopf, keine hergeleitete Zahl. **Heute: n = 8.** |
| **P13** | Akzeptanz für Block C ist, dass der Harness bei n=8 **korrekt nichts promotet** — nicht, dass ein Instinct promotet wird. | Nikinger-Entscheidung 2026-08-31 (Runde 2). Bei 8 Trades in zwei Monaten ist alles andere Substrat-Erfindung — genau das Muster, das Concept §7b als „epistemisch gefährlich" benennt. |
| **P14** | `instrument_source_availability` bleibt ein **Verfügbarkeits-Modell**, kein Aktualitäts-Modell. `last_verified_utc` behält die Semantik „Discovery-Ableitung". | Schließt D5-H.-B (P14-Closeout §7). Unter Pfad C heißt `status='ok'` „GapRescue-Pfad verfügbar", nicht „Live-Coverage" — das ist eine andere Kategorie und war nie eine Lüge. Belegt durch B3 der Phase-13-Beweiswoche. |
| **P15** | Pfad A (Operator-S4) wird **gebaut, aber nicht scharfgeschaltet**: Config-Flag + Operator-Script, Default AUS. Das Scharfschalten ist eine getrennte Nikinger-Aktion. | Hebt D19/L18 (IG-Default AUS) **nicht** auf — es macht das Aufheben erst *möglich*. Gleiche Disziplin wie `enable_shadow_schedule` / `enable_divergence_sampler` / `enable_paper_debate`. |
| **P16** | Kein neues Doku-File außer den in §6 genannten. Jede neue `.md` bekommt ihre `docs/INDEX.md`-Zeile **im selben Commit**. | CLAUDE.md Anti-Pattern-Liste + Doc-Rotation-Hook `--strict` (P14-F, seit Mini-Session 24 Default). |

---

## §2 Selbst gemessene Fakten (Plan-Session, 2026-08-31)

Alles hier ist in dieser Session gegen den Code oder die Live-DB (`mode=ro`) gemessen.
Keine Zahl aus einem Vorgänger-Handover übernommen.

### §2.1 Σ-Test-Baseline — **1703 grün**, selbst gemessen

Kommandoform verifiziert (Phase 7 als Probe gelaufen, 142 passed in 0.10s):

```bash
cd <phaseN> && ../phase1_broker_wrapper/.venv/bin/python -m pytest tests/ -q
```

| Phase | Tests | Phase | Tests |
|---|---|---|---|
| phase1_broker_wrapper | 95 | phase9_universe | 87 |
| phase2_persistence | 77 | phase10_v3 | 165 |
| phase3_external_data | 104 | phase12_data_foundation | 145 |
| phase4_research | 155 | phase13_live_data | 74 |
| phase5_execution | 173 | phase14_discovery | 61 |
| phase6_debate | 76 | root `tests/` | 101 |
| phase7_reward | **142** | | |
| phase8_scheduler | 248 | **Σ** | **1703** |

> ⚠ Die Memory-Notiz `reference_running_phase_tests.md` nennt Baselines von 2026-07-02
> (P1 52 · P2 75 · P4 135 · P5 154 · P6 70 · P7 133 · root 64). Die sind **stale**.
> Die Tabelle oben ist der Stand 2026-08-31. Phase 11 hat kein eigenes `tests/`-Verzeichnis
> (lebt in `phase10_v3/`), Phase 15 bekommt in Step C1 eins.

### §2.2 Laufender Betrieb (`ps aux`, 2026-08-31)

| PID | Prozess |
|---|---|
| 21184 | `python -m data_foundation.run` |
| 21197 | `python -m source_registry.run` |
| 21207 | `python -m scheduler.run` |
| 21248 | `uvicorn webui.api:app --host 127.0.0.1 --port 8000` |
| 21214, 21215 | `[python] <defunct>` — **zwei Zombies**, Elternprozess reapt nicht |

Die Zombies sind **nicht** Teil dieses Plans (kein beobachteter Schaden), aber sie stehen hier,
damit die Exec-Session sie nicht für eine Folge ihrer eigenen Arbeit hält.

### §2.3 Reward-Substrat, live (`data/trading_bot.sqlite`, `mode=ro`)

| trade | P&L EUR | `outcome_score_delta` | `process_score_delta` | `spread_at_entry_pct` | `debate_confidence` | `score_after` |
|---|---|---|---|---|---|---|
| 4 | −585,00 | −2,0000 | **+89,25** | 0,0078073 | 58 | 55,00 |
| 5 | −651,16 | −1,9467 | **+89,25** | 0,0077686 | 58 | 60,00 |
| 6 | −651,16 | −1,9467 | **+87,75** | 0,0047733 | 57 | 65,00 |
| 7 | −643,50 | −1,9500 | **+92,25** | 0,0048154 | 60 | 70,00 |
| 8 | +912,90 | +2,9833 | −1,50 | **1,0** ⚠ | NULL | 71,4833 |
| 9 | +939,75 | +2,9833 | +3,12 | 0,0045601 | 58 | 76,4833 |
| 10 | −653,40 | −2,0167 | +3,12 | 0,0045405 | 58 | 77,5867 |
| 11 | −641,30 | −2,0167 | +3,15 | 0,0045513 | 60 | 78,7200 |

**Σ P&L = −1 972,87 EUR. Σ Score = +28,72.** 6 Verluste, 2 Gewinne, alle `BUY`, alle DAX,
alle `provenance='autonomous'`, Zeitraum 2026-07-02 bis 2026-08-27.

### §2.4 Übriges Substrat

| Tabelle | Zeilen | Anmerkung |
|---|---|---|
| `trade_outcomes` | **8** | alle `status='CLOSED'` |
| `reward_pts` | 8 | `veto_trigger_count` / `gate_fail_count`: **0 von 8 non-NULL** |
| `trade_lessons` | 8 | |
| `abstain_records` | 1902 | `research_empty` 1852 · `debate` 50 · **`veto` 0 · `gate` 0** |
| `decision_context` | 1593 | trägt `veto_results_json` / `gate_results_json` pro Zyklus |
| `market_regime_snapshots` | 1596 | `spread_pct` non-NULL nur in **5** Zeilen (99,7 % leer) |
| `paper_trades` | 1013 | |
| `source_spend` (`data/bars.sqlite`) | 158 | `kind`: `research` 117 / 5025 Punkte · `sample` 37 / 111 · `probe` 4 / 20 · **`rescue` 0** |

### §2.5 Verifizierte Code-Ketten

**Score → Positionsgröße** (jede Stufe gelesen, keine Vermutung):

```
reward_pts.score_after (78,72)
  → Database.get_current_score()      phase2_persistence/persistence/db.py:278-284
  → Database.get_risk_level()         db.py:286-288   ("AGGRESSIV" wenn > _RISK_THRESHOLD = 50.0, db.py:49)
  → sizing.select_risk_pct(db, cfg)   phase5_execution/execution/sizing.py:71-84
  → config.risk_pct_aggressive = 3.0  vs risk_pct_conservative = 2.0   config.py:112-113
  → sizing.compute_size(...)
```

**Score → Research-Prompt:** `phase4_research/research/context_builder.py:272` — `bot_score = db.get_current_score()`.

**Toter Konsument:** `Database.get_risk_mode()` (`db.py`) hat **null** Aufrufer im ganzen Repo.
Nicht anfassen, nicht löschen — außerhalb des Scopes, hier nur vermerkt.

**VETO-Kaskade:** `pre_trade_check()` in `phase5_execution/execution/vetos.py:197-228` ruft
VETO 1–4 sequenziell, Short-Circuit beim ersten `ok=False`. Einziger Aufrufer:
`phase5_execution/execution/executor.py:332`.

**Migrations:** `001`–`008` belegt. **Nächste freie Nummer = `009`.**

### §2.6 Step-0-Ritual (Turbo-/Legacy-Grep) — **ausgeführt, No-Op (5. Mal)**

```
grep -rni "turbo" --include="*.py" --include="*.sql" --include="*.sh" .
```

Treffer sind ausnahmslos der **bewusst behaltene** Legacy-Dateiname `turbo_candidates.json`.
`phase2_persistence/persistence/state.py:27-30` sagt wörtlich: *„Legacy name; content =
DAX-CFD candidates, not turbos/options. Do NOT rename"*. Vorherige Ausführungen:
2026-06-27, 2026-07-10, 2026-08-18, 2026-08-22. **Phase 15 führt keine neue Turbo-Referenz ein.**
Step A-1 führt das Ritual erneut aus und protokolliert das Ergebnis — auch wenn es wieder No-Op ist.

---

## §3 Befunde (neu in dieser Plan-Session)

### B1 — Der Reward-Loop belohnt Verluste. Live belegt, im Code seit 2026-07-31 vorhergesagt.

`phase7_reward/reward/scorer.py:44-49` (verbatim):

```
  asks for. ⚠ The scale fix alone does **not** make the reward loop outcome-neutral
  on a losing streak: a ``CLOSED_BY_BROKER`` stop-out still earns the full
  ``clean_exit_bonus`` (it hit the planned SL), so the score still drifts upward
  (~+1.2 per consecutive loss) after this fix — whether a stop-out should count as a
  "clean exit" is an open design question, not addressed here (Phase-11 H3).
```

Vorhergesagt: **+1,2 pro Verlust.** Live gemessen an den Trades 10 und 11: **+1,10.**
Der Befund ist also **nicht neu** — er ist als Phase-11 **H3** offen (`PHASE11_DEFERRAL_HANDOVER.md`
§1, Zeile „H3 / H5 / H7 — ❌ offen"). Neu ist, dass er jetzt **am echten Konto quantifiziert** ist:
−1 972,87 EUR bei +28,72 Score.

Arithmetische Wurzel: `max|process| = process_weight × (1 + 1 + 0.5) = 1.5 × 2.5 = 3.75`,
`|outcome bei R = −1| = outcome_weight × 1.0 = 2.0`. **Der „schwache" Prozess-Anteil ist
um Faktor 1,875 stärker als der Outcome-Anteil.** Das ist P1/P2.

### B2 — Der Clean-Entry-Bonus ist eine Konstante, kein Signal.

`tight_spread_pct = 0.05` (`models.py:359`), Vergleich in `scorer.py:122-124`. Beobachtete
`spread_at_entry_pct`: 0,00454 – 0,00781 (7 Trades) + 0,0045–0,0248 (5 Snapshots).
Der Schwellwert liegt **~11× über** dem Median (0,00456). Der Bonus feuert in 7 von 8 Trades.
→ **P3: Knopf stehen lassen, Verteilung dokumentieren, nicht auf n=13 fitten.**

### B3 — Die 120×-Vergiftung sitzt noch in vier Live-Zeilen.

Trades 4–7 tragen `process_delta ≈ +89` = `1.5 × (1.0 + 1.0 + 57.5)` — der pre-B2-fix-Wert
`conf − 0.5` statt `conf/100 − 0.5`. Der Fix ist seit 2026-07-31 im Code; die Zeilen wurden
nie nachgezogen und `score_after` ist verkettet. **Nur `max_delta_per_trade = 5.0` hat den
Schaden von +87 auf +5 pro Trade gedeckelt.** → P5 (Reset auf 50).

Nachgerechnet ohne den Bug wäre der Score heute ≈ **63,35** statt 78,72. **Beide > 50 →
`AGGRESSIV` in beiden Fällen. Der Bug hat den Risiko-Modus nicht gekippt.** Das ist die
ehrliche Eingrenzung der Schwere: falscher Lern-Score und falscher Prompt-Input, **kein**
falscher Positions-Sizing-Modus.

### B4 — `GapRescue` (S4) hat nachweislich nie gelaufen und ist nicht verdrahtet.

- `phase13_live_data/live_data/rescue.py:98` definiert die Klasse; `rescue.py:183` bucht
  `self._budget.record_spend(points, "rescue")`.
- Der Ledger `data/bars.sqlite.source_spend` kennt `kind`-Werte `research`/`sample`/`probe` —
  **`rescue` kommt in 158 Zeilen nicht vor.**
- `grep -rn "GapRescue" --include="*.py" phase8_scheduler/` ist **leer** — keine Wiring-Stelle.
- **`enable_gap_rescue` ist kein Config-Feld.** Es existiert ausschließlich als Prosa im
  Docstring (`rescue.py:17`) und als Testname (`test_rescue.py:270`). `SchedulerConfig`
  (`phase8_scheduler/scheduler/config.py`) hat es nicht.
- Das im Docstring erwähnte „Operator-Script in einer späteren Session" existiert nicht.

→ Das ist **exakt der Umfang von Pfad A** (P15/Block D3): Config-Feld + Wiring + Operator-Script.

### B5 — `spread_at_entry_pct = 1.0` bei Trade 8 ist 222× die Geschwisterwerte.

Trade 8 ist zugleich der einzige mit `debate_confidence = NULL` und der einzige, dessen
`process_delta` (−1,50) auf `exit_signal = −clean_exit_bonus` (= `TIME_STOP`) schließen lässt.
**Nicht in dieser Session aufgeklärt** — steht in §9. Erster Verdächtiger: ein zweiter
Schreibpfad, der den Spread als Bruch statt als Prozent-vom-Ask liefert.

---

## §4 Cross-Phase-Freigabe (Nikinger, 2026-08-31)

Freigegeben für Phase 15: **Phase 2, Phase 4, Phase 5, Phase 6, Phase 7, Phase 13, Phase 14.**

D5 verlangt je Phase eine eigene Freigabe; die Phase-14-Liste gilt **nicht** automatisch weiter.
Diese Liste ist die Phase-15-Liste. Alles außerhalb (Phase 1, 3, 8, 9, 10, 12) braucht eine
neue Nikinger-Freigabe — **auch für einen Einzeiler.**

> ⚠ Phase 8 ist **nicht** freigegeben. Kein Step dieses Plans braucht sie — Step D3 ist
> bewusst als Operator-Tool in Phase 13 geschnitten, gerade damit kein `SchedulerConfig`-Feld
> nötig wird. Wer dort landet, hat D3 falsch gelesen.

---

## §5 Contracts — exakte Namen, die die Exec-Session verwendet

Keine Erfindungen. Wer einen Namen ändern will, ändert ihn in diesem Abschnitt zuerst.

### Block B

| Symbol | Datei | Art |
|---|---|---|
| `RewardConfig.process_weight` | `phase7_reward/reward/models.py:357` | Default 1.5 → **0.5** |
| `Scorer.score()` | `phase7_reward/reward/scorer.py:78` | Signatur **unverändert** |
| `reset_score_baseline.py` | `phase7_reward/scripts/reset_score_baseline.py` | **NEU**, einmaliges Operator-Script |

### Block C

| Symbol | Datei | Art |
|---|---|---|
| `009_phase15_instincts.sql` | `phase2_persistence/migrations/` | **NEU** |
| Tabelle `instincts` | dito | `id, trigger, domain, confidence, evidence_trade_ids_json, contradictions_trade_ids_json, status, created_utc, validated_utc, promoted_utc, archived_utc` |
| `Database.insert_instinct(...)` / `.list_instincts(status=None)` / `.update_instinct_status(...)` | `phase2_persistence/persistence/db.py` | **NEU**, Muster `insert_lesson` (`db.py:292`) |
| `_INSTINCT_COLUMNS` | `phase2_persistence/persistence/db.py` | **NEU**, Muster `_LESSON_COLUMNS` (`db.py:41`) |
| `Instinct` (frozen dataclass) | `phase15_v4/instinct/models.py` | **NEU**, Felder = Concept §7b |
| `InstinctConfig` | `phase15_v4/instinct/models.py` | **NEU**, trägt `instinct_n_min: int = 50`, `enable_instinct_promotion: bool = False` |
| `InstinctExtractor.extract(lessons, rewards)` | `phase15_v4/instinct/extractor.py` | **NEU**, spiegelt `Brain.reflect` (`brain.py:187`) — best-effort, wirft nie |
| `InstinctValidator.validate(instinct, trades)` | `phase15_v4/instinct/validator.py` | **NEU**, **rein deterministisch, kein LLM** |
| `promote_eligible(instincts, n_closed, cfg)` | `phase15_v4/instinct/promotion.py` | **NEU**, gibt `[]` zurück solange `n_closed < cfg.instinct_n_min` |
| `longterm_pre_trade_check(candidate, rules)` | `phase5_execution/execution/vetos.py` | **NEU**, VETO 5, gibt `VetoVerdict` |
| `ExecutionConfig.longterm_rules: tuple[Any, ...] = ()` | `phase5_execution/execution/config.py` | **NEU** — so kommt `rules` in `pre_trade_check`, siehe unten |

**Woher `rules` kommt — verifiziert 2026-08-31, keine Vermutung:** `pre_trade_check`s Signatur
ist `(broker, candidate, now, config)` (`vetos.py:197-199`) und `config` ist bereits dabei.
`rules` wird deshalb ein **Feld von `ExecutionConfig`**, nicht ein neuer Parameter. Das erfüllt
drei Bedingungen gleichzeitig:

- **Keine Signatur-Änderung** ⇒ der einzige Aufrufer `executor.py:332` bleibt unangetastet.
- **Kein Cross-Phase-Import.** `vetos.py` importiert heute nur `execution.*` + stdlib
  (`vetos.py:23-31`). `longterm_rules` ist als `tuple[Any, ...]` typisiert und trägt
  **plain deterministische Prädikate**, kein `phase15_v4`-Typ. `phase5_execution` importiert
  **nie** aus `phase15_v4` — die Regeln werden vom Wiring hineingegeben, nicht von Phase 5 geholt.
- **`ExecutionConfig` ist `frozen=True`** (`config.py:30`) ⇒ Default muss ein **Tupel** sein
  (`()`), keine Liste. Leeres Tupel ⇒ `ok=True` ⇒ bit-identisch zu heute.


### Block D

| Symbol | Datei | Art |
|---|---|---|
| `docs/architecture/phase13_14_15.svg` | — | **NEU** |
| `enable_gap_rescue` | siehe §6 Step D3 | **NEU**, Default `False` |
| `phase13_live_data/scripts/gap_rescue_operator.py` | — | **NEU**, Operator-Tool |

---

## §6 Schritt-Sequenz

> **Anker-Konvention:** zu jeder Edit-Stelle steht der **VERBATIM-String** plus die
> Zeilennummer **vom 2026-08-31**. Der String ist der Anker, die Zahl die Abkürzung.
> Frühere Steps verschieben spätere Zeilen — **immer auf den String matchen.**

### Block A — Haushalt (kein Gate)

#### A-0 — Phasenkopf lesen, Modul-Tabelle füllen

`phase15_v4/CLAUDE.md` **existiert bereits** (Plan-Session, Commit nach `f98df68`) und trägt
den `## Session stopped`-Block der Plan-Session. **Zuerst lesen** — er ist die Übergabe.

Zu tun:

```bash
mkdir -p phase15_v4/tests
```

Dann in `phase15_v4/CLAUDE.md`: die Modul-Tabelle mit den tatsächlich gebauten Modulen
füllen (Spalten wie `phase14_discovery/CLAUDE.md`: Modul · Zweck · Tests) und am
Session-Ende den eigenen `## Session stopped`-Block schreiben — den der Plan-Session
**verbatim** nach `phase15_v4/SESSIONS_ARCHIVE.md` rotieren (Rotationsregel, newest-first).

`phase15_v4/README.md` erst, wenn es eine öffentliche Oberfläche gibt — **nicht auf Vorrat**.

#### A-1 — Step-0-Ritual ausführen und protokollieren

```bash
grep -rni "turbo" --include="*.py" --include="*.sql" --include="*.sh" .
grep -rn "EPIC_MAP" --include="*.py" .
```

Ergebnis in `phase15_v4/CLAUDE.md` protokollieren — **auch wenn No-Op** (Erwartung: ist es;
siehe §2.6). Wenn ein Treffer auftaucht, der **nicht** `turbo_candidates.json` ist: stoppen
und melden, nicht selbst umbenennen.

#### A-2 — Regression-Baseline VOR dem ersten Fix

Sweep über alle 13 Phasen + root nach der Kommandoform aus §2.1. Ergebnis-Tabelle in
`phase15_v4/CLAUDE.md`. **Erwartung: Σ = 1703.** Weicht es ab, ist das ein Befund von
*vor* Phase 15 — dokumentieren, nicht stillschweigend als Phase-15-Effekt verbuchen.

#### A-3 — ROADMAP-Wahrheit herstellen (15b / 15c / 15d)

`ROADMAP.md`, drei Edits. Jeder bekommt einen datierten Vermerk „korrigiert gegen Code
2026-08-31 (Phase-15-Plan-Session §2/§3)".

**Anker 1** — `ROADMAP.md:692-694`, verbatim:
```
- [ ] Context-window monitoring during debate (~60–70 %)
- [ ] Compression of Bull/Bear/Judge state into summary
- [ ] New session continuation
```
→ Die ersten beiden auf `[x]` mit Beleg `phase6_debate/debate/debate.py:172` (Schwellwert
`compression_trigger_pct * max_cumulative_input_tokens`) und `debate.py:187-195`
(deterministischer Compression-Latch). Die dritte Zeile wird als **durch Compression ersetzt**
vermerkt — eine neue Session zu starten ist nicht nötig, wenn der Kontext im Lauf komprimiert wird.

**Anker 2** — `ROADMAP.md:697-698`, verbatim:
```
- [ ] `+ process_quality_score` (VETOs, confidence, debate quality, gate path)
- [ ] Anti-emotionality: separate process score from outcome score
```
→ Zweite Zeile auf `[x]` (strukturell getrennt seit Phase 7, `scorer.py:114-133`), mit dem
Zusatz, dass die **Kalibrierung** in Block B gefixt wird (P1/P2). Erste Zeile: „VETOs" und
„gate path" als **gegenstandslos** vermerken (P4, Beleg §2.4); „confidence" und
„debate quality" sind gebaut (`debate_signal`, `spread_at_entry_pct`).

**Anker 3** — `ROADMAP.md:701`, verbatim beginnend:
```
- [ ] Lock force trigger when daily PNL < 0 — das P2-Schema-Feld `force_trigger_locked` existiert
```
→ Auf **„gegenstandslos solange kein Force-Trigger existiert"** umschreiben. Beleg:
`grep -rn "force_trigger" --include="*.py" .` liefert genau einen Treffer,
`phase2_persistence/persistence/defaults.py:27`. CLAUDE.md Hard Rule 5 bleibt wörtlich stehen —
sie ist die Vorschrift für den Tag, an dem jemand einen Force-Trigger baut.

#### A-4 — root-`CLAUDE.md` Statuspflege

**Anker** — `CLAUDE.md:93`, verbatim beginnend:
```
> **✅ 2026-07-03 — Phase 8 ABGESCHLOSSEN + live-verifiziert.** Der weiterlaufende Live-Test lieferte
```
→ Der Block bleibt (Auditability), bekommt aber einen **vorangestellten** aktuellen
Status-Absatz: Phase 13 + 14 abgeschlossen 2026-08-31, Phase 15 eröffnet.

**Anker** — `CLAUDE.md:148`, verbatim beginnend:
```
| 15 — V4: Sophisticated/Optional (Council, Handover, Reward-Reform, Force-Trigger, Instinct-ECC;
```
→ Status von `Deferred, gegatet auf …` auf **🔄 in Arbeit seit 2026-08-31** mit Link auf diesen
Plan und auf `phase15_v4/CLAUDE.md`.

#### A-5 — Doc-Rotation der zwei Übergrößen

| Datei | Größe | Maßnahme |
|---|---|---|
| `ROADMAP.md` | **52 KB** | Phasen 1–8 (abgeschlossen) **verbatim** nach `ROADMAP_ARCHIVE.md`, im ROADMAP je eine Ein-Zeilen-Zusammenfassung + Link. INDEX-Zeile 27 anpassen (nennt heute noch „41KB"). |
| `phase7_reward/CLAUDE.md` | **52 KB** | Rotationsregel anwenden: **genau ein** `## Session stopped`-Block bleibt, alle älteren **verbatim** nach `phase7_reward/SESSIONS_ARCHIVE.md` (newest-first). |

> **Fehlgriff, der wie ein anderer Fehler aussieht:** Der Doc-Rotation-Hook läuft seit
> P14-F Mini-Session 24 mit `--strict` als Default. Wer beim Rotieren die Reihenfolge
> newest-first verletzt, bekommt einen **Hook-Abbruch beim Commit**, der wie ein
> kaputter Hook aussieht. Erster Verdächtiger: `check_archive_sequence`, nicht der Hook selbst.

#### A-6 — `docs/INDEX.md` Doppel-Header + drei stale „P15-Plan-Session offen"-Zeilen

`docs/INDEX.md` hat **zwei** `## Closed phases`-Überschriften (Zeile 34 und Zeile 36).
Zusammenführen.

Zusätzlich sind drei Phasenköpfe stale — sie führen „P15-Plan-Session — offen" als offenen
Punkt, was seit dem Plan-Commit nicht mehr stimmt. Je **eine** Zeile, Cross-Phase ist
freigegeben (§4):

| Datei | Anker (verbatim, Stand 2026-08-31) |
|---|---|
| `phase7_reward/CLAUDE.md:457` | `- **P15-Plan-Session (V4)** — Material jetzt vollständig (P14-F D5 + P13-Findings` |
| `phase13_live_data/CLAUDE.md:238` | `   Vier P15-V4-Kandidaten dokumentiert: Pfad A, Pfad B (aufgehoben solange C),` |
| `phase14_discovery/CLAUDE.md` | die „D5-H.-B offen"-Zeile — wird von Step **D1** ohnehin angefasst, dort mitnehmen |

Reiner Doc-Fix, gehört in denselben Commit wie A-5.

---

### Block B — Reward-Kalibrierung (= Phase-11 H3)

> 🔒 **GATE P7: Dieser Block startet erst, wenn das „Phase-12-Reconcile-Timing
> Live-Verify" abgeschlossen gemeldet ist** — das ist die 24-h-Beobachtung am laufenden
> Bot aus `phase7_reward/CLAUDE.md` (dort „A6" genannt; **nicht** zu verwechseln mit
> einem Akzeptanzkriterium dieses Plans, die heißen AK1–AK14). Vorher: nicht anfangen,
> auch nicht „nur den Test schon mal schreiben" — ein grüner Test auf `scorer.py`
> lädt zum Edit ein.

> ⚠ **Bot-berührend.** Vor jedem Edit in diesem Block: Bot stoppen, dann
> `ps aux | grep scheduler.run` als Gegenprobe (Parallel-Login-Falle,
> `reference_ig_parallel_login_trap`). Nach dem Block: `bash scripts/restart-services.sh restart scheduler`.

#### B1 — Die Invariante als Test, **vor** dem Fix

`phase7_reward/tests/test_scorer.py`, neuer Test:

```python
def test_a_full_stop_loss_never_raises_the_score() -> None:
```

Parametrisiert über **jede** Kombination: `status` ∈ {`CLOSED_BY_BROKER`, `TIME_STOP`, `OTHER`}
× `spread_at_entry_pct` ∈ {tight, wide} × `debate_confidence` ∈ {None, 0, 50, 100}.
Assertion: für `r_multiple = -1.0` ist `result.score_after < result.score_before`.

**Dieser Test muss zuerst ROT sein** (AK5). Ist er beim ersten Lauf grün, stimmt etwas an den
Testparametern nicht — nicht am Code. Erster Verdächtiger: `score_before` wurde so niedrig
gewählt, dass `score_min = 0.0` clampt.

#### B2 — `process_weight` senken

**Anker** — `phase7_reward/reward/models.py:357`, verbatim:
```
    process_weight: float = 1.5
```
→ `0.5`, mit einem `ponytail:`-Kommentar, der die Invariante nennt:
max\|process\| = 0.5 × 2.5 = 1.25 < 2.0 = \|outcome bei R = −1\|.

#### B3 — Docstring-Wahrheit in `scorer.py`

**Anker** — `phase7_reward/reward/scorer.py:45`, verbatim beginnend:
```
  asks for. ⚠ The scale fix alone does **not** make the reward loop outcome-neutral
```
→ Den ⚠-Absatz **nicht löschen**, sondern mit einem datierten Nachtrag versehen:
Phase 15 hat die Invariante hergestellt (P1/P2), H3s Semantik-Frage („ist ein Stop-Out ein
clean exit?") bleibt **offen und bewusst unbeantwortet**, die Live-Messung steht in
diesem Plan §3 B1.

#### B4 — `tight_spread_pct` als sichtbarer Knopf

**Anker** — `phase7_reward/reward/models.py:359`, verbatim:
```
    tight_spread_pct: float = 0.05
```
→ **Wert unverändert.** Darüber ein `ponytail:`-Kommentar mit der gemessenen Verteilung
(§3 B2: n=13, Median 0,00456, Max 0,0248, Schwellwert ~11× darüber → Bonus feuert immer)
und der Bedingung fürs Nachziehen (n ≥ 50 Spread-Beobachtungen).

#### B5 — Die zwei Spalten als gegenstandslos dokumentieren

**Anker** — `phase7_reward/reward/recorder.py:44`, verbatim beginnend:
```
``cfg`` precedes it in the signature. ``veto_trigger_count`` / ``gate_fail_count`` are
```
→ Aus „left NULL in v1 (not load-bearing for the score)" wird ein **datierter,
belegter Vermerk**: strukturell immer 0, weil ein `reward_pts`-Row alle Gates und VETOs
passiert hat; Beleg 0 von 1902 `abstain_records` mit `stage='veto'`/`'gate'` (Stand 2026-08-31).
Die VETO-/Gate-Information für abgelehnte Zyklen lebt in `decision_context`
(`005_v3_learning.sql:78-92`). **Kein Code.**

#### B6 — Score-Reset-Script

`phase7_reward/scripts/reset_score_baseline.py`, **NEU**. Verhalten:

1. Öffnet `data/trading_bot.sqlite` (Pfad als Argument, Default aus `RewardConfig.live_db_path`).
2. Druckt **vorher**: alle 8 Zeilen `id, trade_id, outcome_score_delta, process_score_delta, score_after`.
3. `--dry-run` ist **Default**; schreibt nur mit explizitem `--apply`.
4. Schreibt genau: `UPDATE reward_pts SET score_after = 50.0 WHERE id = (SELECT MAX(id) FROM reward_pts)`.
5. Druckt **nachher** dieselbe Tabelle + einen Audit-Block zum Einkleben in `phase15_v4/CLAUDE.md`.
6. Ist **idempotent**: läuft er zweimal, ändert der zweite Lauf nichts.

Ein Test in `phase15_v4/tests/` gegen eine tmp-DB: `--dry-run` ändert nichts, `--apply` setzt
genau eine Zelle, zweiter `--apply`-Lauf ist No-Op.

> **Der Reset ist eine Nikinger-Aktion** (schreibt in die Live-DB). Die Exec-Session baut
> das Script, führt `--dry-run` aus, legt die Ausgabe vor und **wartet**.

#### B7 — Tests

`cd phase7_reward && ../phase1_broker_wrapper/.venv/bin/python -m pytest tests/ -q`

Erwartung: **142 + neue**, alle grün. **Achtung:** bestehende Tests in `test_scorer.py`
pinnen Relativ-Eigenschaften (`clean.process_delta > sloppy.process_delta`,
`test_scorer.py:41`) — die überleben eine Gewichtsänderung. Tests, die **absolute** Zahlen
pinnen, überleben sie nicht und müssen mit datiertem Kommentar angepasst werden.
`phase7_reward/tests/conftest.py:352` setzt `"process_delta": 1.5` als Fixture-Wert —
das ist ein Fake-Wert, kein berechneter; prüfen, ob er noch passt.

---

### Block C — Instinct-ECC

#### C1 — Migration 009 + P2-Zugriff

`phase2_persistence/migrations/009_phase15_instincts.sql`, **NEU**. Tabelle `instincts`
nach P8. `status` ∈ {`proposed`, `validated`, `refuted`, `promoted`, `archived`}.
`domain` mit `CHECK(domain IN ('entry','exit','sizing','timing'))`.

`phase2_persistence/persistence/db.py`: `_INSTINCT_COLUMNS` + drei Methoden
(§5). **Muster:** `_LESSON_COLUMNS` (`db.py:41`) und `insert_lesson` (`db.py:292`).

**Anker** — `phase2_persistence/persistence/db.py:41`, verbatim:
```
_LESSON_COLUMNS = (
```
→ `_INSTINCT_COLUMNS` direkt danach einfügen.

Migrations-Versions-Test anpassen: `phase2_persistence/tests/test_migrations.py` prüft die
Zielversion — heute `8`, wird `9`. (Präzedenzfall: Mini-Session 26 musste dasselbe für 008
machen, dort waren es 4 Stellen.)

#### C2 — `phase15_v4/instinct/` Package

`models.py` (`Instinct`, `InstinctConfig`), `extractor.py`, `validator.py`, `promotion.py`.

`InstinctExtractor` spiegelt `Brain` (P9): `_LLMClientLike`-Protokoll mit
`ask_candidate(system, user, json_schema)`, ein `_build_instinct_prompt(...)`,
best-effort, **wirft nie**. Wiederverwenden, nicht neu bauen:
`phase7_reward/reward/brain.py:63` (Protokoll), `:111` (Prompt-Builder), `:187` (`reflect`).

`InstinctValidator` ist **rein deterministisch** — zählt `evidence_trade_ids` gegen
`contradictions_trade_ids` aus echten `trade_outcomes`. **Kein LLM in dieser Datei.**
Wer hier einen LLM-Call sieht, hat CLAUDE.md „Core principle" verletzt.

`promote_eligible(instincts, n_closed, cfg)` gibt **`[]`** zurück, solange
`n_closed < cfg.instinct_n_min` (P12: 50) **oder** `cfg.enable_instinct_promotion is False`
(P10: Default). Beide Bedingungen, nicht eine.

#### C3 — VETO 5

**Anker** — `phase5_execution/execution/vetos.py:224`, verbatim:
```
    verdict = veto_position_conflict(broker.get_open_positions(), candidate, config)
```
→ `longterm_pre_trade_check(candidate, rules)` als **VETO 5 danach**, vor dem
abschließenden `return VetoVerdict(ok=True, ...)` in `vetos.py:228`.

`rules` kommt aus `config.longterm_rules` (§5) — ein Tupel promoteter, **deterministischer**
Prädikate. Leeres Tupel ⇒ `ok=True` ⇒ bit-identisches Verhalten zu heute. **Das ist der Default.**

**Anker** — `phase5_execution/execution/config.py:107`, verbatim:
```
    max_spread_pct: float = 0.5            # percent of ask (VETO 2)
```
→ `longterm_rules: tuple[Any, ...] = ()` in denselben `# --- VETOs ---`-Block, mit Kommentar:
leeres Tupel = VETO 5 inaktiv, Regeln kommen vom Wiring, **nie** ein Import aus `phase15_v4`.

**Anker** — `phase5_execution/execution/vetos.py:10-14`, verbatim beginnend:
```
- **VETO 1** ``veto_status_and_window`` — market TRADEABLE and inside the trade window.
```
→ VETO 5 in die Modul-Docstring-Liste aufnehmen.

#### C4 — Tests

`phase15_v4/tests/test_instinct.py` + `phase15_v4/tests/test_promotion.py`.
Mindestens diese Assertions:

| Test | Was er pinnt |
|---|---|
| `test_promotion_refuses_below_n_min` | bei `n_closed=8` gibt `promote_eligible` **`[]`** zurück — **das ist P13 = **AK7**, das Akzeptanzkriterium der Phase** |
| `test_promotion_refuses_when_flag_off` | auch bei `n_closed=999` `[]`, solange `enable_instinct_promotion is False` |
| `test_extractor_never_raises` | LLM-Fake wirft auf jeder Methode ⇒ Extractor gibt ein `ok=False`-Ergebnis, keine Exception |
| `test_validator_has_no_llm` | `grep`-artige Zusicherung: `validator.py` importiert nichts aus `brain`/`llm` |
| `test_veto5_with_empty_rules_is_identity` | `pre_trade_check` mit leerer Regelliste verhält sich bit-identisch zu vorher |

Danach die volle Sweep-Wiederholung (§2.1). Erwartung: **1703 + neue**, alle grün.

---

### Block D — Erbstücke

#### D1 — Quellen-Vertrauens-Lock (nur Doku, ~30 Min)

P14 §7 lässt **D5-H.-B** offen. Phase 15 entscheidet: **Verfügbarkeits-Modell** (P14).

Zu ergänzen:
- `phase14_discovery/CLAUDE.md` — ein datierter Absatz „D5-H.-B geschlossen 2026-08-31
  durch Phase-15: Verfügbarkeits-Modell, `last_verified_utc` behält die Semantik
  ‚Discovery-Ableitung'". **Cross-Phase P14 ist freigegeben** (§4).
- `phase13_live_data/PHASE13_BEWEISWOCHE_FINDINGS_2026-08-31.md` ist ein 📕-Snapshot —
  **nicht editieren.** Der Verweis geht in den Phasenkopf.

**Kein Code.** Wer hier eine Substrat-Coverage-Messung baut, hat P14 gegen sich.

#### D2 — `docs/architecture/phase13_14_15.svg`

Beide Closeouts (P13 §10, P14 §10) empfehlen ausdrücklich **kein** Solo-SVG, sondern ein
gemeinsames Bild. Inhalt, damit nichts erfunden wird — drei Spalten:

| Spalte | Inhalt |
|---|---|
| **Phase 13 — Beschaffung** | S1 LS-Kerzen → S2 yFinance-Recorder → S3 Capital.com → S4 GapRescue *(Default AUS, nie gelaufen — §3 B4)*; alle vier schreiben in `bars.sqlite`; **kein** Pfeil von einem Konsumenten zu einer Quelle |
| **Phase 14 — Vermittlung** | `instrument_source_availability` (38 Zeilen) als einzige Kreuzungs-Wahrheit; Discovery-Daemon (ARM-Datei); Konsumenten lesen die **Tabelle**, nicht den Code; `EPIC_MAP` als durchgestrichener Kasten |
| **Phase 15 — Verwertung** | `reward_pts` → `score` → `risk_pct` → Positionsgröße *(die Kette aus §2.5)*; `trade_lessons` + `reward_pts` → Instinct-Extraktion → deterministische Validierung → VETO 5, **Promotion-Gatter sichtbar zu** |

Der Wert des Bildes liegt in **zwei** Elementen: dem fehlenden Pfeil (Konsument → Quelle)
und dem geschlossenen Promotion-Gatter. Beides muss man sehen können, ohne den Text zu lesen.

INDEX-Zeile im selben Commit (`docs/INDEX.md`, Abschnitt Architektur).

#### D3 — Pfad A: Operator-Tool, gebaut aber AUS (P15)

**Pfad A ist ein Operator-Tool, kein Daemon-Feature.** P13-Findings §8.2 sagt wörtlich
„GapRescue-Skript als Operator-Tool mit Schedule". Damit entfällt die Daemon-Wiring-Frage
vollständig: das Script konstruiert `GapRescue` selbst, der Scheduler tut es nie.

> Der Docstring `phase13_live_data/live_data/rescue.py:17` („sonst ist die ganze Klasse nicht
> im Wiring") **setzt Daemon-Wiring voraus.** Diese Prämisse gilt für das Operator-Tool nicht.
> Wer sie trotzdem übernimmt, landet bei einem `SchedulerConfig`-Feld — und damit in
> Phase 8, die **nicht** cross-phase-freigegeben ist (§4). Nicht dort hinlaufen.

Genau zwei Dinge, beide in Phase 13 (freigegeben):

1. **`RescueConfig`** in `phase13_live_data/live_data/rescue.py` (oder daneben) — trägt
   `enable_gap_rescue: bool = False`, die Epic-Liste und den Punkte-Deckel pro Lauf.
   **Kein** Feld in `SchedulerConfig`, **kein** Wiring in `phase8_scheduler/`.

2. **`phase13_live_data/scripts/gap_rescue_operator.py`** — Operator-Tool.
   `--dry-run` ist **Default**. Druckt vor jedem Aufruf die geplanten Epics und die
   geschätzten IG-Punkte. Schreibt nur mit `--apply` **und** `enable_gap_rescue=True`
   (beide Bedingungen, nicht eine — dieselbe Doppel-Sperre wie `promote_eligible`, P10).

**Budget:** der Ledger zeigt heute 5 156 Punkte über alle `kind`-Werte (158 Zeilen, §2.4).
Das Kontingent ist 10 000/Woche. Ein täglicher 1-Tages-Backfill für 8 Epics ≈ 560 Punkte/Woche
≈ **5,6 %**. ⚠ Diese 560 stammen aus P13-Findings §8.2 und sind in dieser Plan-Session
**nicht** nachgerechnet — siehe §9.

**D19/L18 bleibt gelockt.** Dieser Step baut den Schalter, er legt ihn nicht um (P15).
Das Umlegen ist eine getrennte, kostenpflichtige Nikinger-Aktion.


---

## §7 Akzeptanzkriterien (AK1–AK14)

| # | Kriterium | Wie belegt |
|---|---|---|
| **AK1** | Step-0-Ritual ausgeführt, Ergebnis protokolliert (auch als No-Op) | Absatz in `phase15_v4/CLAUDE.md` |
| **AK2** | Σ-Baseline **vor** dem ersten Fix genommen | Tabelle in `phase15_v4/CLAUDE.md`, Erwartung 1703 |
| **AK3** | ROADMAP 15b/15c/15d stimmen mit dem Code überein, datiert vermerkt | `ROADMAP.md:692-701`-Region |
| **AK4** | `ROADMAP.md` und `phase7_reward/CLAUDE.md` **unter 40 KB** | `find . -name "*.md" -size +40k` listet beide **nicht** mehr |
| **AK5** | **Ein Verlust senkt den Score.** Für `r_multiple ≤ −1.0` gilt `score_after < score_before` — über alle Signal-Kombinationen | `test_a_full_stop_loss_never_raises_the_score` grün; war vor B2 rot |
| **AK6** | Score-Reset ist vorbereitet, `--dry-run`-Ausgabe liegt dem Nikinger vor | Audit-Block in `phase15_v4/CLAUDE.md`; `--apply` nur nach Freigabe |
| **AK7** | **Der Promotion-Harness verweigert bei n=8 korrekt** | `test_promotion_refuses_below_n_min` grün — das ist das Phasen-Akzeptanzkriterium (P13) |
| **AK8** | Kein LLM im Validierungspfad | `test_validator_has_no_llm` grün |
| **AK9** | VETO 5 mit leerer Regelliste ist bit-identisch zu heute | `test_veto5_with_empty_rules_is_identity` grün + Phase-5-Sweep 173 unverändert grün |
| **AK10** | D5-H.-B geschlossen: Verfügbarkeits-Modell | Datierter Absatz in `phase14_discovery/CLAUDE.md` |
| **AK11** | `phase13_14_15.svg` existiert, zeigt den fehlenden Konsument→Quelle-Pfeil und das geschlossene Promotion-Gatter | Datei + INDEX-Zeile |
| **AK12** | `enable_gap_rescue` existiert als **Feld einer `RescueConfig` in Phase 13** mit Default `False`; Operator-Script mit `--dry-run`-Default; **kein** `SchedulerConfig`-Feld, **kein** `phase8_scheduler/`-Diff | `grep -rn "enable_gap_rescue" --include="*.py" .` findet ein Feld, nicht nur Prosa; `git diff --stat` nennt kein `phase8_scheduler/` |
| **AK13** | Σ-Sweep am Ende ≥ 1703, **null** neue Fehler | Sweep-Tabelle |
| **AK14** | Jede neue `.md` hat ihre `docs/INDEX.md`-Zeile im selben Commit | `git show --stat` je Commit |

---

## §8 Fehlgriffe, die wie andere Fehler aussehen

| Symptom | Sieht aus wie | Erster Verdächtiger |
|---|---|---|
| Nach B2 fallen Tests in `test_scorer.py` um | Der `process_weight`-Fix ist falsch | Tests, die **absolute** Zahlen pinnen statt Relativ-Eigenschaften. `conftest.py:352` setzt `"process_delta": 1.5` als **Fake**-Fixture-Wert, nicht als berechneten. |
| `test_a_full_stop_loss_never_raises_the_score` ist **sofort grün** | Der Bug existiert nicht | `score_before` zu niedrig gewählt → `score_min = 0.0` clampt und verdeckt das Vorzeichen. `score_before = 50.0` verwenden. |
| Commit wird vom Hook abgelehnt | Hook kaputt | `check_archive_sequence` mit `--strict` (Default seit P14-F Mini-Session 24). Meist: Archiv-Reihenfolge nicht newest-first, oder neue `.md` ohne INDEX-Zeile. |
| Migration-Test rot nach C1 | Migration 009 fehlerhaft | `phase2_persistence/tests/test_migrations.py` pinnt die Zielversion. Bei 008 waren es **4** Stellen. |
| IG-Auth-Fehler während eines Live-Schritts | Credentials kaputt | Zwei parallele IG-Logins, die sich den Token überschreiben. Bot stoppen, `ps aux \| grep scheduler.run`. Kein Reboot nötig. |
| `get_current_score()` liefert nach B6 nicht 50,0 | Reset hat nicht gegriffen | `get_current_score()` liest `ORDER BY id DESC LIMIT 1` — also die höchste **`id`**, nicht den neuesten `trade_id`. Beide zeigen heute auf dieselbe Zeile; das muss so bleiben. |
| Nach D3 taucht `kind='rescue'` im Ledger auf, obwohl AUS | Das Flag wirkt nicht | Der Ledger hatte vorher **0** `rescue`-Zeilen (§2.4). Jeder Eintrag heißt: S4 lief. Sofort stoppen — das kostet IG-Kontingent. |
| Phase-5-Tests fallen nach C3 | VETO 5 ist falsch | Fast immer: jemand hat `pre_trade_check` **doch** einen `rules`-Parameter gegeben statt das `ExecutionConfig`-Feld zu nutzen (§5). Es gibt genau **einen** Aufrufer, `executor.py:332` — und der übergibt keinen. Zweiter Verdächtiger: mutable Default (`[]` statt `()`) in einem `frozen=True`-Dataclass. |

---

## §9 „Bei Ausführung verifizieren" — vollständige Liste

**Diese Liste ist vollständig. Was hier nicht steht, ist in der Plan-Session gegen Code
oder Live-DB geprüft und darf als Fakt behandelt werden.**

1. **`spread_at_entry_pct = 1.0` bei Trade 8** (§3 B5). Ursache nicht aufgeklärt. Vor B4
   nachsehen, ob ein zweiter Schreibpfad Bruch statt Prozent-vom-Ask liefert.
2. **Die 560 IG-Punkte/Woche für Pfad A** (§6 D3). Stammt aus P13-Findings §8.2,
   **nicht nachgerechnet**. Vor dem Scharfschalten gegen `source_spend` verifizieren.
3. **Der nachgerechnete Score „≈ 63,35"** (§3 B3). **Von Hand gerechnet, nicht ausgeführt.**
   Die tragende Aussage (kein Risiko-Modus-Flip, weil jede Nachrechnung deutlich über 50 landet)
   ist davon unabhängig robust — die Zahl selbst ist es nicht. Wer sie zitiert, rechnet sie
   vorher nach oder schreibt „nicht nachgerechnet" dazu.
4. **`compression_trigger_pct`-Default und ob der Latch je gefeuert hat.** Für A-3 wurde
   die **Existenz** des Mechanismus verifiziert (`debate.py:172`, `:187-195`), **nicht**
   sein Live-Verhalten. Die ROADMAP-Korrektur darf deshalb „gebaut" sagen, aber **nicht**
   „live-verifiziert".
5. **Die zwei Zombie-Prozesse 21214/21215** (§2.2). Kein beobachteter Schaden, Ursache
   nicht untersucht. Falls sie sich nach einem Scheduler-Restart vermehren: eigener Befund.
6. **Ob `RewardConfig.n_min = 10` außerhalb der Wilson-Confidence gelesen wird.** P12 nimmt
   an, dass nein, und legt `instinct_n_min` separat an. Vor C2 einmal greppen.
7. **Genaue Anzahl der Stellen, die `test_migrations.py` bei Version 8 → 9 anpassen muss.**
   Bei 008 waren es 4; für 009 nicht nachgezählt.
8. **Ob `phase15_v4/tests/` eine eigene `conftest.py` braucht.** Die Memory-Notiz
   `reference_running_phase_tests` warnt vor Namenskollisionen bei `tests.conftest` über
   Phasen hinweg. Muster von `phase14_discovery/tests/` übernehmen.

---

## §10 Out-of-Scope (Phase 15 baut das **nicht**)

| Was | Warum nicht |
|---|---|
| **15a Council-Integration** | Nikinger-Entscheidung 2026-08-31, Runde 1 |
| **15d als Code** (Force-Trigger bauen) | moot-by-absence (P4-Analogie, Step A-3 Anker 3). CLAUDE.md Hard Rule 5 bleibt für den Tag stehen, an dem jemand einen baut |
| **Auto-Gap-Fill-Scheduler (D16)** | Nikinger-Entscheidung 2026-08-31, Runde 2 |
| **Dukascopy echt (D15)** | dito — bleibt Mock-only mit `NotImplementedError` |
| **Pfad B — Schema-Reinterpretation** (`status='gap_rescue_only'`) | aufgehoben solange Pfad C gilt (P14 §10) |
| **Phase-11-Wiederaufnahme (WI-2/W2)** | eigene Nikinger-Entscheidung, nicht Teil dieses Plans |
| **`tight_spread_pct` neu kalibrieren** | P3 — n=13 ist Rauschen |
| **H3s Semantik-Frage beantworten** („ist ein Stop-Out ein clean exit?") | P2 — nicht nötig für die Invariante, und ohne Datenbasis |
| **Backfill der Trades 4–7** | P5 — die Deltas sind Messhistorie und bleiben |
| **`Database.get_risk_mode()` löschen** (toter Code, §2.5) | außerhalb des Scopes; hier nur vermerkt |
| **Die zwei Zombie-Prozesse** | §9.5, kein beobachteter Schaden |
| **Jeder Diff in `phase8_scheduler/`** | Phase 8 ist nicht cross-phase-freigegeben (§4); kein Step braucht sie |

---

## §11 Operator-Aktionen (Nikinger, nicht die Exec-Session)

| # | Aktion | Wann | Kosten |
|---|---|---|---|
| 1 | **„Phase-12-Reconcile-Timing Live-Verify" abschließen** (in `phase7_reward/CLAUDE.md` „A6") — 24-h-Beobachtung, nächster OPEN-Trade mit IG-Lag soll ≤ 5 CRITICALs in 24 h liefern (statt 6+ in 52 min) | **vor Block B** (Gate P7) | keine |
| 2 | Bot stoppen vor Block B, danach `bash scripts/restart-services.sh restart scheduler` | Block B | keine |
| 3 | `reset_score_baseline.py --apply` freigeben, nachdem die `--dry-run`-Ausgabe vorliegt | Step B6 | keine |
| 4 | `git push origin main` | nach jedem Block | keine |
| 5 | `enable_gap_rescue` scharfschalten | **nicht in Phase 15** (P15) | ~560 IG-Punkte/Woche, unverifiziert (§9.2) |

---

## §12 Commit-Konvention

`phase15: <imperative>` — ein logischer Schritt pro Commit, Muster wie `phase14:`.
Jede neue `.md` bringt ihre `docs/INDEX.md`-Zeile **im selben Commit** mit (P16).

Blockweise Commits, nicht schrittweise: A ist 3–4 Commits, B ist 2–3, C ist 3–4, D ist 3.

---

> **Stand:** 2026-08-31, Plan-Session (Claude Code, Opus 5).
> **Nächste Aktion:** Nikinger gibt Operator-Aktion 1 („Phase-12-Reconcile-Timing Live-Verify") frei; die Exec-Session (Sonnet 5)
> kann **Block A und Block D sofort** starten — sie hängen nicht am Gate P7.
