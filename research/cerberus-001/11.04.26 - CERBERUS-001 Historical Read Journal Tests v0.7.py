"""
CERBERUS-001 — D historical-read attempt-journal tests v0.7.
SOURCE ONLY: NOT IMPORTED, COMPILED, EXECUTED OR INDEPENDENTLY REVIEWED.
Only pure in-memory journal behavior can be predicted. This is NOT
durable audit completeness, issuer signature verification, a read grant,
external receipt release, or a qualified production effect gate.
"""
from __future__ import annotations

from dataclasses import replace
from hashlib import sha256
import importlib.util
from pathlib import Path
import sys
import unittest


def source_model_for_later_authorized_execution():
    name = "11.04.26 - CERBERUS-001 D Historical Read Attempt Journal v0.7.py"
    spec = importlib.util.spec_from_file_location(
        "cerberus_read_attempt_journal_v07", Path(__file__).with_name(name)
    )
    if spec is None or spec.loader is None:
        raise RuntimeError("missing source")
    model = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = model
    spec.loader.exec_module(model)
    return model


class HistoricalReadJournalTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.m = source_model_for_later_authorized_execution()

    def setUp(self):
        m = self.m
        self.journal = m.DPrivateReadJournal()
        self.intent = m.ReadIntent(
            original_token_bytes=b"synthetic-token-1",
            reservation_id_claim="reservation-1",
            principal_id_claim="principal-1",
            receipt_grant_id_claim="receipt-read-grant-1",
            original_issuer_key_id_claim="retired-key-1",
        )

    def append(self, journal=None, intent=None):
        return self.m.record_d_private_read_attempt(
            self.journal if journal is None else journal,
            self.intent if intent is None else intent,
        )

    def hold(self, outcome):
        self.assertFalse(outcome.durable_commit_proven)
        self.assertFalse(outcome.permit_historical_lookup)
        self.assertFalse(outcome.permit_receipt_release)
        self.assertFalse(outcome.permit_new_effect)
        self.assertTrue(outcome.custody_gap)

    def test_RA01_valid_input_records_private_hold(self):
        result = self.append()
        self.assertEqual(result.status, "D_PRIVATE_READ_ATTEMPT_LOGGED_HOLD")
        self.assertEqual(len(result.journal.attempts), 1)
        self.assertTrue(result.recorded_in_model)
        self.hold(result)

    def test_RA02_duplicate_same_token_appends_separate_observation(self):
        first = self.append()
        second = self.append(journal=first.journal)
        self.assertEqual([r.read_sequence for r in second.journal.attempts], [1, 2])
        self.assertEqual(second.journal.attempts[0].token_sha256,
                         second.journal.attempts[1].token_sha256)
        self.hold(second)

    def test_RA03_changed_token_has_distinct_digest(self):
        first = self.append()
        later = replace(self.intent, original_token_bytes=b"synthetic-token-2")
        second = self.append(journal=first.journal, intent=later)
        self.assertNotEqual(second.journal.attempts[0].token_sha256,
                            second.journal.attempts[1].token_sha256)
        self.hold(second)

    def test_RA04_missing_request_still_records_invalid_attempt(self):
        result = self.m.record_d_private_read_attempt(self.journal, None)
        self.assertEqual(result.status, "D_PRIVATE_READ_ATTEMPT_LOGGED_INVALID")
        self.assertEqual(len(result.journal.attempts), 1)
        self.hold(result)

    def test_RA05_string_token_instead_of_bytes_still_logs(self):
        result = self.append(intent=replace(self.intent, original_token_bytes="bad"))
        self.assertEqual(result.status, "D_PRIVATE_READ_ATTEMPT_LOGGED_INVALID")
        self.assertEqual(result.journal.attempts[0].raw_byte_length, -1)
        self.hold(result)

    def test_RA06_empty_token_is_invalid_but_logged(self):
        result = self.append(intent=replace(self.intent, original_token_bytes=b""))
        self.assertEqual(result.status, "D_PRIVATE_READ_ATTEMPT_LOGGED_INVALID")
        self.hold(result)

    def test_RA07_oversized_token_is_invalid_but_logged(self):
        result = self.append(
            intent=replace(self.intent, original_token_bytes=b"x" * 4097)
        )
        self.assertEqual(result.status, "D_PRIVATE_READ_ATTEMPT_LOGGED_INVALID")
        self.assertEqual(result.journal.attempts[0].raw_byte_length, 4097)
        self.hold(result)

    def test_RA08_invalid_principal_claim_still_logs(self):
        result = self.append(intent=replace(self.intent, principal_id_claim="bad space"))
        self.assertEqual(result.status, "D_PRIVATE_READ_ATTEMPT_LOGGED_INVALID")
        self.hold(result)

    def test_RA09_invalid_read_grant_claim_still_logs(self):
        result = self.append(
            intent=replace(self.intent, receipt_grant_id_claim=None)
        )
        self.assertEqual(result.status, "D_PRIVATE_READ_ATTEMPT_LOGGED_INVALID")
        self.hold(result)

    def test_RA10_invalid_reservation_claim_still_logs(self):
        result = self.append(
            intent=replace(self.intent, reservation_id_claim=True)
        )
        self.assertEqual(result.status, "D_PRIVATE_READ_ATTEMPT_LOGGED_INVALID")
        self.hold(result)

    def test_RA11_invalid_issuer_key_claim_still_logs(self):
        result = self.append(
            intent=replace(self.intent, original_issuer_key_id_claim=[])
        )
        self.assertEqual(result.status, "D_PRIVATE_READ_ATTEMPT_LOGGED_INVALID")
        self.hold(result)

    def test_RA12_stolen_token_and_matching_claim_are_not_rights(self):
        # The same bytes can be presented by another self-claimed principal;
        # claims alone never authorize any historical lookup or release.
        stolen = replace(self.intent, principal_id_claim="impostor")
        outcome = self.append(intent=stolen)
        self.assertEqual(outcome.status, "D_PRIVATE_READ_ATTEMPT_LOGGED_HOLD")
        self.hold(outcome)

    def test_RA13_retired_key_claim_does_not_imply_archival_proof(self):
        result = self.append()
        self.assertEqual(result.status, "D_PRIVATE_READ_ATTEMPT_LOGGED_HOLD")
        self.hold(result)

    def test_RA14_compromised_key_claim_does_not_infer_valid_issuer(self):
        candidate = replace(
            self.intent, original_issuer_key_id_claim="compromised-old-key"
        )
        result = self.append(intent=candidate)
        self.assertEqual(result.status, "D_PRIVATE_READ_ATTEMPT_LOGGED_HOLD")
        self.hold(result)

    def test_RA15_corrupt_journal_head_fails_closed_with_custody_gap(self):
        old = replace(self.journal, read_sequence=1)
        result = self.append(journal=old)
        self.assertFalse(result.recorded_in_model)
        self.assertEqual(result.status, "D_READ_JOURNAL_UNPROVEN")
        self.hold(result)

    def test_RA16_corrupt_prior_read_sequence_fails_closed(self):
        first = self.append()
        badrow = replace(first.journal.attempts[0], read_sequence=2)
        bad = replace(first.journal, attempts=(badrow,))
        result = self.append(journal=bad)
        self.assertEqual(result.status, "D_READ_JOURNAL_UNPROVEN")
        self.hold(result)

    def test_RA17_forged_syntactically_valid_journal_known_custody_gap(self):
        # A copied valid Python journal passes type/sequence checks; this
        # does NOT establish D physical ownership or actual durability.
        copied = replace(self.append().journal)
        result = self.append(journal=copied)
        self.assertTrue(result.recorded_in_model)  # KNOWN MODEL GAP.
        self.hold(result)

    def test_RA18_unhashable_prior_status_fails_closed_not_exception(self):
        first = self.append()
        corrupted = replace(first.journal.attempts[0], status=[])
        bad = replace(first.journal, attempts=(corrupted,))
        result = self.append(journal=bad)
        self.assertEqual(result.status, "D_READ_JOURNAL_UNPROVEN")
        self.hold(result)

    def test_RA19_exhausted_or_impossible_sequence_fails_closed(self):
        bad = replace(self.journal, read_sequence=(2**63) - 1)
        result = self.append(journal=bad)
        self.assertEqual(result.status, "D_READ_JOURNAL_UNPROVEN")
        self.hold(result)

    def test_RA20_raw_token_not_retained_in_private_log_row(self):
        result = self.append()
        row = result.journal.attempts[0]
        self.assertEqual(row.token_sha256, sha256(self.intent.original_token_bytes).hexdigest())
        self.assertFalse(hasattr(row, "original_token_bytes"))
        self.assertFalse(hasattr(row, "receipt_read_authorized"))
        self.hold(result)


if __name__ == "__main__":
    raise SystemExit("Source-only CERBERUS tests cannot execute without separate grant.")
