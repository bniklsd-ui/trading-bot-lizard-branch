# Meta-Phase — Harness- & Laufzeit-Modell-Unabhängigkeit: Hypothese & Entscheidungs-Experiment

> **Status:** Vorschlag, **nicht gelockt**. Dies ist ein **Hypothesen-/Theorie-Dokument**,
> kein Implementierungsplan. Es definiert *eine* falsifizierbare Frage und das Experiment,
> das sie beantwortet — sonst nichts. Ergebnis der Meta-Phase ist eine **Entscheidung**
> (migrieren / nicht migrieren / teil-migrieren), keine gebaute Funktion.
>
> **Bauprinzip:** Diese Meta-Phase baut **kein** Bot-Feature. Sie ist eine Methoden-
> Entscheidung über das *Womit* (Build-Werkzeug) und das *Woraufhin* (Laufzeit-Modelle) —
> nicht über das *Was*. Sie steht **orthogonal** zum funktionalen Strang (Phase 1–9) und
> darf profit-erzeugende Arbeit nur verdrängen, wenn das Risiko real und die Kosten der
> Migration gemessen sind.
>
> **Quelle der Wahrheit bleibt das Repo — und die Messung.** *Keine Migration ohne Zahl.*
> Jede mit **[VERIFY]** markierte Stelle ist vor dem Bauen zu prüfen.
>
> **Einordnung [VERIFY]:** Exakter Einschubpunkt offen — es wurden sowohl
> „zwischen Phase 2 und 3" als auch „Phase 9 v2 im Live-Test" genannt. Da diese Meta-Phase
> orthogonal ist, ist sie kein echter Zwischenschritt der funktionalen Roadmap; Platzierung
> (eigener Strang / Einschub) vom Plan-Chat festzulegen.

---

## 0. Warum diese Meta-Phase existiert (Motivation, projektverankert)

Der Bot hat eine **kleine, bereits isolierte AI-Oberfläche**. Deterministischer Code
(Phase 1, 2, 3, 5, 7, 8) enthält laut Bauprinzip **keinen einzigen LLM-Call**. AI existiert
an genau zwei Stellen:

- **Phase 4 — Research** (der eine Research-Call, über Gate 2 ausgelöst), heute an
  `anthropic_api_key` gebunden.
- **Phase 6 — Bull/Bear/Judge** (Debatte, überschreibt Richtung), ebenfalls Anthropic.

„Wir benutzen Claude" vermischt **zwei völlig verschiedene Abhängigkeiten**. Sie brauchen
verschiedene Gegenmittel und haben verschiedene Dringlichkeit; sie sauber zu trennen ist der
eigentliche Wert dieses Dokuments:

- **Build-Front** = *womit der Bot-Code geschrieben wird* — das Coding-Harness, aktuell
  Claude Code. Betrifft die **Entwicklung**, nicht den laufenden Bot.
- **Laufzeit-Front** = *worauf der laufende Bot angewiesen ist* — die Modell-Calls in
  P4/P6. Betrifft den **Live-Betrieb** (echtes Geld).

| Front | Was hängt an Anthropic | Was ein Ausfall/Bann bricht | Dringlichkeit |
|---|---|---|---|
| **Build** (womit gebaut wird) | Claude Code als Coding-Harness | die **Entwicklung** (nächste Module), nicht den Live-Betrieb | Mittel (Umgehung existiert) — **aber billig & risikoarm zu testen**, daher zuerst (§3-A) |
| **Laufzeit** (womit gelaufen wird) | P4-Research + P6-Debatte (API-Calls *im* Bot) | den **Live-Bot** — kein Research → `save_candidates([])` → kein Trade | **Hoch** (trifft echtes Geld) — aber teurer & riskanter zu prüfen, daher später (§3-A) |

