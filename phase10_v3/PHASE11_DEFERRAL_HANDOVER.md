---
status: snapshot
purpose: Notbremse — Phase 11 wird DEFERRED, bevor ihre Ziele erreicht sind, weil drei Datenwochen an derselben Wurzel gescheitert sind und diese Wurzel wichtiger ist als Phase 11 selbst. Enthält Status, Delta seit dem letzten Handover, die Durability-Anforderungen für den neuen Track (Datenfundament) und die offenen Entscheidungen. KEINE Implementierungsdetails — Code ist Wahrheit.
read-when: als erstes Dokument der nächsten Session; vor jeder weiteren Arbeit an Paper-Trades, H-Serie oder Scheduler-Neustart
detail: L3
up: ./CLAUDE.md
updated: 2026-08-11
---

# Phase 11 → Datenfundament: Deferral-Handover (2026-08-11)

> **Autor:** Claude Code, 2026-08-11, docs-only (kein Code berührt).
> **Adressat:** die **nächste Claude-Code-Session**. Ab jetzt schreibt Claude Code die
> Handovers direkt aus dem Repo — kein Google-Drive-Umweg (Nikinger, 2026-08-11). Der
> zugehörige, für Claude Code umgeschriebene Auftrag liegt in
> [`../docs/HANDOVER_PROMPT.md`](../docs/HANDOVER_PROMPT.md).
> **Was dieses File ist:** ein ehrlicher Abbruch, keine Erfolgsmeldung. Phase 11 wird
> **vor Erreichen ihrer Ziele** zurückgestellt.

---

## §0 BLUF

Phase 11 sollte **eine** Frage beantworten — **WI-2/W2: erreicht ein 30-Punkte-Stop /
45-Punkte-Ziel je seinen 240-Minuten-Time-Stop, oder liegt die Geometrie unter dem Rauschen?**
Nach **drei** Datenwochen: **null** Antworten, dreimal an Infrastruktur gescheitert, nie an der
Messung.

Die Wurzel ist gefunden und sie ist größer als Phase 11: **das Datenfundament ist strukturell
unzuverlässig.** Der Nikinger zieht die Notbremse — erst das Fundament, dann wieder messen.
Diese Reihenfolge ist richtig, und die Begründung steht in §2.

**Der härteste Einzelbefund** (§2.3): die Mehrquellen-Kette, die genau dieses Problem lösen
sollte, **existiert seit Phase 9 fertig gebaut und getestet — und lief noch nie.**
`enable_ig_bars` ist `False` per Default, wird von keinem Startskript gesetzt und taucht in
keinem Log auf.

---

## §1 Status

### Phase 10 (V3) — ✅ abgeschlossen, unverändert
Block A (Abstain-Lessons) und Block B (`market_context` + Paper-Pipeline) sind live auf `main`
und bleiben es. Nichts an dieser Notbremse stellt Phase 10 in Frage.

### Phase 11 (Funnel-/Mess-Fixes) — 🛑 DEFERRED, teilweise geliefert

| Item | Stand | Anmerkung |
|---|---|---|
| B1 point_value-Drift | ✅ gefixt | 40×-Oversizing, erklärt 3 historische Broker-Rejects |
| B2 Reward-Skala | ✅ Skala gefixt | Rest (`clean_exit_bonus`) → H3, offen |
| B4/H6 Mess-Substrat | ✅ gefixt | |
| B5 Lesson-Längengrenze | ✅ gefixt (08-08) | Satzgrenzen-Trimmung, Grenze dokumentiert |
| B3 Margin-Headroom | ⏸ deferred | eigene Session, startet mit Live-Check |
| H1 Shadow-Pairs | ✅ gebaut, 1 Woche gelaufen | **parkiert** — hat den Allowance-Kollaps ausgelöst |
| H4-a Lesson-Alters-Cap | ✅ gebaut (08-08) | **Wirkung ungemessen** |
| H3 / H5 / H7 | ❌ offen | |
| **WI-2 / W2** | ❌ **unbeantwortet** | der eigentliche Zweck der Phase |

**Alles Gebaute bleibt auf `main`, nichts wird zurückgerollt.** „Deferred" heißt: keine weitere
H-Serie, kein Paper-Trade-Ausbau, kein Scharfschalten von H1, bis das Fundament steht.

### Was nachweislich **nicht** verifiziert ist
Sämtliche Fixes vom 08-08 (Stale-Expiry, Budget-Breaker, Fetch-Cap, Phase-9-`RATE_LIMIT`-Guard,
B5, H4-a) sind **ausschließlich offline** bewiesen — 1336 grüne Tests, kein einziger Lauf gegen
echte IG-Daten. Der nächste Daemon-Start ist ihr erster Realkontakt.

---

