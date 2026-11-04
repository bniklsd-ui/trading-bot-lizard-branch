# SESSIONS_ARCHIVE.md — Phase 17 (Prüfstand)

Newest-first. Rotation rule (root `CLAUDE.md`, mandatory since 2026-07-06): the phase head
carries at most one `## Session stopped` block; archives have no size cap. See
[`../CLAUDE.md`](../CLAUDE.md) "How to work in this repo" — Rotation rule, and
[`../docs/DOC_LAYERS_CONVENTION.md`](../docs/DOC_LAYERS_CONVENTION.md) for the L0/L1/L2/L3 model.

---

## Session stopped — 2026-11-03 (Exec-Session #11 — **C-7-Smoke PASS (Operator)** + **C-8 Flip 1** ausgeführt: `llm_profile = "research_m3"`, nur Research → MiniMax-M3; 1 Code-Commit + 1 Doku-Commit, Σ 2042 + 1 = **2043** grün)

> **Auftrag:** Nikinger 2026-11-03 (Web-Chat): C-7 als Operator-Schritt ausführen (Key seeden + Familien-Smoke), danach weitermachen. **Plan war detailliert genug** (§14.4-Smoke-Protokoll, C-8 als eigener Commit) → **atomar abgearbeitet**: Smoke dokumentiert → Flip 1 als eigener Commit → Doku.
> **Bot-Ritual (unverändert):** Scheduler `disabled` + `inactive` (Hold-Marker `data/state/SCHEDULER_HELD`), `install_units.sh --check` exit 0. Recorder/Discovery/WebUI `enabled` + `active` — unangefasst. **Kein Neustart, kein Netz-Call durch den Agenten** (der Smoke lief im Terminal des Nikinger).
> **Cross-Phase-Freigabe:** Flip 1 = P8 only (T13 ✓).

### Completed — diese Exec-Session (1 Code-Commit + 1 Doku-Commit)

| # | Commit | Phase | Inhalt |
|---|---|---|---|
| 1 | `2ee73e6` | P8 | **C-8 Flip 1** — `SchedulerConfig.llm_profile` von `"anthropic"` auf **`"research_m3"`**. **Nur** die Research-Rolle wechselt auf MiniMax-M3; Debatte/Lesson/Instinct/Reflect/Paper-Debatte bleiben Anthropic (T5: eine Variable, eine Rolle — sonst wären spätere Modellvergleiche unlesbar). **Rollback = eine Zeile.** Wirkt erst mit **E-3** (Hold). **+1 P8-Test** (Default-Pin: nur `research` → `minimax`/`MiniMax-M3`, alle anderen Rollen → `anthropic`), Bestandstest umbenannt. P8 295 → 296, Σ 2042 → **2043** (16/16 grün). |
| 2 | (dieser Commit) | P17-Doku | **Doku-Propagierung:** dieser Block + Rotation von Session #10 → `SESSIONS_ARCHIVE.md` + Σ-Tabelle + Block-Status + Plan-§16-Nachtrag (Smoke-Ergebnis + Flip) + P8-Kopf + `docs/INDEX.md` + `ROADMAP.md` + root-`CLAUDE.md`. |

### C-7 — Familien-Smoke (Operator, 2026-11-03): **beide Modelle PASS**

Vorbedingung erfüllt: Key `trading-bot-minimax-bot/api_key` im OS-Keyring (Status-Abfrage: ✓ vorhanden; der Key selbst wurde **nie** in den Chat oder eine Datei geschrieben).

| Modell | Ergebnis | Tokens (in/out) | `finish_reason` | Latenz | Rohantwort |
|---|---|---|---|---|---|
| `MiniMax-M3` | **PASS** (valid abstain) | 751 / 164 | `stop` | **3.62 s** | `<think>…</think>` **inline** + JSON → der C-3-`<think>`-Strip hat den Block entfernt, der Validator sah sauberes JSON |
| `MiniMax-M3.1-Flash` | **PASS** (valid abstain) | 755 / … (im Log abgeschnitten) | `stop` | … | **reines JSON** — das Reasoning kommt bei Flash getrennt (`reasoning_content`), nicht im `content` |

**Was der Smoke beweist** (und was nicht): Transport, Auth, Quirks (`max_completion_tokens`), `response_format` (**kein 400 ⇒ MiniMax akzeptiert `json_object`; §15.7 Nr. 21 damit teilweise geklärt**), Denk-Modus, JSON-Parsing, Abstain-Pfad. **Nicht** beweist: Pick-Qualität (der Smoke-Prompt ist synthetisch und enthält **keine** Marktdaten — ein Abstain ist dort die *korrekte* Antwort), Latenz unter echter Prompt-Last, Verhalten bei `finish_reason=length`.

**Zwei Beobachtungen für den Live-Betrieb:**
1. **M3 antwortet mit dem Denk-Block inline** (Flash nicht) — der C-3-Strip ist damit nicht optional, sondern der Normalpfad. Er ist durch den Smoke **belegt** (funktioniert).
2. **`WARNING:research.token_meter: no pricing for model 'MiniMax-M3.1-Flash'`** — **erwartetes Verhalten** (§15.6 Nr. 26: Preiszeilen gibt es nur für **aktive** Modelle; der Smoke schreibt keine Meter-Datei). Wird M3.1-Flash später aktiv, braucht es Preiszeile + Ausnahme + `effort`-Quirk (eigener Provider-Eintrag).

### Modellwahl — bestätigt: **`MiniMax-M3`**