**Fokus dieser Meta-Phase — konkret und eng:** Getestet wird **ausschließlich die
Build-Front** — also die einzige Frage: *Kann ich den Bot-Code künftig mit einem anderen
Coding-Harness (OpenCode oder Aider) statt mit Claude Code schreiben, bei identischem
Modell, ohne spürbaren Zuverlässigkeitsverlust?* Die Laufzeit-Front (P4/P6-Modelltausch)
wird hier nur **begrifflich abgegrenzt** und bewusst auf einen späteren, eigenen Schritt
vertagt (§3-A). Der scheinbare Widerspruch — niedrigere Dringlichkeit, aber zuerst dran —
ist Absicht: die Build-Front ist an einem Wegwerf-Fork **gefahrlos und billig** messbar,
die Laufzeit-Front nicht.

**Präzedenz, dass das Risiko nicht theoretisch ist:** Claude Fable 5 wurde am 2026-06-12
per Export-Kontrolle suspendiert (später wieder verfügbar). Ein Modell *kann* über Nacht
verschwinden. Der Live-Bot darf davon nicht abhängen.

**Günstiger Ausgangsbefund (verankert):** Die Architektur ist bereits
unabhängigkeits-freundlich. Phase 4 fährt einen **unabhängigen Validator „immer aktiv"**
um den LLM-Output, plus den deterministischen `candidate_filter`; Gating trägt der Code,
nicht das Modell (Entscheidung: LLM-Confidence ist epistemisch schwach, ECE ~0,1,
systematisch overconfident → als Feld speichern, nicht als Gate nutzen). **Genau dieser
Validator ist das Sicherungsnetz, das einen Modell-Tausch überhaupt erst gefahrlos macht.**
Die Unabhängigkeit ist also weniger „neu bauen" als „bereits vorhandene Naht nutzen".

---

## 1. Hypothese (falsifizierbar)

Zwei getrennte Behauptungen, getrennt zu prüfen:

- **H_Build:** Für sequentielle Schritt-Ausführung gegen einen detaillierten Plan erreicht
  ein offener Harness (OpenCode oder Aider) + **festes Modell** eine Task-Completion- und
  Edit-Zuverlässigkeit **innerhalb einer vorab definierten Toleranz Δ** von
  Claude Code + demselben Modell.
  - **H0_Build (Null):** Der Abstand ist > Δ (der offene Harness ist auf *meinem* Repo
    spürbar schlechter). → Nicht migrieren; Claude Code bleiben, kalter Fallback genügt.

- **H_Runtime:** Die P4/P6-AI-Calls laufen gegen ein **Nicht-Anthropic-Modell**
  (gehostetes Open-Weight) ohne die **deterministischen Gate-Ergebnisse** unter eine
  vorab definierte Schwelle zu drücken.
  - **H0_Runtime (Null):** Ein Modelltausch verändert die Gate-/VETO-Pfade oder die
    Kandidaten-Qualität messbar zum Schlechteren. → Anthropic für P4/P6 halten,
    Fallback nur getestet-kalt.

**Explizit als unbewiesen markiert (keine Prämisse!):** Äquivalenzen der Form
„Opus xHigh ≈ Fable Medium" bzw. „Open-Weight-Planer ≈ Opus-Planer" sind **Annahmen**,
nicht Ausgangspunkte. Sie werden gemessen, nicht geglaubt — dieselbe Haltung wie bei der
Confidence-Entscheidung in Phase 4.

---

## 2. Was diese Meta-Phase ist / nicht ist

**Ist:**
- Eine vorregistrierte, falsifizierbare Messung: „Was kostet mich Unabhängigkeit *auf
  meinem* Code — und wie wahrscheinlich/teuer ist der Ausfall, gegen den sie versichert?"
- Eine saubere Trennung von **Build-** und **Laufzeit-**Unabhängigkeit.
- Die Festlegung des **portablen Assets**: nicht das Modell, sondern (a) ein
  provider-agnostischer Seam um P4/P6 und (b) ein Harness-neutrales Kontext-Format
  (`AGENTS.md` + referenzierte Dateien), das die `.claude`-Inhalte ablöst.

**Ist nicht:**
- Keine vorschnelle Migration. Kein Umbau von P4/P6 „auf Verdacht".
- Keine dauerhafte Herabstufung eines Modells (z. B. Planer auf Open-Weight) *bevor*
  gemessen ist, dass die Qualität trägt.
