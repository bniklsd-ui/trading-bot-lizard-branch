# SESSIONS_ARCHIVE.md — Phase 13 (Live-Datenfundament)

Newest-first. Rotation rule (`CLAUDE.md` root, mandatory since 2026-07-06): the phase head
carries exactly one `## Session stopped` block; the previously-newest block moves here
verbatim when a new one is appended.

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
- **A0.0 seither live abgenommen (Nikinger, gleicher Tag, außerhalb dieser Session):** die drei
  Live-Unbekannten lösten sich wie folgt — Basis-URL `.../anthropic` (Claude Code hängt `/v1`
  selbst an), Header `x-api-key` funktioniert (Wrapper setzt `ANTHROPIC_AUTH_TOKEN`/Bearer, beide
  gingen durch), Modell-ID **`MiniMax-M3[1m]`** (nicht `MiniMax-M3` — die 1M-Kontext-Variante,
  Commit `9bf2f0f`). Erster curl-Versuch schlug mit `insufficient_balance_error (1008)` fehl —
  **kein Wiring-Fehler**, sondern der falsche Key-Typ: der zunächst gespeicherte Key war ein
  Pay-as-you-go-API-Key (leere Wallet), MiniMax trennt den vom **Subscription Key** des Token
   Plans (`platform.minimax.io/subscribe/token-plan`). Nach Tausch auf den Subscription Key: curl
   liefert eine echte Antwort, `claude-minimax` lief live, und **MiniMax' eigener
   „active day"-Zähler stieg von 1 auf 2** — der Anbieter-Beweis, nicht nur ein sauberer
   HTTP-Response. Modul-Tabelle jetzt ✅.

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

---

## Session stopped — 2026-08-18 (Session 1: Planungssession — Phase 13 eröffnet, Plan committet, kein Code)

> **Auftrag:** den execution-ready Plan für Phase 13 schreiben, nachdem P12.5 formal gescheitert
> ist. **Volles Ergebnis:**
> [`../docs/concepts/phase13_live_data_plan.md`](../docs/concepts/phase13_live_data_plan.md) —
> dieser Block ist die Kurzfassung. **Keine Code-Änderung in dieser Session.**

### Completed

1. **Vier Entscheidungen beim Nikinger eingeholt** (Closeout §4/§5/§6 verlangte genau das):
   Label = **Phase 13 = Live-Datenfundament, V4 → Phase 14** · Umfang = **mehrstufig, mit einer
   zusätzlichen Beschaffungsstufe** · LS-Prozess = **im Scheduler-Prozess** · Messregel =
   **beides messen, Differenz ist eine eigene Messgröße**.
2. **Plan geschrieben** — L1–L16 gelockt, Blöcke A/B/C, Verbatim-Anker je Edit-Stelle,
   Testliste, PASS-Kriterien P1–P9, §8 „Fehlgriffe, die wie andere Fehler aussehen",
   §9 vollständige Drift-Liste.
3. **Drei neue Befunde selbst nachgemessen** (Plan §4) — keiner stand in einem Vordokument:
   - **F1:** `IX.D.IBEX.FWM2.IP` trägt 301 IG-Bars mit `ts_utc` 2026-07-17, aber `fetched_at`
     **2026-08-18T11:10:17.019Z**. IG liefert für diese Forward-Epic seit einem Monat tote
     Historie und meldet `ok=True`. Sie hatte am 18.08. mit **8** IG-Calls die meisten von
     allen — und null verwertbare Bars. **Korrigiert den Closeout §7:** FWM2 ist nicht der
     „Existenzbeweis für yF-only", sondern der teuerste Blindgänger des Tages.
   - **F2:** `DivergenceSampler.sample_epic` (`heartbeat.py:184-193`) ankert das
     Vergleichsfenster am IG-Bar-Zeitstempel; ist der einen Monat alt, findet es keine yF-Bar
     und kehrt **still** zurück. Der Alarm ist gegen genau F1 strukturell blind. Beleg: **0**
     `quote_divergence`-Events bei **12** bezahlten Samples.
   - **F3:** Eine Lücke *mitten* im Trade-Fenster erzeugt in `resolve_paper_trade`
     (`paper.py:234-278`) eine **erfundene** `TIME_STOP`-Zeile, die in DB und Heartbeat nicht
     von einem echten Time-Stop unterscheidbar ist. Das ist die Begründung dafür, dass die
     Abdeckungsprüfung dem **ganzen** Fenster gilt, nicht dem Schwanz.
