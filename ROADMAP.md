---
status: live
purpose: Phase 9–15 build plan + compact summary of closed phases 1–8 (links to ROADMAP_ARCHIVE.md)
read-when: planning a phase transition or checking what an active phase covers — closed phases live in ROADMAP_ARCHIVE.md
detail: L2
up: CLAUDE.md
down:
  - docs/concepts/          # one snapshot concept/plan per phase
  - ROADMAP_ARCHIVE.md      # 📦 Phases 1–8 verbatim archive (closed, A-5 2026-08-31)
updated: 2026-09-05
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

## Abgeschlossene Phasen (1–8) → [ROADMAP_ARCHIVE.md](./ROADMAP_ARCHIVE.md)

Alle Phasen 1–8 sind seit 2026-07-03 abgeschlossen + live-verifiziert. Die detaillierten
Per-Phase-Beschreibungen (Goal, Done-When, Mission, Status, Hotfix-Tracks, Concept-Links,
v1.5/v1.6/v1.7-Arc) sind **verbatim** in [`ROADMAP_ARCHIVE.md`](./ROADMAP_ARCHIVE.md)
archiviert (Rotation 2026-08-31, Phase-15 A-5; Auditability-Regel: wortgleich, unverändert
— selbe Regel wie bei `docs/sessions/root_claude_md_phase_status_archive.md`).

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

**Volle Phase-Beschreibungen:** [`ROADMAP_ARCHIVE.md`](./ROADMAP_ARCHIVE.md) (~22 KB, alle
Done-When-Checkboxen, Missions, Hotfix-Tracks, Concept-Links verbatim).

---

## Phase 9 — V2: Foundation (Autonome Epic-Research + Daten-Input-Zuverlässigkeit)

> **Status: in Arbeit (Stand 2026-07-07; gekürzt 2026-09-05, Phase-16-Plan-Session — Wortlaut
> bis dahin in `git log -p ROADMAP.md`).** Steps 1–6 + 7a gebaut (7b ohne Fix-Target);
> Live-Baseline-Lauf seit 2026-07-06, Tag 1 end-to-end bewiesen, erster DB-Universum-Pick (CAC).
> Offen: V2-Baseline-Auswertung (echter `open→close`-Trade unter V2 + Variety-These) — seit
> 2026-07-02 acht autonome Trades (id 4–11 CLOSED, davon 4 seit 08-25) und damit faktisch erbracht; `--enable-ig-bars`
> durch Phase-12 `enable_bar_service` abgelöst. Handover:
> [`phase9_universe/PHASE9_V2_LIVE_RESULTS_HANDOVER.md`](./phase9_universe/PHASE9_V2_LIVE_RESULTS_HANDOVER.md) ·
> Plan: [`docs/concepts/phase9_v2_foundation_plan(1).md`](./docs/concepts/phase9_v2_foundation_plan(1).md) ·
> Phase-Head: [`phase9_universe/CLAUDE.md`](./phase9_universe/CLAUDE.md).

**Goal:** die zwei strukturellen Lücken schließen, die den gesamten v1.5→v1.7-Hotfix-Arc
getrieben haben — bevor weitere sophisticated-AI-Arbeit (die alte Phase 9, jetzt Phase 15/V4)
auf einem unzuverlässigen Datenfundament aufbaut.

> **Korrektur (2026-07-08, M1-Housekeeping):** die Checkliste unten stand noch auf `[ ]`,
> obwohl der Status-Block oben + `phase9_universe/CLAUDE.md`s Kontrakt-Tabelle Steps 1–6 + 7a
> längst als ✅ führen — gegen den Code verifiziert (`universe/{discovery,pricing,promotion,
> store,models}.py` existieren, `phase2_persistence/migrations/004_phase9_instrument_universe.sql`
> existiert). Getestetes Verhalten schlägt Doku-Prosa (Working-style-Regel); Boxen unten korrigiert.

### 9a — Autonome Epic-Research (discover → validate → promote)
- [x] `discovery.py` — Seed-Suchbegriff-Sweep + IG `search_markets` + Code-Filter (EUR, Index-CFD,
  TRADEABLE, Kassa-Variante, min size) — kein LLM
- [x] `pricing.py` — deterministischer `point_value`-Resolver (IG-Felder + Namens-/lot_size-Kreuzcheck)
- [x] `promotion.py` — Statusmaschine `discovered → verified → active` voll autonom auf Demo;
  Auto-Demotion (`active → quarantined`) bei wiederholten IG-Verify-Fails
- [x] Migration 004 (`instrument_universe`) + `UniverseStore`; `EXTENDED_UNIVERSE` wird einmaliger
  Seed (`source="curated"`)
- [x] P4 liest das aktive DB-Universum; P8-Runner bekommt eine Universe-Refresh-Naht

### 9b — Daten-Input-Zuverlässigkeit
- [x] `BarProvider`-Kette IG→yFinance + yFinance-Härtung (Backoff, Circuit-Breaker)
- [x] Deterministischer Divergenz-Check (IG-Bar-Close vs. yFinance-Last), gated nichts
- [x] Lightstreamer-Multi-Epic-Diagnose (7a, live 2026-07-06) — **NEGATIV-Befund**, kein Bug,
  kein Fix-Target (7b unblocked-aber-leer)
- [ ] `LiveQuoteCache` in den P4-Research-Kontext verdrahtet — **weiterhin offen**, hing an
  einem 7b-Fix, der mangels Bug nie kam; kein Blocker, re-run erst bei ~10+ aktiven Epics
  (H2-Grenze bei 4 ungeprüft)

