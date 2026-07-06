# Phase 1 (broker_wrapper) — Hardening Plan (V2-Nachzügler)
## Detaillierter Implementierungsplan für Claude Code (Sonnet)

> ✅ **ABGESCHLOSSEN 2026-07-04.** Steps 0–3 alle umgesetzt + committed
> (`a089126` Steps 0–2, `330f531` Step 3). Code-verifiziert 2026-07-06: 429-Retry-Knobs
> in `_request`, `MarketInfo`-Pip-Felder, P1-Suite **85 passed**. Vollständige As-Built-
> Notizen in `phase1_broker_wrapper/CLAUDE.md` (zwei `## Session stopped`-Blöcke). Das
> unten stehende „erst NACH den Live-Tests"-Sequencing wurde durch Nikinger-Freigabe
> überholt (der Plan brauchte keine Live-Tests) — als Historie belassen.

> **Author:** Claude Code (Opus 4.8), 2026-07-04 — Ergebnis des Nikinger-Auftrags
> „scanne die am wenigsten gut geschriebene Phase und schreibe einen Verbesserungsplan".
> **Audience:** Claude Code (Sonnet, medium, Auto-Modus). Ausführungsreif — Entscheidungen
> gelockt, Schritte sequenziert, Anker gegen den echten Code vom 2026-07-04 gepinnt.
> **Sequencing (Nikinger-Vorgabe, verbindlich):** Ausführung **erst NACH den
> Phase-9-Live-Tests** (BarProvider-Flag-Lauf + Step 7a LS-Diagnose), als Teil des
> V2-Bogens. **Kein Code in der Session, die diesen Plan schrieb.**
> **Drift-Konvention:** Datei:Zeile-Anker sind Stand Branch `phase9-v2-foundation`
> (Commit-Bereich 57e7af1 + cosmetic fixes). Alles seither Driftbare ist **[VERIFY]**
> markiert — bei Ausführung gegen den echten Baum prüfen, nie blind übernehmen.

---

## §0 Warum Phase 1 (die Scan-Evidenz, 2026-07-04)

Objektiver Scan aller neun Phasen-Pakete (Zeilen ohne Tests/Scripts, gemockte Testzahl):

| Phase | Zeilen | Tests | Tests/100 Zeilen |
|---|---|---|---|
| **P1 broker_wrapper** | **2256** | **52** | **2.3 ← mit Abstand am niedrigsten** |
| P6 debate | 1490 | 70 | 4.7 |
| P4 research | 2663 | 141 | 5.3 |
| P3 external_data | 1748 | 100 | 5.7 |
| P9 universe | 1068 | 69 | 6.5 |
| P5 execution | 2254 | 154 | 6.8 |
| P7 reward | 1857 | 133 | 7.2 |
| P8 scheduler | 2705 | 217 | 8.0 |
| P2 persistence | 754 | 76 | 10.1 |

Dazu drei **qualitative** Befunde, alle gegen den echten Code verifiziert:

