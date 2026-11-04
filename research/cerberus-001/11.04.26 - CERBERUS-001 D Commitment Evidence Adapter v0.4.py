"""
CERBERUS-001 — source-only D commitment evidence adapter v0.4.

UNEXECUTED, UNREVIEWED, NOT DEPLOYABLE.

This adapter bridges the v0.3 D `A0CommitEvidence.committed(id,seq,digest)`
interface to a *proposed* verifier of a challenge-bound signed A0 response.
It is intentionally ONE-SHOT, even on failed verification. A later request
must obtain a fresh D-owned challenge and separately sourced A0 response.

IMPORTANT SECURITY LIMITS:
- Caller-supplied verifier, trust key, challenge and proof do not establish
  independently pinned D ownership or actual A0 source authentication.
- D still lacks real nonces, immutable challenge registry, physical trust,
  durable storage, externally fresh checkpoint and real signature provider.
- The module is never imported/executed here. No keys/network/filesystem/DB.
- An old signed proof with matching nonce may be authentic but stale if an
  independent checkpoint advanced; D-local grant/generation/STOP fences and
  an external anti-rollback authority still control effect-time validity.
- There is no cryptographically privileged constructor in Python. Only the
  eventual separate D process with its own pinned config could enforce that.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable

CommitProofVerifier = Callable[
    [Any, Any, Any, Any],
    tuple[str, Any | None],
]


@dataclass(frozen=True)
class ModelPortReceipt:
    reservation_id: str
    commit_sequence: int
    payload_sha256: str
    verification_status: str
    consumed: bool


class OneShotCommitEvidence:
    """
    Source-only adapter. Provider MUST be owned by the protected D process.

    `verify_proof` must be the frozen and independently audited
    `verify_commit_proof` function from the sibling v0.4 proof module.
    The builder-side dependency injection used here makes this an untrusted
    model if the caller can choose the provider.
    """

    def __init__(
        self,
        *,
        challenge: Any,
        signed_proof: Any,
        pinned_key: Any,
        signature_provider: Any,
        verify_proof: CommitProofVerifier | None,
    ) -> None:
        self._challenge = challenge
        self._signed_proof = signed_proof
        self._pinned_key = pinned_key
        self._signature_provider = signature_provider
        self._verify_proof = verify_proof
        self._used = False
        self.result = None

    def committed(
        self, reservation_id: str, sequence: int, payload_sha256: str
    ) -> bool:
        if self._used:
            return False
        self._used = True  # Also consume malformed/failed attempts.

        try:
            expected_id = self._challenge.reservation_id
            expected_sequence = self._challenge.reservation_commit_sequence
            expected_digest = self._challenge.reservation_payload_sha256
            arguments_match = (
                type(reservation_id) is str
                and type(sequence) is int
                and sequence > 0
                and type(payload_sha256) is str
                and type(expected_id) is str
                and type(expected_sequence) is int
                and type(expected_digest) is str
                and reservation_id == expected_id
                and sequence == expected_sequence
                and payload_sha256 == expected_digest
            )
        except Exception:
            arguments_match = False
        if not arguments_match:
            self.result = ModelPortReceipt(
                reservation_id=reservation_id if type(reservation_id) is str else "",
                commit_sequence=sequence if type(sequence) is int else -1,
                payload_sha256=payload_sha256 if type(payload_sha256) is str else "",
                verification_status="COMMIT_ARGUMENTS_MISMATCH",
                consumed=True,
            )
            return False

        if self._verify_proof is None:
            status, verified = "PROOF_VERIFIER_UNAVAILABLE", None
        else:
            try:
                status, verified = self._verify_proof(
                    self._signed_proof, self._challenge, self._pinned_key,
                    self._signature_provider,
                )
            except Exception:
                status, verified = "PROOF_VERIFIER_UNAVAILABLE", None

        accepted = (
            status == "PROOF_VERIFIED_FOR_CHALLENGE"
            and verified is not None
            and getattr(verified, "reservation_id", None) == reservation_id
            and getattr(verified, "reservation_commit_sequence", None) == sequence
            and getattr(verified, "reservation_payload_sha256", None)
            == payload_sha256
        )
        self.result = ModelPortReceipt(
            reservation_id=reservation_id,
            commit_sequence=sequence,
            payload_sha256=payload_sha256,
            verification_status=status if type(status) is str else "INVALID_STATUS",
            consumed=True,
        )
        return accepted is True


# No live A0 client, no nonce generator, no keys, no network, no entrypoint.
# Physical D administration and independent proof custody remain unassigned.
