---
status: snapshot
purpose: Execution-ready Plan für Phase 14 (Discovery-Then-Deterministic) — gelockte Entscheidungen D1–D20, Schritt-Sequenz Block 0/A/B/C/D mit Verbatim-Ankern, Testliste, Akzeptanz, vollständige Drift-Liste. Direkt an eine ausführende Session übergebbar.
read-when: Phase 14 gebaut wird; jede Session, die `EPIC_MAP`, `instrument_source_availability`, den Discovery-Daemon oder das UI-Scharfschalten anfasst
detail: L3
up: ../../phase14_discovery/CLAUDE.md
down:
  - ./phase14_discovery_concept.md                              # 📕 Concept-Skizze, die dieser Plan ausfüllt (Q1–Q7 hier beantwortet)
  - ./phase13_c_block_c_replan.md                               # 📕 Block-C-Closure, die Phase 14 lostritt
  - ../../phase13_live_data/PHASE13_CLOSEOUT_HANDOVER.md        # 📕 Phase-13-Abschluss, §1.5 drei geerbte Schnittstellen
  - ./phase13_live_data_plan.md                                 # 📕 L1–L17 (gelockt), gelten weiter
  - ../../phase12_data_foundation/PHASE12_5_CLOSEOUT_HANDOVER.md # 📕 die Lehre „nicht im Konsumentenpfad kaufen"
  - ../../phase14_discovery/PHASE14_C_DAEMON_CWD_BUG_PLAN.md    # 📕 Schwester-Mini-Plan (P14-C, CWD-Pfad-Bug)
  - ../../phase14_discovery/PHASE14_D_DAEMON_SIGNAL_CAP_PLAN.md # 📕 Schwester-Mini-Plan (P14-D, Sleep-Cap-Bug)
updated: 2026-08-27
---

# Phase 14 — Discovery-Then-Deterministic · Execution-ready Plan (2026-08-22)

> **Autor:** Claude Code, Planungssession 2026-08-22 (Opus 5, read-only am Produktionscode —
> **kein** Produktionscode-Edit in dieser Session).
> **Adressat:** die ausführende Session (Sonnet 5). Dieser Plan ist so geschrieben, dass sie
> ihn **nicht neu herleiten muss**: jede Edit-Stelle trägt den Verbatim-String plus die
> heutige Zeilennummer.
>
> **Beweislage:** alles unten ist gegen das Repo, die Live-DB (`mode=ro`) und einen echten
> Testlauf **selbst nachgemessen** — ausgenommen ausschließlich das, was in **§9
> (Drift-Liste)** steht. Was dort nicht steht, gilt als geprüft. Aus Vorgänger-Handovern
> ist **nichts** ungeprüft übernommen; wo ein Vordokument falsch lag, steht die Korrektur
> in **§3**.

---

## §0 BLUF

**Heute** kennt der Code die Quellen. `EPIC_MAP` (`live_data/backfill.py:85-88`) mappt zwei
IG-Epics von Hand auf Capital.com-Kürzel; `yf_ticker` lebt als Spalte in
`instrument_universe`; „welche Quelle kann Epic X?" ist eine Frage, die niemand stellen kann.

**Nach Phase 14** kennt eine Tabelle die Quellen. `instrument_source_availability`
(Migration 007) hält die Kreuzung IG-Epic × Quelle × Auflösung inklusive des
**quelleneigenen Symbols**. Ein autonomer Daemon füllt sie; die UI schaltet ihn scharf; die
Konsumenten lesen sie. `EPIC_MAP` verschwindet.

**Vier Dinge, die diesen Plan von der Concept-Skizze unterscheiden:**

| # | Was |
|---|---|
| 1 | **`source_symbol` ist neu.** Die Concept-Schema-Skizze (§2.2) hat **keine** Spalte für das quelleneigene Symbol und kann `EPIC_MAP` deshalb **nicht** ersetzen — ihr eigenes Done-Kriterium wäre unerreichbar. Datierte Korrektur, s. §3.2. |
| 2 | **`measurable_universe()` wird nicht angefasst.** Die yF-Zeile ist eine *Projektion*, kein zweiter Schreiber. Grund: die Beweiswoche hängt an diesem Gate (§4 D3/D4). |
| 3 | **Discovery gibt strukturell null IG-Punkte aus.** Die IG-Zeile wird *abgeleitet*, nie erprobt — testbar mit einem Provider, der bei jedem Call wirft (§4 D6, Muster L12). |
| 4 | **Ein scharfer Live-Blocker gefunden und reproduziert:** `stale_source` sprengt beim *Lesen* die Registry. Er zündet genau dann, wenn die Beweiswoche ihren Sampler anschaltet. §3.1. |

---

## §1 Mission und Bauprinzip

> **„Was eine Quelle kann, sagt die Quelle — nicht der Konsument."**

1. **Discovery first.** Jede Quelle exponiert ihr Liefer-Spektrum als `SourceProfile`.
2. **Kreuzung second.** Eine Tabelle hält „für Epic X können diese Quellen liefern, mit
   diesem Symbol, dieser Tiefe, dieser Latenz".
3. **Determinism last.** Der Konsument liest die Tabelle und wird dadurch *einfacher*, nicht
   komplizierter — die Auswahl ist vor ihm getroffen.

**Bauprinzip:** „So wenig AI wie möglich, so viel AI wie nötig." **Phase 14 fügt NULL neues
AI hinzu.** Quell-Entdeckung, Symbol-Zuordnung, Verfügbarkeits-Bewertung und
Scharfschalt-Logik sind deterministischer Code. Wer hier ein LLM „Quellen bewerten" oder
„Symbole raten" lassen will → **stop**, das ist Code.

---

## §2 Was diese Planungssession selbst nachgemessen hat (Fakten, 2026-08-22)

Jede Zeile ist eigene Messung dieser Session, nicht aus einem Vordokument übernommen.

### §2.1 Regression-Baseline VOR dem ersten Fix

`phase1_broker_wrapper/.venv/bin/python -m pytest <dir> -q`, je Phase separat
(`tests.conftest`-Namenskollision, Repo-Konvention):

| Suite | Tests | Suite | Tests |
|---|---:|---|---:|
| `phase1_broker_wrapper` | 95 | `phase9_universe` | 80 |
| `phase2_persistence` | 77 | `phase10_v3` | 165 |
| `phase3_external_data` | 104 | `phase12_data_foundation` | 143 |
| `phase4_research` | 155 | `phase13_live_data` | 50 |
| `phase5_execution` | 173 | `meta_m1_harness` | 28 |
| `phase6_debate` | 76 | root `tests/` | 80 |
| `phase7_reward` | 138 | | |
| `phase8_scheduler` | 244 (+1 Warning) | **Summe** | **1608** |

**Alle grün. Working tree clean. `ps aux | grep scheduler.run` leer (kein Bot-Prozess).**

### §2.2 Live-DB-Substrat (`mode=ro`)

`data/trading_bot.sqlite`, `_schema_version` = **6** ⇒ **Migration 007 ist frei.**

`instrument_universe`: **22 Zeilen**.

| `status` | `data_source_status` | n | Epics |
|---|---|---:|---|
| `active` | `ok` | **5** | `IX.D.CAC.IFE.IP`, `IX.D.DAX.IFMM.IP`, `IX.D.DAX.IGN.IP`, `IX.D.IBEX.FWM2.IP`, `IX.D.IBEX.IFM.IP` |
| `active` | `no_intraday_source` | 3 | `IX.D.SUNDAX.IGN.IP`, `IX.D.SUNDOW.IAE.IP`, `IX.D.SUNNAS.IAE.IP` |
| `verified` | `unverified` | 14 | AEX ×3, MIB ×2, IBEX ×2, DOW, FTSE, NASDAQ, SPTRD, STXE, SUNDAX.IFMM, SUNFUN |

`data/bars.sqlite`: **14 846 Bars** — `yf` 11 654 · `ig` 2 230 · `capital` 962
(481 `IX.D.DAX.IFMM.IP` + 481 `IX.D.CAC.IFE.IP`, Fenster 2026-08-21T08:00Z–16:00Z) ·
`ls` **0**. Tabellen dort: `bars`, `source_spend`, `allowance_observations`.

### §2.3 Turbo-/Legacy-Grep-Ritual — **ausgeführt, No-Op**

```
grep -rniE "\b(turbo_research|strike|otm|issuer)\b" --include="*.py" .   (ohne .venv)
```
→ **3 Treffer, alle harmlos:** `phase9_universe/universe/promotion.py:121`, `:277` und
`phase9_universe/tests/test_promotion.py:343` benutzen „strike" im Sinne von *Fehlversuch*
(`fail_count`), nicht im Optionssinn. `turbo_candidates` = **19 Treffer**, der eingefrorene
P5-Gate-2-Contract-Name — **nicht umbenennen**. Ergebnis identisch zu den Ritualen vom
2026-06-27, 2026-07-10 und 2026-08-18. **Phase 14 führt keine neue Turbo-Referenz ein.**
Die ausführende Session **wiederholt dieses Ritual nicht** — sie verweist auf diesen Absatz.

### §2.4 Sonstige geprüfte Fakten

| Fakt | Beleg (heute geprüft) |
|---|---|
| Kein einziges `FOREIGN KEY` in `phase2_persistence/migrations/001…006` | `grep -c "FOREIGN KEY" migrations/*.sql` → 6× `0` |
| `PRAGMA foreign_keys = ON` setzt **nur** `persistence/db.py:65`; `UniverseStore` öffnet eine rohe `sqlite3`-Verbindung ohne Pragma | `store.py:53`, `grep -rn foreign_keys` |
| `BarArchive` öffnet ausschließlich `bars.sqlite` | `archive.py:75-78` |
| `enable_divergence_sampler` Default `False` | `phase8_scheduler/scheduler/config.py:207` |
| `measurable_universe()` hat 6 Live-Caller (kein Test) | `wiring.py:457,857,1015,1109`, `heartbeat.py:97`, `run.py:90`, `capital_backfill.py:109` |
| Migrations-Runner: `NNN_description.sql`, `_schema_version`, je Datei eine Transaktion | `persistence/migrations.py:19,40-67` |
| Web-UI öffnet die DB **strukturell read-only**, Kontrolle ist ausschließlich Datei-Schreibung | `webui/api.py:11-16`, `ro_connect` `api.py:71` |

---

## §3 Befunde dieser Planungssession (B1–B6)

> Alle sechs sind **neu** — keiner steht in einem Vorgänger-Dokument. B1 ist ein scharfer
> Live-Blocker, B2 macht das Concept-Done-Kriterium unerreichbar, B3–B5 sind reale Bugs in
> Phase-13-Code, den Phase 14 anfasst, B6 ist eine Zahlenkorrektur.

### §3.1 B1 — `stale_source` sprengt die Registry beim **Lesen** 🔴

`DS_STALE_SOURCE = "stale_source"` wurde in Phase 13 A4 eingeführt
(`phase12_data_foundation/data_foundation/models.py:33`) und wird von
`wiring.py:1002-1005` (`_mark_stale`) über `UniverseStore.set_symbol` geschrieben.
`set_symbol` schreibt **rohes SQL ohne Validierung** (`store.py:233-237`) — der Write geht
durch. Aber `phase9_universe/universe/models.py:61-63` kennt den Wert nicht:

```python
_VALID_DATA_SOURCE_STATUSES = frozenset(
    {DS_OK, DS_UNVERIFIED, DS_NO_SOURCE, DS_NO_INTRADAY_SOURCE, DS_MISMATCH}
)
```

`UniverseRecord.__post_init__` (`models.py:109-110`) wirft darauf. **Reproduziert** (frische
DB, Migrationen 001–006, ein `active`-Epic, `set_symbol(..., status=DS_STALE_SOURCE)`):

```
write ok, DS_STALE_SOURCE = stale_source
READ RAISES: ValueError invalid data_source_status: 'stale_source'
[]            # measurable_universe() überlebt nur, weil es auf ='ok' filtert
```

