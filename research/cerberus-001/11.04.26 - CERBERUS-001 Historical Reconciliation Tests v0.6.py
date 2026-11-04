"""
CERBERUS-001 — D-private historical receipt classifier source tests v0.6.
NOT IMPORTED, COMPILED, EXECUTED, OR INDEPENDENTLY QUALIFIED.

Source examples are intentionally synthetic. A test PASS would not prove
external principal authorization, real Ed25519, A0 source or D store custody.
"""

from __future__ import annotations

from dataclasses import replace
import importlib.util
from pathlib import Path
import sys
import unittest


def load_model_for_future_authorized_run():
    filename = (
        "11.04.26 - CERBERUS-001 "
        "D Historical Reconciliation Classifier v0.6.py"
    )
    spec = importlib.util.spec_from_file_location(
        "cerberus_historical_reconcile_v06", Path(__file__).with_name(filename)
    )
    if spec is None or spec.loader is None:
        raise RuntimeError("Source model missing")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


class HistoricalReconciliationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.m = load_model_for_future_authorized_run()

    def setUp(self):
        m = self.m
        self.effect = m.InternalHistoricalEffect(
            event_sequence=2,
            root_id="synthetic-root",
            run_id="synthetic-run",
            episode_id="synthetic-episode",
            action_id="synthetic-action",
            grant_id="synthetic-grant",
            generation=4,
            reservation_id="synthetic-reservation",
            token_sha256="a" * 64,
            counter_after=1,
        )
        self.query = m.InternalHistoricalQuery(
            reservation_id=self.effect.reservation_id,
            token_sha256=self.effect.token_sha256,
            root_id=self.effect.root_id,
            run_id=self.effect.run_id,
            episode_id=self.effect.episode_id,
            action_id=self.effect.action_id,
            grant_id=self.effect.grant_id,
            generation=self.effect.generation,
        )
        self.view = m.InternalDHistory(
            effects=(self.effect,), generation_fences=(),
            grant_fences=(), stopped_runs=(),
        )

    def classify(self, *, view=None, query=None):
        return self.m.classify_d_private_history(
            self.view if view is None else view,
            self.query if query is None else query,
        )

    def assert_no_effect_or_release(self, decision):
        self.assertFalse(decision.release_to_external_caller)
        self.assertFalse(decision.authorize_new_effect)

    def test_RH01_matching_D_snapshot_internal_candidate_only(self):
        d = self.classify()
        self.assertEqual(d.status, "D_PRIVATE_HISTORICAL_CANDIDATE")
        self.assertEqual(d.candidate_effect_sequence, 2)
        self.assert_no_effect_or_release(d)

    def test_RH02_after_run_stop_internal_historical_candidate_only(self):
        v = replace(self.view, stopped_runs=("synthetic-run",))
        d = self.classify(view=v)
        self.assertEqual(
            d.status, "D_PRIVATE_HISTORICAL_CANDIDATE_AFTER_FENCE"
        )
        self.assertTrue(d.post_fence)
        self.assert_no_effect_or_release(d)

    def test_RH03_after_generation_fence(self):
        v = replace(self.view, generation_fences=(4,))
        d = self.classify(view=v)
        self.assertTrue(d.post_fence)
        self.assert_no_effect_or_release(d)

    def test_RH04_after_grant_fence(self):
        v = replace(
            self.view,
            grant_fences=((
                "synthetic-root", "synthetic-run", "synthetic-grant"
            ),),
        )
        d = self.classify(view=v)
        self.assertTrue(d.post_fence)
        self.assert_no_effect_or_release(d)

    def test_RH05_different_original_token_hash_is_conflict(self):
        q = replace(self.query, token_sha256="b" * 64)
        d = self.classify(query=q)
        self.assertEqual(d.status, "HISTORICAL_BINDING_CONFLICT")
        self.assertIsNone(d.candidate_effect_sequence)

    def test_RH06_other_root_same_reservation_conflicts(self):
        q = replace(self.query, root_id="other-root")
        self.assertEqual(
            self.classify(query=q).status, "HISTORICAL_BINDING_CONFLICT"
        )

    def test_RH07_other_action_same_reservation_conflicts(self):
        q = replace(self.query, action_id="other-action")
        self.assertEqual(
            self.classify(query=q).status, "HISTORICAL_BINDING_CONFLICT"
        )

    def test_RH08_reservation_not_in_D_ledger(self):
        q = replace(self.query, reservation_id="other-reservation")
        d = self.classify(query=q)
        self.assertEqual(d.status, "HISTORICAL_NOT_FOUND")
        self.assert_no_effect_or_release(d)

    def test_RH09_duplicate_reservation_rows_fail_closed(self):
        second = replace(
            self.effect, event_sequence=9, token_sha256="b" * 64
        )
        v = replace(self.view, effects=(self.effect, second))
        self.assertEqual(
            self.classify(view=v).status, "D_HISTORY_UNPROVEN"
        )

    def test_RH10_duplicate_action_rows_fail_closed(self):
        second = replace(
            self.effect, event_sequence=9,
            reservation_id="different-reservation",
        )
        v = replace(self.view, effects=(self.effect, second))
        self.assertEqual(
            self.classify(view=v).status, "D_HISTORY_UNPROVEN"
        )

    def test_RH11_bool_masquerading_as_generation_refused(self):
        q = replace(self.query, generation=True)
        self.assertEqual(self.classify(query=q).status, "QUERY_INVALID")

    def test_RH12_float_masquerading_as_integer_refused(self):
        q = replace(self.query, generation=4.0)
        self.assertEqual(self.classify(query=q).status, "QUERY_INVALID")

    def test_RH13_corrupt_D_event_sequence_refused(self):
        bad = replace(self.effect, event_sequence=0)
        v = replace(self.view, effects=(bad,))
        self.assertEqual(
            self.classify(view=v).status, "D_HISTORY_UNPROVEN"
        )

    def test_RH14_attacker_supplies_matching_context_known_gap(self):
        # Source type checks cannot establish D provenance or authenticated
        # requester. Even with every field correct, NO external release.
        forged = replace(self.query)
        d = self.classify(query=forged)
        self.assertEqual(d.status, "D_PRIVATE_HISTORICAL_CANDIDATE")
        self.assert_no_effect_or_release(d)

    def test_RH15_no_external_release_even_without_fences(self):
        self.assertFalse(self.classify().release_to_external_caller)

    def test_RH16_no_external_release_after_fence(self):
        v = replace(self.view, generation_fences=(4,))
        self.assertFalse(
            self.classify(view=v).release_to_external_caller
        )

    def test_RH17_empty_D_effect_history(self):
        v = replace(self.view, effects=())
        self.assertEqual(
            self.classify(view=v).status, "HISTORICAL_NOT_FOUND"
        )

    def test_RH18_unrelated_run_fence_does_not_change_history_label(self):
        v = replace(self.view, stopped_runs=("unrelated-run",))
        self.assertEqual(
            self.classify(view=v).status, "D_PRIVATE_HISTORICAL_CANDIDATE"
        )

    def test_RH19_wrong_grant_refuses_binding(self):
        q = replace(self.query, grant_id="different-grant")
        self.assertEqual(
            self.classify(query=q).status, "HISTORICAL_BINDING_CONFLICT"
        )

    def test_RH20_wrong_episode_refuses_binding(self):
        q = replace(self.query, episode_id="different-episode")
        self.assertEqual(
            self.classify(query=q).status, "HISTORICAL_BINDING_CONFLICT"
        )


if __name__ == "__main__":
    raise SystemExit("CERBERUS source tests are not authorized to run.")
