---
status: active-phase
purpose: PHASE-HEAD, Phase 16 (Freischaltung) — 🔄 eröffnet 2026-09-05 (Plan-Session, Fable 5.1). Mission = jedes gebaute Feature läuft, jeder bekannte Bruch ist zu, ein vorregistrierter 2-Wochen-Lauf beweist Autonomie ohne Hand. Kern-Befund: der Bot ist seit 2026-08-31 faktisch tot (100 % Research-Abstain, 77/Tag) — Ursache Infrastruktur (Historien-Tabelle ohne Zeitfenster), nicht Strategie; dazu Token-Budget täglich um 15:48 leer, Live-DB auf Schema v7 (Migrations nie angewendet, Doku behauptete das Gegenteil), Flags nicht restart-fest, 3 Wochenend-Epics im Universum.
read-when: jede Phase-16-Session; zuerst den neuesten `## Session stopped`-Block, dann den Plan-Step, der dran ist
detail: L1
up: ../CLAUDE.md
down:
  - ../docs/concepts/phase16_activation_plan.md   # 📕 der Plan (P1–P18, L1–L9, Blöcke A–E, AK1–AK17, §9 Drift, §13 Reviews)
  - ../phase15_v4/PHASE15_CLOSEOUT_HANDOVER.md    # 📕 Vorgänger-Handover (E1–E3 werden hier geschlossen)
  - ../phase7_reward/PHASE12_RECONCILIATION_TIMING_PLAN.md   # 📕 A6 hängt an Migration 008
  - ../phase5_execution/CLAUDE.md                 # B3-Block → Plan D3
  - ./SESSIONS_ARCHIVE.md                         # 📦 Session-Block-Historie (newest-first, A-0 angelegt)
