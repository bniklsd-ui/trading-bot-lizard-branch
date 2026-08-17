---
status: snapshot
purpose: Phase 12 (Datenfundament) — Stand VOR der Beweiswoche. Steps 0–8.5 gebaut, getestet und am 2026-08-17 erstmals einen ganzen Handelstag live beobachtet. Enthält die Tag-1-Messergebnisse, den Befund warum Step 9 in der aktuellen Konfiguration NICHT bestehen kann, das Delta seit PHASE11_DEFERRAL_HANDOVER.md und die offenen Entscheidungen A–D. Keine Implementierungsdetails — Code ist Wahrheit.
read-when: als erstes Dokument der nächsten Session (insb. der Planungssession — §1a enthält eine verbindliche Rahmen-Änderung: Arbeit ab jetzt unter der Woche, nicht am Wochenende); zwingend vor jedem Scheduler-Neustart, vor Step 9 (Beweiswoche) und vor jeder Aussage darüber, was die Notbremse vom 2026-08-11 gebracht hat
detail: L3
up: ./CLAUDE.md
down:
  - ../docs/concepts/phase12_data_foundation_plan.md    # Bauplan, D1–D20, Steps 0–10, §7 PASS-Kriterien
  - ../phase10_v3/PHASE11_DEFERRAL_HANDOVER.md          # warum dieser Track existiert (Vorgänger-Handover)
  - ../docs/architecture/phase12_preproof.svg           # Bild: was steht, was fehlt
updated: 2026-08-17
---

# Phase 12 — Pre-Proof-Handover (2026-08-17)

> **Autor:** Claude Code (Opus 5), 2026-08-17. Live-DB read-only (`mode=ro`) gelesen,
> kein Bot-berührender Code angefasst (Werktag, Bot läuft — Phase-12-`Rahmen`).
> **Adressat:** die nächste Claude-Code-Session, **bevor** sie einen Detailplan entwirft.
> **Was dieses File NICHT ist:** kein Closeout. Phase 12 ist **nicht abgeschlossen** —
> ihr Done-Kriterium (Plan §7: eine durchlaufende Beweiswoche) ist **nicht** erreicht,
> Step 9 hat nicht begonnen.

---

## §0 BLUF

**Die Infrastruktur, an der drei Datenwochen gestorben sind, ist gebaut, scharf und seit
2026-08-17 einen vollen Handelstag lang live beobachtet. Gemessen wurde trotzdem nichts —
weil der Messarm selbst (`enable_shadow_schedule`) im laufenden Prozess ausgeschaltet ist.**

Das ist exakt dieselbe Fehlerklasse, wegen der die Notbremse gezogen wurde
(`enable_ig_bars` — gebaut, nie eingeschaltet), nur eine Ebene weiter oben. Der Unterschied
zu damals: sie ist **an Tag 1 aufgefallen**, nicht nach drei Wochen.

Die Beweiswoche (Step 9) kann in der aktuellen Konfiguration **strukturell nicht bestehen**
— Plan §7 „Kern" verlangt aufgelöste Shadow-Pairs an ≥ 4 von 5 Handelstagen je `ok`-Epic;
heute wurden **null** Paper-Zeilen erzeugt (die letzten überhaupt: 2026-08-07).

**Dazu kommen drei verifizierte Code-Befunde aus dem Ultrareview vom selben Tag** (§3.0):
der Divergenz-Sampler ist tot (crasht an IGs Timestamp-Format — Kriterium C), und zwei
Bugs im Paper-Pfad schreiben Messzeilen still als `EXPIRED_UNRESOLVED` ab (Kriterium E/Kern).
**Reihenfolge daher: erst diese drei kleinen Fixes, dann der Neustart mit dem Messarm, dann
Step 9** (Entscheidung A) — **unter der Woche, nicht am Wochenende** (Rahmen-Änderung, s. §1a).

---

## §1a Rahmen-Änderung — für die Planungssession verbindlich (2026-08-17)

