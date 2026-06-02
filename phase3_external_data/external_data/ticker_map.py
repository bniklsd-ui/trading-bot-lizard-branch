"""IG-epic → yFinance-symbol resolution for the external-data layer.

:class:`TickerMapper` is the first thing the fetcher calls in every method
(concept §11 step 1): it turns an IG epic such as ``"IX.D.DAX.IFMM.IP"`` into
the yFinance symbol ``"^GDAXI"``. An unmapped epic is a programmer error, so
:meth:`epic_to_yf` raises :class:`EpicNotMappedError` (which the fetcher does
**not** catch) rather than guessing.

It also owns the **ETF-volume-proxy hook** (concept decision §0.1): ``^GDAXI``
reports no native volume, so ``_VOLUME_MAP`` is empty by default and the volume
indicator degrades cleanly (``volume_available=False``). A bot config can later
register a proxy (e.g. iShares Core DAX ``"EXS1.DE"``) with no refactoring.

The class-level ``_MAP`` / ``_VOLUME_MAP`` are **defaults**: ``__init__`` copies
them into per-instance dicts so that :meth:`register` / :meth:`register_volume_proxy`
mutate only this instance and never leak across mappers.
"""

from __future__ import annotations

from .exceptions import EpicNotMappedError


class TickerMapper:
    """Maps IG epics to yFinance symbols (and optional ETF-volume proxies).

    Lookups are exact-match (case-sensitive): IG epics are fixed uppercase
    identifiers, so a differently-cased string is treated as unmapped.
    """

    _MAP: dict[str, str] = {
        "IX.D.DAX.IFMM.IP": "^GDAXI",   # Deutschland 40 Kassa (confirmed Phase 1)
        "IX.D.DAX.DAILY.IP": "^GDAXI",
        "CS.D.EURUSD.MINI.IP": "EURUSD=X",
        "IX.D.DOW.DAILY.IP": "^DJI",
    }
    _VOLUME_MAP: dict[str, str] = {}  # empty default → ^GDAXI degrades (no proxy)

    def __init__(self) -> None:
        """Initialise with per-instance copies of the class-level defaults."""
        self._map: dict[str, str] = dict(self._MAP)
        self._volume_map: dict[str, str] = dict(self._VOLUME_MAP)

    def epic_to_yf(self, epic: str) -> str:
        """Resolve an IG epic to its yFinance symbol.

        Args:
            epic: The IG epic, e.g. ``"IX.D.DAX.IFMM.IP"``.

        Returns:
            The yFinance symbol, e.g. ``"^GDAXI"``.

        Raises:
            EpicNotMappedError: If no symbol is registered for ``epic``.
        """
        try:
            return self._map[epic]
        except KeyError:
            raise EpicNotMappedError(f"no yFinance symbol mapped for epic {epic!r}")

    def epic_to_volume_yf(self, epic: str) -> str | None:
        """Resolve the ETF-volume-proxy symbol for an epic, if one is registered.

        Args:
            epic: The IG epic.

        Returns:
            The volume-proxy yFinance symbol, or ``None`` when no proxy is
            registered (the volume indicator then degrades gracefully).
        """
        return self._volume_map.get(epic)

    def register(self, epic: str, yf_symbol: str) -> None:
        """Register or override an epic → yFinance-symbol mapping (this instance).

        Args:
            epic: The IG epic.
            yf_symbol: The yFinance symbol to map it to.
        """
        self._map[epic] = yf_symbol

    def register_volume_proxy(self, epic: str, volume_yf_symbol: str) -> None:
        """Register an ETF-volume-proxy symbol for an epic (this instance).

        Caveat: an ETF's volume reflects **ETF trading interest**, not the
        underlying index's volume. It is usable as an anomaly signal (unusual
        interest today vs. its own history), **not** as an exact volume figure
        for the index.

        Args:
            epic: The IG epic whose index lacks native volume (e.g. ``^GDAXI``).
            volume_yf_symbol: The proxy yFinance symbol, e.g. ``"EXS1.DE"``
                (iShares Core DAX).
        """
        self._volume_map[epic] = volume_yf_symbol
