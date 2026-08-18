---
status: snapshot
purpose: Abschluss-Handover nach dem formalen Scheitern von P12.5. Nachgemessener As-Built-Stand (Code/Tests/DB, nicht aus Vordokumenten übernommen), zwei datierte Korrekturen an der bisherigen Root-Cause-Erzählung, und die Empfehlung eines strukturell anderen Wegs statt der nächsten Patch-Runde.
read-when: als erstes Dokument der nächsten Session an diesem Track — VOR jedem Detailplan und vor jedem erneuten Scharfstellen des Messarms
detail: L3
up: ./CLAUDE.md
down:
  - ./PHASE12_5_FAILURE_HANDOVER.md          # 📕 Sofort-Befund vom Interventionstag (zwei Aussagen hier korrigiert, §2)
  - ./PHASE12_5_MEASUREMENT_ARM_PLAN.md      # 📕 der gescheiterte Plan (unverändert, nicht editiert)
  - ../docs/concepts/phase12_data_foundation_plan.md   # 📕 Phase-12-Plan: Anforderungen A–G, §7 Done-Kriterium
updated: 2026-08-18
---

# P12.5 — Closeout-Handover: warum der nächste Schritt kein Patch sein sollte

> **Autor:** Claude Code, 2026-08-18 (zweite Session des Tages, read-only nachgemessen).
> **Adressat:** die nächste Session an diesem Track, bevor sie einen Detailplan schreibt.
> **Verhältnis zu [`PHASE12_5_FAILURE_HANDOVER.md`](./PHASE12_5_FAILURE_HANDOVER.md):** jenes
> Dokument hält den Interventionstag fest und bleibt gültig, mit **zwei Ausnahmen** (§2). Dieses
> hier ist der Abschluss und ersetzt insbesondere dessen Empfehlungsteil (§5).

---

## §1 BLUF

P12.5 ist **formal geschlossen und gescheitert**. Alle fünf Code-Änderungen sind korrekt und
bleiben. Gescheitert ist nicht der Code, sondern die **Betriebsannahme**, ein Auflöse-Pfad dürfe
sich seine Daten bei Bedarf bei einer bezahlten, kontingentierten Quelle nachkaufen.

Die entscheidende neue Zahl dieser Session, direkt aus `data/bars.sqlite` nachgemessen:
**von 1782 bei IG gekauften 1-Minuten-Bars trugen 1638 (92 %) Zeitstempel, die als
yFinance-Bar bereits im Archiv lagen.** Gekauft wurden ~144 Bars echter neuer Information —
für 4515 Punkte.

Damit ist die Frage entschieden, die die bisherige Empfehlung offen ließ: das Problem ist
nicht, dass zu *teuer* gekauft wird. Das Problem ist, dass überhaupt gekauft wird.
**Empfehlung: Option B in §4 — der Auflöse-Pfad kauft nie wieder Daten.** Das ist eine
Löschung, kein Umbau.

---

## §2 Zwei datierte Korrekturen an der bisherigen Erzählung

Beide gegen Code und Live-DB geprüft, nicht gegen Dokumente. Der 📕-Snapshot
`PHASE12_5_FAILURE_HANDOVER.md` bleibt konventionsgemäß **unverändert**; diese Sektion ist
die Supersession.

