"""
CERBERUS-001 D2-S2 challenge input validation — prospective tests only.
SOURCE-ONLY; UNIMPORTED, UNCOMPILED, UNEXECUTED, NOT AUTHORITY.
TEST_ONLY_NotEd25519 is a deliberate fixture, NOT a crypto verifier.
"""

from __future__ import annotations

from dataclasses import replace
from hashlib import sha256, sha512
import importlib.util
from pathlib import Path
import sys
from types import SimpleNamespace
import unittest


def load_candidate():
    path = Path(__file__).with_name(
        "11.04.26 - CERBERUS-001 D Challenge Input Validation v0.5.py"
    )
    spec = importlib.util.spec_from_file_location("cerberus_challenge_v05", path)
    if spec is None or spec.loader is None:
        raise RuntimeError("missing source candidate")
    mod = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = mod
    spec.loader.exec_module(mod)
    return mod


class TEST_ONLY_NotEd25519:
    def verify(self, public_key, message, signature):
        return signature == sha512(
            b"TEST-ONLY-NOT-ED25519\x00" + public_key + message
        ).digest()


class ChallengeValidationSourceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.model = load_candidate()

    def setUp(self):
        m = self.model
        self.key = bytes.fromhex("22" * 32)  # NOT a real credential
        self.pinned = m.PinnedProofKey(
            root_id="synthetic-root",
            key_id="synthetic-key",
            raw_public_key=self.key,
            registered_fingerprint_sha256=sha256(self.key).hexdigest(),
        )
        self.challenge = m.DCommitChallenge(
            nonce_hex="0123456789abcdef" * 2,
            root_id="synthetic-root", generation=1, activation_epoch=1,
            registry_digest="a" * 64, checkpoint_digest="c" * 64,
            reservation_id="reservation-1",
            reservation_payload_sha256="b" * 64,
            reservation_commit_sequence=11,
            run_id="run-1", episode_id="episode-1",
            action_id="action-1", grant_id="grant-1",
        )
        self.payload = {
            "schema": m.SCHEMA,
            "authority_id": "A0",
            "proof_status": "COMMITTED_CURRENT",
            "root_id": self.challenge.root_id,
            "key_id": self.pinned.key_id,
            "generation": self.challenge.generation,
            "activation_epoch": self.challenge.activation_epoch,
            "registry_digest": self.challenge.registry_digest,
            "checkpoint_digest": self.challenge.checkpoint_digest,
            "reservation_id": self.challenge.reservation_id,
            "reservation_payload_sha256": self.challenge.reservation_payload_sha256,
            "reservation_commit_sequence": self.challenge.reservation_commit_sequence,
            "a0_head_sequence": 12,
            "challenge_nonce": self.challenge.nonce_hex,
            "run_id": self.challenge.run_id,
            "episode_id": self.challenge.episode_id,
            "action_id": self.challenge.action_id,
            "grant_id": self.challenge.grant_id,
        }
        self.provider = TEST_ONLY_NotEd25519()
        self.proof = self.sign(self.payload)

    def sign(self, payload):
        raw = self.model.canonical_bytes(payload)
        signature = sha512(
            b"TEST-ONLY-NOT-ED25519\x00"
            + self.key + self.model.message_to_verify(raw)
        ).digest()
        return self.model.SignedA0Proof(raw_payload=raw, signature=signature)

    def check(self, **kwargs):
        return self.model.verify_commit_proof(
            kwargs.get("proof", self.proof),
            kwargs.get("expected", self.challenge),
            kwargs.get("pinned", self.pinned),
            kwargs.get("provider", self.provider),
        )[0]

    def test_CV01_fully_typed_synthetic_happy_path(self):
        self.assertEqual(self.check(), "PROOF_VERIFIED_FOR_CHALLENGE")

    def test_CV02_boolean_expected_generation_cannot_equal_one(self):
        bad = replace(self.challenge, generation=True)
        self.assertEqual(self.check(expected=bad), "PROOF_CONTEXT_UNPROVEN")

    def test_CV03_boolean_expected_activation_epoch_cannot_equal_one(self):
        bad = replace(self.challenge, activation_epoch=True)
        self.assertEqual(self.check(expected=bad), "PROOF_CONTEXT_UNPROVEN")

    def test_CV04_float_expected_commit_sequence_cannot_equal_integer(self):
        bad = replace(self.challenge, reservation_commit_sequence=11.0)
        self.assertEqual(self.check(expected=bad), "PROOF_CONTEXT_UNPROVEN")

    def test_CV05_bad_d_digest_in_expected_context(self):
        bad = replace(self.challenge, registry_digest="A" * 64)
        self.assertEqual(self.check(expected=bad), "PROOF_CONTEXT_UNPROVEN")

    def test_CV06_bad_d_nonce_grammar_even_if_proof_well_formed(self):
        bad = replace(self.challenge, nonce_hex="G" * 32)
        self.assertEqual(self.check(expected=bad), "PROOF_CONTEXT_UNPROVEN")

    def test_CV07_duck_typed_expected_context_cannot_impose_authority(self):
        pseudo = SimpleNamespace(**vars(self.challenge))
        self.assertEqual(self.check(expected=pseudo), "PROOF_CONTEXT_UNPROVEN")

    def test_CV08_missing_expected_context_fails_closed(self):
        self.assertEqual(self.check(expected=None), "PROOF_CONTEXT_UNPROVEN")

    def test_CV09_missing_t0_pinned_anchor_fails_closed(self):
        self.assertEqual(self.check(pinned=None), "TRUST_ANCHOR_UNPROVEN")

    def test_CV10_duck_typed_anchor_rejected_even_with_matching_fields(self):
        pseudo = SimpleNamespace(**vars(self.pinned))
        self.assertEqual(self.check(pinned=pseudo), "TRUST_ANCHOR_UNPROVEN")

    def test_CV11_wrong_public_key_length_rejected(self):
        bad = replace(self.pinned, raw_public_key=b"\x01" * 31)
        self.assertEqual(self.check(pinned=bad), "TRUST_ANCHOR_UNPROVEN")

    def test_CV12_valid_d_generation_mismatch_still_refused(self):
        bad = replace(self.challenge, generation=2)
        self.assertEqual(self.check(expected=bad), "PROOF_CONTEXT_MISMATCH")

    def test_CV13_missing_crypto_provider_remains_fail_closed(self):
        self.assertEqual(self.check(provider=None), "PROOF_SIGNATURE_PROVIDER_UNAVAILABLE")

    def test_CV14_missing_or_wrong_proof_type_fails_closed(self):
        self.assertEqual(self.check(proof=None), "PROOF_MALFORMED")


if __name__ == "__main__":
    raise SystemExit("Source-only test definitions: execution not authorized.")
