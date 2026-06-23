"""Phase-7 credential access — the single, deliberate phase-isolation exception.

Every other module in ``reward/`` is phase-isolated: it imports **nothing** from
``broker_wrapper`` / ``research`` at module scope and duck-types its collaborators.
This shim is the one documented exception (concept Decision F, mirroring the
Phase-4 ``research.credentials`` and Phase-6 ``debate.credentials`` shims).

**Why an exception, not a duplicate:** credentials must live *only* in the OS
keyring (root ``CLAUDE.md`` Hard Rule 1). Phase 1 already owns the audited keyring
access path (``broker_wrapper.credentials.get_credential``, service
``"tradingbot"``). Re-implementing it here would mean a second, divergent
credential code path — exactly what the Hard Rule prevents. So we reuse Phase 1's
function verbatim rather than copy it.

The Phase-7 key is ``"anthropic_api_key"`` — the same secret Phase 4/6 use, because
Phase 7's lesson extraction reuses the Phase-4 ``LLMClient`` (Decision F). Seed it
once via Phase 1's helper::

    python phase1_broker_wrapper/scripts/store_credential.py anthropic_api_key

This module is imported by ``scripts/wiring.py`` (operator/live path only). Unit
tests never import it — the LLM client takes the key as a constructor argument and
is mocked, so the test suite stays keyring-free and offline.
"""

from __future__ import annotations

import sys
from pathlib import Path

# Bootstrap the Phase-1 package onto sys.path so this shim is self-contained: it
# resolves whether or not the caller already inserted the path. Repo root is three
# levels up (reward/credentials.py -> reward -> phase7_reward -> repo).
_REPO_ROOT = Path(__file__).resolve().parents[2]
_PHASE1_ROOT = _REPO_ROOT / "phase1_broker_wrapper"
if str(_PHASE1_ROOT) not in sys.path:
    sys.path.insert(0, str(_PHASE1_ROOT))

from broker_wrapper.credentials import get_credential  # noqa: E402

__all__ = ["get_credential"]
