---
status: snapshot
purpose: Mini-Plan P15-F — Doc-Rotation-Hook Step 2 für Phase 15 nachschärfen. Der bestehende Hook (`scripts/check_doc_rotation.py`, P14-F 2026-08-31) prüft die 14 abgeschlossenen Phasen 1–10/12/13/14 + meta_m1_harness. Phase 15 (`phase15_v4/`) ist **nicht** in `PHASE_DIRS`, und die Heading-Form „MiniMax-M3-Exec-Session #N" wird von der bestehenden Regex `(?:Mini-)?Session\s+(\d+)` **nicht** gematcht. Step-2-Logik (`check_archive_sequence`) läuft deshalb für Phase 15 ins Leere. Rein Hygiene, kein Live-Touch, kein Cross-Phase-Code-Edit (nur `scripts/check_doc_rotation.py` + 1 neue Test-Funktionen + INDEX-Zeile). Cross-Phase-Freigabe (Nikinger 2026-08-31): nur das Tool-Skript (Phase-14-eigener Hygiene-Code) — keine `dev_install.sh`-Anbindung (ist schon in P14-F).
read-when: jede Session, die einen Session-Block in `phase15_v4/CLAUDE.md` schreibt; jede Plan-Session, die Phase-15-Doc-Layers erweitert
detail: L3
up: ../CLAUDE.md
down:
  - ./CLAUDE.md                                                    # Phasenkopf, dem dieser Plan folgt
  - ./SESSIONS_ARCHIVE.md                                          # die Archive-Datei, deren Integrität jetzt zusätzlich geprüft wird
  - ../scripts/check_doc_rotation.py                            # das Tool, das erweitert wird (P14-F-Stand)
  - ../tests/test_check_doc_rotation.py                         # die Test-Datei, die erweitert wird (P14-F-Stand)
  - ../docs/INDEX.md                                            # L0-Index, der die Plan-Zeile aufnimmt
  - ../docs/DOC_LAYERS_CONVENTION.md                            # das Doc-Layers-Protokoll, gegen das geprüft wird
  - ../phase14_discovery/PHASE14_F_DOC_ROTATION_HOOK_STEP2_PLAN.md  # 📕 Schwester-Mini-Plan (P14-F, Vorlage)
  - ../phase14_discovery/PHASE14_E_RECORDER_LOOP_PLAN.md          # 📕 Schwester-Mini-Plan (P14-E, Cross-Phase-Beispiel)
  - ../phase14_discovery/PHASE14_D_DAEMON_SIGNAL_CAP_PLAN.md       # 📕 Schwester-Mini-Plan (P14-D)
  - ../phase14_discovery/PHASE14_C_DAEMON_CWD_BUG_PLAN.md          # 📕 Schwester-Mini-Plan (P14-C, Vorlage etabliert)
updated: 2026-08-31
---
# P15-F — Doc-Rotation-Hook für Phase 15 (Mini-Plan)

> **Einordnung:** Phase 15 (V4), nach Block A (A-1..A-6 ✅, 2026-08-31). „P15-F" ist ein
> Label für die Hook-Nachschärfung, **kein** neuer Phase-15-Block — die Lücke ist eine
> fehlende Tool-Abdeckung des bestehenden Hooks, kein fehlendes Feature. Gleiche Konvention
> wie P14-C/P14-D/P14-E/P14-F.
>
> **Adressat:** die ausführende Claude-Code-Session (MiniMax-M3). Alles unten ist gegen den
> Repo-Stand `933167a` (HEAD auf `origin/main` nach P15-A-6-Push) am **2026-08-31** selbst
> nachgemessen. Was nicht verifiziert werden konnte, steht in **§8**.

---

## §0 BLUF

Der bestehende Pre-Commit-Hook (`scripts/check_doc_rotation.py`, P14-F-Stand 2026-08-31)
deckt 14 Phasen ab und nutzt die Regex `(?:Mini-)?Session\s+(\d+)`. Phase 15 (`phase15_v4/`)
ist **nicht** in `PHASE_DIRS`, und die Session-Heading-Form in Phase 15
(`MiniMax-M3-Exec-Session #N`) wird vom Regex nicht gematcht. Konsequenz:

