# SESSIONS_ARCHIVE.md — Phase 17 (Prüfstand)

Newest-first. Rotation rule (root `CLAUDE.md`, mandatory since 2026-07-06): the phase head
carries at most one `## Session stopped` block; archives have no size cap. See
[`../CLAUDE.md`](../CLAUDE.md) "How to work in this repo" — Rotation rule, and
[`../docs/DOC_LAYERS_CONVENTION.md`](../docs/DOC_LAYERS_CONVENTION.md) for the L0/L1/L2/L3 model.

---

## Session stopped — 2026-10-19 (Exec-Session #2 ENDE — Block B-2 Divergenz-Sampler, 2 Commits in P12+P8, Σ 1965 + 4 P12 + 2 P8 = **1971** grün; Scheduler gestoppt + 3 Units laufen weiter; Nikinger-Freigabe zur Beendigung)

> **Auftrag:** Nikinger 2026-10-19 (später Session): „Lets go on with the next step!" → Exec-Session #2 setzt die explizite **Next**-Priorität aus Session #1 um: **B-2 Divergenz-Sampler (D2, P12 + P8)** per Plan §6 verbatim (T13: Code in P12 + P8 ✓, beide Phasen für Cross-Phase-Edits freigegeben).
>
> **Executor-Modus:** MiniMax-M3-Fallback (Plan §14.2) — unverändert. `~/.config/opencode/`, `auth.json`, `opencode.service` weiterhin unangefasst.

### Completed — diese Exec-Session (2 Commits)

| # | Commit | Phase | Inhalt |
|---|---|---|---|
| 1 | `phase17+phase12: B-2 — Divergenz-Sampler (compute_return_divergence → window_return_divergence)` | P12 | `data_foundation/heartbeat.py`: `compute_return_divergence` (Z. 228–252) ersetzt durch `window_return_divergence` (5m IG vs. **gleiches** 5m-yF-Fenster, nicht mehr 2m/5m-Mix); 3 neue Konstanten (`COMPARATOR_LAG_MIN=25`, `IG_SAMPLE_COUNT=8`, `MIN_YF_BARS=4`); `DivergenceSampler.sample_epic` Rumpf Z. 311–371 nach Plan §6 (a)–(g) ersetzt — Throttle erst **nach** erfolgreichem Vergleich, explizites `divergence_ok`-Event, typisierte `no_comparator`-Events. Docstring A6.0-Verweis angepasst |
| 1b | (gleicher Commit) | P12 | `phase12_data_foundation/tests/test_heartbeat.py`: 7 Sampler-Tests umgestellt auf neues Setup (`now=09:35`, 8 IG-Bars endend 09:30, yF-Fenster [09:05, 09:10)) + 4 neue Tests (`test_no_comparator_does_not_consume_daily_throttle`, `test_partial_yf_window_is_no_comparator`, `test_agreement_emits_divergence_ok`, `test_window_return_divergence_same_window`) |
| 2 | `phase17+phase8: B-2 — Divergenz-Sampler-Gate (_sampler_due)` | P8 | `scripts/wiring.py`: neue Helper-Funktion `_sampler_due(now, config)` (Clock-WINDOW + ≥40min nach Öffnung, Clock-Phase via lazy `from scheduler.clock import Phase`) + Edit Z. 1095: `if divergence_sampler is not None:` → `if divergence_sampler is not None and _sampler_due(_now(), config):`. Reuse der Clock-Klassifikation als single source of truth |
| 2b | (gleicher Commit) | P8 | Neue Datei `phase8_scheduler/tests/test_wiring_sampler_gate.py` (Muster `test_wiring_schema_floor.py`): `test_sampler_due_false_on_weekend_and_before_open_plus_40` (Sa 12:00, Mo 09:00, Mo 09:39:59 → False) + `test_sampler_due_true_mid_window` (Mo 09:50, Mo 12:00, Mo 17:29:59 → True; Mo 18:00 → False). +2 P8-Tests grün |