> **Nikinger-Entscheidung:** die Phase-12-Regel „bot-berührende Steps nur am Wochenende"
> (Plan §1) ist **aufgehoben**. Ab jetzt wird **direkt unter der Woche** gearbeitet, auch
> bot-berührend. **Begründung: der Bot läuft ohne die ausstehenden Fixes nicht gescheit** —
> jede Wochenend-Wartezeit verlängert einen kaputten Messbetrieb um eine volle Woche und
> produziert damit genau das, wogegen die Notbremse vom 2026-08-11 gezogen wurde.
>
> **Die nächste Planungssession muss diese Regel übernehmen** und darf U1–U3 (§3.0) nicht
> mehr auf ein Wochenendfenster terminieren. Praktisch: Bot vor dem Edit stoppen (`ps aux |
> grep scheduler.run` als Gegenprobe — sonst Parallel-Login-Falle), Edit, gezielt neu starten.
> Unverändert: Live-/Netz-/Kostenläufe macht der Nikinger, die Live-DB liest Claude nur
> `mode=ro`, Cross-Phase-Edits außerhalb `data_foundation/` bleiben freigabepflichtig
> (U2/U4 liegen in `wiring.py` und fallen darunter).

## §1 Ergebnisse (ehrliche Teilbilanz)

**Fertiggestellt:** Steps 0–8.5 des Plans — `data_foundation/` (Archiv, Budget, Resolver,
BarService, Recorder, Heartbeat + Divergenz-Sampler), Migration 006, die Rewiring-Punkte,
die Operator-Skripte (`probe_allowance.py`, `reset_universe.py`, `data_health.py`,
`run_recorder.sh`), Step 8.5 (`SymbolResolver` → `universe_refresher`).

**Getestet:** `pytest phase12_data_foundation/tests -q` → **117 passed** (heute nachgelaufen,
nicht aus dem Session-Block übernommen). Volle Regression zuletzt Session 5: P1 87 · P2 77 ·
P3 104 · P4 155 · P5 173 · P6 76 · P7 138 · P8 237 · P9 80 · P10 159 · P12 117 · meta 28 ·
root 80.

**Live validiert (2026-08-17, erster voller Handelstag mit dem kompletten Stack):** siehe §2.
Kurz: Resolver, Recorder, Archiv, Budget-Metering und der BarService-Write-Through sind
**alle** end-to-end im Echtbetrieb beobachtet — nicht nur offline bewiesen.

**Gepusht und committet:** ✅ beides — die Steps 4–8.5 liegen auf `main`
(`49902b6`, `473c8e4`, `65ebec7`, `37f2f0a`, `47d89b0`; diese Session ergänzt Doku +
`.gitignore`), und der komplette Stand ist auf `origin/main` gepusht (Nikinger-Freigabe
2026-08-17).

**Nicht erreicht / offen geblieben:**
1. **Die Beweiswoche (Step 9) hat nicht begonnen** und kann im aktuellen Zustand nicht
   bestehen (§3.1). Das Done-Kriterium der Phase ist damit offen.
2. **Step 10 (Lightstreamer-Mitschrieb)** ist unverändert auf Step-9-PASS gegatet — nicht
   angefasst, die Kernfrage (Parallel-Login vs. eigener LS-Prozess) ist weiterhin offen
   (Plan §6 Step 10).
3. **Kein einziger gemessener Tag.** WI-2/W2 — die Frage, für die das ganze Fundament
   gebaut wurde — ist nach wie vor unbeantwortet.
4. Die zwei aus Step 6 bekannten Lücken (G-Deckungslücke an einem POST_WINDOW-losen Tag;
   In-Memory-Sampler-Throttle über Neustarts) bleiben offen — bewusst, unverändert.

---

## §2 Tag-1-Live-Ergebnisse (2026-08-17, read-only erhoben)

