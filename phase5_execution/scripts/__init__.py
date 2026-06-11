"""Phase-5 operator scripts (composition root + smoke/live runners).

Not part of the importable ``execution`` package (excluded from the editable
install by ``pyproject.toml``'s ``include = ["execution*"]``); these are entry
points the **operator** runs. ``wiring.build_executor`` binds the real Phase-1/2/3/4
instances to the phase-isolated ``execution`` core; ``smoke_test`` / ``live_test``
drive it against IG Demo. The runtime ``execution`` package never imports anything
here.
"""

from __future__ import annotations
