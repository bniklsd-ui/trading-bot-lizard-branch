---
status: snapshot
purpose: P12.5 (Messarm) wird FORMAL GESCHLOSSEN — GESCHEITERT, am selben Tag, an dem der Neustart mit beiden Flags lief. Nikinger-Entscheidung 2026-08-18, unmittelbar nach der ersten Live-Woche-Sitzung. Grund + Zahlen + was bleibt gültig + Empfehlung für das Danach. KEINE weiteren P12.5-Bauschritte, nur Tests.
read-when: als erstes Dokument der nächsten Session an diesem Track; vor jedem erneuten Scharfstellen des Messarms
detail: L3
up: ./CLAUDE.md
down:
  - ./PHASE12_5_MEASUREMENT_ARM_PLAN.md   # der gescheiterte Plan selbst (📕, nicht editiert)
updated: 2026-08-18
---

# P12.5 → Formal geschlossen, gescheitert (2026-08-18)

> **Autor:** Claude Code, 2026-08-18. **Adressat:** die nächste Session an diesem Track.
> **Was dieses File ist:** ein ehrlicher Abbruch, keine Erfolgsmeldung. P12.5 wurde am Tag
> seines eigenen Neustarts wieder gestoppt — nicht wegen der vier Code-Befunde (U1/U2/U3/U5)
> oder Entscheidung B, die alle **live bewiesen korrekt** sind, sondern weil ihr
> Zusammenspiel mit einer fünften, vorher nie exponierten Eigenschaft des Systems
> (`BarService.get_window`s Vollfenster-Refetch) das IG-Punktebudget der Woche am **ersten**
> Handelstag verbrannt hätte.

---

## §0 BLUF

P12.5 lief Steps 1–5 sauber durch: alle vier Ultrareview-Befunde + Entscheidung B sind
**live gegen echte Produktionsdaten bewiesen** — `pairs_opened: 90`, `pairs_resolved: 66`,
`pairs_typed_expired: 4`, `resolution_source` erstmals real befüllt, der Alarm-Test
(d-i) korrekt `ok=False` + `"measurement arm off"` gegen den Vortag. Der Messarm **funktioniert**.

Aber: **`resolution_source` zeigt 41 von 90 Zeilen (28 `ig`, 26 `ig+yf` — überschneidend,
tatsächlich jede Zeile mit IG-Beteiligung) mit IG-Beteiligung, und jeder dieser Top-ups holt
das komplette 300-Minuten-Fenster neu (≈301 Punkte), nicht nur die Lücke.** Innerhalb von
~4 Stunden echten Handels sind so **4565 von 10 000 Wochenpunkten** verbrannt — Requirement F
(§7, Soll < 1500/Woche) ist am **ersten** Tag gerissen, und das funktionale Restbudget
(nach `reserve_points=1500`) hätte binnen ein bis zwei weiterer Tage die Budget-Sperre
ausgelöst. **Der Nikinger hat daraufhin sofort interveniert** (2026-08-18): Scheduler
gestoppt, P12.5 formal geschlossen — **gescheitert**, keine weiteren Bauschritte unter
diesem Label, nur noch Tests.

---

## §1 Was bewiesen ist (bleibt gültig, nicht zurückrollen)

Alle fünf P12.5-Code-Änderungen (Commits `83d5ef3`, `ff5741c`) sind **unabhängig korrekt**
und **live verifiziert** — sie sind nicht die Ursache des Scheiterns und sollen **nicht**
revertiert werden:

- **U1** (`service.py:119`, IG-Timestamp-Normalisierung) — der Sampler crasht nicht mehr;
  `research_health.jsonl` zeigt saubere Läufe statt des Ein-Epic-Abbruchs von Tag 1.
- **U3** (`service.py:207`, `_MIN_WINDOW_COVERAGE`) — verhindert nachweislich stille
  Kurzschlüsse bei knappem Archiv; **ist zugleich der direkte Auslöser des Kostenproblems**
  (§2) — korrekt im Verhalten, teuer in der Konsequenz. Das sind zwei verschiedene Aussagen.
- **Entscheidung B** (`heartbeat.py`, `assess_day`) — meldet einen Nulltag jetzt korrekt
  `ok=False` + `"measurement arm off"`; live gegen den 2026-08-17-Nulltag bewiesen (Step 5
  d-i, exit code 1, Problem-String verbatim vorhanden).
- **U2** (`paper.py:588`, Retry-Cap) — belastet den Cap statt sofort abzuschreiben;
  `pairs_typed_expired: 4` und die Verteilung von `resolution_source` (statt durchgehend
  `NULL`) zeigen, dass Trades jetzt tatsächlich mehrere Versuche bekommen.
