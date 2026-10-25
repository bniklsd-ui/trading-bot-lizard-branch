---
status: live
purpose: PHASE-HEAD, Phase 17 (Prüfstand) — 🔄 eröffnet 2026-10-17 (Plan-Session, Opus 5.5). Keine neuen Features. Tiefe Härtung des Bestehenden — vier Phase-16-PASS-Blocker + drei neu gemessene stille Totalausfälle zu, LLM pro Rolle austauschbar (Research zuerst auf GLM über die z.ai-API mit Pay-per-use, Plan §14), Report + Vorregistrierung v5 als Fundament für die ausgiebigen Tests. Executor: offener Test GLM in OpenCode (§14).
read-when: jede Phase-17-Exec-Session — zuerst diesen Kopf, dann den `## Session stopped`-Block, dann den Plan
detail: L1
up: ../CLAUDE.md
down:
  - ../docs/concepts/phase17_testbed_plan.md               # 📕 der Plan (T1–T24, D1–D13, Blöcke A–E, AK1–AK21, §8 Fehlgriffe, §9 Verify)
  - ./provider_plasticity/                                  # 🔄 Working-Notes Provider-Plastizität (2026-10-19, 4 Notizen: 01 Decision T25–T28 · 02 Current-State · 03 Opus-Brief · 04 Open Questions Q1–Q8)
  - ../phase16_activation/PHASE16_CLOSEOUT_HANDOVER.md     # 📕 Vorgänger-Handover (§4 PASS-Blocker, §5 E1–E8)
  - ../phase16_activation/scripts/autonomy_report.py       # Report-Skript, Block E erweitert es in place (--prereg v5)
  - ./SESSIONS_ARCHIVE.md                                  # rotierte Session-Blöcke (L3, newest-first)
