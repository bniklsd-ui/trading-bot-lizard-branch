# Phase 8 → v1.5 Hotfix — Implementierungsplan (für Claude Code)

> **Audience:** Claude Code CLI.
> **Author:** v1.5-Browser-Planner-Chat, 2026-06-30. Decisions mit Niklas gelockt.
> **Was das ist:** der schrittweise Implementierungsplan. Er **ergänzt** und dupliziert nicht
> den code-verankerten `phase8_scheduler/PHASE8_V1.5_HOTFIX_HANDOVER.md` (Diagnose + file:line-Anker
> §2–§8) und den `PHASE8_V1_5_KICKOFF_HANDOVER.md` (gelockte Decisions).
>
> **Read-First-Reihenfolge für dich (Claude Code):**
> 1. diese Datei (Plan + Sequenz)
> 2. `phase8_scheduler/PHASE8_V1.5_HOTFIX_HANDOVER.md` §2–§8 für die **autoritativen** file:line-Anker
> 3. dann pro Step die echten Dateien öffnen + **Anker verifizieren** bevor du editierst

---

## 0. Mission & Leitplanken

**Mission:** Phase 8 ist code-complete + gemergt, aber **halber Abschluss** — der Bot abstaint
fast jeden Zyklus, also gibt es **keinen net-new autonomen Demo-Trade** (open→close in einem Lauf).
Ursache ist **kein Scheduler-Bug**, sondern Research-Überkonservatismus. v1.5 unblockt den
Live-Beweis durch deterministische **Inputs (Universum) + Gates (Clamp/Floor) + Daten-Hygiene
(Provenance)** — und **sonst nichts**.

**Harte Leitplanken (nicht verhandelbar):**

1. **Kein neues AI.** Die AI-Stellen bleiben exakt P4-`ask_candidate`, P6-Debatte, P7-`reflect`.
   v1.5 fügt **keine** AI hinzu — auch nicht für Universum-Erweiterung (das ist P9, nur die
   deterministische Naht wird jetzt gebaut).
2. **AI triggert nie direkt eine Order.** Validator + `candidate_filter` + 4 VETOs + Auto-Confirm
   bleiben vorgelagert und unberührt.
3. **Nie einen VETO umgehen.** Block B ist *Research-Gate*-Tuning, **nicht** VETO-Tuning. Die 4 VETOs
   (`execution/vetos.py`) + 5 Gates bleiben **bit-unberührt**.
4. **Demo-only, fail-closed.** Phase-8-Demo-Lock bleibt (`account="demo"`, nur `get_broker("ig_demo")`,
   AutoConfirm-Re-Check). Alle gelockerten Knobs sind **für Demo-Datensammlung** und **vor Live
   re-baselinen** — explizit als provisorisch markieren.
5. **Additive Nähte, Phasen-Isolation.** Cross-Phase-Edits (P3 TickerMapper, P4 config/filter,
   P7 context_builder) sind erlaubt, jeweils als **dokumentierter Cross-Phase-Edit**. Default-Pfad
   unverändert; **jede Phase bleibt grün** (Regression P1–P8).
6. **Credentials nur im Keyring. `turbo_candidates.json` nicht umbenennen** (P2/P5-Gate-2-Contract).
7. **Live-Tests sind Operator-Sache.** Du lieferst Code + gemockte Tests (kein Netz in Unit-Tests,
   stderr-Logging, atomare Commits). Niklas läuft IG-demo / echte LLM-Runs.

**Working agreement (projekt-locked):** TDD; CLAUDE.md `## Session stopped` als **erste Aktion**
pflegen; well-factored Funktionen statt Monolith; fail-closed bei Ambiguität überall;
**Commit ⇒ Note-Update** (Status + `## Session stopped`). Handover nach ~20–30 Tool-Calls erwägen.

---

## 1. Gelockte Decisions (Referenz)

