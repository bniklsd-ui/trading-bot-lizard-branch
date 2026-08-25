---
status: snapshot
purpose: Phase-12-Closeout-Handover (2026-08-25, Nikinger-Freigabe 2026-08-25) — Phase 12 (Datenfundament) ✅ abgeschlossen. P12.5 (Messarm-Zwischenschritt) war 2026-08-18 formal CLOSED + GESCHEITERT; die fünf Code-Edits davon bleiben gültig. **Die strukturelle Antwort auf das P12.5-Scheitern steht in Phase 13 (Beschaffung ≠ Verbrauch) und Phase 14 (Discovery-Then-Deterministic) — Phase 12 ist abgeschlossen, BEVOR die Beweiswoche durchlief, weil die Trennung Beschaffung/Verbrauch die Voraussetzung ist, die Phase 12 bauen wollte.** Read-only-Inventur, jeder Datenpunkt selbst nachgemessen.
read-when: vor jedem Plan, der Phase 12 wieder aufnimmt; vor jedem Re-Read der P12.5-Failure-Geschichte; vor jeder Frage „ist Phase 12 eigentlich fertig?"; vor jedem Scharfstellen eines Messarms; **vor jedem Code-Edit an data_foundation/** (Konsistenz-Regeln §6)
detail: L3
up: ./CLAUDE.md
down:
  - ./PHASE12_5_CLOSEOUT_HANDOVER.md   # 📕 P12.5 Closeout (2026-08-18) — die As-Built-Analyse mit den zwei Root-Cause-Korrekturen und der Option-B-Empfehlung
  - ./PHASE12_5_FAILURE_HANDOVER.md   # 📕 P12.5 Sofort-Befund (Interventionstag) — bleibt unverändert, mit den zwei Korrekturen in der P12.5-CLOSEOUT-Datei (§2)
  - ./PHASE12_PREPROOF_HANDOVER.md   # 📕 Tag-1-Befund vor P12.5, Pre-P12.5 Status
  - ./PHASE12_5_MEASUREMENT_ARM_PLAN.md   # 📕 der gescheiterte Bauauftrag (superseded, unverändert)
  - ../docs/concepts/phase12_data_foundation_plan.md   # 📕 Phase-12-Plan (D1–D20, Steps 0–10, §7 PASS-Kriterien)
  - ../phase13_live_data/PHASE13_CLOSEOUT_HANDOVER.md   # 📕 die strukturelle Antwort (Phase 13) — was aus P12.5 wurde
  - ../phase14_discovery/PHASE14_CLOSEOUT_HANDOVER.md   # 📕 Phase 14 — die Source-Discovery-Ebene darüber
  - ../docs/architecture/phase12_closeout.svg   # 📕 diese Phase, bildlich (1080×1080, Fehlerbild + Zielbild)
  - ../docs/architecture/phase12_5_failure.svg   # 📕 das P12.5-Fehlerbild im Detail
  - ../docs/architecture/data_foundation.svg   # 📕 der Phase-12-Architektur-Überblick (gültig)
  - ./SESSIONS_ARCHIVE.md   # 📦 volle Session-Historie (verbatim, newest-first)
updated: 2026-08-25
---

# Phase 12 (Datenfundament) — Closeout-Handover (2026-08-25)

> **Autor:** Claude Code, Read-only-Analyse 2026-08-25, **kein** Produktionscode-Edit.
> **Adressat:** die nächste Session an Phase 12 (Folge-Arbeit) oder an Phase 13 / 14 / 15.
> **Quelle aller Zahlen:** eigene Re-Sweeps + Git-Historie + Live-DB `mode=ro`. Nichts aus
> Vordokumenten übernommen, was sich selbst hat prüfen lassen.

---

## §0 BLUF

Phase 12 ist **abgeschlossen**. Steps 0–8.5 stehen live auf `main` (143 Phase-12-Tests grün,
18 Commits auf `origin/main`, `main` = `origin/main` = `b9327ca`). P12.5 (Messarm-
Zwischenschritt) wurde 2026-08-18 formal CLOSED + GESCHEITERT — die fünf Code-Fixes
(U1/U2/U3/U5 + Entscheidung B) bleiben **korrekt im Repo** und gehören zur Phase-12-
Bilanz; nur das **Betriebsmodell „Messarm dauerhaft an"** ist unter dem damaligen
Fetch-Design nicht tragbar (4731/10.000 IG-Wochenpunkte am ersten scharfen Handelstag).

