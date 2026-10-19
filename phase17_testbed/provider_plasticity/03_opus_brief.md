---
status: brief-for-opus-session
purpose: Einseitiges Briefing für die Opus-Session, die einen Miniplan schreiben soll. Antwortet in der Reihenfolge: Frage, Scope, Lieferform, was Opus mitbringen muss.
read-when: Opus-Session, die das Miniplant erstellt (zum Start lesen)
detail: L2
up: ./README.md
down:
  - ./04_open_questions.md   # das, was Opus vorher klären muss
created: 2026-10-19
---

# 03 — Opus-Brief: Provider-Plastizität Miniplan

> **Adressat:** die nächste Opus-Session (Browser oder Claude Code, je nach Setup
> des Nikinger). Eingangslektüre in dieser Reihenfolge:
> `01_decision_proposal.md` (T25–T28) → diese Datei → `02_current_state.md` (was
> schon da ist) → `04_open_questions.md` (was Nikinger noch entscheidet).

---

## §0 — Die Frage in einem Satz

**Wie muss die LLM-Endpoint-Abstraktion des Trading-Bots umgebaut werden, damit
der Bot mit allen „gängigen" Providern funktioniert (Anthropic, OpenAI,
OpenRouter, DeepSeek, Qwen/DashScope, GLM/Zhipu, perspektivisch Moonshot/Doubao/
Baichuan) — ohne pro Provider einen Code-Commit?**

## §1 — Scope (was IN den Miniplan gehört)

1. **Endpunkt-Abstraktion:** _eine_ Stelle (Plan §6 C-4: `_build_llm` in
   `wiring.py`). Anthropic bleibt direkt (`LLMClient`); alles andere geht über
   `OpenAICompatLLMClient`. Keine dritte Implementierung.
2. **Provider-Konfiguration:** `ProviderSpec` (frozen dataclass, Plan §6 C-1)
   wird um `QuirkSpec` erweitert. `QuirkSpec` enthält pro Provider mindestens:
   `max_tokens_field`, `response_format_policy`, `extra_headers`, `streaming`.
3. **Config-Datei (oder Inline-Default):** `PROVIDERS` wandert in eine
   `config/providers.yaml` (oder eine alternative Form, die Nikinger entscheidet
   — siehe `04_open_questions.md`). `check_llm_profile` validiert die geladene
   Datei beim Start und wirft `ValueError` mit der genauen Stelle (Datei:Zeile),
   wo etwas fehlt.
4. **OpenAI-Compat-Härtung:** pro-Provider konfigurierbar. Default = „OpenAI-
   strict" (= heutiges Verhalten, Bit-für-Bit grün).
5. **Smoke-Skript:** `scripts/openrouter_smoke.py` wird zu
   `scripts/provider_smoke.py` mit `--provider`-Switch; bestehende Aufrufe
   bleiben funktional (Default `openrouter`).
6. **Pricing + Exempt-Liste** werden in dieselbe YAML-Datei gezogen; Doppelpflege
   entfällt.
7. **Live-Verifikation:** pro neu aufgenommenem Provider ein Live-Smoke gegen
   die Demo-Pfade — nichts wird als „verbindlich" committet, was nicht live
   belegt ist.

## §2 — Scope (was NICHT in den Miniplan gehört)

- **Keine Strategie-/Edge-Bewertung** (Phase-17-Prinzip bleibt gültig).
- **Keine Modell-Empfehlung** (welches Modell kaufen wir für was — Entscheidung
  des Nikinger, nicht des Miniplans).
