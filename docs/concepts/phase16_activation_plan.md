---
status: snapshot
purpose: Execution-ready Plan für Phase 16 (Freischaltung — alle Löcher zu, alle gebauten Arme scharf, 2-Wochen-Autonomie-Test vorregistriert), geschrieben 2026-09-05 in der Plan-Session gegen den laufenden Code + Live-DB; direkt an Sonnet 5 übergebbar
read-when: vor jedem Phase-16-Schritt; danach nur noch als Snapshot beim Auditieren
detail: L3
up: ../../CLAUDE.md
down:
  - ../../phase16_activation/CLAUDE.md                        # Phasenkopf — trägt den Plan-Session-Block; Step A-0 liest ihn
  - ../../phase15_v4/PHASE15_CLOSEOUT_HANDOVER.md             # §7 E1–E3 (Migration 009, Promotion-Bridge, Ledger-Restore) — hier geschlossen
  - ../../phase7_reward/PHASE12_RECONCILIATION_TIMING_PLAN.md # A6 Live-Verify — hängt an Migration 008 (L3)
  - ../../phase5_execution/CLAUDE.md                          # B3-Block (Margin-Headroom) — Block D3 baut ihn
  - ../../meta_m1_harness/META_M1_PREREGISTRATION.md          # Muster für die Vorregistrierung des 2-Wochen-Tests (Block E)
updated: 2026-09-05
---

# Phase 16 — Freischaltung: Execution-ready Plan (2026-09-05)

> **Adressat:** die ausführende Session (Sonnet 5 / `claude-minimax`). Nichts hier muss neu
> hergeleitet werden. Jede Zahl in §2/§3 ist in der Plan-Session selbst gegen Code oder
> Live-DB (mode=ro) gemessen, mit Datum und Zeilennummer. Was **nicht** geprüft werden konnte,
> steht vollständig in **§9** — was dort nicht steht, gilt als geprüft. Zeilennummern sind
> Stand 2026-09-05 (HEAD `2f9eb82`); **der Verbatim-String ist der Anker, die Zahl die Abkürzung.**

---

## §0 BLUF

**Mission in einem Satz:** jedes gebaute Feature läuft, jeder bekannte Bruch ist zu, und ein
vorregistrierter 2-Wochen-Lauf beweist Autonomie ohne Hand.