**Die strukturelle Antwort steht in Phase 13 + Phase 14** (Nikinger 2026-08-25): der
„Auflöse-Pfad kauft nie wieder Daten" ist nicht mehr eine Empfehlung, sondern eine
umgesetzte Architektur — Phase 13s `BarService.get_window` ist reine Archiv-Lesung,
Phase 14s `instrument_source_availability` macht Quellen zu einer Registry-Zeile statt
einer Code-Konstante. Damit ist das Phase-12-„Done-Kriterium" (Plan §7 PASS) **nicht
mehr nötig**: Phase 13+14 beantworten die Frage, die Phase 12 stellen wollte, mit
anderen Mitteln.

Phase 12 ist **die Foundation**; der **Verbrauch** (was die Foundation wert macht)
ist Phase 13 beweiswoche-track. Saubere Trennung zwischen Foundation und Validation
ist genau das, was die P12.5-Lektion forderte.

---

## §1 Bilanz (5-Zeilen-Schema, Handover-Prompt-Stand)

| Zeile | Stand 2026-08-25 (selbst nachgemessen) |
|---|---|
| **fertig gestellt** | **Steps 0–8.5** (Mo 2026-07-13 live auf main, _build_universe_from_db + BarService.get_window + BarArchive + yF-only Recorder + Heartbeat/DivergenceSampler + D18 scripts + IG-Allowance-Bugfix) · **P12.5 Steps 1–3** (Woche 2026-08-17/18: U1 Stale-Trade-Cleanup, U2 retry-cap (≈ 1 statt 5 Fetches pro Trade), U3 coverage_shadow-Hook, U5 shadow deadline margin (17:20 statt 17:30 Cut-off), Entscheidung B Heartbeat-Tagesbewertung, alle 5 offline grün) · alle 18 Phase-12-Commits auf `origin/main` |
| **getestet** | **143** Phase-12-Unit-Tests grün (heute gemessen 2026-08-25; **+20 Tests seit Closeout-Handover 2026-08-18**, weil Phase-13-Block-A `coverage.py` + `service.py`-Edits dort mit-testen — Korrektur zur Doku im selben Commit) · Σ 1698 repo-weit grün · ⚠ Testlücke aus dem Closeout-Handover weiterhin gültig: **keine** der 143 Tests prüft *Kosten* (für eine künftige Re-Aktivierung des Messarms zwingend zu beheben) |
| **im Rahmen der Möglichkeiten live validiert** | **Step 8.5** (Tag-1-Live): 84 reale Trades aus Vorwoche replayed, Token-Tracker validiert (Pre-Proof-Handover) · **P12.5 U1/U2/U3** real-belegt in der einzigen scharfen Messwoche (70 von 90 Shadow-Trades aufgelöst, `resolution_source` befüllt) · **P12.5 Entscheidung B** real: Heartbeat markiert den Tag als fehlerhaft, 54 von 70 aufgelösten Trades mit IG-Beteiligung, 20 OPEN (gestoppt durch Intervention) · **nur offline** bewiesen: U5 (Shadow-Deadline-Marge, AST-Guard), Plan §7 PASS-Kriterien A–D + G |
| **gepusht und committet** | `main` synchron mit `origin/main` (HEAD = `b9327ca`) · **18** `phase12:`-Commits auf origin · 0 unpushed lokal · **Korrektur zur Closeout-Handover-Head-Zeile**: dort stand „`main` **4 Commits vor `origin/main` (nicht gepusht)**" — diese Lücke wurde in der heutigen Session **nicht** angesprochen; sie war zum damaligen Zeitpunkt real und ist beim Stand 2026-08-25 history. Wer sie noch im aktuellen Stand sucht, sucht vergebens. |
| **nicht erreicht / offen geblieben** | (a) **Step 9 (Beweiswoche)** — nie begonnen unter Phase 12; **abgelöst durch Phase 13+14** (Phase 13s Beweiswoche läuft seit Mo 2026-08-25 separat, gegen die Phase-13-Architektur, nicht gegen die Phase-12-Architektur) · (b) **Plan §7 PASS-Kriterien** — durch Phase 13 strukturell ersetzt; Phase 12 braucht sie nicht mehr zu erfüllen · (c) **WI-2/W2 + H3/H5/H7 + B3-Margin-Headroom** — Phase-11-Inhalte, gehören in die Phase-11-Wiederaufnahme bzw. Phase 15 · (d) **Resolution-Source-Drift `IX.D.IBEX.FWM2.IP`** — 14/14 rein yF, 10 `ig`-ok-Events in `research_health.jsonl` (Ungeklärt, bewusst nicht geraten) · (e) **Testlücke „keine Kosten-Zusicherung"** — relevant nur für eine künftige Re-Aktivierung des Messarms; Latent-Spannung bis dahin |

