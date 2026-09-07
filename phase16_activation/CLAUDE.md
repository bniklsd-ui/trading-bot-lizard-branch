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
updated: 2026-09-07 (+ Exec-Session #12 → Archiv; Exec-Session #13 schließt Pre-Flight-Durchlauf + Drift-Supersede ab: `phase16_activation/PHASE16_E3_RUNBOOK_v2.md` NEU [501 LOC, locked-nach-Commit, supersedet v1 die im Repo als historischer Audit-Stand bleibt mit 'SUPERSEDED durch v2'-Markierung in INDEX.md] + INDEX.md-Update [v2-Zeile NEU + v1-Zeile als superseded markiert]; Runbook-v2 ist die einzige Quelle der Wahrheit für den E3-Operator-Pfad, enthält 6 Schema-/SQL-Drift-Korrekturen + NEU §1 Pflicht-Operator-SQL für 3 SUN*-Epics pre-E3 [B3 forward-only Lücke]); Pre-Flight-Befunde dieser Session: §1.1 Liveness OK (4 Dienste tot seit B2) · §1.2 Schema-Floor v9 wirksam (KORRIGIERT ggü. v1: `PRAGMA user_version` ≠ Schema-Version, Phase-2 trackt via `_schema_version`-Tabelle mit 9 Zeilen) · §1.4 K1-Truncate vorbereitet (4 Wrapper-Logs identifiziert, `run_scheduler.log` NICHT weil Timestamp-Prefix) · §1.5 DB-Health zeigt 5 Schema-Drifts in v1 [active=1 vs status='active', last_verified_utc vs last_verified_at, source_spend in bars.sqlite vs trading_bot.sqlite, paper_trades.resolved vs paper_trades.status, PRAGMA vs _schema_version] · §1.5 Live-Befund 3 SUN*-Epics active (SUNDAX.IGN/SUNDOW/SUNNAS, alle last_verified_at 2026-09-04, vor B3-Commit d82922e Session #3 2026-09-05 → B3 forward-only, AK9 pre-test-FAIL) · Pre-E3-Blocker identifiziert + Runbook-v2 §1 Pflicht-SQL vorbereitet (UPDATE instrument_universe SET status='quarantined' WHERE epic LIKE 'IX.D.SUN%' AND status='active'; wirkt auf 3 Zeilen); Σ 1921 unverändert docs-only; Block E [E1 docs ✅, E2 code ✅, E3 docs v2 supersedet v1 ✅] ⇒ offen nur E3 Runbook-Start [Nikinger-Aktion: Pflicht-SQL §1 v2 + Restart §3 v2] + E4 Tagesroutine+Closeout-Handover+SVG)
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
## Session stopped — 2026-09-07 (MiniMax-M3-Exec-Session #13, Pre-Flight-Durchlauf + Drift-Supersede v1→v2, Σ 1921 grün unverändert [docs-only], Exec-#12-Block verbatim nach SESSIONS_ARCHIVE.md rotiert [13. Eintrag, +1 vs. Stand Session #12], Pause auf Nikinger-Auftrag [Pflicht-SQL + Restart-Tag])

> **Auftrag:** Nikinger-Chat 2026-09-07 (Phase-16-Exec-Folge, „Lass uns das runbook jetzt durcharbeiten arbeiten, es sei denn es ish geblockt. Dann die Block items"): Runbook ist nicht geblockt, also arbeiten wir es durch. Exec-Session macht die read-only Pre-Flight-Checks (§1.1 Liveness, §1.2 Schema-Floor, §1.5 DB-Health), Operator macht §1.3 Keyring + §1.6 Akten-Vermerk + §2 Restart + §3 Day-0-Checks. Pre-Flight-Befund dieser Session: **6 Schema-/SQL-Drifts in v1** (gefunden) + **1 Live-Blocker** (3 SUN*-Epics `status='active'` aus 2026-09-04-Promotions vor B3-Commit `d82922e` Session #3 2026-09-05; B3 ist forward-only). **Blocker fix + Drift-Supersede** (Nikinger-Wahl via interactive-question): Operator-SQL für 3 SUN-Epics (vorbereitet, Nikinger führt aus) + **PHASE16_E3_RUNBOOK_v2.md** NEU [501 LOC, supersedet v1, locked-nach-Commit] mit allen 6 Korrekturen baked-in + §11 Diff-Tabelle. v1 bleibt im Repo als historischer Audit-Stand mit „SUPERSEDED durch v2"-Markierung in INDEX.md. Block E [E1 docs ✅, E2 code ✅, E3 docs v2 supersedet v1] ⇒ offen nur E3 Runbook-Start [Nikinger-Aktion: Pflicht-SQL §1 v2 + Restart §3 v2] + E4 Tagesroutine+Closeout-Handover+SVG.
>
> Plan-Anker: [`../docs/concepts/phase16_activation_plan.md`](../docs/concepts/phase16_activation_plan.md) §6 E3 (S. 797-808, vollständig in v2 §3 Restart-Sequenz übernommen) · §7 AK9 (kein `IX.D.SUN*` in `active`, Prereg §Vorregistrierte Werte / „Universe" → Pflicht-SQL löst die forward-only-Lücke aus B3) · §7 AK4 (Schema-Floor v9 via `_schema_version`-Tabelle, korrigiert ggü. v1) · §1 P11 (Prereg-Disziplin übertragen: v1+v2 beide locked-nach-Commit, kein Edit, nur Supersede) · §1 P15 (neue .md-Datei ⇒ INDEX.md-Zeile im selben Commit; v2-Zeile + v1-Updated-Status).
>
> Ausführungs-Scope: **2 Atomic Commits** (`a660878` phase16: docs -- E3 Runbook v2 (501 LOC) + INDEX.md-Update [v2-Zeile NEU + v1 als superseded markiert] · dieser Final-Commit Session-Rotation #12→#13). Push-Freigabe-Stand: Nikinger hat zwischen #12 und jetzt 0 Commits gepusht (last push war Session #12 ⇒ `a3fa6ce..e66be3a main -> main`, `origin/main = e66be3a` bleibt). Diese Session pusht die **eigenen** 2 Commits **nicht** eigenmächtig.

### Completed

**0. Cross-Session-Drift-Vorab-Check (Session-Start dieser Exec-Folge-Session #13, 2026-09-07):**
- `git log origin/main..HEAD --oneline` → leer (HEAD = `e66be3a` = origin/main; Cross-Session-Pattern bestätigt).
- `git status` → working tree clean bis auf untracked `data/` (gitignored).
- Hook `check_doc_rotation.py --strict --phase phase16_activation` → exit 0 (vor dieser Rotation: Phasenkopf 1 Block Exec-#12, Archiv 12 Blocks).
- Phase-16-Current-State-Sweep: alle 4 Services tot seit B2 (Plan §6 E3 erwartet); `_schema_version` Tabelle hat 9 Zeilen (Schema v9 wirksam) ✅; `instincts` Tabelle existiert ✅; `instrument_universe` hat 8 active + 14 verified Rows (5 davon SUN*, davon 3 active); `bars.sqlite` 962 capital + 2860 ig + 36787 yf + 0 ls (Watch-Item W4, pre-E3 erwartet); `paper_trades` 442 RESOLVED + 571 EXPIRED_UNRESOLVED; `source_spend` 173 research + 37 sample + 4 probe (alle in `data/bars.sqlite`, nicht in `trading_bot.sqlite`).

**1. Pre-Flight-Durchlauf (read-only Exec-Session-Checks aus Runbook v1 §1):**

| Check | v1-Befehl | Tatsächlicher Live-Stand | Drift? |
|---|---|---|---|
| **§1.1 Liveness** | `bash scripts/restart-services.sh status` | 4/4 tot (recorder, discovery, scheduler, webui); `DISCOVERY_ARMED` Flag existiert (Operator-touch); kein `KILL` | ✅ kein Drift |
| **§1.2 Schema-Floor 9** | `PRAGMA user_version;` | **0** (≠ 9 erwartet!) | ⚠️ Drift: `PRAGMA user_version` ist NICHT die Schema-Version |
| **§1.2 Schema-Floor 9 (korrekt)** | `SELECT count(*) FROM _schema_version;` | **9** ✅ | (korrekte Query, in v2 §1.2 verwendet) |
| **§1.4 K1-Log-Truncate** | `truncate -s 0 data/state/run_*.log` (3 Wrapper) | `run_recorder.log` 31 KB, `run_discovery.log` 1 KB, `run_webui.log` **40 MB**, `run_scheduler.log` 596 KB (mit Timestamp-Prefix, NICHT truncaten) | ✅ v1-Empfehlung korrekt |
| **§1.5 DB-Health Spalten** | `instrument_universe WHERE active=1` | Spalte heißt `status`, nicht `active` → Query wirft `Error: no such column: active` | ⚠️ Drift: `active=1` → `status='active'` |
| **§1.5 DB-Health Zeit** | `last_verified_utc` | Spalte heißt `last_verified_at` | ⚠️ Drift |
| **§1.5 DB-Health spend** | `source_spend` (implizit trading_bot.sqlite) | Tabelle ist in `data/bars.sqlite`, nicht in `data/trading_bot.sqlite` | ⚠️ Drift: DB-Pfad |
| **§1.5 DB-Health paper** | `paper_trades WHERE resolved...` | Spalte `resolved` existiert nicht; Spalte heißt `status` (Werte OPEN/RESOLVED/EXPIRED_UNRESOLVED) | ⚠️ Drift |
| **§1.5 SUN*-Check** | `WHERE active=1 AND epic LIKE 'IX.D.SUN%'` | Wirft Spalten-Error. Mit korrigierter Spalte: **3 Epics active** (SUNDAX.IGN, SUNDOW, SUNNAS, alle `last_verified_at=2026-09-04`) | ⚠️ Drift + 🔴 Live-Blocker |

**Befund:** 6 Schema-/SQL-Drifts in v1 + 1 Live-Blocker (3 SUN*-Epics active aus Pre-B3-Promotions 2026-09-04, B3-Commit `d82922e` Session #3 2026-09-05 ist forward-only). B3-Code in `phase9_universe/universe/models.py:90-104` + `discovery._passes_code_filter` + `promotion.run_promotion_cycle` Step 3 wirkt nur forward — die 3 Epics wurden vor B3 aktiv und sind nie demotiert worden.

**2. Blocker-Fix (Nikinger-Aktion, vorbereitet):**
- **Pflicht-SQL vorbereitet** (Operator führt aus, kein Commit, Audit-Trail im Prereg-Aktiv-Block):
  ```sql
  UPDATE instrument_universe SET status='quarantined' WHERE epic LIKE 'IX.D.SUN%' AND status='active';
  ```
- Wirkt auf 3 Zeilen (SUNDAX.IGN, SUNDOW, SUNNAS)
- Analog B2 (Schema-Apply, Session #3): Operator-Aktion vor E3-Restart, dokumentiert in PHASE16_AUTONOMY_PREREGISTRATION.md Aktiv-Block unter „Operator-Aktionen vor E3-Start"
- Phase-9-Pattern: Discovery wird diese Epics nicht erneut promoten (`is_weekend_market` filtert sie im `_passes_code_filter` raus)
- Kein Code-Touch, keine Migration, kein Commit nötig (`data/` ist gitignored)

**3. Drift-Supersede v1 → v2 in 1 atomaren Docs-Commit:**

| Datei | Inhalt | LOC | Σ-Delta | Akzeptanz |
|---|---|---:|---:|---|
| `phase16_activation/PHASE16_E3_RUNBOOK_v2.md` (NEU) | 11 Sektionen + Header-Karte (locked-nach-Commit, supersedet v1, v1 als Audit-Trail im Repo). **§0 BLUF** + Reihenfolge-Operator-Pfad 7 Schritte. **§1 Pflicht-Operator-SQL** (3 SUN-Epics → quarantined, mit `json_set` Audit-Trail). **§2 Pre-Flight** 6 Schritte (korrigiert: `_schema_version` statt `PRAGMA user_version`, `status` statt `active=1`, `last_verified_at` statt `last_verified_utc`, `source_spend` explizit `data/bars.sqlite`). **§2.4 Truncate erweitert** um 4 Pre-Wrapper-Logs (kosmetisch). **§3 Restart-Sequenz** (Plan §6 E3 verbatim). **§4 Day-0-Checks Timeline** (Spalten-Drift korrigiert). **§5 Tagesroutine**. **§6 Trigger-Bedingungen T-1..T-12** (Spalten-Drift korrigiert). **§7 Watch-Items W1-W6**. **§8 Tag-10-Closeout**. **§9 was-das-Runbook-nicht-macht**. **§10 Cross-Refs**. **§11 Diff v1→v2** (8 Änderungen tabelliert, mit v1-Verweis + Begründung). | 501 | – | Plan §1 P11 (locked-nach-Commit, v1+v2 nebeneinander, kein Edit, nur Supersede) + §1 P15 (INDEX.md-Zeile im selben Commit) + Prereg-Disziplin + 6 Schema-Drift-Korrekturen + §1 Pflicht-SQL für Pre-E3-Blocker |
| `docs/INDEX.md` (Update) | Phase-16-Cluster: v1-Zeile als „⚠️ SUPERSEDED durch v2 (siehe nächster Eintrag), bleibt im Repo als historischer Audit-Stand; **nicht** mehr lesen für den E3-Start" markiert; v2-Zeile NEU mit Beschreibung aller 6 Drift-Korrekturen + §1 Pflicht-SQL-Hinweis | (Eintrag-Update) | – | Plan §1 P15 + Doc-Layers-Konvention (v1 als 📕 Audit-Trail, v2 als 📕 locked-quelle) |

**4. Σ-Sweep nach v2-Abschluss (verifiziert 2026-09-07):** **1921 grün unverändert.** Phase-1/2/3/4/5/6/7/8/9/10/12/13/14/15/16/root = 97+82+105+162+190+76+169+256+95+165+145+82+61+126+5+105 = **1921** ✅ Plan-Akzeptanz AK2 trivial erfüllt. Kein Test-File, kein Code-Touch ⇒ Σ bit-identisch.

**5. Hook-Verify:** `python3 scripts/check_doc_rotation.py --strict --quiet` → exit 0 nach Code-Commit (`a660878`) und nach dieser Rotation.

**6. v2-Selbsttest (Markdown-Lint + Cross-Ref-Auflösung):** alle Anchor-Dateien aus §10 (`PHASE16_AUTONOMY_PREREGISTRATION.md`, `PHASE16_E3_RUNBOOK.md` v1, `phase16_activation_plan.md`, `restart-services.sh`, `autonomy_report.py`, `test_autonomy_report.py`, `phase15_v4/PHASE15_CLOSEOUT_HANDOVER.md`, `phase16_activation/SESSIONS_ARCHIVE.md`) existieren (`ls` verified). §11 Diff-Tabelle hat 8 Zeilen (6 Drift-Korrekturen + 1 Pflicht-SQL-Neu + 1 Reihenfolge-Neu). Keine toten Links.

**7. Git-Stand am Session-Ende (vor Push):**
- HEAD = dieser Final-Commit (Session-Rotation #12→#13).
- Commits lokal ahead of `origin/main = e66be3a` = 2 (`a660878` v2-Supersede + dieser Rotation-Commit).
- Working tree clean nach jedem Commit.
- 2 Commits pending nicht eigenmächtig gepusht (Nikinger-Push-Freigabe erwartet).

### Findings

🟢 **6 Schema-Drifts in v1 vollständig in v2 korrigiert:** die Pre-Flight-Checks waren genau dafür gemacht — Drift-Erkennung pre-E3. v2 ist die einzige Quelle der Wahrheit für den Operator-Pfad, v1 bleibt als Audit-Trail im Repo (per Prereg-Disziplin kein Edit, sondern Supersede).

🟢 **Pflicht-Operator-SQL ist minimal-invasiv:** keine Schema-Änderung, keine Migration, kein Code-Touch. Wirkt nur auf 3 Zeilen. Phase-9-Pattern verhindert Re-Promotion (B3-Discovery-Filter). Audit-Trail im Prereg-Aktiv-Block dokumentiert. Identisch zu B2 (Schema-Apply, Session #3) als „Operator-Aktion vor Test-Start" — kein Locked-Verstoß.

🟢 **Prereg-Disziplin symmetrisch:** v1 und v2 sind beide locked-nach-Commit. Korrekturen nur als Supersede (`PHASE16_E3_RUNBOOK_v3.md` mit Datum + Grund). Header-Doc-Kommentar beider Versionen sagt explizit: „Korrekturen nur als neues, datiertes, supersedendes Dokument mit Grund — niemals ein Edit hier". Gleiche Konvention wie `PHASE16_AUTONOMY_PREREGISTRATION.md` und `meta_m1_harness/META_M1_PREREGISTRATION.md`.

🟢 **Runbook-v2 §0 Reihenfolge-Operator-Pfad 7 Schritte** macht den Block-Fix zur Pflicht-Vorbedingung: Schritt 1 = Pflicht-Operator-SQL → Schritt 2 = §2 Pre-Flight → Schritt 3 = §2.6 Prereg-Aktiv-Block → Schritt 4 = §3 Restart → Schritt 5 = §4 Day-0-Checks → Schritt 6 = §5 Tagesroutine → Schritt 7 = §8 Tag-10-Closeout. Operator kann Schritte nicht überspringen — Pflicht-SQL muss **vor** dem ersten `start` laufen, sonst Kriterium 9 bereits pre-FAIL.

🟢 **T-3 Trigger angepasst an korrigierte Spalte:** v2 §6 T-3 sagt explizit „`instrument_universe WHERE status='active' AND epic LIKE 'IX.D.SUN%'` > 0" (statt v1 `active=1`). Operator und Exec-Session sehen die gleiche korrekte Spalte.

🟢 **v2 §2.4 Truncate erweitert um 4 Pre-Wrapper-Logs** (kosmetisch): `scheduler.log`/`webui.log`/`recorder.log`/`discovery.log` (vor der Umstellung auf `run_*-Wrapper`-Skripte). Diese zählen NICHT für K1 (kein `run_`-Wrapper-Prefix), aber wenn der Operator sie nicht truncatet, leben Pre-Wrapper-Restarts weiter in den Logs und verwirren später.

🟢 **`autonomy_report.py` Live-Tree-Smoke weiterhin OK** (unverändert seit Session #11): exit 0, K1–K4 FAIL pre-E3 (keine Bestandteile), K5–K7 PASS. Der Script ist robust gegen die jetzt gefundenen Schema-Drifts: er verwendet korrekte Spalten (`status`, `last_verified_at`, `bars`-Tabelle in `data/bars.sqlite`). Der Drift war nur im Runbook v1 — nicht im E2-Code. (Eigene Verifikation: `grep` durch `autonomy_report.py` für `active=` / `last_verified_utc` = leer.)

🟢 **Cross-Phase-Touch-Disziplin eingehalten:** v2 ist phase-intern (Phase 16), kein Code-Touch. Phase-9-Discovery-Filter (`is_weekend_market`) verhindert strukturell, dass die 3 Epics erneut promoted werden. Kein Phase-9-Code-Change nötig.

🟡 **Watch-Item Plan §13 #8 (Staffelung via `marginDepositBands`)** unverändert Phase-17-Material. v2 §6 T-9 hat den Margen-Reject-Trigger als Exec-Session-Pfad.

🟡 **Watch-Item Phase-9-Discovery-Filter Wirksamkeit:** die 3 manuell `quarantined`-Epics bleiben quarantined solange Phase-9-Discovery nicht läuft. Sobald E3 startet und der Discovery-Daemon refresht, würden sie **automatisch** durch B3-Filter draußen bleiben — d. h. die manuelle Demotion ist ein One-Shot-Fix, der strukturell redundant zu B3 ist (für die Zukunft). Die manuelle Aktion ist trotzdem nötig, weil B3 die 3 Epics nicht retroaktiv demotiert hat.

### Open questions / blockers

- **Blocker-Fix (Pflicht-Operator-SQL)** wartet auf **Nikinger-Aktion**. Wenn Nikinger den SQL ausgeführt hat, ist AK9 (kein `IX.D.SUN*` in active) pre-test-FAIL-status aufgehoben.
- **E3-Restart-Tag** wartet auf **Nikinger-Aktion**. Plan §11 Operator-Aktion #5 + Runbook v2 §3. Empfehlung: Dienstag oder Mittwoch (Donnerstag/Freitag wegen Wochenend-Lücke vermeiden).
- **E4 (Tagesroutine + Closeout)**: wird nach E3 in der Folgesession gestartet; benötigt die ersten `autonomy_report.py --day`-Outputs (v2 §5). Closeout-Handover nach Tag 10 → `phase16_activation/PHASE16_CLOSEOUT_HANDOVER.md` + `docs/architecture/phase16_activation.svg` 1080×1080 + Status-Pflege root-CLAUDE/ROADMAP/README/INDEX + Session-Rotation.
- **Live-DB Schema v7 → v9 Akten-Vermerk** (B2, Sessions #3) — heute nicht Phase-16-Edit, weiter offen.
- **Push-Freigabe-Stand:** Nikinger hat zwischen #12 und jetzt 0 Commits gepusht (letzter Push war `e66be3a` = Stand Session #12). Diese Session 2 Commits pending (`a660878` + Rotation). **Push-Freigabe erwartet**.

### Next (für die Folgesession)

- **E3 — Runbook-Start (Nikinger-Aktion, Runbook v2 §0 Reihenfolge):** Schritt 1 = `UPDATE instrument_universe SET status='quarantined' WHERE epic LIKE 'IX.D.SUN%' AND status='active';` (3 Zeilen, post-Verify = 0) → Schritt 2 = v2 §2 Pre-Flight (6 Schritte, ≤ 5 min, inkl. v2 §2.4 erweiterter Truncate) → Schritt 3 = v2 §2.6 Prereg-Aktiv-Block-Eintragung + Folge-Commit `phase16: docs -- E1-Aktiv-Block-Eintragung` mit Zeitstempel (AK13) → Schritt 4 = v2 §3 Restart-Sequenz (`restart-services.sh start` + K7-Caps-Pin-Verify) → Schritt 5 = v2 §4 Day-0-Checks Timeline (5min/30min/4h/24h, alle SQL-Queries mit korrigierten Spalten) → Schritt 6 = v2 §5 Tagesroutine (täglich `--day`) → Schritt 7 = v2 §8 Tag-10-Closeout (`--summary` + Exec-Session).
- **E4 — Tagesroutine + Closeout**: ab Tag 1 täglich `autonomy_report.py --day` (v2 §5). Nach Tag 10: `--summary` (v2 §8), wenn `overall_verdict == "PASS"` Closeout-Handover + SVG + Status-Pflege.
- **PHASE16_CLOSEOUT_HANDOVER.md + docs/architecture/phase16_activation.svg** nach Tag 10 (Phase-16-Abschluss, Runbook v2 §8).

### Watch-Item / Plan-Hygiene (für spätere Sessions)

- **Pflicht-Operator-SQL §1 v2**: 3 SUN*-Epics müssen pre-E3 demotiert werden. Einmaliger Operator-Akt, analog B2 (Schema-Apply). Kein Code-Touch. Audit-Trail im Prereg-Aktiv-Block.
- **Staffelung via `marginDepositBands`** (Plan §13 #8): unverändert Phase-17-Material. Runbook v2 §6 T-9 → Exec-Session-Pfad.
- **Hybrid-Test-Ansatz** (Session #11 Findings): unverändert Phase-17-Material wenn CI-Run gewünscht.
- **Runbook-Supersede-Disziplin** (P11): wenn nach E3 etwas am Runbook fehlt (z. B. ein neuer Trigger-Bedingung), wird **kein** Edit am bestehenden Runbook gemacht — neues, datiertes, supersedendes Doc (`PHASE16_E3_RUNBOOK_v3.md`) mit Begründung. v1+v2 bleiben beide als historische Stände im Repo.
- **Phase-17-Kandidaten** (aus dem Runbook herausgelesen): Prozess-Supervision (systemd-User-Unit + Auto-Restart nach Reboot + Keyring ohne Login); Strategie-Bewertung (Watch-Items W1 BUY-Bias, W2 DAX-Only → Win-Rate / Sharpe / P&L); CLI-Bridge-Test-Hardening.
- **Phase-9-Discovery-Filter** (`is_weekend_market`) ist die strukturelle Lösung für die 3-Epics-Lücke — die manuelle Demotion ist eine einmalige Operator-Aktion, danach verhindert der Code Re-Promotion automatisch.

**Block-Status nach dieser Session (endgültig):**

| Block | Status |
|---|---|
| A (Haushalt) | ✅ A-0..A-4 + A-5 Push (Sessions #1-#3) |
| B (Substrat) | ✅ B1+B3 code + B2 Operator-Apply + A-5 Push (Session #3) |
| C (Research-Loop) | ✅ C1+C2+C3+C5 endgültig in code; C4 = Doku-Only (Sessions #4-#5) |
| D (Freischaltung) | ✅ D1+D1.2+D2+D3.0+D3.1+D3.2 komplett (Sessions #7-#10) |
| E (Autonomie-Test, Vorregistrierung) | ✅ E1 endgültig in docs (Session #6) |
| E (Autonomie-Test, E2) | ✅ E2 endgültig in code (Session #11) |
| E (Autonomie-Test, E3 Runbook) | ✅ **E3 Runbook v2 endgültig in docs** (Session #13, supersedet v1); E3 Runbook-Start [Nikinger: Pflicht-SQL + Restart] + E4 Tagesroutine+Closeout offen |

**Push-Status dieser Session:** **2 Commits pending** (`a660878` E3 Runbook v2 + dieser Rotation-Commit), 0 Commits gepusht. **Nikinger-Push-Freigabe erwartet**.
