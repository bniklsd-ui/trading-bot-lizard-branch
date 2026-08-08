---
status: snapshot
purpose: Scoping für H4 (Lesson-Feedback-Loop) aus DATA_WEEK_REVIEW_2026-07-31 §5, gegen den As-Built-Code verankert. Kernbefund: die vier einzigen Lessons stammen aus den vier einzigen Trades — alle BUY, alle Verluste — und werden dem Modell über ZWEI Prompt-Kanäle gleichzeitig serviert, inzwischen 5.973-mal. Das `relevance_score`-Feld für den Decay existiert bereits und wird nirgends gelesen. Enthält drei Kandidaten mit Aufwand/Wirkung und eine Empfehlung; KEIN Code geändert.
read-when: vor dem Bau von H4, oder bei der Frage warum der Research-Funnel drei Wochen in Folge 0 Kandidaten liefert
detail: L3
up: ./CLAUDE.md
updated: 2026-08-08
---

# H4 — Lesson-Feedback-Loop: Scoping (2026-08-08, Sa, docs-only)

> **BLUF:** Die Erfahrungsbasis des Modells besteht aus **vier** Trades. Alle vier sind
> `BUY` auf DAX, alle vier Verluste (−585 € bis −651 €). Aus genau diesen vier Trades wurden
> genau vier Lessons destilliert. Beide Blöcke — `recent_trades` **und** `Active lessons` —
> stehen in **jedem** Research-Prompt. Das Modell sieht dieselben vier Verluste zweimal,
> ~73-mal am Tag. Die Zähler sagen: **5 973 Lesson-Renderings aus 4 Datenpunkten.**
>
> Das ist keine Hypothese mehr. Es ist der wahrscheinlichste einzelne Grund, warum der
> Funnel drei Wochen in Folge 0 Kandidaten liefert.
>
> **Diese Session ändert keinen Code.** Freigabe zum Scopen kam vom Nikinger; der Bau ist
> ein eigener Schritt und berührt `phase4_research/` + `phase2_persistence/`.

## 1. Faktenlage (live gemessen, `mode=ro`, 2026-08-08)

`trade_outcomes` — die komplette Handelshistorie des Bots:

| id | epic | direction | status | profit_loss |
|---|---|---|---|---|
| 7 | IX.D.DAX.IGN.IP | BUY | CLOSED | −643,50 € |
| 6 | IX.D.DAX.IGN.IP | BUY | CLOSED | −651,16 € |
| 5 | IX.D.DAX.IFMM.IP | BUY | CLOSED | −651,16 € |
| 4 | IX.D.DAX.IFMM.IP | BUY | CLOSED | −585,00 € |

`trade_lessons` — 1:1 dieselben vier Trades (`trade_id` 4–7):

| id | trade_id | extracted_at | relevance_score | used_in_research |
|---|---|---|---|---|
| 7 | 7 | 2026-07-20 | 1.0 | **1 023** |
| 6 | 6 | 2026-07-10 | 1.0 | **1 419** |
| 5 | 5 | 2026-07-03 | 1.0 | **1 756** |
| 4 | 4 | 2026-07-03 | 1.0 | **1 775** |
| | | | | **Σ 5 973** |

Der Inhalt aller vier ist derselbe Satz in vier Formulierungen: *„Der geplante Stop wurde
korrekt getroffen, was auf sauberes Risikomanagement hindeutet…"*. Keine Richtung, kein
Instrument, kein Drift-Level, keine Tageszeit. Das ist exakt die Kategorie, die
`DATA_WEEK_REVIEW_2026-07-31.md` §5 benannt hat: **kann nur dämpfen, nie korrigieren.**

Der älteste dieser Sätze ist heute **36 Tage** alt und wird weiterhin in jeden Prompt
gerendert.

## 2. Anker gegen den As-Built-Code

| Stelle | Datei | Was tatsächlich dasteht |
|---|---|---|
| Rendering | `phase4_research/research/prompt.py:135-142` `_render_lessons` | Rendert **immer**, ungefiltert. Leere Liste → `"Active lessons: none on record."` |
| Speisung | `phase4_research/research/context_builder.py:262-267` | `db.get_recent_lessons_for_prompt(5, min_hold_min=…, quarantine_before=…, exclude_provenance=…)` |
| Zweiter Kanal | `context_builder.py` (unmittelbar davor) | `db.get_recent_trades_for_prompt(…)` — dieselben vier Trades |
| Query | `phase2_persistence/persistence/db.py:294-…` | Bereits **parameterisiert** mit Caller-seitiger Policy; Filter laufen **in** der Query |
| Zähler-Update | `db.py:352-355` `mark_lesson_used` | Inkrementiert `used_in_research`, stempelt `last_used_ts` |

**Der wichtigste Anker — das Decay-Feld existiert schon und ist tot:**
`relevance_score` wird an **genau einer** Stelle geschrieben
(`phase7_reward/reward/recorder.py:394`, als Konstante `_DEFAULT_RELEVANCE = 1.0`) und von
**keiner** Query gelesen. `used_in_research`/`last_used_ts` werden gepflegt und nur im
Web-UI angezeigt (`phase8_scheduler/webui/api.py:244`), nie zum Filtern benutzt.

**Konsequenz: Kandidat 1 braucht keine Migration.** Die Spalte ist da, das Filtermuster ist
da, es fehlt eine Policy und eine `WHERE`-Klausel.

## 3. Die drei Kandidaten

### H4-a — Alters-Cap / Relevanz-Decay  ★ empfohlen zuerst

