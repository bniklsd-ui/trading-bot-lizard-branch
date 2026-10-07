---
status: plan (Subphase L — LLM-Switch, Ausstehend auf Nikinger-Freigabe §2)
purpose: Exec-Plan der Phase-16-L-Subphase (Hersteller-agnostischer LLM-Endpoint + Wechsel auf günstigeres Modell, empfohlen MiniMax M3). Motivation: F7 (K6 gerissen an 09-16/09-17, 300k-Token-Cap zu klein) + F8 (Cap-basiertes Gate ist ohnehin fragil); der Kostenvorteil ~10× macht das Token-Budget zur kosmetischen Größe und den Cap überdenkbar.
read-when: Ausführung der L-Subphase; vor jedem Edit an research/llm_factory.py, research/models.py, research/scripts/wiring.py, scripts/store_minimax_bot_key.py, tests/test_llm_factory.py
detail: L2
up: ./CLAUDE.md
down:
  - ../docs/concepts/phase16_activation_plan.md            # 📕 Vollplan Phase 16 (Blöcke A–E, L9 = aktuelle Subphase)
  - ./PHASE16_R_EXEC_PLAN.md                                # 📕 R-Subphase (Vorgänger, Blöcke R0–R7 — Muster für Struktur)
  - ./PHASE16_F_EXEC_PLAN.md                                # 📕 F-Subphase (Vorgänger, Blöcke J/H/G/I — Muster für Akzeptanz)
  - ../meta_m1_harness/CLAUDE.md                            # OpenAICompatLLMClient (M1 Step 10, kalter Fallback — wird hier geweckt)
  - ../phase4_research/research/llm_openai_compat.py        # der bestehende OpenAI-Compat-Client (Hersteller-agnostisch bereits, nur cold)
