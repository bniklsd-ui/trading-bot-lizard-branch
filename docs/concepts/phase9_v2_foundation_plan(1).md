# Phase 9 (V2) — Foundation: Autonome Epic-Research + Daten-Input-Zuverlässigkeit
## Detaillierter Implementierungsplan für Claude Code

> **Author:** Phase-9(V2)-Browser-Planungschat, 2026-07-03.
> **Audience:** Claude Code (Sonnet). Dieser Plan ist ausführungsreif — Entscheidungen sind
> gelockt, Schritte sequenziert, Namen fixiert. Nichts hier muss neu hergeleitet werden.
> **Inputs:** `PHASE9_V2_KICKOFF_HANDOVER.md`, `phase8_scheduler/PHASE8_CLOSEOUT_HANDOVER.md`
> (§2 through-line, §4 V2-Vorschlag, §9 Anker-Tabelle), As-Built-Reads vom 2026-07-03:
> `phase4_research/research/models.py`, `phase8_scheduler/scripts/verify_instrument.py`,
> `phase1_broker_wrapper/lightstreamer_integration_notes.md`.
> **Drift-Konvention:** Alles, was seit dem letzten Repo-Read gedriftet sein kann, ist als
> **[VERIFY]** markiert — bei Ausführung gegen den echten Repo-Stand prüfen, nicht als
> gesichert übernehmen. Datei:Zeile-Anker sind Stand v1.7-Merge.

---

## §0 Mission + gelockte Entscheidungen

**Mission V2 (Foundation):** Die zwei strukturellen Lücken schließen, die den gesamten
v1.5→v1.7-Hotfix-Arc getrieben haben:
1. **V2a — Autonome Epic-Research:** discover → validate → promote als Code-Pipeline.
   Kein manueller Code-Edit mehr, damit ein Instrument ins Live-Universum kommt.
2. **V2b — Daten-Input-Zuverlässigkeit:** Provider-Kette mit IG als Primärquelle,
   yFinance strukturell gehärtet (Backoff/Circuit-Breaker), Lightstreamer in den
   Research-Kontextpfad verdrahtet (nach Multi-Epic-Diagnose).

**Grundmotto unverändert:** so wenig AI wie möglich, so viel AI wie nötig. In V2 ist
**null neues AI** verdrahtet — Discovery-/Promotion-Kriterien sind 100 % Code-evaluiert.

### Gelockte Entscheidungen (Operator, 2026-07-03)