**Leitplanke:** kein neues AI im Daten-/Universum-Layer (Discovery-/Promotion-Kriterien sind
100 % code-evaluiert); VETOs/Gates unangetastet; demo-only fail-closed.

**Done when:** mindestens ein net-new Epic durchläuft `discovered → verified → active` ohne
manuellen Code-Edit und erscheint im nächsten Research-Zyklus; ein Safety-Breaker feuert live
(carried-over 5b aus dem v1.5-Plan); STXE/CAC/IBEX-`point_value` wird per Code bestätigt oder
ehrlich quarantänisiert.

**Directory:** `phase9_universe/` *(pkg `universe`)*
**Plan:** [`docs/concepts/phase9_v2_foundation_plan(1).md`](./docs/concepts/phase9_v2_foundation_plan(1).md)

---

## Phase 10 — V3: Persistenz-Reform + No-Trade-Lessons + (optionales) UI

> **Status: ✅ abgeschlossen (Closeout 2026-08-25) — Block A ✅ live auf main seit WE 1
> (2026-07-11, Montag-Restart-Beweis 2026-07-14) + Block B ✅ live auf main seit WE 2
> (2026-07-17) + Bugfix-Block 2026-07-25/31/08-08 + H1 (1 Woche gelaufen) + H4-a.**
> **Council-Paper-Call ✅ gebaut, default `False`, bis auf weiteres in mind Phase 15**
> (Nikinger 2026-08-25). Phase-11-Inhalte (WI-2/W2, H3/H5/H7, B3-Margin-Headroom) bleiben
> offen und gehören in den Datenfundament-Track (Phase 12/13/14) — dort dokumentiert,
> nicht hier. Ausführungsreifer Plan lag
> vor: [`docs/concepts/phase10_v3_plan.md`](./docs/concepts/phase10_v3_plan.md) (Decisions
> V3-D1…D10, Steps 0–11); Kickoff-Kontext:
> [`docs/concepts/PHASE10_V3_KICKOFF_HANDOVER.md`](./docs/concepts/PHASE10_V3_KICKOFF_HANDOVER.md).
> Phase head: [`phase10_v3/CLAUDE.md`](./phase10_v3/CLAUDE.md). Block C (UI) ist explizit
> **nicht** Teil dieses Plans (geparkt, Plan §13) — Abschnitt 10c unten bleibt daher offen.
> ⚠ **2026-07-17 Doku-Fix (code = source of truth):** die 10a/10b-Bullets unten waren seit der
> ursprünglichen Phase-9-Formulierung nicht mehr aktualisiert worden — as-built ist stärker
> (echte `abstain_records`-Taxonomie mit 12 Reasons statt nur der 3 genannten, + eine
> Both-Sides-Shadow-Paper-Pipeline, die im ursprünglichen Text gar nicht vorkam). Bullets unten
> auf den echten Baustand geflippt.

**Goal:** die aktuellen SQLite-V2-Erweiterungen bauen + „warum tradet der Bot nicht" zu einem
lernbaren Signal machen, nicht nur einem verworfenen Reason-Code.

### 10a — SQLite V2 Extensions
- [x] `+ market_regime_snapshots` — Migration 005 (epic-scoped, DROP+CREATE über den
  FK-inkompatiblen P2-Platzhalter), Writer live seit Block B (`market_context/writer.py`);
  observe-only `regime_tag`, degradiert auf `data_source="quote_only"` ohne Bars
- [x] `+ decision_context` — Migration 005, Writer live seit Block B; Bull/Bear-Summary aus
  `DebateOutcome.transcript`, Outcome ∈ `{TRADE, NO_TRADE, ABORT}`
- [ ] `+ lesson_embeddings` (vector store, semantic similarity) — optional/später, V4+

### 10b — No-Trade (Abstain) Lessons
- [x] Eigene `abstain_records`-Tabelle + 12-Reason-Taxonomie (`AbstainReason`,
  `classify_abstain`) — geht über die ursprünglich skizzierten 3 P8-`research_tick`-Reasons
  hinaus (Migration 005, live seit Block A, 318+ reale Zeilen Stand 2026-07-17)
- [x] `reflect_abstain()` (P10, Haiku, best-effort, Tages-Cap) auf `REASON_DEBATE_ABSTAIN`
  erweitert (nicht `reward.brain.reflect()` selbst — eigene, schlankere P10-Reflect-Funktion,
  gleiches Reuse-Muster wie P7); Lessons-Rückspeisung in den P4-Prompt liegt **gebaut, aber
  dunkel** (S6, `include_abstain_lessons=False`, V3-D3 — Aktivierung ist ein separater
  Operator-Schritt nach Lesson-Review, nicht Teil von V3)
- [x] **Zusätzlich (nicht ursprünglich geplant):** Both-Sides-Shadow-Paper-Pipeline
  (`PaperEngine`/`PaperTradeTracker`) — beantwortet "war der Abstain richtig?" für
  `REASON_DEBATE_ABSTAIN`-Fälle deterministisch, ohne Order/Broker-Touch. Council-Paper-Call
  (LLM-Forced-Pick-Variante, `PaperDebateCaller` + additiver Judge-Prompt-Sibling in
  `phase6_debate/`) **✅ gebaut (2026-07-17, Folge-Session)**, hinter Flag
  `enable_paper_debate` (default `False`) — Nikinger flippt, wann gewünscht.

### 10c — UI-Erweiterungen (optional, niedrigere Priorität als 10a/10b)
- [ ] Aufbauend auf dem v1.6-Observability-Log + dem v1.7-DB-gespeisten Status

