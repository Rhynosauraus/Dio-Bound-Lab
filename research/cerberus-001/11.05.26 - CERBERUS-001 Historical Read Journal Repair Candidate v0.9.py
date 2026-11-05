"""
CERBERUS-001 — D historical-receipt READ ATTEMPT JOURNAL v0.9 CANDIDATE.
2026-11-05 · America/Boise · SOURCE ONLY, NEVER EXECUTED.

Additive FZ01/FZ13 source repair candidate derived from frozen v0.7.
It does not establish durability, independent custody, or runtime PASS.

Strict design limit: this function proves only an IN-MEMORY pure transition
assuming D provides a genuine journal; it is NOT a durable log, witness,
authenticated requester, historical A0 issuer archive, read authorization,
crypto verifier, or effect transaction. It NEVER calls a prior effect, the
v0.6 classifier, or a receipt release endpoint.

A real D must atomically persist this stage before consulting historical
records and must separately account for ingress which never reached D.
A valid syntactic principal claim is NOT an authenticated principal.
Historical token possession is NEVER itself receipt-read authorization.
No access to device, network, filesystem, process, DB or external systems.
"""

from __future__ import annotations

from dataclasses import dataclass, replace
from hashlib import sha256
import re

ID = re.compile(r"[A-Za-z0-9._:-]{1,96}\Z", re.ASCII)
DIGEST = re.compile(r"[0-9a-f]{64}\Z", re.ASCII)
MAX_TOKEN_BYTES = 4096
MAX_MODEL_RECORDS = 10000
MAX_SEQUENCE = (2**63) - 1

LOG_STATUSES = frozenset((
    "D_PRIVATE_READ_ATTEMPT_LOGGED_HOLD",
    "D_PRIVATE_READ_ATTEMPT_LOGGED_INVALID",
))


@dataclass(frozen=True)
class ReadIntent:
    """UNTRUSTED; every identifier is a claim, not an authority decision."""
    original_token_bytes: bytes
    reservation_id_claim: str
    principal_id_claim: str
    receipt_grant_id_claim: str
    original_issuer_key_id_claim: str


@dataclass(frozen=True)
class ObservedReadAttempt:
    read_sequence: int
    token_sha256: str
    raw_byte_length: int
    reservation_claim_sha256: str
    principal_claim_sha256: str
    grant_claim_sha256: str
    issuer_key_claim_sha256: str
    status: str


@dataclass(frozen=True)
class DPrivateReadJournal:
    read_sequence: int = 0
    attempts: tuple[ObservedReadAttempt, ...] = ()


@dataclass(frozen=True)
class JournalOutcome:
    journal: object  # Preserve invalid evidence without falsely validating it.
    status: str
    recorded_in_model: bool
    durable_commit_proven: bool = False
    permit_historical_lookup: bool = False
    permit_receipt_release: bool = False
    permit_new_effect: bool = False
    custody_gap: bool = True


def _id(value: object) -> bool:
    return type(value) is str and ID.fullmatch(value) is not None


def _digest(value: object) -> bool:
    return type(value) is str and DIGEST.fullmatch(value) is not None


def _positive(value: object) -> bool:
    return type(value) is int and 1 <= value <= MAX_SEQUENCE


_MISSING = object()

def _safe_field(value: object, field: str) -> object:
    """Malformed exact-class records fail validation rather than raising."""
    try:
        # These exact-class dataclasses store supplied values in __dict__.
        # Do not use getattr(default): journal dataclasses have class-level
        # defaults which could hide a deleted/corrupted instance field.
        owned_fields = object.__getattribute__(value, "__dict__")
        if type(owned_fields) is not dict or field not in owned_fields:
            return _MISSING
        return owned_fields[field]
    except Exception:
        return _MISSING

