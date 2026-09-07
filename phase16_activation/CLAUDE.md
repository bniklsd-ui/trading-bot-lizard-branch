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
updated: 2026-09-07 (+ Exec-Session #8 → Archiv; Exec-Session #9 liefert D3.0 Operator-Probe-Skript [L7, AK11, P1 only], Σ 1909 unverändert [operator-run per P1-Convention], wartet auf Nikinger-Probe-Lauf bevor D3.1+D3.2; Phasenkopf trägt Exec-#9)
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
## Session stopped — 2026-09-07 (MiniMax-M3-Exec-Session #9, Block D Step D3.0 Operator-Probe-Skript endgültig in code, Σ 1909 grün unverändert [operator-run per P1-Convention], Pause auf Nikinger-Probe-Lauf)

> **Auftrag:** Nikinger-Chat 2026-09-07 (Phase-16-Exec-Folge, nach D1.2-Pause): „lass und D3 vorbereiten" — **Block D Step D3.0** (Plan §6 D3.0, L7, P1/P5, AK11) endgültig in code: `phase1_broker_wrapper/scripts/probe_market_margin.py` NEU, operator-run, ~3 GET-Requests gegen IG Demo, 0 Datenpunkte. **Code-Teil fertig**; **Live-Probe ist Nikinger-Job** (Phase-1-Smoke-Konvention: `smoke_test.py` + `test_lightstreamer.py` ebenfalls operator-run, ohne pytest). D3.1 (MarketInfo.margin_factor + margin_factor_unit extrahieren) und D3.2 (sizing.py: cap_size mit margin_factor-Erweiterung + ExecutionConfig.margin_headroom-Feld) folgen in der nächsten Session gegen die Probe-Befunde. Block E (E2/E3/E4) bleibt Alternative falls D3 weiter vertagt wird.
>
> Plan-Anker: [`../docs/concepts/phase16_activation_plan.md`](../docs/concepts/phase16_activation_plan.md) §6 Block D Step D3 (S. 717-756) · §6 D3.0 S. 719-725 (Probe-Skript-Bauanleitung verbatim) · §9 Source-Pin-Liste #4 („D3.0 Skript") · §13 Opus-Review #1 (IG-Margin-Felder unbestätigt) · §1 P13 (Operator-Aktion als Live-Probe) · §1 P10 (Rückfall auf Leverage-Cap statt fail-closed, weil ein fehlender Faktor sonst den Test still auf 0 Trades stellt) · §7 AK11 (Verifikation der Form via 22,0/22,1-Trade-Grenzfall) · Cross-Phase-Freigabe P1 (Phase-1-Convention, operator-run + keyring, im Plan §4 + P12 gelockt).
>
> Ausführungs-Scope: **2 Atomic Commits** (`1761827` D3.0 Probe-Skript · dieser Final-Commit Session-Rotation #8→#9). Push-Freigabe-Stand: Nikinger hatte zwischen Session #8 und jetzt 2 Commits der Session #8 (D1.2 Code + Rotation) gepusht, **`origin/main = 468ce3d`**. Diese Session pusht die **eigenen** 2 Commits **nicht** eigenmächtig.

### Completed

**0. Cross-Session-Drift-Vorab-Check (Session-Start dieser Exec-Folge-Session #9, 2026-09-07):**
- `git log origin/main..HEAD --oneline` → leer (HEAD = `468ce3d` = origin/main; 2 Session-#8-Commits inzwischen gepusht).
- `git status` → working tree clean bis auf untracked `data/` (gitignored).
- Hook `check_doc_rotation.py --strict --phase phase16_activation` → exit 0 (vor dieser Rotation: Phasenkopf 1 Block Exec-#8, Archiv 7 Blocks).
- §6 + §9 Source-Pin-Bestätigung:
  - P1 `broker_wrapper/adapters/ig_adapter.py:479-513` `get_market_info` (Anker für D3.1; heute ohne `marginFactor`/`marginFactorUnit`-Extraktion — bestätigt).
  - P1 `broker_wrapper/adapters/ig_adapter.py:264-355` `_request` (wird für die Probe genutzt; Plan-Vorgabe `IGAdapter._request("GET", ...)`, privater API-Zugriff aus einem intra-Package-Operator-Skript — gleiche Konvention wie `smoke_test.py` intern via `get_broker`).
  - P1 `broker_wrapper/models.py:50-67` `MarketInfo` (8 Felder heute; D3.1 fügt 2 hinzu: `margin_factor`, `margin_factor_unit`).
  - P5 `execution/sizing.py:36-68` `_size_from_risk` + `execution/config.py:124` (Anker für D3.2; `max_leverage` heute = 20.0).
  - Pattern-Vorlage: `scripts/smoke_test.py` (sys.path.insert, `get_broker`, `connect()`/`disconnect()`, Envelope-Print, Exit 0/1).

**1. Block-D Step D3.0 in 1 atomaren Commit:**

| Step | Commit | Scope | Σ-Delta | Akzeptanz |
|---|---|---|---|---|
| **D3.0** Probe-Skript | `1761827` phase16+phase1: code | **NEU** `phase1_broker_wrapper/scripts/probe_market_margin.py` (253 LOC, ~190 ohne Doc-Header): sys.path.insert zu `phase1_broker_wrapper/` (gleiche Konvention wie `smoke_test.py`), `from broker_wrapper import get_broker`, `from broker_wrapper.exceptions import BrokerError`, argparse mit `--broker` (default `ig_demo`), `--epic` (repeatable, default `IX.D.DAX.IFMM.IP`, `IX.D.IBEX.IFM.IP`, `IX.D.AEX.IFM.IP` — die 3 weekend-freien Indizes aus Phase-16-B3), `--quiet` (Logger auf WARNING); `_probe_one()` ruft `broker._request("GET", f"/markets/{epic}", version="3", auth=True)` und extrahiert `instrument.marginFactor`, `instrument.marginFactorUnit`, `instrument.marginDepositBands` **roh** (keine Normalisierung), plus `dealingRules` und `instrument` als full slice für D3.1/D3.2-Inspektion; per-Epic-Verdict (`ok`/`field_missing`/`unit_unexpected:<UNIT>`/`unknown_shape`); partial-fail-tolerant — ein gescheiterter Epic bricht die Probe nicht ab (Operator sieht alle 3 Antworten); stdout = JSON-Liste, stderr = Per-Epic-Empfehlung + RECOMMENDATION-Linie (Exit-Code-basiert: 0 = Form wie erwartet `PERCENTAGE`, 1 = Request fehlgeschlagen, 2 = Feld vorhanden aber Unit/Shape unerwartet — D3.1 muss reicher extrahieren). argparse/offline-Selfcheck gemacht: `python ... --help` zeigt saubere Usage-Lines; `py_compile` clean. | P1 ±0 (operator-run script, kein Test-File per P1-Convention `smoke_test.py` + `test_lightstreamer.py` ist auch operator-run ohne pytest) | AK11-Vorbereitung ✅ (Probe-Skript committed, Probe selbst ist Nikinger-Job) |

**2. Σ-Sweep nach D3.0 (verifiziert 2026-09-07):** **1909 grün unverändert.** Phase-1/2/3/4/5/6/7/8/9/10/12/13/14/15/root = 95+82+105+162+185+76+169+256+95+165+145+82+61+126+105 = **1909** ✅ Plan-Akzeptanz AK2 erfüllt (Σ ≥ Vorblock-Stand 1907). Kein Test-File ⇒ keine Test-Δ. **Hard Rule 3 unangetastet** (reine GET-Probe, kein Order-Pfad, kein VETO, keine AI).

**3. Hook-Verify:** `python3 scripts/check_doc_rotation.py --strict --quiet` → exit 0 nach jedem Commit.

**4. Git-Stand am Session-Ende (vor Push):**
- HEAD = dieser Final-Commit (Session-Rotation #8→#9).
- Commits lokal ahead of `origin/main` = 2 (D3.0 Code + Rotation-Commit).
- Working tree clean.

### Findings

🟢 **D3.0 vollständig:** Probe-Skript committed, offline-verifiziert via argparse-Selfcheck + `py_compile`, Code-Compilation clean. Probe selbst ist Live-Job und liegt bei Nikinger.

🟢 **Phase-1-Convention eingehalten:** operator-run script, kein pytest, keyring-via-`get_broker`, sys.path-Insert analog `smoke_test.py`. Hard Rule „Credentials niemals in Dateien" (root-`CLAUDE.md`-Regel 1) eingehalten — Skript liest **nur** über `get_broker()`, nie direkt aus `.env`/JSON.

🟢 **Partial-fail-Disziplin:** ein Epic der 3 wirft (z. B. unbekannter Epic → `EpicNotFoundError`) → die anderen beiden werden trotzdem gezeigt. Operator sieht alle Befunde auf einmal, muss nicht raten was die anderen 2 antworten würden.

🟢 **Drei Epics-Default ist grounded:** DAX + IBEX + AEX sind die drei bekannten Indizes aus Phase-16-B3-Filter + dem ursprünglichen `EXTENDED_UNIVERSE`-Set; alle weekend-frei (IX.D.SUN* Epics wurden bereits aus dem Universe gefiltert, brauchen hier nicht berücksichtigt zu werden). Operator kann via `--epic` jeden anderen Epic zufügen.

🟡 **`IGAdapter._request` ist privat (`_`-Prefix):** Smoke-Konvention toleriert das (Phase-1-Skripts dürfen intra-Package-Privates nutzen, siehe `smoke_test.py` → `broker.connect()` → `self._session.post(...)`-intern). Plan §6 D3.0 schreibt diese Nutzung explizit vor. Falls die Probe in `pytest`-Mode landen soll, müsste der `_request`-Aufruf durch `get_market_info(epic)` ersetzt werden — was D3.1 voraussetzt (Chicken-and-Egg). Bewusst so belassen, weil der Skript-Zweck die Probe **vor** D3.1 ist.

🟡 **Liefert Probe was anderes als `PERCENTAGE`:** dann muss D3.1 entweder das Unit umrechnen (`POINTS` → andere Formel), oder zusätzliche Felder extrahieren (`marginDepositBands` parsen). Der genaue Pfad hängt vom IG-Response-Schema ab — kann erst nach Probe gesagt werden. Plan §6 D3.0 dokumentiert: „Weicht es ab → Feldnamen im Phasenkopf festhalten, D3.1 entsprechend" — der Phasenkopf ist genau dieses Session-Stopped-Format.

🟢 **Cross-Phase-Touch-Disziplin:** D3.0 berührt ausschließlich **P1** (1 neues Operator-Skript). Keine P2/P3/P4/P5/P7/P8/P9/P15-Touches. P1 ist in Phase-16-Cross-Phase-Freigabe-Liste (Plan §4 + P12: P1, P2, P3 R2, P4, P5, P7, P8, P9, P15) enthalten.

🟢 **Doku-Vermerk:** Plan §6 D3.0 sagt „~3 Requests, 0 Datenpunkte" — die Probe ist **read-only**, zählt also nicht als Datenpunkt (kein Trade, kein LLM-Call, keine State-Mutation). Probe-Lauf kann zu **jeder** Tageszeit (auch Wochenende / Markt-zu) durchgeführt werden, weil `/markets/{epic}` statische Instrument-Metadaten zurückgibt.

### Open questions / blockers

- **Keine inhaltlichen Blocker, sondern ein Live-Schritt:** Nikinger muss die Probe ausführen, das Ergebnis (stdout-JSON + stderr-Verdict) in diese Session zurückreichen, ich baue D3.1 + D3.2 gegen die Befunde in der Folgesession. Konkrete Runbook-Anleitung im nächsten HINWEIS-Block (siehe "Next").
- **Live-DB Schema v7 → v9 Akten-Vermerk** (B2, Sessions #3) bleibt offen — heute nicht Phase-16-Edit.
- **Push-Freigabe:** Nikinger hat zwischenzeitlich Session #8 gepusht. Diese Session 2 Commits pending, Push-Freigabe erwartet (Cross-Session-Pattern).
- **Session-#8 Doku war im Phasenkopf zu detailliert:** ich habe Exec-#8 verbatim nach `SESSIONS_ARCHIVE.md` rotiert (Stand-Text entsprechend aktualisiert: „Archiv trägt **8** Einträge" — Archiv-Header zählt jetzt 8 Sessions inkl. Plan). Phasenkopf trägt neu Exec-#9, Archiv trägt Exec-#8 + #7 + #6 + #5 + #4 + #3 + #2 + #1 + Plan-Session. Hook-Verify (`--strict`) exit 0 nach jeder Rotation.

### Nikinger-Runbook für die Probe (live, Demo, jederzeit möglich)

```bash
# 1) sicherstellen dass Demo-Creds im Keyring sind (sonst: scripts/store_credential.py)
cd /home/trading-bot/trading-bot

# 2) Probe laufen lassen (Default: 3 Epics DAX + IBEX + AEX)
phase1_broker_wrapper/.venv/bin/python phase1_broker_wrapper/scripts/probe_market_margin.py

# 3) Output zurückreichen — beide Ströme sind relevant:
#    stdout = JSON-Liste (für mich zum Inspizieren)
#    stderr = Per-Epic-Empfehlung + Exit-Code-basiertes RECOMMENDATION
#    Exit-Code:
#      0 = marginFactor numerisch + marginFactorUnit == "PERCENTAGE" → D3.1 kann das Schema verbatim 1:1 extrahieren
#      1 = min. ein Request fehlgeschlagen → Credential/Netz-Check, danach re-run
#      2 = Felder vorhanden aber unerwartete Form/Unit → D3.1 muss reicher extrahieren, ich brauche den vollen instrument_full-Slice für den abweichenden Epic

# 4) Optional: zusätzliche Epics testen
phase1_broker_wrapper/.venv/bin/python phase1_broker_wrapper/scripts/probe_market_margin.py \
    --epic IX.D.DAX.IFMM.IP --epic IX.D.CAC.IFM.IP
```

### Next (für die Folgesession, je nach Probe-Befund)

**Wenn Probe Exit 0** (Form bestätigt `PERCENTAGE`):
1. **D3.1** P1 `broker_wrapper/models.py` + 2 Felder (`margin_factor: float | None`, `margin_factor_unit: str | None`) + `ig_adapter.py:503`-Anker-Edit + Helper `_float_or_none` + Test `test_get_market_info_extracts_margin_factor` (P1 +1 Test).
2. **D3.2** P5 `execution/config.py:124` + `margin_headroom: float = 0.95` + `sizing.py:36-68` `_size_from_risk` mit margin_cap-Pfad + `compute_size:139-146` reicht `margin_factor_pct` durch + 3 Tests in `test_sizing.py` (Datenwoche-Grenzfall `available=27_100, ask=24_500, pv=1.0, mf=5.0` → 21,0; `mf=None` → bit-identisch; `unit="PERCENTAGE"`-Pflicht). P5 +3 Tests.
3. **Block E** starten (E2/E3/E4) — unabhängig von D3, kann vorher starten wenn Nikinger das bevorzugt.

**Wenn Probe Exit 1** (Request-Fehler):
- Credential-Check, ggf. `scripts/store_credential.py` neu ausführen, Probe erneut.

**Wenn Probe Exit 2** (unerwartete Form):
- Ich inspiziere den `instrument_full`-Slice für den abweichenden Epic, passe D3.1 an (entweder zusätzliche Felder extrahieren oder Unit-Konversion), D3.2 entsprechend.

**Wenn Nikinger die Probe verschiebt** (z. B. erst E2 starten):
- E2 = `scripts/autonomy_report.py` (deterministisch, read-only, mode=ro) + 5 Tests. Rein mechanisch, kein Operator-Block, sofort ausführbar — kann ohne D3 starten.

**Block-Status nach dieser Session (endgültig):**

| Block | Status |
|---|---|
| A (Haushalt) | ✅ A-0..A-4 + A-5 Push (Sessions #1-#3) |
| B (Substrat) | ✅ B1+B3 code + B2 Operator-Apply + A-5 Push (Session #3) |
| C (Research-Loop) | ✅ C1+C2+C3+C5 endgültig in code; C4 = Doku-Only (Sessions #4-#5) |
| D (Freischaltung) | ✅ **D1+D1.2+D2+D3.0 endgültig in code** (Sessions #7+#8+#9); **D3.1+D3.2 ⏳** (warten auf Probe-Befund) |
| E (Autonomie-Test, Vorregistrierung) | ✅ E1 endgültig in docs (Session #6) |
| E (Autonomie-Test, Rest) | ⏳ E2/E3/E4 (unabhängig von D3, jederzeit möglich) |

**Push-Status dieser Session:** **0 Commits gepusht** (in dieser Session), 2 Commits pending (D3.0 Code + Final-Rotation) ahead of `origin/main` (= `468ce3d`). **Nikinger-Push-Freigabe erwartet**, analog den vorherigen Sessions.