**Done when:** Abstain-Zyklen erzeugen genauso Lessons wie geschlossene Trades; `decision_context`/
`market_regime_snapshots` sind befüllt statt leer. **Erreicht (2026-07-17)** — live Rows folgen
mit dem nächsten Scheduler-Restart (Nikinger).

**📕 Closeout 2026-08-25:** Phase 10 ist abgeschlossen. Council-Paper-Call-Implementation
bleibt im Code (default `False`) als Eingangs-Schnittstelle für Phase 15 (V4 — Council für
Live-Trades + Handover + Reward-Reform). Vollständiger Handover:
[`phase10_v3/PHASE10_CLOSEOUT_HANDOVER.md`](./phase10_v3/PHASE10_CLOSEOUT_HANDOVER.md),
Bild: [`docs/architecture/phase10_v3.svg`](./docs/architecture/phase10_v3.svg).

**Directory:** [`phase10_v3/`](./phase10_v3/)

---

## Phase 11 — V3-Fortsetzung: Funnel-/Mess-Fixes *(aus der zweiten Datenwoche-Review)*

> **Status: 🛑 DEFERRED seit 2026-08-11 (Notbremse, Nikinger-Entscheidung).** B1/B2/B4/B5 sowie
> H1 und H4-a sind gebaut und liegen auf `main`; **WI-2/W2 — die eine Frage, für die es diese
> Phase gibt — bleibt unbeantwortet.** Drei Datenwochen sind an drei unterschiedlichen
> Infrastruktur-Ausfällen gescheitert, nie an der Messung. Die gemeinsame Wurzel ist wichtiger
> als diese Phase: das **Datenfundament**. Nichts wird zurückgerollt; „deferred" heißt keine
> weitere H-Serie, kein Paper-Trade-Ausbau, kein H1-Scharfschalten, bis das Fundament steht.
> Vollständige Begründung, Durability-Anforderungen (A–G) und offene Entscheidungen:
> [`phase10_v3/PHASE11_DEFERRAL_HANDOVER.md`](./phase10_v3/PHASE11_DEFERRAL_HANDOVER.md),
> Bild: [`docs/architecture/data_foundation.svg`](./docs/architecture/data_foundation.svg).
> **Nummerierung final (Nikinger-Entscheidung 2026-08-11):** „Phase 12 = Datenfundament, V4 →
> Phase 13" (Handover §4.1, ausgeführt in [`docs/concepts/phase12_data_foundation_plan.md`](./docs/concepts/phase12_data_foundation_plan.md) D2).
> Der neue Datenfundament-Track lebt als eigene Phase 12 direkt unter dieser (s. u.); V4 ist
> jetzt **Phase 13** (weiter unten), unverändert im Inhalt, zusätzlich gegatet auf ein
> bestandenes Phase-12-PASS (dieselbe Logik wie diese Notbremse: keine weitere
> AI-Sophistication-Arbeit auf einem unzuverlässigen Datenfundament).
>
> ⟳ **Korrektur (2026-08-18, Nikinger-Entscheidung):** nach dem Scheitern von P12.5 ist
> **Phase 13 = Live-Datenfundament** (der strukturelle Schnitt + vierstufige Beschaffung,
> s. u.); **V4 rutscht auf Phase 14**. Jede „Phase 13 (V4)"-Nennung in älteren Zeilen meint
> jetzt Phase 14.
>
> ⟳ **Korrektur (2026-08-22, Nikinger-Entscheidung):** die "discovery-then-deterministic"-
> Architektur aus Block C des Phase-13-Re-Plans wird **eigene Phase 14** (s. u.); V4 rutscht
> entsprechend auf **Phase 15**. Jede „Phase 14 (V4)"-Nennung in älteren Zeilen meint jetzt
> **Phase 15**. Plan für die Live-Daten-Beschaffung:
> [`docs/concepts/phase13_live_data_plan.md`](./docs/concepts/phase13_live_data_plan.md).
>
> Numbering claimed 2026-08-01 (Nikinger-Entscheidung)
> — vorher stand hier "Phase 11 = V4"; V4 ist jetzt **Phase 13** (unten), unverändert im Inhalt.
> Diese Phase ist **keine** neue AI-Sophistication-Arbeit, sondern das Fix-/Diagnostik-Ergebnis
> der zweiten V3-Datenwoche: [`phase10_v3/DATA_WEEK_REVIEW_2026-07-31.md`](./phase10_v3/DATA_WEEK_REVIEW_2026-07-31.md)
> §4 (Befunde B1-B5) + §5 (Hypothesen H1-H7). **Directory:** lebt vorerst weiter in
> [`phase10_v3/`](./phase10_v3/) (`abstain_lessons/`, `market_context/`) — keine physische
> Verzeichnis-Verschiebung in dieser Session, das ist eine eigene, größere Entscheidung.

**Goal:** die Research-Funnel-/Mess-Probleme beheben, die die zweite V3-Datenwoche aufgedeckt hat
(366 Zyklen → 1 Kandidat → 0 Trades), bevor an der Richtungslogik selbst weitergearbeitet wird.

### 11a — Bugs aus der Datenwoche-2-Review
- [x] **B1** `point_value`-Drift (40× Oversizing auf AEX) — P8-Sizing-Quelle + P5-Fail-closed-Guard
  gefixt (2026-08-01)
- [x] **B2** Reward-Score-Skala (`debate_confidence` 0-100 statt [0,1]) — Skala gefixt
  (2026-08-01); Residuum (**H3**, `clean_exit_bonus` auf Stop-outs) bewusst offen gelassen
