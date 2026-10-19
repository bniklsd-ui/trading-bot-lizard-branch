---
status: live
purpose: Phase 15–17 build plan + compact summary of phases 1–14 (links to ROADMAP_ARCHIVE.md)
read-when: planning a phase transition or checking what an active phase covers — closed phases live in ROADMAP_ARCHIVE.md
detail: L2
up: CLAUDE.md
down:
  - docs/concepts/          # one snapshot concept/plan per phase
  - ROADMAP_ARCHIVE.md      # 📦 Phases 1–8 verbatim archive (closed, A-5 2026-08-31)
updated: 2026-10-19 (A-3 sweep — Phasen 9–14 nach ROADMAP_ARCHIVE.md rotiert + 6 Summary-Zeilen ergänzt + neuer Phase-17-Abschnitt; ROADMAP.md < 40 000 B)
---
# Roadmap

The build order is **strict**. Each phase depends on the previous one being
testable and stable. No skipping ahead.

> Rule: Each phase must be fully testable before the next begins.
> After Phase 1: manual trades work. After Phase 5: first automated trade.
> After Phase 7: bot learns. Everything after that is optimization.

> ⚠ **Doc-reconciliation 2026-06-30:** Eine frühere Drive-Version dieser Datei war
> inkonsistent (Phasen 1/3/4 auf altem „ungetestet/to-be-created"-Stand zurückgefallen,
> obwohl längst ✅ live-verifiziert). Diese Fassung führt die Phasen 1–7 wieder korrekt
> und ergänzt Phase 8 (halber Abschluss) + Phase 9 (9f Instinct-ECC).
>
> ⟳ **Doc-Rotation 2026-08-31 (Phase-15 A-5, MiniMax-M3-Exec-Session):** Phasen 1–8 sind
> seit 2026-07-03 abgeschlossen + live-verifiziert. Die ausführlichen Per-Phase-Beschreibungen
> wurden **verbatim** nach `ROADMAP_ARCHIVE.md` rotiert (analog der `SESSIONS_ARCHIVE.md`-
> Konvention aus `CLAUDE.md`); ROADMAP.md trägt jetzt nur die kompakte Summary-Tabelle +
> Link. Der Pre-Rotation-Stand ist im Header der `ROADMAP_ARCHIVE.md` referenziert.

---

## Phasen 1–14 → [ROADMAP_ARCHIVE.md](./ROADMAP_ARCHIVE.md) (archiviert; 9 formal offen, 11 deferred)

Die Phasen 1–14 sind seit 2026-08-31 (Phase-15-A-5, für Phasen 1–8) bzw. 2026-10-19 (Phase-17-A-3, für Phasen 9–14) im Archiv-Pfad der `ROADMAP.md` zusammengefasst. **Phase 9** ist **formell noch offen** (Code produktiv seit 2026-07-06, kein formaler Closeout — Nikinger-Entscheidung §10 des Phase-17-Plans); **Phase 11** ist 🛑 **DEFERRED** (Notbremse 2026-08-11, Datenfundament hat Vorrang). Die detaillierten Per-Phase-Beschreibungen (Goal, Done-When, Mission, Status, Hotfix-Tracks, Concept-Links, v1.5/v1.6/v1.7-Arc) sind **verbatim** in [`ROADMAP_ARCHIVE.md`](./ROADMAP_ARCHIVE.md) archiviert (Rotation 2026-10-19 für Phasen 9–14, 2026-08-31 für Phasen 1–8; Auditability-Regel: wortgleich, unverändert — selbe Regel wie bei `docs/sessions/root_claude_md_phase_status_archive.md`).