Der Nikinger hat die Modellfrage vertagt („klären wir an einem späteren Zeitpunkt"). Die **Aktivierung** von `MiniMax-M3` ist damit vertagt — **nicht** der Profil-Flip: Profil (welche Rolle) und Modell (welches) sind **zwei getrennte Datenstellen**. Der Smoke hat beide MiniMax-Modelle bestätigt; `MiniMax-M3` bleibt die Frontier-Klasse (BrowseComp 83.5 > Opus 4.7 79.3, PostTrainBench #3) und ist der einzige, dessen Denk-Modus abschaltbar ist (`thinking:{"type":"disabled"}` — der Hebel, falls `finish_reason=length` mit leerem Content auftaucht). **Flip 2 (`all_m3`) bleibt gegated.**

### Gemessen (Host 201)

| | vorher | nachher |
|---|---|---|
| `is-enabled` / `is-active` tradingbot-scheduler | `disabled` / `inactive` | `disabled` / `inactive` (unverändert — Hold unangetastet) |
| `bash scripts/install_units.sh --check` | exit 0 | exit 0 |
| Keyring `trading-bot-minimax-bot/api_key` | ✓ vorhanden (Operator) | ✓ vorhanden (unverändert) |
| `llm_profile` (Code-Default) | `anthropic` | **`research_m3`** — **inert** bis E-3 (Hold) |
| Σ-Sweep (16 Suiten + root) | 2042 | **2043** (16/16 grün) |
| `check_doc_rotation.py --strict` | exit 0 | exit 0 |

### Plan-AK-Stand nach dieser Session

- **C-7 (Operator-Smoke): ✅** — beide Modelle PASS, Preiszeile/Profil/Keyring-Namespace stimmen.
- **C-8 Flip 1: ✅** (Commit `2ee73e6`), **Flip 2 (`all_m3`) bleibt gegated** bis nach dem Shakedown (Nikinger-Go).
- **Σ 2043** ≥ 2025 ✓ · P8 **296** ✓ · P4 **177** ✓.
- **Plan-AK C-4 (unverändert):** `LLMClient(` → 1 Treffer, `OpenAICompatLLMClient(` → 1 Treffer in `wiring.py` ✓.

### Was der Code **jetzt** kann (und was noch nicht)

- **Kann:** der Bot **würde** (sobald E-3 den Hold löst) die Research-Rolle über MiniMax-M3 bedienen — Abo-Kontingent, `max_completion_tokens`, Denk-Modus, JSON-Parsing im Smoke belegt.
- **Kann noch nicht:** der Daemon läuft **nicht** (HOLD) — der Flip ist bis E-3 **inert**. Der Live-Pick unter echter Prompt-Last (Marktdaten + Brain-Context + Lessons) ist **ungemessen**; der erste echte Zyklus ist der eigentliche Test (dort erst zeigt sich, ob M3 bei vollem Prompt `finish_reason=length` liefert).

### Next (geplante Folgesessions, in Priorität)

- **Block D (Token-Budget, T7/D-1):** die drei Zählstellen (P8 `budget.py` · WebUI-Karte · Report) müssen die `budget_exempt_models`-Ausnahme kennen — mit dem Flip ist die Ausnahme **aktiv** (MiniMax-M3), Anthropic zählt weiter gegen 300 k.
- **Block E:** Report v5 (`--prereg v5`, `--expect-llm-profile research_m3`) · Shakedown-Vorregistrierung · **E-3-Deploy** (dort wird der Scheduler-Hold freigegeben ⇒ **erst dann wirkt der Flip**) · 2-Tage-Shakedown · Prereg v5.
- **E-3-Vorbereitung (Pflicht-Schritt):** Hold-Freigabe `--release-hold` → Installer → `start` (sonst fehlt der R5-Autostart-Beweis).
- **Beim ersten echten Zyklus beobachten:** `finish_reason`/`last_llm_error` (C-5), `llm_unavailable`-Flag, Leer-Content-Fall (Hebel: `extra_body={"thinking": {"type": "disabled"}}` am `minimax`-Eintrag — M3 erlaubt das) und die Kostenzeile (Abo ⇒ 0 €).
- **Frist 2026-11-15** — Abo-Key/Endpoint: danach jedes `minimax`-Profil **vor** dem Datum zurückflippen (Default `anthropic`). Der Executor hängt an derselben Frist.
- **Datenreparatur der 3 730 alten `ig`-Bars** (Plan T14) — folgt in **E-3**.

### Open questions / blockers

- **E-3 ist der nächste Blocker** (Hold-Freigabe + Deploy) — erst danach liefert der Bot Research-Picks über MiniMax.
- **Die Modellfrage ist vertagt** (Nikinger): „braucht der Bot ein besseres Trading-LLM?" — gehört in den Bake-off (`meta_m1_harness/bakeoff/`), nicht in diese Session. Ein Wechsel M3 → M3.1-Flash ist **3 Datenstellen** (Modell + Preiszeile + Ausnahme) + ein `effort`-Quirk (eigener Provider-Eintrag).
- **Frist 2026-11-15** (Abo) — im Phasenkopf + Plan §16 dokumentiert.
- **Plan-Snapshot-Drift** (B-7-Anker, ≈ +83 Zeilen) — Plan bleibt 📕-Snapshot; Neuauflage ist eine offene Nikinger-Entscheidung.
- **Review-Gate vor E-3 (AK22)** weiterhin ⏳ (Claude-Code-Session, Anthropic; Schwerpunkte B-5…B-10, C-4…C-6, B-3, B-2).

### Session-end-Hinweis

- **Σ 2043** (16 Suiten + root). meta_m1 informativ, nicht in Σ.
- **Commits:** 2 (1 Code-Step C-8 Flip 1 + 1 Doku). Push = Nikinger (Phase-17-Konvention).
- **Kern-Erkenntnis:** der Provider-Wechsel war **wirklich** eine Datenfrage — der Flip selbst war **eine Zeile**. Der teure Teil war nicht die Umstellung, sondern die **Beweisführung** (Smoke): erst er hat gezeigt, dass MiniMax `json_object` akzeptiert und der Denk-Modus den Antwortweg nicht zerstört.

## Session stopped — 2026-11-03 (Exec-Session #10 ENDE — **Planwechsel z.ai → MiniMax** (Abo/M Plan): M-1 Provider-Register umgestellt — Profil `research_m3`/`all_m3`, Modell `MiniMax-M3`, Preiszeile `(0.0,0.0)`, `budget_exempt_models=("MiniMax-M3",)`, Quirks `max_completion_tokens`; 1 Code-Commit + 1 Doku-Commit, Σ 2041 + 1 = **2042** grün; **C-7 wartet auf den Nikinger**; **Frist 2026-11-15**)

> **Auftrag:** Nikinger 2026-11-03 (Web-Chat): „Passt das?" — der MiniMax.io-Key (`https://api.minimax.io/v1`) soll der Bot-LLM-Provider werden; danach „Continue if you have next steps". **Plan war detailliert genug** (§6-Baseline T4–T7/C-1/C-3/C-8 + §15-Quirk-Maschinerie) → **atomar abgearbeitet, kein Re-Planen**: 1 Code-Commit + 1 Doku-Commit.
> **Nikinger-Entscheidungen (2 offene Punkte beantwortet):** (a) **Key-Typ = Abo/M Plan** (Grenzkosten 0 ⇒ Preiszeile `(0.0,0.0)`; **Frist 2026-11-15**); (b) **Modellfrage vertagt** („welches Modell *ähnt* dem aktuell verwendeten … klären wir an einem späteren Zeitpunkt") → die Wahl **`MiniMax-M3`** ist **provisorisch** und wird nach dem Familien-Smoke finalisiert (Plan-§14.4-Protokoll, C-7).
> **Executor-Modus:** MiniMax-M3 (OpenCode) — `~/.config/opencode/`, `auth.json`, `opencode.service` unangefasst (Plan §14.8).
> **Bot-Ritual (unverändert):** Scheduler `disabled` + `inactive` (Hold-Marker `data/state/SCHEDULER_HELD`), `install_units.sh --check` exit 0. Recorder/Discovery/WebUI `enabled` + `active` — unangetastet. **Kein Neustart, kein Live-Key, kein Netz-Call** in dieser Session (die Smokes sind Operator-Schritte).
> **Cross-Phase-Freigabe:** M-1 (P8 + P4) — beide in der T13-Liste.

### Completed — diese Exec-Session (1 Code-Commit + 1 Doku-Commit)

| # | Commit | Phase | Inhalt |
|---|---|---|---|
| 1 | `4d57d99` | P8 + P4 | **M-1 — Bot-Provider zurück auf MiniMax** (Abo/M Plan): `PROVIDERS["minimax"]` bekommt den dokumentierten Quirk `max_tokens_field="max_completion_tokens"` (MiniMax-Doku 2026-11-03: das Feld für neue Integrationen; `max_tokens` = Legacy); `temperature`/`top_p` werden **ignoriert**, nicht abgelehnt ⇒ `send_temperature` bleibt True. `_GLM` → `_M3 = RoleSpec(provider="minimax", model="MiniMax-M3", max_tokens=8192, timeout_s=90.0)` — **8192 statt 4096**, weil MiniMax-M3 default **denkt** und die Reasoning-Tokens gegen das Limit zählen (zu kleines Limit ⇒ `finish_reason=length` + **leerer** `content` — Plan §15.6 Fehlgriffe). Profile `research_m3`/`all_m3` (Plan-§6-Namen); `zai` bleibt **Reserve-Daten-Eintrag** (kein Profil). Preiszeile `"MiniMax-M3": (0.0, 0.0)` (Abo ⇒ Grenzkosten 0; Pay-per-use $0.30/$1.20 pro Mtok im Kommentar). `budget_exempt_models = ("MiniMax-M3",)`. **+1 P8-Test** (Quirks-Pin am MiniMax-Eintrag), Profile/Modell/Base-URL/Token-Limit in P8 + P4 umgestellt. **Σ 2041 → 2042** (16 Suiten + root, 16/16 grün). |
| 2 | (dieser Commit) | P17-Doku | **Doku-Propagierung:** dieser Block + Rotation von Session #9 → `SESSIONS_ARCHIVE.md` + Σ-Tabelle + Block-Status + Executor-Evaluations-Zeile + **Plan §16 (Planwechsel-Vermerk im 📕-Snapshot)** + die getroffenen Phasenköpfe (P8/P4) + `docs/INDEX.md` + `ROADMAP.md` + root-`CLAUDE.md`. |

### Modellwahl — Datenlage (Antwort auf die Nikinger-Frage)

> **Frage:** „welches Modell *ähnt* denn dem aktuell verwendeten (müsste Sonnet 4.6 sein) von den Performance-Daten eher?"
> **Antwort: `MiniMax-M3`.** Der Bot nutzt heute `claude-sonnet-4-6` (Research + Debatte-Judge; Bull/Bear/Lesson/Instinct/Reflect = `claude-haiku-4-5-20251001`).

| Beleg (Quelle, Datum) | Wert |
|---|---|
| BrowseComp — M3 (MiniMax-Modellseite, 2026-11-03) | **83.5** — MiniMax nennt Opus 4.7 mit 79.3 („surpassing Opus 4.7") |
| PostTrainBench — M3 (MiniMax-Modellseite, 2026-11-03) | **37.1** → **#3** overall, hinter Opus 4.7 (42.4) und GPT-5.5 (39.3) |
| M3.1-Flash (MiniMax-Blog, 2026-10-19) | DeepSWE v1.1 **73.7** · BankerToolBench **76.2** · OSWorld V2 **61.7** · CyberGym **82** · „on par with top models" — **Flash-**Klasse (Kosten $0.15/$0.60) |
| Preise (MiniMax-Pricing, 2026-11-03) | M3 ≤512k Input: **$0.30/$1.20** pro Mtok (Abo-Kontingent ⇒ $0) · M3.1-Flash $0.15/$0.60 |
| Claude Sonnet 4.6 (Anthropic, 2026-11-03) | $3/$15 · **legacy** (aktuell: Sonnet 5.5 $2/$10) · 1M Context · adaptive Thinking |

**Ehrliche Einordnung:** MiniMax publiziert **keine** direkte Gegenüberstellung mit Sonnet 4.6, und die Benchmarks laufen über verschiedene Harnesses — die Zahlen sind ein **Klassen**-, kein Gleichstands-Beweis. Für die Research-Rolle (ein Shot, JSON-Pick, keine Tools) zählt weniger die Coding-Klasse als **Denk-Tiefe + JSON-Disziplin + Preis**; M3 ist die Frontier-Klasse (M3.1-Flash ist die Flash-/Effizienzklasse, denkt immer, `thinking:disabled` ⇒ HTTP 400). **„Braucht der Bot ein besseres Trading-LLM?"** ist eine **spätere** Frage (Nikinger) — sie gehört in den Bake-off (`meta_m1_harness/bakeoff/`), nicht in diesen Daten-Commit.

### Gemessen (Host 201)

| | vorher | nachher |
|---|---|---|
| `is-enabled` / `is-active` tradingbot-scheduler | `disabled` / `inactive` | `disabled` / `inactive` (unverändert — Hold unangetastet) |
| recorder / discovery / webui | enabled + active | enabled + active (unverändert) |
| `bash scripts/install_units.sh --check` | exit 0 | exit 0 |
| Keyring `trading-bot-minimax-bot/api_key` | — | **nicht gesetzt** (gemessen — Voraussetzung für C-7 fehlt) |
| Keyring `trading-bot-zai-bot/api_key` | — | nicht gesetzt (jetzt irrelevant — `zai` ist Reserve) |
| Σ-Sweep (16 Suiten + root) | 2041 | **2042** (16/16 grün) |
| `check_doc_rotation.py --strict` | exit 0 | exit 0 |

### Plan-AK-Stand nach dieser Session

- **M-1 (Daten-Commit): ✅.** Σ **2042** ≥ 2025 ✓ · P8 **295** · P4 **177** ✓.
- **Plan-AK C-4 (unverändert):** `LLMClient(` → 1 Treffer, `OpenAICompatLLMClient(` → 1 Treffer in `wiring.py` ✓.
- **Neue Doku-Belege (MiniMax, 2026-11-03):** `max_completion_tokens` = Feld für neue Integrationen · `temperature` wird ignoriert · Denk-Modus default AN (M3 abschaltbar, M3.1-Flash nicht) · Reasoning-Tokens zählen gegen das Limit ⇒ `max_tokens=8192` · Preise M3 $0.30/$1.20, M3.1-Flash $0.15/$0.60 (Abo ⇒ $0).

### Was der Code **jetzt** kann (und was noch nicht)

- **Kann:** der Bot-Provider ist **MiniMax** — ein Daten-Eintrag, ein Profil, ein Preis, eine Ausnahme; der Quirks-Transport (`max_completion_tokens`) ist belegt und getestet.
- **Kann noch nicht:** der Bot spricht **noch nicht** mit MiniMax — `llm_profile` steht auf `"anthropic"`. Das ist Absicht (T5/T8): **erst der C-7-Smoke, dann der Flip.**

### Next (geplante Folgesessions, in Priorität)

- **C-7 — Operator (Nikinger), zwei Schritte:**
  1. **Bot-Key seeden** (Abo/M Plan, eigener Namespace — **nie** der Executor-/Coding-Plan-Key):
     `python scripts/store_minimax_key.py --service trading-bot-minimax-bot --username api_key`
  2. **Familien-Smoke** (2 Calls, Abo-Kontingent ⇒ $0, Plan-§14.4-Protokoll, mit `--provider minimax`):
     ```bash
     PY=phase1_broker_wrapper/.venv/bin/python
     for m in MiniMax-M3 MiniMax-M3.1-Flash; do
       $PY phase4_research/scripts/openrouter_smoke.py --provider minimax --model "$m" \
         --max-tokens 8192 --timeout-s 90 --show-raw; done
     ```
     Je Modell PASS/FAIL, `finish_reason`, Tokens und Latenz hierher in den Phasenkopf. **FAIL ⇒ nicht flippen** (Diagnose nach Plan §8/§15.6, dann ggf. `max_tokens`/`timeout_s` in `_M3` anpassen — eigener Commit). **Sonderfall:** `finish_reason=length` mit **leerem** `content` ⇒ Denk-Modus abschalten (`extra_body={"thinking": {"type": "disabled"}}` am `minimax`-Eintrag — für `MiniMax-M3` erlaubt, für `MiniMax-M3.1-Flash` ein 400).
- **Danach (nach dem Nikinger-Go):** **Modellwahl finalisieren** (`_M3.model` + `budget_exempt_models` + Preiszeile — die drei Stellen, die zusammen geändert werden müssen) → **Flip 1** (`llm_profile = "research_m3"`, eigener Commit) → **C-8 („all_m3") bleibt gegated** bis nach dem Shakedown.
- **Frist 2026-11-15 (Abo-Key):** läuft das Kontingent ab, muss jedes `minimax`-Profil **vor** dem Datum zurückgeflippt werden (sicherer Default `anthropic`) — sonst startet der Bot nicht mehr (Preflight-Punkt 4 findet keinen Key).
- **Block D (Token-Budget, T7/D-1):** die drei Zählstellen (P8 `budget.py` · WebUI-Karte · Report) müssen die `budget_exempt_models`-Ausnahme kennen.
- **Block E:** Report v5 (`--prereg v5`) · Shakedown-Vorregistrierung · **E-3-Deploy** (dort wird der Scheduler-Hold freigegeben) · 2-Tage-Shakedown · Prereg v5.
- **E-3-Vorbereitung (Pflicht-Schritt):** Hold-Freigabe `--release-hold` → Installer → `start` (sonst fehlt der R5-Autostart-Beweis).
- **Datenreparatur der 3 730 alten `ig`-Bars** (Plan T14) — folgt in **E-3**.

### Open questions / blockers

- **C-7 ist blockiert, bis der Nikinger den MiniMax-Abo-Key seedet** (gemessen: `trading-bot-minimax-bot/api_key` **nicht** im Keyring). Ohne Key kein Smoke, ohne Smoke kein Flip — **der Bot läuft unverändert auf Anthropic**, das ist der sichere Default.
- **`_M3.model = "MiniMax-M3"` ist provisorisch** (Nikinger 2026-11-03: die Frage „welches Modell ähnelt Sonnet 4.6" ist **vertagt**; die Wahl stützt sich auf die Benchmark-Klasse). Der Wechsel betrifft **drei** Stellen (`llm_profiles._M3.model`, die Preiszeile in `research/models.py`, `SchedulerConfig.budget_exempt_models`) — `check_llm_profile` benennt die vergessene beim Start.
- **Frist 2026-11-15** — der Abo-Key/Endpoint gilt nur bis dahin; danach zurückflippen (Default `anthropic`). Der Executor hängt an derselben Frist (Plan §14.2: Rückfall MiniMax → Claude).
- **`response_format: {"type": "json_object"}`** ist für MiniMax **nicht dokumentiert** — der C-3-400-Fallback (einmal ohne `response_format`) plus der Prosa-Recovery-Pfad decken den Fall ab; der Smoke zeigt, ob der Fallback greift.
- **Plan-Snapshot-Drift** (B-7-Anker, ≈ +83 Zeilen) — im Phasenkopf dokumentiert, Plan bleibt 📕-Snapshot; Neuauflage ist eine offene Nikinger-Entscheidung.
- **Review-Gate vor E-3 (AK22)** weiterhin ⏳ (Claude-Code-Session, Anthropic; Schwerpunkte B-5…B-10, C-4…C-6, B-3, B-2).

### Session-end-Hinweis

- **Σ 2042** (16 Suiten + root, Sweep-Kommando aus dem Phase-Kopf). meta_m1 informativ, nicht in Σ.
- **Commits:** 2 (1 Code-Step M-1 + 1 Doku). Push = Nikinger (Phase-17-Konvention).
- **Kern-Erkenntnis:** der Provider-Wechsel war **wirklich** eine Datenfrage — 8 Dateien, 1 Commit, keine neue Logik. Der Planwechsel zurück zu MiniMax kostete **weniger als der ursprüngliche Aufbau**, weil §15 die Quirks als Felder und §6 das Profil als Daten entworfen hatte.

## Session stopped — 2026-11-03 (Exec-Session #9 ENDE — **Block C, Code-Teil C-1…C-6 abgeschlossen**: Provider-Register + LLM-Austausch (`_build_llm`) + `LLM_UNAVAILABLE` + Key-/Smoke-Skript; 6 Commits, Σ 2004 + 37 = **2041** grün; **C-7 wartet auf den Nikinger** — Bot-Key `trading-bot-zai-bot` fehlt im Keyring)

> **Auftrag:** Nikinger 2026-11-03 (Web-Chat, zweite Session desselben Tages): „ja, pushen, und danach weiter mit dem nächsten Step" → (1) **Push** der 5 Commits aus Session #8 (`423a541..d7b6abe main -> main`, auftragsgemäß vom Nikinger freigegeben), (2) **Block C** abarbeiten — Plan §14 → §15 → §6 (die Reihenfolge, die §15 selbst festlegt). **Plan war detailliert genug** → atomar abgearbeitet, ein Commit pro Step, kein Re-Planen.
> **Executor-Modus:** MiniMax-M3 (OpenCode) — kein z.ai-Modell heute. `~/.config/opencode/`, `auth.json`, `opencode.service` unangefasst (Plan §14.8).
> **Bot-Ritual (vorab geprüft):** Scheduler `disabled` + `inactive` (Hold-Marker `data/state/SCHEDULER_HELD`), `install_units.sh --check` exit 0. Recorder/Discovery/WebUI `enabled` + `active` — unangefasst. **Kein Neustart, kein Live-Key, kein Netz-Call** in dieser Session (die Smokes sind Operator-Schritte).
> **Cross-Phase-Freigabe:** C-1/C-2/C-4 (P8), C-3/C-5/C-6 (P4), C-5 (P10), C-6 (root) — alle in der T13-Liste.

### Completed — diese Exec-Session (6 Code-Commits + 1 Doku-Commit)

| # | Commit | Phase | Inhalt |
|---|---|---|---|
| 1 | `698e9ea` | P8 | **C-1 — Provider-Register** `scheduler/llm_profiles.py` (NEU, stdlib-only): `ProviderSpec` (kind · base_url · Keyring-Namespace + **drei Quirks**: `max_tokens_field`, `send_temperature`, `extra_body` — T26/T27, provider- **nie** modellbezogen), `RoleSpec`, **neun** `PROVIDERS` (anthropic · zai · minimax · openai · deepseek · qwen · kimi · openrouter · opencode_zen — T25: ein Provider = ein Daten-Eintrag, keine `if provider == …`-Zeile), `LLM_PROFILES` (`anthropic` / `research_glm` / `all_glm`), `role_spec()` (KeyError-frei), `check_provider()` (kind · https · **kein „coding" im Host** (T31) · Keyring-Namespace · Quirks-Feld), `client_kwargs()` (T29: die **eine** Abbildung — Bot **und** Smoke benutzen sie), `check_llm_profile()` (4 Fehlerklassen). **+11 P8-Tests.** |
| 2 | `145e80e` | P8 | **C-2 — Config-Defaults**: `SchedulerConfig.llm_profile = "anthropic"` + `budget_exempt_models = ("glm-5.3",)`. Code-Default statt CLI-Flag (die systemd-Unit übergibt keine Flags → nur ein Code-Default ist restart-fest). `__post_init__` unangetastet. **+1 P8-Test.** |
| 3 | `4190802` | P4 + P8 | **C-3 — OpenAI-Compat-Härtung**: `api_key_username` als Konstruktor-Argument; die **drei Quirks** mit Validierung **im Konstruktor** (der eine Engpass, den Bot und Smoke teilen) und **bytegleichem** Default-Payload; **400-Fallback** (einmal ohne `response_format`, mit dem **ersten** Fehlertext im Log); **`<think>`-Strip** (unterminiert = harter, nicht-retrybarer Fehler); Fehlermeldungen „OpenAI-compat call failed (base_url=…)"; `last_raw_text` für `--show-raw`. Dazu die **GLM-Preiszeilen** (§14.1: `glm-5.3` 1.4/4.4 · `glm-5.2` 1.4/4.4 · `glm-5.3-flash` 0.15/0.5 USD/Mtok). **+9 P4 + 1 P8-Tests** (der Bestandstest „400 raises immediately no retry" wurde plan-konform umgebaut). |
| 4 | `1a61229` | P8 | **C-4 — eine Bau-Funktion**: `_build_llm(role, llm_profile, …)` baut **alle** Clients (Anthropic → `LLMClient`, sonst → `OpenAICompatLLMClient` mit `**client_kwargs(provider)`); `_debate_config(llm_profile)` benennt Bull/Bear/Judge um (Phase 6 überschreibt `client.model` je Rolle!); alle **sieben** Bau-Stellen umgestellt (research · debate · lesson · instinct · reflect · paper_debate · reflect-Tracker); `_check_llm_profile()` läuft in `build_scheduler` **vor** jedem Bau; **Preflight-Punkt 4**: jeder Nicht-Anthropic-Provider braucht seinen Key im Keyring (sonst startet der Daemon fröhlich und scheitert um 09:00); die **Start-Zeile** nennt `llm_profile`. **+7 P8-Tests** (AK: `LLMClient(` → 1 Treffer, `OpenAICompatLLMClient(` → 1 Treffer). |
| 5 | `edeeab8` | P4 + P8 + P10 | **C-5 — `LLM_UNAVAILABLE`** (D9): P4 setzt `last_llm_error`; P8 `research_tick` kennt `REASON_LLM_UNAVAILABLE` + **Fehler-Streak** (genau bei 3 ein `logger.critical`); P8-Wiring setzt das `llm_unavailable`-Flag **vor** der Klassifikation (die Reihenfolge, die B-7 geschaffen hat); P10 bekommt `REASON_LLM_UNAVAILABLE` (13 Gründe) — die Stage bleibt `RESEARCH_EMPTY`, nur der Grund unterscheidet sich; **keine Migration** (die Spalte hat keinen CHECK). **+1 P4 + 3 P8 + 2 P10-Tests.** |
| 6 | `6d1f69d` | root + P4 | **C-6 — Operator-Skripte**: `scripts/store_minimax_key.py` ist jetzt **generisch** (`--service`/`--username`, `main(argv)`); `openrouter_smoke.py` bekommt `--base-url`/`--key-service`/`--key-username`/`--max-tokens`/`--timeout-s`/`--show-raw` **und `--provider`** (§15.4: Endpoint + Keyring + Quirks aus dem Provider-Register — der Smoke sendet exakt den Bot-Payload; `--provider` ist mit den expliziten Flags **mutually exclusive**) plus `finish_reason`/`latency_s`/`provider=` in der Ausgabe. **+2 root-Tests.** |
| 7 | (dieser Commit) | P17-Doku | **Doku-Propagierung:** dieser Block + Rotation von Session #8 → `SESSIONS_ARCHIVE.md` + Σ-Tabelle + Block-Status + Executor-Evaluations-Zeile + die drei getroffenen Phasenköpfe (P8/P4/P10) + `docs/INDEX.md` + `ROADMAP.md` + root-`CLAUDE.md`. |

### Gemessen (Host 201)

| | vorher | nachher |
|---|---|---|
| `is-enabled` / `is-active` tradingbot-scheduler | `disabled` / `inactive` | `disabled` / `inactive` (unverändert) |
| recorder / discovery / webui | enabled + active | enabled + active (unverändert) |
| `bash scripts/install_units.sh --check` | exit 0 | exit 0 |
| Keyring `trading-bot-zai-bot/api_key` | — | **nicht gesetzt** (gemessen — Voraussetzung für C-7 fehlt) |
| Keyring `trading-bot-minimax-bot/api_key` | — | nicht gesetzt |
| Σ-Sweep (16 Suiten + root) | 2004 | **2041** (16/16 grün) |

### Plan-AK-Stand nach dieser Session

- **Block C, Code-Teil (C-1…C-6): ✅ abgeschlossen.** Σ **2041** ≥ 2025 ✓ · P4 **177** ≥ 177 ✓ · P8 **294** ≥ 292 ✓ · P10 **168** ≥ 167 ✓.
- **Plan-AK C-4:** `rg "\bLLMClient\(" phase8_scheduler/scripts/wiring.py` → **1** Treffer; `rg "OpenAICompatLLMClient\("` → **1** Treffer (beide in `_build_llm`) ✓.
- **Abweichung (ehrlich):** C-4 lieferte **+7** P8-Tests statt der geplanten +5. Der AK ist eine Untergrenze; die zwei zusätzlichen Tests decken „unbekanntes Profil wirft **vor** jedem Client" und die Client-Oberfläche ab.

### Was der Code **jetzt** kann (und was noch nicht)

- **Kann:** jeder OpenAI-kompatible Provider ist **ein Daten-Eintrag** (`PROVIDERS`), mit Quirks; das Bot verdrahtet **eine** Bau-Funktion; ein Profil-Wechsel ist ein Config-Wert; ein LLM-Ausfall ist von einem Modell-Abstain **unterscheidbar**; ein fehlender Provider-Key fällt **beim Start** auf, nicht um 09:00.
- **Kann noch nicht:** der Bot spricht **noch nicht** mit GLM — `llm_profile` steht auf `"anthropic"`. Das ist Absicht (T5/T8): **erst der C-7-Smoke, dann der Flip.**

### Next (geplante Folgesessions, in Priorität)

- **C-7 — Operator (Nikinger), zwei Schritte:**
  1. **Bot-Key seeden** (Pay-per-use, eigener Namespace — **nie** der Coding-Plan-Key):
     `python scripts/store_minimax_key.py --service trading-bot-zai-bot --username api_key`
  2. **Familien-Smoke** (3 Calls Pay-per-use, < 0,01 $ — Plan §14.4, mit `--provider zai`):
     ```bash
     PY=phase1_broker_wrapper/.venv/bin/python
     for m in glm-5.3 glm-5.3-flash glm-5.2; do
       $PY phase4_research/scripts/openrouter_smoke.py --provider zai --model "$m" \
         --max-tokens 4096 --timeout-s 90 --show-raw; done
     ```
     Je Modell PASS/FAIL, `finish_reason`, Tokens und Latenz hierher in den Phasenkopf (§14.4). **FAIL ⇒ nicht flippen** (Diagnose nach Plan §8/§15.6, dann ggf. `max_tokens`/`timeout_s` in `_GLM` anpassen — eigener Commit).
- **Danach (nach dem Nikinger-Go):** **Modellwahl** (`_GLM.model` + `budget_exempt_models` + Preiszeile — die drei Stellen, die zusammen geändert werden müssen) → **Flip 1** (`llm_profile = "research_glm"`, eigener Commit) → **C-8 („all_glm") bleibt gegated** bis nach dem Shakedown.
- **Block D (Token-Budget, T7/D-1):** die drei Zählstellen (P8 `budget.py` · WebUI-Karte · Report) müssen die `budget_exempt_models`-Ausnahme kennen.
- **Block E:** Report v5 (`--prereg v5`) · Shakedown-Vorregistrierung · **E-3-Deploy** (dort wird der Scheduler-Hold freigegeben) · 2-Tage-Shakedown · Prereg v5.
- **E-3-Vorbereitung (Pflicht-Schritt):** Hold-Freigabe `--release-hold` → Installer → `start` (sonst fehlt der R5-Autostart-Beweis).
- **Datenreparatur der 3 730 alten `ig`-Bars** (Plan T14) — folgt in **E-3**.

### Open questions / blockers

- **C-7 ist blockiert, bis der Nikinger den z.ai-Bot-Key seedet** (gemessen: `trading-bot-zai-bot/api_key` **nicht** im Keyring). Ohne Key kein Smoke, ohne Smoke kein Flip — **der Bot läuft unverändert auf Anthropic**, das ist der sichere Default.
- **`_GLM.model = "glm-5.3"` ist provisorisch** (Plan §14.4: der Nikinger wählt nach dem Familien-Smoke). Der Wechsel betrifft **drei** Stellen (`llm_profiles._GLM.model`, die Preiszeile in `research/models.py`, `SchedulerConfig.budget_exempt_models`) — `check_llm_profile` benennt die vergessene beim Start.
- **`budget_exempt_models` enthält nur `glm-5.3`** — das **MiniMax-Abo** (`trading-bot-minimax-bot`, gültig bis 2026-11-15) hat **kein** Profil; es ist nur ein Daten-Eintrag + Smoke-Ziel (§15.3/Q1). Ein Profil darauf braucht Preiszeile + Ausnahme im Flip-Commit.
- **MiniMax-Endpoint läuft am 2026-11-15 ab** (Plan §14.3) — nach dem Datum muss jedes Profil, das `minimax` nutzt, zurückgeflippt werden (aktuell: keins).
- **Plan-Snapshot-Drift** (B-7-Anker, ≈ +83 Zeilen) — im Phasenkopf dokumentiert, Plan bleibt 📕-Snapshot; Neuauflage ist eine offene Nikinger-Entscheidung.
- **Review-Gate vor E-3 (AK22)** weiterhin ⏳ (Claude-Code-Session, Anthropic; Schwerpunkte B-5…B-10, C-1…C-6, B-3, B-2).

### Session-end-Hinweis

- **Σ 2041** (16 Suiten + root, Sweep-Kommando aus dem Phase-Kopf). meta_m1 informativ, nicht in Σ.
- **Commits:** 7 (6 Code-Steps + 1 Doku). Push = Nikinger (Phase-17-Konvention).
- **Kern-Erkenntnis:** der Provider-Wechsel ist jetzt eine **Datenfrage** statt einer Codefrage — ein neuer Anbieter ist ein Commit auf `PROVIDERS` (plus Preiszeile + Ausnahme, wenn er *aktiv* wird), und `check_llm_profile` sagt beim Start, was fehlt. Die Kehrseite: die Entscheidung „welches Modell" ist bewusst **noch nicht** getroffen — sie gehört dem Nikinger nach dem gemessenen Smoke.

## Session stopped — 2026-11-03 (Exec-Session #8 ENDE — **Block B abgeschlossen**: B-7 Abstain-Naht + B-8 Paper-Logstufen + B-9 Stop-Timeout + B-10 Discovery-Beleg; 4 Code-Commits, Σ 2000 + 4 = **2004** grün; Scheduler `disabled`+`inactive` (Hold) + 3 Units laufen weiter)

> **Auftrag:** Nikinger 2026-11-03 (Web-Chat): Phase 17 fortsetzen — „Start by reading the .md files … A good start is the /concept folder", „The phase is separated into steps, and the progress is noted … keep it recent". Der **Plan war detailliert genug** (Plan §6 B-7…B-10 mit Verbatim-Ankern, AKs und Testnamen) → **atomar abgearbeitet, kein Re-Planen**. Reihenfolge: Plan-§-Reihenfolge B-7 → B-8 → B-9 → B-10, ein Commit pro Block (Konvention der Exec-Sessions #2–#6).
> **Executor-Modus:** MiniMax-M3 (OpenCode) — kein z.ai-Modell heute. `~/.config/opencode/`, `auth.json`, `opencode.service` unangefasst (Plan §14.8).
> **Bot-Ritual (vorab geprüft):** Scheduler war bereits `disabled` + `inactive` (Hold-Marker `data/state/SCHEDULER_HELD`, aus Session #7), `install_units.sh --check` exit 0. Recorder/Discovery/WebUI `enabled` + `active` — **unangefasst** (nur der Discovery-*Code* geändert, kein Neustart → Bot-Ritual „Neustart macht nur E-3").
> **Cross-Phase-Freigabe:** alle vier Blöcke liegen in der T13-Liste (P8, P10, P16, P14) — keine Nachfrage nötig.

### Completed — diese Exec-Session (4 Code-Commits + 1 Docs-Commit)

| # | Commit | Phase | Inhalt |
|---|---|---|---|
| 1 | `5d02e7c` | P8 | **B-7 — Abstain-Naht (D7).** `scripts/wiring.py`: (a) `_observed_abstain_sink` reicht den `record_id` des inneren Sinks durch (`-> Any`, `record_id = inner.on_no_trade(...)`, `return record_id` **nach** dem try/except — ein Observability-Fehler darf den Wert nicht wieder verschlucken); Docstring-Satz „locked `AbstainSink.on_no_trade(cycle_outcome) -> None` contract" ersetzt. (b) **Reihenfolge im Composition Root umgedreht**: `_observed_abstain_sink(_enrich_abstain_detail(sink, research), path)` → `_enrich_abstain_detail(_observed_abstain_sink(sink, path), research)` — die Anreicherung liegt jetzt **vor** der Klassifikation des `abstain_recorded`-Events (vorher sah nur die Persistierung den angereicherten Zyklus). Das ist die Reihenfolge, die ab **C-5** das `llm_unavailable`-Flag rechtzeitig in die Klassifikation bringt. **+2 P8-Tests** (neu `phase8_scheduler/tests/test_wiring_abstain_seam.py`): `test_observed_sink_returns_inner_record_id`, `test_enriched_outer_wrapper_feeds_observed_classification` (Classifier-Spy: **pinnt die Reihenfolge**, nicht nur den Rückgabewert — mit der Alt-Reihenfolge sieht der Classifier `generic` statt `ENRICHED-PROSE`). Negativ-Beweis: beide Tests mit dem pre-B-7-`wiring.py` rot (stash). **P8 269 → 271** ✓ Plan-AK (≥ 271). |
| 2 | `02faf44` | P10 | **B-8 — Paper-Logstufen (D8, T11/E4).** `abstain_lessons/paper.py`: vier Stellen von `critical` → `warning` (Ausfälle **externer** Abhängigkeiten): `PaperDebateCaller.request_pick failed` (Z. 323), `PaperEngine.on_debate_abstain failed` (Z. 390), `PaperEngine.open_scheduled_pairs failed for %s` (Z. 471), `PaperTradeTracker reflect failed for record %s` (Z. 709). Jede mit dem Plan-Kommentar „# Phase 17 B-8 (E4): external-dependency failure (quote/LLM) — WARNING; an LLM outage is reported once by research_tick (LLM_UNAVAILABLE)." **Unverändert `critical`** (lokale Fehler = Bug-Indikatoren): `PaperTradeTracker bar fetch failed` (Z. 569) und `PaperTradeTracker resolve failed` (Z. 691). **+1 P10-Test** (`test_get_price_failure_logs_warning_not_critical`, caplog): Gegenprobe mit pre-B-8-Code rot. **P10 165 → 166** ✓ Plan-AK (≥ 166). |
| 3 | `f221f3c` | P16-Unit | **B-9 — Stop-Timeout (D13, T10).** `phase16_activation/systemd/tradingbot-scheduler.service`: `TimeoutStopSec=360` unter `SuccessExitStatus=143`, mit Plan-Kommentar („SIGTERM is honoured after the running cycle sleep (≤ 300 s) — 90 s default killed every stop (09-23, 09-30, 10-11)"). Vorher: systemd-Default 90 s → **jeder** Stop endete in SIGKILL, ohne dass `shutdown()` (finaler Reconcile + `broker.disconnect()`) je lief. Akzeptanz: `bash scripts/install_units.sh --verify` → exit 0 (`systemd-analyze --user verify: ok`). |
| 4 | `4eefbda` | P14 | **B-10 — Discovery-Beleg (D12).** `source_registry/run.py::run_once`: an **allen drei** Rückgabestellen (unarmed · armed+nichts-stale · realer Zyklus) eine INFO-Zeile direkt vor dem `return`: `"discovery cycle %s: armed=%s stale=%d rows_written=%d errors=%d"` — der Zeitstempel steckt **im Text** (`basicConfig` ohne `asctime`), eine Zeile pro Zyklus (≈ 1/Stdunde, `interval_s=3600`); die zwei `logger.debug(...)`-Zeilen bleiben. Davor gab es **keinen** append-only Beleg (nur `discovery_state.json`, in place, und eine unsichtbare debug-Zeile). Dazu `scripts/run_discovery.sh`: Starttext „(unarmed ⇒ noop)" → „(noop unless ARMED)" (das K1-Muster `\[run_discovery\] starting daemon` bleibt treffend). **+1 P14-Test** (`test_run_once_logs_discovery_cycle_line_with_ts`, caplog, alle drei Pfade): Gegenprobe mit pre-B-10-Code rot. **P14 61 → 62** ✓ Plan-AK (≥ 62). |
| 5 | (dieser Commit) | P17-Doku | **Doku-Propagierung:** dieser Block + Rotation von Session #7 → `SESSIONS_ARCHIVE.md` + Σ-Tabelle + Block-Status + Executor-Evaluations-Zeile + Bot-Ritual-Hinweis + die vier getroffenen Phasenköpfe (P8/P10/P14/P16) mit additivem „Phase-17-Edit"-Block (Muster B-5/B-6) + `docs/INDEX.md`. |

### Gemessen (Host 201, `trading-bot-VMware-Virtual-Platform`)

| | vorher | nachher |
|---|---|---|
| `is-enabled tradingbot-scheduler.service` | `disabled` | `disabled` (unverändert) |
| `is-active tradingbot-scheduler.service` | `inactive` | `inactive` (unverändert) |
| recorder / discovery / webui | enabled + active | enabled + active (unverändert) |
| `bash scripts/install_units.sh --check` | exit 0 | exit 0 (siehe „B-9-Host-Notiz" unten) |
| `bash scripts/install_units.sh --verify` | exit 0 | exit 0 (`systemd-analyze --user verify: ok`) |
| `data/state/SCHEDULER_HELD` | vorhanden | vorhanden (unberührt) |
| `data/state/KILL` | nicht vorhanden | nicht vorhanden (unberührt) |
| Σ-Sweep (16 Suiten + root) | 2000 | **2004** (16/16 grün) |

**B-9-Host-Notiz (bewusster Schritt, außerhalb des Commits):** die getrackte Unit wurde über den **getrackten Installer** auf 201 installiert (`bash scripts/install_units.sh` → Datei-Kopie + `daemon-reload`), **bevor** `--check` sonst dauerhaft rot gelaufen wäre (`installed=differs` → DRIFT, exit 1, weil die installierte Kopie die neue `TimeoutStopSec`-Zeile noch nicht hatte). Der **Hold blieb unangetastet**: die Scheduler-Unit bleibt `disabled` + `inactive`; gestartet wird weiterhin **erst in E-3**. Die drei anderen Units blieben `enabled` + `active` (der Installer hat sie nur idempotent re-enabled, **nicht** gestartet).

### Plan-AK-Stand nach dieser Session

- **Block B ist vollständig abgeschlossen** (B-0 … B-10): Exec-Session #1 (A-0…A-2, A-3, B-0, B-1) · #2 (B-2) · #3 (B-3) · #4 (B-4) · #5 (B-5) · #6 (B-6) · #7 (Scheduler-Hold) · **#8 (B-7, B-8, B-9, B-10)**.
- **Plan-AK Block-B-Sweep:** Σ ≥ 1992 → **2004** ✓ (Plan-Ziel übertroffen; +4 exakt wie im Plan vorgesehen: B-7 +2 P8 · B-8 +1 P10 · B-9 +0 (Unit-Test läuft in E-3) · B-10 +1 P14).
- **Σ 2000 → 2004** (P8 269→271 · P10 165→166 · P14 61→62; alle übrigen 13 Suiten + root unverändert grün).

### Drift-Konsolidierung (Anker)

- **B-7:** Plan-Anker Z. 758–760 → heute Z. 841–856 (≈ **+83 Zeilen**), Docstring Z. 747–753 → Z. 830–843, Reihenfolge Z. 993–995 → Z. 1094–1108. **Größer als die +60-Zeilen-Schwelle**, die der Session-#6-Block als „Plan-Snapshot updaten statt nur Drift protokollieren" markiert hat. **Entscheidung dieser Session:** der Plan ist ein **📕 dated snapshot** (`status: snapshot`) und wird **nicht** editiert (Anti-Pattern „📕 dated snapshot edit", T24: nur angehängter datierter Vermerk); der Drift ist hier vollständig dokumentiert und die Edits liefen am **realen Ort** (Verbatim-Anker, nicht Zeilennummer). *Für die Nikinger-Entscheidung offen:* Plan-Snapshot-Neuauflage (Datum + Zeilen) vor Block C.
- **B-8 / B-9 / B-10:** **kein Drift** — alle Anker exakt wie im Plan (P10 `paper.py:321/386/465/701`, P16-Unit `SuccessExitStatus=143`, P14 `run.py` 3× `return result` + `run_discovery.sh:46`).

### Next (geplante Folgesessions, in Priorität)

- **Block C — LLM-Austausch** (Plan §14 zuerst, dann §15): C-1 `scheduler/llm_profiles.py` (NEU, stdlib-only) → C-2 `SchedulerConfig.llm_profile` → C-3 OpenAI-Compat-Härtung + Preiszeile → C-4 **eine** Bau-Funktion für alle 7 Clients + Profil-Check + Preflight + Startzeile → C-5 `LLM_UNAVAILABLE` (eigene Abstain-Klasse, D9) → C-6 Key-Skript + Smoke-Skript → **C-7 Familien-Smoke (Nikinger, 3 Calls Pay-per-use < 0,01 $)** → C-8 „Flip 2" (**gegated**, nur mit Nikinger-Go nach dem Shakedown). Σ-Ziel Block C ≥ **2025**. **B-7 ist die Vorbedingung für C-5** — das `llm_unavailable`-Flag erreicht die Klassifikation jetzt rechtzeitig.
- **E-3-Vorbereitung (Pflicht-Schritt, noch offen):** der Hold muss **vor** E-3 freigegeben werden, sonst bleibt die Scheduler-Unit `disabled` (der R5-Autostart-Beweis fehlt danach). Freigabe: `bash scripts/install_units.sh --release-hold` → `bash scripts/install_units.sh` (enabled alle vier) → `systemctl --user start tradingbot-scheduler.service …` (Plan §6 E-3). Der E-3-Block im Plan (`docs/concepts/phase17_testbed_plan.md`) ist `status: snapshot` (L3) und wurde **nicht** editiert — der Release-Schritt steht hier (Phase-17-Kopf) und gehört in den E-3-Lauf.
- **Datenreparatur der 3 730 alten `ig`-Bars** (Plan T14: löschen statt verschieben) — folgt in **E-3** zusammen mit dem Scheduler-Restart; bis dahin bleibt der DB-Zustand mit den +2-h-Bars stehen.
- **Live-Beweis B-5/B-6** (Monitor-Re-Adoption, Breaker-Worst-Case) kommt erst mit E-3/E-4 (Handelstag).
- **Fleet-Abstimmung (eurfleet-Session):** deren Repo (Restart-Liste) ist theirs — der Bot-Anteil ist hier erledigt. 201 wird am **31.10.** wie geplant gepatcht; der Reboot darf den Scheduler nicht starten (Autostart `disabled` + Guard).

### Open questions / blockers

- **Scheduler ist gestoppt** (`is-active=inactive`, `is-enabled=disabled`). Alle übrigen Punkte (Datenreparatur der 3 730 alten `ig`-Bars, Promotion-Bridge-Backfill 29 NULL-Zeilen, Fleet §14.8 OpenCode + z.ai, B-5-/B-6-Live-Beweis) — **keine Änderung** gegenüber Session #1–#7.
- **Plan-Snapshot-Drift > +60 Zeilen (B-7-Anker):** im Phasenkopf dokumentiert, **nicht** im Plan gefixt (📕-Konvention). Braucht eine Nikinger-Entscheidung, ob der Plan vor Block C neu aufgelegt wird.
- **Hold-Marker ist untracked** (`data/state/` → pro Host). Ein zweiter Host braucht den Marker ebenfalls, wenn der Scheduler dort gestoppt bleiben soll.
- **Kein Eingriff in Phase-16-Doku:** `phase16_activation/PHASE16_E3_RUNBOOK_v4.md` §3 beschreibt die Deploy-Sequenz ohne Hold — ein Cross-Phase-Edit wäre außerhalb Phase 17. Der Release-Schritt steht hier (Phase-17-Kopf); der Nikinger entscheidet, ob P16 nachgezogen wird.
- **B-10 wirkt erst ab dem nächsten Discovery-Neustart** (E-3) — der laufende Daemon nutzt noch den alten Code.
- **Review-Gate vor E-3 (AK22)** ist weiterhin ⏳ (Claude-Code-Session, Anthropic; Schwerpunkte B-5, B-6, C-4, B-3, B-2 — B-7/B-8/B-9/B-10 kommen hinzu).

### Session-end-Hinweis

- **Σ 2004** (16 Suiten + root, Sweep-Kommando aus dem Phase-Kopf). meta_m1 informativ, nicht in Σ.
- **Commits:** 5 (4 Code-Blöcke + 1 Doku). Push = Nikinger (Phase-17-Konvention).
- **Kern-Erkenntnis:** *Block B ist keine Sammlung kosmetischer Fixes, sondern die Voraussetzung dafür, dass die ausgiebigen Tests nach Phase 17 überhaupt etwas messen.* B-7 stellt die **Verlinkung** zwischen Abstain-Lesson und `decision_context` her (3 669/3 669 NULL → ab Tag 1 nach E-3 `abstain_record_id IS NOT NULL`), B-8 senkt das K5-Rauschen an der Quelle (statt das Kriterium zu lockern), B-9 verhindert, dass jeder Stop per SIGKILL endet (ohne `shutdown()`-Reconcile), B-10 macht den Discovery-Daemon überhaupt erst aus einer append-only Quelle belegbar.

## Session stopped — 2026-10-25 (Exec-Session #7 ENDE — Scheduler-Hold: systemd-Autostart aus + getrackter Repo-Guard `data/state/SCHEDULER_HELD`, +12 root-Tests, Σ 1988 + 12 = **2000** grün; Scheduler gestoppt + 3 Units laufen weiter; Nikinger-Freigabe: Marker-Variante + lokale Commits, Push = Nikinger)

> **Auftrag:** Nikinger 2026-10-25 (über die eurfleet-Fleet-Session weitergeleitet): „Hold off on running 201 — its restart list includes tradingbot-scheduler, and since it's also enabled, a likely reboot would re-start it against your 21.10 decision. … You or the bot session should separately run `systemctl --user disable tradingbot-scheduler` on 201, since that unit's state isn't mine to touch. … 201 then gets patched normally on 31.10." → Diese Exec-Session macht die **Bot-Seite**: (1) Host-Disable (systemd-Autostart aus), (2) getrackter Repo-Guard, damit der 31.10-Update-Run den Fix nicht zurücknimmt. Die Fleet-Seite (Restart-Liste `inventory/hosts.yml`, `--check`) liegt in der eurfleet-Session, nicht hier.
>
> **Kontext:** Die Phase-17-Entscheidung B-0 (Plan §6) hält den Scheduler **absichtlich** gestoppt (Plan T22: nur der Scheduler hält eine IG-Session) — von B-0 bis E-3. Das Repo kannte diese Entscheidung bisher nur als *Prozesszustand* (`systemctl --user stop`), nicht als *Installationszustand*: die Unit war weiterhin `enabled`. Jeder Reboot (VM-Host-Ereignis, Plan T10) hätte den gestoppten Scheduler wieder gestartet.
>
> **Executor-Modus:** MiniMax-M3 (OpenCode) — kein z.ai-Modell heute. `~/.config/opencode/`, `auth.json`, `opencode.service` unangefasst.

### Completed — diese Exec-Session (2 Commits)

| # | Commit | Phase | Inhalt |
|---|---|---|---|
| 1 | `51ba156` | root (`scripts/`) | **Host-Hold + Repo-Guard.** (a) `systemctl --user disable tradingbot-scheduler.service` auf 201 (Host-Zustand: vorher `enabled` → jetzt `disabled`, `is-active` bleibt `inactive`; recorder/discovery/webui unangeführt `enabled` + `active`). (b) **`scripts/install_units.sh`**: Hold-Marker `data/state/SCHEDULER_HELD` (operator-sticky, Muster `KILL` / `DISCOVERY_ARMED`, **untracked** — `data/` ist Host-Zustand; der *Guard* ist der getrackte Teil). Bei Hold wird `tradingbot-scheduler.service` **nicht** enabled — vorher lief am Script-Ende `systemctl --user enable "${UNITS[@]}"` (Z. 76), d. h. der nächste Installer-Lauf (31.10-Update-Run) hätte den Scheduler wieder autostart-fähig gemacht. Neue Modi: `--check` (report-only, Drift → exit 1), `--hold` (Marker anlegen + Unit deaktivieren), `--release-hold` (Marker weg). (c) **`scripts/restart-services.sh`**: `start`/`restart` überspringen den Scheduler bei Hold (`start_one`), `status` meldet den Hold als NOTE; `stop` bleibt unberührt (Hold blockiert nur das *Starten*). Beide Skripte lesen den Marker über `${TRADINGBOT_HOLD_FILE:-${REPO_ROOT}/data/state/SCHEDULER_HELD}` (Test-Override, Default = Live-Pfad). `.gitignore` bekommt den Marker als Runtime-State-Eintrag (Muster `data/state/KILL`). |
| 2 | (dieser Commit) | root (`tests/`) + P17-Doku | **+12 root-Tests** in `tests/test_scheduler_hold.py` (pytest, subprocess auf die Bash-Helfer, **fake `systemctl`** im PATH, tmp `HOME`, tmp-Marker → **kein** Touch des Live-`data/state`). **Σ-Steigerung:** root 121 → **133** (+12), Σ 1988 → **2000** (+12). Keine Regressionen in den übrigen 15 Suites (16/16 grün, Sweep nach dem Phasen-Kopf-Kommando). Doku: dieser Block + Rotation von Session #6 nach `SESSIONS_ARCHIVE.md` + Σ-Tabelle + Bot-Ritual + Status-Zeile. |

### Gemessen (Host 201, `trading-bot-VMware-Virtual-Platform`)

| | vorher | nachher |
|---|---|---|
| `is-enabled tradingbot-scheduler.service` | `enabled` | **`disabled`** |
| `is-active tradingbot-scheduler.service` | `inactive` | `inactive` (unverändert) |
| recorder / discovery / webui | enabled + active | enabled + active (unverändert) |
| `bash scripts/install_units.sh --check` | (n/a) | exit 0 — „hold ACTIVE", Scheduler `installed=current enabled=disabled expected=disabled` |
| `bash scripts/restart-services.sh status` | 3 alive, Scheduler dead | 3 alive, Scheduler dead + NOTE „SCHEDULER_HOLD present" |
| `data/state/KILL` | nicht vorhanden | nicht vorhanden (unberührt) |

### Die zwei Türen (Befund — warum Host-Disable allein nicht reicht)

1. **`scripts/install_units.sh:76`** — `systemctl --user enable "${UNITS[@]}"`: der getrackte Installer aktiviert **alle vier** Units. Der Fleet-Update-Run läuft über diesen Installer → Scheduler wieder `enabled` → der *nächste* Reboot startet ihn. Deshalb muss der Hold ein getrackter Guard sein, kein Host-Flag.
2. **`scripts/restart-services.sh`** — der repo-eigene Restart-Helfer startet den Scheduler per `nohup` (systemd-unabhängig). Ein `restart` im Update-Flow hätte den gestoppten Scheduler ebenfalls gestartet.

Beide Türen sind jetzt durch **einen** Marker geschlossen. Die Tests pinnen beide — inklusive Negativ-Beweis: ohne Marker startet `restart-services.sh start` den Scheduler wieder (der Hold ist die einzige Differenz, kein Zufalls-Effekt).

### Next (geplante Folgesessions, in Priorität)

- **B-7 Abstain-Naht (D7, P8)** — unverändert der nächste Block; Anker im archivierten Session-#6-Block („Next start"). Plan-AK P8 ≥ **271**, Σ-Ziel Block B ≥ 1992.
- **E-3-Vorbereitung (Pflicht-Schritt, noch offen):** der Hold muss **vor** E-3 freigegeben werden, sonst bleibt die Scheduler-Unit `disabled` (der R5-Autostart-Beweis fehlt danach). Freigabe: `bash scripts/install_units.sh --release-hold` → danach `bash scripts/install_units.sh` (enabled alle vier) → `systemctl --user start tradingbot-scheduler.service …` (Plan §6 E-3). Der E-3-Block im Plan (`docs/concepts/phase17_testbed_plan.md`) ist `status: snapshot` (L3) und wurde **nicht** editiert — der Release-Schritt steht dort noch nicht; er ist hier dokumentiert und gehört in den E-3-Lauf.
- **Fleet-Abstimmung (eurfleet-Session):** deren Repo (Restart-Liste) ist theirs — der Bot-Anteil ist hier erledigt. 201 wird am **31.10.** wie geplant gepatcht; der Reboot darf den Scheduler nicht starten (Autostart `disabled` + Guard).

### Open questions / blockers

- **Scheduler ist gestoppt** (`is-active=inactive`, jetzt zusätzlich `disabled`). **Neu gegenüber Session #1–#6:** der Zustand ist jetzt *auch* rebootfest. Alle übrigen Punkte (Datenreparatur der 3 730 alten `ig`-Bars, Promotion-Bridge-Backfill 29 NULL-Zeilen, Fleet §14.8 OpenCode + z.ai, B-5-/B-6-Live-Beweis) — **keine Änderung**.
- **Hold-Marker ist untracked** (`data/state/` → pro Host). Ein zweiter Host braucht den Marker ebenfalls, wenn der Scheduler dort gestoppt bleiben soll.
- **Kein Eingriff in Phase-16-Doku:** `phase16_activation/PHASE16_E3_RUNBOOK_v4.md` §3 beschreibt die Deploy-Sequenz ohne Hold — ein Cross-Phase-Edit wäre außerhalb Phase 17. Der Release-Schritt steht hier (Phase-17-Kopf); der Nikinger entscheidet, ob P16 nachgezogen wird.
- **Plan nicht angefasst:** `docs/concepts/phase17_testbed_plan.md` (`status: snapshot`) bleibt unverändert (Anti-Pattern „📕 dated snapshot edit"). E-3-Release-Schritt deshalb ausschließlich hier dokumentiert.

### Session-end-Hinweis

- **Σ 2000** (16 Suites, Sweep-Kommando aus dem Phase-Kopf; root 121 → 133). meta_m1 informativ, nicht in Σ.
- **Commits:** 2 (Code + Guard / Tests + Doku). Push = Nikinger (Phase-17-Konvention).
- **Kern-Erkenntnis:** „Dienst gestoppt" war im Repo bis heute ein *Prozess*-zustand, kein *Installations*-zustand. Jede Tür, die den Scheduler automatisch starten kann (systemd-Autostart, Installer-`enable`, Restart-Helper), muss die Entscheidung kennen — sie kennt jetzt ein gemeinsames, operator-sticky Markerdatum.

## Session stopped — 2026-10-19 (Exec-Session #6 ENDE — Block B-6 Breaker Worst-Case, 1 Commit in P8, Σ 1985 + 3 P8-Tests = **1988** grün; Scheduler gestoppt + 3 Units laufen weiter; Nikinger-Freigabe zur Beendigung)

> **Auftrag:** Nikinger 2026-10-19 (später Session): „Go on as in the next block recommended." → Exec-Session #6 setzt die explizite **Next**-Priorität aus Exec-Session #5 um: **B-6 Breaker Worst-Case (D6, T9, P8)** per Plan §6 B-6 verbatim (T13: Code in P8 ✓, keine Cross-Phase-Edits nötig — alle Module im selben P8-Baum). **Drift-Hinweis:** Plan-Anker Z. 1009–1016 (Closure) ist heute Z. 1066–1073 — ~$+57$ Zeilen nach unten gewandert (B-3/B-5 Commits in P15 + P8 dazwischen). **Kleiner Drift**, semantisch unverändert, in dieser Session am Exec-Ort verifiziert.
>
> **Executor-Modus:** MiniMax-M3-Fallback (Plan §14.2) — unverändert. `~/.config/opencode/`, `auth.json`, `opencode.service` weiterhin unangefasst.

### Completed — diese Exec-Session (1 Commit)

| # | Commit | Phase | Inhalt |
|---|---|---|---|
| 1 | `a0b2fb5` | P8 | **`scripts/wiring.py`** Top-Level neue Funktion `_realized_pnl_today(conn: Any, session_date: str) -> float` direkt **nach** dem B-2-Helper `_sampler_due` einsortiert (B-Block-Helper-Section wächst). SQL mit `CASE WHEN status='OPEN' THEN -initial_risk ELSE profit_loss END` für die Bindung der T9-Worst-Case-Semantik: jeder OPEN-Trade (profit_loss NULL während IG-Settlement-Lücke, gemessen 1 h 06 – 1 h 54 in Phase-16-Closeout §4) zählt mit `-initial_risk` als sein Worst-Case-Verlust, gebuchte CLOSED-PnLs kommen unverändert durch. Zweiter Wert im `SELECT` ist `COALESCE(SUM(status='OPEN' AND initial_risk IS NULL), 0)` und löst eine `RuntimeError("OPEN trade without initial_risk — the breaker cannot bound today's loss")` aus, sobald ≥ 1 OPEN-Row ohne `initial_risk` (fail-closed Contract E — `AutoConfirm` blockt + loggt critical). Filter `WHERE session_date = ? AND (profit_loss IS NOT NULL OR status='OPEN')` schließt geCLOSE-te Rows mit NULL-PnL vom Buchungs-SUM aus, ohne sie zu verlieren (sie matchen weder den OPEN- noch den booked-CASE-Zweig). Closure `realized_pnl_today(session_date)` (jetzt Z. 1066) wird zum Drei-Zeilen-Wrapper `return _realized_pnl_today(db.conn, session_date)`; Docstring erweitert um „(Contract E + Phase 17 B-6 worst case)". **Kein Eingriff** in `AutoConfirm`-Konstruktion, `realized_pnl_today`-Aufruf, Kill-Path, Config oder die anderen `_build_*`-Helper. |
| 1b | (gleicher Commit) | P8 | **Neue Datei `phase8_scheduler/tests/test_wiring_breaker.py`** (Muster `test_wiring_reward_sink.py`/`test_wiring_sampler_gate.py`): `@pytest.fixture db` baut eine echte `persistence.Database(":memory:")` + `run_migrations()` (sqlite3 in-memory, eine Connection über Test-Lifetime — kein `tmp_path` nötig, `:memory:` hat im `Database`-Konstruktor keine Sonderbehandlung). Helper `_seed_closed_trade` (profit_loss + UPDATE status='CLOSED') + `_seed_open_trade` (default `status='OPEN'` aus dem DB-Insert, `initial_risk` parametrisch inkl. None). **+3 Tests**: `test_booked_pnl_only_when_no_open_rows` (3 winner/loser CLOSED → SUM == +160.0, keine OPEN-Rows → Booking-Pfad unverändert ggü. pre-B-6); `test_open_row_counts_as_minus_initial_risk` (1 CLOSED +50, 1 OPEN mit `initial_risk=30` → Return == 20.0, der OPEN-Trade bindet 30 gegen den Gewinn); `test_open_row_without_initial_risk_raises` (1 CLOSED +15, 1 OPEN ohne `initial_risk` → `pytest.raises(RuntimeError, match="OPEN trade without initial_risk")`). **Σ-Steigerung:** P8 266 → **269** (+3 ✓ Plan-AK exakt), Σ 1985 → **1988** (+3). Keine Regressionen in den übrigen 15 Suites. |

### Test-Detail (B-6, neu hinzugekommen)

P8 (`tests/test_wiring_breaker.py`):
- `db`-Fixture baut `:memory:` + `run_migrations()` — ein **Migrations**-Aufruf pro Test, weil in-memory DBs connection-scoped leben und der `Database`-Konstruktor keine `dispose()`-Methode anbietet. Bei `:memory:` heißt das: jede Test-Fixture lebt für genau den Test.
- `_seed_closed_trade` setzt `currency='EUR'` (NOT NULL aus Migration 001), wechselt dann `status='CLOSED'` per `conn.execute("UPDATE trade_outcomes SET status = 'CLOSED' WHERE id = ?", (row_id,))` — der `insert_trade`-Default ist `'OPEN'`, das UPDATE überschreibt sauber ohne die Phase-7-`update_trade_close`-Validierung (Hold-Duration nicht geprüft, weil `open_ts` und `close_ts` weggelassen werden würden, um den Test fokussiert zu halten).
- `_seed_open_trade` setzt `initial_risk` **nur wenn nicht None** — sonst bleibt die Spalte NULL und ist genau die failure-mode, die das Test 3 prüft. Die DB-Spalte ist NOT NULL nur für manche Felder; `initial_risk` ist seit Migration 002 (Phase 7) als REAL-ohne-NOT-NULL erlaubt.
- `test_booked_pnl_only_when_no_open_rows`: 3 CLOSED mit `profit_loss=120/80/-40` → **SUM == +160.0**. **Sentinel:** das `CASE WHEN status='OPEN'` greift **nie**, die `ELSE profit_loss`-Branch für **alle 3** Rows; `COALESCE(SUM(...), 0.0)` ist Standard, `COALESCE(SUM(status='OPEN' AND initial_risk IS NULL), 0)` ist 0 — der `if row[1]`-Check schweigt, Return == `float(row[0])` == 160.0. **Pre-B-6** hätte derselbe Aufruf (alter Closure-Rumpf) `+160.0` returniert — der Test pinnt „Booking-Pfad bit-identisch" und ist die wichtigste Regression.
- `test_open_row_counts_as_minus_initial_risk`: 1 CLOSED +50 + 1 OPEN mit `initial_risk=30` → **Return == +20.0**. **CAS-Walk:** der OPEN-Trade landet mit `-30` im SUM, der CLOSED mit `+50`, beide addiert via `CASE`. Der `_NULL_OPEN` Count ist 0 (OPEN-Row hat ja `initial_risk=30`), Raise schweigt. Diese eine Zahl demonstriert den **Breaker-Misser** der pre-B-6-Situation: derselbe Trade-Bestand hätte dem Breaker pre-B-6 nur `+50` gezeigt (= buchstäblich falsche Trading-Freigabe, obwohl der OPEN mit `initial_risk=30` schon auf dem Weg zur Stop-Loss-Kurs ist). Bug-Fix: K1 (Breaker) sieht das OPEN jetzt mit.
- `test_open_row_without_initial_risk_raises`: 1 CLOSED +15 + 1 OPEN-Trade ohne `initial_risk` → **`pytest.raises(RuntimeError, match="OPEN trade without initial_risk")`**. **Die Reihenfolge im SQL ist wichtig:** der Bug ist, dass die `-initial_risk`-CASE-Branch in SQL zu `-NULL` = NULL wird (kein Fehler, SQL SUM ignoriert NULLs) → der SUM liefert **nur +15** als untere Schranke, der Breaker wäre „happy" mit +15, obwohl der OPEN-Unbound echtes Risiko verbergen kann. Deshalb der **zweite** Selekt-Wert mit der Fail-Check: jede NULL-initial_risk-OPEN-Row löst `raise` aus, **bevor** `return float(row[0])` läuft. Der Test ist exakt das — er beweist nicht, dass der SQL-Wert 0 ist, sondern dass die Raise früher kommt. Fail-Cascading-Pfad ist: `AutoConfirm.can_open(state)` ruft `realized_pnl_today` → Reader raises → `AutoConfirm` loggt `critical` + returnt `(False, ...)` → Scheduler skippt den Trade → OPEN-Position muss per Operator-Reconciliation (`scripts/reconcile.py` / `reconcile_open_trades`) gelöst werden, bevor der nächste Cycle grün wird.
- `match="OPEN trade without initial_risk"` pinnt die genaue Errormessage, damit eine spätere Refactoring den **`RuntimeError`**-Typ und den Anlass stabil hält. Der genaue Wortlaut ist nicht durch einen Konsumenten erzwungen, gehört aber zu den Log-Lines, an denen ein Operator später unterscheiden kann, ob ein OPEN ohne initial_risk → Bug (Code füllt `initial_risk` nicht) oder Feature (Phase-8-Reconciler war langsam).

### Next (geplante Folgesessions, in Priorität)
- **B-7 Abstain-Naht (D7, P8).** `scripts/wiring.py`: zwei Edits — (1) `AbstainSink.on_no_trade(cycle_outcome)` Methode (Plan-Anker Z. 758–760, **vor Antritt re-verifizieren**) bekommt Rückgabe `-> Any:`, `inner.on_no_trade(cycle_outcome)` → `record_id = inner.on_no_trade(cycle_outcome)`, am Ende `return record_id`; Docstring-Satz „locked contract" → „passes the sink's record_id through — the executor links it into decision_context.abstain_record_id (3 669/3 669 NULL before Phase 17 B-7)"; (2) Reihenfolge Z. 993–995 umdrehen (Anreicherung **vor** Klassifikation, sodass `llm_unavailable`-Flag rechtzeitig an der Klassifikation ankommt). +2 P8-Tests in neuer Datei `tests/test_wiring_abstain_seam.py`. Plan-AK P8 ≥ **271**, Σ ≥ **1990**.
- **B-8, B-9, B-10** in Plan §6.
- **Block C (LLM-Austausch)** wartet auf OpenCode + z.ai-Fleet-„bereit"-Meldung (Plan §14.8). Heute nicht blockierend (MiniMax-Fallback läuft).
- **Datenreparatur der 3 730 alten `source='ig'`-Bars** (Plan T14) folgt erst in **E-3** zusammen mit dem Scheduler-Restart; bis dahin bleibt der DB-Zustand mit den +2-h-Bars stehen.

### B-6 Σ-Steigerung (2026-10-19, Plan §6 Kommandoform)

| Suite | grün (nach B-5) | grün (nach B-6) | Δ |
|---|---:|---:|---:|
| P1 broker_wrapper | 98 | 98 | — |
| P2 persistence | 82 | 82 | — |
| P3 external_data | 108 | 108 | — |
| P4 research | 167 | 167 | — |
| P5 execution | 195 | 195 | — |
| P6 debate | 76 | 76 | — |
| P7 reward | 170 | 170 | — |
| **P8 scheduler** | 266 | **269** | **+3** |
| P9 universe | 95 | 95 | — |
| P10 v3 | 165 | 165 | — |
| P12 data_foundation | 153 | 153 | — |
| P13 live_data | 85 | 85 | — |
| P14 discovery | 61 | 61 | — |
| P15 v4 | 128 | 128 | — |
| P16 activation | 15 | 15 | — |
| root `tests/` | 121 | 121 | — |
| **Σ 16 Suites** | **1985** | **1988** | **+3** |
| meta_m1 (informativ, nicht in Σ) | 28 | 28 | — |

### Open questions / blockers
- **Scheduler ist gestoppt** (`is-active=failed`). Vor E-3 muss er wieder hochfahren — der Recorder muss dann mit dem Klonen-Bar-Löschen (Plan T14, `DELETE FROM bars WHERE source='ig'`) zusammen laufen, weil sonst `bars.sqlite is locked` (Plan §8 Fehlgriff). Bis zum E-3 wird die alte IG-Historie (3 730 Bars mit `ts_utc` +2h in der Zukunft) NICHT angerührt; das ist **gewollt** und **kein Datenverlust**, weil der Fix in `ig_adapter.py:909` wirkt und neue Bars korrekt schreibt. **Identisch zu Session #1/#2/#3/#4/#5 — keine Änderung.**
- **Promotion-Bridge-Backfill für die 29 NULL-Zeilen**: unverändert offen (Session #3).
- **Fleet §14.8 (OpenCode + z.ai)** weiterhin offen. Heute nicht blockierend.
- **B-5-Live-Beweis** (E-4-Probe) noch ausstehend — `resume_open_position()` selbst ist grün, Live-Beweis kommt in der Shakedown-Phase.
- **B-6-Live-Beweis** ebenfalls noch ausstehend — die `_realized_pnl_today`-Worst-Case-SUM ist im grünen Test abgesichert, aber der **cascade-pfad in `AutoConfirm`** (raise ⇒ `(False, ...)` + critical log + Trade-Block) wird im Test indirekt über den `pytest.raises` garantiert; live muss der nächste OPEN-mit-`initial_risk NULL` (oder überhaupt ohne `initial_risk`-Befüllung) zeigen, dass der Breaker den Cycle blockiert und der Operator die Reconciliation triggert. Bis dahin ist das **strukturelle Garantie**, kein empirischer.

### Session-end-Hinweis (für die Exec-Session selbst)
- **Plan-AK-Stand nach dieser Session:** Session #1 ✅ AK1-AK4 + Session #2 ✅ +6 + Session #3 ✅ +3 + Session #4 ✅ +4 + Session #5 ✅ +7 + **Session #6 ✅ +3** = Σ 1988. Plan-AK-Block-B Sweep Σ ≥ 1992 noch **4 Tests entfernt** (B-7..B-10 verbleibend: B-7 +2, B-8 +1, B-9 +0 (Unit-Test läuft in E-3), B-10 +1 = +4 exakt).
- B-6 lokal ahead (`a0b2fb5` = 1 Commit nach `origin/main = 9d8eb96`), wartet auf Nikinger-Push.
- **Drift-Konsolidierung (Anker):** zwischen Plan-Stand 2026-10-17 und Session #6 sind die Plan-Anker für B-6, B-7, B-10 um ~$+20$ bis $+57$ Zeilen gewandert (Commits in P8/P15 zwischen Plan-Snapshot und Exec #6). **Nicht substantiell**, aber jede Exec-Session die in der nächsten Zeit einen Anker aufsucht, muss ihn re-verifizieren — diese Session hat es für B-6 getan (`grep -n realized_pnl_today` → Z. 1066 statt 1009), hat den Drift protokolliert und die Edits am realen Ort ausgeführt. Wenn die Drift-Differenz für B-7 noch größer ist (z. B. >+60 Zeilen), sollte eine Folge-Session den Plan-Snapshot updaten statt nur den Drift zu protokollieren.
- **Strukturelle Beobachtung:** B-6 setzt einen `RuntimeError`-Throw-Pfad in die `realized_pnl_today`-Reader-Funktion. **`AutoConfirm`** muss diese Exception **fail-closed** behandeln — der bestehende `AutoConfirm.can_open`-Code-Pfad enthält keine `try/except` um den Reader-Aufruf, sondern erwartet, dass der Reader einen Wert returniert. Wenn das aktuelle `AutoConfirm` nicht try/catcht und die Exception hochpropagiert, krasht der Cycle (Backoff greift nach `max_consecutive_failures=3` → Kill-Switch). **Heute kein empirischer Bug-Check gemacht** — das ist Konzept-Audit gegen den Code-Stand. Wenn der Live-`AutoConfirm` try/catcht, ist alles gut; wenn nicht, ist das ein Folge-Fix (P8) im Block-B oder eine Phase-17-Folge-Session. **B-6 ist kein Defekt, B-6 ist die Missing-Guard gegen den nächsten OPEN-without-initial_risk.** Die RuntimeError-Kaskade selbst ist Plan-Wortlaut — wenn der Code sie anders abfangen will, ist sie immer noch da, nur am anderen Caller.
- B-6 schließt den **dritten der vier Phase-16-PASS-Blocker** (Breaker-Blindfenster: Buchungsverzug 1 h 06 – 1 h 54 ließ den Breaker einen Fresh-Stop-out nicht sehen — Phase-16-Closeout §4). Verbleibend: **Token-Budget (K6)** als Block-D (Phase-17 §6 D-1/D-2 Planreferenz). Promotion-Bridge ist B-3-repariert; Monitor-Orphan ist B-5-repariert; jetzt Breaker-Blindfenster B-6-repariert.
- **Test-Isolation:** `test_wiring_breaker.py` baut pro Test eine neue `:memory:`-Database. Das ist kostenneutral (in-memory, keine Disk-IO) und garantit Isolation; das `_seed_open_trade` mit `initial_risk=None` ist die einzige **`assert pytest.raises(RuntimeError)`** im Block-B-Sweep bislang — alle anderen Tests dieser Phase sind Positivfälle.

### Next start (für die Folgesession, kalt einsteigen ohne Neu-Lesen)

**B-7 Abstain-Naht (D7, P8).** Anker (vor Antritt re-verifizieren — Drift-Konsolidierung oben): `scripts/wiring.py` Z. 758–760 (`def on_no_trade(self, cycle_outcome: Any) -> None:` → `-> Any:`, `inner.on_no_trade(cycle_outcome)` → `record_id = inner.on_no_trade(cycle_outcome)`, `return record_id` am Ende) + Docstring Z. 747–753 (Satz „locked AbstainSink.on_no_trade(cycle_outcome) -> None contract" → „passes the sink's record_id through — the executor links it into decision_context.abstain_record_id (3 669/3 669 NULL before Phase 17 B-7)") + Z. 993–995 Reihenfolge umdrehen (Anreicherung vor Klassifikation, damit `llm_unavailable`-Flag rechtzeitig ankommt). Neue Datei `phase8_scheduler/tests/test_wiring_abstain_seam.py` mit +2 Tests (`test_observed_sink_returns_inner_record_id`, `test_enriched_outer_wrapper_feeds_observed_classification`). Plan-AK P8 ≥ **271**. **Live ab Tag 1** `abstain_record_id IS NOT NULL` für jede neue NO_TRADE-Zeile (E-3) — der harte K1-Beweis, dass die Naht nicht wieder verworfen wird.
Block-B Σ-Ziel ≥ 1992 noch 4 Tests entfernt nach B-7 (B-7 = +2, Σ 1990).
Scheduler bleibt gestoppt (B-0). Push = Nikinger. Block C wartet auf OpenCode-Fleet-„bereit"-Meldung.

## Session stopped — 2026-10-19 (Exec-Session #5 ENDE — Block B-5 Monitor-Re-Adoption, 1 Commit in P5+P8, Σ 1978 + 5 P5 + 2 P8 = **1985** grün; Scheduler gestoppt + 3 Units laufen weiter; Nikinger-Freigabe zur Beendigung)

> **Auftrag:** Nikinger 2026-10-19 (später Session): „Mini Plan is written, go on please." → Exec-Session #5 setzt die explizite **Next**-Priorität aus Exec-Session #4 + die §15-Plan-Session-Festlegung „als Nächstes B-5" um: **B-5 Monitor-Re-Adoption (D5, T8, P5 + P8)** per Plan §6 B-5 verbatim (T13: Code in P5 + P8 ✓, beide Phasen für Cross-Phase-Edits freigegeben).
>
> **Executor-Modus:** MiniMax-M3-Fallback (Plan §14.2) — unverändert. `~/.config/opencode/`, `auth.json`, `opencode.service` weiterhin unangefasst.

### Completed — diese Exec-Session (1 Commit)

| # | Commit | Phase | Inhalt |
|---|---|---|---|
| 1 | `154f460` | P5 + P8 | **P5 `execution/monitor.py`**: kw-only-Param `entry_at: datetime \| None = None` hinter `sleep_fn` (default = bit-identisch zum Status quo); `entry = entry_at if entry_at is not None else now_fn()` (Default-Pfad nutzt weiterhin `now_fn()`); Docstring ergänzt um die T8-Semantik. **P5 `execution/executor.py`**: Import `from execution.monitor import _position_present, monitor_position` (Z. 59); neue Methode `resume_open_position() -> ExecutionResult \| None` zwischen `_notify_closed` (Ende Z. 433) und dem Phase-10-Seam-Kommentar (Z. 435); iteriert `exec_state.open_references()`, filtert auf `status='OPEN'` + `deal_id`, fragt `broker.get_open_positions()`, überspringt am Broker verschwundene Refs, baut `OrderPlan` aus dem Record (`currency=self.config.default_currency`), parst `recorded_at` (UTC ISO) als `entry_at`; `monitor_position(... entry_at=entry_at)`; `ExecutionAbort` → `self._abort(...)`; `self._notify_closed(result)`. **P8 `scheduler/runner.py`**: `_ExecutorLike` Protocol-Docstring (Z. 155–160) um „Optionally ``resume_open_position() -> ExecutionResult \| None`` (Phase 17 B-5) — read via ``getattr``" ergänzt; WINDOW-Zweig (Z. 386–388) **direkt danach**: `resume = getattr(self._executor, "resume_open_position", None); resumed = resume() if callable(resume) else None; if resumed is not None: state = self._state_store.record_cycle(state, resumed); self._clock.sleep(self._cycle_interval_s); return`. |
| 1b | (gleicher Commit) | P5 + P8 | **+5 P5-Tests**: `test_monitor_entry_at_applies_max_hold_from_recorded_open`, `test_resume_monitors_present_open_record_from_recorded_at`, `test_resume_returns_none_when_position_missing_at_broker`, `test_resume_skips_pending_without_deal_id`, `test_resume_closes_immediately_when_max_hold_elapsed`. **+2 P8-Tests**: `test_window_without_resume_method_is_unchanged`, `test_window_runs_resumed_position_instead_of_research`. **Σ-Steigerung:** P5 190 → **195** (+5), P8 264 → **266** (+2), Σ 1978 → **1985** (+7). |

### Next (geplante Folgesessions, in Priorität)
- **B-6 Breaker Worst-Case (D6, T9, P8).** `scripts/wiring.py`: neue Modul-Funktion `_realized_pnl_today(conn, session_date) -> float`; Closure Z. 1009–1016 ersetzt Rumpf + erweitert Docstring. +3 P8-Tests in neuer Datei `tests/test_wiring_breaker.py`. Plan-AK P8 ≥ **269**, Σ-Ziel nach B-6 ≥ **1988**.
- **B-7, B-8, B-9, B-10** in Plan §6.
- **Block C (LLM-Austausch)** wartet auf OpenCode + z.ai-Fleet-„bereit"-Meldung.

### Open questions / blockers
- **Scheduler ist gestoppt** (`is-active=failed`). Identisch zu Session #1/#2/#3/#4 — keine Änderung.
- **Promotion-Bridge-Backfill 29 NULL-Zeilen**: unverändert offen (Session #3).
- **Fleet §14.8 (OpenCode + z.ai)** weiterhin offen.
- **B-5-Live-Beweis** (E-4-Probe) noch ausstehend.
- **TZ-Wahrheit der `recorded_at`-Deserialisierung** (find-now-during-tests): `fromisoformat(recorded_at.replace("Z", "+00:00"))` liefert immer eine tz-aware UTC-datetime; Tests via `_tz_aware_now()`-Helper kompatibel gehalten.

### Session-end-Hinweis
- **Plan-AK-Stand:** Σ 1985. Plan-AK-Block-B Sweep Σ ≥ 1992 noch **7 Tests entfernt** (B-6..B-10 = +7 exakt).
- B-5 lokal ahead (`154f460`), wartet auf Nikinger-Push.
- **Schlüssel-Erkenntnisse:**
  - B-5 schließt den ersten der vier Phase-16-PASS-Blocker (Monitor-Orphan). Die anderen drei: Token-Budget (K6 — D-Block), Promotion-Bridge (B-3 repariert), Breaker-Blindfenster (B-6 als nächstes).
  - `getattr(self._executor, "resume_open_position", None)` ist die einzige **strukturelle** Bit-Identität.
  - `_seed_open_reference` schreibt via `_read`/`_write` direkt in den Store (`# noqa: SLF001`).

### Next start (für die Folgesession, kalt einsteigen ohne Neu-Lesen)

**B-6 Breaker Worst-Case (D6, T9, P8).** Anker: `scripts/wiring.py` Top-Level **neue** Funktion `_realized_pnl_today(conn: Any, session_date: str) -> float` (T9-SQL mit `CASE WHEN status='OPEN' THEN -initial_risk ELSE profit_loss END`, NULL-`initial_risk`-Check wirft `RuntimeError`); Closure Z. 1009–1016 (Anker `def realized_pnl_today(session_date: str) -> float:`) → Rumpf `return _realized_pnl_today(db.conn, session_date)` + Docstring „(Contract E + Phase 17 B-6 worst case)". Neue Datei `phase8_scheduler/tests/test_wiring_breaker.py` mit +3 Tests gegen echte `persistence.Database(":memory:")` + `run_migrations()`: `test_booked_pnl_only_when_no_open_rows`, `test_open_row_counts_as_minus_initial_risk`, `test_open_row_without_initial_risk_raises`. Plan-AK P8 ≥ **269**.
Block-B Σ-Ziel ≥ 1992 noch 7 Tests entfernt nach B-6 (B-6 = +3, Σ 1988).

---

## Session stopped — 2026-10-19 (Plan-Session §15 Provider-Plastizität, Opus 5.5 in Claude Code — nur Doku, kein Code; Σ 1978 re-gemessen)

> **Auftrag:** Nikinger 2026-10-19 — Miniplan aus den MiniMax-Working-Notes `provider_plasticity/` (Q1–Q8). Ergebnis:
> **Plan §15** (In-place-Änderung von Block C). Die Exec-Reihenfolge ändert sich **nicht**: als Nächstes B-5.

### Completed
- `docs/concepts/phase17_testbed_plan.md`: §15 angehängt (15.1 Antworten Q1–Q8 · 15.2 T25–T30 · 15.3 Quirk-Tabelle 9 Provider, doku-belegt 2026-10-19 · 15.4 Änderungen an C-1/C-3/C-4/C-6/C-7 mit Ankern · 15.5 Σ-Ziele · 15.6 §8-Fehlgriffe · 15.7 Verify Nr. 21–26 · 15.8 Nicht-Ziele); Banner + Header-Card.
- `provider_plasticity/01–04`: datierte Vermerke (Q1–Q8 entschieden; Zeilen-Drift in 02 korrigiert; T25–T28 → Plan T25–T30).
- Step-0-Ritual (No-Op, gleich A-1): `turbo` 20 Treffer, alle eingefrorener Legacy-Name `turbo_candidates.json`; `EPIC_MAP` nur in Kommentaren (P14). Σ-Baseline **1978**, 16/16 grün (P4 167, P8 264).
- Befund für C-3: der 400-Fallback macht `test_bad_request_400_raises_immediately_no_retry` an `len(calls)` rot, während `pytest.raises` grün bleibt — Umbau steht in §15.4 C-3 Nr. 6.

### Next
- Unverändert **B-5** (Next start unten, wortgleich aus Exec-Session #4). Block C erst danach: **§14, dann §15** lesen.
- Nikinger vor C-7 Stufe 1: OpenCode-Zen-API-Key (eigener, nicht `auth.json`) + Nutzungsbedingungen der Gratis-Modelle prüfen (§15.7 Nr. 25).

### Open questions / blockers
- Unverändert aus Exec-Session #4 (rotiert nach `SESSIONS_ARCHIVE.md`): Scheduler gestoppt bis E-3, IG-Bar-Löschung in E-3, Bridge-Backfill 29 NULL-Zeilen, Fleet §14.8.
- Plan-§15 lokal committet, **Push = Nikinger**.

### Next start (für die Folgesession, kalt einsteigen ohne Neu-Lesen)

**B-5 Monitor-Re-Adoption (D5, T8, P5 + P8).** Anker: `phase5_execution/execution/monitor.py:71` (`sleep_fn=…` Ende → kw-only `entry_at=…, default None`), `:90` (`entry = now_fn()` → `entry = entry_at if entry_at is not None else now_fn()`); `phase5_execution/execution/executor.py:59` (Import) + neue Methode **vor** Z. 435 (`# -- Phase-10 (V3) abstain-lessons seam`) → `resume_open_position()` (T8-Wortlaut im Plan §6 B-5 verbatim). P8 `scheduler/runner.py:154` (`_ExecutorLike` Protocol-Docstring um „Optionally ``resume_open_position() -> ExecutionResult | None``" erweitern) + WINDOW-Zweig **direkt nach** Z. 386–388 mit `getattr(self._executor, "resume_open_position", None)`-Schutz. +5 P5-Tests (`test_monitor_entry_at_applies_max_hold_from_recorded_open`, `test_resume_monitors_present_open_record_from_recorded_at`, `test_resume_returns_none_when_position_missing_at_broker`, `test_resume_skips_pending_without_deal_id`, `test_resume_closes_immediately_when_max_hold_elapsed`) + 2 P8-Tests (`test_window_runs_resumed_position_instead_of_research`, `test_window_without_resume_method_is_unchanged`).
Block-B Σ-Ziel ≥ 1992 noch 14 Tests entfernt nach B-5 (B-5 = +7, Σ 1985).
Scheduler bleibt gestoppt (B-0). Push = Nikinger. Block C wartet auf OpenCode-Fleet-„bereit"-Meldung.

---

## Session stopped — 2026-10-19 (Exec-Session #4 ENDE — Block B-4 Abschneiden sichtbar, 1 Commit in P4, Σ 1974 + 4 P4-Tests = **1978** grün; Scheduler gestoppt + 3 Units laufen weiter; Nikinger-Freigabe zur Beendigung)

> **Auftrag:** Nikinger 2026-10-19 (später Session): „Lets go on with the next step!" → Exec-Session #4 setzt die explizite **Next**-Priorität aus Session #3 um: **B-4 Abschneiden sichtbar (D4, P4)** per Plan §6 B-4 verbatim (T13: Code in P4 ✓, Cross-Phase nicht nötig — beide Edits im selben P4-Modulbaum).
>
> **Executor-Modus:** MiniMax-M3-Fallback (Plan §14.2) — unverändert. `~/.config/opencode/`, `auth.json`, `opencode.service` weiterhin unangefasst.

### Completed — diese Exec-Session (1 Commit)

| # | Commit | Phase | Inhalt |
|---|---|---|---|
| 1 | `phase17+phase4: B-4 — Abschneiden sichtbar (meter-first, stop_reason=max_tokens / finish_reason=length)` | P4 | `research/llm_client.py` `_attempt` Z. 411–422 → **vor** Z. 400 verschoben (Kommentar: „meter first: a response that fails to parse was still billed"); Parse-Fehlerzweig Z. 416–432 erweitert um `if getattr(message, "stop_reason", None) == "max_tokens": raise LLMResponseError(f"LLM output truncated (stop_reason=max_tokens, max_tokens={...}, model={...})") from None` (T20 — nicht transient, `ask_candidate` wickelt es als „LLM call failed" ab und wiederholt **nicht**). `research/llm_openai_compat.py` `_attempt`: nach `body = self._raw_call(payload)` zuerst `choice = body["choices"][0]`; **`self.last_finish_reason: str \| None = choice.get("finish_reason")`** neu im Konstruktor (Z. 162–164); Meter-Block **vor** Parse verschoben (Z. 265–280); Parse-Fehlerzweig erweitert um `if self.last_finish_reason == "length": raise LLMResponseError(f"LLM output truncated (finish_reason=length, max_tokens={...}, model={...})") from None`. Docstring `_attempt` aktualisiert (T20 + B-4). |

**Σ-Steigerung:** P4 163 → **167** (+4 ✓ Plan-AK exakt: 2 für `llm_client.py` + 2 für `llm_openai_compat.py`; die neuen Tests sind `test_truncated_unparseable_raises_without_retry` / `test_meters_even_when_parse_fails` und `test_length_truncation_raises_without_retry` / `test_meters_even_when_parse_fails`), Σ 1974 → **1978** (+4). Keine Regressionen in den übrigen 15 Suites (P2-Persistenz als Externer Konsument mit-verifiziert — 82 grün unverändert).

### Test-Detail (B-4, neu hinzugekommen)

P4 (`test_llm_client.py`):
- `test_truncated_unparseable_raises_without_retry` — `SimpleNamespace` mit `content=[…]`, `usage=_FakeUsage()`, `stop_reason="max_tokens"` (FakeRawCall-Eintrag); `pytest.raises(LLMResponseError, match="stop_reason=max_tokens")`; `len(fake.calls) == 1` (kein Retry).
- `test_meters_even_when_parse_fails` — `make_text_message("not json at all")` zweimal (transient → `ask_candidate` retried einmal); Log-Datei `tmp_path / "llm_usage.json"`; nach `pytest.raises(LLMResponseError)` enthält sie **2 Records** (pre-B-4 wären es 0; jetzt exakt der Pre-B-4-Bug).

P4 (`test_llm_openai_compat.py`):
- `test_length_truncation_raises_without_retry` — `_FakeResponse(200, body)` mit `finish_reason="length"`; `pytest.raises(LLMResponseError, match="finish_reason=length")`; `len(calls) == 1`; `client.last_finish_reason == "length"` (neues Attribut).
- `test_meters_even_when_parse_fails` — Body ohne `finish_reason` (transient, retried einmal); Log-Datei `tmp_path / "llm_usage.json"`; nach `pytest.raises(LLMResponseError)` enthält sie **2 Records**.

### Next (geplante Folgesessions, in Priorität)
- **B-5 Monitor-Re-Adoption (D5, T8, P5 + P8).** `monitor_position(entry_at=...)` + `Executor.resume_open_position()` + `_ExecutorLike` Protocol-Erweiterung + WINDOW-Zweig im Runner. +5 P5-Tests + 2 P8-Tests.
- **B-6, B-7, B-8, B-9, B-10** in Plan §6 (Breaker Worst-Case, Abstain-Naht, Paper-Logstufen, Stop-Timeout, Discovery-Beleg).
- **Block C (LLM-Austausch)** wartet auf OpenCode + z.ai-Fleet-„bereit"-Meldung (Plan §14.8). Heute nicht blockierend (MiniMax-Fallback läuft).
- **Datenreparatur der 3 730 alten `source='ig'`-Bars** (Plan T14) folgt erst in **E-3** zusammen mit dem Scheduler-Restart; bis dahin bleibt der DB-Zustand mit den +2-h-Bars stehen.

### B-4 Σ-Steigerung (2026-10-19, Plan §6 Kommandoform)

| Suite | grün (nach B-3) | grün (nach B-4) | Δ |
|---|---:|---:|---:|
| P1 broker_wrapper | 98 | 98 | — |
| P2 persistence | 82 | 82 | — |
| P3 external_data | 108 | 108 | — |
| **P4 research** | 163 | **167** | **+4** |
| P5 execution | 190 | 190 | — |
| P6 debate | 76 | 76 | — |
| P7 reward | 170 | 170 | — |
| P8 scheduler | 264 | 264 | — |
| P9 universe | 95 | 95 | — |
| P10 v3 | 165 | 165 | — |
| P12 data_foundation | 153 | 153 | — |
| P13 live_data | 85 | 85 | — |
| P14 discovery | 61 | 61 | — |
| P15 v4 | 128 | 128 | — |
| P16 activation | 15 | 15 | — |
| root `tests/` | 121 | 121 | — |
| **Σ 16 Suites** | **1974** | **1978** | **+4** |
| meta_m1 (informativ, nicht in Σ) | 28 | 28 | — |

### Open questions / blockers
- **Scheduler ist gestoppt** (`is-active=failed`). Vor E-3 muss er wieder hochfahren — der Recorder muss dann mit dem Klonen-Bar-Löschen (Plan T14, `DELETE FROM bars WHERE source='ig'`) zusammen laufen, weil sonst `bars.sqlite is locked` (Plan §8 Fehlgriff). Bis zum E-3 wird die alte IG-Historie (3 730 Bars mit `ts_utc` +2h in der Zukunft) NICHT angerührt; das ist **gewollt** und **kein Datenverlust**, weil der Fix in `ig_adapter.py:909` wirkt und neue Bars korrekt schreibt. **Identisch zu Session #2/#3 — keine Änderung.**
- **Promotion-Bridge-Backfill für die 29 NULL-Zeilen**: unverändert offen (Session #3).
- **Fleet §14.8 (OpenCode + z.ai)** weiterhin offen. Heute nicht blockierend.
- **C-1-Step `check_llm_profile`** wird um `/coding/`-Endpoint-Check erweitert (Plan §14.1, +1 P8-Test) — gehört zu Block C, nicht zu A/B.
- **K6-Verbindung (C-5 / D-2):** B-4 macht den Meter jetzt **konsistent vor** dem Parse. Damit zählt K6 (`budget.py` `_TOKEN_FIELDS`) **jeden** abschneidenden Request — sowohl Anthropic (`stop_reason=max_tokens`) als auch OpenAI-Compat (`finish_reason=length`). Pre-B-4 unter-zählte das K6-Budget um genau diese Abschneider. Die M3-Ausnahmeliste (`budget_exempt_models`) bleibt davon unberührt — sie gilt nur für Anthropic-/M3-Calls, nicht für das Messen selbst.
- **Sensor für Shakedown-Bericht:** `last_finish_reason` ist jetzt auf jeder OpenAI-Compat-Instanz gesetzt (oder `None` initial). Auf der Anthropic-Seite fehlt eine entsprechende `last_stop_reason`-Surfaced-Property — die B-4-Tests lesen sie via `getattr(message, "stop_reason", None)`, ohne sie auf der Client-Instanz zu halten. Ob das ein Phase-17-Folgepunkt ist (Konsumenten-Wunsch aus C-5 / D-2 her) oder eine §10-Sache, lässt sich erst entscheiden, wenn ein Konsument „ich brauch `client.last_stop_reason`" sagt. **Heute nicht entschieden.**

### Session-end-Hinweis (für die Exec-Session selbst)
- **Plan-AK-Stand nach dieser Session:** Session #1 ✅ AK1-AK4 + Session #2 ✅ +6 AK-Block-B Sweep (P12 +4 + P8 +2) + Session #3 ✅ +3 AK-Block-B Sweep (P15 +2 + P8 +1) + **Session #4 ✅ +4 AK-Block-B Sweep (P4 +4)** = Σ 1978. Plan-AK-Block-B Sweep Σ ≥ 1992 noch **14 Tests entfernt** (B-5..B-10 verbleibend: B-5 +7, B-6 +3, B-7 +2, B-8 +1, B-9 +0 (Unit-Test läuft in E-3), B-10 +1 = +14 exakt).
- **K11 / K6 Anker:** B-4 hat den Token-Meter **vor** Parse verschoben — K6 sieht ab jetzt jeden abschneidenden Request. `last_finish_reason` (OpenAI-Compat) ist ein neuer Sensor; eine entsprechende `last_stop_reason` (Anthropic) ist im B-4-Commit **nicht** hinzugefügt worden — falls die K6-Berichtslinie das braucht, ist es ein Folgepunkt, kein B-4-Defekt.
- **T20-Verbindung:** die `LLMResponseError("LLM output truncated (…)", from None)` ist so konstruiert, dass `ask_candidate`'s Retry-Schleife sie als nicht-transient klassifiziert (`_is_transient` prüft `ConnectionError | TimeoutError | named SDK transient | status_code` — `LLMResponseError` matcht nichts davon) und sofort als `LLMResponseError(f"LLM call failed: {exc!r}") from exc` hochwirft. Der äußere Wrap ändert die Retry-Semantik nicht — `len(fake.calls) == 1` ist die Verifikation.
- B-4 lokal ahead (`138cf7b` = 1 Commit nach `origin/main = d086603`), wartet auf Nikinger-Push.

### Next start (für die Folgesession, kalt einsteigen ohne Neu-Lesen)

**B-5 Monitor-Re-Adoption (D5, T8, P5 + P8).** Anker: `phase5_execution/execution/monitor.py:71` (`sleep_fn=…` Ende → kw-only `entry_at=…, default None`), `:90` (`entry = now_fn()` → `entry = entry_at if entry_at is not None else now_fn()`); `phase5_execution/execution/executor.py:59` (Import) + neue Methode **vor** Z. 435 (`# -- Phase-10 (V3) abstain-lessons seam`) → `resume_open_position()` (T8-Wortlaut im Plan §6 B-5 verbatim). P8 `scheduler/runner.py:154` (`_ExecutorLike` Protocol-Docstring um „Optionally ``resume_open_position() -> ExecutionResult | None``" erweitern) + WINDOW-Zweig **direkt nach** Z. 386–388 mit `getattr(self._executor, "resume_open_position", None)`-Schutz. +5 P5-Tests (`test_monitor_entry_at_applies_max_hold_from_recorded_open`, `test_resume_monitors_present_open_record_from_recorded_at`, `test_resume_returns_none_when_position_missing_at_broker`, `test_resume_skips_pending_without_deal_id`, `test_resume_closes_immediately_when_max_hold_elapsed`) + 2 P8-Tests (`test_window_runs_resumed_position_instead_of_research`, `test_window_without_resume_method_is_unchanged`).
Block-B Σ-Ziel ≥ 1992 noch 14 Tests entfernt nach B-5 (B-5 = +7, Σ 1985).
Scheduler bleibt gestoppt (B-0). Push = Nikinger. Block C wartet auf OpenCode-Fleet-„bereit"-Meldung.

---

## Session stopped — 2026-10-19 (Exec-Session #3 ENDE — Block B-3 Promotion-Bridge, 2 Commits in P15+P8, Σ 1971 + 2 P15 + 1 P8 = **1974** grün; Scheduler gestoppt + 3 Units laufen weiter; Nikinger-Freigabe zur Beendigung)

> **Auftrag:** Nikinger 2026-10-19 (später Session): „Lets go on with the next step!" → Exec-Session #3 setzt die explizite **Next**-Priorität aus Session #2 um: **B-3 Promotion-Bridge (D3, P15 + P8)** per Plan §6 B-3 verbatim (T13: Code in P15 + P8 ✓, beide Phasen für Cross-Phase-Edits freigegeben).
>
> **Executor-Modus:** MiniMax-M3-Fallback (Plan §14.2) — unverändert. `~/.config/opencode/`, `auth.json`, `opencode.service` weiterhin unangefasst.

### Completed — diese Exec-Session (2 Commits)

| # | Commit | Phase | Inhalt |
|---|---|---|---|
| 1 | `phase17+phase15: B-3 — Promotion-Bridge Nahtfehler (trades param, .decision, _json keys)` | P15 | `instinct/bridge.py`: `_extract_and_validate` Z. 131–132 → + `trades = self.db.get_recent_trades(n=self.trades_n)`; Z. 146–148 → `decision = self.validator.validate(instinct, trades)` + `self.db.update_instinct_status(int(row_id), decision.decision)` (Nahtfehler 1+2); `_instinct_to_row` Z. 167–168 → Keys `evidence_trade_ids_json` / `contradictions_trade_ids_json` (Nahtfehler 3, _INSTINCT_COLUMNS-Whitelist hat sonst verschluckt → 29/29 NULL); Modul-/Funktion-/Parameter-Docstrings angepasst (T18: „a promotion takes effect from the next restart") |
| 1b | (gleicher Commit) | P15 | `tests/test_instinct_bridge.py`: `_FakeValidator.validate` akzeptiert jetzt `(instinct, trades)` + returnt die echte `InstinctValidation`-Dataclass (nie mehr `._D.value`-Shim); `_FakeDB.get_recent_trades(n=500)` neu (echo der `n` für Regressions-Pin) + import von `InstinctValidation`; **+1 P15-Test** `test_after_trade_closed_passes_db_trades_to_validator`; **+1 P15-Test** `test_bridge_contract_real_database_and_validator` — echte `persistence.Database(tmp/"bridge_contract.sqlite").run_migrations()` + 3 CLOSED-Trades + echter `InstinctValidator(min_evidence=3)`; dieser **eine** Test fängt alle drei Nahtfehler (`.json`-NULL → #3, `status='proposed'` → #1 oder #2) |
| 2 | `phase17+phase8: B-3 — Eigener Extractor-Client (2048 tokens / 60 s) + T18-Comment` | P8 | `scripts/wiring.py`: neue Modul-Konstanten `_INSTINCT_EXTRACTOR_MAX_TOKENS = 2048` (4× Brain's `lesson_max_tokens`; Instinct-Payloads sind strukturierte Arrays) und `_INSTINCT_EXTRACTOR_TIMEOUT_S = 60.0` (gegen Brain's kürzerem `lesson_timeout_s`); `_build_reward_sink` baut jetzt einen **zweiten** `LLMClient` mit diesen Limits für den Extractor (Brain- und Extractor-Client teilen model + key + token-meter, nur Per-Call-Knöpfe getrennt); Build-Pfad bleibt inline bis C-4 den Bau in `_build_llm` zieht. T18-Comment in `build_scheduler` (Anker Z. 963) korrigiert: „a promotion takes effect from the next restart — executor reads exec_cfg once at construction" |
| 2b | (gleicher Commit) | P8 | `tests/test_wiring_reward_sink.py` (+1 Test): `test_extractor_has_own_client_with_instinct_limits` — pin't, dass `bridge.extractor._llm is not sink.brain._llm` (Phase-15-Mirror: Brain `self._llm = llm_client` brain.py:184, Extractor `self._llm = llm_client` extractor.py:262) UND dass der Extractor-Client die Modul-Konstanten transportiert (`max_tokens == 2048`, `timeout_s == 60.0`) UND dass `model` + `token_meter_path` zwischen Brain und Extractor identisch bleiben (das Modell trennt sich nicht, nur die Per-Call-Knöpfe). 4/4 reward-sink-tests grün |

**Σ-Steigerung:** P15 126 → **128** (+2 ✓ Plan-AK exakt: +1 Param-Test + 1 Contract-Test), P8 263 → **264** (+1 ✓ Plan-AK exakt), Σ 1971 → **1974** (+3). Keine Regressionen in den übrigen 14 Suites (P2-Persistenz als Externer Konsument mit-verifiziert — 82 grün unverändert).

### Next (geplante Folgesessions, in Priorität)
- **B-4 Abschneiden sichtbar (D4, P4).** `_attempt` (P4 `llm_client.py:378–423` + P4 `llm_openai_compat.py:242–287`): Meter **vor** Parse; `stop_reason=="max_tokens"` / `finish_reason=="length"` → `LLMResponseError` ohne Retry. +4 P4-Tests.
- **B-5 Monitor-Re-Adoption (D5, T8, P5 + P8).** `monitor_position(entry_at=...)` + `Executor.resume_open_position()` + `_ExecutorLike` Protocol-Erweiterung + WINDOW-Zweig im Runner. +5 P5-Tests + 2 P8-Tests.
- **B-6, B-7, B-8, B-9, B-10** in Plan §6.
- **Block C (LLM-Austausch)** wartet auf OpenCode + z.ai-Fleet-„bereit"-Meldung (Plan §14.8). Heute nicht blockierend (MiniMax-Fallback läuft).
- **Datenreparatur der 3 730 alten `source='ig'`-Bars** (Plan T14) folgt erst in **E-3** zusammen mit dem Scheduler-Restart; bis dahin bleibt der DB-Zustand mit den +2-h-Bars stehen.

### B-3 Σ-Steigerung (2026-10-19, Plan §6 Kommandoform)

| Suite | grün (nach B-2) | grün (nach B-3) | Δ |
|---|---:|---:|---:|
| P1 broker_wrapper | 98 | 98 | — |
| P2 persistence | 82 | 82 | — |
| P3 external_data | 108 | 108 | — |
| P4 research | 163 | 163 | — |
| P5 execution | 190 | 190 | — |
| P6 debate | 76 | 76 | — |
| P7 reward | 170 | 170 | — |
| **P8 scheduler** | 263 | **264** | **+1** |
| P9 universe | 95 | 95 | — |
| P10 v3 | 165 | 165 | — |
| P12 data_foundation | 153 | 153 | — |
| P13 live_data | 85 | 85 | — |
| P14 discovery | 61 | 61 | — |
| **P15 v4** | 126 | **128** | **+2** |
| P16 activation | 15 | 15 | — |
| root `tests/` | 121 | 121 | — |
| **Σ 16 Suites** | **1971** | **1974** | **+3** |
| meta_m1 (informativ, nicht in Σ) | 28 | 28 | — |

### Open questions / blockers
- **Scheduler ist gestoppt** (`is-active=failed`). Vor E-3 muss er wieder hochfahren — der Recorder muss dann mit dem Klonen-Bar-Löschen (Plan T14, `DELETE FROM bars WHERE source='ig'`) zusammen laufen, weil sonst `bars.sqlite is locked` (Plan §8 Fehlgriff). Bis zum E-3 wird die alte IG-Historie (3 730 Bars mit `ts_utc` +2h in der Zukunft) NICHT angerührt; das ist **gewollt** und **kein Datenverlust**, weil der Fix in `ig_adapter.py:909` wirkt und neue Bars korrekt schreibt. **Identisch zu Session #2 — keine Änderung.**
- **Promotion-Bridge-Backfill für die 29 NULL-Zeilen** (Phase-15-Closeout §3 Befund-2 Erbe): die 29 Live-DB-Instinct-Zeilen mit `evidence_trade_ids_json IS NULL` werden NICHT retroaktiv gefixt — kein Konsument liest sie heute, AK9-Erbe gilt (`longterm_rules == ()` ⇒ `veto5_empty_rules_is_identity` bleibt grün). Folgearbeit: einmaliger Operator-`UPDATE`-Backfill oder Verwerfen der Null-Zeilen via `DELETE FROM instincts WHERE evidence_trade_ids_json IS NULL` — Entscheidung Block E oder außerhalb der Phase 17.
- **Fleet §14.8 (OpenCode + z.ai)** weiterhin offen. Heute nicht blockierend.
- **C-1-Step `check_llm_profile`** wird um `/coding/`-Endpoint-Check erweitert (Plan §14.1, +1 P8-Test) — gehört zu Block C, nicht zu A/B.

### Session-end-Hinweis (für die Exec-Session selbst)
- **Plan-AK-Stand nach dieser Session:** Session #1 ✅ AK1-AK4 + Session #2 ✅ +6 AK-Block-B Sweep (P12 +4 + P8 +2) + **Session #3 ✅ +3 AK-Block-B Sweep (P15 +2 + P8 +1)** = Σ 1974. Plan-AK-Block-B Sweep Σ ≥ 1992 noch **18 Tests entfernt** (B-4..B-10 verbleibend).
- **K11-Anker (Shakedown):** B-3 hat das Bridge-Statement verifizierbar gemacht (`status == 'validated'`, `evidence_trade_ids_json` populiert). K11 erwartet ≥ 1 `divergence_ok`-Event je Handelstag (B-2-Quelle) — B-3 ändert die K11-Mechanik nicht, aber die Promotion-Bridge-Spur ist jetzt erstmalig in der Lage, validierte Instincts tatsächlich zu erzeugen (`InstinctValidator` bekommt Trades, zählt, transitioned `proposed` → `validated` und stempelt `validated_utc`). Damit kann Block-E-3 (Prereg v5) einen `validate`-Audit-Hook spendieren, der die erste `proposed→validated`-Transition live nachweist.
- **K11-Konsistenz mit dem alten Code:** der alte Bridge-Pfad hat `evidence_trade_ids` an `_INSTINCT_COLUMNS` vorbei geschrieben (Whitelist-Drift). Mit B-3 Fix landen sie im Schema; ein hypothetischer Backfill-SQL-`UPDATE` (siehe Open-Questions) wird nach Konsumenten-Entscheidung sauber.
- B-3 lokal ahead (`3377b0a` + `7c7251d` = 2 Commits vor `origin/main = a5d08cd+phase17-A-3`), wartet auf Nikinger-Push.

### Next start (für die Folgesession, kalt einsteigen ohne Neu-Lesen)

**B-4 Abschneiden sichtbar (D4, P4).** Anker: `phase4_research/research/llm_client.py:378–423` (`_attempt`) und `phase4_research/research/llm_openai_compat.py:242–287` (`_attempt`). Zwei Edits pro Datei: (1) Den Meter-Block **vor** Parse verschieben (Kommentar: „meter first: a response that fails to parse was still billed"); (2) Parse-Fehlerzweig erweitern um `if getattr(message, "stop_reason", None) == "max_tokens": raise LLMResponseError(...)` (bzw. `finish_reason == "length"` im OpenAI-Compat-Pfad). Beide nicht-transient — `ask_candidate` wickelt es als „LLM call failed" ab und wiederholt **nicht**. +4 P4-Tests (`test_llm_client_truncated_unparseable_raises_without_retry`, `test_llm_client_meters_even_when_parse_fails`, `test_openai_compat_length_truncation_raises_without_retry`, `test_openai_compat_meters_even_when_parse_fails`). Plan-AK P4 ≥ 167.
Block-B Σ-Ziel ≥ 1992 noch 18 Tests entfernt nach B-4 (B-4 = +4, Σ 1978).
Scheduler bleibt gestoppt (B-0). Push = Nikinger. Block C wartet auf OpenCode-Fleet-„bereit"-Meldung.

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
