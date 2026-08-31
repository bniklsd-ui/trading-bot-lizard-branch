# SESSIONS_ARCHIVE.md — Phase 15 (V4: Reward-Kalibrierung · Instinct-ECC · Quellen-Vertrauens-Lock)

Newest-first. Rotation rule (root `CLAUDE.md`, mandatory since 2026-07-06): the phase head
carries exactly one `## Session stopped` block; archives have no size cap. See
[`../CLAUDE.md`](../CLAUDE.md) "Rotation rule (mandatory since 2026-07-06)" for the full
contract, and [`../docs/DOC_LAYERS_CONVENTION.md`](../docs/DOC_LAYERS_CONVENTION.md) for
the L0/L1/L2/L3 model.

---

## Session stopped — 2026-08-31 (Plan-Session, Opus 5)

### Completed

- **`docs/concepts/phase15_v4_plan.md`** (NEU, 746 Zeilen): execution-ready Plan.
  P1–P16 gelockt mit Begründung je Zeile · §2 selbst gemessene Fakten · §3 fünf Befunde ·
  §5 Contracts mit exakten Namen · §6 Schritt-Sequenz mit Verbatim-Ankern ·
  §7 Akzeptanz AK1–AK14 · §8 „Fehlgriffe, die wie andere Fehler aussehen" ·
  §9 vollständige „bei Ausführung verifizieren"-Liste · §10 Out-of-Scope ·
  §11 Operator-Aktionen. Commit `f98df68` (+ Folge-Commit mit den Korrekturen unten).
- **`docs/INDEX.md`**: Index-Zeile im selben Commit (P16).
- **Σ-Baseline selbst gemessen: 1703 grün**, per-Phase-Tabelle in Plan §2.1.
  Kommandoform verifiziert. Die Memory-Notiz mit den 2026-07-02-Baselines ist **stale**.
- **Live-DB read-only inventarisiert** (Plan §2.3/§2.4) — 8 Trades, 1902 Abstains
  (davon 1852 `research_empty`, **0** `veto`/`gate`), 5 von 1596 Snapshots mit Spread.
- **Fünf Befunde** (Plan §3): B1 Reward belohnt Verluste · B2 Clean-Entry-Bonus ist eine
  Konstante · B3 vier Live-Zeilen tragen noch die 120×-Vergiftung · B4 `GapRescue` (S4)
  hat nachweislich nie gelaufen und ist nicht verdrahtet · B5 `spread_at_entry_pct = 1.0`
  bei Trade 8 (unaufgeklärt, in §9).
- **Advisor-Review eingearbeitet** (2 Runden): Akzeptanzkriterien auf `AK*` umbenannt
  (kollidierten mit den Step-Buchstaben und mit dem „A6"-Gate), Gate überall voll
  ausgeschrieben, VETO-5-`rules`-Quelle als `ExecutionConfig.longterm_rules` festgelegt
  und gegen `vetos.py:23-31` + `config.py:30` verifiziert, D3 auf ein Operator-Tool in
  Phase 13 zusammengezogen (die Phase-8-Frage entfällt damit ganz).

### Nikinger-Entscheidungen dieser Session (2026-08-31)

| # | Frage | Entscheidung |
|---|---|---|
| 1 | Blöcke | **A + B + C** (nicht 15a Council) |
| 2 | A6 vs. Block B | **A6 zuerst**, Block B als spät gegateter Step |
| 3 | 15d Force-Trigger | **moot-by-absence** erklären und dokumentieren |
| 4 | Cross-Phase | **P2 + P4 + P5 + P6 + P7 + P13 + P14** freigegeben |
| 5 | Block B Schnitt | **Kalibrierung fixen**, die zwei NULL-Spalten dokumentiert leer lassen |
| 6 | Score-Historie | **Score auf 50 zurücksetzen**, alte Deltas bleiben stehen |
| 7 | Block C Akzeptanz | Extraktion + Validierung, Promotion hinter Flag, **Akzeptanz = „verweigert korrekt bei n=8"** |
| 8 | Erbstücke | Quellen-Vertrauens-Lock + `phase13_14_15.svg` + **Pfad A** (nicht D15/D16) |
| 9 | Startblock | **Block A** (nicht Block D zuerst) — Nikinger 2026-08-31, nach dem Plan-Commit |
| 10 | Gate P7 | **A6 ist freigegeben** (Beobachtung autorisiert) — ⚠ freigegeben ≠ abgeschlossen, siehe unten |

### Next

**Startblock ist Block A** (Nikinger 2026-08-31). Erster Schritt: Plan §6 Step **A-1**
(Step-0-Ritual ausführen und protokollieren), dann **A-2** (Σ-Baseline, Erwartung 1703),
dann A-3 … A-6. Block D danach — er hängt auch nicht am Gate, ist aber nachgeordnet.

**Block B startet nicht.** Gate P7 ist **zu**.

### Gate-P7-Stand (gemessen 2026-08-31, nach der Nikinger-Freigabe)

Der Nikinger hat A6 **freigegeben** — das heißt: die Beobachtung ist autorisiert und der
Bot läuft dafür (PIDs 21184 / 21197 / 21207). Es heißt **nicht**, dass A6 abgeschlossen ist:

| geprüft | Ergebnis |
|---|---|
| OPEN-Trades in `trade_outcomes` | **0** — alle 8 Zeilen `status='CLOSED'` |
| neuester Trade | `id=11`, `2026-08-27T08:15:08Z`, geschlossen |
| `reward_pts` | 8 Zeilen, unverändert |

A6 braucht einen **OPEN-Trade mit IG-Lag** und danach 24 h Beobachtung. Beides ist noch
nicht passiert. **Gate P7 öffnet erst, wenn A6 als abgeschlossen gemeldet ist** — nicht
mit der Freigabe. Wer Block B vorher anfängt, macht die Messung wertlos (P7-Begründung).

### Open questions / blockers

- **Gate P7 ist der einzige harte Blocker** und weiterhin zu: wartet auf einen OPEN-Trade
  + 24 h. Erwarteter Live-Effekt: ≤ 5 CRITICALs in 24 h statt 6+ in 52 min;
  > 24 h ohne Auflösung = WARNING statt CRITICAL.
- **Push ist erledigt** — `origin/main` = `d1dd26b` (Nikinger, 2026-08-31), 0 ahead / 0 behind.
- Die vollständige Drift-Liste steht in **Plan §9** (8 Punkte). Was dort nicht steht,
  ist in der Plan-Session gegen Code oder Live-DB geprüft.
