# CLAUDE.md — Phase 13: Live-Datenfundament (`phase13_live_data/`)

> Zwei Fundament-Anläufe sind an derselben Stelle gestorben: **der Verbrauchspfad besorgt sich
> seine Daten selbst.** Phase 13 trennt Beschaffung und Verbrauch endgültig.
> **Quelle der Wahrheit ist der Plan + der Code, nicht dieses Dokument.**
> Vollständiger Plan: [`../docs/concepts/phase13_live_data_plan.md`](../docs/concepts/phase13_live_data_plan.md).
> Vorgeschichte: [`../phase12_data_foundation/PHASE12_5_CLOSEOUT_HANDOVER.md`](../phase12_data_foundation/PHASE12_5_CLOSEOUT_HANDOVER.md).

## Mission (zuerst lesen)

**Ein Konsument, der Daten braucht, die er nicht hat, bekommt einen typisierten Status — nie
einen Kauf.**

Beschaffung ist ein vierstufiges System, das nach Kosten und Latenz gestaffelt in *ein* Archiv
schreibt (`data/bars.sqlite`, Phase 12):

| Stufe | Quelle | Kosten | Latenz | Rolle |
|---|---|---|---|---|
| **S1** | IG Lightstreamer `CHART:{epic}:1MINUTE` (Fallback: Tick-Aggregation) | 0 | Echtzeit | der Schwanz — **dieselbe Preisreihe wie der Einstieg** |
| **S2** | yFinance-Recorder (existiert, läuft) | 0 | ~15 Min | der Rumpf — Backfill, Neustart, Off-Hours |
| **S3** | unabhängige Fremdquelle (Auswahl in Block C1) | 0 | Minuten–Stunden | Gegenprobe + Tiefen-Backfill |
| **S4** | IG REST `/prices` (Bereichs-API, gedrosselt) | gedeckelt | sofort | Rettung — gealterte Restlücken, **Default AUS** |

Verbrauch liest ausschließlich das Archiv. Die Frage lautet nicht mehr „ist das Archiv jetzt
aktuell?", sondern „**deckt das Archiv das Fenster genau dieses Trades dicht genug ab?**" —
über das **ganze** Fenster, mit Dichte- *und* Lückenschwelle.

**Done-Kriterium:** Beweiswoche gegen P1–P9 (Plan §7). Erste Akzeptanzbedingung ist eine
**strukturelle Kostenzusicherung**: der Tracker-Pfad läuft im Test gegen einen IG-Provider,
der bei jedem Call wirft.

## Bauprinzip

„So wenig AI wie möglich, so viel AI wie nötig." **Phase 13 fügt NULL neues AI hinzu.**
Lückenerkennung, Abdeckungsbewertung, Quellenwahl, Bar-Aggregation und Frische-Prüfung sind
deterministischer Code. Wer hier ein LLM „Lücken schätzen", „Quellen bewerten" oder „Bars
plausibilisieren" lassen will → **stop**, das ist Code.

## Scope

- **DRIN:** `live_data/` (Stream-Recorder, Backfill, Gap-Rescue, Reports), der Schnitt in
  `data_foundation/service.py`, `data_foundation/coverage.py` (neu), `sources`-Filter +
  `tick_count` in `data_foundation/archive.py`, die Sampler-/Heartbeat-Reparatur, das
  Kerzen-Abo in `phase1_broker_wrapper/broker_wrapper/streaming/`, die additive `window_ok`-Naht
  in `phase10_v3/abstain_lessons/paper.py`, Lebenszyklus + Flags in `phase8_scheduler/`.
- **DRAUSSEN:** WI-2/W2-Auswertung + H-Serie (Phase-11-Wiederaufnahme), Research-Funnel-Fix,
  der Research-Seam `BarService.get_bars` (L15 — erst nach Block B neu messen),
  `resolve_paper_trade` selbst (unangetastet, der Guard sitzt davor), Momentum-VETO/Gates/
  Sizing/P6/P7 (L13), B3-Margin-Headroom, Council-Paper-Call, UI, Live-Konto.

## Rahmen