4. **Extern bestätigt:** IGs Streaming-Kanal läuft gegen ein **anderes** Kontingent (~40
   gleichzeitige Subscriptions je Verbindung), nicht gegen die 10 000 Historienpunkte/Woche;
   `CHART:{epic}:{scale}` existiert mit fertigen Kerzenfeldern (`OFR_*`, `BID_*`, `CONS_END`,
   `CONS_TICK_COUNT`). **Aber:** die Feldliste stammt aus Drittbibliotheken, labs.ig.com gab
   HTTP 403 — deshalb ist der CHART-Live-Check **Block B0** und gatet Block B.
5. **Step-0-Ritual (Turbo-/Legacy-Grep) ausgeführt — dokumentierter No-Op:** 3 Treffer, alle
   `strike` im Sinne von *Fehlversuch* (`phase9_universe/universe/promotion.py:121`, `:277`,
   `tests/test_promotion.py:343`), kein Options-Vokabular. `turbo_candidates` = 19 Treffer,
   der eingefrorene P5-Gate-2-Contract-Name — nicht umbenennen. Identisch zu den Ritualen vom
   2026-06-27 und 2026-07-10.
6. **Nummerierungs-Kaskade ausgeführt** (L16, derselbe Commit): Root-`CLAUDE.md`, `ROADMAP.md`
   (neuer Phase-13-Abschnitt + V4 → Phase 14), `README.md`, `ARCHITECTURE.md`, `docs/INDEX.md`,
   `phase9_universe/CLAUDE.md`, `phase10_v3/CLAUDE.md`. Historische Aussagen wurden **nicht**
   umgeschrieben, sondern mit datierten `⟳ Korrektur`-Notizen superseded.

### Verified

- `pytest phase12_data_foundation/tests -q` → **123 passed** · `pytest phase10_v3/tests -q` →
  **160 passed** (beide heute, 2026-08-18, geteiltes Venv `phase1_broker_wrapper/.venv`).
  **Alle übrigen Phasen-Zählstände sind ungeprüft** — Plan §9.8, Block A0.2 misst sie neu.
- Alle Zahlen in §4 des Plans stammen aus eigenen `mode=ro`-Abfragen gegen `data/bars.sqlite`,
  `data/trading_bot.sqlite` und `data/state/research_health.jsonl`, nicht aus Vordokumenten.
- Jeder Datei:Zeile-Anker im Plan wurde per Grep auf seinen Verbatim-String geprüft.

### Next

- **Block A0** (Plan §6): Regression-Baseline **aller** Phasen, Phasen-Gerüst
  (`README.md`, `pyproject.toml`, `requirements.txt`, `live_data/`, `tests/`,
  `scripts/dev_install.sh`-Kette). Der Phasen-Kopf (dieses File) existiert bereits.
- Danach **A1 → A7 strikt der Reihe nach.** Block A ist eine Löschung und macht einen sicheren
  Neustart möglich, **bevor** Block B gebaut ist — deshalb ist die Reihenfolge gelockt (L4).

### Open questions / blockers

- **Kein technischer Blocker.** Bot steht, Recorder sammelt weiter kostenlos.
- **Offen bis Block B0:** ob `CHART:{epic}:1MINUTE` auf diesem Konto überhaupt liefert
  (Plan §9.2). Beide Zweige sind ausgeplant — die ausführende Session stallt daran nicht.
- **Offen bis Block C1:** welche Fremdquelle S3 wird. Auswahlkriterien stehen im Plan (§6 C1),
  die Recherche lief parallel zu dieser Session.
- **`main` liegt 4 Commits vor `origin/main`** (Stand vor diesem Commit) — Push bleibt eine
  bewusste Einzelfreigabe des Nikinger.

---

## Session stopped — 2026-08-18 (Session 3: Block A1 — assess_window + WindowCoverage)

> **Auftrag:** Step A1 (Plan §6 A1, §5.1). Reine Funktion, kein I/O, kein Cross-Phase-Import.

### Completed

