---
status: archive
purpose: Verbatim session-history archive rotated out of `CLAUDE.md`
read-when: auditing how a past phase-10 (V3) decision came about — never needed at session start
detail: L3
up: ./CLAUDE.md
updated: 2026-08-25
---

# phase10_v3 — Session Archive

> The blocks below were moved here **verbatim, unedited** from `CLAUDE.md` per the Doc-Layers
> rotation rule ([docs/DOC_LAYERS_CONVENTION.md](../docs/DOC_LAYERS_CONVENTION.md)). Source order
> preserved (newest-first). The newest `## Session stopped` block always stays in the source file;
> at each session end, the previously-newest block rotates here.

---
## Session stopped — 2026-08-11 (Di — 🛑 NOTBREMSE: Phase 11 deferred, Datenfundament-Track eröffnet)

> **BLUF:** Der Nikinger zieht die Notbremse. Phase 11 wird **vor Erreichen ihrer Ziele**
> zurückgestellt, weil drei Datenwochen an derselben Wurzel gescheitert sind und diese Wurzel
> wichtiger ist als die Phase. Vollständiger Handover — **das erste Dokument der nächsten
> Session**: [`PHASE11_DEFERRAL_HANDOVER.md`](./PHASE11_DEFERRAL_HANDOVER.md).
> Docs-only, kein Code berührt.

### Completed

- **36 Commits gepusht.** Der Baum war sauber, aber `main` lag **36 Commits vor
  `origin/main`** — die gesamte Arbeit seit dem 07-31-Bugfix-Block war lokal geblieben. Jetzt
  `main...origin/main` ohne Abstand.
- **`PHASE11_DEFERRAL_HANDOVER.md` geschrieben** — Status, Delta seit dem P8-Closeout,
  Durability-Anforderungen **A–G** für den neuen Track, offene Entscheidungen, Datei-Anker.
  Nach Handover-Vertrag: keine Implementierungsdetails wiederholt, Code bleibt Wahrheit.
- **`docs/architecture/data_foundation.svg`** (1080×1080) — Fehlerbild + Zielbild.
- **`docs/HANDOVER_PROMPT.md`** — der Handover-Auftrag des Nikinger, von Browser-Chat auf
  Claude Code umgeschrieben: Google-Drive-Upload und Drive-Analyse entfallen ersatzlos (Claude
  Code liest das Repo; eine gespiegelte Kopie ist eine zweite Wahrheit mit eigenem
  Verfallsdatum). Bewusst **dazugekommen**: eine Ergebniszeile „nicht erreicht / offen
  geblieben" (die alte Fassung listete nur Erfolge — ein Deferral hat genau die andere Sorte
  Inhalt), die Pflicht zu benennen was **nur offline** bewiesen ist, „selbst nachprüfen statt
  aus früheren Handovers übernehmen", und Entscheidungen mit Empfehlung statt Fragen ins Leere.
- **Zwei Befunde, die die Notbremse tragen** (beide neu heute, beide im Handover ausgeführt):
  1. **Dieselbe Tatsache in drei divergenten Speichern** — `KNOWN_YF_TICKERS` (12
     Namensmuster) · `instrument_universe.yf_ticker` · `TickerMapper._MAP` (7 Defaults).
     Ein Writer, einmalig, per Namensabgleich bei der Entdeckung. Ergebnis: der
     yFinance-Fallback deckt **1 von 4 aktiven Epics**. Das ist die **dritte** Instanz
     derselben Fehlerklasse wie B1 (statisches Artefakt vs. autonom wachsende Menge, ohne
     Divergenz-Erkennung).
  2. **Die Mehrquellen-Kette aus Phase 9 Step 6 lief noch nie.** `enable_ig_bars` ist
     `False` per Default, wird von keinem Startskript gesetzt, taucht in keinem Log auf. V2s
     ausdrücklicher zweiter Auftrag hieß „Daten-Input-Zuverlässigkeit" — die **entdeckende**
     Hälfte lief mit voller Geschwindigkeit, die **absichernde** blieb dunkel. Der Abstand
     zwischen beiden ist exakt der heutige Ausfall.
- **Korrektur an [`DATA_SOURCE_STRATEGY_2026-08-11.md`](./DATA_SOURCE_STRATEGY_2026-08-11.md)
  (heute früher, selbe Session):** dessen §2 stützt sich auf das Setup eines Kollegen als
  Bestätigung — der Kollege bezeichnet es selbst als **Workaround**, nicht als
  funktionierendes System. Bestätigung zurückgezogen, Richtung bleibt. Ebenso zu schwach war
  der dortige Vorschlag, „nur die Kette zu verdrahten": auf dem realen aktiven Universum hätte
  das 1 von 4 Epics abgedeckt.
- Status propagiert: Root-`CLAUDE.md` (Phasenzeile + neue Track-Zeile), `ROADMAP.md`
  (Phase-11-Header auf DEFERRED), `docs/INDEX.md` (3 Einträge), dieser Kopf.

### Next (die nächste Session startet hier)

1. **`PHASE11_DEFERRAL_HANDOVER.md` lesen** — §3 (Anforderungen A–G) und §4 (offene
   Entscheidungen) sind der eigentliche Auftrag.
2. ✅ **Nummerierung final (2026-08-11):** „Phase 12 = Datenfundament, V4 → Phase 13" —
   entschieden, in allen fünf Dokumenten nachgezogen (Root-`CLAUDE.md`, `ROADMAP.md`,
   `README.md`, `ARCHITECTURE.md`, `docs/INDEX.md`). Plan: `docs/concepts/phase12_data_foundation_plan.md`.
3. ✅ **Live-Check erledigt (2026-08-11):** `GET /markets/{epic}` (Rohdaten, nicht die
   projizierte `get_market_info`-Envelope) auf DAX (gemappt), US 500 (ungemappt), SUNDAX
   (Wochenend) — Ergebnis + B3-Margin-Felder in `phase12_data_foundation/CLAUDE.md`.
