"""
CERBERUS-001 — authenticated reservation boundary, SOURCE DESIGN v0.2.

NO EXECUTION AUTHORIZED, NO RUNTIME TESTS, NO REAL KEYS, NO NETWORK,
NO PERSISTENCE, NO DEPLOYMENT. Not a production authorization service.

Implements a pure *proposed* D-side effect gate:
  (a) reject malformed/noncanonical reservation envelopes;
  (b) verify against an externally pinned A0 Ed25519 public-key fingerprint;
  (c) require an injected verifier and an independent A0 commit-evidence port;
  (d) match every signed field to a D-owned expected action context;
  (e) check D-local generation and global-stop fences at effect transition;
  (f) intentionally expose duplicate *authenticated* dispatches by counting both.

A Python object, injected verifier, and in-memory set are not independent
trust domains. The Ed25519 adapter requires the separately pinned dependency
`cryptography`, not installed or tested by this source packet. No keys are
generated or provisioned. The legacy v0.1 D effect function remains unsafe to
expose directly, even if this wrapper is correct.

Date: November 4, 2026 (America/Boise).
"""

from __future__ import annotations

from dataclasses import dataclass, replace
from hashlib import sha256
import hmac
import json
import re
from typing import Protocol

SCHEMA = "CERBERUS-001-A0-RESERVATION-v0.2"
DOMAIN = b"CERBERUS-001\x00A0-RESERVATION-v0.2\x00"
MAX_PAYLOAD_BYTES = 4096
EXPECTED_SIGNATURE_BYTES = 64
EXPECTED_ED25519_KEY_BYTES = 32
IDENTIFIER = re.compile(r"[A-Za-z0-9._:-]{1,96}\Z", re.ASCII)
DIGEST = re.compile(r"[0-9a-f]{64}\Z", re.ASCII)

FIELDS = frozenset((
    "schema", "authority_id", "decision", "root_id", "generation",
    "activation_epoch", "registry_digest", "key_id", "manifest_id",
    "manifest_sha256", "run_id", "episode_id", "trial_id",
    "attempt_id", "action_id", "grant_id", "operation",
    "request_sha256", "reservation_id", "reservation_nonce",
    "commit_sequence",
))
IDENTIFIER_FIELDS = (
    "root_id", "key_id", "manifest_id", "run_id", "episode_id",
    "trial_id", "attempt_id", "action_id", "grant_id",
    "reservation_id", "reservation_nonce",
)
DIGEST_FIELDS = ("registry_digest", "manifest_sha256", "request_sha256")
INTEGER_FIELDS = ("generation", "activation_epoch", "commit_sequence")
BOUND_FIELDS = (
    "root_id", "generation", "activation_epoch", "registry_digest",
    "manifest_id", "manifest_sha256", "run_id", "episode_id",
    "trial_id", "attempt_id", "action_id", "grant_id", "operation",
    "request_sha256", "reservation_id",
)


class EnvelopeInvalid(ValueError):
    """The candidate bytes are not a valid canonical signed payload."""


class SignatureProviderUnavailable(RuntimeError):
    """No independently approved cryptographic verification implementation."""


class SignatureVerifier(Protocol):
    def verify(self, public_key: bytes, message: bytes, signature: bytes) -> bool:
        """Return True ONLY for a valid Ed25519 signature of exact bytes."""


class CommitEvidence(Protocol):
    def committed(self, reservation_id: str, sequence: int, digest: str) -> bool:
        """Independent authenticated durable A0 commit-evidence lookup.

        The caller must implement a real trust and freshness boundary. A
        locally constructed dictionary is NOT such an implementation.
        """


@dataclass(frozen=True)
class PinnedA0Key:
    """Expected fingerprint MUST originate from independently enrolled T0."""
    root_id: str
    key_id: str
    public_key: bytes
    expected_fingerprint_sha256: str


@dataclass(frozen=True)
class SignedReservation:
    """Only these exact bytes are signed; no caller-provided dict is trusted."""
    payload_bytes: bytes
    signature_bytes: bytes
    key_id: str


@dataclass(frozen=True)
class ExpectedEffect:
    """D-owned context; the gateway MUST NOT be its sole source of truth."""
    root_id: str
    generation: int
    activation_epoch: int
    registry_digest: str
    manifest_id: str
    manifest_sha256: str
    run_id: str
    episode_id: str
    trial_id: str
    attempt_id: str
    action_id: str
    grant_id: str
    operation: str
    request_sha256: str
    reservation_id: str


