"""One-time database initialization.

Creates the runtime ``data/`` directories, applies all migrations, and seeds the
default ``ig_config_state`` rows. Idempotent — safe to run repeatedly.

    python scripts/init_db.py
    python scripts/init_db.py --db-path /custom/trading_bot.sqlite --state-dir /custom/state

Defaults place the DB and JSON state under a root-level ``data/`` directory
(``<repo_root>/data/``), shared by later phases and gitignored.
"""

from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path

# Make the `persistence` package importable when run as a script.
_PACKAGE_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_PACKAGE_ROOT))

from persistence.db import Database  # noqa: E402
from persistence.state import StateManager  # noqa: E402

_REPO_ROOT = _PACKAGE_ROOT.parent
_DEFAULT_DB_PATH = _REPO_ROOT / "data" / "trading_bot.sqlite"
_DEFAULT_STATE_DIR = _REPO_ROOT / "data" / "state"

log = logging.getLogger("init_db")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Initialize the Phase 2 persistence layer.")
    parser.add_argument(
        "--db-path", default=str(_DEFAULT_DB_PATH),
        help=f"SQLite database path (default: {_DEFAULT_DB_PATH})",
    )
    parser.add_argument(
        "--state-dir", default=str(_DEFAULT_STATE_DIR),
        help=f"Directory for JSON state files (default: {_DEFAULT_STATE_DIR})",
    )
    args = parser.parse_args(argv)

    logging.basicConfig(
        level=logging.INFO, format="%(levelname)s %(message)s", stream=sys.stderr
    )

    db_path = Path(args.db_path)
    db_path.parent.mkdir(parents=True, exist_ok=True)

    with Database(str(db_path)) as db:
        version = db.run_migrations()
        config = db.get_all_config()
    log.info("Database ready at %s (schema version %d)", db_path, version)
    log.info("Seeded config keys: %s", ", ".join(sorted(config)))

    # Ensure the JSON state directory exists (no files written yet).
    StateManager(args.state_dir)
    log.info("State directory ready at %s", args.state_dir)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
