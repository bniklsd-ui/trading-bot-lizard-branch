# SESSIONS_ARCHIVE.md — Phase 17 (Prüfstand)

Newest-first. Rotation rule (root `CLAUDE.md`, mandatory since 2026-07-06): the phase head
carries at most one `## Session stopped` block; archives have no size cap. See
[`../CLAUDE.md`](../CLAUDE.md) "How to work in this repo" — Rotation rule, and
[`../docs/DOC_LAYERS_CONVENTION.md`](../docs/DOC_LAYERS_CONVENTION.md) for the L0/L1/L2/L3 model.

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