updated: 2026-10-07 (MiniMax-M3-Exec-Session #36, Plan-Entwurf, Nikinger-Freigabe §2 ausstehend)
---
# Phase 16 L — Exec-Plan (LLM-Switch)

> **Plan-Session 2026-10-07 (MiniMax-M3, OpenCode).** Jede Annahme unten ist an diesem Tag
> gegen den Code geprüft. Code = Source of Truth. Was nicht prüfbar war (MiniMax-Endpoint-URL,
> exakter Modellstring, Token-Plan-Details) steht in §2 als **offen** markiert und wartet auf
> Nikinger-Input.

## §0 BLUF

- **F7+K8+Empfehlung der vorangegangenen Session:** Token-Cap-basierte K6-Schwelle ist an
  Debatte-Volltagen (113–121 Calls) zu klein (F7) UND ein toter Bot meldet sie grün (F8). Der
  einzig ehrliche Fix ist ein so günstiges Modell, dass der Cap kein Sicherheits-Tor mehr ist,
  sondern ein Logging-Detail.
- **Vorbedingung (für den Erfolg) ist eine Hersteller-agnostische Factory:** der bestehende
  `OpenAICompatLLMClient` (M1 Step 10, kalter OpenRouter-Fallback, smoke-verifiziert) ist
  bereits Hersteller-agnostisch (jeder OpenAI-compatible Endpunkt + jeder Keyring-Service).
  Was fehlt, ist die **Verdrahtung** — heute ist er ``code-aktiv, wiring-cold``.
- **Empfehlung an Nikinger (Wortlaut aus Vorgespräch):** Default-Flip auf `llm_provider =
  "openai_compat"` mit Modell `MiniMax/MiniMax-M3` (Beispiel, exakter String aus §2) für Phase 4
  (Research — höchste Token-Masse, größter Hebel). Phase 6 (Debatte) bleibt Anthropic (Qualität
  Judge = Sonnet, kleinere Token-Masse, geringer Hebel). Phase 5/7/8/15 folgen in einer
  Folgesession, sobald P4 eine Woche stabil läuft (siehe §5).
- **Cross-Phase:** P4/5/7/8/9/15 erlaubt für Phase 16 (CLAUDE.md „Current state" + R-Plan §4).
  P6 **nicht** erlaubt → P6-Wiring bleibt unangetastet, Default-Modelle in `DebateConfig`/
  `RewardConfig` ebenfalls (sonst wäre das Cross-Phase-Arbeit an P6).
- **Smoke-Pflicht-Block:** vor Live-Account mindestens ein Demo-Live-Cycle mit
  `scripts/openrouter_smoke.py`-Pendant gegen MiniMax. Ohne Demo-PASS kein Live.

## §1 Selbst gemessene Fakten (2026-10-07)

### 1.1 Aktueller LLM-Stack (gemessen gegen Code)

| Datei | Rolle |
|---|---|
| `phase4_research/research/llm_client.py:1` | `LLMClient` (Anthropic-Messages-API, `claude-*`), heute einzige verdrahtete Wahl |
| `phase4_research/research/llm_openai_compat.py:1` | `OpenAICompatLLMClient` (OpenAI-Chat-Completions), M1-Step-10, **kalther Fallback**, smoke-verified gegen OpenRouter |
| `phase4_research/research/models.py:536` | `_DEFAULT_PRICING_USD_PER_MTOK` mit 3 Anthropic-Rows |
| `phase4_research/research/models.py:602` | `ResearchConfig.model` Default `claude-sonnet-4-6` |
| `phase4_research/research/models.py:694` | `pricing_usd_per_mtok` Field mit `default_factory` auf obige Dict |
| `phase4_research/research/token_meter.py:61` | `estimate_cost(usage, model, config)` — Pricing-Dict-Lookup, unknown model → `(0,0)` + warn |
| `phase4_research/scripts/wiring.py:180` | `LLMClient(model=config.model, api_key=get_credential("anthropic_api_key"), ...)` — hardcoded |
| `phase4_research/scripts/openrouter_smoke.py:117` | `--model` OpenRouter-Id, Key aus `keyring.get_password("openrouter", "api_key")` |

### 1.2 Modelle, die die Phasen heute aufrufen (alle in wiring.py, hart-importiert `LLMClient`)

| Phase | Datei : Zeile | Default-Modell |
|---|---|---|
| 4 (Research) | `scripts/wiring.py:180` | `claude-sonnet-4-6` |
| 5 (Execution) | `scripts/wiring.py:76` | (aus cfg) |
| 6 (Debate) | `scripts/wiring.py:93`, `:100`; `debate/models.py:134-136` | `model_bull/bear = claude-haiku-4-5-20251001`, `model_judge = claude-sonnet-4-6` |
| 7 (Reward) | `scripts/wiring.py:79`, `reward/models.py:378` | `lesson_model = claude-haiku-4-5-20251001` |
| 8 (Scheduler) | `scripts/wiring.py:299, 336, 345, 384, 391, 400, 464, 471, 500, 522, 528, 686` | gemischt (alle 3) |
| 15 (V4) | (kein direktes LLM — nutzt P7-Recorder) | n/a |

P4 ist die einzige Phase, deren **Default-Modell selbst ein Wechsel-Kandidat** ist
(`config.model = "claude-sonnet-4-6"`). Die anderen Phasen bekommen ihren Modellnamen aus
ihrer Phase-eigenen Config — die Wiring-Datei wählt nur den Client.

### 1.3 Hersteller-Agnostik: was schon im M1-Step-10 steckt

`OpenAICompatLLMClient.__init__` (Phase 4:107-160) akzeptiert:
- `model` — beliebige OpenAI-kompatible Modell-ID
- `base_url` — Default `https://openrouter.ai/api/v1`, **überschreibbar** pro Instanz
- `api_key_service` — Default `"openrouter"`, **überschreibbar** (z.B. `"trading-bot-minimax-bot"`)
- `api_key` lookup: `keyring.get_password(api_key_service, "api_key")` — gleiche
  Username-Konvention wie für OpenRouter

→ Hersteller-Agnostik ist **bereits gebaut**, nur nicht verdrahtet. Diese Subphase re-konfiguriert
die existierenden Bausteine, sie erfindet nichts.

### 1.4 Tests heute (gemessen, `phase4_research/tests/`)

| Test-Datei | Tests | Bemerkung |
|---|---:|---|
| `test_llm_openai_compat.py` | (mehrere, gemockt) | Pinnt Adapter-Interface; Smoke-Test existiert in `openrouter_smoke.py` |
| `test_token_meter.py` | 6+ | Pinnt Pricing-Lookup + Unknown-Model → `(0,0)` |

Phase-4-Test-Count vor dieser Subphase: **163** (laut Session #35 Sweep-Tabelle).

## §2 Nikinger-Entscheidungen (ausstehend bis §2 abgehakt)

| # | Frage | Vorschlag | Warum |
|---|---|---|---|
| L-D1 | Genaues MiniMax-Modell-String | `minimax/MiniMax-M3` | OpenAI-Kompat-Provider-Konvention (Provider/Modell), passt zu `OpenRouter`-Namespace. Bei direktem MiniMax-API-Endpoint: anderer Namespace — siehe L-D2. |
| L-D2 | OpenAI-Compat-Endpoint-URL für MiniMax | `https://api.minimax.chat/v1` (oder ein anderer — muss Nikinger bestätigen, weil ich keinen Netzwerk-Call machen kann in dieser Umgebung) | Wenn der Endpunkt anders heißt, ändert sich `base_url` in der Factory. |
| L-D3 | Keyring-Namespace für Bot-MiniMax-Key | `trading-bot-minimax-bot` | Eigenes Namespace nach M1-Isolations-Pattern (`openrouter`, `tradingbot`, `trading-bot-minimax` schon belegt — der letzte ist für Claude-Code-Dev-Harness, nicht der Bot). |
| L-D4 | `ResearchConfig.model` Default ändern? | Ja → `minimax/MiniMax-M3` | Nur P4-Default. P5/6/7/8/15-Defaults bleiben unverändert (P6 Cross-Phase-Sperre; P5/7/8/15 in Folgesession). |
| L-D5 | `ResearchConfig.llm_provider` Default? | `"openai_compat"` | Production-Run soll den günstigen Provider nehmen. Anthropic bleibt über das gleiche Config-Feld wählbar (manuelles Override für Tests). |
| L-D6 | `OpenAICompatLLMClient` Pricing-Row für M3? | `(0.30, 1.50)` (Annahme — MiniMax-Pricing-Seite, Stand 2026-10-07) | ~10× günstiger als Haiku 4.5 ($1/$5). **Annahme, muss gegen MiniMax-Pricing-Page verifiziert werden — Kommentar im Code verweist darauf.** |
| L-D7 | Smoke-Test gegen MiniMax | Sofort durch Nikinger nach `scripts/store_minimax_bot_key.py` (Key via getpass) | Ohne Demo-PASS kein Flip auf Live. |
| L-D8 | Reihenfolge: Plan → Code → Tests → Demo-Smoke → Commit | Wie vorgeschlagen | Default-Flip tritt erst bei nächstem Service-Restart in Kraft (R5-Units). |

**Wenn Nikinger L-D1/L-D2 nicht aus dieser Umgebung beantworten kann, mache ich L-D1/L-D2 zu
Configurable-Defaults (Override via Env oder Config-Datei), so dass die spätere
Smoke-Verifikation den exakten String ohne Code-Edit einsetzen kann.**

## §3 Locks (gelockte Design-Entscheidungen, nicht ohne Nikinger umwerfen)

- **L-L1:** Hersteller-Agnostik geht **über eine Factory**, nicht über Vererbung oder
  Monkey-Patching. Beide Clients (`LLMClient`, `OpenAICompatLLMClient`) bleiben eigenständige
  Klassen — die Factory wählt zwischen ihnen anhand `config.llm_provider`.
- **L-L2:** Default-Auswahl pro Phase: **P4 openai_compat, P5/6/7/8/15 unverändert (Phase-16
  Cross-Phase-Liste).** P5/7/8/15 folgen in einer eigenen Folgesession (siehe §5).
- **L-L3:** P6 wird in dieser Subphase **nicht angefasst.** Weder `scripts/wiring.py`, noch
  `debate/models.py`, noch `reward/models.py` (Cross-Phase-Sperre).
- **L-L4:** Keyring-Isolation: **eigener Namespace** (`trading-bot-minimax-bot`) für den
  Bot-Key. Der vorhandene `trading-bot-minimax`-Service bleibt für den Claude-Code-Dev-Harness
  (M1-Konvention).
- **L-L5:** `scripts/store_minimax_bot_key.py` ist ein neues Skript nach exakt demselben Muster
  wie `scripts/store_minimax_key.py` (getpass, keyring, idempotent, `--status`/`--delete`).
- **L-L6:** Smoke-Pflicht: ohne Demo-Live-Cycle-PASS kein Live-Account-Schaltung. Default-Flip
  tritt mit dem nächsten Service-Restart in Kraft; vor dem Restart kann der Nikinger die
  Konfiguration in `config.py` (oder per Env-Variable) nochmal überschreiben.
- **L-L7:** Token-Meter-Pricing-Row ist **additiv** — kein bestehender Eintrag wird geändert.
  `unknown model → (0,0) + warn` ist die bestehende Sicherheits-Schiene für unbekannte IDs.
- **L-L8:** Strukturelle Code-Sperre: **kein** LLM-Call darf an `open_position` weitergereicht
  werden ohne den bestehenden Validator + Candidate-Filter (Root-Regel 3, unverändert).
  Der Wechsel ändert die Modell-Qualität, nicht die Code-Sicherheits-Architektur.

## §4 Schritt-Sequenz

### Schritt 1 — `phase4_research/research/llm_factory.py` (neu)

- Funktion `build_llm_client(config, *, max_tokens, temperature, timeout_s, token_meter_path) -> LLMClientLike`
- Verzweigung auf `config.llm_provider`:
  - `"anthropic"` (Default, rückwärtskompatibel): `LLMClient(model=..., api_key=get_credential("anthropic_api_key"), ...)`
  - `"openai_compat"`: `OpenAICompatLLMClient(model=..., base_url=config.llm_base_url, api_key_service=config.llm_api_key_service, ...)`
- Vollständig typisiert (`_LLMLike`-Protocol aus `llm_client.py` als Rückgabe-Typ)
- Module-Docstring erklärt die Wahl, die Default-Werte und warum die Factory die einzige
  Schnittstelle für Wiring-Code ist (so dass `scripts/wiring.py` in allen erlaubten Phasen nur
  `build_llm_client(config)` aufrufen muss, nicht direkt `LLMClient(...)`)
- Test-Pin: `test_factory_anthropic_returns_LLMClient_instance`, `test_factory_openai_compat_returns_OpenAICompatLLMClient_instance`, `test_factory_default_is_anthropic`, `test_factory_unknown_provider_raises`

### Schritt 2 — `phase4_research/research/models.py`

- Neue Felder in `ResearchConfig`:
  - `llm_provider: str = "anthropic"` (Locked-Default; wird durch L-D5 zu `openai_compat` umgestellt)
  - `llm_base_url: str = "https://api.minimax.chat/v1"` (Locked-Default; per L-D2 zu verifizieren)
  - `llm_api_key_service: str = "trading-bot-minimax-bot"` (Locked-Default)
- `_DEFAULT_PRICING_USD_PER_MTOK` additive Row: `"minimax/MiniMax-M3": (0.30, 1.50)` mit ⚠-Kommentar (Preis-Annahme, verifizieren)
- Doc-Update: Erklärung der drei neuen Felder + Cross-Ref auf `llm_factory.py`

### Schritt 3 — `phase4_research/scripts/wiring.py`

- `LLMClient`-Direktimport (`from research.llm_client import LLMClient`) bleibt für den
  `anthropic`-Pfad; **kein Entfernen** des Imports (Rückwärtskompatibilität)
- Neue Imports: `from research.llm_factory import build_llm_client`, `from research.llm_openai_compat import OpenAICompatLLMClient`
- Ersetze `llm = LLMClient(model=config.model, ...)` durch `llm = build_llm_client(config, max_tokens=..., temperature=..., timeout_s=..., token_meter_path=str(_USAGE_LOG))`
- Doc-Update: erklärt, warum die Factory der einzige Pfad ist
- **Keine** Änderung am Live-Verhalten, solange `config.llm_provider == "anthropic"` (Default)

### Schritt 4 — `scripts/store_minimax_bot_key.py` (neu)

- Vorlage: wortgleich `scripts/store_minimax_key.py` mit folgenden Änderungen:
  - `SERVICE_NAME = "trading-bot-minimax-bot"`
  - `USERNAME = "minimax_bot_api_key"`
  - Doc-String: erklärt, dass dieser Key für den **Bot** ist, nicht für den Claude-Code-Dev-Harness
- Operations: `--status` zeigt ✓/✗ (kein Wert), `--delete` idempotent, Standard-Prompt via getpass + Confirm

### Schritt 5 — `phase4_research/tests/test_llm_factory.py` (neu)

- 6–8 Tests, alle gemockt (kein Netzwerk-Call):
  - `test_factory_default_provider_is_anthropic` — Default-Verhalten rückwärtskompatibel
  - `test_factory_anthropic_uses_anthropic_api_key_credential` — Key-Lookup gegen `tradingbot`-Service
  - `test_factory_openai_compat_uses_configured_api_key_service` — Key-Lookup gegen `trading-bot-minimax-bot`-Service
  - `test_factory_openai_compat_uses_configured_base_url` — base_url-Override
  - `test_factory_openai_compat_returns_instance_with_ask_candidate` — Interface-Parität (`ask_candidate`, `.model`, `.last_usage`)
  - `test_factory_unknown_provider_raises_ValueError` — fail-closed bei Tippfehler
  - `test_factory_passes_max_tokens_temperature_timeout_through` — alle 3 Knobs werden durchgereicht
  - `test_factory_unknown_model_minimally_logs_warning_not_crash` — Token-Meter-Resilience (separater Test, der `estimate_cost` mit MiniMax-Modell-ID aufruft → `(0,0)` + warn, kein Crash)

### Schritt 6 — `pytest tests/ -v` grün-Sweep

- Mindestens P4-Suite bleibt grün (`≥163`), plus die neuen Factory-Tests
- Σ-Regression: keine andere Suite verändert (kein Cross-Phase-Code-Touch außer P4)
- Doc-Rotation-Hook (`scripts/check_doc_rotation.py`) bleibt grün — kein neues File im
  Phase-Head-Verzeichnis ohne INDEX-Eintrag

### Schritt 7 — Doku-Updates (additiv, kein Edit an vorhandenen Locked-Plänen)

- `phase4_research/CLAUDE.md`: 🔁-Note unter dem Header „Phase-16-L-Subphase (LLM-Switch, 2026-10-07)" — verweist auf Factory + neue Config-Felder; ändert nichts an Phase-4-Decisions
- `phase16_activation/CLAUDE.md`: `## Session stopped — 2026-10-07 (MiniMax-M3-Exec-Session #36)` Block (dieser Session); `updated:`-Zeile ergänzen
- `docs/INDEX.md`: 2 neue Zeilen — `phase16_activation/PHASE16_LLM_SWITCH_PLAN.md` (dieser Plan) + `scripts/store_minimax_bot_key.py`

### Schritt 8 — Commit + INDEX

- **Commit 1:** `phase4: factory + openai-compat wiring + M3 pricing + store-script + tests (Phase 16 L-Subphase)` (eigenständig committbar nach Schritten 1–6)
- **Commit 2:** `phase16: docs — L-Subphase plan + session #36 block + INDEX` (Schritt 7)
- **Nicht in den Commits:** `config.llm_provider` Default-Flip auf `openai_compat` — der kommt
  erst nach Demo-Smoke-PASS (Nikinger-Aktion, siehe L-D7)

### Schritt 9 — Operator-Smoke (Nikinger, getrennt vom Exec)

- `python scripts/store_minimax_bot_key.py` → Key eingeben
- `python phase4_research/scripts/openrouter_smoke.py --model <MiniMax-Modell-String aus L-D1>` → erwartet PASS (valid abstain oder valid pick)
- Bei FAIL: `config.llm_provider` Default **nicht** flippen, Diagnose zurück in Phase-16-L-Plan

### Schritt 10 — Default-Flip (Nikinger-Aktion, dokumentiert)

- Nach Demo-PASS: Edit auf `ResearchConfig.llm_provider = "openai_compat"` (nur diese Zeile)
- Service-Restart über `systemctl --user restart tradingbot-scheduler.service`
- Erster Produktions-Cycle zeigt im Log: `llm_provider=openai_compat`, `model=minimax/MiniMax-M3`, Key-Lookup gegen `trading-bot-minimax-bot`
- Beobachtungsposten für Tag 2–5: Token-Count vs. Anthropic-Quote (~10× weniger erwartet)

## §5 Follow-ups (eigene Sessions, nicht in dieser Subphase)

| # | Was | Warum nicht jetzt |
|---|---|---|
| L-FU1 | P5/7/8/15 `scripts/wiring.py` auf Factory umstellen | Cross-Phase-Freigabe OK, aber qualitativ kleinerer Hebel (P4 = ~94 % der Token-Masse, R6 Session #34) — erst nach 1 Woche P4-Live-Daten |
| L-FU2 | P6 (Debatte) auf openai_compat erwägen | Cross-Phase-Sperre (P6 nicht in Phase-16-Liste); qualitative Bedenken (Judge-Synthesis) |
| L-FU3 | K6-Threshold neu denken (Token-Cap → Cost-Cap) | Wenn P4-Live-Daten 1 Woche stabil sind, ist die ökonomische Begründung klar; ohne Daten bleibt K6 ein willkürlicher Cap |
| L-FU4 | `wiring.py:1240`-Style-Drift-Sweep in den geänderten Phasen | Code-Review, nicht im aktuellen Scope |
| L-FU5 | Live-Account-Schaltung | Erste separate Phase nach Tag-10-Closeout, mit Demo-Subphase dazwischen |

## §6 Akzeptanz (für „Subphase L done")

- **AK-L1:** Factory in P4 vorhanden + ≥6 Tests grün + Σ-Regression 0
- **AK-L2:** `ResearchConfig.llm_provider/base_url/api_key_service` drei neue Felder mit ⚠-Hinweis-Kommentar
- **AK-L3:** `_DEFAULT_PRICING_USD_PER_MTOK` additive M3-Row
- **AK-L4:** `scripts/wiring.py` (P4) ruft Factory statt direkt `LLMClient`
- **AK-L5:** `scripts/store_minimax_bot_key.py` vorhanden + `--status`/`--delete` funktionieren (Demo-Test)
- **AK-L6:** Smoke gegen MiniMax: PASS (Nikinger-Aktion, in §4 Schritt 9)
- **AK-L7:** Default-Flip **nicht** in den Commits — explizit als Nikinger-Aktion dokumentiert
- **AK-L8:** Doku-Updates additiv, Phase-4-Decisions unverändert

## §7 Out-of-Scope (für diese Subphase)

- Andere Hersteller (OpenAI direkt, Google, Mistral) — nur MiniMax-via-OpenAI-Compat
- Asynchrone LLM-Calls — Forschungs-Layer bleibt synchron
- Caching — bestehendes `cache_system`-Flag (Phase 6) bleibt unverändert
- Streaming / Tool-Use — kein Use-Case
- Kosten-Auto-Pilot / dynamische Provider-Switch — out
- Live-Account-Schaltung — out (eigene Subphase)