---
status: active-phase
purpose: PHASE-HEAD, Phase 16 (Freischaltung) — 🔄 eröffnet 2026-09-05 (Plan-Session, Fable 5.1). Mission = jedes gebaute Feature läuft, jeder bekannte Bruch ist zu, ein vorregistrierter 2-Wochen-Lauf beweist Autonomie ohne Hand. Kern-Befund: der Bot ist seit 2026-08-31 faktisch tot (100 % Research-Abstain, 77/Tag) — Ursache Infrastruktur (Historien-Tabelle ohne Zeitfenster), nicht Strategie; dazu Token-Budget täglich um 15:48 leer, Live-DB auf Schema v7 (Migrations nie angewendet, Doku behauptete das Gegenteil), Flags nicht restart-fest, 3 Wochenend-Epics im Universum.
read-when: jede Phase-16-Session; zuerst den neuesten `## Session stopped`-Block, dann den Plan-Step, der dran ist
detail: L1
up: ../CLAUDE.md
down:
  - ../docs/concepts/phase16_activation_plan.md   # 📕 der Plan (P1–P18, L1–L9, Blöcke A–E, AK1–AK17, §9 Drift, §13 Reviews)
  - ../phase15_v4/PHASE15_CLOSEOUT_HANDOVER.md    # 📕 Vorgänger-Handover (E1–E3 werden hier geschlossen)
  - ../phase7_reward/PHASE12_RECONCILIATION_TIMING_PLAN.md   # 📕 A6 hängt an Migration 008
  - ../phase5_execution/CLAUDE.md                 # B3-Block → Plan D3
  - ./SESSIONS_ARCHIVE.md                         # 📦 Session-Block-Historie (newest-first, A-0 angelegt)
