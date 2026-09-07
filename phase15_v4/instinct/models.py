"""Instinct + InstinctConfig — frozen dataclasses, the Instinct-ECC value types.

Schema is wörtlich nach ``docs/concepts/phase7_reward_concept.md §7b`` (the schema
Phase 7 deferred to a later step — that step is Phase 15 Block C, Plan §6 C2):

    trigger / domain ∈ {entry, exit, sizing, timing} /
    confidence / evidence_trade_ids[] / contradictions_trade_ids[]

Plus the lifecycle status (``proposed`` → ``validated`` → ``promoted``, or
``proposed`` → ``refuted``, or ``promoted`` → ``archived``) — the C1 addition
(Plan §6 C1, Migration 009). The validator (C2) is the only authority that may
move an instinct out of ``proposed``; ``promote_eligible`` (C2) gates the
``promoted`` step (P10/P12).

``InstinctConfig`` carries the two promotion gates:

- ``instinct_n_min`` (P12): default ``50`` closed trades before any instinct may be
  promoted. **Deliberately separate** from ``RewardConfig.n_min = 10`` (Wilson
  confidence threshold) — the two have unrelated meanings and conflating them
  would couple two independent thresholds (§9.6 der Plan-Session,
  ``RewardConfig.n_min`` ist nur in ``confidence.py`` + Tests referenziert).
- ``enable_instinct_promotion`` (P10): default ``False``. Promotion is **off by
  default** — the only way instincts reach VETO 5 is via a Nikinger-authorized
  config flip.

Both are ``frozen=True`` to match the project's dataclass discipline (Phase 5/7/10).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


# Valid domain values — pinned by the SQL CHECK constraint
# (`phase2_persistence/migrations/009_phase15_instincts.sql`).
# Kept here as a module constant so the validator can sanity-check before INSERT
# and tests can parameterize over it.
DOMAINS: tuple[str, ...] = ("entry", "exit", "sizing", "timing")

# Lifecycle statuses — wörtlich nach C1 `phase2_persistence/persistence/db.py:_INSTINCT_STATUSES`.
# The validator moves ``proposed`` → ``validated`` or ``proposed`` → ``refuted``;
# ``promote_eligible`` moves ``validated`` → ``promoted``; operator / cron archives.
INSTINCT_STATUSES: tuple[str, ...] = (
    "proposed", "validated", "refuted", "promoted", "archived",
)


def is_valid_domain(value: Any) -> bool:
    """Return True if ``value`` is one of the four valid Instinct domains."""
    return value in DOMAINS


def is_valid_status(value: Any) -> bool:
    """Return True if ``value`` is one of the five lifecycle statuses."""
    return value in INSTINCT_STATUSES


@dataclass(frozen=True)
class Instinct:
    """A structured, evidence-anchored learning rule extracted from closed trades.

    This is the Instinct-ECC value type (Plan §6 C2). The fields are exactly
    what :class:`Database.insert_instinct` (Phase 2, Migration 009) accepts —
    the schema is the contract.

    Attributes:
        trigger: short, free-text description of the rule (e.g.
            *"Avoid entries when spread > 0.015 %"*). Plain text — the LLM
            extracts language, the validator counts evidence.
        domain: one of :data:`DOMAINS`. Determines which downstream path may
            consult the instinct (VETO 5 / sizing / timing). Pinned by the
            ``CHECK(domain IN (...))`` constraint.
        confidence: 0.0–1.0 model self-assessment, ``None`` when not yet
            rated (i.e. just after extraction). ``None`` ⇒ unpromotable.
        evidence_trade_ids: tuple of ``trade_outcomes.id`` rows that support
            the trigger. Backs the validator's evidence-vs-contradiction count.
            Tuple (not list) for frozen-dataclass discipline.
        contradictions_trade_ids: tuple of ``trade_outcomes.id`` rows that
            contradict the trigger. Validator refutes when contradictions
            outnumber evidence (Plan §6 C2).
        status: lifecycle state, one of :data:`INSTINCT_STATUSES`.
            ``proposed`` by default; the validator advances to ``validated``
            or ``refuted``; ``promote_eligible`` advances to ``promoted``.
        created_utc: ISO-8601 UTC timestamp of insertion. Default ``""``
            — the DB layer fills ``utc_iso_now()`` if missing (see
            ``Database.insert_instinct``).
        validated_utc / promoted_utc / archived_utc: per-transition
            timestamps, set by ``Database.update_instinct_status``. ``None``
            when the transition has not yet happened.
        id: row id from the ``instincts`` table, or ``None`` if the
            instinct has not been inserted yet. The constructor does not
            assign one — callers use ``Database.insert_instinct`` and read
            the returned int back into ``.id``.
    """

    trigger: str
    domain: str
    confidence: float | None = None
    evidence_trade_ids: tuple[int, ...] | list[int] = ()
    contradictions_trade_ids: tuple[int, ...] | list[int] = ()
    status: str = "proposed"
    created_utc: str = ""
    validated_utc: str | None = None
    promoted_utc: str | None = None
    archived_utc: str | None = None
    id: int | None = None

    def __post_init__(self) -> None:
        """Validate + normalise the immutable invariants (Plan §1 P8 + Migration 009 CHECK).

        Two normalisations happen here:
        - ``evidence_trade_ids`` and ``contradictions_trade_ids`` accept either a
          ``tuple`` or a ``list`` for ergonomics (callers coming from JSON have
          lists) but store the canonical form as a ``tuple`` — frozen-dataclass
          discipline, same as the rest of the project.
        - Domain / status / confidence / trigger are validated before the
          instance escapes; failures raise ``ValueError`` with the exact same
          message that the SQL CHECK constraints would emit on insert.
        """
        # Normalise list → tuple (frozen-dataclass discipline). Done via
        # ``object.__setattr__`` because the dataclass is frozen — but we're
        # inside ``__post_init__``, after ``__init__`` ran, so the slots are
        # still mutable for this one assignment.
        object.__setattr__(
            self, "evidence_trade_ids",
            tuple(self.evidence_trade_ids),
        )
        object.__setattr__(
            self, "contradictions_trade_ids",
            tuple(self.contradictions_trade_ids),
        )

        if not is_valid_domain(self.domain):
            raise ValueError(
                f"domain must be one of {DOMAINS}, got {self.domain!r}"
            )
        if not is_valid_status(self.status):
            raise ValueError(
                f"status must be one of {INSTINCT_STATUSES}, got {self.status!r}"
            )
        if self.confidence is not None and not (
            0.0 <= self.confidence <= 1.0
        ):
            raise ValueError(
                f"confidence must be in [0.0, 1.0] or None, got {self.confidence!r}"
            )
        if not self.trigger.strip():
            raise ValueError("trigger must be a non-empty string")


@dataclass(frozen=True)
class InstinctConfig:
    """The Instinct-ECC promotion gates (Plan §1 P10/P12).

    Two fields, both deliberately conservative:

    - ``instinct_n_min`` (P12): closed trades required before any instinct
      may be promoted to VETO 5. Default ``50`` (separate from
      ``RewardConfig.n_min = 10`` which is the Wilson confidence floor —
      §9.6 der Plan-Session bestätigt: ``RewardConfig.n_min`` wird NUR in
      ``confidence.py`` + Tests gelesen, ein Conf laten ist ausgeschlossen).
    - ``enable_instinct_promotion``: master switch. The real gates are
      ``instinct_n_min`` (today 50) and the deterministic validator — this
      switch only suppresses the **Promotion-Bridge** path. Phase 16 D1:
      default ``True`` (Plan §1 P5 supersedes Phase-15-P10). The validator
      is code, not AI — Hard Rule 3 stays satisfied (no AI→VETO path).
    """

    instinct_n_min: int = 50
    # Phase 16 D1: ON by default; the Promotion-Bridge wires the close-seam
    # of ``RewardSink`` through to ``promote_eligible`` (Plan §6 D2).
    enable_instinct_promotion: bool = True

    def __post_init__(self) -> None:
        """Reject negative or zero ``instinct_n_min`` — would make the gate trivial."""
        if self.instinct_n_min <= 0:
            raise ValueError(
                f"instinct_n_min must be > 0, got {self.instinct_n_min}"
            )

    @staticmethod
    def from_dict(record: dict[str, Any]) -> "InstinctConfig":
        """Build an ``InstinctConfig`` from a plain dict (DB/config file row).

        Missing keys fall back to the dataclass defaults — defensive against
        a config row that pre-dates one of the fields.
        """
        return InstinctConfig(
            instinct_n_min=int(record.get("instinct_n_min", 50)),
            # Phase 16 D1: default True; ``from_dict`` mirrors the dataclass default.
            enable_instinct_promotion=bool(
                record.get("enable_instinct_promotion", True)
            ),
        )