1. **429 → sofortiger Raise, kein Retry** (`ig_adapter.py:321-322`), während 401 einen
   Re-Login-Retry bekommt (`:301-303`). Konsequenz: **fünf** Call-Sites reimplementieren
   Pacing-Disziplin (`pace_s`/`sleep_fn`): `scripts/resolve_epics.py`,
   `scripts/verify_instrument.py`, `scripts/diag_lightstreamer_multi.py`,
   `phase9_universe/universe/discovery.py`, `phase9_universe/universe/promotion.py`.
   Der v1.5-CAC/AEX/IBEX-Resolutionsausfall war exakt dieses Loch (dokumentiert in
   `phase8_scheduler/CLAUDE.md`, Session 2026-07-01 Step 2B: „~35 ungebremste
   Broker-Calls → Rate-Limit-Kaskade"). Die Resilienz gehört **in** `_request`,
   nicht an jede Aufrufstelle (Altitude-Prinzip).
2. **`get_market_info` verwirft IGs Pip-/Contract-Felder** (`ig_adapter.py:440-462`
   parst `instrument` → `MarketInfo` mit exakt 8 Feldern, `models.py` `MarketInfo`).
   IGs `/markets/{epic}`-Antwort trägt `valueOfOnePip`/`onePipMeans`/`contractSize`
   **[VERIFY gegen echte Demo-Antwort — die Feldnamen sind IG-dokumentiert, aber vom
   Repo nie live gedumpt]** — ohne Passthrough bleibt P9s `resolve_point_value`-Pfad 1
   (`ig_fields`, `phase9_universe/universe/pricing.py`) dauerhaft dormant und der
   point_value-Beweis hängt allein an der Namens-Regex-Heuristik (Pfad 2). Der
   Passthrough ist als offener Punkt in `phase9_universe/CLAUDE.md` (Step 2) und im
   Phase-9-Plan §11 (Cross-Phase-Edit-Register, „additiv **[VERIFY nötig?]**")
   bereits vorgemerkt — dieser Plan löst ihn ein.
3. **Test-Lücken genau in der bewiesenen Live-Bug-Klasse.** `test_ig_adapter.py`
   (231 Zeilen, 15 Tests) deckt von ~20 öffentlichen Methoden nur Login/Price/
   Validierung/Close ab. **Ungetestet:** `get_ohlcv`-Happy-Path (Envelope-Shape +
   `_parse_bar`-Mid-Berechnung!), `get_historical_ohlcv`, `get_market_info`,
   `search_markets`, `get_account`, `get_open_positions`, `get_trade_history` +
   `_parse_transaction` (vorzeichenbehaftete Size!), `open_position`-Happy-Path,
   `reconcile_positions`, `_poll_confirms`, der 401-Re-Login-Pfad und der 429-Pfad
   von `_request`. Der Phase-8-Live-Bug vom 2026-06-29 (`'Envelope' object has no
   attribute 'get'`) bewies: **Fakes, die von der echten Shape abweichen, beißen
   live** — und die echten Shapes leben genau hier, ungetestet.

**Bewusst NICHT Teil dieses Plans:**
- **Kein Split von `ig_adapter.py` (930 Zeilen).** Erwogen und **verworfen**: die Datei
  ist groß, aber kohäsiv (ein Adapter, eine API), live-verifiziert seit Phase 1, und
  ein Refactor-Split würde reine Struktur-Ästhetik mit realem Regressionsrisiko auf
  der Order-Pfad-Ebene bezahlen. Weniger ist hier mehr.
- **Kein Lightstreamer-Fix.** Das ist Phase 9 Step 7b (nach 7a-Diagnose), bereits
  geplant — Doppelung wäre Drift-Risiko. Dieser Plan berührt `streaming/` nicht.
- **Keine Envelope-/Public-Surface-Änderung.** Hard Rule 6 (Envelope kanonisch);
  alles hier ist additiv oder rein intern.

---

## §1 Gelockte Leitplanken

- Public Surface stabil: jede bestehende Methode behält Signatur + Envelope-Shape.
  Neue Felder nur **additiv** in `data`-Dicts (Konsumenten lesen per `.get`).
- Default-Verhalten bit-identisch, wo nicht ausdrücklich anders gesagt (Step 1
  ändert 429-Verhalten bewusst — s. dort für die Begründung, warum das sicher ist).
- Kein LLM irgendwo (P1 ist 100 % Code). Kein Live-Test durch Claude (Operator).
- `pytest phase1_broker_wrapper/tests -v` grün nach jedem Step; volle per-Phase-
  Regression am Ende (bekannte `tests.conftest`-Kollision: Phasen separat laufen).
- Atomare Commits, ein Step = ein Commit. `## Session stopped` in
  `phase1_broker_wrapper/`-Notizen **[VERIFY: P1 hat kein eigenes CLAUDE.md im
  Paketwurzel-Stil der späteren Phasen — falls keines existiert, eines nach dem
  P9-Skeleton-Muster anlegen (Step 0) statt Notizen in fremde Phasen zu schreiben]**.

---

## §2 Step 0 — Baseline + P1-CLAUDE.md

1. Volle Regression laufen, Zahlen protokollieren (Erwartung Stand 2026-07-04:
   P1 52 · P2 76 · P3 100 · P4 141 · P5 154 · P6 70 · P7 133 · P8 217 · P9 69 ·
   root 77 — **[VERIFY]**, die Zahlen wachsen mit V2).
2. Falls `phase1_broker_wrapper/CLAUDE.md` fehlt **[VERIFY]**: Skeleton anlegen
   (Muster: `phase9_universe/CLAUDE.md` — Zweck, Konventionen, Statusliste,
   `## Session stopped` leer). P1 ist die einzige Phase ohne dieses Rückgrat.

**Akzeptanz:** docs-only Commit, Baseline dokumentiert.

---

## §3 Step 1 — 429-Retry/Backoff zentral in `_request`

**Ziel:** Die in fünf Call-Sites duplizierte Pacing-Disziplin bekommt ihr strukturelles
Fundament dort, wo jeder IG-Call durchläuft.

**Design (gelockt):**
- In `IGAdapter._request` (`ig_adapter.py:252` **[VERIFY Zeile]**): bei
  `resp.status_code == 429` **nicht** sofort raisen, sondern bis zu
  `retry_429_attempts` (Default **2**) Wiederholungen mit exponentiellem Backoff
  `retry_429_base_s * 2**attempt` (Default Base **1.0 s** → 1 s, 2 s), via
  injizierbarem `sleep_fn` (Konstruktor-Parameter, Default `time.sleep` — Muster:
  P3 `_fetch_with_retry`). Nach Erschöpfung: der bestehende `RateLimitError`,
  unverändert (Envelope-Mapping bleibt identisch).
- **Warum das sicher ist, obwohl es Verhalten ändert:** heute wandelt jede
  aufrufende Ebene den `RateLimitError` ohnehin in einen Error-Envelope/Degrade um
  (kein Caller verlässt sich auf „schneller Fail"); ein 1–3 s späterer Erfolg ist
  in jedem Pfad (Research-Kontext, Verify, Discovery) strikt besser als ein Fail.
  Der **Order-Pfad** (`open_position`/`close_position`) läuft ebenfalls über
  `_request` — dort ist ein 429 heute ein harter Fail eines sicherheitsrelevanten
  Calls; zwei paced Retries verschlechtern nichts (die Order ist noch nicht
  platziert, der Confirm-Poll `_poll_confirms` hat eigenes Timing **[VERIFY: dass
  `_poll_confirms` seine eigenen `_request`-Calls macht — dann bekommt er den
  Schutz gratis]**).
- Konstruktor additiv: `IGAdapter(..., retry_429_attempts: int = 2,
  retry_429_base_s: float = 1.0, sleep_fn: Callable[[float], None] = time.sleep)`
  — Tests injizieren `sleep_fn`, **kein echtes Sleep in Unit-Tests**.
- **Die fünf Call-Site-Pacings bleiben unangetastet** (belt-and-braces: Pacing
  *vermeidet* 429s, der Retry *überlebt* sie — komplementär, keine Duplikation).
  Nur ein dated Kommentar je Datei, dass P1 jetzt zusätzlich selbst retried.

**Tests (≥5, gemockte HTTP-Responses, injiziertes `sleep_fn`):** 429→Erfolg nach
1 Retry (Sleep-Sequenz [1.0] geprüft); 429×3→`RateLimitError` (Sleep-Sequenz
[1.0, 2.0]); `retry_429_attempts=0` → heutiges Sofort-Raise (Opt-out); 401-Re-Login-
Pfad unverändert (Regression-Guard, bisher ungetestet — hier mit abdecken);
kein Sleep bei 200.

**Akzeptanz:** ein simulierter 429-Burst kostet exakt `attempts` Netz-Versuche +
dokumentierte Sleeps und endet im unveränderten Envelope-Fehlerbild.

---

## §4 Step 2 — `get_market_info`-Feld-Passthrough (aktiviert P9-Pricing Pfad 1)

**Ziel:** Der dormante `ig_fields`-Resolver-Pfad (P9 `pricing.py`) bekommt echte Daten.

**Design (gelockt):**
- `MarketInfo` (`models.py`) bekommt drei **additive** Felder mit Default `None`:
  `value_of_one_pip: str | None`, `one_pip_means: str | None`,
  `contract_size: str | None` (als **rohe Strings** — IG liefert Strings, das
  strikte Parsen ist bewusst P9s `_parse_ig_field_value`-Job, eine Wahrheit).
- `get_market_info` mappt sie aus `instr.get("valueOfOnePip")` /
  `instr.get("onePipMeans")` / `instr.get("contractSize")` **[VERIFY Feldnamen
  gegen einen echten Demo-Response-Dump — Operator-Lauf `python - <<'PY' ...`
  oder ein Wegwerf-Script, das den rohen `/markets/{epic}`-Body für die DAX-Epic
  nach stderr dumpt; die Namen sind IG-API-dokumentiert, aber im Repo nie
  verifiziert]**. Fehlende Keys → `None` (to_dict trägt sie dann als `null` —
  additive Konsumenten-Sicht, kein bestehender Reader bricht, alle lesen `.get`).
- **P9-Seite: null Änderung nötig.** `resolve_point_value` liest die Keys bereits
  fixture-getestet (`test_pricing.py`); sobald der Envelope sie trägt, aktiviert
  sich Pfad 1 von selbst (so wurde er in Step 2 der Phase 9 bewusst gebaut).
- Nach dem Passthrough: `promotion.py`s kuratierte Bestätigung bekommt beim
  nächsten Operator-Zyklus erstmals die Chance, STXE/CAC/IBEX über **zwei**
  unabhängige Pfade zu beweisen (ig_fields **und** name_lotsize) — im
  Promotion-Log sichtbar via `point_value_source`.

**Tests (≥4):** Passthrough happy-path (drei Felder im Envelope-`data`); fehlende
IG-Keys → `None`-Felder, kein Crash; bestehende 8 Felder byte-identisch;
`to_dict`-Roundtrip. Plus 1 P9-Integrationstest (Fixture-`market_info` mit
`value_of_one_pip="1"` → `("ig_fields")`-Source — existiert vermutlich schon
**[VERIFY: `test_ig_fields_value_of_one_pip_resolves` deckt genau das]**, dann
nur Cross-Referenz im Commit-Text).

**Akzeptanz:** Operator-`verify_instrument`-Lauf gegen DAX zeigt die neuen Felder
im `market_info`; P9-Regression unverändert grün.

---

## §5 Step 3 — Test-Backfill der ungetesteten Adapter-Flächen

**Ziel:** Die Live-Bug-Klasse „Fake weicht von echter Shape ab" strukturell
austrocknen — Envelope-`data`-Shapes und Parser sind die Priorität, nicht
Coverage-Prozente.

**Reihenfolge (nach Live-Risiko):**
1. `_parse_bar` (Mid-Berechnung bid/ask, fehlende Seiten **[VERIFY: was tut
   `mid()` bei `None`-bid/ask heute?]**) + `get_ohlcv`-Happy-Path
   (Envelope trägt `{"bars": [...], "allowance": ...}` — exakt die Shape, auf die
   sich P9s `IGBarProvider` verlässt; dieser Test ist der Regressions-Guard für
   die 2026-07-04-Wiring-Verifikation).
2. `_parse_transaction` + `get_trade_history` (vorzeichenbehaftete Size, kein
   `deal_id` — die P7-Reconcile-Heuristik hängt an dieser Shape).
3. `get_market_info` (nach Step 2 ohnehin fällig) + `search_markets`
   (P9-Discovery-Grundlage, `instrument_type`/`market_status`-Mapping
   `ig_adapter.py:480-493` **[VERIFY]**).
4. `open_position`-Happy-Path inkl. `_poll_confirms`-Mock (ACCEPTED/REJECTED),
   `reconcile_positions`, `get_open_positions`/`_parse_position`, `get_account`.
5. `_request`-Kernpfade, soweit nicht schon in Step 1 gedeckt (401-Re-Login,
   Header-Aufbau v2/v3).

**Konvention:** gemockte `requests`-Responses (bestehendes `test_ig_adapter.py`-
Muster **[VERIFY dessen Mock-Idiom — monkeypatch auf `requests.request` oder
Session?]**), kein Netz. Erwartung grob **+25–35 Tests** (P1 52 → ~80+),
Detailzahl ist Ergebnis, kein Ziel.

**Akzeptanz:** jede öffentliche Adapter-Methode hat mindestens einen
Happy-Path-Test, der die **echte** Envelope-`data`-Shape asserted (Feldnamen +
Typen), + die dokumentierten Fehlerpfade.

---

## §6 Cross-Phase-Impact-Register

| Phase | Wirkung | Charakter |
|---|---|---|
| P3/P4/P8 | 429-Bursts enden seltener im Degrade (Retry in P1) | Verhalten nur besser, Shape identisch |
| P5 | Order-Pfad-Calls erben den 429-Retry | additiv, VETO/Gate-Logik unberührt |
| P9 pricing | Pfad 1 (`ig_fields`) aktiviert sich von selbst | null P9-Code-Änderung |
| P9 promotion | `confirm_curated` bekommt Zwei-Pfad-Beweis-Chance | null P9-Code-Änderung |
| scripts/* | Pacing bleibt (belt-and-braces), nur dated Kommentar | docs-only |

**Nicht angefasst:** `streaming/` (Step 7b), Envelope-Modul, `filters.py`,
`credentials.py`, alle VETOs/Gates/Sizing (P5), jede LLM-Fläche.

---

## §7 Akzeptanz des Gesamtplans

- P1-Suite deutlich verdichtet (~52 → ~80+), alle Phasen separat grün.
- Ein simulierter 429-Burst wird in P1 selbst überlebt (Tests beweisen es).
- `get_market_info`-Envelope trägt die drei Pip-Felder; ein Operator-
  `verify_instrument`-Lauf zeigt sie live; P9-Pricing kann Pfad 1 feuern.
- Kein Public-Surface-Bruch: P3–P9-Regression unverändert grün ohne Test-Edits
  außerhalb P1 (einzige Ausnahme: ggf. neue **additive** Asserts).
- P1 hat ein `CLAUDE.md` mit Status + `## Session stopped`-Konvention.

---

*Ende. Ausführung: Sonnet (medium, Auto-Modus), NACH den Phase-9-Live-Tests,
als Teil des V2-Bogens — Nikinger triggert den Start.*
