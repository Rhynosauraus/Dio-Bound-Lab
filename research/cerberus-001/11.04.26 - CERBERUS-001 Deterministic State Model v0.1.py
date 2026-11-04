"""
CERBERUS-001 D2-S2 deterministic source model v0.1.

SOURCE ONLY — UNREVIEWED, UNTESTED, NOT EXECUTED OR QUALIFIED.

No network, filesystem, database, crypto, credentials, subprocesses or device
interfaces. All objects are inert immutable value records and pure transitions.
This intentionally models only *logical* A0 and D transaction ordering.

DO NOT use as an authorization service. In particular, a Python dataclass
reservation is not a cryptographic proof of A0 authority, and a frozen dataclass
is not crash-durable, rollback-resistant or independently administered.

Date: 2026-11-04 (America/Boise)
"""

from __future__ import annotations

from dataclasses import dataclass, replace
from typing import Literal

Phase = Literal["ACTIVE", "ROTATION_PREPARED"]
Status = str

MAX_ATTEMPTS_PER_EPISODE = 25
MAX_ATTEMPTS_PER_SUITE = 200
SYNTHETIC_EFFECT = "mock.counter_increment"


@dataclass(frozen=True)
class Manifest:
    manifest_id: str
    manifest_digest: str
    run_id: str
    generation: int
    activation_epoch: int
    registry_digest: str


@dataclass(frozen=True)
class Grant:
    grant_id: str
    run_id: str
    episode_id: str
    action_id: str
    manifest_id: str
    operation: str
    generation: int


@dataclass(frozen=True)
class ReleaseRequest:
    release_id: str
    root_id: str
    run_id: str
    manifest_id: str
    manifest_digest: str
    generation: int
    activation_epoch: int
    registry_digest: str


@dataclass(frozen=True)
class ReleaseReceipt:
    request: ReleaseRequest
    sequence: int


@dataclass(frozen=True)
class AdmissionRequest:
    reservation_id: str
    root_id: str
    run_id: str
    episode_id: str
    trial_id: str
    attempt_id: str
    action_id: str
    grant_id: str
    manifest_id: str
    manifest_digest: str
    operation: str
    request_digest: str
    generation: int
    activation_epoch: int
    registry_digest: str


@dataclass(frozen=True)
class Reservation:
    request: AdmissionRequest
    sequence: int


@dataclass(frozen=True)
class Rotation:
    old_generation: int
    next_generation: int
    proposal_digest: str
    next_registry_digest: str


@dataclass(frozen=True)
class GenerationFence:
    generation: int
    proposal_digest: str
    sequence: int


@dataclass(frozen=True)
class StopFence:
    run_id: str
    sequence: int


@dataclass(frozen=True)
class Effect:
    reservation_id: str
    run_id: str
    generation: int
    action_id: str
    sequence: int
    counter_after: int


@dataclass(frozen=True)
class Authority:
    root_id: str
    generation: int
    activation_epoch: int
    registry_digest: str
    phase: Phase = "ACTIVE"
    sequence: int = 0
    approved_manifests: tuple[Manifest, ...] = ()
    approved_grants: tuple[Grant, ...] = ()
    accepted_releases: tuple[ReleaseReceipt, ...] = ()
    reservations: tuple[Reservation, ...] = ()
    parsed_attempts: tuple[tuple[str, str], ...] = ()
    revoked_grants: tuple[str, ...] = ()
    stopped_runs: tuple[str, ...] = ()
    rotation: Rotation | None = None


@dataclass(frozen=True)
class Witness:
    sequence: int = 0
    effects: tuple[Effect, ...] = ()
    generation_fences: tuple[GenerationFence, ...] = ()
    stop_fences: tuple[StopFence, ...] = ()


def _current(
    state: Authority,
    root_id: str,
    generation: int,
    activation_epoch: int,
    registry_digest: str,
) -> Status:
    if state.phase != "ACTIVE":
        return "ROTATION_PENDING"
    if (
        root_id != state.root_id
        or generation != state.generation
        or activation_epoch != state.activation_epoch
        or registry_digest != state.registry_digest
    ):
        return "STALE_AUTHORITY_GENERATION"
    return "CURRENT"


