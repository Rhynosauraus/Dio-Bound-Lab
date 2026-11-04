"""
CERBERUS-001 — D-side one-use synthetic effect claim (SOURCE CANDIDATE v0.3).

UNEXECUTED / UNCOMPILED / UNREVIEWED / NOT AN AUTHORIZATION SERVICE.
No real keys, I/O, database, network, subprocesses, device interfaces or
actual host/security operations.

This source extends the v0.2 reservation *design* with two distinct facts:

  Attempt observation: every invocation presented to D is recorded, including
  invalid tokens, duplicates and attempts following STOP.
  Effect claim: for a valid signed and independently committed A0 reservation,
  D may record at most one synthetic effect for each reservation AND each
  (root_id, run_id, episode_id, action_id) tuple.

The model assumes one indivisible transition per call. A real D would require
one durable, serializable transaction containing attempt receipt, one-use
claim uniqueness, local fence checks, effect counter and return receipt.
This model provides none of that atomicity or administration.

The verifier and commit oracle are injected interfaces, not trusted
implementation. They MUST be pinned by a later protected D deployment; a
test-only verifier/commit oracle does NOT establish Ed25519 or A0 provenance.
The old v0.1/v0.2 raw effect functions still exist on this branch and MUST
NOT be exposed in a deployed effect endpoint. M10's historical failure remains
frozen in v0.2; this is a proposed semantic CHANGE for independent review.

Date: November 4, 2026 (America/Boise).
"""

from __future__ import annotations

from dataclasses import dataclass, replace
from hashlib import sha256
from typing import Any, Callable, Protocol


class A0CommitEvidence(Protocol):
    def committed(self, reservation_id: str, sequence: int, digest: str) -> bool:
        """Authenticated, durable source outside D and B; no local test double in production."""


VerifyEnvelope = Callable[[Any, Any, Any, Any], tuple[str, dict | None]]


@dataclass(frozen=True)
class ObservedAttempt:
    sequence: int
    payload_sha256: str
    status: str
    committed_now: bool
    prior_effect_sequence: int | None = None


@dataclass(frozen=True)
class EffectReceipt:
    sequence: int
    root_id: str
    run_id: str
    episode_id: str
    action_id: str
    grant_id: str
    generation: int
    reservation_id: str
    token_sha256: str
    counter_after: int


@dataclass(frozen=True)
class GenerationFence:
    sequence: int
    generation: int
    proposal_digest: str


@dataclass(frozen=True)
class GrantFence:
    sequence: int
    root_id: str
    run_id: str
    grant_id: str


@dataclass(frozen=True)
class RunStop:
    sequence: int
    run_id: str


@dataclass(frozen=True)
class Ledger:
    sequence: int = 0
    attempts: tuple[ObservedAttempt, ...] = ()
    effects: tuple[EffectReceipt, ...] = ()
    generation_fences: tuple[GenerationFence, ...] = ()
    grant_fences: tuple[GrantFence, ...] = ()
    stopped_runs: tuple[RunStop, ...] = ()


@dataclass(frozen=True)
class Outcome:
    ledger: Ledger
    status: str
    committed_now: bool
    historical_effect: EffectReceipt | None = None


def _request_digest(token: Any) -> str:
    """Hash only raw bytes; malformed objects count as attempts with an empty-byte marker."""
    raw = getattr(token, "payload_bytes", None)
    return sha256(raw if type(raw) is bytes else b"").hexdigest()


def _finalize_denial(
    ledger: Ledger, payload_digest: str, status: str,
    prior: EffectReceipt | None = None,
) -> Outcome:
    sequence = ledger.sequence + 1
    attempt = ObservedAttempt(
        sequence=sequence,
        payload_sha256=payload_digest,
        status=status,
        committed_now=False,
        prior_effect_sequence=prior.sequence if prior is not None else None,
    )
    return Outcome(
        ledger=replace(
            ledger, sequence=sequence,
            attempts=ledger.attempts + (attempt,),
        ),
        status=status,
        committed_now=False,
        historical_effect=prior,
    )


