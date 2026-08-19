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