**Σ-Steigerung:** P12 149 → **153** (+4 ✓ Plan-AK), P8 261 → **263** (+2 ✓ Plan-AK), Σ 1965 → **1971** (+6). Keine Regressionen in den übrigen 14 Suites.

### Next (geplante Folgesessions, in Priorität)
- **B-3 Promotion-Bridge (D3, P15 + P8).** 3 Nahtfehler (`validate` ohne `trades`, `.value` statt `.decision`, Keys ohne `_json` → 29/29 NULL) + Contract-Test mit echter `persistence.Database`. Eigener Extractor-Client (`max_tokens=2048`, `timeout_s=60`). +2 P15-Tests + 1 P8-Test.
- **B-4 Abschneiden sichtbar (D4, P4).** `_attempt`: Meter **vor** Parse; `stop_reason=="max_tokens"` / `finish_reason=="length"` → `LLMResponseError` ohne Retry. +4 P4-Tests.
- **B-5 Monitor-Re-Adoption (D5, T8, P5 + P8).** `monitor_position(entry_at=...)` + `Executor.resume_open_position()` + `_ExecutorLike` Protocol-Erweiterung + WINDOW-Zweig im Runner. +5 P5-Tests + 2 P8-Tests.
- **B-6, B-7, B-8, B-9, B-10** in Plan §6.
- **Block C (LLM-Austausch)** wartet auf OpenCode + z.ai-Fleet-„bereit"-Meldung (Plan §14.8). Heute nicht blockierend (MiniMax-Fallback läuft).
- **Datenreparatur der 3 730 alten `source='ig'`-Bars** (Plan T14) folgt erst in **E-3** zusammen mit dem Scheduler-Restart; bis dahin bleibt der DB-Zustand mit den +2-h-Bars stehen.

### B-2 Σ-Steigerung (2026-10-19, Plan §6 Kommandoform)

| Suite | grün (nach B-1) | grün (nach B-2) | Δ |
|---|---:|---:|---:|
| P1 broker_wrapper | 98 | 98 | — |
| P2 persistence | 82 | 82 | — |
| P3 external_data | 108 | 108 | — |
| P4 research | 163 | 163 | — |
| P5 execution | 190 | 190 | — |
| P6 debate | 76 | 76 | — |
| P7 reward | 170 | 170 | — |
| **P8 scheduler** | 261 (1 alt Warning) | **263** | **+2** |
| P9 universe | 95 | 95 | — |
| P10 v3 | 165 | 165 | — |
| **P12 data_foundation** | 149 | **153** | **+4** |
| P13 live_data | 85 | 85 | — |
| P14 discovery | 61 | 61 | — |
| P15 v4 | 126 | 126 | — |
| P16 activation | 15 | 15 | — |
| root `tests/` | 121 | 121 | — |
| **Σ 16 Suites** | **1965** | **1971** | **+6** |
| meta_m1 (informativ, nicht in Σ) | 28 | 28 | — |

### Open questions / blockers
- **Scheduler ist gestoppt** (`is-active=failed`). Vor E-3 muss er wieder hochfahren — der Recorder muss dann mit dem Klonen-Bar-Löschen (Plan T14, `DELETE FROM bars WHERE source='ig'`) zusammen laufen, weil sonst `bars.sqlite is locked` (Plan §8 Fehlgriff). Bis zum E-3 wird die alte IG-Historie (3 730 Bars mit `ts_utc` +2h in der Zukunft) NICHT angerührt; das ist **gewollt** und **kein Datenverlust**, weil der Fix in `ig_adapter.py:909` wirkt und neue Bars korrekt schreibt.
- **Fleet §14.8 (OpenCode + z.ai)** weiterhin offen. Heute nicht blockierend.
- **C-1-Step `check_llm_profile`** wird um `/coding/`-Endpoint-Check erweitert (Plan §14.1, +1 P8-Test) — gehört zu Block C, nicht zu A/B.