- **Keine Adapter-Tests gegen die echten Demo-Konten** der chinesischen
  Anbieter — der Miniplan beschreibt das Vorhaben, die Tests laufen in der
  Exec-Session (Nikinger führt die Live-Smokes selbst durch, gemäß
  Plan-§14.1 „C-7 Familien-Smoke").
- **Keine Token-Budget-Reform** (das ist Block D, separat).
- **Keine Force-Trigger- oder Live-Money-Änderung** (Hard Rule 4 + 5).

## §3 — Lieferform des Miniplans

Der Miniplan muss **ausführungsreif** sein — d.h. eine Folge-Session kann ihn
ohne Rückfragen in Commits umsetzen, so wie es Phase-17-Hauptplan für Blöcke A–E
ist. Strukturell:

| Sektion | Inhalt |
|---|---|
| BLUF | Empfehlung in 3 Sätzen |
| **Entscheidungen E1–E8** | was Opus bei welchen Nikinger-Fragen vorschlägt (jeweils mit Begründung) |
| **Ist-Stand mit Datei:Zeile** | gegen Code, alles selbst gemessen — Verweise auf `./02_current_state.md`, aber jeder Miniplan-Block steht für sich |
| **Quirk-Tabelle** | je Provider: `max_tokens_field` / `response_format_policy` / `extra_headers` / `streaming` / Preis-Status / Verifikations-Stand |
| **Step-Plan** (atomar, ein Commit pro Step) | analog Phase-17-Hauptplan §6: pro Step **Ziel → Anker → Edit → Tests → Akzeptanz** |
| **Validierungs-/Pre-Flight-Strategie** | wie wird beim Start jeder neue Provider gegen `check_llm_profile` validiert |
| **Live-Smoke-Reihenfolge** | welcher Provider wird in welcher Reihenfolge live-probiert |
| **§8 Fehlgriffe** | die typischen Fehler, die ein neuer Provider mitbringt (Endpoint-Drift, Pricing-Drift, Key-Drift, Rate-Limit-Drift, Response-Format-Drift) |
| **AK1–AKN** | Akzeptanzkriterien für die Block-C2-Commits |
| **Block-Bezeichnung + Phasen-Zuordnung** | „gehört in Phase 17 zwischen B-5 und E-1?" oder „eigene Phase 18?" (Nikinger entscheidet in `04_open_questions.md`) |

## §4 — Was die Opus-Session an Vorbereitung mitbringen muss

- **Quirk-Tabelle** für mindestens 4 Provider: DeepSeek, Qwen/DashScope,
  GLM/Zhipu, modernes OpenAI. Erste 2 sind OpenAI-kompatibel, GLM hat
  Besonderheiten (z.B. „all-tools-must-be-empty"), modernes OpenAI hat
  `max_completion_tokens`.
- **Eine** Gegenprüfung der OpenRouter-Endpoints (welche Modelle aktuell
  verfügbar sind, welche Quirks dokumentiert sind).
- **Konkrete Validierungs-Beispiele:** wie sehen typische Fehler im
  `check_llm_profile` aus (z.B. Preiszeile fehlt, Exempt-Liste vergessen,
  base_url ohne Trailing-Slash, Key-Provider ohne `api_key_service`)?
- **Vorschlag für die Phasen-Zuordnung** (eigener Block C2 in Phase 17 vs.
  Phase 18). Begründung anhand der Step-Granularität + Review-Gate-Logik.
- **Konfig-Form-Empfehlung** (YAML vs. Python-Datei vs. Env-Vars). Begründung
  anhand Versionierbarkeit, Hot-Swap, Operator-Aufwand.
- **Mindestens 1 Mini-Backfill-Test-Skizze** (welche Tests +wie viele in
  welcher Suite; Anker im bestehenden Test-Pattern).

## §5 — Verbindlichkeiten (vom Phase-17-Hauptplan, muss der Miniplan respektieren)

- **T13 Cross-Phase-Freigabe:** Code in P1, P4, P5, P8, P10, P12, P14, P15, P16;
  P2 nur in Tests; **kein Code in P6/P7/P13**. Provider-Plastizität wird voraussichtlich
  P4 (`llm_openai_compat.py`), P8 (`llm_profiles.py`, `wiring.py`), P16
  (`autonomy_report.py` Smoke-Sektion) anfassen — alle innerhalb T13.
- **T17 Profile sind Code-Defaults** — kein CLI-Flag. Rollback = Commit-Revert +
  Restart. Falls die YAML-Config-Diskussion gegen T17 läuft, muss Opus das
  begründen.
- **T22 Executor:** Miniplan wird von Opus geschrieben (Browser / Claude Code),
  nicht von der Exec-Session. Ausführung kommt erst, wenn Nikinger den Miniplan
  freigibt.
- **Plan §14 Provider-Wechsel-Logik (GLM via z.ai, Endpoint `/paas/v4` nie
  `/coding/`)** bleibt gültig; falls GLM in den Miniplan aufgenommen wird,
  übernimmt der Miniplan die Logik verbatim.
- **Step-0-Ritual** (`grep turbo`, `grep EPIC_MAP`, Quellenvergleich) gilt auch
  für die Miniplan-Session.

## §6 — Was die Opus-Session _nicht_ muss

- **Keine Code-Edits.** Der Miniplan beschreibt; die Commits führt eine spätere
  Exec-Session.
- **Keine Live-Probes.** Die führt Nikinger (Plan-§14.1 „C-7 Familien-Smoke",
  jeder Provider einzeln).
- **Keine Preisrecherche „was kostet was pro 1M Tokens"** — das misst der
  Budget-Block später. Miniplan listet nur die Slots.
- **Kein Force-Trigger-Test** (Hard Rule 4 + 5).