Prozesse: Recorder `pid 33151` (09:56 CEST), Scheduler `pid 35195` (12:09 CEST,
`python -m scheduler.run --enable-divergence-sampler`).

| Was | Beobachtung | Bedeutung |
|---|---|---|
| **Resolver (Step 3+8.5)** | Pass 1 um `10:14:38Z` (Startup-erzwungen, `runner.py:285` im Preflight), Pass 2 um `12:19Z`. Registry: 22 Zeilen → **5 `active`/`ok`**, **3 `active`/`no_intraday_source`** (SUN*-Wochenend-Epics, korrekt typisiert), 13 `verified`/`unverified`, 1 `quarantined` | `measurable_universe()` ist **erstmals nicht leer**. Step 8.5 ist damit **live bewiesen**, nicht nur regression-grün. Kein `NULL`-Fallback-Pfad ausgelöst (Kriterium D) |
| **Recorder (Step 5)** | Erster 1m-Write `10:16:32Z` — **114 Sekunden** nach dem ersten Resolver-Write. Danach 62 Fetch-Batches im 5-Minuten-Takt bis `15:22:43Z`, `errors: []`, `skipped_off_hours: false` | Die Kette Resolver → `measurable_universe()` → Recorder → Archiv greift ohne Operator-Eingriff |
| **Archiv (Step 1)** | **1891 Bars, alle heute geschrieben** (das Archiv war heute früh leer): yf 1m (5 Epics, Recorder), yf 5m + ig 5m (BarService-Write-Through) | Bars überleben jetzt den Bot-Zustand — die Wurzel von Ausfall 3 |
| **Budget (Step 2) + Allowance-Bugfix** | 28 echte `allowance_observations`: `total=10000`, `remaining=9724`, `expiry=2026-08-23T20:53Z`. Verbrauch heute **136 Punkte** (probe 20 / research 110 / sample 6), Prognose ~500 Tage bis Erschöpfung | Der Fix aus Session 5 wirkt **live**: vorher war das Feld strukturell blind (`body["allowance"]` statt `body["metadata"]["allowance"]`). Verbrauch ist jetzt gemessen, nicht geschätzt — Soll laut §7/F: < 1500 |
| **Heartbeat (Step 6)** | `data_health.py --day 2026-08-17` → `ok: True`, Exit `0`, `bars_today: 1891`, `measurable_epics: 5`, **`pairs_opened: 0`** | Erste echte Ausführung des Operator-Pfads — **und zugleich der schärfste Befund dieser Session**, s. §3.2 |
| **Divergenz-Sampler** | 2 Samples (`source_spend.kind='sample'`), **kein** `mismatch`, **null** `quote_divergence`-Events | ❌ **Läuft NICHT** — er crasht beim ersten Epic jedes Passes (§3.0 / U1). Sollwert wäre 5 Samples/Tag (1×/Epic/Tag über `measurable_universe()`); beobachtet: **exakt 1 Epic pro Pass, und pro Pass rückt es um genau eins weiter** — der Fingerabdruck eines Absturzes nach dem ersten Epic bei bereits gesetzter Tages-Drossel, nicht eines laufenden Samplers |
| **Scheduler** | `consecutive_failures: 0`, `trades_today: 0`, 79 Research-Ticks, alle Abstain | Kein Crash, kein KILL, kein Backoff — der Stack trägt einen vollen Tag |

**Antwort auf „was hat die Notbremse gebracht?"** — nach einem Tag, ehrlich:
Die **drei** Mechanismen, an denen die Datenwochen starben, sind einzeln nachweisbar
entschärft: (a) das Symbol-Mapping ist abgeleitet **und** code-verifiziert statt deklariert,
(b) der IG-Verbrauch ist gemessen statt blind, (c) Bars werden unabhängig vom Bot-Zustand
persistiert. **Was sie noch nicht gebracht hat: einen einzigen gemessenen Tag.**

---

## §3 Befunde, die vor Step 9 entschieden werden müssen

