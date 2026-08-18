---
status: live
purpose: PHASE-HEAD, Phase 12 (Datenfundament) — Registry + BarService + Bar-Archiv + Recorder + Heartbeat. Steps 0-8.5 gebaut, getestet und auf main committed. P12.5 (Messarm-Fixes, 2026-08-17/18): Steps 1-3 gebaut + live verifiziert (U1/U2/U3/U5 + Entscheidung B, alle korrekt) — ABER P12.5 formal CLOSED, GESCHEITERT (2026-08-18, Nikinger-Intervention): BarService.get_window's Vollfenster-Refetch verbrannte 4731/10000 IG-Wochenpunkte am ersten scharfen Handelstag. Scheduler gestoppt, kein weiterer Verbrauch. Die fünf Code-Fixes bleiben gültig; keine weiteren P12.5-Bauschritte, nur Tests. Step 9 (Beweiswoche) weiterhin nicht begonnen.
read-when: working in phase12_data_foundation/ — read PHASE12_5_FAILURE_HANDOVER.md first (Root Cause, Zahlen, was bleibt gültig, Empfehlung fürs Danach), dann diesen Kopf + den newest Session-stopped block; PHASE12_5_MEASUREMENT_ARM_PLAN.md ist superseded (unverändert, nicht editiert); der Mutterplan (docs/concepts/phase12_data_foundation_plan.md) bleibt der §7-PASS-Kriterien-Ausführungsvertrag
detail: L2
up: ../CLAUDE.md
down:
  - ./PHASE12_5_FAILURE_HANDOVER.md                     # P12.5 CLOSED/FAILED: Root Cause, Zahlen, Empfehlung (L3, dated) — READ FIRST
  - ./PHASE12_5_MEASUREMENT_ARM_PLAN.md                 # superseded Bauauftrag: E1-E9, Steps 1-7 (L3, nicht editiert)
  - ./PHASE12_PREPROOF_HANDOVER.md                      # Befundlage vor P12.5, Tag-1-Ergebnisse (L3, dated)
  - ../docs/concepts/phase12_data_foundation_plan.md   # full execution-ready plan, D1-D20, Steps 0-10, §7 PASS-Kriterien (L3)
  - ../phase10_v3/PHASE11_DEFERRAL_HANDOVER.md          # why this track exists (L3, dated)
  - ../docs/architecture/phase12_preproof.svg · data_foundation.svg  # Tag-1-/Fehlerbild
  - ./SESSIONS_ARCHIVE.md                               # rotierte Session-Blöcke (L3)
updated: 2026-08-18
---
# CLAUDE.md — Phase 12: Datenfundament (`phase12_data_foundation/`)

> Three data weeks (Phase 11) died on infrastructure, never on measurement. Root cause: one
> instrument fact lived in three divergent stores, the Phase-9 multi-source bar chain
> (`ChainedBarProvider`) was built and never switched on (`enable_ig_bars` default `False`).
> **Source of truth is the plan doc + the code, not this file.** Full plan:
> `../docs/concepts/phase12_data_foundation_plan.md`.

## Mission (zuerst lesen)
Ein neues Fundament, sequenziell (Überweg C, D1, Nikinger-Entscheidung 2026-08-11):
1. **Instrument-Registry** wird die eine Wahrheit für Instrument-Fakten; Symbol-Mapping
   abgeleitet + code-verifiziert statt deklariert.
2. **BarService** wird der eine Bar-Pfad für alle Konsumenten (Research + Paper Tracker).
3. **Bar-Archiv** (`data/bars.sqlite`) — jede gefetchte Bar wird persistiert, quellenagnostisch.
4. **Recorder** — eigener yF-only-Prozess, schreibt kontinuierlich, unabhängig vom Bot-Zustand.
5. **Mess-Heartbeat** — ein Ausfalltag fällt am selben Tag auf.
6. **Lightstreamer-Mitschrieb** (Step 10) — gated auf die bestandene Beweiswoche.

**Done-Kriterium der Phase:** eine echte Beweis-Messwoche läuft durch, ohne dass Infrastruktur
die Messung tötet (Plan §7). Die WI-2-Auswertung selbst bleibt Phase-11-Wiederaufnahme.

