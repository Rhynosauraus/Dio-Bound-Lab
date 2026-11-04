"""
CERBERUS-001 D2-S2 proposed unit tests v0.1.

NOT EXECUTED. No tests, services, credentials or device commands were run by
the authoring process. A later authorized examiner may run this inert suite
in an independently designated disposable/off-host environment.

Technical note: dynamic import is used only because the user-facing source
filename follows MM.DD.YY - Short Descriptive Title.py.
"""

from __future__ import annotations

from dataclasses import replace
from pathlib import Path
import importlib.util
import sys
import unittest

SOURCE_FILE = Path(__file__).with_name(
    "11.04.26 - CERBERUS-001 Deterministic State Model v0.1.py"
)


def load_reference_module():
    """Used only if these tests are actually run under later authorization."""
    spec = importlib.util.spec_from_file_location(
        "cerberus_d2_source_only_reference_v01", SOURCE_FILE
    )
    if spec is None or spec.loader is None:
        raise RuntimeError("Reference source not found in same directory")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


# Module loading is defined here but not invoked until a real test class
# is instantiated under an explicitly authorized future test runner.
class ModelSourceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.m = load_reference_module()

    def setUp(self):
        m = self.m
        self.manifest4 = m.Manifest("m4", "digest-m4", "run-1", 4, 4, "registry-g4")
        self.manifest5 = m.Manifest("m5", "digest-m5", "run-1", 5, 5, "registry-g5")
        self.grant4 = m.Grant(
            "grant4", "run-1", "episode-1", "action4", "m4",
            "mock.counter_increment", 4
        )
        self.grant5 = m.Grant(
            "grant5", "run-1", "episode-1", "action5", "m5",
            "mock.counter_increment", 5
        )
        self.a0 = m.Authority(
            root_id="synthetic-root-0",
            generation=4,
            activation_epoch=4,
            registry_digest="registry-g4",
            approved_manifests=(self.manifest4, self.manifest5),
            approved_grants=(self.grant4, self.grant5),
        )
        self.d = m.Witness()
        self.release4 = m.ReleaseRequest(
            "release-4", "synthetic-root-0", "run-1", "m4",
            "digest-m4", 4, 4, "registry-g4"
        )
        self.release5 = m.ReleaseRequest(
            "release-5", "synthetic-root-0", "run-1", "m5",
            "digest-m5", 5, 5, "registry-g5"
        )
        self.req4 = m.AdmissionRequest(
            "reservation4", "synthetic-root-0", "run-1", "episode-1",
            "trial-1", "attempt-1", "action4", "grant4", "m4",
            "digest-m4", "mock.counter_increment", "request-digest-4",
            4, 4, "registry-g4"
        )
        self.req5 = m.AdmissionRequest(
            "reservation5", "synthetic-root-0", "run-1", "episode-1",
            "trial-2", "attempt-2", "action5", "grant5", "m5",
            "digest-m5", "mock.counter_increment", "request-digest-5",
            5, 5, "registry-g5"
        )

    def release(self, request=None):
        self.a0, status, receipt = self.m.accept_release_if_current(
            self.a0, self.release4 if request is None else request
        )
        self.assertEqual(status, "RELEASE_ACCEPTED")
        self.assertIsNotNone(receipt)
        return receipt

    def reserve(self, request=None):
        self.a0, status, token = self.m.reserve_if_current(
            self.a0, self.req4 if request is None else request
        )
        self.assertEqual(status, "RESERVED")
        self.assertIsNotNone(token)
        return token

    def rotate(self):
        self.a0, status = self.m.prepare_rotation(
            self.a0, "proposal-4-5", "registry-g5"
        )
        self.assertEqual(status, "ROTATION_PREPARED")
        self.d, status, fence = self.m.fence_generation(
            self.d, 4, "proposal-4-5"
        )
        self.assertEqual(status, "GENERATION_FENCED")
        self.assertIsNotNone(fence)
        self.a0, status = self.m.activate_rotation(self.a0, self.d, fence)
        self.assertEqual(status, "ROTATION_ACTIVE")

    def test_M01_permitted_one_effect(self):
        self.release()
        token = self.reserve()
        self.d, status, effect = self.m.apply_synthetic_effect(self.d, token)
        self.assertEqual(status, "EFFECT_COMMITTED")
        self.assertEqual(effect.counter_after, 1)

    def test_M02_stale_release_after_rotation(self):
        self.rotate()
        self.a0, status, _ = self.m.accept_release_if_current(
            self.a0, self.release4
        )
        self.assertEqual(status, "STALE_AUTHORITY_GENERATION")

    def test_M03_stale_reservation_after_rotation(self):
        self.release()
        self.rotate()
        self.a0, status, token = self.m.reserve_if_current(self.a0, self.req4)
        self.assertEqual(status, "STALE_AUTHORITY_GENERATION")
        self.assertIsNone(token)

    def test_M04_old_reservation_rejected_after_D_generation_fence(self):
        self.release()
        token = self.reserve()
        self.rotate()
        self.d, status, effect = self.m.apply_synthetic_effect(self.d, token)
        self.assertEqual(status, "GENERATION_FENCED")
        self.assertIsNone(effect)

    def test_M05_effect_before_D_fence_remains_historical(self):
        self.release()
        token = self.reserve()
        self.d, status, effect = self.m.apply_synthetic_effect(self.d, token)
        self.assertEqual(status, "EFFECT_COMMITTED")
        self.rotate()
        self.assertEqual(len(self.d.effects), 1)

    def test_M06_rotation_pending_blocks_reservation(self):
        self.release()
        self.a0, status = self.m.prepare_rotation(
            self.a0, "proposal-4-5", "registry-g5"
        )
        self.assertEqual(status, "ROTATION_PREPARED")
        self.a0, status, _ = self.m.reserve_if_current(self.a0, self.req4)
        self.assertEqual(status, "ROTATION_PENDING")

    def test_M07_D_first_stop_does_not_claim_A0_admission_stop(self):
        self.release()
        self.d, status, _ = self.m.stop_effects(self.d, "run-1")
        self.assertEqual(status, "EFFECT_STOP_FENCED")
        token = self.reserve()
        self.d, status, _ = self.m.apply_synthetic_effect(self.d, token)
        self.assertEqual(status, "EFFECT_STOP_FENCED")
        facts = self.m.stop_status(self.a0, self.d, "run-1")
        self.assertFalse(facts["admission_stopped_at_A0"])
        self.assertTrue(facts["effects_stopped_at_D"])

    def test_M08_A0_first_stop_does_not_claim_D_effect_stop(self):
        self.release()
        token = self.reserve()
        self.a0, status = self.m.stop_admissions(self.a0, "run-1")
        self.assertEqual(status, "ADMISSION_STOP_PREPARED")
        self.d, status, effect = self.m.apply_synthetic_effect(self.d, token)
        self.assertEqual(status, "EFFECT_COMMITTED")
        self.assertIsNotNone(effect)

    def test_M09_both_stops_do_not_prove_worker_termination(self):
        self.a0, _ = self.m.stop_admissions(self.a0, "run-1")
        self.d, _, _ = self.m.stop_effects(self.d, "run-1")
        facts = self.m.stop_status(self.a0, self.d, "run-1")
        self.assertTrue(facts["admission_stopped_at_A0"])
        self.assertTrue(facts["effects_stopped_at_D"])
        self.assertFalse(facts["worker_tree_termination_proven"])
        self.assertFalse(facts["combined_stop_qualified"])

    def test_M10_duplicate_forwarding_counts_two_real_synthetic_effects(self):
        self.release()
        token = self.reserve()
        self.d, code1, _ = self.m.apply_synthetic_effect(self.d, token)
        self.d, code2, _ = self.m.apply_synthetic_effect(self.d, token)
        self.assertEqual((code1, code2), ("EFFECT_COMMITTED", "EFFECT_COMMITTED"))
        self.assertEqual(len(self.d.effects), 2)  # Detectable BLOCK, not safety PASS.

    def test_M11_lost_reservation_ack_is_reconcilable(self):
        self.release()
        token = self.reserve()
        found = self.m.find_reservation(self.a0, self.req4.reservation_id)
        self.assertEqual(found, token)
        self.a0, status, second = self.m.reserve_if_current(self.a0, self.req4)
        self.assertEqual(status, "DUPLICATE_RESERVATION")
        self.assertIsNone(second)
        self.assertEqual(len(self.a0.parsed_attempts), 2)

    def test_M12_denials_count_against_parsed_request_budget(self):
        rejected = replace(self.req4, operation="mock.purchase")
        for i in range(25):
            self.a0, status, _ = self.m.reserve_if_current(
                self.a0, replace(rejected, attempt_id=f"denied-{i}")
            )
            self.assertEqual(status, "OPERATION_DENIED")
        self.a0, status, _ = self.m.reserve_if_current(self.a0, self.req4)
        self.assertEqual(status, "BUDGET_EXHAUSTED")
        self.assertEqual(len(self.a0.parsed_attempts), 25)

    def test_M13_revoked_grant_unspent_does_not_reserve(self):
        self.release()
        self.a0 = self.m.revoke_grant(self.a0, "grant4")
        self.a0, status, _ = self.m.reserve_if_current(self.a0, self.req4)
        self.assertEqual(status, "GRANT_REVOKED")

    def test_M15_structural_token_forgery_is_unmodeled_security_gap(self):
        # A directly constructed dataclass has no A0 signature. This should
        # demonstrate an explicitly known gap in the reference model.
        fake = self.m.Reservation(request=self.req4, sequence=999)
        self.d, status, _ = self.m.apply_synthetic_effect(self.d, fake)
        self.assertEqual(status, "EFFECT_COMMITTED")  # NOT real-world security.

    def test_M16_unknown_manifest_rejected(self):
        wrong = replace(self.release4, manifest_id="unknown")
        self.a0, status, _ = self.m.accept_release_if_current(self.a0, wrong)
        self.assertEqual(status, "MANIFEST_UNAPPROVED")

    def test_M18_rotation_needs_a_registered_D_fence(self):
        self.a0, status = self.m.prepare_rotation(
            self.a0, "proposal-4-5", "registry-g5"
        )
        fake_fence = self.m.GenerationFence(4, "proposal-4-5", 999)
        self.a0, status = self.m.activate_rotation(
            self.a0, self.d, fake_fence
        )
        self.assertEqual(status, "D_FENCE_UNPROVEN")
        self.assertEqual(self.a0.generation, 4)

    def test_M19_global_stop_dominates_later_rotation(self):
        self.d, _, _ = self.m.stop_effects(self.d, "run-1")
        self.rotate()
        self.release(self.release5)
        token = self.reserve(self.req5)
        self.d, status, _ = self.m.apply_synthetic_effect(self.d, token)
        self.assertEqual(status, "EFFECT_STOP_FENCED")

    def test_M20_same_action_replay_denied_even_with_new_reservation_id(self):
        self.release()
        self.reserve()
        repeated = replace(
            self.req4, reservation_id="new-reservation",
            attempt_id="new-attempt"
        )
        self.a0, status, _ = self.m.reserve_if_current(self.a0, repeated)
        self.assertEqual(status, "DUPLICATE_RESERVATION")
        self.assertEqual(len(self.a0.parsed_attempts), 2)

    def test_release_ID_reuse_rejected(self):
        self.release()
        self.a0, status, _ = self.m.accept_release_if_current(
            self.a0, self.release4
        )
        self.assertEqual(status, "DUPLICATE_RELEASE_ID")

    def test_wrong_epoch_rejected(self):
        self.release()
        wrong = replace(self.req4, activation_epoch=12345)
        self.a0, status, _ = self.m.reserve_if_current(self.a0, wrong)
        self.assertEqual(status, "STALE_AUTHORITY_GENERATION")


if __name__ == "__main__":
    raise SystemExit(
        "CERBERUS tests require separate explicit run authorization; "
        "do not invoke this file as an autonomous service."
    )