---

## §2 Architektur-Bild (in einer Zeile)

```
                Phase 12 (✅ abgeschlossen)               Phase 13+14 (✅ strukturelle Antwort)
                ─────────────────────────                ───────────────────────────────
data/trading_bot.sqlite         data/bars.sqlite         BarArchive ← S1 LS/S2 yF Recorder
   instrument_universe             bar_archive             │           S3 Capital.com
        (Migration 006)         (quellen-agnostisch)      │           S4 GapRescue AUS
   + _build_universe_from_db    + Coverage + Source-   Verbraucher = liest nur,
   + SymbolResolver (Step 8.5)    Disclosure (P12.5)    kauft NIE (Phase 13 §0 L1)
                                                              ↑
                                                ┌─────────────────────┴──────────────────┐
                                                │                                        │
                                       PaperTracker   Research (P4)   DivergenceSampler
                                                               │
                                                       instrument_source_availability
                                                       (Phase 14 Registry, D2)
```

Quellen-Tabelle: siehe Code. Der Plan `phase12_data_foundation_plan.md` bleibt `📕` (nicht
editieren); diese Zeile ist die kanonische Zusammenfassung für Folge-Sessions. Bildlich:
`../docs/architecture/phase12_closeout.svg` (1080×1080, dieses Commits) — Fehlerbild
(Auflöse-Pfad kaufte von IG) + Zielbild (Beschaffung ≠ Verbrauch, Phase 13+14).

---

## §3 Delta seit dem letzten Handover

Letzter Handover: `phase12_data_foundation/PHASE12_5_CLOSEOUT_HANDOVER.md` (2026-08-18) —
genau eine Woche her. Phase-10-Closeout (gestern, Commit `b9327ca`) hat **nichts** an
Phase 12 angefasst; was sich seitdem geändert hat, in der Reihenfolge der Audit-Relevanz:

### 3.1 Phase 13 ist die strukturelle Antwort — Code-complete, live-verifiziert
Phase 13 (Live-Datenfundament, geöffnet 2026-08-18 nach P12.5-Scheitern, Block-A/B/C
code-complete + live-verifiziert für DE40/FR40 am 2026-08-22) **ist die Phase, die
P12.5 nicht bauen konnte**: BarService.get_window ist seit Phase 13 Block A
**reine Archiv-Lesung** (`data_foundation/service.py` post Phase 13 A2). Der
vierstufige Beschaffungs-Stack (S1 LS → S2 yF Recorder → S3 Capital.com PARTIAL →
S4 GapRescue AUS) schreibt in *ein* Archiv; der Verbrauchspfad ruft nie einen
externen Fetch. Das ist Option B aus dem Closeout-Handover §4 — **bereits umgesetzt**.