## Bauprinzip
„So wenig AI wie möglich, so viel AI wie nötig." **Phase 12 fügt NULL neues AI hinzu** (Plan
§1) — Symbol-Verifikation ist ein deterministischer Preisvergleich (IG-Snapshot vs. yF-Last),
kein LLM-Aufruf. Wer hier ein LLM „mappen/prüfen/schätzen" lassen will → stop, das ist Code.

## Scope
- **DRIN:** `data_foundation/` Paket (Archiv, Budget, Resolver, BarService, Recorder,
  Heartbeat), Migration 006 (Registry-Erweiterung + `paper_trades.resolution_source`), die
  Rewiring-Punkte in `phase8_scheduler/scripts/wiring.py` (Steps 3/4/6/7, Wochenend-Arbeit).
- **DRAUSSEN:** WI-2/W2-Auswertung + jede weitere H-Serie (Phase-11-Wiederaufnahme nach PASS),
  Research-Funnel-Fix, B3-Margin-Headroom-Umsetzung (nur Feld-Scouting hier, s. Session-Block),
  Council-Paper-Call, UI, Live-Konto, Lightstreamer für Live-Quotes (Step 10 hier ist reiner
  Archiv-Mitschrieb, anderer Zweck). Momentum-VETO bleibt unangetastet (D16) — sourct immer
  direkt aus P1-IG-Echtzeit-Bars, nie aus BarService/Archiv/yF.

## Rahmen (Plan §1) — ⚠️ seit 2026-08-17 geändert

> **Nikinger-Entscheidung 2026-08-17 (überschreibt Plan §1 für den Rest von Phase 12):**
> **Arbeit findet ab jetzt direkt unter der Woche statt**, auch bot-berührend. Begründung:
> der Bot läuft ohne die ausstehenden Fixes (U1–U3, s. Handover §3.0) **nicht gescheit** —
> die Wochenend-Regel würde einen kaputten Messbetrieb um jeweils eine ganze Woche
> verlängern, also genau das produzieren, wogegen die Notbremse gezogen wurde.
> **Diese Entscheidung ist für die nächste Planungssession verbindlich zu übernehmen.**

Daraus folgt für Werktags-Sessions:
- Bot-berührende Änderungen sind erlaubt. **Vorher den Bot stoppen** (Kill-Switch oder
  `kill <pid>`, `ps aux | grep scheduler.run` als Gegenprobe) — ein Datei-Edit wirkt ohnehin
  nicht auf einen laufenden Prozess, und ein zweiter Scheduler daneben löst die
  Parallel-Login-Falle aus. Nach dem Edit gezielt neu starten.
- Unverändert gültig: Live-/Netz-/kostenpflichtige Läufe macht der **Nikinger**; die
  Live-DB wird von Claude nur read-only (`mode=ro`) gelesen; Cross-Phase-Edits außerhalb
  `data_foundation/` bleiben freigabepflichtig (die U2/U4-Fixorte in `wiring.py` fallen
  darunter).

**Vorherige Regel (historisch, bis 2026-08-17):** bot-berührende Steps nur am Wochenende
(Bot steht, Markt zu); werktags docs-only / `data_foundation/`-Paket-Code selbst.

## Modul-Tabelle
Siehe [`README.md`](./README.md).

---

## Session stopped — 2026-08-18 (Session 9: Closeout-Analyse nach dem Scheitern — Root Cause korrigiert, neuer Weg empfohlen)

> **Auftrag:** die abgeschlossene/zurückgestellte Phase gegen den As-Built-Zustand prüfen
> (selbst nachmessen, nicht aus Handovers übernehmen), SVG + Closeout-Handover + Statuspflege.
> **Volles Ergebnis:
> [`PHASE12_5_CLOSEOUT_HANDOVER.md`](./PHASE12_5_CLOSEOUT_HANDOVER.md)** — dieser Block ist die
> Kurzfassung. Keine Produktionscode-Änderung in dieser Session.

### Completed

1. **As-Built selbst nachgemessen** (Code, Tests, Live-DB `mode=ro`): Tests **123 / 160** grün,
   `main` **4 Commits vor `origin/main` (nicht gepusht)**, Scheduler aus, Recorder (`pid 33151`)
   läuft kostenlos weiter, IG-Fenster 4731/10 000, IG-eigene Restmeldung 5054 (14:08).
