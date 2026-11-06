#!/usr/bin/env python3
"""Reproducible, synthetic PE receipt contract tests. Not independent qualification."""
import copy
import hashlib
import json
import random
import runpy
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
LINTER = HERE / '11.05.26 - Decision Receipt Offline Linter v0.2.py'
SCHEMA = HERE / '11.05.26 - Decision Receipt Schema v0.2.json'
EXAMPLE = HERE / '11.05.26 - Decision Receipt Example v0.2.json'
EXPECTED_SHA256 = {
    LINTER.name: '6ca7543868dc8dac66d3926236abd1f2e62b1577fa6941aff347e604cc2819a2',
    SCHEMA.name: '84a1aa12b92ae75807568034933e64705afd910383a6390b76a450b974fdc5de',
    EXAMPLE.name: '91bb630a74502fc2ddc72efbdf0cd8b10c6fbd46bef179f18db8af1199606e6f',
}

class ReceiptContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        for path in (LINTER, SCHEMA, EXAMPLE):
            digest = hashlib.sha256(path.read_bytes()).hexdigest()
            if digest != EXPECTED_SHA256[path.name]:
                raise AssertionError('SOURCE_DRIFT: ' + path.name)
        cls.mod = runpy.run_path(str(LINTER), run_name='unit_test_loader')
        cls.base = json.loads(EXAMPLE.read_text(encoding='utf-8'))
        cls.question = cls.base['exact_proposition']

    def deny(self, mutate):
        specimen = copy.deepcopy(self.base)
        mutate(specimen)
        self.assertTrue(self.mod['check'](specimen, self.question))

    def cli(self, raw_bytes, extra_args=()):
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory)/'input.json'
            source.write_bytes(raw_bytes)
            return subprocess.run([sys.executable, str(LINTER), str(source), *extra_args],
                                  capture_output=True, text=True, timeout=8)

    def test_nominal_fixture(self):
        self.assertEqual(self.mod['check'](self.base, self.question), [])

    def test_required_receipt_id(self):
        self.deny(lambda d: d.update(receipt_id=[]))

    def test_extra_authority_grant(self):
        self.deny(lambda d: d['authorization'].update(deployment_granted=True))

    def test_extra_independence_attestation(self):
        self.deny(lambda d: d['independence'].update(certified_independent=True))

    def test_untyped_approval_evidence(self):
        self.deny(lambda d: d['authorization'].update(external_approval_evidence={'approved': True}))

    def test_stage_objection_array(self):
        def mutate(d):
            d['depth'] = 'THREE'
            d['stages'] = [{'name': name, 'contribution': 'Observed question',
                            'cited_source_ids': ['G1'], 'objection': ['untyped']}
                           for name in ('ANJA', 'CHAT', 'RHYAN')]
        self.deny(mutate)

    def test_nonstring_forecast_horizon(self):
        self.deny(lambda d: d.update(forecasts=[{'status':'FORECAST', 'claim':'A',
                         'causal_pathway':'A to B', 'disconfirmation_condition':'not B', 'horizon':[]}]))

    def test_unpaired_unicode(self):
        self.deny(lambda d: d.update(exact_proposition='\ud800'))

    def test_duplicate_json_keys_cli(self):
        data = EXAMPLE.read_text().replace('"receipt_id": "PE-PORTABLE-DEMO-001",',
                  '"receipt_id": "MALICIOUS", "receipt_id": "PE-PORTABLE-DEMO-001",', 1)
        result = self.cli(data.encode('utf-8'), ('--unbound-structural-only',))
        self.assertEqual(result.returncode, 2)
        self.assertIn('BLOCK', result.stdout)

    def test_nonfinite_json_cli(self):
        data = EXAMPLE.read_text().replace('"receipt_id": "PE-PORTABLE-DEMO-001",',
                                         '"receipt_id": NaN,', 1)
        result = self.cli(data.encode('utf-8'), ('--unbound-structural-only',))
        self.assertEqual(result.returncode, 2)

    def test_oversize_cli(self):
        data = EXAMPLE.read_bytes() + b' ' * (1024 * 1024)
        result = self.cli(data, ('--unbound-structural-only',))
        self.assertEqual(result.returncode, 2)

    def test_external_original_required(self):
        result = self.cli(EXAMPLE.read_bytes())
        self.assertEqual(result.returncode, 3)

    def test_anchored_proposition_works(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory)/'original-question.txt'
            path.write_bytes(self.question.encode('utf-8'))
            result = self.cli(EXAMPLE.read_bytes(), ('--expected-proposition-file',str(path)))
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            self.assertIn('PROPOSITION-BOUND STRUCTURAL PASS ONLY', result.stdout)

    def test_wrong_external_original_blocked(self):
        result = self.cli(EXAMPLE.read_bytes(), ('--expected-proposition','Another question'))
        self.assertEqual(result.returncode, 2)

    def test_optimized_python_selftest_retained(self):
        result = subprocess.run([sys.executable, '-O', str(LINTER), '--self-test'],
                                capture_output=True, text=True, timeout=8)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn('23 deliberate structural violations rejected', result.stdout)

    def test_seeded_malformed_type_fuzz(self):
        rng = random.Random(37091)
        keys = ['status','depth','verdict','recommendation','authorization',
                'independence','stages','source_packet','original_question_sha256',
                'exact_proposition','forecasts']
        vals = [None, 0, 17, True, False, {}, [], [1], {'x': 1}, '']
        for _ in range(750):
            case = copy.deepcopy(self.base)
            case[rng.choice(keys)] = copy.deepcopy(rng.choice(vals))
            outcome = self.mod['check'](case, self.question)
            self.assertIsInstance(outcome, list)

if __name__ == '__main__':
    print('Synthetic, same-author tests only: no source authentication, semantic truth or independent adjudication.')
    unittest.main(verbosity=2)