### 3.2 Phase 14 macht Quellen zu einer Registry-Zeile
Phase 14 (Discovery-Then-Deterministic, Blöcke 0/A/B/C code-complete 2026-08-22,
Migration 007 + `instrument_source_availability`) verallgemeinert das: Quellen sind
**keine Code-Konstante** mehr (`EPIC_MAP` ist verschwunden, Block C Re-Plan §3),
sondern eine **DB-Tabelle** mit `(epic, source, resolution, source_symbol, status,
origin)`. Der Code-Deploy beim Hinzufügen einer neuen Quelle entfällt — eine
Datenbank-Zeile reicht. Cross-Phase-Edits sind freigegeben, Phase 13+14 sind
die Nachfolger, die aus P12.5 gebaut wurden.

### 3.3 Beweiswoche läuft seit Mo 2026-08-25
Die Phase-13-Beweiswoche P1–P9 (operator-getrieben) läuft seit Mo 2026-08-25 — die
„Phase-12-Beweiswoche" (Plan §7), die nie begonnen wurde, ist **abgelöst** durch
die Phase-13-Beweiswoche. Beide messen verschiedene Dinge (Phase 12 hat gefragt
„deckt das Archiv das Fenster?"; Phase 13 fragt „deckt das Archiv das Fenster
+ Coverage-Threshold?"). Phase 12s Frage ist subsumiert.

### 3.4 Heute gemessen, nicht aus Vordokumenten
- `phase12_data_foundation/` Source-Files (non-test): **11** (gezählt via `find`, exkl. `__pycache__` + `.pytest_cache`)
- `phase12_data_foundation/tests/*.py`: **8** Test-Files
- Phase-12-Tests: **143 grün** (war im Closeout-Handover 2026-08-18 noch „123"
  behauptet; Code = source of truth, real 143, +20 Tests seit Closeout-Tag durch
  Phase-13-Block-A-Coverage-Code, der mit in `phase12_data_foundation/tests/` lebt)
- Σ-Sweep: **1698 grün, 0 fails**
- `git log origin/main -- phase12_data_foundation/`: **18 Commits** Phase-12 mit
  Prefix `phase12:`
- `git log --grep='^phase12:'` lokal: **18** (identisch mit origin), 0 unpushed
- `git log --grep='^phase12:'` insgesamt (alle Branches): **18**

---

## §4 Offene Entscheidungen (Nikinger) — **alle vorab geklärt durch deine Anweisung 2026-08-25**

Der Closeout-Handover 2026-08-18 enthielt drei offene Entscheidungen (Weg, Label,
Wiederanlauf-Zeitpunkt). Durch deine Anweisung „die darauffolgenden Phasen DIE
Antwort darauf wahren" sind sie **im Sinne der Empfehlung entschieden**; die
expliziten 5-Zeilen-Bilanzen folgen, damit klar ist, was geklärt ist:

1. **Weg** — **Option B** (struktureller Schnitt): „der Auflöse-Pfad kauft nie
   wieder Daten". **Realisiert durch Phase 13 Block A** (`BarService.get_window
   ist jetzt reine Archiv-Lesung`, Commit `e8c5b94`). Frage wechselt von „reicht
   das Archiv bis jetzt?" zu „deckt es das Fenster dieses Trades bis
   `time_stop_utc`?" — durch Coverage-Threshold (`coverage_assess`) umgesetzt.
2. **Label** — **kein neues Unter-Label** (wie empfohlen). P12.5 bleibt als benannte
   Fehlgeschichte stehen; P12 + P12.5 schließen unter einem Closeout-Handover.
3. **Wiederanlauf-Zeitpunkt** — **abgelöst durch Phase 13**. Die Phase-12-Beweiswoche
   wird nicht wieder aufgenommen; die Phase-13-Beweiswoche läuft seit
   2026-08-25-00:01 separat.

Zusätzlich:

4. **Resolution-Source-Drift `IX.D.IBEX.FWM2.IP`** (14/14 rein yF, 10 `ig`-ok-Events
   in `research_health.jsonl`, Closeout-Handover §3) — **bleibt ungeklärt**, aber
   durch Phase 13+14 überholt. Wer es wissen will, kann es aus den Live-Daten
   nachmessen; für den Closeout ist es nicht blocker-relevant.

5. **Testlücke „keine Kosten-Zusicherung"** (Closeout-Handover §3) — **bleibt latent
   wirksam**, bis eine künftige Re-Aktivierung des Messarms eine solche Zusicherung
   fordert. Dann: ein Test, der prüft, dass ein Auflösungs-Zyklus ≤ X Punkte kosten
   darf. Empfehlung: **nicht proaktiv patchen** — die Architektur, die das Problem
   strukturell löste, ist Phase 13, nicht eine Test-Erweiterung in Phase 12.

---

## §5 Datei-Anker

**Zuerst lesen:**
- [`./CLAUDE.md`](./CLAUDE.md) — Phasenkopf + neuester Session-Block
- [`./PHASE12_5_CLOSEOUT_HANDOVER.md`](./PHASE12_5_CLOSEOUT_HANDOVER.md) — die Analyse vom 2026-08-18 mit den zwei Root-Cause-Korrekturen (K1 + K2, datiert)
- [`./PHASE12_5_FAILURE_HANDOVER.md`](./PHASE12_5_FAILURE_HANDOVER.md) — der Sofort-Befund vom Interventionstag; mit den beiden P12.5-CLOSEOUT-Korrekturen oben drauf
- [`../docs/concepts/phase12_data_foundation_plan.md`](../docs/concepts/phase12_data_foundation_plan.md) — der frozen Plan (📕, „never edit"); §7 PASS-Kriterien sind durch Phase 13 abgelöst
- [`../docs/architecture/phase12_closeout.svg`](../docs/architecture/phase12_closeout.svg) — diese Phase, bildlich (1080×1080)

**Die strukturelle Antwort, die Phase 12 abgelöst hat:**
- [`../phase13_live_data/PHASE13_CLOSEOUT_HANDOVER.md`](../phase13_live_data/PHASE13_CLOSEOUT_HANDOVER.md) — vier Stufen Beschaffung, ein Archiv; der Verbrauchspfad kauft nie
- [`../phase14_discovery/CLAUDE.md`](../phase14_discovery/CLAUDE.md) — `instrument_source_availability` als Registry (D1); `EPIC_MAP` ist verschwunden (A2 grün)

**Die Nähte, die Phase 12 dem Restprojekt gegeben hat (Code ist Wahrheit — hier nur Wegweiser):**
- `phase2_persistence/migrations/006_phase12_registry.sql` — Migration 006 (`yf_ticker` + `point_value` + `point_value_source` Felder-Erweiterung)
- `phase12_data_foundation/data_foundation/` — `models.py` (KNOWN_SOURCES, DS_STALE_SOURCE), `archive.py` (`tick_count` + `sources`-Filter, Phase 13 erweitert), `service.py` (BarService.get_window, seit Phase 13 A2 reine Archiv-Lesung), `coverage.py` (NEU durch Phase 13), `symbols.py` (SymbolResolver), `recorder.py`, `budget.py`, `heartbeat.py` (DivergenceSampler), `run.py`
- Cross-Phase-Nähte: `phase9_universe/universe/store.py` (wiring, phase12:629), `phase8_scheduler/scripts/wiring.py` (Steps 3/4/6/7 + Allowance-Bugfix), `phase8_scheduler/scheduler/config.py`, `phase10_v3/abstain_lessons/paper.py` (`window_ok`-Param durch Phase 13)

**Historie, nur bei Bedarf:** `phase8_scheduler/PHASE8_CLOSEOUT_HANDOVER.md` (war der
letzte echte Closeout vor Phase 9-12), `phase12_data_foundation/PHASE12_PREPROOF_HANDOVER.md`
(Tag-1-Befund), `phase12_data_foundation/PHASE12_5_MEASUREMENT_ARM_PLAN.md` (superseded
Bauauftrag, nicht editiert — Convention), `phase10_v3/PHASE11_DEFERRAL_HANDOVER.md` (warum
dieser Track überhaupt entstanden ist), `phase12_data_foundation/SESSIONS_ARCHIVE.md`.

---

## §6 Konsistenz-Regeln, die Phase-12-Code aufstellt (nicht antasten, ohne Not)

1. **NULL neues AI in Phase 12.** Symbol-Verifikation = deterministischer Preisvergleich
   (IG-Snapshot vs. yF-Last), kein LLM-Aufruf. Phase 12 fügt keine AI-Naht hinzu.
   Wer das anfasst, bricht den Plan-§1-Vertrag.

2. **Eine Wahrheit pro Instrument-Tatsache** (Durability-Anforderung A aus dem
   Datenfundament-Handover). Migration 006 hat `yf_ticker` + `point_value` +
   `point_value_source` zentralisiert; jede Verbraucher-Phase (Phase 9, Phase 13)
   liest über diese Registry. **Drei Speicher wären eine Regression.**

3. **Coverage-Frage vor Auflösung** (Phase 13 §0 L1 + Closeout-Handover Empfehlung B):
   der Auflöse-Pfad fragt zuerst „deckt das Archiv das Fenster dicht genug?",
   **bevor** er irgendeinen externen Fetch startet. Wer eine `if`-Verzweigung
   einbaut, die direkt IG-REST ruft, **rollt den Fail wieder rein**.

4. **Quell-Disclosure ist nicht optional** (P12.5-Entscheidung B): jede Bar trägt
   `source` + `tick_count`. Gemischte IG/yF-Wochen sind ohne das **nicht auswertbar**
   (Spread-/Zeitstempel-Drift). Diese Spalte ist hartkodiert im Schema, nicht
   konfigurierbar.

5. **Ressourcen sind modelliert** (Anforderung F): jeder Fetch geht durch `budget.py`,
   ohne `remainingAllowance`-Probe kein externer Call. P12.5-Symptom (4731/10.000
   in einem Tag) war genau das Fehlen dieser Modellierung.

6. **Momentum-VETO bleibt unangetastet** (D16): sourct direkt aus P1-IG-Echtzeit-Bars,
   nie aus `BarService` / `bar_archive` / yF. Wer das umstellt, bricht den
   D16-Vertrag, der die Pipeline-Trennung garantiert.

---

## §7 Was die nächste Session **nicht** tun soll

- **Keine** Wiederaufnahme der Phase-12-Beweiswoche — sie ist durch Phase 13
  abgelöst. Wer misst, misst auf der Phase-13-Architektur.
- **Kein** Patch auf P12.5-Symptomebene mehr — die Wurzel ist in Phase 13+
  umgebaut. Wer einen Patch hinzufügt, **rollt den Fail wieder rein**, den
  die Trennung gerade behoben hat.
- **Keine** Code-Edits an `data_foundation/`, die die fünf Konsistenz-Regeln aus §6
  verletzen. Besonders: keine Coverage-Frage aus dem Auflöse-Pfad entfernen;
  keine Quell-Disclosure-Dropdowns; keine Modifikation am Momentum-VETO-Pfad.
- **Keine** „nur zur Sicherheit"-Re-Aktivierung des Messarms. Wer den Messarm
  braucht, holt eine eigene Freigabe, schreibt den Plan, **und** klärt vorher,
  ob die Kostenzusicherung als Test vorliegt.
- **Kein** Scheduler-Restart für Messzwecke, solange die Phase-13-Beweiswoche
  läuft und das Restart-Gate aus `ALLOWANCE_INCIDENT_2026-08-08.md` (Phase-10-
  Kontext) gilt.
- **Keine** Duplikation von Phase-12-Wissen an einer anderen Stelle: das
  Closeout-Handover hier, der Phasenkopf dort, die P12.5-CLOSEOUT-Datei als
  Analyse — drei Quellen, drei Rollen, keine neuen Vierten.

---

> **Autor dieses Files:** Claude Code (Sonnet 5, MiniMax M3 via claude-minimax),
> Read-only-Session 2026-08-25. Cross-Phase-Liste (Plan §4 + Session-9-NEXT)
> abgearbeitet: Phase-12-Files editiert (1 NEU + 2 Updates), Phase-13/14
> (`block_diff`, `discovery`, `coverage`) **nicht** angefasst — die sind die
> strukturelle Antwort und bleiben autonom. **Phase-12-Closeout-Handover ist
> eine eigenständige dokumentationsdominierte Atom-Einheit** — keine
> Cross-Phase-Produktionscode-Edits am Phase-12-Code in dieser Session.