@dataclass(frozen=True)
class EffectReceipt:
    reservation_id: str
    run_id: str
    generation: int
    sequence: int
    counter_after: int


@dataclass(frozen=True)
class EffectState:
    sequence: int = 0
    effects: tuple[EffectReceipt, ...] = ()
    generation_fences: tuple[int, ...] = ()
    stopped_runs: tuple[str, ...] = ()


@dataclass(frozen=True)
class Decision:
    state: EffectState
    status: str
    effect: EffectReceipt | None = None


class CryptographyEd25519Verifier:
    """Optional provider; not imported, installed, or exercised here."""

    def verify(self, public_key: bytes, message: bytes, signature: bytes) -> bool:
        try:
            from cryptography.exceptions import InvalidSignature
            from cryptography.hazmat.primitives.asymmetric.ed25519 import (
                Ed25519PublicKey,
            )
        except ImportError as exc:
            raise SignatureProviderUnavailable(
                "cryptography Ed25519 provider is not installed/approved"
            ) from exc
        try:
            Ed25519PublicKey.from_public_bytes(public_key).verify(
                signature, message
            )
            return True
        except (InvalidSignature, ValueError, TypeError):
            return False


def _without_duplicate_fields(pairs: list[tuple[str, object]]) -> dict:
    obj = {}
    for key, value in pairs:
        if key in obj:
            raise EnvelopeInvalid("duplicate key")
        obj[key] = value
    return obj


def canonical_bytes(payload: dict) -> bytes:
    """Deterministic ASCII JSON for a tightly restricted value schema."""
    try:
        return json.dumps(
            payload, sort_keys=True, separators=(",", ":"),
            ensure_ascii=True, allow_nan=False,
        ).encode("ascii")
    except (TypeError, ValueError, UnicodeError) as exc:
        raise EnvelopeInvalid("nonserializable payload") from exc


def _decode_strict(raw: bytes) -> dict:
    if type(raw) is not bytes or not (1 <= len(raw) <= MAX_PAYLOAD_BYTES):
        raise EnvelopeInvalid("invalid payload bytes or length")
    try:
        text = raw.decode("ascii", errors="strict")
        value = json.loads(text, object_pairs_hook=_without_duplicate_fields)
    except (UnicodeError, json.JSONDecodeError, ValueError) as exc:
        raise EnvelopeInvalid("malformed JSON") from exc

    if type(value) is not dict or frozenset(value.keys()) != FIELDS:
        raise EnvelopeInvalid("missing or extra fields")
    if raw != canonical_bytes(value):
        raise EnvelopeInvalid("noncanonical byte encoding")

    if value["schema"] != SCHEMA or value["authority_id"] != "A0":
        raise EnvelopeInvalid("wrong envelope domain")
    if value["decision"] != "RESERVED":
        raise EnvelopeInvalid("not a committed reservation decision")

    for name in IDENTIFIER_FIELDS:
        field = value[name]
        if type(field) is not str or IDENTIFIER.fullmatch(field) is None:
            raise EnvelopeInvalid("invalid identifier: " + name)
    if value["operation"] != "mock.counter_increment":
        raise EnvelopeInvalid("operation not in synthetic allowlist")
    for name in DIGEST_FIELDS:
        field = value[name]
        if type(field) is not str or DIGEST.fullmatch(field) is None:
            raise EnvelopeInvalid("invalid sha256 digest: " + name)
    for name in INTEGER_FIELDS:
        field = value[name]
        if type(field) is not int or field <= 0 or field > 2**63 - 1:
            raise EnvelopeInvalid("invalid positive integer: " + name)
    return value


def signing_message(raw: bytes) -> bytes:
    """Domain-separated, exact-length message; not an HTTP encoding."""
    if len(raw) > MAX_PAYLOAD_BYTES:
        raise EnvelopeInvalid("payload too long")
    return DOMAIN + len(raw).to_bytes(4, "big") + raw