- Kein Feature, kein Scoring, kein neuer Trade-Pfad.
- Keine Änderung an laufender Live-Infrastruktur (Phase-9-v2-Live-Test bleibt unberührt).

---

## 3. Entscheidungen — gelockt vs. offen

| # | Thema | Festlegung / Status |
|---|---|---|
| **A** | Reihenfolge der Fronten | **Build zuerst messen** (billig, risikoarm, throwaway-Fork). Laufzeit (P4/P6-Swap) ist höherwertiger *und* riskanter (Modellqualität auf realen Kandidaten unbewiesen) → **eigener, späterer Schritt**, nicht in denselben Topf. **Gelockt.** |
| **B** | Portables Asset | Unabhängigkeit kommt vom **Harness-neutralen Seam + `AGENTS.md`-Kontext**, nicht vom Modelltausch. Ein Bann wird dann eine Config-Zeile, kein Rewrite. **Gelockt.** |
| **C** | Messung vor Migration | Kein Wechsel ohne Zahl aus dem Experiment (§4). **Gelockt.** |
| **D** | Modell fixiert im Build-Test | Im Harness-Vergleich ist das **Modell identisch** (gleiches Sonnet 5 / Opus, gleicher Effort, gleiche Temperatur). Sonst misst der Test nichts. **Gelockt.** |
| **E** | `.claude` → `AGENTS.md` | OpenCode liest `CLAUDE.md`/`~/.claude/` nativ als Fallback; Kontext portiert also fast ohne Arbeit. **Frontmatter-Link-Graph wird NICHT automatisch geparst** — die „lies `@ref` on need-to-know"-Disziplin muss als **explizite Anweisung** mitgenommen und pro Executor-Modell **nachgetestet** werden. **Gelockt als Erkenntnis, Umsetzung offen.** |
| **F** | Δ (Build-Toleranz) | **[OFFEN — vor dem Experiment zu setzen]** Maximaler Gate-Pass-Abstand, den ich zu akzeptieren bereit bin, um Unabhängigkeit zu kaufen. |
| **G** | X (Bedrohungswert) | **[OFFEN — vor dem Experiment zu setzen]** Erwartungswert der Ausfallkosten (P(Anthropic für mich unbrauchbar in 12 Mon.) × Kosten eines ~2-Wochen-Ausfalls). |
| **H** | P4/P6-Swap-Scope | **[OFFEN]** Ob der Laufzeit-Swap Teil *dieser* Meta-Phase oder einer späteren ist — abhängig von A und den Ergebnissen. |

---

## 4. Das Experiment — „Winner-Finding"-Step (vorregistriert)

> **Anti-Pattern-Warnung (analog Phase 4):** Das Anpassen von Δ oder X **nach** Sicht der
> Ergebnisse ist „nach einem migrationsfreundlichen Ergebnis shoppen". **Verboten.** Δ und X
> stehen schriftlich, **bevor** die erste Zahl existiert.

**Instrument:** Harness-Bake-off (fixes Modell, beide Harnesse als Black-Box über ihre CLI).
Referenz-Skript vorhanden (`harness_bakeoff.py`) — dient als Beispiel/Instrument, ist aber
ersetzbar.

**Aufbau:**
- **N ≥ 5** echte Schritt-Specs (aus dem nächsten, isolierten Modul-Plan).
- **≥ 2 Wiederholungen** je (Harness × Step). Varianz wird berichtet, nicht versteckt.
- **Fork** mit eigener Git-History; **kein geteilter Schreibpfad** zu irgendetwas, das der
  Live-Test (Phase 9 v2) liest/schreibt. **Wegwerf-/Paper-Credentials**, nie Live-Keys.
  Zwischen jedem Trial: `git reset --hard` + `clean` (ein Fehlgriff darf den nächsten
  Trial nicht vergiften).

