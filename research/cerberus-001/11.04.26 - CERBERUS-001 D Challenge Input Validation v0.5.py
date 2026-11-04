"""
CERBERUS-001 — D challenge input validator v0.5 (same v0.4 proof wire format)
SOURCE ONLY; NOT IMPORTED, COMPILED, EXECUTED, OR INDEPENDENTLY QUALIFIED.

Source-only refinement: v0.4 accepted Python equality of malformed D expected
values (e.g., True == 1) and dereferenced unvalidated pinned objects.
This candidate requires exact D-owned context and anchor types. It does NOT
establish actual D ownership, key provenance, real crypto, or freshness.

Pure verification of a signed challenge response. No generation of keys or
nonces, no network, no filesystem or database, no live service. Not a D runtime
security boundary until independently pinned ownership, real crypto,
authenticated transport, durable challenge issuance and checkpoint freshness
are implemented. Caller MUST NOT be allowed to choose D's trust inputs.

A valid signed A0 response proves only a statement signed by its pinned key.
It DOES NOT alone prove up-to-date authority: replayed checkpoints, A0 rollback
and revocation-vs-effect races remain separately gated by independent A0
monotonic checkpoint and D-local generation/grant/STOP fences.

Created November 4, 2026 (America/Boise).
"""

from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
from hmac import compare_digest
import json
import re
from typing import Protocol

SCHEMA = "CERBERUS-001-A0-COMMIT-PROOF-v0.4"
DOMAIN = b"CERBERUS-001\x00A0-COMMIT-PROOF-v0.4\x00"
MAX_PROOF_BYTES = 4096
SIGNATURE_BYTES = 64
ED25519_PUBLIC_KEY_BYTES = 32
HEX_64 = re.compile(r"[0-9a-f]{64}\Z", re.ASCII)
HEX_32 = re.compile(r"[0-9a-f]{32}\Z", re.ASCII)
ID = re.compile(r"[A-Za-z0-9._:-]{1,96}\Z", re.ASCII)
IDENTIFIERS = (
    "root_id", "key_id", "reservation_id", "run_id", "episode_id",
    "action_id", "grant_id",
)
DIGESTS = (
    "registry_digest", "reservation_payload_sha256", "checkpoint_digest",
)
INTEGERS = (
    "generation", "activation_epoch", "reservation_commit_sequence",
    "a0_head_sequence",
)
FIELDS = frozenset((
    "schema", "authority_id", "proof_status", "root_id", "key_id",
    "generation", "activation_epoch", "registry_digest", "reservation_id",
    "reservation_payload_sha256", "reservation_commit_sequence",
    "a0_head_sequence", "checkpoint_digest", "challenge_nonce",
    "run_id", "episode_id", "action_id", "grant_id",
))


class ProofInvalid(ValueError):
    """Malformed or non-canonical A0 proof source bytes."""


class ProviderUnavailable(RuntimeError):
    """Verified signing provider absent/failed; no permissive fallback."""


class Ed25519Verifier(Protocol):
    def verify(self, public_key: bytes, message: bytes, signature: bytes) -> bool:
        """Must return True only for valid Ed25519 signature of exact bytes."""


@dataclass(frozen=True)
class PinnedProofKey:
    root_id: str
    key_id: str
    raw_public_key: bytes
    registered_fingerprint_sha256: str


@dataclass(frozen=True)
class DCommitChallenge:
    """Must be generated and retained by D under a unique durable nonce."""
    nonce_hex: str
    root_id: str
    generation: int
    activation_epoch: int
    registry_digest: str
    checkpoint_digest: str
    reservation_id: str
    reservation_payload_sha256: str
    reservation_commit_sequence: int
    run_id: str
    episode_id: str
    action_id: str
    grant_id: str


@dataclass(frozen=True)
class SignedA0Proof:
    raw_payload: bytes
    signature: bytes


@dataclass(frozen=True)
class VerifiedProof:
    reservation_id: str
    reservation_commit_sequence: int
    reservation_payload_sha256: str
    challenge_nonce: str
    proof_sha256: str
    authority_head_sequence: int
    checkpoint_digest: str