| Phase | Goal (Kurzform) | Stand |
|---|---|---|
| 1 — Broker API Wrapper | Unified Python-Interface für Broker + Envelope-JSON | ✅ live-verifiziert (2026-05-21) |
| 2 — Persistenz | SQLite + JSON, TTL, Migrationen | ✅ live-verifiziert (2026-05-22) |
| 3 — External Data (yFinance) | Drift, History, Volume-Anomalie, Momentum-Kontext | ✅ live-verifiziert (2026-06-02) |
| 4 — research.py + LLM | AI-Pick aus code-vorbereiteten Daten | ✅ live-getestet (2026-06-09) |
| 5 — ig_bot Gates 1–5 | Erster End-to-End-Execution-Pfad (manuell) | ✅ live-verifiziert (2026-06-12) |
| 6 — Bull/Bear/Judge Debate | Adversarial early-stop debate; AI nur Bull/Bear + Judge | ✅ live-verifiziert (2026-06-16) |
| 7 — Reward/Brain | Prozess-bewusster Score + Lessons + observe-only Confidence | ✅ live-verifiziert (2026-06-26, gepusht) |
| 8 — Scheduler | Autonome Demo-Trade-Generierung + Safety-Breaker | ✅ live-verifiziert (2026-07-03) — zwei autonome Trades + ein auslösender Safety-Breaker (Token-Budget) |
| 9 — V2: Foundation | Autonome Epic-Research (DB-Picks) + Daten-Input-Zuverlässigkeit | 🔄 in Arbeit seit 2026-07-07 — Code produktiv, formeller Closeout ausstehend (Nikinger) |
| 10 — V3: Persistenz-Reform + No-Trade-Lessons | Migration 005, `abstain_lessons/`, Paper-Trades | ✅ abgeschlossen Closeout 2026-08-25 (Σ 1698, 25 phase10_v3-Commits auf main) |
| 11 — V3-Fortsetzung: Funnel-/Mess-Fixes | Aus der zweiten Datenwoche-Review | 🛑 DEFERRED (Notbremse 2026-08-11) — drei Datenwochen an drei Infrastruktur-Ausfällen gescheitert |
| 12 — Datenfundament | Registry + BarService + Bar-Archiv + Recorder | ✅ abgeschlossen Closeout 2026-08-25 (Σ 1698, 143 Tests; P12.5 CLOSED + GESCHEITERT) |
| 13 — Live-Datenfundament | 4-stufige Beschaffung (LS → yF → Fremdquelle → IG-Rettung) | ✅ abgeschlossen Closeout 2026-08-31 Session 18 (Σ 1703, 74 Tests) |
| 14 — Discovery-Then-Deterministic | `instrument_source_availability` + autonomer Daemon | ✅ abgeschlossen Closeout 2026-08-31 Session 23 (Σ 1703, 61 Tests, D5 freigegeben) |

**Volle Phase-Beschreibungen:** [`ROADMAP_ARCHIVE.md`](./ROADMAP_ARCHIVE.md).


---

## Phase 15 — V4: Sophisticated / Optional *(die alte Phase 9, deferred; vormals "Phase 12",
dann "Phase 13", dann "Phase 14", jetzt Phase 15 — umnummeriert 2026-08-11, 2026-08-18 und 2026-08-22)*

