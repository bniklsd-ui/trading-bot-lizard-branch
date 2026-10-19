---
status: proposal
purpose: T25–T28-Skizze für die Provider-Plastizität — gelockte Entscheidung Nikinger 2026-10-19, mit Begründung. Kein Plan, sondern Input für die Opus-Session.
read-when: Opus-Session, die das Miniplant erstellt
detail: L2
up: ./README.md
down:
  - ./02_current_state.md   # was der Code heute kann (Lücken hier nur erwähnt, Detail drüben)
  - ./03_opus_brief.md      # das eigentliche Briefing
created: 2026-10-19
---

# 01 — Decision Proposal: Provider-Plastizität

> 🟡 **Überholt 2026-10-19:** T25–T28 dieser Skizze sind in Plan §15.2 als **T25–T30** neu gefasst und gelockt —
> abweichend: keine `QuirkSpec`-Klasse, kein YAML, kein Streaming/`extra_headers`/`response_format_policy`
> (Begründung je Zeile dort).

> **Quelle der Wahrheit ist der Code.** Diese Notiz ist ein Vorschlag, kein Plan.
> Stand: Nikingers Auftrag 2026-10-19, unmittelbar nach B-4 (Session #4 ENDE).

## Die Entscheidung (Nikinger 2026-10-19, wörtlich)

> „der Endpunkt für trading bot Aktivitäten sollte so umgebaut werden, das er
> mit sämtlichen ‚gängigen' Endpunkten funktioniert (antrhopic, openai, die
> chinesischen Anbieter etc)."

Interpretation der Exec-Session 2026-10-19:

- **Nicht** nur „ein zusätzlicher Provider-Wechsel" (das wäre Block C).
- **Sondern:** die Endpoint-Abstraktion wird so erweitert, dass das Hinzufügen
  eines neuen Providers ohne Code-Edit im LLM-Routing möglich wird.
- **„Gängige" Provider** = mindestens Anthropic, OpenAI, OpenRouter, DeepSeek,
  Qwen/DashScope, GLM/Zhipu. Moonshot, Doubao, Baichuan als „Operator-erweiterbar".

## Was im aktuellen Code schon da ist (Verweis, nicht Detail)

| Stein | Datei | Ist-Stand |
|---|---|---|
| Provider-Registry | `phase8_scheduler/scheduler/llm_profiles.py` (`PROVIDERS`) | 2 Einträge hartkodiert (`anthropic`, `minimax`) |
| Per-Rolle-Spec | `phase8_scheduler/scheduler/llm_profiles.py` (`RoleSpec`) | `provider / model / max_tokens / timeout_s` |
| Profile-Dict | `phase8_scheduler/scheduler/llm_profiles.py` (`LLM_PROFILES`) | 3 Profile: `anthropic`, `research_m3`, `all_m3` |
| OpenAI-Compat-Client | `phase4_research/research/llm_openai_compat.py` | OpenAI-Annahmen (siehe `02_current_state.md`) |
| Validierung beim Start | `check_llm_profile(profile, pricing, default_models, exempt_models)` | 4 Regeln |

**Detail siehe `02_current_state.md`.**

## Die Lücken — was heute nicht geht

Auf Basis der Plan-§6-C-Sektion + der LLM-Client-Inspektion 2026-10-19:

1. **Provider-Liste ist Code, nicht Config.** Jeder neue Provider = Git-Commit
   am `PROVIDERS`-Dict + `check_llm_profile`-Call-Site.
2. **`OpenAICompatLLMClient` ist OpenAI-strict.** `max_tokens` (modernes OpenAI
   will `max_completion_tokens`), `response_format={"type":"json_object"}` (Qwen
   lehnt das ab, will Prompt-Instruction), kein Custom-Header-Slot, kein
   Streaming-Toggle.
3. **Per-Provider-Quirks sind fall-through** statt individuell: ein einziger
   400→drop-response_format-Fallback. Qwen/DashScope haben z.B. eigene
   `incremental`-JSON-Option, Doubao eigene `thinking`-Felder, GLM eigene
   „all-tools-must-be-empty"-Sonderprüfung.
4. **Pricing-Ausnahmeliste (`budget_exempt_models`) ist modellblind.** Drei
   Stellen müssen dieselbe Liste kennen; neue Provider = drei Edits.

## T25–T28 — Skizze (Vorschlag Exec-Session, **nicht** gelockt)

| ID | Kern | Plan-Destination |
|---|---|---|
| **T25** | Eine Abstraktion für alle Endpoints — `OpenAICompatLLMClient` und `LLMClient` (Anthropic) sind die einzigen beiden Implementierungen; jeder Provider ist ein `ProviderSpec`-Eintrag + ein `QuirkSpec`-Eintrag. **Keine** if/else pro Provider im Code. | Plan §1 + §6 (neuer Block C2: Provider-Plastizität) |
| **T26** | `OpenAICompatLLMClient` wird per-Provider konfigurierbar: `max_tokens_field ∈ {"max_tokens","max_completion_tokens"}`, `response_format_policy ∈ {"strict","drop-on-400","never"}`, `extra_headers: Mapping[str,str]`, `streaming: bool`. Default = OpenAI-strict, kein Verhalten bricht. | Plan §6 C-3 (Erweiterung von `llm_openai_compat.py:107`) |
| **T27** | `ProviderSpec` bekommt `quirks: QuirkSpec`. `check_llm_profile` akzeptiert neue Provider ohne Code-Edit (Default-Quirks = openai-strict). Provider-Liste wandert in eine `config/providers.yaml` (mit JSON-Schema-Validierung); `ProviderSpec` lädt sie beim Start. | Plan §6 C-1 + C-2 (Erweiterung `llm_profiles.py`) |
| **T28** | Miniplan-Modus für die Opus-Session: (a) Quirk-Tabelle als Operator-Doku (Provider → Quirks, mit Live-Verifikations-Status), (b) Client-Umbau, (c) Validierung, (d) Operator-Smoke pro Provider. Erst der Miniplan, dann die Commits. | Plan §0 Miniplan-Reihenfolge |

## Was die Opus-Session klären soll (siehe `04_open_questions.md`)

- **Provider-Liste.** Welche namentlich, welche „operator-erweiterbar".
- **Phasen-Zuordnung.** Gehört C2 in Phase 17 (zwischen B-5 und E-1) oder in eine
  eigene Phase 18 (höhere Wahrscheinlichkeit, weil Step-Granularität + Review-Gate)?
- **Config-Datei oder YAML?** Trade-off: Versionierbarkeit (YAML in Git) vs.
  Runtime-Hot-Swap (YAML an dynamic path).
- **Live-Verifikation pro Provider.** Welche Provider werden vor jedem Step
  live-probiert (Smoke), welche nur dokumentiert?

## Verbindung zum bestehenden Plan

- **T16** (Plan §6 C-4) bleibt richtig: Composition Root bleibt `wiring.py`.
- **§6 C-7** (Familien-Smoke) wird von „GLM only" auf „alle aktiven Provider"
  erweitert.
- **`scripts/openrouter_smoke.py`** wird zu `scripts/provider_smoke.py`
  (mehrere `--provider` Endpoints), bestehende Backwards-Compat erhalten.
