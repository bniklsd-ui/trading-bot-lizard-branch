"""`assess_window` — fensterweite Abdeckungsprüfung (Phase 13 §6 Step A1, §5.1).

Reine Funktion, kein I/O. Beantwortet: **deckt das Archiv das Fenster genau dieses
Trades dicht genug ab?** — mit *zwei* Schwellen, weil eine einzelne nicht reicht:

- Dichte: ``present / expected`` >= ``MIN_WINDOW_RATIO``
- Lücke: kein zusammenhängender Run fehlender Schritte länger als ``MAX_WINDOW_GAP_MIN``

Eine Lücke *mitten* im Fenster erzeugt heute in ``resolve_paper_trade`` eine
*erfundene* ``TIME_STOP``-Zeile (Plan §4 F3) — weder eine Schwanz-Prüfung noch eine
reine Quote-Dichte kann das sehen (300-Min-Fenster mit 20-Min-Loch = Quote 0,93).
Dieser Guard sitzt **vor** der Auflösefunktion; er ersetzt sie nicht.

Zeitstempel werden lexikalisch verglichen, wo es geht (Repo-Konvention,
``paper.py:240``-Docstring). Für die Gap-Rechnung wird ein ``datetime``-Parse nötig;
dafür ``_parse`` aus ``archive.py`` **lokal** dupliziert — keine
Cross-Phase-Import-Abhängigkeit (Phasen-Isolation, Plan §6 A1).
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Sequence


# v1-Kalibrierungsknöpfe — Plan §5.1, §6 A1. Block A misst die reale Verteilung und
# justiert; vorerst sind das absichtliche Heuristiken, keine versteckten Konstanten.
MIN_WINDOW_RATIO: float = 0.90
MAX_WINDOW_GAP_MIN: int = 5


@dataclass(frozen=True)
class WindowCoverage:
    """Ergebnis einer Fenster-Abdeckungsprüfung (§5.1)."""

    covered: bool
    present: int           # vorhandene distinkte Bar-Minuten im Fenster
    expected: int          # naiv erwartete Bar-Anzahl (Wanduhr, keine Session-Kalender)
    ratio: float           # present / expected, auf 1.0 gedeckelt
    largest_gap_min: int   # größte zusammenhängende Lücke in Minuten
    reason: str | None     # None wenn covered; sonst 'empty' | 'sparse' | 'gap'


def _parse(ts_utc: str) -> datetime:
    """Lokale Kopie von ``archive._parse`` — Phasen-Isolation statt Cross-Phase-Import."""
    normalized = ts_utc.replace("Z", "+00:00") if ts_utc.endswith("Z") else ts_utc
    dt = datetime.fromisoformat(normalized)
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt


def assess_window(
    timestamps: Sequence[str],
    start_utc: str,
    end_utc: str,
    resolution_minutes: int,
    *,
    min_ratio: float = MIN_WINDOW_RATIO,
    max_gap_min: int = MAX_WINDOW_GAP_MIN,
) -> WindowCoverage:
    """Prüft, ob ``timestamps`` das Fenster ``[start_utc, end_utc)`` dicht genug abdecken.

    ``start`` inklusiv, ``end`` exklusiv (analog ``BarArchive.window``).
    Zeitstempel außerhalb des Fensters werden ignoriert; Duplikate zählen einmal.

    ``reason``-Semantik — bei mehreren zutreffenden Gründen gewinnt der
    spezifischste: ``empty`` > ``gap`` > ``sparse``.
    """
    start_dt = _parse(start_utc)
    end_dt = _parse(end_utc)
    expected = max(
        0, int((end_dt - start_dt).total_seconds() // 60 // resolution_minutes)
    )

    # Distinkte Zeitstempel im Fenster (ISO 8601 UTC ms 'Z' sind lexikalisch sortierbar).
    marks_dt: list[datetime] = []
    seen: set[str] = set()
    for ts in timestamps:
        if not ts or ts in seen:
            continue
        if ts < start_utc or ts >= end_utc:
            continue
        seen.add(ts)
        marks_dt.append(_parse(ts))
    marks_dt.sort()
    present = len(marks_dt)

    if expected == 0 or present == 0:
        return WindowCoverage(False, present, expected, 0.0, 0, "empty")

    # Größter Run fehlender Schritte im Fenster, in Minuten.
    # Ränder zählen mit: die erste fehlende Lücke liegt zwischen start_dt und der
    # ersten Bar, die letzte zwischen der letzten Bar und end_dt.
    max_gap_steps = (marks_dt[0] - start_dt).total_seconds() // 60 // resolution_minutes
    for i in range(1, present):
        gap_steps = (
            (marks_dt[i] - marks_dt[i - 1]).total_seconds() // 60 // resolution_minutes - 1
        )
        if gap_steps > max_gap_steps:
            max_gap_steps = gap_steps
    end_gap_steps = (
        (end_dt - marks_dt[-1]).total_seconds() // 60 // resolution_minutes - 1
    )
    if end_gap_steps > max_gap_steps:
        max_gap_steps = end_gap_steps
    largest_gap_min = int(max_gap_steps * resolution_minutes)

    ratio = min(1.0, present / expected)

    if largest_gap_min > max_gap_min:
        reason: str | None = "gap"
    elif ratio < min_ratio:
        reason = "sparse"
    else:
        reason = None

    return WindowCoverage(
        reason is None, present, expected, ratio, largest_gap_min, reason
    )
