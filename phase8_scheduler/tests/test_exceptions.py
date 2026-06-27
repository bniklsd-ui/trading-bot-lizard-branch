"""Module 2 — the scheduler exception hierarchy.

Pure type checks: the base/subclass relationship, the ``code`` class attributes, the
family-catch behaviour, and that a message round-trips. No network, no I/O.
"""

from __future__ import annotations

import pytest

from scheduler import PreflightError as ExportedPreflightError
from scheduler import SchedulerError as ExportedSchedulerError
from scheduler.exceptions import PreflightError, SchedulerError


def test_base_is_an_exception_with_its_code() -> None:
    """``SchedulerError`` is a plain ``Exception`` carrying the family code."""
    assert issubclass(SchedulerError, Exception)
    assert SchedulerError.code == "SCHEDULER_ERROR"


def test_preflight_is_a_scheduler_error_with_its_code() -> None:
    """``PreflightError`` extends the base and overrides ``code``."""
    assert issubclass(PreflightError, SchedulerError)
    assert PreflightError.code == "PREFLIGHT_ERROR"


def test_codes_are_distinct() -> None:
    """Subclass code differs from the base — precise catches can branch on it."""
    assert PreflightError.code != SchedulerError.code


def test_preflight_is_caught_by_the_family() -> None:
    """A raised ``PreflightError`` is catchable as ``SchedulerError`` (family catch)."""
    with pytest.raises(SchedulerError) as excinfo:
        raise PreflightError("keyring unreachable")
    assert isinstance(excinfo.value, PreflightError)


def test_message_round_trips_and_code_is_readable_on_instance() -> None:
    """The exception carries its message; ``code`` is reachable on the instance."""
    exc = PreflightError("keyring unreachable")
    assert "keyring unreachable" in str(exc)
    assert exc.code == "PREFLIGHT_ERROR"


def test_exported_from_package_root() -> None:
    """Both classes are re-exported from ``scheduler`` and are the same objects."""
    assert ExportedSchedulerError is SchedulerError
    assert ExportedPreflightError is PreflightError
