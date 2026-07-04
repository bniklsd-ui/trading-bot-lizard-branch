"""Dependency wiring for Phase 4 — build a real :class:`Research` (concept §8).

This is the **only** place the phase-isolated ``research`` package is bound to
the concrete Phase-1/2/3 implementations. Every ``research/`` module types its
collaborators via local ``typing.Protocol``\\ s and imports nothing cross-phase;
here we do the ``sys.path`` bootstrap, construct the real adapters, and inject
them through the :class:`Research` constructor.

Construction touches the keyring (the Anthropic key, via the Decision-6
``research.credentials`` shim) but does **no** network call — IG ``connect`` and
the LLM SDK are both lazy (they fire inside ``Research.run``). So ``pytest`` does
not import this module (it would pull the keyring + cross-phase packages); the
operator scripts ``smoke_test.py`` / ``live_test.py`` are its only callers.

Runtime data lives under the gitignored ``<repo_root>/data/`` tree, the same
layout Phase-2 ``scripts/init_db.py`` provisions (SQLite + ``state/``) and Phase-3
uses for ``cache/``.
"""

from __future__ import annotations

import logging
import sys
from pathlib import Path

# --- sys.path bootstrap: this package + the three upstream phases ------------
_PACKAGE_ROOT = Path(__file__).resolve().parent.parent      # phase4_research/
_REPO_ROOT = _PACKAGE_ROOT.parent                           # repo root
for _p in (
    _PACKAGE_ROOT,
    _REPO_ROOT / "phase1_broker_wrapper",
    _REPO_ROOT / "phase2_persistence",
    _REPO_ROOT / "phase3_external_data",
):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

# Phase-4 (own package) — safe to import without network.
from research import EXTENDED_UNIVERSE, Research, ResearchConfig, universe_from_records  # noqa: E402
from research.credentials import get_credential  # noqa: E402  (Decision-6 shim)
from research.llm_client import LLMClient  # noqa: E402

logger = logging.getLogger(__name__)

# --- Runtime data locations (gitignored) -------------------------------------
_DATA_DIR = _REPO_ROOT / "data"
_DB_PATH = _DATA_DIR / "trading_bot.sqlite"
_STATE_DIR = _DATA_DIR / "state"
_CACHE_DIR = _DATA_DIR / "cache"
_USAGE_LOG = _STATE_DIR / "llm_usage.json"


def build_universe_from_db(db_path: str | Path | None = None) -> tuple:
    """Build the research universe from the Phase-9 (V2) ``instrument_universe`` table.

    Falls back to ``EXTENDED_UNIVERSE`` with a ``logger.warning`` if the DB is
    unreachable (Phase 9 not built/seeded yet on this checkout, wrong path, locked
    file, ...) or has no active rows — never silently, never a crash. Lazy
    cross-phase import (the ``universe`` package, Phase 9) so this module's own
    import stays network/DB-free (mirrors every other cross-phase import here).
    """
    path = Path(db_path) if db_path is not None else _DB_PATH
    try:
        from universe import UniverseStore  # noqa: PLC0415 — lazy, phase isolation

        store = UniverseStore(path)
        try:
            records = [rec.to_instrument_spec() for rec in store.active_universe()]
        finally:
            store.close()
    except Exception as exc:  # noqa: BLE001 — any DB problem is a graceful fallback, not a crash
        logger.warning(
            "build_universe_from_db: instrument_universe unreachable (%s) — "
            "falling back to EXTENDED_UNIVERSE", exc,
        )
        return EXTENDED_UNIVERSE
    return universe_from_records(records, fallback=EXTENDED_UNIVERSE)


def build_research(config: ResearchConfig | None = None) -> Research:
    """Construct a fully wired :class:`Research` against IG Demo + the real LLM.

    Builds the real Phase-1 broker (``ig_demo``), Phase-2 ``Database`` /
    ``StateManager``, Phase-3 ``MarketDataFetcher`` (with the configured volume
    proxy registered on the anchor epic), and the Phase-4 :class:`LLMClient`
    (API key from the keyring), then injects them into the orchestrator.

    No network call happens here — IG ``connect`` and the Anthropic SDK are both
    lazy and fire inside ``Research.run``. The keyring *is* read (the Anthropic
    key), so this must run with the keyring available and the demo creds seeded.

    Args:
        config: the run config; defaults to :class:`ResearchConfig` built from the
            Phase-9 (V2) DB-backed universe (:func:`build_universe_from_db`), which
            itself falls back to the v1.5 curated ``EXTENDED_UNIVERSE`` (DAX + Euro
            Stoxx 50 + CAC 40 + IBEX 35) if the ``instrument_universe`` table is
            empty/unreachable — so an unbuilt/unseeded Phase 9 on a given checkout
            behaves exactly like pre-Phase-9 (bit-identical). Pass an explicit
            ``config`` (as ``smoke_test.py``/``live_test.py`` do via ``--epic``) to
            constrain to one instrument for a deterministic single-epic test run.

    Returns:
        A ready-to-``run`` :class:`Research`.
    """
    config = config if config is not None else ResearchConfig(universe=build_universe_from_db())

    # Phase-1 broker — keyring-backed, no network at construction.
    from broker_wrapper import get_broker  # noqa: E402

    broker = get_broker("ig_demo")

    # Phase-2 persistence — on-disk SQLite + JSON state under data/.
    from persistence import Database, StateManager  # noqa: E402

    db = Database(str(_DB_PATH))
    state = StateManager(str(_STATE_DIR))

    # Phase-3 market data — register the ETF volume proxy on the anchor epic so
    # ^GDAXI does not degrade to volume_available=False (Decision 5).
    from external_data import FileCache, MarketDataFetcher, TickerMapper  # noqa: E402

    mapper = TickerMapper()
    # v1.5 (Issue C): register each curated instrument's yFinance ticker + volume proxy
    # from the typed universe (single source of truth). The DAX default is unchanged
    # (^GDAXI is already a TickerMapper built-in; the volume proxy matches the pre-v1.5
    # single registration), so the default path behaves identically.
    for spec in config.universe or ():
        if spec.yf_ticker:
            mapper.register(spec.epic, spec.yf_ticker)
        if spec.volume_proxy:
            mapper.register_volume_proxy(spec.epic, spec.volume_proxy)
    market_data = MarketDataFetcher(mapper, FileCache(str(_CACHE_DIR)))

    # Phase-4 LLM client — the single AI call site. Key from the keyring shim.
    llm = LLMClient(
        model=config.model,
        api_key=get_credential("anthropic_api_key"),
        max_tokens=config.max_tokens,
        temperature=config.temperature,
        timeout_s=config.timeout_s,
        token_meter_path=str(_USAGE_LOG),
        config=config,
    )

    return Research(broker, db, state, market_data, llm, config)