**Warum jetzt:** der Bot ist seit 2026-08-31 faktisch tot — 100 % Research-Abstain (77/Tag),
0 Kandidaten, 0 Trades — und drei weitere Löcher machen jeden Restart schlechter als den
vorherigen (Flags verloren, Migrations nie angewendet, Token-Budget täglich um 15:48 leer).
Keines davon ist Strategie; alle sind Infrastruktur. Phase 16 stopft sie **und** schaltet
im selben Zug alle vier bewusst-AUS-gebauten Arme scharf (Nikinger-Philosophiewechsel
2026-09-05: *„wenn etwas AUS sein soll, braucht es ein extra Flag"*).

**Fünf Blöcke, in dieser Reihenfolge:**

| Block | Inhalt | Gate |
|---|---|---|
| **A** | Haushalt: Step-0-Ritual, Σ-Baseline **1843**, Code↔.md-Sweep (4 falsche Behauptungen), WebUI-Log, Push + Ledger-Restore (Operator) | keins |
| **B** | Substrat: Schema-Floor im Preflight (L3) + Operator-Apply mit Backup; Wochenend-Filter (L5) | nach A |
| **C** | Research-Loop: Historien-Fenster (L1), Budget 300 k (L2), Breaker-Semantik (L9, braucht P3-Freigabe) | nach B |
| **D** | Freischaltung: Defaults flippen (L4), Promotion-Bridge + Prädikat-Compiler (L6), Margin-Headroom (L7) | nach C |
| **E** | 2-Wochen-Autonomie-Test: Vorregistrierung, `autonomy_report.py`, Runbook, Closeout | nach D, Bot-Restart |

**Ehrliche Grenzen:** Phase 16 bewertet keine Edge (alle 8 Trades BUY/DAX, 2 W : 6 L bleibt ein
Watch-Item, kein Fix-Target). Profit ist **kein** PASS-Kriterium des Tests.

---

## §1 Gelockte Entscheidungen (Nikinger 2026-09-05, Runde 1 — je Zeile mit Begründung)

| ID | Entscheidung | Begründung (warum niemand sie gutgemeint aufmacht) |
|---|---|---|
| **P1** | Phase heißt „Freischaltung", Verzeichnis `phase16_activation/`, Commit-Scope `phase16:` | Namenskontinuität (phase13_live_data / phase14_discovery / phase15_v4); „Aktivierung" beschreibt den Inhalt, nicht eine Technik |
| **P2** | L1-Fix = **Zeitfenster 14 Kalendertage UND max 8 Trades**, als P4-seitiger Post-Filter (kein P2-Query-Touch) **plus ein Prompt-Satz** | Das Fenster ist der deterministische Fix (Historie altert von selbst); der Satz verhindert, dass zwei Verluste in 14 Tagen dasselbe auslösen. Post-Filter statt SQL, weil `get_recent_trades_for_prompt` drei Filter-Signale schon in der Query hat und ein viertes die P2-Schnittstelle unnötig breiter macht |
| **P3** | L2-Fix = `daily_token_budget` **200 000 → 300 000** (Config-Default + CLI-Default). `cache_system=True` für den Research-Client wird **nicht** gebaut | Das Budget hebt den täglichen 15:48-Deckel sofort. Caching kann das Kriterium **strukturell nicht** bewegen — zwei verifizierte Fakten: (a) `budget.py:70-75` summiert `input + output + cache_creation + cache_read` gleichgewichtet (Cache-Reads zählen voll), (b) Sonnet 4.6 cached erst ab **1024 Tokens** Präfix, das System-Prompt hat ~250 → Marker inert. Nikinger #3 („können wir testen") ist damit ein Test mit bekanntem Ergebnis → nicht gebaut, im Phasenkopf begründet (Nikinger kann das in Runde 2 überstimmen) |
| **P4** | L4-Fix = **Defaults im Code flippen**: `enable_shadow_schedule`, `enable_divergence_sampler`, `enable_bar_stream`, `enable_paper_debate` **= True** — **in `SchedulerConfig` UND in `run.py` (`--no-*`-Schalter + `config_from_args`) im Gleichschritt**; die `--enable-*`-Flags werden **entfernt**. Dazu gehört der Bar-Stream-Token-Fix (D1.2), sonst ist der Arm nach der ersten IG-Token-Rotation tot | Nur ein Code-Default ist restart-fest (vierter Wiederholungsfall des Memory-Musters „Flag prüfen, bevor ‚ist live' behauptet wird"). `config_from_args` (`run.py:159-169`) setzt **jedes** Feld explizit aus argparse — ein Dataclass-Flip allein wäre ein No-Op (Opus-Review §13). Args-Datei = zweite Wahrheit. Alte `--enable-*` wären No-Op-Leichen (Nikinger #6) |
| **P5** | Dieselbe Philosophie gilt für `InstinctConfig.enable_instinct_promotion` → **Default True**; die echten Gatter bleiben `instinct_n_min = 50` **und** der deterministische Validator | **Supersedet Phase-15-P10** (Nikinger #4 + #6). Sicher by construction: VETO 5 kann nur vetoen, nie öffnen (Hard Rule 3 bleibt erfüllt — Validator ist Code). Heute n=8 → Gatter bleibt zu |
| **P6** | **Ausnahme:** `RescueConfig.enable_gap_rescue` bleibt **False** (Operator-Tool, Doppel-Sperre) | Pfad-C-Entscheidung Phase 13 L18 / Phase 14 D19 (IG-Default-AUS, budgetgebunden) ist eine **Kosten**-Entscheidung, kein Feature-Flag; GapRescue ist kein Daemon-Arm (D16 out-of-scope seit P15). Bleibt gelockt, bis der Nikinger sie eigens öffnet |
| **P7** | L5-Fix = Wochenend-Instrumente werden in **Discovery** gefiltert (`weekend_market`) **und** in `run_promotion_cycle` Step 3 aktiv **demotet** (`quarantined`) — Prädikat: IG-Name enthält `wochenend`/`weekend` **oder** Epic enthält `.SUN` | Handelsfenster ist Mo–Fr 09:00–17:30 (`ExecutionConfig`): Wochenend-Märkte sind dort nie handelbar, belegen aber 3 von 8 Slots und 30–50 % der IG-Research-Punkte. Demotion im Code statt Operator-SQL, damit es self-healing ist (keine Leiche in einem Runbook) |
| **P8** | L3-Fix = **kein** `run_migrations()` im Daemon. Stattdessen: `preflight_fn` bekommt einen **Schema-Floor** (`_schema_version >= 9`, fail-closed mit Handlungsanweisung) **und** einmaliger Operator-Apply mit Backup bei gestoppten Diensten | *(Geändert nach Opus-Review §13, 2026-09-05.)* `wiring.py:1070-1071` trägt die gelockte Entscheidung *„Verify rather than silently migrate (a safety-critical daemon does not mutate schema)"*; die Live-DB läuft mit `journal_mode=delete` und `sqlite3.connect` ohne `busy_timeout` — `executescript` bräuchte ein EXCLUSIVE-Lock gegen den laufenden Discovery-Daemon → `database is locked` → Daemon-Exit. Der Floor macht den v7-Fehlermodus **laut** (Daemon startet nicht) statt still |
| **P9** | L6 = Bridge **jetzt** bauen: Extractor-Hook am Close-Seam von `RewardSink` → Validator → DB; Promotion beim Start und nach jedem Close; Prädikat-Compiler nur für Domain `entry` mit **Mini-Grammatik** `avoid <BUY\|SELL>[ on <EPIC>]`; alles andere → kein Rule, WARNING | Ohne Bridge sammelt der 2-Wochen-Test keine Instincts. Freitext-Trigger sind nicht deterministisch kompilierbar; die Grammatik macht den AI→VETO-Übergang code-prüfbar (Hard Rule 3). Unbekannt = inert + laut, nie geraten |
| **P10** | L7 = B3 rein, als **letzter** Code-Block D3, mit Operator-Live-Probe **vor** dem Code; fehlt der IG-Margin-Faktor → Rückfall auf den heutigen Leverage-Cap (nicht fail-closed) | B3 rejects (22,1 vs 22,0) sind ein reales Loch; Rückfall statt fail-closed, weil ein fehlender Faktor sonst den ganzen Test still auf 0 Trades stellt |
| **P11** | PASS-Kriterien des 2-Wochen-Tests werden **vor** dem Start committet (Block E1) und danach nicht geändert; Profit ist kein Kriterium. Jedes Kriterium hat eine **append-only** Messquelle (§6 E2) | M1-Vorregistrierungs-Disziplin; ein nach dem Lauf geschriebenes Kriterium beweist nichts. `scheduler_state.json` / `recorder_state.json` / `discovery_state.json` werden in-place überschrieben und taugen nicht als Beleg (Opus-Review §13) |
| **P17** | **Erlaubte Operator-Ereignisse im Test** (vorregistriert, gezählt, nie still): (a) Backoff-KILL (`runner.py:355-361`, 3 Zyklus-Exceptions in Folge → `data/state/KILL`) darf **einmal** mit geloggtem Grund gelöscht + neu gestartet werden, der Root-Cause wird als Befund geführt; ein zweites Mal = FAIL Kriterium 1. (b) Reboot/Keyring-Relogin = Restart-Ritual, zählt als Intervention (FAIL Kriterium 1), Lauf geht weiter. `max_consecutive_failures` bleibt **3** | Der einzige automatische KILL-Schreiber ist der Backoff; `restart-services.sh` fasst KILL nie an (Z. 22). Kein systemd-Unit, kein Cron, kein Auto-Reboot (`Automatic-Reboot` auskommentiert = false; letzte Reboots 08-25/08-30 waren manuelle VM-Wartung). Der Keyring braucht einen Desktop-Login → ein Reboot ist ohne Hand nicht überlebbar; das wird ehrlich als Grenze vorregistriert, nicht wegautomatisiert (Supervision ist Phase-17-Material) |
| **P12** | Cross-Phase-Freigabe (Nikinger #9, „mit Hinweis zur wirklich ausgiebigen Situation"): **P1, P2, P4, P5, P7, P8, P9, P15** — jeder Touch nur, wo ein Step ihn braucht; **P3 (fetcher.py, L9) ist NICHT enthalten** → Step C5 wartet auf eigene Freigabe | Phase 8 war in P15 gesperrt, Phase 16 braucht sie zwingend (Defaults, Wiring, Migrations-Aufruf) |
| **P13** | Operator-Aktionen sind freigegeben (Nikinger #10): Push, Ledger-Restore, Migrations-Apply, Demotion-Verify, Live-Probe — die Exec-Session bereitet Befehl + Kosten vor, führt **nicht** selbst aus | Live-/Netz-/kostenpflichtige Läufe bleiben Nikinger-Job (CLAUDE.md Working style) |
| **P14** | Bot-berührende Edits: erst `bash scripts/restart-services.sh stop`, `ps aux \| grep scheduler.run` als Gegenprobe; Neustart erst nach dem letzten Code-Commit eines Blocks | Parallel-Login-Falle; Python cached Module (`sys.modules`) — Code-Edits wirken erst nach Restart (P14-D §10) |
| **P15** | Neue `.md`/`.svg` ⇒ `docs/INDEX.md`-Zeile im selben Commit; Phasenkopf trägt genau einen `## Session stopped`-Block | Doc-Layers-Konvention + Hook `check_doc_rotation.py --strict` |
| **P16** | Advisor-Ersatz: Opus-Plan-Agent-Review vor dem Festlegen (gelaufen, §13), Sonnet-Cold-Read vor „fertig" | `/advisor` ist in Claude Code nicht verfügbar; Agent-Freigabe Nikinger 2026-09-05 |

---

## §2 Selbst gemessene Fakten (2026-09-05, Plan-Session)

### 2.1 Σ-Baseline — **1843 grün** (Kommandoform verifiziert)

```bash
cd <phaseN> && ../phase1_broker_wrapper/.venv/bin/python -m pytest tests/ -q -p no:cacheprovider
# root: phase1_broker_wrapper/.venv/bin/python -m pytest tests/ -q -p no:cacheprovider
```

| Phase | grün | | Phase | grün |
|---|---:|---|---|---:|
| phase1_broker_wrapper | 95 | | phase9_universe | 87 |
| phase2_persistence | 78 | | phase10_v3 | 165 |
| phase3_external_data | 104 | | phase12_data_foundation | 145 |
| phase4_research | 155 | | phase13_live_data | 82 |
| phase5_execution | 185 | | phase14_discovery | 61 |
| phase6_debate | 76 | | phase15_v4 | 91 |
| phase7_reward | 166 | | root `tests/` | 105 |
| phase8_scheduler | 248 (1 Warning, pre-existing) | | **Σ** | **1843** |

Jede Phase **getrennt** laufen lassen (geteilter `tests.conftest`-Name kollidiert).

### 2.2 Git

HEAD `2f9eb82`, **7 Commits lokal ahead** of `origin/main` (Sessions #10–#13). Working tree
clean bis auf `?? data/` (untracked, die Einzeldateien sind per `.gitignore` gedeckt — `git
check-ignore` bestätigt für `*.sqlite` und `*.log`).

### 2.3 Laufende Prozesse (`ps`, 2026-09-05)

| PID | Dienst | seit | argv |
|---|---|---|---|
| 124485 | Recorder (`data_foundation.run`) | 09-03 12:00 | — |
| 124512 | Discovery (`source_registry.run`) | 09-03 12:00 | armed (DISCOVERY_ARMED seit 08-26) |
| **124569** | Scheduler | 09-03 12:00 | **`python -m scheduler.run` — keine Flags** (`/proc/124569/cmdline`) |
| 124611 | WebUI (uvicorn) | 09-03 12:00 | — |
| 124576/124577 | `[python] <defunct>` | — | 2 Zombies, kein Schaden (P15 §9.5) |

### 2.4 Live-DB `data/trading_bot.sqlite` (mode=ro)

| Größe | Wert |
|---|---|
| `_schema_version` max | **7** (Migrations 008 + 009 fehlen; `trade_outcomes` hat **keine** Spalte `last_resolve_attempt_utc`, `instincts` existiert nicht) |
| `trade_outcomes` | 8 CLOSED (id 4–11), alle `BUY`, alle DAX, alle `account='demo'`, `provenance='autonomous'`; letzter Close 2026-08-27; 0 OPEN |
| `abstain_records` seit 2026-08-31 | **380 Zeilen, 100 % `research_empty / reason_no_candidates`** (76/76/77/74/77 pro Tag); bis 08-28 zusätzlich `debate / reason_debate_abstain` (4–12/Tag) |
| `instrument_universe` | 8 `active`, davon **3 Wochenend** (`IX.D.SUNNAS.IAE.IP` „Wochenend-US Tech 100", `IX.D.SUNDOW.IAE.IP` „Wochenend-Wall Street", `IX.D.SUNDAX.IGN.IP` „Wochenend-Deutschland 40"); 14 `verified` (u. a. MIB, AEX 40 €, STXE, FTSE, DOW, NASDAQ, SPTRD, IBEX.IFD 10 €); 2 weitere `SUN*` in `verified` |
| `paper_trades` | 1013 Zeilen, letzte `created_utc` **2026-08-28** (Shadow-Schedule seit dem Restart 08-31 aus) |
| `reward_pts` id=11 | `score_after = 50.0` (P15 Block B live) |

### 2.5 `data/bars.sqlite` (mode=ro)

| Größe | Wert |
|---|---|
| `bars` by source | `yf` 36 787 · `ig` 2 860 · `capital` 962 · **`ls` 0** (Bar-Stream nie live gelaufen) |
| `source_spend` | `research` 173 Zeilen / 5 305 Pkt (60–80/Tag) · `rescue` **5 Zeilen / 250 Pkt, ts 2026-09-04T07:12Z** (Handover sagt 09-03 — Datumsdrift) · `sample` 37/111 (letzte 08-28) · `probe` 4/20 |
| `allowance_observations` letzte | total 10 000, **remaining 9 671**, expiry 2026-09-10T07:03Z |
| IG-Research-Spend nach Epic (09-03/09-04) | SUNDOW 5+3, SUNNAS 5+3, alle anderen je 1 → **Wochenend-Epics = 10 von 13 Fetches** |

### 2.6 Laufzeit-Signale (`data/state/`)

| Quelle | Befund |
|---|---|
| `run_scheduler.log` | pro Tag ~55 ERROR (alle `yfinance: $^FCHI/$^IBEX possibly delisted (period=1d)` zwischen 09:05:00 und 09:05:31) + **1 CRITICAL** (Heartbeat `not ok`: *„measurement arm off: enable_shadow_schedule is False"* + 5 Epics unter Coverage-Schwelle, `worst_coverage 0.34`) |
| `llm_usage.json` | 77–78 Sonnet-4.6-Calls/Tag, je 2 296 Input-Tokens (konstant), `cache_read_input_tokens` **0**; Tages-Σ **201 087 / 201 907 / 200 582 / 200 223** → Budget 200 000 täglich erschöpft; `scheduler_state.last_research_ts = 15:48` bei Fenster-Ende 17:30 |
| `research_health.jsonl` | Heartbeat 09-04: `pairs_opened 0`, `measurable_epics 5`, `ok false` |
| `run_webui.log` | **32 MB in 2 Tagen**, 510 736 `GET /api`-Zeilen (uvicorn Access-Log, Polling 7 s); außerdem zweimal `daily_loss_cap is None — INACTIVE` (WebUI baut `SchedulerConfig()` mit Default, `webui/api.py:75`) |
| Scheduler-Start-Zeile | `starting scheduler daemon (account=demo, max_trades=5, daily_loss_cap=1800.0, cycle=5min)` — Loss-Cap ist im Scheduler **aktiv** (CLI-Default 1800) |

### 2.7 Step-0-Ritual (Turbo / EPIC_MAP) — Erwartung No-Op, 6. Mal

Phase 15 A-1 (2026-08-31): 14 Repo-Treffer `turbo` = ausnahmslos der bewusst behaltene
Legacy-Dateiname `turbo_candidates.json` (`state.py:27-30` „Do NOT rename"); 3 `EPIC_MAP`-Treffer =
Phase-14-Doku-Kommentare. Phase 16 führt keine neue Turbo-Referenz ein.

### 2.8 Was heute **nicht** existiert (Doku-Leichen)

- `LiveQuoteCache` — **0 Treffer** im Repo (`grep -rn LiveQuoteCache --include=*.py`); ROADMAP.md:99 + `phase9_universe/CLAUDE.md:47,133` führen es als offenes Item.
- `Database.get_risk_mode()` — 0 Treffer (P15 §10 nannte es „toter Code"; ist bereits weg).
- Produktions-Aufrufer von `run_migrations()` — 0 (nur `phase2_persistence/scripts/init_db.py:54`, `live_test.py`, `backfill_synthetic.py`, Tests).
- Force-Trigger — 0 Code-Pfad (P15 A-3), Hard Rule 5 bleibt Vorschrift für den Tag, an dem einer gebaut wird.

---

## §3 Befunde L1–L9 (alle selbst verifiziert 2026-09-05)

### L1 — Research-Todesspirale (🔴 Bot tot)

`phase4_research/research/context_builder.py:251-256` holt **genau 8** Trades ohne Zeitfenster:

```python
    recent_trades = db.get_recent_trades_for_prompt(
        8,
        min_hold_min=config.recent_trades_min_hold_min,
        quarantine_before=config.recent_trades_quarantine_before,
        exclude_provenance=config.recent_trades_exclude_provenance,
    )
```

Seit den zwei Verlusten 08-26/08-27 lautet die Tabelle „5–6 von 7 Verluste"; das LLM nennt sie in
fast jedem Abstain als Faktor (1). Da nur ein neuer Trade die Tabelle ändert und kein Trade
mehr entsteht, ist der Zustand **absorbierend**. Vorher (08-24 bis 08-28) gab es täglich
Picks + Debatten + Trades bei fast identischer Verlusthistorie — der Kipppunkt ist der 7. Trade.
Das System-Prompt (`prompt.py:38-51`) sagt *„When in doubt, ABSTAIN"* und nichts über die
Rolle der Historie.

### L2 — Token-Budget stranguliert den Nachmittag (🔴)

77 Calls × ~2 600 Tokens = 200 k = exakt `daily_token_budget` (`config.py:134`, `run.py:57`).
Der Budget-Breaker (`scheduler/budget.py:188-192`, inklusive Grenze) blockiert ab ~15:48 jeden
weiteren Trade-Zyklus. `LLMClient(cache_system=...)` (`llm_client.py:224`) wird in
`_build_research` (`wiring.py:248-256`) nicht gesetzt. **Caching-Realität:** Sonnet 4.6 cached
erst ab 1024 Präfix-Tokens (claude-api-Skill, `prompt-caching.md:136`); das System-Prompt hat
~250 → `cache_system=True` allein bringt **erwartet 0**. Der wirksame Fix ist das Budget.

### L3 — Migrations nie angewendet, Doku behauptet das Gegenteil (🔴)

`phase8_scheduler/scripts/wiring.py:803` `    db = Database(str(_DB_PATH))` — kein
`run_migrations()`. Zwei Restarts (08-31, 09-03) haben v7 nicht verändert. Folgen:

- `phase7_reward/reward/recorder.py:335` `row.get("last_resolve_attempt_utc")` → immer `None`
  → Backoff-Skip nie; Pre-Claim `db.update_trade_resolve_attempt` (`db.py:212-216`, UPDATE auf
  fehlende Spalte) wirft `OperationalError`, wird in `recorder.py:358-366` als **DEBUG** geschluckt.
  **A6 (P7) ist nicht live-verifizierbar, solange 008 fehlt.**
- `instincts`-Tabelle fehlt → Bridge (D2) würde beim ersten Close crashen (best-effort-gekapselt, aber inert).

Falsche Behauptungen: root `CLAUDE.md:119-120` (nach dem Phase-16-Absatz der Plan-Session; vorher 108-109) („`db.py:run_migrations()` wendet sie beim
nächsten Service-Restart automatisch an"), `PHASE15_CLOSEOUT_HANDOVER.md` §7 E1 + §9.13 + §10
Punkt 4 (📕 → nur 🟡-Vermerk), `ROADMAP.md:441` (Phase-15-Status-Absatz).

### L4 — Flags nicht restart-fest (🟠)

`run_scheduler.sh` endet mit `exec python -m scheduler.run "$@"`; `restart-services.sh`
startet die Wrapper ohne Argumente (`SERVICES`-Registry Z. 64-69, `cmd_start` übergibt nichts).
Jeder Restart = Defaults = alle vier Arme aus. `last_shadow_pairs_ts = 2026-08-28` beweist, dass
der Arm vor dem 08-31-Restart an war.

### L5 — Wochenend-Instrumente (🟠)

`phase9_universe/universe/discovery.py:131` prüft `market_status == "TRADEABLE"` **zum
Discovery-Zeitpunkt** (am Wochenende wahr). Research überspringt sie unter der Woche
(`context_builder.py:135` `log.info("context: %s not TRADEABLE (status=%s) — skipping", epic, market_status)` — im Log als `status=EDITS_ONLY`), der `universe_refresher`
(`wiring.py:~940-975`) und die Symbol-Resolver-Pfade bezahlen trotzdem IG-Research-Punkte
(yF hat kein Intraday für `SUN*` → IG-Fallback). `run_promotion_cycle` (Signatur-Default `    max_active: int = 8,` — `promotion.py:165`) füllt Slots mit ihnen.

### L6 — Promotion-Bridge fehlt (🟡)

Existiert: `phase15_v4/instinct/{extractor,validator,promotion}.py`, `Database.insert_instinct /
list_instincts / update_instinct_status` (`db.py:416/433/460`), VETO 5 (`vetos.py:206-260`,
Rules = `Callable[[dict], bool]` über den Kandidaten-Dict mit `epic`/`direction`). Fehlt: jeder
Aufrufer, die Prädikat-Kompilierung, `ExecutionConfig.longterm_rules`-Befüllung beim Start.

### L7 — B3 Margin-Headroom (🟡)

`sizing.py:65` `cap_size = (available_balance * max_leverage) / (price * point_value)` bindet bei
jedem DAX-Trade; `MarketInfo` (`models.py:50-64`) trägt kein Margin-Feld; `get_market_info`
(`ig_adapter.py:479-513`) extrahiert keines. Design + Prep: `phase5_execution/CLAUDE.md:231-280`.

### L8 — WebUI-Access-Log (🟢)

`phase8_scheduler/scripts/run_webui.sh` letzte Zeile
`exec uvicorn webui.api:app --host 127.0.0.1 --port "${PORT}"` — kein `--no-access-log`; kein
`RotatingFileHandler`/`logrotate` im Repo (0 Treffer).

### L9 — yF-Breaker trippt jeden Morgen um 09:05 (🟢, braucht P3-Freigabe)

`fetcher.py:407-411`: `DataUnavailableError` (leerer Frame, „got 0, want >= 1, attempt 3/3")
zählt als Circuit-Failure; `_TickerCircuit(open_after=4, cooldown_s=900)`. Yahoo hat um 09:05
noch keine Intraday-Bars des Tages → nach dem 4. leeren Frame 15 min „circuit open" für
`^GDAXI`, `^FCHI`, `^IBEX` gleichzeitig (Log 09:05:15 „circuit open for ^GDAXI"). Der Recorder
schreibt für dieselben Ticker 500+ 1m-Bars/Tag — der Ticker ist nicht tot, er ist um 09:05 leer.

---

## §4 Cross-Phase-Freigabe (P12) — was wo angefasst wird

| Phase | Datei(en) | Step | Art |
|---|---|---|---|
| P1 | `broker_wrapper/models.py` (`MarketInfo` +2 Felder), `adapters/ig_adapter.py:489-503`, `scripts/probe_market_margin.py` (NEU), `tests/test_ig_adapter.py` | D3 | additiv |
| P2 | `persistence/db.py` (`get_recent_rewards`, `count_closed_trades`), `tests/test_db.py` | D2 | additiv |
| P4 | `research/models.py` (+1 Feld), `research/context_builder.py:251-256` (Post-Filter), `research/prompt.py:45,124` (1 Satz + Header), `tests/` | C1, C2 | additiv/minimal |
| P5 | `execution/config.py:124` (+`margin_headroom`), `execution/sizing.py:36-68,139-146`, `tests/test_sizing.py` | D3 | additiv |
| P7 | `reward/recorder.py:167-185,428-429` (`instinct_hook`-Seam), `tests/conftest.py`, `tests/test_recorder.py` | D2 | additiv (Seam-Muster wie `confidence_provider`) |
| P8 | `scheduler/config.py:134,178,189,207,215`, `scheduler/run.py:57,97-135,165-168`, `scripts/wiring.py:302-325,790-803,1066-1077,1091-1134`, `webui/api.py:75`, `scripts/run_webui.sh`, `tests/test_run.py`, `tests/test_config.py`, `tests/test_webui.py:338-348` | A-4, B1, C3, D1, D2 | Defaults + Wiring + Preflight-Floor + Bar-Stream-Wrapper |
| P9 | `universe/discovery.py:131`, `universe/promotion.py:251-262`, `universe/models.py` (Prädikat), `tests/test_discovery.py`, `tests/test_promotion.py` | B3 | additiv |
| P15 | `instinct/models.py:171`, `instinct/extractor.py` (Trigger-Grammatik im Prompt), `instinct/bridge.py` (NEU), `instinct/compile.py` (NEU), `tests/` | D1, D2 | eigene Phase |
| **P3** | `external_data/fetcher.py:407-411` | **C5 — NUR mit eigener Nikinger-Freigabe** | Semantik-Änderung |
| **P13 / P1** | `live_data/stream.py`, `streaming/ig_lightstreamer.py` | **nicht angefasst** — der Token-Fix D1.2 lebt als Wrapper in P8 `wiring.py` | — |
| root + Doku anderer Phasen | `scripts/check_doc_rotation.py:66`, `.gitignore` (+`data/reports/`), `CLAUDE.md`, `ROADMAP.md`, `README.md`, `docs/INDEX.md`; **A-3 zusätzlich** `phase9_universe/CLAUDE.md:133` (Vermerk) + `phase15_v4/PHASE15_CLOSEOUT_HANDOVER.md` (🟡-Anhang, 📕) | A-0, A-3, E | Doku/Hygiene — Doku-Vermerke in fremden Phasenköpfen sind kein Code-Touch (P15-Konvention) |

**Nicht angefasst:** Phase 6 (Debatte), Phase 10, Phase 12, Phase 13 (`RescueConfig` bleibt, P6),
Phase 14.

---

## §5 Contracts (verifiziert 2026-09-05)

| Contract | Wo | Verbatim |
|---|---|---|
| VETO-5-Regel | `phase5_execution/execution/vetos.py:206-208` | `def longterm_pre_trade_check(candidate: dict[str, Any], rules: tuple[Any, ...]) -> VetoVerdict` — Regel `Callable[[dict], bool]`, `True` = passt; Exception = Veto (`reason=f"rule[{idx}] raised: {exc}"`) |
| Kandidaten-Dict-Keys | `vetos.py:274-275` (`candidate["epic"]`, `candidate["direction"]`), `gates.py:151,166` (`candidate.get("direction")`, `candidate.get("epic")`) | Werte `"BUY"`/`"SELL"`; Prädikate benutzen `.get` (fail-closed auf fehlenden Key durch VETO 5) |
| `ExecutionConfig.longterm_rules` | `execution/config.py:119` | `    longterm_rules: tuple[Any, ...] = ()` |
| Extractor | `phase15_v4/instinct/extractor.py:250-254` | `SingleShotInstinctExtractor.extract(lessons: list[dict], rewards: list[dict]) -> InstinctExtractionResult` (`.ok`, `.instincts`, `.error`; never raises) |
| Validator | `validator.py:97-101`, `:55-78` | `InstinctValidator.validate(instinct: Instinct, trades: Iterable[dict]) -> InstinctValidation`; **`InstinctValidation.decision: str`** ∈ `validated`/`refuted`/`proposed` (verifiziert 2026-09-05, Sonnet-Cold-Read) |
| Promotion | `promotion.py:32-36` | `promote_eligible(instincts: Iterable[Instinct], n_closed: int, cfg: InstinctConfig) -> list[Instinct]` — pure, kein DB-Touch |
| Instinct | `models.py:97-129` | Felder `trigger, domain, confidence, evidence_trade_ids, contradictions_trade_ids, status, created_utc, validated_utc, promoted_utc, archived_utc, id`; `__post_init__` (Z. 108-129) normalisiert list/tuple-IDs zu `tuple`; DOMAINS `("entry","exit","sizing","timing")`; **kein** `from_row` |
| DB-Instinct-API | `db.py:416,433,460` | `insert_instinct(dict) -> int`; `list_instincts(status=None, n=None) -> list[dict]` (JSON-Spalten `evidence_trade_ids_json`, `contradictions_trade_ids_json`); `update_instinct_status(id, status) -> bool` |
| RewardSink-Seam-Muster | `reward/recorder.py:167-176` | kwargs `db, broker, scorer, brain, cfg, confidence_provider=None` — `instinct_hook` folgt exakt diesem Muster |
| Trade-Close-Seam | `recorder.py:424-429` | `(5) best-effort lesson … self._extract_lesson(...)` dann `self._observe_confidence(deal_id)`; `trade_id = row.get("id")` (Z. 323) ist im Scope |
| Migrations | `persistence/migrations.py:54-57`, `db.py:88-96` | `executescript` (DDL committed implizit), `run_migrations()` idempotent, seedet `ig_config_state` mit `INSERT OR IGNORE` |
| Scheduler-CLI → Config | `scheduler/run.py:149-169` | `config_from_args` baut `SchedulerConfig(account="demo", …, enable_paper_debate=args.enable_paper_debate, …)` |
| `_size_from_risk` | `sizing.py:36-68` | kwargs `available_balance, risk_pct, stop_distance_points, price, max_leverage, point_value=1.0`; `cap_size` Z. 65 |
| `get_market_info` Roh-Body | `ig_adapter.py:482-484` (mehrzeilig) | `                body = self._request(` / `                    "GET", f"/markets/{epic}", version="3", auth=True,` / `                )`; danach `instr = body.get("instrument", {}) or {}` (Z. 485) |
| Discovery-Filter | `discovery.py:118-140` | `_passes_code_filter(hit, siblings, filtered) -> bool`, `hit` trägt `name`, `market_status`; `_bump(filtered, reason)` |
| Universe-Demotion | `store.py:159-200` | `UniverseStore.set_status(epic, status, *, checks=None, …)`; `UniverseRecord.name: str \| None` (`models.py:96`) |
| Heartbeat-Schwelle | `data_foundation/heartbeat.py:124` | `largest_gap_min > 5` **oder** Density < 90 % ⇒ Epic „below threshold" |

---

## §6 Schritt-Sequenz

> Konvention wie P15: pro Step **Ziel → Anker (verbatim) → Edit → Tests → Akzeptanz**.
> „Bot stoppen" steht explizit dabei, wo nötig (P14). Alle Steps sind atomar committbar.

### Block A — Haushalt

#### A-0 — Phase anlegen + Phasenkopf lesen

- Verzeichnis `phase16_activation/` existiert seit der Plan-Session mit `CLAUDE.md` (Header-Card +
  Mission + Plan-Session-`## Session stopped`-Block). Zuerst lesen, dann diesen Block per
  Rotationsregel nach `phase16_activation/SESSIONS_ARCHIVE.md` (NEU) rotieren und den eigenen
  Session-Block anlegen.
- `scripts/check_doc_rotation.py:66` Anker `    "phase15_v4",` → darunter `    "phase16_activation",`.
  Test: `python3 scripts/check_doc_rotation.py --strict --phase phase16_activation` exit 0.
- `phase16_activation/tests/` + `phase16_activation/scripts/` anlegen (Inhalt kommt in E2).
  **Kein** `pip install -e` nötig (keine Package-Imports aus anderen Phasen; das Report-Skript
  importiert `persistence` über den venv, der schon alle Phasen editable installiert hat — §9 #12).

#### A-1 — Step-0-Ritual (auch als No-Op protokollieren)

```bash
grep -rni "turbo" --include="*.py" --include="*.sql" --include="*.sh" . --exclude-dir=.venv
grep -rn "EPIC_MAP" --include="*.py" . --exclude-dir=.venv
```

Erwartung: 14 + 3 Treffer wie §2.7. Ergebnis in `phase16_activation/CLAUDE.md`. Jeder Treffer,
der **nicht** `turbo_candidates.json` oder Phase-14-Doku ist: stoppen, melden, nicht umbenennen.

#### A-2 — Regression-Baseline VOR dem ersten Fix

Sweep nach §2.1. **Erwartung Σ = 1843.** Abweichung = Befund von *vor* Phase 16, dokumentieren.

#### A-3 — Code↔.md-Sweep (vier falsche Behauptungen + Leichen)

| Datei | Anker (verbatim, heutige Zeile) | Edit |
|---|---|---|
| root `CLAUDE.md:119-120` | `> **Live-DB Migration 009** — additive Schema-Migration, ` … `run_migrations()` wendet sie` / `> beim nächsten Service-Restart automatisch an (Schema heute v7).` | ersetzen durch: *„Live-DB Migration 008 + 009 — **nicht** automatisch: kein Produktions-Caller von `run_migrations()` (korrigiert 2026-09-05, Phase-16-Plan §3 L3). Phase 16 B1 verdrahtet den Aufruf, B2 wendet sie einmalig an."* |
| root `CLAUDE.md` Status-Tabelle Zeile `\| 15 — V4: …` (Z. 167) | Teilstring `Live-DB Migration 009 (additiv, beim nächsten Service-Restart)` | → `Live-DB Migration 008+009 (nicht automatisch — Phase 16 B1/B2)` |
| `README.md:39` | `\| 15    \| V4: Reward-Kalibrierung · Instinct-ECC · Quellen-Vertrauens-Lock \| 🔄 **in execution seit 2026-09-01**` | Status-Zelle → `✅ **abgeschlossen (Closeout 2026-09-05, Session #13)**`; neue Zeile 16 „Freischaltung 🔄 seit 2026-09-05" |
| `ROADMAP.md:99` | `- [ ] \`LiveQuoteCache\` in den P4-Research-Kontext verdrahtet — **weiterhin offen**, hing an` | Item auf `- [ ] ~~…~~ *gegenstandslos (korrigiert 2026-09-05, Phase 16 A-3): `LiveQuoteCache` existiert nicht im Repo (0 Treffer); der Bedarf ist durch Phase 12/13 BarService + LS-Tick-Aggregation abgelöst.*` |
| `ROADMAP.md:441` | Teilstring `Live-DB Migration 009 (additiv, beim nächsten Service-Restart)` | → `Live-DB Migration 008+009 (nicht automatisch, korrigiert 2026-09-05 → Phase 16 B1/B2)` |
| `phase9_universe/CLAUDE.md:133` | Zeile beginnt `\| Step 7b — LS-Fix + \`LiveQuoteCache\` \|` | datierter Vermerk in der Status-Zelle: „*2026-09-05: `LiveQuoteCache` nie gebaut (0 Treffer), Item geschlossen (Phase 16 A-3)*" |
| `phase15_v4/PHASE15_CLOSEOUT_HANDOVER.md` (📕) | Dateiende | **nur** anhängen: `> 🟡 **Korrekturhinweis 2026-09-05 (Phase 16 A-3):** §7 E1, §9.13 und §10 Punkt 4 behaupten einen automatischen Migrations-Apply beim Restart — falsch, kein Produktions-Caller (Plan §3 L3). §4 „Live-Substrate": die 5 Rescue-Zeilen tragen ts 2026-09-04T07:12Z, nicht 09-03.` |
| `ROADMAP.md` | Abschnitt `## Phase 16 — Freischaltung` **existiert bereits** (Plan-Session, vor `## Meta-Strang` Z. 496); Phase-9-Absatz Z. 60-68 bereits datiert gekürzt | nur die Block-Häkchen `[ ]` → `[x]` pflegen; AK: ROADMAP.md bleibt < 40 k (heute 40 562 B, `find -size +40k` leer) |

#### A-4 — WebUI-Access-Log (L8) + irreführende WebUI-Warnung

- `phase8_scheduler/scripts/run_webui.sh` Anker `exec uvicorn webui.api:app --host 127.0.0.1 --port "${PORT}"`
  → `exec uvicorn webui.api:app --host 127.0.0.1 --port "${PORT}" --no-access-log`.
- `phase8_scheduler/webui/api.py:75` Anker `        SchedulerConfig(),` — die WebUI baut die Config nur
  für Budget-Anzeige; die Konstruktion löst `__post_init__`s Loss-Cap-WARNING aus. Edit:
  `SchedulerConfig(daily_loss_cap=1800.0)` **mit Kommentar** „Anzeige-Default = CLI-Default
  `run.py --daily-loss-cap`; die WebUI gatet nichts". Test: `tests/test_webui.py` bleibt grün (§9 #7).
- Wirkt erst nach WebUI-Restart (Block-D-Restart reicht).

#### A-5 — Operator (P13): Push

```bash
git push origin main                      # 7 Commits (Sessions #10–#13) + A-Commits
```

Der Ledger-Restore wandert nach **B2** (Recorder ist der Live-Schreiber von `bars.sqlite.source_spend`,
`journal_mode=delete` — Opus-Review §13: mit gestopptem Recorder ausführen, nicht daneben).

**Block-A-Commits:** 3 (A-0+A-1+A-2 Doku · A-3 Sweep · A-4 WebUI).

### Block B — Substrat

#### B1 — Schema-Floor im Preflight (L3, P8) — *geändert nach Opus-Review (§13)*

**Nicht** `run_migrations()` im Daemon (P8-Begründung §1). Anker `phase8_scheduler/scripts/wiring.py:1066-1077`:

```python
    def preflight_fn() -> None:
        """Fail-closed startup probe: keyring reachable + DB migration 002 applied."""
        ...
        cols = {row[1] for row in db.conn.execute("PRAGMA table_info(trade_outcomes)").fetchall()}
        if "account" not in cols:
            raise RuntimeError(
                "DB schema out of date (migration 002 not applied — 'account' column missing). "
                "Run `python phase2_persistence/scripts/init_db.py` before starting the daemon."
            )
```

Edit: neue Modul-Konstante `REQUIRED_SCHEMA_VERSION = 9` (Kommentar: *„Phase 16 B1 — 008 =
reconcile backoff column, 009 = instincts; bump when a migration lands that the daemon relies on"*)
und **nach** dem `account`-Check:

```python
        # Phase 16 B1 (2026-09-05): schema floor. The live DB sat on v7 across two restarts
        # while docs claimed migrations "apply automatically" — nothing in production ever
        # called run_migrations(). Same discipline as above: verify, never mutate.
        version = db.conn.execute("SELECT MAX(version) FROM _schema_version").fetchone()[0] or 0
        if version < REQUIRED_SCHEMA_VERSION:
            raise RuntimeError(
                f"DB schema out of date (version {version} < required {REQUIRED_SCHEMA_VERSION}). "
                "Stop all four services, back up data/trading_bot.sqlite, then run "
                "`python phase2_persistence/scripts/init_db.py --db-path data/trading_bot.sqlite`."
            )
```

Tests (`phase8_scheduler/tests/`): `preflight_fn` ist eine Closure in `build_scheduler` → nicht
offline erreichbar. Deshalb den Check als **reine Modul-Funktion** herausziehen:
`def assert_schema_floor(conn, required: int = REQUIRED_SCHEMA_VERSION) -> int` (Modul-Level in
`wiring.py`, von `preflight_fn` aufgerufen) → 3 Tests gegen eine `:memory:`-DB mit
`_schema_version`-Rows: v9 ok, v7 raise mit `init_db.py` im Text, leere Tabelle raise.
Dazu ein Source-Pin `assert "assert_schema_floor(" in inspect.getsource(...)` ist unnötig —
der Aufruf steht im selben Closure wie der bestehende `account`-Check.

#### B2 — Operator-Apply + Ledger-Restore (P13, alle vier Dienste gestoppt)

```bash
bash scripts/restart-services.sh stop && ps aux | grep -E "scheduler.run|data_foundation.run|source_registry.run|uvicorn" | grep -v grep   # muss leer sein
cp data/trading_bot.sqlite data/trading_bot.sqlite.bak-20260905-pre-mig009
phase1_broker_wrapper/.venv/bin/python phase2_persistence/scripts/init_db.py --db-path data/trading_bot.sqlite
sqlite3 "file:data/trading_bot.sqlite?mode=ro" "SELECT MAX(version) FROM _schema_version; PRAGMA table_info(trade_outcomes);" | grep -E "^9$|last_resolve_attempt_utc"
sqlite3 data/bars.sqlite "SELECT COUNT(*), SUM(points) FROM source_spend WHERE kind='rescue';"   # erwartet 5 | 250
sqlite3 data/bars.sqlite "DELETE FROM source_spend WHERE kind='rescue';"
```

Erwartung: `9` + Spalte vorhanden + Tabelle `instincts` + 0 Rescue-Zeilen. **Restart erst nach
Block D** (P14) — bis dahin bleibt der Bot aus **oder** wird mit altem Code wieder gestartet
(Nikinger-Wahl; die Abstain-Schleife kostet ~0,85 $/Tag, sonst nichts). Empfehlung: aus lassen,
Blöcke B–D dauern eine Session. ⚠ Ein Start mit **neuem** Code vor B2 scheitert jetzt laut am
Schema-Floor — das ist gewollt.

#### B3 — Wochenend-Filter + Demotion (L5, P9)

1. `phase9_universe/universe/models.py` — neue reine Funktion (neben `UniverseRecord`):

```python
WEEKEND_NAME_MARKERS: tuple[str, ...] = ("wochenend", "weekend")

def is_weekend_market(epic: str | None, name: str | None) -> bool:
    """Phase 16 B3: IG weekend markets (EDITS_ONLY Mon–Fri) never fit the 09:00–17:30 window."""
    e = (epic or "").upper()
    n = (name or "").lower()
    return ".SUN" in e or any(m in n for m in WEEKEND_NAME_MARKERS)
```

2. `discovery.py:131` Anker `    if hit.get("market_status") != "TRADEABLE":` → **davor**:

```python
    if is_weekend_market(hit.get("epic"), hit.get("name")):
        _bump(filtered, "weekend_market")
        return False
```

3. `promotion.py:262` Anker `    for rec in store.active_universe():` → als erste Zeile im Loop:

```python
        if is_weekend_market(rec.epic, rec.name):
            store.set_status(rec.epic, "quarantined", checks={"reason": "weekend_market"})
            _emit(health_sink, {"event": "universe_demote", "epic": rec.epic, "reason": "weekend_market"})
            continue
```

   und dieselbe Sperre vor der Promotion `verified → active` (Step 2, Z. 251-258, Anker
   `    active_count = len(store.active_universe())` — im Kandidaten-Loop `continue` bei Wochenend).

Tests (`phase9_universe/tests/`): `test_is_weekend_market` (5 Fälle: `.SUN`-Epic, „Wochenend-",
„Weekend", None-Name, DAX negativ) · `test_discover_filters_weekend_market` (Fixture-Hit mit
`name="Wochenend-Wall Street-Kassa (1€)"` → `filtered["weekend_market"] == 1`) ·
`test_promotion_demotes_active_weekend_epic` · `test_promotion_never_activates_weekend_epic`.
**Erwartung Live** (nach Restart, erster `universe_refresher`-Lauf ≤ 240 min): 3 `SUN*` →
`quarantined`, `active` füllt auf 8 aus `verified` (z. B. MIB, STXE, FTSE, AEX).
⚠ AEX `point_value 40.0` ist seit Phase-10 B1 korrekt in `point_values` — kein 40×-Risiko mehr,
aber §9 #10 prüfen.

**Block-B-Commits:** 2 (B1 · B3) + Operator-Notiz B2.

### Block C — Research-Loop

#### C1 — Historien-Fenster (L1, P2, P4)

`phase4_research/research/models.py:681` Anker `    recent_trades_quarantine_before: str | None = None`
→ darunter:

```python
    # Phase 16 C1 (2026-09-05, L1): a trade older than this many calendar days no longer
    # appears in the prompt's recent-trades table. Without a window the table only changes
    # when a new trade closes — and after the 7th loss the LLM abstained on that table alone,
    # 77×/day, for five days (an absorbing state). None = off (bit-identical to pre-P16).
    recent_trades_max_age_days: int | None = 14
```

`context_builder.py:251-256` (Anker oben, §3 L1) → nach dem Aufruf:

```python
    if config.recent_trades_max_age_days is not None:
        recent_trades = _drop_older_than(recent_trades, config.recent_trades_max_age_days, now=...)
```

`_drop_older_than` ist eine reine Modul-Funktion: parst `close_ts` (Fallback `open_ts`) mit
`datetime.fromisoformat` (beide Formate `+02:00` und `Z` kommen vor — `Z` vorher ersetzen),
unparsbar ⇒ **behalten** (fail-open Richtung „LLM sieht mehr", nie weniger). `now` per
`now_fn`-Parameter injizierbar (Testbarkeit; Default `datetime.now(timezone.utc)`).
`_render_trades`-Header (`prompt.py:124`) `"Recent trades (newest first):"` →
`"Recent trades (last 14 days, newest first):"` — Zahl aus der Config rendern, nicht hardcoden.

Tests (`phase4_research/tests/`): `test_drop_older_than_keeps_recent_drops_old` ·
`test_drop_older_than_keeps_unparsable` · `test_build_context_window_default_14_days` (8
Trades, 6 davon 20 Tage alt → 2 im Kontext) · `test_window_none_is_bit_identical`.

#### C2 — Ein Prompt-Satz (P4)

`prompt.py:45` Anker `    "- When in doubt, ABSTAIN. A skipped session is cheap; a bad trade is not.\n"`
→ **danach**:

```python
    "- Recent trades are context for lessons and sizing, NOT a veto: a losing streak by "
    "itself is never a reason to abstain — judge the setup in front of you.\n"
```

Test: `test_system_prompt_names_history_as_context_not_veto` (Substring-Pin). §9 #2: kein
bestehender Test pinnt den Prompt-Text (grep 2026-09-05 leer).

#### C3 — Budget 300 k (L2, P8)

- `scheduler/config.py:134` Anker `    daily_token_budget: int | None = 200_000  # v1 runaway breaker ≈ €0.8/day; None ⇒ explicitly disabled (WARNING in budget.py)`
  → `300_000  # Phase 16 C3: 200k was exhausted daily at ~15:48 (77 research calls × 2.6k); ≈ €1.2/day worst case`.
- `scheduler/run.py:57` Anker `        default=200_000,` → `300_000` + Help-Text.
- Tests anpassen: `test_run.py:20,52`, `test_config.py:39`, `test_webui.py:338-339,348`
  (`percent` wird `100*1800/300000 = 0.6`).
- **Kein `cache_system=True`** (P3-Begründung §1: Meter zählt Cache-Reads voll, Präfix < 1024).
  Im Phasenkopf als „bewusst nicht gebaut" mit beiden Fakten notieren.

#### C4 — Research-Ökonomie (nur Doku, kein Code)

Mit 300 k reicht der Tag (102 Zyklen × 2,6 k = 265 k). Ein Dedupe („Prompt unverändert → kein
Call") ist **nicht** möglich, weil Live-Quotes im User-Prompt jede Runde variieren — bewusst
nicht gebaut, im Phasenkopf so notieren (YAGNI mit Begründung).

#### C5 — Breaker-Semantik (L9) — **wartet auf P3-Freigabe**

`fetcher.py:407-411` Anker:

```python
        except (DataUnavailableError, RateLimitError):
            self._circuit.record_failure(symbol)
            raise
```

Edit: nur `RateLimitError` (und echte Transport-Exceptions) öffnen den Circuit; ein leerer
Frame ist ein **Daten**-Urteil, kein Ausfall:

```python
        except RateLimitError:
            self._circuit.record_failure(symbol)
            raise
        except DataUnavailableError:
            # Phase 16 C5: empty-at-open is not an outage — do not open the circuit.
            raise
```

Kosten: an einem wirklich toten Ticker 3 Retries × Backoff pro Zyklus (~7 s) statt 15 min
Sperre — akzeptabel, weil `no_intraday_source`-Epics die Registry ohnehin überspringt.
Tests (`phase3_external_data/tests/`): bestehende Circuit-Tests anpassen (welche: §9 #8) +
`test_empty_frame_does_not_open_circuit`. **Ohne Freigabe: Step übersprungen, im Phasenkopf
als „offen, P3 nicht freigegeben" geführt — kein stilles Weglassen.**

**Block-C-Commits:** 2–3 (C1 · C2+C3 · C5 nur falls freigegeben).

### Block D — Freischaltung

#### D1 — Defaults flippen (L4, P4/P5, P8 + P15)

`scheduler/config.py` — vier Anker, je `False` → `True`, Kommentar je Zeile *„Phase 16 D1: ON
by default; `--no-…` disables"*:

| Zeile | Anker |
|---|---|
| 178 | `    enable_paper_debate: bool = False` |
| 189 | `    enable_shadow_schedule: bool = False` |
| 207 | `    enable_divergence_sampler: bool = False` |
| 215 | `    enable_bar_stream: bool = False` |

`scheduler/run.py:97-135` — die vier `parser.add_argument("--enable-…")`-Blöcke **ersetzen**
durch `--no-paper-debate`, `--no-shadow-schedule`, `--no-divergence-sampler`, `--no-bar-stream`
(`action="store_true"`, Help nennt Kosten wie bisher). `run.py:165-168` Anker
`        enable_paper_debate=args.enable_paper_debate,` (+3 Geschwister) → `=not args.no_paper_debate` usw.

`phase15_v4/instinct/models.py:171` Anker `    enable_instinct_promotion: bool = False` → `True`
(Kommentar: *„Phase 16 P5 supersedes P15-P10; the real gates are `instinct_n_min` + the validator"*).

Tests: `test_run.py:64-92` (vier Tests: Default `True`, `--no-*` → `False`), `test_config.py:61,65,72`,
`test_instinct_models.py:178,199`, `test_promotion.py:195` umdrehen; **neu**
`test_default_profile_is_fully_armed` (P8): `SchedulerConfig()` hat alle vier `True`,
`enable_paper_trades True`, `enable_measurement_heartbeat True`, `enable_bar_service True`.
`phase13_live_data/tests/test_rescue.py::test_enable_gap_rescue_is_NOT_in_scheduler_config`
bleibt unverändert grün (P6). Offline-Smoke `phase8_scheduler/scripts/smoke_test.py` 3/3 (§9 #9).

**Bar-Stream-Risiko (geprüft):** Build (`wiring.py:1091-1134`) und Start
(`runner.py:469-482`) sind fail-soft (`logger.critical`, Daemon läuft weiter). Erster Live-Lauf
des `TickAggregatorRecorder` überhaupt (`bars.source='ls'` = 0 heute) → Day-0-Check in E3.

#### D1.2 — Bar-Stream-Token-Fix als Wrapper (P8 only) — *aus dem Opus-Review (§13), selbst verifiziert*

**Befund:** `wiring.py:1101-1104` baut `            ls_client = IGLightstreamerClient(` / `                cst=broker._cst,` / `                security_token=broker._security_token,` (mehrzeilig)
— der Client **snapshottet** die Tokens (`ig_lightstreamer.py:232-233`, Passwort-String Z. 256).
`runner._restart_bar_stream` (`runner.py:493-511`) wird nach jeder IG-Token-Rotation aus
`_warm_session` gerufen und ruft `restart()` bzw. `stop()+start()` **auf demselben Objekt** →
der Stream verbindet mit dem alten CST → auth-tot + ein CRITICAL pro Rotation, direkt ins
A6-Kriterium. Latent seit Phase 13 B3, nie aufgefallen, weil der Arm nie live war.

**Fix (nur `wiring.py`, kein P13/P1-Touch):** den Recorder-Build in eine Factory ziehen und ein
Wrapper-Objekt übergeben, das bei jedem `start()` **frisch** aus den aktuellen Broker-Tokens baut:

```python
class _RebuildingBarStream:
    """Phase 16 D1.2: rebuild the LS client from the broker's CURRENT tokens on every start.
    ``IGLightstreamerClient`` snapshots CST/XST at construction; after a token rotation the
    runner's ``_restart_bar_stream`` must get a fresh client, not the stale one."""
    def __init__(self, build_fn: Callable[[], Any]) -> None: self._build, self._inner = build_fn, None
    def start(self) -> None:  self._inner = self._build(); self._inner.start()
    def stop(self) -> None:   (self._inner.stop() if self._inner is not None else None); self._inner = None
    def restart(self) -> None: self.stop(); self.start()
```

Anker `wiring.py:1131` `            bar_stream = recorder` → `bar_stream = _RebuildingBarStream(_build_recorder)`,
wobei `_build_recorder` der bisherige Konstruktions-Block (Z. 1103-1129) als lokale Funktion ist.
Tests (P8): `test_rebuilding_bar_stream_uses_fresh_tokens` (Fake-Broker mit veränderlichem `_cst`,
Fake-Build-Fn zählt Aufrufe und merkt sich das Token → nach `restart()` zweiter Build mit neuem
Token) · `test_rebuilding_bar_stream_stop_before_start_is_noop`.

#### D2 — Promotion-Bridge + Prädikat-Compiler (L6, P2/P7/P8/P15)

**D2.1 P2** (`persistence/db.py`, nach `get_recent_lessons` Z. 322-327):

```python
    def get_recent_rewards(self, n: int = 20) -> list[dict[str, Any]]:
        """Phase 16 D2: newest ``reward_pts`` rows for the instinct extractor."""
        cur = self.conn.execute("SELECT * FROM reward_pts ORDER BY id DESC LIMIT ?", (n,))
        return self._rows(cur)

    def count_closed_trades(self) -> int:
        """Phase 16 D2: ``n_closed`` for ``promote_eligible`` (P12 gate)."""
        cur = self.conn.execute("SELECT COUNT(*) FROM trade_outcomes WHERE status = 'CLOSED'")
        return int(cur.fetchone()[0])
```

**D2.2 P15 `instinct/compile.py` (NEU):**

```python
TRIGGER_RE = re.compile(r"^\s*avoid\s+(BUY|SELL)(?:\s+on\s+([A-Z0-9.]+))?\s*$", re.IGNORECASE)

def instinct_from_row(row: dict) -> Instinct: ...      # JSON-Spalten → tuple[int,...]
def compile_rule(instinct: Instinct) -> Callable[[dict], bool] | None:
    """entry-domain + grammar match → predicate; anything else → None (logged WARNING)."""
def compile_rules(rows: Iterable[dict]) -> tuple[Callable[[dict], bool], ...]
```

Prädikat: `lambda c: not (c.get("direction") == D and (E is None or c.get("epic") == E))`.
`domain != "entry"` → `None` + WARNING *„no consumer for domain X"*. Fail-closed bleibt VETO 5s Sache.

**D2.3 P15 `instinct/extractor.py`** — im Prompt (`_build_instinct_prompt`, Zeile mit
`f"Felder trigger (string), domain (eines von: {domain_list}), "`, §9 #6) die Grammatik nennen:
*„`trigger` MUSS die Form `avoid BUY` / `avoid SELL` / `avoid BUY on <EPIC>` haben"* + im JSON-Schema
`"trigger": {"type": "string", "pattern": "^avoid (BUY|SELL)( on [A-Z0-9.]+)?$"}`.

**D2.4 P15 `instinct/bridge.py` (NEU):**

```python
class InstinctBridge:
    def __init__(self, db, extractor, validator, cfg: InstinctConfig, *,
                 lessons_n: int = 20, rewards_n: int = 20, trades_n: int = 500) -> None: ...
    def after_trade_closed(self, trade_id: int) -> None:
        """Best-effort, never raises: extract → insert(proposed) → validate → status → promote()."""
    def promote(self) -> list[int]:
        """validated rows → promote_eligible(…, db.count_closed_trades(), cfg) → status 'promoted'."""
    def load_rules(self) -> tuple[Callable[[dict], bool], ...]:
        """compile_rules(db.list_instincts(status='promoted'))."""
```

**D2.5 P7 `reward/recorder.py`:** `__init__` (Z. 167-176) + `instinct_hook: Callable[[int], None] | None = None`
(Docstring-Zeile analog `confidence_provider`); Anker Z. 428-429:

```python
        # observe-only confidence (forward-compat; never gates — Decision C).
        self._observe_confidence(deal_id)
```

→ **davor**:

```python
        # Phase 16 D2: best-effort instinct extraction (Phase-15 bridge). Never raises.
        if self.instinct_hook is not None and trade_id is not None:
            try:
                self.instinct_hook(int(trade_id))
            except Exception as exc:  # noqa: BLE001
                logger.critical("reward: instinct_hook raised for deal_id=%s: %s", deal_id, exc)
```

**D2.6 P8 `wiring.py`:** `_build_reward_sink(broker, db)` (Z. 302-325) baut zusätzlich
`SingleShotInstinctExtractor(llm)` (derselbe Haiku-Client), `InstinctValidator()`,
`InstinctBridge(db, extractor, validator, InstinctConfig())` und gibt
`RewardSink(..., instinct_hook=bridge.after_trade_closed)` **und** die Bridge zurück (Signatur
`-> tuple[Any, Any]`; einziger Aufrufer in `build_scheduler`, §9 #11). In `build_scheduler`
Anker `wiring.py:832` `    reward_sink = _build_reward_sink(broker, db)` → **ersetzen** durch:

```python
    reward_sink, instinct_bridge = _build_reward_sink(broker, db)
    instinct_bridge.promote()
    exec_cfg = dataclasses.replace(exec_cfg, longterm_rules=instinct_bridge.load_rules())
```

(Die Bridge liest `instincts` → **setzt B2 voraus**; vor dem Preflight-Floor läuft dieser Code
nicht, also kein Crash-Pfad auf v7 — `build_scheduler` ruft `preflight_fn` erst im Runner; ein
Start auf v7 endet damit am Floor, nicht an einer fehlenden Tabelle. §9 #20 prüfen.)

(`exec_cfg` wird Z. ~790 gebaut und erst danach verbraucht — kein Reorder nötig.) Eine
Promotion **mitten im Lauf** wirkt auf VETO 5 erst nach Restart — im Phasenkopf so dokumentiert
(n_min=50 macht das im Test irrelevant).

Tests: P15 `test_compile.py` (Grammatik ok/Epic-frei/unbekannt→None/domain exit→None/Prädikat
vetoed BUY-DAX, passt SELL) · `test_bridge.py` (Fake-DB + Fake-Extractor: proposed→validated→
promote bei n≥50 / `[]` bei n=8 / Extractor-Fehler → 0 Inserts, kein Raise) · P7
`test_recorder.py` `test_instinct_hook_called_after_close_and_never_raises` (+ `conftest.FakeDB`
ggf. um `count_closed_trades`) · P2 `test_db.py` 2 Tests · P5 unverändert (VETO 5 bereits gepinnt).
**AK9-Erbe:** mit 0 `promoted`-Rows bleibt `longterm_rules == ()` → `test_pre_trade_check_veto5_empty_rules_is_identity` grün.

#### D3 — Margin-Headroom B3 (L7, P1/P5) — erst Live-Probe, dann Code

**D3.0 Operator-Probe (P13, Demo, ~3 Requests, 0 Datenpunkte):** neues Skript
`phase1_broker_wrapper/scripts/probe_market_margin.py --epic IX.D.DAX.IGN.IP --epic IX.D.IBEX.IFM.IP --epic IX.D.AEX.IFM.IP`
— nutzt `IGAdapter._request("GET", f"/markets/{epic}", version="3", auth=True)` und druckt
`instrument.marginFactor`, `instrument.marginFactorUnit`, `instrument.marginDepositBands`,
`dealingRules` roh als JSON (stderr-Log, stdout JSON). **Erwartung (unverifiziert, §9 #1):**
`marginFactor` numerisch (z. B. `5`), `marginFactorUnit == "PERCENTAGE"`. Weicht es ab → Feldnamen
im Phasenkopf festhalten, D3.1 entsprechend.

**D3.1 P1:** `broker_wrapper/models.py:62-64` nach `    contract_size: str | None = None`:
`    margin_factor: float | None = None` + `    margin_factor_unit: str | None = None`.
`ig_adapter.py:503` Anker `                    contract_size=instr.get("contractSize"),` → darunter
`margin_factor=_float_or_none(instr.get("marginFactor")), margin_factor_unit=instr.get("marginFactorUnit"),`
(+ Helper). Test `test_get_market_info_extracts_margin_factor` (Mock-Body mit beiden Feldern;
fehlend → `None`).

**D3.2 P5:** `execution/config.py:124` nach `    max_leverage: float = 20.0             # notional cap = balance × this (ESMA ceiling)`:
`    margin_headroom: float = 0.95          # Phase 16 D3: fraction of available balance the margin cap may use`.
`sizing.py:36-68` `_size_from_risk(..., margin_factor_pct: float | None = None, margin_headroom: float = 1.0)`;
nach Z. 65 `cap_size = …`:

```python
    if margin_factor_pct is not None and margin_factor_pct > 0:
        margin_cap = (available_balance * margin_headroom) / (price * point_value * margin_factor_pct / 100.0)
        cap_size = min(cap_size, margin_cap)
```

`compute_size` (Z. 139-146) reicht `margin_factor_pct` durch — **kein Caller-Touch**: der einzige
Produktions-Aufrufer `executor.py:321-324` (`market_info_env = self.broker.get_market_info(epic)` →
`compute_size(account_env, price_env, market_info_env, risk_pct, self.config, epic=epic)`) übergibt
den Envelope schon heute; `compute_size` liest `margin_factor`/`margin_factor_unit` aus
`market_info_env.data` selbst, nur wenn `margin_factor_unit == "PERCENTAGE"`, sonst `None` + einmaliges WARNING
(*„margin factor unavailable/unit X — falling back to leverage cap"*, P10).
Tests `test_sizing.py`: Datenwoche-Grenzfall `available=27_100, ask=24_500, pv=1.0, mf=5.0`
→ Leverage-Cap 22,12, Margin-Cap 21,0 → `size == 21.0` (IG lehnte 22,1 ab, nahm 22,0);
`mf=None` → bit-identisch zu heute; `unit="PERCENTAGE"`-Pflicht.

**Block-D-Commits:** 6 (D1 · D1.2 · D2.1+D2.2+D2.3 · D2.4+D2.5+D2.6 · D3.0 Skript · D3.1+D3.2).
**Nach dem letzten D-Commit:** Operator-Restart (E3-Runbook).

### Block E — 2-Wochen-Autonomie-Test

#### E1 — Vorregistrierung (P11) — `phase16_activation/PHASE16_AUTONOMY_PREREGISTRATION.md` (📕, NEU)

Inhalt, **vor** dem Restart committet: Start-/Enddatum (10 Handelstage), Konfiguration
(Demo, `max_trades 5`, `daily_loss_cap 1800`, Budget 300 k, alle vier Arme ON, Universe ohne
Wochenend), **PASS-Kriterien AK15 (§7) mit je einer append-only Messquelle**, erlaubte
Operator-Ereignisse (P17: Backoff-KILL einmal, Reboot = Intervention; Daily-Loss-Cap trippt =
Tag zählt, Lauf geht weiter), Watch-Items (BUY-Bias, DAX-Only, 09:05-Breaker, LS-Bars,
Zombie-Zahl, `min_evidence` vs. Trade-Zahl), Operator-Regel: **nichts anfassen außer dem täglichen
Report**; Desktop-Session bleibt eingeloggt (Keyring). INDEX-Zeile im selben Commit.

#### E2 — `phase16_activation/scripts/autonomy_report.py` (deterministisch, read-only)

```
python phase16_activation/scripts/autonomy_report.py --day 2026-09-08            # Tagesbericht
python phase16_activation/scripts/autonomy_report.py --from 2026-09-08 --to 2026-09-19 --summary   # PASS-Auswertung
```

Liest **nur** append-only Quellen, `mode=ro` (Opus-Review §13: die drei `*_state.json` werden
in-place überschrieben und beweisen nichts):

| Kriterium | Messquelle (append-only) | Regel |
|---|---|---|
| 1 kein Operator-Restart | `run_scheduler.log` Zeilen `starting scheduler daemon`; `run_recorder.log` `[run_recorder] starting`; `run_discovery.log` Start-Zeile; `run_webui.log` `Started server process` | pro Dienst genau **1** Start-Zeile im Fenster (die vom E3-Start) |
| 2 Dienste pro Handelstag aktiv | Scheduler: ≥ 1 `research_health.jsonl`-Event am Tag · Recorder: ≥ 1 `bars`-Zeile `source='yf'` am Tag · Discovery: `max(instrument_source_availability.last_verified_utc)` am Tag · WebUI: **Operator-Sichtung** (kein append-only Beleg existiert — ehrlich so vorregistriert) | 3/3 automatisch + 1 manuell |
| 3 ≥ 5 autonome Trades | `trade_outcomes` `status='CLOSED' AND provenance='autonomous'` im Fenster | Zahl |
| 4 Heartbeat ok ≥ 8/10 | `research_health.jsonl` `measurement_heartbeat.ok` je Tag | Zahl |
| 5 ≤ 5 CRITICAL / 24 h nach OPEN | `run_scheduler.log` CRITICAL-Zeilen im 24-h-Fenster ab jedem `trade_outcomes.open_ts` | max |
| 6 Budget nie vor 17:30 leer | `llm_usage.json` Tages-Σ (Berlin-Tag wie `budget.py`) und Zeitpunkt des Erreichens von 300 k; **Report bricht ab**, wenn die Datei nicht parst oder ihre Zeilenzahl nicht wächst (Budget fällt sonst still offen) | 0 Tage |
| 7 Caps unverändert | `starting scheduler daemon (…max_trades=5, daily_loss_cap=1800.0…)`-Zeile + `trade_outcomes.account='demo'` | exakt |

Ausgabe: JSON auf stdout + `data/reports/autonomy_<day>.json` (`.gitignore` +`data/reports/`);
`--summary` bewertet die sieben Zeilen `PASS/FAIL` mit Zahl. **Kein LLM, keine Netzaufrufe,
kein `pgrep`** (Momentaufnahmen sind kein Beleg).
Tests (`phase16_activation/tests/test_autonomy_report.py`): Fixture-DB per
`Database(tmp).run_migrations()` + eingefügte Zeilen → Tagesbericht-Felder; Summary-Bewertung
mit synthetischen 10 Tagen (PASS) und einem Restart-Tag (FAIL Kriterium 1).

#### E3 — Runbook Start (Operator, P13/P14)

```bash
bash scripts/restart-services.sh status            # alles dead nach B2, sonst stop
bash scripts/restart-services.sh start
cat /proc/$(pgrep -f "python -m scheduler.run")/cmdline | tr '\0' ' '     # keine Flags = volles Profil
grep "starting scheduler daemon" data/state/run_scheduler.log | tail -1
```

Day-0-Checks (nach 30 min, dann Tag 1): `bars WHERE source='ls'` > 0 (erster LS-Live-Lauf) ·
`paper_trades` neue Zeilen · `source_spend kind='sample'` neue Zeilen · Preflight läuft ohne Schema-Fehler durch (Floor 9 erfüllt) · `instrument_universe` ohne `SUN*` in `active` · Heartbeat Tag 1 `ok` ·
`llm_usage` Tages-Σ < 300 k und `last_research_ts` ≥ 17:25 · `cache_read_input_tokens` (C3b-Regel).

#### E4 — Tagesroutine + Closeout

Täglich: `autonomy_report.py --day` (Nikinger oder Cron, 0 Kosten). Nach Tag 10: `--summary`,
Closeout-Handover `phase16_activation/PHASE16_CLOSEOUT_HANDOVER.md` nach `docs/HANDOVER_PROMPT.md`
(BLUF, Bilanz, Bild `docs/architecture/phase16_activation.svg` 1080×1080, offene Entscheidungen),
Status-Pflege root-CLAUDE/ROADMAP/README/INDEX, Session-Rotation.

**Block-E-Commits:** 2 (E1+E2 · Closeout).

---

## §7 Akzeptanzkriterien

| AK | Kriterium | Beleg |
|---|---|---|
| **AK1** | Step-0-Ritual protokolliert (auch No-Op) | Phasenkopf A-1 |
| **AK2** | Σ-Baseline **1843** vor dem ersten Fix gemessen; jeder Block endet mit Σ ≥ Vorblock | Phasenkopf-Tabellen |
| **AK3** | Die vier falschen Doku-Behauptungen (§6 A-3) tragen datierte Korrekturen; `LiveQuoteCache`-Items geschlossen | `grep -rn "automatisch an (Schema heute v7)" CLAUDE.md` leer |
| **AK4** | `assert_schema_floor` wirft bei v7 mit `init_db.py` im Text, passt bei v9; `REQUIRED_SCHEMA_VERSION == 9`; Live-DB `_schema_version` = **9**, `instincts` existiert, `trade_outcomes.last_resolve_attempt_utc` existiert; **kein** `run_migrations()`-Aufruf in `wiring.py` | 3 Tests B1 + Operator-SQL B2 + `grep -n run_migrations phase8_scheduler/scripts/wiring.py` leer |
| **AK5** | `SchedulerConfig()` ⇒ `enable_shadow_schedule/divergence_sampler/bar_stream/paper_debate` alle `True`; `config_from_args(parse_args([]))` ebenso; `--no-*` flippt; `python -m scheduler.run --help` zeigt **keine** `--enable-*`-Flags mehr | `test_default_profile_is_fully_armed` + 4 Flag-Tests + `--help`-Grep |
| **AK5b** | `_RebuildingBarStream.restart()` baut den LS-Client mit den **aktuellen** Broker-Tokens neu; Live: nach der ersten Token-Rotation im Test weiter `source='ls'`-Bars, kein `bar stream restart failed` | 2 Tests D1.2 + Day-1-SQL |
| **AK6** | `RescueConfig().enable_gap_rescue is False` unverändert; `test_enable_gap_rescue_is_NOT_in_scheduler_config` grün | P6 (Regressions-Pin, kein bauender Step — bewusst) |
| **AK7** | `build_context` mit 8 Trades, davon 6 älter als 14 Tage ⇒ 2 im Prompt; `recent_trades_max_age_days=None` bit-identisch; System-Prompt enthält den C2-Satz | P4-Tests |
| **AK8** | `daily_token_budget` Default 300 000 in Config **und** CLI; `test_webui` Prozent-Pin auf 0.6 | P8-Tests |
| **AK9** | `is_weekend_market` 5/5; Discovery zählt `weekend_market`; Promotion demotet aktive `SUN*` und promotet nie eines; live nach erstem Refresh: 0 `SUN*` in `active` | P9-Tests + `instrument_universe`-SQL |
| **AK10** | Bridge: Close ⇒ `instinct_hook` genau einmal, Exceptions gekapselt; Compiler: Grammatik ⇒ Prädikat, sonst `None`; `longterm_rules == ()` bei 0 promoted (AK9-Erbe grün) | P15/P7/P5-Tests |
| **AK11** | `MarketInfo.margin_factor` aus `marginFactor` extrahiert; Sizing-Grenzfall 27 100 / 24 500 / mf 5 ⇒ 21,0; `mf=None` ⇒ heutiger Cap | P1/P5-Tests |
| **AK12** | `run_webui.sh` mit `--no-access-log`; `run_webui.log` wächst < 1 MB/Tag nach Restart | `ls -l` Tag 1 |
| **AK13** | Vorregistrierung committet **vor** dem E3-Restart (Commit-Zeit < Start-Zeile im Log) | `git log` vs. `run_scheduler.log` |
| **AK14** | `autonomy_report.py --day` läuft offline gegen Fixture; `--summary` bewertet 7 Kriterien | P16-Tests |
| **AK15** | **2-Wochen-Test PASS** = alle sieben (Messquellen §6 E2): (1) genau eine Start-Zeile je Dienst im Fenster (≥ 10 Handelstage ohne Operator-Restart; P17-Ausnahme einmal Backoff-KILL) · (2) Scheduler/Recorder/Discovery an jedem Handelstag mit append-only Beleg aktiv + WebUI operator-gesichtet · (3) ≥ 5 autonome open→close-Trades · (4) Heartbeat `ok` an ≥ 8/10 Tagen · (5) ≤ 5 CRITICALs in den 24 h nach jedem OPEN (A6) · (6) Token-Budget an 0 Tagen vor 17:30 erschöpft · (7) Daily-Loss-Cap/`max_trades`/Demo unverändert | `--summary` |
| **AK17** *(nur mit P3-Freigabe)* | leerer yF-Frame öffnet den Circuit **nicht**; `RateLimitError` weiterhin; live: 0 `circuit open`-Zeilen um 09:05–09:20 an Tag 1 | P3-Tests C5 + Log-Grep |
| **AK16** | Closeout-Handover + SVG + INDEX + Status-Pflege in einem Commit; Phasenkopf trägt genau einen Session-Block; `check_doc_rotation.py --strict` exit 0 | E4 |

---

## §8 Fehlgriffe, die wie andere Fehler aussehen (Symptom → erster Verdächtiger)

| Symptom | Erster Verdächtiger | Zweiter |
|---|---|---|
| Heartbeat nach D1 weiter CRITICAL „measurement arm off" | Bot nicht neu gestartet (`sys.modules`-Cache) — `/proc/<pid>/cmdline` + Startzeit prüfen | `--no-shadow-schedule` in einem Wrapper/Alias |
| `sqlite3.OperationalError: database is locked` beim Scheduler-Start | B1 lief bei laufendem Discovery-Daemon → `restart-services.sh` Reihenfolge; B2 hätte vorher mit allen Diensten aus laufen müssen | WebUI hält `mode=ro`-Handle offen (harmlos) |
| Research abstained nach C1 weiter 100 % | Log-Zeile `context built` zeigt noch 8 Trades ⇒ Fenster greift nicht (`close_ts`-Format `+02:00` vs `Z`) | Dann ist es „on merit" — 09:05-Breaker (L9) oder alle Epics `not TRADEABLE` |
| Token-Budget trotzdem vor 17:30 leer | `cache_read_input_tokens` 0 ist **erwartet** (C3b); Budget-Default in **beiden** Stellen (Config + CLI) geflippt? | Council-Paper-Call (3 Debatten/Tag) + Reflect-Cap 10 addieren ~40 k |
| VETO 5 vetoet jeden Kandidaten | `reason="rule[i] raised"` ⇒ Prädikat wirft (Kandidat ohne `direction`-Key) | `rule[i] vetoed` ⇒ eine `avoid BUY`-Regel ohne Epic wurde promotet — prüfen, ob n≥50 wirklich erreicht |
| `ERROR yfinance … possibly delisted` um 09:05 bleibt nach C5 | Das sind die Retry-**WARNINGs**; Erfolg misst man an `circuit open`-Zeilen, nicht an `delisted` | `open_after` weiterhin über `RateLimitError` erreicht (echter 429) |
| Sizing liefert 0 nach D3 (`below_min_deal_size`) | `marginFactor` in Prozent statt Bruch interpretiert (5 vs 0,05) — Unit-Check | `margin_headroom` 0,95 mit `min_deal_size` 0,5 bei kleinem Konto |
| Universe schrumpft nach B3 auf < 5 | `is_weekend_market` matcht zu breit (Name-Marker) — `filtered["weekend_market"]`-Zähler im Log | `max_active` 8, aber `verified`-Kandidaten haben `fail_count` > 0 (Backoff) |
| `RATE_LIMIT`-Aborts in den ersten Zyklen nach Restart | Bekannt, selbstheilend ab Zyklus 2 (Startup-Refresher frisst Request-Allowance) | Shadow-Schedule (130 Quote-Calls/Tag) + Sampler gleichzeitig am Start → Intervall 30→60 nur wenn es **nach** Zyklus 3 anhält |
| `bars.source='ls'` bleibt 0 nach E3 | `bar stream build failed` / `start failed` CRITICAL im Log — LS-Token vom Broker-Login (`broker._cst`) | `measurable_universe()` leer (Registry `ok`-Zeilen) |
| Bridge: 0 `instincts`-Zeilen nach erstem Close | `instincts`-Tabelle fehlt (B2 nicht gelaufen) → `insert_instinct` wirft, Hook loggt CRITICAL | Extractor `ok=False` (Schema-`pattern` zu streng) — `instinct.extract failed` im Log |
| `git push` rejected | `origin/main` hat sich bewegt (andere Maschine) — nie `--force` | — |
| Daemon startet nach Block D nicht: `PreflightError … schema … version 7 < required 9` | **Gewollt** — B2 (Operator-Apply) noch nicht gelaufen; nicht den Floor senken | `init_db.py` gegen falschen Pfad gelaufen (Default ist `data/trading_bot.sqlite` relativ zum Repo-Root — `pwd` prüfen) |
| `bar stream restart failed` / LS-Bars enden nach einigen Stunden | D1.2-Wrapper nicht verkabelt (Z. 1131 gibt noch `recorder` statt Wrapper zurück) | IG-Token-Rotation ohne `_warm_session`-Aufruf (Runner-Pfad) — `restart` wurde nie gerufen |
| Test-Kriterium 1 FAIL, obwohl niemand etwas tat | `data/state/KILL` mit `auto:backoff` — drei Zyklus-Exceptions in Folge; das Traceback der **ersten** ist der Befund | Reboot (`last reboot`) |

---

## §9 „Bei Ausführung verifizieren" — vollständige Liste

Was hier **nicht** steht, gilt als geprüft (Stand 2026-09-05).

1. **IG-Margin-Felder** (`instrument.marginFactor`, `marginFactorUnit`, `marginDepositBands`) — nur per Live-Probe D3.0 bestätigbar. Erwartung `PERCENTAGE`.
2. **Phase-4-Tests, die `_SYSTEM_PROMPT` oder den Trades-Header pinnen** — grep 2026-09-05 auf `When in doubt` / `Recent trades (newest` in `phase4_research/tests/` war leer; vor C2 nochmals prüfen.
3. **Weitere Pins auf `200_000`** außerhalb `test_run.py:20,52`, `test_config.py:39`, `test_webui.py:338-348` (gefunden 2026-09-05) — `grep -rn "200_000\|200000" --include=*.py` vor C3.
4. **Wo der B1-Source-Pin lebt** (root `tests/` importiert `scripts.wiring`? sonst P8 `tests/`) — der Import darf offline kein Broker-Modul ziehen; `inspect.getsource` auf die Funktion, nicht auf das Modul.
5. ~~Attributname der Validator-Entscheidung~~ — **geprüft 2026-09-05 (Sonnet-Cold-Read): `InstinctValidation.decision`**; `Instinct.__post_init__` akzeptiert list/tuple-IDs.
6. **Exakte Zeile des Extractor-Prompt-Satzes** (`extractor.py` ~172, `f"Felder trigger (string), domain (eines von: {domain_list}), "`) und ob das JSON-Schema `pattern` bereits in `_build_instinct_prompt` Z. 44-70 gesetzt werden kann, ohne `_coerce_instincts` zu brechen.
7. **`test_webui.py`-Tests, die die `SchedulerConfig()`-Konstruktion aus `api.py:75` implizit pinnen** (Loss-Cap-Anzeige?) — vor A-4.
8. **Welche Phase-3-Tests die Circuit-Öffnung über `DataUnavailableError` pinnen** (`grep -n "record_failure\|CircuitOpen" phase3_external_data/tests/`) — nur relevant, falls C5 freigegeben wird.
9. **Offline-Smoke** `phase8_scheduler/scripts/smoke_test.py` läuft nach D1 noch 3/3 (die Fakes bauen ggf. `SchedulerConfig` mit Annahme „Arme aus").
10. **AEX/MIB/STXE-`point_value` in `instrument_universe`** stimmen (40 / 1 / 2) **und** landen über `_build_universe_from_db()` in `ExecutionConfig.point_values` — sobald sie nach B3 aktiv werden, sonst `point_value_unmapped` (fail-closed, kein Schaden, aber 0 Trades auf diesen Epics).
11. **Einziger Aufrufer von `_build_reward_sink`** ist `build_scheduler` (grep vor D2.6; `live_test.py`?).
12. **Import-Pfad des Report-Skripts**: `persistence` ist im gemeinsamen venv editable installiert (`dev_install.sh` 13 Schritte) — sonst `sys.path`-Insert wie `run.py:199`.
13. **`ROADMAP.md` < 40 KB nach dem Phase-16-Abschnitt** (heute 39 109 B) — ggf. Phase-9-Absatz kürzen, datiert.
14. **`UniverseRecord.name` der drei aktiven `SUN*`-Rows ist gesetzt** (SQL 2026-09-05: ja, „Wochenend-…") — das Epic-Muster `.SUN` fängt sie ohnehin.
15. **`InstinctValidator()`-Default `min_evidence`** (`validator.py:91`, `MIN_EVIDENCE`) passt zu n≈10–20 Trades im Test — sonst bleiben alle Instincts `proposed` (kein Fehler, aber Vorregistrierung soll die Zahl nennen).
16. **Anthropic-Modell des Extractors**: Haiku-Client aus `_build_reward_sink` (`cfg.lesson_model = claude-haiku-4-5-20251001`) — Cache-Minimum 4096 Tokens, Caching dort irrelevant.
17. **`TickAggregatorRecorder` hat kein `restart()`** (`stream.py:353-385`: nur `start`/`stop`; `restart` existiert nur auf `LSBarRecorder` Z. 117) — der Runner nimmt dann `stop()+start()` auf demselben Objekt. Der D1.2-Wrapper liefert `restart` selbst; prüfen, dass `stop()` des inneren Recorders idempotent ist (Z. 378-385 sieht so aus).
18. **Wie oft rotiert IG das Token im Live-Betrieb** (`_warm_session`-Aufrufe `runner.py:381-433`, Log `session re-warmed`?) — bestimmt, ob AK5b am Tag 1 oder erst später beobachtbar ist.
20. **`build_scheduler`-Reihenfolge für D2.6**: `preflight_fn` (Floor) läuft erst in `runner.preflight()`; `instinct_bridge.promote()`/`load_rules()` in `build_scheduler` würden auf v7 **vor** dem Floor die fehlende `instincts`-Tabelle treffen → beide Aufrufe müssen `sqlite3.OperationalError` fangen und `()` liefern (WARNING), oder in den Preflight-Pfad nach dem Floor wandern. Vor D2.6 entscheiden; Test pinnt das Verhalten auf einer v7-DB.
19. **Start-Zeilen-Muster der vier Wrapper** für Kriterium 1 (`run_scheduler.log` „starting scheduler daemon" ✓ gemessen 6×; `run_recorder.log` „[run_recorder] starting" ✓; `run_discovery.log` / `run_webui.log` „Started server process" — vor E2 nachgreppen).

---

## §10 Out-of-Scope (Phase 16 baut das **nicht**)

| Was | Warum nicht |
|---|---|
| Strategie-/Edge-Bewertung (BUY-Bias, DAX-only, R:R 1,5, 2 W : 6 L) | Phase 16 stopft Infrastruktur; Watch-Item der Vorregistrierung, Auswertung im Closeout |
| Research-Dedupe / Zyklus-Streckung | Quotes im Prompt variieren je Runde (C4); Budget 300 k löst den Tag |
| `enable_gap_rescue` Default | P6 — Kostenentscheidung Phase 13/14, bleibt Operator-Tool |
| Auto-Gap-Fill-Scheduler (D16), Dukascopy (D15), Pfad B | P15 §10, unverändert |
| Force-Trigger bauen | existiert nicht; Hard Rule 5 bleibt Vorschrift |
| Log-Rotation über `--no-access-log` hinaus | `run_scheduler.log` 120 KB/Tag — kein Problem in 2 Wochen |
| Zombie-Prozesse 124576/124577 | kein Schaden, Ursache unbekannt — im Test beobachten (Anzahl darf nicht wachsen) |
| Prozess-Supervision (systemd-User-Unit, Auto-Restart nach Reboot, Keyring ohne Login) | Opus-Review §13 #5: reale Lücke, aber eine eigene Betriebs-Phase (Phase 17-Kandidat); im Test per P17 ehrlich als Grenze vorregistriert |
| Research-Prompt-Caching (`cache_system=True`) | P3: strukturell wirkungslos für das Budget (Meter zählt Cache-Reads voll) und Präfix < 1024 Tokens |
| Council-Integration 15a als Pipeline-Input | Nikinger 2026-08-31; der Council-**Paper**-Call wird über D1 scharf, das reicht |
| Live-Account | Hard Rule 4; Demo bleibt |

---

## §11 Operator-Aktionen (Nikinger, nicht die Exec-Session)

| # | Wann | Was | Kosten |
|---|---|---|---|
| 1 | A-5 | `git push origin main` | — |
| 3 | B2 | Stop aller 4 Dienste → Backup → `init_db.py --db-path data/trading_bot.sqlite` → SQL-Verify v9 | — |
| 4 | D3.0 | `probe_market_margin.py` für 3 Epics (Demo) | 3 Requests, 0 Datenpunkte |
| 3b | B2 | Ledger-Restore SQL (mit gestopptem Recorder, §6 B2) | — |
| 5 | E3 | `restart-services.sh start` + Day-0-Checks; Desktop-Session eingeloggt lassen (Keyring); **kein** Reboot im Fenster | Shadow ~130 Quote-Requests/Tag · Sampler ~120 IG-Punkte/Woche (Budget-Rest 9 671) · Council 3 Sonnet-Debatten/Tag ≈ 0,10 $ · Research bis 300 k Tokens ≈ 1,20 $/Tag |
| 6 | täglich | `autonomy_report.py --day` lesen; **nichts** anfassen | — |
| 7 | Tag 10 | `--summary`, Closeout-Session | — |

---

## §12 Commit-Konvention

`phase16: <imperative>` — ein logischer Schritt pro Commit. Cross-Phase-Touches nennen beide
Scopes (`phase16+phase8: …`), wie `6065e6c phase15+phase5:`. Jede neue `.md`/`.svg` bringt ihre
`docs/INDEX.md`-Zeile im selben Commit. Blockweise: A 3 · B 2 · C 3 · D 5 · E 2 + Closeout.

---

## §13 Advisor-Review (P16) — Opus-Plan-Agent, 2026-09-05 (read-only, 29 Tool-Calls)

| # | Review-Befund | Selbst verifiziert? | Konsequenz im Plan |
|---|---|---|---|
| 1 | `run_migrations()` im Daemon kollidiert mit der gelockten Preflight-Entscheidung (`wiring.py:1070-1071`) und riskiert `database is locked` (`journal_mode=delete`, kein `busy_timeout`, `executescript` = EXCLUSIVE) | ✅ beide Zeilen + `PRAGMA journal_mode` gelesen | **B1 umgebaut** auf Schema-Floor; P8 neu formuliert |
| 2 | `IGLightstreamerClient` snapshottet CST/XST; `_restart_bar_stream` reused das Objekt → nach Token-Rotation auth-tot, 1 CRITICAL/Rotation | ✅ `ig_lightstreamer.py:232-233,256`, `runner.py:493-511`, `wiring.py:1103-1108` | **D1.2 neu** (Wrapper, P8-only) + AK5b |
| 3 | Caching kann das Budget-Kriterium nicht bewegen: `budget.py:70-75` zählt `cache_read` voll | ✅ gelesen | **C3b gestrichen**, P3 neu formuliert |
| 4 | Dataclass-Default-Flip allein ist No-Op, weil `config_from_args` jedes Feld setzt | ✅ (war im Plan schon so, jetzt explizit in P4) | P4 präzisiert |
| 5 | Keine Supervision (kein systemd/cron), Keyring braucht Desktop-Login; Backoff-KILL (3 Exceptions) ist der einzige Auto-Killer und braucht Hand | ✅ `last reboot`, `crontab -l`, `~/.config/systemd/user`, `runner.py:355-361`, `restart-services.sh:22`; Auto-Reboot ist **aus** | **P17 neu** (erlaubte Operator-Ereignisse vorregistriert); Supervision als Phase-17-Material in §10 |
| 6 | Aliveness-Kriterien unmessbar aus `*_state.json` (in-place) | ✅ | **E2 umgebaut** auf append-only Quellen; AK15 neu formuliert; WebUI ehrlich „operator-gesichtet" |
| 7 | Ledger-Restore trifft `bars.sqlite`, dessen Live-Schreiber der Recorder ist | ✅ | A-5 → **B2** verschoben |
| 8 | Prädikat-Compiler sei unerreichbarer Code (n=8+5 ≪ 50) → weglassen oder nur Dict-Lookup, nie Freitext parsen | teils: Unerreichbarkeit im Test stimmt; „Freitext" stimmt **nicht** mehr, sobald das Extractor-Schema `pattern` erzwingt (D2.3) | **Beibehalten** (Nikinger #6: Bridge komplett; der Compiler ist das letzte Glied, per Tests erreichbar, VETO 5 bleibt fail-closed). Dissens hier dokumentiert |
| 9 | `llm_usage.json` fällt bei Korruption offen | ✅ (`budget.py` `_load_log`) | E2 Regel „Report bricht ab, wenn Datei nicht parst / nicht wächst" |
| 10 | Log-Retention für CRITICAL-Kriterium | n/a — `run_scheduler.log` ist append-only ohne Rotation (120 KB/Tag), A-4 betrifft nur das WebUI-Access-Log | keine Änderung |

**Netto:** drei Struktur-Änderungen (B1, D1.2, E2), zwei Streichungen (C3b, Ledger aus A-5), ein
Dissens (Compiler). Kein Block wurde hinzugefügt oder entfernt.

**Sonnet-Cold-Read (P16, zweiter Checkpoint, 2026-09-05, 33 Tool-Calls):** alle §3/§5/§6-Anker
per `grep -nF` nachgeprüft — 8 Korrekturen eingearbeitet (mehrzeilige Aufrufe in `ig_adapter.py`
und `wiring.py` verbatim gemacht; `gates.py` nutzt `.get`; `context_builder.py:135` ist ein
`%s`-Format; `max_active=8` ist ein Signatur-Default; root-`CLAUDE.md`/`ROADMAP.md`-Zeilen um die
Plan-Session-Einfügungen verschoben), `InstinctValidation.decision` verifiziert, D2.6-Einfügepunkt
auf `wiring.py:832` festgelegt, D3.2-Aufrufkette (`executor.py:321-324`, kein Caller-Touch)
ergänzt, §4 um die Fremd-Phasen-Doku-Vermerke aus A-3, §7 um AK17 (C5) und §9 um #20 erweitert.


---

> **Stand:** 2026-09-05, Plan-Session (Claude Code, Fable 5.1). Σ-Baseline 1843, HEAD `2f9eb82`
> + 7 ahead. **Nächste Aktion:** Exec-Session (Sonnet 5) startet mit **Block A, Step A-0**;
> Operator-Aktionen 1–2 sind freigegeben und können sofort laufen.