### 3.0 Vier Code-Befunde aus dem Ultrareview — alle gegen den Code nachverifiziert

Ein Cloud-Ultrareview über den Phase-12-Diff (2026-08-17) lieferte vier Befunde. Alle vier
sind **nachgelesen und bestätigt**, einer zusätzlich **live belegt**. Sie sind hier
absichtlich **nicht gefixt** (Analyse/Fix-Trennung — Opus analysiert, die Umsetzung ist ein
eigener Schritt). Die Fixes sind klein und werden **unter der Woche** gemacht, nicht am
Wochenende (§1a).

| # | Befund | Ort | Wirkung auf §7 |
|---|---|---|---|
| **U1** | **`DivergenceSampler` crasht an echten IG-Bar-Timestamps.** `BudgetedIGBarProvider` reicht IGs Rohformat `yyyy/MM/dd HH:mm:ss` unnormalisiert durch (`service.py:119`), `heartbeat.py:175` parst es mit `datetime.fromisoformat` ⇒ `ValueError`. Die Tages-Drossel wird **vor** dem Crash gesetzt (`heartbeat.py:167`) und die Ausnahme killt die ganze Epic-Schleife | `data_foundation/heartbeat.py:175` (Fix: `normalize_bar_ts` aus `models.py:70` — existiert bereits und kann beide Formate) oder kanonisch `service.py:119` | **Kriterium C tot.** Nie ein `quote_divergence`-Event, nie ein `mismatch` |
| **U2** | **Der Retry-Cap des Paper-Trackers ist wirkungslos.** `_charge_failed_attempt` feuert nur im `except` um `bar_fetch` (`paper.py:544-548`), aber `BarService.get_window` ist durchgehend fail-soft und liefert `[]` statt zu werfen ⇒ eine Zeile wird beim **ersten** schlechten Tick als `EXPIRED_UNRESOLVED` abgeschrieben statt ~1 h lang erneut versucht | `phase8_scheduler/scripts/wiring.py:514-517`; der Kommentar bei `:477-480` behauptet ausdrücklich das Gegenteil und ist damit falsch | **Kriterium E / Kern gefährdet** — genau die WI-2-Zeilen, die die Phase erzeugen soll |
| **U3** | **`_covers_tail` prüft nur das Fensterende, nie den Anfang** (`service.py:254-261`) ⇒ ein frisches, aber kurzes Archiv (Recorder-Neustart, erster Tag, Lücke) kurzschließt die Kette, `resolve_paper_trade` findet keine Bar ≤ `time_stop_utc` und die Zeile läuft still ab. Kombiniert mit U2 ohne zweiten Versuch | `data_foundation/service.py:202-228` | **Kriterium E / Kern**, verstärkt U2 |
| **U4** | **Der Scheduler-`TickerMapper` wird nur beim Start befüllt** (`wiring.py:175-180`, `if spec.yf_ticker:`). Ein Epic, dessen `yf_ticker` erst ein späterer Resolver-Pass setzt, fehlt bis zum Neustart ⇒ yF-Leg wirft `EpicNotMappedError`, die Kette fällt auf IG zurück und verbrennt Allowance. Der Recorder macht es richtig (registriert pro Tick neu, `run.py:82-99`) | `phase8_scheduler/scripts/wiring.py:175-180` | Nur Kosten (F); heilt beim Neustart, heute vermutlich nicht ausgelöst |

**U1 ist zusätzlich live belegt** (`data/state/research_health.jsonl`): Pass 1 (12:14 CEST)
sampelte genau **ein** Epic (`IX.D.DAX.IFMM.IP`, `ok: true`), Pass 2 (14:19 CEST) genau eines
(`IX.D.DAX.IGN.IP`) — das jeweils nächste in der Liste. Ein funktionierender Sampler hätte im
ersten Pass alle 5 `ok`-Epics abgearbeitet. Der IG-Fetch **gelingt** (die Punkte werden
gebucht), der Crash liegt danach.