**Welcher Befehl (Nikinger 2026-08-18, Kostengrund):**
**Ausführungs-Sessions laufen über `claude-minimax`** (Claude Code gegen MiniMax M3, Plan §6
Step A0.0). **Debugging-Sessions laufen weiterhin über `claude`.** Der normale Befehl bleibt
unangetastet — der Wechsel ist ein Wrapper-Skript, das nur die Umgebung seines eigenen
Kindprozesses setzt. ⚠️ Das ändert **nicht**, welches Modell der *Bot* benutzt: P4-Research,
P6-Debatte und die Lessons rufen unverändert Anthropic mit dem Key aus dem
`tradingbot`-Keyring-Namensraum.

**Übernommen aus Phase 12:**

- **Werktags-Arbeit erlaubt, auch bot-berührend.** Vorher den Bot stoppen,
  `ps aux | grep scheduler.run` als Gegenprobe (Parallel-Login-Falle). Danach gezielt neu starten.
- **Live-/Netz-/kostenpflichtige Läufe macht der Nikinger.** Befehl vorbereiten, Kosten nennen,
  vorher fragen.
- **Live-DB nur `mode=ro`.**
- **Cross-Phase-Edits sind für Phase 13 freigegeben** (Nikinger 2026-08-18).

## Modul-Tabelle

| Datei | Zweck | Status |
|---|---|---|
| *(Repo-Wurzel)* `scripts/store_minimax_key.py` · `scripts/claude-minimax` | Harness-Vorstufe: zweiter Claude-Code-Befehl auf MiniMax M3, Key nur im Keyring (`trading-bot-minimax`) | ⬜ Dateien geschrieben, Abnahme offen (Nikinger: Key seeden, symlinken, curl-Vorabtest, MiniMax-Verbrauchsanzeige) |
| `live_data/stream.py` | `LSBarRecorder` + `TickAggregator` (S1) | ⬜ Block B2 |
| `live_data/backfill.py` | `ExternalBackfill` (S3) | ⬜ Block C1 |
| `live_data/rescue.py` | `GapRescue` (S4, Default AUS) | ⬜ Block C2 |
| `scripts/probe_chart_stream.py` | Gating-Live-Check: liefert `CHART:` auf diesem Konto? | ⬜ Block B0 |
| `scripts/source_delta.py` | Doppelauflösung je Quelle, Differenz als Messgröße | ⬜ Block C3 |
| `tests/` | gemockt, kein Netz, kein LLM | ⬜ |
| *(cross-phase)* `data_foundation/coverage.py` | `assess_window` / `WindowCoverage` | ⬜ Block A1 |

---

## Session stopped — 2026-08-18 (Session 2: Block A0 — Baseline, Gerüst, A0.0-Dateien)

> **Auftrag:** Block A0 der Reihe nach abarbeiten (A0.0 Datei-Bau, A0.1 Ritual — bereits erledigt,
> A0.2 Baseline, A0.3 Gerüst, A0.4 Nummerierungs-Grep). Danach A1–A7 der Schnitt, streng in
> Reihenfolge (L4).

### Completed

1. **A0.0 — `scripts/store_minimax_key.py` + `scripts/claude-minimax` geschrieben**, Plan §6
   verbatim (Wrapper-Skript, Keyring-Namensraum `trading-bot-minimax`), `chmod +x` gesetzt.
   Fund am Sessionstart: der Commit `1ab208c` ("add Step A0.0") hatte im Commit-Text „Two files,
   both versioned in the repo" behauptet, aber nur die Plan-/CLAUDE.md-Dokumentation geändert —
   die Dateien existierten nicht (`find . -iname "*minimax*"` leer). Keine Code-Drift (die
   Modul-Tabelle stand korrekt auf ⬜), nur eine irreführende Commit-Message. Jetzt gebaut, alle
   vier Abnahmekriterien sind Operator-Schritte (Key seeden, `ln -s`, curl-Vorabtest, MiniMax-
   Verbrauchsanzeige) — **Abnahme bleibt beim Nikinger**, s. Next.