**Metriken (objektiv, geloggt — keine Eindrücke):**
- `gate_pass_rate` — hat der Schritt-Gate nach dem Lauf bestanden (Exit 0)?
- `edit_failures` — behauptete/nötige Änderungen, die nicht auf Platte landeten.
- `turns_to_completion`, `wall_seconds`, `token_spend`.

**Vorregistrierte Entscheidungsregel:**
- **Migrieren nur wenn** (a) gemessener `gate_pass`-Abstand **≤ Δ** **UND** (b) Bedrohungs-
  Erwartungswert **≥ X**.
- Sonst: **Claude Code bleiben**, `AGENTS.md`-Kontext + provider-agnostischer Seam
  **getestet, aber kalt** vorhalten, Wechsel nur wenn erzwungen. (≈ 90 % der Versicherung,
  ~0 % tägliche Reibung.)

**Threats to Validity (aktiv kontrolliert):**
- *Modell-Drift* → Modell fixiert (Decision D).
- *N=1-Rauschen* → Wiederholungen; wenn Innerhalb-Varianz > Zwischen-Harness-Abstand,
  ist der „Sieger" Rauschen.
- *Harness-Config-Schiefe* → gleicher Effort/Temp/Toolset.
- *Confirmation-Shopping* → Δ/X vorregistriert (s. o.).
- *Frontmatter-Verhalten portiert nicht automatisch* → als eigener Kontrollpunkt pro
  Executor-Modell prüfen (Decision E).

---

## 5. Risiken & Konflikte mit Projektzielen

- **Live-Blast-Radius (hart):** Der Fork darf State/DB/Credentials des Phase-9-v2-Live-Tests
  **nicht** berühren. Ein Bake-off-Executor, der einen Stray-Command absetzt, muss den
  Live-Pfad nicht erreichen können. Isolierter Fork + Paper-Keys, nicht verhandelbar.
- **Opportunity-Cost:** Dies ist Methodik, kein Return. Rechtfertigt sich nur, wenn X
  (§3-G) nicht-trivial ist. Ist X klein, ist das korrekte Ergebnis „kalter Fallback,
  keine Migration" — und die Meta-Phase endet nach der Zahl, nicht nach einem Umbau.
- **Reihenfolge-Risiko:** Laufzeit-Unabhängigkeit (P4/P6) ist wichtiger *und* unsicherer
  (Open-Weight-Research-/Debatten-Qualität auf realen DAX-Kandidaten unbewiesen). Nicht mit
  dem billigen Build-Test vermengen (Decision A).
- **Stilles Kontext-Leck:** Wissen, das nur im Web-Memory lebte und nie in eine Projekt-
  datei geschrieben wurde, portiert nicht. Vor Migration auf implizite Abhängigkeiten
  auditieren.

---

## 6. Offene Fragen / [VERIFY]

1. **[VERIFY]** Einschubpunkt/Strang in der Roadmap (orthogonal — vermutlich eigener Strang).
2. **[SET]** Δ (Build-Toleranz) und X (Bedrohungs-Erwartungswert) — **vor** dem Experiment.
3. **[DECIDE]** P4/P6-Laufzeit-Swap in dieser Meta-Phase oder später (hängt an A + Ergebnis).
4. **[VERIFY]** Aktuelle CLI-Syntax der Harnesse (Flags ändern sich zwischen Versionen) —
   vor dem Bake-off gegen `--help` prüfen; falsche `argv` misst nichts.
5. **[DECIDE]** Planer-Modell: Opus behalten (billig, low-volume, human-in-loop) + getesteter
   Open-Weight-Fallback — vs. präventiver Flip auf Open-Weight-Planer. Default-Empfehlung:
   **behalten + Fallback**, Flip nur bei bewusster Souveränitäts-/Lern-Absicht.

---

> **Definition of Done dieser Meta-Phase:** Eine Zahl (Δ-Vergleich), eine dokumentierte
> Ja/Nein-Migrationsentscheidung nach vorregistrierter Regel, und — unabhängig vom
> Ausgang — ein getesteter, kalter provider-agnostischer Fallback für P4/P6. **Kein**
> Umbau der Live-Pfade als Teil dieser Phase.