- [x] **B5** Paper-/Abstain-Lesson-Prompt/Validator-Zeichengrenzen-Drift — gefixt (2026-08-01)
- [x] **B4 / H6** leeres Mess-Substrat (`abstain_records.detail`/`spread_pct` nie befüllt) —
  gefixt (2026-08-01): `detail` wird jetzt aus dem Executor durchgereicht (+ die
  `Research.last_no_pick_reasoning`-Anreicherung für den dominanten `research_empty`-Fall in der
  P8-Wiring), `spread_pct` an allen drei `_notify_context`-Call-Sites verdrahtet
- [ ] **B3** Leverage-Cap ohne Margin-Headroom — **NICHT gefixt, Design + Prep dokumentiert**
  für eine eigene, größere Session (P1-Adapter-Feld + P5-Gate-4-Änderung, cross-phase; braucht
  zuerst einen Live-Demo-Call gegen `/markets/{epic}`, um IGs echte Margin-Felder zu bestätigen).
  Details: `phase5_execution/CLAUDE.md` B3-Block.

### 11b — H1-H7 (offene Hypothesen, Reihenfolge H2→H1→H6, danach datengetrieben H7/H4/H3/H5)
- [x] **H2** (B1-Anteil) — gefixt, s. 11a. B3-Anteil bleibt offen.
- [x] **H6** — gefixt, s. 11a (B4).
- [ ] **H1** *(größter Hebel, nächste eigene Session)* — Shadow-Pairs zeitgesteuert statt an
  `REASON_DEBATE_ABSTAIN` gekoppelt (neuer Scheduler-Tick + schlanker `PaperEngine`-Einstieg,
  ~130 Paare/Tag, IG-Allowance-Budget einplanen). Beantwortet WI-2 (Sub-Noise-Geometrie-Frage,
  **H7**) an einem Tag statt in Wochen.
- [ ] **H3** — Reward-Loop-Residuum (`clean_exit_bonus` auf Stop-outs) — Designfrage, nach B2.
- [ ] **H4** — Lesson-Sackgasse aufbrechen (Relevanz-Decay, Doppelzählung Lessons/`recent_trades`
  beenden, Lessons skopieren).
- [ ] **H5** — Nachmittag zurückkaufen (Prompt-Caching für Research, `LLMClient(cache_system=True)`
  existiert bereits, wird von Research nicht genutzt).
- [ ] **H7** — Geometrie-Rahmenfrage (30/45-Punkte-DAX-Stops gewinnbar?) — datengetrieben, wartet
  auf H1s Ergebnis.

**Done when:** B1-B5 entschieden (gefixt oder bewusst dokumentiert-deferred, ✅ erreicht
2026-08-01) UND mindestens H1 gebaut + WI-2 beantwortet.

**Directory:** [`phase10_v3/`](./phase10_v3/) *(vorerst — kein Verzeichnis-Split in dieser Session)*

---

## Phase 12 — Datenfundament (Registry + BarService + Bar-Archiv + Recorder)

