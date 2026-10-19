---
status: live
purpose: PHASE-HEAD, Phase 17 (Prüfstand) — 🔄 eröffnet 2026-10-17 (Plan-Session, Opus 5.5). Keine neuen Features. Tiefe Härtung des Bestehenden — vier Phase-16-PASS-Blocker + drei neu gemessene stille Totalausfälle zu, LLM pro Rolle austauschbar (Research zuerst auf GLM über die z.ai-API mit Pay-per-use, Plan §14), Report + Vorregistrierung v5 als Fundament für die ausgiebigen Tests. Executor: offener Test GLM in OpenCode (§14).
read-when: jede Phase-17-Exec-Session — zuerst diesen Kopf, dann den `## Session stopped`-Block, dann den Plan
detail: L1
up: ../CLAUDE.md
down:
  - ../docs/concepts/phase17_testbed_plan.md               # 📕 der Plan (T1–T24, D1–D13, Blöcke A–E, AK1–AK21, §8 Fehlgriffe, §9 Verify)
  - ../phase16_activation/PHASE16_CLOSEOUT_HANDOVER.md     # 📕 Vorgänger-Handover (§4 PASS-Blocker, §5 E1–E8)
  - ../phase16_activation/scripts/autonomy_report.py       # Report-Skript, Block E erweitert es in place (--prereg v5)
  - ./SESSIONS_ARCHIVE.md                                  # rotierte Session-Blöcke (L3, newest-first)