1. **`data_foundation/coverage.py` (NEU, 99 Zeilen)** — `WindowCoverage` (frozen dataclass:
   `covered`, `present`, `expected`, `ratio`, `largest_gap_min`, `reason`) und
   `assess_window(timestamps, start_utc, end_utc, resolution_minutes, *, min_ratio, max_gap_min)`
   strikt nach §5.1-Signatur. Reason-Priorität `empty > gap > sparse` (§5.1).
   Konstanten `MIN_WINDOW_RATIO=0.90` / `MAX_WINDOW_GAP_MIN=5` sind die gelockten v1-Knöpfe
   (Plan §9.14: Block A misst die reale Verteilung, justiert danach). `_parse` aus
   `archive.py:222-227` **lokal** dupliziert (Phasen-Isolation, Plan §6 A1). Ränder fließen in
   die Gap-Rechnung ein — sonst wären Tests 4/5 (Loch am Fensteranfang/-ende) blind.
2. **`tests/test_coverage.py` (NEU, 12 Tests)** — die 9 Pflicht-Tests aus §6 A1 wortgleich:
   volles Fenster, leer, **Mitten-Loch** (F3-Fang, ratio > min_ratio trotzdem reason='gap'),
   Rand-Lücken, gleichmäßig dünn, `gap` > `sparse`, `expected==0` ohne `ZeroDivisionError`,
   Duplikate zählen einmal. Plus 3 defensive: Timestamps außerhalb des Fensters ignoriert,
   Defaults halten die Modul-Konstanten, `WindowCoverage` ist `frozen`.
3. **`phase12_data_foundation/README.md`** — Modul-Tabelle um `coverage.py` ergänzt (Verweis auf
   Phase 13 §6 A1). Sonst nichts geändert.
4. **Rotation:** Session-2-Block verbatim nach `SESSIONS_ARCHIVE.md` verschoben.

### Verified

- `pytest phase12_data_foundation/tests -q` → **135 passed** (Baseline 123 + 12 hinzu, 0 Regressionen).
  Phase-12-Suite allein, geteiltes Venv `phase1_broker_wrapper/.venv`.
- Akzeptanz A1 wortgleich erfüllt: *"die neun Tests grün; `assess_window` hat null Aufrufer"*.
- `grep -n "_covers_tail\|MIN_WINDOW_COVERAGE\|_ig_provider" phase12_data_foundation/`: alle drei
  noch vorhanden — A1 fasst sie nicht an, **A2** löscht sie (L2).
- `assess_window` hat 0 Produktions-Aufrufer (gegrept); Verdrahtung kommt in A2
  (`BarService.get_window`-Body-Ersatz) und A3 (Tracker-Naht in `paper.py`).

### Next

- **Step A2** (Plan §6, Zeile 604): `BarService.get_window` zu einer reinen Archiv-Lesung kürzen
  (Verbatim-Anker-Tabelle in §6 A2 prüfen, Zeilen können sich verschoben haben). L12-Test
  `test_get_window_never_fetches` (IG-Provider wirft `AssertionError`) ist die **strukturelle
  Kostenzusicherung** — der Kernpunkt von L12. **Pause für Nikinger-Bestätigung** vor Cross-
  Phase-Edits in A3 (das ist die nächste Stufe, die `paper.py` und `wiring.py` berührt).

### Note

- Netto-Diff: +2 neue Dateien + 1 README-Zeile + 1 Session-Block-Tausch. Kein Eingriff in
  laufende Komponenten. `data_foundation` ist cross-phase-Paket (Phase 12), `live_data`
  importiert es (L11) — der neue Modul liegt also **in** Phase 12, **benutzt von** Phase 13.
- Die zwei bisherigen Live-Unbekannten aus A0.0 sind gelöst (Modell-ID `MiniMax-M3[1m]`,
  Bearer-Header, Subscription-Key-Tausch), siehe Session-2-Block.

### Open questions / blockers

- **Kein technischer Blocker für A2.** Bot steht sicher, Recorder sammelt kostenlos weiter.
- **A2 ist der Lösch-Step** (L2): danach kauft der Tracker-Pfad **per Konstruktion** keine
  IG-Punkte mehr — der strukturelle Schnitt, den Closeout §1 empfohlen hat. Genau da, **nicht
  jetzt**, ist der Moment, das mit dem Nikinger kurz zu bestätigen, bevor A3 (die Cross-
  Phase-Naht) anläuft.
- **`main` liegt jetzt 6 Commits vor `origin/main`** (inkl. dieses Commits) — Push bleibt
  bewusste Einzelfreigabe des Nikinger.