| Block | Decision | Gelockt |
|---|---|---|
| 0 | `bot_score`-Messung | **Plan-Step 1, datengetrieben** (Operator läuft den read-only Dump, Werte gaten Step 3 B). |
| 0b | Doku-Reconciliation | **eigener Step + Commit, VOR Code.** Claude Code prüft echten Repo-Stand gegen As-Built-Checkliste (§Step 0b). |
| Step 0 | turbo-Cleanup | **nur stray Code-Refs verifizieren/entfernen**, `turbo_candidates.json`-Name bleibt eingefroren. |
| C1/C4 | Universum | **3–4 kuratierte liquide EUR-Index-CFDs** (DAX + Euro Stoxx 50 + CAC 40 [+ optional AEX/IBEX 35]), **operator-verifiziert auf IG demo**. Als **typisiertes Config-Objekt** (`InstrumentSpec`-Liste + `source`-Feld + validierender Loader) = deterministische Naht für spätere P9-Research-Erweiterung. **Keine AI verdrahtet.** |
| C2 | EUR-only | **beibehalten.** |
| C3 | Volume `None` | **toleriert** (reduced-signal, kein Crash). |
| B1 | Differenzierung | **P6-Debatte + 4 VETOs** als Richtungs-Check; P4-Gate nur permissiv genug für *einen* Kandidaten. |
| B2 | Clamp/Floor | **entkoppeln** (heute hart bei 50.0 gekoppelt). |
| B3 | Werte | **temporär** (`data-collection mode`, `enable_long_bias_clamp=False`), Werte aus Step-1-Messung, explizit provisorisch markiert, re-baseline bei Live. |
| A | Lesson-Provenance | **Seed-Marker + Hold-Time-Heuristik** (kein Migration 003 / kein DB-Schema-Touch im Hotfix). Prompt-Filter + Quarantäne-by-date. **Nach C/B.** |

---

## 2. Sequenz (Überblick)

```
Step 0   Cleanup (turbo) + Verify-Baseline (Regression grün, BEVOR irgendwas)
Step 0b  Doku-Reconciliation (eigener Commit)
Step 1   MESSEN: bot_score-Verteilung (read-only Diagnostic; Operator läuft)
Step 2   C — Universum als typisiertes Config-Objekt + 3–4 Epics integrieren   ← größter Hebel
Step 3   B — Clamp/Floor entkoppeln + relaxen (data-collection mode; Werte aus Step 1)
Step 4   A — Lesson-Provenance (Seed-Marker + Hold-Time; Prompt-Filter + Quarantäne)   ← nach C/B
Step 5   Operator-Live-Runs: 5a Varietät (open→close)  +  5b Breaker-Fire (separat, eng)
Step 6   Doku/Note-Update: Phase 8 → ✅, CLAUDE.md Session stopped, ROADMAP
```

**Token-/Zeit-Fallback:** Wenn knapp → **C, dann B** ist das Minimum für autonome Trades.
A (Lessons) + Breaker-Test folgen. Step 0/0b/1 sind billig und zuerst.

> **⚠ Reihenfolge-Update (2026-07-01, Claude Code, Nikinger-freigegeben — Code = Source of Truth):**
> **Ausführungsreihenfolge auf B-vor-C gedreht** (Step 3 vor Step 2). Der Plan blieb inhaltlich
> unverändert; nur die *Reihenfolge* wurde nach der Step-1-Messung angepasst. **Das Warum
> (datengetrieben):** die Messung ergab **alle 3 real gescorten Trades < 50** (100 %; s. Step-1-Block
> unten). Der below-50-Doppel-Clamp feuert also **jeden** Zyklus, nicht nur im Ausnahmefall — B ist ein
> *konstanter* Blocker. Zudem ist **C's Nutzen bis B gelockert ist gedämpft**: solange unter Score 50
> alles auf BUY-only + Floor 70 geklemmt wird und der Bot strukturell < 50 lebt, kann ein breiteres
> Universum keinen differenzierten Kandidaten erzeugen. **B ist der Unlock, der C's Varietät erst
> nutzbar macht.** B ist außerdem klein, in `phase4_research/` isoliert und **ohne Operator-
> Prerequisite**, während C den per-Epic-Brain-Context-Refactor + die Operator-Epic-Auflösung braucht.
> C folgt unverändert nach B. **✅ B umgesetzt 2026-07-01** (s. Step-3-Block).

---

## Step 0 — Cleanup + Verify-Baseline

**Ziel:** sauberer, grüner Ausgangszustand. Build-Order ist `Cleanup → Verify → …` — also zuerst.

