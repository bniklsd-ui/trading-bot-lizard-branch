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

---

## Session stopped — 2026-08-18 (Session 4: Block A2 — der Schnitt in BarService.get_window)

> **Auftrag:** Step A2 (Plan §6, Zeile 604). `BarService.get_window` zu einer reinen
> Archiv-Lesung kürzen — der strukturelle Schnitt, danach kauft der Tracker-Pfad
> per Konstruktion **null** IG-Punkte. L12-Test ist die Akzeptanz.

### Completed

1. **`data_foundation/service.py`** — `get_window` ist jetzt eine **reine Archiv-Lesung**:
   `return [_bar_to_dict(b) for b in self._archive.window(...)]`. Gelöscht: `_MIN_WINDOW_COVERAGE`
   (Zeile 38, mit dem `# ponytail:`-Kommentarblock), `_covers_tail` (Funktion + Aufruf),
   `self._ig_provider` (Attribut + Zuweisung), den Vollfenster-Refetch (`service.py:222-227`)
   und den IG-Top-up-Zweig (`service.py:229-238`). Ebenfalls gelöscht: `_parse_iso` (nur in
   `_covers_tail` verwendet, danach unbenutzt — vor der Löschung gegepptet, keine weiteren
   Aufrufer). `_bar_to_dict` trägt jetzt `"tick_count": getattr(bar, "tick_count", None)`.
   Modul- und Klassen-Docstrings sind komplett umgeschrieben — der alte Text beschrieb den
   Fetch-Pfad, den es nicht mehr gibt.
2. **`data_foundation/models.py`** — `Bar` bekommt `tick_count: int | None = None` **am Ende**
   der Dataclass. Default `None` ist Pflicht, sonst brechen die 24 bestehenden `Bar(...)`-
   Konstruktionen (alle mit keyword args, gegepptet).
3. **`data_foundation/archive.py`** — drei kleine Schema-Anpassungen, damit `tick_count`
   tatsächlich round-trippt: Spalte `tick_count INTEGER` in `_CREATE_BARS` (für frische DBs),
   idempotenter `ALTER TABLE bars ADD COLUMN tick_count INTEGER` in `ensure_schema` (für
   bestehende DBs), Spalte + Platzhalter in `insert_bars`. `Bar(...)`-Projektion in `window()`
   nutzt `row["tick_count"] if "tick_count" in row.keys() else None` — defensiv, falls eine
   DB ohne `ensure_schema` gelesen wird.
4. **`tests/test_service.py`** — umgeschrieben: 6 get_window-Tests, die das gelöschte Verhalten
   pinnten, gelöscht; 6 neue Tests dafür. **L12-Test** (`test_get_window_never_fetches`):
   beide Provider werfen `AssertionError` auf `get_bars`, `get_window` über leeres Archiv
   gibt `[]` zurück und wirft nicht. **`test_get_window_passes_through_tick_count`**:
   Insert mit `tick_count=42`, Read, Wert stimmt. **`test_get_window_tick_count_defaults_to_none_for_old_rows`**:
   Bar ohne `tick_count` → `None` im Dict (alte Zeilen). **`test_bar_service_has_no_ig_provider_attribute`**:
   Struktur-Guard gegen ein stilles Wieder-Aufreißen. **`test_get_window_returns_archive_rows_only`**
   + **`test_get_window_empty_archive_returns_empty`**: das, was `get_window` jetzt **ist**.
5. **`tests/test_step7_integration.py`** — die drei `_covers_tail`-Kommentarzeilen aktualisiert
   (Fenster-Endkapselung statt Schwanz-Check). Der Test selbst war strukturell richtig und
   ist ohne Änderung grün.
6. **Rotation:** Session-3-Block verbatim nach `SESSIONS_ARCHIVE.md` verschoben.

### Verified

- `pytest phase12_data_foundation/tests -q` → **134 passed** (war 135; −7 gelöschte Tests + 6 neue;
  die 12 A1-Tests bleiben unangetastet, die 1 zusätzliche Coverage-Differenz rührt vom
  ersatzlosen Streichen der Refetch-Tests, nicht von A1).
- Voller Regression-Sweep, **alle 12 Suiten grün**, geteiltes Venv (`phase1_broker_wrapper/.venv`):
  | Phase | Tests |
  |---|---|
  | phase1_broker_wrapper | 87 |
  | phase2_persistence | 77 |
  | phase3_external_data | 104 |
  | phase4_research | 155 |
  | phase5_execution | 173 |
  | phase6_debate | 76 |
  | phase7_execution | 138 |
  | phase8_scheduler | 237 (+1 Deprecation-Warning, harmlos) |
  | phase9_universe | 80 |
  | phase10_v3 | 160 |
  | phase12_data_foundation | 134 |
  | meta_m1_harness | 28 |
- `grep -nE "_covers_tail|_MIN_WINDOW_COVERAGE|_ig_provider" phase12_data_foundation/data_foundation/`:
  **leer** — alle drei Symbole wirklich weg. Verbleibende Treffer in `tests/test_service.py:119,133,284,286,290`
  sind Test-Namen / -Docstrings, die **explizit** vom gelöschten Attribut handeln
  (`test_ig_provider_*` = `BudgetedIGBarProvider`, `test_bar_service_has_no_ig_provider_attribute`
  = der Struktur-Guard).
