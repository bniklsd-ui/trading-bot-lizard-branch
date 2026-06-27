"""Typed exception hierarchy for the Phase 8 scheduler daemon.

Mirrors the Phase-1/3/4/5/6/7 pattern: one base (:class:`SchedulerError`) carrying a
``code`` class attribute, plus specific subclasses so callers can catch the whole
family or be precise. Independent of the sibling phases' hierarchies (phase
isolation — imports nothing cross-phase). Errors are never swallowed silently.

The scheduler's runtime contract is mostly **fail-closed without raising**: the
auto-confirm gate returns ``(bool, reason)``, the budget gate returns ``bool``, and
the reconcile / research ticks log ``critical`` and carry on rather than re-raise (a
data-collection daemon must not die on a transient blip — the backoff tracker trips
the kill-switch after ``max_consecutive_failures``). So this hierarchy is deliberately
small: the **only** custom raise site today is the startup preflight.

- :class:`PreflightError` is **fail-closed**: a startup prerequisite could not be
  verified, so the daemon exits cleanly **without attempting any trade**. The
  motivating case is the deployment top-risk (concept Q3) — the gnome-keyring /
  Secret-Service is unreachable from a non-interactive session, so credentials cannot
  be read. The bot must never trade on an unverified credential path.

The file grows per module: if a later module genuinely needs a new typed exception, it
is added here then (the same "grow per module" discipline the package ``__init__`` and
the prior phases follow), not speculatively now.
"""

from __future__ import annotations


class SchedulerError(Exception):
    """Base class for all Phase-8 scheduler errors."""

    code: str = "SCHEDULER_ERROR"


class PreflightError(SchedulerError):
    """Fail-closed startup-preflight failure: a prerequisite could not be verified.

    Raised by ``runner.preflight()`` (Module 11) before the loop starts when any hard
    prerequisite is unverifiable — the keyring / Secret-Service is unreachable
    (``broker_wrapper.credentials.get_credential`` fails), ``broker.connect`` is not
    ok, or the DB / migrations are missing. The daemon then exits cleanly **without
    attempting any trade**; the operator must resolve the prerequisite first.

    The keyring-in-a-non-interactive-session case is the deployment top-risk (concept
    Q3): live tests work in the operator's unlocked interactive session, but a bare
    background service without a session bus cannot read credentials — the preflight
    catches that loudly instead of trading blind.
    """

    code = "PREFLIGHT_ERROR"