**0a — turbo-Cleanup (verify-only, wahrscheinlich fast leer):**
- `grep -rn` im Repo nach stray turbo-/Options-Vokabular **im Code** (`turbo_research`, `pre_trade_option_check`, `CALL`/`PUT`/`Strike`/`OTM`, `expected hold ≥`). Tote/Legacy-Refs entfernen.
- **NICHT anfassen:** `turbo_candidates.json` (eingefrorener Dateiname, P2/P5-Contract) und die **dokumentierte** Legacy-Namens-Note in den Konzepten („hieß im Erbe `turbo_research.py`").
- Akzeptanz: keine stray turbo-Code-Refs mehr; Contract-Dateiname unverändert.

**0c — Verify-Baseline:**
- Volle Regression **vor** jeder Änderung: `pytest` über P1–P8. Muss grün sein.
- Ermittle die **echte** aktuelle Test-Zahl per `pytest --collect-only -q | tail -n1` (siehe Step 0b: die Docs nennen widersprüchlich 181 vs. 173 — **rate nicht, lies sie aus** und vereinheitliche auf den wahren Wert).
- Akzeptanz: grüne Baseline + verifizierte Test-Zahl notiert.

---

## Step 0b — Doku-Reconciliation (eigener Commit, VOR Code)

**Ziel:** die Docs, die der nächste Chat als Kontext liest, auf den As-Built-Stand bringen.
**Wichtig:** Hardcode **nicht** „P1/P3/P4 regressiert" — lies den **echten Repo-Stand** und gleiche
gegen die folgende **As-Built-Wahrheits-Checkliste** ab (die Projekt-Kopien sind teils schon
reconciled, die Repo-Kopien können abweichen).

**As-Built-Wahrheit (autoritativ):**

| Doc | Soll-Zustand | Häufiger Drift |
|---|---|---|
| `ROADMAP.md` | P1–P7 = ✅ abgeschlossen + live-verifiziert. **P8 = code-complete / „halber Abschluss" / autonomer-Trade-unverifiziert** (12 Module + webui, gemergt main 2026-06-30, Test-Zahl = der in Step 0c ausgelesene Wert). P9 mit 9a–9e inkl. 9b Instinct-ECC. | P8 noch im `[ ]`-Planungs-Zustand / „to be created"; P1/P3/P4 auf „ungetestet/to be created" zurückgefallen. |
| `ARCHITECTURE.md` | As-Built: **CFD, keine Optionen** (BUY/SELL, kein CALL/PUT); Prozess-bewusster Reward; `research.py`; `turbo_candidates.json` **Legacy-Name behalten**. SVG-Referenz **klären**: existiert `docs/architecture/tradingbot_v2_architecture.svg` noch, vs. neue `docs/architecture/phase8_scheduler_concept.svg`? → Referenz reconcilen (nicht auf eine tote Datei zeigen). | Legacy-Naming (`turbo_research.py`, `pre_trade_option_check()`, Gate5 „CALL/PUT"), Freund-Bot-Reward-Formel (`base+gain×10`). |
| `README.md` | Status-Tabelle P1–P7 ✅, **P8 🟡 halber Abschluss**. | i. d. R. ok — verifizieren. |
| root-`CLAUDE.md` (~40 KB) | Current-state korrekt; **Test-Zahl-Inkonsistenz im P8-Block vereinheitlichen** (Header vs. Detail-Notes → der in Step 0c ausgelesene wahre Wert). | 181 vs. 173. |

**NICHT behaupten (Ehrlichkeits-Leitplanke in allen Docs):** dass der Bot „in Produktion" autonom
tradet (er abstaint); dass die Lessons schon sinnvoll sind (Verifikations-Trades); irgendeine
Profitabilität/Edge (nie gemessen, nie im Scope). **Korrekte `main`-Formel:** „code-complete,
mechanisch bewiesen, autonomer-Trade-unverifiziert" → bekannte Ursache → v1.5-Hotfix.

- Akzeptanz: vier Root-Docs konsistent + As-Built; SVG-Referenz zeigt auf eine existierende Datei;
  ein sauberer Doku-Commit; CLAUDE.md `## Session stopped` aktualisiert.

---

## Step 1 — MESSEN: bot_score-Verteilung (read-only)

**Ziel:** datengetriebene Werte für Step 3 (B). Sagt, ob B (Clamp/Floor) oder C (Universum)
quantitativ dominiert und welche Floor-Schwelle sinnvoll ist.

- **Read-only Diagnostic-Script** (z. B. `scripts/diag_score_distribution.py`): liest aus der
  Live-DB (`live_db_path=data/trading_bot.sqlite`) den aktuellen Score (`db.get_current_score()`)
  **und** die Score-Trajektorie aus `reward_pts` (`score_after`-Historie). Gibt aus: aktueller
  Score, Anzahl/Anteil < 50, < 35, Min/Max/Median. **Keine** Pipeline-Änderung, **keine** Writes.
- Fehlende/leere Daten → sauberer Hinweis („insufficient history"), kein Crash.
- **Operator** läuft das Script und gibt dir die Verteilung → fließt in die Floor-Werte in Step 3.
- Akzeptanz: lauffähiges read-only Script; gemockter Unit-Test (kein echtes DB-Netz); Output liegt
  vor, bevor Step 3 die Floor-Werte fixiert.

> **✅ ERLEDIGT (2026-07-01). Script `scripts/diag_score_distribution.py` (repo-root, phasenlos, 20
> Tests) gebaut; Operator lief es gegen die echte `data/trading_bot.sqlite`. Gemessene Verteilung:**
>
> | Metrik | Wert |
> |---|---|
> | n (gescorte Trades) | **3** (small sample, n<10) |
> | current_score | **45.83** |
> | Bereich (min–max) | **45.83 – 49.86** |
> | Median / Mean | **47.45 / 47.71** |
> | p25 / p75 | 46.64 / 48.65 |
> | **Anteil < 50** | **3/3 = 100 %** |
> | Anteil < 35 | 0/3 = 0 % |
> | Accounts | demo: 3 |
> | Zeitraum | 2026-06-26 .. 2026-06-29 |
>
> **Befund (der Grund für die B-vor-C-Reihenfolge, s. §2):** der Bot lebt **strukturell unter Score 50**
> — jeder je gescorte Trade liegt darunter. Der below-50-Doppel-Clamp (BUY-only + Floor 55→70) ist damit
> das **Default-Regime, nicht die Ausnahme** → er force-abstained jeden Zyklus (genau der 2026-06-29-Lauf,
> Score 45.83). ⚠ n=3 ist ein **sehr kleines Sample** — die Verteilung ist ein grober Hinweis, kein hartes
> Signal; teils lebt der Score auch deshalb niedrig, *weil* der Bot kaum tradet (Henne-Ei mit C). Für Step 3
> (B) reicht der Befund: der Floor-70-Sprung ist bei diesen Scores **unerreichbar** → auf 55 (= Default)
> kollabiert.

---

## Step 2 — C: Universum (größter Hebel)

> **Anker (aus Handover/Memory — verifiziere in §8 des HOTFIX-Handovers + im echten Code):**
> `phase4_research/research/models.py:320` (`epic_allowlist=("IX.D.DAX.IFMM.IP",)`),
> P3 `TickerMapper`, Sizing in Gate 4 (`execution`), Momentum-VETO-Quelle `get_ohlcv` (P1).

**C.0 — Operator-Prerequisite (blockt C):** je Instrument den exakten **Epic-String**,
`currency==EUR`, `min_deal_size`, Point-Value verifizieren und ob `get_ohlcv` Bars liefert.
Shortlist: **DAX `IX.D.DAX.IFMM.IP` (vorhanden), Euro Stoxx 50, CAC 40** [+ optional **AEX** /
**IBEX 35**]. → füllt die Universum-Config (C.1). **Epic-Strings nicht raten.**

> **Methode (autoritativ — kein Web):** IG-Epic-Strings sind account-/demo-spezifisch; Web-Suche
> (Research-Chat oder Browser-Plugin) ist unzuverlässig (live-only/stale). **Claude Code schreibt ein
> read-only Resolver-Script** (z. B. `scripts/resolve_epics.py`), das via `broker_wrapper`
> `search_markets`/Market-Navigation gegen IG **demo** die Kandidaten auflöst und je Treffer
> `epic`, `instrumentName`, `currency`, `min_deal_size`, Point-Value + `get_ohlcv`-Verfügbarkeit
> ausgibt — genau wie `IX.D.DAX.IFMM.IP` in P1 bestätigt wurde. **Read-only, keine Order, keine
> Writes.** **Operator** läuft es (Keyring/Netz = Operator-Sache, Leitplanke 7); die bestätigten
> Strings trägt er in die `InstrumentSpec`-Liste (C.1). Decision-5-Konsistenz: `search_markets` dient
> hier nur der **einmaligen Setup-Auflösung**, nicht als Runtime-Universum-Selektor.

**C.1 — Universum als typisiertes Config-Objekt (die deterministische Naht):**
- Ersetze das hardcodierte `epic_allowlist`-Tuple durch eine **kuratierte, validierte Liste** aus
  einem **einzigen** Config-Source-of-Truth. Pro Eintrag z. B. `InstrumentSpec` (dataclass/typed dict):
  `epic`, `yf_ticker: Optional[str]`, `volume_proxy: Optional[str]`, `point_value`, `min_deal_size`,
  `currency` (muss EUR sein), `source: str` (`"curated"` jetzt; später `"research_promoted"`).
- **Validierender Loader** `load_universe()`: prüft jeden Eintrag (EUR-only erzwingen, epic non-empty,
  numerische Felder plausibel) und **fail-closed** bei malformed (drop + `logger.warning`, oder
  Abort je nach Schwere — kein stiller Pass).
- **Extension-Point dokumentieren** (Docstring/Kommentar): „künftiger Research-Step hängt validierte
  `InstrumentSpec(source='research_promoted')` über einen deterministischen validate→promote-Pfad an
  (P9, spiegelt Instinct→VETO-ECC). **KEINE AI in v1.5 verdrahtet.**"
- `candidate_filter`/Research konsumieren die Liste statt des Tuples; jeder Epic darf Kandidat werden.

**C.2 — P3 TickerMapper:** je Epic einen Eintrag IG-Epic → yFinance-Ticker (Kontext) ergänzen;
Volume-Proxy je Index wo billig (sonst `None` → reduced-signal, C3-toleriert). Cross-Phase-Edit (P3),
dokumentieren. Default-Verhalten für DAX unverändert.

**C.3 — Sizing-Sanity je Epic:** Gate-4-Sizing (**risk-per-trade ÷ stop-distance**) muss
Point-Value/Min-Size jedes Instruments korrekt verarbeiten. Pro Epic eine Sanity-Prüfung/Test, sodass
ein mis-specctes Instrument **fail-closed** (kein Mis-Sizing). Min-Size-Untergrenze respektieren.

**C.4 — VETO-Quelle je Epic:** der Momentum-VETO muss je Epic **IG-Echtzeit-Bars** (`get_ohlcv`,
P1) ziehen, **nicht** das ~15 min verzögerte yFinance. Wenn Bars für ein Epic fehlen → fail-closed
(dieser Epic abstaint, kein Crash). VETO-Logik selbst **unberührt** — nur sicherstellen, dass die
Quelle je Epic auflöst.

**Tests (kein Netz; Broker/yFinance mocken):**
- `load_universe()`: wohlgeformte Liste lädt; non-EUR-Eintrag wird gedroppt/abgelehnt; malformed →
  fail-closed.
- TickerMapper resolved jeden Epic (oder explizit `None` → reduced-signal Pfad ohne Crash).
- Sizing-Sanity je Epic (korrekte Größe + fail-closed bei mis-spec).
- VETO-Quelle: fehlende Bars für einen Epic → fail-closed ABSTAIN für diesen Epic, andere unberührt.
- **Default-Pfad (nur DAX) bleibt bit-identisch** → bestehende P4/P5-Tests grün.

**Akzeptanz:** Research kann für **jeden** Epic im Universum einen Kandidaten emittieren; Gates/VETOs
laufen per-Epic; malformed Eintrag failt closed; Regression grün.

> **✅ Step 2A ERLEDIGT (2026-07-01, Claude Code — Code = Source of Truth). Zwei Operator-Entscheidungen
> (AskUserQuestion): „Framework now, populate later"; point_value JETZT in P5 threaden (ehrlich dokumentiert).**
> Umsetzung wich in **Details** vom Plan ab (Anker-Zeilen verschoben; Ist-Stand):
> - **C.1 (models.py):** `InstrumentSpec` + `load_universe()` gebaut; `ResearchConfig.universe` ist SoT,
>   `__post_init__` versöhnt mit dem Legacy `epic_allowlist` (beide Konstruktions-Stile funktionieren).
>   Default-Universum = 1 DAX-Spec = bit-identisch zum alten `epic_allowlist`. +13 Tests.
> - **C.1+ per-Epic-Brain-Context (war im Plan als „Herz" markiert, hier explizit):** vorher bekam **nur**
>   der Anchor Brain-Context. Jetzt `ResearchContext.brain_contexts` (je Epic), `context_builder` holt je
>   tradeable Epic, `prompt` rendert die Nicht-Anchor-Snapshots, `candidate_filter`/`research.py`
>   Drift/`drift_at_pick` keyen auf den **Kandidaten-Epic** (Fallback Anchor). +5 Tests.
> - **C.0 (resolve_epics.py):** read-only Operator-Resolver gebaut (broker-injiziert, offline-testbar,
>   nur GETs). ⚠ **point_value NICHT resolvebar** (IG exponiert es nicht → `lot_size`-Hinweis + manuelle
>   Bestätigung). +6 Tests (repo-root `tests/`).
> - **C.2/C.3 Reconciliation:** **C.3-Sizing (point_value) VORGEZOGEN nach 2A** (Operator wollte es jetzt);
>   Naht **P5-seitig** (`ExecutionConfig.point_values` + `point_value_for`, frozen Candidate + IG ohne
>   Point-Value → zwei bewusste SoTs). **C.2 (P3 TickerMapper) + die echten Epic-Werte bleiben 2B**
>   (operator-gated). C.4 (VETO-Quelle je Epic) in 2B verifizieren. +7 P5 Tests.
> - **Wiring (P4+P8):** registriert je `InstrumentSpec` Ticker+Proxy aus dem Universum. DAX-Default unverändert.
> - **Grün:** P4 99→**117**, P5 146→**153**, root `tests` 20→**26**; Regression P6 70 · P7 128 · P8 181 unberührt.
>   Import-Isolation gewahrt. **2B (echte Epics) + Step 4 (A) offen.** Detail: `phase8_scheduler/CLAUDE.md`.

> **🔶 Step 2B TEILWEISE ERLEDIGT (2026-07-01, Claude Code, nach dem ersten `resolve_epics.py`-Live-Lauf
> des Nikinger).** **Euro Stoxx 50 aufgenommen** (`IX.D.STXE.IFM.IP`, `research.models.EXTENDED_UNIVERSE`,
> live bestätigt currency/min_deal_size/TRADEABLE/ohlcv; `point_value`/`yf_ticker`/`volume_proxy` inferiert/
> öffentlich bekannt, NICHT unabhängig live verifiziert). **CAC 40 / AEX / IBEX 35 zurückgestellt** — der
> Live-Lauf zeigte am Ende (France 40 + beide Restterme) ein Rate-Limit-Kaskaden-Muster (`IGAdapter`
> wirft `RateLimitError` auf HTTP 429 ohne eigenen Retry; der Resolver machte ~35 ungebremste Calls in
> Folge), **nicht** eine echte „nicht verfügbar"-Datenlage — insbesondere `ohlcv_available=False` für den
> einzigen CAC-Treffer, der überhaupt antwortete, ist damit **inkonklusiv**, nicht bestätigt fehlend.
> Da VETO 3 ohne Bars fail-closed ist, wäre ein Aufnehmen ohne Klärung ein Phantom-Instrument-Risiko —
> bewusst zurückgestellt. **Fix:** `scripts/resolve_epics.py` pausiert jetzt (`--pace-s`, Default 0.6 s)
> zwischen jedem Broker-Call + surfaced den echten `env.error` (vorher hartcodiert `None`). **Zusätzlicher
> Fund:** die 2A.4-Wiring-Schleife (dynamische Registrierung) deckt den Daemon-Pfad, aber NICHT die
> Operator-Verifizierbarkeit über P3s eigene `smoke_test.py` (die einen bare `TickerMapper()` baut) — ein
> **statischer P3-`ticker_map.py`-Eintrag bleibt nötig** für `IX.D.STXE.IFM.IP → ^STOXX50E`. Wiring (P4
> `build_research`, P8 `_build_research` + `build_scheduler`) opt-in jetzt explizit in
> `EXTENDED_UNIVERSE`; P5 `point_values` wird **von `EXTENDED_UNIVERSE` abgeleitet** (eine SoT, keine
> Hand-Duplizierung). Grün: P3 70→**71** · P4 117→**120** · root `tests` 26→**28**; P5 153 · P6 70 ·
> P7 128 · P8 181 unberührt. **Next (Operator):** P3-`smoke_test.py`-Verify für STXE + ein gepacter
> `resolve_epics.py`-Re-Lauf für CAC/AEX/IBEX. Detail: `phase8_scheduler/CLAUDE.md`.

---

## Step 3 — B: Clamp/Floor entkoppeln + relaxen (data-collection mode)

> **Anker (verifizieren):** long-bias BUY-only `models.py:322-323`, confidence-floor 55→70
> `models.py:328-329`, Kopplung/Floor in `candidate_filter.py:47-66` und `:70+`. Flag
> `enable_long_bias_clamp` existiert bereits.

**B.1 — Entkoppeln:** Direction-Clamp und Confidence-Floor sind heute hart bei `50.0` gekoppelt.
Trenne in **zwei unabhängige Knobs**: „erlaubte Richtungen" und „Confidence-Schwelle".

**B.2 — Relaxen (data-collection mode):**
- `enable_long_bias_clamp=False` setzen (Demo-Datensammlung).
- Confidence-Floor: den 55→70-Sprung durch **einen** permissiv-aber-sinnvollen Wert ersetzen —
  **Wert aus Step-1-Messung** (z. B. knapp unter dem Median, sodass typische Kandidaten passieren,
  aber Müll nicht). Differenzierung wird an **P6-Debatte + 4 VETOs** delegiert (B1).
- **B4 (falls Clamp überhaupt behalten):** erst in **stark** gebiastem Markt greifen (z. B. Score < 35
  aus Step 1), nicht schon unter neutral.

**B.3 — Provisorisch markieren:** alle gelockerten Werte in der Config mit
`# data-collection mode — re-baseline before live (P7/P9 anchor confidence on real outcomes)`
kommentieren, sodass das Go-Live-Re-Baselining unmissable ist.

**Tests:**
- Mit Clamp off + relaxtem Floor: ein **sub-50-aber-sonst-valider** Kandidat **passiert** das
  P4-Gate (erreicht die Debatte) — der Fall, der heute force-abstaint.
- VETOs/Gates feuern **unabhängig** weiter (Beweis: B berührt keinen VETO).
- **Default (Clamp on) bleibt unverändert** → bestehende Tests grün.

**Akzeptanz:** P4 emittiert einen Kandidaten, wo es vorher force-abstainte; P6+VETOs bleiben der echte
Richtungs-Check; **kein VETO/Gate angefasst**; Regression grün.

> **✅ ERLEDIGT (2026-07-01, Claude Code — Code = Source of Truth). Umgesetzt VOR Step 2 (s. §2-Reorder).**
> Umsetzung wich in **Details** vom Plan ab (Anker-Zeilen hatten sich verschoben; hier die Ist-Werte):
> - **B.1 Entkoppeln:** die Floor-Grenze war **kein** Config-Feld, sondern das hartcodierte Modul-Literal
>   `candidate_filter._NEUTRAL_SCORE = 50.0` (die Clamp-Grenze war das Config-Feld `long_bias_below_score`).
>   Neues Feld **`ResearchConfig.confidence_floor_below_score = 50.0`** (`models.py`), `confidence_threshold`
>   liest es jetzt; das Literal ist entfernt. → Floor-Grenze und Clamp-Grenze sind zwei unabhängige Knobs.
> - **B.2 Relaxen (Defaults geändert — Wiring überschreibt sie nie, also ist der Dataclass-Default der Hebel):**
>   `enable_long_bias_clamp: True → **False**` (SELL unter neutral erlaubt; P6-Debatte + 4 VETOs sind der
>   Richtungs-Check). `confidence_floor_low_score: 70.0 → **55.0**` (= Default; der 70-Floor war bei den
>   gemessenen Sub-50-Scores unerreichbar). **B4 verworfen** (Clamp nicht auf `<35` verschoben, sondern
>   schlicht abgeschaltet — sauberer/reversibler; Messung zeigt 0 % unter 35, also für aktuelle Daten ohnehin
>   äquivalent).
> - **B.3 Provisorisch markiert:** beide geänderten Defaults tragen einen `# v1.5 data-collection mode —
>   re-baseline before live`-Kommentar; der `ResearchConfig`-Docstring erklärt Entkopplung + provisorische Werte.
> - **Tests:** `phase4_research/tests/test_candidate_filter.py` von 15 → 18 (Default-Verhalten neu asserted +
>   ein **Entkopplungs-Beweis** + der Clamp-*Mechanismus* via explizitem `clamped_config()` weiter gedeckt).
>   **P4 96 → 99 grün**, `test_research.py` (17) unberührt (keine clamp-abhängige Assertion), **P8 181 grün**.
>   `enable_long_bias_clamp is False`, `confidence_threshold(40.0, ResearchConfig()) == 55.0`,
>   `resolve_allowed_directions(40.0, ResearchConfig()) == ("BUY","SELL")` direkt verifiziert.
> - **Kein VETO/Gate angefasst** (nur `phase4_research/` + Doku). Live-Beweis (Kandidat wird erzeugt statt
>   force-abstain) = Operator-Lauf des P8-Daemons/`live_test.py` im Handelsfenster.

---

## Step 4 — A: Lesson-Provenance (nach C/B)

> **Anker (verifizieren):** Seed-Marker `"MANUAL SEED (not a real research pick)"`
> `seed_candidate.py:62`; Prompt-Injektion der Lessons `context_builder.py:184`; Auswahl
> `get_recent_lessons`.
> **Sequencing:** echte, sinnvolle Lessons entstehen erst **nach** realen autonomen Outcomes
> (= nach C/B). Mechanismus jetzt bauen, Nutzen kommt nach C/B.

**A.1 — Identifikation „Verifikations-Trade" (billig, kein DB-Schema-Touch):** Seed-Marker
(`seed_candidate.py:62`) + Hold-Time-Heuristik. **Kein Migration 003** im Hotfix (→ v1.6 falls nötig).

**A.2 — Prompt-Filter:** `get_recent_lessons` (Prompt-Auswahl) nach Provenance filtern —
Verifikations-Lessons aus dem **Research-Prompt** ausschließen (`context_builder.py:184`).
**Reward/Score darf weiter auf ihnen rechnen** — nur der Prompt wird gereinigt.

**A.3 — Quarantäne bestehender verschmutzter Lessons:** **by-date, reversibel** (Flag/Markierung,
kein Hard-Purge). Mit A.2 paaren, damit nicht re-verschmutzt wird.

**Tests:** Verifikations-Lesson **nicht** im Prompt-Kontext; echte Lesson **drin**; Quarantäne
reversibel; **Reward-Pfad unberührt** (rechnet weiter auf allen Lessons).

**Akzeptanz:** Research-Prompt bekommt keine Verifikations-Trade-Lessons mehr; echte Post-C/B-Lessons
fließen normal; Reward unverändert.

---

## Step 5 — Operator-Live-Runs (zwei getrennte Beweise)

> **Operator-Sache** (IG-demo / Netz / echte LLM-Runs). Du (Claude Code) lieferst nur ggf.
> die Test-Configs als benannte Profile.

**5a — Varietäts-Run (open→close einfangen):** normalere Caps (z. B. `max_trades_per_day=5`,
`cycle_interval_min=5`), über **mehrere Demo-Tage** laufen lassen, bis ein **net-new autonomer
open→close** in einem sauberen Lauf fällt. **Erwartung:** mehrere Tage, kein Heldenlauf — braucht
ein tradeable Setup im Fenster.

**5b — Breaker-Fire-Run (separat, bewusst eng — „sachte"):** bei vergrößertem Pool reicht ggf.
`max_trades_per_day=2`, **oder** ein **echter kleiner `daily_loss_cap`** statt des bewussten
Platzhalters. Laufen lassen, bis ein Breaker **real trippt** → fail-closed → auto Kill-Switch
beobachten. **Nicht** mit 5a vermischen (sonst Tagesbudget weg, bevor 5a den open→close zeigt).

**Diese zwei Beweise schließen das Phase-8-✅-Gate** (net-new autonomer Trade + real auslösender
Safety-Breaker).

---

## Step 6 — Doku/Note-Update + Abschluss

- Nach 5a/5b: `ROADMAP.md` Phase 8 → **✅** (mit korrekter Formel: autonomer Trade + Breaker
  verifiziert; weiterhin **kein** Profit/Edge behaupten).
- CLAUDE.md `## Session stopped` final; **Commit ⇒ Note-Update** je Step.
- Falls v1.5 zur Datensammlung-Pause überleitet: kurzer Hinweis im Note, dass die Weiterentwicklung
  (P9) temporär pausiert, bis reale Demo-Trades gesammelt sind.

---

## Anhang — Cross-Phase-Edit-Register (für Phasen-Isolation-Audit)

| Phase | Datei (verifizieren) | Edit | Default unverändert? |
|---|---|---|---|
| P4 | `research/models.py`, `candidate_filter.py`, neuer `load_universe()`/`InstrumentSpec` | Universum-Config + Clamp/Floor entkoppeln/relaxen | DAX-only-Pfad bit-identisch |
| P3 | `TickerMapper` | je Epic Ticker/Volume-Proxy-Eintrag | DAX-Mapping unverändert |
| P7/P4 | `context_builder.py`, `get_recent_lessons` | Provenance-Prompt-Filter | Reward-Pfad unberührt |
| — | `scripts/diag_score_distribution.py` (neu) | read-only Diagnostic | n/a |
| — | `scripts/resolve_epics.py` (neu) | read-only IG-demo Epic-Resolver (C.0) | n/a |
| docs | ROADMAP/ARCHITECTURE/README/CLAUDE.md/SVG | As-Built-Reconciliation | n/a |

> Jeder Edit als **dokumentierter Cross-Phase-Edit** committen. **Regression P1–P8 nach jedem Step
> grün.** Bei Ambiguität: fail-closed + fragen, nicht raten.