def verify_envelope(
    token: SignedReservation,
    pinned: PinnedA0Key,
    expected: ExpectedEffect,
    verifier: SignatureVerifier | None,
) -> tuple[str, dict | None]:
    """Fail closed unless exact signed fields and externally pinned key match."""
    try:
        value = _decode_strict(token.payload_bytes)
    except (EnvelopeInvalid, AttributeError, TypeError):
        return "ENVELOPE_INVALID", None

    if (
        type(token.key_id) is not str
        or token.key_id != pinned.key_id
        or value["key_id"] != pinned.key_id
        or value["root_id"] != pinned.root_id
    ):
        return "A0_KEY_OR_ROOT_MISMATCH", None

    if (
        type(pinned.public_key) is not bytes
        or len(pinned.public_key) != EXPECTED_ED25519_KEY_BYTES
        or type(pinned.expected_fingerprint_sha256) is not str
        or DIGEST.fullmatch(pinned.expected_fingerprint_sha256) is None
        or not hmac.compare_digest(
            sha256(pinned.public_key).hexdigest(),
            pinned.expected_fingerprint_sha256,
        )
    ):
        return "TRUST_ANCHOR_UNPROVEN", None

    if type(token.signature_bytes) is not bytes or (
        len(token.signature_bytes) != EXPECTED_SIGNATURE_BYTES
    ):
        return "SIGNATURE_INVALID", None

    for name in BOUND_FIELDS:
        if value[name] != getattr(expected, name):
            return "REQUEST_BINDING_MISMATCH", None

    if verifier is None:
        return "SIGNATURE_PROVIDER_UNAVAILABLE", None
    try:
        signed = signing_message(token.payload_bytes)
        valid = verifier.verify(pinned.public_key, signed, token.signature_bytes)
    except (SignatureProviderUnavailable, RuntimeError, ValueError, TypeError):
        return "SIGNATURE_PROVIDER_UNAVAILABLE", None
    if valid is not True:
        return "SIGNATURE_INVALID", None
    return "VERIFIED_SIGNATURE_AND_BINDINGS", value


def fence_generation(state: EffectState, generation: int) -> EffectState:
    """Pure logical D fence; real D must commit it durably with effects."""
    if generation in state.generation_fences:
        return state
    return replace(
        state,
        sequence=state.sequence + 1,
        generation_fences=state.generation_fences + (generation,),
    )


def stop_run(state: EffectState, run_id: str) -> EffectState:
    """Pure logical D global STOP; does not stop A0 admissions."""
    if run_id in state.stopped_runs:
        return state
    return replace(
        state,
        sequence=state.sequence + 1,
        stopped_runs=state.stopped_runs + (run_id,),
    )


def verify_and_apply(
    state: EffectState,
    token: SignedReservation,
    pinned: PinnedA0Key,
    expected: ExpectedEffect,
    verifier: SignatureVerifier | None,
    commit_evidence: CommitEvidence | None,
) -> Decision:
    """Proposed D-only effect entry; do not expose raw v0.1 model effect API.

    The signed token must be checked against a *separately authenticated*
    durable A0 commitment. An absent oracle refuses all effects. The model
    presumes the transition is serialized with D fences; Python is not a
    cross-process lock or durable transaction.

    Duplicate authentic dispatches are intentionally counted twice. This
    demonstrates that a signature check is NOT exactly-once protection.
    """
    status, value = verify_envelope(token, pinned, expected, verifier)
    if status != "VERIFIED_SIGNATURE_AND_BINDINGS" or value is None:
        return Decision(state=state, status=status)
    if commit_evidence is None:
        return Decision(state=state, status="A0_COMMITMENT_UNPROVEN")
    try:
        digest = sha256(token.payload_bytes).hexdigest()
        committed = commit_evidence.committed(
            value["reservation_id"], value["commit_sequence"], digest
        )
    except (RuntimeError, ValueError, TypeError, AttributeError):
        return Decision(state=state, status="A0_COMMITMENT_UNPROVEN")
    if committed is not True:
        return Decision(state=state, status="A0_COMMITMENT_UNPROVEN")

    if value["run_id"] in state.stopped_runs:
        return Decision(state=state, status="EFFECT_STOP_FENCED")
    if value["generation"] in state.generation_fences:
        return Decision(state=state, status="GENERATION_FENCED")

    receipt = EffectReceipt(
        reservation_id=value["reservation_id"],
        run_id=value["run_id"],
        generation=value["generation"],
        sequence=state.sequence + 1,
        counter_after=len(state.effects) + 1,
    )
    return Decision(
        state=replace(
            state,
            sequence=receipt.sequence,
            effects=state.effects + (receipt,),
        ),
        status="EFFECT_COMMITTED",
        effect=receipt,
    )


# Intentionally no __main__, persistence, networking, key creation,
# deployment or device interface. All actual security claims remain blocked.
