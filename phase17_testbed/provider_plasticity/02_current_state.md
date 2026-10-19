---
status: code-as-of-2026-10-19
purpose: Was der Code heute schon kann (Anker + Verbatim-Stellen, gegen die die Opus-Session ihre Miniplan-Commits pinnt). Nichts interpretiert, nur beschrieben.
read-when: Opus-Session beim Erstellen des Miniplans
detail: L2
up: ./README.md
down:
  - ./01_decision_proposal.md   # welche Lücken diese Bestandsaufnahme belegt
  - ./03_opus_brief.md          # die Verwertung im Briefing
created: 2026-10-19
---

# 02 — Current State: Provider-Routing im Code (2026-10-19)

> 🟡 **Korrigiert gegen Code 2026-10-19 (Plan-Session Opus 5.5):** Zeilenangaben sind verschoben —
> `llm_openai_compat.py` `max_tokens` Z. 264 (nicht 254), `response_format` Z. 266 (nicht 256), Keyring-Lookup Z. 174
> (nicht 170); `wiring.py`-Konstruktionen heute Z. 331/362/428/445/525/582/740 (nicht 313/344/390/400/470/527/685).
> Die Qwen/Doubao/GLM-Annahmen in §I sind durch Doku-Abruf ersetzt (Plan §15.3); „Qwen lehnt `json_object` ab" ist
> **nicht** belegt. Quelle ist jetzt Plan §15.

> **Source of Truth ist der Code.** Belegt gegen Plan-§6 (Commit-Bereitschaft
> 2026-10-17, Plan-Session Opus 5.5; §14-Nachtrag 2026-10-18).
> Zeilennummern = Stand HEAD-~origin/main von Session #4.

## A. `phase8_scheduler/scheduler/llm_profiles.py`

Vom Plan §6 C-1 noch **nicht implementiert** (Block C ist ⏳, siehe
`../CLAUDE.md` Status-Tabelle). Aktuell existieren nur:

| Stück | Heute | Anmerkung |
|---|---|---|
| `LLM_ROLES` | _fehlt_ | wird in C-1 als `("research", "debate", "lesson", "instinct", "reflect", "paper_debate")` definiert |
| `ProviderSpec` (frozen dataclass) | _fehlt_ | Plan: `kind / base_url / api_key_service / api_key_username` |
| `RoleSpec` (frozen dataclass) | _fehlt_ | Plan: `provider / model / max_tokens / timeout_s` |
| `PROVIDERS` (dict) | _fehlt_ | Plan: 2 Einträge (`anthropic`, `minimax`) — code-default |
| `LLM_PROFILES` (dict) | _fehlt_ | Plan: 3 Profile (`anthropic`, `research_m3`, `all_m3`) |
| `role_spec(profile, role) -> RoleSpec` | _fehlt_ | wirft ValueError |
| `check_llm_profile(profile, *, pricing, default_models, exempt_models)` | _fehlt_ | 4 Regeln, ValueError |

**Heute in Wiring (P8):** die Profil-Logik existiert **nicht**. Alle 6 heutigen
Client-Konstruktionen in `scripts/wiring.py` (Z. 313, 344, 390, 470, 527, 685 —
Plan §5) sind hartkodiert `LLMClient(...)` für Anthropic.

## B. `scripts/wiring.py` — die 6 heutigen Client-Konstruktionen

| Z. | Rolle | Konstruktor | Modell | Caller |
|---|---|---|---|---|
| 313 | research | `LLMClient` | `config.model` | `_build_research` |
| 344 | debate | `LLMClient` (`cache_system=True`) | `cfg.model_judge` | `_make_debate_runner._build` |
| 390 | lesson | `LLMClient` | `cfg.lesson_model` | `_build_reward_sink` |
| 400 (B-3) | instinct | `LLMClient` (zweiter, eigenes `max_tokens=2048`, `timeout=60`) | `cfg.lesson_model` | `_build_reward_sink` |
| 470 | reflect | `LLMClient` | `cfg.lesson_model` | `_build_abstain_sink` |
| 527 | paper_debate | `LLMClient` | `dcfg.model_judge` | `_build_paper_engine` |
| 685 | reflect | `LLMClient` | `cfg.lesson_model` | `_build_paper_tracker` |