updated: 2026-10-25 (Exec-Session #7 ENDE — Scheduler-Hold: systemd-Autostart aus + getrackter Repo-Guard `data/state/SCHEDULER_HELD`, +12 root-Tests, Σ **2000**) | 2026-10-19 (Exec-Session #6 ENDE — B-6 Breaker Worst-Case, 1 Commit in P8, Σ 1985 + 3 P8-Tests = **1988** grün; Scheduler gestoppt + 3 Units laufen weiter; Nikinger-Freigabe zur Beendigung) | 2026-10-19 (Exec-Session #5 ENDE — B-5 Monitor-Re-Adoption, 1 Commit in P5+P8, Σ 1978 + 5 P5 + 2 P8 = **1985** grün; Scheduler gestoppt + 3 Units laufen weiter; Nikinger-Freigabe zur Beendigung) | 2026-10-19 (Plan-Session §15 Provider-Plastizität — Forward-Agenda C2 → Plan §15, Σ-Ziele C/D/E-1 +9, Σ 1978 re-gemessen) | 2026-10-19 (Exec-Session #4 ANSCHLUSS — `provider_plasticity/` Working-Notes-Set angelegt (kein Plan, Input für Opus-Miniplan-Session; 5 INDEX-Einträge); Nikinger-Entscheidungen Q1–Q8 ausstehend) | 2026-10-19 (Exec-Session #4 ENDE — B-4 Abschneiden sichtbar, 1 Commit in P4, Σ 1974 + 4 P4-Tests = **1978** grün; Scheduler gestoppt + 3 Units laufen weiter; Nikinger-Freigabe zur Beendigung) | 2026-10-19 (Exec-Session #3 ENDE — B-3 Promotion-Bridge Nahtfehler, 2 Commits in P15+P8, Σ 1971 + 2 P15 + 1 P8 = **1974** grün; Scheduler gestoppt + 3 Units laufen weiter; Nikinger-Freigabe zur Beendigung) | 2026-10-19 (Exec-Session #2 ENDE — B-2 Divergenz-Sampler Reparatur, Σ 1965 + 4 P12-Tests + 2 P8-Tests = **1971** grün) | 2026-10-19 (Exec-Session #1 ENDE — A-0+A-1+A-2 + A-3 + B-0 + B-1, Σ 1965) | 2026-10-18 (Plan-§14-Nachtrag) | 2026-10-17 (Plan-Session, Opus 5.5)
---

# CLAUDE.md — Phase 17: Prüfstand (`phase17_testbed/`)

> **Quelle der Wahrheit ist der Code, dann der Plan, dann dieser Kopf.**
> Plan: [`../docs/concepts/phase17_testbed_plan.md`](../docs/concepts/phase17_testbed_plan.md).

## Mission

Der Bot wird zum **Prüfstand**. Für die anschließenden ausgiebigen Tests muss gelten:
- jeder vorhandene Arm liefert nachweisbar, was er liefern soll;
- jeder bekannte Mess- und Geldpfad-Defekt ist zu;
- das LLM ist pro Rolle austauschbar.

Nikinger 2026-10-17: *„keine besondere Feature-Session — bildet eher das Fundament für ausgiebige
Tests. LLM-Austausch wäre aber trotzdem sehr wichtig"* · *„kein zusätzlicher Umfang, eher extrem
tiefe Optimierung von dem, was schon da ist."*

**Abnahme:** Shakedown-Vorregistrierung → 2-Tage-Shakedown PASS → Prereg v5 committet (Plan AK19 + AK20 + AK21).
Der 10-Tage-Lauf selbst ist die Testreihe **nach** Phase 17.

## Gelockt (Kurzform — volle Begründung Plan §1, **Vorrang hat Plan §14** vom 2026-10-18)

| ID | Kern |
|---|---|
| T4/T5 (§14) | **GLM über die allgemeine z.ai-API, Pay-per-use** (`https://api.z.ai/api/paas/v4`, **nie** `/api/coding/` — prüft `check_llm_profile` beim Start). Das Modell wählt der Nikinger nach dem Familien-Smoke C-7 (`glm-5.3` / `glm-5.3-flash` / `glm-5.2`). **Flip 1** = `research_glm`, **Flip 2** = `all_glm`, nur auf Nikinger-Go nach dem Shakedown |
| T6 (§14) | Bot-Key im eigenen Namespace `trading-bot-zai-bot` / `api_key` (Keyring; nie der Coding-Plan-Key) |
| T7 (§14) | Das GLM-Bot-Modell ist budgetfrei (`budget_exempt_models`; die Kadenz begrenzt es auf ≤ 102 Research-Calls/Tag). Es hat eine **echte Preiszeile**, also wird € gemessen. Anthropic bleibt bei 300 k; K6-Einheit entscheidet der Nikinger nach dem Shakedown |
| T8 | Monitor-Re-Adoption nach Restart, nur im WINDOW, inklusive Sofort-Close bei überschrittener Haltezeit |
| T9 | Breaker zählt heutige OPEN-Zeilen mit `−initial_risk`; NULL → fail-closed |
| T13 | Code in P1, P4, P5, P8, P10, P12, P14, P15, P16; P2 nur Tests; **kein** Code in P6/P7/P13 |
| T14/T15 | IG-Zeitstempel-Fix (+ Löschen der 3 730 falschen `ig`-Bars), Divergenz-Sampler-Reparatur |
| T22 (§14) | Exec = **offener Test in OpenCode + z.ai Coding Plan**, Start `zai-coding-plan/glm-5.3-flash`, Familie `glm-5.2`/`glm-5.3` zugelassen. Claude Code bleibt Anthropic-only und macht das **Pflicht-Review-Gate vor E-3**. Rückfall auf MiniMax (bis 2026-11-15) oder Claude, wenn ein Step zweimal scheitert oder ein Test nach 3 Versuchen rot bleibt. Scheduler gestoppt von B-0 bis E-3 |

## Bot-Ritual (vor jedem bot-berührenden Edit)

```bash
systemctl --user stop tradingbot-scheduler.service       # bis B-9 deployt ist: ≤ 90 s, ggf. SIGKILL (Plan D13, erwartet)
ps aux | grep "scheduler.run" | grep -v grep             # Gegenprobe: leer
```

- Recorder, Discovery und WebUI halten keine IG-Session und laufen weiter (Plan T22).
- Den Neustart macht nur **E-3**, die Deploy-Sequenz im Plan.
- **Scheduler-HOLD (B-0, seit 2026-10-25, Exec-Session #7):** der Scheduler ist über den
  Stopp hinaus **autostart-fest abgesichert** — systemd `disabled` + Marker
  `data/state/SCHEDULER_HELD` (operator-sticky, Muster `KILL`/`DISCOVERY_ARMED`). Beide
  Repo-Türen respektieren den Marker: `scripts/install_units.sh` enabled die Scheduler-Unit
  bei Hold **nicht**, `scripts/restart-services.sh` startet sie bei Hold **nicht**.
  Zustandsprüfung: `bash scripts/install_units.sh --check` (exit 0 = alles wie erwartet;
  Drift → exit 1). Nicht von Hand `enable`/`start` ohne Freigabe.
  Freigabe (E-3): `bash scripts/install_units.sh --release-hold` → `bash scripts/install_units.sh`
  → `systemctl --user start tradingbot-scheduler.service`.

## Test-Sweep (jede Suite getrennt; Σ = 16 Suites, meta_m1 nicht in Σ)

```bash
cd /home/trading-bot/trading-bot && PY=/home/trading-bot/trading-bot/phase1_broker_wrapper/.venv/bin/python
for d in phase1_broker_wrapper phase2_persistence phase3_external_data phase4_research phase5_execution \
         phase6_debate phase7_reward phase8_scheduler phase9_universe phase10_v3 phase12_data_foundation \
         phase13_live_data phase14_discovery phase15_v4 phase16_activation; do
  echo "$d | $(cd $d && $PY -m pytest tests/ -q -p no:cacheprovider 2>&1 | tail -1)"; done
echo "root | $($PY -m pytest tests/ -q -p no:cacheprovider 2>&1 | tail -1)"
```

| Stand | Σ | Quelle |
|---|---:|---|
| Baseline (Plan-Session, 2026-10-17) | **1964** (+ meta 28) | Plan §2.1 |
| Nach Exec-Session #1 (B-1, 2026-10-19) | **1965** | +1 P1-Test |
| Nach Exec-Session #2 (B-2, 2026-10-19) | **1971** | +4 P12 + 2 P8 |
| Nach Exec-Session #3 (B-3, 2026-10-19) | **1974** | +2 P15 + 1 P8 |
| Nach Exec-Session #4 (B-4, 2026-10-19) | **1978** | +4 P4 |
| Nach Exec-Session #5 (B-5, 2026-10-19) | **1985** | +5 P5 + 2 P8 |
| Nach Exec-Session #6 (B-6, 2026-10-19) | **1988** | +3 P8 |
| Ziel nach Block B / C / D / E-1 | ≥ 1992 / ≥ 2025 / ≥ 2028 / ≥ 2035 | Plan §6 + §14 (+1) + §15 (+9, P4 +5 · P8 +4) |
| Re-Messung Exec-Session #6 (2026-10-19) | **1988** | unverändert, 16/16 grün |
| Nach Exec-Session #7 (Scheduler-Hold, 2026-10-25) | **2000** | +12 root-Tests (root 121 → 133), 16/16 grün |

## Phase-17-Status

| Block | Status |
|---|---|
| A Haushalt | ✅ (Session #1) |
| B-0 Scheduler-Stopp + IG-Probe | ✅ (Session #1) |
| B-1 IG-UTC-first | ✅ (Session #1) |
| B-2 Divergenz-Sampler | ✅ (Session #2) |
| B-3 Promotion-Bridge (3 Nahtfehler) | ✅ (Session #3) |
| B-4 Abschneiden sichtbar (D4) | ✅ (Session #4) |
| B-5 Monitor-Re-Adoption (D5, T8) | ✅ (Session #5) |
| B-6 Breaker Worst-Case (D6, T9) | ✅ (Session #6) |
| B-7 … B-10 | ⏳ |
| Scheduler-Hold (B-0 → E-3) | ✅ aktiv (2026-10-25): systemd `disabled` + `data/state/SCHEDULER_HELD`, beide Repo-Türen (Installer, Restart-Helper) respektieren den Marker — **Freigabe erst in E-3** (`bash scripts/install_units.sh --release-hold`) |
| C LLM-Austausch | ⏳ — **zuerst Plan §14, dann §15** (Provider-Plastizität, in place) |
| D Token-Budget | ⏳ |
| E Test-Fundament | ⏳ |

## Forward-Agenda (zwischen den Blöcken B-5..B-10 und C)

| # | Thema | Status | Link |
|---|---|---|---|
| **C2 — Provider-Plastizität** | Endpoint-Abstraktion für alle „gängigen" Provider (Anthropic + OpenAI + DeepSeek + Qwen + GLM + …). Nikinger-Entscheidung 2026-10-19 („soll mit sämtlichen gängigen Endpunkten funktionieren"). | ✅ **Plan §15** (2026-10-19, Plan-Session Opus 5.5) — ändert C-1/C-3/C-4/C-6/C-7 in place; Q1–Q8 entschieden | [`../docs/concepts/phase17_testbed_plan.md` §15](../docs/concepts/phase17_testbed_plan.md) |

> **Update 2026-10-19 (Plan-Session):** C2 ist jetzt **Teil von Block C** (Plan §15, Nikinger Q2) — kein eigener Block, keine Phase 18. Σ-Ziel Block C ≥ **2025** (statt 2016). Der Absatz unten ist historisch.

Diese Forward-Agenda ist **kein Block** der Phase 17 — sie ist „Material für eine Opus-Miniplan-Session nach den Blöcken B-5..B-10", wie es der Nikinger mit seiner Entscheidung intendiert hat. Eine spätere Session `Exec-Session #5+` wird je nach Nikingers Q2-Antwort entweder einen Plan-§-Anker (neuer Block C2 in Phase 17) oder einen eigenständigen Phasenkopf Phase 18 schreiben.

## Executor-Evaluation (Plan §14.2 — je Exec-Session eine Zeile)

| Session | Datum | Modell (`zai-coding-plan/…`) | Steps | Kontingent vorher → nachher (z.ai-Dashboard) | Tests | Rückfall | Notiz |
|---|---|---|---|---|---|---|---|
| #6 (B-6) | 2026-10-19 | MiniMax-M3-Fallback (Plan §14.2) — kein z.ai-Modell heute in Verwendung | B-6 Breaker Worst-Case (D6, T9, P8) | n/a | Σ 1985 → **1988** (+3, P8 +3 ✓ Plan-AK exakt) | — | Plan-Anker Z. 1009–1016 (Closure `realized_pnl_today`) ist zwischen Plan-Session 2026-10-17 und Session #6 auf Z. 1066–1073 gewandert (~$+57$ Zeilen durch Folge-Commits in P15/P8); **kleiner Drift**, semantisch unverändert. Neuer Modul-Helper `_realized_pnl_today` direkt nach `_sampler_due` einsortiert (B-Block-Helper-Section). Test-File `tests/test_wiring_breaker.py` neu — DB-Path `:memory:` (sqlite3 in-memory, ein Connection über Test-Lifetime, keine `tmp_path`-Notwendigkeit) |
| #5 (B-5) | 2026-10-19 | MiniMax-M3-Fallback (Plan §14.2) — kein z.ai-Modell heute in Verwendung | B-5 Monitor-Re-Adoption (D5, T8, P5 + P8) | n/a | Σ 1978 → **1985** (+7, P5 +5 + P8 +2 ✓ Plan-AK exakt) | — | B-5 ist die letzte Single-Commit-Block: 1 Commit (154f460) in P5+P8. Bit-Identität via `getattr(self._executor, "resume_open_position", None)` — alle Bestands-Fakes unverändert grün |
| — | — | — | — | — | — | — | Der 5.2-Quirk: bei Flash-ähnlichem Kontingent-Verbrauch einen vergleichbaren Step mit `glm-5.2` fahren |

**Review-Gate vor E-3 (AK22):** ⏳ (Claude-Code-Session, Anthropic; Schwerpunkte B-5, B-6, C-4, B-3, B-2)

> **Integration des Executors = eurofyx-fleet, getrennt vom Plan (Plan §14.8, Nikinger 2026-10-18).** Die Fleet richtet ein: OpenCode-Provider `zai-coding-plan` (Auth), Modell, Neustart von `opencode.service`, MiniMax-Rückweg. Diese Exec-Session fasst `~/.config/opencode/`, `auth.json` und `opencode.service` **nicht** an. A-0 startet erst, wenn die Fleet „OpenCode + z.ai bereit" meldet.

---

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


---

> **Ältere Session-Blöcke** (verbatim ausgelagert, newest-first): [SESSIONS_ARCHIVE.md](./SESSIONS_ARCHIVE.md) — Rotation per Doc-Layers-Konvention ([docs/DOC_LAYERS_CONVENTION.md](../docs/DOC_LAYERS_CONVENTION.md)).
