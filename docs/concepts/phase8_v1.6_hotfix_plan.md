# Phase 8 → v1.6 Hotfix — Initial-Plan (das „Was")

> **Audience:** die spätere Claude-Code-Session, die aus diesem „Was" den detaillierten
> Ausführungsplan (das „Wie") baut — und danach die Implementierungs-Sessions.
> **Author:** Claude Code, 2026-07-02 (dieselbe Repo-Umgebung, Code = Source of Truth).
> **Was diese Datei ist:** der initiale, Nikinger-beauftragte v1.6-Plan — **Richtung +
> Steps + Entscheidungsregeln**, bewusst noch ohne file-für-file-Editierplan. Sie
> **ergänzt** und dupliziert nicht das Diagnose-Dokument
> `phase8_scheduler/PHASE8_V1.6_HANDOVER.md` (Symptome, Code-Pfad, Datei-Anker §5).
>
> **Read-First-Reihenfolge für die „Wie"-Session:**
> 1. diese Datei (Richtung + Steps)
> 2. `phase8_scheduler/PHASE8_V1.6_HANDOVER.md` (Diagnose + autoritative Datei-Anker)
> 3. `docs/concepts/phase8_v1.5_hotfix_plan.md` (Format-Vorlage + was v1.5 bereits baute)
> 4. dann pro Step die echten Dateien öffnen + **Anker verifizieren, bevor editiert wird**

---

## 0a. Warum dieser Plan in Claude Code entstand (nicht im Web-Chat)

Die Projekt-Konvention („Claude browser plant; Claude Code implementiert", root-`CLAUDE.md`
§Phase transitions) wurde hier **bewusst und dokumentiert** durchbrochen — Nikinger-Entscheidung
2026-07-02. Drei Gründe:

1. **Der Root-Cause ist ungepinnt und nur per Code-Lektüre eingrenzbar.** Der zentrale neue
   Befund dieses Plans (§1: Daily-Fetches funktionieren, nur die Intraday-5m-Fetches failen)
   entstand aus dem Abgleich des Operator-Logs mit `phase3_external_data/external_data/fetcher.py`
   — eine Web-Session ohne Repo-Zugriff hätte auf der gröberen Handover-Hypothese
   („liefern keine Kursdaten") planen müssen und den falschen Fix-Raum aufgespannt.
2. **v1.5 hat bewiesen, dass Browser-Plan-Anker driften.** Mehrere v1.5-Steps mussten beim Bau
   gegen verschobene `file:line`-Anker reconciled werden (dokumentiert in den ✅-Blöcken des
   v1.5-Plans). Ein Plan, der direkt gegen den echten Baum geschrieben wird, startet ohne
   diese Drift.
3. **Die v3-Zukunftssicherung hängt an einer existierenden Code-Naht.** Das „Was" dieses Plans
   baut auf dem in v1.5 bereits reservierten Extension-Point
   `InstrumentSpec.source="research_promoted"` (`phase4_research/research/models.py:294/304`)
   auf — den muss man **verifizieren** statt erinnern, sonst plant man eine zweite,
   konkurrierende Naht.

**Zwei-Stufen-Modell (Nikinger-Auftrag):** diese Datei = das **„Was"** (Richtung, Steps,
Entscheidungsregeln, offene Fragen). Eine **spätere Claude-Code-Session** baut daraus das
**„Wie"** (file-für-file-Editierplan, Test-Plan, Reihenfolge-Feinschnitt) — ebenfalls in
Claude Code, aus denselben drei Gründen.

---

## 0b. Mission & Leitplanken

**Mission:** v1.5 lieferte alle drei Code-Fixes (B Clamp/Floor, C 4-Instrument-Universum,
A Lesson-Provenance), aber der erste Live-Lauf zeigte: **die Hälfte des Universums läuft
reduced-signal** (`^FCHI`/`^IBEX` ohne Daten) und **niemand kann strukturiert sehen, warum
der Bot tut, was er tut** (kein echtes Logging). v1.6 macht das System **beobachtbar**,
klärt die zwei kranken Instrumente (**fix oder drop**), gießt Instrument-Onboarding in eine
**wiederholbare, deterministische Verifikations-Pipeline** (die v3-Naht) — und holt dann den
noch ausstehenden **Live-Beweis** (net-new autonomer open→close + real auslösender Breaker).

**Harte Leitplanken (unverändert aus v1.5, nicht verhandelbar):**

1. **Kein neues AI.** Observability, Verifikation, Fix/Drop sind 100 % deterministischer Code.
   Die AI-Stellen bleiben exakt P4-`ask_candidate`, P6-Debatte, P7-`reflect`.
2. **Nie einen VETO umgehen.** Der Momentum-VETO sourcet aus IG-Echtzeit-Bars
   (`execution/vetos.py`), **nicht** yFinance — dieser Blocker berührt keinen VETO, und v1.6
   ändert daran nichts.
3. **Demo-only, fail-closed** bleibt (Demo-Lock, AutoConfirm, Kill-Switch unberührt).
4. **Additive Nähte, Phasen-Isolation.** Cross-Phase-Edits (P3/P4/P8) je als dokumentierter
   Cross-Phase-Edit mit dated Note; Default-Pfad unverändert; Regression P1–P8 grün.
5. **Live-/Netz-Läufe sind Operator-Sache** (Nikinger). Claude Code liefert Code + gemockte Tests.
6. **Ehrlichkeits-Leitplanke:** kein ✅-Flip, keine Autonomie-/Edge-Behauptung, bevor die
   Step-4-Beweise real gefallen sind.

---

## 1. Befund-Update (verfeinert das Handover — Code = Source of Truth, 2026-07-02)

Das Handover sagt „`^FCHI`/`^IBEX` liefern keine Kursdaten". Der Abgleich des Operator-Logs
mit dem echten Fetcher-Code grenzt das ein:

- Die Fehler-Signatur (`period=1d`, `got 0, want >= 4`) matcht die **Intraday-5m-Fetches**:
  `get_drift` (`fetcher.py:352`), `get_momentum` (`fetcher.py:401`) und das Intraday-Leg von
  `get_high_low_distance` (`fetcher.py:450`) — alle drei rufen `period="1d", interval="5m"`.
  (`want >= 4` = `bars_back + 1` des 15-min-Momentums.)
- Das Log zeigt zugleich `intraday price unavailable for ^IBEX; using last daily close`
  (`fetcher.py:453`) — dieser Fallback **hatte einen letzten Daily-Close**, d. h. die
  **Daily-Fetches (`interval="1d"`) haben funktioniert.**

**Arbeitshypothese H1 (stark, testbar):** Yahoo liefert für `^FCHI`/`^IBEX` **Daily-, aber
keine 5m-Intraday-Daten** — anders als `^GDAXI`/`^STOXX50E`. Konsequenz: der Brain-Context
dieser Epics ist vermutlich **teil-degradiert** (drift/momentum/`5m`-abhängige Felder `None`,
Daily-Signale wie history/volume-z/high-low intakt), **nicht** komplett `None` —
`get_brain_context` degradiert per-Feld (`fetcher.py:461`ff), und P4s `_safe_brain_context`
(`context_builder.py:141`) fängt nur einen Komplett-Raise auf `None` ab. **Genau diese
Unterscheidung kann heute niemand sehen — das ist der Observability-Gap** und der Grund für
Step 0.

**Zu testende Hypothesen (Step 1, Operator):**

| # | Hypothese | Test |
|---|---|---|
| H1 | Yahoo hat für `^FCHI`/`^IBEX` kein 5m-Intraday (Daily ok) | bare `yf.Ticker("^IBEX").history(period="1d", interval="5m")` vs. `interval="1d"`; dasselbe für `^FCHI`; Gegenprobe `^GDAXI` |
| H2 | Symbol/Params falsch (anderes Symbol oder `period`/`interval`-Kombi nötig) | Symbol-Varianten + `period="5d"`-Intraday probieren; was liefert Yahoo-Finance-Web für CAC 40/IBEX 35? |
| H3 | yfinance-Version/Upstream-API-Änderung (betrifft nur manche Indizes) | installierte yfinance-Version gegen die P3-Pin-Range (`>=0.2.65,<0.3`) + Changelog/Issues prüfen |
| H4 | Rate-Limit/transient (Fehlerbild wäre intermittierend) | Wiederholte, gepacte Einzel-Probes zu verschiedenen Zeiten; `possibly delisted` spricht eher dagegen |

> **✅ Step 1 ERLEDIGT (2026-07-02, Operator-Lauf gegen echtes yfinance —
> `scripts/2026_07_02-v1.6-step1-diagnosis.md`). Ergebnis dreht die Diagnose: H1 widerlegt,
> H4 gestützt, ein neuer, bisher undokumentierter Befund kommt dazu.**
>
> - **H1 widerlegt.** `^FCHI` UND `^IBEX` lieferten **sowohl** `period=5d,interval=1d`
>   (5 rows) **als auch** `period=1d,interval=5m` (**19 rows**) — identisch zur
>   `^GDAXI`-Kontrolle (ebenfalls 5 / 19 rows). Kein Daily-vs-Intraday-Unterschied.
> - **H2 hinfällig** (die Basis-Calls liefen bereits durch): zusätzliche Varianten
>   (`15m/1d` → 7 rows, `5m/5d` → 427 rows, `1m/1d` → 95 rows) liefen für beide Ticker
>   sauber durch. Kein Symbol-/Param-Problem.
> - **Der P3-`smoke_test.py`-Lauf war für BEIDE Epics vollständig grün:** `drift`,
>   `momentum_15m`, `bars(5m,5)`, `history(30d)` und der volle `brain_context` kamen
>   **populiert** zurück (kein `None`-Feld außer `volume` — das ist der **erwartete**,
>   dokumentierte C3-Degrade-Pfad, da bewusst kein Volume-Proxy registriert ist, s.
>   `ticker_map.py`-Kommentar — kein Bug). Das widerspricht der ursprünglichen
>   „teil-degradiert"-Annahme aus §1 oben: an diesem Tag war der Kontext für beide Epics
>   **voll**, nicht teil-degradiert.
> - **H4 gestützt (ohne einen zweiten zeitversetzten Lauf nötig zu haben):** exakt dieselben
>   Fetches, die im Live-Lauf `possibly delisted; no price data found` warfen, liefen jetzt
>   fehlerfrei — das ist bereits der Intermittenz-Beweis (zwei Zeitpunkte, unterschiedliches
>   Ergebnis bei identischem Code/Symbol/Parametern). Ein weiterer H4-Spot-Check ist
>   **optional**, kein Blocker (s. §3 Carry).
> - **★ Neuer Befund (bisher nicht dokumentiert): yfinance-Versions-Drift.** Installiert ist
>   **`yfinance==1.4.1`**, aber `phase3_external_data/requirements.txt:6` pinnt
>   `yfinance>=0.2.65,<0.3` — eine Major-Version-Drift weit außerhalb des dokumentierten
>   Pins. yfinance hatte zwischen 0.2.x und 1.x größere interne Rewrites (Yahoo-API/
>   Cookie-Crumb-Handling), ein bekannter Quell intermittierender Fehler wie
>   `possibly delisted`. **Plausibelster Einzel-Kandidat für die Root Cause der
>   Intermittenz** — muss in der „Wie"-Session verifiziert werden (wann/wie wich die
>   installierte Version vom Pin ab; ob ein Re-Pin + reproduzierbarer Fehler mit der
>   gepinnten Version das bestätigt).
>
> **Auswirkung auf Step 3 (Fix-oder-Drop):** die binäre Entscheidungsregel „Fix vs. Drop" aus
> §3 unten deckt dieses Ergebnis nicht sauber — es gibt jetzt eine **dritte, plausiblere
> Option: Toleranz statt Fix/Drop.** Die Instrumente sind nicht defekt und brauchen keinen
> Symbol-Patch; sie sind (vermutlich versions-/Yahoo-seitig) **gelegentlich flaky**. Das
> spricht für: (a) den Versions-Pin-Drift klären/beheben, (b) die bereits vorhandene
> Retry-Logik (`fetcher.py:_fetch_with_retry`, exp. Backoff 1→2→4s, ≤3 Versuche) auf
> Robustheit gegen genau dieses Fehlerbild prüfen (reicht sie? ist `possibly delisted` von
> `_is_rate_limit_error` erfasst oder fällt es in den `DataUnavailableError`-Pfad?), (c) NICHT
> vorschnell droppen, ohne die Versions-Frage geklärt zu haben. §3 unten entsprechend
> nachgeführt.

