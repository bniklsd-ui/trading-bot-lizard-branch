"""Tests for the v1.5 typed research universe (Issue C — variety).

Covers ``InstrumentSpec`` + ``load_universe`` (the validating loader) and the
``ResearchConfig`` reconciliation between the typed ``universe`` (source of truth)
and the derived ``epic_allowlist`` (backward-compat input). Pure — no network, no I/O
beyond the ``logger.warning`` a dropped entry emits.
"""

from __future__ import annotations

import dataclasses

import pytest

from research.models import (
    EXTENDED_UNIVERSE,
    InstrumentSpec,
    ResearchConfig,
    _DEFAULT_UNIVERSE,
    load_universe,
)

DAX = "IX.D.DAX.IFMM.IP"


def _spec(epic: str, **over: object) -> InstrumentSpec:
    base: dict[str, object] = dict(
        epic=epic,
        yf_ticker=None,
        volume_proxy=None,
        point_value=1.0,
        min_deal_size=0.5,
        currency="EUR",
        source="curated",
    )
    base.update(over)
    return InstrumentSpec(**base)  # type: ignore[arg-type]


# --------------------------------------------------------------------------- #
# InstrumentSpec                                                              #
# --------------------------------------------------------------------------- #
def test_instrument_spec_is_frozen() -> None:
    spec = _spec(DAX)
    with pytest.raises(dataclasses.FrozenInstanceError):
        spec.point_value = 2.0  # type: ignore[misc]


# --------------------------------------------------------------------------- #
# load_universe                                                              #
# --------------------------------------------------------------------------- #
def test_load_universe_wellformed_preserves_order() -> None:
    specs = [_spec(DAX), _spec("IX.D.STXE.IFMM.IP")]
    out = load_universe(specs)
    assert isinstance(out, tuple)
    assert [s.epic for s in out] == [DAX, "IX.D.STXE.IFMM.IP"]


def test_load_universe_drops_non_eur_keeps_rest(caplog: pytest.LogCaptureFixture) -> None:
    specs = [_spec(DAX), _spec("USD.THING", currency="USD")]
    with caplog.at_level("WARNING"):
        out = load_universe(specs)
    assert [s.epic for s in out] == [DAX]
    assert any("USD.THING" in r.message for r in caplog.records)


@pytest.mark.parametrize(
    "bad",
    [
        {"epic": "   "},            # empty/whitespace epic
        {"point_value": 0.0},       # non-positive point value
        {"point_value": -1.0},
        {"min_deal_size": 0.0},     # non-positive min size
    ],
)
def test_load_universe_drops_malformed(bad: dict[str, object]) -> None:
    # A single good anchor keeps the universe non-empty so we assert the *drop*.
    epic = bad.pop("epic", "BAD.ONE")  # type: ignore[arg-type]
    specs = [_spec(DAX), _spec(epic, **bad)]  # type: ignore[arg-type]
    out = load_universe(specs)
    assert [s.epic for s in out] == [DAX]


def test_load_universe_all_invalid_raises() -> None:
    with pytest.raises(ValueError):
        load_universe([_spec("X", currency="USD")])


def test_load_universe_empty_raises() -> None:
    with pytest.raises(ValueError):
        load_universe([])


# --------------------------------------------------------------------------- #
# ResearchConfig reconciliation (universe <-> epic_allowlist)                #
# --------------------------------------------------------------------------- #
def test_default_config_universe_matches_default_and_allowlist() -> None:
    cfg = ResearchConfig()
    assert cfg.epic_allowlist == (DAX,)
    assert cfg.universe is not None
    assert [s.epic for s in cfg.universe] == [DAX]
    # Derived default reproduces the curated default universe (DAX 1.0 €/pt, proxies).
    dax = cfg.universe[0]
    assert (dax.yf_ticker, dax.volume_proxy, dax.point_value, dax.currency) == (
        "^GDAXI",
        "EXS1.DE",
        1.0,
        "EUR",
    )
    assert _DEFAULT_UNIVERSE[0].epic == DAX


def test_explicit_universe_is_sot_and_rederives_allowlist() -> None:
    specs = (_spec(DAX, yf_ticker="^GDAXI"), _spec("IX.D.CAC.IFMM.IP", point_value=1.0))
    cfg = ResearchConfig(universe=specs)
    # epic_allowlist is re-derived from the universe (SoT), regardless of its default.
    assert cfg.epic_allowlist == (DAX, "IX.D.CAC.IFMM.IP")
    assert [s.epic for s in cfg.universe] == [DAX, "IX.D.CAC.IFMM.IP"]


def test_legacy_epic_allowlist_derives_universe() -> None:
    cfg = ResearchConfig(epic_allowlist=(DAX, "SIBLING.EPIC"))
    assert cfg.epic_allowlist == (DAX, "SIBLING.EPIC")
    assert cfg.universe is not None
    by_epic = {s.epic: s for s in cfg.universe}
    # DAX anchor keeps its known mapping/proxy; the unknown sibling degrades to None.
    assert by_epic[DAX].yf_ticker == "^GDAXI"
    assert by_epic["SIBLING.EPIC"].yf_ticker is None
    assert by_epic["SIBLING.EPIC"].volume_proxy is None


def test_explicit_universe_with_all_invalid_fails_closed() -> None:
    with pytest.raises(ValueError):
        ResearchConfig(universe=(_spec("X", currency="USD"),))


# --------------------------------------------------------------------------- #
# EXTENDED_UNIVERSE (v1.5 Step 2B — confirmed via resolve_epics.py 2026-07-01)  #
# --------------------------------------------------------------------------- #
def test_extended_universe_is_valid_and_dax_unchanged() -> None:
    # Passes through the same validation ResearchConfig(universe=...) applies.
    validated = load_universe(EXTENDED_UNIVERSE)
    assert [s.epic for s in validated] == [s.epic for s in EXTENDED_UNIVERSE]
    assert EXTENDED_UNIVERSE[0] is _DEFAULT_UNIVERSE[0]  # DAX spec reused, not duplicated


def test_extended_universe_has_two_eur_instruments() -> None:
    epics = [s.epic for s in EXTENDED_UNIVERSE]
    assert epics == ["IX.D.DAX.IFMM.IP", "IX.D.STXE.IFM.IP"]
    assert all(s.currency == "EUR" for s in EXTENDED_UNIVERSE)


def test_config_can_opt_into_extended_universe() -> None:
    cfg = ResearchConfig(universe=EXTENDED_UNIVERSE)
    assert cfg.epic_allowlist == ("IX.D.DAX.IFMM.IP", "IX.D.STXE.IFM.IP")
    assert cfg.universe[1].point_value == 2.0
