# SESSIONS_ARCHIVE.md — Phase 17 (Prüfstand)

Newest-first. Rotation rule (root `CLAUDE.md`, mandatory since 2026-07-06): the phase head
carries at most one `## Session stopped` block; archives have no size cap. See
[`../CLAUDE.md`](../CLAUDE.md) "How to work in this repo" — Rotation rule, and
[`../docs/DOC_LAYERS_CONVENTION.md`](../docs/DOC_LAYERS_CONVENTION.md) for the L0/L1/L2/L3 model.

---

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