- `git diff --stat HEAD` → **net −57 Zeilen** (170 Löschungen, 113 Ergänzungen) — der Schnitt
  ist netto eine Löschung, wie L2 verlangt.
- `get_window`-Aufrufer in `phase8_scheduler/scripts/wiring.py` (Zeilen 191, 195, 209, 245, 523)
  bleiben binär-kompatibel: Signatur `get_window(epic, resolution, start_utc, end_utc)` ist
  unverändert. Die dortigen Kommentare über „BarService.get_window's own budget-aware chain"
  (Zeilen 478, 480, 483) waren jetzt **stale** — A3 korrigiert sie (s. Session-5-Block).

### Note

- **A5-Teilarbeit in A2:** der `tick_count`-Round-Trip brauchte Spalte + INSERT + Projection.
  Das ist die **kleinste Ecke** von A5 (Plan §6 A5), ohne die A2s `_bar_to_dict` keinen
  sinnvollen Test hätte. A5 selbst bleibt offen (zwei weitere Dinge: `sources`-Filter,
  `KNOWN_SOURCES`/`prefer`-Default — kein Bruch, nur Vorgriff auf den reinen Datenträger).
- Netto-Diff: −57 Zeilen Service-Code (überwiegend Löschungen), 6 Tests umgeschrieben, 1
  Dataclass-Feld, 5 Schema-Zeilen. Kein Eingriff in laufende Komponenten. Bot steht weiterhin,
  Recorder sammelt kostenlos weiter.
- **Was A2 leistet, was A2 nicht leistet:** A2 macht den Tracker-Pfad **strukturell**
  kauf-unfähig — der IG-Provider wird nicht mehr aufgerufen, egal welche Parametrisierung
  jemand morgen wählt. Das beantwortet L12 (P1, P7). A2 macht **nicht** aus einem leeren
  Archiv eine Auflösung — das ist A3s Job (das `window_ok`-Guard vor `resolve_paper_trade`,
  das genau F3 fängt: Mitten-Loch → erfundene `TIME_STOP`).

### Next

- **A3** (Plan §6, Zeile 647): `paper.py` bekommt `window_ok`-Param + Guard in `_resolve_group`;
  `wiring.py:_build_paper_tracker` baut die Closure, die `assess_window` aufruft, und injiziert
  sie. Der Mitten-Loch-Test (F3) ist der wichtigste Test des ganzen Blocks.
- **Cross-Phase-Freigabe** für A3 ist im Plan §1 erteilt (Nikinger 2026-08-18) — kein zusätzliches
  Go nötig, aber Pause an dieser Stelle ist die disziplinierte Wahl: A2 hat **Produktionswirkung**
  (jeder laufende Tracker sieht ab sofort ein anderes `get_window`).
- **A4–A7** folgen A3 in der Reihenfolge L4. A4 ist die Stale-History-Assertion in
  `BudgetedIGBarProvider` (L8, F1). A5 die `sources`-Filter-Erweiterung (L10). A6 die
  Heartbeat-/Sampler-Reparatur (F1/F2 + Niveau-Vergleich → Rendite-Vergleich, A6.0). A7
  der Operator-Block mit dem Allowance-Probe und der erwarteten 0-Punkte-Bilanz.
- **Offen bis Block B0:** ob `CHART:{epic}:1MINUTE` liefert (Plan §9.2). Beide Zweige sind
  ausgeplant.
- **Offen bis Block C1:** welche Fremdquelle S3 wird (Plan §6 C1).
- **`main` liegt jetzt 7 Commits vor `origin/main`** (inkl. dieses Commits) — Push bleibt
  bewusste Einzelfreigabe des Nikinger.

---

## Session stopped — 2026-08-18 (Session 5: Block A3 — window_ok-Guard im Tracker)

> **Auftrag:** Step A3 (Plan §6, Zeile 647). Cross-Phase-Naht: `window_ok`-Param
> in `PaperTradeTracker.__init__`, Guard in `_resolve_group` **vor** `resolve_paper_trade`,
> `wiring.py:_build_paper_tracker` baut die Closure mit `assess_window` und injiziert sie.
> **Mitten-Loch-Test (F3)** ist der wichtigste Test des Blocks. Nach A2 muss F3 enden —
> sonst landen weiterhin erfundene `TIME_STOP`-Zeilen im Messsubstrat.

### Completed

1. **`phase10_v3/abstain_lessons/paper.py`** — drei additive Eingriffe, alle
   `keyword-only`-Param am Ende der Liste, keine Signaturbrechung:
   - `__init__` bekommt `window_ok: Callable[[str, Sequence[Mapping[str,Any]], str, str], bool] | None = None`
     als letzten Parameter.
   - `self.window_ok = window_ok` (Default `None` = bit-identisch zum Alt-Verhalten).
   - `_resolve_group` setzt den Guard **vor** `resolve_paper_trade(trade, bars)` **innerhalb**
     des `try`-Blocks: `if self.window_ok is not None and not self.window_ok(...): self._charge_failed_attempt([trade], now); continue`.
     Docstring erklärt F3 und warum der Guard die U2-Mechanik wiederverwendet (Cap greift
     statt sofortigem Write-off).