**K1 — U3 ist NICHT der Auslöser des Kostenpfads (Korrektur zu Failure-Handover §2 und zum
Session-8-Block in [`CLAUDE.md`](./CLAUDE.md)).**
Die Bedingung in `data_foundation/service.py:218-219` lautet
`_covers_tail(...) and coverage_ratio(...) >= _MIN_WINDOW_COVERAGE`. Python wertet von links
aus und kurzschließt: ist `_covers_tail` bereits `False`, wird U3s Schwelle nie erreicht.
`_covers_tail` verlangt eine Bar, die **höchstens ein Bar-Intervall (1 Minute) alt** ist —
gemessen am 18.08. lag die jüngste yF-Bar bei 15:05 und wurde um 15:20 geholt, also ~15 Minuten
Verzug (yFinance-Eigenverzug; der Recorder pollt alle 300 s, `run.py:119`, ist also nicht die
Ursache). `_covers_tail` war deshalb strukturell **immer** `False`, und U3s
`coverage_ratio` (bei 486 archivierten yF-Bars ≈ 0,95, weit über der Schwelle 0,5) hat den
Refetch nie ausgelöst — es *konnte* ihn nicht auslösen.
**Folge, sauber getrennt in zwei Aussagen:**
- **Preis pro Call (301 Punkte): fix-unabhängig.** Er folgt allein aus `count` über das volle
  Fenster und hätte ohne jeden P12.5-Fix identisch gegolten. Der Pfad lag seit Phase-12-Step-4
  latent und brauchte nur eines: dass überhaupt Shadow-Trades existieren, damit `bar_fetch` je
  aufgerufen wird. **Auslöser ist das Einschalten des Messarms, nicht U3** — U3 ist damit als
  Auslöser vollständig entlastet.