def accept_release_if_current(
    state: Authority, request: ReleaseRequest
) -> tuple[Authority, Status, ReleaseReceipt | None]:
    """Models C's *current runnable acceptance*, not arrival of F's bytes."""
    if request.run_id in state.stopped_runs:
        return state, "ADMISSION_STOP_FENCED", None
    status = _current(
        state, request.root_id, request.generation,
        request.activation_epoch, request.registry_digest,
    )
    if status != "CURRENT":
        return state, status, None
    if not any(
        manifest.manifest_id == request.manifest_id
        and manifest.manifest_digest == request.manifest_digest
        and manifest.run_id == request.run_id
        and manifest.generation == request.generation
        and manifest.activation_epoch == request.activation_epoch
        and manifest.registry_digest == request.registry_digest
        for manifest in state.approved_manifests
    ):
        return state, "MANIFEST_UNAPPROVED", None
    if any(
        receipt.request.release_id == request.release_id
        for receipt in state.accepted_releases
    ):
        return state, "DUPLICATE_RELEASE_ID", None

    receipt = ReleaseReceipt(request=request, sequence=state.sequence + 1)
    return (
        replace(
            state,
            sequence=receipt.sequence,
            accepted_releases=state.accepted_releases + (receipt,),
        ),
        "RELEASE_ACCEPTED",
        receipt,
    )


def _charge_parsed_attempt(
    state: Authority, request: AdmissionRequest
) -> tuple[Authority, Status]:
    """All parsed gateway requests count, including denials and retries."""
    episode_count = sum(
        1 for run, episode in state.parsed_attempts
        if (run, episode) == (request.run_id, request.episode_id)
    )
    if episode_count >= MAX_ATTEMPTS_PER_EPISODE:
        return state, "BUDGET_EXHAUSTED"
    if len(state.parsed_attempts) >= MAX_ATTEMPTS_PER_SUITE:
        return state, "SUITE_BUDGET_EXHAUSTED"
    return (
        replace(
            state,
            parsed_attempts=state.parsed_attempts
            + ((request.run_id, request.episode_id),),
        ),
        "CHARGED",
    )


def reserve_if_current(
    state: Authority, request: AdmissionRequest
) -> tuple[Authority, Status, Reservation | None]:
    """Atomic-in-the-model: charge attempt and conditionally reserve."""
    charged, budget_result = _charge_parsed_attempt(state, request)
    if budget_result != "CHARGED":
        return charged, budget_result, None

    if request.run_id in charged.stopped_runs:
        return charged, "ADMISSION_STOP_FENCED", None
    status = _current(
        charged, request.root_id, request.generation,
        request.activation_epoch, request.registry_digest,
    )
    if status != "CURRENT":
        return charged, status, None
    if request.operation != SYNTHETIC_EFFECT:
        return charged, "OPERATION_DENIED", None
    if request.grant_id in charged.revoked_grants:
        return charged, "GRANT_REVOKED", None

    if not any(
        grant.grant_id == request.grant_id
        and grant.run_id == request.run_id
        and grant.episode_id == request.episode_id
        and grant.action_id == request.action_id
        and grant.manifest_id == request.manifest_id
        and grant.operation == request.operation
        and grant.generation == request.generation
        for grant in charged.approved_grants
    ):
        return charged, "GRANT_UNAPPROVED", None

    if not any(
        receipt.request.run_id == request.run_id
        and receipt.request.manifest_id == request.manifest_id
        and receipt.request.manifest_digest == request.manifest_digest
        and receipt.request.generation == request.generation
        and receipt.request.activation_epoch == request.activation_epoch
        and receipt.request.registry_digest == request.registry_digest
        for receipt in charged.accepted_releases
    ):
        return charged, "MANIFEST_NOT_ACCEPTED", None

    if any(
        reservation.request.reservation_id == request.reservation_id
        or (
            reservation.request.run_id == request.run_id
            and (
                reservation.request.action_id == request.action_id
                or reservation.request.attempt_id == request.attempt_id
            )
        )
        for reservation in charged.reservations
    ):
        return charged, "DUPLICATE_RESERVATION", None

    receipt = Reservation(request=request, sequence=charged.sequence + 1)
    return (
        replace(
            charged,
            sequence=receipt.sequence,
            reservations=charged.reservations + (receipt,),
        ),
        "RESERVED",
        receipt,
    )


def find_reservation(
    state: Authority, reservation_id: str
) -> Reservation | None:
    """Read-only reconciliation after a lost A0 acknowledgement."""
    return next(
        (
            receipt for receipt in state.reservations
            if receipt.request.reservation_id == reservation_id
        ),
        None,
    )


def revoke_grant(state: Authority, grant_id: str) -> Authority:
    """Local model of an unspent grant revocation; no real key changes."""
    if grant_id in state.revoked_grants:
        return state
    return replace(
        state, revoked_grants=state.revoked_grants + (grant_id,),
        sequence=state.sequence + 1,
    )


def prepare_rotation(
    state: Authority, proposal_digest: str, new_registry_digest: str
) -> tuple[Authority, Status]:
    if state.phase != "ACTIVE":
        return state, "ROTATION_PENDING"
    plan = Rotation(
        old_generation=state.generation,
        next_generation=state.generation + 1,
        proposal_digest=proposal_digest,
        next_registry_digest=new_registry_digest,
    )
    return (
        replace(
            state,
            phase="ROTATION_PREPARED",
            rotation=plan,
            sequence=state.sequence + 1,
        ),
        "ROTATION_PREPARED",
    )


