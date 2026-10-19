---
status: needs-decisions-from-nikinger
purpose: Was die Opus-Session vom Nikinger zurückfragen muss, bevor sie plant. Kein Material hier ist gelockt; jeder Eintrag wartet auf eine Nikinger-Entscheidung.
read-when: Opus-Session _bevor_ sie den Miniplan schreibt
detail: L2
up: ./README.md
down:
  - ./03_opus_brief.md   # wie diese Fragen in den Miniplan einfließen
created: 2026-10-19
---

# 04 — Open Questions (Nikinger)

> Jede dieser Fragen muss vor dem Miniplan-Commit entschieden sein. Reihenfolge
> wie hier — wer Phase-17-Logik kennt, kann manche schon am Telefon klären.

## Q1 — Provider-Liste (Wahl der „gängigen")

Die Exec-Session schlägt **6 Provider** als Default-Set vor:
Anthropic, OpenAI, OpenRouter, DeepSeek, Qwen/DashScope, GLM/Zhipu.

| Provider | HTTP-Form | Heute verifiziert? | Im Default-Set? (Y/N/Maybe) |
|---|---|---|---|
| Anthropic | `api.anthropic.com` (REST) | ja, voll | _Nikinger_ |
| OpenAI | `api.openai.com/v1/chat/completions` | nein (Bot nutzt heute Anthropic-only) | _Nikinger_ |
| OpenRouter | `openrouter.ai/api/v1/chat/completions` | ja (M1 Step 10) | _Nikinger_ |
| DeepSeek | `api.deepseek.com/v1/chat/completions` | nein (Doku, kein Live-Probe) | _Nikinger_ |
| Qwen / DashScope | `dashscope.aliyuncs.com/compatible-mode/v1/chat/completions` | nein | _Nikinger_ |
| GLM / Zhipu | `api.z.ai/api/paas/v4/chat/completions` | nein (Plan §14) | _Nikinger_ |
| Moonshot / Kimi | `api.moonshot.cn/v1/chat/completions` | nein | _Nikinger_ (Operator-erweiterbar?) |
| Doubao / Volcengine ARK | `ark.cn-beijing.volces.com/api/v3/chat/completions` | nein | _Nikinger_ (Operator-erweiterbar?) |
| Baichuan | `api.baichuan-ai.com/v1/chat/completions` | nein | _Nikinger_ (Operator-erweiterbar?) |

**Entscheidung benötigt:**
- Welche 4–6 Namen sind **Default** (gehen in `config/providers.yaml` mit)?
- Welche sind **„operator-erweiterbar"** (gehen nur als Beispiel in die Doku)?
- Welche sind explizit **nicht im Scope** (z.B. wenn der Nikinger keinen
  chinesischen Anbieter einkaufen will)?

## Q2 — Phasen-Zuordnung (Block C2 in Phase 17 oder neue Phase 18?)