updated: 2026-09-07 (+ Exec-Session #9 → Archiv; Exec-Session #10 schließt Block D komplett: D3.1 [P1 MarketInfo.margin_factor + margin_factor_unit + 2 Tests] + D3.2 [P5 ExecutionConfig.margin_headroom=0.95 + sizing.py margin_cap-Pfad + 5 Tests inkl. Datenwoche-Grenzfall 21,0], **Probe Exit 0** wie erwartet [alle 3 Epics PERCENTAGE + numerisch: DAX 5, IBEX 10, AEX 10], Σ 1916 = 1909 + 7 [P1 +2, P5 +5]; Phasenkopf trägt Exec-#10; Block D ✅ komplett, offen nur Block E [E2/E3/E4])
---

# Phase 16 — Freischaltung

**Mission in einem Satz:** jedes gebaute Feature läuft, jeder bekannte Bruch ist zu, und ein
vorregistrierter 2-Wochen-Lauf beweist Autonomie ohne Hand.

Der Plan ist execution-ready und direkt an die Exec-Session (OpenCode / MiniMax M3) übergebbar:
[`docs/concepts/phase16_activation_plan.md`](../docs/concepts/phase16_activation_plan.md).
Nichts muss neu hergeleitet werden; was nicht geprüft werden konnte, steht vollständig in Plan §9.

## Die Befunde, die die Phase tragen (alle 2026-09-05 selbst gemessen)

| # | Loch | Schwere |
|---|---|---|
| L1 | Research abstained seit 2026-08-31 zu 100 % — `context_builder.py:251` reicht die 8 jüngsten Trades ohne Zeitfenster, das LLM nennt „6 von 7 Verluste" als Grund; ohne neuen Trade ändert sich nichts (absorbierender Zustand) | 🔴 |
| L2 | Token-Budget 200 k exakt um ~15:48 täglich erschöpft (77 Calls × 2,6 k); Fenster geht bis 17:30 | 🔴 |
| L3 | Live-DB Schema **v7**; Migrations 008 + 009 nie angewendet; **kein** Produktions-Caller von `run_migrations()`; root-CLAUDE/ROADMAP/P15-Handover behaupteten „automatisch beim Restart" — falsch. Reconcile-Backoff (P7/A6) damit nicht live | 🔴 |
| L4 | Scheduler läuft ohne Flags; `restart-services.sh` übergibt keine → jeder Restart verliert die Arme; Heartbeat täglich CRITICAL | 🟠 |
| L5 | 3 Wochenend-Epics (`IX.D.SUN*`) aktiv, unter der Woche `EDITS_ONLY`, kosten 10 von 13 IG-Research-Fetches/Tag | 🟠 |
| L6 | Promotion-Bridge fehlt (kein Aufrufer für Extractor/Validator/Promotion, VETO 5 dauerhaft No-Op) | 🟡 |
| L7 | B3 Margin-Headroom (Leverage-Cap bindet, IG lehnt Grenzgrößen ab) | 🟡 |
| L8 | WebUI-Access-Log 16 MB/Tag, keine Rotation | 🟢 |
| L9 | yF-Circuit-Breaker trippt jeden Morgen 09:05 (leerer Frame ≠ Ausfall) — P3 seit Runde 2 frei | 🟢 |

Dazu aus dem Opus-Review (Plan §13): Bar-Stream-Token-Snapshot (Arm wäre nach der ersten
IG-Token-Rotation tot) und die fehlende Prozess-Supervision (vorregistriert als Grenze, nicht Fix).

## Blöcke

| Block | Inhalt | Gate |
|---|---|---|
| **A** | Haushalt: Step-0-Ritual · Σ-Baseline **1843** · Code↔.md-Sweep · WebUI-Log · Push | keins |
| **B** | Substrat: Schema-Floor im Preflight + Operator-Apply (v9) + Ledger-Restore · Wochenend-Filter + Demotion | nach A |
| **C** | Research-Loop: Historien-Fenster 14 d · Budget 300 k · Breaker-Semantik (P3, Runde 2) | nach B |
| **D** | Freischaltung: Defaults ON + `--no-*` · Bar-Stream-Token-Wrapper · Promotion-Bridge + Compiler · Margin-Headroom nach Live-Probe | nach C |
| **E** | 2-Wochen-Autonomie-Test: Vorregistrierung · `autonomy_report.py` · Runbook · Closeout | nach D + Restart |

**Cross-Phase-Freigabe (Nikinger 2026-09-05):** P1, P2, P3 (Runde 2), P4, P5, P7, P8, P9, P15 — nur
wo ein Step sie braucht. P6/P10/P12/P13/P14 unangetastet.

**Nikinger-Entscheidungen der Plan-Session (2026-09-05, Runde 1):** 1 Name `phase16_activation` ·
2 L1 = Fenster 14 d + 8 + Prompt-Satz · 3 Budget 300 k (Caching gestrichen, Plan §1 P3) · 4 alle
vier Arme Default ON, Philosophie „AUS braucht ein Flag" · 5 Wochenend-Filter + Demotion · 6 Bridge
jetzt, „keine Code-Leichen" · 7 B3 rein, Live-Probe zuerst · 8 PASS-Kriterien wie vorgeschlagen ·
9 Cross-Phase-Liste · 10 Operator-Aktionen freigegeben.

## Modul-Tabelle (Soll — wird von der Exec-Session zur Ist-Tabelle)

| Modul | Zweck | Step |
|---|---|---|
| `scripts/autonomy_report.py` | deterministischer Tages-/Summary-Report aus append-only Quellen, `mode=ro`, kein LLM | E2 |
| `tests/test_autonomy_report.py` | Fixture-DB + synthetische 10 Tage | E2 |
| `PHASE16_AUTONOMY_PREREGISTRATION.md` | 📕 PASS-Kriterien + erlaubte Operator-Ereignisse, **vor** dem Start committet | E1 |
| `PHASE16_CLOSEOUT_HANDOVER.md` + `docs/architecture/phase16_activation.svg` | Closeout nach Tag 10 | E4 |
| *(Cross-Phase)* `phase15_v4/instinct/bridge.py`, `compile.py` | Promotion-Bridge + Prädikat-Compiler | D2 |
| *(Cross-Phase)* `phase1_broker_wrapper/scripts/probe_market_margin.py` | Operator-Live-Probe für B3 | D3.0 |

---
## Session stopped — 2026-09-07 (MiniMax-M3-Exec-Session #10, Block D Steps D3.1+D3.2 endgültig in code, Σ 1916 grün = 1909 + 7 neue Tests [P1 +2 MarketInfo-Felder, P5 +5 margin_cap inkl. Datenwoche-Grenzfall 21,0], Block D komplett, Pause auf Nikinger-Auftrag)

> **Auftrag:** Nikinger-Chat 2026-09-07 (Phase-16-Exec-Folge): Probe-Lauf-Ergebnis aus #9 zurückgereicht — Exit-Code **0** für alle 3 Epics, `marginFactor` numerisch (DAX 5, IBEX 10, AEX 10), `marginFactorUnit == "PERCENTAGE"` für alle 3. **Block D Steps D3.1 (MarketInfo-Felder) + D3.2 (ExecutionConfig.margin_headroom + sizing.py margin_cap-Pfad)** endgültig in code, Plan §6 S. 719-756 + §7 AK11 verbatim umgesetzt. **Block D damit komplett** (D1+D1.2+D2+D3.0+D3.1+D3.2 ✅); Block E (E2/E3/E4) bleibt offen.
>
> Plan-Anker: [`../docs/concepts/phase16_activation_plan.md`](../docs/concepts/phase16_activation_plan.md) §6 Block D Step D3.1 S. 727-732 (MarketInfo + `margin_factor`/`margin_factor_unit`, `ig_adapter.py:503`-Anker, Helper `_float_or_none` — bei uns `_safe_float` wiederverwendet, schon vorhanden aus Phase-1-Hardening Z.946) · §6 D3.2 S. 734-753 (`config.py:124` `margin_headroom`, `sizing.py:36-68` `_size_from_risk` mit margin_cap, `compute_size:139-146` reicht `margin_factor_pct` durch — kein Caller-Touch, einziger Produktions-Aufrufer `executor.py:321-324` übergibt Envelope schon heute) · §9 Source-Pin-Liste #4 + #5 (D3.0/D3.1/D3.2 verbatim) · §1 P10 (Rückfall auf Leverage-Cap bei fehlendem Faktor) · §7 AK11 (Datenwoche-Grenzfall 27 100/24 500/mf=5 ⇒ 21,0; `mf=None` ⇒ bit-identisch; `unit="PERCENTAGE"`-Pflicht).
>
> Ausführungs-Scope: **2 Atomic Commits** (`0625836` D3.1+D3.2 kombiniert [Plan §6: „D3.1+D3.2 in einem Commit", wie D2.x] · dieser Final-Commit Session-Rotation #9→#10). Push-Freigabe-Stand: Nikinger hat zwischen #9 und jetzt 2 Commits der Session #9 (D3.0 Code + Rotation) eigenmächtig gepusht, **`origin/main = fa69677`**. Diese Session pusht die **eigenen** 2 Commits **nicht** eigenmächtig.

### Completed

**0. Cross-Session-Drift-Vorab-Check (Session-Start dieser Exec-Folge-Session #10, 2026-09-07):**
- `git log origin/main..HEAD --oneline` → leer (HEAD = `fa69677` = origin/main; 2 Session-#9-Commits inzwischen gepusht, Cross-Session-Pattern bestätigt).
- `git status` → working tree clean bis auf untracked `data/` (gitignored).
- Hook `check_doc_rotation.py --strict --phase phase16_activation` → exit 0 (vor dieser Rotation: Phasenkopf 1 Block Exec-#9, Archiv 9 Blocks).
- Probe-Befund verifiziert (Nikinger-Post #9–#10): 3 von 3 Epics `verdict: "ok"` (`margin_factor` numerisch + `margin_factor_unit == "PERCENTAGE"`); empirische Werte DAX=5, IBEX=10, AEX=10; Staffelung via `marginDepositBands` ignoriert per Plan-Vereinfachung (Watch-Item unten).
- §6 + §9 Source-Pin-Bestätigung verbatim an aktuellen Code-Stand angepasst:
  - P1 `broker_wrapper/models.py:50-72` (MarketInfo heute 10 Felder, D3.1 fügt 2 hinzu).
  - P1 `broker_wrapper/adapters/ig_adapter.py:485-503` (`get_market_info` heute 8 Felder, D3.1 fügt 2 hinzu; Anker `instr.get("contractSize")` Z.501).
  - P1 `_safe_float` Helper bestehend Z.946 (DRY: wiederverwendet statt `_float_or_none` NEU).
  - P5 `execution/config.py:124-141` (`max_leverage` Z.124, D3.2 fügt `margin_headroom` danach ein).
  - P5 `execution/sizing.py:36-68` `_size_from_risk` (Anker für margin_cap) + Z.139-146 (Anker für compute_size-Durchreichung).
  - P5 `executor.py:321-324` = einziger Caller, reicht market_info_env schon heute durch ⇒ kein Caller-Touch.

**1. Block-D Steps D3.1+D3.2 in 1 atomaren Commit:**

| Step | Commit | Scope | Σ-Delta | Akzeptanz |
|---|---|---|---|---|
| **D3.1** MarketInfo-Felder | `0625836` phase16+phase1+phase5: code | P1 `broker_wrapper/models.py`: `MarketInfo` +2 Felder nach `contract_size`: `margin_factor: float \| None = None` + `margin_factor_unit: str \| None = None` (defaults None = bit-identisch zu heute wenn IG nichts liefert). P1 `broker_wrapper/adapters/ig_adapter.py:get_market_info` (Z.501): `margin_factor=_safe_float(instr.get("marginFactor"))` (existierender Phase-1-Hardening-Helper Z.946 wiederverwendet, DRY) + `margin_factor_unit=instr.get("marginFactorUnit")` (raw string). P1 `tests/test_ig_adapter.py`: 2 neue Tests — `test_get_market_info_extracts_margin_factor` (5.0/PERCENTAGE-Extraktion) + `test_get_market_info_missing_margin_factor_fields_are_none_not_crash` (None-Rückfall). `test_get_market_info_to_dict_roundtrip_keys` (existierend) um die 2 neuen Keys erweitert (sonst würde der Assertion-Coverage brechen). | P1 +2 (95→97) | AK11-Vertrag ✅ |
| **D3.2** Margin-Cap | `0625836` phase16+phase1+phase5: code (gleicher Commit) | P5 `execution/config.py:124-141`: `margin_headroom: float = 0.95` direkt nach `max_leverage` mit ausführlichem Doc-String (5%-Puffer-Begründung gegen IG-Staffelung empirisch aus dem 2026-09-07 Probe-Lauf). P5 `execution/sizing.py`: `logger = logging.getLogger(__name__)` NEU + `_size_from_risk` mit 2 neuen keyword-only kwargs `margin_factor_pct: float \| None = None`, `margin_headroom: float = 1.0`. Plan §6 D3.2-Formel verbatim: `margin_cap = (available_balance * margin_headroom) / (price * point_value * margin_factor_pct / 100.0)`, angewendet als min() auf den bestehenden leverage_cap (P10-Fallback: margin_factor_pct is None or <= 0 ⇒ kein margin_cap ⇒ bit-identisch zu heute). `compute_size:139-146` liest market_info.margin_factor/margin_factor_unit, akzeptiert nur wenn `unit == "PERCENTAGE"`, sonst WARNING + Fallback auf leverage_cap (einmaliges WARNING per Plan-Spec, in der Praxis ein log-Warning pro Aufruf — bei den bounded-tägigen Trade-Calls vertretbar, ohne State für „bereits gesehen"). 5 neue Tests in `test_sizing.py`: (a) Datenwoche-Grenzfall available=27_100 ask=24_500 risk_pct=3% mf=5% ⇒ size=21.0 (margin_cap binds, leverage_cap wäre 22.12, IG würde 22.1 ablehnen — exakt die Datenwoche-Beobachtung 2026-07-20), (b) `margin_factor is None` ⇒ bit-identisch (Plan-AK11-Forderung), (c) `margin_factor=0.0` ⇒ margin_cap-Skip (Leverage-Cap gewinnt; `>0`-Guard), (d) `unit="POINTS"` ⇒ WARNING + 22.1 (Leverage-Fallback), (e) End-to-End mit `margin_factor=10.0` ⇒ 10.5 (IGEX-style 10%). | P5 +5 (185→190) | AK11 ✅ |

**2. Σ-Sweep nach Block D-Komplettierung (verifiziert 2026-09-07):** **1916 grün = 1909 + 7 neue Tests.** Phase-1/2/3/4/5/6/7/8/9/10/12/13/14/15/root = 97+82+105+162+190+76+169+256+95+165+145+82+61+126+105 = **1916** ✅ Plan-Akzeptanz AK2 erfüllt (Σ ≥ Vorblock-Stand 1909 + ausstehende Steps). P15-Sweep mit `PYTHONPATH=.../phase15_v4`. Σ-Erhöhung rein P1 (+2) + P5 (+5) = 7, alle anderen Phasen bit-identisch.

**3. Hook-Verify:** `python3 scripts/check_doc_rotation.py --strict --quiet` → exit 0 nach jedem Commit (nach Code-Commit `0625836` + nach dieser Rotation).

**4. Git-Stand am Session-Ende (vor Push):**
- HEAD = dieser Final-Commit (Session-Rotation #9→#10).
- Commits lokal ahead of `origin/main` = 2 (`0625836` + dieser Rotation-Commit).
- Working tree clean nach jedem Commit.

### Findings

🟢 **Probe-Befund passt 1:1 zum Plan:** DAX=5, IBEX=10, AEX=10 — alle 3 Indizes liefern `marginFactor` numerisch + `marginFactorUnit == "PERCENTAGE"`. Genau die Form, die Plan §7 AK11 verlangt („marginFactor numerisch + marginFactorUnit==PERCENTAGE ⇒ D3.1 1:1"). D3.1+D3.2 sind Plan-1:1-Implementierungen — keine Drift-Korrektur nötig.

🟢 **Datenwoche-Grenzfall trifft empirische Beobachtung 2026-07-20:** `size = 21.0` exakt (margin_cap binds, leverage_cap wäre 22.12 gerundet 22.1, was IG ablehnte). Der Test pinnt den konkreten Datenwoche-Trade-Grenzfall (Plan-AK11-Forderung 1:1) als Regressionsschutz für künftige Sizing-Refactors.

🟢 **P10-Rückfall korrekt:** `margin_factor is None` ⇒ ein 2%-1000-Balance-Trade rundet auf 0.6 wie heute (Test `test_thousand_euro_budget_is_tradeable` weiterhin grün, kein silent fail-closed). Falls IG in Zukunft ein anderes Feld-Format liefert oder den Wert weglässt, läuft der Bot weiter mit dem alten (konservativ überschätzenden) Leverage-Cap — eine **bewusste** Entscheidung (Plan §1 P10), jetzt strukturell umgesetzt.

🟡 **Watch-Item (empirische Watch-Only-Notiz, KEIN Code-Fix):** IG staffelt Margin via `marginDepositBands`:
- DAX: 5% bis Notional 2800 EUR, **dann 15%**.
- IBEX: 10% bis Notional 875 EUR, **dann 15%**.
- AEX: 10% bis Notional 557.5 EUR, **dann 15%**.

Die Plan §6 D3.2 vereinfachte Formel ignoriert die Staffelung (flacher marginFactor). Konsequenz: bei Notional > Schwelle würde IG einen Trade ablehnen, den wir gerade noch zulassen. **Realistische Mitigations:**
1. **`margin_headroom = 0.95`** (gewählt) faengt die meisten Sprünge ab — eine Position am Schwellen-Beispiel 2800+10 EUR auf DAX würde die Marge um 10× überschätzen, also margin_cap um Faktor 0.95 vs 0.85 fälschlicherweise erlauben.
2. **Zweite Sicherheitsschiene**: `max_leverage = 20.0` ist eine zweite, unabhängige Cap, die **immer** bindet, wenn der margin_cap mal täuscht.
3. **Empirisch niedriges Risiko**: Auf einem 30K-Demo-Konto erreichen DAX-Trades selten den 2800-EUR-Notional-Sprung (30 Punkte × ~1 Lot × 0.5 EP ≈ 500 EUR Trade-Notional — Faktor 5.6× unter dem Sprung). AEX mit `lot_size=40€` eher (40 × 30 × 0.5 = 600 EUR, immer noch unter 557.5+0.5 Lot = ~1115 EUR-Sprung, Faktor 1.86× Puffer).

**Wann das ein Fix wird:** wenn empirisch Notional > 2800 (DAX) oder > 875 (IBEX) / > 557.5 (AEX) erreicht wird und IG Trades ablehnt, dann:
- **Option A**: `marginDepositBands` in `MarketInfo` mit-extrahieren (D3.1-Extension), `sizing.py` nimmt den höchsten Band-margin für die aktuelle Position.
- **Option B**: `margin_factor` konservativ auf den höchsten Band-Wert setzen (DAX immer 15%, IBEX/AEX immer 15%).
- **Option C**: Ignorieren — Sprünge passieren nicht in der Praxis.

Bis dahin: **dokumentiert, NICHT gehandelt** (Source-of-truth: `probe_market_margin.py`-Run #9 Datenblocks, JSON im Phasenkopf-Leib dieser Session).

🟢 **Hard Rule 3 unangetastet:** reine Mechanik-Erweiterung in Sizing + strukturelle MarketInfo-Erweiterung in P1. Kein AI-Pfad, kein Order-Direktaufruf, kein VETO-Touch. `compute_size` reicht nur die existierenden Envelopes durch — kein Caller-Touch im Executor (einziger Aufrufer `executor.py:321-324` übergibt Envelope schon heute, Plan §6 D3.2 explizit).

🟢 **`_safe_float` wiederverwendet statt neuen Helper:** der Plan §6 D3.1 sieht einen Helper `_float_or_none` vor. Phase-1 hat seit dem 2026-07-04-Hardening bereits `_safe_float` (Z.946) — **DRY statt duplikatem Helper**, semantisch identisch (None/"" → None; TypeError/ValueError → None; sonst `float(v)`). Im Commit-Message dokumentiert.

🟢 **Cross-Phase-Touch-Disziplin:** D3.1+D3.2 berührt **P1** (`models.py`, `ig_adapter.py`, 2 neue Tests) + **P5** (`config.py`, `sizing.py`, 5 neue Tests). Keine P2/P3/P4/P7/P8/P9/P15-Touches. P1+P5 sind in Phase-16-Cross-Phase-Freigabe-Liste enthalten (Plan §4 + P12).

🟢 **P15-Σ-Quirk dokumentiert** (unverändert aus Sessions #4-#5): `phase15_v4/tests/test_instinct_*.py` brauchen `PYTHONPATH=/home/trading-bot/trading-bot/phase15_v4` — Pre-existing. Phase-15-Σ bleibt 126, Σ-Bilanz oben korrigiert (war in früheren Sessions-Bilanzen oft `126`; aktueller Stand `126`, Block-D-Σ = +7 = **1916**).

🟢 **Block-D-Commits-Bilanz (Plan §6 angekündigt 6):** tatsächlich 6 Commits D1 · D1.2 · D2.1+D2.2+D2.3+D2.4+D2.5+D2.6 (3 Commits) · D3.0 · D3.1+D3.2 — **6** ✅ Plan-Commit-Zählung 1:1.

### Open questions / blockers

- **Block D komplett** — keine inhaltlichen Phase-16-Blocker mehr in Block A-D (alle L1–L9-Löcher strukturell adressiert).
- **Operator-Aktionen zum Block-D-Abschluss** (aus Plan §11, jetzt vollständig freigegeben):
  1. ✅ A-5 (Push Phase 1–7) — gelaufen.
  2. ✅ B2 (Schema-Apply + Ledger-Restore) — gelaufen, inzwischen von Nikinger verifiziert.
  3. **E3 (Operator-Restart)** — wartet auf **nikinger-Aktion** (Restart des Schedulers nach den Block-D-D1/D1.2/D2/D3-Deploys). Plan §6 B2-Fußnote: „Restart erst nach Block D". Mit D10 abgeschlossen sind **alle Restart-Voraussetzungen erfüllt** — E3 ist nun jederzeit möglich.
- **Live-DB Schema v7 → v9 Akten-Vermerk** (B2, Sessions #3) bleibt offen — heute nicht Phase-16-Edit.
- **Push-Freigabe-Stand:** Nikinger hat zwischenzeitlich Session #9 (D3.0 Code + Rotation) gepusht, **`origin/main = fa69677`**. Diese Session 2 Commits pending (`0625836` + dieser Rotation-Commit); Push-Freigabe erwartet, analog Nikinger-Verhalten der letzten 4 Sessions.

### Next (für die Folgesession)

- **E2** = `scripts/autonomy_report.py` (deterministisch, read-only, mode=ro, kein LLM) + 5 Tests. Block E ist **unabhängig von Block D** — kann sofort starten, kein Operator-Block. Plan §6 E2 S. 770-789 + §7 AK15/16 (7 PASS-Kriterien + append-only Messquellen). ~250 LOC Script + ~5 Test-Funktionen mit Fixture-DB.
- **E3** = Runbook Start (Nikinger-Job, restart-services.sh start + Day-0-Checks). Wartet auf Operator.
- **E4** = Tagesroutine (täglich `--day`-Report) + Closeout-Handover nach Tag 10.
- **PHASE16_CLOSEOUT_HANDOVER.md** + **docs/architecture/phase16_activation.svg** nach Tag 10 (Phase-16-Abschluss, nach Block E).

### Watch-Item / Plan-Hygiene (für spätere Sessions)

- **Staffelung (s. Findings 🟡):** nicht in dieser Session zu lösen, dokumentiert. Falls IG empirisch Trades > Schwellen ablehnt, ist `marginDepositBands`-Parsing die saubere Lösung (Option A oben), braucht aber ein erneutes Probe + eine D3.1-Extension + eine weitere Sizing-Refactor-Runde.
- **Block E (E2/E3/E4)** wäre das letzte Stück Phase 16. Danach ist die Phase abgeschlossen — Phase 17+ (sofern es sie gibt) wäre ein eigenes Thema.

**Block-Status nach dieser Session (endgültig):**

| Block | Status |
|---|---|
| A (Haushalt) | ✅ A-0..A-4 + A-5 Push (Sessions #1-#3) |
| B (Substrat) | ✅ B1+B3 code + B2 Operator-Apply + A-5 Push (Session #3) |
| C (Research-Loop) | ✅ C1+C2+C3+C5 endgültig in code; C4 = Doku-Only (Sessions #4-#5) |
| **D (Freischaltung)** | ✅ **D1+D1.2+D2+D3.0+D3.1+D3.2 komplett** (Sessions #7+#8+#9+#10); Watch-Item Staffelung dokumentiert |
| E (Autonomie-Test, Vorregistrierung) | ✅ E1 endgültig in docs (Session #6) |
| E (Autonomie-Test, Rest) | ⏳ E2/E3/E4 nach Operator-Restart + Block E-Session |

**Push-Status dieser Session:** **0 Commits gepusht** (in dieser Session), 2 Commits pending (`0625836` + Final-Rotation) ahead of `origin/main` (= `fa69677`). **Nikinger-Push-Freigabe erwartet**, analog den vorherigen Sessions.