- **U5** (`wiring.py:805`, Deadline-Marge) — Rechnung `17:30 − 10min = 17:20` verifiziert;
  keine direkte Live-Beobachtung nötig, die Struktursicherung (AST-Guard) hält.

**Alle Tests grün, unverändert seit Step 3:** `phase12_data_foundation` 123, `phase10_v3` 160.

---

## §2 Die eigentliche Ursache (fünfter Befund, nicht Teil der ursprünglichen U-Liste)

`BarService.get_window` (`service.py:202-228`) fordert bei jedem Coverage-Miss — egal ob
`_covers_tail` oder die neue `coverage_ratio`-Schwelle (U3) den Ausschlag gibt — über
`self._chain.get_bars(epic, resolution=resolution, count=count)` das **komplette**
angefragte Fenster neu an, nicht nur die fehlende Lücke. `count` ist bei einem
300-Minuten-Fenster/1-Minuten-Auflösung ≈ 301 — ein IG-Top-up kostet damit fast immer den
vollen Punktpreis, auch wenn 95 % des Fensters bereits im Archiv liegen.

**Das ist kein neuer Bug von P12.5** — dieser Pfad existiert unverändert seit Phase-12-Step-4.
Er wurde nie sichtbar, weil der Messarm (der einzige Aufrufer, der große Fenster wiederholt
anfragt) bis P12.5 nie lief. **U3 ist der Auslöser, nicht die Ursache:** vor U3 hätte ein
kurzes Archiv den `_covers_tail`-Check bestanden und **gar keinen** Refetch ausgelöst (der
alte U3-Bug selbst) — U3s Korrektheit ist es, die den teuren Pfad erstmals scharf schaltet.
U2 verschärft es zusätzlich: eine Epic, die dauerhaft knapp unter der Schwelle bleibt, kann
bis zu 12 Ticks lang je einen Vollfenster-Refetch auslösen, statt nach dem ersten Fehlschlag
abzuschreiben.

**Zur Verwirrung trug bei:** der geteilte IG-Provider (`wiring.py:189`) markiert **jeden**
Call — Research **und** Tracker-Top-up — mit `spend_kind="research"`. Die Kostenexplosion
war im Ledger nicht vom normalen Research-Verbrauch unterscheidbar, bis die Punktzahlen
selbst (10× 5 Punkte vs. 15× exakt 301 Punkte) den Split erzwangen.

---

## §3 Zahlen (Stand der Intervention, 2026-08-18 ~14:35 UTC)

| Messgröße | Wert |
|---|---|
| IG-Verbrauch im rollierenden 7-Tage-Fenster | **4731 / 10 000** Punkte |
| davon heute, Tracker-Top-up (`spend_kind` fälschlich `research`, 301-Pkt-Cluster) | 4515 Punkte über 15 Calls |
| davon heute, echter Research-Verbrauch (5-Pkt-Cluster) | 50 Punkte über 10 Calls |
| Divergenz-Sampler (`kind='sample'`) | 15 Punkte über 5 Calls — unauffällig, wie geplant |
| `reserve_points` (`SourceBudget`, unverändert Default) | 1500 |
| Funktionales Restbudget zum Interventionszeitpunkt | ≈ 3554 Punkte ≈ **11–12 weitere Vollfenster-Top-ups** |
| `pairs_opened` / `pairs_resolved` / `pairs_typed_expired` (2026-08-18, vor Stop) | 90 / 66 / 4 |
| Requirement F (§7, Soll < 1500 Punkte/Woche) | **gerissen am Tag 1** |

Die von `data_health.py` ausgegebene `predicted_exhaustion_days: 7.5` ist **irreführend** —
sie mittelt über den langen ruhigen Zeitraum vor dem Neustart und unterschätzt die reale
Erschöpfungsgeschwindigkeit massiv. Nicht ungeprüft zitieren.

---

## §4 Intervention (Nikinger, 2026-08-18)

> **Entscheidung, wörtlich:** „Let's intervene now - phase 12.5 is formally over - failed.
> We are still spending too much points, so we have to work on a different solution. I
> think phase 12.5 shouldn't have any more steps apart from testing."

1. Scheduler (`pid 46390`, `--enable-divergence-sampler --enable-shadow-schedule`) per
   `kill` gestoppt — sofortiges Ende weiterer IG-Käufe.