- **Anzahl der Calls (15): nicht fix-unabhängig.** U2 wandelt einen sofortigen Abschreiber in
  einen gezählten Retry um; damit bleiben mehr Trades fällig, und mehr fällige Trades bedeuten
  mehr `bar_fetch`-Aufrufe. Die 15 sind eine **Nach-U2-Zahl**. Das deckt sich mit dem
  Failure-Handover („U2 verschärft es") und widerspricht ihm nicht — U2 hat den Verbrauch
  plausibel erhöht, ohne die Ursache zu sein. Die Ursache ist der Preis pro Call, und der ist
  ein Entwurfsfehler, der bisher nur nie ausgeführt wurde.

**K2 — Zahlenkorrektur (zu Failure-Handover §0).** Dort: „41 von 90 Zeilen mit
IG-Beteiligung". Nachgemessen: die 90 Zeilen des 18.08. sind **45 Paare** (SHADOW_BUY/SELL),
davon **70 aufgelöst**, und mit IG-Beteiligung sind **54 von 70** (28 × `ig`, 26 × `ig+yf`);
16 rein `yf`. 20 Zeilen blieben `OPEN` (Scheduler mitten im Lauf gestoppt) und werden beim
nächsten Start über den Staleness-Guard typisiert ablaufen, nicht auflösen.

**Nebenbei korrigiert:** `ROADMAP.md` nannte „P12 117" Tests; tatsächlich sind es **123**
(`phase10_v3` 160), heute beide grün gelaufen.

---

## §3 As-Built-Stand, selbst nachgemessen (nicht aus Vordokumenten übernommen)

| Frage | Antwort |
|---|---|
| **Fertiggestellt** | P12.5-Plan Steps 1–3 (fünf Code-Änderungen: U1, U2, U3, U5, Entscheidung B) + Step 4 (Neustart, Operator) + Step 5 (falsifizierbarer Nachweis, vierteilig). **Steps 6 (Beweiswoche) und 7 (PASS-Handover) entfallen ersatzlos** — sie wurden nie begonnen. |
| **Getestet** | `phase12_data_foundation/tests` **123 passed**, `phase10_v3/tests` **160 passed** (heute getrennt gelaufen, Konvention `reference_running_phase_tests`). **Lücke:** keine einzige Zusicherung im Suite betrifft *Kosten* — `test_service.py` prüft, **dass** ein Refetch feuert, nie **wie viele Punkte** er kostet. Genau deshalb konnten 123 grüne Tests diesen Fehler nicht sehen. |
| **Live validiert** | U1, U2, U3 und Entscheidung B gegen echte Produktionsdaten belegt (Details Failure-Handover §1). Requirement **E** erstmals real: `resolution_source` befüllt, 70 Zeilen, **ein** Tag. |
| **Nur offline bewiesen** | **U5** (Shadow-Deadline-Marge): Rechnung `17:30 − 10 min = 17:20` + AST-Struktur-Guard, **keine** Live-Beobachtung. Ebenso rein offline: sämtliche Kriterien A–D und G aus Plan §7. |
| **Committet / gepusht** | 4 Commits auf `main` (`cc3770e`, `83d5ef3`, `ff5741c`, `4bdd808` + dieser). **Nicht gepusht** — `main` liegt vor `origin/main`. Push bleibt bewusste Einzelfreigabe. |
| **Nicht erreicht** | Das **Done-Kriterium der Phase 12** (Plan §7, eine durchlaufende Beweiswoche gegen A–G) — unverändert offen. Requirement **F aktiv gerissen** (4731/10 000 an Tag 1, Soll < 1500/Woche). A–D, G: ungeprüft. Step 9 nie begonnen, Step 10 (Lightstreamer) weiter gegatet. **U4** (TickerMapper wird nur beim Prozessstart befüllt, `wiring.py:175-180`) und **Entscheidung C** (SUN*-Epics) bleiben ungebaut. Phase-11-Kernfrage **WI-2/W2 unverändert unbeantwortet** — der eigentliche Zweck des ganzen Strangs. |

**Betriebszustand jetzt:** Scheduler gestoppt (kein IG-Verbrauch). Recorder läuft weiter
(`pid 33151`, `python -m data_foundation.run`) — reiner yFinance-Prozess, kostenlos, füllt das
Archiv weiter. Das ist erwünscht: es baut genau die Substanz auf, von der Option B lebt.

**Bild:** [`../docs/architecture/phase12_5_failure.svg`](../docs/architecture/phase12_5_failure.svg)
(Fehlerbild + Zielbild + was offen bleibt).

---

## §4 Offene Entscheidung 1 — der Weg nach P12.5

> Der Nikinger hat vorgegeben: **kein Patch-nach-Patch mehr.** Die Optionen sind entsprechend
> geschnitten; A steht nur der Vollständigkeit halber da.

**Option A — die Patch-Leiter (Failure-Handover §5: Spend-Kind-Tagging → Lücken-Fetch statt
Vollfenster → Drossel).**
*Folge:* Drei Eingriffe, davon einer in die Provider-Contracts. Der Verbrauch fiele rechnerisch
in den zulässigen Bereich (15 Calls × ~15 Bars ≈ 225 Punkte/Tag) — die Kostenrechnung dieser
Option ist also **nicht** falsch. Falsch ist ihre Prämisse: sie kauft weiterhin Daten, die das
Archiv ~15 Minuten später ohnehin kostenlos hat (92 %-Befund, §1), und lässt die Kopplung
„Auflösung hängt an einer bezahlten Live-Quelle" bestehen. Der nächste unentdeckte Pfad in
dieser Kopplung ist dann die nächste Überraschung. **Nicht empfohlen.**

**Option B — Beschaffung und Verbrauch entkoppeln (EMPFOHLEN).**
Der Tracker-Pfad kauft **nichts** mehr. Konkret ändert sich eine Frage:
`get_window` fragt heute „reicht das Archiv bis *jetzt*?" (`_covers_tail` gegen `end_utc = now`).
Richtig wäre „deckt das Archiv das Fenster **dieses Trades** bis `time_stop_utc`?". Ist es noch
nicht gedeckt, bleibt der Trade offen und wird beim nächsten Tick erneut geprüft — bei 240 Minuten
Haltedauer gegen ~15 Minuten Quellverzug kostet das Warten **null Messqualität**. Ist es dauerhaft
nicht gedeckt, greift ein typisierter Status. IG-Punkte fließen dann nur noch in Research,
Promotion-Probe und Divergenz-Sample (gemessen 65 Punkte/Tag) — Anforderung F ist per Konstruktion
erfüllt statt per Tuning.
*Folge:* Netto eine **Löschung** (der IG-Top-up-Zweig `service.py:229-238` und der Vollfenster-
Refetch im Tracker-Seam entfallen) plus eine geänderte Abdeckungsfrage; kein neuer Provider-
Contract, keine neue Abhängigkeit. Preis: manche Trades lösen später oder gar nicht auf —
und genau diese Rate wird damit zur **gemessenen Größe** statt zur Annahme. Existenzbeweis, dass
das trägt: `IX.D.IBEX.FWM2.IP` löste am 18.08. 14 von 14 Trades rein aus yF auf, ohne einen
IG-Punkt.

**Option C — Stream zuerst (Step 10 entgaten und vorziehen).**
Lightstreamer-Mitschrieb ins selbe Archiv bauen, damit die Abdeckung echt lückenlos wird, und
erst danach messen.
*Folge:* Löst die Abdeckungsfrage an der Wurzel, ist aber die teuerste Variante an Zeit und hat
eine **ungelöste Kernfrage** (LS braucht CST/XST aus einer IG-REST-Session → Parallel-Login-Falle;
Plan §6 Step 10 nennt drei Optionen, keine entschieden). Verschiebt jede Messung um Wochen.
**Empfehlung: nicht jetzt** — aber als Folgeschritt offenhalten, *gegatet auf die von Option B
gemessene Abdeckungsrate*. Damit entscheidet eine Zahl über C, keine Vermutung.

**Geltungsbereich von Option B — bewusst nur der Tracker-Seam.** Der Research-Seam
(`service.py:190-201`) trägt dasselbe Muster: er prüft `coverage_ratio >= 1.0` gegen ein Fenster,
das **ebenfalls bei `now` endet**, kann diese Prüfung mit yFinances ~15-Min-Verzug also praktisch
nie bestehen und geht jedes Mal an die Kette. Heute ist das harmlos, weil dort `count` klein ist
(gemessen 10 × 5 Punkte) — aber das ist eine **Eigenschaft der aktuellen Parametrisierung, keine
Garantie**. Der Research-Seam will legitim frische Daten (der Tracker nicht), deshalb ist die
Löschung dort **nicht** die richtige Antwort; er braucht eine eigene, kleine Entscheidung. Wer
Option B umsetzt, sollte das explizit als „nicht in diesem Schnitt enthalten" festhalten, statt es
stillschweigend mitzunehmen oder zu vergessen.

**Nebenbedingung, unabhängig von der Wahl:** die heutige Gating-Reihenfolge ist verkehrt herum —
Step 10 ist auf eine bestandene Beweiswoche gegatet, während die Beweiswoche an fehlender
Abdeckung scheitert. Option B löst das auf, indem sie die Abdeckung zur Messgröße macht, statt sie
vorauszusetzen.

---

## §5 Offene Entscheidung 2 — Nummerierung / Label

Projektweit sichtbar, deshalb **nicht von Claude entschieden** (bereits im Failure-Handover §5
angestoßen, weiterhin offen).

- **B1 — kein neues Unter-Label:** ein klein geschnittener Fix-Block direkt in
  `phase12_data_foundation/`, Phase 12 bleibt Phase 12. *Folge:* keine Doku-Kaskade, aber die
  Historie „Phase 12 → P12.5 → ?" wird unschärfer.
- **B2 — eigenes Label (P12.6 o. ä.):** *Folge:* saubere Nachvollziehbarkeit, aber ein weiteres
  Unter-Label an einem Strang, der bereits an einem Unter-Label gescheitert ist — und ein neues
  Label suggeriert Fortsetzung, wo ein Bruch gemeint ist.

*Empfehlung:* **B1**, konsistent mit dem Failure-Handover. Option B in §4 ist eine Löschung plus
eine geänderte Bedingung — dafür ein eigenes Phasen-Label zu ziehen wäre mehr Buchhaltung als
Arbeit.

---

## §6 Offene Entscheidung 3 — wann darf der Messarm wieder scharf

Das rollierende 7-Tage-Fenster trägt am 2026-08-18 **4731 Punkte**; IG selbst meldete um 14:08
noch **5054 von 10 000** Rest. Der Verbrauch rollt erst gegen **2026-08-25** wieder ab.

- **C1 (empfohlen):** kein Neustart mit IG-berührendem Messarm, bevor (a) Option B umgesetzt ist
  **und** (b) eine frische `remainingAllowance`-Beobachtung vorliegt (`scripts/probe_allowance.py`,
  5 Punkte). Erst rechnen, dann starten.
- **C2:** sofort neu starten, nur mit abgeschaltetem Shadow-Arm. *Folge:* kein Verbrauch, aber
  auch keine Messung — das ist der Zustand, gegen den die Notbremse von Phase 11 gezogen wurde.

**Operativ offen und billig:** die 20 am 18.08. offen gebliebenen Shadow-Zeilen. Sie laufen beim
nächsten Start typisiert ab (Staleness-Guard) — kein Eingriff nötig, aber die nächste Auswertung
sollte sie nicht als Messausfall verbuchen.

---

## §7 Delta seit [`PHASE12_5_FAILURE_HANDOVER.md`](./PHASE12_5_FAILURE_HANDOVER.md) (gleicher Tag)

1. **Root Cause präzisiert und teilweise korrigiert** — K1/K2 in §2. Nicht U3, sondern das
   Einschalten des Messarms; die Fixes sind vollständig entlastet.
2. **Der 92-%-Duplikat-Befund** (§1) ist neu und ist der Grund, warum die Empfehlung von
   „billiger kaufen" auf „nicht kaufen" kippt.
3. **Mechanismus benannt:** yF-Eigenverzug ~15 Min vs. `_covers_tail`-Anspruch ≤ 1 Min — der
   teure Zweig war nie der Ausnahmefall.
4. **Empfehlungsteil ersetzt:** Failure-Handover §5 (drei Bausteine) → §4 hier (drei Optionen,
   B empfohlen, A explizit abgelehnt).
5. **Testlücke benannt:** keine Kosten-Zusicherung in 123 grünen Tests (§3).
6. **Zweiter Fundort desselben Musters:** der Research-Seam prüft ebenfalls gegen `now` und
   besteht die Prüfung deshalb praktisch nie — heute billig, aber nicht per Entwurf (§4,
   Geltungsbereich).
7. **Unerklärt und bewusst nicht geraten:** warum `IX.D.IBEX.FWM2.IP` als einzige Epic ohne
   IG-Beteiligung auflöste (identische Zeitfenster und identische yF-Abdeckung wie die anderen
   vier; `research_health.jsonl` zeigt für sie dennoch 10 `ig`-ok-Events). Eine Frage, die die
   nächste Session in Minuten klären kann — und die Antwort ist für Option B unmittelbar
   relevant, weil FWM2 der Existenzbeweis ist.

---

## §8 Was die nächste Session zuerst tun sollte

1. Diesen Kopf und §4 lesen; **Entscheidungen §4/§5/§6 einholen**, bevor irgendetwas geplant wird.
2. Erst dann einen Detailplan schreiben — und in ihm die **erste Akzeptanzbedingung als
   Kostenzusicherung** formulieren (ein Test, der fehlschlägt, wenn der Tracker-Pfad überhaupt
   einen IG-Punkt ausgibt). Das ist die Lehre aus §3.
3. Bindend übernehmen: die **Werktags-Arbeitsregel** vom 2026-08-17 (Phasen-`CLAUDE.md`,
   „Rahmen") — bot-berührende Arbeit ist erlaubt, vorher Bot stoppen, Live-/Netz-/kostenpflichtige
   Läufe macht der Nikinger, DB nur `mode=ro`.
4. **Nicht** anfassen: die fünf P12.5-Fixes (korrekt, live belegt), den 📕-Plan und den
   📕-Failure-Handover (superseden, nicht editieren).