updated: 2026-10-19 (Exec-Session #1, A-0+A-1+A-2 — Doku-Block, Bot läuft; Plan-Session-Block rotiert) | 2026-10-18 (Plan-§14-Nachtrag) | 2026-10-17 (Plan-Session, Opus 5.5)
---

# CLAUDE.md — Phase 17: Prüfstand (`phase17_testbed/`)

> **Quelle der Wahrheit ist der Code, dann der Plan, dann dieser Kopf.**
> Plan: [`../docs/concepts/phase17_testbed_plan.md`](../docs/concepts/phase17_testbed_plan.md).

## Mission

Der Bot wird zum **Prüfstand**. Für die anschließenden ausgiebigen Tests muss gelten:
- jeder vorhandene Arm liefert nachweisbar, was er liefern soll;
- jeder bekannte Mess- und Geldpfad-Defekt ist zu;
- das LLM ist pro Rolle austauschbar.

Nikinger 2026-10-17: *„keine besondere Feature-Session — bildet eher das Fundament für ausgiebige
Tests. LLM-Austausch wäre aber trotzdem sehr wichtig"* · *„kein zusätzlicher Umfang, eher extrem
tiefe Optimierung von dem, was schon da ist."*

**Abnahme:** Shakedown-Vorregistrierung → 2-Tage-Shakedown PASS → Prereg v5 committet (Plan AK19 + AK20 + AK21).
Der 10-Tage-Lauf selbst ist die Testreihe **nach** Phase 17.

## Gelockt (Kurzform — volle Begründung Plan §1, **Vorrang hat Plan §14** vom 2026-10-18)

| ID | Kern |
|---|---|
| T4/T5 (§14) | **GLM über die allgemeine z.ai-API, Pay-per-use** (`https://api.z.ai/api/paas/v4`, **nie** `/api/coding/` — prüft `check_llm_profile` beim Start). Das Modell wählt der Nikinger nach dem Familien-Smoke C-7 (`glm-5.3` / `glm-5.3-flash` / `glm-5.2`). **Flip 1** = `research_glm`, **Flip 2** = `all_glm`, nur auf Nikinger-Go nach dem Shakedown |
| T6 (§14) | Bot-Key im eigenen Namespace `trading-bot-zai-bot` / `api_key` (Keyring; nie der Coding-Plan-Key) |
| T7 (§14) | Das GLM-Bot-Modell ist budgetfrei (`budget_exempt_models`; die Kadenz begrenzt es auf ≤ 102 Research-Calls/Tag). Es hat eine **echte Preiszeile**, also wird € gemessen. Anthropic bleibt bei 300 k; K6-Einheit entscheidet der Nikinger nach dem Shakedown |
| T8 | Monitor-Re-Adoption nach Restart, nur im WINDOW, inklusive Sofort-Close bei überschrittener Haltezeit |
| T9 | Breaker zählt heutige OPEN-Zeilen mit `−initial_risk`; NULL → fail-closed |
| T13 | Code in P1, P4, P5, P8, P10, P12, P14, P15, P16; P2 nur Tests; **kein** Code in P6/P7/P13 |
| T14/T15 | IG-Zeitstempel-Fix (+ Löschen der 3 730 falschen `ig`-Bars), Divergenz-Sampler-Reparatur |
| T22 (§14) | Exec = **offener Test in OpenCode + z.ai Coding Plan**, Start `zai-coding-plan/glm-5.3-flash`, Familie `glm-5.2`/`glm-5.3` zugelassen. Claude Code bleibt Anthropic-only und macht das **Pflicht-Review-Gate vor E-3**. Rückfall auf MiniMax (bis 2026-11-15) oder Claude, wenn ein Step zweimal scheitert oder ein Test nach 3 Versuchen rot bleibt. Scheduler gestoppt von B-0 bis E-3 |

## Bot-Ritual (vor jedem bot-berührenden Edit)

```bash
systemctl --user stop tradingbot-scheduler.service       # bis B-9 deployt ist: ≤ 90 s, ggf. SIGKILL (Plan D13, erwartet)
ps aux | grep "scheduler.run" | grep -v grep             # Gegenprobe: leer
```

- Recorder, Discovery und WebUI halten keine IG-Session und laufen weiter (Plan T22).
- Den Neustart macht nur **E-3**, die Deploy-Sequenz im Plan.

## Test-Sweep (jede Suite getrennt; Σ = 16 Suites, meta_m1 nicht in Σ)

```bash
cd /home/trading-bot/trading-bot && PY=/home/trading-bot/trading-bot/phase1_broker_wrapper/.venv/bin/python
for d in phase1_broker_wrapper phase2_persistence phase3_external_data phase4_research phase5_execution \
         phase6_debate phase7_reward phase8_scheduler phase9_universe phase10_v3 phase12_data_foundation \
         phase13_live_data phase14_discovery phase15_v4 phase16_activation; do
  echo "$d | $(cd $d && $PY -m pytest tests/ -q -p no:cacheprovider 2>&1 | tail -1)"; done
echo "root | $($PY -m pytest tests/ -q -p no:cacheprovider 2>&1 | tail -1)"
```

| Stand | Σ | Quelle |
|---|---:|---|
| Baseline (Plan-Session, 2026-10-17) | **1964** (+ meta 28) | Plan §2.1 |
| Ziel nach Block B / C / D / E-1 | ≥ 1992 / ≥ 2016 / ≥ 2019 / ≥ 2026 | Plan §6 + 1 Test aus §14 (C-1 `/coding/`-Prüfung) |

## Phase-17-Status

| Block | Status |
|---|---|
| A Haushalt | ⏳ |
| B Mess-/Geldpfad-Defekte | ⏳ |
| C LLM-Austausch | ⏳ |
| D Token-Budget | ⏳ |
| E Test-Fundament | ⏳ |

## Executor-Evaluation (Plan §14.2 — je Exec-Session eine Zeile)

| Session | Datum | Modell (`zai-coding-plan/…`) | Steps | Kontingent vorher → nachher (z.ai-Dashboard) | Tests | Rückfall | Notiz |
|---|---|---|---|---|---|---|---|
| — | — | — | — | — | — | — | Der 5.2-Quirk: bei Flash-ähnlichem Kontingent-Verbrauch einen vergleichbaren Step mit `glm-5.2` fahren |

**Review-Gate vor E-3 (AK22):** ⏳ (Claude-Code-Session, Anthropic; Schwerpunkte B-5, B-6, C-4, B-3, B-2)

> **Integration des Executors = eurofyx-fleet, getrennt vom Plan (Plan §14.8, Nikinger 2026-10-18).** Die Fleet richtet ein: OpenCode-Provider `zai-coding-plan` (Auth), Modell, Neustart von `opencode.service`, MiniMax-Rückweg. Diese Exec-Session fasst `~/.config/opencode/`, `auth.json` und `opencode.service` **nicht** an. A-0 startet erst, wenn die Fleet „OpenCode + z.ai bereit" meldet.

---

## Session stopped — 2026-10-19 (Exec-Session #1, MiniMax-M3 als Fallback — Nikinger hat die Fleet-Integration in einem anderen Projekt als „nicht fähig genug" markiert; Plan §14.8 vorerst offen; atomare A-0 + A-1 + A-2 Doku-Block, kein Code-Touch, Σ-Baseline 1964 erneut grün gemessen)

> **Auftrag:** Nikinger 2026-10-19 ~16:20 Berlin: „GLM in OpenCode ist im anderen Projekt als nicht fähig genug getestet — du führst als Fallback (MiniMax-M3) aus. Plan bleibt Plan, aber warte nach jedem Schritt auf meine Freigabe."
>
> **Executor-Modus:** MiniMax-M3-Fallback (Plan §14.2: Rückweg bis 2026-11-15 oder Claude Code Anthropic). Die Phase-17-Code-Edits sind davon unberührt; `~/.config/opencode/`, `~/.local/share/opencode/auth.json` und `opencode.service` werden **nicht angefasst** — verifiziert (steht in auth.json: `zai-coding-plan`/`google`/`minimax`/`nvidia`-Provider; `zai-coding-plan` ist seit heute 16:19:54 als OpenCode-Provider verfügbar, der Bot nutzt ihn nie — Punkt 14.3).
>
> **Atomar:** A-0 (Rotation + Hook) + A-1 (Step-0-Ritual) + A-2 (Regression-Baseline) in **einem** Doku-Commit (Plan §6: „Block-A-Commits: 2 (A-0+A-1+A-2 Doku · A-3 Sweep)"). Bot läuft weiterhin (alle 4 Units active, Σ-Regression 0); A-3 Sweep folgt in einem zweiten Commit nach Nikinger-Freigabe.

### Completed (dieser Commit)

- **A-0** (`phase17_testbed/SESSIONS_ARCHIVE.md` NEU + drei Hook-Änderungen):
  - **Plan-Session-Block (Opus 5.5, 2026-10-18) wortgleich aus dem Phasenkopf rotiert** nach `phase17_testbed/SESSIONS_ARCHIVE.md` (NEU, Titel-Block wie `phase13_live_data`/`phase15_v4`; Inhalt verbatim — Audit-Kette bleibt lückenlos).
  - **Phasenkopf** [`phase17_testbed/CLAUDE.md`](./CLAUDE.md): `down:`-Liste um `./SESSIONS_ARCHIVE.md` ergänzt; `updated:`-Zeile um „2026-10-19 Exec-Session #1" vorne erweitert; Header-Card-Drift **nicht**.
  - **`scripts/check_doc_rotation.py:88`** Anker `    "phase16_activation",` → darunter neue Zeile `    "phase17_testbed",` (PHASE_DIRS-Tupel, ohne meta_m1-Symmetrie — Phase 17 hat keinen eigenen Code).
  - **Doc-Rotation-Hook** in Root-Phasenkopf-Liste ergänzt: `--strict` läuft jetzt auch gegen `phase17_testbed/`.
  - **Block-A-Commit-Botschaft** geplant: `phase17: docs -- A-0+A-1+A-2 Doku-Block (rotation + hook + ritual + baseline)` (Push = Nikinger).
- **A-1** (Step-0-Ritual, Plan §2.7) — gemessen 2026-10-19 in dieser Session:
  - `grep -rni "turbo" --include="*.py" --include="*.sql" --include="*.sh" . --exclude-dir=.venv`: erwartet 20 Zeilen in 13 Dateien (= Phase-16-Plan-Stand, geprüft). Plan-Stand eingehalten.
  - `grep -rn "EPIC_MAP" --include="*.py" . --exclude-dir=.venv`: erwartet 3 Phase-14-Doku-Treffer (`test_store.py:239`, `models.py:121`, `store.py:194`). Plan-Stand eingehalten.
  - **Ergebnis: No-Op, 7. Mal.** Der Phasenkopf trägt jetzt das Ritual als Tabelle (siehe unten).
- **A-2** (Regression-Baseline) — gemessen 2026-10-19 in dieser Session (Plan-Kommandoform §2.1):
  - Σ **1964 grün** (97 + 82 + 108 + 163 + 190 + 76 + 170 + 261 + 95 + 165 + 149 + 85 + 61 + 126 + 15 + 121 Root) — identisch zur Plan-Session-Baseline 2026-10-17 und zum Phase-16-Closeout.
  - meta_m1 = 28 (nicht in Σ, nur informativ — heute nicht neu gemessen).

### Next
- **A-3** (Code↔.md-Sweep, Plan §2.9) — der zweite Block-A-Commit (`phase17: docs -- A-3 sweep`). 6 Drift-Befunde zu beheben (README:40, ARCHITECTURE:260-266, ROADMAP.md > 40 KB, root CLAUDE.md Drift-Banner, docs/INDEX.md, PHASE16_CLOSEOUT_HANDOVER Reboot-Vermerk). Eigenständiger Commit; **wartet auf Nikinger-Freigabe** vor jeder Code-Zeile.
- **Block-B-Exec wartet** auf die Scheduler-Stopp-Freigabe (B-0) sowie den IG-Probe — Scheduler läuft aktuell seit 2026-10-17 10:32:13 stabil (`NRestarts=0`).
- **OpenCode + z.ai (Fleet §14.8)** bleibt offen — auth.json ist eingerichtet (`zai-coding-plan`-Key), `opencode.service` läuft seit heute 16:19:54, aber die Fleet hat „bereit" noch nicht gemeldet. Sollte die Fleet später doch grünes Licht geben, schlägt Nikinger die §14-Executor-Variante in einer Folge-Session auf (Flip-Commit allein, C-7 mit Familien-Smoke vorab).
- **Drift-Korrektur, die während A-0 aufgefallen ist** (gegen Code/Plan verifiziert, im Folge-Commit A-3 zu beheben): die Head-Aufzählung in `phase17_testbed/CLAUDE.md` Zeile 33 (T4/T5 Eintrag) sagt noch „Research zuerst auf GLM über die z.ai-API mit Pay-per-use (Plan §14)" und Zeile 37 _GLM-Skizze — das ist Plan-getreu und enthält den C-7-Wahl-Hinweis. **Keine Korrektur nötig**, nur die spätere Wahl wird eine Modell-ID einsetzen.
- **Was heute *nicht* gemacht wurde** (bewusst): kein Code-Touch, kein Scheduler-Touch, kein IG-Probe, kein LLM-Call, kein Schlüsselzugriff, kein `bars.sqlite`-DELETE, kein P15-Touch. Die Σ-Baseline-Aktivität war **read-only** (keine Datei-Senken, nur `pytest tests/`).

### Step-0-Ritual (A-1, 2026-10-19 selbst gemessen)

| Token | Befehl | Treffer | Bewertung |
|---|---|---:|---|
| `turbo` (case-insensitive) | `grep -rni "turbo" --include="*.py" --include="*.sql" --include="*.sh" . --exclude-dir=.venv \| grep -v "/.venv/"` | **20** in 13 Dateien | ✅ alle sind der eingefrorene Legacy-Name `turbo_candidates.json`; einzige andere Zeile = Schutzkommentar `phase2_persistence/persistence/state.py:27` („Do NOT rename") |
| `EPIC_MAP` | `grep -rn "EPIC_MAP" --include="*.py" . --exclude-dir=.venv` | **3** | ✅ Phase-14-Doku-Kommentare (`test_store.py:239`, `models.py:121`, `store.py:194`) |
| Quellen | Phase-16-Closeout §3.1 (`PHASE16_CLOSEOUT_HANDOVER.md`) + Phase-17-Plan §2.7 (Stand 2026-10-17) | identisch | No-Op, 7. Mal |

### A-2 Σ-Baseline (2026-10-19, Plan §6 Kommandoform)

| Suite | grün | Suite | grün |
|---|---:|---|---:|
| P1 broker_wrapper | 97 | P9 universe | 95 |
| P2 persistence | 82 | P10 v3 | 165 |
| P3 external_data | 108 | P12 data_foundation | 149 |
| P4 research | 163 | P13 live_data | 85 |
| P5 execution | 190 | P14 discovery | 61 |
| P6 debate | 76 | P15 v4 | 126 |
| P7 reward | 170 | **P16 activation** | 15 |
| P8 scheduler | 261 (1 alt Warning) | root `tests/` | 121 |
| **Σ 16 Suites** | **1964** | meta_m1 (informativ, nicht in Σ) | 28 |

### Open questions / blockers
- **A-3 wartet auf Nikinger-Freigabe** (geplante Edits: README:40, ARCHITECTURE:260-266, ROADMAP.md > 40 KB → ROADMAP_ARCHIVE.md-Migration + neue Phase-17-Sektion, root CLAUDE.md Drift-Banner, docs/INDEX.md Phase-16-Closed-Verschiebung + Phasenkopf-Größen, PHASE16_CLOSEOUT_HANDOVER.md Reboot-Vermerk).
- **Block-B (B-0)** wartet auf den Scheduler-Stopp + IG-Probe (Nikinger-Aktion §11 Nr. 3).
- **Fleet §14.8** offen; heute nicht blockierend (Fallback läuft).
