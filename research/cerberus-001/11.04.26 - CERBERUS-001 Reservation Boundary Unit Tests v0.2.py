"""
CERBERUS-001 reservation boundary v0.2 — UNEXECUTED unit-test SOURCE.

The test-only verifier uses SHA-512 as a deterministic fixture convention;
it is NOT Ed25519 and provides NO cryptographic security. No real keys are
created, and this source is not approved for a live or production runtime.

All tests are authored but NOT RUN. No Python import/AST compilation was
performed while constructing this packet.
"""

from __future__ import annotations

from dataclasses import replace
from hashlib import sha256, sha512
import importlib.util
from pathlib import Path
import sys
import unittest


def _load_source():
    """Future authorized tests only; resolves the date-first sibling filename."""
    filename = (
        "11.04.26 - CERBERUS-001 Authenticated Reservation Boundary v0.2.py"
    )
    spec = importlib.util.spec_from_file_location(
        "cerberus_reservation_boundary_source_only_v02",
        Path(__file__).with_name(filename),
    )
    if spec is None or spec.loader is None:
        raise RuntimeError("missing dated source file")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


class TEST_ONLY_NotEd25519Verifier:
    """NEVER use outside these inert source-only semantic test fixtures."""

    @staticmethod
    def _fixture_signature(public_key: bytes, message: bytes) -> bytes:
        return sha512(
            b"TEST-ONLY-NOT-ED25519\x00" + public_key + message
        ).digest()

    def verify(self, public_key: bytes, message: bytes, signature: bytes) -> bool:
        return signature == self._fixture_signature(public_key, message)


class TEST_ONLY_CommitSet:
    """Not remotely sourced, cryptographic, durable, or independent."""

    def __init__(self, entries):
        self.entries = frozenset(entries)

    def committed(self, reservation_id: str, sequence: int, digest: str) -> bool:
        return (reservation_id, sequence, digest) in self.entries


class TEST_ONLY_UnavailableCommit:
    def committed(self, reservation_id, sequence, digest):
        raise RuntimeError("test-only A0 unavailable")


class TEST_ONLY_UnavailableVerifier:
    def verify(self, public_key, message, signature):
        raise RuntimeError("test-only verifier unavailable")


class ReservationBoundaryTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.m = _load_source()

    def setUp(self):
        m = self.m
        self.public_key = bytes.fromhex("10" * 32)  # TEST fixture, not a live key.
        self.verifier = TEST_ONLY_NotEd25519Verifier()
        self.pinned = m.PinnedA0Key(
            root_id="synthetic-root",
            key_id="synthetic-a0-key",
            public_key=self.public_key,
            expected_fingerprint_sha256=sha256(self.public_key).hexdigest(),
        )
        self.context = m.ExpectedEffect(
            root_id="synthetic-root",
            generation=4,
            activation_epoch=4,
            registry_digest="a" * 64,
            manifest_id="manifest-4",
            manifest_sha256="b" * 64,
            run_id="run-1",
            episode_id="episode-1",
            trial_id="trial-1",
            attempt_id="attempt-1",
            action_id="action-1",
            grant_id="grant-1",
            operation="mock.counter_increment",
            request_sha256="c" * 64,
            reservation_id="reservation-1",
        )
        self.payload = {
            "schema": m.SCHEMA,
            "authority_id": "A0",
            "decision": "RESERVED",
            "root_id": self.context.root_id,
            "key_id": self.pinned.key_id,
            "generation": self.context.generation,
            "activation_epoch": self.context.activation_epoch,
            "registry_digest": self.context.registry_digest,
            "manifest_id": self.context.manifest_id,
            "manifest_sha256": self.context.manifest_sha256,
            "run_id": self.context.run_id,
            "episode_id": self.context.episode_id,
            "trial_id": self.context.trial_id,
            "attempt_id": self.context.attempt_id,
            "action_id": self.context.action_id,
            "grant_id": self.context.grant_id,
            "operation": self.context.operation,
            "request_sha256": self.context.request_sha256,
            "reservation_id": self.context.reservation_id,
            "reservation_nonce": "nonce-test-1",
            "commit_sequence": 42,
        }
        self.state = m.EffectState()
        self.token = self.make_token(self.payload)
        self.oracle = self.oracle_for(self.token)

    def make_token(self, payload):
        m = self.m
        raw = m.canonical_bytes(payload)
        sig = self.verifier._fixture_signature(
            self.public_key, m.signing_message(raw)
        )
        return m.SignedReservation(
            payload_bytes=raw, signature_bytes=sig, key_id=self.pinned.key_id
        )

    def oracle_for(self, token):
        return TEST_ONLY_CommitSet(
            {("reservation-1", 42, sha256(token.payload_bytes).hexdigest())}
        )

    def call(
        self, token=None, pinned=None, context=None, verifier=None,
        oracle=None, state=None,
    ):
        return self.m.verify_and_apply(
            self.state if state is None else state,
            self.token if token is None else token,
            self.pinned if pinned is None else pinned,
            self.context if context is None else context,
            self.verifier if verifier is None else verifier,
            self.oracle if oracle is None else oracle,
        )

    def test_RB01_valid_synthetic_test_fixture_effect(self):
        response = self.call()
        self.assertEqual(response.status, "EFFECT_COMMITTED")
        self.assertEqual(response.effect.counter_after, 1)

    def test_RB02_unsigned_structural_token_is_rejected(self):
        unsigned = replace(
            self.token, signature_bytes=b"\x00" * 64
        )
        response = self.call(token=unsigned)
        self.assertEqual(response.status, "SIGNATURE_INVALID")

    def test_RB03_wrong_pinned_fingerprint_refuses(self):
        wrong = replace(
            self.pinned, expected_fingerprint_sha256="0" * 64
        )
        self.assertEqual(
            self.call(pinned=wrong).status, "TRUST_ANCHOR_UNPROVEN"
        )

    def test_RB04_wrong_key_id_refuses(self):
        swapped = replace(self.token, key_id="attacker-key")
        self.assertEqual(
            self.call(token=swapped).status, "A0_KEY_OR_ROOT_MISMATCH"
        )

    def test_RB05_wrong_root_refuses(self):
        altered = dict(self.payload, root_id="wrong-root")
        self.assertEqual(
            self.call(token=self.make_token(altered)).status,
            "A0_KEY_OR_ROOT_MISMATCH",
        )

    def test_RB06_old_generation_against_new_D_context_refuses(self):
        newer = replace(self.context, generation=5)
        self.assertEqual(
            self.call(context=newer).status, "REQUEST_BINDING_MISMATCH"
        )

    def test_RB07_wrong_action_id_refuses(self):
        changed = replace(self.context, action_id="other-action")
        self.assertEqual(
            self.call(context=changed).status, "REQUEST_BINDING_MISMATCH"
        )

    def test_RB08_wrong_manifest_hash_refuses(self):
        changed = replace(self.context, manifest_sha256="f" * 64)
        self.assertEqual(
            self.call(context=changed).status, "REQUEST_BINDING_MISMATCH"
        )

    def test_RB09_not_allowed_operation_refuses(self):
        altered = dict(self.payload, operation="mock.purchase")
        self.assertEqual(
            self.call(token=self.make_token(altered)).status,
            "ENVELOPE_INVALID",
        )

    def test_RB10_extra_field_refuses(self):
        altered = dict(self.payload, claimed_access="all")
        self.assertEqual(
            self.call(token=self.make_token(altered)).status,
            "ENVELOPE_INVALID",
        )

    def test_RB11_duplicate_raw_JSON_key_refuses(self):
        raw = self.token.payload_bytes
        duplicated = raw[:-1] + b',"root_id":"synthetic-root"}'
        altered = replace(self.token, payload_bytes=duplicated)
        self.assertEqual(
            self.call(token=altered).status, "ENVELOPE_INVALID"
        )

    def test_RB12_noncanonical_spacing_refuses(self):
        raw = self.token.payload_bytes
        spaced = raw.replace(b':"', b': "', 1)
        self.assertNotEqual(raw, spaced)
        self.assertEqual(
            self.call(token=replace(self.token, payload_bytes=spaced)).status,
            "ENVELOPE_INVALID",
        )

    def test_RB13_boolean_masquerading_as_integer_refuses(self):
        altered = dict(self.payload, generation=True)
        self.assertEqual(
            self.call(token=self.make_token(altered)).status,
            "ENVELOPE_INVALID",
        )

    def test_RB14_missing_issuer_commitment_refuses(self):
        missing = TEST_ONLY_CommitSet(set())
        self.assertEqual(
            self.call(oracle=missing).status, "A0_COMMITMENT_UNPROVEN"
        )

    def test_RB15_commitment_store_unavailable_refuses(self):
        self.assertEqual(
            self.call(oracle=TEST_ONLY_UnavailableCommit()).status,
            "A0_COMMITMENT_UNPROVEN",
        )

    def test_RB16_verifier_provider_unavailable_refuses(self):
        self.assertEqual(
            self.call(verifier=TEST_ONLY_UnavailableVerifier()).status,
            "SIGNATURE_PROVIDER_UNAVAILABLE",
        )

    def test_RB17_D_generation_fence_prevents_old_effect(self):
        fenced = self.m.fence_generation(self.state, 4)
        self.assertEqual(
            self.call(state=fenced).status, "GENERATION_FENCED"
        )

    def test_RB18_D_global_stop_prevents_effect(self):
        stopped = self.m.stop_run(self.state, "run-1")
        self.assertEqual(
            self.call(state=stopped).status, "EFFECT_STOP_FENCED"
        )

    def test_RB19_valid_duplicate_dispatch_is_detected_not_prevented(self):
        first = self.call()
        second = self.call(state=first.state)
        self.assertEqual(second.status, "EFFECT_COMMITTED")
        self.assertEqual(len(second.state.effects), 2)  # Must score BLOCK.

    def test_RB20_mutated_authenticated_bytes_fail_signature(self):
        raw = self.token.payload_bytes
        changed = raw.replace(b"nonce-test-1", b"nonce-test-2")
        self.assertNotEqual(raw, changed)
        altered = replace(self.token, payload_bytes=changed)
        self.assertEqual(
            self.call(token=altered).status, "SIGNATURE_INVALID"
        )

    def test_RB21_wrong_authority_decision_refuses(self):
        changed = dict(self.payload, decision="DENIED")
        self.assertEqual(
            self.call(token=self.make_token(changed)).status,
            "ENVELOPE_INVALID"
        )

    def test_RB22_negative_or_noninteger_commit_sequence_refuses(self):
        for value in (-1, "42", 0):
            altered = dict(self.payload, commit_sequence=value)
            self.assertEqual(
                self.call(token=self.make_token(altered)).status,
                "ENVELOPE_INVALID",
            )

    def test_RB23_length_limit_refuses(self):
        oversized = replace(
            self.token, payload_bytes=self.token.payload_bytes + b" " * 4100
        )
        self.assertEqual(
            self.call(token=oversized).status, "ENVELOPE_INVALID"
        )

    def test_RB24_cross_run_reuse_is_bound_to_D_context(self):
        other_run = replace(self.context, run_id="run-2")
        self.assertEqual(
            self.call(context=other_run).status, "REQUEST_BINDING_MISMATCH"
        )


if __name__ == "__main__":
    raise SystemExit(
        "No CERBERUS executable tests authorized by source creation alone."
    )