**Wirkung:** `active_universe()` (`store.py:210-212` → `list_by_status`) wirft ab dem
Moment, in dem ein Epic als `stale_source` markiert wurde. Damit stirbt `wiring.py:131`
(`_build_research`) beim nächsten Daemon-Start. **Scharf wird das genau dann, wenn die
Beweiswoche `enable_divergence_sampler=True` setzt — was P9 („Kein Epic mit toter Historie
steht auf `ok`") zwingend verlangt.** Heute noch unscharf (Default `False`).

**Fix:** zwei Zeilen in `phase9_universe/universe/models.py` + ein Regressionstest, der
genau diesen `ValueError` fängt. **Block A1**, nach Block 0, eigener Commit (D19).

### §3.2 B2 — Die Concept-Schema-Skizze kann `EPIC_MAP` nicht ersetzen

`phase14_discovery_concept.md` §2.2 listet
`(epic, source, resolution, history_min_days, latency_min, last_verified_utc, notes)`.
`EPIC_MAP` bildet aber `IX.D.DAX.IFMM.IP → "DE40"` ab — ein **Symbol**, keine Verfügbarkeit.
Ohne eine Spalte dafür kann `run_capital_backfill` die Tabelle nicht lesen und das
Concept-Done-Kriterium („`grep -n "EPIC_MAP" phase13_live_data/` ist leer") ist unerreichbar.

**Korrektur (datiert 2026-08-22):** die Tabelle bekommt `source_symbol TEXT`. Damit ist
`instrument_universe.yf_ticker` exakt `source_symbol WHERE source='yf'` — dieselbe
Generalisierung, die die yF-Projektion (D4) überhaupt erst stimmig macht.

### §3.3 B3 — `capital_backfill.py --auto` ist strukturell kaputt

`_resolve_epics` (`scripts/capital_backfill.py:102-113`) baut
`UniverseStore(args.db)`. `args.db` hat den Default `data/bars.sqlite`
(`capital_backfill.py:47,88`). `instrument_universe` liegt aber in
`data/trading_bot.sqlite` — heute nachgeprüft: `bars.sqlite` enthält nur
`bars`, `source_spend`, `allowance_observations`, `sqlite_sequence`.

⇒ `--auto` läuft in `sqlite3.OperationalError: no such table: instrument_universe`.
Ein `--db data/trading_bot.sqlite` würde es „lösen" und stattdessen das **Archiv** auf die
Trading-DB umbiegen. Die Option ist seit Session 12 nie erfolgreich gelaufen (der
Live-Lauf 2026-08-22 nutzte `--epics`).

**Fix:** eigenes `--universe-db`-Argument mit Default `data/trading_bot.sqlite`
(Muster: `data_foundation/run.py:114-116` trennt `--universe-db` und `--bars-db` genau so).

### §3.4 B4 — `NameError` im Fehlerpfad desselben Scripts

`capital_backfill.py:187-191`:

```python
    except Exception as exc:  # noqa: BLE001 — top-level safety net
        _eprint(f"[capital_backfill] backfill raised: {exc}")
        print(json.dumps({"ok": False, "error": f"backfill_raised: {exc}",
                          "partial_results": results}))
```

`results` wird erst durch die Zuweisung in Zeile 186 gebunden. Wirft
`run_capital_backfill`, ist der Name ungebunden ⇒ der Handler wirft `NameError` und
verschluckt die eigentliche Fehlermeldung.

### §3.5 B5 — `written` zählt Versuche, nicht Schreibvorgänge

`backfill.py:414-416`:

```python
            try:
                archive.insert_bars([archive_bar])
                written += 1
```

`BarArchive.insert_bars` **gibt die Zahl der wirklich neuen Zeilen zurück**
(`archive.py:119-133`, `INSERT OR IGNORE` + `cur.rowcount`). Der Rückgabewert wird
verworfen; ein Duplikat zählt als Schreibvorgang.

**Konsequenz für die Beweislage:** die live-verifizierte Zahl „962 bars written"
(`PHASE13_CLOSEOUT_HANDOVER.md` §2.4) heißt korrekt **„962 Insert-Versuche"**. Sie stimmt
mit der Archiv-Zählung überein (heute nachgemessen: 962 `source='capital'`-Zeilen), aber
**nur weil es ein Erstlauf war** — die Übereinstimmung ist kein Beweis dafür, dass der
Zähler richtig ist. Ein zweiter Lauf über dasselbe Fenster meldete erneut 962 und schriebe 0.

### §3.6 B6 — Die Test-Summe 1508 ist ein Additionsfehler

`phase13_live_data/CLAUDE.md:169` nennt „1508 passed". Die **Einzelzahlen derselben
Tabelle** summieren sich auf **1608**, und mein heutiger Sweep reproduziert jede Einzelzahl
exakt. Es ist ein Summenfehler, **keine Drift** — niemand muss 100 fehlende Tests suchen.

---

## §4 Gelockte Entscheidungen D1–D20

> **Diese Tabelle wird nicht neu verhandelt.** Jede Zeile trägt ihren Grund, damit niemand
> sie gutgemeint wieder aufmacht. Widerspricht neue Evidenz einer Zeile: **als Finding
> melden, nicht still abweichen** (Root-`CLAUDE.md`, Working style).

| # | Entscheidung | Begründung |
|---|---|---|
| **D1** | Neue Tabelle **`instrument_source_availability`**, Phase-2-**Migration 007**, in `data/trading_bot.sqlite`. | 007 ist frei (`_schema_version`=6, heute gemessen). Dieselbe DB wie `instrument_universe` ⇒ ein Migrationsrunner, ein Backup, keine Cross-File-Transaktion. |
| **D2** | Die Tabelle hat **`source_symbol TEXT`**. | Ohne sie kann sie `EPIC_MAP` nicht ersetzen ⇒ das Done-Kriterium wäre unerreichbar. Korrigiert Concept §2.2 (§3.2). |
| **D3** | **`measurable_universe()` und `data_source_status` bleiben unangetastet.** Kein Re-Point des Mess-Gates in Phase 14. | Die Beweiswoche (P2/P3/P5/P8) hängt an diesem Gate, E7 lockt „parallel". 6 Live-Caller in vier Phasen. Repo-Regel nach P12.5: den neuen Pfad danebenlegen, den bewiesenen nicht umbiegen (L14-Muster). |
| **D4** | Die **`yf`-Zeile ist eine Projektion** mit `origin='registry'`, geschrieben **in `UniverseStore.set_symbol`** — dem einen Choke-Point. Nie unabhängig geschrieben, nie vom Mess-Gate gelesen. | „Eine Tatsache, drei Speicher" ist die Sünde *unabhängiger Schreiber*, nicht die eines benannten, geprüften Read-Models. `set_symbol` ist laut eigenem Docstring (`store.py:222`) „the one writer of `yf_ticker`" — alle Aufrufer laufen dort durch. |
| **D5** | Die Projektion darf den Registry-Write **niemals scheitern lassen**: Registry zuerst, Projektion danach, Fehler laut geloggt und **nicht-fatal**. | Fehlgriff-Symptom §8.2: ein Epic fällt still aus der Messung. Ein Projektions-Bug darf die Registry nicht mitreißen. |
| **D6** | Die **`ig`-Zeile wird abgeleitet, nie erprobt**: jede `instrument_universe`-Zeile *ist* per Definition eine IG-Epic. Discovery ruft **nie** `/prices` und **nie** `search_markets`. | Struktureller Kostendeckel statt Zählwert — dieselbe Beweisform wie L12 (`test_get_window_never_fetches`). Die Lehre aus P12.5: 123 grüne Tests konnten den Kostenfehler nicht sehen, eine Struktur-Zusicherung schon. |
| **D7** | **`prefer` in `BarArchive.window` bleibt unangetastet.** | `BarArchive` öffnet ausschließlich `bars.sqlite` (`archive.py:75-78`), die Tabelle liegt in `trading_bot.sqlite`. Tabellenbewusstes `window()` wäre genau die Cross-File-Kopplung, die Phase 12 D4 bewusst vermieden hat. Beantwortet Concept-Q3 mit **Nein**. |
| **D8** | Die Tabelle ist eine **Fakten**-Tabelle (was kann wer), **keine Präferenz-Tabelle**. | Concept §4, unverändert gültig. Rangfolge bleibt Sache des Konsumenten. |
| **D9** | Discovery läuft als **eigener Daemon** `source_registry/run.py`, Muster `data_foundation/run.py` (PID-File, `SIGTERM`/`SIGINT` → graceful, `--interval-s`). **Nie eine IG-Session.** | Nikinger-Entscheidung 2026-08-22. Isolation wie beim Recorder: ein Discovery-Fehler kann den Trading-Daemon nicht bremsen, und der Prozess mit der einen warmen IG-Session bekommt kein zweites Fremd-Credential. |
| **D10** | Der Daemon arbeitet **nur scharfgestellt** — Flag-Datei `data/state/DISCOVERY_ARMED`. Die sichere Richtung jeder Mehrdeutigkeit ist **NICHT scharf**. | Gegenteil des KILL-Files (dort heißt Mehrdeutigkeit „gekillt"), und genau deshalb explizit festgehalten: unscharf kostet null Netz und null Kontingent. Ein halb geschriebenes Flag darf nie versehentlich fetchen. |
| **D11** | Die **UI schaltet scharf per Datei-Schreibung**, nie per DB-Write. | `webui/api.py` öffnet die DB strukturell read-only (`api.py:11-13`), Kontrolle ist per Design „files only" (`api.py:14-16`). Ein DB-Write aus der UI wäre ein Architektur-Bruch, kein Feature. |
| **D12** | Bis scharfgestellt zeigt die UI eine **Warnung** (Banner-Muster `kill-banner`, `index.html:61-64`). | Nikinger-Anforderung 2026-08-22: „die UI zeigt so lange eine Warnung, bis man über einen Button aktiviert". |
| **D13** | Jeder Discovery-Fetch, der Netz kostet, wird im **existierenden** Ledger gebucht: `SourceBudget.record_spend(points, kind='discovery')`. | Eigener `spend_kind` — Muster `GapRescue`s `'rescue'`. Der Anlass steht im Failure-Handover §5.1: ein geteilter Provider taggte Tracker-Top-ups fälschlich als `research`. Ledger-Eindeutigkeit ist billiger als Forensik. |
| **D14** | Harte Deckel: `max_probe_calls_per_source_per_run` (Default **8**), `profile_ttl_days` (Default **7**) gegen `last_verified_utc`. | Beantwortet Concept-Q2/Q7 und E2 („wöchentlich"). Die TTL ist eine **Drossel im Daemon**, kein Scheduler-Input — `last_verified_utc` bleibt eine Report-Spalte. |
| **D15** | **Kein Dukascopy-Code, kein Stub.** SP35 (`IX.D.IBEX.FWM2.IP`) bekommt eine Zeile mit `status='no_source'` und typisierter Begründung in `notes`. | Nikinger 2026-08-22: „Raus aus Phase 14, aber nicht ganz raus." Die Beweiswoche entscheidet, ob SP35 überhaupt eine Fremdquelle braucht und ob Dukascopy das richtige Werkzeug ist. Ein `NotImplementedError`-Stub wäre Code, den niemand ausführt. |
| **D16** | Code lebt in **`phase14_discovery/`**, Paket **`source_registry`** — **nicht** `discovery`. | Repo-Konvention „each phase is a self-contained directory". Der Paketname `discovery` kollidiert mit `universe.discovery` (Phase 9, Epic-Sweep) — eine garantierte Verwechslung in jeder Folge-Session. |
| **D17** | **`KNOWN_SOURCES` bleibt der Gatekeeper** für `bars.source` (`data_foundation/models.py:23-25`). Eine Quelle, die in der Verfügbarkeits-Tabelle steht, aber nicht in `KNOWN_SOURCES`, darf **entdeckt**, aber **nicht ins Archiv geschrieben** werden. | Das ist kein Widerspruch zu „neue Quelle = Konfiguration": eine Ein-Zeilen-Vokabular-Erweiterung liegt weit unter dem ≤50-Zeilen-Kriterium und ist ein bewusstes Sicherheitstor. Wer `KNOWN_SOURCES` dynamisch aus der DB speist, macht den Archiv-Schreibpfad konfigurierbar — genau das darf er nicht sein. |
| **D18** | Der `status`-Wortschatz der Tabelle ist **identisch** mit `KNOWN_DATA_SOURCE_STATUSES` (`data_foundation/models.py:34-36`). | Damit ist die yF-Projektion eine **Kopie**, keine Übersetzung. Eine Mapping-Tabelle zwischen zwei Vokabularen wäre die nächste Drift-Quelle. |
| **D19** | Der B1-Fix (`stale_source`) kommt **nach Block 0**, als **eigener Commit vor jedem Phase-14-Code**. | Nikinger 2026-08-22: „nach den initial steps, sonst womöglich auf falsches Fundament bauen". Zusätzlich bleibt die Baseline-Zuordnung sauber: der Sweep nach Block 0 ist noch 1608, der nach A1 ist 1608 + 1. |
| **D20** | Reihenfolge **Block 0 → A → B → C → D ist gelockt.** | 0 ist Hausputz + Baseline (ohne sie ist hinterher nicht zuzuordnen, was der Plan verursacht hat). A ist das Fundament (Fix + Schema + Store + Projektion). B stellt Konsumenten um. C macht es autonom + scharfschaltbar. Wer C vor B baut, hat einen Daemon, der eine Tabelle füllt, die niemand liest. |

**Cross-Phase-Freigabe:** mit der Beantwortung der D19-Frage am 2026-08-22 erteilt, für
**Phase 2** (Migration 007), **Phase 8** (`webui/`, `run_scheduler.sh`), **Phase 9**
(`models.py`, `store.py`), **Phase 12** (`budget.py`-Nutzung, kein Edit vorgesehen) und
**Phase 13** (`backfill.py`, `scripts/`). Ein Touch **außerhalb** dieser Liste ist erneut
freigabepflichtig.

---

## §5 Contracts (verbindlich, gegen diese wird gebaut und getestet)

### §5.1 Migration 007 — `instrument_source_availability`

**Datei:** `phase2_persistence/migrations/007_phase14_source_availability.sql` (NEU).

```sql
CREATE TABLE IF NOT EXISTS instrument_source_availability (
    epic              TEXT NOT NULL,
    source            TEXT NOT NULL,   -- 'ig'|'yf'|'ls'|'capital'|… (frei, D17 gattet nur den Schreibpfad)
    resolution        TEXT NOT NULL,   -- '1m'|'5m'|'1h'|'1d'
    source_symbol     TEXT,            -- D2: 'DE40' | '^GDAXI' | NULL (Quelle nutzt die Epic selbst)
    status            TEXT NOT NULL,   -- D18: identisch zu KNOWN_DATA_SOURCE_STATUSES
    origin            TEXT NOT NULL,   -- 'discovery'|'registry'|'derived'|'operator'
    history_min_days  INTEGER,
    latency_min       INTEGER,
    last_verified_utc TEXT NOT NULL,
    notes             TEXT,
    PRIMARY KEY (epic, source, resolution)
);

CREATE INDEX IF NOT EXISTS idx_isa_source_status
    ON instrument_source_availability(source, status);
```

**Und im selben Migrationsfile der einmalige Backfill** (Block-C-Re-Plan §2 nennt genau
diesen Schritt: „Tabelle anlegen, Backfill einmalig laufen lassen, Konsumenten umstellen"):

```sql
INSERT OR IGNORE INTO instrument_source_availability
    (epic, source, resolution, source_symbol, status, origin, last_verified_utc, notes)
SELECT epic, 'yf', '1m', yf_ticker, data_source_status, 'registry',
       COALESCE(symbol_checked_at, updated_at),
       'backfilled from instrument_universe by migration 007'
FROM instrument_universe;
```

**Warum das in die Migration gehört und nicht in einen Resolver-Lauf:** `SymbolResolver.resolve_epic`
ruft `set_symbol` in **sechs** von acht Pfaden **nicht** — heute nachgemessen an
`phase12_data_foundation/data_foundation/symbols.py`:

| Zeilen | Pfad | schreibt? |
|---|---|---|
| 194-199 | Wochenend-Instrument, **schon** `no_intraday_source` | **nein** (Kurzschluss auf Zeile 195) |
| 207-210 | kein Kandidat, **schon** `no_source` | **nein** (Kurzschluss auf Zeile 208) |
| 213-214 | Markt geschlossen | nein |
| 219-220 | `quote_fetch`/`yf_last_fetch` wirft | nein |
| 222-223 | `yf_result is None` | nein |
| 229-230 | yF-Bar älter als `max_yf_age_min` | nein |

Die drei `SUN*`-Epics stehen **heute schon** auf `no_intraday_source` (§2.2) ⇒ Zeile 195
schließt kurz ⇒ ohne Migrations-Backfill bekämen sie **nie** eine Projektionszeile, egal wie
oft der Resolver läuft. Ein Lauf bei geschlossenem Markt schriebe überhaupt nichts.

Der Backfill kauft zusätzlich den **Identitätsbeweis**: unmittelbar nach der Migration,
**vor der ersten Zeile neuem Code**, muss
`SELECT epic FROM instrument_source_availability WHERE source='yf' AND status='ok'`
genau die fünf Epics aus §2.2 liefern. Offline testbar, kein Live-Lauf nötig.

> **Präzision, damit später niemand darüber stolpert:** die Tabelle ist **nicht**
> epic-status-bewusst (D8 — Fakten, kein Gate). Der Backfill nimmt *alle* 22
> `instrument_universe`-Zeilen, nicht nur die `active`. Dass die `(yf,'ok')`-Menge heute
> exakt der `measurable_universe()`-Menge entspricht, ist eine **Eigenschaft des heutigen
> Substrats** (die 14 `verified`-Zeilen stehen auf `unverified`), keine strukturelle
> Invariante. Wer sie später als Invariante behandelt, baut das Gate nach — genau das
> verbietet D3.

Der Backfill verletzt **D4 nicht**: er ist eine einmalige Ableitung aus der Registry, mit
`origin='registry'` markiert — dieselbe Richtung, derselbe Ursprung, weiterhin ein Schreiber
der zugrunde liegenden Tatsache.

**Kein `FOREIGN KEY`** — bewusst: in `001…006` gibt es **null** FK-Klauseln (heute
gezählt), und `UniverseStore` öffnet eine rohe Verbindung ohne `PRAGMA foreign_keys = ON`
(nur `persistence/db.py:65` setzt es). Ein nicht erzwungener FK ist Dokumentation, die sich
als Constraint verkleidet. Zusätzlich inhaltlich richtig: eine Verfügbarkeits-Zeile für ein
später zurückgezogenes Epic ist **Datum**, keine Korruption.

**`origin`-Wortschatz** (Modul-Konstanten in `source_registry/models.py`):

| Wert | Bedeutung | Schreiber |
|---|---|---|
| `discovery` | eine `Source.discover()` hat es erhoben | Discovery-Daemon |
| `registry` | Projektion aus `instrument_universe` (D4) | `UniverseStore.set_symbol` |
| `derived` | aus vorhandenem Wissen abgeleitet, ohne Netz (D6: `ig`) | Discovery-Daemon |
| `operator` | von Hand gesetzt | Operator-Script |

### §5.2 `SourceProfile` + `Source` (Protocol)

**Datei:** `phase14_discovery/source_registry/models.py` (NEU).

```python
@dataclass(frozen=True)
class SourceAvailability:
    """Eine Zeile der Kreuzungs-Tabelle."""
    epic: str
    source: str
    resolution: str
    source_symbol: str | None
    status: str                 # aus KNOWN_DATA_SOURCE_STATUSES (D18)
    origin: str
    history_min_days: int | None
    latency_min: int | None
    last_verified_utc: str
    notes: str | None = None


@dataclass(frozen=True)
class SourceProfile:
    """Was eine Quelle über sich selbst sagt — das Ergebnis eines discover()-Laufs."""
    source: str
    rows: tuple[SourceAvailability, ...]
    probe_calls_used: int = 0     # D13: was gebucht werden muss
    errors: tuple[str, ...] = ()  # fail-soft: eine kaputte Quelle kippt den Lauf nicht


class Source(Protocol):
    def name(self) -> str: ...
    def discover(self, epics: Sequence[str], *, max_probe_calls: int) -> SourceProfile: ...
```

`discover` bekommt die Epic-Liste **hereingereicht** (aus `instrument_universe`) und
entscheidet selbst, welche davon es beantworten kann. Es öffnet **keine** DB.

### §5.3 `SourceAvailabilityStore`

**Datei:** `phase14_discovery/source_registry/store.py` (NEU). Eigene `sqlite3`-Verbindung
auf `trading_bot.sqlite` (Phasen-Isolation D3-Muster von `UniverseStore`/`BarArchive`).

```python
class SourceAvailabilityStore:
    def __init__(self, db_path: str | Path) -> None: ...
    def close(self) -> None: ...
    def upsert(self, row: SourceAvailability) -> None: ...
    def upsert_many(self, rows: Sequence[SourceAvailability]) -> int: ...
    def for_epic(self, epic: str, *, resolution: str | None = None) -> list[SourceAvailability]: ...
    def for_source(self, source: str, *, status: str | None = None,
                   resolution: str | None = None) -> list[SourceAvailability]: ...
    def symbol_for(self, epic: str, source: str, resolution: str = "1m") -> str | None: ...
    def stale_rows(self, *, ttl_days: int, now_utc: str) -> list[SourceAvailability]: ...
```

`symbol_for` ist die eine Methode, die `EPIC_MAP.get(epic)` ersetzt. `upsert` ist
`INSERT … ON CONFLICT(epic, source, resolution) DO UPDATE` — Muster
`UniverseStore.upsert_discovered` (`store.py:130-137`).

### §5.4 Scharf-Flag

**Datei:** `phase14_discovery/source_registry/arm.py` (NEU), Muster
`phase8_scheduler/scheduler/killswitch.py` (atomar `.tmp` + `os.replace`, fail-soft, wirft nie).

```python
def is_armed(arm_path: str) -> bool: ...          # fehlend/leer/unparsebar/unbekannt -> False (D10)
def arm(arm_path: str, by: str) -> None: ...      # {"armed": true, "by": ..., "ts": ...}
def disarm(arm_path: str) -> None: ...            # Datei löschen (No-Op wenn absent)
def read_state(arm_path: str) -> dict | None: ...  # für die UI-Anzeige
```

Default-Pfad: `data/state/DISCOVERY_ARMED`.

### §5.5 Web-UI-Naht

**Datei:** `phase8_scheduler/webui/api.py`.

| Endpoint | Verhalten |
|---|---|
| `GET /api/discovery` | `{armed, armed_by, armed_ts, last_run_utc, rows_total, rows_by_source, stale_rows}` — reine Lesung (`ro_connect` + Flag-Datei) |
| `POST /api/discovery/arm` | `arm.arm(path, by="dashboard")` → `{ok: true, armed: true}` |
| `POST /api/discovery/disarm` | `arm.disarm(path)` → `{ok: true, armed: false}` |

Front-End: Warn-Banner + zwei Buttons, Muster `kill-banner` / `btn-kill`.

---

## §6 Schritt-Sequenz

> **Commit nach jedem Schritt** (Nikinger-Auflage, gilt weiter). Nach jedem Schritt
> `pytest <betroffene Suite> -q` — ein Schritt ist nicht fertig, bevor seine Tests grün sind.
> **Push fragt der Nikinger frei**, nie selbst pushen.

### Block 0 — Hausputz und Baseline (kein neuer Produktionscode)

#### 0.0 — Gegenprobe und Baseline

```bash
git status --short                  # muss leer sein
ps aux | grep scheduler.run         # muss leer sein (Parallel-Login-Falle)
```

Regression-Baseline: **bereits am 2026-08-22 von der Planungssession aufgenommen**, §2.1.
Die ausführende Session **wiederholt den Sweep einmal** und vergleicht gegen die Tabelle.
Abweichung ⇒ **stop und melden**, nicht weiterbauen — die Baseline ist der Bezugspunkt für
alles, was danach kommt.

**Akzeptanz 0.0:** Sweep reproduziert 1608, working tree clean, kein Bot-Prozess.

#### 0.1 — Turbo-/Legacy-Grep-Ritual: **nicht wiederholen**

Ergebnis steht in §2.3 (3 harmlose „strike"-Treffer, `turbo_candidates` = eingefrorener
Contract-Name). Die ausführende Session schreibt **eine Zeile** in ihren Session-Block, die
auf §2.3 verweist. **Akzeptanz:** dokumentierter No-Op.

#### 0.2 — Nummerierungs-Nachlese (ein Doc-Commit)

Die Kaskade vom 2026-08-22 (V4 → Phase 15) hat vier Stellen übersehen. Alle vier sind
derselbe Fehler.

| Datei:Zeile | Verbatim-Anker (heute) | Änderung |
|---|---|---|
| `ROADMAP.md:625` | `### 14a — Council Skill Integration *(vormals 9a / 11a / 12a / 13a)*` | `### 15a — … *(vormals 9a / 11a / 12a / 13a / 14a)*` |
| `ROADMAP.md:629` | `### 14b — Handover-Logik (Bull/Bear/Judge) *(vormals 9b / 11b / 12b / 13b)*` | analog `15b` |
| `ROADMAP.md:634` | `### 14c — Reward/Punishment Reform *(vormals 9d / 11c / 12c / 13c)*` | analog `15c` |
| `ROADMAP.md:638` | `### 14d — Force Trigger Safeguard *(vormals 9e / 11d / 12d / 13d)*` | analog `15d` |
| `ROADMAP.md:643` | `### 14e — Instinct-Promotion (ECC) + Longterm VETO` | analog `15e` |
| `README.md:126` | `**Phase 14 (V4)** *(umnummeriert 2026-08-11 und erneut 2026-08-18 — war vorher "Phase 12",` | `**Phase 15 (V4)** *(umnummeriert 2026-08-11, 2026-08-18 und 2026-08-22 — war vorher "Phase 12",` + Phase-14-Erwähnung (Discovery) in der Aufzählung darunter |
| `phase10_v3/CLAUDE.md:21` | `  - ../ROADMAP.md   # Phase 11 (this work, deferred) + Phase 12 (Datenfundament) + Phase 13 (Live-Datenfundament, opened 2026-08-18) + Phase 14 (V4) sections` | `… + Phase 14 (Discovery) + Phase 15 (V4) sections` |
| `ARCHITECTURE.md:60` | `> **V4 moves to Phase 14.** Every "Phase 13 (V4)" reference below now means Phase 14.` | neue datierte Korrekturzeile darunter: `⟳ Correction (2026-08-22): V4 moves again, to **Phase 15**; **Phase 14** is Discovery-Then-Deterministic.` (die alte Zeile **stehen lassen** — Auditkette) |
| `ARCHITECTURE.md:171` | `  deferred to **Phase 14e (V4)**, gated on real outcomes **and** on Phase 9/10 (V2/V3) landing first` | `**Phase 15e (V4)**` |
| `ARCHITECTURE.md:230` | `   enforce it against — tracked as Phase 14d (V4), whenever manual override is built.` | `Phase 15d (V4)` |
| `ARCHITECTURE.md:261` | `- Phase 14 (V4 — Sophisticated/Optional, deferred) — no concept doc yet` | zwei Zeilen: Phase 14 (Discovery, mit Plan-Link) + Phase 15 (V4, deferred) |

Zusätzlich im selben Commit, **E6 aus dem Closeout-Handover**:

| Datei:Zeile | Verbatim-Anker | Änderung |
|---|---|---|
| `phase13_live_data/CLAUDE.md:83` | `| \`tests/\` | gemockt, kein Netz, kein LLM | ✅ 39 Tests grün |` | `50 Tests grün` |
| `phase13_live_data/CLAUDE.md:169` | `    Docs-Edits, aber unverändert): 1508 passed.` | `1608 passed` + Fußnote „(Summenkorrektur 2026-08-22: die Einzelzahlen derselben Tabelle ergeben 1608; kein Test verschwunden — §3.6 des Phase-14-Plans)" |
| `phase13_live_data/CLAUDE.md:76,77,82` | die drei Block-C-Modulzeilen | Zusatz `— final (Block C geschlossen 2026-08-22)` |

**Akzeptanz 0.2:** `grep -rn "Phase 14 (V4)" --include=*.md .` liefert nur noch Treffer in
📦-Archiven und 📕-Snapshots (die werden **nicht** editiert). Ein Doc-Commit, keine
Code-Änderung.

#### 0.3 — Die drei Phase-13-Script-Bugs (B3/B4/B5)

Ein Commit, drei Fixes, drei Tests. Sie gehören **vor** Block B, weil Block B genau diese
Funktionen umbaut — ein Fehlschlag dort wäre sonst nicht zuzuordnen.

**B3** — `phase13_live_data/scripts/capital_backfill.py`

Anker (Zeile 47): `_DEFAULT_DB_PATH = _REPO_ROOT / "data" / "bars.sqlite"`
Anker (Zeile 87-90):
```python
    parser.add_argument(
        "--db", default=str(_DEFAULT_DB_PATH),
        help=f"path to bars.sqlite (default: {_DEFAULT_DB_PATH})",
    )
```
Anker (Zeile 107): `        store = UniverseStore(args.db)`

Fix: `_DEFAULT_UNIVERSE_DB_PATH = _REPO_ROOT / "data" / "trading_bot.sqlite"` ergänzen, ein
`--universe-db`-Argument mit diesem Default hinzufügen, Zeile 107 auf `args.universe_db`
umstellen. **Muster:** `data_foundation/run.py:114-116` trennt `--universe-db`/`--bars-db`
genau so.

**B4** — dieselbe Datei, Anker (Zeile 185-191):
```python
    try:
        results = run_capital_backfill(source, archive, epics, start, end)
    except Exception as exc:  # noqa: BLE001 — top-level safety net
        _eprint(f"[capital_backfill] backfill raised: {exc}")
        print(json.dumps({"ok": False, "error": f"backfill_raised: {exc}",
                          "partial_results": results}))
```
Fix: `results: dict[str, int] = {}` **vor** dem `try` binden.

**B5** — `phase13_live_data/live_data/backfill.py`, Anker (Zeile 414-416):
```python
            try:
                archive.insert_bars([archive_bar])
                written += 1
```
Fix: `written += archive.insert_bars([archive_bar])`. Docstring von `run_capital_backfill`
(Zeile 376-380) auf „genuinely new rows" präzisieren.

**Tests** (`phase13_live_data/tests/test_backfill.py` + NEU
`phase13_live_data/tests/test_capital_backfill_script.py`, ≥ 3):
1. `run_capital_backfill` mit einem Archiv-Fake, dessen `insert_bars` `0` zurückgibt
   (Duplikat) ⇒ `results[epic] == 0`, **nicht** `n`.
2. `_resolve_epics(--auto)` öffnet den Universe-DB-Pfad, **nicht** den Bars-Pfad
   (Assertion auf das übergebene Pfad-Argument eines gemockten `UniverseStore`).
3. Der `except`-Pfad in `main` produziert gültiges JSON mit `partial_results: {}` statt
   `NameError` (gemocktes `run_capital_backfill`, das wirft).

**Akzeptanz 0.3:** `pytest phase13_live_data/tests -q` → 50 + 3 = **53 grün**.

#### 0.4 — Phasen-Gerüst

Neu anzulegen:

```
phase14_discovery/
├── CLAUDE.md            ← existiert bereits (mit diesem Plan committet) — NICHT neu anlegen,
│                          nur den Session-Block nach der Rotationsregel fortschreiben
├── README.md            ← NEU (public surface, Modul-Tabelle)
├── pyproject.toml       ← NEU (Muster: phase13_live_data/pyproject.toml, name = "source_registry")
├── requirements.txt     ← NEU (leer bzw. nur `requests` falls eine Quelle es braucht)
├── source_registry/__init__.py   ← NEU (leer)
└── tests/__init__.py             ← NEU (leer)
```

`scripts/dev_install.sh` — Anker (Zeile 58-59):
```
    phase13_live_data
do
```
⇒ `phase13_live_data \` + neue Zeile `    phase14_discovery`. Die Abschluss-Zeile
(`dev_install.sh:65`) sagt „all twelve packages" — auf „thirteen" korrigieren (heute schon
falsch: es sind zwölf Einträge, aber der Satz stammt aus der Zeit vor `phase13_live_data`;
nach dem Anhängen sind es dreizehn).

Jede neue `.md` bekommt ihre `docs/INDEX.md`-Zeile im **selben** Commit.

**Akzeptanz 0.4:** `python -c "import source_registry"` läuft; `docs/INDEX.md` kennt jede
neue Datei; `pytest phase14_discovery/tests -q` läuft (0 Tests, kein Fehler).

---

### Block A — Fundament

#### A1 — B1-Fix: `stale_source` (eigener Commit, D19)

**Datei:** `phase9_universe/universe/models.py`.

Anker (Zeile 55-59):
```python
DS_OK = "ok"
DS_UNVERIFIED = "unverified"
DS_NO_SOURCE = "no_source"
DS_NO_INTRADAY_SOURCE = "no_intraday_source"
DS_MISMATCH = "mismatch"
```
⇒ `DS_STALE_SOURCE = "stale_source"` ergänzen, mit Kommentar `# Phase 13 §6 A4 (F1): IG
lieferte ok=True auf tote Historie — geschrieben von wiring.py::_mark_stale`.

Anker (Zeile 61-63):
```python
_VALID_DATA_SOURCE_STATUSES = frozenset(
    {DS_OK, DS_UNVERIFIED, DS_NO_SOURCE, DS_NO_INTRADAY_SOURCE, DS_MISMATCH}
)
```
⇒ `DS_STALE_SOURCE` in das Set.

**Test** (`phase9_universe/tests/test_store.py`, +1):
- `set_symbol(epic, ticker, symbol_source='seed', status='stale_source')`, danach
  `active_universe()` ⇒ liefert die Zeile zurück, **wirft nicht**. Ohne den Fix ist der
  Fehler `ValueError: invalid data_source_status: 'stale_source'` (§3.1, reproduziert).

**Akzeptanz A1:** `pytest phase9_universe/tests -q` → 80 + 1 = **81 grün**;
Gesamt-Baseline 1608 + 4 (A1 + 0.3) = **1612**.

> **Warum nicht in Block 0:** Nikinger-Entscheidung 2026-08-22 — „nach den initial steps,
> sonst womöglich auf falsches Fundament bauen". Der Hausputz beweist zuerst, dass die
> Baseline stimmt; erst danach wird an einer abgeschlossenen Phase operiert.

#### A2 — Migration 007 + `SourceAvailabilityStore`

**Dateien:** `phase2_persistence/migrations/007_phase14_source_availability.sql` (NEU,
Contract §5.1), `phase14_discovery/source_registry/models.py` (NEU, Contract §5.2),
`phase14_discovery/source_registry/store.py` (NEU, Contract §5.3).

Implementierungshinweise:
- Der Migrations-Header trägt dieselbe Kommentar-Disziplin wie `006_…sql:1-14`: **warum**,
  nicht nur **was**. Insbesondere: warum kein FK (§5.1), und dass `status` bewusst denselben
  Wortschatz wie `data_source_status` benutzt (D18).
- `store.py` duplizieren, nicht importieren: `utc_iso_now` (Muster `store.py:36-39`) —
  Phasen-Isolation, kein Cross-Phase-Import auf Modulebene.
- `upsert` als `INSERT … ON CONFLICT(epic, source, resolution) DO UPDATE SET …` (Muster
  `UniverseStore.upsert_discovered`, `store.py:130-137`).
- `stale_rows(ttl_days, now_utc)`: Vergleich **lexikalisch** über `last_verified_utc <
  cutoff_iso` — Repo-Konvention, jeder Zeitstempel dieser Tabelle kommt aus demselben
  Formatter, also ist lexikalische Ordnung chronologische Ordnung.

**Tests** (`phase14_discovery/tests/test_store.py`, NEU, ≥ 10):
1. `ensure`/Migration legt die Tabelle an, `PRAGMA table_info` zeigt alle 10 Spalten
2. `upsert` schreibt, `for_epic` liest zurück (Round-Trip inkl. `source_symbol=None`)
3. `upsert` derselben `(epic, source, resolution)` **überschreibt**, legt keine zweite Zeile an
4. `upsert_many` gibt die Zahl der berührten Zeilen zurück
5. `for_source('capital', status='ok')` filtert korrekt
6. `for_epic(epic, resolution='1m')` filtert korrekt
7. `symbol_for` liefert `'DE40'` für die Capital-Zeile
8. `symbol_for` liefert `None` für eine unbekannte Kombination (**wirft nicht**)
9. `stale_rows(ttl_days=7)` liefert genau die Zeile mit altem `last_verified_utc`
10. eine Zeile mit einem `source`, der nicht in `KNOWN_SOURCES` steht, lässt sich schreiben
    und lesen (D17: die Tabelle gattet nicht, der Archiv-Schreibpfad gattet)
11. **Identitätsprobe des Migrations-Backfills:** eine Fixture-DB mit den 22 Zeilen aus §2.2
    (fünf `active`+`ok`, drei `active`+`no_intraday_source`, 14 `verified`+`unverified`),
    Migration 007 anwenden ⇒ `for_source('yf', status='ok')` liefert **genau** die fünf
    Epics aus §2.2, und die drei `SUN*`-Epics stehen auf `no_intraday_source`. ← das ist der
    Test, der beweist, dass die Umstellung nichts verliert
12. Migration 007 zweimal anwenden ist ein No-Op (`INSERT OR IGNORE`, keine Duplikate)

**Akzeptanz A2:** 12 Tests grün; `SourceAvailabilityStore` hat **null Aufrufer** (wird in
A3/A4 verdrahtet).

#### A3 — Quell-Profile: `derived` (IG) + `static` (LS) + Registry-Projektion (yF)

**Datei:** `phase14_discovery/source_registry/sources.py` (NEU).

Drei Quellen, **keine einzige davon macht einen Netz-Call**:

| Quelle | `discover()` | `origin` | Netz |
|---|---|---|---|
| `IGDerivedSource` | jede übergebene Epic ⇒ eine Zeile `status='ok'`, `source_symbol=None`, `history_min_days=30`, `latency_min=0` | `derived` | **nein** (D6) |
| `LSStaticSource` | statisches Profil: `status='no_source'` solange `bars.source='ls'` leer ist; `latency_min=0` | `derived` | **nein** |
| `RegistryYFSource` | liest die übergebenen `UniverseRecord`-Shapes und spiegelt `yf_ticker` + `data_source_status` | `registry` | **nein** (D4) |

Der **strukturelle Kostentest** ist der wichtigste Test dieses Schritts:

**Tests** (`phase14_discovery/tests/test_sources.py`, NEU, ≥ 8):
1. `IGDerivedSource.discover(epics, max_probe_calls=0)` liefert für jede Epic eine Zeile
2. **`IGDerivedSource` bekommt einen Broker-Fake, dessen jede Methode `AssertionError`
   wirft — `discover()` läuft trotzdem durch und `probe_calls_used == 0`.** ← das ist der
   Test, der D6 strukturell zusichert (Muster `test_get_window_never_fetches`)
3. dasselbe für `RegistryYFSource` (Store-Fake, dessen Fetch-Methoden werfen)
4. `RegistryYFSource` spiegelt `data_source_status='ok'` 1:1 nach `status='ok'`
5. `RegistryYFSource` spiegelt `no_intraday_source` 1:1 (kein Downgrade auf `no_source`)
6. `RegistryYFSource` setzt `origin='registry'` auf jeder Zeile
7. `LSStaticSource` liefert `no_source` für jede Epic (heute; `bars.source='ls'` = 0)
8. eine Quelle, die intern wirft, liefert `SourceProfile(errors=(...,))` statt zu werfen

**Akzeptanz A3:** 8 Tests grün; **Test 2 ist das Akzeptanzkriterium der Phase für D6.**

#### A4 — Die yF-Projektion in `UniverseStore.set_symbol`

**Datei:** `phase9_universe/universe/store.py`.

Anker (Zeile 214-238) — `def set_symbol(` bis `self.conn.commit()`. Der bestehende
Registry-Write bleibt **unverändert**; **danach**, in einem eigenen `try/except`, die
Projektion:

```python
        # Phase 14 D4/D5: Projektion in instrument_source_availability. Die Registry
        # bleibt der eine Schreiber der yF-Wahrheit; diese Zeile ist ein benanntes
        # Read-Model (origin='registry'), das das Mess-Gate NIE liest. Nicht-fatal:
        # ein Projektions-Fehler darf den Registry-Write nicht mitreißen (D5) —
        # sonst fällt ein Epic still aus der Messung (§8.2).
        try:
            self._project_availability(epic, yf_ticker, status, now)
        except Exception:  # noqa: BLE001 — D5
            logger.warning(
                "source-availability projection failed for %s (registry write stands)",
                epic, exc_info=True,
            )
```

**Schreib-Mechanik — gelockt, nicht der ausführenden Session überlassen:**
`_project_availability` setzt **rohes SQL über `self.conn` ab** und importiert
`source_registry` **nicht**.

Grund, in zwei Sätzen: `phase9_universe` ist eine abgeschlossene Phase, von der
`phase14_discovery` abhängt — die Gegenrichtung wäre ein Paket-Zyklus, den auch ein Lazy-Import
im Funktionsrumpf nur zur Importzeit versteckt, nicht architektonisch auflöst. Und ein
`SourceAvailabilityStore` würde aus einer Klasse heraus, die bereits eine Verbindung auf
`trading_bot.sqlite` hält, eine **zweite** öffnen — genau die Schreiblast-Trennung, deretwegen
`bars.sqlite` überhaupt eine eigene Datei ist (`archive.py:4-7`).

**Der Preis** (bewusst bezahlt): die Spaltenliste steht an zwei Stellen. Drei Mitigationen
sind Pflicht:
1. Das **DDL steht ausschließlich in Migration 007** — weder `set_symbol` noch
   `SourceAvailabilityStore` legt die Tabelle an. Fehlt sie, ist das ein Operator-Fehler, der
   sichtbar sein muss (und in `set_symbol` durch D5 nicht-fatal bleibt).
2. Beide Schreiber benutzen **denselben** `INSERT … ON CONFLICT(epic, source, resolution) DO UPDATE`.
3. **Ein Test vergleicht sie:** derselbe Input über `set_symbol` und über
   `SourceAvailabilityStore.upsert` erzeugt **bit-identische Zeilen** (`SELECT *` beider Wege
   gleich). Divergiert die Spaltenliste je, fällt dieser Test — nicht der Live-Betrieb.

`_project_availability` öffnet **keine zweite Verbindung** — dieselbe Datei, eine Transaktion
pro `commit`. `store.py` hat heute **keinen** `logger` und importiert `logging` nicht
(`store.py:15-24` geprüft); beides ergänzen (Repo-Konvention: stderr, nie stdout).

**Tests** (`phase9_universe/tests/test_store.py`, +6):
1. nach `set_symbol(epic, '^GDAXI', symbol_source='seed', status='ok')` existiert genau
   eine Zeile `(epic, 'yf', '1m')` mit `source_symbol='^GDAXI'`, `status='ok'`,
   `origin='registry'`
2. ein zweiter `set_symbol`-Aufruf mit anderem Status **überschreibt** die Projektion
3. `set_symbol(epic, None, symbol_source=None, status='no_source')` projiziert
   `source_symbol=None`, `status='no_source'`
4. **fehlt die Tabelle (alte DB ohne Migration 007), wirft `set_symbol` nicht** und der
   Registry-Wert steht trotzdem korrekt in `instrument_universe` ← D5
5. `measurable_universe()` liefert **exakt dasselbe** wie vor dem Schritt (Byte-gleicher
   Vergleich über eine Fixture mit den fünf Live-Epics)
6. **Doppelschreiber-Gleichheit:** derselbe Input über `set_symbol` und über
   `SourceAvailabilityStore.upsert` erzeugt bit-identische Zeilen

**Akzeptanz A4 (falsifizierbar, gegen das heutige Substrat) — der Beweis liegt bei der
Migration, nicht beim Resolver-Lauf:** unmittelbar nach Migration 007 (A2, Test 11) muss
`(source='yf', status='ok')` genau `IX.D.CAC.IFE.IP`, `IX.D.DAX.IFMM.IP`, `IX.D.DAX.IGN.IP`,
`IX.D.IBEX.FWM2.IP`, `IX.D.IBEX.IFM.IP` enthalten und die drei `SUN*`-Epics auf
`no_intraday_source` stehen. **A4 selbst beweist nur den inkrementellen Pfad**: dass ein
*Statuswechsel* durch `set_symbol` in der Tabelle ankommt.

> **Warum die Akzeptanz nicht am Resolver-Lauf hängen darf:** `resolve_epic` ruft `set_symbol`
> in sechs von acht Pfaden nicht (Tabelle in §5.1). Ein Epic, das schon auf seinem Zielstatus
> steht, erzeugt **nie** eine Projektionszeile — deshalb macht die Migration den Grundbestand
> und `set_symbol` nur die Fortschreibung.

---

### Block B — Konsumenten lesen die Tabelle

#### B1 — `CapitalSource.discover()` + Operator-Probe

**Datei:** `phase13_live_data/live_data/backfill.py` (Cross-Phase, freigegeben).

Neue Methode auf `CapitalSource`, unterhalb von `fetch_window` (heute Zeile 167-228):

```python
    def discover(self, epics, *, max_probe_calls: int = 8) -> "SourceProfile": ...
```

**Wie sie entdeckt:** `GET /api/v1/markets?searchTerm=<Suchbegriff>` je Epic-Name, das
Ergebnis auf ein Kürzel (`DE40`) abbilden. **Achtung — die Antwort-Form ist unbekannt.**
`_extract_ohlc` (`backfill.py:339-366`) rät heute vier Feldnamen-Varianten pro OHLC-Feld,
weil die REST-Form nie inspiziert wurde (eigener Docstring, `backfill.py:341-344`). Die
Discovery wird dieselbe Unsicherheit treffen.

**Deshalb ist B1 zweigeteilt:**

- **B1a (Operator, Netz, kostenlos):** `phase13_live_data/scripts/probe_capital.py` um einen
  `--markets`-Modus erweitern, der `GET /markets?searchTerm=…` roh ausgibt. Der Nikinger
  läuft ihn; die ausführende Session **liest den Output und baut danach**. Kosten: 0 €
  (Demo-Konto), kein IG-Kontingent berührt. Befehl:
  ```bash
  phase1_broker_wrapper/.venv/bin/python phase13_live_data/scripts/probe_capital.py \
      --markets --terms "Germany 40,France 40,Spain 35"
  ```
- **B1b:** `discover()` gegen die **beobachtete** Form bauen, gemockt getestet.

**Kein Raten.** Wenn B1a nicht gelaufen ist, wird B1b nicht gebaut — dann bleibt die
Capital-Zeile `origin='operator'` und wird von einem kleinen Seed-Script gesetzt (die zwei
heute bekannten Paare). Das erfüllt Block B trotzdem, weil `EPIC_MAP` verschwindet.

**Tests** (`phase13_live_data/tests/test_backfill.py`, +4): gemockt, kein Netz;
`max_probe_calls=0` ⇒ null HTTP-Calls, `probe_calls_used == 0`; ein 404 auf Spain 35 ⇒
`status='no_source'` + `notes`, **kein** Raise.

#### B2 — `run_capital_backfill` liest die Tabelle, `EPIC_MAP` verschwindet

**Datei:** `phase13_live_data/live_data/backfill.py`.

Anker (Zeile 85-88):
```python
EPIC_MAP: dict[str, str] = {
    "IX.D.DAX.IFMM.IP": "DE40",   # Germany 40
    "IX.D.CAC.IFE.IP":  "FR40",   # France 40
}
```
⇒ **löschen.**

Anker (Zeile 180): `        capital_epic = EPIC_MAP.get(epic)`
⇒ `capital_epic = self._symbol_lookup(epic)` — ein **hereingereichter** Callable
`Callable[[str], str | None]`, Default `lambda _e: None`. `CapitalSource` bekommt **keine**
DB-Verbindung (Phasen-Isolation; die Auflösung ist Sache des Aufrufers).

Anker (Zeile 369-375): `def run_capital_backfill(` — Signatur um
`symbol_lookup: Callable[[str], str | None]` erweitern und an die Source durchreichen.

Anker (Zeile 182-186) — die Warnung, die auf Path C verweist:
```python
            logger.warning(
                f"CapitalSource: epic {epic!r} not in EPIC_MAP — "
                f"caller should fall back to path C (Dukascopy)"
            )
```
⇒ neu formulieren: „keine `capital`-Zeile in `instrument_source_availability` für {epic} —
Discovery hat diese Quelle für dieses Epic nicht bestätigt". **Kein Dukascopy-Verweis
mehr** (D15).

`scripts/capital_backfill.py` baut den Lookup aus `SourceAvailabilityStore.symbol_for`
gegen `--universe-db` (nach 0.3 existiert das Argument).

**Tests:** die bestehenden 11 in `test_backfill.py` sind auf `EPIC_MAP` gepinnt —
insbesondere `test_backfill.py:355-359` (der Lock-in-Test „SP35/AEX/MIB sind **nicht** in
`EPIC_MAP`"). Sie werden auf den Lookup umgeschrieben, **nicht** gelöscht: derselbe Beweis,
neue Quelle der Wahrheit (ein Lookup-Fake ohne SP35-Eintrag ⇒ `fetch_window` gibt `[]`
zurück, kein HTTP).

**Akzeptanz B2:** `grep -rn "EPIC_MAP" phase13_live_data/ --include=*.py` ist **leer**.
Das ist das Done-Kriterium der Phase aus `ROADMAP.md:608`.

#### B3 — `source_delta.py` trennt „nicht abrufbar" von „divergiert"

**Datei:** `phase13_live_data/scripts/source_delta.py`.

Anker (Zeile 157-161):
```python
            yf_bars = _fetch_bars(bars_conn, t["epic"], window_start, window_end, "yf")
            ls_bars = _fetch_bars(bars_conn, t["epic"], window_start, window_end, "ls")
            yf_reason, yf_pnl = _resolve_per_source(t, yf_bars)
            ls_reason, ls_pnl = _resolve_per_source(t, ls_bars)
            if yf_reason is None or ls_reason is None:
```

Heute sind die zwei Quellen hartkodiert und ein `None` heißt undifferenziert „nicht
vergleichbar". Neu: die Quellenliste kommt aus
`SourceAvailabilityStore.for_epic(epic, resolution='1m')` (Zeilen mit `status='ok'`), und
der Report unterscheidet drei Fälle:

| Fall | Bedeutung |
|---|---|
| `not_available` | keine Zeile mit `status='ok'` für diese Quelle ⇒ **war prinzipiell nicht abrufbar** |
| `available_but_empty` | Zeile vorhanden, aber keine Bars im Fenster ⇒ Beschaffungslücke |
| `compared` | verglichen; `agree` oder `diverge` |

Das ist die Outcome-Zeile des Concepts („`source_delta.py` P6 zeigt ‚war prinzipiell nicht
abrufbar' getrennt von ‚war abrufbar und hat divergiert'").

**Tests** (`phase13_live_data/tests/test_source_delta.py`, +4): je ein Test pro Fall plus
einer, der beweist, dass eine fehlende Verfügbarkeits-Tabelle den Report nicht killt
(fail-soft ⇒ alle Quellen gelten als „unbekannt", Exit 0).

---

### Block C — Autonomie und Scharfschalten

#### C1 — Scharf-Flag

**Datei:** `phase14_discovery/source_registry/arm.py` (NEU, Contract §5.4).
**Muster verbatim übernehmen** aus `phase8_scheduler/scheduler/killswitch.py`
(atomar `.tmp` + `os.replace`, fail-soft, wirft nie) — mit **einem bewusst umgedrehten
Detail**: die sichere Richtung ist `False` (D10), nicht `True`. Das gehört in den Docstring,
sonst kopiert es später jemand falsch zurück.

**Tests** (`phase14_discovery/tests/test_arm.py`, NEU, ≥ 6): fehlende Datei ⇒ `False`;
leere Datei ⇒ `False`; kaputtes JSON ⇒ `False`; `{"armed": false}` ⇒ `False`;
`arm()`/`is_armed()` Round-Trip; `disarm()` auf nicht existierende Datei ist No-Op.

#### C2 — Der Daemon

**Datei:** `phase14_discovery/source_registry/run.py` (NEU).
**Muster:** `phase12_data_foundation/data_foundation/run.py` (PID-File `_already_running`
`run.py:39-46`, `_write_pid` `:49-53`, Signal-Handler `:141-146`, `finally: pid_path.unlink()`
`:150-154`).

Schleife, je Durchlauf:
1. `is_armed(arm_path)` ⇒ **nein: schlafen, nichts tun, nichts loggen außer einem
   Debug-Tick.** Kein Netz, kein DB-Write.
2. `stale_rows(ttl_days=profile_ttl_days)` — nichts stale ⇒ schlafen (D14).
3. Epic-Liste aus `UniverseStore.list_by_status('active', 'discovered')`.
4. Je registrierte `Source`: `discover(epics, max_probe_calls=…)`, fail-soft
   (`SourceProfile.errors` sammeln, nie werfen), `upsert_many`.
5. `probe_calls_used > 0` ⇒ `SourceBudget.record_spend(points, kind='discovery')` (D13).
6. State-Datei `data/state/discovery_state.json` mit `{ts, rows_written, errors}` —
   Muster `recorder_state.json` (Format s. `data_health.py:36-44`, das es liest).

CLI: `--pid-file`, `--state-path`, `--universe-db`, `--bars-db`, `--arm-file`,
`--interval-s` (Default **3600**), `--once` (ein Durchlauf, dann Exit — der Operator-Modus).

**Tests** (`phase14_discovery/tests/test_run.py`, NEU, ≥ 6): unscharf ⇒ null
`discover`-Aufrufe (Fake-Source, die bei Aufruf wirft); scharf + alles frisch ⇒ null
`discover`-Aufrufe; scharf + stale ⇒ genau ein `discover` je Quelle; eine werfende Quelle
kippt den Durchlauf nicht; `probe_calls_used=0` ⇒ **kein** `record_spend`;
`--once` beendet sich.

#### C3 — Web-UI: Warnung + Button

**Datei:** `phase8_scheduler/webui/api.py` (Cross-Phase, freigegeben).

Anker (Zeile 361): `    # --- control endpoints (file writes ONLY) ------------------------------`
Anker (Zeile 386-388) — Ende von `post_command`:
```python
        command.write_command(cfg.command_path, cmd)
        return {"ok": True, "cmd": cmd}
```
⇒ die drei Endpoints aus §5.5 **danach**, **vor** `    # --- static dashboard ---`
(Zeile 390). Import von `source_registry.arm` **lazy im Endpoint-Body** — Repo-Konvention
(`api.py:18-20`: „Cross-phase reads … are lazy inside the endpoint, so `import webui.api`
pulls only fastapi + scheduler.* + stdlib").

`cfg` hat heute kein Feld dafür: den Pfad in `default_config()` (`api.py:56-70`, Anker
Zeile 66: `        kill_path=str(_DATA_DIR / "state" / "KILL"),`) **nicht** anfügen — dafür
müsste `SchedulerConfig` erweitert werden (Phase 8). Stattdessen ein Modul-Konstante
`_ARM_PATH = _DATA_DIR / "state" / "DISCOVERY_ARMED"` neben `_STATIC_DIR` (`api.py:50`).
Kleinerer Diff, keine Config-Migration.

**Datei:** `phase8_scheduler/webui/static/index.html`.
Anker (Zeile 61-64):
```html
      <div id="kill-banner" class="kill-banner" hidden>
        <span class="kill-banner-label">KILLED</span>
        <span id="kill-reason" class="kill-banner-reason"></span>
      </div>
```
⇒ ein zweites Banner `id="discovery-banner"` mit demselben CSS-Muster (aber Amber statt
Rot — `var(--amber)` wird in `app.js:450` schon benutzt), Text: „SOURCE DISCOVERY NOT ARMED
— sources are not being re-verified".

Anker (Zeile 74-77):
```html
      <div class="btn-row">
        <button id="btn-kill" class="btn btn--kill" type="button">KILL</button>
        <button id="btn-clear" class="btn btn--clear" type="button">CLEAR KILL</button>
      </div>
```
⇒ eine dritte `btn-row` mit `btn-discovery-arm` / `btn-discovery-disarm`.

**Datei:** `phase8_scheduler/webui/static/app.js`.
Anker (Zeile 156-162) — die Banner-Logik von `kill-banner`; das Discovery-Banner analog
aus dem neuen `/api/discovery`-Poll.
Anker (Zeile 454-460) — `control(action)`; zwei Zweige ergänzen.
Anker (Zeile 468-471) — die vier `addEventListener`; zwei ergänzen.

**Tests** (`phase8_scheduler/tests/test_webui.py`, +4): `GET /api/discovery` unscharf ⇒
`armed: false`; `POST /arm` ⇒ Datei existiert, Folge-`GET` meldet `armed: true`;
`POST /disarm` ⇒ Datei weg; **`GET /api/discovery` funktioniert auch ohne Tabelle 007**
(fail-soft, `rows_total: null`).

#### C4 — Start-Naht

**Datei:** `phase8_scheduler/scripts/run_scheduler.sh`, Anker (Zeile 38-39):
```bash
nohup bash "$REPO_ROOT/phase12_data_foundation/scripts/run_recorder.sh" \
    >>"$REPO_ROOT/data/state/recorder.log" 2>&1 &
```
⇒ analoger Block für `phase14_discovery/scripts/run_discovery.sh` (NEU, Muster
`phase12_data_foundation/scripts/run_recorder.sh`). Der Daemon startet **immer** mit, tut
aber **nichts**, solange das Flag fehlt (D10) — genau deshalb ist der Autostart
unbedenklich und die UI der einzige Schalter.

**Akzeptanz Block C:** Daemon startet unscharf, macht null Netz-Calls, null DB-Writes;
UI zeigt die Warnung; ein Klick auf ARM erzeugt `data/state/DISCOVERY_ARMED`; der nächste
Daemon-Tick schreibt Zeilen.

---

### Block D — Closeout

- **D1** Modul-Tabelle in `phase14_discovery/CLAUDE.md` gegen den As-Built-Stand füllen
  (Testzahlen aus dem finalen Sweep, nicht geschätzt).
- **D2** Finaler Regression-Sweep, je Phase separat, Tabelle in den Session-Block; Delta
  gegen die 1608 aus §2.1 explizit ausweisen.
- **D3** `## Session stopped`-Block schreiben; Rotationsregel beachten (Session 1 ist der
  Block, den **dieser Plan-Commit** anlegt — er wandert beim zweiten Block ins
  `SESSIONS_ARCHIVE.md`).
- **D4** Root-`CLAUDE.md` + `ROADMAP.md` + `docs/INDEX.md`: Phase-14-Zeile auf den
  erreichten Stand; jede neue `.md` im selben Commit indiziert.
- **D5** Ein Closeout-Handover **nur**, wenn die Phase geschlossen wird — nicht als Ritual.

---

## §7 Akzeptanz (PASS-Kriterien A1–A8)

| # | Kriterium | Wie belegt |
|---|---|---|
| **A1** | Discovery gibt **strukturell** null IG-Punkte aus | `test_sources.py` Test 2: Broker-Fake, dessen jede Methode `AssertionError` wirft, `discover()` läuft durch, `probe_calls_used == 0` |
| **A2** | `grep -rn "EPIC_MAP" phase13_live_data/ --include=*.py` ist **leer** | Shell, nach B2. **Der `--include=*.py`-Filter ist Absicht**, nicht Schummelei: `phase13_live_data/CLAUDE.md:201`, `SESSIONS_ARCHIVE.md` und der 📕-Closeout nennen `EPIC_MAP` in ihrer Chronik und dürfen **nicht** editiert werden (📕 never edit / 📦 verbatim history). `ROADMAP.md:608` nennt das Kriterium ohne Filter — dort im selben Schritt nachziehen, sonst „scheitert" später eine bestandene Phase an einem Doku-Treffer. |
| **A3** | `measurable_universe()` liefert vor und nach Phase 14 dasselbe | `test_store.py` Test A4.5 + Read-only-Probe gegen die Produktions-DB (dieselben 5 Epics wie §2.2) |
| **A4** | Die yF-Projektion reproduziert das heutige Registry-Substrat exakt | **Migration 007 (A2, Test 11)**: 5× `(yf, ok)` + 3× `(yf, no_intraday_source)`, namentlich in §2.2. `set_symbol` (A4) beweist zusätzlich nur die Fortschreibung — nicht den Grundbestand (Begründung in §5.1/§6 A4) |
| **A5** | Der Daemon tut unscharf **nichts** | `test_run.py`: Fake-Source, die bei Aufruf wirft; unscharfer Durchlauf wirft nicht |
| **A6** | Die UI warnt, bis scharfgestellt, und schaltet per Datei | `test_webui.py` +4; Sichtprüfung durch den Nikinger |
| **A7** | `source_delta.py` unterscheidet „nicht abrufbar" von „divergiert" | `test_source_delta.py` +4 |
| **A8** | Kein roter Test, keine uncommitteten Änderungen | finaler Sweep, Delta gegen 1608 ausgewiesen |

**Nicht Teil der Akzeptanz** (bewusst): dass Capital.com für SP35 eine Quelle findet (D15),
dass `ls` Bars liefert (Phase-13-Beweiswoche), dass die Discovery *nützliche* neue Quellen
entdeckt (das entscheidet die Beweiswoche, nicht dieser Plan).

---

## §8 Fehlgriffe, die wie andere Fehler aussehen

> Jeweils: **Symptom** → **erster Verdächtiger**. Das ist billiger als die Debug-Session danach.

### §8.1 „`--auto` findet keine Epics / Discovery schreibt nichts"

**Erster Verdächtiger ist NICHT die neue Tabelle**, sondern B3 (§3.3): `args.db` zeigt per
Default auf `bars.sqlite`, wo `instrument_universe` nicht existiert. Wenn Block 0.3
übersprungen wurde, sieht ein Phase-14-Konsumenten-Umbau exakt so aus, als hätte er die
Discovery zerbrochen. **Erst 0.3 prüfen, dann suchen.**

### §8.2 „Ein Epic fällt nach Phase 14 still aus der Messung"

**Erster Verdächtiger ist die Projektion (A4), nicht die Resolver-Logik.** Wenn
`_project_availability` wirft und der `except`-Block fehlt oder zu eng ist, reißt sie den
Registry-Write mit — `data_source_status` bleibt auf dem alten Wert stehen und
`measurable_universe()` verliert das Epic lautlos. **Deshalb D5: Registry zuerst,
Projektion danach, Fehler laut und nicht-fatal.** Gegenprobe: `set_symbol` gegen eine DB
**ohne** Tabelle 007 (Test A4.4) muss durchlaufen.

### §8.3 „Nach dem Sampler-Anschalten startet der Daemon nicht mehr"

**Erster Verdächtiger ist B1 (§3.1), nicht Phase-14-Code.** `active_universe()` wirft
`ValueError: invalid data_source_status: 'stale_source'` beim **Lesen**, der Stacktrace
zeigt auf `wiring.py:131` (`_build_research`) — sieht aus wie ein Wiring-Bug, ist ein
Vokabular-Loch in `phase9_universe/universe/models.py:61-63`. Wenn A1 gelaufen ist, ist der
Verdacht erledigt; wenn nicht, ist er die Antwort.

### §8.4 „Capital.com liefert plötzlich für gar nichts mehr"

**Erster Verdächtiger ist der Symbol-Lookup, nicht die API.** Nach B2 kommt das Kürzel aus
der Tabelle. Ist die Tabelle leer (Daemon nie scharf geschaltet, oder Migration 007 auf der
Produktions-DB nicht gelaufen), gibt `symbol_for` **korrekt** `None` zurück und
`fetch_window` liefert `[]` — ohne Fehler, ohne HTTP. Das sieht aus wie ein API-Ausfall.
Gegenprobe in einer Zeile:
```bash
sqlite3 "file:data/trading_bot.sqlite?mode=ro" \
  "SELECT epic, source_symbol, status FROM instrument_source_availability WHERE source='capital'"
```

### §8.5 „Der Discovery-Daemon verbrennt Kontingent"

**Erster Verdächtiger ist eine neue Quelle, die im Konsumentenpfad fetcht** — nicht der
Daemon selbst. D6 sichert nur die **heute registrierten** Quellen strukturell ab. Wer
später eine Quelle registriert, deren `discover()` `/prices` ruft, hat P12.5 wiederholt.
**Deshalb ist Test 2 aus A3 ein Muster, das jede neue Quelle mitbringen muss**, und
`spend_kind='discovery'` (D13) macht den Verbrauch im Ledger sofort sichtbar:
```bash
sqlite3 "file:data/bars.sqlite?mode=ro" \
  "SELECT kind, SUM(points) FROM source_spend GROUP BY kind"
```

### §8.6 „Die Tests sind grün, aber live passiert nichts"

Der wiederkehrende Fehlermodus dieses Repos (`feedback_verify_flags_are_on`: viermal
derselbe — `enable_ig_bars`, `SymbolResolver`, `enable_shadow_schedule`). Phase 14 hat
**zwei** solche Schalter: die Flag-Datei (D10) und Migration 007 auf der Produktions-DB.
**Grüne Tests beweisen keinen von beiden.** Gegenprobe vor jedem „läuft live":
```bash
ls -l data/state/DISCOVERY_ARMED
sqlite3 "file:data/trading_bot.sqlite?mode=ro" "SELECT MAX(version) FROM _schema_version"   # muss 7 sein
sqlite3 "file:data/trading_bot.sqlite?mode=ro" "SELECT COUNT(*) FROM instrument_source_availability"
```

---

## §9 Drift-Liste — **bei Ausführung verifizieren**

> **Diese Liste ist vollständig.** Was hier nicht steht, hat diese Planungssession am
> 2026-08-22 selbst gegen das Repo, die Live-DB oder einen Testlauf geprüft und ist als
> Fakt formuliert. Rate nichts nach; prüfe diese und nur diese.

1. **Zeilennummern verschieben sich.** Jeder Anker oben trägt den **Verbatim-String** —
   der ist der Anker, die Zahl ist die Abkürzung. Schritte verschieben einander die Zeilen
   (0.2 verschiebt `phase13_live_data/CLAUDE.md`, 0.3 verschiebt `capital_backfill.py`,
   A1 verschiebt `phase9_universe/universe/models.py`). **Immer per String suchen.**
2. **Der Handover nennt `EPIC_MAP` in `backfill.py:67-72`** (`PHASE13_CLOSEOUT_HANDOVER.md`
   §1.5, `phase13_c_block_c_replan.md` §1.1). **Das ist stale** — heute gemessen: **85-88**.
   Verlass dich auf den Verbatim-String, nicht auf die Handover-Zahl.
3. **Capital.com `GET /markets?searchTerm=` — Antwort-Form unbekannt.** Nie inspiziert.
   `_extract_ohlc` (`backfill.py:339-366`) rät aus genau diesem Grund vier Feldnamen-
   Varianten. B1a (Operator-Probe) muss **vor** B1b laufen; ohne den Output wird nicht
   gebaut, sondern auf `origin='operator'` ausgewichen.
4. **Capital.com Demo-URL** `https://demo-api-capital.backend-capital.com`
   (`backfill.py:117`) — heute nicht gegen ein Swagger-File verifiziert. Vor jedem
   Live-Lauf prüfen.
5. **`data_health.py` und die neue Tabelle:** ob der Tages-Report eine Konsistenz-Zeile
   („Projektion ≠ Registry") bekommen soll, ist **nicht** entschieden. Ich habe
   `data_health.py:1-50` gelesen, aber den Rumpf (`main`, ab Zeile 49) nicht.
   Vorschlag für die ausführende Session: **erst nicht**, und nach dem ersten scharfen Lauf
   neu bewerten. Wenn doch: es ist ein Read-only-Zusatz, kein Schema-Touch.
6. **`DivergenceSampler.sample_epic`** (`heartbeat.py`) — ich habe `assess_day`
   (`heartbeat.py:60-140`) gelesen, `sample_epic` **nicht**. Phase 14 fasst den Sampler
   nicht an; falls B3 (`source_delta.py`) an ihm entlanglaufen soll, erst lesen.
7. **`SchedulerConfig`** — ich habe nur `config.py:201-207` gelesen (der
   `enable_divergence_sampler`-Block). Ob es dort schon ein Feld gibt, das C3 wiederverwenden
   könnte, ist ungeprüft. Der Plan umgeht die Frage per Modul-Konstante (C3), aber falls
   ein passendes Feld existiert, ist es der bessere Weg.
8. **`run_recorder.sh`** — als Muster für `run_discovery.sh` genannt, aber **nicht gelesen**.
   Vor C4 öffnen.
9. **`webui/static/style.css`** — die Klassennamen `kill-banner` / `btn--kill` sind aus
   `index.html` belegt, die zugehörigen CSS-Regeln habe ich **nicht** gelesen. Ob eine
   Amber-Variante existiert oder neu geschrieben werden muss: bei C3 nachsehen.
10. **`probe_capital.py`** — nur der Dateiname ist belegt, der Inhalt **nicht gelesen**.
    B1a erweitert ihn; erst lesen.
11. **`tests/test_backfill.py:355-359`** — ich kenne die drei Assertions aus dem Grep, nicht
    den umgebenden Test. Vor B2 vollständig lesen (er wird umgeschrieben, nicht gelöscht).
12. **Ob `logging` in `phase9_universe/universe/store.py` schon importiert ist** — heute
    steht dort kein `logger`; ob `import logging` fehlt, habe ich nicht separat geprüft
    (im gelesenen Kopf `store.py:15-24` ist es **nicht** dabei). A4 ergänzt beides.
13. **Produktions-DB-Migration:** dass `run_migrations` gegen `data/trading_bot.sqlite`
    007 sauber anwendet, ist **nicht** getestet — nur der Runner-Code ist gelesen. Das ist
    ein **Operator-Schritt** (Nikinger), kein Test: `python phase2_persistence/scripts/init_db.py`
    (Existenz dieses Scripts ist aus `run_scheduler.sh:24` belegt, der Inhalt nicht gelesen).
    **Vorher Backup** von `data/trading_bot.sqlite` — additive Migration, aber die DB trägt
    reale Trade-Historie.

---

## §10 Out of Scope (Phase 14 macht das **nicht**)

- **`measurable_universe()` / `data_source_status` umbauen** — D3, gelockt.
- **`prefer` in `BarArchive.window`** — D7, gelockt (beantwortet Concept-Q3 mit Nein).
- **Dukascopy** — D15. Re-Evaluation nach der Beweiswoche.
- **`KNOWN_SOURCES` dynamisch aus der DB** — D17, ausdrücklich verboten.
- **Quell-Authentifizierung, Rate-Limits, Backoff zentralisieren** — Concept §4, bleibt je
  Quelle. Phase 14 macht **Sichtbarkeit**, keine zentrale Quell-Verwaltung.
- **`TickerMapper`-Cache aufräumen** (`phase3_external_data/external_data/ticker_map.py:37`)
  — Concept §4, out-of-scope; die Tabelle läuft parallel.
- **Momentum-VETO, Gates, Sizing, P6-Debatte, P7-Brain** — Phase-13-L13, gilt weiter.
- **`resolve_paper_trade`** — unangetastet, der Guard sitzt davor (Phase-13-L3/A3).
- **Beweiswoche P1–P9** — separater Track, läuft parallel (E7).
- **WI-2/W2 + H-Serie, Research-Funnel-Fix, B3-Margin-Headroom, Council-Paper-Call, Live-Konto**
  — Phase 15.
- **Ein Revert der fünf P12.5-Fixes** — Phase-13-L14, gilt weiter.

---

## §11 Korrekturnotiz (Mini-Session Do 2026-08-27 — vier Post-Execution-Drifts)

> **Konvention:** diese Notiz steht hier, **nach** §10, weil sie keine
> Plan-Korrektur ist (keine der ursprünglichen D1–D20 ändert sich), sondern
> vier **post-execution** Drifts, die die Plan-Session am 2026-08-22 nicht
> vorhersehen konnte und die der Phase-14-Lauf dann operativ aufgedeckt hat.
> Sie ergänzt §9 (Drift-Liste), ersetzt keinen Eintrag dort — §9 zählte die
> *Plan*-Drift, diese Notiz zählt die *Ausführungs*-Drift. Cross-Phase-Referenz:
> P14-C-Mini-Plan [`../phase14_discovery/PHASE14_C_DAEMON_CWD_BUG_PLAN.md`](../phase14_discovery/PHASE14_C_DAEMON_CWD_BUG_PLAN.md) §3.1,
> P14-D-Mini-Plan [`../phase14_discovery/PHASE14_D_DAEMON_SIGNAL_CAP_PLAN.md`](../phase14_discovery/PHASE14_D_DAEMON_SIGNAL_CAP_PLAN.md) §3.2,
> Phase-14-Session-12-Block ([`../phase14_discovery/SESSIONS_ARCHIVE.md`](../phase14_discovery/SESSIONS_ARCHIVE.md) Z. 93–102).

### §11.1 B5 (Code-Bug) — `insert_bars`-Rückgabewert wird verworfen

> **Korrekturnotiz (2026-08-27, Mini-Session 15+16):** dieser Eintrag war
> in der Erstfassung von Session 15 als „latent" beschrieben — **das stimmt
> nicht mehr**. Der Fix wurde bereits am 2026-08-22 im Commit
> **`4681d68`** (`phase14: fix -- Phase-13 script bugs B3/B4/B5 (Block 0.3)`)
> zusammen mit B3 und B4 live gebracht, **bevor** Phase 14 die §11-Notiz
> überhaupt schrieb (Plan-Datum 2026-08-22, Notiz-Datum 2026-08-27).
> Heute nachgemessen: `backfill.py:649` hat `written += archive.insert_bars(...)`,
> inkl. Inline-Kommentar mit explizitem Hinweis auf B5.
> Regressionstest `test_run_capital_backfill_counts_only_genuinely_new_rows`
> (`test_capital_backfill_script.py:169-200`) pinnt das Verhalten.
> **Status:** ✅ gefixt + getestet, **kein** offener Hygiene-Punkt.

`phase13_live_data/live_data/backfill.py:644-649` (heute):

```python
            try:
                # insert_bars returns the number of *genuinely new* rows
                # (cur.rowcount over INSERT OR IGNORE). Duplicates don't
                # count; that's what the script-level "bars_written" metric
                # is supposed to mean (Phase-14 finding B5).
                written += archive.insert_bars([archive_bar])
```

`BarArchive.insert_bars` (`archive.py:119-133`, `INSERT OR IGNORE` +
`cur.rowcount`) **gibt die Zahl der wirklich neu geschriebenen Zeilen zurück**.
Wird seit Commit `4681d68` korrekt summiert; ein Duplikat zählt **nicht**
als Schreibvorgang.

> **Hinweis aus dem Plan** (Mutterplan §3.5 B5, am 2026-08-22 selbst
> geschrieben, *vor* dem Fix-Commit): das war ein **echter Bug**, **kein**
> Phase-14-Code-Edits nötig gewesen wären — der Fix kam als **Block 0.3
> Cross-Phase-Edit** im Phase-14-Setup-Sweep. Der Zähler ist ein
> Diagnose-Instrument, **kein** Gate oder VETO (kein Code-Pfad schaltet
> auf den Zähler). Beweiswoche läuft seit 2026-08-25; Re-Lauf über
> dasselbe Fenster zeigt korrekt 0 neue Rows für die bereits
> geschriebenen Bars.

### §11.2 P14-C-Befund (Impl-Drift zu D11) — Modul-Konstanten-Konvention `parents[2]` fehlte an einer Stelle

`source_registry/arm.py:55` baute den ARM-Pfad mit einem **relativen**
String (`"data/state/DISCOVERY_ARMED"`) statt mit
`Path(__file__).resolve().parents[2] / "data" / "state" / "DISCOVERY_ARMED"`
wie die anderen fünf Konsumenten (`run.py:62`, `api.py:49-50`,
`webui/static/…`). Konsequenz: `run_discovery.sh` setzt CWD nach
`phase14_discovery/`, der Daemon-Pfad wurde `phase14_discovery/data/state/...`
statt `data/state/...`, der Daemon sah `armed: false`, die UI sah
`armed: true` — Phase 14 war operativ **falsch stumm** (20 h seit
Scharfschaltung 2026-08-25 14:12).

> **Drift-Befund:** kein fehlender Code, sondern eine **fehlende Konvention**.
> Der Plan hat den Pattern (`parents[2]`) an zwei Stellen explizit
> dokumentiert (D11-Cross-Phase-Note + WebUI-Block), aber **nicht als
> allgemeine Konvention** im §4 (gelockte Entscheidungen) festgeschrieben.
> Folge: ein sechstes Modul (`arm.py`) hat eine eigene Variante
> eingeführt, ohne dass der Plan widersprochen hätte — das ist kein
> Plan-Konflikt, sondern eine **Impl-Drift zu D11** („UI schaltet per
> Datei"). Der Plan bleibt unverändert; die Lehre für Phase 15:
> **Modul-Konstanten mit Repo-Root-Anteil brauchen eine explizite
> Konvention**, nicht nur Beispiele.

> **Fix bereits auf `origin/main`** (Session 11, Fix-Commit `4e44b73` —
> *nicht* `2769763`, das war der Mini-Plan-Doc-Commit;
> P14-C-Mini-Plan D1-D4 gelockt): `arm.py` verwendet jetzt
> `parents[2]`, Regressionstest pinnt CWD-Unabhängigkeit, Daemon-Restart
> hat die Lücke operativ geschlossen.

> **Korrekturnotiz (2026-08-27, Mini-Session 15+16):** Erstfassung von
> Session 15 nannte den Doc-Commit `2769763` als Fix-Anker — das ist
> der **Mini-Plan**, nicht der **Code-Fix**. Der Fix lebt in `4e44b73`
> (`phase14: code+tests -- P14-C fix: DEFAULT_ARM_PATH absolut (CWD-Falle)`).
> Inhaltlich richtig (Fix ist live), Anker falsch.

### §11.3 P14-D-Befund (Impl-Drift zum Phase-8-POST_WINDOW-Hotfix) — Sleep-Cap-Konvention für Daemon-Loops fehlte

`source_registry/run.py` (`run_forever`, vor Fix) rief
`time.sleep(self._interval_s)` mit `interval_s=3600` auf. Python PEP 475
retryt interrupted syscalls; der Signal-Handler setzte zwar
`self._stop = True`, aber der Top-of-Iteration-Check kam erst nach
Ablauf. Folge: `kill <pid>` war bis zu 1 h wirkungslos (reproduziert in
Session 11: SIGTERM no-op, SIGKILL nötig).

> **Drift-Befund:** strukturell identisch zum Phase-8-POST_WINDOW-Bug,
> dort 2026-07-11 mit `min(seconds_until(...), idle_poll_s)` gefixt.
> Der Phase-14-Plan hat das Pattern an einer Stelle (`run_forever`)
> **nicht** als verbindlich übernommen — die Phase-13-L13-Note
> („Momentum-VETO bleibt unangetastet") traf nicht dasselbe.
> **Impl-Drift zum Phase-8-Hotfix**, nicht zum Phase-14-Plan.

> **Fix bereits auf `origin/main`** (Session 13+14, Commit `27f04d9`,
> P14-D-Mini-Plan D1-D3 gelockt): `_sleep_capped(total_s)` chunked den
> Sleep in Brocken `≤ signal_check_interval_s` (Default 60 s) und
> prüft `self._stop` **zwischen** Brocken. Discovery-Daemon
> reagiert jetzt auf SIGTERM innerhalb von max. 60 s.
>
> **Offene Variante desselben Bugs:** der Recorder-Daemon
> (`phase12_data_foundation/data_foundation/run.py:146`, `interval_s=300`,
> 12× weniger schmerzhaft) hat denselben theoretischen Bug, **nicht
> behoben**. Phase-15-Territorium — beim Phase-15-Plan wird eine
> Helper-Klasse in einem gemeinsamen Modul empfohlen, die beide
> Daemons einmal mit dem Cap ausstattet.

### §11.4 Doc-Rotation-Drift (Prozess-Befund) — Inline-Duplikat eines Session-Blocks im Phasenkopf

Beim Schreiben von Session 13 (Commit `22cc688`, 2026-08-26) wurde
Session 12 **nicht** aus dem Phasenkopf entfernt, sondern nur Session 13
oben angehängt. Resultat: der Phasenkopf trug **zwei** Session-Blöcke
(Session 13 oben, Session 12 darunter inline) — Verstoß gegen die
Doc-Layers-Konvention (genau **ein** Block im Phasenkopf, der Rest
im `SESSIONS_ARCHIVE.md`).

> **Drift-Befund:** die Rotation-Regel ist in `CLAUDE.md` (Root) +
> `docs/DOC_LAYERS_CONVENTION.md` festgeschrieben, aber **nicht in
> einer maschinen-prüfbaren Form** (z. B. ein Pre-Commit-Hook, der
> sicherstellt, dass `grep -c '^## Session stopped' phase14_discovery/CLAUDE.md == 1`).
> Folge: der Drift bleibt unsichtbar, bis eine Review-Session ihn findet.
>
> Session 13 hat den Drift entdeckt + mit derselben Rotation aufgeräumt
> (Session 11 inline-duplicate entfernt, Session 12 ins Archiv). Seit
> Commit `22cc688` ist der Phasenkopf wieder single-block. Lehre für
> die nächste Plan-Session: einen **Hygiene-Pre-Commit-Hook**
> diskutieren — oder zumindest eine **Editor-Checklist** am Ende
> jedes Session-Commits („genau ein `## Session stopped`-Block im
> Phasenkopf, vorheriger Block im Archiv").

### §11.5 Was diese Notiz **nicht** macht

- Sie ändert **keine** D1–D20. Alle 20 gelockten Entscheidungen halten.
- Sie ersetzt **keinen** §9-Eintrag. §9 zählt Plan-Drift (vor Ausführung);
  §11 zählt Ausführungs-Drift (nach Ausführung).
- Sie ist **keine** Schritt-Sequenz. Die Phase bleibt
  **closed-in-all-but-D5** (Phase 14-CLAUDE.md Session 14).
- Sie ist **kein** Live-Change. Reine Dokumentation, keine
  Code-Konsequenz für heute — alle drei Code-relevanten Drifts
  (§11.1, §11.2, §11.3) sind entweder **out-of-scope** (§11.1) oder
  **bereits gefixt + live-verifiziert** (§11.2, §11.3) oder
  **explizit Phase-15-Territorium** (§11.3 Recorder-Daemon).

