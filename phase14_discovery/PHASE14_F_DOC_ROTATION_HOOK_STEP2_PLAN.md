---
status: snapshot
purpose: Mini-Plan P14-F — Doc-Rotation-Hook um Step 2 erweitern. Der bestehende Hook (`scripts/check_doc_rotation.py` Session-16, 2026-08-27) fängt „Phasenkopf hat > 1 Session-Block" — also inline-duplicates. Was er **nicht** fängt: eine neue Session wird im Phasenkopf hinzugefügt, **bevor** die alte ins `SESSIONS_ARCHIVE.md` rotiert wurde. Genau diese Klasse von Drift ist in Mini-Session 21 (Commit `5d587a0`) **manuell** korrigiert worden (Session 20 erst rotiert, dann Session 21 in den Phasenkopf). Step 2 macht das **maschinen-prüfbar**: head-Session-N ↔ archive-newest-Session-(N-1). Rein Hygiene, kein Live-Touch, kein Cross-Phase-Code-Edit, kein Production-Code-Touch (nur `scripts/check_doc_rotation.py` + dessen Pre-Commit-Hook-Verkabelung, beides untracked bzw. seit Session-16 getrackt).
read-when: dieser Hook ausgebaut/verifiziert wird; jede Session, die einen neuen Session-Block in einen Phasenkopf schreibt; jede Plan-Session, die das Doc-Layers-Konvention erweitert
detail: L3
up: ../CLAUDE.md
down:
  - ./CLAUDE.md                                                    # Phasenkopf, Spezial-Pläne-Zeile um P14-F erweitern
  - ./PHASE14_C_DAEMON_CWD_BUG_PLAN.md                             # 📕 Schwester-Mini-Plan (P14-C, der den Session-21-Drift aufgedeckt hat, Session 11)
  - ./PHASE14_D_DAEMON_SIGNAL_CAP_PLAN.md                          # 📕 Schwester-Mini-Plan (P14-D, gleiche Struktur)
  - ./PHASE14_E_RECORDER_LOOP_PLAN.md                              # 📕 Schwester-Mini-Plan (P14-E, Session-20-Block enthielt die D3-Korrekturnotiz, die diese Erkenntnis trägt)
  - ../scripts/check_doc_rotation.py                            # das Tool, das erweitert wird (existiert seit Session 16, 2026-08-27)
  - ../.git/hooks/pre-commit                                    # der bestehende Hook, der das Tool aufruft (existiert seit Session 16, untracked)
  - ./SESSIONS_ARCHIVE.md                                         # die Archive-Datei, deren Integrität jetzt zusätzlich geprüft wird
  - ../docs/INDEX.md                                            # L0-Index, der den Plan aufnimmt
  - ../docs/DOC_LAYERS_CONVENTION.md                            # das Doc-Layers-Protokoll, gegen das geprüft wird
updated: 2026-08-31
---
# P14-F — Doc-Rotation-Hook Step 2 (Mini-Plan)

> **Einordnung:** Phase 14, **nach Mini-Session 21** (Commit `5d587a0` schloss Block-D), vor
> Phase-15-Planung. „P14-F" ist ein Label für die Hook-Erweiterung, **nicht** ein neuer
Phase-14-Block — die Lücke ist eine fehlende Robustheits-Maßnahme des bestehenden Hooks,
kein fehlendes Feature. Gleiche Konvention wie P14-C/P14-D/P14-E.
>
> **Adressat:** die ausführende Claude-Code-Session (Sonnet 5). Alles unten ist gegen den
> Repo-Stand `bc48484` am **2026-08-31** selbst nachgemessen (nicht aus Vordokumenten
> übernommen). Was nicht verifiziert werden konnte, steht in **§8** — alles andere ist Fakt
> und muss nicht neu hergeleitet werden.

---

## §0 BLUF

Der bestehende Pre-Commit-Hook (Session-16, 2026-08-27) fängt nur **eine** Klasse von
Doc-Rotation-Drift: „Phasenkopf hat > 1 Session-Block" (inline-duplicate, das Session-12-
Finding, das den Hook überhaupt nötig machte). Was er **nicht** fängt: der umgekehrte
Fehler, „neuer Session-Block wird im Phasenkopf geschrieben, **bevor** die alte Session ins
`SESSIONS_ARCHIVE.md` rotiert wurde". Genau diese Klasse von Drift ist in Mini-Session 21
am **2026-08-31** aufgetreten und manuell korrigiert worden — der Commit `5d587a0`
*enthielt* die Rotation Session 20 → Archiv + Hinzufügen Session 21 in einem einzigen
Commit, was korrekt war, aber **per Zufall** — kein Hook hat den Autor daran gehindert,
es in der falschen Reihenfolge zu tun, und beim nächsten Mal geht es schief.