def _fence_status(ledger: Ledger, value: dict) -> str | None:
    if any(record.run_id == value["run_id"] for record in ledger.stopped_runs):
        return "RUN_STOP_FENCED"
    if any(
        record.generation == value["generation"]
        for record in ledger.generation_fences
    ):
        return "GENERATION_FENCED"
    if any(
        record.root_id == value["root_id"]
        and record.run_id == value["run_id"]
        and record.grant_id == value["grant_id"]
        for record in ledger.grant_fences
    ):
        return "GRANT_FENCED"
    return None


def record_one_use_effect(
    ledger: Ledger,
    token: Any,
    pinned_key: Any,
    d_owned_expected: Any,
    verifier: Any,
    commit_evidence: A0CommitEvidence | None,
    verify_envelope: VerifyEnvelope | None,
) -> Outcome:
    """One pure model transition: observe attempt and optionally commit one effect.

    Both observations MUST be in one real durable D transaction when built.
    A separate transport-side tap must witness whether D omitted an incoming
    attempt; an internally complete D attempt list is not a global guarantee.
    """
    payload_digest = _request_digest(token)
    if verify_envelope is None:
        return _finalize_denial(
            ledger, payload_digest, "VERIFICATION_UNAVAILABLE"
        )
    try:
        status, value = verify_envelope(
            token, pinned_key, d_owned_expected, verifier
        )
    except (RuntimeError, ValueError, TypeError, AttributeError, KeyError):
        return _finalize_denial(
            ledger, payload_digest, "VERIFICATION_UNAVAILABLE"
        )

    if status != "VERIFIED_SIGNATURE_AND_BINDINGS" or type(value) is not dict:
        return _finalize_denial(
            ledger, payload_digest,
            status if type(status) is str else "ENVELOPE_UNVERIFIED",
        )

    if any(
        name not in value or
        value[name] != getattr(d_owned_expected, name, object())
        for name in (
            "root_id", "run_id", "episode_id", "action_id", "grant_id",
            "generation", "reservation_id",
        )
    ) or type(value.get("commit_sequence")) is not int:
        return _finalize_denial(
            ledger, payload_digest, "D_CONTEXT_OR_VERIFICATION_OUTPUT_INVALID"
        )

    if (
        commit_evidence is None
        or value.get("reservation_id") is None
        or type(value.get("commit_sequence")) is not int
    ):
        return _finalize_denial(
            ledger, payload_digest, "A0_COMMITMENT_UNPROVEN"
        )
    try:
        is_committed = commit_evidence.committed(
            value["reservation_id"], value["commit_sequence"], payload_digest
        )
    except (RuntimeError, ValueError, TypeError, AttributeError, KeyError):
        return _finalize_denial(
            ledger, payload_digest, "A0_COMMITMENT_UNPROVEN"
        )
    if is_committed is not True:
        return _finalize_denial(
            ledger, payload_digest, "A0_COMMITMENT_UNPROVEN"
        )

    # Historical receipt reconciliation occurs only AFTER re-verifying the
    # token and A0 commitment. It is never a new effect or new admission.
    by_reservation = next(
        (
            effect for effect in ledger.effects
            if effect.reservation_id == value["reservation_id"]
        ),
        None,
    )
    if by_reservation is not None:
        if (
            by_reservation.token_sha256 != payload_digest
            or by_reservation.root_id != value["root_id"]
            or by_reservation.run_id != value["run_id"]
        ):
            return _finalize_denial(
                ledger, payload_digest, "RESERVATION_ID_CONFLICT"
            )
        fence = _fence_status(ledger, value)
        return _finalize_denial(
            ledger, payload_digest,
            "ALREADY_COMMITTED_AFTER_FENCE_HISTORICAL_ONLY"
            if fence is not None else "ALREADY_COMMITTED_HISTORICAL_ONLY",
            prior=by_reservation,
        )

    # Distinct reservation IDs may not reauthorize the same action in the
    # same run/episode (even if a broken A0 were to sign the second).
    by_action = next(
        (
            effect for effect in ledger.effects
            if effect.root_id == value["root_id"]
            and effect.run_id == value["run_id"]
            and effect.episode_id == value["episode_id"]
            and effect.action_id == value["action_id"]
        ),
        None,
    )
    if by_action is not None:
        return _finalize_denial(
            ledger, payload_digest, "ACTION_ALREADY_COMMITTED"
        )

    fence = _fence_status(ledger, value)
    if fence is not None:
        return _finalize_denial(ledger, payload_digest, fence)

    # The logical linearization covers BOTH attempt observation and effect
    # claim. This is NOT a real lock/SQLite transaction or durable storage.
    attempt_sequence = ledger.sequence + 1
    effect_sequence = ledger.sequence + 2
    attempt = ObservedAttempt(
        sequence=attempt_sequence,
        payload_sha256=payload_digest,
        status="EFFECT_COMMITTED",
        committed_now=True,
        prior_effect_sequence=None,
    )
    effect = EffectReceipt(
        sequence=effect_sequence,
        root_id=value["root_id"],
        run_id=value["run_id"],
        episode_id=value["episode_id"],
        action_id=value["action_id"],
        grant_id=value["grant_id"],
        generation=value["generation"],
        reservation_id=value["reservation_id"],
        token_sha256=payload_digest,
        counter_after=len(ledger.effects) + 1,
    )
    new_ledger = replace(
        ledger,
        sequence=effect_sequence,
        attempts=ledger.attempts + (attempt,),
        effects=ledger.effects + (effect,),
    )
    return Outcome(
        ledger=new_ledger, status="EFFECT_COMMITTED",
        committed_now=True, historical_effect=effect,
    )