→ **7 Client-Instanzen, alle heute Anthropic.** Genau **eine** zentrale
Bau-Funktion `_build_llm(role, llm_profile, …)` ist geplant (Plan §6 C-4 Punkt 1).

## C. `phase4_research/research/llm_client.py` — Anthropic-Wrapper

Wichtige Annahmen (gegen `LLMClient._attempt` Z. 378–423 verifiziert 2026-10-17 + B-4-Edit 2026-10-19):

| Stein | Heute | Relevant für Provider-Plastizität? |
|---|---|---|
| `_raw_call(system, user, json_schema=…)` | einmaliger SDK-Call mit `output_config.format` (Structured Outputs) | nein (Anthropic-spezifisch) |
| Meter-First (`B-4`, 2026-10-19) | läuft vor Parse; `stop_reason=="max_tokens"` → `LLMResponseError` ohne Retry | nein |
| Keyring-Username | fest `"api_key"` in `keyring.get_password(self.api_key_service, _KEYRING_USERNAME)` (Z. 170) | nein — Anthropic bleibt single-user-key |

## D. `phase4_research/research/llm_openai_compat.py` — OpenAI-Compat

Der „cold fallback" (Plan-§3 D3, T19), heute noch **nicht** verkabelt. Annahmen:

| Stein | Heute | Lücke für „alle gängigen" |
|---|---|---|
| Default-Endpoint | `https://openrouter.ai/api/v1` (Z. 81) | hartkodiert; Konfig nur über `OpenAICompatLLMClient(base_url=…)` zur Konstruktion |
| Endpoint-Form | `POST /chat/completions` Bearer-Auth | Qwen/DashScope nutzt dieselbe Form (OpenAI-kompatibel) — passt |
| `response_format` | `{"type": "json_object"}` wird **immer** mitgesendet (Z. 256) | Qwen lehnt das mit 400 ab, Doubao ignoriert es, GLM versteht es |
| `max_tokens` | wird **immer** als `max_tokens` mitgesendet (Z. 254) | modernes OpenAI will `max_completion_tokens` (Anthropic will `max_tokens`) — keine Trennung |
| Custom Headers | nicht möglich | manche Provider brauchen `X-Client-Name`, `X-First-Token-Latency`, … |
| Streaming | nicht möglich (immer Non-Stream) | Doubao & DeepSeek liefern schneller mit Stream |
| 400-Fallback (Plan §6 C-3) | einmal ohne `response_format` retry | generisch; pro-Provider-Policy fehlt |
| `<think>`-Strip (Plan §6 C-3 b) | universell nach `re.sub(r"(?s)<think>.*?</think>", "", text).strip()` | bei GLM/Doubao verändert das die Bedeutung nicht; korrekt |
| Keyring-Lookup | `keyring.get_password(self.api_key_service, _KEYRING_USERNAME)` (Z. 170) | Username fest `"api_key"` → pro Provider überschreibbar (Plan §6 C-3 Punkt 2) |
| `last_finish_reason` (B-4, 2026-10-19) | wird pro Call gesetzt | Sensor vorhanden — gut |

## E. Token-Meter (`phase4_research/research/token_meter.py`)

| Stein | Heute | Bezug Plastizität |
|---|---|---|
| `pricing_usd_per_mtok` | Mapping im `ResearchConfig` (P4 `models.py:530+`); pro Modell-ID eine `(input, output)` USD-Zeile | jede neue Provider-Aufnahme = 1 neue Zeile |
| Unbekanntes Modell | Kosten 0 + WARNING (Z. 79–82) | fail-soft — keine Migration nötig |
| Cache-Felder | nur Anthropic sinnvoll (cache_creation_input_tokens, cache_read_input_tokens); OpenAI-Compat füllt sie mit 0 | bleibt |

