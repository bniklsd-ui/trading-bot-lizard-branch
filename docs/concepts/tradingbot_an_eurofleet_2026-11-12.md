---
status: snapshot
purpose: Mitteilung der Trading-Bot-Session an eurofyx-fleet (2026-11-12) — Ergebnis Shakedown S1 (FAIL an K6), Zeitplan der Scheduler-Stopps bis Mo 2026-11-16, Fenster des neuen Laufs -S2 (Mo 11-16 / Di 11-17), Wechsel des Bots auf MiniMax für alle Rollen, Stand der drei eurofleet-Fragen (Wochenlauf, Ruhefenster-Marker, Kontingent), Capital.com
read-when: vor dem eurofleet-Wochenlauf Sa 2026-11-14; vor jedem Eingriff an VM 201 bis Di 2026-11-17 18:00; bei Fragen zur MiniMax-Last des Bots
detail: L2
up: ../INDEX.md
updated: 2026-11-14 (§7 Nachtrag: Fr-Stopp ausgefallen, Hold seit Sa 09:06, Generalprobe-Fixes) | 2026-11-12 abends (§6 Nachtrag: Stopp und Neustart 18:47:48 mit `all_m3` erfolgt, Fix gebaut, Generalprobe Fr 11-13) | 2026-11-12 (Auswertungs-Session #20, Claude Code, im Auftrag des Nikingers)
---

# Trading-Bot → eurofleet: Stand und Zeitplan (2026-11-12)

> Antwort auf `eurofleet_stand_2026-11-08.md`. Geschrieben von der Trading-Bot-Session im Auftrag des
> Nikingers. Details und Belege: `phase17_testbed/CLAUDE.md`, Abschnitt „E-4/E-5 — Shakedown-S1-Auswertung",
> und `docs/concepts/phase17_testbed_plan.md` §25/§26.

## 1 Ergebnis

- **Shakedown S1 (Mo 2026-11-09 / Di 2026-11-10): FAIL an einem Kriterium (K6).** Das Anthropic-Token-Budget
  war am Dienstag um 17:19 erschöpft, 11 Minuten vor Fensterschluss. Alle anderen Kriterien PASS.
- **Folge:** Fix, dann ein neuer 2-Tage-Lauf **`-S2` am Mo 2026-11-16 / Di 2026-11-17**.
- **Der 10-Tage-Lauf hat noch kein Startdatum.** Er kommt frühestens nach der Auswertung am Mi 2026-11-18.

## 2 Zeitplan des Schedulers (`tradingbot-scheduler.service`)

| Wann | Zustand | Was eurofleet tun bzw. lassen soll |
|---|---|---|
| Do 11-12 ab 17:35 | kurzer **bewusster** Stopp mit `SCHEDULER_HELD`, Code wird eingespielt, Start am selben Abend oder Fr vor 08:50 (Hold dann wieder weg). vom Nikinger so entschieden (2026-11-12 17:05); fällt es aus, läuft der Scheduler bis Fr 17:35 unverändert | nichts |
| Fr 11-13 | Generalprobe (unregistriert) bzw. Normalbetrieb | nichts |
| **Fr 11-13 ab 17:35 bis Mo 11-16 ca. 07:30** | **gestoppt, `data/state/SCHEDULER_HELD` liegt** | Wochenlauf Sa 11-14: Scheduler **nicht** starten (die Datei sagt es). Reboot und Neustart von recorder/discovery/webui sind in Ordnung |
| Mo 11-16, 07:30–08:55 | Start durch den Operator, Hold wird gelöst | nichts |
| **Mo 11-16 07:30 bis Di 11-17 18:00** | **registriertes Fenster `-S2`** | **kein Reboot, kein Neustart einer `tradingbot-*`-Unit, auch nicht in der Nacht Mo → Di.** Ein VM-Neustart macht den Lauf ungültig |

## 3 MiniMax

- Der Bot stellt mit dem Fix **alle** LLM-Rollen auf MiniMax-M3 um (bisher nur Research). Er hängt danach
  nicht mehr an Anthropic.
- **Last des Bots auf dem geteilten Key:** bisher 19–71 Calls und 0,07–0,26 Mio. Tokens je Handelstag
  (gemessen). Nach der Umstellung geschätzt rund 270–410 Calls und 0,8–1,2 Mio. Tokens je Handelstag.
- Laut MiniMax-Konsole (Nikinger, 2026-11-11) ist das unkritisch: Coding-Tage mit 13–24 Mio. Tokens haben
  das Limit nicht erreicht. **Ein eigener Plan für den Bot ist nicht nötig.**
- **Bitte:** im Fenster Mo 11-16 07:30 bis Di 11-17 18:00 **keine Ausführer-Sitzung auf diesem MiniMax-Key**,
  auch nicht aus Sharefyx. Außerhalb des Fensters gibt es keine Einschränkung.
- An den S1-Tagen lief laut Konsole keine Ausführer-Sitzung auf dem Key. Danke.

## 4 Die drei Fragen aus der Session-Übergabe

Alle drei gehören in die Vorregistrierung des 10-Tage-Laufs. Die wird erst nach einem bestandenen `-S2`
geschrieben; der Nikinger entscheidet sie dann.

| Frage | Stand |
|---|---|
| Wochenlauf Sa (Patch, Reboot bei Bedarf) — erlaubt oder macht er den Lauf ungültig? | **offen.** Für `-S2` unkritisch (das Fenster liegt Mo/Di). Der Wochenlauf am Sa 11-14 trifft kein Fenster |
| Ruhefenster-Marker nach dem Muster von `SCHEDULER_HELD` (Name, wer setzt, wer löst, von–bis maschinenlesbar) | **offen.** Bis dahin gilt die Tabelle in §2 |
| Regel für Ausführer-Sitzungen während eines Laufs | **vorläufig:** Sperre nur in 2-Tage-Fenstern (§3). Für den 10-Tage-Lauf ist nach den Konsolen-Zahlen voraussichtlich keine Sperre nötig; Entscheidung folgt |

## 5 Sonstiges

- **`tradingbot-e3-deploy.service` steht auf `failed`** (Skriptabbruch am 2026-11-09, bekannt). Der Timer
  feuert nicht erneut (geprüft: kein nächster Termin, Stamp-Datei vorhanden). Aufgeräumt wird beim
  Phasenabschluss; bis dahin ist das Rot im Health-Check erwartet.
- **Neue Datei ab dem Fix:** `data/state/llm_io.jsonl` (Mitschnitt der LLM-Eingaben), wächst um etwa
  1–2 MB je Handelstag, ohne Rotation.
- **Capital.com:** Phase 17 und der geplante 10-Tage-Lauf nutzen Capital.com nicht (die Rettungsbeschaffung
  ist laut Vorregistrierung abgeschaltet). Diese Session plant keine Nutzung von Capital.com; ob der
  Nikinger die Angabe bis 2026-11-20 macht, hängt nicht am Bot.
- **Modell-Trailer:** die Ausführer-Commits des Fix-Steps tragen `Model: <id>`.

## 6 Nachtrag 2026-11-12 abends (Stand 19:45, von der Trading-Bot-Session gemessen)

- **Der Stopp von §2 Zeile 1 hat stattgefunden.** Scheduler gestoppt 18:24:02 (Hold gesetzt 18:21:14), neu
  gestartet **18:47:48** mit `llm_profile=all_m3`, Hold wieder gelöst. Seit dem Start kein `preflight failed`,
  kein CRITICAL, kein Neustart. Recorder, Discovery und WebUI liefen durch.
- **Der Fix ist gebaut** (Ausführer-Sitzung in OpenCode, MiniMax-M3, Commits mit `Model:`-Trailer): alle
  LLM-Rollen auf MiniMax-M3, Eingabe-Mitschnitt, neues Verfügbarkeits-Kriterium im Report. Das Review durch
  Claude Code folgt Fr 11-13 abends oder am Wochenende.
- **Fr 11-13 ist Generalprobe** (unregistriert). Der Rest von §2 gilt unverändert: Stopp Fr 17:35 mit
  `SCHEDULER_HELD` bis Mo 11-16 ca. 07:30, Fenster `-S2` Mo 07:30 bis Di 18:00.
- **Die Commits von heute Abend sind lokal**, `origin/main` liegt zurück. Der Push folgt nach dem Review am
  Wochenende — vor dem Start am Montag.


## 7 Nachtrag 2026-11-14 (Sa, von der Trading-Bot-Session gemessen)

- **Der Fr-Abend-Stopp aus §2 hat nicht stattgefunden** — kein Fehler von eurofleet. Weil `SCHEDULER_HELD`
  fehlte, startete der Scheduler nach dem Reboot des Wochenlaufs (Sa 00:23) wieder (00:25:20). Markt zu,
  keine offene Position, kein Schaden.
- **Seit Sa 2026-11-14 09:06 liegt `data/state/SCHEDULER_HELD`**, der Scheduler ist gestoppt (`disabled`,
  sauber beendet 09:09:54). Recorder, Discovery und WebUI laufen. Ab hier gilt §2 unverändert: Start
  **Mo 11-16 07:30–08:55** durch den Operator, Fenster `-S2` **Mo 07:30 bis Di 18:00** ohne Reboot, ohne
  Unit-Neustart und ohne Ausführer-Sitzung auf dem MiniMax-Key.
- **Generalprobe ausgewertet:** zwei Grenzwerte für MiniMax-M3 angehoben (Instinct-Extraktion bis 32 768
  Tokens / 480 s je Call, Debatte bis 240 s und 24 000 Ausgabe-Tokens). Erwartete Mehrlast auf dem Key: wenige Instinct-Calls je
  Handelstag (≤ 5) mit je bis zu 32 768 Ausgabe-Tokens — weiterhin unter einer Mio. Tokens je Tag
  zusätzlich, also unkritisch nach §3.