**Folge für die Reihenfolge:** ein Neustart mit dem Shadow-Flag allein genügt **nicht** mehr —
er würde Pairs erzeugen, die U2/U3 still abschreiben können, während der Sampler weiter tot
ist. Siehe die korrigierte Entscheidung A in §5.

### 3.1 Der Messarm ist aus — und er ist der einzige (blockierend)

- `SchedulerConfig.enable_shadow_schedule` ist Default **`False`**
  (`phase8_scheduler/scheduler/config.py:189`); der laufende Prozess wurde **ohne**
  `--enable-shadow-schedule` gestartet. Folge: `shadow_pair_scheduler` ist `None`
  (`wiring.py:775-776`) → heute **0** Paper-Zeilen, letzte überhaupt am 2026-08-07.
- **Der abstain-getriebene Pfad kann das nicht auffangen:** `open_shadow_pair(...)` verlangt
  ein nicht-leeres `epic` (`phase10_v3/abstain_lessons/paper.py:191-213`). Von **1476**
  `abstain_records` aller Zeiten haben **1465** `epic IS NULL` (alle `reason_no_candidates`);
  nur 11 (`reason_debate_abstain`) tragen ein Epic. Unter dem heutigen Funnel (79/79
  `research_empty`) ist dieser Pfad **strukturell inert**.
- ⇒ **Der H1-Timer ist der einzige lebende Messarm**, und er zieht seine Epics aus
  `measurable_universe()` (`wiring.py:790`) — was bis heute früh dauerhaft leer war.
  Beide Hälften sind jetzt reparierbar in **einem** Neustart.
- Plan §7 „Kern" verlangt aufgelöste Shadow-Pairs an ≥ 4/5 Handelstagen je `ok`-Epic ⇒
  **ohne dieses Flag ist Step 9 ein garantierter FAIL.**

### 3.2 Der Ausfall-Alarm ist blind für genau diesen Ausfall (Requirement G)

`assess_day` setzt `ok=False` nur bei (a) `measurable_epics > 0` **und** null Bars, oder
(b) **`shadow_enabled`** **und** null aufgelöste/typisiert abgelaufene Pairs
(`data_foundation/heartbeat.py:44-107`). Ist Shadow aus, entfällt (b) — und der Tag gilt als
gesund. **Heute live vorgeführt:** `ok: True`, Exit `0`, bei `pairs_opened: 0`.

