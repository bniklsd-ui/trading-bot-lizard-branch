"""Puts meta_m1_harness/bakeoff/ on sys.path so tests can import harness_bakeoff/analyze
the same flat way the scripts import each other when run directly (no package/install needed
for this standalone operator tool)."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "bakeoff"))
