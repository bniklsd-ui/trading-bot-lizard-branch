---
status: concept-brief (für Opus-Plan-Session, Nikinger-Eingabe; Detail-Plan: ./PHASE16_LLM_SWITCH_PLAN.md, root-cause F7+F8+Session-#34-Empfehlung)
purpose: Plan-Grundlagen-Dokument für die kommende Opus-Plan-Session der Phase-16-LLM-Subphase — selbst-enthaltend, prompt-shaped, mit Verbatim-Ankern auf den Code und die Vorarbeiten. Was Opus nach diesem Brief können soll: einen execution-ready Plan mit Locks + Schritt-Sequenz + Akzeptanz liefern, der gegen Code + Live-Daten + K6-realisierte Fakten geprüft ist.
read-when: vor dem Eröffnen der Opus-Plan-Session für die Phase-16-LLM-Subphase; nicht zum Weiterausführen — Cross-Phase-Edits (P4/5/7/8/15) sollen in Opus' Hand, nicht in der Phase-16-Exec-Hand
detail: L1
up: ./CLAUDE.md
down:
  - ./PHASE16_LLM_SWITCH_PLAN.md                  # 📕 Detail-Plan (MiniMax-M3-Session 2026-10-07, 10 Schritte, 8 Locks, 8 Akzeptanz) — Opus-Basis
  - ./PHASE16_R_EXEC_PLAN.md                       # 📕 Strukturelles Vorbild (F/Session #33, 339 Zeilen, R0–R7)
  - ./PHASE16_F_EXEC_PLAN.md                       # 📕 Strukturelles Vorbild (J/H/G/I-Block, Akzeptanz A1–A8)
  - ../meta_m1_harness/CLAUDE.md                   # M1-Step-10 OpenAICompatLLMClient (cold, smoke-verified, M1 → Hersteller-Agnostik-Vorstufe)
  - ../phase4_research/research/llm_openai_compat.py  # 📕 der bestehende OpenAI-Compat-Client (Hersteller-agnostisch bereits, wiring-cold)
  - ../docs/concepts/phase16_activation_plan.md    # 📕 Parent-Plan Phase 16 (P1–P17, L1–L9, Blöcke A–E, AK1–AK16)
  - ../CLAUDE.md#current-state                     # Phase 16 als active phase (Cross-Phase-Freigabe: P1/2/3/4/5/7/8/9/15)
updated: 2026-10-07 (MiniMax-M3-Exec-Session #36, Plan-Grundlage für Opus)
---
# Phase 16 LLM — Hersteller-Agnostik (Subphase LLM-Switch) — Plan-BRIEF für Opus

> **Wofür dieses Dokument ist:** Nikinger plant, in einer Folge-Session Opus 5 die Planung der
> **Phase-16-LLM-Subphase** (Hersteller-Agnostik / LLM-Switch, intern: Phase 16 L) zu geben.
> Phase 16 LLM ist eine **Subphase** unter dem Phase-16-Schirm (analog Phase 16 F für Audit +
> Restplan und Phase 16 R für Reparatur 2 + Neustart) — das Suffix bleibt bewusst bei „16",
> damit der Lauf-Zeitstrahl und die Cross-Phase-Freigabe aus dem aktiven Phase-16-Setup weiter
> gelten. Das hier ist der Briefing-Text, der **vor** dem Opus-Prompt gelesen wird — damit Opus
> nicht das halbe Repo crawlen muss, sondern die Anker kennt und die Constraints versteht. Der
> Detail-Plan (`PHASE16_LLM_SWITCH_PLAN.md`, 380 Zeilen) ist die zweite Stufe; Opus darf ihn
> lesen, soll aber **nicht** nur re-plan-en, sondern verifizieren/ankern und entscheiden, was
> noch fehlt.
>
> **Status:** dieses Dokument ist **kein** Plan und **kein** Lock — es ist Briefing-Material.
> Alle Zahlen sind heute selbst gemessen (gegen Code, Daten, Logs). Was unsicher ist, ist
> explizit als ⚠️ gekennzeichnet.

---

## 1. Mission (warum wir das machen)

Der Bot ist seit 2026-08-31 zu 100 % im Research-Abstain (Phase 16 L1, gefixt), aber das
Token-Budget reißt an Debatte-Volltagen (F7: 09-16 = 301 225 Tokens, 09-17 = 302 892 Tokens,
beide vor 17:30 Berlin, beide über dem 300k-Cap). Die **ökonomische Wurzel**: jeder Token
kostet uns bei Anthropic voll, obwohl derselbe Token-Use-Case (strukturierte JSON-Ausgabe
aus einer ~1k-Token-Frage) bei günstigeren Modellen **deutlich weniger** kostet. Ein
10×-Kostenvorteil würde den 300k-Token-Cap zu einer Logging-Notiz degradieren statt eines
Sicherheits-Tors.

**Sekundäre Befunde, die mit-stützen:**
- **F8 (Phase 16 R-Subphase, Session #32):** vier von sieben Kriterien (K1/K5/K6/K7) im
  Tagesreport melden PASS an einem Tag, an dem der Bot gar nicht lief. K6 (Token-Budget) ist
  also strukturell fragil — wenn der Cap irrelevant wird (weil günstig), fällt die Fragilität
  weg.
- **Empfehlung Session #34 (R6):** „Research = 94 % des Token-Caps" → P4 ist der Hebel-Punkt.
  P5/P6/P7/P8/P15 sind in Summe klein.

**Was die Mission NICHT ist:**
- Kein Live-Account-Schalter (eigene Subphase nach Tag-10-Closeout, Demo dazwischen).
- Kein Strategie-Tweak (kein VETO, kein Sizing, kein Filter ändert sich).
- Kein AI-Triggert-Order-Bypass (Wurzel-Regel 3 unverändert).

## 2. Vorhandene Bauanleitung (der Code heute)

| Datei | Was | Stand |
|---|---|---|
| `phase4_research/research/llm_client.py:1` | `LLMClient` (Anthropic-Messages-API, `claude-*`), einzige verdrahtete Wahl | ✅ live |
| `phase4_research/research/llm_openai_compat.py:107` | `OpenAICompatLLMClient` (OpenAI-Chat-Completions), M1-Step-10 | ✅ code-complete + smoke-verified mit OpenRouter (`META_M1_RESULTS.md` → „Fallback") — **aber wiring-cold** |
| `phase4_research/research/models.py:536` | `_DEFAULT_PRICING_USD_PER_MTOK` mit 3 Anthropic-Rows | ✅ |
| `phase4_research/research/models.py:602` | `ResearchConfig.model` Default `claude-sonnet-4-6` | ✅ |
| `phase4_research/research/token_meter.py:61` | `estimate_cost(usage, model, config)` — unknown model → `(0,0)` + warn (Resilience) | ✅ |
| `phase4_research/scripts/wiring.py:180` | `LLMClient(model=config.model, api_key=get_credential("anthropic_api_key"), ...)` — **hardcoded** | ⚠️ das ist die Stelle, die Hersteller-agnostisch werden muss |
| `phase4_research/scripts/openrouter_smoke.py` | Operator-Smoke gegen OpenRouter; nutzt `keyring.get_password("openrouter", "api_key")` | ✅ als Smoke-Vorlage für MiniMax wiederverwendbar |
| `scripts/store_minimax_key.py` | Key-Storage für den **Claude-Code-Dev-Harness** (Service `trading-bot-minimax`) | ✅ — getrennt vom Bot-Key |

**Was die Bauanleitung HERSTELLT, aber nicht TUT:** `OpenAICompatLLMClient` ist **bereits
Hersteller-agnostisch** (akzeptiert `model`, `base_url`, `api_key_service` als Konstruktor-Args).
Was fehlt, ist die **Verdrahtung** in `scripts/wiring.py`. Die Subphase ist daher im Kern ein
**Rekonfiguration + Defaults-Flip**, nicht ein „neuer Adapter bauen".

## 3. Constraints (was die Planung respektieren muss)

### 3.1 Cross-Phase-Freigabe (verbindlich, aus `CLAUDE.md` → „Current state")

> „Cross-Phase frei: P1/2/3/4/5/7/8/9/15 (P3 seit Runde 2)"

- **P4, P5, P7, P8, P9, P15:** dürfen editiert werden.
- **P6 (Debatte): NICHT freigegeben** für Phase 16 → keine Wiring-Änderung, keine Default-
  Änderung an `DebateConfig`/`RewardConfig` (das wäre Cross-Phase-Arbeit).
- **P3, P12, P14:** schon Phase-16-cross-phase-frei (per Session #31), aber in dieser Subphase
  kein Bedarf (P3 = Marktdaten, P12 = BarArchiv, P14 = Source-Registry).

### 3.2 Hard Rules (root CLAUDE.md, ausnahmslos)

- **Credentials im Keyring, sonst nirgendwo** (nicht .env, nicht JSON, nicht YAML, nicht Code).
- **Kein AI-Output triggert direkt eine Order** (Wurzel-Regel 3). Der bestehende Validator +
  Candidate-Filter in P4 bleibt unverändert — der Wechsel ändert Modell-Qualität, nicht die
  Sicherheits-Architektur.
- **Demo vor Live:** ohne Demo-PASS kein Live-Account (gilt für jede Subphase, die Code
  auf den Live-Pfad bringt).
- **Kein „temporary hardcoded value"** der einen Check umgeht.

### 3.3 Keyring-Isolation

Drei Namespaces heute, sauber getrennt:
- `tradingbot` — Anthropic (Bot, via `broker_wrapper.credentials`)
- `openrouter` — OpenRouter-Fallback (M1 Step 10)
- `trading-bot-minimax` — Claude-Code-Dev-Harness (NICHT der Bot)

Für den Bot-MiniMax-Key ist ein **vierter, eigenständiger Namespace** zu wählen — die
Detail-Plan-Vorlage schlägt `trading-bot-minimax-bot` vor (analog zum M1-Isolations-Pattern).

### 3.4 Smoke-Pflicht (Lock-Vorschlag im Detail-Plan §3 L-L6)

Ohne Demo-Live-Cycle-PASS kein Flip auf Live-Account. Für diese Subphase heißt das: der
Default-Flip (`config.llm_provider = "openai_compat"`) tritt **erst nach** Demo-Smoke-PASS in
Kraft — egal ob im selben Commit oder in einem Folge-Commit.

## 4. Empfehlung (was MiniMax-M3-Eval-Session für richtig hält)

| Punkt | Empfehlung | Begründung |
|---|---|---|
| **Scope dieser Subphase** | **MVP:** Factory in P4 + P4-Defaults + Key-Skript + Tests. P5/7/8/15 folgen in einer Folgesession nach 1 Woche P4-Live-Daten. | P4 = ~94 % des Token-Caps (R6 Session #34) → größter Hebel, kleinster Risiko-Footprint. |
| **P6** | **Nicht anfassen** | Cross-Phase-Sperre; qualitative Bedenken (Judge-Synthesis); kleinere Token-Masse. |
| **Modell** | `minimax/MiniMax-M3` als Beispiel — exakter String muss Nikinger bestätigen oder per ENV/Config überschreibbar sein | OpenAI-Compat-Namespace-Konvention; bei direktem MiniMax-API kann der String abweichen. |
| **Endpoint** | `https://api.minimax.chat/v1` als Beispiel-Annahme — siehe ⚠️ | Default konfigurierbar; Smoke-Test verifiziert die echte URL. |
| **Default-Flip** | **Konservativ:** Factory + Config-Felder + Tests in den Commits, **Default bleibt `anthropic`**. Nikinger macht den Flip nach Demo-PASS in einer Mini-Commit (eine Zeile + Service-Restart). | Geringeres Risiko; reversibel in Sekunden; strukturelle Sichtbarkeit des Flip-Moments. |
| **Pricing-Row** | `(0.30, 1.50)` USD/Mtok für MiniMax-M3 als **Annahme** mit ⚠️-Kommentar (verifizieren gegen MiniMax-Pricing-Page) | Token-Meter-`unknown model → (0,0)` + warn ist die bestehende Sicherheitsschiene — auch wenn die Row falsch ist, crasht nichts. |
| **Key-Skript** | `scripts/store_minimax_bot_key.py` als exakte Kopie von `store_minimax_key.py` mit anderen Konstanten | Pattern-Konsistenz; idempotent; kein neues Konzept. |

## 5. Was die Plan-Session liefern muss (Output-Spec)

Opus' Plan sollte analog zu existierenden Phase-Plans folgende Struktur haben
(Detail-Plan-Vorlage `PHASE16_LLM_SWITCH_PLAN.md` hat diese schon — Opus darf verifizieren/ankern,
nicht wortgleich kopieren):

- **§0 BLUF** mit dem konkreten Outcome dieser Subphase
- **§1 selbst gemessene Fakten** mit Datei:Zeile-Ankern für jede Annahme (gegen den Detail-Plan
  und gegen den Code prüfen — bei Drift korrigieren und dated note lassen)
- **§2 Nikinger-Entscheidungen** (mindestens: exakter Modell-String, exakte Base-URL, Scope
  P5/7/8/15 — drinnen oder raus?, Smoke-Pflicht-Bestätigung)
- **§3 Locks** (L-L1 bis L-L8 aus dem Detail-Plan als Anker; weitere, falls Opus zusätzliche
  Risiken sieht)
- **§4 Schritt-Sequenz** mit konkreten Datei-Edits, Tests, Commit-Strategie
- **§5 Follow-ups** (was bewusst out-of-scope bleibt)
- **§6 Akzeptanz** (jedes Kriterium mit Mess-Vorschrift + Verifikation)
- **§7 Out-of-Scope**
- **§8 Commit-Konvention** (analog zu existierenden Plänen)
- **§9 Review-Protokoll** (analog `phase16_activation_plan.md §13`)

## 6. Offene Fragen für die Opus-Plan-Session (vom Nikinger zu beantworten oder von Opus zu eskalieren)

| Q | Frage | Wahrscheinliche Antwort |
|---|---|---|
| Q1 | Genaues MiniMax-Modell-String | `minimax/MiniMax-M3` (Beispiel-Annahme) — Nikinger bestätigt |
| Q2 | Exakte MiniMax-API-Base-URL | `https://api.minimax.chat/v1` (Annahme) — Nikinger bestätigt |
| Q3 | Soll der Default-Flip in dieser Subphase committet werden? | **Konservativ empfohlen: NEIN** — nach Demo-PASS als separate 1-Zeilen-Commit-Aktion |
| Q4 | P5/P7/P8/P15-Wirings in dieser Subphase mit anpassen? | **Nein** (Cross-Phase-Sperre hebt das nicht auf, aber der Hebel ist klein; Folgesession nach 1 Woche P4-Daten) |
| Q5 | P6 (Debatte) in dieser Subphase? | **Nein** (Cross-Phase-Sperre + qualitative Bedenken) |
| Q6 | Live-Account-Schalter in dieser Subphase? | **Nein** (eigene Subphase nach Tag-10-Closeout des aktuellen Laufs) |

## 7. Was diese Subphase NICHT macht (Klare Außenkante)

- Kein Live-Account.
- Kein VETO/Sizing-Filter/Validator-Code-Touch (Wurzel-Regel 3).
- Kein Caching-Tweak (bestehendes `cache_system`-Flag bleibt).
- Kein Streaming-/Tool-Use (kein Use-Case).
- Kein dynamischer Provider-Switch zur Laufzeit (Konfiguration, nicht Laufzeit-Auto-Pilot).
- Keine Drittanbieter außer MiniMax-via-OpenAI-Compat (OpenAI direkt, Google, Mistral sind out).
- Keine Änderung an P6-Debatte oder P7-Reward-Defaults.

## 8. Wenn etwas schiefgeht (Rollback-Pfad)

- **Config-Flip zurück:** `ResearchConfig.llm_provider = "anthropic"` (eine Zeile) + Service-Restart → Bot fährt auf Anthropic hoch, Code-Pfade (Validator/Filter) unverändert, Verhalten bit-identisch zu heute.
- **Smoke-FAIL:** kein Flip; Diagnose als Plan-Anhang.
- **Kritischer Folge-Fehler:** die Commit-Konvention soll atomic sein — jeder Commit ist
  rückrollbar (kein Squash, kein Force-Push). Falls nötig, `git revert` + Push.

---

## Anhang A — Code-Anker zum Selbst-Checken (für Opus)

Diese Zeilen heute (gegen den Code prüfen, bei Drift korrigieren + dated note):

- `phase4_research/research/llm_client.py:180` — `_raw_call` einziger mockbarer Call-Site
- `phase4_research/research/llm_openai_compat.py:183` — `_raw_call` einziger mockbarer Call-Site
- `phase4_research/research/models.py:602` — `ResearchConfig.model` Default
- `phase4_research/research/models.py:694` — `pricing_usd_per_mtok` Field
- `phase4_research/research/token_meter.py:79` — Pricing-Lookup + Unknown-Model-Resilience
- `phase4_research/scripts/wiring.py:180` — der einzige LLMClient-Konstruktor im P4-Path
- `phase4_research/scripts/openrouter_smoke.py:117` — Smoke-Vorlage
- `scripts/store_minimax_key.py:26` — Key-Storage-Pattern für den **neuen** Bot-Key

## Anhang B — Cross-Phase-Tabelle (für die Schritt-Sequenz in Opus' Plan)

| Phase | Datei : Zeile | Default-Modell | Cross-Phase-frei? | In dieser Subphase? |
|---|---|---|---|---|
| 4 (Research) | `scripts/wiring.py:180` | `claude-sonnet-4-6` | ✅ P4 | ✅ **JA** — Factory + P4-Default-Flip (konservativ: getrennt) |
| 5 (Execution) | `scripts/wiring.py:76` | (aus cfg) | ✅ P5 | ⏸ Folgesession |
| 6 (Debate) | `scripts/wiring.py:93`, `:100` | `haiku-4-5` / `sonnet-4-6` | ❌ **NICHT freigegeben** | ❌ NEIN |
| 7 (Reward) | `scripts/wiring.py:79`, `reward/models.py:378` | `haiku-4-5` (lesson_model) | ✅ P7 | ⏸ Folgesession |
| 8 (Scheduler) | `scripts/wiring.py:299, 336, 345, 384, 391, 400, 464, 471, 500, 522, 528, 686` | gemischt | ✅ P8 | ⏸ Folgesession |
| 9 (Universe) | — | — | ✅ P9 | ❌ Kein LLM-Code-Touch nötig |
| 15 (V4) | — | — | ✅ P15 | ❌ Kein LLM-Code-Touch nötig |

## Anhang C — MiniMax-M3 Spec-Hinweise (für die Planung, NICHT als Lock)

- MiniMax-M3 ist das Modell aus der MiniMax-API.
- OpenAI-Compat-Endpoint erwartet `chat/completions` mit Bearer-Auth (das Schema, das
  `OpenAICompatLLMClient` schon spricht).
- Structured Outputs werden per Prompt-Instruction erzwungen (kein decode-layer-Schema) — die
  bestehende `OpenAICompatLLMClient` macht das genau so (siehe Modul-Docstring §"Structured
  Outputs — no equivalent, so it's a prompt instruction instead").
- ⚠ Token-Pricing: in der Detail-Plan-Vorlage als `(0.30, 1.50)` USD/Mtok angenommen — gegen
  die aktuelle MiniMax-Pricing-Page verifizieren. Token-Meter fällt auf `(0,0) + warn` zurück,
  wenn die Row fehlt — kein Crash.