4. **Erst danach** den Datenfundament-Plan entwerfen. Ein Rewrite der Datenschicht ist
   ausdrücklich erlaubt („by all means", Nikinger 2026-08-11).
5. **Restart-Gate + Universe-Reset** unverändert gesperrt — aber **nicht mehr dringend**,
   solange nicht gemessen wird. Der Allowance-Probe-Einzeiler bleibt ein kostenloser
   Tagescheck.

### Open questions / blockers

- **Alles vom 08-08 Gebaute ist ausschließlich offline bewiesen** (1336 grüne Tests, kein Lauf
  gegen echte IG-Daten). Der nächste Daemon-Start ist ihr erster Realkontakt — beim Auswerten
  nicht mit „verifiziert" verwechseln.
- **WI-2/W2 bleibt unbeantwortet**, jetzt zum dritten Mal, und wird es bis nach dem Fundament
  bleiben. Das ist der bewusst akzeptierte Preis der Notbremse.
- **H4-as Wirkung ungemessen**, und der Alters-Cap rollt: bei einem Neustart ab **2026-08-20**
  überleben **0** Lessons und der Prompt-Block rendert dauerhaft „none on record". Gewollt,
  kein Bug — aber beim Auswerten zu wissen.
- Offene Nummerierung (s. Next 2) blockiert nichts, sollte aber vor dem nächsten Doc-Schwung
  entschieden sein, sonst wird sie in weiteren Dateien zementiert.

---
## Session stopped — 2026-08-08 (Sa — Allowance-Root-Cause + Tracker-Fix; Neustart bleibt gesperrt)

> **BLUF:** Der `/prices`-Health-Check des Nikinger hat die Diagnose der letzten Session
> umgeworfen. **Kein IG-Ausfall — unser eigenes Konto-Kontingent für historische Kursdaten,
> aufgebraucht vom Paper-Tracker.** Der Tracker-Fix ist gebaut und grün; **Universe-Reset und
> H1-Scharfschaltung sind bewusst NICHT erfolgt** — beide hängen an einem beobachteten
> `remainingAllowance`. Volle Forensik: [`ALLOWANCE_INCIDENT_2026-08-08.md`](./ALLOWANCE_INCIDENT_2026-08-08.md).

### Completed

- **Root Cause korrigiert.** Live-Check (Nikinger, 08-08 06:44 UTC) gegen `IX.D.DAX.IFMM.IP`:
  `error.public-api.exceeded-account-historical-data-allowance`. IG rechnet `/prices` in
  **Datenpunkten, nicht Requests** ab — `_PAPER_BAR_COUNT = 300` heißt 300 Punkte **pro
  Fetch**. Aus `paper_trades` rekonstruiert: ≥66 erfolgreiche Fetches ≈ **19.800 Punkte** am
  08-03/08-04, Erschöpfung nach ~einem Tag H1-Vollbetrieb. `DATA_WEEK_REVIEW_2026-08-07.md`
  §3.1/§3.2 hatte Symptom und Mechanismus richtig, die **Ursachenzuschreibung falsch**
  (dated snapshot → nicht editiert, per Konvention superseded).
- **Phase-9-Promotion-Probe als Verursacher ausgeschlossen:** `verify_instrument.py:78-79`
  nutzt `MINUTE_5` × 3 Bars = 3 Punkte/Epic/Runde, 100× billiger als der Tracker. Phase 9 ist
  **Opfer**, nicht Mitverursacher.
- **Zweiter, unabhängiger Befund — eine Datenintegritäts-Falle:** `resolve_paper_trade`
  filtert Bars nur über `timestamp >= created_utc` und prüft den SL-Treffer **bedingungslos
  vor** dem Time-Stop-Ausstieg. Der erste Tick nach einem Neustart hätte einen Teil der **390**
  liegengebliebenen `OPEN`-Zeilen mit **erfundenem** `exit_level`/`pnl_points` als `RESOLVED`
  ins WI-2-Substrat geschrieben — **auch bei gesundem Endpoint, auch ohne
  `--enable-shadow-schedule`** (`_run_paper_tracker` tickt an `enable_paper_trades` allein).
  Das ist der Grund, warum die Branch-Logik der letzten Session („gesund → Reset") nicht
  tragfähig war.
- **Fix gebaut** (2 Dateien, additiv, keine Gate-/VETO-/Order-Pfade):
  - `abstain_lessons/paper.py` — `PaperTradeTracker` bekommt `stale_after_minutes` (Trade
    älter als der Schnitt → `EXPIRED_UNRESOLVED` **ohne Fetch**) und `budget_ok` (**einmal**
    pro Tick geprüft → ein erschöpftes Budget kostet null Calls für den ganzen Tick, nicht
    einen pro Epic; gleiche Callable-Form wie das bestehende `reflect_cap_check`).
    Schnitt ist **Wanduhr**, nicht `bar_count × bar_minutes`, und wird aus
    `exec_cfg.max_hold_minutes + 60` gezogen — eine zweite hartcodierte Kopie dieser Zahl wäre
    die Drift-Klasse von Befund B1.
  - `phase8_scheduler/scripts/wiring.py` — `bar_fetch` trippt bei `RATE_LIMIT` einen
    60-Minuten-Cooldown und unterhalb eines Reserve-Floors (`_PAPER_ALLOWANCE_FLOOR = 2000`,
    **Platzhalter bis ein `totalAllowance` beobachtet ist**, existiert damit die Phase-9-Probe
    weiterläuft); `env.error` wird **nicht mehr verschluckt** (4.232 CRITICAL-Zeilen letzte
    Woche trugen den echten IG-Code nirgends); das `allowance`-Objekt wird einmal pro Prozess
    geloggt (`totalAllowance` = Deckel, `allowanceExpiry` = Reset-Termin — beides kommt gratis
    in jeder erfolgreichen Antwort und wurde bisher weggeworfen).
    `_build_paper_tracker` nimmt dafür `exec_cfg` entgegen (Call-Site mitgezogen).
- **Zur Abnahme-Eigenschaft, ohne Schönfärberei:** die letzte Session forderte „ein
  wiederholter `get_ohlcv`-Fehler muss künftiges Call-Volumen **senken**".
  `stale_after_minutes` **begrenzt** nur (monotones Wachstum → Plateau); erst `budget_ok`
  **senkt** tatsächlich, auf null während des Cooldowns. Zusammen erfüllt.
- **Verifiziert:** `pytest phase10_v3/tests` **141 passed** (138 + 3 neue). `pytest
  phase8_scheduler/tests` **229 passed**. `wiring.py` per `py_compile` (kein pytest-Testfile,
  dokumentierte „operator-run"-Konvention). **Hinweis:** die Zählungen im Modul-Tree oben
  („125 Tests") und in älteren Blöcken („P8 217/222") sind stale — real 141 bzw. 229.
  Gegen die echte DB gerechnet (read-only, Stichtag Mo 08-10 07:05 UTC): **390/390 Rückstands-
  Zeilen fallen unter den Stale-Schnitt → alle expiren beim ersten Tick, 0 Fetches.**
- **H4 gescopet** (Nikinger-Go, docs-only): [`H4_LESSON_FEEDBACK_SCOPE_2026-08-08.md`](./H4_LESSON_FEEDBACK_SCOPE_2026-08-08.md).
  Kernbefund live gemessen: **4 Trades total, alle BUY, alle Verluste** → **4 Lessons** aus
  genau diesen 4 Trades → beide Blöcke (`recent_trades` **und** `Active lessons`) stehen in
  **jedem** Prompt, inzwischen **5.973 Lesson-Renderings**. Und: `relevance_score` existiert
  als Spalte, wird als Konstante 1.0 geschrieben (`reward/recorder.py:394`) und von **keiner**
  Query gelesen — **Kandidat H4-a braucht keine Migration.** Empfehlung: H4-a (Alters-Cap)
  zuerst und allein, H4-b danach entscheiden (wird durch a evtl. gegenstandslos), H4-c erst
  wenn wieder Trades entstehen. Warnung im Doc: ein 30-Tage-Cap entfernt 3 von 4 Lessons, ein
  14-Tage-Cap alle 4 — Verhaltenswechsel für die einzige AI-Entscheidung, Nikinger-Sache.
- **Output-Style** `~/.claude/output-styles/military-brief.md` erstellt (Nikinger-Nebenauftrag,
  außerhalb des Repos, gegen die offizielle Doku verifiziert statt geraten:
  `keep-coding-instructions: true`). BLUF-Format + WHY-Sektion; die Spannung zu ponytail-full
  („drei kurze Zeilen") ist im File **ausgeschrieben** aufgelöst, über ponytails eigene
  Ausnahme für explizit angeforderte Erklärungen. Aktivierung ist ein Nikinger-Schritt
  (`/config` → Output style, wirkt nach `/clear`).

### Nachtrag (gleiche Session) — vier Folge-Fixes gebaut, alle Nikinger-freigegeben

Aus der Liste offener Punkte oben wurden vier abgearbeitet. Alles am Wochenende, Bot steht.

1. **Fetch-Versuche pro Paper-Trade gedeckelt** (`paper.py` + `wiring.py`,
   `_PAPER_MAX_FETCH_ATTEMPTS = 12`). Ein fälliger Trade braucht genau **einen** erfolgreichen
   Fetch — `_resolve_group` terminiert ihn immer, RESOLVED oder EXPIRED. Ein *fehlgeschlagener*
   Fetch ist also der einzige Weg, wie ein Trade einen Tick überlebt. Bisher wurde er jeden
   Zyklus neu geholt, bis `stale_after_minutes` griff: bis zu 60 Versuche bei 5-Minuten-Kadenz.
   Jetzt sind Retries an **fällige Trades** gebunden, nicht an die Ausfalldauer. Zähler
   in-memory (Daemon läuft tagelang; `stale_after_minutes` ist der Backstop über Neustarts —
   eine Spalte wäre eine Migration, um etwas zu begrenzen, das schon begrenzt ist). Wird
   **nicht** belastet, wenn `budget_ok` den Tick abbricht: kein Call, kein Versuch.
   **Kein reiner Gewinn — bewusster Tausch** (Advisor-Befund, Zahl daraufhin von 3 auf 12
   angehoben): der Cap verkürzt auch die Toleranz gegenüber *transienten* Fehlern (500,
   405-market-offline, Netz-Blip), und was dabei stirbt, ist eine WI-2-Messzeile — genau das
   Produkt dieser Phase. Bei 3 Versuchen wären das 15 Minuten Toleranz statt vorher 300; bei
   12 ist es ~1 Stunde, und der unbegrenzte Fall ist immer noch 5× gekappt. Für den
   Allowance-Fall ist der Cap ohnehin nicht die wirksame Bremse — dort trippt `budget_ok`
   schon beim ersten `RATE_LIMIT`.
2. **Phase-9 `check_ig_side` gefixt** (cross-phase, Nikinger-Go): `verdict` trägt jetzt
   `ig_ohlcv_error_code` — **top-level, bewusst außerhalb von `checks`**, weil sowohl
   `failed_checks` als auch `_ig_side_failed`/`_yf_side_failed` dort nach Boolean-`False`
   scannen. `promotion.py` prüft an **beiden** Call-Sites `_ig_side_indeterminate` vor jedem
   DB-Write: eine unbestimmte Runde schreibt **gar nichts** — nicht den Status, nicht
   `fail_count`, nicht `checks_json`. „Wir haben nichts gelernt" darf nichts ändern, und
   insbesondere `fail_count` **nicht zurücksetzen** (der Spiegelfehler). Verworfen:
   `ig_ohlcv_available: None` — `_ig_side_failed` läse das als Pass, und ein `discovered`
   Kandidat könnte ohne jeden OHLCV-Beweis `VERIFIED` erreichen (Verstoß gegen D6). Eng
   gehalten: ein Epic, dessen Bars aus **eigenem** Grund fehlen, demotet unverändert.
3. **B5-Restfehlerrate geschlossen** (`reflect.py`): zu lange Lessons werden auf den letzten
   **ganzen Satz** unter der Grenze getrimmt statt verworfen. Zwei Qualitätswächter, weil genau
   das die Sorge des Nikinger war: der Schnitt **muss** auf einer Satzgrenze landen (ein
   mitten im Satz gekappter Text kann das Gegenteil des Gemeinten aussagen — „…war nicht
   schlecht" → „…war nicht"), und was übrig bleibt muss substanziell sein (≥150 Zeichen).
   Sonst gilt weiter die alte Ablehnung. Text innerhalb der Grenze kommt **byte-identisch**
   zurück (die 58 von 68 gesunden Fälle sind unberührt, per Test gepinnt).
   **Grenze der Zusage, ehrlich benannt** (Advisor-Befund): getrimmt wird vom Ende, also
   bleibt der **Kopf** stehen. Eine Lesson, deren handlungsrelevanter Teil hinten steht,
   verliert ihn — und liest sich trotzdem als vollständiger Satz. Genau diese Form haben alle
   vier vorhandenen Lessons („…, was auf sauberes Risikomanagement hindeutet — überprüfe …").
   **Nicht messbar:** die 10 zu langen Texte wurden nie gespeichert, nur ihre Ablehnung. Wer
   die ersten getrimmten Lessons reviewt, prüft gezielt auf eine fehlende Schlussfolgerung.
   Die Zusage lautet „besser als nichts", **nicht** „Qualität erhalten".
4. **H4-a gebaut** (`lesson_max_age_days = 30`): rollender Alters-Cap auf die Prompt-Lessons.
   Eigener Knopf, **nicht** `quarantine_before` zweckentfremdet (einmaliger Operator-Reset mit
   festem Datum vs. stehende Policy mit wanderndem). Cutoff wird in **Python** berechnet, nicht
   in SQL: SQLites `datetime('now')` liefert `"YYYY-MM-DD HH:MM:SS"` und vergleicht sich
   **falsch** gegen die `...T...mmmZ`-Timestamps dieses Projekts — eine Falle für stille
   Fehlergebnisse, keine Stilfrage. `None` = altes Verhalten, für ein kontrolliertes A/B.

**Regression, alle Suiten einzeln** (`tests.conftest`-Kollision): P1 87 · P2 **76** · P3 100 ·
P4 155 · P5 173 · P6 76 · P7 138 · P8 229 · P9 **75** · P10 **147** · root **80** = **1336**,
0 failed. `py_compile` clean auf `wiring.py` + `verify_instrument.py`.

**Was H4-a ausdrücklich nicht ist:** es entfernt einen Dämpfer, es fügt kein Signal hinzu.
Liefert der Funnel mit nur noch einer Lesson weiterhin 0 Kandidaten, waren die Lessons nicht
die Ursache — drei Wochen Verdacht sauber ausgeschlossen, was für sich ein Ergebnis ist.
**H4-b (Doppelzählung) bleibt bewusst danach** — der Alters-Cap kann sie gegenstandslos machen,
und zwei Hebel gleichzeitig zu ziehen hat bei H1 schon Messwochen gekostet.

### Next

1. **Nikinger, das Restart-Gate:** denselben Einzeiler **einmal täglich** laufen lassen, bis
   `"ok": true` kommt, dann das `allowance`-Objekt zurückspielen. **Heute (08-08) nicht erneut
   laufen lassen** — bereits ausgeführt, Ergebnis oben; ein zweiter Lauf am selben Tag liefert
   dieselbe Antwort, weil das Kontingent an einer Perioden-Grenze zurückgesetzt wird, nicht
   fortlaufend. Ein abgelehnter Call kostet nichts (403, wird nicht abgerechnet), tägliches
   Prüfen ist also gratis.
   ```bash
   phase1_broker_wrapper/.venv/bin/python -m broker_wrapper.cli \
     --broker ig_demo ohlcv --epic IX.D.DAX.IFMM.IP --resolution MINUTE --count 5
   ```
   `totalAllowance` dimensioniert das Budget, `allowanceExpiry` datiert den Reset.
2. **Erst danach** Universe-Reset der 18 quarantined Epics (Präzedenzfall 2026-07-06). Vorher
   ist er **schädlich**, nicht nur wirkungslos: `fail_count=0` gegen ein noch erschöpftes
   Kontingent quarantäniert alle 22 binnen drei Verify-Runden erneut.
3. **Vor einer echten Messwoche: H1s Grundverbrauch budgetieren. → ENTSCHIEDEN 2026-08-11,
   eigenes Dokument:** [`DATA_SOURCE_STRATEGY_2026-08-11.md`](./DATA_SOURCE_STRATEGY_2026-08-11.md).
   Kurzfassung: IGs Kontingent ist bestätigt **10.000 Datenpunkte/Woche** (festes 7-Tage-Fenster
   ab dem ersten Request nach einem Reset, **nicht** rollend — Korrektur zur Erstannahme). H1
   bräuchte ~49.500; selbst `MINUTE_5`×60 landet bei 9.900 = 99 % ohne jede Reserve. Damit ist
   das kein Tuning-, sondern ein Architektur-Problem: **IG darf nicht die Bar-Quelle bleiben.**
   Entscheidung: der Paper-Tracker geht auf die **bereits gebaute** `ChainedBarProvider`-Kette
   (IG→yFinance, Phase 9 Step 6) — er ist der einzige Bar-Konsument, der noch fest an
   `broker.get_ohlcv` hängt. **Nicht** Lightstreamer: das ist ein Live-Tick-Strom, der Tracker
   braucht *historische* Bars; ihn dafür zu nutzen hieße den Strom selbst mitzuschreiben und zu
   persistieren — das *ist* der Eigenbau. Unabhängig bestätigt: ein Kollege des Nikinger lief
   mit eigenem IG-Setup auf dasselbe Limit und landete bei derselben Multi-Source-Antwort;
   seine Limit-Erhöhungs-Anfrage bei IG scheiterte, weshalb **kein Schritt darauf warten darf**.
   Ungebaut — Reihenfolge in §6 des Dokuments. Die alte Zwei-Hebel-Notiz darunter ist damit
   überholt, bleibt aber als Kontext stehen:
   (a) `MINUTE_5` × 60 = ⅕ der Kosten, (b) weniger Epics/Paare. **(a) nicht blind schalten** —
   `resolve_paper_trade` löst Same-Bar-SL+TP bedingungslos zu SL auf, gröbere Bars könnten den
   SL-Anteil systematisch aufblähen. Der Offline-Test dazu ist **nicht möglich** (Roh-Bars
   werden nirgends persistiert: nur Auflösungen in `paper_trades`, `data/cache/` sind
   yFinance-**Tages**bars, alle 1.082 `market_regime_snapshots` sind `quote_only` mit
   `atr_points IS NULL`). Ersatz: budgetierter Live-Test nach dem Reset — je ein
   `get_ohlcv(MINUTE,300)` und `get_ohlcv(MINUTE_5,60)` auf demselben Epic, 360 Punkte einmalig.
4. ~~H4-a bauen~~ ✅ **gebaut** (s. Nachtrag Punkt 4, `lesson_max_age_days = 30`). Der
   **Effekt** ist ungemessen — das braucht eine Woche mit laufendem Daemon, hängt also an
   Punkt 1–2. **Die Erwartung ist datumsabhängig, nicht fix** (Korrektur eines Rechenfehlers
   in der Erstfassung, Advisor-Befund): Lessons vom 07-20/07-10/07-03/07-03 gegen einen
   rollenden 30-Tage-Cap ⇒ **2 Überlebende bei Neustart am 08-09, 1 ab 08-12, 0 ab 08-20**.
   Ab dann rendert der Block dauerhaft „none on record", solange keine neuen Trades entstehen
   — Dämpfer vollständig entfernt, erreicht durch Nichtstun, **kein Bug**. Wer den Effekt
   auswertet, muss zuerst das Neustart-Datum notieren, sonst prüft er gegen die falsche Zahl.
5. **H4-b (Doppelzählung) erst nach dieser Messung entscheiden** — der Alters-Cap kann sie
   gegenstandslos machen (s. Scope-Doc §3/§4).
6. **B3** (Margin-Headroom) unverändert parkiert, eigene Session.
7. **H3/H5/H7** offen, nachrangig zu H4.

### Open questions / blockers

- **`totalAllowance`/`allowanceExpiry` unbekannt** — blockiert 1–3 oben. Der Floor-Wert 2000
  im Code ist ein **deklarierter Platzhalter**, kein gemessener Wert.
- ~~Phase-9 `check_ig_side` liest einen kontoweiten Budget-Ausfall als
  Instrumenten-Untauglichkeit.~~ ✅ **gefixt** (Nachtrag Punkt 2, Nikinger-Go für den
  Cross-Phase-Eingriff). Offline per Test bewiesen, **nicht** live — der Beweis am echten
  Universum kommt erst mit dem nächsten Daemon-Lauf.
- **Mess-Substrat WI-2 — gesichert:** die `paper_id`s der 390 Zeilen sind **vor** dem ersten
  Tick nach `OUTAGE_EXPIRED_PAPER_IDS_2026-08-08.json` geschrieben (read-only erzeugt, kein
  Schema-Zusatz) — danach wären sie nicht mehr von echten Geometrie-Expiries zu trennen. Die
  115 bereits am 08-04 expirierten sind **nicht** enthalten; für die bleibt nur die
  Datumsabgrenzung.
- **`_PAPER_ALLOWANCE_FLOOR = 2000` ist ein Ausfallrisiko, keine bloße Ungenauigkeit:** liegt
  das echte `totalAllowance` bei oder unter 2000, ist `budget_ok()` dauerhaft `False` und der
  Tracker löst **gar nichts** mehr auf — einziges Signal wäre eine CRITICAL-Log-Zeile. Nach
  dem ersten erfolgreichen Fetch das geloggte `allowance`-Objekt prüfen und ggf. senken.
- **W2 (Sub-Noise-Geometrie) weiterhin unbeantwortet** — jetzt zum dritten Mal an einer
  Infrastrukturfrage statt am Funnel gescheitert.
- ~~B5-Restfehlerrate~~ ✅ **gefixt** (Nachtrag Punkt 3, Satzgrenzen-Trimmung mit zwei
  Qualitätswächtern).
- **Neu offen — der Floor und H4-a sind beide ungemessen:** `_PAPER_ALLOWANCE_FLOOR` wartet auf
  ein echtes `totalAllowance`, H4-as Wirkung auf eine Woche mit laufendem Daemon. Beide sind
  gebaut und getestet, aber **offline** — keiner von beiden hat je gegen echte IG-Daten gelaufen.

---

## Session stopped — 2026-08-07 (Fr — erste H1-Live-Woche ausgewertet, read-only)

> Read-only Datenwoche-Review, angestoßen durch den Nikinger ("week is over now. wanna have a
> look? the bots paused, everything should be safe"). Kein Code berührt, keine Migration, kein
> Scheduler-Neustart — nur `mode=ro`-DB-Reads + Log-Lesen, exakt wie die beiden Vorwochen-
> Reviews. Vollständige Auswertung: `phase10_v3/DATA_WEEK_REVIEW_2026-08-07.md`.

### Completed
- Verifiziert: Scheduler lief die ganze Woche durchgehend (ein Start 2026-08-01 12:18 lokal,
  kein Neustart, kein Crash), sauberer Stop kurz vor dieser Session (kein `KILL`-File, letzter
  Reconcile 23:13 lokal). **Kein Order-Risiko** — 0 echte Trades, `trade_outcomes` unverändert
  seit 07-20.
- **Funnel weiterhin vollständig kollabiert:** 360 `abstain_records`, 100 % `REASON_NO_CANDIDATES`,
  5/5 Tage — unverändert gegenüber den beiden Vorwochen, nichts Neues.
- **H1 produzierte wie geplant** (600 Shadow-Pairs geöffnet, 0 `open_scheduled_pairs failed`)
  — aber deckte dabei einen **IG-`/prices`-Endpoint-Ausfall** auf, der ab 08-04 einsetzte und
  bis zum letzten Verify-Versuch heute (08-07 15:14 lokal) anhält. Erst als Chat-Erstauswertung
  falsch gelesen (52 SL / 43 TP als "Trefferquote"), dann per Advisor-Pass korrigiert: die
  SL/TP-Verteilung eines Both-Sides-Paars ist mechanisch gekoppelt, keine Edge-Aussage — s.
  Review §2 für die korrigierte Lesart.
- **Root Cause identifiziert:** nicht der 30-Minuten-`shadow_schedule_interval_min` (öffnet nur
  neue Paare), sondern die vorbestehende **5-Minuten-`_run_paper_tracker()`-Kadenz** (Block B,
  seit 07-17, vor H1 mit fast nichts zu tun) — ein wachsender Rückstand fälliger `OPEN`-Trades
  erzeugt monoton eskalierende `get_ohlcv`-Fehlversuche (218→516→786→1148→1564 CRITICAL-
  Zeilen/Tag, Σ 4232). **Korrektur der eigenen Empfehlung aus der letzten Session:** dort stand
  "der Intervall-Regler ist die Stellschraube, falls die Allowance zu heiß läuft" — falsch für
  dieses Ausfallmuster, der Intervall-Regler wirkt auf einen anderen Mechanismus.
  `instrument_universe.checks_json` liefert einen sauberen endpoint-spezifischen Beleg
  (`get_market_info`-Checks grün, `ig_ohlcv_available: false`, gleiche Verify-Runde).
- **Kaskaden-Schaden gefunden:** dieselbe `check_ig_side`-Probe läuft unabhängig von H1 auch in
  der Phase-9-Promotion-Pipeline — 18 von 22 `instrument_universe`-Epics sind jetzt
  `quarantined`, **inklusive des seit Wochen live-verifizierten Kerns** (DAX/CAC/IBEX/AEX/STXE,
  `point_value_source='ig_fields'`). Die verbleibenden 4 aktiven Epics stehen bei
  `fail_count=2` gegen `demote_after_fails=3` — eine Verify-Runde vom vollständigen Leerlauf
  entfernt. Das ist der wichtigste Befund der Woche, nicht die Shadow-Pair-Zahlen selbst.
- **WI-2/W2 bleibt unbeantwortet** — 0 `TIME_STOP` unter den 95 resolved Pairs ist ein Artefakt
  des Ausfalls (keine Bars bis `time_stop_utc`), keine Antwort auf die Geometrie-Frage.
- Zwei Nebenbefunde protokolliert, nicht gefixt: B5-Restfehlerrate (10/68 Reflect-Versuche
  überschreiten weiterhin die 300-Zeichen-Grenze trotz des 07-31-Fixes), `env.error` wird in
  `wiring.py::_build_paper_tracker`s `bar_fetch` verschluckt — die gesamte Diagnose dieser
  Woche lief über `instrument_universe.checks_json`, nicht über die 4232 CRITICAL-Zeilen selbst,
  die den echten IG-Fehlercode nirgends trugen.
- `phase10_v3/DATA_WEEK_REVIEW_2026-08-07.md` geschrieben + in `docs/INDEX.md` registriert.
  Vorheriger Session-Block (2026-08-01, H1 built) verbatim nach `SESSIONS_ARCHIVE.md` rotiert.

### Nachtrag (gleiche Session, Chat-Follow-up) — Strategie-Priorisierung für die
### Wochenend-Session morgen

Der Nikinger fragte nach einer Gesamteinordnung über alle drei Datenwochen + diesen Vorfall
hinweg. Ein Advisor-Pass vor der Antwort korrigierte drei Punkte an der Erstfassung — die
Korrekturen sind unten bereits eingearbeitet, nicht separat vermerkt:

1. **Das Universum ist eingefroren, nicht am Verfallen.** Die Promotion-Pipeline läuft nur,
   wenn der Daemon läuft — solange der Bot pausiert ist, tickt keine Uhr gegen die 4
   verbleibenden aktiven Epics. Das Risiko ist **nicht** „jeder Tag, der vergeht", sondern **der
   nächste Daemon-Start mit einem noch toten Endpoint**. Das nimmt den falschen Zeitdruck fürs
   Wochenende raus — der Health-Check vor dem Neustart ist der eigentliche Gate, keine Uhr.
2. **Der Tracker-Fix braucht eine benannte Eigenschaft, keine bloße Form.** „Kadenz
   entkoppeln/drosseln" beschreibt eine Form, keine Anforderung. Die tatsächlich nötige
   Eigenschaft: **ein wiederholter `get_ohlcv`-Fehler muss künftiges Call-Volumen SENKEN, nicht
   erhöhen.** Heute ist es umgekehrt — ein Fehler lässt den Trade `OPEN`, `OPEN`-Trades
   akkumulieren, der nächste Tick hat mehr Epics zum erneuten Scheitern. Ein reines
   Intervall-Verlängern verlangsamt nur dieselbe Divergenz, kehrt sie nicht um. Der Mechanismus
   (Backoff, Circuit-Breaker, Retry-Cap pro Trade) ist der Wochenend-Session überlassen — aber
   er muss zusätzlich die **bestehenden 328 Rückstands-Zeilen** behandeln, nicht nur neuen
   Rückstand verhindern.
3. **`env.error` nicht verschlucken** bleibt ein kleiner, kostenloser Mitnahme-Fix im selben
   File (`wiring.py::_build_paper_tracker`s `bar_fetch`).
4. **Korrektur der eigenen Zuschreibung:** H1 hat den Ausfall nicht *verursacht* — es hat das
   Call-Volumen erhöht, das eine bereits vorhandene Phase-9-Lücke (`check_ig_side`s
   Demote-bei-IG-Fail-Pfad) freigelegt hat. Dieser Pfad hätte bei jedem sustained
   `/prices`-Ausfall demotiert, unabhängig von H1 (steht bereits so in
   `DATA_WEEK_REVIEW_2026-08-07.md` — hier nur nochmal explizit festgehalten, damit die
   Zuschreibung im Kopf konsistent bleibt).
5. **Die H3/H4/H5/H7-Sequenzierung neu bewertet, mit einer Empfehlung, nicht nur einer Frage:**
   die bisherige Reihenfolge gatete H4 (Lesson-Feedback-Loop) auf eine „saubere H1-Woche". Das
   Gate ist jetzt **dreimal an drei unabhängigen Gründen gescheitert** (Tracker-Bug Woche 1,
   Funnel-Kollaps Woche 2, IG-Ausfall Woche 3) — das ist selbst Evidenz, dass das Gate
   unzuverlässig ist, nicht dass eine saubere Woche kurz bevorsteht. H4s eigene Evidenzbasis
   hängt nicht von WI-2 ab: W5 ist bereits bestätigt, 4.529 Lesson-Renderings, explizites Zitieren
   in jeder bisher eingefangenen Begründung, jetzt drei Wochen in Folge dasselbe Abstain-Muster.
   **Empfehlung: H4 muss nicht auf H1 warten** — Scoping kann parallel zum Infra-Fix laufen,
   braucht keinen laufenden Daemon. Ehrliches Gegenargument aus H7s eigener Logik: nicht an der
   Richtungslogik drehen, bevor die Geometrie bekannt ist. Aber H4 ist keine Richtungslogik —
   es entfernt einen Dämpfer, der die **Sample-Erzeugung selbst** unterdrückt, eine andere
   Kategorie als das, was H7 meinte. Die ursprüngliche Reihenfolge hat das vermutlich vermengt.
   **Das ist eine Empfehlung, keine getroffene Entscheidung** — der Nikinger kann sie morgen
   bestätigen oder überstimmen, ohne dass vorher etwas umgeschrieben werden muss.

### Next (morgige Wochenend-Session startet hier)

1. **Nikinger, vor allem anderen:** ein einzelner `get_ohlcv`-Live-Call gegen z. B.
   `IX.D.DAX.IFMM.IP`, um `/prices` zu bestätigen. Kein Zeitdruck (s. Punkt 1 oben) — aber
   nichts danach ist sicher zu sequenzieren, ohne das zu wissen.
2. **Branch auf das Ergebnis:**
   - Gesund → DB-Reset der 18 quarantined Epics (Präzedenzfall 2026-07-06).
   - Weiterhin tot → **keinen Neustart**, auch nicht ohne `--enable-shadow-schedule` — der
     nächste Punkt (Fix) kommt zuerst so oder so.
3. **Bevor irgendein Neustart mit dem Flag passiert:** der Tracker-Fix nach der oben benannten
   Eigenschaft (Punkt 2 im Nachtrag) + der `env.error`-Mitnahme-Fix, im selben File.
4. **Erst danach H1 wieder scharf schalten** für eine echte Datenwoche.
5. **H4 (Lesson-Feedback-Loop) parallel scopen** — unabhängig von 1–4, kein laufender Daemon
   nötig, s. Empfehlung Punkt 5 oben. Startpunkt: `DATA_WEEK_REVIEW_2026-07-31.md` §5 H4 (die
   drei konkreten Kandidaten: Relevanz-Decay, Doppelzählungs-Ende, Lesson-Skopierung).
6. **B3 (Margin-Headroom) bleibt unverändert parkiert**, unabhängig von alldem — eigene Session,
   startet mit dem live `/markets/{epic}`-Check (`phase5_execution/CLAUDE.md`).
7. **H3/H5/H7** bleiben offen, jetzt nachrangig zu H4 statt gleichrangig gegatet.

### Open questions / blockers
- **Root Cause des IG-`/prices`-Ausfalls selbst** (Wochenkontingent erschöpft vs. etwas
  anderes) — nicht aus dem Repo feststellbar, braucht den Live-Check aus Next #1.
- **W2 (Sub-Noise-Geometrie) weiterhin unbeantwortet** — unverändert der Wurzel-Punkt, jetzt
  zum dritten Mal an einer externen Störung statt am Funnel selbst gescheitert.
- **H4-vor-H1-Empfehlung ist unbestätigt** — s. Nachtrag Punkt 5, wartet auf Nikinger-Go/No-Go.

---

## Session stopped — 2026-08-01 (H1 built: time-scheduled shadow pairs, default OFF)

> Building session on the same working thread as the earlier 2026-08-01 (Phase 11 claim +
> B4/H6 + B3-deferred) session — that block rotated verbatim to `SESSIONS_ARCHIVE.md`. Per the
> Nikinger's confirmed ordering, H1 (time-scheduled shadow pairs) was the next content step: it
> decouples paper-trade measurement from the collapsed research funnel entirely and answers W2,
> the root open question everything else is gated on. Planned in Claude-Code plan mode first
> (anchors verified against live code before writing any line), approved, then built atomically.

### Completed
- **`PaperEngine.open_scheduled_pairs(epics, deadline=None)`** (`phase10_v3/abstain_lessons/
  paper.py`) — a new, lean entry point alongside the existing event-triggered
  `on_debate_abstain`: one shared `now` per tick, opens a Both-Sides-Shadow pair per epic via
  the existing (unmodified) `open_shadow_pair`, each epic isolated in its own try/except
  (mirrors `PaperTradeTracker.tick`'s per-epic isolation) so one epic's quote-fetch failure
  never blocks the rest. Synthetic `abstain_record_id = f"sched:{uuid4()}"` (schema-verified:
  the column has no FK) — the `sched:` prefix keeps these trivially distinguishable from
  debate-triggered pairs (bare UUIDs) in later analysis, per the review's own recommendation.
  Deliberately **no** Council-Paper-Call from this path — that call is conceptually tied to an
  actual debate-abstain, not a bare timer tick. +6 tests in `phase10_v3/tests/test_paper_engine.py`.
- **`deadline` guard, added after an Advisor pass caught a real correctness gap in the first
  cut:** `PaperTradeTracker` only ticks during the WINDOW phase, so a pair opened late enough
  that `now + max_hold_minutes` lands after `window_close` would sit unresolved overnight; worse,
  `resolve_paper_trade` checks SL/TP touch on **every** bar with no cut-off at `time_stop_utc`,
  so a next-morning gap bar can register as a "touch" hours after the intended hold ended — a
  fabricated fill, not a real one. Fixed by skipping the **whole tick** (same `now`/
  `max_hold_minutes` for every epic, so either all would overrun the deadline or none would)
  when the prospective time-stop would exceed a passed-in `deadline`. `wiring.py`'s
  `shadow_pair_scheduler()` computes that deadline as today's `config.window_close` in the
  daemon's tz and passes it through — `resolve_paper_trade` itself is **untouched** (it's shared
  with the debate-triggered path; a behaviour change there is its own decision, not folded in
  here). +3 more tests in `test_paper_engine.py` (skips whole tick past deadline / proceeds
  within it / `deadline=None` stays unrestricted).
- **Scheduler wiring** — the exact structural precedent as the Phase-9 `universe_refresher`
  (injected closure + fail-soft fire-and-forget wrapper + throttled caller via the shared
  `_due_after` helper), with one deliberate difference: **no preflight firing** (a timer tick
  needs no daemon-start warm-up, unlike a universe refresh):
  - `phase8_scheduler/scheduler/config.py`: `enable_shadow_schedule: bool = False`,
    `shadow_schedule_interval_min: int = 30`. **Corrected sizing (post deadline-guard, do not
    use the review's ~130-136 figure):** with `window_close=17:30` and `max_hold_minutes=240`,
    the last productive tick is 13:30, so at the 8-epic active universe this is **10 ticks ×
    8 epics ≈ 80 pairs/day**, not 130 — the guard trades some volume for a same-day-clean
    sample. Still answers WI-2 in ~1-2 sessions instead of two dead weeks. Two tuning levers if
    more volume is wanted: shrink `shadow_schedule_interval_min` (20 min → ~14 productive ticks
    ≈ 112 pairs/day) or shorten the scheduled pairs' own hold (would need a separate
    `max_hold_minutes` for this path — not built, `open_scheduled_pairs` reuses the shared
    `ExecutionConfig.max_hold_minutes` today). No new CLI flag on the interval (mirrors
    `universe_refresh_interval_min`/`reflect_daily_cap` — config-only default).
  - `phase8_scheduler/scheduler/state.py`: `last_shadow_pairs_ts: str | None = None` — cross-day,
    kept across `rollover_if_new_day` (same category as `last_universe_refresh_ts`).
  - `phase8_scheduler/scheduler/runner.py`: `shadow_pair_scheduler` ctor param,
    `_run_shadow_pair_scheduler()` (fail-soft) + `_maybe_run_shadow_pairs()` (throttled), called
    from the WINDOW phase right after `_maybe_refresh_universe` — independent of the auto-confirm
    gate, since paper trades never touch real trade caps.
  - `phase8_scheduler/scripts/wiring.py`: a `shadow_pair_scheduler()` closure inside
    `build_scheduler()`, gated on `enable_paper_trades AND enable_shadow_schedule` both true,
    queries `UniverseStore.active_universe()` (identical pattern the `universe_refresher` closure
    already uses) for the active epic list, computes today's `window_close` deadline, and calls
    `paper_engine.open_scheduled_pairs(epics, deadline=deadline)`. No dedicated test file for
    `wiring.py` (documented "operator-run, not pytest-collected" convention) — verified via
    `py_compile`.
  - **`phase8_scheduler/scheduler/run.py`: `--enable-shadow-schedule` CLI flag** (mirrors
    `--enable-ig-bars`/`--enable-paper-debate` exactly — `store_true`, threaded into
    `config_from_args`). Caught by the same Advisor pass: without this, `enable_shadow_schedule`
    had no path to `True` via the documented `python -m scheduler.run` entry at all.
  - +9 tests in `phase8_scheduler/tests/test_runner.py` (none/runs-once/throttled/re-fires-after-
    interval/not-in-non-WINDOW-phases/fail-soft, mirroring the `universe_refresher` test block),
    +2 default assertions in `test_config.py`, +2 field roundtrip assertions in `test_state.py`,
    +1 CLI-flag-threads-through test in `test_run.py`.
- **Ships default OFF** (`enable_shadow_schedule=False`) — bit-identical to today's behaviour
  until the Nikinger consciously arms it (mirrors `enable_paper_debate`'s discipline), given the
  real IG-allowance cost. No live/network run this session (repo convention: live runs are the
  Nikinger's job) — that's the natural next step once armed.
- Full cross-phase regression before AND after all edits, everything green: **P1 87 · P2 75 ·
  P3 100 · P4 155 · P5 173 · P6 76 · P7 138 · P8 229 (was 222, +7) · P9 72 · P10 138 (was 132,
  +6) · meta_m1_harness 28 · root 77.**
- Earlier 2026-08-01 session-block (Phase-11-claim + B4/H6 + B3-deferred) verbatim nach
  `SESSIONS_ARCHIVE.md` rotiert.

### Next
- **Operator (Nikinger):** flip `--enable-shadow-schedule` on a live demo run once ready (paper
  trades already default on), and watch the IG-allowance budget — the interval is the tuning
  knob if it's too hot. This is what actually answers W2 (do the paper pairs' SL/TP/time-stop
  resolution rates look like the review's W2 hypothesis predicts). **Open verification item for
  that live run:** confirm whether IG's `get_ohlcv(epic, "MINUTE", 300)` returns only
  trading-hours bars or includes out-of-hours — this determines how much slack the deadline
  guard actually needs; not verifiable from the repo, only from a live call.
- **B3 (its own session, whenever the Nikinger picks it up):** start with the live `/markets/
  {epic}` inspection — see `phase5_execution/CLAUDE.md`'s B3 block for the exact plan.
- **`resolve_paper_trade`'s no-cutoff-at-`time_stop_utc` behaviour** (flagged, not fixed — see
  the deadline-guard note above): if a future session wants belt-and-braces protection on the
  debate-triggered path too (not just H1's scheduled pairs), that means changing shared Block-B
  code — a decision for the Nikinger, not a silent fold-in.
- **H3/H4/H5/H7** remain fully open, data-gated on H1's live results per the review's own
  ordering — read the resolved scheduled pairs before touching any of them.
- Scheduler daemon still not started — unchanged, an operator decision outside this session.

### Open questions / blockers
- **W2 (Sub-Noise geometry) still unanswered** — the whole point of shipping H1 is to answer it;
  needs a live run with the flag armed, not more code.
- None new from this session's own work (all edits additive, full regression green) beyond the
  two items above, both already actioned (deadline guard + CLI flag) or explicitly deferred.

---

## Session stopped — 2026-08-01 (Phase 11 claimed + B4/H6 fixed + B3 designed-and-deferred)

> Follow-up in the same working thread as the 2026-07-31 bugfix session. Four design questions
> from that session's summary were put back to the Nikinger via `AskUserQuestion` instead of
> being decided unilaterally: (1) B3 approach → **"do it correctly, defer with documentation"**
> (rejected the quick `max_leverage` buffer hack); (2) B4/H6 → **"do the full scope now"**;
> (3) H1 → **confirmed separate session** (no build here); (4) the Phase-11/V4 naming collision →
> **"claim Phase 11 for the H1-H7 work, renumber V4 to Phase 12."** All four executed as answered.

### Completed
- **B4/H6 fixed, full scope** (`phase10_v3/DATA_WEEK_REVIEW_2026-07-31.md` §4 B4): the empty
  measurement substrate now gets filled on every NO_TRADE/ABORT/TRADE cycle:
  - `phase5_execution/execution/executor.py::_no_trade` now threads its own `reason` string
    into `cycle_outcome["detail"]` (was computed for the `ExecutionResult` but never handed to
    the classifier — every branch's `AbstainRecord.detail` landed at the model default `""`).
    `phase10_v3/abstain_lessons/classifier.py::classify_abstain` reads it on all 5 branches.
  - `spread_pct` now reaches `ContextRecorder.on_decision` at all three call sites
    (`_no_trade` when a Gate-4 price snapshot is already in scope, i.e. sizing/VETO failures;
    `_abort`'s post-`place_order` call site; `_notify_opened`'s TRADE path) — the recorder
    already accepted the param, the gap was purely that no call site passed it. Early gates
    (1/2/3/5, debate) still pass `None` — no price snapshot exists yet at that point, so `None`
    is correct, not a regression.
  - **The dominant `research_empty` case** (364/366 records in the review week) needed a
    cross-phase bridge: Gate 2's own `detail` is a fixed generic string, never the LLM's actual
    abstain prose (`Research.last_no_pick_reasoning`, held on the `Research` object `research_tick`
    already drove that same cycle). New `phase8_scheduler/scripts/wiring.py::_enrich_abstain_detail`
    wraps the abstain sink (same pattern as the existing `_observed_abstain_sink`) and backfills
    `cycle_outcome["detail"]` with the model's real reasoning when present, only for
    `research_empty` cycles — a preflight/exception abstain (no LLM call happened) keeps Gate 2's
    generic detail.
  - +5 tests in `phase5_execution/tests/test_executor.py` (detail-carries-rationale for debate
    and VETO paths, spread_pct present/absent across NO_TRADE/ABORT/TRADE), +7 tests in
    `phase10_v3/tests/test_classifier.py` (detail threaded on every branch, defaults to `""`,
    coerces `None` safely). **P5 168 → 173, P10 125 → 132.** `wiring.py` unaffected test count
    (222, no dedicated test file, verified `py_compile`).
- **B3 designed, deliberately NOT fixed** — the Nikinger rejected the quick `max_leverage`
  buffer (a static guess, doesn't scale per-instrument, same failure pattern as B1's stale
  doc-note). `phase5_execution/CLAUDE.md`'s B3 block now carries the full why (margin cap has
  zero headroom, empirically 22.0 accepted / 22.1 rejected) + what (P1 needs a live `/markets/
  {epic}` inspection to confirm IG's actual margin field names — a live/network call, Nikinger's
  job per repo convention — then a new `MarketInfo` field + a margin-based `compute_size` cap,
  cross-phase P1+P5, with the fail-closed-vs-fallback question left as an explicit open design
  call for that session) — enough for a cold start next time, no re-derivation needed.
- **Phase-11/V4 naming collision resolved.** `ROADMAP.md`'s "Phase 11" (the old deferred V4:
  Council/Handover/Reward-Reform/Force-Trigger/Instinct-ECC) is now **Phase 12**, content
  unchanged (`11a-e` → `12a-e`, `phase11_v4/` → `phase12_v4/`). **Phase 11** is now claimed for
  this data-week-review-driven funnel/measurement work (H1-H7 + B1-B5) — living in `phase10_v3/`
  for now, **no physical directory move** (a separate, larger decision, not made here). Updated:
  `ROADMAP.md` (new Phase 11 section + renumbered Phase 12), root `CLAUDE.md` (phase table),
  `ARCHITECTURE.md` (3 refs + a dated correction note), `README.md`, `phase9_universe/CLAUDE.md`,
  `docs/INDEX.md`. Left untouched (dated snapshots, never edited):
  `phase10_v3/DATA_WEEK_REVIEW_2026-07-31.md`, `docs/concepts/phase9_v2_foundation_plan(1).md`.
- Full cross-phase regression before AND after all edits: **P1 87 · P2 75 · P3 100 · P4 155 ·
  P5 173 (was 168) · P6 76 · P7 138 · P8 222 (unaffected) · P9 72 · P10 132 (was 125) ·
  meta_m1_harness 28 · root 77.**
- Session-Block 2026-07-31 (B1/B2/B5 bugfix session) verbatim nach `SESSIONS_ARCHIVE.md` rotiert.

### Next
- **H1 (next, separate session, per the Nikinger's confirmation):** time-scheduled shadow pairs
  — decouples paper-trade measurement from the collapsed research funnel, the review's
  highest-leverage item. Needs a new scheduler tick + a leaner `PaperEngine` entry point (today's
  `on_debate_abstain` expects a real `AbstainRecord`; the time-scheduled path needs the ~10-line
  variant the review sketched) + an IG-allowance budget for ~136 extra quote-calls/day. Not
  scoped in detail this session (the Nikinger chose to let the next session do that fresh).
- **B3 (its own session, whenever the Nikinger picks it up):** start with the live `/markets/
  {epic}` inspection — see `phase5_execution/CLAUDE.md`'s B3 block for the exact plan.
- **H3/H4/H5/H7** remain fully open, data-gated on H1's results per the review's own ordering.
- Scheduler daemon still not started — unchanged, an operator decision outside this session.

### Open questions / blockers
- **W2 (Sub-Noise geometry) still unanswered** — still the root question; H1 answers it in days.
- None new from this session's own work (all edits additive, full regression green).

---

## Session stopped — 2026-07-31 (bugfix follow-up session, bot stopped — B1/B2/B5 fixed)

> Special-Task-Session (Nikinger): „Weekend blocks went through, there's an analysis file with
> tasks for Phase 11 — this is a bug-fixing phase." Scope confirmed via `AskUserQuestion` before
> any edit: fix exactly B1+B2+B5 (the three the review flagged as fixable without waiting on the
> Phase-11/H1-H7 scope call); B3/B4 stay open for a design decision; B1(b)'s fail-closed guard
> only fires when `point_values` is populated (keeps 14 existing P5 tests untouched — verified by
> grep before choosing the shape, on advisor's flag). Bot/scheduler confirmed not running, no
> `KILL` file, before touching any code.

### Completed
- **B1 fixed, two parts** (`phase10_v3/DATA_WEEK_REVIEW_2026-07-31.md` §4 B1): (a)
  `phase8_scheduler/scripts/wiring.py` now sources `ExecutionConfig.point_values` from
  `_build_universe_from_db()` (already existed in the same file, fail-soft to
  `EXTENDED_UNIVERSE`) instead of the static 4-epic list; (b)
  `phase5_execution/execution/sizing.py::compute_size` fails closed
  (`(0.0, "point_value_unmapped")`) for an epic missing from a **populated** `point_values` map,
  instead of silently sizing at the 1.0 default — `point_value_for()` itself is unchanged
  (its 1.0 default now only fires on an empty/unwired map), so `executor.py:379`'s
  `build_opened(point_value=...)` call stays bit-identical. +1 test
  (`test_point_value_unmapped_epic_fails_closed_when_map_populated`). **P5 167 → 168.**
- **B2 scale fixed, residual explicitly NOT fixed** (`...` §4 B2):
  `phase7_reward/reward/scorer.py:115` now divides `debate_confidence` by 100 before centering
  (`DebateOutcome.confidence` is 0-100, the formula assumed [0,1]). Rescaled 5 existing
  `debate_confidence` values in `test_scorer.py` to the real scale + added 1 new regression-pin
  test replicating the review's Trade-7 numbers (confidence=60, a near-total loss must not clamp
  to the cap). **Deliberately left open, per the review's own warning:** the score still drifts
  ~+1.2 per consecutive loss after this fix (`clean_exit_bonus` still pays out on a
  `CLOSED_BY_BROKER` stop-out) — whether a stop-out counts as a "clean exit" is Phase-11 H3, not
  addressed here. **P7 137 → 138.**
- **B5 fixed** (`...` §4 B5): both `build_abstain_prompt` and `build_paper_lesson_prompt`
  (`abstain_lessons/reflect.py`) now state the `_MAX_LESSON_CHARS` limit in the prompt text
  itself (sourced from the constant, not a hardcoded "300") — previously only
  `validate_abstain_lesson` enforced it, so the LLM was never told, causing paid-for/rejected
  calls (6 on 2026-07-27, 4 too long). Also fixed the sibling `build_abstain_prompt`, which had
  the identical drift and would have hit it the first time a lesson ran long. **P10 125
  unchanged** (no test pins exact prompt wording; behavior covered by existing
  `validate_abstain_lesson` tests).
- **Not touched, by design:** B3 (margin headroom — needs a Nikinger design call), B4 (empty
  measurement substrate — that's H6, part of the still-open Phase-11 scope decision), all of
  H1-H7, S6 (stays OFF).
- Full cross-phase regression run before AND after all edits (shared venv
  `phase1_broker_wrapper/.venv`): **P1 87 · P2 75 · P3 100 · P4 155 · P5 168 (was 167) · P6 76 ·
  P7 138 (was 137) · P8 222 (unaffected, no dedicated `wiring.py` test file — verified via
  `py_compile`) · P9 72 · P10 125 (unaffected) · meta_m1_harness 28 · root 77** — every other
  phase's count is bit-identical to the fresh pre-edit baseline captured at session start.
- Docs committed in two atomic commits: (1) the prior read-only session's 6 modified
  `CLAUDE.md`/`INDEX.md` files + the new `DATA_WEEK_REVIEW_2026-07-31.md`, unchanged from that
  session; (2) this session's code fixes + the three phase `CLAUDE.md` "NOT YET FIXED" → fixed
  flips (P5/P7/P8, each in the same commit as its fix, per the commit⇒note-update rule).
- Session-Block 2026-07-31 (the data-week review) verbatim nach `SESSIONS_ARCHIVE.md` rotiert.

### Next
- **Nikinger, Entscheidung (unverändert offen, s. Review §5/§8):** Phase-11-Scope, Reihenfolge
  **H2 → H1 → H6**, danach mit echten Daten H7/H4/H3/H5. H2's B1-Anteil ist jetzt erledigt; H2's
  verbleibender Anteil ist **B3** (Margin-Headroom).
- **Naming-Kollision zu flaggen:** `ROADMAP.md` definiert „Phase 11" bereits als das deferred
  „V4: Sophisticated/Optional" (Council/Handover/Reward-Reform/Force-Trigger/Instinct-ECC,
  `phase11_v4/` noch nicht angelegt) — das ist **nicht** dasselbe wie diese Bugfix-Session oder
  die H1-H7-Hypothesen aus dem Datenwoche-Review. Keine `phase11_v4/`-Struktur in dieser Session
  angelegt; die Nikinger-Entscheidung zur H-Reihenfolge sollte auch klären, ob/wie die
  ROADMAP-Nummerierung angepasst wird.
- B3/B4/H1-H7 bleiben wie vom Review vorgeschlagen — kein Code dafür in dieser Session.

### Open questions / blockers
- **W2 (Sub-Noise-Geometrie) weiterhin unbeantwortet** — unverändert die Wurzel, H1 liefert die
  Antwort in Tagen (unverändert aus dem 07-31-Review).
- Scheduler-Daemon weiterhin nicht gestartet (bewusst — Restart ist ein Operator-Schritt, kein
  Teil dieser Bugfix-Session).

---

## Session stopped — 2026-07-31 (Fr — zweite Datenwoche ausgewertet, read-only; 3 neue Bugs + Phase-11-Scope)

> Special-Task-Session (Nikinger): „Datenwoche ist rum — sag direkt, wenn etwas schiefgelaufen
> ist; wenn genug Daten da sind, tiefe Analyse + Hypothesen für Phase 11." Kein Code-Touch,
> DB nur `mode=ro` (Wochentags-Regel). Advisor vor dem Report konsultiert — sein
> Diskriminator-Query (Regime-Snapshots auf dem Happy Path) hat B4 von „leer weil Funnel leer"
> auf „teils Design, teils Verdrahtungslücke" präzisiert; seine Warnung zu B2 (Ein-Zeichen-Fix
> repariert den Loop nicht) ist im Report als eigene Rechnung belegt.

### Completed
- **`DATA_WEEK_REVIEW_2026-07-31.md`** (neu, 📕 dated, in `docs/INDEX.md`) — vollständige
  Auswertung. Kernzahlen der Woche: **366 Research-Zyklen, 1 Kandidat, 1 Debatte, 0 Trades,
  0 neue Paper-Trades**, 364 Abstain-Records zu 100 % `REASON_NO_CANDIDATES`. Mechanik
  einwandfrei (0 `consecutive_failures`, kein Kill, 10/10 Tage stabil) — der Funnel selbst
  ist der Ausfall.
- **WI-1 + WI-5 sind beantwortet, W1 + W5 bestätigt.** Es gab rote Tage (3 von 4 auswertbaren
  DAX-Sessions negativ). Am 07-30, bei breiter europäischer Schwäche, erzeugte Research
  **einen BUY** auf dem einzigen Instrument mit positivem Drift und schrieb die Begründung
  selbst hin: *„a SELL on DAX/CAC/IBEX [is] tempting, **but** recent trade history shows 4
  consecutive BUY losses on DAX — avoiding that instrument."* Die Verluste dämpfen die
  **Instrumentenwahl**, nicht die Richtungswahl. Stand kumulativ: 30 Debatten, 29 BUY-Seeds
  vs. 1 SELL, **nie ein Richtungs-Flip**, 8× TRADE (alle BUY).
- **WI-2 zum zweiten Mal tot** — diesmal ohne Bug: der Shadow-Pair-Trigger ist
  `REASON_DEBATE_ABSTAIN`, und die eine Debatte der Woche sagte TRADE. WI-3 bestätigt (10/10
  Tage an der 200k-Kappe, Research endet 15:2x). WI-6 ohne neue Evidenz.
- **Drei neue harte Bugs, alle seit Rollout falsch, alle exakt nachgerechnet** (Details +
  Fix-Ausdrücke im Review-Doc §4):
  1. **B1 `point_value`-Drift** (`phase8_scheduler/scripts/wiring.py:616`): `point_values`
     kommt aus der statischen 4-Epic-`EXTENDED_UNIVERSE`, Research handelt aber die
     8-Epic-DB-Universe → AEX mit 1,0 statt **40,0 €/Punkt** → **40× Oversizing**
     (Size 26,8 = 1,18 Mio € Nominale, Risiko am Stop **120 % des Kontos**). Erklärt **alle
     drei** AEX-Rejects (07-15/07-20/07-30) und löst damit den als „unrettbar verloren"
     abgelegten Bug-B-Vorfall vom 07-15. **50 % aller 8 TRADE-Entscheidungen der Historie sind
     an Sizing-Config gestorben, nicht am Markt.**
  2. **B2 Reward-Score-Inversion** (`phase7_reward/reward/scorer.py:115`): `debate_confidence`
     wird als [0,1] behandelt, geliefert wird 0–100 → `process_delta` +92,25 statt ~+3 →
     per-Trade-Delta clamped **immer** auf +5 → Score **55→60→65→70 über vier Totalverluste**
     → `get_risk_level()` = AGGRESSIV → `risk_pct` 3 % statt 2 %. Die Unit-Tests kodieren die
     falsche Skala (`debate_confidence=0.9`), deshalb unsichtbar. ⚠ **Der Skalen-Fix allein
     repariert es nicht** (bliebe +1,2/Verlust, weil ein SL-Treffer den `clean_exit_bonus`
     kassiert) — das ist eine Phase-11-Designfrage.
  3. **B5 Paper-Lesson-Prompt** (`abstain_lessons/reflect.py:62-65` vs. `:78`): Prompt sagt
     „max. zwei Sätze", Validator erzwingt ≤300 Zeichen, die Grenze steht nicht im Prompt →
     am 07-27 6 Reflect-Calls bezahlt, 2 Lessons persistiert.
- **Zwei strukturelle Lücken (B3/B4, brauchen Designentscheidung, kein Quickfix):**
  Leverage-Cap ohne Margin-Headroom (Nominale konstruktionsbedingt auf `available × 20`
  gepinnt; 22,1 rejected / 22,0 accepted am selben Vormittag) und das **leere Mess-Substrat**
  (alle 1.036 `abstain_records` mit `detail=''`/`context_json='{}'`; alle 722
  `market_regime_snapshots` `quote_only`/NULL — Bars sind dokumentierte Degradation,
  `spread_pct` dagegen eine echte Verdrahtungslücke an den drei `_notify_context`-Call-Sites).
- **Korrektur am 07-27-Block:** der Bug-2-Fix vom 07-25 **ist** live bewiesen — am 07-27 liefen
  6 Haiku-Calls über denselben gefixten `_AbstainLLMAdapter._SCHEMA` (Abstain-Sink *und*
  Paper-Pfad teilen ihn), 2 Lessons persistiert, kein HTTP 400. Der 07-27-Block sagte „kein
  Call wurde versucht" — das galt nur für den Debatte-Abstain-Pfad, nicht für den Adapter.
- **Der Kern-Befund** (Review §3): eine geschlossene Rückkopplung — 4 SL-Verluste → 4 Lessons
  („prüfe die Entry-Qualität", **4.529× in den Prompt gerendert**) + dieselben 4 Verluste als
  zweiter Kanal via `recent_trades` → Modell abstaint 365/366 und begründet es wörtlich damit
  → keine Trades → keine neuen Outcomes → die 4 alten Lessons bleiben. Ein **absorbierender
  Zustand**, aus dem sich der Loop nicht selbst befreien kann.
- Session-Block 2026-07-27 verbatim nach `SESSIONS_ARCHIVE.md` rotiert.

### Next
- **Nikinger, Entscheidung:** Phase-11-Scope. Vorschlag im Review §5, Reihenfolge
  **H2 → H1 → H6**, danach mit echten Daten H7/H4/H3/H5:
  - **H2** Sizing-Wahrheitskette (B1-Fix + fail-closed statt still 1,0 + Margin-Headroom) —
    klein, sicherheitskritisch, **vor** jedem Live-Gedanken.
  - **H1** *(größter Hebel)* Messung vom Funnel entkoppeln: Shadow-Pairs **zeitgesteuert**
    statt an `REASON_DEBATE_ABSTAIN` gekoppelt. 8 Epics × alle 30 min ≈ **130 Paare/Tag**,
    risikofrei, null LLM-Kosten, beantwortet **WI-2 an einem Tag**. Nutzt `PaperEngine` +
    `PaperTradeTracker` unverändert; neu ist nur ein Scheduler-Tick (Muster:
    `universe_refresher` + `_due_after()`).
  - **H6** Mess-Substrat füllen (`last_no_pick_reasoning` in die ohnehin geschriebene
    `abstain_records`-Zeile; `spread_pct` durchreichen) — klein, ~70 Begründungen/Tag statt 1.
- **B1/B2/B5 sind fixbar, ohne den Phase-11-Scope abzuwarten** (klein, additiv, in bereits von
  V3 berührtem Code). Bei B2 **zwingend** die Testskala in `test_scorer.py` mitziehen, sonst
  bleibt der Fix ungeprüft. Alles am Wochenende bei gestopptem Bot.
- **⚠ S6 bleibt AUS.** Die 5 vorhandenen Paper-Lessons sind tautologisch, auf beiden Seiten
  desselben Paares wortgleich und aus Backfill-Artefakten abgeleitet.

### Open questions / blockers
- **W2 (Sub-Noise-Geometrie) ist weiterhin unbeantwortet** und ist die Wurzel: solange nicht
  klar ist, ob 30/45 Punkte auf DAX überhaupt gewinnbar sind, ist jede Arbeit an der
  Richtungslogik verfrüht. H1 liefert die Antwort in Tagen.
- Der Scheduler-Daemon lief bei Analyse-Ende (Fr 21:26 lokal) nicht mehr (letzter Reconcile
  21:22, kein Prozess). Freitagabend unauffällig — falls das nicht der Nikinger war, startet
  er Montag aber auch nicht von selbst.
- N1 (`INSUFFICIENT_FUNDS`) ist **kein** Beobachtungspunkt mehr, sondern durch B1/B3
  vollständig erklärt.

---

## Session stopped — 2026-07-27 (Mo — Tag-1-Quick-Check der neuen Datenwoche, read-only)

> Special-Task-Session (Nikinger): Quick-Check, ob die beiden am 2026-07-25 gefixten Bugs
> wirklich tot sind und Tag 1 der neuen Datenwoche wie erwartet lief. Kein Code-Touch,
> DB nur `mode=ro` (Wochentags-Regel).

### Completed
- **Bug 1 (Paper-Tracker `MINUTE_1`→`MINUTE`) ✅ live-bestätigt:** erster Tracker-Tick heute
  07:05:40Z löste alle 15 hängenden Paper-Trades der Vorwoche auf; heute **null** 422/`MINUTE_1`
  in `research_health.jsonl` (die 7 Grep-Treffer im Log sind Vorwoche bzw. Timestamp-Zufall).
  **⚠ Daten-Caveat zu den 15 Backfill-Auflösungen:** `resolve_paper_trade` ist first-touch über
  die *gelieferten* Bars — für die 7 Tage alten Trades lagen nur die heutigen MINUTE-Bars vor
  (max. 1000 Bars ≈ 16h zurück), der echte Pfad 07-20→07-27 wurde nie gescannt. Ergebnis-Muster
  (alle BUY→TP +45, alle SELL→SL −30, identisches `resolved_utc`) spiegelt nur "Markt steht
  heute über den Entries von 07-20". Für WI-2-Auswertung **nicht als echte R-Multiples werten**
  — Mechanik bewiesen, Zahlen sind Backfill-Artefakte. Frische Pairs dieser Woche werden korrekt
  aufgelöst (Time-Stop 240 min, Bars reichen dann).
- **Bug 2 (`reflect_abstain`-Schema) ⚪ heute nicht testbar, aber kein Fehler:** Sink reflektiert
  per Default nur `stage=DEBATE` (`sink.py:49`), heute waren alle 72 Abstains
  `research_empty/reason_no_candidates` → 0 Lessons ist **korrektes** Verhalten, kein
  HTTP-400/Fehl-Event in den Logs (es wurde schlicht nie ein Call versucht). Live-Bestätigung
  des Fixes kommt erst mit dem ersten Debatte-Abstain der Woche.
- **Tag-1-Gesundheitsbild:** Mechanik sauber — 72 Zyklen, 72× `abstain_recorded` +
  72× `context_recorded` (1:1), `consecutive_failures: 0`, kein Kill, Reconcile tickt bis in
  den Abend. yFinance-Circuit früh offen (09:00–09:31 lokal, `^GDAXI` 0 rows), danach voll
  erholt — bekanntes Degrade-Verhalten. Budget-Kappe beendete Research ~15:26 lokal
  (WI-3-Muster, unverändert). 0 echte Trades, 0 neue Paper-Trades (kein Zyklus erreichte
  Kandidaten-/Debatte-Stufe).
- **N2 (Funnel-Kollaps) wiederholt sich + frische W5-Evidenz:** 72/72
  `REASON_NO_CANDIDATES`, Ursache heute belegbar LLM-seitig (`picked: false`,
  `LLM_ABSTAIN`, "validator abstain (no pick)"). Die Abstain-Begründung in
  `scheduler_state.json` zitiert **explizit die aktiven Lessons** ("Four consecutive losing
  BUY trades … active lessons explicitly warn about poor entry quality") — die 4 historischen
  SL-Stops in `trade_outcomes` dämpfen via P7-Lessons den Research-Pick. Das ist die erste
  frische Evidenz für W5 (Lesson-Dämpfung) seit der Vordiagnose: der Funnel-Kollaps ist
  mindestens teilweise **strukturell** (Lesson-Feedback-Schleife), nicht nur Marktregime.

### Next
- **Operator (Nikinger):** Woche weiterlaufen lassen (kein Eingriff nötig). Beobachten:
  1. erster Debatte-Abstain → prüfen, ob `reflect_abstain` jetzt eine Lesson schreibt
     (Bug-2-Live-Bestätigung) und ob Shadow-Pairs frisch erzeugt + binnen ~4h aufgelöst werden.
  2. `INSUFFICIENT_FUNDS`-Beobachtungspunkt aus 07-25 unverändert (heute nicht aufgetreten —
     es gab keine Order).
- Bei der Wochen-Auswertung die 15 Backfill-Rows (alle `resolved_utc` = `2026-07-27T07:05:40Z`)
  aus der WI-2-Statistik ausschließen oder separat ausweisen.
- W5-Frage für die V4-Scope-Diskussion mitnehmen: Lesson-Dämpfung drosselt aktuell den
  gesamten Funnel — gewollt konservativ oder Überkorrektur? (Entscheidung Nikinger, nicht
  diese Woche.)

### Open questions / blockers
- Keine neuen Blocker. Bug 2 formal noch ohne Live-Positiv-Beweis (mangels Debatte-Abstain) —
  Code-Fix steht, Logs zeigen keinen Fehlversuch.
- N1 bleibt reiner Beobachtungspunkt (heute keine Order, daher keine neue Evidenz).

---

## Session stopped — 2026-07-25 (Sa — erste Datenwoche ausgewertet, 2 Bugs gefunden + gefixt)

> Special-Task-Folgesession (Nikinger): Bot lief Mo–Fr mit `--enable-paper-debate` (s. Session
> 2026-07-19), Wochenende-Auswertung entlang WI-1…WI-6. Advisor konsultiert vor dem Report
> (bestätigte die Einordnung + gab die Fix-Priorisierung: MINUTE_1 sofort, reflect_abstain erst
> nach Mechanismus-Bestätigung).

### Completed
- **`DATA_WEEK_REVIEW_2026-07-25.md`** (neu, 📕 dated, in `docs/INDEX.md`): WI-2 (Shadow-Pairs,
  das Schlüssel-Experiment) **tot** — 15 Paper-Trades erzeugt, 0 aufgelöst. WI-1 (roter Tag →
  SELL-Seed) **untestbar** — Di–Fr 100 % `REASON_NO_CANDIDATES`, kein einziger Zyklus erreichte
  die Kandidaten-Stufe; Montags einziger Handelstag war durchgehend positiv-driftend. WI-3
  (Budget-Kappe ~14–15 Uhr) + WI-4 (Paper-Trigger selten) **bestätigt**. Zwei neue Befunde:
  **N1** zwei Broker-Rejects `INSUFFICIENT_FUNDS` (DAX + AEX, selber Vormittag, ein dritter
  Trade selben Vormittags erfolgreich) — widerlegt die unbestätigte AEX-Stop-Distanz-Hypothese
  aus der Bug-B-Session. **Operator-Check nachgeliefert (Nikinger, `broker_wrapper.cli`, selber
  Tag):** `get-account` → `available == balance` = 26.815,63 € exakt, `get-positions` → `[]` —
  **kein Dauer-Margin-Problem, Stale-Deal-Hypothese widerlegt.** Montags Reject bleibt
  unerklärt, aber nachweislich transient (kein Fix, nur Beobachten nächste Woche, s. Review-Doc).
  **N2** Funnel-Kollaps Di–Fr ist schlechter als die Vorwoche, Ursache
  (Marktregime vs. strukturell) mit einer Woche nicht unterscheidbar. **Empfehlung: kein
  V4-Scope aus dieser Woche** — beide Schlüssel-Fragen unbeantwortet wegen kaputter Messwerkzeuge,
  nicht wegen fehlender Marktbewegung.
- **Zwei Bugs root-caused + gefixt** (`scripts/wiring.py`, dated 🔁-Note in
  `phase8_scheduler/CLAUDE.md`): (1) `PaperTradeTracker`s `bar_fetch` rief `get_ohlcv(epic,
  "MINUTE_1", …)` — ungültige IG-Resolution, 422 Fehlschläge diese Woche, 0/15 Paper-Trades je
  aufgelöst seit Block B (07-17). Fix: `"MINUTE"`. (2) `_AbstainLLMAdapter._SCHEMA` fehlte
  `additionalProperties: False` → Anthropic lehnt den Structured-Output-Call ab (HTTP 400,
  in den Logs bestätigt) → Klartext-Fallback → `json.loads` scheitert immer → `reflect_abstain`
  hat **seit Rollout (07-15) nie** eine Lesson erzeugt. Fix: Feld ergänzt (Muster aus dem
  bewährten `brain.py`-Schema). Beide additiv, ein-Wert-Korrekturen in bereits von V3 berührtem
  Code, am Wochenende bei gestopptem Bot. `scripts/wiring.py` hat laut Projekt-Konvention keine
  eigene Testdatei ("operator-run, not pytest-collected") — verifiziert via `py_compile` (clean)
  + volle Regression (**P8 222 · P10 125, beide unverändert** — nur String-/Dict-Literale
  berührt, kein getestetes Modul).
- Session-Block 2026-07-19 rotiert nach `SESSIONS_ARCHIVE.md`.

### Next
- **Operator (Nikinger):**
  1. ✅ **erledigt diese Session:** `get_account`/`get_positions`-Check (N1) — Konto gesund,
     kein Dauerproblem. Verbleibt nur als **Beobachtungspunkt**: taucht `INSUFFICIENT_FUNDS`
     nächste Woche wieder auf, direkt danach `get-account` laufen lassen (nicht Tage später),
     um den zeitlichen Zusammenhang zu fangen.
  2. Nächste Datenwoche starten (gleicher Command, Fixes sind bereits im Code) — dort WI-1/WI-2
     erneut prüfen, jetzt mit funktionierender Paper-Pipeline; beobachten, ob N2 (Funnel-Kollaps)
     sich wiederholt.
  3. Row-id=6-Korrektur (Bug A) und `enable_paper_debate`-Frage sind erledigt/entschieden;
     unverändert offen: keine neuen Blocker.
- V4-Scope-Entscheidung bleibt auf eine saubere Woche verschoben (kein Schnitt diese Session).

### Open questions / blockers
- **N1** ist kein Blocker mehr (Konto-Check bestanden) — nur noch ein Beobachtungspunkt bei
  Wiederauftreten, kein offener Live-Check.
- Unverändert offen: `used_in_research`/Lesson-Dämpfung (W5) hat diese Woche keine frische
  Evidenz geliefert, bleibt aus der Vordiagnose unverändert gültig.

---

## Session stopped — 2026-07-19 (Sa — read-only Strukturdiagnose vor der V4-Datenwoche)

> Special-Task-Session (Nikinger): kein Code-Touch, keine DB-Writes (`mode=ro` durchgehend).
> Auftrag: strukturelle Schwächen hinter „fast nur BUY-Trades, alle per SL gestoppt" finden,
> mit Daten-/Code-Beweis, plus Watch-Items für die Datenwoche ab Montag 2026-07-20 — damit V4
> aus echten Befunden geformt wird statt aus Vermutungen.

### Completed
- **`TRADE_DATA_DIAGNOSIS_2026-07-19.md`** (neu, 📕 dated, in `docs/INDEX.md` eingetragen):
  6 belegte Befunde + falsifizierbare Watch-Items WI-1…WI-6. Kurzfassung:
  - **W1** BUY-Bias = Abstain-Asymmetrie in P4: bei positivem Drift → BUY-Seed (19/20
    Debatten), bei negativem Drift → Abstain statt SELL (Smoking Gun: 07-17
    `last_no_trade_detail`, LLM erwägt SELL zweimal und verwirft ihn). Kein Clamp aktiv.
  - **W2** Fixe 30-pt-Stop-Distanz ist auf DAX (~0.117 %) Sub-Noise — unter der eigenen
    Momentum-VETO-Schwelle (0.15 %/h); Geometrie 30/45 = EV ≈ 0 vor Kosten; Trades 4/5 in
    3.6–9.3 min exakt −30 pts gestoppt. Auf AEX wären dieselben 30 pts 2.73 % (Faktor ~23).
  - **W3** `daily_token_budget=200k` wird JEDEN Handelstag erreicht (5/5 Tage 195k–203k) →
    Research endet täglich ~14–15 Uhr, Nachmittag blind.
  - **W4** Paper-Pipeline (das V4-Datenwerkzeug) triggert fast nie: 98.4 % der Abstains sind
    `REASON_NO_CANDIDATES` (kein Paper-Trigger); `paper_trades` = 0 Zeilen.
  - **W5** Lesson-Loop dämpft generell statt richtungsspezifisch (3 identische Stop-out-
    Lessons in jedem Prompt, zitiert als Abstain-Grund auch gegen SELL).
  - **W6** Gate 1 erlaubt Entries bis 17:30, Square-off ist 17:15 — Spät-Entries haben
    verkürzte/negative Max-Haltezeit (Trade 4: Entry 16:58).
  - Explizit NICHT kaputt: Mechanik/Sizing/Fail-closed/VETOs — kein Execution-Bug.

### Next
- **Operator (Nikinger), vor/während der Datenwoche ab Mo 2026-07-20:**
  1. **Empfehlung: `enable_paper_debate=True` flippen** (gebaut + getestet, Cap 3/Tag) —
     ohne den Flip bleibt WI-2/WI-4 mangels `paper_trades`-Zeilen unbeantwortbar.
  2. Bot Montag normal starten (Neustart-Pickup + erste `market_regime_snapshots`/
     `decision_context`-Zeilen sind weiterhin offene Beweis-Punkte aus der Vorsession).
- **Auswertung am Wochenende 2026-07-25/26** entlang WI-1…WI-6 (Queries stehen in der
  Diagnose-Datei); daraus den V4-Scope schneiden.
- Unverändert offen aus Vorsessions: Row-id=6-Korrektur (Bug A), Reflect-Pfad
  `lesson_extracted=0`, AEX-Reject-Hypothese (jetzt self-diagnosing).

### Open questions / blockers
- Keine technischen. Reine Lese-Session; einzige Edits: neue Diagnose-Datei, `docs/INDEX.md`
  (+1 Zeile), dieser Session-Block (Rotation regelkonform).

---

## Session stopped — 2026-07-17 (WE 2 follow-up: Bug A + Bug B fixed, Council-Paper-Call built)

> Same-day follow-up to the Block-B session above (now rotated to `SESSIONS_ARCHIVE.md`).
> Nikinger's special task: "this session is only actually solving these bugs + papertrade
> council logic." All three delivered. Advisor consulted twice (once before implementation —
> caught a real timezone defect in the planned Bug-A fix before it shipped; the Council-
> Paper-Call reuse-shape question was also resolved there, since the plan's own `[VERIFY aus
> §5.5]` pointer turned out to reference a section that doesn't exist in the plan doc).

### Completed

**Bug A — FIXED** (`phase7_reward/reward/pnl_resolver.py`, cross-phase, dated 🔁-note in
`phase7_reward/CLAUDE.md`): `resolve()` branch 3 now rejects any `get_trade_history`
candidate whose `close_date` predates the trade's own `open_ts` (new `_parse_instant`
helper — tz-aware, compares in UTC, conservative/no-reject on parse failure).
**Advisor-caught defect avoided:** a naive string compare across `open_ts` (local offset,
e.g. `+02:00`) and IG's `close_date` (UTC) would have rejected legitimate same-day matches
too. `_OpenCtx` (`recorder.py`'s cold-reconcile path) gained `open_ts`. +4 tests, **P7 133 →
137**, including a golden replay of the row-6 incident and a dedicated tz-correctness case.
**Not done:** correcting the already-persisted bad row (`id=6`) — needs a live
`get_trade_history` read (deal `DIAAAAXZEYXT8BC` should be settled by now) + a manual DB
`UPDATE`, both left to the Nikinger (network + live-DB write are operator actions per
project convention).

**Bug B — root cause confirmed correct, visibility gap closed, root reason unrecoverable**
(`phase5_execution/execution/executor.py`, dated 🔁-note in `phase5_execution/CLAUDE.md`):
the 2026-07-15 AEX order was a genuine broker `REJECTED` → `ExecutionAbort` — correct
fail-closed behavior, not a gate/VETO/order-path bug. But `_abort()`'s `_notify_context`
call hardcoded `veto_results_json={"vetos": "pass"}`, dropping the actual `detail` (IG's
reject reason) — so even with last session's ABORT-visibility fix, a future rejection would
still need stderr access to know why. Fixed: `detail` now folds into
`{"vetos": "pass", "abort_detail": detail}` (no schema change). **The original 2026-07-15
reason itself is confirmed unrecoverably lost** — checked `logs/` (only covers 2026-07-16+,
daemon restarted since) and `journalctl` (nothing bot-related for that window). **Flagged
to the Nikinger, unconfirmed:** the rejected instrument was AEX, not DAX — the fixed
`stop_distance_points`/`limit_distance_points` (30/45) apply to every epic, and the existing
v1.5-hotfix note already flags non-DAX `point_values` as provisional; the same DAX-
calibration risk plausibly extends to stop/limit distances tripping an IG minimum-distance
rule on the ~1000-level AEX index. Unconfirmed — watch for it on the next rejection, now
self-diagnosing from the DB.

**Council-Paper-Call (§10.3) — built, off by default** (`enable_paper_debate` stays `False`,
matches the plan's Drop-Order + the Nikinger's build-then-flip pattern for every other V3
flag):
- `phase6_debate/debate/prompts.py` (dated 🔁-note in `phase6_debate/CLAUDE.md`): additive
  sibling to the live Judge — `build_paper_pick_prompt(digest)` + `_paper_pick_schema()` +
  `_PAPER_PICK_SYSTEM` (forced BUY/SELL, no ABSTAIN branch, one-sentence rationale). Zero
  diff to `build_judge_prompt`/the live Bull/Bear/Judge orchestrator. **P6 70 → 76** (+6).
- `phase10_v3/abstain_lessons/paper.py`: `PaperDebateCaller` (`request_pick(digest) ->
  tuple[str,int]|None`, injected `llm` + `prompt_builder` — no `debate` import, phase
  isolation preserved by construction, verified again by `test_separation_guarantees.py`).
  `PaperEngine` gained `council_daily_cap` (default 3) and `_maybe_council_pick`: after the
  shadow pair, checks `store.count_today(COUNCIL_PICK, ...)` against the cap, calls
  `debate_caller.request_pick({"epic","bid","ask"})` (same quote already fetched for the
  shadow pair — no second IG call), inserts a `COUNCIL_PICK` `PaperTrade` with
  `council_confidence` set on a valid pick. Digest is deliberately thin (epic + one quote)
  — `PaperEngine.on_debate_abstain` only ever receives a sparse `cycle_outcome`
  (confirmed: `AbstainRecord.detail`/`.context_json` are never actually populated by
  `classify_abstain` today — a separate, pre-existing gap, out of this session's scope, not
  touched). **P10 113 → 125** (+12: `PaperDebateCaller` validation + `PaperEngine`
  integration).
- `phase8_scheduler/scripts/wiring.py`: `_build_paper_engine` now builds a
  `PaperDebateCaller` when `config.enable_paper_debate` (lazy import, mirrors the existing
  `enable_abstain_reflect` LLM-construction pattern exactly — same `get_credential`/
  `LLMClient`/`ResearchConfig`). Model = `DebateConfig().model_judge` (Sonnet, matching the
  real Judge — deliberately not the cheap Haiku reflect model; the cap keeps cost trivial
  regardless). `py_compile` clean; not pytest-collected (scripts convention).

### Verifiziert
- Volle Cross-Phase-Regression: P1 87 · P2 75 · P3 100 · P4 155 · P5 **167** (unverändert —
  Bug-B-Fix erweiterte einen Bestandstest statt einen neuen anzulegen) · P6 **76** (+6) ·
  P7 **137** (+4) · P8 221 (unverändert) · P9 72 · P10 **125** (+12) · meta_m1_harness 28 ·
  root 77.
- Kein Live-/Netz-/Smoke-Test diese Session (kein neuer Broker-/Order-Pfad berührt) —
  Live-Verifikation (inkl. `enable_paper_debate`-Flip, wenn gewünscht) bleibt Operator-Aufgabe.

### Next
- **Operator (Nikinger):**
  1. Row-`id=6`-Korrektur (Bug A): optional, network + live-DB write, s. o. — nur falls die
     historische Zeile es wert ist, korrigiert zu werden.
  2. AEX-Stop-Distanz-Hypothese (Bug B): unbestätigt, beobachten bei der nächsten
     ABORT-Zeile (jetzt self-diagnosing via `decision_context.veto_results_json`).
  3. `enable_paper_debate=True` flippen, wann gewünscht — Council-Paper-Call ist gebaut +
     getestet, aber bewusst noch nicht live.
  4. Montag-Restart-Beweis Runde 2 (aus der Vorsession, weiterhin offen): erste echte
     `market_regime_snapshots`/`decision_context`/`paper_trades`-Zeilen protokollieren.
- **Reflect-Pfad-Watch-Item** (aus dem Week-1-Review, weiterhin offen): warum
  `lesson_extracted=0` bei allen realen `REASON_DEBATE_ABSTAIN`-Records — unverändert aus der
  Vorsession, nicht Teil dieser Session's Scope.

### Open questions / blockers
- Keine technischen. Volle Regression grün, keine VETO-/Gate-/Order-Pfad-Änderung diese
  Session (Bug-B-Fix ist rein additiv an einer bereits Nikinger-autorisierten Beobachtungs-
  Naht, kein neuer Order-Pfad-Touch).

---

## Session stopped — 2026-07-17 (WE 2: Block B live — market_context + Paper-Pipeline)

> **Zwei vom Nikinger geflaggte Anomalien** wurden zuerst forensisch untersucht (read-only,
> DB + `execution_state.json` + `llm_usage.json` + `logs/`), beide root-caused, keine davon
> diese Session gefixt (Nikinger: dokumentieren, Fix später):
> - **Bug A** (Trade `id=6`, 2026-07-10): `close_level`/`profit_loss` waren **byte-identisch**
>   zu Trade `id=5` (anderes Epic, 7 Tage älter) — der `pnl_resolver`-Fallback-Match
>   (`phase7_reward/reward/pnl_resolver.py`) hat keinen Plausibilitäts-Guard und griff die
>   einzige größen-passende (aber völlig unpassende) History-Transaktion. Dokumentiert in
>   `phase7_reward/CLAUDE.md` (dated 🔁-Block), Fix vorgeschlagen (Reject bei
>   `close_date < eigener open_ts`), nicht angewandt (Phase-7-Code, außerhalb Block-B-Scope).
> - **Bug B** (2026-07-15T11:57:34): Debatte entschied `TRADE`/`BUY`, Broker **REJECTED**
>   (`execution_state.json`: `deal_id: null`) → `ExecutionAbort` — **korrektes** Verhalten
>   (root-`CLAUDE.md`-Vokabular), aber ABORT-Zyklen waren bis dato für `decision_context`
>   unsichtbar (dieselbe Lücke wie beim `abstain_sink`). **Nikinger-Entscheidung: Block B
>   erweitert `context_recorder` auf ABORT** (s. u.) — Scope-Erweiterung über den
>   ursprünglichen Plan hinaus.

### Completed

**Step-8-Nachzügler:** `phase10_v3/WEEK1_REVIEW_2026-07-17.md` (Nikinger: "wenn du die Daten
hast, mach es jetzt") — 318 reale `abstain_records` seit Montag-Restart (313
`REASON_NO_CANDIDATES`, **erste 5 echte `REASON_DEBATE_ABSTAIN`** am 2026-07-15, alle
dasselbe AEX-Kandidat über den Tag verteilt debattiert). Watch-Item: alle 5 zeigen
`lesson_extracted=0` trotz `enable_abstain_reflect=True` — `reflect_abstain` ist
best-effort/schluckt Fehler still, kein Stderr-Log für diesen Tag verfügbar zur
Root-Cause-Klärung; nicht blockierend, vermerkt für den nächsten Live-Lauf.

**Step 9 — `phase10_v3/market_context/`** (neues Paket, `pyproject.toml`-`include` um
`market_context*` erweitert, editable reinstalled): `models.py` (`RegimeSnapshot`/
`DecisionContext`, Felder = Migration-005-Spalten — **Schema lag bereits seit Block A auf
main**, keine neue Migration nötig), `regime.py` (`compute_regime_features`/
`classify_regime_tag`, deterministisch, **degradiert immer auf `data_source="quote_only"`**
— verifiziert: `pre_trade_check`/`veto_momentum` geben die `get_ohlcv`-Bars nie nach außen,
kein VETO-Code-Touch nötig/erlaubt diese Session, s. Regime §14-Fallback), `writer.py`
(`MarketContextWriter` + `ContextRecorder.on_decision`, Bull/Bear-Summary aus
`DebateOutcome.transcript` — letzter `BULL`/`BEAR`-Turn).

**P5-Executor-Naht** (`executor.py`): neuer keyword-only `context_recorder=None`.
**Drei** Call-Sites (nicht zwei): `_notify_opened` (TRADE), `_no_trade`/`_notify_no_trade`
(NO_TRADE — `AbstainSink.on_no_trade` **Rückgabetyp erweitert** `-> str | None`, liefert den
echten `record_id` für den FK-Link; **nicht** die `_observed_abstain_sink`-Re-Klassifizieren-
Masche kopiert, die mintet pro Aufruf eine neue UUID4 → falscher FK), und **neu** `_abort`
(ABORT, nur am post-`place_order`-Call-Site — der frühe Session-Health-Abort bekommt bewusst
keinen `candidate` übergeben, bleibt unaufgezeichnet). `_abort` von `@staticmethod` zu
Instanzmethode (wie `_no_trade` in Block A). **Default `None` ⇒ bit-identisch** (161→161
Bestandstests unverändert, **+6 neue Naht-Tests → P5 161→167**). Dated 🔁-Block in
`phase5_execution/CLAUDE.md` (+ ein retroaktiver Block für Block A's `abstain_sink`, der dort
bisher fehlte).

**P8-Wiring:** `enable_context_persistence=True` (Config), `_build_context_recorder` +
`_observed_context_recorder` (`context_recorded`-Event, mirrors `_observed_abstain_sink`).
**P8 217→221 Tests** (+4: none/fires/not-in-window/fail-soft — analog `universe_refresher`).

**Step 10 — Paper-Pipeline** (`abstain_lessons/paper.py`, Modelle lagen seit Block A):
`open_shadow_pair` (Both-Sides-Shadow, liest **direkt** `config.stop_distance_points`/
`limit_distance_points`/`max_hold_minutes` — kein `compute_size`-Call nötig, das liefert nur
`size`, nicht Distanzen), `resolve_paper_trade` (First-Touch SL/TP, Bars ab `created_utc`
gefiltert, Same-Bar⇒konservativ SL, kein Touch bis Time-Stop⇒`TIME_STOP`, sonst `None`⇒
Aufrufer setzt `EXPIRED_UNRESOLVED`), `PaperEngine` (`on_debate_abstain`, doppelter
V3-D5-Guard, `debate_caller` akzeptiert aber **nie aufgerufen** — Council-Paper-Call
deferred, s. u.), `PaperTradeTracker` (`tick()`, ein `bar_fetch`-Call je betroffenem Epic,
Reflect einmal pro aufgelöstem Paar über den gemeinsamen Cap). `PaperTradeStore.
count_lessons_today` ergänzt (mirrors `AbstainStore`).

**P8-Wiring:** `enable_paper_trades=True`, `enable_paper_debate=False` (Config).
`_build_paper_engine`/`_build_paper_tracker` (eigene `get_price`/`get_ohlcv`-Closures über
den geteilten Broker; `_PAPER_BAR_COUNT=300` 1-Min-Bars, deckt `max_hold_minutes=240`
komfortabel). `PaperEngine` in `AbstainLessonSink(paper_engine=...)` injiziert (Naht
existierte seit Block A). `SchedulerRunner` bekam `paper_tracker=None`-Param (mirrors
`universe_refresher`), `_run_paper_tracker()` getickt in der WINDOW-Phase nach dem
Executor-Run. **P8 221 unverändert + 4 neue Runner-Tests** (bereits oben gezählt).

**§10.4 Trennungs-Garantien** (`phase10_v3/tests/test_separation_guarantees.py`):
AST-basierter Import-Scan (kein Substring-Grep — `market_context` als Wort existiert schon
länger unabhängig in P7s `market_context_json`/`market_context: dict`-Parameter, ein
Substring-Match hätte falsch positiv getroffen): `paper.py`/`paper_store.py` importieren
keinen Broker-Order-Pfad und kein `execution`-Paket; `reward/` importiert nirgends
`abstain_lessons`/`market_context`. P7s **eigene 133 Tests bleiben unverändert grün** — kein
Byte in `phase7_reward/reward/` diese Session verändert (nur die dated Bug-A-Notiz in
`CLAUDE.md`), das **ist** der Confidence-N-Unberührtheits-Beweis.

**S7 `abstain_report.py`:** `--paper`-Flag (Counts je Variant/Exit,
Abstain-Validierungsquote — beide Shadow-Seiten negativ/breakeven = Abstain validiert).
Default (`--paper` weg) bit-identisch zu Block A (goldener Test explizit dafür).

### Verifiziert
- Volle Cross-Phase-Regression: P1 87 · P2 75 · P3 100 · P4 155 · P5 **167** (+6) · P6 70 ·
  P7 133 (unverändert) · P8 **221** (+4) · P9 72 · P10 **113** (+46: Regime/Writer 19,
  Paper-Engine 22, Separation 3, Report 2) · meta_m1_harness 28 · root 77.
- `py_compile` clean auf `scripts/wiring.py` (nicht pytest-importiert, Konvention).
- Kein Live-/Netz-/Smoke-Test diese Session (Scheduler-Daemon vom Nikinger gestoppt für die
  Session) — Live-Verifikation bleibt Operator-Aufgabe.

### Next
- **Operator (Nikinger):** Scheduler-Restart ist ein bewusster Schritt. Montag-Restart-Beweis
  Runde 2 (Plan §11): erste echte `market_regime_snapshots`/`decision_context`/
  `paper_trades`-Zeilen — wortgleich protokollieren, sobald verfügbar.
- **Bug A** (`pnl_resolver`-Plausibilitäts-Guard): offen, Fix-Vorschlag in
  `phase7_reward/CLAUDE.md`, wartet auf Nikinger-Priorisierung.
- **Council-Paper-Call (§10.3):** diese Session **deferred**, am Sessionende erneut gefragt
  (Nikinger, 2026-07-17: "leave it for a future session, context is already very full") —
  bleibt offen für einen Folge-Termin, keine weitere Rückfrage nötig, bis der Nikinger es
  selbst anstößt.
- **Reflect-Pfad-Watch-Item** (aus dem Week-1-Review): warum `lesson_extracted=0` bei allen 5
  realen `REASON_DEBATE_ABSTAIN`-Records trotz `enable_abstain_reflect=True` — braucht Stderr/
  Log-Sicht während eines laufenden Live-Fensters, nicht aus persistiertem State
  rekonstruierbar.

### Open questions / blockers
- Council-Paper-Call: s. Next. Sonst keine technischen Blocker — volle Regression grün,
  keine VETO-/Gate-/Order-Pfad-Änderung diese Session.

---

## Session stopped — 2026-07-11 (WE 1: Block A live on main — Migration 005 + abstain_lessons)

> **Nebenbefund am Sessionstart (nicht Teil dieses Plans):** Phase-8-Scheduler-Kill-Switch
> war bis zu ~63h wirkungslos (uncapped POST_WINDOW-Sleep) — diagnostiziert, gefixt
> (Nikinger-Freigabe), Prozess gestoppt (`kill -9`), dokumentiert in
> `phase8_scheduler/CLAUDE.md` → `## Session stopped — 2026-07-11`. Der Scheduler steht seit
> dieser Session (KILL-Datei, `manual:dashboard`); Restart ist ein bewusster Operator-Schritt.

### Completed
- **Migration `005_v3_learning.sql`** (`phase2_persistence/migrations/`): `abstain_records` +
  `paper_trades` (additiv), **DROP+CREATE** von `market_regime_snapshots`/`decision_context`
  (Nikinger-Freigabe via AskUserQuestion — FK-inkompatibel, 0 Zeilen, keine Live-Referenz;
  dokumentierte Ausnahme von Phase 2s "additive only"-Regel, s.
  `phase2_persistence/CLAUDE.md` Don't-Liste). **Backup vor Migration:**
  `data/trading_bot.sqlite.2026-07-11.bak` (gitignored, `*.bak`-Pattern). Live angewandt via
  `phase2_persistence/scripts/init_db.py` → Schema-Version 5, verifiziert (3 Bestands-Trades
  unberührt, alle 4 neuen Tabellen leer + korrektes Schema).
- **Konsequenz-Fixes derselben Migration** (root-cause, nicht nur Symptom): `Database.
  insert_regime_snapshot`/`insert_decision_context` (trade_id-basiert, jetzt schema-inkompatibel)
  entfernt aus `phase2_persistence/persistence/db.py`; `scripts/archive_verification_trades.py`s
  `_CHILD_TABLES` von den beiden Tabellen bereinigt (hätten sonst auf eine nicht mehr existierende
  `trade_id`-Spalte gequeryt); betroffene Tests in `phase2_persistence/tests/test_db.py`,
  `test_migrations.py` (Version 4→5, neuer `test_v3_learning_tables_present`),
  `tests/test_archive_verification_trades.py` aktualisiert.
- **`phase10_v3/abstain_lessons/`** (neues Paket, `pyproject.toml` + editable install, in
  `scripts/dev_install.sh` aufgenommen): `models.py`/`exceptions.py` (S1: `AbstainStage` 5
  Werte, `AbstainReason` 12 Werte, `AbstainRecord` frozen), `classifier.py` (S2:
  `classify_abstain`, Prioritätsordnung exakt wie gespecct), `reflect.py` (S4: `AbstainLLM`
  Protocol, `reflect_abstain` best-effort/nie werfend, `build_paper_lesson_prompt` für WE 2),
  `store.py` (S3: `AbstainStore`, UniverseStore-Own-Connection-Muster), `paper.py` (nur
  Modelle — `PaperTrade`/`PaperVariant`/`PaperStatus`/`PaperExitReason`; die "deterministischer
  Kern"-Engine ist WE 2), `paper_store.py` (`PaperTradeStore`, analog `AbstainStore`),
  `sink.py` (S5: `AbstainLessonSink`, `paper_engine=None` bis WE 2).
- **P5-Executor-Naht** (`phase5_execution/execution/executor.py` + `protocols.py`): neuer
  keyword-only `abstain_sink=None`; `_no_trade` von `@staticmethod` zu Instanzmethode mit
  Cycle-Outcome-Keywords, neuer `_notify_no_trade`-Helper (Muster wie `_notify_opened`,
  Decision J). Alle 8 NO_TRADE-Rückgabepfade übergeben jetzt ihre bekannten Felder
  (Gate-ID-Mapping `time_window→G1, load_candidates→G2(→research_empty statt failed_gate),
  constraints→G3, sizing→G4, direction_consistency→G5`; Veto-IDs matchten bereits 1:1).
  **Default `None` ⇒ bit-identisch bewiesen** (154→154 Bestandstests unverändert grün,
  **+7 neue Naht-Tests → P5 154→161**).
- **P8-Wiring** (`scheduler/config.py`, `scripts/wiring.py`): `enable_abstain_lessons=True`,
  `enable_abstain_reflect=True`, `reflect_daily_cap=10` (V3-D8: **an by default**, anders als
  z. B. `enable_ig_bars` — bewusst, s. Plan). `_build_abstain_sink` (AbstainStore + optionaler
  `_AbstainLLMAdapter` über die wiederverwendete P4-`LLMClient`/Haiku, `RewardConfig.lesson_*`-
  Knobs) + `_observed_abstain_sink`-Wrapper (`abstain_recorded`-Event via
  `observability.record_event`, generischer Call wie im Anker-Annex vorgesehen). In die
  Executor-Konstruktion verdrahtet. **P8 217 Tests unverändert grün** (Config-Defaults
  erweitert, kein neuer Test nötig).
- **S7** `phase10_v3/scripts/abstain_report.py`: deterministisches `--db`-CLI (Counts je
  Reason, letzte N Records, Lesson-Quote), Golden-Output-Test, manuell gegen die echte
  (aktuell leere) Live-DB smoke-verifiziert.
- **S6 dunkel** (`phase4_research/research/prompt.py`): `build_prompt` bekam
  `include_abstain_lessons`/`abstain_lessons`/`include_paper_lessons`/`paper_lessons`
  (alle default aus/`None`) — **pure Funktion bleibt pure** (Lessons werden als
  vorgefertigte String-Listen übergeben, kein eigener DB-Zugriff in `prompt.py`, anders
  als der Plan-Wortlaut "AbstainStore.recent_lessons als Prompt-Block" wörtlich nahelegt —
  bewusste Abweichung, um die dokumentierte "Pure function — no I/O"-Invariante des
  Moduls nicht zu brechen; der Aufrufer holt die Lessons). Default aus ⇒ **P4 148→148
  Bestandstests unverändert grün, +7 neue Flag-Tests → P4 148→155**. **Aktivierung bleibt
  ausdrücklich außerhalb V3** (V3-D3) — niemand im Repo setzt die Flags aktuell `True`.

### Verifiziert
- Volle Cross-Phase-Regression (jede Phase separat, `tests.conftest`-Kollision):
  P1 87 · P2 **75** (−1: 2 alte Regime/Context-Tests entfernt, 1 neuer Migrations-Test) ·
  P3 100 · P4 **155** (+7) · P5 **161** (+7) · P6 70 · P7 133 · P8 217 · P9 72 ·
  **P10 67 (neu)** · meta_m1_harness 28 · root 77. `py_compile` clean auf allen
  berührten Dateien (inkl. `scripts/wiring.py`, laut Konvention nicht pytest-importiert).
- Live-Migration gegen die echte `data/trading_bot.sqlite` angewandt + verifiziert
  (s. o.) — nicht nur gegen `tmp_path`.
- `phase2_persistence/CLAUDE.md` + `phase8_scheduler/CLAUDE.md`(Nebenbefund) dokumentiert
  Doku-Drift-Fixes im selben Commit-Satz (Doku-Hygiene-Regel).

### Next
- **Operator (Nikinger), Montag:** Scheduler-Restart ist ein bewusster Schritt (KILL-Datei
  erst löschen). Montag-Restart-Beweis (Plan §7.3 Akzeptanzkriterium): erste echte
  `abstain_records`-Zeilen + `abstain_recorded`-Events im Health-Log — wortgleich hier
  protokollieren, sobald der Nikinger den Restart macht.
- **Woche 2 (wochentags, docs-only):** Review-Note nach den ersten realen
  `abstain_records`-Zeilen (Plan §8) — insbesondere `REASON_DEBATE_ABSTAIN`-Reflect-Cap-
  Verteilung gegen die 94/6-Analyse aus Step 2 prüfen.
- **WE 2 (18.–19.07.):** Block B — `market_context/` Paket (Modelle, `regime.py`,
  `writer.py`, `context_recorder`-Naht am P5-Executor) + Paper-Pipeline (die
  "deterministischer Kern"-Engine für `paper.py`, `PaperEngine`, Both-Sides-Shadow +
  optionaler Council-Paper-Call). Plan §9–§11.

### Open questions / blockers
- Keine technischen. Eine Beobachtung für die Woche-2-Review: der `_no_trade`-Seam übergibt
  `research_empty=True` für JEDE Gate-2-Fehlschlag (nicht nur `research_empty` im engeren
  Sinn) — das war bereits die S2-Contract-Absicht (G2 → `REASON_NO_CANDIDATES`), aber am
  echten Datenbild (94 % der Abstains sind genau dieser Pfad) lohnt ein Blick, ob die
  12-Reason-Taxonomie an dieser Stelle granular genug bleibt.

### Nachtrag (2026-07-14, Di) — Montag-Restart-Beweis erbracht ✅

Scheduler seit Mo 2026-07-13 durchgehend gelaufen (PID 129102, KILL-Datei vom Nikinger vor
dem Restart gelöscht), `scheduler_state.json` zeigt `consecutive_failures: 0`, `kill_reason:
null` — sauberer, unbeaufsichtigter Lauf. Read-only via `mode=ro`-URI gegen die Live-DB
geprüft (Plan §7.3 Akzeptanzkriterium):

**`abstain_records`** (66 Zeilen, 2026-07-13T07:05:42.541Z … 2026-07-13T14:47:42.545Z, alle
`epic: null`/`stage: research_empty`/`reason: reason_no_candidates`/`lesson_extracted: 0`).
Erste 3 Zeilen wortgleich:
```
{'record_id': 'fc38dd85-a8f3-47a8-a722-8f4d71ac4748', 'created_utc': '2026-07-13T07:05:42.541Z', 'epic': None, 'stage': 'research_empty', 'reason': 'reason_no_candidates', 'lesson_extracted': 0}
{'record_id': 'ae4615b6-a371-4908-96ce-f38cef069aff', 'created_utc': '2026-07-13T07:10:52.196Z', 'epic': None, 'stage': 'research_empty', 'reason': 'reason_no_candidates', 'lesson_extracted': 0}
{'record_id': '7165c61a-a1b1-4fa9-b07e-800536eb881b', 'created_utc': '2026-07-13T07:15:59.476Z', 'epic': None, 'stage': 'research_empty', 'reason': 'reason_no_candidates', 'lesson_extracted': 0}
```

**`research_health.jsonl`** — 66 `abstain_recorded`-Events, 1:1 deckungsgleich mit den
DB-Zeilen (gleiche Reason/Stage/Epic, unabhängiger zweiter Kanal). Letzte 3 wortgleich:
```
{"event": "abstain_recorded", "reason": "reason_no_candidates", "stage": "research_empty", "epic": null, "ts": "2026-07-13T14:37:20.513400+02:00"}
{"event": "abstain_recorded", "reason": "reason_no_candidates", "stage": "research_empty", "epic": null, "ts": "2026-07-13T14:42:31.614240+02:00"}
{"event": "abstain_recorded", "reason": "reason_no_candidates", "stage": "research_empty", "epic": null, "ts": "2026-07-13T14:47:42.546626+02:00"}
```

**Einordnung:** 66/66 sind `REASON_NO_CANDIDATES` (Research-Stufe) — deckt sich exakt mit der
Step-2-Baseline (94.3 % dieses Pfads über 8 Tage). `lesson_extracted` 0/66 ist **erwartetes
Verhalten**, kein Fehler: `reflect_stages` defaultet auf `{AbstainStage.DEBATE}` (V3-D8) —
Research-Stufe-Abstains reflektieren bewusst nie. Noch kein einziger `REASON_DEBATE_ABSTAIN`
in diesem Fenster beobachtet → der Reflect-Pfad selbst ist am echten Live-Lauf noch
unbewiesen (Beobachtungspunkt für die Woche-2-Review, s. o.). **WE-1-Akzeptanzkriterium
(Plan §7.3) damit vollständig erfüllt** — Block A ist nicht nur code-complete, sondern
live am echten unbeaufsichtigten Bot bewiesen.

---

## Session stopped — 2026-07-10 (Steps 0–3 komplett, docs-only/read-only)

### Completed
- `phase10_v3/CLAUDE.md`: Phasen-Skeleton, Housekeeping-Ergebnisse (Legacy-Grep clean,
  Baseline 1162 grün mit P4-Korrektur 141→148), vollständiger Verified-anchors-Annex
  (9 Punkte, s. o.).
- `docs/INDEX.md`: Phase 10 als aktive Sektion eingetragen, Phase 9 zur "Prior phase"
  umgehängt, alle 4 neuen/verifizierten Docs indiziert.
- Root `CLAUDE.md` + `ROADMAP.md`: Current-state-Tabellenzeile bzw. Phase-10-Statuszeile
  von stale ("Geplant"/"keine Konzept-Session") auf real (🔄 aktiv, Kickoff 2026-07-10)
  korrigiert — Tabellen-Edit only, keine neue Root-Prosa (Doku-Hygiene-Regel).
- `phase10_v3/STEP0_DATA_ANALYSIS_2026-07-10.md`: V2-Baseline (2 reale Trades, beide vor
  07-06, beide Verlust-Stopouts), Abstain-Ist-Analyse (97.6 % Zyklen-Abstain-Quote, davon
  94.3 % Research-Stufe `REASON_NO_CANDIDATES` — Gate-/VETO-/Error-Reasons real **nie**
  aufgetreten in 8 Tagen), Gap-Check (Feld-Mapping S2-Contract + Block-B) inkl. zweier
  echter Lücken: Session-Health-`ABORT`-Zyklen (11×) fallen außerhalb des geplanten
  NO_TRADE-only-Sink-Scopes; `CAC`/`IBEX` laufen 84–97 % der Zeit `degraded` (fehlend
  `volume`) — bestätigt den Bedarf für `data_source`/`degraded` in
  `market_regime_snapshots` konkret statt nur theoretisch.
- 3 Commits: Step 0 (`dce5002`), Step 1 (`76992a0`), Step 2 (`95690b0`); Step 3 (dieser
  Annex + dieser Session-Block) folgt als 4. Commit direkt im Anschluss.
- `data/` während der gesamten Session ausschließlich `mode=ro` gelesen — verifiziert,
  keine Schreibzugriffe.

### Next
- **WE 1 (11.–12.07.):** Migration `005_v3_learning.sql` (Backup-Protokoll zuerst!) +
  `AbstainStore`/`PaperTradeStore` (Plan §6) — dabei die oben dokumentierte
  DROP+CREATE-Empfehlung für `market_regime_snapshots`/`decision_context` final
  entscheiden (Nikinger). Danach S1/S2/S4-Module (Plan §7.1), dann Sink-Naht +
  P8-Wiring + S7-Report + S6-dunkel (Plan §7.2), dann WE1-Regression + Montag-
  Restart-Beweis (Plan §7.3).
- Vor WE 1 starten: kurz `docs/concepts/phase10_v3_plan.md` §6 erneut lesen (Migration-
  Schema-Details), Operator-Checkliste dort beachten (Scheduler-Stop bestätigen, Backup
  vor Migration).
- Woche 2 (wochentags, docs-only): Review-Note nach den ersten realen
  `abstain_records`-Zeilen (Plan §8) — insbesondere prüfen, ob `REASON_DEBATE_ABSTAIN`
  je einen Reflect-Cap-Slot bekommt, gegeben die 94/6-Verteilung aus der heutigen
  Analyse.

### Open questions / blockers
- Keine Blocker für WE 1. Eine Entscheidung liegt an: DROP+CREATE vs. anderer Ansatz für
  die beiden inkompatiblen Placeholder-Tabellen (Empfehlung: DROP+CREATE, s. Anker-Annex
  Punkt 3) — bindend erst am Migrations-Commit, nicht heute.