def _distinct_pairs(pairs: list[tuple[str, object]]) -> dict:
    value = {}
    for name, item in pairs:
        if name in value:
            raise ProofInvalid("duplicate JSON field")
        value[name] = item
    return value


def canonical_bytes(value: dict) -> bytes:
    try:
        return json.dumps(
            value, sort_keys=True, separators=(",", ":"),
            ensure_ascii=True, allow_nan=False,
        ).encode("ascii")
    except (ValueError, TypeError, UnicodeError) as exc:
        raise ProofInvalid("unencodable proof fields") from exc


def decode_strict(raw: bytes) -> dict:
    if type(raw) is not bytes or not 1 <= len(raw) <= MAX_PROOF_BYTES:
        raise ProofInvalid("bad raw payload size or type")
    try:
        value = json.loads(raw.decode("ascii"), object_pairs_hook=_distinct_pairs)
    except (ValueError, UnicodeError) as exc:
        raise ProofInvalid("unparseable proof") from exc
    if type(value) is not dict or frozenset(value) != FIELDS:
        raise ProofInvalid("wrong field set")
    if raw != canonical_bytes(value):
        raise ProofInvalid("noncanonical proof bytes")
    if (
        value["schema"] != SCHEMA
        or value["authority_id"] != "A0"
        or value["proof_status"] != "COMMITTED_CURRENT"
    ):
        raise ProofInvalid("wrong domain or decision")
    for name in IDENTIFIERS:
        if type(value[name]) is not str or ID.fullmatch(value[name]) is None:
            raise ProofInvalid("invalid identifier " + name)
    for name in DIGESTS:
        if type(value[name]) is not str or HEX_64.fullmatch(value[name]) is None:
            raise ProofInvalid("invalid digest " + name)
    if (
        type(value["challenge_nonce"]) is not str
        or HEX_32.fullmatch(value["challenge_nonce"]) is None
    ):
        raise ProofInvalid("invalid 128-bit challenge nonce")
    for name in INTEGERS:
        if (
            type(value[name]) is not int
            or not 1 <= value[name] <= 2**63 - 1
        ):
            raise ProofInvalid("invalid authority integer " + name)
    if value["a0_head_sequence"] < value["reservation_commit_sequence"]:
        raise ProofInvalid("impossible authority sequence")
    return value


def message_to_verify(raw: bytes) -> bytes:
    if type(raw) is not bytes or not 1 <= len(raw) <= MAX_PROOF_BYTES:
        raise ProofInvalid("wrong proof size")
    return DOMAIN + len(raw).to_bytes(4, "big") + raw


def _validated_d_challenge(expected: object) -> bool:
    """Exact D challenge shape; Python equality is not enough."""
    if type(expected) is not DCommitChallenge:
        return False
    for name in (
        "root_id", "reservation_id", "run_id", "episode_id",
        "action_id", "grant_id",
    ):
        value = getattr(expected, name)
        if type(value) is not str or ID.fullmatch(value) is None:
            return False
    for name in (
        "registry_digest", "checkpoint_digest",
        "reservation_payload_sha256",
    ):
        value = getattr(expected, name)
        if type(value) is not str or HEX_64.fullmatch(value) is None:
            return False
    if (
        type(expected.nonce_hex) is not str
        or HEX_32.fullmatch(expected.nonce_hex) is None
    ):
        return False
    for name in (
        "generation", "activation_epoch", "reservation_commit_sequence",
    ):
        value = getattr(expected, name)
        if type(value) is not int or not 1 <= value <= 2**63 - 1:
            return False
    return True


def _validated_trust_anchor(pinned: object) -> bool:
    """Exact pin shape; actual T0 enrollment must be independently witnessed."""
    if type(pinned) is not PinnedProofKey:
        return False
    if (
        type(pinned.root_id) is not str
        or ID.fullmatch(pinned.root_id) is None
        or type(pinned.key_id) is not str
        or ID.fullmatch(pinned.key_id) is None
        or type(pinned.raw_public_key) is not bytes
        or len(pinned.raw_public_key) != ED25519_PUBLIC_KEY_BYTES
        or type(pinned.registered_fingerprint_sha256) is not str
        or HEX_64.fullmatch(pinned.registered_fingerprint_sha256) is None
    ):
        return False
    return compare_digest(
        sha256(pinned.raw_public_key).hexdigest(),
        pinned.registered_fingerprint_sha256,
    )


