"""
CERBERUS-001 D2-S2 A0 proof challenge/adapter tests — SOURCE ONLY.

NOT EXECUTED, COMPILED, IMPORTED, OR RUNTIME-QUALIFIED.
The deterministic SHA-512 test-only verifier is NOT Ed25519; it has no
cryptographic authenticity. No key generation, host/network or DB actions.
"""

from __future__ import annotations

from dataclasses import replace
from hashlib import sha256, sha512
import importlib.util
from pathlib import Path
import sys
import unittest


def _load_sibling(name: str, module_id: str):
    spec = importlib.util.spec_from_file_location(
        module_id, Path(__file__).with_name(name)
    )
    if spec is None or spec.loader is None:
        raise RuntimeError("missing source file")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


class TEST_ONLY_NotEd25519:
    def verify(self, key: bytes, message: bytes, signature: bytes) -> bool:
        return signature == sha512(
            b"TEST-ONLY-NOT-ED25519\x00" + key + message
        ).digest()


class TEST_ONLY_FailingProvider:
    def verify(self, key, message, signature):
        raise RuntimeError("unavailable signed receipt provider")


class ProofTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.proofs = _load_sibling(
            "11.04.26 - CERBERUS-001 A0 Commitment Proof Verifier v0.4.py",
            "cerberus_a0_proof_v04_source",
        )
        cls.bridge = _load_sibling(
            "11.04.26 - CERBERUS-001 D Commitment Evidence Adapter v0.4.py",
            "cerberus_d_a0_bridge_v04_source",
        )

    def setUp(self):
        p = self.proofs
        self.key = bytes.fromhex("22" * 32)  # fixture, not a real credential
        self.pinned = p.PinnedProofKey(
            root_id="synthetic-root", key_id="synthetic-proof-key",
            raw_public_key=self.key,
            registered_fingerprint_sha256=sha256(self.key).hexdigest(),
        )
        self.challenge = p.DCommitChallenge(
            nonce_hex="0123456789abcdef" * 2,
            root_id="synthetic-root",
            generation=4, activation_epoch=4,
            registry_digest="a" * 64,
            checkpoint_digest="c" * 64,
            reservation_id="reservation-1",
            reservation_payload_sha256="b" * 64,
            reservation_commit_sequence=11,
            run_id="run-1", episode_id="episode-1",
            action_id="action-1", grant_id="grant-1",
        )
        self.values = {
            "schema": p.SCHEMA,
            "authority_id": "A0",
            "proof_status": "COMMITTED_CURRENT",
            "root_id": self.challenge.root_id,
            "key_id": self.pinned.key_id,
            "generation": self.challenge.generation,
            "activation_epoch": self.challenge.activation_epoch,
            "registry_digest": self.challenge.registry_digest,
            "checkpoint_digest": self.challenge.checkpoint_digest,
            "reservation_id": self.challenge.reservation_id,
            "reservation_payload_sha256":
                self.challenge.reservation_payload_sha256,
            "reservation_commit_sequence":
                self.challenge.reservation_commit_sequence,
            "a0_head_sequence": 14,
            "challenge_nonce": self.challenge.nonce_hex,
            "run_id": self.challenge.run_id,
            "episode_id": self.challenge.episode_id,
            "action_id": self.challenge.action_id,
            "grant_id": self.challenge.grant_id,
        }
        self.verifier = TEST_ONLY_NotEd25519()
        self.proof = self.signed(self.values)

    def signed(self, value):
        p = self.proofs
        raw = p.canonical_bytes(value)
        sig = sha512(
            b"TEST-ONLY-NOT-ED25519\x00"
            + self.key + p.message_to_verify(raw)
        ).digest()
        return p.SignedA0Proof(raw_payload=raw, signature=sig)

    def verify(self, **updates):
        return self.proofs.verify_commit_proof(
            updates.get("proof", self.proof),
            updates.get("challenge", self.challenge),
            updates.get("pinned", self.pinned),
            updates.get("provider", self.verifier),
        )

    def adapter(self, **updates):
        return self.bridge.OneShotCommitEvidence(
            challenge=updates.get("challenge", self.challenge),
            signed_proof=updates.get("proof", self.proof),
            pinned_key=updates.get("pinned", self.pinned),
            signature_provider=updates.get("provider", self.verifier),
            verify_proof=updates.get(
                "verify_proof", self.proofs.verify_commit_proof
            ),
        )

    def invoke(self, port, **args):
        return port.committed(
            args.get("reservation_id", "reservation-1"),
            args.get("sequence", 11),
            args.get("digest", "b" * 64),
        )

    def test_AP01_valid_test_only_response_matches_challenge(self):
        status, receipt = self.verify()
        self.assertEqual(status, "PROOF_VERIFIED_FOR_CHALLENGE")
        self.assertEqual(receipt.reservation_id, "reservation-1")

    def test_AP02_replayed_response_for_different_nonce_refused(self):
        challenge = replace(self.challenge, nonce_hex="f" * 32)
        self.assertEqual(
            self.verify(challenge=challenge)[0], "PROOF_CONTEXT_MISMATCH"
        )

    def test_AP03_changed_generation_refused(self):
        challenge = replace(self.challenge, generation=5)
        self.assertEqual(
            self.verify(challenge=challenge)[0], "PROOF_CONTEXT_MISMATCH"
        )

    def test_AP04_changed_checkpoint_digest_refused(self):
        challenge = replace(self.challenge, checkpoint_digest="d" * 64)
        self.assertEqual(
            self.verify(challenge=challenge)[0], "PROOF_CONTEXT_MISMATCH"
        )

    def test_AP05_mutated_raw_payload_fails_signature(self):
        raw = self.proof.raw_payload
        mutated = raw.replace(b"reservation-1", b"reservation-2")
        self.assertNotEqual(mutated, raw)
        proof = replace(self.proof, raw_payload=mutated)
        self.assertEqual(
            self.verify(proof=proof)[0], "PROOF_CONTEXT_MISMATCH"
        )  # Binding fails first; not evidence of signature verification.

    def test_AP06_invalid_signature_refused(self):
        proof = replace(self.proof, signature=b"\x00" * 64)
        self.assertEqual(
            self.verify(proof=proof)[0], "PROOF_SIGNATURE_INVALID"
        )

    def test_AP07_bad_pinned_fingerprint_refused(self):
        pinned = replace(
            self.pinned, registered_fingerprint_sha256="d" * 64
        )
        self.assertEqual(
            self.verify(pinned=pinned)[0], "TRUST_ANCHOR_UNPROVEN"
        )

    def test_AP08_key_id_substitution_refused(self):
        value = dict(self.values, key_id="attacker-key")
        self.assertEqual(
            self.verify(proof=self.signed(value))[0], "A0_PROOF_KEY_MISMATCH"
        )

    def test_AP09_noncanonical_spacing_refused(self):
        altered = self.proof.raw_payload.replace(b':"', b': "', 1)
        self.assertNotEqual(altered, self.proof.raw_payload)
        p = replace(self.proof, raw_payload=altered)
        self.assertEqual(self.verify(proof=p)[0], "PROOF_MALFORMED")

    def test_AP10_duplicate_json_field_refused(self):
        raw = self.proof.raw_payload
        duplicated = raw[:-1] + b',"root_id":"synthetic-root"}'
        proof = replace(self.proof, raw_payload=duplicated)
        self.assertEqual(self.verify(proof=proof)[0], "PROOF_MALFORMED")

    def test_AP11_boolean_masquerading_as_generation_refused(self):
        value = dict(self.values, generation=True)
        self.assertEqual(
            self.verify(proof=self.signed(value))[0], "PROOF_MALFORMED"
        )

    def test_AP12_authority_head_behind_commit_refused(self):
        value = dict(self.values, a0_head_sequence=10)
        self.assertEqual(
            self.verify(proof=self.signed(value))[0], "PROOF_MALFORMED"
        )

    def test_AP13_missing_crypto_provider_refused(self):
        self.assertEqual(
            self.verify(provider=None)[0],
            "PROOF_SIGNATURE_PROVIDER_UNAVAILABLE",
        )

    def test_AP14_crypto_provider_runtime_failure_refused(self):
        self.assertEqual(
            self.verify(provider=TEST_ONLY_FailingProvider())[0],
            "PROOF_SIGNATURE_PROVIDER_UNAVAILABLE",
        )

    def test_AP15_altered_proof_status_refused(self):
        value = dict(self.values, proof_status="UNKNOWN")
        self.assertEqual(
            self.verify(proof=self.signed(value))[0], "PROOF_MALFORMED"
        )

    def test_AP16_valid_one_shot_adapter_returns_true_once(self):
        adapter = self.adapter()
        self.assertTrue(self.invoke(adapter))
        self.assertFalse(self.invoke(adapter))
        self.assertEqual(
            adapter.result.verification_status,
            "PROOF_VERIFIED_FOR_CHALLENGE",
        )

    def test_AP17_adapter_does_not_accept_other_commit_digest(self):
        adapter = self.adapter()
        self.assertFalse(self.invoke(adapter, digest="f" * 64))
        self.assertFalse(self.invoke(adapter))  # Failed attempt consumed.

    def test_AP18_adapter_refuses_other_reservation_id(self):
        adapter = self.adapter()
        self.assertFalse(
            self.invoke(adapter, reservation_id="reservation-2")
        )
        self.assertEqual(
            adapter.result.verification_status, "COMMIT_ARGUMENTS_MISMATCH"
        )

    def test_AP19_adapter_rejects_missing_challenge_without_crashing(self):
        adapter = self.adapter(challenge=None)
        self.assertFalse(self.invoke(adapter))
        self.assertEqual(
            adapter.result.verification_status, "COMMIT_ARGUMENTS_MISMATCH"
        )

    def test_AP20_adapter_rejects_missing_verifier(self):
        adapter = self.adapter(verify_proof=None)
        self.assertFalse(self.invoke(adapter))
        self.assertEqual(
            adapter.result.verification_status, "PROOF_VERIFIER_UNAVAILABLE"
        )

    def test_AP21_old_checkpoint_statement_cannot_prove_live_freshness(self):
        # The model verifies consistency with the D-owned checkpoint, but
        # cannot tell if an independently managed checkpoint advanced
        # *after* this challenge was created. No security PASS from this.
        result, receipt = self.verify()
        self.assertEqual(result, "PROOF_VERIFIED_FOR_CHALLENGE")
        self.assertEqual(receipt.checkpoint_digest, "c" * 64)

    def test_AP22_all_true_dependency_is_known_unqualified_gap(self):
        def forged(*args):
            return (
                "PROOF_VERIFIED_FOR_CHALLENGE",
                self.proofs.VerifiedProof(
                    reservation_id="reservation-1",
                    reservation_commit_sequence=11,
                    reservation_payload_sha256="b" * 64,
                    challenge_nonce=self.challenge.nonce_hex,
                    proof_sha256="0" * 64,
                    authority_head_sequence=14,
                    checkpoint_digest="c" * 64,
                )
            )
        adapter = self.adapter(verify_proof=forged)
        self.assertTrue(self.invoke(adapter))  # UNQUALIFIED dependence.

    def test_AP23_cross_run_substitution_refused(self):
        changed = replace(self.challenge, run_id="different-run")
        self.assertEqual(
            self.verify(challenge=changed)[0], "PROOF_CONTEXT_MISMATCH"
        )

    def test_AP24_noncanonical_unsigned_payload_length_refused(self):
        proof = replace(
            self.proof,
            raw_payload=self.proof.raw_payload + b" " * 4100,
        )
        self.assertEqual(self.verify(proof=proof)[0], "PROOF_MALFORMED")


    def test_AP25_separate_one_shot_ports_reuse_same_nonce_known_gap(self):
        first = self.adapter()
        second = self.adapter()
        self.assertTrue(self.invoke(first))
        self.assertTrue(self.invoke(second))  # NO shared durable nonce ledger.
        # Separate D effect uniqueness must prevent a second effect; this
        # local port alone is NOT a replay-control guarantee.

    def test_AP26_same_old_checkpoint_after_external_advance_known_gap(self):
        # The external high-watermark is NOT modeled here. A previously
        # signed challenge response can still verify if D keeps the old
        # expected checkpoint; this is NOT proof of fresh authority.
        status1, _ = self.verify()
        status2, _ = self.verify()
        self.assertEqual(
            (status1, status2),
            ("PROOF_VERIFIED_FOR_CHALLENGE",) * 2
        )


if __name__ == "__main__":
    raise SystemExit(
        "CERBERUS tests not authorized for execution by source creation."
    )