## §2 Delta seit dem letzten Handover

Letzter Handover: `phase8_scheduler/PHASE8_CLOSEOUT_HANDOVER.md` (2026-07-03) → begründete V2
(Phase 9). Was seitdem passiert ist, in der Reihenfolge der Wichtigkeit:

### 2.1 Der Auslöser des letzten Reframes ist zurück — unverändert

Der P8-Closeout wurde geschrieben, **weil yFinance-Daten intermittierend ausfielen** und die
Entscheidung lautete: „nicht zum dritten Mal symptomatisch patchen, sondern re-scopen." Daraus
entstand V2 mit dem ausdrücklichen zweiten Auftrag **„V2b — Daten-Input-Zuverlässigkeit"**.

Heute stehen wir am selben Punkt, mit anderer Quelle. **Das ist das zweite Reframe an derselben
Wurzel.** Wer diesen Handover liest, sollte das als Warnung lesen, nicht als Zufall: die
Datenschicht ist zweimal als Problem erkannt und zweimal nicht zu Ende gebracht worden.

### 2.2 Warum drei Messwochen ausfielen

| Woche | Gescheitert an | Klasse |
|---|---|---|
| 1 (07-20/24) | `"MINUTE_1"` ist keine gültige IG-Resolution | Kontrakt-Drift |
| 2 (07-27/31) | Research-Funnel liefert 0 Kandidaten | Feedback-Schleife |
| 3 (08-03/07) | IG-Kontingent erschöpft → 18/22 Epics quarantined | Ressourcen-Modell fehlt |

Dreimal unterschiedliche Symptome, dreimal dieselbe Ebene: **die Beschaffung, nicht die
Auswertung.** Die Messlogik war jedes Mal in Ordnung.

### 2.3 Der strukturelle Kern — eine Fehlerklasse, dritte Instanz

> **Ein statisches, handgepflegtes Artefakt muss mit einer autonom wachsenden Menge synchron
> bleiben, und nichts erkennt die Divergenz.**

| Instanz | Statisch | vs. wachsend | Preis |
|---|---|---|---|
| B1 (07-31) | `EXTENDED_UNIVERSE`-`point_values` | DB-Universum | 40×-Oversizing, 3 Rejects |
| **heute** | `KNOWN_YF_TICKERS` / `TickerMapper._MAP` | entdecktes Universum | Fallback deckt **1 von 4** aktiven Epics |
| (latent) | Ressourcenannahme „Bars sind gratis" | reales IG-Kontingent | 3. Messwoche vernichtet |

Dieselbe Tatsache — *welches yFinance-Symbol gehört zu diesem Epic* — liegt in **drei**
divergenten Speichern, geschrieben von **einem** Writer, **einmal**, per Namensabgleich:
`phase9_universe/universe/discovery.py:57,240` · `instrument_universe.yf_ticker` ·
`phase3_external_data/external_data/ticker_map.py:31`. Zur Laufzeit gewinnt die DB
(`phase8_scheduler/scripts/wiring.py:203-210` registriert aus `active_universe()`).

**Warum die Abdeckung zwangsläufig verfällt:** Discovery ist der einzige Writer und läuft nur
bei der Entdeckung. Jedes neu gefundene Instrument, dessen *Name* nicht in einer 12-Einträge-
Tupel steht, bleibt dauerhaft `NULL`. V2a wurde gebaut, um autonom Instrumente zu finden — die
Zuordnung wurde nicht dafür gebaut. Die sieben aktuell unzugeordneten Epics sind Dow, FTSE 100,
Nasdaq, S&P 500 und drei Wochenend-Varianten; ihre Symbole sind vollkommen gewöhnlich. Sie
fehlen, weil niemand ein Tupel editiert hat.

### 2.4 Der Befund, der alles einordnet: V2b wurde gebaut und nie eingeschaltet

`ChainedBarProvider` (IG→yFinance, mit Circuit-Breaker und Divergenz-Check) existiert seit
Phase 9 Step 6, ist getestet und im Wiring verdrahtet — **hinter `enable_ig_bars`, Default
`False`**. Kein Startskript setzt das Flag, kein Log kennt es. Lightstreamer (Step 7b) wurde
mit „kein Fix-Target" geparkt.

Daraus folgt die eigentliche Diagnose dieser Phase, und sie ist unbequem:

> **Die entdeckende Hälfte von V2 lief mit voller Geschwindigkeit, die absichernde Hälfte blieb
> dunkel.** Der Abstand zwischen beiden ist exakt der heutige Ausfall.

