"""OS keyring access for broker credentials.

Design intent — keep credentials out of any file an AI agent can read:

    - Production credentials live ONLY in the OS keyring
      (macOS Keychain, Windows Credential Manager, Linux Secret Service).
    - Code reads via `get_credential(name)` — no plaintext on disk, ever.
    - Credentials are seeded via `scripts/store_credential.py`,
      which prompts the human via getpass. AI never sees the input.
    - For development against a demo broker account, a separate set
      of credentials may be stored under the "demo" namespace.

What this prevents:
    - An AI agent reading config files and exfiltrating production keys.
    - Accidental commits of plaintext credentials to git.

What this does NOT prevent:
    - An AI agent that EXECUTES this code at runtime can call
      get_credential() and obtain the value in memory. Defense against
      runtime AI agency is a separate problem (human approval gates on
      order placement) and is intentionally out of scope here.
"""

from __future__ import annotations

import os
from typing import Final

try:
    import keyring  # type: ignore
    from keyring.errors import KeyringError  # type: ignore
    _KEYRING_AVAILABLE = True
except ImportError:  # pragma: no cover
    keyring = None  # type: ignore
    KeyringError = Exception  # type: ignore
    _KEYRING_AVAILABLE = False

from broker_wrapper.exceptions import CredentialNotFoundError

SERVICE_NAME: Final[str] = "tradingbot"

# Standard credential keys — keep these as constants so callers
# never have to remember the exact string.
IG_USERNAME: Final[str] = "ig_username"
IG_PASSWORD: Final[str] = "ig_password"
IG_API_KEY: Final[str] = "ig_api_key"
IG_ACCOUNT_ID: Final[str] = "ig_account_id"

# Demo namespace — non-sensitive, may also be in env vars for CI.
IG_DEMO_USERNAME: Final[str] = "ig_demo_username"
IG_DEMO_PASSWORD: Final[str] = "ig_demo_password"
IG_DEMO_API_KEY: Final[str] = "ig_demo_api_key"
IG_DEMO_ACCOUNT_ID: Final[str] = "ig_demo_account_id"


def get_credential(name: str, *, fallback_env: bool = False) -> str:
    """Read a credential from the OS keyring.

    Args:
        name: credential key (use the module-level constants).
        fallback_env: if True, fall back to environment variable
            "TRADINGBOT_<NAME_UPPER>" when the keyring entry is missing.
            Intended for CI / containers; never use for production prod keys.

    Raises:
        CredentialNotFoundError: if the credential is not present.
    """
    if _KEYRING_AVAILABLE:
        try:
            value = keyring.get_password(SERVICE_NAME, name)
            if value:
                return value
        except KeyringError as exc:
            # Keyring backend issue (e.g. headless Linux). Fall through to env.
            if not fallback_env:
                raise CredentialNotFoundError(
                    f"Keyring access failed for '{name}': {exc}"
                ) from exc

    if fallback_env:
        env_key = f"TRADINGBOT_{name.upper()}"
        env_value = os.environ.get(env_key)
        if env_value:
            return env_value

    raise CredentialNotFoundError(
        f"Credential '{name}' not found. "
        f"Run `python scripts/store_credential.py {name}` to set it."
    )


def store_credential(name: str, value: str) -> None:
    """Store a credential in the OS keyring.

    Should only be called from scripts/store_credential.py — never from
    bot code. Code that stores credentials is a security smell.
    """
    if not _KEYRING_AVAILABLE:
        raise RuntimeError(
            "keyring package not installed. Run: pip install keyring"
        )
    keyring.set_password(SERVICE_NAME, name, value)


def delete_credential(name: str) -> None:
    """Remove a credential from the OS keyring."""
    if not _KEYRING_AVAILABLE:
        raise RuntimeError("keyring package not installed.")
    try:
        keyring.delete_password(SERVICE_NAME, name)
    except keyring.errors.PasswordDeleteError:
        # Already absent — idempotent.
        pass


def check_credentials(names: list[str], *, fallback_env: bool = False) -> dict[str, bool]:
    """Return a dict of {name: is_set} without leaking values.

    Use this for startup diagnostics and CLI status output.
    """
    result = {}
    for name in names:
        try:
            get_credential(name, fallback_env=fallback_env)
            result[name] = True
        except CredentialNotFoundError:
            result[name] = False
    return result