---

## 2. Die v3-Linse (der Kern der Zukunftssicherung — Nikinger-Auftrag)

Ein späteres Update (**v3**) will **semi-automatisches Research** ergänzen: Research schlägt
neue Instrumente vor, die über einen deterministischen **validate→promote-Pfad** ins Universum
kommen (`InstrumentSpec(source="research_promoted")` — die Naht ist seit v1.5 im Code
reserviert, `research/models.py:273/294/304`, bewusst ohne AI verdrahtet).

**Warum das den v1.6-Fix formt:** der aktuelle Blocker ist kein Zufall, sondern der
strukturelle Beweis, dass Instrument-Onboarding heute an einem **manuellen Einmal-Schritt**
hängt, der übersprungen werden kann — `^FCHI`/`^IBEX` gingen als „well-known, not
live-verified" ins Universum, der P3-`smoke_test`-Check wurde zweimal explizit geflaggt und
nie gelaufen. Sobald v3 Onboarding **wiederkehrend** macht, skaliert dieser Fehlermodus mit:
jedes semi-automatisch vorgeschlagene Instrument hätte dieselbe Lücke.

**Der zukunftssichere Fix ist deshalb kein Ticker-Patch, sondern:**

1. **Die „validate"-Hälfte des validate→promote-Pfads jetzt bauen** (Step 2): ein
   deterministisches, wiederholbares, read-only Verifikations-Gate, das für einen
   Instrument-Kandidaten die **komplette** Onboarding-Checkliste maschinenlesbar prüft.
   v1.6 nutzt es manuell (Operator); v3 hängt die Promotion daran — **ohne** es umzubauen.