### 2.5 Externes Kontingent, hart und nicht verhandelbar
IG: **10.000 historische Datenpunkte/Woche**, kontoweit, festes 7-Tage-Fenster ab dem ersten
Request nach einem Reset. Im erschöpften Zustand liefert IG **keine** Auskunft über den Reset —
weder per API noch im Dashboard (vom Nikinger geprüft). Eine Limit-Erhöhung ist bei Privatkunden
faktisch nicht erreichbar (unabhängig bestätigt). Details:
[`./ALLOWANCE_INCIDENT_2026-08-08.md`](./ALLOWANCE_INCIDENT_2026-08-08.md).

### 2.6 Korrektur an [`./DATA_SOURCE_STRATEGY_2026-08-11.md`](./DATA_SOURCE_STRATEGY_2026-08-11.md)
Dieses Dokument (heute früher geschrieben) stützt sich in §2 auf das Setup eines Kollegen des
Nikinger als Bestätigung. **Der Kollege bezeichnet sein System selbst als Workaround, nicht als
funktionierendes System** — die Bestätigung wird damit zurückgezogen. Die *Richtung*
(mehrquellig, IG nur für Orders) bleibt plausibel; die Zuversicht nicht. Ebenso zu schwach: der
Vorschlag, einfach die Kette zu verdrahten, hätte auf dem realen aktiven Universum **1 von 4**
Epics abgedeckt.

---

## §3 Der neue Track — Anforderungen, nicht Lösung

Was folgt sind **Durability-Anforderungen**. Sie sind bewusst als Eigenschaften formuliert, die
prüfbar sind, nicht als Bauanleitung — die Lösung entwirft die nächste Session, gegen den Code.

> **Explizit erlaubt (Nikinger, 2026-08-11): „by all means".** Die frühere Grenze „kein Rewrite"
> ist aufgehoben. Wenn Dauerhaftigkeit einen Umbau der Datenschicht verlangt, ist der Umbau der
> Auftrag. Ein weiterer Patch auf dieselbe Fehlerklasse ist **nicht** akzeptabel.

**A — Eine Wahrheit pro Tatsache.** Eine Instrument-Eigenschaft (Symbol, `point_value`,
Handelbarkeit) hat genau **einen** Speicher, den alle Konsumenten über **eine** Naht lesen.
Kriterium: ein Grep nach der Tatsache findet einen schreibenden Ort, nicht drei.

**B — Abgeleitet, nicht deklariert.** Eigenschaften eines Instruments kommen vom Instrument
(IG-Metadaten), nicht aus einer parallelen Tabelle. Statische Tabellen dürfen nur noch
**Fallback** sein, nie Quelle. Kriterium: ein neu entdecktes Instrument ist ohne Code-Edit
vollständig beschrieben — oder es ist ausdrücklich als unvollständig markiert (D).

**C — Divergenz ist erkennbar.** Es gibt einen wiederkehrenden Abgleich, der laut fehlschlägt,
wenn abgeleitete und konsumierte Menge auseinanderlaufen. Kriterium: B1 wäre damit **beim
Auftreten** aufgefallen, nicht drei Wochen später in einer Datenreview.

**D — Degradierung ist typisiert und laut.** „Keine Quelle für dieses Instrument" ist ein
erstklassiger Zustand mit eigenem Feld und eigenem Event — kein `NULL`, das still auf einen
Default fällt. Ein degradiertes Instrument wird **von der Messung ausgeschlossen**, nicht
stillschweigend mitgemessen. Kriterium: die Fehlerklasse aus §2.3 kann nicht mehr still sein.

**E — Provenienz an jeder Messzeile.** Jede Bar trägt, welche Quelle sie geliefert hat, und jede
Messzeile trägt das weiter. Ohne das ist eine gemischte IG/yFinance-Woche **nicht auswertbar**
(unterschiedliche Spreads und Zeitstempel). Kriterium: eine SL/TP-Verteilung ist nach Quelle
filterbar.

**F — Ressourcen sind modelliert, nicht entdeckt.** Jede Quelle hat ein deklariertes
Kontingentmodell und laufende Verbrauchsrechnung; Erschöpfung wird **vorhergesagt**, nicht als
403 erlebt. Kriterium: der 08-03-Vorfall wäre vor dem ersten Fehlversuch sichtbar gewesen.

**G — Messfähigkeit ist eine Betriebseigenschaft.** Eine Woche, in der keine Messung entsteht,
muss **am selben Tag** auffallen, nicht am Freitag der Review. Drei Wochen Totalausfall ohne
Alarm sind der eigentliche Skandal dieser Phase.

**Ausdrücklich nicht Teil der Anforderungen:** eine bestimmte Technologie. Lightstreamer,
Tick-Recorder, weitere Provider — alles Kandidaten, keiner ist gesetzt. Insbesondere gilt
weiterhin (unverändert korrekt): **Lightstreamer ist ein Live-Tick-Strom und beantwortet die
rückblickende High/Low-Frage des Trackers nicht**, außer man schreibt den Strom selbst mit —
was ein Eigenbau ist und als solcher zu bewerten wäre, nicht als „nur ein Flag".