> **Status: ✅ ABGESCHLOSSEN am 2026-09-05 (Session #13, MiniMax-M3-Exec)** — Closeout-Handover [`phase15_v4/PHASE15_CLOSEOUT_HANDOVER.md`](../phase15_v4/PHASE15_CLOSEOUT_HANDOVER.md), Bild [`docs/architecture/phase15_closeout.svg`](../docs/architecture/phase15_closeout.svg). Pattern-Vergleich zu Phase-12/13/14. **4 Blöcke alle ✅**: A (Haushalt) endgültig · B (Reward-Kalibrierung) live-validiert (Score 78,72 → 50,00) · C (Instinct-ECC) code-complete, heute bit-identical via VETO-5-leere-Regelliste (AK9) · D (Erbstücke + Folgefix Variante C) endgültig. **Σ 1843 grün repo-weit**. 18 Commits gepusht, 6 Commits lokal ahead (Push-Freigabe ausstehend). **Offen (alle nicht-Phase-15-Blocker):** Promotion-Bridge (Plan §10), Ledger-Restore (250 Punkte, Nikinger-Aktion), Live-DB Migration 008+009 (nicht automatisch — Phase 16 B1/B2, korrigiert 2026-09-05 → Phase-16-Plan §3 L3), Gate P7/A6 (wartet auf nächsten OPEN-Trade).
> 🟡 *Nachtrag 2026-10-16 (Phase-16-Closeout):* von den „Offen"-Punkten sind Ledger-Restore und Migration 008+009 erledigt; die Promotion-Bridge ist gebaut (Phase 16 D2), live aber tot (`bridge.py:146`); Gate P7/A6 ist gemessen (deal-bezogene CRITICALs max 2 je Trade) — Öffnen = Entscheidung E6 im [Phase-16-Handover](./phase16_activation/PHASE16_CLOSEOUT_HANDOVER.md).
>
> Phasenkopf: [`phase15_v4/CLAUDE.md`](../phase15_v4/CLAUDE.md). Plan: [`docs/concepts/phase15_v4_plan.md`](./docs/concepts/phase15_v4_plan.md) (P1–P16, AK1–AK14, 📕).

**Goal:** Implement the V2 improvements identified in the Council analysis.

### 15a — Council Skill Integration *(vormals 9a / 11a / 12a / 13a / 14a)* — **zurückgestellt**
- [ ] Integrate `verbesserungsvorschlaege` as structured input to pipeline — *Nikinger-Entscheidung 2026-08-31 Runde 1 (Plan §10): Council-Use-Case ist in Phase 10 (V3) gebaut, `default=False` (Phase-10-Closeout 2026-08-25). **Out-of-scope für Phase 15**.*
- [ ] Trigger detection for ad-hoc strategy evaluation — *siehe oben.*

### 15b — Handover-Logik (Bull/Bear/Judge) *(vormals 9b / 11b / 12b / 13b / 14b)* — **abgeschlossen**
- [x] Context-window monitoring during debate (~60–70 %) — *korrigiert 2026-08-31: Schwellwert-Mechanismus gebaut, `phase6_debate/debate/debate.py:172`. Live-Verhalten nicht verifiziert (Plan §9 #4).*
- [x] Compression of Bull/Bear/Judge state into summary — *korrigiert 2026-08-31: deterministischer Compression-Latch, `phase6_debate/debate/debate.py:187-195`.*
- [ ] New session continuation — *korrigiert 2026-08-31: **gegenstandslos** — durch laufende Compression ersetzt.*

### 15c — Reward/Punishment Reform *(vormals 9d / 11c / 12c / 13c / 14c)* — **abgeschlossen mit Block B (live-validiert)**
- [x] `+ process_quality_score` (VETOs, confidence, debate quality, gate path) — *korrigiert 2026-08-31: „VETOs"/„gate path" gegenstandslos (Plan P4); „confidence"/„debate quality" gebaut (`phase7_reward/reward/scorer.py:122-131`). 2/4 Sub-Signale „partial".*
- [x] Anti-emotionality: separate process score from outcome score — *korrigiert 2026-08-31: strukturell getrennt seit Phase 7, `phase7_reward/reward/scorer.py:114-133`. **Block B (Plan P1/P2)**: `process_weight` 1.5 → 0.5 (AK5), `--apply` 2026-09-03 Score 78,72 → 50,00 live (AK6).*

### 15d — Force Trigger Safeguard *(vormals 9e / 11d / 12d / 13d / 14d)* — **gegenstandslos bestätigt**
- [ ] Lock force trigger when daily PNL < 0 — *korrigiert 2026-08-31: **gegenstandslos** — kein Force-Trigger existiert (`grep` zeigt nur 3 Schema/Test-Treffer, kein Code-Pfad). CLAUDE.md Hard Rule 5 bleibt wörtlich stehen.*

### 15e — Instinct-Promotion (ECC) + Longterm VETO *(vormals 9f / 11e / 12e / 13e / 14e, aus Phase 7 hierher verschoben)* — **abgeschlossen mit Block C (strukturell zu, Promotion-Pipeline offen)**
- [x] AI extrahiert strukturierte Instincts — *Session #11 Block C Step C2: `phase15_v4/instinct/extractor.py` (`SingleShotInstinctExtractor`, LLM, best-effort, eigenes `_LLMClientLike`-Protocol, 22 Tests).*
- [x] Code validiert + promotet — *Sessions #11 + #12 Block C Steps C2 + C3: `validator.py` (deterministisch, AK8 triple-pin) + `promotion.py` (Doppel-Sperre, AK7) + `vetos.py:206-228` (VETO 5, AK9 bit-identical-to-today). `instincts`-Tabelle in Migration 009.*
- [ ] **Harte Leitplanke:** Promotion in die VETO-Schicht — *Strukturelle Antwort steht; die **Pipeline** `list_instincts(status='validated')` → `promote_eligible(...)` → `longterm_rules`-Befüllung **existiert noch nicht** (Plan §10 out-of-scope). Heute n=8 < n_min=50: Promotion returnt `[]`, VETO 5 ist No-Op. **Bewusst offen** für Phase 15.5 / 16.*

**Done when (Phase 15, alle 4 Blöcke + ROADMAP 15a–15e):** **✅ erreicht am 2026-09-05.** 15a zurückgestellt · 15b strukturell zu · 15c vollständig zu (live-validiert) · 15d gegenstandslos · 15e strukturell zu, **Pipeline offen** für Promotion-Bridge (Plan §10).

**Directory:** `phase15_v4/` (erstellt 2026-08-31 mit `instinct/` Package + `tests/` + `scripts/`).

---

## Phase 16 — Freischaltung *(eröffnet 2026-09-05, Plan-Session Fable 5.1; abgeschlossen 2026-10-16)*

> **Status: ✅ abgeschlossen mit Teilbilanz (Closeout 2026-10-16, Session #38).** Handover
> [`phase16_activation/PHASE16_CLOSEOUT_HANDOVER.md`](./phase16_activation/PHASE16_CLOSEOUT_HANDOVER.md),
> Bild [`docs/architecture/phase16_activation.svg`](./docs/architecture/phase16_activation.svg). Plan
> [`docs/concepts/phase16_activation_plan.md`](./docs/concepts/phase16_activation_plan.md) (P1–P18, L1–L9,
> Blöcke A–E, AK1–AK17). Phasenkopf: [`phase16_activation/CLAUDE.md`](./phase16_activation/CLAUDE.md).
> 🟡 *Korrigiert 2026-10-16 gegen Code/Git:* die Checkboxen B–E standen seit 09-05 auf offen, obwohl B–D seit
> Sessions #3–#10 im Code sind.

**Goal:** jedes gebaute Feature läuft, jeder Bruch ist zu, ein vorregistrierter 2-Wochen-Lauf
(Demo) beweist Autonomie ohne Hand. Der Bot ist seit 2026-08-31 faktisch tot (100 % Research-
Abstain) — Ursache Infrastruktur, nicht Strategie.

- [x] **A Haushalt** — Ritual, Σ-Baseline 1843, Code↔.md-Sweep, WebUI-Log, Push
- [x] **B Substrat** — Schema-Floor + Operator-Apply (Live-DB v9) + Ledger-Restore; Wochenend-Epics raus
- [x] **C Research-Loop** — 14-Tage-Fenster (Bot handelt wieder) · Breaker-Semantik ✓ · Token-Budget 300 k
  gebaut, **reicht live nicht** (K6 FAIL)
- [x] **D Freischaltung** — vier Arme Default ON ✓ · Bar-Stream-Token-Wrapper ✓ · Margin-Headroom ✓ ·
  Promotion-Bridge gebaut, **live tot** (Validator-Aufruf ohne `trades`)
- [ ] **E 2-Wochen-Autonomie-Test** — Prereg v1–v4 + Report-Skript + Runbook + systemd-Autostart gebaut;
  **kein Lauf PASS** (v1/v2 abgebrochen, v3 FAIL K1/K5/K6, v4 FAIL K6)
- Subphasen unter dem Phase-16-Schirm: **F** (Audit + J-Fixes) ✅ · **R** (Drift #12/#13, Autostart) ✅ ·
  **LLM** (Modellwechsel für K6) nur geplant, kein Code

**Done when:** AK1–AK16 des Plans, insbesondere AK15 — **AK15 nicht erreicht**; Folgearbeit (Token-Budget,
Bridge, Monitor-Re-Adoption, Breaker-Blindfenster, neuer Lauf) siehe Handover §4/§5.

**Directory:** `phase16_activation/`

---

## Meta-Strang (orthogonal, hochzählbar)

> Läuft **quer** zur funktionalen Nummerierung oben (1–11) — keine echte Phase, keine
> Verdrängung von Profit-Arbeit. Eigener Präfix `M`, hochzählbar (M2, M3, …).

### M1 — Harness-Unabhängigkeit (Build-Front) — ✅ CLOSED (2026-07-09)
**Ziel:** vorregistrierte Messung, ob der Bot-Code künftig mit einem offenen Harness
(OpenCode) statt Claude Code gebaut werden kann, plus — unabhängig vom Ausgang — zwei
Feuerlöscher: ein harness-neutraler Kontext-Einstieg (`AGENTS.md`) und ein getesteter, kalter
provider-agnostischer LLM-Fallback für P4/P6. Kein Bot-Feature, kein Umbau der Live-Pfade.

**Ergebnis:** Steps 0–10 alle fertig. 20/20 Trials real gelaufen (kein Budget-Stopp, kein
Isolationsvorfall). `gate_pass_rate` 90%/90%, Gap 0,00pp — **"not distinguishable"** per der
vorregistrierten Rausch-Regel. Regel wörtlich angewandt: **keine Migration** — war bereits vor
der Messung determiniert (E=73,50€ < M=120€), jetzt zusätzlich durch die Messung bestätigt.
`AGENTS.md` auf `main` · `OpenAICompatLLMClient` getestet + Operator-Smoke-PASSed (real gegen
OpenRouter), null Live-Pfad-Diff · alle Regressionen grün · Phase-9-Live-Test zu keinem
Zeitpunkt berührt.

**Verweise:** [`meta_m1_harness/CLAUDE.md`](./meta_m1_harness/CLAUDE.md) (Phasen-Kopf,
geschlossen) · [`meta_m1_harness/META_M1_RESULTS.md`](./meta_m1_harness/META_M1_RESULTS.md) +
[`META_M1_DECISION.md`](./meta_m1_harness/META_M1_DECISION.md) (Zahlen + Entscheidung) ·
[`meta_m1_harness/META_M1_CLOSEOUT_HANDOVER.md`](./meta_m1_harness/META_M1_CLOSEOUT_HANDOVER.md) (Delta zum
Plan + optionaler M2-Vorschlag, ungelockt) · [`docs/concepts/meta_m1_harness_plan.md`](./docs/concepts/meta_m1_harness_plan.md) (Plan,
Steps 0–10) · [`docs/concepts/meta_phase_unabhaengigkeit_konzept.md`](./docs/concepts/meta_phase_unabhaengigkeit_konzept.md) (Hypothese).

---

## Cross-cutting concerns (always)

- **Smoke tests** before any production change
- **No credentials in files** — keyring only
- **No AI for code-doable work** — every reach for AI must be justified
- **Atomic git commits** with clear messages; **Commit ⇒ Note-Update**
- **Phase isolation** — cross-phase imports only through defined contracts / Protocols

---

## Phase 17 — Prüfstand *(eröffnet 2026-10-17, Plan-Session Opus 5.5)*

> **Status: 🔄 in execution seit 2026-10-17.** Plan [`docs/concepts/phase17_testbed_plan.md`](./concepts/phase17_testbed_plan.md) (T1–T24, D1–D13, Blöcke A–E, AK1–AK21, §8 Fehlgriffe, §9 Verify, §14 OpenCode-GLM-Nachtrag 2026-10-18). Phasenkopf [`phase17_testbed/CLAUDE.md`](../phase17_testbed/CLAUDE.md).

**Goal:** *„keine neuen Features — tiefe Härtung des Bestehenden. Jeder vorhandene Arm liefert nachweisbar, was er liefern soll; jeder bekannte Mess- und Geldpfad-Defekt ist zu; das LLM ist pro Rolle austauschbar (Research zuerst auf GLM über die z.ai-API mit Pay-per-use, Plan §14); Report + Vorregistrierung v5 als Fundament für die ausgiebigen Tests."* Repariert 4 Phase-16-PASS-Blocker + 3 neu gemessene stille Totalausfälle (Plan §3 D1–D13).

- [ ] **A Haushalt** — Step-0-Ritual, Σ-Baseline 1964, Code↔.md-Sweep, Push
- [ ] **B Mess- und Geldpfad-Defekte** — IG-Zeitstempel (`snapshotTimeUTC`), Divergenz-Sampler (reale Vergleichsbasis), Promotion-Bridge (3 Nahtfehler + Contract-Test mit echter DB), Abschneiden sichtbar (T20), Monitor-Re-Adoption nach Restart, Breaker Worst-Case (`−initial_risk` für offene Zeilen, NULL fail-closed), Abstain-Naht (`record_id`-Rückgabe), Paper-Logstufen (Rauschen runter), Stop-Timeout (T10), Discovery-Beleg (append-only)
- [ ] **C LLM-Austausch** — `scheduler/llm_profiles.py` (NEU, stdlib-only) + `_build_llm` (eine Bau-Funktion für alle 6+1 Client-Konstruktionen) + `OpenAI-Compat`-Härtung + Preiszeilen GLM-Familie + Key-Skript-Hardening + Familien-Smoke → **Flip 1** (`research_glm` nach Demo-Smoke); **Flip 2** (`all_glm`) gegated durch Nikinger-Go nach Shakedown
- [ ] **D Token-Budget** — Budget-Ausnahme an allen drei Zählstellen (`budget_exempt_models`); Messen + Entscheidung K6-Einheit (Nikinger)
- [ ] **E Test-Fundament** — Report v5 (in-place Erweiterung `--prereg v5`, v4 verdikt-identisch) + Shakedown-Vorregistrierung + Deploy-Sequenz + **2-Tage-Shakedown** (PASS-Reporter mit `--expect-llm-profile research_glm`) + Prereg v5 (10 Handelstage) + Closeout (Handover + SVG + Memory)
- Subphasen-TBD: nichts vorgesehen (Phase-17 ist Atom-Einheit, kein F/R/LLM-Schirm wie Phase 16)
- 🟡 *Nachtrag 2026-10-18 (Plan §14, Nikinger):* Executor-Test GLM in OpenCode (Claude Code bleibt Anthropic-only; Review-Gate vor E-3 = AK22, durch Claude-Code-Session, Schwerpunkte B-5/B-6/C-4/B-3/B-2). Bot-Provider = z.ai Pay-per-use, **nie** der Coding-Plan-Endpoint (`check_llm_profile` lehnt `/coding/` ab). Fleet-Integration (§14.8) läuft getrennt über eurofyx-fleet — diese Exec-Session fasst `~/.config/opencode/`, `auth.json`, `opencode.service` **nicht** an. Aktuell fährt MiniMax-M3-Fallback, weil GLM in OpenCode in einem anderen Projekt als nicht fähig genug getestet wurde (Nikinger 2026-10-19).

**Done-when:** AK19 (Shakedown-Prereg vor E-3-Start committet + Shakedown PASS) + AK20 (Prereg v5 committet, Profil + K6-Einheit gepinnt) — setzt AK1–AK18 voraus + AK21 (Closeout-Handover + Phasenkopf mit genau einem Session-Block + `check_doc_rotation.py --strict` exit 0).

**Directory:** [`phase17_testbed/`](../phase17_testbed/)