2. **Permanente per-Epic-Daten-Health-Observability** (Step 0): nicht nur ein Debug-Werkzeug
   für diesen Vorfall, sondern der dauerhafte Feedback-Kanal, über den ein (später
   automatisch promotetes) Instrument auffällt, wenn seine Datenquelle **nach** dem Onboarding
   degradiert. Verifikation fängt den Eintritt, Observability den Betrieb.
3. **Keine AI in v1.6.** Die Promotion-Logik selbst (wer schlägt Instrumente vor) bleibt v3;
   v1.6 baut nur die deterministische Infrastruktur, auf der sie sicher landen kann.

---

## 3. Steps (das „Was" — dependency-geordnet; das „Wie" schneidet fein)

```
Step 0   Observability zuerst (der Enabler — ohne sie ist alles Weitere Blindflug)
Step 1   Diagnose ^FCHI/^IBEX (Operator-gated; H1–H4 aus §1 testen)
Step 2   Instrument-Verification-Harness (die v3-Naht; konsolidiert die Einmal-Tools)
Step 3   Fix oder Drop (per Entscheidungsregel, datengetrieben aus Step 1/2)
Step 4   Live-Beweis (carried v1.5-Step-5: 5a Varietäts-Run + 5b Breaker-Fire)
Step 5   Doku-Flip + Carries
```