---

## §4 Offene Entscheidungen (Nikinger)

1. **Nummerierung.** Vorschlag: **Phase 12 = Datenfundament**, V4 rutscht auf **Phase 13** —
   konsistent mit dem Präzedenzfall vom 2026-08-01 (V4 wurde schon einmal 11→12 verschoben).
   Alternative: ein nicht-numerischer Track wie der Meta-Strang M1. **Nicht eigenmächtig
   entschieden**, weil die Nummerierung projektweit in fünf Dokumenten sichtbar ist.
2. **Reichweite von B (abgeleitet statt deklariert).** Braucht als erstes einen **Live-Check**
   von `get_market_info` auf einem zugeordneten und einem nicht zugeordneten Epic, um zu sehen,
   welche Felder IG überhaupt liefert. **Nikinger-Aufgabe** (Repo-Konvention). Sinnvoll zu
   bündeln mit B3s ausstehendem `/markets/{epic}`-Margin-Check — dieselbe Response.
3. **Umgang mit dem erschöpften Kontingent.** Das Restart-Gate aus
   `ALLOWANCE_INCIDENT_2026-08-08.md` §6 gilt unverändert. Solange nicht gemessen wird, ist es
   allerdings **nicht dringend** — das nimmt Zeitdruck aus allen anderen Entscheidungen.
4. **Universe-Reset (18 quarantined Epics).** Weiterhin gesperrt bis zu einem beobachteten
   `remainingAllowance`. Zusätzlich jetzt: ein Reset ohne A–D wiederholt nur den Zustand, aus
   dem der Ausfall entstand.
5. **H4-as Wirkung bleibt ungemessen** und wird es bis nach dem Fundament bleiben. Der
   Alters-Cap rollt — bei einem Neustart ab dem **2026-08-20** überleben **0** Lessons, der
   Block rendert dann dauerhaft „none on record". Das ist gewollt und kein Bug, muss aber beim
   Auswerten bekannt sein.

---

## §5 Datei-Anker

**Zuerst lesen:**
- [`./CLAUDE.md`](./CLAUDE.md) — Phasenkopf + neuester Session-Block
- [`./ALLOWANCE_INCIDENT_2026-08-08.md`](./ALLOWANCE_INCIDENT_2026-08-08.md) — Kontingent, Fix, Restart-Gate
- [`./DATA_SOURCE_STRATEGY_2026-08-11.md`](./DATA_SOURCE_STRATEGY_2026-08-11.md) — Richtung, mit der Korrektur aus §2.6
- [`../docs/architecture/data_foundation.svg`](../docs/architecture/data_foundation.svg) — Fehlerbild + Zielbild

**Die Nähte, die der neue Track anfasst** (Code ist Wahrheit — hier nur Wegweiser):
- `phase3_external_data/external_data/providers.py` — `BarProvider` / `IGBarProvider` / `YFinanceBarProvider` / `ChainedBarProvider`
- `phase3_external_data/external_data/ticker_map.py` — `TickerMapper` (statische Defaults + `register`)
- `phase9_universe/universe/discovery.py` — `KNOWN_YF_TICKERS`, einziger Writer von `yf_ticker`
- `phase9_universe/universe/promotion.py` — Statusmaschine, `data_degraded`, Verify-Runde
- `scripts/verify_instrument.py` — `check_ig_side` (liest `get_market_info`, der Ort für B)
- `phase8_scheduler/scripts/wiring.py` — `_build_universe_from_db`, `_build_market_data` (`enable_ig_bars`), `_build_paper_tracker` (der einzige Bar-Konsument außerhalb der Kette)
- `phase8_scheduler/scheduler/observability.py` — `record_event`, bereits vorgesehene Event-Typen (`bar_fetch`, `quote_divergence`, `universe_*`)

**Historie, nur bei Bedarf:** `phase8_scheduler/PHASE8_CLOSEOUT_HANDOVER.md` (das erste Reframe
an derselben Wurzel), `./DATA_WEEK_REVIEW_2026-07-25.md` / `-07-31.md` / `-08-07.md`,
`./SESSIONS_ARCHIVE.md`.

---

## §6 Was die nächste Session **nicht** tun soll

- Keine weitere H-Serie, kein Paper-Trade-Ausbau, kein H1-Scharfschalten.
- **Kein vierter Patch auf §2.3.** Wenn die vorgeschlagene Lösung eine weitere Tabelle pflegt,
  ist sie falsch.
- Kein Scheduler-Neustart ohne das Restart-Gate.
- Keine Technologiewahl vor Entscheidung 2 (§4) — der Live-Check kommt zuerst.