**Problem:** 4 Datenpunkte aus ~5 Wochen dominieren dauerhaft 100 % der Entscheidungen.

**Kleinster Eingriff:** ein `max_age_days`-Parameter an `get_recent_lessons_for_prompt`,
plus der zugehörige Config-Key in Phase 4 — exakt das Muster, das `min_hold_min` /
`quarantine_before` / `exclude_provenance` dort schon etabliert haben. Filter in der Query,
Policy beim Caller, Phase 2 bleibt der dumme parameterisierte Store.

**Ausdrücklich verworfen:** `quarantine_before` dafür zweckentfremden (Caller rechnet
`heute − N Tage`). Spart eine Zeile und überlädt einen Knopf mit zwei Policies — die
einmalige, reversible Quarantäne und den laufenden Decay. Beim nächsten Debugging kostet
das mehr, als es heute spart.

**Nebenwirkung, die vorher entschieden gehört:** mit einem 30-Tage-Cap fallen **drei der
vier** Lessons sofort weg; mit 14 Tagen **alle vier**, und `_render_lessons` gibt
`"none on record"` aus. Das ist ein **echter Verhaltenswechsel für die einzige
AI-Entscheidung des Systems** und keine Nebensache — Nikinger-Entscheidung, kein
Implementierungsdetail.

### H4-b — Doppelzählung beenden

**Problem:** dieselben vier Verluste in zwei Blöcken desselben Prompts. `recent_trades`
liefert die Rohdaten (Epic, Richtung, P&L), `Active lessons` die Prosa-Destillation
derselben Zeilen. Einer der beiden Kanäle genügt.

**Aufwand:** eine Zeile in `context_builder.py` (einen Block nicht mehr befüllen) plus die
Prompt-Erwartung nachziehen.

**Welcher fliegt?** Fachlich klar: **die Lessons**, nicht `recent_trades`. Die Rohzeilen
tragen Richtung, Instrument und Betrag; die Prosa trägt heute nichts, was die Rohzeile nicht
schon sagt. Kollidiert allerdings frontal mit H4-c (Lessons *besser* machen statt entfernen).
→ H4-b und H4-c sind **Alternativen, keine Ergänzungen.** Die Reihenfolge in §4 löst das auf.

### H4-c — Lessons skopieren

**Problem:** freie Prosa ohne Richtung/Instrument. Verwertbar wäre *„BUY auf DAX nach +2,3 %
Drift lief schlecht"*; nicht verwertbar ist *„prüfe die Entry-Qualität"*.

**Aufwand:** deutlich größer als a und b — der Lesson-Prompt in `phase7_reward/reward/brain.py`
müsste strukturierte Felder verlangen, das Schema müsste sie tragen, das Rendering müsste sie
zeigen. Berührt Phase 7 **und** Phase 4 **und** Phase 2.

**Und der Kern des Problems bleibt:** mit vier Datenpunkten wäre auch eine perfekt
strukturierte Lesson noch *„BUY auf DAX lief 4/4-mal schlecht"*. H4-c erhöht die Qualität
pro Datenpunkt, nicht die Zahl der Datenpunkte. **Der Engpass ist die Stichprobe, nicht das
Format.**

### Unverändert: S6 bleibt AUS

Die Rückspeisung von Abstain-/Paper-Lessons in den Research-Prompt bleibt abgeschaltet
(`DATA_WEEK_REVIEW_2026-07-31.md` §5). Die vorhandenen Paper-Lessons sind tautologisch, auf
beiden Seiten desselben Paares wortgleich und aus Backfill-Artefakten abgeleitet. Sie jetzt
zuzuschalten würde die Rückkopplung verstärken. **Diese Session ändert daran nichts.**

## 4. Empfehlung

**H4-a zuerst, allein, und dann messen.**

Begründung: es ist der einzige Kandidat, der (i) keine Migration braucht, (ii) das
vorhandene Filtermuster exakt wiederverwendet, (iii) auf **eine** Phase begrenzt bleibt und
(iv) ein sauberes Vorher/Nachher liefert — die Abstain-Rate mit und ohne Lessons im Prompt,
bei ansonsten unverändertem System.

H4-b **danach** entscheiden, nicht gleichzeitig: fällt mit einem Alters-Cap ohnehin alles
weg, ist die Doppelzählung faktisch aufgelöst und H4-b wird gegenstandslos. Zwei Hebel
gleichzeitig ziehen macht das Ergebnis unlesbar — dasselbe Muster, das bei H1 schon
Messwochen gekostet hat.

H4-c erst, wenn wieder Trades entstehen. Vorher optimiert es das Format einer Stichprobe
der Größe 4.

## 5. Was H4 nicht ist

Der Ehrlichkeit halber, gegen Übererwartung: H4 entfernt einen **Dämpfer**, es fügt kein
Signal hinzu. Wenn der Funnel nach einem Alters-Cap immer noch 0 Kandidaten liefert, liegt
die Ursache nicht bei den Lessons und die drei Wochen Verdacht sind sauber ausgeschlossen —
was für sich schon ein Ergebnis ist. Das ist die Kategorie, in die H4 gehört: eine
Hypothese, die **billig falsifizierbar** ist, nicht eine, von der ein Ertrag erwartet wird.

Der Unterschied zu H7 (Richtungslogik) bleibt bestehen und ist der Grund, warum H4 nicht auf
eine saubere H1-Woche warten muss: H4 dreht nicht an der Entscheidungslogik, es entfernt eine
Unterdrückung der **Stichprobenerzeugung selbst**. Die ursprüngliche Sequenzierung hat das
vermengt.