## F. Token-Budget (`phase8_scheduler/scheduler/budget.py`)

| Stein | Heute | Bezug Plastizität |
|---|---|---|
| `_TOKEN_FIELDS` | summiert alle Records des Tages, modellblind | drei Stellen summieren dasselbe (Plan §3 D10): `budget.py`, `webui/api.py:289-296`, `autonomy_report.py:369-425` |
| `SchedulerConfig.budget_exempt_models` | Default `("MiniMax-M3",)` (Plan §6 C-2) | jeder neue exempt-Provider = Tuple-Erweiterung |

## G. Was heute schon geht (= Plan-§6-C-Scope, **nicht** Block C2 nötig)

1. **Anthropic** bleibt unverändert (LLMClient).
2. **OpenAI-kompatible Provider** (OpenRouter) funktioniert über das bestehende
   `OpenAICompatLLMClient`.
3. **DeepSeek** (OpenAI-kompatibel, gleiche Auth-Form, gleiche Felder) sollte
   mit den bestehenden Defaults funktionieren.
4. **`scripts/openrouter_smoke.py`** ist als Single-Provider-Smoke geschrieben
   (default `https://openrouter.ai/api/v1`).

## H. Was heute NICHT geht (= Plastizitäts-Lücken)

| Lücke | Datei | Neue Anforderung |
|---|---|---|
| Provider-Liste ist Code, nicht Config | `llm_profiles.py` (geplant) | wandert in `config/providers.yaml` oder einen durch `ProviderSpec` abstrahierten Default |
| `response_format` ist OpenAI-strict | `llm_openai_compat.py:256` | per-Provider konfigurierbar (`strict`, `drop-on-400`, `never`) |
| `max_tokens`-Feldname ist hartkodiert | `llm_openai_compat.py:254` | per-Provider wählbar (`max_tokens` vs `max_completion_tokens`) |
| Custom-Header fehlen | `llm_openai_compat.py:192-200` | `extra_headers: Mapping[str, str]` |
| Streaming fehlt | `llm_openai_compat.py:_raw_call` | `streaming: bool` Toggle |
| 400-Fallback ist pauschal | `llm_openai_compat.py` (geplant §6 C-3 a) | per-Provider `response_format_policy` |
| Single-Username-Keyring-Lookup | `_KEYRING_USERNAME = "api_key"` (Z. 82) | pro Provider überschreibbar (Plan §6 C-3 Punkt 2 ist die Spur) |
| Exempt-Liste ist Tuple im Code | `SchedulerConfig.budget_exempt_models` | yaml-Config oder eine zweite Quelle (Konflikt mit „Code-Default" — siehe Nikinger T17) |
| OpenRouter-Smoke ist Single-Provider | `scripts/openrouter_smoke.py` | `--provider`-Switch, mehrere Default-Endpoints |

## I. Wo die Annahmen zu „allen gängigen" herkommen

| Annahme | Beleg | Aktualität |
|---|---|---|
| Qwen lehnt `response_format: json_object` ab | nicht live-verifiziert im Bot (Doku DashScope) | Plan-§14.1 schreibt Live-Probe pro Step vor — nicht gemacht |
| Doubao hat eigene `thinking`-Felder | nicht live-verifiziert (Doku Volcengine ARK) | ungeprüft |
| GLM versteht `response_format: json_object` | Plan-§14 setzt GLM über OpenAI-Compat voraus | ungeprüft für konkrete Felder |
| Modernes OpenAI will `max_completion_tokens` | öffentliche OpenAI-API-Doku, Stabilisierungs-Datum 2024 | aktuell |
| DeepSeek = OpenAI-kompatibel | DeepSeek-API-Doku, live bestätigt durch M1-OpenRouter-Smoke | aktuell |

**Wichtig:** die Tabelle ist **Doku-Stand** und braucht eine Live-Verifikation
in der Opus-Session, bevor Quirks als „verbindlich" committet werden.
