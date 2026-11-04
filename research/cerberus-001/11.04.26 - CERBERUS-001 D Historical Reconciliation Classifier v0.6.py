"""
CERBERUS-001 — D-private historical receipt classification, candidate v0.6.
CREATED 2026-11-04 America/Boise. SOURCE ONLY / NOT EXECUTED / UNQUALIFIED.

PURPOSE: classify a D-owned *already committed* effect as a historical
reconciliation candidate WITHOUT using a fresh A0 one-use proof, and WITHOUT
authorizing another effect or authorizing external disclosure of the receipt.

Why: v0.3 record_one_use_effect() verifies A0 commitment BEFORE its historical
lookup; v0.4 OneShotCommitEvidence consumes one proof per instance. A replay
after first effect using the original instance is refused before history lookup.
A new A0 challenge is not automatically appropriate for a historical receipt,
especially after A0 or D revocation. This is a protocol conflict, not a
security PASS. This source does NOT revise or replace the v0.3 implementation.

Non-goals: no signature verification, caller authorization, A0 channel, key
management, fresh authority, durable attempt logging, effect commit, network,
database, deployment entrypoint, or operation against any live device/host.
Inputs here are assumed D-private; Python types do not prove that custody.
This helper MUST NOT be exposed to untrusted external callers.
"""

from __future__ import annotations

from dataclasses import dataclass
import re

ID = re.compile(r"[A-Za-z0-9._:-]{1,96}\Z", re.ASCII)
SHA256 = re.compile(r"[0-9a-f]{64}\Z", re.ASCII)


@dataclass(frozen=True)
class InternalHistoricalEffect:
    # Illustrative in-memory projection of v0.3 D EffectReceipt.
    event_sequence: int
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
class InternalDHistory:
    # Only the future D-owned transaction could produce an authoritative view.
    effects: tuple[InternalHistoricalEffect, ...]
    generation_fences: tuple[int, ...]
    grant_fences: tuple[tuple[str, str, str], ...]
    stopped_runs: tuple[str, ...]


@dataclass(frozen=True)
class InternalHistoricalQuery:
    # ALL fields must be independently derived within D from a previously
    # verified original identity, not a gateway-supplied "verified" object.
    reservation_id: str
    token_sha256: str
    root_id: str
    run_id: str
    episode_id: str
    action_id: str
    grant_id: str
    generation: int


@dataclass(frozen=True)
class InternalClassification:
    status: str
    candidate_effect_sequence: int | None
    post_fence: bool
    release_to_external_caller: bool = False
    authorize_new_effect: bool = False


def _valid_id(value: object) -> bool:
    return type(value) is str and ID.fullmatch(value) is not None


def _valid_digest(value: object) -> bool:
    return type(value) is str and SHA256.fullmatch(value) is not None


def _valid_positive_int(value: object) -> bool:
    return type(value) is int and 1 <= value <= (2**63 - 1)


def _valid_query(query: object) -> bool:
    if type(query) is not InternalHistoricalQuery:
        return False
    return (
        all(_valid_id(getattr(query, f)) for f in (
            "reservation_id", "root_id", "run_id", "episode_id",
            "action_id", "grant_id",
        ))
        and _valid_digest(query.token_sha256)
        and _valid_positive_int(query.generation)
    )


def _valid_effect(effect: object) -> bool:
    if type(effect) is not InternalHistoricalEffect:
        return False
    return (
        all(_valid_id(getattr(effect, f)) for f in (
            "reservation_id", "root_id", "run_id", "episode_id",
            "action_id", "grant_id",
        ))
        and _valid_digest(effect.token_sha256)
        and _valid_positive_int(effect.event_sequence)
        and _valid_positive_int(effect.generation)
        and _valid_positive_int(effect.counter_after)
    )


def _valid_view(view: object) -> bool:
    if type(view) is not InternalDHistory:
        return False
    if not all(
        type(part) is tuple
        for part in (
            view.effects, view.generation_fences, view.grant_fences,
            view.stopped_runs,
        )
    ):
        return False
    if not all(_valid_effect(record) for record in view.effects):
        return False
    if len({r.event_sequence for r in view.effects}) != len(view.effects):
        return False
    if not all(_valid_positive_int(g) for g in view.generation_fences):
        return False
    if not all(_valid_id(run_id) for run_id in view.stopped_runs):
        return False
    if not all(
        type(fence) is tuple and len(fence) == 3
        and all(_valid_id(value) for value in fence)
        for fence in view.grant_fences
    ):
        return False
    if len({r.reservation_id for r in view.effects}) != len(view.effects):
        return False
    if len({
        (r.root_id, r.run_id, r.episode_id, r.action_id)
        for r in view.effects
    }) != len(view.effects):
        return False
    return True


def classify_d_private_history(
    view: InternalDHistory,
    query: InternalHistoricalQuery,
) -> InternalClassification:
    """
    Private consistency classifier, NEVER a receipt-disclosure policy.

    This function has NO permission to make a new effect or externally release
    a receipt. The future D process must separately and independently:
      * record each ingress attempt (including denial) in its durable log;
      * verify a historical ORIGINAL token against D-enrolled historical key
        and snapshot (do NOT mistake current A0 liveness for old validity);
      * authenticate the requesting principal and its receipt-read rights;
      * obtain a D-owned durable view under appropriate transaction isolation;
      * check receipt identity/token digest against immutable D history;
      * release only a permitted historical receipt via a dedicated adapter.
    """
    if not _valid_query(query):
        return InternalClassification("QUERY_INVALID", None, False)
    if not _valid_view(view):
        return InternalClassification("D_HISTORY_UNPROVEN", None, False)

    matches = tuple(
        record for record in view.effects
        if record.reservation_id == query.reservation_id
    )
    if not matches:
        return InternalClassification("HISTORICAL_NOT_FOUND", None, False)

    # The ledger uniqueness check above prevents more than one result.
    record = matches[0]
    if any((
        record.token_sha256 != query.token_sha256,
        record.root_id != query.root_id,
        record.run_id != query.run_id,
        record.episode_id != query.episode_id,
        record.action_id != query.action_id,
        record.grant_id != query.grant_id,
        record.generation != query.generation,
    )):
        return InternalClassification("HISTORICAL_BINDING_CONFLICT", None, False)

    post_fence = (
        query.run_id in view.stopped_runs
        or query.generation in view.generation_fences
        or (query.root_id, query.run_id, query.grant_id) in view.grant_fences
    )
    return InternalClassification(
        status=(
            "D_PRIVATE_HISTORICAL_CANDIDATE_AFTER_FENCE"
            if post_fence else "D_PRIVATE_HISTORICAL_CANDIDATE"
        ),
        candidate_effect_sequence=record.event_sequence,
        post_fence=post_fence,
        release_to_external_caller=False,
        authorize_new_effect=False,
    )


# No __main__, no imports of predecessor model, no internal invocation of
# A0.committed(), no new effect function, no claim to authenticated provenance.