class CryptographyEd25519Adapter:
    """Optional future dependency; this source never imports it at module load."""
    def verify(self, public_key: bytes, message: bytes, signature: bytes) -> bool:
        try:
            from cryptography.exceptions import InvalidSignature
            from cryptography.hazmat.primitives.asymmetric.ed25519 import (
                Ed25519PublicKey,
            )
        except ImportError as exc:
            raise ProviderUnavailable("pinned crypto provider unavailable") from exc
        try:
            Ed25519PublicKey.from_public_bytes(public_key).verify(
                signature, message
            )
            return True
        except (InvalidSignature, TypeError, ValueError):
            return False


def verify_commit_proof(
    proof: SignedA0Proof,
    expected: DCommitChallenge,
    pinned: PinnedProofKey,
    provider: Ed25519Verifier | None,
) -> tuple[str, VerifiedProof | None]:
    """
    No implicit trust in the proof issuer, current registry or caller-chosen
    expected context. Real D must own/pin expected, key, provider and durable
    issuance of each unique nonce; an injected fixture cannot establish it.
    """
    if not _validated_d_challenge(expected):
        return "PROOF_CONTEXT_UNPROVEN", None
    if not _validated_trust_anchor(pinned):
        return "TRUST_ANCHOR_UNPROVEN", None
    if type(proof) is not SignedA0Proof:
        return "PROOF_MALFORMED", None
    try:
        raw = proof.raw_payload
        value = decode_strict(raw)
    except (AttributeError, TypeError, ProofInvalid):
        return "PROOF_MALFORMED", None

    if (
        value["root_id"] != pinned.root_id
        or value["key_id"] != pinned.key_id
    ):
        return "A0_PROOF_KEY_MISMATCH", None

    if (
        type(proof.signature) is not bytes
        or len(proof.signature) != SIGNATURE_BYTES
    ):
        return "PROOF_SIGNATURE_INVALID", None
    checks = (
        ("challenge_nonce", "nonce_hex"),
        ("root_id", "root_id"),
        ("generation", "generation"),
        ("activation_epoch", "activation_epoch"),
        ("registry_digest", "registry_digest"),
        ("checkpoint_digest", "checkpoint_digest"),
        ("reservation_id", "reservation_id"),
        ("reservation_payload_sha256", "reservation_payload_sha256"),
        ("reservation_commit_sequence", "reservation_commit_sequence"),
        ("run_id", "run_id"),
        ("episode_id", "episode_id"),
        ("action_id", "action_id"),
        ("grant_id", "grant_id"),
    )
    try:
        if any(
            value[field] != getattr(expected, context)
            for field, context in checks
        ):
            return "PROOF_CONTEXT_MISMATCH", None
    except (AttributeError, TypeError):
        return "PROOF_CONTEXT_UNPROVEN", None
    if provider is None:
        return "PROOF_SIGNATURE_PROVIDER_UNAVAILABLE", None
    try:
        valid = provider.verify(
            pinned.raw_public_key, message_to_verify(raw), proof.signature
        )
    except Exception:
        return "PROOF_SIGNATURE_PROVIDER_UNAVAILABLE", None
    if valid is not True:
        return "PROOF_SIGNATURE_INVALID", None
    return (
        "PROOF_VERIFIED_FOR_CHALLENGE",
        VerifiedProof(
            reservation_id=value["reservation_id"],
            reservation_commit_sequence=value["reservation_commit_sequence"],
            reservation_payload_sha256=value["reservation_payload_sha256"],
            challenge_nonce=value["challenge_nonce"],
            proof_sha256=sha256(raw).hexdigest(),
            authority_head_sequence=value["a0_head_sequence"],
            checkpoint_digest=value["checkpoint_digest"],
        ),
    )


# NO network client, nonce generator, issuer, signature generation, key
# provisioning, DB, durable transaction or device interface. The result
# must NOT be used as permission to execute a real effect.
# Validator v0.5 preserves proof wire schema and signing bytes v0.4.