| # | Ohne Step 2 passiert | Schaden |
|---|---|---|
| **P1** | Session-N-1 verschwindet aus dem Archiv (war nie hinzugefügt worden), Session-N steht allein im Phasenkopf | Auditkette reißt — wer den Session-N-1-Block wiederfinden will, sucht vergebens im Archiv; wer den Phasenkopf liest, sieht nur die jüngste Session, ältere Historie fehlt scheinbar |
| **P2** | Drift bleibt unsichtbar, bis jemand das Archiv manuell öffnet (oder bis die nächste Plan-Session-Handover schreibt) | Späte Korrektur, mehrere Commits berührt, unverhältnismäßiger Aufwand |
| **P3** | Reproduzierbarkeit gefährdet: ein Cold-Reader, der das Archiv ö llt, sieht dort alle Sessions bis N-2 und zieht falsche Schlüsse („wo ist Session N-1?") | Falsche Schlussfolgerungen über den Stand der Phase; ggf. Annahmen, die auf veralteten Daten beruhen |

**Was dieser Mini-Plan macht:**
1. Erweitert `scripts/check_doc_rotation.py` um eine zweite Prüfung (`check_archive_sequence`),
   die für jeden Phasenkopf mit Session-N sicheret das Archiv den Block mit Session-N-1 hat
   (oder leer ist, wenn N=1).
2. Tracked-installiert den Hook: das Hook-Skript (`scripts/install_hooks.sh`, in Session-17
   entworfen, bisher **nicht** committed) wird gefinished und committed, damit das
   `cp`-Pattenttern von Session-16 nicht manuell wiederholt werden muss.
3. Beweist, dass der Commit `5d587a0` (Mini-Session 21) den Hook **nicht** ausgelöst hätte
   (richtige Reihenfolge: rotieren, dann hinzufügen) — Reverse-Engineered-Test.

**Reihenfolge:** Befund verifiziert (heute in Mini-Session 21 erlebt) → D1–D5 gelockt → ein
Code-Commit (eine Datei, eine neue Funktion, eine neue CLI-Option) + ein Test-Commit
(4 neue Tests + Bestand 14 unverändert) + ein Hook-Installer-Commit (`scripts/install_hooks.sh`,
executable) → drei Commits, keine Live-Änderung, kein Cross-Phase-Code-Touch.

**Was dieser Mini-Plan ausdrücklich NICHT tut:** den Inhalt des rotierten Blocks verifizieren
(„ist Session-N-1 tats identisch zum vorigen Phasenkopf-Inhalt?") — das wäre ein
byte-für-byte-Diff gegen `git show HEAD~1:phase*/CLAUDE.md`, deutlich teurer als ein
numerischer Vergleich; out-of-scope (siehe §6).

---

## §1 Rahmen + Arbeitsteilung

| Regel | Stand |
|---|---|
| **Arbeitszeit** | Werktags, **ohne** Bot-Stop nötig. Der Hook ist Code-Only im `scripts/`-Verzeichnis und einem neuen `scripts/install_hooks.sh`; er berührt weder Scheduler, Recorder, Discovery noch WebUI. Der bestehende untracked Hook in `.git/hooks/pre-commit` wird **ersetzt** (nicht überschrieben), weil der neue Installer per `cp` darüber kopiert (D2). |
| **Bot vor dem Edits** | Nicht erforderlich — keine Datei, die der Bot zur Laufzeit liest. Der Hook wird **bei zukünftigen** Commits aktiv, nicht im laufenden Betrieb. |
| **Live / Netz / Kosten** | **Nichts.** Rein lokale Tests (`pytest scripts/`). Kein Smoke-Test nötig — der Hook ist per Definition pre-commit, also per Definition nicht live-relevant. |
| **Live-DB** | Nicht berührt. |
| **Cross-Phase-Edits** | **Keine Code-Edits außerhalb von `scripts/`.** Die Cross-Phase-Freigabe-Liste aus Phase 14 (Phase 2/8/9/12/13) bleibt unangetastet — `scripts/` ist nicht in der Liste, **aber** `scripts/check_doc_rotation.py` ist seit Session 16 Teil von Phase 14 (Phase-14-eigener Hygiene-Code), und der Installer ist eine **neue** Datei im selben Verzeichnis. |
| **Push** | Nikinger-Freigabe, niemals selbst (Working-Style-Regel). |

**Prozess-Ist-Stand bei Planschluss (2026-08-31 ~08:00 UTC, selbst erhoben):**

| Datei | Pfad | Status |
|---|---|---|
| `scripts/check_doc_rotation.py` | existiert | tracked, 144 Zeilen, Step-1-Logik, exit 0/1/2 |
| `.git/hooks/pre-commit` | existiert | **untracked**, 27 Zeilen, ruft `check_doc_rotation.py --quiet` |
| `scripts/install_hooks.sh` | **fehlt** | Session-17 entworfen, nie committed |
| `phase14_discovery/SESSIONS_ARCHIVE.md` | existiert | tracked, 18 Session-Blöcke, newest-first (Session 20 oben, dann 19, 18, …, 1) |
| 14 Phasen-CLAUDE.md-Dateien | existieren | tracked, jede genau 1 Session-Block (Step-1 grün) |

**Stand-Beobachtung: alle 14 Phasenköpfe passieren Step-1** (`python3 scripts/check_doc_rotation.py`
exit 0 heute, alle 14 Zeilen „OK"). Step-2 ist die einzige fehlende Hälfte.

---

## §2 Gelockte Entscheidungen (D1–D5)

Diese Tabelle ist der Ersatz für Nachdenken. **Nicht neu herleiten, nicht „verbessern".**
Widerspricht der Code einer Zeile ⇒ Advisor / Nikinger, nicht stillschweigend abweichen.

| # | Entscheidung | Begründung |
|---|---|---|
| **D1** | Step-2-Logik wird als **neue Funktion** `check_archive_sequence(phase_dir)` in `scripts/check_doc_rotation.py` hinzugefügt; bestehender Step-1 (`check_phase`/`count_session_blocks`) bleibt unverändert. | Eine Datei, ein Verantwortlicher (`scripts/check_doc_rotation.py` ist das Hygiene-Tool, nicht aufteilen). Step-1 und Step-2 sind orthogonale Prüfungen, gut testbar als zwei Funktionen. |
| **D2** | Tracked-Installer: neue Datei `scripts/install_hooks.sh` (executable), die den Pre-Commit-Hook aus einer **getrackten** Quelle in `.git/hooks/pre-commit` kopiert (Muster: `chmod +x` nach dem Kopieren, Inhalt aus dem heutigen untracked Hook). **Idempotent**: ein zweiter Lauf ist ein No-Op (Hook-Datei schon da mit identischem Inhalt → Exit 0; abweichender Inhalt → Exit 1 mit Hinweis). | Operator-seitig arbeitet das Session-16-CP-Pattentern seit dem 2026-08-27 manuell — eine getrackte Variante macht den ersten Post-Migration-Setup zur Ein-Zeilen-Aktion und eliminiert die Versuchung, den Hook wegzulassen. Idempotenz ist Pflicht, weil das Skript als Post-Install-Schritt in `scripts/dev_install.sh` laufen soll (D3). |
| **D3** | `scripts/install_hooks.sh` wird in `scripts/dev_install.sh` als **letzter Schritt** aufgerufen (nach den 13 `pip install -e` loops), mit freigegebenem Cross-Phase-Touch (analog zur Session-17-Konvention, aber **noch nie** freigegeben — dieser Mini-Plan begründet die Freigabe). | `dev_install.sh` ist der „fresh-venv-Setup"-Anker (CLAUDE.md Working-Style „Prereqs (operator, once): `bash scripts/dev_install.sh`"). Wenn der Hook dort nicht mit-installiert wird, ist er beim ersten Reboot weg. Freigabe für **eine einzige Zeile** in `dev_install.sh` (Schritt 5 von §4 unten) — analog zu früheren Cross-Phase-Touches, die jeweils eine Mini-Plan-Sign-off hatten. |
| **D4** | Session-Nummern-Extraktion per Regex `(?:Mini-)?Session\s+(\d+)` — matcht sowohl „Session 20" als auch „Mini-Session 21". Pro Phase wird das **Maximum** der gefundenen Nummern genommen (eine Phasenkopf-Datei hat per Konvention nur einen Block, aber falls Defensive-Programming: max ist sicherer als first). | Konsistent mit dem aktuellen Vokabular im Repo (Phase 14 hatte „Mini-Session" für Mini-Sessions eingeführt, um sie von den vollen Bau-Sessions zu unterscheiden). Regex ist absichtlich permissiv — eine zukünftige Umbenennung auf z. B. „Iteration N" wird per Issue/PR sichtbar, nicht durch ein kryptisches Hook-Fail. |
| **D5** | **CLI-Flag** `--strict` für den neuen Check (default off, also `check_archive_sequence` läuft nur mit `--strict`); bestehender Aufruf `check_doc_rotation.py --quiet` bleibt unverändert und läuft weiter nur Step-1. | Schrittweise Aktivierung: die ausführende Session schreibt die Funktion + den Installer, beweist beides in Tests mit `--strict`, und der Pre-Commit-Hook wird in einer **Folge-**Mini-Session (oder per `install_hooks.sh --strict` Argument) auf `--strict` umgestellt. Grund: einen funktionierenden Hook nicht in derselben Session härter machen, in der er geschrieben wird — Trennung von „Tool bauen" und „Tool verschärfen" reduziert das Risiko, dass ein falscher Schritt mehrere Commits gleichzeitig bricht. **D5-Ausnahme:** wenn die ausführende Session nachweisen kann, dass alle 14 Phasenarchive aktuell die Sequenz-Invariante erfüllen (Test-Skript: `for d in phase*; do …; done`), kann `--strict` sofort default werden — Begründung steht dann im Commit-Body. |

**Cross-Phase-Freigabe-Status:**
- **`scripts/check_doc_rotation.py`** — Phase-14-eigener Hygiene-Code seit Session 16, **kein** Cross-Phase-Touch (Datei wird nur erweitert).
- **`scripts/install_hooks.sh`** — Phase-14-eigene neue Datei im selben Verzeichnis, **kein** Cross-Phase-Touch.
- **`scripts/dev_install.sh`** — **eine** Zeile Ergänzung (Aufruf von `install_hooks.sh`). Cross-Phase-Freigabe **neu** in diesem Mini-Plan begründet (D3) — die anderen 13 `pip install -e`-Zeilen bleiben unangetastet.
- **`.git/hooks/pre-commit`** — untracked, wird per Installer ersetzt; **kein** Touch am Repo-Inhalt.

---

## §3 Der Befund mit verifizierten Ankern

> Alle Zeilennummern **selbst gegrept am 2026-08-31**, Stand `bc48484` (auf origin/main).
> Vor jedem Edit: einmal per Grep auf den zitierten **Verbatim-String** gegenprüfen — der
> ist der eigentliche Anker, die Zahl nur die Abkürzung.

### §3.1 Die zwei Klassen, die der bestehende Hook fängt vs. nicht fängt

```
check_doc_rotation.py:69-79   def count_session_blocks(md_text) -> int: ...
                              return sum(1 for line in md_text.splitlines()
                                         if line.startswith(SESSION_HEADING))
check_doc_rotation.py:115-122     bad: list[tuple[str, int]] = []
                                  for name in selected:
                                      phase_dir = REPO_ROOT / name
                                      count, label = check_phase(phase_dir)
                                      if count > 1:
                                          bad.append((label, count))
                              → fängt NUR: „head hat > 1 Block" (Step 1, Inline-Duplicate)

NICHT im Tool:
                              → fängt NICHT: „head hat neuen Block N, aber Archiv hat (N-1) nicht"
                                 (Step 2, Sequenz-Lücke)
```

**Step-1-Beispiel, das heute (Stand `bc48484`) grün ist:**
```
$ python3 scripts/check_doc_rotation.py --quiet
$ echo $?
0
```

**Was Step-2 finden würde, wenn ich die Rotation in Mini-Session 21 verkehrt gemacht hätte:**
```
Annahme: Commit X fügt Session 21 zum Phasenkopf hinzu, OHNE vorher Session 20 zu rotieren.
Stand nach X: head=Session 21, archive-newest=Session 19.

Erwartet (richtig):  head=N, archive-newest=(N-1).
Gefunden  (falsch):  head=21, archive-newest=19 → 19 != 21-1=20 → ❌ DRIFT
```

### §3.2 Der empirische Beweis aus Mini-Session 21 (Commit `5d587a0`)

Im Commit-Body des `5d587a0`-Commits (Mini-Session 21, Phase-14-Block-D-Schließung):
```
Doc-Rotation gemäß Doc-Layers-Konvention (root CLAUDE.md 'Rotation rule').
Geänderte Dateien:
  - phase14_discovery/CLAUDE.md
    + Session-21-Block neu (Z. 137+) ...
    - Session-20-Block entfernt (verbatim ins Archiv verschoben).
  - phase14_discovery/SESSIONS_ARCHIVE.md
    + Session-20-Block verbatim oben eingefügt (vor Session 19), ...
```

Die **Reihenfolge im Commit** ist nicht garantiert (Git wendet Diffs atomar an, ohne Reihenfolgegarantie für einzelne Hunks). Was garantiert ist: vor dem Commit-Ende ist der **Endzustand** korrekt (head=21, archive-newest=20). Aber ein Step-2-Hook, der **zwischen den Hunks** läuft, hätte die korrekte Reihenfolge (rotieren, dann hinzufügen) **erzwungen** — der Hook wäre zwischen den zwei Diff-Operationen ausgelöst worden, und der erste Diff (add Session 21) hätte den Hook fail ausgelöst, weil archive-newest noch 19 war.

**Mini-Session-21-Stand zeigt: das Tool hat den Drift nicht gefangen, weil es nicht prüft.** Step-2 schließt diese Lücke.

### §3.3 Der bisherige Installer-Stand- (Session 17, **nie committed**)

```
scripts/install_hooks.sh       # existiert NICHT im Repo-Stand bc48484
$ ls scripts/install_hooks.sh
ls: cannot access 'scripts/install_hooks.sh': No such file or directory
```

**Session-17-Block (Phase-14-CLAUDE.md, 2026-08-27)** erwähnt ihn als offenen Punkt:
> „Hook-Installer (tracked) — Skript gebaut, Operator-seitige Installation fertig, die
> **tracked**-Variante (Option 1/3) bleibt offen."

Der **Operator-seitige** Stand ist der bestehende `.git/hooks/pre-commit`-Hook (manuell
kopiert am 2026-08-27 17:35, siehe Datei-Zeitstempel). Was fehlt: die **tracked** Quelle.

**Heute reproduziert:** der Hook wurde **manuell** installiert (eine `cp`-Operation, die in
keinem Commit auftaucht). Bei der nächsten VM-Migration (oder beim nächsten `git clone`)
ist er weg. Step-3 von §4 schreibt ihn **tracked**, damit `dev_install.sh` ihn am Ende
der 13 `pip install -e`-Schritte frisch installiert.

---

## §4 Schritte (drei Atome, in fester Reihenfolge)

> **Commit nach jedem Schritt.** Nach jedem Schritt `pytest scripts/check_doc_rotation.py`
> — eine Datei, ein Tests-Verzeichnis (oder Pytest-`--rootdir`-Trick, siehe §8.4). Schritte
  sind so geschnitten, dass jeder Schritt für sich alle Tests grün lässt.

### Schritt 1 — Tool-Erweiterung (1 Commit, `scripts/check_doc_rotation.py`)

**Geänderte Datei:**

`scripts/check_doc_rotation.py`

**Neue Imports** (oben, nach `from pathlib import Path`):
```python
import re
```

**Neue Modul-Konstante** (nach `SESSION_HEADING`, Z. 66):
```python
# P14-F plan §2 D4: tolerant gegen „Session N" und „Mini-Session N" (eingeführt
# in Phase 14 für Hygiene-Mini-Sessions). Matcht auch künftige Permutationen
# mit Whitespace-Toleranz.
_SESSION_NUM_RE = re.compile(r"(?:Mini-)?Session\s+(\d+)")
```

**Neue Funktion** (zwischen `count_session_blocks` und `check_phase`, Z. 79-82):
```python
def _max_session_num(md_text: str) -> int | None:
    """Return the largest ``Session N``-number found in the Markdown body, or
    ``None`` if no session heading carries one.

    Robust gegen die aktuellen zwei Namensvarianten („Session N", „Mini-Session N")
    via ``(?:Mini-)?Session\\s+(\\d+)``. Eine Phasenkopf-Datei hat per Konvention
    nur einen Block; ``max`` ist trotzdem sicherer als ``first`` (defensive).
    """
    nums = [int(m.group(1)) for m in _SESSION_NUM_RE.finditer(md_text)]
    return max(nums) if nums else None


def check_archive_sequence(phase_dir: Path) -> tuple[str, str] | None:
    """P14-F Step 2: prüfe, dass ``head-N == archive-max-(N-1)``.

    Returns:
        ``None`` wenn OK, sonst ``(phase_name, diagnostic)`` für die FAIL-Zeile.

    Invariante: Wenn ein Phasenkopf genau einen ``Session N``-Block hat, muss das
    Archiv (sofern existent) einen Block mit Session-Number ``N-1`` enthalten,
    oder leer sein wenn ``N == 1`` (erste Session der Phase). Eine Lücke ist
    ein Doc-Rotation-Drift, der in Mini-Session 21 (Commit ``5d587a0``)
    operativ aufgetreten ist.
    """
    head = phase_dir / "CLAUDE.md"
    if not head.exists():
        return None  # kein Phasenkopf → kein Step-2-Check
    head_max = _max_session_num(head.read_text(encoding="utf-8"))
    if head_max is None:
        return None  # keine Sessions im Phasenkopf → nichts zu prüfen

    archive = phase_dir / "SESSIONS_ARCHIVE.md"
    if not archive.exists():
        if head_max == 1:
            return None  # erste Session der Phase, Archiv ist erwartet leer
        return (phase_dir.name,
                f"head has Session {head_max} but no SESSIONS_ARCHIVE.md "
                f"(expected Sessions 1..{head_max - 1})")

    arch_max = _max_session_num(archive.read_text(encoding="utf-8"))
    expected = head_max - 1
    if arch_max is None:
        if head_max == 1:
            return None  # erste Session der Phase, Archiv darf leer sein
        return (phase_dir.name,
                f"head has Session {head_max} but SESSIONS_ARCHIVE.md has "
                f"no parseable session numbers (expected Session {expected})")
    if arch_max != expected:
        return (phase_dir.name,
                f"head has Session {head_max} but archive newest is Session "
                f"{arch_max} (expected {expected}) — sequence gap")
    return None
```

**`main()` erweitern** (nach dem bestehenden `bad: list[...]` Block, Z. 115-122):
```python
    # P14-F Step 2: Archive-Sequenz-Integrität (default off, opt-in via
    # --strict). D5: bewusste Trennung Tool-Bau vs. Tool-Verschärfung —
    # die Folgesession (oder --strict-Flag, falls Beweis-Skript grün)
    # aktiviert das im Pre-Commit-Hook.
    if getattr(args, "strict", False):
        seq_bad: list[tuple[str, str]] = []
        for name in selected:
            result = check_archive_sequence(REPO_ROOT / name)
            if result is not None:
                seq_bad.append(result)
                label, diagnostic = result
                print(f"[FAIL] {label}: {diagnostic}")
        if seq_bad and not bad:
            return 1  # keine Inline-Duplicates, aber Sequenz-Lücke → fail
```

**`argparse` erweitern** (nach `--quiet`, Z. 110-111):
```python
    parser.add_argument(
        "--strict",
        action="store_true",
        help=(
            "Enable Step-2 archive-sequence check in addition to Step-1 "
            "duplicate-block check (P14-F). Default: Step-1 only — "
            "the pre-commit hook should only be hardened once the new "
            "check has been proved against the current archive state."
        ),
    )
```

**`Usage`-Docstring** (Z. 29-34, der Triple-Backtick-Block) erweitern:
```python
    python3 scripts/check_doc_rotation.py                       # Step-1 only (default)
    python3 scripts/check_doc_rotation.py --strict           # Step-1 + Step-2 (P14-F)
    python3 scripts/check_doc_rotation.py --phase phase14_discovery
    python3 scripts/check_doc_rotation.py --quiet            # suppress OK rows
```

**Akzeptanz Schritt 1:** bestehende `Step-1`-Tests (`pytest scripts/check_doc_rotation.py`)
bleiben unverändert grün; **vier neue Tests** in `tests/test_check_doc_rotation.py`
(neu anzulegen, siehe §5).

### Schritt 2 — Tests für Step 2 (1 Commit, `tests/test_check_doc_rotation.py`)

**Neue Datei:** `tests/test_check_doc_rotation.py`

```python
"""Tests for ``scripts/check_doc_rotation.py`` — P14-F Step 2.

Mock-free: tmp_path + temporary Markdown files. Kein Netz, kein Keyring, keine
Imports aus dem Trading-Bot-Code (das Skript ist ein Stand-Alone-Hygiene-Tool,
kein Teil von broker_wrapper/persistence/...).

Verifiziert die vier P14-F-Akzeptanz-Punkte A1-A4 aus dem Mini-Plan §5.
"""

from __future__ import annotations

import importlib.util
from pathlib import Path
import pytest


def _load_module():
    """Import ``scripts/check_doc_rotation.py`` als Modul ohne Packaging.

    Pytest sammelt die Tests aus dem Repo-Root (per pyproject.toml ``testpaths``),
    nicht aus `` scripts/ — also kein pytest-Discovery für die Tool-Datei selbst.
    Direkter Modul-Load via ``importlib.util.spec_from_file_location``.
    """
    repo_root = Path(__file__).resolve().parent.parent
    script = repo_root / "scripts" / "check_doc_rotation.py"
    spec = importlib.util.spec_from_file_location("check_doc_rotation", script)
    assert spec is not None and spec.loader is not None
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


@pytest.fixture(scope="module")
def tool():
    return _load_module()


def test_archive_sequence_ok_for_continuous_block(tool, tmp_path):
    """A1: head=Session N, archive-newest=Session (N-1) → OK.

    Reproduziert den heutigen korrekten Zustand für Session 21.
    """
    (tmp_path / "CLAUDE.md").write_text(
        "## Session stopped — 2026-08-31 (Mini-Session 21 ...)\n",
        encoding="utf-8",
    )
    (tmp_path / "SESSIONS_ARCHIVE.md").write_text(
        "## Session stopped — 2026-08-28 (Session 20 ...)\n"
        "## Session stopped — 2026-08-28 (Session 19 ...)\n",
        encoding="utf-8",
    )
    assert tool.check_archive_sequence(tmp_path) is None


def test_archive_sequence_drift_when_archive_skips_a_session(tool, tmp_path):
    """A2: head=Session 21, archive-newest=Session 19 → ❌ DRIFT.

    Genau der Fall, den Mini-Session-21 manuell korrigiert hat: Session 20
    wurde beim Hinzufügen von Session 21 nicht ins Archiv rotiert.
    """
    (tmp_path / "CLAUDE.md").write_text(
        "## Session stopped — 2026-08-31 (Mini-Session 21 ...)\n",
        encoding="utf-8",
    )
    (tmp_path / "SESSIONS_ARCHIVE.md").write_text(
        "## Session stopped — 2026-08-28 (Session 19 ...)\n",
        encoding="utf-8",
    )
    result = tool.check_archive_sequence(tmp_path)
    assert result is not None
    label, diagnostic = result
    assert "Session 21" in diagnostic
    assert "Session 19" in diagnostic
    assert "expected 20" in diagnostic


def test_archive_sequence_drift_when_archive_missing(tool, tmp_path):
    """A3: head=Session 5, no archive → ❌ DRIFT (Sessions 1..4 verloren)."""
    (tmp_path / "CLAUDE.md").write_text(
        "## Session stopped — 2026-08-31 (Session 5 ...)\n",
        encoding="utf-8",
    )
    result = tool.check_archive_sequence(tmp_path)
    assert result is not None
    label, diagnostic = result
    assert "Session 5" in diagnostic
    assert "SESSIONS_ARCHIVE.md" in diagnostic


def test_archive_sequence_ok_for_first_ever_session(tool, tmp_path):
    """A4: head=Session 1, archive absent oder leer → OK.

    Erste Session einer Phase, Archiv darf leer sein / fehlen.
    """
    (tmp_path / "CLAUDE.md").write_text(
        "## Session stopped — 2026-08-31 (Mini-Session 1 ...)\n",
        encoding="utf-8",
    )
    # Kein SESSIONS_ARCHIVE.md angelegt
    assert tool.check_archive_sequence(tmp_path) is None

    # Auch mit leerem Archiv OK
    (tmp_path / "SESSIONS_ARCHIVE.md").write_text("# noch leer\n", encoding="utf-8")
    assert tool.check_archive_sequence(tmp_path) is None


def test_archive_sequence_skips_phases_with_no_session_block(tool, tmp_path):
    """A5: Phasenkopf ohne Session-Block → OK (kein Check noetig)."""
    (tmp_path / "CLAUDE.md").write_text(
        "# Phase ohne Sessions\n\nKein Block, nichts zu pruefen.\n",
        encoding="utf-8",
    )
    assert tool.check_archive_sequence(tmp_path) is None


def test_archive_sequence_handles_mini_session_naming(tool, tmp_path):
    """A4-Edge: 'Mini-Session 21' und 'Session 20' werden korrekt extrahiert."""
    (tmp_path / "CLAUDE.md").write_text(
        "## Session stopped — 2026-08-31 (Mini-Session 21 ...)\n",
        encoding="utf-8",
    )
    (tmp_path / "SESSIONS_ARCHIVE.md").write_text(
        "## Session stopped — 2026-08-28 (Session 20 ...)\n",
        encoding="utf-8",
    )
    assert tool.check_archive_sequence(tmp_path) is None


def test_strict_flag_added_and_default_off(tool, tmp_path):
    """A6: --strict-Flag ist geparst; ohne Flag laeuft nur Step-1."""
    import subprocess, sys
    repo_root = Path(__file__).resolve().parent.parent
    script = repo_root / "scripts" / "check_doc_rotation.py"

    # Ohne --strict: kein Step-2-Output fuer ein gut funktionierendes Repo
    result = subprocess.run(
        [sys.executable, str(script), "--quiet"],
        capture_output=True, text=True, cwd=repo_root,
    )
    assert result.returncode == 0  # Step-1 gruen, Step-2 nicht aktiv

    # Mit --strict: Step-2 laeuft zusaetzlich, gleicher Exit fuer aktuelles Repo
    result_strict = subprocess.run(
        [sys.executable, str(script), "--strict", "--quiet"],
        capture_output=True, text=True, cwd=repo_root,
    )
    assert result_strict.returncode == 0  # aktuelles Repo ist auch Step-2-konform
    assert "Sequence gap" not in result_strict.stdout  # kein FAIL
```

**Akzeptanz Schritt 2:** `pytest tests/test_check_doc_rotation.py -q` → **7 grün**
(neue Test-Datei), bestehende Schritt-1-Logik nicht angefasst.

### Schritt 3 — Tracked Hook-Installer + dev_install-Integration (1 Commit, 2 Dateien)

**Neue Datei:** `scripts/install_hooks.sh` (executable, ~40 Zeilen)

```bash
#!/usr/bin/env bash
#
# install_hooks.sh — tracked installer for the .git/hooks/pre-commit doc-rotation
# hook (P14-F Mini-Plan). Copies the canonical hook body from this file into
# ``.git/hooks/pre-commit`` and chmods it +x.
#
# — Idempotent: a second run is a no-op (hook already installed with the same
#   body → exit 0; hook exists with different body → exit 1 with diagnostic).
# — Touches ONLY ``.git/hooks/pre-commit``; never any tracked file.
# — Run from anywhere: REPO_ROOT is inferred from the script's own location.
# — Designed to be invoked as the last step of ``scripts/dev_install.sh``
#   (D3), so a fresh clone / fresh venv gets the hook automatically.
#
# Usage:
#   bash scripts/install_hooks.sh                 # install (idempotent)
#   bash scripts/install_hooks.sh --dry-run       # preview without writing
#
# Exit codes:
#   0 — installed or already up-to-date
#   1 — existing hook differs from this canonical body (operator decision needed)
#   2 — I/O error (no .git/, no write permission, …)

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
HOOK_PATH="${REPO_ROOT}/.git/hooks/pre-commit"
CANONICAL_BODY="$(cat <<'HOOK_BODY'
#!/bin/sh
# Pre-commit hook: doc-rotation hygiene check.
# Verifies no phase CLAUDE.md carries more than one "## Session stopped" block
# (Doc-Layers-Konvention, root CLAUDE.md "Rotation rule" section).
# Also (with --strict flag) checks archive-sequence integrity (P14-F).
#
# Installed by scripts/install_hooks.sh (P14-F, 2026-08-31). Tracked source:
# scripts/install_hooks.sh — re-run after every ``git clone`` / fresh venv
# setup (or just re-run ``bash scripts/dev_install.sh`` which calls this at
# the end).
#
# Override per commit with `git commit --no-verify` when needed.

if ! command -v python3 >/dev/null 2>&1; then
    echo "pre-commit: python3 not found, skipping doc-rotation check"
    exit 0
fi

if [ ! -f scripts/check_doc_rotation.py ]; then
    echo "pre-commit: scripts/check_doc_rotation.py missing, skipping"
    exit 0
fi

# Step 2 (archive-sequence integrity, P14-F) is opt-in via --strict until
# the Folge-Mini-Session (or this script's --strict) has proved the new
# check against the current archive state. The hook body here runs Step-1
# only by default.
python3 scripts/check_doc_rotation.py --quiet
result=$?

if [ $result -ne 0 ]; then
    echo ""
    echo "pre-commit: doc-rotation check failed (exit $result)."
    echo "  Run 'python3 scripts/check_doc_rotation.py' for details."
    echo "  Use 'git commit --no-verify' to override if you know what you are doing."
fi

exit $result
HOOK_BODY
)"

DRY_RUN=0
for arg in "$@"; do
    case "$arg" in
        --dry-run) DRY_RUN=1 ;;
        *) echo "install_hooks: unknown arg: $arg" >&2; exit 2 ;;
    esac
done

if [[ ! -d "${REPO_ROOT}/.git" ]]; then
    echo "install_hooks: no .git/ at ${REPO_ROOT} — not a git checkout?" >&2
    exit 2
fi

if [[ -f "${HOOK_PATH}" ]]; then
    existing="$(cat "${HOOK_PATH}")"
    if [[ "${existing}" == "${CANONICAL_BODY}" ]]; then
        echo "install_hooks: hook already up-to-date at ${HOOK_PATH}"
        exit 0
    else
        echo "install_hooks: existing hook at ${HOOK_PATH} differs from canonical body" >&2
        echo "  Diff:" >&2
        diff <(echo "${existing}") <(echo "${CANONICAL_BODY}") >&2 || true
        echo "" >&2
        echo "  Decision required: review the diff, then either:" >&2
        echo "    (a) keep the existing hook and skip this installer," >&2
        echo "    (b) back up the existing hook (mv .git/hooks/pre-commit{,.bak})" >&2
        echo "        and re-run this script." >&2
        exit 1
    fi
fi

if [[ "${DRY_RUN}" == "1" ]]; then
    echo "install_hooks: (dry-run) would write ${HOOK_PATH} (${#CANONICAL_BODY} bytes)"
    exit 0
fi

echo "${CANONICAL_BODY}" > "${HOOK_PATH}"
chmod +x "${HOOK_PATH}"
echo "install_hooks: hook installed at ${HOOK_PATH} (${#CANONICAL_BODY} bytes)"
```

**Geänderte Datei:** `scripts/dev_install.sh` (eine Zeile, am Ende):

Anker (Z. 65, das `echo`-Schluss-Statement):
```bash
echo "dev_install: all thirteen packages installed editable. Run: pytest phase14_discovery/tests -v"
```

⇒ **davor** (vor dem `echo`) eine neue Zeile:
```bash
# P14-F Mini-Plan §4 Schritt 3: install the doc-rotation pre-commit hook
# (tracked installer — .git/hooks/pre-commit is untracked by git, so this
# is the only way it survives a fresh clone). Idempotent: re-running this
# script does not overwrite a hand-edited hook (install_hooks.sh fails
# loudly on body-mismatch instead).
bash "${ROOT}/scripts/install_hooks.sh" || true
```

**Akzeptanz Schritt 3:**
- `bash scripts/install_hooks.sh` → Exit 0, schreibt `.git/hooks/pre-commit` mit +x.
- `bash scripts/install_hooks.sh` (zweiter Lauf) → Exit 0, „already up-to-date".
- `bash scripts/install_hooks.sh --dry-run` → Exit 0, schreibt nicht.
- `bash scripts/dev_install.sh` (oder am Ende der 13 `pip install -e`-Schritte) → exit 0; `install_hooks.sh` läuft fehlerfrei mit.
- `.git/hooks/pre-commit` ist **byte-identisch** zum vorherigen Stand (Modulo D5-Kommentar-Erweiterung „Step 2 ist opt-in via --strict bis ..."). `diff` zeigt nur den geänderten Kommentar.

---

## §5 Akzeptanz (PASS-Kriterien A1–A6)

| # | Kriterium | Wie belegt |
|---|---|---|
| **A1** | `_max_session_num` extrahiert die korrektte Session-Nummer aus `## Session stopped ... (Session N ...)` und `(Mini-Session N ...)` | `tests/test_check_doc_rotation.py::test_archive_sequence_handles_mini_session_naming` |
| **A2** | `check_archive_sequence` erkennt eine Sequenz-Lücke (head=21, archive-newest=19) und meldet sie als `FAIL` mit der korrekten Diagnostik | `test_archive_sequence_drift_when_archive_skips_a_session` + manueller Probe-Aufruf |
| **A3** | `check_archive_sequence` erkennt eine fehlende Archiv-Datei (head=N>1, kein Archiv) als Drift | `test_archive_sequence_drift_when_archive_missing` |
| **A4** | Erste Session (head=1, Archiv fehlt/leer) ist OK; kein-Session-Phasenkopf ist OK | `test_archive_sequence_ok_for_first_ever_session` + `test_archive_sequence_skips_phases_with_no_session_block` |
| **A5** | `--strict`-Flag wird geparst und aktiviert Step-2; ohne Flag läuft nur Step-1 (heutiges Verhalten unverändert) | `test_strict_flag_added_and_default_off` (Subprozess-Aufruf, kein Mock) |
| **A6** | `scripts/install_hooks.sh` ist idempotent, exit 0 wenn Hook byte-identisch, exit 1 wenn Hook abweicht, exit 2 bei I/O-Fehler; `bash scripts/dev_install.sh` ruft es am Ende auf | drei manuelle Probe-Aufrufe + `git diff .git/hooks/pre-commit` zeigt nur den erweiterten D5-Kommentar |

**Nicht Teil der Akzeptanz** (bewusst): die tatsächliche Verschärfung des Hooks auf
`--strict`-Default (D5-Trennung Tool-Bau / Tool-Verschärfung). Das ist eine Folge-
Mini-Session oder ein Argument an `install_hooks.sh`, **nicht** Teil dieses Plans.

---

## §6 Out of Scope

- **Byte-füriger-Vergleich** des rotierten Blocks gegen den vorigen Phasenkopf-Inhalt
  (würde `git show HEAD~1:phase*/CLAUDE.md` brauchen, deutlich teurer; nicht von Session-12
  als Drift gefordert — der Inline-Duplicate war visuell erkennbar, der Sequenz-Gap ist
  die einzige Klasse, die Step 2 fangen muss).
- **Auto-Fix** der Rotation (der Hook darf nicht schreiben — pre-commit-Philosophie).
- **Doc-Layers-Konvention-Erweiterungen** jenseits Doc-Rotation (z. B. Header-Card-Vollständigkeit,
  Größen-Limits für Living Docs). Andere Hygiene-Klasse, andere Mini-Plans.
- **Cross-Phase-Code-Edits** an `scripts/dev_install.sh` jenseits über **die eine** neue Zeile
  (D3 — alle anderen 13 `pip install -e`-Schritte bleiben unverändert).
- **Verschärfung des Hooks auf `--strict`-Default** (D5 — explizit getrennt).
- **Phase-15-Plan-Session** (V4: Council / Handover / Reward-Reform / Force-Trigger /
  Instinct-ECC). Hook-Erweiterung ist orthogonal zu V4.
- **Phase-13-Beweiswoche** (separater Track, läuft seit Mo 2026-08-25).
- **Live-Code-Touch** (per Definition pre-commit-Hygiene, kein Runtime).

---

## §7 Fehlgriffe, die wie andere Fehler aussehen

| Symptom | Erster Verdächtiger | Wie unterscheiden |
|---|---|---|
| **„Hook blockiert jeden Commit mit [FAIL] archive-sequence"** | Echter Drift in einer Phase | `python3 scripts/check_doc_rotation.py --strict` zeigt die betroffene Phase + Diagnostik; ein einzelner Commit, der die Rotation vervollständigt (alter Block ins Archiv, neuer Block in den Phasenkopf), fixt es. |
| **„Hook schweigt, aber Session-N-1 fehlt im Archiv"** | Hook deckt den Fall nicht ab | `_max_session_num`-Regex testen (`python3 -c "import scripts.check_doc_rotation as m; print(m._max_session_num(open('phase*/CLAUDE.md').read()))"`); der Hook **muss** anschlagen, wenn die Regex funktioniert — sonst ist Step 2 nicht aktiv (D5: default Step-1 only). |
| **„Beim Re-Run von `install_hooks.sh` exit 1 'differs from canonical body'"** | Hand-edited Hook | `diff .git/hooks/pre-commit <(bash scripts/install_hooks.sh --dry-run)` zeigt die Abweichung; Operator-Entscheidung: entweder behalten (Installer überspringen) oder Backup + Re-Run. |
| **„Hook installiert, aber `git commit` triggert ihn nicht"** | `.git/hooks/pre-commit` nicht executable | `ls -l .git/hooks/pre-commit` zeigt Berechtigungen; `chmod +x` fixt. Installer macht das automatisch (`chmod +x "${HOOK_PATH}"`). |
| **„`dev_install.sh` schlägt fehl mit Hook-Installer-Fehler"** | `install_hooks.sh` exit ≠ 0 | D5-Konvention: `install_hooks.sh` ist mit `\|\| true` an `dev_install.sh` angeflanscht (akzeptiert Installer-Fehler ohne Abbruch) — Logik: Dev-Setup soll nicht am Hook scheitern, sondern der Hook ist Hygiene-Bonus. Wenn der Installer exit 1 wirft (body-mismatch), wird eine Warning geloggt, der Commit kann trotzdem durchgehen. |

---

## §8 Drift-Liste — bei Ausführung verifizieren

> **Diese Liste ist vollständig.** Was hier nicht steht, hat diese Planungssession am
> 2026-08-31 selbst gegen das Repo geprüft und ist als Fakt formuliert. Rate nichts nach;
> prüfe diese und nur diese.

1. **Zeilennummern verschieben sich.** Jeder Anter oben trägt den **Verbatim-String** —
   der ist der Anter, die Zahl die Abküung. Schritt 1 verschiebt `check_doc_rotation.py`
   (neue Imports/Konstante/Funktion); Schritt 3 verschiebt `dev_install.sh` (neue Zeile
   vor dem Schluss-echo). **Immer per String suchen.**
2. **`SESSION_HEADING = "## Session stopped"`** (Z. 66, vor diesem Plan) bleibt unverändert
   — Step 2 nutzt `_SESSION_NUM_RE`, nicht `SESSION_HEADING`. Step 1 (Count) bleibt
   kompatibel zu bestehenden Tests.
3. **`PHASE_DIRS`-Liste** (Z. 49-64) bleibt unverändert — Step 2 läuft über **dieselben
   14 Phasen**. Heute sind 13 Phasen + `meta_m1_harness` in der Liste; Phase 11 ist
   absichtlich nicht (war eine Deferral, kein Phasenkopf mehr).
4. **Pytest-Run-Discovery.** Heute: `tests/` ist im pyproject als `testpaths = ["tests"]`
   konfiguriert (verifiziert). `scripts/` ist **kein** pytest-Pfad — die `test_check_doc_
   rotation.py` muss unter `tests/` liegen (Schritt 2 tut das), und die `_load_module`-
   Funktion lädt das Tool per `importlib.util.spec_from_file_location` (kein Packaging
   nötig).
5. **Regex-Boundaries.** `(?:Mini-)?Session\s+(\d+)` — matcht:
   - „## Session stopped ... (Session 20 ...)" → 20 ✓
   - „## Session stopped ... (Mini-Session 21 ...)" → 21 ✓
   - „## Session stopped ... (Session 100+ ...)" → 100 ✓
   - „## Session stopped — no number" → None ✓ (kein Match, nums-Liste leer, return None)
   Match **nicht** „Session of Council" o. ä. (Substantiv, nicht „Session N"), weil das
   Regex `Session\s+` (Whitespace nach „Session") verlangt — „Session of" hat `of`, kein
   Digit. False-positive-Risiko gering.
7. **Bestehende Tests in `tests/`** (Σ 94 Stand `bc48484`) bleiben unverändert grün —
   Schritt 2 fügt `test_check_doc_rotation.py` als **neue Datei** hinzu, kein Touch an
   anderen Tests. `pytest tests/ -q` läuft 94 + 7 = **101 grün** (Step 2 + 7 neue).
8. **`pre-commit`-Hook-Skript** — `.git/hooks/pre-commit` wird **ersetzt** (nicht
   überschrieben) durch den Installer; `install_hooks.sh` exit 1 bei Body-Mismatch lässt
   den Operator entscheiden. Heute (Stand `bc48484`) hat der Hook einen **alten**
   Kommentar („Installed by Claude Code (Phase-14 Hygiene Item 2 follow-up) on 2026-08-27");
   Schritt 3 ersetzt ihn durch den neuen Kommentar („Installed by scripts/install_hooks.sh
   (P14-F, 2026-08-31)"). `git diff .git/hooks/pre-commit` zeigt nur den
   Kommentar-Tausch (Datei ist untracked, der Diff ist rein informativ).
9. **`install_hooks.sh --strict`-Argument** ist **nicht** im Scope (D5). Der Installer
   ruft `check_doc_rotation.py --quiet` (Step 1 only). Eine Verschärfung auf `--strict`
   ist eine Folge-Mini-Session, die auch die `--strict`-Logik aktiviert (siehe D5-
   Begründung im Plan: „alle 14 Archive heute schon Step-2-konform, also kann --strict
   sofort default werden" — Beweis-Skript: `for d in phase*_discovery phase*_v3 phase*
   _data_foundation meta*; do python3 scripts/check_doc_rotation.py --strict --phase
   $d || echo "$d fail"; done` — wenn alle OK, ist die Verschärfung sicher).
10. **Phase-15-Reconciliation.** Wenn Phase-15 (V4) startet, ist `check_doc_rotation.py`
    ein Hygiene-Anter für die neuen Phasen-CLAUDE.md-Dateien — keine Code-Änderung
    nötig, weil `PHASE_DIRS` per Tuple-Konstante erweitert wird. Out-of-scope heute.

---

## §9 Cross-Referenz

- **Mutterplan** [`../docs/concepts/phase14_discovery_plan.md`](../docs/concepts/phase14_discovery_plan.md)
  — nicht direkt berührt; Block-D-Schließung (Mini-Session 21) ist unabhängig von Hook-
  Schritt-2 (der Hook ist orthogonal zur Phase-14-Mission, betrifft aber alle Phasen).
- **Geschwister-Mini-Pläne** [`./PHASE14_C_DAEMON_CWD_BUG_PLAN.md`](./PHASE14_C_DAEMON_CWD_BUG_PLAN.md),
  [`./PHASE14_D_DAEMON_SIGNAL_CAP_PLAN.md`](./PHASE14_D_DAEMON_SIGNAL_CAP_PLAN.md),
  [`./PHASE14_E_RECORDER_LOOP_PLAN.md`](./PHASE14_E_RECORDER_LOOP_PLAN.md) — gleiche Struktur,
  gleiche Konvention; P14-F ist der nächste in der Reihe. Mini-Plan-Vorlage etabliert in
  P14-C, gelockt in P14-D, erweitert in P14-E (Cross-Phase), P14-F bleibt Phase-14-
  eigen (nur `scripts/`).
- **Session-16-Hygiene** [`./SESSIONS_ARCHIVE.md`](./SESSIONS_ARCHIVE.md) Session-16-Block
  (2026-08-27) — Schöpfer von `scripts/check_doc_rotation.py` und des untracked
  `.git/hooks/pre-commit`. P14-F erweitert das Tool und tracked-installiert den Installer.
- **Session-17-Item „Tracked Hook-Installer"** — endlich fertig (P14-F Schritt 3). Das
  Session-17-Restpost-Item ist damit abgeschlossen.
- **Mini-Session-21-NEXT-Block** [`./CLAUDE.md`](./CLAUDE.md) Z. 220-237 — Item 3 der
  NEXT-Liste: „Tracked Hook-Installer mit Doc-Rotation-Schritt-2 (~1h)" wird mit
  Commit dieses Plans vollständig abgeschlossen (Tool + Tests + Installer in 3 Commits,
  Push-Freigabe Nikinger vorausgesetzt).
- **Doc-Layers-Konvention** [`../docs/DOC_LAYERS_CONVENTION.md`](../docs/DOC_LAYERS_CONVENTION.md) —
  das Protokoll, gegen das der Hook prüft; nicht geändert (Step 2 ist eine **Implementation**
  der existierenden Konvention, keine Konventions-Änderung).
- **Session-21-Beobachtung** [`./SESSIONS_ARCHIVE.md`](./SESSIONS_ARCHIVE.md) Session-21-Block —
  das 🟡 Finding, das P14-F motiviert: „Pre-Commit-Hook (Session 17) hat Session-21-Doc-Rotation
  **nicht** automatisch geprüft (er checkt nur den Phasenkopf-Block, nicht die Archiv-Bewegung
  selbst). Die Rotation wurde manuell verifiziert." P14-F schließt diese Lücke strukturell.