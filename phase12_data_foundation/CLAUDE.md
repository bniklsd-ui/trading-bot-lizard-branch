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

## Session stopped — 2026-08-18 (Session 8: Step 4/5 live durchgeführt, P12.5 dann formal CLOSED — GESCHEITERT)

> **Verlauf:** Step 4 (Neustart mit beiden Flags) lief Nikinger-seitig 2026-08-17 abends.
> Diese Session verifizierte Step 5 (der vierteilige falsifizierbare Nachweis) über zwei
> Tage hinweg — und fand dabei einen fünften, ungeplanten Befund, der den ganzen Track
> stoppte. **Volles Ergebnis:
> [`PHASE12_5_FAILURE_HANDOVER.md`](./PHASE12_5_FAILURE_HANDOVER.md)** — dieser Block ist
> die Kurzfassung.

### Completed

1. **Step 5 verifiziert, in drei Teilen über zwei Tage** (read-only, kein Code-Touch bis
   zur Intervention):
   - **(a)/(b)** sofort grün: echte argv zeigten beide Flags (`pid 46390`), Config-Default
     bestätigt.
   - **(d-i)** sofort grün: `data_health.py --day 2026-08-17` (ohne `--shadow-enabled`)
     lieferte exakt den geforderten Beweis — `ok=False`, Exit 1, Problem-String
     `"measurement arm off"` verbatim, gegen den echten Tag-1-Nulltag.
   - **(c)** am Vorabend leer (kein Fund, kein Diagnosefall — WINDOW war vor dem Neustart
     bereits zu), am Folgetag (2026-08-18, erster voller Handelstag mit scharfem Messarm)
     **real bestätigt**: `pairs_opened: 90`, `pairs_resolved: 66`, `pairs_typed_expired: 4`,
     `resolution_source` erstmals mit echten Werten (`yf`, `ig`, `ig+yf`).
2. **Beim Auswerten von (c): der IG-Budget-Befund.** `spent_in_window` sprang von 151 auf
   4731 Punkte binnen ~4 Handelsstunden. Attribution zweifelsfrei über die
   Punktzahl-Verteilung erzwungen (10× 5 Punkte reales Research vs. **15× exakt 301
   Punkte** — Vollfenster-Top-ups des Paper-Trackers, fälschlich unter `spend_kind=
   "research"` gebucht, `wiring.py:189`). Root Cause: `BarService.get_window`
   (`service.py:202-228`) fordert bei jedem Coverage-Miss das **komplette** Fenster neu
   an, nicht die Lücke — ein vorher nie exponierter Pfad, weil der Messarm bis P12.5 nie
   lief; **U3s Korrektheit** (nicht ein neuer Bug) schaltet ihn erstmals scharf, U2s
   Retry-Cap verstärkt ihn (bis zu 12 Top-ups je Epic statt einem). Funktionales
   Restbudget (`reserve_points=1500` unverändert) lag bei Fund-Zeitpunkt nur noch bei
   ≈ 11–12 weiteren Vollfenster-Fetches — die von `data_health.py` ausgegebenen
   `predicted_exhaustion_days: 7.5` waren irreführend (mitteln über die lange Ruhephase
   vor dem Neustart).
3. **Nikinger-Intervention, sofort:** „Let's intervene now - phase 12.5 is formally over
   - failed. […] phase 12.5 shouldn't have any more steps apart from testing." Scheduler
   (`pid 46390`) per `kill` gestoppt, Exit binnen weniger Minuten bestätigt (`ps aux`
   leer). Recorder (`pid 33151`) bewusst weiterlaufen gelassen — reiner
   yFinance-Prozess, kein IG-Verbrauch.
4. **`PHASE12_5_FAILURE_HANDOVER.md`** (neu) — Root Cause, Zahlen, was bleibt gültig
   (alle fünf Code-Fixes U1/U2/U3/U5/Entscheidung B sind unabhängig korrekt und live
   bewiesen, **nicht** revertieren), Empfehlung fürs Danach (drei Bausteine, priorisiert:
   Spend-Kind-Korrektur → Top-up auf die Lücke begrenzen statt Vollfenster → optionale
   Once-per-Epic-Drossel).
5. **Doku-Sync** (dieser Commit): Root-`CLAUDE.md` Phase-12-Zeile, `ROADMAP.md`,
   `docs/INDEX.md` (+ neue Zeile für den Failure-Handover), dieser Kopf inkl. Rotation
   des Session-7-Blocks nach `SESSIONS_ARCHIVE.md`.

### Verified

- Alle fünf P12.5-Fixes (U1/U2/U3/U5/Entscheidung B) live gegen echte Produktionsdaten
  bestätigt korrekt (s. Completed 1) — **keiner** davon ist die Fehlerursache.
- IG-Spend-Attribution zweifelsfrei über die Punktzahl-Verteilung (5 vs. 301) belegt,
  nicht nur vermutet.
- Scheduler-Stop verifiziert (`ps aux` vor/nach dem `kill`, Exit bestätigt).
- `pytest phase12_data_foundation/tests -q` / `phase10_v3/tests -q` unverändert grün
  (123 / 160) — diese Session hat keinen Produktionscode geändert.

### Next

- **P12.5 ist formal geschlossen — keine weiteren Bauschritte unter diesem Label, nur
  Tests.** Der nächste Fix-Block (Empfehlung: Spend-Kind-Korrektur + Top-up-auf-Lücke-
  begrenzen, s. Failure-Handover §5) ist ungebaut und unfreigegeben — Nikinger entscheidet
  Nummerierung/Label, wenn es losgeht.
- Phase-12-Done-Kriterium (Beweiswoche, Plan §7) weiterhin offen — nach diesem Scheitern
  weniger denn je erreicht.
- Push-Entscheidung offen wie üblich (bewusste, separate Freigabe).

### Open questions / blockers

- Der eigentliche nächste Schritt (Fetch-auf-Lücke-Design) ist noch nicht durchdacht
  genug für eine Implementierung — Failure-Handover §5 nennt die Richtung, nicht das Design.
- Kein technischer Blocker sonst — der Bot steht sicher (Scheduler aus, Recorder läuft
  kostenlos weiter).

---

> **Ältere Session-Blöcke** (verbatim ausgelagert, newest-first): [SESSIONS_ARCHIVE.md](./SESSIONS_ARCHIVE.md) — Rotation per Doc-Layers-Konvention ([docs/DOC_LAYERS_CONVENTION.md](../docs/DOC_LAYERS_CONVENTION.md)).