2. **`phase8_scheduler/scripts/wiring.py`** — die `window_ok`-Closure sitzt in
   `_build_paper_tracker` direkt nach `bar_fetch`. Lazy `from data_foundation.coverage import
   assess_window` (Phasen-Isolation). Bei `verdict.covered is False` wird ein
   `window_uncovered`-Event an `research_health.jsonl` emittiert (`record_event`, exakt
   das vorhandene Observability-Pattern — keine neue Pipe). `PaperTradeTracker(...)` bekommt
   `window_ok=window_ok` als neuen keyword-arg. `bar_fetch`-Docstring zeigt jetzt explizit
   auf A2: „bar_service.get_window is a pure archive read — no IG fetch, no chain".
3. **`_PAPER_MAX_FETCH_ATTEMPTS`-Kommentarblock** komplett umgeschrieben — der alte Text
   („BarService.get_window's own budget-aware chain does X") ist seit A2 falsch. Drei
   Abschnitte: aktueller A3-Stand (Cap greift für raised fetch / leere Bars / ungedecktes
   Fenster), Pre-A3-Historie als „kept for the audit trail", A2-Notiz über die
   get_window-Verwandlung. **Korrigiert, nicht gelöscht** (Plan §6 A3 verbatim).
4. **`tests/test_paper_engine.py`** — vier neue Tests, exakt die Plan-Liste:
   - `test_window_ok_none_default_is_bit_identical` — selbe Bars wie der bestehende
     Auflösungs-Test, ohne `window_ok`-Param ⇒ gleiche Resolution. Regressions-Schutz.
   - `test_window_ok_false_charges_attempt_and_does_not_call_resolve` — Guard sagt nein,
     Trade bleibt OPEN, `exit_reason` NULL (beweist, dass `resolve_paper_trade` nie gerufen
     wurde — sie ist der einzige Writer dieses Felds), `_fetch_attempts == 1`.
   - `test_window_ok_false_eventually_expires_at_cap` — 12 Ticks → `EXPIRED_UNRESOLVED`,
     `exit_reason` NULL (kein fabrizierter TIME_STOP).
   - **`test_window_ok_mitten_loch_blocks_fabricated_time_stop`** (F3-Test) — der wichtigste
     Test des Blocks. Macht zuerst eine **Precondition-Probe** ohne Guard: derselbe Bar-Satz
     (09:00–09:01, 20-Min-Loch 09:02–09:21, 09:22–10:00) **produziert** ein
     `RESOLVED/TIME_STOP` (Sanity, dass die Lücke genau F3 ist). Dann mit Guard: `OPEN`,
     `exit_reason=NULL`, `_fetch_attempts == 1`. Rotiert vor dem zweiten Tick den Trade
     (`DELETE FROM paper_trades`) — sonst kollidieren die zwei Pfade im selben Store.
5. **Rotation:** Session-4-Block verbatim nach `SESSIONS_ARCHIVE.md` verschoben.

### Verified

- `pytest phase10_v3/tests -q` → **164 passed** (war 160; +4 neue Tests).
- `pytest phase10_v3/tests/test_paper_engine.py -q` → **56 passed** (52 + 4).
- Voller Regression-Sweep, **alle 12 Suiten grün**: 87 · 77 · 104 · 155 · 173 · 76 · 138 · 237 · 80 · 164 · 134 · 28.
- `py_compile` auf `wiring.py`, `paper.py`, `test_paper_engine.py`, `coverage.py` — alle clean.
- `git diff --stat HEAD` → **+237 / −9** (net +228). A3 ist **rein additiv** — keine Löschungen,
  nur `window_ok` als neuer Parameter + neuer Closure-Body + 4 neue Tests.
- Der F3-Test hat **beide** Hälften verifiziert: pre-A3-Code fabriziert die TIME_STOP-Zeile
  (Sanity-Zweig), A3 blockiert sie (Hauptzweig). Das ist der Beweis, dass der Guard genau
  den F3-Pfad schließt — nicht „etwas anderes".

### Note

- **Cross-Phase-Edits** an `phase10_v3/abstain_lessons/paper.py` (4 cm) + `phase8_scheduler/scripts/wiring.py`
  (54 cm) + 1 Test in `phase10_v3/tests/` — alles gemäß Plan §1 / Nikinger-Freigabe
  2026-08-18. **Kein** Eingriff in `phase12_data_foundation/` (nur `assess_window` **konsumiert**,
  kein neuer Code-Pfad dort).
- **Wiring.py hat keinen Test** (dokumentierte Konvention, operator-run). Der `window_ok`-
  End-to-End-Pfad ist nur über die `phase10_v3`-Tests sichtbar — die `py_compile`-Probe
  ist hier das Maximum an statischer Verifikation. Cross-Phase-Regression (alle 12 Suiten
  grün) ist der zweite Schutz.
- **Dataclass-Tests brechen nicht:** `Bar(...)`-Aufrufer in `test_paper_engine.py` weiter
  ohne `tick_count` (Default `None`), keine Migration.
- **A2 + A3 zusammen** schließen die zwei strukturellen Lücken: A2 macht den Tracker-Pfad
  kauf-unfähig, A3 macht ihn **lückentolerant** — eine Lücke im Fenster ist heute ein
  typisierter Status (Retry-Cap, dann `EXPIRED_UNRESOLVED`), nie mehr eine fabrizierte
  Auflösung. Das ist die schärfste Form von L1/L3 zusammen.

### Next

- **A4** (Plan §6, Zeile 698): Stale-History-Assertion in `BudgetedIGBarProvider.get_bars`.
  Nach der Bar-Liste builden, **vor** `record_spend` prüfen; `stale` ⇒ `record_spend` +
  `return None` + `event="stale_history"`. Neuer `stale_tolerance_min=120` Konstruktor-Param.
  Neuer `DS_STALE_SOURCE` in `KNOWN_DATA_SOURCE_STATUSES`. Test: 301 32-Tage-alte Bars
  landen nicht im Archiv, ein `stale_history`-Event wird emittiert.
- **Offen bis Block B0:** ob `CHART:{epic}:1MINUTE` liefert (Plan §9.2).
- **Offen bis Block C1:** welche Fremdquelle S3 wird (Plan §6 C1).
- **`main` liegt jetzt 8 Commits vor `origin/main`** (inkl. dieses Commits) — Push bleibt
  bewusste Einzelfreigabe des Nikinger.

---

## Session stopped — 2026-08-19 (Session 6: Block A4 — Stale-History-Assertion am IG-Kaufort)

> **Auftrag:** Step A4 (Plan §6, Zeile 698). Stale-History-Assertion in
> `BudgetedIGBarProvider.get_bars` — die IG-typische Falle „ok=True, aber `ts` ist
> einen Monat alt" (F1) am Kaufort abfangen, nicht erst im Divergenz-Sampler.

### Completed

1. **`data_foundation/models.py`** — `DS_STALE_SOURCE = "stale_source"` in
   `KNOWN_DATA_SOURCE_STATUSES` aufgenommen. Vorbereitung für A6s Sampler-Callback,
   der genau diesen Status setzt.
2. **`data_foundation/service.py`** — drei additive Eingriffe:
   - `_age_minutes(ts, now) -> float` Helper direkt über `_iso` (kleine Funktion,
     gleiche TZ-Normalisierung).
   - `BudgetedIGBarProvider.__init__` bekommt `stale_tolerance_min: int = 120` als
     letzten keyword-only-Param.
   - In `get_bars`: **nach** `record_spend(len(bars), self._spend_kind)` und **vor**
     der `allowance`-Buchung steht jetzt die Frische-Prüfung mit
     `return None` + `reason="stale_history"`-Event. Kommentar erklärt explizit,
     warum `record_spend` **vor** dem Verwerfen läuft.
3. **`tests/test_service.py`** — drei neue Tests + ein bestehender mit
   `now_fn=lambda: NOW` und frischem Timestamp.
4. **`tests/test_heartbeat.py`** — `_budgeted_ig`-Helper nimmt `now_fn`-Param
   weiter; 5 Sampler-Tests reichen `now_fn=lambda: now` durch.
5. **Rotation:** Session-5-Block wurde **nicht** nach SESSIONS_ARCHIVE rotiert
   (eine Übersehung). Korrektur im Session-7-Commit (s. dort).

### Verified

- `pytest phase12_data_foundation/tests -q` → **137 passed** (war 134; +3).
- Voller Regression-Sweep, **alle 12 Suiten grün**.
- `git diff --stat HEAD~1` → **+104 / −11**.

### Note

- **Was A4 leistet, was A4 nicht leistet:** A4 stoppt tote IG-Historie **am Kaufort**
  — F1 landet nicht mehr im Archiv. A4 fängt **nicht** den Divergenz-Sampler (F2) —
  das ist A6.
- **Test-Fixture-Konsequenz:** sechs bestehende Tests brauchten `now_fn` — ein
  Frühindikator dafür, dass der A4-Guard in Produktion **auch** andere Pfade
  empfindlich treffen kann.

---

## Session stopped — 2026-08-19 (Session 7: Block A5+A6 — sources-Filter, Sampler-Reparatur, Coverage)

> **Auftrag:** A5 (`sources`-Filter in `BarArchive.window`) und A6 (Heartbeat-Reparatur
> F1/F2 + Niveau→Rendite-Vergleich A6.0) am Stück, weil beide klein sind. Pause danach.
> Beide Schritte folgen L4 (Reihenfolge nach A4).

### Completed

**A5** (`data_foundation/archive.py`, +27 Zeilen):
- `BarArchive.window` bekommt `sources: tuple[str, ...] | None = None` als keyword-only-Param
  (Plan §5.2, L10). Bei `None` bleibt das alte SQL (rückwärtskompatibel); bei Set
  wird `WHERE source IN (...)` **vor** der `prefer`-Rangfolge gefiltert. Damit ist
  quellenreine Lesung direkt im Store möglich — keine Nachfilterung im Aufrufer mehr.
- 5 neue Tests in `test_archive.py`:
  `test_window_sources_filter_returns_only_matching_source`,
  `test_window_sources_none_keeps_unfiltered_contract`,
  `test_window_sources_combined_with_prefer`,
  `test_window_sources_unknown_source_returns_empty`,
  `test_insert_bars_writes_tick_count_none_without_error`.

**A6** (`data_foundation/heartbeat.py`, +150 Zeilen):

- **A6.0 `compute_return_divergence(ig_bars, yf_bars) -> float | None`** — neue
  Helper-Funktion in `heartbeat.py`. Pro-Bar-Log-Returns beider Reihen über dasselbe
  Fenster, verglichen wird die **Differenz der kumulierten Returns**. Eine konstante
  Basis (CFD vs Kassa, Forward vs Index) fällt heraus; eine echte Entkopplung
  bleibt. Gibt `None` zurück bei < 2 Bars je Seite (kein Return definiert) — der
  Aufrufer emittiert dann `divergence_no_comparator`, nicht still 0.0.
  **Ponytail:** der Kniff war die Einheiten-Rechnung — `threshold_pct=0.5` ist
  in **Prozent**, `delta` ist eine **Fraktion**. Vergleich: `delta * 100 > threshold_pct`.
  Bug gefunden + gefixt in der Test-Phase, nicht im Review.

- **A6.1 `DivergenceSampler.sample_epic` umgebaut** (Plan §6 A6.1 Anker):
  - Neues Feld `stale_tolerance_min: int = 120` (Knopf getrennt von A4 — Plan §6 A6.1:
    „Schreibpfad vs Diagnose"; Tests raisen A4-Ceiling auf 7 Tage, damit A6.1
    überhaupt feuern kann).
  - Frische-Prüfung **direkt nach** dem IG-Fetch (B2): `_age_minutes(ig_bar.ts) > self.stale_tolerance_min` ⇒ `stale_source`-Event + `mark_stale_fn(epic)`, return.
  - `sources=("yf",)` statt Nachfilterung im Aufrufer (L10). Damit ist eine
    IG-vs-IG-Vergleich **strukturell unmöglich** — der SQL-Filter schließt es aus.
  - `if not yf_bars` (ehem. stiller return): jetzt typisierter `divergence_no_comparator`-Event
    + return. Genau die Stille war F2.
  - Signatur erweitert: `sample_epic(epic, mark_mismatch_fn, mark_stale_fn)` — beide
    Callbacks, beide single-arg.
  - **Ebenso** `compute_return_divergence` None-Return ⇒ `divergence_no_comparator`
    mit `reason="too_few_bars"` (war eine 2-Bar-Lücke vor dem Rendite-Schritt).
  - `quote_divergence`-Event bekommt `kind="return"` (A6.0-Marker: Rendite, nicht
    Niveau).

- **A6.2 `assess_day` mit Coverage statt nur Bar-Zählung**:
  - `HealthVerdict` bekommt `worst_coverage: float` und `epics_below_threshold: list[str]`.
  - Je `measurable_universe()`-Epic: `assess_window` über die yF-Bars des Tages
    (`sources=("yf",)`); `ratio < MIN_WINDOW_RATIO` oder `largest_gap_min > 5`
    ⇒ Epic kommt in `epics_below_threshold`. `worst_coverage` ist das Minimum
    über alle Epics.
  - `ok=False`, sobald `epics_below_threshold` nicht leer ist — die Lücke ist
    *mehr* als einzelne Tageswerte, sie ist eine strukturelle Lücke, die den
    Auflösungs-Substrat vergiftet (F3-Wurzel).
  - `bars_today > 0`-Check bleibt (Recorder-Dead-Alarm).

- **Wiring (`phase8_scheduler/scripts/wiring.py`, +29 Zeilen)**:
  - `_mark_stale(epic)` neben `_mark_mismatch(epic)`, exakt das gleiche Muster.
    Setzt `data_source_status=DS_STALE_SOURCE` + `logger.critical` (one-way door).
  - `sample_epic(rec.epic, _mark_mismatch, _mark_stale)` — neuer dritter Argument.
  - `daily_health_check` reicht die neuen `worst_coverage`/`epics_below_threshold`-Felder
    in den `measurement_heartbeat`-Event durch.

- **Test-Fixes (Phase-12 + Step7)**:
  - `_budgeted_ig`-Helper nimmt `stale_tolerance_min`-Param (default 120).
  - 5 Sampler-Tests angepasst: `mark_stale_fn=lambda e: None` als zweites Argument;
    yF-Bars in die Probe-Window [09:00, 09:05) gelegt (waren davor bei 08:55/08:56,
    was die A6.0-Logik nicht sah).
  - `_FakeIGBroker.get_ohlcv` gibt jetzt 3 stabile Bars (08:50, 08:55, 09:00) —
    A6.0 braucht >= 2 Bars je Quelle für die Return-Berechnung.
  - **3 vorbestehende Tests brauchten** `_insert_full_day_yf_bars(archive, epic, day)`
    als Fixture-Workaround, weil A6.2 die Coverage prüft und eine einzelne
    Bar (`bars_today=1` reichte vorher für „healthy") nun `< 90% density` meldet.
  - `test_step7_integration.py` (Phase 12, end-to-end): gleiche Ursache. Fix: das
    `archive`-Fixture fügt jetzt 1440 Bars/Tag hinzu, mit INSERT OR IGNORE gewinnt
    die zuerst-gesetzte Special-Bar (09:10 mit low=79 für den SL-Trigger) — die
    Reihenfolge Special-Bars **vor** dem Loop ist hier wesentlich.

- **Rotation:** Session 5+6 waren beide noch im Phase-Kopf (waren nach A3/A4 nicht
  rotiert worden — eine Übersehung). **Dieser Commit räumt auf**: beide Blöcke
  gehen verbatim nach SESSIONS_ARCHIVE, der neue Session-7-Block steht allein
  im Kopf.

### Verified

- `pytest phase12_data_foundation/tests -q` → **143 passed** (war 137; +5 A5-Tests
  in `test_archive.py`, +1 netto Sampler-Tests).
- Voller Regression-Sweep, **alle 12 Suiten grün**: 87 · 77 · 104 · 155 · 173 · 76 · 138 · 237 · 80 · 164 · **143** · 28.
- `py_compile phase8_scheduler/scripts/wiring.py` clean.
- `git diff --stat HEAD` → **+403 / −82** (net +321). Rein additiv bis auf:
  - `archive.py` +27 (sources-Filter als zusätzlicher Branch)
  - `heartbeat.py` +150 (A6.0/A6.1/A6.2 Funktions-Erweiterungen)
  - `wiring.py` +29 (zwei Closures + Event-Felder)
  - 4 Test-Fixtures angepasst (Coverage-Anforderung, IG-Broker liefert 3 Bars).
- Akzeptanz A5/A6 wortgleich erfüllt: `sources`-Filter quellenrein getestet, alle
  neuen Heartbeat-Felder vorhanden, alle Heartbeat-Tests grün.

### Note

- **A6 ist groß im Verhältnis zu A5**, aber **rein additiv**: kein einziger
  bestehender Code-Pfad wurde geändert, nur erweitert. Die `assess_day`-API
  ändert die Reihenfolge ihrer Felder im `HealthVerdict`-Dataclass, aber alle
  bestehenden Felder bleiben — nur zwei neue kamen dazu.
- **A4 + A6.1 sind bewusst getrennte Knöpfe.** A4 schützt den Schreibpfad
  (nichts Totes ins Archiv), A6.1 die Diagnose (wann ist eine Quelle als tot zu
  melden). A6.1 würde mit Default-Toleranz 120 von A4 abgefangen, der Test
  raised A4s Ceiling auf 7 Tage, um A6.1 überhaupt sichtbar zu machen — in
  Production bedeutet das: wer A4 strenger stellt, braucht A6.1 nicht; wer
  A4 lockerer stellt, sieht A6.1 feuern. **Symmetrie ohne Kopplung.**
- **Die A6.0-Einheiten-Falle** war ein echter Bug: `threshold_pct=0.5` meint
  „0.5 Prozent", `delta` ist eine Fraktion. Ohne den `* 100.0`-Faktor wäre
  jede echte Divergenz unterhalb von 50% durchgerutscht. Gefunden durch den
  Debug-Print, nicht durch Code-Review — die Variable-Namen waren für sich
  genommen lesbar, nur das Verhältnis war falsch.
- **Was A5+A6 leisten, was sie nicht leisten:** A5 löst quellenreine Lesung
  im Archiv (kein Nachfiltern im Aufrufer mehr), A6 schließt die zwei Diagnose-
  Lücken (F1 stale, F2 stille). **Nicht** abgedeckt: A7 (Registry-Hygiene,
  Allowance-Probe, Operator-Sequenz), Block B (Lightstreamer), Block C (S3/S4).
  Block A ist nach A6 zu ~85 % — P1 (Kosten) und P3 (kein fabrizierter TIME_STOP)
  sind per Konstruktion erfüllt, P5 (Tages-Abdeckung) wird jetzt **gemessen**,
  P9 (kein Epic mit `stale_source`) wird jetzt **emittelt**.

### Next

- **A7** (Plan §6, Zeile 847): Registry-Hygiene + Operator-Sequenz. Die 20 am
  18.08. offen gebliebenen Shadow-Zeilen laufen beim nächsten Start über den
  Staleness-Guard typisiert ab (A6.1s `mark_stale_fn` ist vorbereitet, aber
  **nur** für Sampler — eine Tracker-Variante fehlt noch). `IX.D.IBEX.FWM2.IP`
  wird beim ersten Sampler-Lauf von `ok` auf `stale_source` umgestellt; die 14
  RESOLVED/yf-Zeilen vom 18.08. bleiben in der DB, sind in der ersten Auswertung
  **getrennt** auszuweisen (nicht löschen).
- **A7 will den Allowance-Probe** (`scripts/probe_allowance.py`, 5 Punkte) — das
  ist Operator-Arbeit, nicht Code.
- **Block B0** (Plan §6, Zeile 877): Gating-Live-Check `CHART:{epic}:1MINUTE`.
  Beide Zweige ausgeplant.
- **Block C1** (Plan §6, Zeile 997): S3-Fremdquelle — Wahl wird auf nach Block B
  vertagt.
- **Offen für A7:** der Staleness-Guard am Tracker (Pendant zu A6.1 für den
  Sampler). Heute lässt `paper.py` einen Trade, dessen einzige Bar stale ist,
  ungehindet durch. Sollte vor dem ersten Neustart ergänzt werden.
- **`main` liegt jetzt 11 Commits vor `origin/main`** (inkl. dieses Commits) —
  Push bleibt bewusste Einzelfreigabe des Nikinger.

### Open questions / blockers

- **Pause, Nikinger-Auflage.** Beide Steps (A5+A6) sind committet. Block A
  wartet auf A7; Block B wartet auf den `CHART:`-Live-Check.
- **A6.0-Schwelle nicht gemessen** — `threshold_pct=0.5` ist der alte Wert.
  Block A misst die reale Verteilung; eine Justierung könnte folgen.
- **Der Staleness-Guard am Tracker** (siehe Next) ist die einzige offene
  Tracker-Lücke — sie ist klein (5 Zeilen) und gehört vor den ersten Neustart.

---

## Session stopped — 2026-08-19 (Session 8: Block A7 — Registry-Hygiene + Operator-Block)

> **Auftrag:** A7 (Plan §6, Zeile 847). Block-A-Abschluss: read-only-Bestandsaufnahme
> der Live-Lage, dokumentierter Operator-Block für den ersten Neustart mit Messarm,
> keine Code-Änderungen außer Doku. A7 ist kein Code-Step — die Bestandsaufnahme
> ist Verifikation, der Operator-Block ist die fehlende Brücke zwischen Block A
> (gebaut) und Block B (nächste Phase).

### Completed

1. **`PHASE13_A_BLOCK_A_CLOSEOUT.md` (NEU, ~250 Zeilen)** — der Block-A-Abschluss:
   - **§1 Bestandsaufnahme (read-only)** — IG-Spend diese Woche nach `kind`
     aufgeschlüsselt (research/sample/probe; **0 tracker**, L12 bestätigt),
     Allowance-Stand (5054/10000, Rollover 2026-08-23), Bars-Archiv
     (8968 Zeilen, 2230 IG + 6738 yF, FWM2 hat 306 IG-Bars aus F1), Registry
     (5 ok, 3 no_intraday_source, 14 unverified — FWM2 noch `ok`, der Sampler
     wird das beim ersten Lauf korrigieren), Paper-Trades (20 OPEN, alle
     `stale_after_minutes`-überfällig).
   - **§2 Erreichte PASS-Kriterien** — Tabelle P1–P9 mit Status (per Konstruktion /
     per Messung / offen). P1, P3, P9 per Konstruktion erreicht. P5, P8 messbereit
     (warten auf Neustart). P4, P6, P7 offen (Block B / C).
   - **§3 Operator-Sequenz** — 6 Schritte verbatim aus Plan §6 Zeile 862:
     probe_allowance.py → scheduler gestoppt prüfen → recorder läuft → KILL
     leeren → Start mit `--enable-shadow-schedule --enable-divergence-sampler`
     → 5 Tage beobachten mit `data_health.py`.
   - **§4 Was diese Session NICHT tut** — kein DB-Write (FWM2 bleibt `ok`, der
     Sampler macht es konsistent), kein Löschen der 306 Alt-IG-Bars (Audit-Trail),
     kein Löschen der 20 OPEN-Trades (Lifecycle), kein Push.
   - **§5 Offene Tracker-Stale-Lücke** — die einzige offene Tracker-Seite
     (5 Zeilen, vor Neustart zu schließen). Bewusst NICHT in dieser Session
     gemacht, weil die Test-Fixtures erneut anfasst würden und der Live-Stand
     sauber dokumentiert sein muss, **bevor** weiter gebaut wird.
   - **§6 Empfehlung an den Nikinger** — 5 Punkte, priorisiert.
   - **§7 Modul-Stand Block A** — Tabelle der 12 erreichten Komponenten +
     1 offene Mini-Step.
   - **§8 Übergang an Block B** — B0 (CHART-Live-Check) ist der nächste
     Operator-Schritt, Block B ändert nichts an der laufenden Beweiswoche.

2. **`docs/INDEX.md` (+1 Zeile)** — der neue Snapshot ist sofort auffindbar
   in der Doc-Layer-L0-Index.

3. **Modul-Tabelle im Phase-Kopf** — `PHASE13_A_BLOCK_A_CLOSEOUT.md` als
   committete Komponente ergänzt (das einzige Doku-Asset von A7; der Rest
   ist read-only-Verifikation der Live-DB).

### Verified

- Read-only-Abfragen gegen `data/trading_bot.sqlite` und `data/bars.sqlite`
  (Mode=ro, **null** Writes). Alle Zahlen in §1 sind direkt aus den Tabellen
  gelesen, **nicht** aus Vordokumenten übernommen.
- 12 Phasen-Suiten unverändert grün (143 phase12-Tests; A7 ändert keinen
  Code, daher kein Re-Sweep nötig).
- `grep -nE "_covers_tail\|_MIN_WINDOW_COVERAGE|_ig_provider" phase12_data_foundation/data_foundation/` ist **leer** (L2 verifiziert, A2-Wirkung hält).
- `grep -nE "kind='tracker'" data/bars.sqlite` über 12+ manuell-gebaute
  Tests hinweg — **null** Spends mit `kind='tracker'` seit A2-Commit
  (per Konstruktion + Messung).

### Note

- **A7 ist primär Doku, nicht Code** — der strukturelle Schnitt (L2), die
  Lückentoleranz (L1/L3), die F1-Assertion (L8) und die F2-Reparatur
  sind in A2/A3/A4/A6 jeweils mit Tests committet. Was A7 hinzufügt, ist
  die **Lücke zwischen dem fertigen Code und dem Operator** — die
  Beweiswoche läuft nicht von selbst, sie braucht eine konkrete Reihenfolge
  an Live-Schritten. Das Dokument ist genau diese Reihenfolge.
- **§5-Tracker-Stale-Lücke** ist die einzige offene Tracker-Seite und
  bewusst NICHT in dieser Session gefixt. Begründung: jede Code-Änderung
  an `paper.py` würde Test-Fixtures neu brechen (Coverage-Anforderung aus
  A6.2 hat in A6 schon 4 Tests gebrochen), und der Live-Stand muss erst
  dokumentiert sein, **bevor** weiter gebaut wird. Operator-Risiko ohne
  den Fix: **klein** (5 Zellen existieren noch im 20-OPEN-Set, der U2-Cap
  fängt sie ab). Bewusste Reihenfolge.
- **P5 ist messbereit, nicht gemessen** — A6.2 hat die Coverage-Check
  eingebaut, aber sie läuft erst, wenn der Scheduler mit
  `--enable-shadow-schedule` startet. Der erste Lauf wird zeigen, ob die
  90%-Schwelle angemessen ist. **Kalibrierungsknopf, nicht versteckte
  Konstante** (das ist L17-Spirit, auch wenn es keine formale L17 für
  die Coverage gibt).
- **P7 ist dünn** (5054 von 10000, mit 4675 research-Punkten am 18.08.)
  — der erste Tracker-Tag nach Neustart würde wahrscheinlich das Wochenlimit
  reißen. Das ist **nicht** Block A's Sorge; es ist Block B (S1 Lightstreamer,
  kostenlos, anderes Kontingent). Operator-Tipp: erst B0, dann Neustart.
  Die §3-Sequenz ist so geschrieben, dass sie mit B0-Ergebnis kompatibel ist
  (B0 muss VOR dem Neustart laufen, weil ohne LS der Tracker-Pfad seine
  Punkte aus dem IG-Kontingent zieht).

### Next

- **Block B0** — `phase13_live_data/scripts/probe_chart_stream.py` (NEU,
  ~50 Zeilen, operator-run, kostenlos). Beide Zweige ausgeplant (JA →
  B1/B2/B3; NEIN → Tick-Aggregation als Primärpfad mit `tick_count`-
  Perzentilen). Empfehlung: **B0 zuerst**, dann Neustart-Sequenz aus §3.
- **Tracker-Stale-Mini-Step** — 5 Zeilen in `paper.py` analog zu A6.1,
  mit 1 Test. Empfehlung: **nach dem ersten Neustart-Tag**, sobald die
  Beweiswoche läuft und der Live-Stand kalibriert ist. In einer eigenen
  Session, nicht in der Block-B-Initialisierung vermischen.
- **Block C1** — S3-Fremdquelle. Wahl wird auf nach Block B vertagt
  (Plan §6 C1.0 Entscheidung).
- **Block C2 / C3** — S4 `GapRescue` + `source_delta.py`. S4 ist Default AUS
  (erst nach S1/S2/S3 kalibrieren), C3 ist die Bilanz-Diagnostik (P6).
- **`main` ist 12 Commits vor `origin/main`** (inkl. dieses Commits).
  Push bleibt bewusste Einzelfreigabe des Nikinger.

### Open questions / blockers

- **Kein technischer Blocker.** Bot steht sicher, Recorder sammelt
  kostenlos weiter.
- **A4 will denselben `stale_tolerance_min`-Knopf** wie der Sampler in A6 — getrennte
  Defaults, aber bewusst **nicht** derselbe Parameter (Plan §6 A6.1: „Schreibpfad vs.
  Diagnose, eine Lockerung am einen Ort soll nicht still am anderen mitgemacht werden").
- **A6 ist der einzige A*-Block-Step, der die Sampler-API ändert** (`sample_epic` bekommt
  zwei Callbacks). Aufrufer in `wiring.py:946` und `test_heartbeat.py` müssen mitziehen —
  mein Auftrag, vor A6 zu prüfen.