> **⟳ Ausführungsreihenfolge-Notiz (2026-07-02, „Wie"-Session, Nikinger-Freigabe):** die
> Nummerierung oben bleibt für die Kontinuität zum „Was"-Dokument unverändert, aber die
> **tatsächliche Baureihenfolge** dieser Session weicht bewusst ab — dokumentiert statt still
> abgewichen (v1.5-Präzedenz: „B vor C"-Reorder). Step 0 war ursprünglich vor Step 3 geplant,
> weil dessen Daten für die Fix/Drop-Entscheidung nötig schienen; Step 1s Diagnose hat diese
> Entscheidung aber bereits billig + schlüssig getroffen, **ohne** Step 0. Reale Reihenfolge:
> **Step 3a** (billig: Re-Pin + Doku, ✅ erledigt) → **Step 0** (jetzt umgerahmt als
> Sicherheitsnetz für einen Rückfall, Nikinger-Bedingung — nicht mehr Step-3-Voraussetzung) →
> **Step 2** (Harness, zukunftssicher) → **Step 4** (Live-Beweis, Operator) → **Step 5**
> (Doku-Flip). Voller Kontext: `phase8_scheduler/CLAUDE.md` → `## Session stopped` (v1.6 „Wie").

**Step 0 — Observability (Enabler + permanenter v3-Feedback-Kanal).**
Strukturiertes, **persistiertes** Logging dessen, was heute nur als stderr-Rauschen existiert:
- **Per-Zyklus/per-Epic Daten-Health:** welches Brain-Context-Signal war full / degraded /
  fehlend, und **warum** (welcher Fetch schlug fehl, mit welchem Fehler) — die Granularität,
  die §1s „teil-degradiert vs. komplett `None`"-Frage beantwortbar macht.
- **Research-Decision-Log:** pro Zyklus der Ausgang (Pick/Abstain/Fehler) mit dem vorhandenen
  Reason-Gerüst (`research_tick.py:84-89`; die reservierten feineren Codes
  `EMPTY_UNIVERSE`/`VALIDATOR_REJECT`/`FILTER_FAIL` sind ein **Kandidat** für diesen Step —
  ob ihr Ausbau in Step 0 gehört oder P9 bleibt: offene Frage §4).
- Ziel-Ort: `data/state/` (gitignored, atomic-write-Pattern des Repos), optional im Webui
  sichtbar. Grobe Verortung: P3-Fetcher (Fehler-Detail nach oben reichen) + P8 (persistieren);
  **additiv**, Default-Pfad unverändert.
- **Akzeptanz:** nach einem Daemon-Lauf kann der Operator aus einer Datei (nicht aus
  stderr-Scrollback) ablesen, welches Instrument in welchem Zyklus welche Signale hatte und
  warum der Zyklus (nicht) tradete.

**Step 1 — Diagnose (Operator-gated; billig, parallel zu Step 0 möglich).**
Der zweimal geflaggte, nie gelaufene P3-Check + gezielte Probes:
- `python phase3_external_data/scripts/smoke_test.py --epic IX.D.CAC.IFE.IP` und
  `--epic IX.D.IBEX.IFM.IP` (echtes yfinance, Operator).
- Die H1–H4-Probes aus §1 (bare-yfinance-Einzelabfragen, gepact).
- **Akzeptanz:** die Hypothesen-Tabelle §1 ist entschieden (mindestens H1 bestätigt/verworfen);
  das Ergebnis gated Step 3s Entscheidungsregel.

**Step 2 — Instrument-Verification-Harness (das Zukunftssichere).**
Ein read-only, deterministisches, **wiederverwendbares** Verifikations-Tool (Arbeitstitel
`scripts/verify_instrument.py`; Script vs. P3-Modul = offene Frage §4), das für einen
Instrument-Kandidaten die komplette Checkliste maschinenlesbar prüft:
- yf-Ticker liefert **Daily**-Daten · yf-Ticker liefert **Intraday-5m** (die Lücke, die
  diesen Vorfall verursacht hat — heute prüft das **kein** Tool explizit) · Volume-Proxy
  (falls gesetzt) liefert echtes Volumen · IG-Epic existiert + `ohlcv_available=True` ·
  `currency=EUR` + `min_deal_size` plausibel.
- Konsolidiert die heute verstreuten Einmal-Tools (`scripts/resolve_epics.py` = IG-Seite,
  P3-`smoke_test.py` = yf-Seite) zu **einem** Verdikt pro Instrument; stdout = ein
  maschinenlesbares JSON-Verdikt (Konvention: Narrative → stderr, JSON → stdout).
- **v3-Naht:** dieses Verdikt ist der künftige Promotion-Gate — ein
  `source="research_promoted"`-Kandidat kommt nur mit grünem Verdikt ins Universum. In v1.6
  läuft es manuell (Operator), gated aber schon jetzt jede Universum-Erweiterung.
- Offen für die „Wie"-Session: ob das Verdikt zusätzlich **persistiert** wird (z. B. ein
  Verification-Status je `InstrumentSpec` — Feld vs. Sidecar-Datei, §4).
- **Akzeptanz:** ein Operator-Lauf pro Instrument liefert ein eindeutiges, wiederholbares
  PASS/FAIL-Verdikt je Checklisten-Punkt; die vier Bestands-Instrumente sind damit erstmals
  **einheitlich** verifiziert (statt „DAX/STXE ja, CAC/IBEX geraten").

**Step 3 — Fix, Tolerieren oder Drop (Entscheidungsregel, datengetrieben aus Step 1/2).**

> **✅ ENTSCHIEDEN (2026-07-02, „Wie"-Session, Nikinger-Freigabe): Tolerieren.**
> `^FCHI`/`^IBEX` bleiben unverändert in `ticker_map.py`/`EXTENDED_UNIVERSE` — Step 1 hat
> bewiesen, dass beide voll funktionieren (Daily **und** 5m-Intraday, kompletter
> `brain_context`). Einzige Code-Änderung: `phase3_external_data/requirements.txt` von
> `yfinance>=0.2.65,<0.3` (stale) auf `yfinance>=1.4.0,<1.5` (die tatsächlich installierte,
> tatsächlich getestete Version) re-gepinnt — eine **separate Hygiene-Korrektur**, **nicht**
> der Fix für den Live-Ausfall. Kein Retry/Backoff-Code-Änderung nötig (die bestehende
> 3×-Exponential-Backoff-Logik hat den Fehler laut Log korrekt behandelt, sie hat nur diesen
> einen Transienten nicht überstanden). **Nikinger-Bedingung:** dies wird von Step 0
> (Observability) als „sophisticated logging, um bei einer Wiederholung die echte Ursache zu
> finden" begleitet — Step 0 ist damit das Sicherheitsnetz für einen Rückfall, nicht nur ein
> Nice-to-have.
>
> **⚠ Korrektur einer vorherigen Theorie:** die zuvor geflaggte „yfinance-Versions-Pin-Drift"
> (installiert `1.4.1` vs. damals gepinnt `>=0.2.65,<0.3`) ist **NICHT** die Ursache der
> Intermittenz. Sowohl der **fehlgeschlagene** Live-Lauf als auch der **erfolgreiche**
> Diagnose-Lauf liefen gegen dieselbe installierte `1.4.1` — Versions-Drift kann den
> Unterschied zwischen zwei Läufen auf identischer Version nicht erklären. Der Pin war
> trotzdem stale (ein frischer venv-Install hätte still eine ungetestete uralte `0.2.x`
> bekommen) und wurde als unabhängige Korrektur re-gepinnt, s. o.
>
> *(Ursprüngliche Nachführung 2026-07-02 vor der Entscheidung, zur Nachvollziehbarkeit
> belassen:)* die ursprünglich binäre Fix-vs-Drop-Regel unten passt nicht sauber auf den
> echten Befund (H1 widerlegt, H4 gestützt, Versions-Drift-Theorie entdeckt-aber-später-
> widerlegt — s. §1-Addendum). Eine **dritte Option (Tolerieren)** erwies sich als die
> richtige Wahl; Fix/Drop bleiben unten als historischer Kontext / Fallback-Dokumentation.

- **Tolerieren (neue Präferenz-1-Option, aus dem Step-1-Befund):** wenn die „Wie"-Session
  bestätigt, dass es sich um **intermittente Yahoo-/Versions-Flakiness** handelt (nicht um
  eine strukturelle Symbol-/Intervall-Lücke) — dann ist der richtige Fix **kein**
  Ticker-Patch, sondern (a) den yfinance-Versions-Pin-Drift klären (installiert `1.4.1`
  vs. gepinnt `>=0.2.65,<0.3`, `requirements.txt:6`) und ggf. re-pinnen/testen, (b) die
  bestehende Retry/Backoff-Logik (`fetcher.py:_fetch_with_retry`) gegen genau dieses
  Fehlerbild prüfen/härten (fängt sie `possibly delisted` zuverlässig als
  `DataUnavailableError` mit Retry, statt beim ersten Versuch aufzugeben?). Die Instrumente
  **bleiben im Universum**, der Daemon toleriert einen gelegentlichen Miss ohne Log-Sturm.
- **Fix (Fallback)**, falls doch ein strukturelles Problem auftaucht — in Präferenz-
  Reihenfolge: (a) korrigiertes Symbol/Params (`ticker_map`/Fetch-Params, cross-phase P3),
  (b) **daily-only-Toleranz**: falls eine Intervall-Lücke sich doch reproduzierbar zeigt,
  ist zu entscheiden (§4), ob ein Instrument mit ehrlich gelabeltem daily-only Brain-Context
  (drift/momentum `n/a`, Daily-Signale voll) ein **tolerierter Modus** wird — der
  Momentum-VETO ist davon unberührt (IG-Bars), es geht nur um LLM-Kontext-Qualität.
- **Drop (letzter Ausweg)**, wenn weder Tolerieren noch Fix einen verifizierten Weg liefern:
  CAC 40 + IBEX 35 aus `EXTENDED_UNIVERSE` (`research/models.py:369`) + `ticker_map`
  entfernen → zurück auf die zwei voll verifizierten Instrumente. **Universum-Ehrlichkeit
  schlägt Instrumenten-Zahl.** Ersatz-Instrumente (andere EUR-Indizes) nur über den
  Step-2-Harness — nie wieder „well-known, not verified".
- **Akzeptanz:** jedes Instrument im Universum hat ein grünes Step-2-Verdikt (oder eine
  explizit dokumentierte, tolerierte Flakiness-Klassifikation); die Logs eines Daemon-Laufs
  sind frei von unerklärten yfinance-Fehler-Stürmen.
- **Carry (optionaler H4-Spot-Check, nicht blockierend):** ein zweiter, zeitversetzter
  Wiederholungslauf des H1-Blocks (z. B. am Folgetag) würde die Intermittenz-These weiter
  erhärten, ist aber kein Gate für die „Wie"-Session — der bereits vorliegende
  Zwei-Zeitpunkte-Kontrast (Live-Fail vs. Diagnose-Erfolg) reicht als Beleg.

**Step 4 — Live-Beweis (Operator; carried aus v1.5-Step-5, unverändert).**
- **5a Varietäts-Run:** mehrere Demo-Tage, normale Caps → den ersten **net-new autonomen
  open→close** in einem sauberen Lauf einfangen (jetzt mit sauberem Signal + Step-0-Logs,
  die einen Abstain-Tag erklärbar machen).
- **5b Breaker-Fire-Run:** separat, bewusst enge Caps → einen Safety-Breaker **real
  auslösen** sehen.
- Diese zwei Beweise schließen das Phase-8-✅-Gate.

**Step 5 — Doku-Flip + Carries.**
- Nach 5a/5b: ROADMAP/README/CLAUDE.md Phase 8 → ✅ (korrekte Formel; weiterhin kein
  Profit/Edge behaupten).
- **Carry (vor jedem Live-Konto zwingend, nicht v1.6-blockierend):** `point_value` für
  STXE/CAC/IBEX unabhängig bestätigen (bleibt aus IGs „(X€)"-Naming inferiert).

**Token-/Zeit-Fallback:** Wenn knapp → Step 0 (Observability) + Step 3 als **Drop** (der
billige, ehrliche Weg auf 2 verifizierte Instrumente) sind das Minimum vor Step 4. Der
Harness (Step 2) ist die Zukunftssicherung und fällt als Letztes — aber **vor** jeder
*neuen* Universum-Erweiterung.

---

## 4. Offene Fragen für die „Wie"-Session

1. **Step-0-Format/-Ort:** eine JSON-Lines-Datei pro Tag vs. eine rollende Datei in
   `data/state/`? Webui-Anzeige in v1.6 oder später? (Decision-14-Disziplin: UI liest nur.)
2. **Abstain-Taxonomie:** gehört der Ausbau der reservierten Codes
   (`EMPTY_UNIVERSE`/`VALIDATOR_REJECT`/`FILTER_FAIL`, `research_tick.py:87-89`) in Step 0
   (P4 muss dafür einen Grund nach oben reichen — kleiner Cross-Phase-Edit) oder bleibt er
   P9? Das Handover nennt die grobe v1-Taxonomie explizit als Teil des Meta-Gaps.
3. **Daily-only als tolerierter Modus (falls H1 bestätigt):** Instrument mit ehrlich
   gelabeltem daily-only-Kontext behalten (mehr Varietät, schwächeres Signal) oder droppen
   (nur voll-signalige Instrumente)? Betrifft die Fix-Präferenz (b) in Step 3.
4. **Harness-Verortung:** repo-root `scripts/verify_instrument.py` (Konvention der
   bisherigen Operator-Tools, phasenlos) vs. P3-Modul mit dünnem Script-Wrapper
   (importierbar für den v3-Promotion-Pfad)? Und: Verdikt nur ausgeben oder **persistieren**
   (Verification-Status je `InstrumentSpec` — Feld vs. Sidecar)?
5. **Fetcher-Fehler-Detail nach oben:** reicht ein strukturiertes Log aus P3 heraus, oder
   braucht `get_brain_context` eine additive „health"-Rückgabe (z. B. per-Feld-Status im
   `BrainContext`), damit P8 sie persistieren kann? (Additiv halten — Default-Shape
   unverändert.)
6. **★ NEU (aus dem Step-1-Ergebnis): yfinance-Versions-Pin-Drift.** Installiert `1.4.1`,
   gepinnt `>=0.2.65,<0.3` (`phase3_external_data/requirements.txt:6`). Klären: seit wann
   driftet die installierte Version vom Pin? War der Pin je durchgesetzt (frische
   `pip install -r requirements.txt` in einer sauberen venv)? Reproduziert eine
   gepinnte `0.2.x`-Installation das `possibly delisted`-Fehlerbild NICHT (stützt die
   Versions-Hypothese) oder GENAUSO (widerlegt sie, zurück zu reiner H4-Transienz)? Ist ein
   Re-Pin auf eine getestete `1.x`-Version sicherer als ein Downgrade (P3-Tests liefen
   bereits gegen die installierte `1.4.1` grün — ein Downgrade könnte selbst neue Brüche
   einführen)?

---

## 5. Cross-Phase-Register — ✅ so umgesetzt (die „Wie"-Session, 2026-07-02)

> Ursprünglich antizipiert (s. Historie unten); hier durch den tatsächlichen Umsetzungsstand
> ersetzt (Code = Source of Truth). Kein Drop-Pfad genommen (Step 3 = Tolerieren) → **kein**
> `ticker_map.py`/`EXTENDED_UNIVERSE`/`execution/config.py`-Touch.

| Phase | Datei | Tatsächlicher Edit | Default unverändert? |
|---|---|---|---|
| P3 | `external_data/requirements.txt` | Re-Pin `yfinance>=0.2.65,<0.3` → `>=1.4.0,<1.5` (Step 3a) | n/a (Dep-Pin) |
| P3 | `external_data/models.py` + `fetcher.py` | `BrainContext.field_errors` (Step 0, additiv, nicht im Prompt-Dict) | ja — additiv |
| P4 | `research/models.py` + `context_builder.py` + `research.py` | `ResearchContext.brain_context_health` + `Research.last_context_health`/`last_abort_detail` (Step 0, additiv) | ja — additiv |
| P8 | `scheduler/observability.py` (neu) + `research_tick.py` + `config.py` + `runner.py` + `__init__.py` | Per-Zyklus-JSONL-Log (Step 0, additiv, nur auf dem `can_open`-PASS-Pfad) | ja — additiv |
| — | `scripts/verify_instrument.py` (neu) | der Verification-Harness (Step 2, read-only) | n/a (read-only Tool) |
| — | `tests/test_verify_instrument.py` (neu) | 22 Tests, `importlib`-Pattern | n/a |
| root | `.gitignore` | `data/state/research_health.jsonl` ergänzt | n/a |
| docs | `phase3_external_data/CLAUDE.md`, `phase4_research/CLAUDE.md`, `phase8_scheduler/CLAUDE.md`, dieser Plan | dated Notes je Edit; ✅-Flip weiterhin erst nach Step 4 (Live-Beweis, Operator) | n/a |

**Nicht angefasst (Step 3 = Tolerieren, kein Drop/Fix nötig):** `external_data/ticker_map.py`,
`research/models.py`s `EXTENDED_UNIVERSE`-Liste selbst, `execution/config.py` `point_values`.

> Regression nach jedem Step separat grün (bekannte `tests.conftest`-Namenskollision):
> **P1 52 · P2 67 · P3 73 (+1) · P4 133 (+11) · P5 154 · P6 70 · P7 131 · P8 197 (+15) ·
> root-`tests` 50 (+22)** — Baseline bei v1.6-Start war P1 52 · P2 67 · P3 72 · P4 122 ·
> P5 154 · P6 70 · P7 131 · P8 182 · root-`tests` 28.

---

*Ende des Plans (Was + Wie). Step 4 (Live-Beweis) und Step 5 (Doku-Flip) sind Operator-Schritte —
s. `phase8_scheduler/CLAUDE.md` → `## Session stopped` (v1.6 „Wie") für die volle Implementierungs-
Zusammenfassung.*