> **Status: ✅ abgeschlossen (Closeout 2026-08-25) — Steps 0–8.5 auf `main`, 143 Tests grün
> (Stand 2026-08-25), 18 Phase-12-Commits auf `origin/main`.** **Die strukturelle Antwort
> auf das P12.5-Scheitern steht in Phase 13+14** (Nikinger 2026-08-25): der Auflöse-Pfad
> kauft nie wieder Daten — Phase 13 Block A trennte Beschaffung und Verbrauch, Phase 14
> macht Quellen zur Registry-Zeile. **Phase-12-Beweiswoche wird nicht wieder aufgenommen**;
> die Phase-13-Beweiswoche läuft seit Mo 2026-08-25 separat, gegen die Phase-13-Architektur.
> P12.5 wurde 2026-08-18 formal CLOSED + GESCHEITERT — die fünf Code-Edits (U1/U2/U3/U5 +
> Entscheidung B) bleiben **unabhängig korrekt im Repo**. Notbremse aus Phase 11 (oben):
> die gemeinsame Wurzel war strukturell, nicht messbar — durch Phase 13+14 abgelöst.
> Closeout-Handover: [`phase12_data_foundation/PHASE12_CLOSEOUT_HANDOVER.md`](./phase12_data_foundation/PHASE12_CLOSEOUT_HANDOVER.md),
> Bild: [`docs/architecture/phase12_closeout.svg`](./docs/architecture/phase12_closeout.svg).
> As-Built-Analyse: [`PHASE12_5_CLOSEOUT_HANDOVER.md`](./phase12_data_foundation/PHASE12_5_CLOSEOUT_HANDOVER.md),
> Sofort-Befund: [`PHASE12_5_FAILURE_HANDOVER.md`](./phase12_data_foundation/PHASE12_5_FAILURE_HANDOVER.md).
> Plan: [`docs/concepts/phase12_data_foundation_plan.md`](./docs/concepts/phase12_data_foundation_plan.md).
>
> **Tag-1-Live-Auswertung (2026-08-17):** die Kette Resolver → Registry → `measurable_universe()`
> → Recorder/BarService → `bars.sqlite` läuft end-to-end im Echtbetrieb (5 `ok`-Epics, 3 typisiert
> `no_intraday_source`, 1891 Bars an einem Tag, IG-Verbrauch erstmals gemessen: 136/10 000 Punkte).
> **Gemessen wurde trotzdem nichts:** der Messarm `enable_shadow_schedule` ist Default `False` und
> im laufenden Prozess nicht gesetzt ⇒ 0 Paper-Zeilen — dieselbe Fehlerklasse wie `enable_ig_bars`,
> diesmal aber an Tag 1 bemerkt. Stand, Befunde und Entscheidungen A–D:
> [`phase12_data_foundation/PHASE12_PREPROOF_HANDOVER.md`](./phase12_data_foundation/PHASE12_PREPROOF_HANDOVER.md),
> Bild dazu: [`docs/architecture/phase12_preproof.svg`](./docs/architecture/phase12_preproof.svg).
>
> **P12.5 (Messarm-Fixes) — formal CLOSED, GESCHEITERT (2026-08-18):** Steps 1–3 fixten U1/U2/U3/
> U5 + Entscheidung B, alle live gegen echte Daten bewiesen korrekt (`pairs_opened: 90`,
> `pairs_resolved: 66`, `resolution_source` erstmals real befüllt). Aber der scharf gestellte
> Messarm exponierte einen fünften, vorher nie aufgerufenen Pfad: `BarService.get_window` fordert
> bei jedem Coverage-Miss das **komplette** Fenster neu an (≈301 IG-Punkte/Top-up) statt nur die
> Lücke — 4731/10 000 Wochenpunkte in ~4 Stunden verbrannt, Requirement F (Soll < 1500/Woche) am
> ersten Tag gerissen. Nikinger-Intervention: Scheduler gestoppt, P12.5 ohne weitere Bauschritte
> geschlossen. Sofort-Befund des Interventionstags:
> [`phase12_data_foundation/PHASE12_5_FAILURE_HANDOVER.md`](./phase12_data_foundation/PHASE12_5_FAILURE_HANDOVER.md).
>
> **Closeout-Analyse (2026-08-18, nachgemessen — korrigiert die obige Root-Cause-Erzählung):**
> Von **1782 bei IG gekauften 1-Min-Bars trugen 1638 (92 %) Zeitstempel, die bereits als
> yFinance-Bar im Archiv lagen** — gekauft wurde für 4515 Punkte fast nur, was ohnehin schon da war.
> Ursache ist nicht U3 (die `and`-Bedingung kurzschließt links, U3s Schwelle wurde nie erreicht),
> sondern `_covers_tail`s Anspruch auf eine ≤ 1 Minute alte Bar gegen yFinances ~15 Minuten
> Eigenverzug: der teure Zweig war der Normalfall, latent seit Step 4, scharf erst durch das
> Einschalten des Messarms. **Empfehlung daher kein weiterer Patch, sondern ein struktureller
> Schnitt** (Auflöse-Pfad kauft nie wieder Daten; die Frage wechselt von „reicht das Archiv bis
> jetzt?" zu „deckt es das Fenster dieses Trades bis `time_stop_utc`?"). Offene Entscheidungen
> (Weg / Label / Wiederanlauf) und der volle As-Built-Stand:
> [`phase12_data_foundation/PHASE12_5_CLOSEOUT_HANDOVER.md`](./phase12_data_foundation/PHASE12_5_CLOSEOUT_HANDOVER.md),
> Bild: [`docs/architecture/phase12_5_failure.svg`](./docs/architecture/phase12_5_failure.svg).

**Goal:** eine echte Beweis-Messwoche läuft durch, ohne dass Infrastruktur die Messung tötet.
Instrument-Registry wird die eine Wahrheit (abgeleitetes, code-verifiziertes Symbol-Mapping statt
Deklaration), ein `BarService` wird der eine Bar-Pfad für alle Konsumenten, jede gefetchte Bar
landet in einem eigenen Archiv (`data/bars.sqlite`), ein Recorder-Prozess (yFinance-only) schreibt
kontinuierlich unabhängig vom Bot-Zustand, und ein Mess-Heartbeat lässt einen Ausfalltag am selben
Tag auffallen statt erst Wochen später.

**Done when:** siehe Plan §7 (PASS-Kriterien A–G + Kern). WI-2/W2-Auswertung selbst bleibt
Phase-11-Wiederaufnahme, nicht Teil dieser Phase.

**Directory:** [`phase12_data_foundation/`](./phase12_data_foundation/)

---

## Phase 13 — Live-Datenfundament *(eröffnet 2026-08-18 nach dem Scheitern von P12.5, abgeschlossen 2026-08-31)*