def fence_generation(
    ledger: Ledger, generation: int, proposal_digest: str
) -> tuple[Ledger, str]:
    if any(f.generation == generation for f in ledger.generation_fences):
        if any(
            f.generation == generation and f.proposal_digest == proposal_digest
            for f in ledger.generation_fences
        ):
            return ledger, "GENERATION_FENCE_ALREADY_COMMITTED"
        return ledger, "GENERATION_FENCE_CONFLICT"
    fence = GenerationFence(
        sequence=ledger.sequence + 1, generation=generation,
        proposal_digest=proposal_digest,
    )
    return (
        replace(
            ledger, sequence=fence.sequence,
            generation_fences=ledger.generation_fences + (fence,),
        ),
        "GENERATION_FENCED",
    )


def fence_grant(
    ledger: Ledger, root_id: str, run_id: str, grant_id: str
) -> tuple[Ledger, str]:
    if any(
        f.root_id == root_id and f.run_id == run_id and f.grant_id == grant_id
        for f in ledger.grant_fences
    ):
        return ledger, "GRANT_FENCE_ALREADY_COMMITTED"
    fence = GrantFence(
        sequence=ledger.sequence + 1, root_id=root_id,
        run_id=run_id, grant_id=grant_id,
    )
    return (
        replace(
            ledger, sequence=fence.sequence,
            grant_fences=ledger.grant_fences + (fence,),
        ),
        "GRANT_FENCED",
    )


def fence_run(ledger: Ledger, run_id: str) -> tuple[Ledger, str]:
    if any(f.run_id == run_id for f in ledger.stopped_runs):
        return ledger, "RUN_STOP_ALREADY_COMMITTED"
    fence = RunStop(sequence=ledger.sequence + 1, run_id=run_id)
    return (
        replace(
            ledger, sequence=fence.sequence,
            stopped_runs=ledger.stopped_runs + (fence,),
        ),
        "RUN_STOP_FENCED",
    )


def ledger_facts(ledger: Ledger) -> dict[str, int]:
    """Descriptive counters only; not a qualification certificate."""
    return {
        "observed_attempts_at_D": len(ledger.attempts),
        "committed_effects_at_D": len(ledger.effects),
        "generation_fences_at_D": len(ledger.generation_fences),
        "grant_fences_at_D": len(ledger.grant_fences),
        "global_run_stops_at_D": len(ledger.stopped_runs),
    }


# NO __main__, network entrypoint, filesystem I/O, key generation, persistence,
# OS or device operations. Historical v0.1/v0.2 source remains unchanged.