2. **Neuer, entscheidender Befund:** von **1782 bei IG gekauften 1-Min-Bars trugen 1638 (92 %)
   Zeitstempel, die bereits als yF-Bar im Archiv lagen** — gekauft wurden ~144 Bars echter neuer
   Information für 4515 Punkte. Das kippt die Empfehlung von „billiger kaufen" auf „nicht kaufen".
3. **Zwei Korrekturen an der bisherigen Root-Cause-Erzählung** (Closeout §2, datiert):
   **K1** — `_covers_tail and coverage_ratio` kurzschließt links; `_covers_tail` verlangt eine
   Bar ≤ 1 Min alt, yF liefert mit ~15 Min Eigenverzug (15:05er Bar um 15:20 geholt, Recorder-Takt
   300 s) ⇒ **U3 kann den Refetch nie ausgelöst haben**; Auslöser ist allein das Einschalten des
   Messarms, der Pfad lag seit Step 4 latent. **K2** — „41 von 90" war falsch: 45 Paare / 90
   Zeilen, 70 aufgelöst, **54 von 70** mit IG-Beteiligung, 20 blieben OPEN.
4. **Testlücke benannt:** keine der 123 Zusicherungen prüft *Kosten* — `test_service.py` prüft,
   **dass** ein Refetch feuert, nie **wie teuer** er ist.
5. **Neue Dateien:** [`PHASE12_5_CLOSEOUT_HANDOVER.md`](./PHASE12_5_CLOSEOUT_HANDOVER.md) und
   [`../docs/architecture/phase12_5_failure.svg`](../docs/architecture/phase12_5_failure.svg)
   (1080×1080: Fehlerbild → Zielbild → was offen bleibt).
6. **Doku-Sync + Korrekturen** (dieser Commit): Root-`CLAUDE.md`, `ROADMAP.md` (u. a. „P12 117"
   → **123**), `docs/INDEX.md` (+2 Zeilen), dieser Kopf inkl. Rotation des Session-8-Blocks.

### Verified

- 123 / 160 Tests heute getrennt gelaufen, beide grün.
- Alle Zahlen dieses Blocks stammen aus eigenen read-only Abfragen gegen `data/bars.sqlite` und
  `data/trading_bot.sqlite`, nicht aus Vordokumenten.
- K1 gegen den Quelltext geprüft (`service.py:218-219`, `:229-238`, `_covers_tail` ab `:266`),
  nicht nur argumentiert.

### Next

- **Entscheidungen einholen, bevor geplant wird** (Closeout §4/§5/§6): Weg (Empfehlung
  **Option B** — Auflöse-Pfad kauft nie wieder Daten, Frage wechselt von „reicht das Archiv bis
  jetzt?" zu „deckt es das Fenster dieses Trades bis `time_stop_utc`?"; Option A/Patch-Leiter
  explizit abgelehnt), Label (Empfehlung: kein neues Unter-Label), Wiederanlauf-Zeitpunkt
  (Empfehlung: nicht vor Umsetzung + frischer `remainingAllowance`-Probe; Fenster rollt ~25.08. ab).
- Erste Akzeptanzbedingung des nächsten Plans soll eine **Kostenzusicherung** sein.

### Open questions / blockers

- **Ungeklärt, bewusst nicht geraten:** warum `IX.D.IBEX.FWM2.IP` als einzige Epic 14/14 Trades
  rein aus yF auflöste (identische Zeitfenster und yF-Abdeckung wie die anderen vier, dennoch
  10 `ig`-ok-Events in `research_health.jsonl`). Für Option B unmittelbar relevant — sie ist der
  Existenzbeweis.
- Kein technischer Blocker: Bot steht sicher, Recorder sammelt weiter kostenlos.

---

> **Ältere Session-Blöcke** (verbatim ausgelagert, newest-first): [SESSIONS_ARCHIVE.md](./SESSIONS_ARCHIVE.md) — Rotation per Doc-Layers-Konvention ([docs/DOC_LAYERS_CONVENTION.md](../docs/DOC_LAYERS_CONVENTION.md)).