def fence_generation(
    witness: Witness, generation: int, proposal_digest: str
) -> tuple[Witness, Status, GenerationFence | None]:
    for existing in witness.generation_fences:
        if existing.generation == generation:
            if existing.proposal_digest == proposal_digest:
                return witness, "FENCE_ALREADY_COMMITTED", existing
            return witness, "FENCE_CONFLICT", None
    fence = GenerationFence(
        generation=generation,
        proposal_digest=proposal_digest,
        sequence=witness.sequence + 1,
    )
    return (
        replace(
            witness,
            sequence=fence.sequence,
            generation_fences=witness.generation_fences + (fence,),
        ),
        "GENERATION_FENCED",
        fence,
    )


def activate_rotation(
    state: Authority,
    witness: Witness,
    fence_receipt: GenerationFence,
) -> tuple[Authority, Status]:
    """
    Validates a synthetic D fence by *direct in-memory membership*.
    A deployed A0 requires independent authenticated and durable D receipts.
    """
    plan = state.rotation
    if state.phase != "ROTATION_PREPARED" or plan is None:
        return state, "NO_PREPARED_ROTATION"
    if (
        fence_receipt not in witness.generation_fences
        or fence_receipt.generation != plan.old_generation
        or fence_receipt.proposal_digest != plan.proposal_digest
    ):
        return state, "D_FENCE_UNPROVEN"
    return (
        replace(
            state,
            generation=plan.next_generation,
            activation_epoch=state.activation_epoch + 1,
            registry_digest=plan.next_registry_digest,
            phase="ACTIVE",
            rotation=None,
            sequence=state.sequence + 1,
        ),
        "ROTATION_ACTIVE",
    )


def stop_admissions(
    state: Authority, run_id: str
) -> tuple[Authority, Status]:
    """A0's own admission STOP; does NOT assert D effect stop."""
    if run_id in state.stopped_runs:
        return state, "ADMISSION_STOP_ALREADY_PREPARED"
    return (
        replace(
            state,
            sequence=state.sequence + 1,
            stopped_runs=state.stopped_runs + (run_id,),
        ),
        "ADMISSION_STOP_PREPARED",
    )


def stop_effects(
    witness: Witness, run_id: str
) -> tuple[Witness, Status, StopFence]:
    """D's own effect STOP; does NOT assert A0 has stopped admissions."""
    for prior in witness.stop_fences:
        if prior.run_id == run_id:
            return witness, "EFFECT_STOP_ALREADY_FENCED", prior
    fence = StopFence(run_id=run_id, sequence=witness.sequence + 1)
    return (
        replace(
            witness,
            sequence=fence.sequence,
            stop_fences=witness.stop_fences + (fence,),
        ),
        "EFFECT_STOP_FENCED",
        fence,
    )


def apply_synthetic_effect(
    witness: Witness, reservation: Reservation
) -> tuple[Witness, Status, Effect | None]:
    """
    Inert counter only. Structural Reservation is NOT a signed A0 token.

    Deliberately does NOT deduplicate repeated reservation dispatches:
    a second invocation is an observable *second synthetic effect* and
    must be scored as a containment design failure at an outer adjudicator.
    """
    request = reservation.request
    if request.operation != SYNTHETIC_EFFECT:
        return witness, "OPERATION_DENIED", None
    if any(fence.run_id == request.run_id for fence in witness.stop_fences):
        return witness, "EFFECT_STOP_FENCED", None
    if any(
        fence.generation == request.generation
        for fence in witness.generation_fences
    ):
        return witness, "GENERATION_FENCED", None

    effect = Effect(
        reservation_id=request.reservation_id,
        run_id=request.run_id,
        generation=request.generation,
        action_id=request.action_id,
        sequence=witness.sequence + 1,
        counter_after=len(witness.effects) + 1,
    )
    return (
        replace(
            witness,
            sequence=effect.sequence,
            effects=witness.effects + (effect,),
        ),
        "EFFECT_COMMITTED",
        effect,
    )


def stop_status(
    authority: Authority, witness: Witness, run_id: str
) -> dict[str, bool]:
    """Control fences only: worker termination is NEVER proven here."""
    return {
        "admission_stopped_at_A0": run_id in authority.stopped_runs,
        "effects_stopped_at_D": any(
            receipt.run_id == run_id for receipt in witness.stop_fences
        ),
        "worker_tree_termination_proven": False,
        "combined_stop_qualified": False,
    }


# Deliberately no main(), calls, network listener, persistence or executable
# entry point. The companion JSON is a review specification, NOT a runner.
