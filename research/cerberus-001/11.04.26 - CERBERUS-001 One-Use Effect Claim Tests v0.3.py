"""
CERBERUS-001 D one-use source model — proposed unit tests, NOT EXECUTED.

Both sibling sources have date-first filenames; any future test runner must
explicitly import them. They use a deterministic SHA-512 comparison fixture
marked TEST_ONLY, NOT Ed25519. No real keys, networks, databases, or services.

These tests deliberately include known-unqualified dependency-injection paths;
a green unit test is not containment qualification.
"""

from __future__ import annotations

from dataclasses import replace
from hashlib import sha256, sha512
import importlib.util
from pathlib import Path
import sys
import unittest

_USE_DEFAULT = object()


def load_source(filename: str, module_name: str):
    """For a future independently authorized test run; never called here."""
    spec = importlib.util.spec_from_file_location(
        module_name, Path(__file__).with_name(filename)
    )
    if spec is None or spec.loader is None:
        raise RuntimeError("Missing frozen reference source")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


class TEST_ONLY_NotEd25519Verifier:
    def verify(self, public_key: bytes, message: bytes, signature: bytes) -> bool:
        return signature == sha512(
            b"TEST-ONLY-NOT-ED25519\x00" + public_key + message
        ).digest()


class TEST_ONLY_A0CommitSet:
    """NOT independent, signed, live, serialized or durable."""

    def __init__(self, records):
        self.records = frozenset(records)

    def committed(self, reservation_id: str, sequence: int, digest: str) -> bool:
        return (reservation_id, sequence, digest) in self.records


class TEST_ONLY_UnavailableCommit:
    def committed(self, reservation_id, sequence, digest):
        raise RuntimeError("Synthetic A0 commitment inaccessible")


class TEST_ONLY_AlwaysTrueCommit:
    def committed(self, reservation_id, sequence, digest):
        return True  # Deliberate insecure dependency, not production evidence.


class OneUseEffectClaimTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.boundary = load_source(
            "11.04.26 - CERBERUS-001 Authenticated Reservation Boundary v0.2.py",
            "cerberus_v02_source_only",
        )
        cls.once = load_source(
            "11.04.26 - CERBERUS-001 One-Use Effect Claim Model v0.3.py",
            "cerberus_v03_source_only",
        )

    def setUp(self):
        b = self.boundary
        self.public_key = bytes.fromhex("10" * 32)  # Test fixture only
        self.pinned = b.PinnedA0Key(
            root_id="synthetic-root",
            key_id="synthetic-a0-key",
            public_key=self.public_key,
            expected_fingerprint_sha256=sha256(self.public_key).hexdigest(),
        )
        self.expected = b.ExpectedEffect(
            root_id="synthetic-root", generation=4, activation_epoch=4,
            registry_digest="a" * 64,
            manifest_id="manifest-4", manifest_sha256="b" * 64,
            run_id="run-1", episode_id="episode-1", trial_id="trial-1",
            attempt_id="attempt-1", action_id="action-1", grant_id="grant-1",
            operation="mock.counter_increment", request_sha256="c" * 64,
            reservation_id="reservation-1",
        )
        self.fields = {
            "schema": b.SCHEMA, "authority_id": "A0",
            "decision": "RESERVED", "key_id": self.pinned.key_id,
            "root_id": self.expected.root_id,
            "generation": self.expected.generation,
            "activation_epoch": self.expected.activation_epoch,
            "registry_digest": self.expected.registry_digest,
            "manifest_id": self.expected.manifest_id,
            "manifest_sha256": self.expected.manifest_sha256,
            "run_id": self.expected.run_id,
            "episode_id": self.expected.episode_id,
            "trial_id": self.expected.trial_id,
            "attempt_id": self.expected.attempt_id,
            "action_id": self.expected.action_id,
            "grant_id": self.expected.grant_id,
            "operation": self.expected.operation,
            "request_sha256": self.expected.request_sha256,
            "reservation_id": self.expected.reservation_id,
            "reservation_nonce": "nonce-1", "commit_sequence": 11,
        }
        self.verifier = TEST_ONLY_NotEd25519Verifier()
        self.token = self.token_for(self.fields)
        self.oracle = self.oracle_for(self.token, self.fields)
        self.ledger = self.once.Ledger()

    def token_for(self, fields):
        b = self.boundary
        raw = b.canonical_bytes(fields)
        sig = sha512(
            b"TEST-ONLY-NOT-ED25519\x00"
            + self.public_key + b.signing_message(raw)
        ).digest()
        return b.SignedReservation(
            payload_bytes=raw, signature_bytes=sig,
            key_id=self.pinned.key_id,
        )

    def oracle_for(self, token, fields):
        return TEST_ONLY_A0CommitSet({
            (
                fields["reservation_id"],
                fields["commit_sequence"],
                sha256(token.payload_bytes).hexdigest(),
            )
        })

    def submit(
        self, *, ledger=_USE_DEFAULT, token=_USE_DEFAULT,
        expected=_USE_DEFAULT, pinned=_USE_DEFAULT,
        verifier=_USE_DEFAULT, oracle=_USE_DEFAULT, checker=_USE_DEFAULT,
    ):
        return self.once.record_one_use_effect(
            self.ledger if ledger is _USE_DEFAULT else ledger,
            self.token if token is _USE_DEFAULT else token,
            self.pinned if pinned is _USE_DEFAULT else pinned,
            self.expected if expected is _USE_DEFAULT else expected,
            self.verifier if verifier is _USE_DEFAULT else verifier,
            self.oracle if oracle is _USE_DEFAULT else oracle,
            self.boundary.verify_envelope if checker is _USE_DEFAULT else checker,
        )

    def first(self):
        outcome = self.submit()
        self.assertEqual(outcome.status, "EFFECT_COMMITTED")
        self.assertTrue(outcome.committed_now)
        return outcome

    def test_EC01_one_authenticated_test_fixture_commits_one_effect(self):
        o = self.first()
        self.assertEqual((len(o.ledger.attempts), len(o.ledger.effects)), (1, 1))

    def test_EC02_identical_retry_observed_but_no_second_effect(self):
        first = self.first()
        again = self.submit(ledger=first.ledger)
        self.assertEqual(again.status, "ALREADY_COMMITTED_HISTORICAL_ONLY")
        self.assertFalse(again.committed_now)
        self.assertEqual(len(again.ledger.attempts), 2)
        self.assertEqual(len(again.ledger.effects), 1)
        self.assertEqual(again.historical_effect, first.historical_effect)

    def test_EC03_retry_after_run_stop_returns_history_only(self):
        first = self.first()
        stopped, _ = self.once.fence_run(first.ledger, "run-1")
        again = self.submit(ledger=stopped)
        self.assertEqual(
            again.status, "ALREADY_COMMITTED_AFTER_FENCE_HISTORICAL_ONLY"
        )
        self.assertFalse(again.committed_now)
        self.assertEqual(len(again.ledger.effects), 1)

    def test_EC04_retry_after_grant_fence_returns_history_only(self):
        first = self.first()
        fenced, _ = self.once.fence_grant(
            first.ledger, "synthetic-root", "run-1", "grant-1"
        )
        again = self.submit(ledger=fenced)
        self.assertEqual(
            again.status, "ALREADY_COMMITTED_AFTER_FENCE_HISTORICAL_ONLY"
        )
        self.assertFalse(again.committed_now)

    def test_EC05_invalid_signed_token_attempt_still_observed(self):
        bad = replace(self.token, signature_bytes=b"\x00" * 64)
        one = self.submit(token=bad)
        two = self.submit(ledger=one.ledger, token=bad)
        self.assertEqual(two.status, "SIGNATURE_INVALID")
        self.assertEqual((len(two.ledger.attempts), len(two.ledger.effects)), (2, 0))

    def test_EC06_missing_A0_commitment_observed_and_refused(self):
        denied = self.submit(oracle=None)
        self.assertEqual(denied.status, "A0_COMMITMENT_UNPROVEN")
        self.assertEqual(len(denied.ledger.attempts), 1)
        self.assertFalse(denied.committed_now)

    def test_EC07_wrong_pinned_fingerprint_no_effect(self):
        wrong = replace(self.pinned, expected_fingerprint_sha256="f" * 64)
        denied = self.submit(pinned=wrong)
        self.assertEqual(denied.status, "TRUST_ANCHOR_UNPROVEN")
        self.assertEqual(len(denied.ledger.effects), 0)

    def test_EC08_wrong_D_owned_generation_no_effect(self):
        denied = self.submit(expected=replace(self.expected, generation=5))
        self.assertEqual(denied.status, "REQUEST_BINDING_MISMATCH")
        self.assertEqual(len(denied.ledger.effects), 0)

    def test_EC09_global_run_stop_before_effect(self):
        stopped, status = self.once.fence_run(self.ledger, "run-1")
        self.assertEqual(status, "RUN_STOP_FENCED")
        denied = self.submit(ledger=stopped)
        self.assertEqual(denied.status, "RUN_STOP_FENCED")
        self.assertEqual(len(denied.ledger.effects), 0)

    def test_EC10_generation_fence_before_effect(self):
        fenced, _ = self.once.fence_generation(self.ledger, 4, "rotation-4-5")
        denied = self.submit(ledger=fenced)
        self.assertEqual(denied.status, "GENERATION_FENCED")
        self.assertEqual(len(denied.ledger.effects), 0)

    def test_EC11_grant_fence_before_effect(self):
        fenced, _ = self.once.fence_grant(
            self.ledger, "synthetic-root", "run-1", "grant-1"
        )
        denied = self.submit(ledger=fenced)
        self.assertEqual(denied.status, "GRANT_FENCED")
        self.assertEqual(len(denied.ledger.effects), 0)

    def test_EC12_grant_fence_after_effect_preserves_historical_receipt(self):
        first = self.first()
        fenced, _ = self.once.fence_grant(
            first.ledger, "synthetic-root", "run-1", "grant-1"
        )
        again = self.submit(ledger=fenced)
        self.assertEqual(again.historical_effect, first.historical_effect)
        self.assertEqual(len(again.ledger.effects), 1)

    def test_EC13_different_reservation_same_action_no_second_effect(self):
        first = self.first()
        new_fields = dict(
            self.fields, reservation_id="reservation-2",
            attempt_id="attempt-2", reservation_nonce="nonce-2",
            commit_sequence=12,
        )
        token = self.token_for(new_fields)
        expected = replace(
            self.expected, reservation_id="reservation-2",
            attempt_id="attempt-2",
        )
        again = self.submit(
            ledger=first.ledger, token=token, expected=expected,
            oracle=self.oracle_for(token, new_fields),
        )
        self.assertEqual(again.status, "ACTION_ALREADY_COMMITTED")
        self.assertEqual(len(again.ledger.effects), 1)

    def test_EC14_same_reservation_id_different_action_conflicts(self):
        first = self.first()
        new_fields = dict(
            self.fields, action_id="action-2", attempt_id="attempt-2",
            reservation_nonce="nonce-2", commit_sequence=12,
        )
        token = self.token_for(new_fields)
        expected = replace(
            self.expected, action_id="action-2", attempt_id="attempt-2"
        )
        again = self.submit(
            ledger=first.ledger, token=token, expected=expected,
            oracle=self.oracle_for(token, new_fields),
        )
        self.assertEqual(again.status, "RESERVATION_ID_CONFLICT")
        self.assertEqual(len(again.ledger.effects), 1)

    def test_EC15_same_reservation_id_different_run_conflicts(self):
        first = self.first()
        new_fields = dict(
            self.fields, run_id="run-2", action_id="action-2",
            attempt_id="attempt-2", reservation_nonce="nonce-2",
            commit_sequence=12,
        )
        token = self.token_for(new_fields)
        expected = replace(
            self.expected, run_id="run-2", action_id="action-2",
            attempt_id="attempt-2",
        )
        again = self.submit(
            ledger=first.ledger, token=token, expected=expected,
            oracle=self.oracle_for(token, new_fields),
        )
        self.assertEqual(again.status, "RESERVATION_ID_CONFLICT")
        self.assertEqual(len(again.ledger.effects), 1)

    def test_EC16_lost_effect_ack_retry_is_history_not_reexecution(self):
        first = self.first()
        retry = self.submit(ledger=first.ledger)
        self.assertEqual(
            retry.status, "ALREADY_COMMITTED_HISTORICAL_ONLY"
        )
        self.assertIsNotNone(retry.historical_effect)
        self.assertEqual(retry.historical_effect.sequence, 2)

    def test_EC17_invalid_valid_and_replay_are_three_observed_attempts(self):
        bad = replace(self.token, signature_bytes=b"\xff" * 64)
        one = self.submit(token=bad)
        two = self.submit(ledger=one.ledger)
        three = self.submit(ledger=two.ledger)
        self.assertEqual(
            self.once.ledger_facts(three.ledger)["observed_attempts_at_D"], 3
        )
        self.assertEqual(len(three.ledger.effects), 1)

    def test_EC18_causal_sequences_are_monotonic(self):
        first = self.first()
        self.assertEqual(first.ledger.attempts[0].sequence, 1)
        self.assertEqual(first.ledger.effects[0].sequence, 2)
        replay = self.submit(ledger=first.ledger)
        self.assertEqual(replay.ledger.attempts[1].sequence, 3)
        fenced, _ = self.once.fence_run(replay.ledger, "run-1")
        self.assertEqual(fenced.stopped_runs[0].sequence, 4)
        later = self.submit(ledger=fenced)
        self.assertEqual(later.ledger.attempts[-1].sequence, 5)

    def test_EC19_fabricated_verifier_output_cannot_mismatch_D_context(self):
        def lying(*args):
            return (
                "VERIFIED_SIGNATURE_AND_BINDINGS",
                dict(self.fields, action_id="forged-action"),
            )
        denied = self.submit(checker=lying)
        self.assertEqual(
            denied.status, "D_CONTEXT_OR_VERIFICATION_OUTPUT_INVALID"
        )
        self.assertEqual(len(denied.ledger.effects), 0)

    def test_EC20_missing_verification_interface_is_observed(self):
        denied = self.submit(checker=None)
        self.assertEqual(denied.status, "VERIFICATION_UNAVAILABLE")
        self.assertEqual(len(denied.ledger.attempts), 1)

    def test_EC21_exception_in_verifier_is_denied_and_observed(self):
        def unavailable(*args):
            raise RuntimeError("synthetic failure")
        denied = self.submit(checker=unavailable)
        self.assertEqual(denied.status, "VERIFICATION_UNAVAILABLE")
        self.assertEqual(len(denied.ledger.effects), 0)

    def test_EC22_commitment_oracle_exception_is_denied(self):
        denied = self.submit(oracle=TEST_ONLY_UnavailableCommit())
        self.assertEqual(denied.status, "A0_COMMITMENT_UNPROVEN")
        self.assertEqual(len(denied.ledger.attempts), 1)

    def test_EC23_grant_fence_idempotence_does_not_reopen(self):
        first, status = self.once.fence_grant(
            self.ledger, "synthetic-root", "run-1", "grant-1"
        )
        second, repeated = self.once.fence_grant(
            first, "synthetic-root", "run-1", "grant-1"
        )
        self.assertEqual(repeated, "GRANT_FENCE_ALREADY_COMMITTED")
        self.assertEqual(second, first)
        self.assertEqual(status, "GRANT_FENCED")

    def test_EC24_generation_fence_conflict_refuses_rewrite(self):
        first, _ = self.once.fence_generation(self.ledger, 4, "proposal-a")
        repeat, status = self.once.fence_generation(first, 4, "proposal-a")
        changed, conflict = self.once.fence_generation(
            first, 4, "proposal-b"
        )
        self.assertEqual(status, "GENERATION_FENCE_ALREADY_COMMITTED")
        self.assertEqual(conflict, "GENERATION_FENCE_CONFLICT")
        self.assertEqual(repeat, first)
        self.assertEqual(changed, first)

    def test_EC25_stop_fence_idempotence_does_not_reopen(self):
        first, status = self.once.fence_run(self.ledger, "run-1")
        second, repeated = self.once.fence_run(first, "run-1")
        self.assertEqual(status, "RUN_STOP_FENCED")
        self.assertEqual(repeated, "RUN_STOP_ALREADY_COMMITTED")
        self.assertEqual(second, first)

    def test_EC26_untrusted_always_true_oracle_is_known_gap(self):
        result = self.submit(oracle=TEST_ONLY_AlwaysTrueCommit())
        # Proof of dependency trust assumption, NOT independent A0 authority.
        self.assertEqual(result.status, "EFFECT_COMMITTED")


if __name__ == "__main__":
    raise SystemExit(
        "CERBERUS source-only tests were not authorized for execution."
    )