Das ist die Anforderung G („ein Ausfalltag fällt am selben Tag auf") an ihrer eigenen
Definition vorbei. Gute Nachricht: dasselbe Flag aus 3.1 schärft den Alarm automatisch mit.
Trotzdem eine Entscheidung, kein Cleanup (Entscheidung B).

### 3.3 Drei von acht Aktiv-Plätzen sind dauerhaft nicht messbar

`promotion.run_promotion_cycle` hat `max_active: int = 8`
(`phase9_universe/universe/promotion.py:165,253`) und kennt `data_source_status`
**überhaupt nicht** (null Treffer in der Datei). Aktuell belegen 3 SUN*-Wochenend-Epics
(`no_intraday_source`) Werktags-Plätze, auf denen sie nie messbar werden ⇒ der messbare Pool
ist strukturell auf **5** gedeckelt. Die 13 `verified`-Zeilen werden vom Resolver nie
angefasst — er liest nur `active` + `discovered` (`data_foundation/symbols.py:268`).
Kein Bug, aber ein Durchsatz-Deckel für die Beweiswoche (Entscheidung C).

### 3.4 Der Funnel-Reason-Code verdeckt, was wirklich passiert (Phase-11-Scope, nur Befund)

Alle 79 heutigen Abstains sind `stage='research_empty'` / `reason='reason_no_candidates'` —
aber ihr `detail` trägt eine ausformulierte LLM-Begründung mit **echten Marktzahlen**
(„negative drift −0.29 % bis −0.32 %", „volume z-score −2.08", „CAC and IBEX lack volume
data"). Der Bucket vermischt also **„keine Daten kamen an"** mit **„das LLM hat sich bewusst
enthalten"**.

Das ist **nicht neu** und **nicht** von Phase 12 verursacht: am 2026-08-03 und 2026-08-07
identisch, am 2026-07-27 dagegen mit **leerem** `detail`. Die Konsequenz ist eine
historische Lesekorrektur, eng gefasst: der *Bucket* war über drei Datenwochen einheitlich,
die *Ursache* darunter nachweislich nicht. **Das entwertet die Notbremse nicht** — die stützte
sich auf drei separate Infrastruktur-Ausfälle, die davon unberührt sind.

Der feinere Name existiert bereits scheduler-seitig (`REASON_LLM_ABSTAIN`,
`phase8_scheduler/scheduler/research_tick.py:84`, sichtbar in
`scheduler_state.json:last_no_trade_reason`) — er erreicht `abstain_records` nur nicht, weil
der Classifier Gate 2 pauschal auf `REASON_NO_CANDIDATES` mappt
(`phase10_v3/abstain_lessons/classifier.py:18,67`). ⇒ **Durchreichen, nicht neu erfinden.**

### 3.5 `market_regime_snapshots` ist zu 100 % leer (Phase-10-Scope, nur Befund)

**1162 von 1162** je geschriebenen Zeilen sind `degraded=1` / `data_source='quote_only'`
(1152 mit `epic IS NULL`, 10 **auch mit** Epic). `build_regime_snapshot` degradiert, sobald
keine/zu wenige Bars vorliegen (`phase10_v3/market_context/regime.py:86-97`). Es gab also
**nie** eine befüllte Kontext-Zeile. Seit dem BarService existiert erstmals eine Quelle, die
das füllen könnte.

### 3.6 Historischer Kontext zum Paper-Tracker

Aller Zeiten: 107 `RESOLVED` vs. **505 `EXPIRED_UNRESOLVED`**. Die drei Tage vor dem
Allowance-Incident (2026-08-05/06/07) haben **null** Auflösungen produziert — zeitlich
konsistent mit der erschöpften IG-Allowance (`phase10_v3/ALLOWANCE_INCIDENT_2026-08-08.md`),
was genau die Lücke ist, die Archiv + Recorder + Budget jetzt schließen sollen. In der
Beweiswoche ist das die zu beobachtende Kennzahl (Kriterium E: `resolution_source ≠ NULL`).

---

## §4 Delta seit `PHASE11_DEFERRAL_HANDOVER.md` (2026-08-11)

| Anf. (A–G) | Stand heute |
|---|---|
| A — eine Wahrheit je Instrument-Fakt | ✅ gebaut + live: Registry ist alleiniger Schreiber, 22/22 Zeilen typisiert, kein Parallel-Speicher entstanden |
| B — Mapping abgeleitet + verifiziert | ✅ gebaut + **live bewiesen** (5 `ok` per Preisvergleich, 3 `no_intraday_source`); Beweis „ohne Code-Edit über eine Woche" steht aus (Step 9) |
| C — Bars quellenagnostisch persistiert | ✅ 1891 Bars an Tag 1 |
| D — typisierte Nicht-Messbarkeit | ✅ live (`no_intraday_source` statt stiller NULL) |
| E — Provenienz je Paper-Zeile | ⚠️ Spalte existiert (Migration 006), **ungetestet in echt** — es gab heute keine Paper-Zeile |
| F — Budget modelliert statt entdeckt | ✅ live, 136/10000 Punkte, Prognose vorhanden |
| G — Messausfall fällt am selben Tag auf | ⚠️ **gebaut, aber im Ist-Zustand blind** (§3.2) |

Zusätzlich seit dem Deferral-Handover: zwei echte IG-Allowance-Bugs gefunden **und** gefixt
(Session 5), Step 8.5 als neuer, blockierender Plan-Schritt entdeckt und geschlossen.

---

## §5 Offene Entscheidungen (Optionen → Empfehlung → Folge)

**A — Wann startet die Beweiswoche?** *(blockierend für Step 9; korrigiert nach dem
Ultrareview — die ursprüngliche Fassung „nur ein Flag" ist überholt)*
- (a) **Erst U1–U3 fixen (unter der Woche, Bot vorher stoppen — §1a), dann Neustart mit
  `--enable-divergence-sampler --enable-shadow-schedule`, dann Step 9.** → *Empfehlung.*
  Die drei Fixes sind klein und liegen zu zweidritteln in Phase-12-eigenem Code
  (`heartbeat.py`/`service.py`; nur U2s Fix-Ort liegt in `wiring.py`). Ohne sie misst die
  Woche entweder nichts (C) oder schreibt ihre eigenen Messzeilen ab (E/Kern).
- (b) Sofort neu starten, nur mit dem Flag, Fixes danach. → Pairs entstehen, aber U2/U3
  können sie still abschreiben und der Sampler bleibt tot ⇒ die Woche wäre bestenfalls
  teilweise auswertbar. Nur sinnvoll, wenn Zeitdruck über Datenqualität geht.
- (c) Beweiswoche ohne Shadow starten. → Garantierter FAIL an §7 „Kern"; vierte verlorene
  Datenwoche.
- **Fix-Reihenfolge innerhalb (a):** U1 (eine Zeile, `normalize_bar_ts` existiert bereits) →
  U3 (Start-Seite in `_covers_tail` bzw. `coverage_ratio` prüfen) → U2 (Retry-Cap greifen
  lassen **und** den falschen Kommentar bei `wiring.py:477-480` korrigieren). U4 ist reine
  Kostenoptimierung und kann warten.
- **Ablauf (Nikinger) — erst stoppen, dann starten.** Ein zweiter Scheduler neben dem
  laufenden würde zwei IG-Logins parallel öffnen und sich gegenseitig die Session-Tokens
  zerschießen (`phase1_broker_wrapper/lightstreamer_integration_notes.md`, „Parallel-login
  auth trap") — der Fehler sähe dann aus wie „das Flag wirkt nicht":
  1. Laufenden Scheduler stoppen (Kill-Switch im Dashboard oder `kill <pid>`; POST_WINDOW
     greift seit dem 2026-07-11-Hotfix binnen ≤ 5 Min) und mit `ps aux | grep scheduler.run`
     **bestätigen, dass keiner mehr läuft**.
  2. `bash phase8_scheduler/scripts/run_scheduler.sh --enable-divergence-sampler --enable-shadow-schedule`
     (Flags verbatim gegen `phase8_scheduler/scheduler/run.py:105,115` geprüft). Der Recorder
     wird vom Skript mitgestartet und darf ruhig weiterlaufen — seine PID-Datei verweigert
     das Duplikat selbst. **Ein zweites Flag ist nicht nötig:** `enable_paper_trades` ist
     bereits Default `True` (`config.py:177`).
  3. Der Universe-Refresher läuft im Preflight sofort (`runner.py:285`), nicht erst nach der
     240-Min-Drossel — der Resolver-Log mit den `ResolverReport`-Zählern kommt also binnen
     Minuten.
- **Prüfpunkt danach:** binnen ~30 Min neue Zeilen in `paper_trades` mit `variant IN
  ('SHADOW_BUY','SHADOW_SELL')`; `data_health.py --day <heute> --shadow-enabled` als
  Gegenprobe (muss dann bei null Pairs `ok=False` liefern — das ist der gewünschte Alarm).

**B — Soll der Heartbeat „Messarm aus" als Problem werten?**
- (a) **`assess_day` meldet an einem geplanten Messtag mit `shadow_enabled=False` ein
  Problem + `ok=False`.** → *Empfehlung.* Kleine, phasen-interne Änderung
  (`data_foundation/heartbeat.py`, + Test), zusammen mit U1–U3 unter der Woche (§1a). Danach kann
  der Alarm nicht mehr „gesund" sagen, während null gemessen wird.
- (b) So lassen, nur dokumentieren. → Der Alarm bleibt genau für die Fehlerklasse blind,
  wegen der die Phase existiert.

**C — Wochenend-Epics in den Aktiv-Plätzen** *(cross-phase, `phase9_universe`)*
- (a) `run_promotion_cycle` berücksichtigt `data_source_status` (SUN* zählen werktags nicht
  gegen `max_active`). → Messbarer Pool wächst 5 → bis 8, die Beweiswoche wird statistisch
  belastbarer. Kosten: Eingriff in Phase-9-Code, daher weiterhin Nikinger-Freigabe (der
  Cross-Phase-Vorbehalt bleibt auch unter der neuen Werktags-Regel bestehen, §1a).
- (b) `max_active` anheben. → Billiger, aber erhöht auch den IG-Verbrauch; Budget hat
  Luft (136/10000).
- (c) Nichts tun, Pool bleibt 5. → *Für die erste Beweiswoche vertretbar* — 5 Epics × 5 Tage
  reichen für §7 „Kern". Empfehlung: **(c) jetzt, (a) nach Step 9.**

**D — Push?** ✅ **erledigt (Nikinger-Freigabe 2026-08-17)** — der komplette Phase-12-Stand
ist auf `origin/main`.

---

## §6 Vorschlag: was nach Steps 9 und 10 kommt

Steps 9+10 sind klein (Beweiswoche = Operator + eine Review-Session; Step 10 = eigene
Design-Session). Danach liegen vier Kandidaten auf dem Tisch, alle aus den Befunden in §3
abgeleitet — **die Nummerierung (eigene Phase 12 Steps 11+ vs. Phase-11-Wiederaufnahme)
entscheidet der Nikinger, nicht diese Session:**

1. **Funnel-Reason-Split durchreichen** (§3.4) — `REASON_LLM_ABSTAIN` existiert bereits, er
   erreicht nur `abstain_records` nicht. **Empfehlung: als Erstes.** Ohne ihn produziert die
   Beweiswoche Daten, die niemand interpretieren kann — genau die Wand, an der Phase 11 stand.
   Klein, gut abgegrenzt.
2. **Promotion lernt `data_source_status`** (§3.3) — hebt den messbaren Durchsatz von 5 auf
   bis zu 8 Epics. Folge: aussagekräftigere Woche, mehr IG-Verbrauch (Budget hat Luft).
3. **`market_context` aus dem BarService füllen** (§3.5) — beendet 1162/1162 leere
   Kontextzeilen. Voraussetzung für belastbare No-Trade-Lessons und für den Phase-13-Council.
   Opportunistisch, sobald jemand ohnehin in dem Code ist.
4. **Phase 11 / WI-2 wiederaufnehmen** — die eigentliche Frage. Gatet auf 1., inhaltlich
   auf einen Step-9-PASS.

Empfohlene Reihenfolge: **1 → 2 → 4**, mit 3 nebenher.

---

## §7 Was die nächste Session zuerst tun sollte

1. Diesen Handover + den Session-Block in [`CLAUDE.md`](./CLAUDE.md) lesen — **nicht** den
   ganzen Plan; nur den betreffenden §6-Step-Block, wenn gebaut wird.
2. Prüfen, ob Entscheidung A gezogen wurde: läuft der Scheduler mit
   `--enable-shadow-schedule`? (`ps aux | grep scheduler.run`) — wenn nein, ist alles
   Weitere an Step 9 sinnlos.
3. `phase1_broker_wrapper/.venv/bin/python phase12_data_foundation/scripts/data_health.py
   --day <letzter Handelstag> --shadow-enabled` — read-only, kein Netz, werktags erlaubt.
4. Erst dann bauen. Live-, Netz- und kostenpflichtige Läufe macht der Nikinger.
