"""Factory for instantiating broker adapters from a config dict.

Keeps adapter construction out of the bot core. Credentials are read
from the OS keyring at this point — never passed in via config.
"""

from __future__ import annotations

from typing import Any

from broker_wrapper.adapters.base import BrokerAdapter
from broker_wrapper.adapters.ig_adapter import IGAdapter
from broker_wrapper.credentials import (
    get_credential,
    IG_USERNAME, IG_PASSWORD, IG_API_KEY, IG_ACCOUNT_ID,
    IG_DEMO_USERNAME, IG_DEMO_PASSWORD, IG_DEMO_API_KEY, IG_DEMO_ACCOUNT_ID,
)


def get_broker(name: str, config: dict[str, Any] | None = None) -> BrokerAdapter:
    """Build a configured adapter by name.

    Args:
        name: broker identifier — currently only "ig" or "ig_demo".
        config: non-secret options (timeouts, demo flag, etc).

    Credentials are pulled from the OS keyring — never passed in config.
    """
    cfg = config or {}

    if name == "ig":
        return IGAdapter(
            username=get_credential(IG_USERNAME),
            password=get_credential(IG_PASSWORD),
            api_key=get_credential(IG_API_KEY),
            account_id=get_credential(IG_ACCOUNT_ID),
            demo=False,
            request_timeout=cfg.get("request_timeout", 10.0),
            max_retries=cfg.get("max_retries", 2),
        )

    if name == "ig_demo":
        return IGAdapter(
            username=get_credential(IG_DEMO_USERNAME, fallback_env=True),
            password=get_credential(IG_DEMO_PASSWORD, fallback_env=True),
            api_key=get_credential(IG_DEMO_API_KEY, fallback_env=True),
            account_id=get_credential(IG_DEMO_ACCOUNT_ID, fallback_env=True),
            demo=True,
            request_timeout=cfg.get("request_timeout", 10.0),
            max_retries=cfg.get("max_retries", 2),
        )

    raise ValueError(
        f"unknown broker '{name}'. Supported: 'ig', 'ig_demo'. "
        "Add IBKR/Saxo adapters in a future phase."
    )