updated: 2026-09-07 (+ Exec-Session #16 → Archiv; Exec-Session #17 schließt ab: Block-E-Pre-Step **Option B** — Import-Smoke-Test für `scripts/wiring.py` [`phase8_scheduler/tests/test_wiring_reward_sink.py` NEU, 3 Tests, P8 256 → 259, Σ 1921 → **1924**] + **Hotfix #3** `wiring.py:404-405` [`intinct_extractor`/`intinct_validator` → `instinct_*`, 2 Zeichen, der VIERTE und letzte D2.6-Regression-Bug aus Commit `bfab841`; `grep -c intinct wiring.py` == 0 ⇒ Typo-Familie erschöpft], Test+Fix in EINEM GREEN-Commit `0cfcd6e`; erstmals der ganze `bfab841`-Diff enumeriert statt Restart-für-Restart: **3 Hunks, 6 Fehler in 5 Zeilen** [nicht 4], Hunk 3 `build_scheduler:888-890` gegen Code verifiziert und KORREKT [promote/load_rules/longterm_rules existieren, kein Bug #5]; Cross-Phase-Freigabe P8 per Phase-16-Plan §4 (Nikinger 2026-09-05), Phase-15-Code nur gelesen, Hard Rule 3 unangetastet; Exec-#16-Block verbatim nach SESSIONS_ARCHIVE.md rotiert [17. Eintrag]; Block E [E1 ✅, E2 ✅, E3 docs v2 ✅, Phase-15-install ✅, Hotfix #1 ✅, Hotfix #2 ✅, **Pre-Step Smoke-Test + Hotfix #3 ✅**] ⇒ offen: Scheduler-Restart #4 durch Nikinger + E4 Tagesroutine+Closeout+SVG; **16** Commits pending lokal ahead of `origin/main` = **`e219a25`** — Korrektur einer seit Session #12 mitgeschleppten Falschangabe, siehe F6 | Σ 1924 erstmals NACHGEMESSEN statt geerbt [voller Sweep; Konvention: `meta_m1_harness/` 28 zählt nicht mit, repo-weit über alles 1952] (F7); 2 bei den Rotationen #14/#15 verlorene `## Session stopped`-Überschriften (Blöcke #13+#14) verbatim aus Git wiederhergestellt ⇒ Archiv jetzt 17 Überschriften, Folge lückenlos (F8); `check_archive_sequence` prüft keine Lücken — Phase-17-Watch-Item (F9 | 2026-09-08: Nikinger-Restart #4 um 09:30:49 ERFOLGREICH — Scheduler laeuft (PID 281715, kein Traceback, K7-Caps-Pin verbatim in der Startzeile), alle 4 Dienste up; die 4er-Bug-Kette aus `bfab841` ist im `run_scheduler.log` lueckenlos belegt und abgeschlossen; NEU als erster Punkt der Folgesession: tiefer repo-weiter Doc-Drift-Audit (Nikinger-Auftrag, 6 read-only Checks aus der F6/F7/F8-Klasse | 2026-09-08 Nikinger-Korrektur: Tag 1 ist **Di** 2026-09-08, nicht Mo (Datum war richtig, Wochentag aus dem Vorgaengerblock geerbt statt berechnet -- dritte Instanz der F6/F7-Klasse; Prereg 6279874 war korrekt); Folgesession-Reihenfolge auf Nikinger-Wunsch: (1) F9-Luecken-Check in check_doc_rotation.py bauen [Cross-Phase-Freigabe P14 hiermit erteilt], (2) danach der tiefe Doc-Drift-Audit; Commits dieser Session gepusht)
---

# Phase 16 — Freischaltung

**Mission in einem Satz:** jedes gebaute Feature läuft, jeder bekannte Bruch ist zu, und ein
vorregistrierter 2-Wochen-Lauf beweist Autonomie ohne Hand.

Der Plan ist execution-ready und direkt an die Exec-Session (OpenCode / MiniMax M3) übergebbar:
[`docs/concepts/phase16_activation_plan.md`](../docs/concepts/phase16_activation_plan.md).
Nichts muss neu hergeleitet werden; was nicht geprüft werden konnte, steht vollständig in Plan §9.

## Die Befunde, die die Phase tragen (alle 2026-09-05 selbst gemessen)

| # | Loch | Schwere |
|---|---|---|
| L1 | Research abstained seit 2026-08-31 zu 100 % — `context_builder.py:251` reicht die 8 jüngsten Trades ohne Zeitfenster, das LLM nennt „6 von 7 Verluste" als Grund; ohne neuen Trade ändert sich nichts (absorbierender Zustand) | 🔴 |
| L2 | Token-Budget 200 k exakt um ~15:48 täglich erschöpft (77 Calls × 2,6 k); Fenster geht bis 17:30 | 🔴 |
| L3 | Live-DB Schema **v7**; Migrations 008 + 009 nie angewendet; **kein** Produktions-Caller von `run_migrations()`; root-CLAUDE/ROADMAP/P15-Handover behaupteten „automatisch beim Restart" — falsch. Reconcile-Backoff (P7/A6) damit nicht live | 🔴 |
| L4 | Scheduler läuft ohne Flags; `restart-services.sh` übergibt keine → jeder Restart verliert die Arme; Heartbeat täglich CRITICAL | 🟠 |
| L5 | 3 Wochenend-Epics (`IX.D.SUN*`) aktiv, unter der Woche `EDITS_ONLY`, kosten 10 von 13 IG-Research-Fetches/Tag | 🟠 |
| L6 | Promotion-Bridge fehlt (kein Aufrufer für Extractor/Validator/Promotion, VETO 5 dauerhaft No-Op) | 🟡 |
| L7 | B3 Margin-Headroom (Leverage-Cap bindet, IG lehnt Grenzgrößen ab) | 🟡 |
| L8 | WebUI-Access-Log 16 MB/Tag, keine Rotation | 🟢 |
| L9 | yF-Circuit-Breaker trippt jeden Morgen 09:05 (leerer Frame ≠ Ausfall) — P3 seit Runde 2 frei | 🟢 |

Dazu aus dem Opus-Review (Plan §13): Bar-Stream-Token-Snapshot (Arm wäre nach der ersten
IG-Token-Rotation tot) und die fehlende Prozess-Supervision (vorregistriert als Grenze, nicht Fix).

## Blöcke

| Block | Inhalt | Gate |
|---|---|---|
| **A** | Haushalt: Step-0-Ritual · Σ-Baseline **1843** · Code↔.md-Sweep · WebUI-Log · Push | keins |
| **B** | Substrat: Schema-Floor im Preflight + Operator-Apply (v9) + Ledger-Restore · Wochenend-Filter + Demotion | nach A |
| **C** | Research-Loop: Historien-Fenster 14 d · Budget 300 k · Breaker-Semantik (P3, Runde 2) | nach B |
| **D** | Freischaltung: Defaults ON + `--no-*` · Bar-Stream-Token-Wrapper · Promotion-Bridge + Compiler · Margin-Headroom nach Live-Probe | nach C |
| **E** | 2-Wochen-Autonomie-Test: Vorregistrierung · `autonomy_report.py` · Runbook · Closeout | nach D + Restart |

**Cross-Phase-Freigabe (Nikinger 2026-09-05):** P1, P2, P3 (Runde 2), P4, P5, P7, P8, P9, P15 — nur
wo ein Step sie braucht. P6/P10/P12/P13/P14 unangetastet.

**Nikinger-Entscheidungen der Plan-Session (2026-09-05, Runde 1):** 1 Name `phase16_activation` ·
2 L1 = Fenster 14 d + 8 + Prompt-Satz · 3 Budget 300 k (Caching gestrichen, Plan §1 P3) · 4 alle
vier Arme Default ON, Philosophie „AUS braucht ein Flag" · 5 Wochenend-Filter + Demotion · 6 Bridge
jetzt, „keine Code-Leichen" · 7 B3 rein, Live-Probe zuerst · 8 PASS-Kriterien wie vorgeschlagen ·
9 Cross-Phase-Liste · 10 Operator-Aktionen freigegeben.

## Modul-Tabelle (Soll — wird von der Exec-Session zur Ist-Tabelle)

| Modul | Zweck | Step |
|---|---|---|
| `scripts/autonomy_report.py` | deterministischer Tages-/Summary-Report aus append-only Quellen, `mode=ro`, kein LLM | E2 |
| `tests/test_autonomy_report.py` | Fixture-DB + synthetische 10 Tage | E2 |
| `PHASE16_AUTONOMY_PREREGISTRATION.md` | 📕 PASS-Kriterien + erlaubte Operator-Ereignisse, **vor** dem Start committet | E1 |
| `PHASE16_CLOSEOUT_HANDOVER.md` + `docs/architecture/phase16_activation.svg` | Closeout nach Tag 10 | E4 |
| *(Cross-Phase)* `phase15_v4/instinct/bridge.py`, `compile.py` | Promotion-Bridge + Prädikat-Compiler | D2 |
| *(Cross-Phase)* `phase1_broker_wrapper/scripts/probe_market_margin.py` | Operator-Live-Probe für B3 | D3.0 |

---
## Session stopped — 2026-09-07 (Opus-5-Exec-Session #17, Block E Pre-Step Option B: Import-Smoke-Test für `scripts/wiring.py` + Hotfix #3 `wiring.py:404-405` — der **vierte und letzte** D2.6-Regression-Bug, Σ 1921 → **1924** grün [P8 256 → 259, +3 neue Tests] — Σ erstmals seit Sessions #14-#16 **nachgemessen** statt geerbt, siehe F7, Exec-#16-Block verbatim nach SESSIONS_ARCHIVE.md rotiert [17. Eintrag, +1 vs. Stand Session #16], **16** Commits pending lokal ahead of `origin/main` = **`e219a25`** — Korrektur einer seit Session #12 mitgeschleppten Falschangabe, siehe F6)

> **Auftrag:** Nikinger-Chat 2026-09-07 (Fortsetzung Session #16, „Scheduler-Restart #3 nach Hotfix #2"): Hotfix #2 war erfolgreich (Scheduler kam über Z. 400 hinaus), aber **vierter Blocker** auf Z. 404: `NameError: name 'intinct_extractor' is not defined`. Der Auftrag war diesmal ausdrücklich **nicht** „fix den Typo", sondern **Option B**: den strukturellen Grund abstellen, dass jede `wiring.py`-Edit ungetestet committet wird. Vier Liefer­artefakte verlangt (Test-Skeleton mit Fakes, vollständiger Diagnose-Bericht mit Phase-15-Signatur-Beleg, atomarer Fix-Plan RED→GREEN, Verifikation ohne Σ-Regression).
>
> Plan-Anker: [`../docs/concepts/phase16_activation_plan.md`](../docs/concepts/phase16_activation_plan.md) §6 E3 + §13 · Phase-16-Phasenkopf Session-#16 Watch-Item („dringend: Import-Smoke-Test für `scripts/wiring.py`") · `phase15_v4/instinct/{bridge,extractor,validator}.py` (Signatur-Beleg) · `phase8_scheduler/tests/test_wiring_schema_floor.py` (Test-Vorbild) · Cross-Phase-Freigabe P8 per Plan §4 (Nikinger 2026-09-05).
>
> Ausführungs-Scope: **1 Atomic Code-Commit** (`0cfcd6e phase16+phase8: test+fix -- Hotfix #3 wiring.py:404-405 + Import-Smoke-Test`) + dieser Session-Rotation-Commit. Push-Freigabe-Stand: Nikinger hat zwischen #16 und #17 0 Commits gepusht.

### Completed

- **Vollständige `bfab841`-Enumeration statt Restart-für-Restart-Entdeckung.** Erstmals wurde der Commit als Ganzes gelesen (`git show bfab841 -- phase8_scheduler/scripts/wiring.py`) statt nur die Zeile aus dem letzten Traceback. Ergebnis: **3 Hunks**, nicht 1. Hunk 2 (`_build_reward_sink`, 5 neue Zeilen) enthielt **6 Fehler**; Hunk 1 (`_make_debate_runner`-Kontext) und **Hunk 3 (`build_scheduler:888-890`)** waren bis dahin nie geprüft worden. `grep -c intinct phase8_scheduler/scripts/wiring.py` == **0** nach diesem Commit ⇒ die Typo-Familie ist repo-weit erschöpft.
- **Hunk 3 gegen den Code verifiziert — KORREKT, kein Bug #5.** `instinct_bridge.promote()` existiert (`phase15_v4/instinct/bridge.py:174`), `load_rules()` existiert (`bridge.py:205`), `ExecutionConfig.longterm_rules` existiert (`phase5_execution/execution/config.py:119`), alle 4 `from instinct import`-Namen werden von `instinct/__init__.py` exportiert (im Ziel-venv nachgeladen, nicht nur gelesen).
- **`phase8_scheduler/tests/test_wiring_reward_sink.py` NEU (3 Tests, P8 256 → 259).** RED vor dem Fix verifiziert — alle 3 Tests scheiterten mit exakt dem `NameError` aus dem Operator-Log, nicht mit einem Ersatz-Fehler.
- **Hotfix #3 `wiring.py:404-405`:** `intinct_extractor` → `instinct_extractor`, `intinct_validator` → `instinct_validator` (2 Zeichen, 2 Zeilen). **Test und Fix im selben Commit** (GREEN), kein RED-Commit — Repo-Regel „ein Subtask ist nicht fertig, bis seine Tests grün sind".
- **Verifikation:** `pytest phase8_scheduler/tests -q` = **259 passed** (vorher 256, +3 neu, 0 regressiert); `scripts/check_doc_rotation.py --strict --quiet` exit **0** nach Code-Commit und nach dieser Rotation.

### Findings

- **F1 — `bfab841` hatte 6 Fehler in 5 Zeilen, nicht 4 in 5.** Die Session-#14/#15/#16-Blöcke zählten „3 Bugs", weil jeder Restart genau einen aufdeckte. Der Diff zeigt **fünf** `intinct`-Typos (nicht drei) plus die falsche Extractor-Signatur. Zwei der fünf verschwanden als Nebenwirkung: Hotfix #1 fixte `cfg=intinct_cfg` in `InstinctBridge(...)`, Hotfix #2 löschte `cfg=intinct_cfg` im Extractor-Call komplett weg. Übrig blieben die zwei, die diese Session schließt. **Lesson:** ein Traceback nennt genau einen Namen; ein Diff nennt alle. Bei einem Commit, der schon zweimal zurückgeschlagen hat, ist der Diff die billigere Quelle.
- **F2 — der Test-venv und der Daemon-Runtime-Pfad sind dieselbe Umgebung, und nichts testete das.** `python -c "import reward, research, instinct"` läuft im `phase1_broker_wrapper/.venv` durch. Das ist erst seit dem Session-#14-editable-install so. Dieser Install war damit **load-bearing** für den Daemon-Start, ohne dass ein einziger Test ihn abgesichert hätte — Bug #1 wäre nach einem venv-Rebuild kommentarlos zurückgekehrt. Der neue Test importiert `instinct` über `_build_reward_sink` und schlägt fehl, wenn der Install fehlt.
- **F3 — jeder Konstruktor der `_build_reward_sink`-Kette ist reines Attribut-Binden.** Nachgemessen 2026-09-07 an `LLMClient.__init__` (llm_client.py:246-259, SDK explizit lazy: `self._client = None`), `Scorer` (scorer.py:84), `Brain` (brain.py:184), `RewardSink` (recorder.py:189-199), `SingleShotInstinctExtractor` (extractor.py:262), `InstinctValidator` (validator.py:95), `InstinctBridge` (bridge.py:97-103). **Deshalb** ist der Smoke-Test billig: der einzige unreine Call in der ganzen Funktion ist der Keyring-Read. Das ist die Eigenschaft, die Option B überhaupt erst praktikabel macht — sie gilt nicht automatisch für die Geschwister-Builder (siehe Watch-Item).
- **F4 — `promote()` und `load_rules()` schlucken *jede* Exception** (`bridge.py:201` bzw. `216`, beide `except Exception → logger.critical` + leeres Ergebnis). Ein Phase-15-Rename einer der beiden Methoden fiele damit **still** in ein permanent leeres Regelset: VETO 5 wäre tot, `longterm_rules == ()` sähe wie das erwartete AK9-Erbe aus, alle Tests grün. Der dritte neue Test benutzt deshalb ein protokollierendes `_FakeDB` statt eines nackten Sentinels — die Asserts auf die tatsächlich erfolgten DB-Reads unterscheiden den Live-Pfad vom `except`-Arm. Gegen `object()` wären beide Fälle identisch grün gewesen.
- **F5 — Keyring-Stub via `sys.modules`, nicht via Attribut-Patch.** `_build_reward_sink` macht `from reward.credentials import get_credential` **im Funktionskörper**; dieser Import konsultiert zuerst `sys.modules`. Ein Stub-Eintrag dort gewinnt, und das echte Modul (das `keyring` importiert) wird nie geladen — genau das, was Phase-7s eigener `credentials.py`-Docstring von Unit-Tests verlangt. `monkeypatch.setitem` ist dabei Pflicht, nicht Stil: ein geleakter `sys.modules`-Eintrag hätte die anderen 256 P8-Tests im selben Prozess vergiftet.

- **F6 — `origin/main` ist `e219a25`, nicht `e66be3a`; der Branch ist 16 Commits ahead, nicht 15.** `e66be3a` ("Session-Rotation #11->#12") ist selbst ein **ungepushter** Commit — er steht an Position 15 der Liste `git rev-list origin/main..HEAD`. Ab Session #12 hat jeder Session-Block diese Zahl vom Vorgänger übernommen und um die eigenen Commits erhöht, ohne `git rev-parse origin/main` je nachzumessen; die Sessions #13-#16 haben die Falschangabe damit viermal weitergereicht. Nachgemessen 2026-09-07: `git rev-parse --short origin/main` = `e219a25`, `git rev-list --count origin/main..HEAD` = **16**. **Für den Nikinger relevant, nicht kosmetisch:** die ausstehende Push-Menge ist eine größer als dokumentiert, und der vermeintliche Basis-Commit ist Teil davon. **Lesson (deckungsgleich mit `feedback_verify_flags_are_on`):** eine vom Vorgänger geerbte Zahl ist kein Messwert. Ein Push-Stand wird gemessen, nicht fortgeschrieben.

- **F7 — Σ 1924 ist jetzt gemessen, und die Σ-Konvention ist: `meta_m1_harness/` zählt nicht mit.** Wie beim Push-Stand war auch die Σ von Session #14 bis #16 nur weitergereicht („Σ 1921 unverändert"), nie nachgemessen. Voller repo-weiter Sweep 2026-09-07 (jedes Phasen-Verzeichnis einzeln, wie `reference_running_phase_tests.md` es verlangt — `tests.conftest` kollidiert sonst): P1 97 · P2 82 · P3 105 · P4 162 · P5 190 · P6 76 · P7 169 · **P8 259** · P9 95 · P10 165 · P12 145 · P13 82 · P14 61 · P15 126 · P16 5 · root 105 = **1924**. Plus `meta_m1_harness/` 28 ⇒ **1952 repo-weit über alles**. Die überlieferte Σ stimmt also — aber nur unter der nirgends aufgeschriebenen Konvention, dass der **geschlossene** Meta-Strang M1 nicht mitgezählt wird. Das ist hiermit protokolliert, damit die nächste Session nicht 1952 misst und einen Bruch vermutet, den es nicht gibt.
- **F8 — die Rotationen der Sessions #14 und #15 haben je die `## Session stopped`-Überschrift verloren; in diesem Commit verbatim aus Git wiederhergestellt.** Die Blöcke #13 und #14 lagen im Archiv **ohne Überschrift** — ihr Text begann direkt mit `> **Auftrag:**`. Der Inhalt war also nie weg, aber die Blöcke waren für die Konvention unsichtbar: `grep '^## Session stopped' SESSIONS_ARCHIVE.md` fand 15 statt der dokumentierten 17 Einträge, und die Nummernfolge hatte ein Loch bei 13/14. **Der `--strict`-Hook hat das nicht gemeldet** (er prüft die Anschluss-Nummer zum Phasenkopf, nicht die Lückenlosigkeit des Archivs) — die „hook exit 0"-Zeilen der Sessions #14-#16 waren insofern korrekt und trotzdem irreführend. **Reparatur:** beide Überschriften **verbatim** aus der Historie geholt (`git show 4481672^:phase16_activation/CLAUDE.md` für #13, `git show 994a5af^:…` für #14) — kein Wort rekonstruiert oder neu formuliert. Danach: 17 `## Session stopped`-Überschriften, Folge #16…#1 + Plan-Session lückenlos, exakt die schon dokumentierte Zahl. **Kein 📕-Supersede-Verstoß:** hier wurde keine archivierte Aussage geändert, sondern eine bei der Rotation verlorene Zeile zurückgelegt.
- **F9 (Watch-Item für Phase 17) — `check_archive_sequence` prüft keine Lücken.** F8 wäre bei einer Gap-Prüfung sofort aufgefallen statt drei Sessions später. Ein Zusatz-Check „Archiv-Nummern sind lückenlos absteigend" wäre wenige Zeilen in `scripts/check_doc_rotation.py`. **Nicht in dieser Session gebaut** — der Hook ist Phase-14-Erbe (P14-F) und lag außerhalb der Phase-16-Freigabeliste. **Entschieden 2026-09-08: der Nikinger hat ihn als ersten Punkt der Folgesession beauftragt** (siehe „Next"), Cross-Phase-Freigabe P14 damit erteilt.

### Open questions / blockers

- **Live-Stand — SCHEDULER LÄUFT (nachgemessen 2026-09-08 09:32, nach Nikinger-Restart #4 um 09:30:49):** `data/state/run_scheduler.log` endet mit `2026-09-08 09:30:49,985 INFO scheduler.run: starting scheduler daemon (account=demo, max_trades=5, daily_loss_cap=1800.0, cycle=5min).` — **kein Traceback dahinter**. Prozess `281715 python -m scheduler.run`. Damit ist die K7-Caps-Pin-Verifikation in derselben Zeile miterledigt: alle vier Werte stimmen verbatim mit Runbook v2 §3 überein. **Alle vier Dienste up:** Scheduler `281715` (neu) · Recorder `268859` `python -m data_foundation.run` · Discovery `268871` `python -m source_registry.run` · WebUI `268921` uvicorn (die drei letzten seit ~11 h durchgehend, PIDs identisch mit Session #16). Die Zeilen „already running (pid file …) — exiting" in `recorder.log`/`discovery.log` sind **korrektes** Verhalten, kein Fehler: `restart-services.sh start` trifft auf laufende Daemons und beendet sich; beide PIDs sind per `kill -0` als lebend verifiziert, die PID-Dateien sind **nicht** stale.
- **Die vollständige Bug-Kette ist im Log belegt und abgeschlossen.** `run_scheduler.log` zeigt die vier Crashes in genau der Reihenfolge, in der die Sessions #13-#17 sie gefunden haben — `ModuleNotFoundError: No module named 'instinct'` (Z. 4910) → `NameError: intinct_cfg` (Z. 4927) → `TypeError: … unexpected keyword argument 'llm'` (Z. 4944) → `NameError: intinct_extractor` (Z. 4961) → **sauberer Start**. Vier Restarts, vier Bugs, ein Commit `bfab841`. Das ist der empirische Beleg, dass Bug #4 der letzte war.
- **Restspiel-Einschätzung, ehrlich beziffert:** die vier bekannten Bugs sind zu, und die Typo-Familie ist mit `grep -c intinct == 0` erschöpft. Der neue Test deckt aber nur `_build_reward_sink` + die zwei Bridge-Calls aus Hunk 3 ab — **nicht** `build_scheduler` als Ganzes und nicht die ~10 Geschwister-Builder. Ein Bug in einem *anderen* Builder würde immer noch erst beim Restart auffallen. „Restart #4 kommt durch" ist damit begründet erwartbar, aber **nicht** getestet.
- **E3-Restart-Tag: erledigt — Tag 1 läuft seit heute, Di 2026-09-08, 09:30:49.** (Korrektur Nikinger 2026-09-08: der Wochentag stand in den Session-#16/#17-Blöcken als „Mo" — **falsch**, das Datum war richtig. `date -d 2026-09-08` = **Tuesday**. Die Vorregistrierung selbst war von Anfang an korrekt: Commit `6279874` nennt „Tag 1 **Di** 2026-09-08" und listet die 10 Handelstage 8./9./10./11./14./15./16./17./18./21. Sept, Ende 2026-09-21 — das passt auf Di als Start. **Dritte Instanz derselben F6/F7-Klasse in dieser Session:** ich habe den Wochentag aus dem Vorgängerblock übernommen statt ihn zu berechnen. Die archivierten Blöcke #16/#17 bleiben unangetastet — 📕-Disziplin, der Fehler wird hier korrigiert, nicht dort überschrieben.)
- **E4 (Tagesroutine + Closeout):** nach E3 in der Folgesession.
- **Push-Freigabe-Stand — KORRIGIERT, bitte vor dem Push lesen (Nikinger):** `origin/main` steht auf **`e219a25`**, nicht auf `e66be3a`. Der Branch ist **16 Commits ahead**, nicht 15. Siehe F6. Diese Session trägt 2 davon bei (`0cfcd6e` Test+Fix + diese Rotation); die übrigen 14 stammen aus den Sessions #12-#16.

### Next (für die Folgesession)

- **ZUERST: den Lücken-Check in `scripts/check_doc_rotation.py` bauen (F9 — Nikinger-Freigabe 2026-09-08).** Bis heute war F9 nur ein Watch-Item, weil der Hook Phase-14-Erbe (P14-F) ist und außerhalb der Phase-16-Freigabeliste liegt; **der Nikinger hat ihn am 2026-09-08 ausdrücklich als nächsten Punkt beauftragt** — damit ist die Cross-Phase-Freigabe für P14 erteilt und aktenkundig. Inhalt: `check_archive_sequence` prüft heute nur den Anschluss Phasenkopf→Archiv, nicht die **Lückenlosigkeit** der Archiv-Nummern. Genau deshalb ist F8 (fehlende Blöcke #13+#14) drei Sessions lang unentdeckt geblieben, obwohl der Hook jedes Mal exit 0 lieferte. Erwartete Form: die Archiv-Nummern absteigend einsammeln (`_SESSION_NUM_RE` existiert bereits) und melden, wenn zwischen `max` und `min` eine Nummer fehlt; Plan-Session-Block ohne Nummer bleibt korrekt ausgenommen (die Preamble beschreibt das Verhalten schon). Tests in der Phase-14-Konvention dazu. **Wichtig als Selbsttest:** der neue Check muss gegen das *heutige, reparierte* Phase-16-Archiv grün sein **und** gegen den Stand *vor* der F8-Reparatur rot — sonst prüft er nicht, was er prüfen soll.
- **DANACH, wenn nichts anderes offen ist, das jetzt machbar wäre:** der tiefe Doc-Drift-Audit unten. Reihenfolge auf Nikinger-Wunsch 2026-09-08: erst den Detektor bauen, dann damit suchen — Check #3 des Audits ist genau das, was der Hook danach automatisch kann.
- **Tiefer Doc-Drift-Audit über das ganze Repo (Nikinger-Auftrag 2026-09-08, läuft NACH dem F9-Lücken-Check).** Diese Session hat in einer einzigen Phase drei Doku-Defekte gefunden (F6 falscher Push-Baseline seit #12, F7 nie nachgemessene Σ, F8 zwei bei der Rotation verlorene Archiv-Überschriften) — alle drei nach demselben Muster: **eine Zahl vom Vorgänger geerbt statt gemessen.** Bei 16 Phasen-Verzeichnissen und ~17 Session-Archiven ist die Annahme unbegründet, dass Phase 16 der einzige betroffene Ort ist. Der Audit ist **read-only Messung**, kein Umschreiben; jeder Fund wird gemeldet, nicht still korrigiert (📕-Snapshots bleiben unangetastet — verlorene Struktur wie in F8 darf verbatim aus Git zurück, geänderte Aussagen brauchen ein Supersede). Konkrete Checks, alle billig:
  1. **Push-Baseline (F6-Klasse):** `git rev-parse --short origin/main` + `git rev-list --count origin/main..HEAD` gegen die Behauptung im Phasenkopf **jeder** aktiven Phase. Gemessen, nie fortgeschrieben.
  2. **Σ-Konsistenz (F7-Klasse):** voller Sweep pro Phasen-Verzeichnis (getrennt, `tests.conftest` kollidiert sonst — `reference_running_phase_tests.md`) gegen jede Σ-Behauptung in root-`CLAUDE.md`, `ROADMAP.md` und den Phasenköpfen. Konvention beachten: `meta_m1_harness/` (28) zählt **nicht** mit, Σ ohne M1 = 1924, mit = 1952.
  3. **Archiv-Integrität (F8-Klasse), repo-weit:** für jede `SESSIONS_ARCHIVE.md` `grep -c '^## Session stopped'` gegen die im Preamble behauptete Zahl, **und** die Nummernfolge auf Lücken prüfen. Phase 16 hatte 15 statt 17 mit einem Loch bei #13/#14 — der `--strict`-Hook meldet das nicht (F9).
  4. **Genau ein Session-Block pro Phasenkopf:** `grep -c '^## Session stopped' <phase>/CLAUDE.md` == 1 für jede Phase (Rotationsregel seit 2026-07-06).
  5. **`docs/INDEX.md`-Vollständigkeit:** jede `.md` im Repo hat eine INDEX-Zeile, jede INDEX-Zeile zeigt auf eine existierende Datei (beide Richtungen — verwaiste Zeilen zählen genauso).
  6. **Header-Card-Links:** `up:`/`down:`-Ziele existieren; ein toter Link ist derselbe Defekt wie eine verlorene Überschrift, nur leiser.
  - **Erwartung realistisch halten:** das ist normale Alterung eines großen, dokumentations-schweren Repos, kein Hinweis auf schlampige Arbeit — die Sessions #12-#16 haben die Zahlen gewissenhaft *weitergegeben*, nur nie *nachgemessen*. Der Audit hat Wert, weil er die Klasse schließt, nicht weil er jemanden fängt.

- **Scheduler-Restart-Versuch #4 (Nikinger-Aktion):** `bash scripts/restart-services.sh start` → `sleep 30` + K7-Caps-Pin-Verify (`account=demo, max_trades=5, daily_loss_cap=1800.0, cycle=5min`). Falls Scheduler crasht: Log teilen — und **vor** dem nächsten Punkt-Fix prüfen, ob der crashende Builder einen Smoke-Test nach dem Muster von `test_wiring_reward_sink.py` bekommen kann.
- **E3 — Runbook-Start nach erfolgreichem Restart (Nikinger-Aktion, Runbook v2 §0 Reihenfolge):** Schritt 1 Pflicht-Operator-SQL ✅ (Session #13) → Schritt 2 v2 §2 Pre-Flight → Schritt 3 v2 §2.6 Prereg-Aktiv-Block ✅ → Schritt 4 v2 §3 Restart-Sequenz → Schritt 5 v2 §4 Day-0-Checks → Schritt 6 v2 §5 Tagesroutine → Schritt 7 v2 §8 Tag-10-Closeout.
- **E4 — Tagesroutine + Closeout:** ab Tag 1 täglich `autonomy_report.py --day`; nach Tag 10 `--summary`, bei `overall_verdict == "PASS"` Closeout-Handover + SVG + Status-Pflege.

### Watch-Item / Plan-Hygiene (für spätere Sessions)

- **Import-Smoke-Test für `scripts/wiring.py` — Watch-Item bleibt offen, jetzt aber präzise geschnitten.** Session #16 hatte ihn als „dringend" notiert; diese Session hat den **ersten Baustein** geliefert (`_build_reward_sink` + Hunk 3). Ungedeckt bleiben `build_scheduler` selbst (braucht einen gefakten `get_broker("ig_demo")`, deshalb bewusst ausgelassen) und die Geschwister `_build_paper_tracker` / `_build_paper_engine` / `_build_context_recorder` / `_build_data_foundation` / `_build_research` / `_build_universe_from_db` / `_build_abstain_sink` — alle mit derselben „operator-run, not pytest-collected"-Exposition. **Phase-17-Material.**
- **Phase-15-Wiring-Doku (Phase-17-watch):** die 3 Konstruktor-Signaturen prominent im Phase-15-Repo dokumentieren (unverändert aus Session #16).
- **Pflicht-Operator-SQL §1 v2:** ✅ DONE (Session #13, Commit `6279874`).
- **Staffelung via `marginDepositBands`** (Plan §13 #8): Phase-17-Material.
- **Hybrid-Test-Ansatz** (Session #11 Findings): Phase-17-Material.
- **Runbook-Supersede-Disziplin** (P11): kein Edit am Runbook — neues, datiertes, supersedendes Doc.
- **Phase-9-Discovery-Filter** (`is_weekend_market`): strukturelle Lösung für die 3-Epics-Lücke.
- **Phase-15-`requires-python` Align-Option:** falls Nikinger strikt `>=3.12` statt `>=3.11` will, 1-Zeilen-Edit.

**Block-Status nach dieser Session (endgültig):**

| Block | Status |
|---|---|
| A (Haushalt) | ✅ A-0..A-4 + A-5 Push (Sessions #1-#3) |
| B (Substrat) | ✅ B1+B3 code + B2 Operator-Apply + A-5 Push (Session #3) |
| C (Research-Loop) | ✅ C1+C2+C3+C5 endgültig in code; C4 = Doku-Only (Sessions #4-#5) |
| D (Freischaltung) | ✅ D1+D1.2+D2+D3.0+D3.1+D3.2 komplett (Sessions #7-#10) |
| E (Autonomie-Test, Vorregistrierung) | ✅ E1 endgültig in docs (Session #6) |
| E (Autonomie-Test, E2) | ✅ E2 endgültig in code (Session #11) |
| E (Autonomie-Test, E3 Runbook) | ✅ E3 Runbook v2 endgültig in docs (Session #13, supersedet v1) |
| E (Autonomie-Test, Pre-Step Phase-15-install) | ✅ endgültig in packaging (Session #14) |
| E (Autonomie-Test, Hotfix Typo-Bug) | ✅ endgültig in code (Session #15) |
| E (Autonomie-Test, Hotfix #2 Signatur) | ✅ endgültig in code (Session #16) |
| E (Autonomie-Test, Pre-Step Smoke-Test + Hotfix #3) | ✅ endgültig in code + tests (Session #17, P8 256 → 259) |
| E (Autonomie-Test, E3 Runbook-Start) | 🔴 offen [Nikinger-Aktion: Restart #4] |
| E (Autonomie-Test, E4) | 🔴 offen [nach E3-Restart-Start] |