2. **A0.2 — Regression-Baseline, alle 13 Suiten separat** (`phase1_broker_wrapper/.venv`,
   je `pytest <phase>/tests -q`):

   | Phase | Ergebnis |
   |---|---|
   | phase1_broker_wrapper | 87 passed |
   | phase2_persistence | 77 passed |
   | phase3_external_data | 104 passed |
   | phase4_research | 155 passed |
   | phase5_execution | 173 passed |
   | phase6_debate | 76 passed |
   | phase7_reward | 138 passed |
   | phase8_scheduler | 237 passed, 1 warning (harmlose `httpx`-Deprecation) |
   | phase9_universe | 80 passed |
   | phase10_v3 | 160 passed |
   | phase12_data_foundation | 123 passed |
   | meta_m1_harness | 28 passed |
   | root `tests/` | 80 passed (Memory nannte 64 am 2026-07-02 — kein Regress, seither gewachsen) |

   Alle 13 grün — **echte Baseline, vor dem ersten Fix**, nicht nachträglich grün gezogen.
3. **A0.3 — Phasen-Gerüst** angelegt, Muster = `phase12_data_foundation` (Editable-Install,
   `own-connection`-Kommentarstil): `phase13_live_data/README.md`, `pyproject.toml`
   (`name = "live_data"`), `requirements.txt` (`pytest`), `live_data/__init__.py` (leer),
   `tests/__init__.py` (leer). `scripts/dev_install.sh` um P13 verlängert (Kette jetzt zwölf
   Pakete). `docs/INDEX.md` bekam drei neue Zeilen (`CLAUDE.md`, `README.md`,
   `SESSIONS_ARCHIVE.md`) im selben Commit.
4. **A0.4 — Nummerierungs-Grep** (`grep -rn "Phase 13 (V4)" --include="*.md" .`): 3 Treffer, alle
   in `ARCHITECTURE.md`, `ROADMAP.md` und diesem Plan selbst — jeder ist die datierte
   Korrekturnotiz, die die alte Bezeichnung als Zitat erklärt, keine lebende Referenz. Kein
   Nachbessern nötig.
5. **Rotation:** Session-1-Block verbatim nach
   [`SESSIONS_ARCHIVE.md`](./SESSIONS_ARCHIVE.md) verschoben, dieser Kopf trägt jetzt nur
   Session 2.

### Verified

- `python -c "import live_data"` läuft **nach** `pip install -e phase13_live_data --no-deps
  --no-build-isolation` (offline, kein Netzzugriff — dieselbe Form wie bei `data_foundation`).
  `pytest phase13_live_data/tests -q` → „no tests ran" (Verzeichnis ist leer, wie erwartet vor
  Block A1).
- `ps aux | grep scheduler.run` vor dem Test-Sweep: leer — kein Parallel-Login-Risiko, Sweep war
  gefahrlos.

### Next

- **Block A1** (Plan §6, Zeile 569): `phase12_data_foundation/data_foundation/coverage.py` neu —
  `assess_window` + `WindowCoverage`, reine Funktion, kein I/O. Danach A2 → A7 strikt der Reihe
  nach (L4).
- **A0.0-Abnahme ist Nikinger-Job**, nicht blockierend für A1: Key seeden
  (`phase1_broker_wrapper/.venv/bin/python scripts/store_minimax_key.py`), symlinken
  (`ln -s ~/trading-bot/scripts/claude-minimax ~/.local/bin/claude-minimax`), bare curl gegen den
  Endpunkt, dann ein echter `claude-minimax`-Lauf + MiniMax-Verbrauchsanzeige prüfen. Die drei
  offenen Live-Unbekannten (Basis-URL mit/ohne `/v1`, Bearer vs. `x-api-key`, exakte Modell-ID)
  lösen sich nur im Live-Test — dafür stehen die Env-Var-Overrides (`MINIMAX_BASE_URL`,
  `MINIMAX_MODEL`) im Wrapper.

### Note

- Root `CLAUDE.md`'s Phase-13 row still says "Bau nicht begonnen" — stale as of this session,
  left unchanged deliberately: the doc-hygiene rule routes phase-status updates to the phase
  head, not root.

### Open questions / blockers

- **Kein technischer Blocker für A1.** Bot steht weiterhin, Recorder sammelt kostenlos weiter.
- **Offen bis Block B0:** ob `CHART:{epic}:1MINUTE` auf diesem Konto liefert (Plan §9.2).
- **Offen bis Block C1:** welche Fremdquelle S3 wird.
- **`main` liegt jetzt 5 Commits vor `origin/main`** (inkl. dieser Session) — Push bleibt eine
  bewusste Einzelfreigabe des Nikinger.
