---
status: live
purpose: Wiederverwendbarer Auftragstext, mit dem der Nikinger eine Phase abschließt oder zurückstellt und Claude Code das Handover schreiben lässt. Ersetzt die frühere, für den Browser-Chat gebaute Fassung (Google-Drive-Upload, Drive-Analyse) — Claude Code liest das Repo direkt.
read-when: beim Abschluss oder Deferral einer Phase, vor dem Kopieren des Prompts
detail: L2
up: ./INDEX.md
updated: 2026-08-11
---

# Handover-Prompt (Claude Code)

> **Was sich geändert hat und warum** (2026-08-11, Nikinger-Entscheidung): Handovers wurden
> bisher im Browser-Chat geschrieben, der den Projektstand über Google Drive gespiegelt bekam.
> Claude Code liest Code, Tests, Git-Historie und Live-DB direkt — die Drive-Kopie war eine
> zweite Wahrheit, die veralten konnte. Die Drive-Schritte entfallen deshalb ersatzlos; das
> Handover-Vertrag selbst („Status + Delta + offene Entscheidungen + Datei-Pfade") bleibt
> unverändert, er war nie das Problem.

## Benutzung

Blocktext unten kopieren, `X` durch die Phasennummer ersetzen, die Ergebniszeilen auf
**zutreffend/nicht zutreffend** trimmen (ein Deferral hakt nicht dieselben Zeilen ab wie ein
Abschluss), und unter **Besondere Notiz** das eintragen, was nur diese Phase betrifft. Der Rest
ist bewusst stabil, damit Handovers untereinander vergleichbar bleiben.

---

```
Guten Tag Claude! Phase X ist abgeschlossen / wird zurückgestellt (Zutreffendes behalten).

Ergebnisse (nur eintragen, was wirklich zutrifft — eine ehrliche Teilbilanz ist mehr wert
als eine vollständige Häkchenliste):
- fertig gestellt:
- getestet:
- im Rahmen der Möglichkeiten live validiert:
- gepusht und committet:
- nicht erreicht / offen geblieben:

Hinweise/Rahmen:
- Quelle der Wahrheit ist das Repo: Code, Tests, Git-Historie, und für Laufzeitfragen die
  Live-DB read-only (mode=ro). Wo ein .md-Dokument dem Code widerspricht, gewinnt der Code —
  korrigiere das Dokument im selben Zug und vermerke die Korrektur datiert.
- Aktualisiere nicht nur Notizen, sondern auch deine direkten Erinnerungen (Memory).
- Prüfe den Stand selbst nach, statt ihn aus früheren Handovers zu übernehmen: git log,
  Testzahlen je Phase (getrennt laufen lassen), und bei Bedarf die DB.
- Live-, Netz- und kostenpflichtige Aufrufe macht der Nikinger. Du bereitest den Befehl vor
  und fragst.

Auftrag:
1. Aufmerksame Analyse der beendeten/zurückgestellten Phase gegen den As-Built-Zustand.
   Nenne ausdrücklich, was NICHT erreicht wurde und was nur offline bewiesen ist.
2. SVG-Grafik, 1080x1080 (groß genug, dass der Text passt), nach docs/architecture/.
   Sie soll die Phase grafisch darstellen und grob erklären — bei einem Deferral: Fehlerbild
   und Zielbild.
3. Handover-File als .md: was die nächste Session wissen muss, BEVOR sie einen detaillierten
   Plan entwirft. Führe die bereits verwendeten Benennungen fort (PHASE<N>_<ART>_HANDOVER.md)
   und beachte, was frühere Dokumente ausdrücklich als handover-würdig markiert haben.
4. Statuspflege im selben Commit: Root-CLAUDE.md, ROADMAP.md, docs/INDEX.md, der Phasenkopf,
   plus neuer `## Session stopped`-Block mit Rotation des vorigen nach SESSIONS_ARCHIVE.md.

Zum Handover an sich:
Handover = Status + Delta seit letztem Handover + offene Entscheidungen + Datei-Pfade als
Verweise. Keine Implementierungsdetails erneut ausschreiben, die schon in Code, Tests oder
Plan-Docs stehen — Code ist Wahrheit, nicht der Handover-Text. Ziel: die nächste Session
braucht minimalen Kontext, keine zweite Kopie des Plans.

Offene Entscheidungen gehören als Entscheidungen formuliert (Optionen + Empfehlung + was
jeweils daraus folgt), nicht als Fragen ins Leere. Entscheide nichts eigenmächtig, was
projektweit sichtbar ist (z. B. Nummerierung).

Besondere Notiz:
xxx
```

---

## Warum die drei entfallenen Punkte entfallen sind

| Früher | Warum weg |
|---|---|
| „aktuellen Stand auf GDrive hoch geladen" | Claude Code liest das Repo. Eine gespiegelte Kopie ist eine zweite Wahrheit mit eigenem Verfallsdatum. |
| „Analyse via Google Drive" | ersetzt durch Analyse gegen den As-Built-Code — dieselbe Regel, die im Projekt ohnehin gilt. |
| „Phase X+15 Chat" | Adressat ist jetzt die nächste Claude-Code-Session, nicht ein späterer Browser-Chat. |

## Was bewusst dazugekommen ist

- **„nicht erreicht / offen geblieben"** als eigene Ergebniszeile. Die alte Fassung listete nur
  Erfolge; ein Deferral hat aber genau die andere Sorte Inhalt, und die ist für die nächste
  Session die wichtigere.
- **„was nur offline bewiesen ist"**. Grüne Tests sind kein Live-Beweis — diese Unterscheidung
  ist im Projekt schon einmal teuer geworden.
- **Selbst nachprüfen statt übernehmen.** Handovers haben im Projekt bereits veraltete
  Testzahlen und Statuszeilen weitergereicht.
- **Entscheidungen mit Empfehlung**, statt offener Fragen — und das ausdrückliche Verbot,
  projektweit sichtbare Dinge eigenmächtig zu entscheiden.
