#!/usr/bin/env python3
"""Same-author synthetic checks for the non-authorizing v0.3 classifier.

Mocked structural checker tests NEVER qualify real v0.2 integration or reasoning.
"""
import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

HERE = Path(__file__).resolve().parent
GATE = HERE / '11.06.26 - Philosophical Engine Assurance Gate v0.3.py'
spec = importlib.util.spec_from_file_location('assurance_gate', GATE)
gate = importlib.util.module_from_spec(spec)
spec.loader.exec_module(gate)


def receipt():
    return {
        'exact_proposition': 'The synthetic run authorizes live deployment.',
        'verdict': 'REFUTED',
        'source_packet': {'records': [
            {'id':'G1','kind':'STIPULATED_SYNTHETIC_RECORD',
             'statement':'A fictional policy requires human approval.',
             'provenance':'fictional sealed packet G1'}]},
        'authorization': {'external_approval_evidence': 'Supervisor says yes'}
    }


def catalog(r):
    return {'schema_id':'labyrinth.pe.source_catalog.v0.3', 'records': [
        {'id':x['id'], 'kind':x['kind'],
         'statement_sha256':gate.digest(x['statement'].encode()),
         'provenance_sha256':gate.digest(x['provenance'].encode())}
        for x in r['source_packet']['records']]}


class GateTests(unittest.TestCase):
    def check(self,r,original=None,cat=None):
        return gate.evaluate(r,expected_original=original,catalog=cat,
                             linter=lambda doc, source: [] if source is None or doc['exact_proposition']==source else ['changed proposition'])

    def test_unbound_has_nonzero_gate_code(self):
        x=self.check(receipt())
        self.assertEqual(x['result_class'],'STRUCTURAL_UNBOUND')
        self.assertNotEqual(gate.RESULT_CODES[x['result_class']],0)
        self.assertEqual(x['adoption_gate'],'BLOCKED')

    def test_bound_has_nonzero_gate_code(self):
        r=receipt(); x=self.check(r,r['exact_proposition'])
        self.assertEqual(x['result_class'],'STRUCTURAL_BOUND')
        self.assertNotEqual(gate.RESULT_CODES[x['result_class']],0)
        self.assertEqual(x['source_authentication'],'NOT_PERFORMED')

    def test_exact_catalog_still_not_authenticated(self):
        r=receipt(); x=self.check(r,r['exact_proposition'],catalog(r))
        self.assertEqual(x['result_class'],'SOURCE_CATALOG_MATCHED')
        self.assertEqual(x['catalog_bytes'],'MATCHED_NOT_AUTHENTICATED')
        self.assertEqual(x['human_authorization'],'NOT_VERIFIED')
        self.assertNotEqual(gate.RESULT_CODES[x['result_class']],0)

    def test_free_text_approval_never_grants(self):
        r=receipt(); x=self.check(r,r['exact_proposition'])
        self.assertTrue(x['free_text_approval_claim_present'])
        self.assertFalse(x['execution_authorized'])

    def test_mismatched_external_original_refused(self):
        x=self.check(receipt(),'Some other proposition')
        self.assertEqual(x['result_class'],'REFUSED')

    def test_catalog_requires_external_original(self):
        r=receipt(); x=self.check(r,cat=catalog(r))
        self.assertEqual(x['result_class'],'REFUSED')

    def test_forged_statement_fails_catalog_bytes(self):
        r=receipt(); expected=catalog(r)
        r['source_packet']['records'][0]['statement']='I made up a source.'
        x=self.check(r,r['exact_proposition'],expected)
        self.assertEqual(x['result_class'],'REFUSED')

    def test_unknown_categories_not_enough_for_strong_verdict(self):
        for kind in ('WISH','UNKNOWN','FORECAST','HYPOTHESIS','METAPHOR'):
            r=receipt(); r['source_packet']['records'][0]['kind']=kind
            self.assertEqual(self.check(r,r['exact_proposition'])['result_class'],'REFUSED')

    def test_uncertain_truth_can_use_unknown(self):
        r=receipt();r['source_packet']['records'][0]['kind']='UNKNOWN';r['verdict']='INCONCLUSIVE'
        self.assertEqual(self.check(r,r['exact_proposition'])['result_class'],'STRUCTURAL_BOUND')

    def test_fabricated_observation_not_authenticated(self):
        r=receipt();r['source_packet']['records'][0]['kind']='OBSERVATION';r['source_packet']['records'][0]['statement']='Fabricated observation'
        result=self.check(r,r['exact_proposition'])
        self.assertEqual(result['result_class'],'STRUCTURAL_BOUND')
        self.assertEqual(result['source_authentication'],'NOT_PERFORMED')
        self.assertEqual(result['semantic_adjudication'],'NOT_PERFORMED')

    def test_duplicate_catalog_record_ids_refused(self):
        r=receipt(); c=catalog(r); c['records'].append(copy.deepcopy(c['records'][0]))
        self.assertEqual(self.check(r,r['exact_proposition'],c)['result_class'],'REFUSED')

    def test_omitted_catalog_record_refused(self):
        r=receipt(); c=catalog(r); c['records']=[]
        self.assertEqual(self.check(r,r['exact_proposition'],c)['result_class'],'REFUSED')

    def test_nonfinite_and_duplicate_json_refused(self):
        with tempfile.TemporaryDirectory() as d:
            path=Path(d)/'x.json'
            for raw in (b'{"a":1,"a":2}',b'{"a":NaN}',b'{"a":Infinity}'):
                path.write_bytes(raw)
                with self.assertRaises(ValueError):gate.strict_json(path)

    def test_oversized_input_refused(self):
        with tempfile.TemporaryDirectory() as d:
            path=Path(d)/'large.json';path.write_bytes(b' '*((1024*1024)+1))
            with self.assertRaises(ValueError):gate.strict_json(path)

    def test_source_file_missing_fails_closed(self):
        with tempfile.TemporaryDirectory() as d:
            with self.assertRaises(OSError):gate.load_pinned_linter(d)

    def test_cli_refuses_when_original_linter_missing(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'receipt.json';p.write_text(json.dumps(receipt()))
            result=subprocess.run([sys.executable,str(GATE),str(p)],capture_output=True,text=True,timeout=8)
            self.assertEqual(result.returncode,2)
            self.assertEqual(json.loads(result.stdout)['result_class'],'REFUSED')

    def test_no_success_exit_classes(self):
        self.assertTrue(all(v!=0 for v in gate.RESULT_CODES.values()))

    def test_no_path_to_effect_authorization(self):
        r=receipt()
        for original,cat in [(None,None),(r['exact_proposition'],None),(r['exact_proposition'],catalog(r))]:
            x=self.check(r,original,cat)
            self.assertFalse(x['execution_authorized'])
            self.assertEqual(x['adoption_gate'],'BLOCKED')

if __name__=='__main__':
    print('Same-author synthetic suite: source-pinned live validator and semantic assessment NOT run.')
    unittest.main(verbosity=2)