2. Recorder (`pid 33151`) **unverändert weiterlaufen gelassen** — reiner yFinance-Prozess,
   kein IG-Verbrauch, keine Budget-Gefahr.
3. **P12.5 formal CLOSED — FAILED.** Steps 6 (Beweiswoche) und 7 (Handover-nach-PASS) aus
   dem ursprünglichen Plan entfallen ersatzlos — dieses Dokument **ist** der Abschluss, kein
   PASS-Handover. Keine weiteren P12.5-Bauschritte; erlaubt bleibt ausschließlich **Testen**
   (Regressionstests, ggf. ein gezielter Test für den in §2 beschriebenen Kostenpfad),
   **kein** neuer Fix-Commit unter diesem Label.
4. Der P12.5-Plandokument (`PHASE12_5_MEASUREMENT_ARM_PLAN.md`) bleibt **unverändert** als
   📕-Snapshot stehen (Konvention: superseden, nicht editieren) — dieses File ist die
   Supersession.

---

## §5 Empfehlung für das Danach (Vorschlag, nicht gebaut, nicht freigegeben)

Ziel: den Messarm wieder scharf schalten können, ohne das Wochenbudget zu sprengen. Drei
Bausteine, in Empfehlungsreihenfolge:

**1. Sofortmaßnahme, klein, isoliert (empfohlen als erster Schritt vor allem anderen):**
Den geteilten IG-Provider (`wiring.py:189`) korrekt taggen — Tracker-Top-up bekommt einen
eigenen `spend_kind` (z. B. `"tracker"`), getrennt von echtem `"research"`. Reine
Beobachtbarkeits-Korrektur, kein Verhalten geändert, macht aber jede künftige
Budget-Diagnose sofort eindeutig statt wie diesmal aus der Punktzahl-Verteilung rekonstruiert.

**2. Die eigentliche Struktur-Korrektur — Top-up auf die Lücke begrenzen, nicht das ganze
Fenster:** `BarService.get_window`s Top-up-Call (`service.py:212` und `:223`) soll bei einem
Coverage-Miss nur die **fehlende** Zeitspanne anfragen (typischerweise ein kleiner Tail, z. B.
letzte 30–60 Min), nicht erneut das komplette 300-Minuten-Fenster. Das drückt die Kosten pro
Top-up von ~301 auf eine zweistellige Punktzahl — bei ähnlicher Trefferquote. Das ist ein
echter Entwurfs-Eingriff (Chain-Provider ist count-basiert, nicht zeitraum-basiert; braucht
sauberes Nachdenken über Provider-Contracts), kein Ein-Zeilen-Fix — verdient eine eigene
kleine Design-Runde, nicht einen Schnellschuss mitten in einer Beweiswoche.

**3. Zusätzliche Bremse, falls 1+2 nicht reichen:** ein Once-per-Epic-per-Intervall-Throttle
auf den Tracker-eigenen IG-Top-up, nach dem exakten Muster von `DivergenceSampler`s
Einmal-pro-Tag-Drossel (`heartbeat.py`, `_last_sample_date`). Deckelt den Worst Case hart,
unabhängig davon, wie oft eine Epic knapp unter der Coverage-Schwelle bleibt — auf Kosten von
mehr `EXPIRED_UNRESOLVED`-Zeilen in Grenzfällen.

**Nicht empfohlen:** die `_MIN_WINDOW_COVERAGE`-Schwelle einfach absenken. Das verschiebt nur,
wann der teure Pfad greift — es verkleinert nicht, wie teuer er ist, wenn er greift (§6 des
alten Plans hatte diesen Zielkonflikt bereits vorhergesehen, nur die Größenordnung nicht).

**Nummerierung / Label des Danach** entscheidet der Nikinger — Vorschlag: kein neues P12.6,
sondern ein einzelner, klein geschnittener Fix-Block direkt in `phase12_data_foundation/`
(Baustein 1+2 zusammen sind überschaubar), bevor der Messarm ein zweites Mal scharf gestellt
wird.

---

## §6 Was unverändert offen bleibt

- Phase-12-Done-Kriterium (Plan §7, eine durchlaufende Beweiswoche) weiterhin **nicht
  erreicht** — nach diesem Scheitern weniger denn je.
- Requirement E (`resolution_source` real befüllt) ist inhaltlich bereits **teilweise
  gezeigt** (heutige 90 Zeilen), aber nicht über eine volle Woche.
- U4 (TickerMapper) und Entscheidung C (SUN*-Epics) bleiben wie in E9 draußen — unverändert.
- Kein Push nötig für dieses Dokument allein — folgt der üblichen bewussten Push-Freigabe.