### Session-end-Hinweis (für die Exec-Session selbst)
- **Plan-AK-Stand nach dieser Session:** Session #1 ✅ AK1-AK4 + Session #2 ✅ neu: AK-Block-B Sweep **+6** (P12 +4 + P8 +2 = Plan-Ziel exakt erreicht). B-2 ist Plan-AK für Phase-12-Step-6 (Divergenz-Sampler, D2). Σ 1971 — Block-B Sweep-Ziel ≥ 1992 ist noch **21 Tests entfernt** (B-3..B-10 verbleibend).
- **K11-Anker (Shakedown):** das neue `divergence_ok`-Event ist genau die Append-Only-Quelle für K11 (`evaluate_k11(health_jsonl, from_day, to_day)`: jeder Handelstag ≥ 1 Event `divergence_ok`/`quote_divergence`). Ohne B-2 wäre K11 strukturell unerreichbar — die alte Rechnung produzierte entweder `quote_divergence` (falsche Horizonte ⇒ falsche-positive) oder `divergence_no_comparator` (still, nicht „vergleichbar").
- B-2 lokal ahead, wartet auf Nikinger-Push.

### Next start (für die Folgesession, kalt einsteigen ohne Neu-Lesen)

**B-3 Promotion-Bridge (D3, P15 + P8).** Anker: `phase15_v4/instinct/bridge.py:131-132`, `:146-148`, `:167-168`, Docstrings `:22-25` + `:177`. Drei Nahtfehler:
1. `validate()` bekommt kein `trades` (Parameter `trades_n=500` reserviert, Docstring Z. 91–95 → #541 ergänzen).
2. `decision.decision` statt `decision.value` (Plan §6 B-3 §2).
3. `evidence_trade_ids_json` / `contradictions_trade_ids_json` (Keys mit `_json`) → aktuell NULL-INSERTs auf 29/29 Zeilen.
+ Contract-Test mit echter `persistence.Database` (Stub reichte nicht), +2 P15-Tests + 1 P8-Test. Eigener Extractor-Client (`max_tokens=2048`, `timeout_s=60`).
Block-B Σ-Ziel ≥ 1992 noch 21 Tests entfernt nach B-3 (B-3 = +3, Σ 1974).
Scheduler bleibt gestoppt (B-0). Push = Nikinger. Block C wartet auf OpenCode-Fleet-„bereit"-Meldung.

---

## Session stopped — 2026-10-19 (Exec-Session #1 ENDE — Block A + B-0 + B-1, 4 Commits, Σ 1964 + 1 P1-Test = **1965** grün; Scheduler gestoppt + 3 Units laufen weiter; Nikinger-Freigabe zur Beendigung)

> **Auftrag:** Nikinger 2026-10-19 ~16:20 Berlin: „GLM in OpenCode ist im anderen Projekt als nicht fähig genug getestet — du führst als Fallback (MiniMax-M3) aus. Plan bleibt Plan, aber warte nach jedem Schritt auf meine Freigabe." Drei Commits später (~17:30) wurde die Freigabe erweitert: „Das sind eigentlich Aktionen, die auch du ausführen könntest - tue das" → Exec-Session übernahm Push + Scheduler-Stopp + IG-Probe + B-1-Edit. Abschluss mit „Session an dieser Stelle korrekt beenden, commit, push".
>
> **Executor-Modus:** MiniMax-M3-Fallback (Plan §14.2). `~/.config/opencode/`, `~/.local/share/opencode/auth.json`, `opencode.service` wurden **nicht angefasst** — verifiziert (auth.json: `zai-coding-plan`/`google`/`minimax`/`nvidia`; `zai-coding-plan` läuft seit heute 16:19:54 als OpenCode-Provider, **Bot nutzt ihn nie** — Plan §14.3).

### Completed — diese Exec-Session (4 Commits in `phase17_testbed/CLAUDE.md`)

| # | Commit | Step(s) | Inhalt |
|---|---|---|---|
| 1 | `2c7b9c1` | A-0 + A-1 + A-2 | SESSIONS_ARCHIVE rotiert + Hook-Liste erweitert + Step-0-Ritual No-Op + Σ-Baseline 1964 |
| 2 | `a5d08cd` | A-3 | Code↔.md-Sweep: README/ARCHITECTURE/ROADMAP/ROADMAP_ARCHIVE/CLAUDE/INDEX + PHASE16-Handover Reboot-Vermerk |
| 3 | `2675129` | B-1 | `ig_adapter.py:909` UTC-first + `test_parse_bar_prefers_snapshot_time_utc_over_local_snapshot_time`; P1 97→98 |
| (Push) | `git push -u origin main` | A-Push | Block A (`b3fccc9..a5d08cd`) auf `origin/main` — vor B-1 ausgeführt; B-1 (`2675129`) wurde gegen `origin/main` (~a5d08cd) committed |

**B-0 (gestoppt + IG-Probe, 2026-10-19 selbst ausgeführt):**
- `systemctl --user stop tradingbot-scheduler.service`: Status `is-active=failed` (Plan D13, 90-s-Stop-Timeout hat SIGKILL-Pfad genommen — erwartet). Recorder/Discovery/WebUI laufen weiter (alle 3 `is-active=active`).
- IG-Probe gegen `IX.D.DAX.IFMM.IP` MINUTE_5 bei gestopptem Scheduler (1 Datenpunkt, Allowance 8 194/10 000 nach Probe):
  - `snapshotTime     = '2026/10/19 17:35:00'` (Ortszeit Europe/Berlin CEST+2)
  - `snapshotTimeUTC  = '2026-10-19T15:35:00'` (UTC ISO, korrekt)
  - Δ = 2 h exakt CEST (heute 2026-10-19, **vor** DST-Wechsel 2026-10-25) → **Plan §B-1** (UTC-first), nicht B-1b (Fallback Europe/Berlin→UTC). Verifiziert §9 Nr. 1.
- Push Block A (`git push -u origin main`): `b3fccc9..a5d08cd main -> main` ✓.

**B-1 — IG-UTC-first** (`2675129`):
- Edit: `phase1_broker_wrapper/broker_wrapper/adapters/ig_adapter.py:909` `p.get("snapshotTime") or p.get("snapshotTimeUTC", "")` → `p.get("snapshotTimeUTC") or p.get("snapshotTime", "")` mit Kommentar D1 (Plan §A-3 verbatim — 4 Zeilen).
- Test: `tests/test_ig_adapter.py::test_parse_bar_prefers_snapshot_time_utc_over_local_snapshot_time` — 3 Fixtures (beide Felder / nur `snapshotTime` / nur `snapshotTimeUTC`); legt explizit fest, dass UTC ISO verlustfrei übernommen wird, während `snapshotTime` als Legacy-Fallback grün bleibt.
- `pytest phase1_broker_wrapper/tests` → **98 grün** (97 + 1 = AK-Block-B Sweep +1 erreicht). Σ-Baseline-Steigerung: 1964 → **1965**.

### Next (geplante Folgesessions, in Priorität)
- **B-2 Divergenz-Sampler (D2, P12 + P8).** `heartbeat.py:228-251` `compute_return_divergence` (5-min-gegen-1-min-Rechenfehler) → neue `window_return_divergence` (abgeschlossener 5m-Bar, ≥ 25 min alt vs. yF-1m-Bars desselben Fensters, ≥ 4 von 5). `DivergenceSampler.sample_epic` Rumpf von Z. 311–371 ersetzt: erst Vergleich, dann Throttle, explizites `divergence_ok`-Event. P8 `_sampler_due(now, config)` (WINDOW + ≥ 40 min nach Öffnung). +4 P12-Tests + 2 P8-Tests. AK ≥ 1992 nach Block-B-Sweep.
- **B-3 Promotion-Bridge (D3, P15 + P8).** 3 Nahtfehler (validate ohne trades, .value statt .decision, Keys ohne _json → 29/29 NULL) + Contract-Test mit echter `persistence.Database`. Eigener Extractor-Client (`max_tokens=2048`, `timeout_s=60`). +2 P15-Tests + 1 P8-Test.
- **B-4 Abschneiden sichtbar (D4, P4).** `_attempt`: Meter **vor** Parse; `stop_reason=="max_tokens"` / `finish_reason=="length"` → `LLMResponseError` ohne Retry. +4 P4-Tests.
- **B-5 Monitor-Re-Adoption (D5, T8, P5 + P8).** `monitor_position(entry_at=...)` + `Executor.resume_open_position()` + `_ExecutorLike` Protocol-Erweiterung + WINDOW-Zweig im Runner. +5 P5-Tests + 2 P8-Tests.
- **B-6, B-7, B-8, B-9, B-10** in Plan §6.
- **Block C (LLM-Austausch)** wartet auf OpenCode + z.ai-Fleet-„bereit"-Meldung (Plan §14.8). Heute nicht blockierend (MiniMax-Fallback läuft).
- **Datenreparatur der 3 730 alten `source='ig'`-Bars** (Plan T14) folgt erst in **E-3** zusammen mit dem Scheduler-Restart; bis dahin bleibt der DB-Zustand mit den +2-h-Bars stehen, der Fix in `ig_adapter.py:909` wirkt erst für **neue** IG-Bars ab dem nächsten Scheduler-Start.

### Step-0-Ritual (A-1, 2026-10-19 selbst gemessen)

| Token | Befehl | Treffer | Bewertung |
|---|---|---:|---|
| `turbo` (case-insensitive) | `grep -rni "turbo" --include="*.py" --include="*.sql" --include="*.sh" . --exclude-dir=.venv \| grep -v "/.venv/"` | **20** in 13 Dateien | ✅ alle sind der eingefrorene Legacy-Name `turbo_candidates.json`; einzige andere Zeile = Schutzkommentar `phase2_persistence/persistence/state.py:27` („Do NOT rename") |
| `EPIC_MAP` | `grep -rn "EPIC_MAP" --include="*.py" . --exclude-dir=.venv` | **3** | ✅ Phase-14-Doku-Kommentare (`test_store.py:239`, `models.py:121`, `store.py:194`) |
| Quellen | Phase-16-Closeout §3.1 (`PHASE16_CLOSEOUT_HANDOVER.md`) + Phase-17-Plan §2.7 (Stand 2026-10-17) | identisch | No-Op, 7. Mal |

### A-2 Σ-Baseline + B-1 Σ-Steigerung (2026-10-19, Plan §6 Kommandoform + Block-B Sweep Stand)

| Suite | grün (vor B-1) | grün (nach B-1) | Δ |
|---|---:|---:|---:|
| **P1 broker_wrapper** | 97 | **98** | **+1** |
| P2 persistence | 82 | 82 | — |
| P3 external_data | 108 | 108 | — |
| P4 research | 163 | 163 | — |
| P5 execution | 190 | 190 | — |
| P6 debate | 76 | 76 | — |
| P7 reward | 170 | 170 | — |
| P8 scheduler | 261 (1 alt Warning) | 261 | — |
| P9 universe | 95 | 95 | — |
| P10 v3 | 165 | 165 | — |
| P12 data_foundation | 149 | 149 | — |
| P13 live_data | 85 | 85 | — |
| P14 discovery | 61 | 61 | — |
| P15 v4 | 126 | 126 | — |
| **P16 activation** | 15 | 15 | — |
| root `tests/` | 121 | 121 | — |
| **Σ 16 Suites** | **1964** | **1965** | **+1** |
| meta_m1 (informativ, nicht in Σ) | 28 | 28 | — |

### Open questions / blockers
- **Scheduler ist gestoppt** (`is-active=failed`). Vor E-3 muss er wieder hochfahren — der Recorder muss dann mit dem Klonen-Bar-Löschen (Plan T14, `DELETE FROM bars WHERE source='ig'`) zusammen laufen, weil sonst `bars.sqlite is locked` (Plan §8 Fehlgriff). Bis zum E-3 wird die alte IG-Historie (3 730 Bars mit `ts_utc` +2h in der Zukunft) NICHT angerührt; das ist **gewollt** und **kein Datenverlust**, weil der Fix in `ig_adapter.py:909` wirkt und neue Bars korrekt schreibt.
- **Fleet §14.8 (OpenCode + z.ai)** weiterhin offen. Heute nicht blockierend. Sollte die Fleet doch „bereit" melden, baut eine Folge-Session §14-Pfad auf mit C-7-Familien-Smoke vor jedem Flip-Commit.
- **C-1-Step `check_llm_profile`** wird um `/coding/`-Endpoint-Check erweitert (Plan §14.1, +1 P8-Test) — gehört zu Block C, nicht zu A/B.

### Session-end-Hinweis (für die Exec-Session selbst)
- 4 Commits in `phase17_testbed/CLAUDE.md` Update-Zeile zusammengefasst (siehe oben).
- Phase-16 Block A bereits auf `origin/main`. Phase-17 B-1 (`2675129`) **lokal ahead**, wartet auf Nikinger-Push.
- **Plan-AK-Stand nach dieser Session:** AK1 ✅ (Step-0-Ritual), AK2 ✅ (Σ 1964 → 1965, keine Regression), AK3 ✅ (ROADMAP.md < 40 KB, root CLAUDE.md < 25 KB, PHASE16-Handover Reboot-Vermerk), **AK4 ✅ (IG-Probe dokumentiert + `_parse_bar` bevorzugt `snapshotTimeUTC`)** + **+1 P1-Test grün** (Datenreparatur E-3 ausstehend). Block-B Sweep-Σ noch **27 Tests entfernt vom Plan-Ziel ≥ 1992**.

---

## Session stopped — 2026-10-18 (Plan-Session, Opus 5.5 — begonnen 2026-10-17; Phase 17 eröffnet, Plan committet + gepusht)

> **Auftrag:** Nikinger 2026-10-17. „Du bist der Phase-17-Chat — die Planungssession." Fragen gebündelt in zwei Runden (F1–F12, F13–F14), danach den ausführungsreifen Plan für Sonnet 5 schreiben und committen. Push = Nikinger.

### Completed
- **Plan** [`../docs/concepts/phase17_testbed_plan.md`](../docs/concepts/phase17_testbed_plan.md) (📕). Er enthält:
  - T1–T24 gelockt, je mit Begründung;
  - §2 selbst gemessene Fakten (Baseline, Git/Units/Journal, Live-DB, `bars.sqlite`, `llm_usage.json`, Health-Events, Funktions-Inventar, Doku-Drift);
  - D1–D13 Befunde mit Datei:Zeile;
  - Blöcke A–E mit verbatim Ankern;
  - AK1–AK21;
  - §8 Fehlgriffe;
  - §9 Verify-Liste (14 Punkte).
- **Σ 1964 grün** selbst gemessen (16 Suites einzeln, meta 28) — identisch zum Phase-16-Closeout.
- **Neu gemessene stille Totalausfälle**, alle drei jetzt Plan-Steps:
  - (1) IG-REST-Bars +2 h in der Zukunft (`ig_adapter.py:909` `snapshotTime` = Ortszeit). Preisbeweis: IG „09:00Z" = LS 07:04Z = 49 663,2.
  - (2) Divergenz-Sampler 233/233 `no_comparator` seit 08-25. Dazu ein Rechenfehler: 5-min- gegen 1-min-Renditen.
  - (3) `decision_context.abstain_record_id` 3 669/3 669 NULL (`wiring.py:758-760` verwirft den Rückgabewert).
- **Bridge-Befund erweitert:** drei Nahtfehler statt einem (`validate` ohne `trades`, `.value` statt `.decision`, Keys ohne `_json` → 29/29 Evidence NULL).
- **„Unbekannte" Phase-16-Stopps aufgeklärt:** VM-Reboots, plus SIGKILL nach dem 90-s-Stop-Timeout (Journal). Nikinger: Reboots vom VM-Host.
- **Nikinger-Entscheidungen** F1–F14 eingearbeitet (Plan §1).
- **Advisor zweimal** — vor dem Ansatz und vor „fertig". Die sieben Punkte des zweiten Reviews stehen im Folge-Commit (Plan §13): Flip-2-Tag vorregistriert, Modell-ID-Drift prüft der Start, Verbatim-Anker ergänzt.
- **Plan-Nachtrag §14 (2026-10-18, Nikinger):** Executor-Test GLM in OpenCode (Claude Code bleibt Anthropic-only; Review-Gate vor E-3; Rückfallregel; 5.2-Quirk), Bot-Provider z.ai mit Pay-per-use statt MiniMax M3. Belege aus der z.ai Usage Policy, dem Coding Plan nur für unterstützte Tools, und dem OpenCode-Katalog `~/.cache/opencode/models.json` mit Modellen, Endpoints und Preisen. `opencode.json` bleibt unverändert.
- **Plan §14.8 (2026-10-18):** Die Executor-Integration übernimmt eurofyx-fleet, getrennt vom Plan. Die Fakten, die die Fleet braucht, stehen in §14.8 (Katalog, Provider-ID, Endpoint, Modelle, Service-Hinweis).
- **Plan-Step A-4 ist schon in dieser Session erledigt** (Nikinger-Freigabe 2026-10-17):
  - Push `be15cf9..399a9df` nach `origin/main`; das nimmt `e19c178` mit.
  - `sunshine_2026.906.222525-1+ubuntu24.04_amd64.deb` aus dem Repo-Root nach `~/Downloads/` **verschoben**, nicht gelöscht. Sunshine selbst bleibt per `dpkg` installiert (`install ok installed`) und läuft als `/usr/bin/sunshine`.
  - Exec-Session: A-4 nur noch als ✅ abhaken. Die A-Commits pusht wie üblich der Nikinger.

### Next
- **eurofyx-fleet (Nikinger):** die Executor-Integration nach Plan §14.8 (OpenCode + `zai-coding-plan`), danach die Meldung „bereit".
- **Exec-Session #1 (OpenCode, `zai-coding-plan/glm-5.3-flash`, Plan §14):** startet **nach** der Fleet-Meldung mit Plan **A-0** (zuerst §14 lesen):
  - diesen Block wortgleich nach `SESSIONS_ARCHIVE.md` (NEU) rotieren;
  - `scripts/check_doc_rotation.py:88` um `"phase17_testbed",` ergänzen;
  - danach A-1 (Step-0-Ritual), A-2 (Baseline), A-3 (Doku-Sweep).

### Open questions / blockers
- Keine Planungsfragen offen.
- **Blocker für den Exec-Start:** die Fleet-Integration nach Plan §14.8 (OpenCode + `zai-coding-plan`).
- Offen, aber erst in der Ausführung messbar (Plan §9 + §14.6): IG `snapshotTimeUTC` (Probe B-0) sowie für den Bot der z.ai-Pay-per-use-Endpoint, Key, Preise, Reasoning-Tokens gegen `max_tokens`, `response_format` (Familien-Smoke C-7). Für den Executor: Kontingent-Verbrauch je GLM-Modell (Basis des 5.2-Quirks).