def _valid_prior_attempt(value: object, expected_index: int) -> bool:
    if type(value) is not ObservedReadAttempt:
        return False
    seq = _safe_field(value, "read_sequence")
    raw_length = _safe_field(value, "raw_byte_length")
    status = _safe_field(value, "status")
    return (
        _positive(seq) and seq == expected_index
        and all(_digest(_safe_field(value, key)) for key in (
            "token_sha256", "reservation_claim_sha256",
            "principal_claim_sha256", "grant_claim_sha256",
            "issuer_key_claim_sha256",
        ))
        and type(raw_length) is int and raw_length >= -1
        and type(status) is str and status in LOG_STATUSES
    )

def _valid_journal(journal: object) -> bool:
    if type(journal) is not DPrivateReadJournal:
        return False
    seq = _safe_field(journal, "read_sequence")
    attempts = _safe_field(journal, "attempts")
    if (
        type(seq) is not int or not 0 <= seq < MAX_SEQUENCE
        or type(attempts) is not tuple
        or len(attempts) != seq
        or len(attempts) >= MAX_MODEL_RECORDS
    ):
        return False
    return all(
        _valid_prior_attempt(row, index)
        for index, row in enumerate(attempts, 1)
    )

def _safe_claim_hash(value: object) -> str:
    # Never logs raw requester/reservation/grant/key-claim identifiers.
    # Invalid claims use a fixed marker and an invalid-input status.
    data = value.encode("ascii") if _id(value) else b""
    return sha256(data).hexdigest()


def record_d_private_read_attempt(
    journal: DPrivateReadJournal,
    intent: object,
) -> JournalOutcome:
    """
    Pure source model for D-internal attempt record creation ONLY.

    The return value cannot claim actual durable persistence: downstream
    classification, active principal-rights checks, historical issuer-key
    verification, and any disclosure must be separate protected interfaces.
    """
    if not _valid_journal(journal):
        # There is no safe place to append: treat custody as GAP/UNKNOWN.
        # A real ingress witness must still retain this lost attempt.
        return JournalOutcome(
            journal=journal,
            status="D_READ_JOURNAL_UNPROVEN",
            recorded_in_model=False,
        )
    # Reject foreign objects before resolving any attribute. A property
    # lookup on attacker-supplied Python objects can run arbitrary methods.
    correct_class = type(intent) is ReadIntent
    if correct_class:
        raw = _safe_field(intent, "original_token_bytes")
        reservation = _safe_field(intent, "reservation_id_claim")
        principal = _safe_field(intent, "principal_id_claim")
        grant = _safe_field(intent, "receipt_grant_id_claim")
        issuer = _safe_field(intent, "original_issuer_key_id_claim")
    else:
        raw, reservation, principal, grant, issuer = (
            None, None, None, None, None
        )

    raw_valid = type(raw) is bytes and 1 <= len(raw) <= MAX_TOKEN_BYTES
    complete = (
        correct_class and raw_valid and
        all(_id(item) for item in (reservation, principal, grant, issuer))
    )
    row = ObservedReadAttempt(
        read_sequence=journal.read_sequence + 1,
        token_sha256=sha256(raw if raw_valid else b"").hexdigest(),
        raw_byte_length=len(raw) if type(raw) is bytes else -1,
        reservation_claim_sha256=_safe_claim_hash(reservation),
        principal_claim_sha256=_safe_claim_hash(principal),
        grant_claim_sha256=_safe_claim_hash(grant),
        issuer_key_claim_sha256=_safe_claim_hash(issuer),
        status=(
            "D_PRIVATE_READ_ATTEMPT_LOGGED_HOLD"
            if complete else "D_PRIVATE_READ_ATTEMPT_LOGGED_INVALID"
        ),
    )
    next_journal = replace(
        journal,
        read_sequence=row.read_sequence,
        attempts=journal.attempts + (row,),
    )
    return JournalOutcome(
        journal=next_journal,
        status=row.status,
        recorded_in_model=True,
        # The pure return is NOT a durability receipt or authenticated
        # authority; no next-stage lookup or disclosure is permitted.
    )


# Not an execution entrypoint. No __main__, I/O, import of v0.6, effect
# function, token signature check, source of truth or privilege assertion.