| # | Entscheidung | Lock |
|---|---|---|
| D1 | Reframe V2/V3/V4 | **Angenommen.** Phase 9 = V2 (Foundation). V3 = Phase 10 (Persistenz-Reform + Abstain-Lessons + UI), V4 = Phase 11 (Sophisticated: Council, Debate-Handover, Reward-Reform, Force-Trigger-Guard, Instinct-ECC), gated auf V2/V3 + reale Outcomes. ROADMAP-Umbau in Step 0b. |
| D2 | Neues Paket | `phase9_universe/` mit Package `universe/` (Konvention `phaseN_xxx/<paket>/`). Phasen-isoliert, Cross-Phase nur über typisierte Contracts / duck-typed Injection. |
| D3 | Discovery-Quelle | **Seed-Longlist von Suchbegriffen + IG `search_markets`-Sweep**, Kriterien = Code (EUR, Index-CFD, TRADEABLE, Kassa-Variante, min size). Kein LLM. yf_ticker-Mapping über statische Code-Tabelle, unbekannt → `None` (reduced-signal toleriert, Konzept C3). |
| D4 | Promotion | **Voll autonom** auf Demo: `discovered → verified → active` ohne Operator-Gate. Das Operator-Gate wird durch ein **hartes Code-Gate ersetzt**: Aktivierung nur bei deterministisch aufgelöstem `point_value` (D6). Auto-**Demotion** (`active → quarantined`) bei wiederholten IG-seitigen Verify-Fails. Wird das im Demo-Run nicht sauber, wird ein Nikinger-Gate nachgerüstet (explizite Operator-Vorgabe). |
| D5 | Persistenz | **DB-Tabelle `instrument_universe`** (Migration 004) statt Config-Datei. `EXTENDED_UNIVERSE` wird zum einmaligen Seed (`source="curated"`). Kein Config-File-Drift. |
| D6 | point_value | Carried-over-Punkt stirbt strukturell: `resolve_point_value()` leitet den Wert deterministisch aus IG-API-Felddaten + Namenskonvention + lot_size-Kreuzcheck ab. Kein aufgelöster Wert → keine Aktivierung. **Non-Demo-Broker → Promotion wirft hart** (`UniverseSafetyError`), Demo-only bleibt fail-closed. |
| D7 | V2b-Umfang | **(i)** BarProvider-Kette IG→yFinance + yFinance-Härtung: verbindlich. **(ii)** Lightstreamer-Multi-Epic-Diagnose + `LiveQuoteCache` in den Research-Kontext: verbindlich, als eigene Schritte hinter (i). Keine dritte externe Quelle, kein neuer API-Key (Lock #8). Momentum-VETO bleibt unangetastet auf P1-IG-Bars. |
| D8 | „2 unabhängige Echtzeitquellen" — ehrliche Auflösung | Eine echte zweite **unabhängige Echtzeit**quelle für EU-Index-CFDs existiert ohne bezahlten/gekeyten Provider nicht (Lock #8 schließt das aus; yFinance ist ~15 min delayed). Gelockt wird stattdessen: **Redundanz über zwei IG-Transportwege** (Lightstreamer-Stream primär für Live-Quotes, IG-REST-Bars als Fallback + Bar-Quelle) **plus yFinance als unabhängiger Delayed-Cross-Check** mit deterministischem Divergenz-Alarm in der Observability (gated nichts). Will der Operator später echte Zweit-Echtzeit, ist das ein V3+-Item mit Key-Provider — hier bewusst out of scope. |

### Leitplanken (unverändert, bestätigt)
Kein neues AI im Daten-/Universum-Layer · AI-Output triggert nie direkt eine Order ·
VETOs/Gates unantastbar (insbesondere: Momentum-VETO-Datenquelle P5←P1 wird **nicht**
angefasst) · demo-only fail-closed · additive, getestete, phasen-isolierte Nähte ·
Credentials nur im Keyring · Live-Runs = Operator · TDD, keine Netzwerk-Calls in Unit-Tests ·
atomare Commits · stderr-Logging · Handover nach ~20–30 Tool-Calls via `## Session stopped`.

---

## §1 Schrittsequenz (Übersicht)

| Step | Inhalt | Commit-Grenze |
|---|---|---|
| 0 | Legacy-Grep + Regression-Baseline | eigener Commit |
| 0b | Doku-Reconciliation: ROADMAP-Buckets, ARCHITECTURE-Check, `phase9_universe/CLAUDE.md`-Skeleton | eigener Commit |
| 1 | Migration 004 + `UniverseStore` | eigener Commit |
| 2 | `pricing.py` — deterministischer point_value-Resolver | eigener Commit |
| 3 | `discovery.py` — Seed-Sweep + Code-Filter | eigener Commit |
| 4 | `promotion.py` — Statusmaschine, Auto-Promote/Demote, Safety | eigener Commit |
| 5 | Integration: P4 liest DB-Universum, P8-Runner bekommt Universe-Refresh-Naht | eigener Commit |
| 6 | V2b-i: BarProvider-Kette + yFinance-Backoff/Circuit-Breaker + Divergenz-Check | eigener Commit |
| 7 | V2b-ii: LS-Multi-Epic-Diagnose (7a) → Fix → `LiveQuoteCache` + Kontext-Enrichment (7b) | 2 Commits |
| 8 | Operator-Live-Runs: 8a Autonomie-Beweis, 8b Breaker-Fire (carried-over 5b) | docs-only Commits |
| Post | Doku-Sync, SVG, Handover | eigener Commit |

Reihenfolge-Begründung: 1–5 (V2a) vor 6–7 (V2b), weil die Promotion-Pipeline der
Verbraucher der Datenpfad-Verbesserungen ist und Step 8a beides zusammen beweist.

---

## §2 Step 0 — Housekeeping: Legacy-Grep + Regression-Baseline

**Ziel:** Sauberer Startpunkt, keine toten Vokabulare, grüne Baseline.

Aktionen:
1. `grep -rn -i "turbo\|CALL/PUT\|pre_trade_option_check\|expected hold" --include="*.py" --include="*.md"` über das Repo. Bekannter Restbestand **[VERIFY]**: `turbo_candidates.json` wird in `phase4_research/research/models.py` (Candidate-Docstring) als Persistenzname referenziert — das ist ein **aktiver Dateiname**, kein totes Vokabular. Entscheidung: **nicht umbenennen** (P5-Gate-2-Contract), nur im Grep-Protokoll als „known, active" vermerken. Alles andere Gefundene: bereinigen oder begründet stehen lassen (Protokoll in Commit-Message).
2. Volle Regression: `pytest` über alle Phasen. Erwartung **[VERIFY]**: P1–P8 grün (zuletzt 181 Unit-Tests P8 + Bestand P1–P7). Zahl im Protokoll festhalten = Baseline.
3. Root-`CLAUDE.md`-Nit fixen: Testzahl-Inkonsistenz (181 Header vs. 173 Detail im P8-Block) **[VERIFY]** — auf den realen pytest-Count angleichen.

**Akzeptanz:** Grep-Protokoll in Commit-Message; Baseline grün; kein Verhalten geändert.

---

## §3 Step 0b — Doku-Reconciliation (vor jedem Code)

**Ziel:** ROADMAP spiegelt die gelockten Buckets; das neue Phasen-Paket hat sein
CLAUDE.md-Skeleton als **allererste Aktion** (etablierte Regel).

Aktionen:
1. `ROADMAP.md`: Phase-9-Sektion umbauen →
   - **Phase 9 (V2 — Foundation):** V2a autonome Epic-Research (discover/validate/promote), V2b Datenpfad (Provider-Kette, yF-Härtung, Lightstreamer-Research-Wiring). Status: in Arbeit.
   - **Phase 10 (V3):** Persistenz-Reform (`market_regime_snapshots`, `decision_context`, optional `lesson_embeddings`), No-Trade-/Abstain-Lessons (REASON_*-Taxonomie befüllen + `reflect()`-Variante), UI-Enhancements. Gated auf Phase 9.
   - **Phase 11 (V4):** Council-Integration, Bull/Bear/Judge-Handover, Reward-Reform, Force-Trigger-Guard, Instinct-ECC + Longterm-VETO. Gated auf Phase 9+10 **und** reale Outcomes.
   - Carried-over-Sektion aktualisieren: 5b bleibt offen (→ Step 8b), point_value (→ durch D6 strukturell adressiert, Vermerk), yFinance-Root-Cause (→ durch D7 strukturell adressiert statt gepinnt, Vermerk).
2. `ARCHITECTURE.md` **[VERIFY]**: v1.5–v1.7-As-Built prüfen (EXTENDED_UNIVERSE, provenance-Spalte/Migration 003, observability.py, DB-fed WebUI-Status). Abweichungen fixen — Code ist Wahrheit.
3. **`phase9_universe/CLAUDE.md` anlegen (Skeleton):** Zweck, Bauprinzip (kein AI im Layer), Modulliste (§4–§7), Statusmaschine-Diagramm (ASCII), Test-/Wiring-Konventionen, `## Session stopped`-Block leer.
4. `README.md`: Phasenliste um 9/10/11 ergänzen.
5. **Root-`CLAUDE.md`-Entschlackung (~61 KB, Claude-Code warnt über Limit) — by concern, nicht by size:** CLAUDE.md ist das Auditability-/Handover-Rückgrat; naives Zerschneiden nach Größe zerstört genau die Single-File-Übersicht, die der Sinn ist. Deshalb **stabile Referenzinhalte herauslösen, CLAUDE.md als schlanke Steuer-Datei behalten:**
   - **Bleibt in CLAUDE.md** (das operativ „Heiße"): Bauprinzip/Motto, aktueller Projektstand (letzter abgeschlossener Phasenstand + aktive Arbeit), Modell-/Infra-Kurzreferenz, **die letzten ~3–5 `## Session stopped`-Blöcke**, plus ein **Index/Pointer-Block** auf die ausgelagerten Dateien. Zielgröße: schlank genug, dass Claude Code nicht mehr warnt **[VERIFY: konkrete Byte-/Token-Grenze, ab der die Warnung feuert — danach dimensionieren]**.
   - **Ausgelagert nach `docs/`** (stabil, selten gelesen): historische Session-Logs → **`docs/handover_history/` mit einer Datei pro Kalendertag** (`YYYY-MM-DD.md`, enthält alle `## Session stopped`-Blöcke + Bugfix-/Findings-Journale dieses Tages, wortgleich kopiert); phasenübergreifende Architektur-/Entscheidungsdetails → ARCHITECTURE.md (verschieben, nicht duplizieren).
   - **Regel für den Split:** reine **Verschiebung + Pointer**, kein Umschreiben von Inhalt (Auditability = wortgleiche Historie). Jede ausgelagerte Sektion hinterlässt in CLAUDE.md eine Einzeiler-Zeile „→ siehe `docs/handover_history/…`". Nichts wird gelöscht, nur umgezogen.
   - **Gilt nur für Root-CLAUDE.md.** Große Phasen-`CLAUDE.md` (mehrere sind ebenfalls groß **[VERIFY: Größen]**) sind eigene Baustellen — hier **nicht** anfassen (Scope), aber im Grep-Protokoll als „bekannt groß, deferred" vermerken. Wenn Claude Code auch dort warnt: gleiche Methode, aber **je ein eigener Commit pro Phasen-Datei**, damit ein fehlerhafter Split isoliert reversibel ist.
   - **Stehende Regel (in Handover-Konvention aufnehmen):** neue `## Session stopped`-Blöcke gehen ab sofort direkt in die Tagesdatei `docs/handover_history/YYYY-MM-DD.md`; Root-CLAUDE.md hält nur den aktuellen Stand + einen Pointer-Index auf die Tagesdateien (letzte ~3–5 verlinkt). Damit wächst CLAUDE.md nicht wieder zu.

**Akzeptanz:** Ein docs-only Commit (Split als eigener Sub-Commit für saubere Reversibilität); ROADMAP/README/ARCHITECTURE konsistent mit Locks; Skeleton existiert; Root-CLAUDE.md unter der Warngrenze, Historie wortgleich in `docs/handover_history/` erhalten.

---

## §4 Step 1 — Migration 004 + UniverseStore

**Ziel:** Das Universum wird DB-persistiert; `EXTENDED_UNIVERSE` wird zum Seed.

**Migration** — in das bestehende P2-Migrationsframework **[VERIFY: Pfad + Mechanik; Migrationen 001–003 liegen in `phase2_persistence/`, Namensschema der Vorgänger übernehmen]**:

```sql
-- migration 004: instrument_universe
CREATE TABLE IF NOT EXISTS instrument_universe (
    epic                TEXT PRIMARY KEY,
    name                TEXT,
    yf_ticker           TEXT,
    volume_proxy        TEXT,
    point_value         REAL,            -- NULL bis deterministisch aufgelöst
    point_value_source  TEXT,            -- 'ig_fields' | 'name_lotsize_agree' | 'curated_confirmed' | NULL
    min_deal_size       REAL,
    currency            TEXT NOT NULL,
    status              TEXT NOT NULL,   -- 'discovered'|'verified'|'active'|'quarantined'|'retired'
    source              TEXT NOT NULL,   -- 'curated'|'research_promoted'
    checks_json         TEXT,            -- letztes verify-Verdict (JSON)
    fail_count          INTEGER NOT NULL DEFAULT 0,
    data_degraded       INTEGER NOT NULL DEFAULT 0,  -- yF-seitig degradiert, NICHT demotierend
    last_verified_at    TEXT,
    created_at          TEXT NOT NULL,
    updated_at          TEXT NOT NULL
);
```

**Neues Paket `phase9_universe/universe/`:**

- `models.py` — Typen only, kein I/O (Konvention wie P4):
  - `STATUS_DISCOVERED = "discovered"`, `STATUS_VERIFIED = "verified"`, `STATUS_ACTIVE = "active"`, `STATUS_QUARANTINED = "quarantined"`, `STATUS_RETIRED = "retired"` (Modul-Konstanten, Muster `REASON_*`).
  - `@dataclass(frozen=True) class UniverseRecord:` Felder = Tabellenspalten (`checks: dict[str, Any]` deserialisiert), Methoden `to_row() -> dict`, `from_row(row) -> UniverseRecord`, `to_instrument_spec(self) -> "InstrumentSpec-shaped dict"` — **als plain dict**, nicht als P4-Import (Phasen-Isolation; P4 baut daraus selbst `InstrumentSpec`, siehe §8).
- `exceptions.py`: `UniverseError(Exception)` (code="UNIVERSE_ERROR"), `UniverseSafetyError(UniverseError)` (code="UNIVERSE_SAFETY"), `UniverseStoreError(UniverseError)` — Muster P4-Hierarchie.
- `store.py` — `class UniverseStore:` (SQLite, injizierter DB-Pfad; **[VERIFY]** ob P2 eine wiederverwendbare Connection-/Path-Konvention exportiert — wenn ja nutzen, sonst eigene sqlite3-Verbindung mit `data/trading_bot.sqlite`-Default über Wiring):
  - `seed_curated(self, specs: Iterable[Any]) -> int` — idempotent (INSERT OR IGNORE), setzt `status=STATUS_ACTIVE`, `source="curated"`, `point_value_source="curated_confirmed"` **nur für DAX** (live-bestätigt); STXE/CAC/IBEX seeden mit `point_value_source=NULL` + ihrem kuratierten Wert in `point_value` → sie durchlaufen Step-2-Resolver zur Bestätigung (D6/carried-over). Rückgabe: Anzahl eingefügt.
  - `upsert_discovered(self, rec: UniverseRecord) -> None`
  - `get(self, epic: str) -> UniverseRecord | None`
  - `list_by_status(self, *statuses: str) -> list[UniverseRecord]`
  - `set_status(self, epic: str, status: str, *, checks: dict | None = None, fail_increment: bool = False) -> None`
  - `set_pricing(self, epic: str, point_value: float, source: str) -> None`
  - `active_universe(self) -> list[UniverseRecord]` — nur `STATUS_ACTIVE`, deterministische Ordnung (created_at, epic).

**Tests** (`phase9_universe/tests/test_store.py`, in-memory SQLite `:memory:` + Migrations-SQL direkt): seed-Idempotenz, Status-Roundtrip, fail_count-Inkrement, active-Ordnung, `from_row/to_row`-Symmetrie. Migrationstest im P2-Suite-Stil **[VERIFY Muster von 003]**.

**Akzeptanz:** Migration läuft vorwärts auf frischer + bestehender DB; Seed aus `EXTENDED_UNIVERSE` erzeugt exakt 4 Zeilen; alle Tests grün; keine bestehende Tabelle berührt.

---

## §5 Step 2 — `pricing.py`: deterministischer point_value-Resolver

**Ziel:** Der inferierte point_value (STXE/CAC/IBEX, carried-over) wird durch einen
Code-Beweis ersetzt; ohne Beweis keine Aktivierung.

`phase9_universe/universe/pricing.py`:

```python
def resolve_point_value(market_info: dict[str, Any]) -> tuple[float, str] | None:
    """Deterministisch aus IG-Marktdaten. None = nicht beweisbar -> keine Aktivierung."""
```

Auflösungsordnung (erste Übereinstimmung gewinnt, alles Code):
1. **IG-Instrumentfelder** — `valueOfOnePip`/`onePipMeans`/`contractSize`/`lotSize` **[VERIFY: welche dieser Felder P1s `get_market_info`-Envelope heute durchreicht — sehr wahrscheinlich nur `currency`/`min_deal_size`/`lot_size`-Teilmenge. Falls Felder fehlen: P1 `ig_adapter.py::get_market_info` additiv erweitern (Feld-Passthrough, kein Verhaltenswechsel) → Cross-Phase-Edit-Register §11].** Parsing: `valueOfOnePip` ist bei IG ein String (z. B. `"1"`/`"2"` oder mit Einheit) — strikt parsen, bei Mehrdeutigkeit `None`. Quelle-Tag: `"ig_fields"`.
2. **Namens-/lot_size-Kreuzcheck** — Regex `\((\d+(?:[.,]\d+)?)\s*€\)` auf `name` + Gleichheit mit `lot_size`. Nur wenn **beide vorhanden und gleich** → `(wert, "name_lotsize_agree")`. Das kodifiziert exakt das dokumentierte v1.5-Inferenzmuster (models.py-Kommentarblock), jetzt aber als *Zwei-Quellen-Übereinstimmung* statt Ein-Quellen-Inferenz.
3. Sonst `None`.

Zusätzlich: `confirm_curated(record: UniverseRecord, market_info: dict) -> bool` — für geseedete Instrumente: Resolver-Ergebnis == kuratierter Wert → `point_value_source` upgraden; Widerspruch → `status=STATUS_QUARANTINED` + Log-WARNUNG (ein kuratierter, aber widerlegter point_value ist gefährlicher als ein fehlender).

**Tests** (`test_pricing.py`, reine Fixture-Dicts, kein Netz): ig_fields-Pfad, Namens-Kreuzcheck happy/mismatch/fehlend, Komma-Dezimale, Widerspruchs-Quarantäne.

**Akzeptanz:** Resolver ist pure function; STXE-Fixture (`"(2€)"`, lot_size 2.0) → `(2.0, "name_lotsize_agree")`; widersprüchliche Fixture → `None`.

---

## §6 Step 3 — `discovery.py`: Seed-Sweep + Code-Filter

**Ziel:** Etwas *findet* Kandidaten. Rein deterministisch.

`phase9_universe/universe/discovery.py`:

- `SEARCH_TERMS: tuple[str, ...]` — kuratierte Seed-Longlist der Suchbegriffe (nicht Epics!), Start: `("Germany 40", "Deutschland 40", "Europe 50", "France 40", "Frankreich 40", "Spain 35", "Spanien 35", "Netherlands 25", "Niederlande 25", "Italy 40", "Italien 40", "Switzerland 20", "Schweiz 20", "Sweden 30", "US 500", "US Tech 100", "Wall Street", "UK 100")` — **[VERIFY: IG-Demo-Suchbegriffe sind kontosprachabhängig (deutsches Konto → deutsche Namen, „Kassa"); beide Sprachvarianten drin lassen, tote Begriffe kosten nur einen paced Call].** Nicht-EUR-Treffer (US/UK/CH) fallen im Currency-Filter — bewusst: die Longlist bleibt breit, der Filter ist das Kriterium.
- `KNOWN_YF_TICKERS: dict[str, str]` — statisches Muster→Ticker-Mapping (z. B. Name enthält `"Germany 40"|"Deutschland 40"` → `"^GDAXI"`, `"Europe 50"` → `"^STOXX50E"`, `"France|Frankreich 40"` → `"^FCHI"`, `"Spain|Spanien 35"` → `"^IBEX"`, `"Netherlands|Niederlande 25"` → `"^AEX"`, `"Italy|Italien 40"` → `"FTSEMIB.MI"`). Kein Treffer → `yf_ticker=None` (reduced-signal, C3). `KNOWN_VOLUME_PROXIES: dict[str, str]` analog (DAX→`EXS1.DE`, STXE→`EXW1.DE`; Rest leer — kein Raten, dokumentiertes v1.5-Prinzip).
- `def discover(broker: Any, store: UniverseStore, *, search_terms: tuple[str, ...] = SEARCH_TERMS, pace_s: float = 1.0, sleep_fn=time.sleep) -> DiscoveryReport:`
  - je Term: `broker.search_markets(term)` **[VERIFY exakte P1-Signatur + Envelope-Shape — `scripts/resolve_epics.py` ist die Referenznutzung]**, paced (1.0 s, das bestätigte Anti-Rate-Limit-Muster aus v1.5).
  - Code-Filter je Hit: `currency == "EUR"` · `instrument_type` enthält `INDICES` **[VERIFY Feldname/Wert im Envelope]** · `market_status == "TRADEABLE"` · Kassa-Präferenz: bei mehreren Varianten pro Index die mit kleinstem `lot_size`, Name ohne Forward-Marker (kodifiziert das dokumentierte DAX/STXE-Auswahlmuster) · `min_deal_size > 0`.
  - Bereits bekannte Epics (jeder Status) → skip. Neue → `UniverseRecord(status=STATUS_DISCOVERED, source="research_promoted", point_value=None, …)` via `store.upsert_discovered`.
  - `@dataclass class DiscoveryReport:` `terms_searched: int`, `hits: int`, `new: list[str]`, `skipped_known: int`, `filtered: dict[str, int]` (Filtergrund→Anzahl).
  - Fail-soft je Term (ein 500 killt nie den Sweep — Muster `check_ig_side`).

**Tests** (`test_discovery.py`, Fake-Broker mit Fixture-Envelopes): Filtergreifen je Kriterium, Kassa-Auswahl bei Mehrfachtreffern, Skip bekannter Epics, fail-soft, Report-Zählung, Pacing via injiziertem `sleep_fn` (keine echten Sleeps).

**Akzeptanz:** `discover()` gegen Fixtures produziert exakt vorhersagbare `discovered`-Zeilen; kein Netzwerk in Tests; kein LLM-Import irgendwo im Paket (Grep-Assertion im Test: `import anthropic` verboten in `phase9_universe/`).

---

## §7 Step 4 — `promotion.py`: Statusmaschine + Safety

**Ziel:** Verifizierte Kandidaten werden ohne Menschen aktiv; kranke Aktive fliegen raus.

`phase9_universe/universe/promotion.py`:

- Verify-Wiederverwendung: Check-Funktionen aus `phase8_scheduler/scripts/verify_instrument.py` via `importlib.util.spec_from_file_location` importieren (`check_ig_side`, `check_yf_side`, `verdict_for` — genau die dokumentierte, duck-typed v3-Naht; Präzedenz `tests/test_resolve_epics.py`). **Kein Copy-Paste** — eine Wahrheit.
- `def run_promotion_cycle(broker: Any, fetcher: Any, store: UniverseStore, *, is_demo: bool, max_active: int = 8, demote_after_fails: int = 3, pace_s: float = 1.0, sleep_fn=time.sleep, health_sink: Callable[[dict], None] | None = None) -> PromotionReport:`
  1. **Safety zuerst:** `if not is_demo: raise UniverseSafetyError("promotion is demo-only")` — fail-closed, keine Ausnahme. (`is_demo` kommt aus Wiring, nicht aus dem Broker erraten.)
  2. **Kandidaten prüfen** (`STATUS_DISCOVERED` + `STATUS_QUARANTINED` mit Backoff: nur wenn `fail_count`-abhängige Wartezeit abgelaufen — einfache Treppe `2**fail_count` Stunden gegen `last_verified_at`): `verify_instrument(...)`-Verdict + `resolve_point_value(market_info)`. **PASS + point_value aufgelöst** → `STATUS_VERIFIED` + `set_pricing`. PASS ohne point_value → bleibt `discovered` (checks_json dokumentiert warum). FAIL → `STATUS_QUARANTINED`, fail_count++.
  3. **Auto-Aktivierung:** alle `STATUS_VERIFIED` → `STATUS_ACTIVE`, solange `len(active) < max_active` (Sizing-Sanity: Research-Prompt-Budget wächst pro Epic; 8 ist die konservative Obergrenze, Config).
  4. **Health-Recheck der Aktiven** (gleiche Verify-Funktionen): **IG-seitiger** Check-Fail → fail_count++; bei `fail_count >= demote_after_fails` → `STATUS_QUARANTINED` (**Demotion** — das ist die strukturelle Antwort auf „Instrument liefert dauerhaft nicht"). **yF-seitiger** Fail → nur `data_degraded=1` (reduced-signal toleriert, demotiert NIE — Konzept C3; P3 degradiert ohnehin sauber). Erfolg → fail_count=0, data_degraded zurücksetzen.
  5. Jede Statusänderung als Event in `health_sink` (→ Observability, §9).
- Kuratierte Bestätigung: für Aktive mit `point_value_source IS NULL` in Schritt 4 `confirm_curated()` mitlaufen lassen — damit werden STXE/CAC/IBEX beim **ersten** Zyklus bestätigt oder quarantänisiert (carried-over stirbt hier messbar).
- `@dataclass class PromotionReport:` `verified: list[str]`, `activated: list[str]`, `demoted: list[str]`, `quarantined: list[str]`, `confirmed_pricing: list[str]`, `unchanged: int`.

**Tests** (`test_promotion.py`, Fake-broker/fetcher/store bzw. in-memory Store): Safety-Raise bei `is_demo=False`, Happy-Path discovered→verified→active, PASS-ohne-pricing bleibt liegen, Demotion nach 3 IG-Fails, yF-Fail demotiert nicht sondern setzt degraded, Backoff-Treppe, max_active-Kappung, curated-Bestätigung + Widerspruchs-Quarantäne.

**Akzeptanz:** Statusmaschine vollständig durch Tests abgedeckt (jede Kante); kein Pfad aktiviert ohne point_value; kein Pfad läuft auf non-demo.

---

## §8 Step 5 — Integration: P4 liest DB-Universum, P8 bekommt Refresh-Naht

**Ziel:** Das aktive DB-Universum ist die Wahrheit für Research; der Daemon hält es frisch.

**P4 (Cross-Phase-Edit, Register §11):**
- `phase4_research/research/models.py`: **nichts strukturell ändern.** `InstrumentSpec`/`load_universe`/`EXTENDED_UNIVERSE` bleiben (Fallback + Seed-Quelle + Testbestand).
- **Wiring** (`scripts/wiring.py` **[VERIFY Pfad — der Kommentar in models.py nennt `scripts/wiring.py` als den Ort, an dem `universe=EXTENDED_UNIVERSE` übergeben wird]**): neue Funktion `build_universe_from_db(store: UniverseStore) -> tuple[InstrumentSpec, ...]` — mappt `UniverseRecord.to_instrument_spec()`-Dicts auf `InstrumentSpec(**d)` und reicht sie als `ResearchConfig(universe=...)` durch. Damit läuft **alles Bestehende unverändert** durch `load_universe()`-Validierung (fail-closed inklusive). Fallback-Kette: DB leer/nicht erreichbar → `EXTENDED_UNIVERSE` + WARN (nie stillschweigend, nie Crash — ein leeres Universum ist per `load_universe` ohnehin ValueError).
- `TickerMapper`-Registrierung: wie im verify-Script-Muster je Spec `register`/`register_volume_proxy` — **[VERIFY: wo Wiring das heute für EXTENDED_UNIVERSE tut; Muster übernehmen]**.

**P8 (Cross-Phase-Edit, Register §11):**
- `phase8_scheduler/scheduler/runner.py`: optionale Injektion `universe_refresher: Callable[[], Any] | None = None` **[VERIFY Konstruktor-/Config-Form des Runners]**. Aufruf: (a) im Preflight, (b) danach 1× je `universe_refresh_interval_min` (Default 240, Config) im bounded loop, **nie** innerhalb eines Research-Ticks. Default `None` = exakt heutiges Verhalten (additiv, bit-identisch ohne Wiring-Opt-in).
- Wiring verdrahtet `universe_refresher = lambda: run_promotion_cycle(broker, fetcher, store, is_demo=True, health_sink=observability_writer)` und optional davor 1× täglich `discover(...)` (eigener Zähler im Runner-State **[VERIFY state.py-Muster für Tageszähler — day-rollover existiert]**).
- Token-Budget/Safety: Promotion-Zyklus macht **null** LLM-Calls → Budget unberührt. Broker-Calls sind paced; Anzahl ≈ (#kandidaten + #aktive) × 2 GETs je Zyklus — bei Intervall 240 min vernachlässigbar gegen IG-Limits **[VERIFY grob gegen beobachtete Rate-Limits aus v1.5-resolve-Läufen]**.

**Tests:** Wiring-Unit (Fake-Store → ResearchConfig.universe korrekt, Fallback-Kette), Runner-Test (refresher wird im Preflight + nach Intervall gerufen, nie im Tick; `None` → nie gerufen). Regression P4/P8 komplett grün.

**Akzeptanz:** Mit gefüllter DB kommt das Research-Universum aus der DB; mit leerer DB verhält sich alles wie v1.7; ein in der DB aktiviertes Test-Epic erscheint ohne Code-Edit in `tradeable_epics` des nächsten Kontexts (Integrationstest mit Fakes).

---

## §9 Step 6 — V2b-i: BarProvider-Kette + yFinance-Härtung + Divergenz-Check

**Ziel:** Research-Daten kommen primär von IG (real-time), yFinance wird Fallback und
crasht/hämmert nie mehr; Divergenzen werden sichtbar.

**P3 (Cross-Phase-Edits, Register §11) — alles additiv:**

- Neu `phase3_external_data/external_data/providers.py`:
  - `class BarProvider(Protocol):` `def get_bars(self, epic: str, *, resolution: str, count: int) -> list[dict] | None: ...` (Bar-Dict-Shape = bestehende Fetcher-Bar-Shape **[VERIFY Shape in fetcher.get_bars]**).
  - `class IGBarProvider:` duck-typed `broker` injiziert; Mapping `{"5m": "MINUTE_5", "1m": "MINUTE", "15m": "MINUTE_15", "1h": "HOUR", "1d": "DAY"}` **[VERIFY P1-Resolution-Konstanten gegen `get_ohlcv`-Signatur]**; Envelope→Bar-Liste; not-ok → `None` (nie raise).
  - `class YFinanceBarProvider:` delegiert an den bestehenden Fetcher-Pfad (Injektion des Fetchers, kein Re-Implement).
  - `class ChainedBarProvider:` `__init__(self, providers: Sequence[tuple[str, BarProvider]], health_sink: Callable[[dict], None] | None = None)`; `get_bars` iteriert, erster non-None gewinnt; je Versuch Event `{"event": "bar_fetch", "provider": name, "epic": epic, "ok": bool}` an health_sink.
- `fetcher.py`: 
  - Konstruktor additiv `bar_provider: Any | None = None` — Default `None` = heutiger Pfad bit-identisch. Gesetzt → `get_bars` nutzt die Kette. **Off-hours-Disziplin bleibt im Fetcher** (davor prüfen, nicht in Provider duplizieren) **[VERIFY wo der Off-hours-Check heute sitzt]**.
  - **Backoff:** interne Helper `def _with_backoff(fn: Callable[[], T], *, attempts: int = 3, base_delay_s: float = 0.75, sleep_fn=time.sleep) -> T` (exponentiell + deterministischer Jitter aus attempt-Index, kein random in Tests) um die rohen yfinance-Calls **[VERIFY exakte Call-Sites: get_history/get_bars/get_volume_anomaly]**. Letzter Fehlschlag → bestehendes degrade-Verhalten (field_errors), nie neuer Fehlertyp nach außen.
  - **Circuit-Breaker:** `class _TickerCircuit:` pro Ticker, `open_after: int = 4` konsekutive Fails, `cooldown_s: float = 900`; offen → sofortiger Degrade ohne Netz-Call (Event `{"event": "circuit_open", "ticker": ...}`). Half-open nach Cooldown: ein Probe-Call. Damit hämmert der Bot Yahoo nie mehr in einen härteren Rate-Limit — die strukturelle Antwort auf die ^FCHI/^IBEX-Intermittenz (Root-Cause bleibt ungepinnt, Verhalten wird robust; ehrlich so dokumentieren).
- **Divergenz-Check** (deterministisch, gated nichts): in P4 `context_builder` **oder** P8-Observability **[Entscheidung: P8-Observability — kein Prompt-Einfluss, reine Diagnose]**: wenn für ein Epic sowohl IG-Bar-Close als auch yF-Last vorliegen: `divergence_pct = abs(ig_close - yf_last) / ig_close * 100`; `> 0.5 %` → Event `{"event": "quote_divergence", "epic": ..., "pct": ...}` in `research_health.jsonl` via bestehendes `observability.py` **[VERIFY dessen Writer-API]**.

**Wiring:** ChainedBarProvider mit `[("ig", IGBarProvider(broker)), ("yf", YFinanceBarProvider(fetcher_raw_path))]` bauen und dem Fetcher geben. **IG-Allowance-Hinweis** ins Wiring-Docstring: IG-REST-Historical-Bars haben ein wöchentliches Datenpunkt-Kontingent (**[VERIFY aktuelle Demo-Allowance, Größenordnung 10.000 Punkte/Woche]**) — Counts klein halten (bestehende count≈5-Muster reichen), Verbrauch als Observability-Zähler `{"event": "ig_points_used", "n": count}` loggen. Kein Hard-Gate in V2 (erst messen).

**Tests:** Provider-Kette (Fakes: erster None → zweiter gewinnt; Events), IGBarProvider Envelope-Mapping + Resolution-Map, Backoff (injizierter sleep_fn, Fail→Fail→Pass), Circuit (öffnet nach 4, blockt, half-open Probe), Fetcher-Default-Pfad bit-identisch (bestehende P3-Suite unverändert grün), Divergenz-Berechnung.

**Akzeptanz:** P3-Regression grün ohne Änderung an bestehenden Tests; mit Provider verdrahtet liefert `get_bars` IG-Daten, fällt bei IG-Ausfall auf yF; ein simulierter Dauer-Fail eines Tickers erzeugt exakt 4 Netz-Versuche und dann Circuit-Events statt weiterer Calls.

---

## §10 Step 7 — V2b-ii: Lightstreamer Multi-Epic (Diagnose → Fix → LiveQuoteCache)

**Kontext (ehrlich):** LS ist v10 = offizielles SDK, live PASS mit **einem** Epic (DAX).
Der Operator berichtet Fehler („bestimmte Syntaxen stimmen nicht") bei <10 Epics — **in
keiner Note dokumentiert**. Darum ist 7a eine echte Diagnose, kein Fix ins Blaue.

### 7a — Diagnose-Harness (eigener Commit)
Neu `scripts/diag_lightstreamer_multi.py` (Repo-Script-Konvention: Narrativ→stderr, JSON→stdout, exit 0):
- Verbindet via P1 (`get_stream(adapter)`), abonniert die **aktiven** Universum-Epics inkrementell in zwei Modi: (M1) eine `Subscription` pro Epic; (M2) eine `Subscription` mit Item-Liste `["PRICE:{acct}:{e1}", "PRICE:{acct}:{e2}", …]`.
- Fängt je Epic/Modus: `onSubscription`, `onSubscriptionError(code, message)`, `onItemUpdate`-Zähler, Client-Status. JSON-Report je Kombination.
- **Hypothesen, die der Harness unterscheidet (im Report als `hypothesis_hits` markieren):**
  H1 Item-String-Problem (bestimmte Epics erzeugen LS-seitige Item-Name-Fehler),
  H2 Subscription-Anzahl-Limit (IG-seitig, ~40 concurrent **[VERIFY]**),
  H3 Mehr-Item-Subscription vs. Einzel-Subscriptions verhalten sich unterschiedlich,
  H4 Fehler nur bei Epics bestimmter Instrumentklassen.
- Operator-Run während Handelszeiten (Mo–Fr 08:00–22:30 CET), Ergebnis in `phase1_broker_wrapper/lightstreamer_integration_notes.md` als neue Sektion dokumentieren (Konvention der Datei: jede Erkenntnis als Bugfix-/Findings-Block).

### 7b — Fix + LiveQuoteCache + Kontext-Enrichment (eigener Commit, erst nach 7a-PASS)
- Fix in `phase1_broker_wrapper/broker_wrapper/streaming/ig_lightstreamer.py` gemäß Diagnose **[bei Ausführung: exakte Änderung folgt aus 7a — wahrscheinlichste Form: Subscribe-Strategie auf „eine Subscription je Epic" normieren + Epic-String-Validierung vor Subscribe + `onSubscriptionError`-Handler mit per-Epic-Fehlerdurchreichung statt Silent-Fail]**. Public Surface unverändert.
- Neu `broker_wrapper/streaming/quote_cache.py`: `class LiveQuoteCache:` thread-safe (`threading.Lock`), `on_tick(tick) -> None` (als PriceCallback registrierbar), `get(epic) -> LiveQuote | None`, `@dataclass(frozen=True) class LiveQuote:` `epic, bid, ask, ts_iso, age_s(now) -> float`. Kein I/O, reine Struktur.
- **P4-Enrichment (Cross-Phase, Register):** `ResearchConfig` additiv `enable_live_quotes: bool = False`; `context_builder.build_context` bekommt optional `quote_cache: Any | None = None` — gesetzt + Flag an → je tradeable Epic `{"live_bid", "live_ask", "live_age_s"}` in den Epic-Dict **[VERIFY: Render-Stelle im Prompt-Builder; Alter > 120 s → Feld weglassen statt stale anbieten]**. Flag bleibt default aus; Wiring schaltet es erst nach 7a/7b-PASS an.
- Momentum-VETO: **unberührt** (eigener P1-REST-Pfad, nicht Cache).

**Tests:** quote_cache (Threading-sicher via einfachem Concurrency-Test, age-Berechnung, unbekanntes Epic), Subscribe-Strategie-Unit gegen gemocktes SDK (Muster bestehender `test_lightstreamer.py`), context_builder-Enrichment (Flag aus = bit-identisch; an = Felder da; stale = Felder weg).

**Akzeptanz 7a:** Report reproduziert den Fehler und ordnet ihn genau einer Hypothese zu.
**Akzeptanz 7b:** Operator-Re-Run des Harness = PASS für alle aktiven Epics; Research-Kontext enthält bei Flag-an Live-Quotes mit age < 60 s; Flag-aus-Pfad bit-identisch (Regression).

---

## §11 Cross-Phase-Edit-Register (Isolation-Audit)

| Phase | Datei | Änderung | Charakter |
|---|---|---|---|
| P1 | `adapters/ig_adapter.py` | ggf. Feld-Passthrough in `get_market_info` (valueOfOnePip/contractSize/lot_size/name) | additiv **[VERIFY nötig?]** |
| P1 | `streaming/ig_lightstreamer.py` | Multi-Epic-Fix gemäß 7a | Verhalten nur Streaming, Surface stabil |
| P1 | `streaming/quote_cache.py` | neu | additiv |
| P2 | Migration 004 | neue Tabelle | additiv |
| P3 | `external_data/providers.py` | neu | additiv |
| P3 | `external_data/fetcher.py` | optionaler `bar_provider`, Backoff, Circuit | Default-Pfad bit-identisch |
| P4 | `research/models.py` | `enable_live_quotes`-Feld in ResearchConfig | additiv, Default aus |
| P4 | `research/context_builder.py` | optionales quote_cache-Enrichment | Default-Pfad bit-identisch |
| P8 | `scheduler/runner.py` | optionaler `universe_refresher` + Intervall | Default `None` = heutiges Verhalten |
| P8 | `scheduler/observability.py` | neue Event-Typen (bar_fetch, circuit_open, quote_divergence, universe_*) | additiv **[VERIFY Writer generisch genug]** |
| Wiring | `scripts/wiring.py` | build_universe_from_db, Provider-Kette, Refresher, Flag-Schaltung | zentrale Cross-Phase-Konfig (der dafür vorgesehene Ort) |

Nicht angefasst: P5 (Gates/VETOs/Sizing), P6 (Debatte), P7 (Reward). Null LLM-Änderungen.

---

## §12 Step 8 — Operator-Live-Runs (getrennt halten)

**8a — Autonomie-Beweis (V2-Missionskriterium):** Daemon-Start mit Discovery+Promotion
verdrahtet. Erfolg = mindestens **ein net-new Epic** durchläuft
`discovered → verified (inkl. point_value_source gesetzt) → active` **ohne manuellen
Code-Edit** und erscheint im nächsten Research-Zyklus in `tradeable_epics`
(research_health.jsonl + DB als Beweis). Zweitkriterium: STXE/CAC/IBEX-`point_value`
wird im ersten Zyklus per `confirm_curated` bestätigt (oder ehrlich quarantänisiert).
Mehrere Demo-Tage einplanen — kein Single-clean-run-Anspruch (etablierte Erwartung).

**8b — Breaker-Fire-Run (carried-over 5b, unverändert aus dem v1.5-Plan):** Tight-Cap-Run,
ein Safety-Breaker feuert nachweislich live. Bewusst getrennt von 8a (ein Run, ein Beweisziel).

Beide Runs = Operator; Ergebnisse als docs-only Commits (CLAUDE.md `## Session stopped` + Notes).

---

## §13 Post-Steps

1. Doku-Sync: `phase9_universe/CLAUDE.md` As-Built, Root-Docs (ROADMAP-Status, README, ARCHITECTURE §Universe/§Datenpfad), LS-Notes-Sektion aus 7a/7b.
2. SVG `docs/architecture/phase9_v2_concept.svg` (GitHub-Dark, 1080×1080, cairosvg-validiert): Discovery→Validate→Promote-Statusmaschine + Provider-Kette + LS-Pfad.
3. `PHASE10_V3_KICKOFF_HANDOVER.md` im schlanken Format (Status + Delta + offene Entscheidungen + Pfade — neue Handover-Konvention).

---

## §14 Sammelliste **[VERIFY bei Ausführung]**

1. P2-Migrationspfad/-mechanik + Namensschema (Vorlage: Migration 003).
2. Envelope-Felder von `get_market_info` (welche IG-Instrumentfelder heute durchgereicht werden) und `search_markets` (Signatur, Feldnamen `instrument_type`/`market_status`, Referenz `scripts/resolve_epics.py`).
3. P1-`get_ohlcv`-Resolution-Konstanten + Bar-Shape; Fetcher-Bar-Shape; Off-hours-Check-Ort; exakte yfinance-Call-Sites in `fetcher.py`.
4. `scripts/wiring.py` — Ort/Struktur der Universe- und TickerMapper-Verdrahtung.
5. Runner-Konstruktor/Config-Form + State-Tageszähler-Muster.
6. `observability.py`-Writer-API (generischer Event-Writer vorhanden?).
7. Prompt-Render-Stelle für tradeable-Epic-Dicts (Live-Quote-Felder).
8. IG-Demo-Wochen-Allowance für REST-Historical-Bars (Größenordnung, nur Doku/Zähler).
9. IG-Lightstreamer-Concurrent-Subscription-Limit (Hypothese H2).
10. Suchbegriffs-Sprache des Demo-Kontos (deutsche vs. englische Marktnamen).
11. Root-`CLAUDE.md`-Testzahl (181 vs. 173) gegen realen pytest-Count.
12. Restvorkommen von Legacy-Vokabular (Step-0-Grep) — `turbo_candidates.json` ist bekannt-aktiv.

---

## §15 Explizit out of scope (V2)

- Kein neues AI irgendwo (auch nicht für yf_ticker-Mapping — statische Tabelle; AI-Vorschlagspfad wäre V4).
- Keine dritte externe Datenquelle, kein neuer API-Key (D8).
- Keine Abstain-/No-Trade-Lessons (V3), keine DB-Reform jenseits Migration 004 (V3), keine UI-Arbeit (V3, „UI ist das Erste, was fällt").
- Council, Debate-Handover, Reward-Reform, Force-Trigger-Guard, Instinct-ECC (V4).
- Kein Touch an P5-Gates/VETOs/Sizing-Formeln; `point_value` fließt weiter über die bestehende InstrumentSpec-Naht.
- Kein Live-(non-demo)-Konto — die Promotion-Pipeline verweigert es hart per Code.

---

*Ende. Direkt an Claude Code (Sonnet) übergebbar. Erste Aktion dort: Step 0 + 0b,
inkl. `phase9_universe/CLAUDE.md`-Skeleton als allererste Datei.*