| # | Ohne P15-F passiert | Schaden |
|---|---|---|
| **P1** | Der Hook prüft Phase 15 **gar nicht** (PHASE_DIRS endet bei `phase14_discovery`) | Inline-Duplicates in `phase15_v4/CLAUDE.md` (MiniMax-M3-Exec-Session-#1..#4) würden unentdeckt bleiben; Rotation-Regel-Verletzung rutscht ins Repo |
| **P2** | Selbst wenn Phase 15 in PHASE_DIRS stünde, fände `check_archive_sequence` für Phase 15 **keine Session-Nummer** (Regex matcht nicht) | `head_max = None` → Hook-Step-2 wird stillschweigend übersprungen, keine Sequenz-Validierung |
| **P3** | Phase 16+ (zukünftig) verwendet voraussichtlich dieselbe „Exec-Session #N"-Form, weil MiniMax-M3 das Standardvokabular etabliert hat | Wenn P15-F nicht jetzt macht, müsste Phase 16 dasselbe Problem erneut lösen — **jetzt** ist die richtige Zeit, das Vokabular zu fixieren |

**Was dieser Mini-Plan macht:**
1. Erweitert `scripts/check_doc_rotation.py`:
   - `PHASE_DIRS` um `"phase15_v4"` ergänzen
   - `_SESSION_NUM_RE` permissiver machen, sodass auch „Exec-Session #N" und
     „MiniMax-M3-Exec-Session #N" (MiniMax-3-spezifisches Vokabular) extrahiert werden
2. Schreibt 4 neue Tests in `tests/test_check_doc_rotation.py` (A3–A6; A1+A2 gibt's
   schon aus P14-F) für die neuen Heading-Formen
3. Bewiest durch Probe-Aufruf, dass `phase15_v4` mit `--strict` jetzt sauber
   Step-2-konform ist (`head=3`, `archive-newest=2`)
4. Updated `docs/INDEX.md` mit einer neuen Mini-Plan-Zeile

**Was dieser Mini-Plan ausdrücklich NICHT tut:**
- `dev_install.sh` anfassen — `install_hooks.sh` ist dort schon angeflanscht (P14-F §4 Schritt 3)
- Heading-Form in Phase-15 ändern — die aktuelle Form ist **konsistent und lesbar**, das
  Tool muss permissiv genug sein, nicht die Dokumente
- Auf `--strict` für Phase-15 **eigene** Heading-Form bestehen — der Hook soll alle aktuellen
  + zukünftigen MiniMax-M3-Vokabulare matchen

**Reihenfolge:** Befund verifiziert (heute Probe-Aufruf `python3 scripts/check_doc_rotation.py
--strict --phase phase15_v4`) → D1–D3 gelockt → 1 Code-Commit (PHASE_DIRS + Regex) +
1 Test-Commit (4 neue Tests) → 2 Commits, keine Live-Änderung.

---

## §1 Rahmen + Arbeitsteilung

| Regel | Stand |
|---|---|
| **Arbeitszeit** | Werktags, **ohne** Bot-Stop nötig. P15-F ist Hygiene-Code (`scripts/`), kein Live-Touch. Der bestehende Pre-Commit-Hook (P14-F) wird durch die Erweiterung **strenger** für Phase 15 — kein Lock für andere Commits. |
| **Bot vor den Edits** | Nicht erforderlich — keine Datei, die der Bot zur Laufzeit liest. |
| **Live / Netz / Kosten** | **Nichts.** Rein lokale Tests (`pytest tests/test_check_doc_rotation.py`). Kein Smoke-Test nötig. |
| **Live-DB** | Nicht berührt. |
| **Cross-Phase-Edits** | **Nur `scripts/check_doc_rotation.py`** + **`tests/test_check_doc_rotation.py`** + **`docs/INDEX.md`**. Phase 15 (`phase15_v4/CLAUDE.md`) selbst bleibt **unangetastet** — keine Heading-Änderung. Die existierende Heading-Form ist lesbar und konsistent. |
| **Push** | Nikinger-Freigabe (erteilt 2026-08-31: „Du darfst pushen"). |

**Prozess-Ist-Stand bei Planschluss (2026-08-31, selbst erhoben):**

| Datei | Pfad | Status |
|---|---|---|
| `scripts/check_doc_rotation.py` | existiert | tracked, 243 Zeilen (P14-F-Stand: PHASE_DIRS endet bei `phase14_discovery`, Regex `(?:Mini-)?Session\s+(\d+)`, `--strict` default per install_hooks.sh) |
| `tests/test_check_doc_rotation.py` | existiert | tracked, 7 Tests (A1–A6 + 1 edge-case) |
| `scripts/install_hooks.sh` | existiert | tracked, ruft `--strict --quiet` (P14-F §4 Schritt 3) |
| `scripts/dev_install.sh` | existiert | tracked, ruft `install_hooks.sh` als letzten Schritt (Z. 85) |
| `phase15_v4/CLAUDE.md` | existiert | tracked, 579 Zeilen, 1 Session-Block (MiniMax-M3-Exec-Session #3), Heading-Form „MiniMax-M3-Exec-Session #N" |
| `phase15_v4/SESSIONS_ARCHIVE.md` | existiert | tracked, 412 Zeilen, 3 Blöcke (MiniMax-M3 #2, #1, Plan-Session Opus 5), gleiche Heading-Form |

**Stand-Beobachtung:** `python3 scripts/check_doc_rotation.py --strict` heute → 14
Phasen-OK, Phase 15 **nicht** abgedeckt. `python3 scripts/check_doc_rotation.py
--strict --phase phase15_v4` → `[OK] phase15_v4: 1 session block` (Step-1 grün,
Step-2 silent-skipped weil `_max_session_num` für die MiniMax-M3-Exec-Session-Heading
`None` returnt).

---

## §2 Gelockte Entscheidungen (D1–D3)

| # | Entscheidung | Begründung |
|---|---|---|
| **D1** | `PHASE_DIRS` wird um `"phase15_v4"` ergänzt (eine Zeile, am Ende der Tuple, vor `meta_m1_harness` falls relevant). | Phase 15 ist seit 2026-08-31 in execution (Plan-Commit `f98df68`, MiniMax-M3-A-1..A-6); sie braucht die gleiche Hygiene-Prüfung wie die 14 abgeschlossenen Phasen. meta_m1_harness bleibt in der Liste (separates `SESSIONS_ARCHIVE.md`, gleiche Konvention). Phase 15 ist nach `phase14_discovery` einsortieren, weil sie die jüngste Phase ist (Lesereihenfolge = Chronologie). |
| **D2** | `_SESSION_NUM_RE` wird permissiver gemacht: `(?:Mini-\|MiniMax-\w+-Exec-\|Exec-)?Session\s+#?(\d+)`. Matcht: „Session N" (generisch, P14-F-Stand), „Mini-Session N" (P14-F-Stand), „Exec-Session #N" (Phase-15-Vokabular), „MiniMax-M3-Exec-Session #N" (Phase-15-spezifisch mit optionalem „MiniMax-X-Exec-"-Prefix). `MiniMax-` ist hier als „Modell-Vendor-Prefix" etabliert (MiniMax-M3 in Phase 15, potenziell MiniMax-4/5 in Folge-Sessions). | Konsistent mit dem aktuellen Vokabular im Repo. **Permissivität ist Absicht:** eine zukünftige Variante (z.B. „MiniMax-4-Exec-Session" statt „MiniMax-M3-Exec-Session") wird ohne neue Mini-Plan-Session gematcht — das ist explizit gewollt, eine neue Variante kündigt sich per Issue/PR an, nicht durch ein kryptisches Hook-Fail. **Defensive** Annahme: `\w+` matcht alphanumeric+underscore, also auch „MiniMax-Opus-Exec-", falls jemand so kreativ sein will. |
| **D3** | Heading-Form in Phase 15 wird **nicht** geändert. Begründung: die aktuelle Form „(MiniMax-M3-Exec-Session #N, ...)" ist explizit (Modell-Name, Session-Typ, Session-Nummer) und für Cold-Reader besser als „(Session N: ...)" (generisch). Der Hook muss permissiv sein (D2), nicht die Doku. | Wenn der Hook starr wäre, müssten alle Phasen-15-Headings auf eine generische Form normalisiert werden — das wäre invasiv (4 Heading-Edits in `phase15_v4/CLAUDE.md` + 4 Heading-Edits in `phase15_v4/SESSIONS_ARCHIVE.md` + 1 Plan-Session-Block), verliert Lese-Information (Modell-Name ist auditability-pflichtig), und bringt keinen Sicherheits-Gewinn. |

**Cross-Phase-Freigabe-Status:**
- **`scripts/check_doc_rotation.py`** — Phase-14-eigener Hygiene-Code seit Session 16, **kein** Cross-Phase-Touch (Datei wird nur erweitert).
- **`tests/test_check_doc_rotation.py`** — Phase-14-eigene Test-Datei seit P14-F, **kein** Cross-Phase-Touch (nur Erweiterung um neue Tests).
- **`docs/INDEX.md`** — L0-Index, jede neue Mini-Plan-Zeile geht hier hin (Konvention, AK14).
- **`phase15_v4/CLAUDE.md`** + **`phase15_v4/SESSIONS_ARCHIVE.md`** — **nicht** angefasst (D3, Heading-Form bleibt).

---

## §3 Der Befund mit verifizierten Ankern

> Alle Zeilennummern **selbst gegrept am 2026-08-31**, Stand `933167a` (HEAD auf `origin/main`
> nach P15-A-6-Push). Vor jedem Edit: einmal per Grep auf den zitierten **Verbatim-String**
> gegenprüfen — der ist der eigentliche Anker, die Zahl nur die Abkürzung.

### §3.1 Die zwei Lücken

```
scripts/check_doc_rotation.py:51-66   PHASE_DIRS: tuple[str, ...] = (
                                           "phase1_broker_wrapper",
                                           "phase2_persistence",
                                           ...,
                                           "phase14_discovery",
                                       )
                                       → endet bei phase14_discovery, phase15_v4 fehlt

scripts/check_doc_rotation.py:73      _SESSION_NUM_RE = re.compile(
                                           r"(?:Mini-)?Session\s+(\d+)"
                                       )
                                       → matcht NICHT "MiniMax-M3-Exec-Session #3"
                                       → matcht NICHT "Exec-Session #3"
```

### §3.2 Probe-Aufruf (heute, 2026-08-31, selbst ausgeführt)

```
$ python3 scripts/check_doc_rotation.py --strict
[OK]   phase1_broker_wrapper: 1 session block
... (12 weitere OK) ...
[OK]   phase14_discovery: 1 session block
All phase heads OK.
→ exit 0, aber phase15_v4 fehlt komplett

$ python3 scripts/check_doc_rotation.py --strict --phase phase15_v4
[OK]   phase15_v4: 1 session block
All phase heads OK.
→ Step-1 grün, Step-2 silent-skipped weil _max_session_num für die
  Heading "## Session stopped — 2026-08-31 (MiniMax-M3-Exec-Session #3, …)"
  None returnt (Regex matcht nicht).
```

**Was nach P15-F passieren wird:**
```
$ python3 scripts/check_doc_rotation.py --strict
... (14 OK) ...
[OK]   phase15_v4: 1 session block
All phase heads OK.
→ 15 Phasen-OK, phase15_v4 jetzt mit echter Step-2-Prüfung:
  head=3 (MiniMax-M3-Exec-Session #3), archive-newest=2 (MiniMax-M3-Exec-Session #2),
  expected=2 → ✅ konform.
```

### §3.3 Heading-Inventar in Phase 15 (heute, 2026-08-31, selbst gegrept)

```
phase15_v4/CLAUDE.md:407       ## Session stopped — 2026-08-31 (MiniMax-M3-Exec-Session #3, Block A Step A-6 + Block A endgültig abgeschlossen)
phase15_v4/SESSIONS_ARCHIVE.md:11   ## Session stopped — 2026-08-31 (MiniMax-M3-Exec-Session #2, Block A Step A-5 + Session-Rotation)
phase15_v4/SESSIONS_ARCHIVE.md:158  ## Session stopped — 2026-08-31 (MiniMax-M3-Exec-Session, Block A: A-1..A-4 + Session-End-Rotation)
phase15_v4/SESSIONS_ARCHIVE.md:342  ## Session stopped — 2026-08-31 (Plan-Session, Opus 5)
```

**Beobachtungen:**
- 3 von 4 Headings matchen die Form `MiniMax-M3-Exec-Session #N` (oder ohne #N — MiniMax-M3 #1 hat keine explizite Nummer, aber die implizite Nummerierung ist 1).
- 1 Heading (`Plan-Session, Opus 5`) ist die **Pre-Phase-Session** — sie zählt **nicht** in der `head-N == archive-max-(N-1)`-Sequenz, weil sie die Phase-15-Planung war (vor der Execution). Sie hat „Opus 5" als Identifikator, nicht als Session-Nummer.
- **Mit D2-Regex** `(?:Mini-|MiniMax-\w+-Exec-|Exec-)?Session\s+#?(\d+)`:
  - MiniMax-M3-Exec-Session #3 → 3 ✓
  - MiniMax-M3-Exec-Session #2 → 2 ✓
  - MiniMax-M3-Exec-Session → None (kein #N, kein `\d+` nach "Session") — **gewollt**, wird als nicht-Session gezählt
  - Plan-Session, Opus 5 → None (kein `\d+` direkt nach "Plan-Session") — **gewollt**, Pre-Phase-Session
- **`max()`** der gefundenen Session-Nummern in `phase15_v4/CLAUDE.md` = 3, im Archiv = 2 → Sequenz-Invariante ✅

### §3.4 `scripts/install_hooks.sh` ist seit P14-F auf `--strict` (selbst gegrept)

```
scripts/install_hooks.sh:56    python3 scripts/check_doc_rotation.py --strict --quiet
→ P15-F Erweiterung wird **automatisch** wirksam, sobald sie commited ist.
  Kein `install_hooks.sh`-Edit nötig.
```

---

## §4 Schritte (zwei Atome, in fester Reihenfolge)

> **Commit nach jedem Schritt.** Nach jedem Schritt `pytest tests/test_check_doc_rotation.py`
> — eine neue Test-Funktion pro Schritt 2. Schritte sind so geschnitten, dass jeder Schritt
> für sich alle Tests grün lässt.

### Schritt 1 — Tool-Erweiterung (1 Commit, `scripts/check_doc_rotation.py`)

**Geänderte Datei:** `scripts/check_doc_rotation.py` (2 Edits, ~5 Zeilen)

**Edit 1 — `PHASE_DIRS` um `phase15_v4` erweitern** (vor dem Kommentar-Block):

```python
PHASE_DIRS: tuple[str, ...] = (
    "phase1_broker_wrapper",
    "phase2_persistence",
    "phase3_external_data",
    "phase4_research",
    "phase5_execution",
    "phase6_debate",
    "phase7_reward",
    "phase8_scheduler",
    "phase9_universe",
    "phase10_v3",
    "phase11_housekeeping",  # falls existent (siehe Drift §8 #5)
    "meta_m1_harness",
    "phase12_data_foundation",
    "phase13_live_data",
    "phase14_discovery",
    "phase15_v4",  # P15-F: Phase 15 (V4) seit 2026-08-31 in execution
)
```

> **Drift-Hinweis:** `phase11_housekeeping` ist **nicht** im aktuellen PHASE_DIRS (P14-F-Plan §8 #3
> bestätigt: „Phase 11 ist absichtlich nicht — war eine Deferral, kein Phasenkopf mehr"). Diese
> Mini-Plan-Änderung fügt **nur** `phase15_v4` hinzu. Wenn `phase11_housekeeping` jemals
> einen Phasenkopf bekommt, wird er in einem Folge-Mini-Plan ergänzt.

**Edit 2 — `_SESSION_NUM_RE` permissiver machen** (Z. 73):

```python
# P15-F plan §2 D2: permissiver gegen MiniMax-Vendor-Prefix und optionales '#'-Zeichen.
# Matcht weiterhin P14-F-Stand („Session N", „Mini-Session N") plus die Phase-15-
# Vokabulare („Exec-Session #N", „MiniMax-M3-Exec-Session #N"). \w+ im Prefix-
# Block matched jeden Vendor-Prefix (MiniMax-M3, MiniMax-4, MiniMax-Opus, …),
# sodass zukünftige Varianten ohne Mini-Plan-Anpassung laufen.
_SESSION_NUM_RE = re.compile(
    r"(?:Mini-|MiniMax-\w+-Exec-|Exec-)?Session\s+#?(\d+)"
)
```

**Akzeptanz Schritt 1:** bestehende P14-F-Tests bleiben unverändert grün;
**vier neue Tests** in `tests/test_check_doc_rotation.py` (siehe Schritt 2).

### Schritt 2 — Tests für Phase-15-Heading-Formen (1 Commit, `tests/test_check_doc_rotation.py`)

**Geänderte Datei:** `tests/test_check_doc_rotation.py` (4 neue Test-Funktionen am Ende).

```python
def test_archive_sequence_recognises_exec_session_with_hash(tool, tmp_path):
    """A3: head=Exec-Session #3, archive-newest=Exec-Session #2 → OK (Phase 15, Block A).

    Reproduziert den aktuellen Phase-15-Stand (MiniMax-M3-Exec-Session #3 im
    Phasenkopf, #2 im Archiv, #1 auch im Archiv).
    """
    (tmp_path / "CLAUDE.md").write_text(
        "## Session stopped — 2026-08-31 (MiniMax-M3-Exec-Session #3, ...)\n",
        encoding="utf-8",
    )
    (tmp_path / "SESSIONS_ARCHIVE.md").write_text(
        "## Session stopped — 2026-08-31 (MiniMax-M3-Exec-Session #2, ...)\n"
        "## Session stopped — 2026-08-31 (MiniMax-M3-Exec-Session, ...)\n"  # #1 ohne Nummer
        "## Session stopped — 2026-08-31 (Plan-Session, Opus 5)\n",  # Pre-Phase
        encoding="utf-8",
    )
    assert tool.check_archive_sequence(tmp_path) is None


def test_archive_sequence_drift_when_phase15_skips_a_session(tool, tmp_path):
    """A4: head=Exec-Session #3, archive-newest=Exec-Session #1 (überspringt #2) → ❌ DRIFT."""
    (tmp_path / "CLAUDE.md").write_text(
        "## Session stopped — 2026-08-31 (MiniMax-M3-Exec-Session #3, ...)\n",
        encoding="utf-8",
    )
    (tmp_path / "SESSIONS_ARCHIVE.md").write_text(
        "## Session stopped — 2026-08-31 (MiniMax-M3-Exec-Session #1, ...)\n",
        encoding="utf-8",
    )
    result = tool.check_archive_sequence(tmp_path)
    assert result is not None
    label, diagnostic = result
    assert "Session 3" in diagnostic or "Exec-Session" in diagnostic
    assert "expected 2" in diagnostic


def test_archive_sequence_ignores_plan_session_without_number(tool, tmp_path):
    """A5: archive enthält Plan-Session-Block (kein \d+) → wird ignoriert, nicht als max gezählt.

    Phase 15 hat im Archiv einen Pre-Phase-Session-Block „Plan-Session, Opus 5"
    (Planungs-Session, VOR der Execution). Wenn dieser Block fälschlich als
    Session-N gezählt würde, wäre archive_max falsch → false-positive DRIFT.
    Die D2-Regex stellt sicher, dass „Plan-Session, Opus 5" **nicht** als
    Session-Nummer extrahiert wird (kein \d+ direkt nach "Plan-Session").
    """
    (tmp_path / "CLAUDE.md").write_text(
        "## Session stopped — 2026-08-31 (MiniMax-M3-Exec-Session #3, ...)\n",
        encoding="utf-8",
    )
    (tmp_path / "SESSIONS_ARCHIVE.md").write_text(
        "## Session stopped — 2026-08-31 (Plan-Session, Opus 5)\n"
        "## Session stopped — 2026-08-31 (MiniMax-M3-Exec-Session #2, ...)\n",
        encoding="utf-8",
    )
    assert tool.check_archive_sequence(tmp_path) is None


def test_strict_check_passes_for_phase15_v4_against_real_repo(tool, tmp_path):
    """A6: Echte Repo-Phase-15-Struktur (Head mit #3, Archiv mit #2) ist Step-2-konform.

    Probe-Aufruf gegen die echte Repo-Struktur (phase15_v4/CLAUDE.md +
    phase15_v4/SESSIONS_ARCHIVE.md). Wenn dieser Test grün ist, ist die
    Phase-15-Härtung wirksam.
    """
    import subprocess, sys
    repo_root = Path(__file__).resolve().parent.parent
    result = subprocess.run(
        [sys.executable, str(repo_root / "scripts" / "check_doc_rotation.py"),
         "--strict", "--phase", "phase15_v4"],
        capture_output=True, text=True, cwd=repo_root,
    )
    assert result.returncode == 0, (
        f"check_doc_rotation --strict --phase phase15_v4 failed:\n"
        f"stdout: {result.stdout}\nstderr: {result.stderr}"
    )
    assert "phase15_v4" in result.stdout
    assert "Sequence gap" not in result.stdout
```

**Akzeptanz Schritt 2:** `pytest tests/test_check_doc_rotation.py -q` → **11 grün**
(7 P14-F + 4 P15-F), `pytest tests/ -q` (root tests/) → **105 grün** (101 + 4 neu).
Bestehende Tests in anderen Phasen unverändert.

### Schritt 3 — INDEX.md + Phase-15-Phasenkopf updaten (1 Commit, 2 Dateien)

**Geänderte Datei 1 — `docs/INDEX.md`:**

Aktuell (Z. 33) hat die Phase-15-Zeile nur den Hinweis auf den Plan, nicht auf den Plan +
Mini-Plan. Eine neue Zeile analog P14-F (siehe `docs/INDEX.md:46` für `PHASE14_F_…_PLAN.md`):

```
- [phase15_v4/PHASE15_HOOK_HARDENING_PLAN.md](../phase15_v4/PHASE15_HOOK_HARDENING_PLAN.md) — 📕 **Mini-Plan P15-F (Doc-Rotation-Hook für Phase 15, 2026-08-31)**: PHASE_DIRS-Erweiterung + permissive MiniMax-M3-Exec-Session-#N-Regex + 4 neue Tests A3–A6; analog P14-F (Phase-14-Schwester). Cross-Phase-Freigabe: nur `scripts/check_doc_rotation.py` (Phase-14-eigener Hygiene-Code).
```

**Geänderte Datei 2 — `phase15_v4/CLAUDE.md`:**

Im Header-Card `down:`-Block eine neue Zeile:

```yaml
down:
  - ./SESSIONS_ARCHIVE.md                  # full session history (L3)
  - ./README.md
  - ./PHASE15_HOOK_HARDENING_PLAN.md       # 📕 Mini-Plan P15-F (Doc-Rotation-Hook-Härtung für Phase 15, 2026-08-31)
  - ../docs/concepts/phase7_reward_concept.md
  - ../phase10_v3/PHASE11_DEFERRAL_HANDOVER.md
  - ../phase14_discovery/PHASE14_CLOSEOUT_HANDOVER.md
  - ../docs/concepts/phase15_v4_plan.md
```

**Akzeptanz Schritt 3:** `docs/INDEX.md` (1 neue Zeile) + `phase15_v4/CLAUDE.md`
(`down:`-Block, 1 neue Zeile + `updated:` von `2026-08-31` auf `2026-08-31 (+ P15-F
Doc-Rotation-Hook-Härtung)`). `pytest tests/ -q` unverändert 105 grün.

---

## §5 Akzeptanz (PASS-Kriterien A1–A6)

| # | Kriterium | Wie belegt |
|---|---|---|
| **A1** | `_max_session_num` extrahiert die korrekte Session-Nummer aus `## Session stopped ... (Session N ...)` und `(Mini-Session N ...)` | P14-F-Tests `test_archive_sequence_handles_mini_session_naming` + `test_archive_sequence_ok_for_continuous_block` (unverändert grün) |
| **A2** | `_max_session_num` extrahiert die korrekte Session-Nummer aus `(Exec-Session #N)` und `(MiniMax-M3-Exec-Session #N)` | **A3** (neu in P15-F) |
| **A3** | `check_archive_sequence` ist OK für Phase-15-Stand: head=#3, archive-newest=#2, expected=2 | `test_archive_sequence_recognises_exec_session_with_hash` (neu in P15-F) |
| **A4** | `check_archive_sequence` erkennt eine Phase-15-Sequenz-Lücke (head=#3, archive-newest=#1) als FAIL | `test_archive_sequence_drift_when_phase15_skips_a_session` (neu in P15-F) |
| **A5** | `check_archive_sequence` ignoriert den Plan-Session-Block „Plan-Session, Opus 5" (kein `\d+` nach „Plan-Session") | `test_archive_sequence_ignores_plan_session_without_number` (neu in P15-F) |
| **A6** | `--strict --phase phase15_v4` exit 0 gegen die echte Repo-Struktur | `test_strict_check_passes_for_phase15_v4_against_real_repo` (Subprozess, kein Mock) |

**Akzeptanz-Σ:** `pytest tests/ -q` → **105 grün** (101 root + 4 P15-F-Test-Datei
`tests/test_check_doc_rotation.py` bekommt +4 Tests, war 7 → 11).

---

## §6 Out of Scope

- **Phase-15-Heading-Änderungen** — die aktuelle Form „(MiniMax-M3-Exec-Session #N, ...)"
  ist lesbar, das Tool ist permissiv genug (D2).
- **Cross-Phase-Code-Edits** außer `scripts/check_doc_rotation.py` + `tests/test_check_doc_rotation.py`.
  Insbesondere **kein** `scripts/install_hooks.sh`-Touch (P14-F-Stand reicht — `--strict`
  ist bereits Default).
- **`dev_install.sh`-Anbindung** — bereits in P14-F erfolgt (Z. 85, `bash "${ROOT}/scripts/install_hooks.sh" || true`).
- **Auto-Fix der Drift** (der Hook darf nicht schreiben — pre-commit-Philosophie).
- **Phase-15-Plan-Session-Block (Opus 5) als „Session #0" markieren** — Plan-Session zählt
  per Konvention nicht in der `head-N == archive-max-(N-1)`-Sequenz; die Heading
  „Plan-Session, Opus 5" wird absichtlich **nicht** als Session-Nummer extrahiert
  (D2-Regex verlangt `\d+` direkt nach „Plan-Session", das ist hier nicht gegeben).
- **Phase-16+-Vokabular-Erweiterungen** — D2-Regex ist permissiv genug für MiniMax-M3,
  MiniMax-4, etc. (jeder `MiniMax-\w+-Exec-`-Prefix matched); falls eine ganz andere
  Variante kommt, ist das ein Folge-Mini-Plan.
- **Live-Code-Touch** (per Definition pre-commit-Hygiene, kein Runtime).

---

## §7 Fehlgriffe, die wie andere Fehler aussehen

| Symptom | Erster Verdächtiger | Wie unterscheiden |
|---|---|---|
| **„`check_doc_rotation.py --strict` FAIL bei phase15_v4"** | Echte Sequenz-Lücke in Phase 15 | `python3 scripts/check_doc_rotation.py --strict --phase phase15_v4` zeigt die Diagnostik; ein einzelner Commit, der die fehlende Session ins Archiv rotiert, fixt es |
| **„P15-F-Test grün lokal, aber `scripts/check_doc_rotation.py --strict` zeigt FAIL"** | Test-Mismatch oder vergessener PHASE_DIRS-Edit | `grep "phase15_v4" scripts/check_doc_rotation.py` muss genau 1 Treffer zeigen; der Test ruft `--phase phase15_v4` und umgeht damit die PHASE_DIRS-Konfiguration — der Hook-Aufruf ohne `--phase` braucht den PHASE_DIRS-Eintrag |
| **„Regex matcht MiniMax-M3-Exec-Session, aber MiniMax-4-Exec-Session nicht"** | \w+ deckt nicht den Bindestrich zwischen Ziffern | Aktuelle Regex: `MiniMax-\w+-Exec-`. \w+ matcht `[a-zA-Z0-9_]`, kein Bindestrich. **Test:** `re.match(r"MiniMax-\w+-Exec-", "MiniMax-4-Exec-")` → matcht nicht, weil zwischen "4" und "Exec" ein Bindestrich steht, der nicht zu `\w+` gehört — aber `\w+` kann greedy matchen bis „4-Exec", und dann ist „-Exec-" der Prefix. Korrekt funktioniert es, weil `\w+` greedy ist und „4" frisst, dann muss das nächste Zeichen „-" sein (was es ist), dann „Exec-" — alles matched. Falls das in einem Test fehlschlägt: Regex auf `(?:Mini-|MiniMax-[\w-]+-Exec-|Exec-)?` anpassen (Bindestrich in Character-Class). |
| **„Hook zeigt OK für Phase 15, aber `SESSIONS_ARCHIVE.md` zeigt nur einen Eintrag"** | Plan-Session-Block wurde als Session gezählt | `_max_session_num` testen — sollte None für „Plan-Session, Opus 5" returnen. Wenn doch: Regex hat einen Bug (z.B. `(?:Plan-)?Session\s+\d+` würde auch „Plan-Session 5" matchen, aber nicht „Plan-Session, Opus 5" — das Komma schützt). |

---

## §8 Drift-Liste — bei Ausführung verifizieren

> **Diese Liste ist vollständig.** Was hier nicht steht, hat diese Planungssession am
> 2026-08-31 selbst gegen das Repo geprüft und ist als Fakt formuliert. Rate nichts nach;
> prüfe diese und nur diese.

1. **Zeilennummern verschieben sich.** Jeder Anker oben trägt den **Verbatim-String** —
   der ist der Anker, die Zahl die Abkürzung. Schritt 1 verschiebt
   `scripts/check_doc_rotation.py` (PHASE_DIRS + Regex); Schritt 2 verschiebt
   `tests/test_check_doc_rotation.py` (4 neue Tests am Ende). **Immer per String suchen.**
2. **`SESSION_HEADING = "## Session stopped"`** (Z. 68, vor diesem Plan) bleibt unverändert
   — Step 2 nutzt `_SESSION_NUM_RE`, nicht `SESSION_HEADING`. Step 1 (Count) bleibt
   kompatibel zu bestehenden Tests.
3. **Bestehende P14-F-Tests** (`pytest tests/test_check_doc_rotation.py` 7 grün) bleiben
   unverändert grün — Schritt 2 fügt 4 neue Tests hinzu, kein Touch an anderen Tests.
   Σ-Sweep 101 root tests + 7 P14-F-Tests + 4 P15-F-Tests = **112 root + P14-F + P15-F**
   (oder: root `tests/` ist 101, separater Test-Pfad `tests/test_check_doc_rotation.py`
   ist 7+4=11 — beide werden von pytest getrennt entdeckt, je nach pyproject-`testpaths`).
4. **Plan-Session-Block (Opus 5)** im `phase15_v4/SESSIONS_ARCHIVE.md` Z. 342 — wird **bewusst
   nicht** als Session-Nummer extrahiert (D2-Regex matcht nicht ohne `\d+` direkt nach
   „Plan-Session"). Das ist gewollt: Plan-Session ist Pre-Phase, nicht Teil der Sequenz.
5. **`phase11_housekeeping` ist nicht in PHASE_DIRS** (P14-F-Plan §8 #3 bestätigt: Phase 11
   lebt in `phase10_v3/`, kein eigener Phasenkopf). P15-F fügt **nur** `phase15_v4` hinzu,
   nicht `phase11_housekeeping`. Wenn Phase 11 jemals einen eigenen Phasenkopf bekommt,
   wird er in einem Folge-Mini-Plan ergänzt.
6. **`scripts/install_hooks.sh` ruft `--strict --quiet`** (P14-F-Stand, Z. 56) — P15-F
   wirkt automatisch nach Commit, kein Installer-Edit nötig.
7. **`scripts/dev_install.sh` ruft `install_hooks.sh` als letzten Schritt** (P14-F-Stand,
   Z. 85) — P15-F braucht hier nichts.
8. **`meta_m1_harness` in PHASE_DIRS** — bleibt in der Liste (P14-F-Stand: „separates
   `SESSIONS_ARCHIVE.md`, gleiche Konvention; included here for symmetry"). P15-F fügt
   nichts an dieser Position.

---

## §9 Cross-Referenz

- **Mutterplan** [`../docs/concepts/phase15_v4_plan.md`](../docs/concepts/phase15_v4_plan.md)
  — nicht direkt berührt; P15-F ist Hygiene (analog P14-F), unabhängig von V4-Mission.
- **Geschwister-Mini-Plans** [`../phase14_discovery/PHASE14_F_DOC_ROTATION_HOOK_STEP2_PLAN.md`](../phase14_discovery/PHASE14_F_DOC_ROTATION_HOOK_STEP2_PLAN.md)
  (Vorlage) + [`../phase14_discovery/PHASE14_E_RECORDER_LOOP_PLAN.md`](../phase14_discovery/PHASE14_E_RECORDER_LOOP_PLAN.md) (Cross-Phase-Beispiel).
  P15-F ist die direkte Folge von P14-F (gleiches Tool, andere Phase).
- **PHASE15-Plan** [`../docs/concepts/phase15_v4_plan.md`](../docs/concepts/phase15_v4_plan.md)
  §6 Step-A-Liste — P15-F ist **kein** offizieller Step im Plan, sondern Hygiene aus
  dem NEXT-Block der Session-#2-Beobachtung (A-5 + A-6 Session-Stops).
- **Phase-13-CLOSE-OUT + Phase-14-CLOSE-OUT** — nicht berührt, unabhängige Hygiene-Tracks.
- **Doc-Layers-Konvention** [`../docs/DOC_LAYERS_CONVENTION.md`](../docs/DOC_LAYERS_CONVENTION.md)
  — nicht geändert; P15-F ist eine **Implementation** der existierenden Konvention
  (PHASE_DIRS-Erweiterung + Regex-Permissivität), keine Konventions-Änderung.
- **P15-A-5 + P15-A-6 Session-Blocks** (in `phase15_v4/SESSIONS_ARCHIVE.md`) — P15-F
  begründet die Heading-Form „MiniMax-M3-Exec-Session #N" als **permissiv** zu unterstützen.
  Wenn eine andere Phase in Zukunft ein anderes Vokabular etabliert, wird ein Folge-
  Mini-Plan die Regex erweitern (oder, wenn systematisch genug, eine generischere Regex).