| Pfad | Pro | Contra |
|---|---|---|
| **Block C2 in Phase 17** (zwischen B-5 und E-1, ca. 4–8 Steps) | Miniplan landet direkt im laufenden Phase-17-Hauptplan; Tests zählen sofort in den Σ-Sweep; Review-Gate vor E-3 (Anthropic-Schwerpunkt) sieht auch Block C2 | Phase 17 wird länger; bisherige 5 Blöcke (A–E) bekommen einen sechsten — Namens-Drift; Step-Granularität + Review-Gate-Müdigkeit |
| **Eigene Phase 18** („Provider-Plastizität" oder ähnlich) | klare Trennung; eigener Plan-Commit, eigener Phasenkopf; Plan §14 bleibt 1:1 lesbar | neue Phase = eigenes Handover, neuer Pre-Maintenance-Aufwand; der §14-GLM-Endpoint ist heute schon Phase-17-„Block C2-äquivalent" — Bruch |

**Entscheidung benötigt:** A oder B (oder hybrid: Phase 17 mit `Block C2` als
informeller Untertitel, ohne den Hauptplan §0–§6 umzubenennen).

## Q3 — Konfig-Form

| Form | Pro | Contra |
|---|---|---|
| **YAML** in `config/providers.yaml` | versionierbar; diff-fähig; Editor-tauglich; Schema-Validierung mit JSON-Schema | zusätzliche Dep (PyYAML schon da? — Opus prüft); ein Pfad mehr |
| **Python-Dataclass-Defaults** in `llm_profiles.py` | bleibt im Code, eine Quelle; Type-Sicherheit | jeder neue Provider = Git-Commit (genau die Lücke aus der Exec-Session) |
| **ENV-Vars** in `tradingbot-scheduler.service` | hot-swap-fähig; keine zweite Datei | schwer versionierbar (mehrere `.env`-Files, Snapshot-Drift); kein Diff in PR-Reviews |

**Empfehlung Exec-Session (nicht gelockt): YAML**, weil die Lücke aus
Decision-Proposal genau „Provider-Liste ist Code, nicht Config" war und YAML das
_ohne_ Hot-Swap-Versprechen schließt. Aber T17 sagt „Profile sind Code-Defaults"
— Konflikt. Bitte klären.

## Q4 — Live-Verifikation pro Provider

| Stufe | Was | Wer |
|---|---|---|
| **Doku-only** | Anbieter-Doku lesen, Endpoints notieren | Opus-Session |
| **Live-Smoke** | einen Call pro Provider gegen den Demo-Key | Nikinger (Operator) |
| **Pro Endpoints/Provider** | mehrere Endpoints (Anthropic hat `/v1/messages`, OpenAI `/v1/chat/completions`, DashScope „compatible-mode" + „generation") | Nikinger |

**Entscheidung benötigt:** welcher Provider bekommt welche Stufe? Vorschlag
Exec-Session: **alle Default-Set-Provider bekommen Live-Smoke vor Commit**;
„operator-erweiterbar" bleibt Doku-only.

## Q5 — Backwards-Compatibility zu Block C (Plan §6)

Heute geplant: 2 Clients (`LLMClient`, `OpenAICompatLLMClient`), 3 Profile
(`anthropic`, `research_m3`, `all_m3`), 1 Standard-Config (`anthropic`).

**Frage:** wenn der Miniplan die `OpenAICompatLLMClient`-Per-Call-Optionen
einführt (Plan §6 C-3 abgedeckt) und die `QuirkSpec`-Datenstruktur (C-1
erweitert um `quirks: QuirkSpec`) — bleibt der bestehende Plan §6 C-1
verbatim, oder muss er angepasst werden?

**Vermutung Exec-Session:** §6 C-1 wird um **eine** Zeile (`quirks: QuirkSpec`)
erweitert; §6 C-3 wird um 4 Per-Provider-Options ergänzt; §6 C-4 bleibt
verbatim. **Miniplan entscheidet das.**

## Q6 — Verbindung zum Bericht (Block E)

`scripts/autonomy_report.py` hat heute K7 ohne LLM-Profil (Plan §3 D11). Wenn
die Provider-Plastizität mehr als 2 Profile einführt, muss K7 diese zählen
oder um eine Tabelle erweitert werden.

**Entscheidung benötigt:** wird Block E (Prereg v5) im Miniplan mit-erwähnt
oder getrennt behandelt? Vermutung: Miniplan sagt nur „Anker für Block E",
ohne E zu planen.

## Q7 — Token-Budget-Ausnahmen (Plan §6 D-1)

Heute: `SchedulerConfig.budget_exempt_models = ("MiniMax-M3",)`. Wenn GLM,
DeepSeek, Qwen dazukommen — gleiche Liste, oder neue Liste pro
Provider-Klasse („chinesische Anbieter")?

**Vermutung Exec-Session:** eine Liste, alphabetisch. Miniplan entscheidet.

## Q8 — Phase-17-Closeout-Reihenfolge

Wenn der Miniplan in Phase 17 integriert wird (Q2 = A), ändert sich die
Abnahme-Reihenfolge: Prereg v5 muss **nach** Block C2 stehen, sonst enthält
sie noch keine Profil-Tabelle.

**Entscheidung benötigt:** wird die Miniplan-Ausführung vor E-3 (Plan §0
„Restart in E-3") abgeschlossen, oder danach in einem „Phase-17.5"-Block?

---

## Antwortformat (für Nikinger)

Am liebsten als knapper Antwortblock, der diese Datei aktualisiert:

```
Q1: Default = Anthropic, OpenAI, OpenRouter, DeepSeek, GLM/Zhipu.
    Operator-erweiterbar = Qwen, Moonshot, Doubao, Baichuan.
    Nicht im Scope = —
Q2: Phase 17, Block C2 (kein Phase-18).
Q3: YAML.
...
```

Die Exec-Session würde Q1–Q8 in `04_open_questions.md` als entschieden markieren
(`✅` jeweils), bevor die Opus-Session loslegt.