> **Status: ✅ abgeschlossen (Closeout 2026-08-31, Session 18).** Blöcke A + B + C code-complete (Stand 2026-08-22) + Beweiswoche ausgewertet (Mini-Session 23, 2026-08-31) + Pfad-C-Entscheidung (Mini-Session 24, 2026-08-31) + Befund-Inversion. 74 Phase-13-Tests grün, 53 `phase13:`-Commits auf `origin/main`, Σ 1703 grün repo-weit.
> **Plan:** [`docs/concepts/phase13_live_data_plan.md`](./docs/concepts/phase13_live_data_plan.md)
> (gelockte Entscheidungen L1–L17 + L18 Pfad-C-Erweiterung, Blöcke A/B/C, §9-Drift-Liste).
> **Block-C-Closeout + Phase-14-Handoff (2026-08-22):**
> [`docs/concepts/phase13_c_block_c_replan.md`](./docs/concepts/phase13_c_block_c_replan.md).
> **Beweiswoche-Findings (2026-08-31, Mini-Session 23) + Pfad-C-Nachtrag (§8, Mini-Session 24):**
> [`phase13_live_data/PHASE13_BEWEISWOCHE_FINDINGS_2026-08-31.md`](../phase13_live_data/PHASE13_BEWEISWOCHE_FINDINGS_2026-08-31.md) — 14-Tage-Fenster source_delta-Diagnose, drei empirische Befunde (B1 IG-Bars-Lücke 2/13 Tage **by-design**, B2 53.6 % Divergenzrate **Stichprobe Operator-Run-Tag**, B3 `last_verified_utc` semantisch korrekt unter Pfad C); Befund-Inversion: **kein Recorder-Mapping-Bug** — Phase-13-Architektur sieht strukturell keine kontinuierliche `source='ig'`-Beschaffung vor.
> **Closeout-Handover (2026-08-31, Session 18):**
> [`phase13_live_data/PHASE13_CLOSEOUT_HANDOVER.md`](../phase13_live_data/PHASE13_CLOSEOUT_HANDOVER.md) — Pattern-Vergleich zu Phase-12-CLOSEOUT (§0 BLUF + 5-Zeilen-Bilanz, L1–L18, F1/F2/F3 + B1/B2/B3, Pfad-C-Entscheidung, §9 Konsistenz-Regeln inkl. IG-Default-AUS, §10 Don'ts).
> **Vorgeschichte:** [`phase12_data_foundation/PHASE12_5_CLOSEOUT_HANDOVER.md`](./phase12_data_foundation/PHASE12_5_CLOSEOUT_HANDOVER.md) und [`phase12_data_foundation/PHASE12_CLOSEOUT_HANDOVER.md`](./phase12_data_foundation/PHASE12_CLOSEOUT_HANDOVER.md) (Pattern-Vorbild).

**Goal:** Beschaffung und Verbrauch von Kursdaten endgültig trennen. Kein Konsumentenpfad löst
je einen externen Fetch aus; Beschaffung ist ein vierstufiges, nach Kosten/Latenz gestaffeltes
System in *ein* Archiv (S1 LS-Kerzen → S2 yF-Recorder → S3 Fremdquelle → S4 budgetierte
IG-Rettung, Default AUS). Die Abdeckungsfrage gilt dem **ganzen** Trade-Fenster statt dem
Schwanz. Drei nachgemessene Befunde tragen die Phase (Plan §4): tote IG-Historie mit `ok=True`,
ein dagegen blinder Divergenz-Sampler, und eine **erfundene** `TIME_STOP`-Auflösung bei einer
Lücke mitten im Fenster. Drei empirische Beweiswoche-Befunde (B1/B2/B3) bestätigen + invertieren
(kein Recorder-Mapping-Bug, sondern Architektur-konform).

**Block-Stand 2026-08-31 (final):**

- **Block A** (Schnitt + `assess_window` + Tracker-Guard + Stale-Assertion + Sampler-Reparatur
  + Registry-Hygiene) — ✅ committed, `git log` zeigt 13+ Commits zwischen A0 und A7+A7.5.
- **Block B** (Lightstreamer + TickAggregator-Fallback + Scheduler-Lebenszyklus +
  Token-Rotation) — ✅ committed, B0=NO → L6-Fallback aktiv. B0-Probe-Ergebnis im
  `phase13_live_data/CLAUDE.md` Kopf.
- **Block C** (Capital.com Pfad B + `GapRescue` S4 + `source_delta.py`) — ✅ **PARTIAL by
  design**: Pfad B live-verifiziert 2026-08-22 (962 `source='capital'`-Bars, DAX + CAC);
  Spain 35 (IBEX) wartet auf Phase 14 (Dukascopy wird dort eine Quell-Registry-Zeile, kein
  Backfill-Code mehr). Vollständiger Block-C-Stand im Re-Plan-Handover.
- **Beweiswoche** (Plan §7 P1–P9) — ✅ **gelaufen 2026-08-25 → 2026-08-31**, Mini-Session 23
  wertet aus, Mini-Session 24 entscheidet Pfad C (IG = S4-GapRescue, Default AUS, L18).

**Done-Kriterium:** erfüllt. Beweiswoche gelaufen + Pfad-C-Entscheidung getroffen +
Befund-Inversion dokumentiert. Erste Akzeptanzbedingung (strukturelle Kostenzusicherung
statt Zählwert) bleibt gelockt — `test_get_window_never_fetches` ist der Beleg.

**Directory:** [`phase13_live_data/`](../phase13_live_data/) (Kopf + Modul-Tabelle in
`phase13_live_data/CLAUDE.md`).

---

## Phase 14 — Discovery-Then-Deterministic *(eröffnet 2026-08-22 aus dem Session-13-Architektur-Insight, abgeschlossen 2026-08-31)*

> **Status: ✅ abgeschlossen (Closeout 2026-08-31, Session 23).** Blöcke 0 + A + B + C code-complete + Block-D-Doku-Updates ✅ (Stand 2026-08-31, Mini-Sessions 21+22+23+24) + D5-Handover **komplett freigegeben** (Mini-Session 24, Pfad-C-Entscheidung 2026-08-31). **Phase-13-CLOSE-OUT (Commit `0ff55d2`) hat die D5-Handover-Voraussetzung freigegeben.** 61 Phase-14-Tests grün, 54 `phase14:`-Commits auf `origin/main`, 38 Zeilen in `instrument_source_availability`, Σ 1703 grün repo-weit.
> **Plan:** [`docs/concepts/phase14_discovery_plan.md`](./docs/concepts/phase14_discovery_plan.md)
> (D1–D20 gelockt, Blöcke 0/A/B/C/D mit Verbatim-Ankern, Akzeptanz A1–A8, Drift-Liste §9,
> §11 Post-Execution-Korrekturnotizen).
> **Closeout-Handover (2026-08-31, Session 23):** [`phase14_discovery/PHASE14_CLOSEOUT_HANDOVER.md`](../phase14_discovery/PHASE14_CLOSEOUT_HANDOVER.md) — Pattern-Vergleich zu Phase-12/13 (§0 BLUF + 5-Zeilen-Bilanz, D1–D20 mit D19 = IG-Default-AUS + D20 = Brücke zur Phase 15, A1–A8-Akzeptanz mit Beleg, §9 13 Konsistenz-Regeln, §10 Don'ts).
> **Phasenkopf:** [`phase14_discovery/CLAUDE.md`](../phase14_discovery/CLAUDE.md)
> (Modul-Tabelle jetzt mit `Tests`-Spalte + Σ-Sweep-Tabelle + Phase-14-Closeout-Row, Session-23-Block).
> **Concept-Skizze:** [`docs/concepts/phase14_discovery_concept.md`](./docs/concepts/phase14_discovery_concept.md)
> (drei Bausteine: Quell-Profil + Kreuzungs-Tabelle + Konsumenten-Umstellung; sieben offene
> Fragen für die Plan-Session — vom Plan Q1–Q7 beantwortet).
> **Block-C-Handoff:** [`docs/concepts/phase13_c_block_c_replan.md`](./docs/concepts/phase13_c_block_c_replan.md)
> §3 + §5 (warum die Architektur eine eigene Phase rechtfertigt; was Phase 14 implizit
> absorbiert: hardcoded `EPIC_MAP`, Path C Dukascopy).
> **Spezial-Pläne (alle abgeschlossen, D5-Beweis erbracht):**
>   - [`phase14_discovery/PHASE14_C_DAEMON_CWD_BUG_PLAN.md`](../phase14_discovery/PHASE14_C_DAEMON_CWD_BUG_PLAN.md) (P14-C, Discovery-Daemon-CWD-Path-Bug, Mini-Session 17, 2026-08-26) — ARM-Pfad absolut
>   - [`phase14_discovery/PHASE14_D_DAEMON_SIGNAL_CAP_PLAN.md`](../phase14_discovery/PHASE14_D_DAEMON_SIGNAL_CAP_PLAN.md) (P14-D, Discovery-Daemon-Signal-Response-Bug, Mini-Session 18, 2026-08-26 + §10 Korrekturnotiz 2026-08-31) — `signal_check_interval_s`-Cap
>   - [`phase14_discovery/PHASE14_E_RECORDER_LOOP_PLAN.md`](../phase14_discovery/PHASE14_E_RECORDER_LOOP_PLAN.md) (P14-E, Recorder-Sleep-Cap + Restart-Loop-Hunt, Mini-Session 20, 2026-08-28 + §2 D3-Korrekturnotiz) — Cross-Phase-Phase-12
>   - [`phase14_discovery/PHASE14_F_DOC_ROTATION_HOOK_STEP2_PLAN.md`](../phase14_discovery/PHASE14_F_DOC_ROTATION_HOOK_STEP2_PLAN.md) (P14-F, Doc-Rotation-Hook Step 2, Mini-Session 22+24, 2026-08-31) — `--strict` als Default nach D5-Beweis
>
> **Akzeptanz A1–A8 (Plan §7), Stand 2026-08-22 nach Session 9, A1–A8 alle grün (unverändert):**
> A1 (Discovery 0 IG-Punkte strukturell), A2 (`grep EPIC_MAP phase13_live_data/*.py` leer),
> A3 (`measurable_universe()`-Identität), A4 (yF-Projektion), A5 (Daemon unscharf = nichts),
> A6 (UI warnt + scharf per Datei), A7 (`source_delta.py` Drei-Fälle-Trennung), A8 (Sweep
> 1659→1698→1703).
>
> **Block-D ✅ (Mini-Session 21, 2026-08-31) + P14-F ✅ (Mini-Session 22+24):**
> Block-D Hygiene-Edits als 4 Commits + P14-F Doc-Rotation-Hook Step 2 als 5 Commits
> (`94e0c35`/`d32e93a`/`8fe439c`/`8db5a1c`/`c4f7d9c`).
>
> **D5-Handover-Status 2026-08-31 (Mini-Session 23 + 24):** **komplett freigegeben** —
> architektonisch (Mini-Session 23: Tabelle + Discovery + Source-Delta arbeiten wie designed)
> + operativ (Mini-Session 24: Pfad-C-Entscheidung, IG = S4-GapRescue Default AUS, by-design,
> Phase-13-Recorder-Mapping-Initiative entfällt als architektur-konform — siehe
> [Findings-Notiz §8.1](../phase13_live_data/PHASE13_BEWEISWOCHE_FINDINGS_2026-08-31.md)).
> **Phase-13-CLOSE-OUT (Commit `0ff55d2`) hat die formale Phase-14-D5-Handover-Voraussetzung
> freigegeben** — Phase 14 ist abgeschlossen.

**Goal:** jede Quelle (IG, yFinance, LS, Capital.com, später Dukascopy) **exponiert selbst**,
was sie liefern kann. Eine DB-Tabelle (`instrument_source_availability`) hält die Kreuzung
zwischen IG-Tradeable-Epics und verfügbaren Quellen. Konsumenten lesen die Tabelle, nicht den
Code. Hinzufügen einer Quelle ist eine Konfiguration, kein Code-Deploy.

**Why this is its own phase (Nikinger 2026-08-22):** die "discovery-then-deterministic"-
Architektur ist umfangreich genug (neues Schema, neue Schnittstelle pro Quelle, drei
Konsumenten-Migrationen, ToS-Tracking via `notes`-Spalte, Profile-Cache-TTL), dass sie den
Block-C-Closure sprengen würde. Phase 14 ist die **Brücke** zwischen dem
Datenfundament (Phase 13) und der AI-Sophistication (Phase 15): V4 setzt voraus, dass die
Daten-Infrastruktur **konfigurierbar** ist, nicht nur vorhanden.

**Scope-Skizze** (Concept, kein Plan):

- Quell-Profil-Schnittstelle (`SourceProfile` + `Source.discover()`), implementiert für
  Capital.com, yFinance, IG; LS bleibt Sonderfall (kein Discovery-API, Profil statisch).
- Phase-2-Migration `007_instrument_source_availability.sql` (Nummer in Plan-Session zu
  bestätigen).
- `run_capital_backfill` liest die Tabelle statt `EPIC_MAP`; `BarArchive.window(sources=…)`
  wird tabellenbewusst statt rang-bewusst; `source_delta.py` P6 trennt „nicht abrufbar" von
  „abrufbar und divergiert".
- Path C Dukascopy wird eine Quell-Registry-Zeile, **kein** Code-Touch in `live_data/`.

**Done-Kriterium** (Concept, zu schärfen in der Plan-Session): eine neue Quelle (Dukascopy
als Test-Kandidat) ist mit ≤ 50 Zeilen Commit angebunden, ohne dass ein Konsument
angefasst wird. `grep -rn "EPIC_MAP" phase13_live_data/ --include=*.py` ist leer.
*(`--include=*.py` ist Absicht: Phasenkopf, Session-Archiv und Closeout-Handover nennen
`EPIC_MAP` in ihrer Chronik und werden nicht editiert — 📕/📦-Konvention. Präzisiert
2026-08-22 im Phase-14-Plan §7/A2.)*

**Directory:** noch nicht angelegt — entsteht in der Plan-Session.

---

## Phase 15 — V4: Sophisticated / Optional *(die alte Phase 9, deferred; vormals "Phase 12",
dann "Phase 13", dann "Phase 14", jetzt Phase 15 — umnummeriert 2026-08-11, 2026-08-18 und 2026-08-22)*

> **Status: ✅ ABGESCHLOSSEN am 2026-09-05 (Session #13, MiniMax-M3-Exec)** — Closeout-Handover [`phase15_v4/PHASE15_CLOSEOUT_HANDOVER.md`](../phase15_v4/PHASE15_CLOSEOUT_HANDOVER.md), Bild [`docs/architecture/phase15_closeout.svg`](../docs/architecture/phase15_closeout.svg). Pattern-Vergleich zu Phase-12/13/14. **4 Blöcke alle ✅**: A (Haushalt) endgültig · B (Reward-Kalibrierung) live-validiert (Score 78,72 → 50,00) · C (Instinct-ECC) code-complete, heute bit-identical via VETO-5-leere-Regelliste (AK9) · D (Erbstücke + Folgefix Variante C) endgültig. **Σ 1843 grün repo-weit**. 18 Commits gepusht, 6 Commits lokal ahead (Push-Freigabe ausstehend). **Offen (alle nicht-Phase-15-Blocker):** Promotion-Bridge (Plan §10), Ledger-Restore (250 Punkte, Nikinger-Aktion), Live-DB Migration 009 (additiv, beim nächsten Service-Restart), Gate P7/A6 (wartet auf nächsten OPEN-Trade).
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

## Phase 16 — Freischaltung *(eröffnet 2026-09-05, Plan-Session Fable 5.1)*

> **Status: 🔄 in Arbeit seit 2026-09-05.** Execution-ready Plan
> [`docs/concepts/phase16_activation_plan.md`](./docs/concepts/phase16_activation_plan.md)
> (P1–P17, L1–L9, Blöcke A–E, AK1–AK16). Phasenkopf:
> [`phase16_activation/CLAUDE.md`](./phase16_activation/CLAUDE.md).

**Goal:** jedes gebaute Feature läuft, jeder Bruch ist zu, ein vorregistrierter 2-Wochen-Lauf
(Demo) beweist Autonomie ohne Hand. Der Bot ist seit 2026-08-31 faktisch tot (100 % Research-
Abstain) — Ursache Infrastruktur, nicht Strategie.

- [ ] **A Haushalt** — Ritual, Σ-Baseline 1843, Code↔.md-Sweep, WebUI-Log, Push
- [ ] **B Substrat** — Schema-Floor (Live-DB v7, Migrations 008/009 nie angewendet) + Operator-
  Apply + Ledger-Restore; Wochenend-Epics raus
- [ ] **C Research-Loop** — 14-Tage-Fenster für die Trade-Historie + ein Prompt-Satz; Token-Budget
  300 k; Breaker-Semantik (P3-Freigabe offen)
- [ ] **D Freischaltung** — vier Arme **Default ON** (`--no-*`), Bar-Stream-Token-Wrapper,
  Promotion-Bridge + Compiler (Gatter n ≥ 50 bleibt), Margin-Headroom (B3)
- [ ] **E 2-Wochen-Autonomie-Test** — Vorregistrierung, `autonomy_report.py`, Runbook, Closeout

**Done when:** AK1–AK16 des Plans, insbesondere AK15 (sieben PASS-Kriterien; Profit ist keines).

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
