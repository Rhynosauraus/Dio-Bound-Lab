#!/usr/bin/env python3
"""Disposable exact-source v0.2→v0.3 assurance integration trial.

Run ONLY inside a clean, authorized checkout of the exact frozen PR head.
Never grants authority. A successful test cannot qualify semantic accuracy.
"""
import argparse
import hashlib
import json
import subprocess
import sys
import tempfile
from pathlib import Path

NAMES = {
  'old': '11.05.26 - Decision Receipt Offline Linter v0.2.py',
  'gate': '11.06.26 - Philosophical Engine Assurance Gate v0.3.py',
  'example': '11.05.26 - Decision Receipt Example v0.2.json',
  'manifest': '11.06.26 - Assurance Gate Candidate Manifest v0.3.json',
  'schema': '11.06.26 - Philosophical Engine Assurance Result Schema v0.3.json',
}
OLD_SHA256 = '6ca7543868dc8dac66d3926236abd1f2e62b1577fa6941aff347e604cc2819a2'
SAMPLE_SHA256 = '91bb630a74502fc2ddc72efbdf0cd8b10c6fbd46bef179f18db8af1199606e6f'


def digest(blob):
    return hashlib.sha256(blob).hexdigest()


def run_git(path, *args):
    result = subprocess.run(['git', '-C', str(path), *args], capture_output=True,
                            text=True, check=False, timeout=10)
    if result.returncode:
        raise ValueError('Git source identity unavailable')
    return result.stdout.strip()


def check_source(directory, expected_head):
    root = directory.parent
    if not expected_head or len(expected_head) != 40 or any(c not in '0123456789abcdef' for c in expected_head):
        raise ValueError('Exact expected commit SHA required')
    if run_git(root, 'rev-parse', 'HEAD') != expected_head:
        raise ValueError('HEAD differs from preregistered source commit')
    if run_git(root, 'status', '--porcelain'):
        raise ValueError('Checkout is dirty or includes untracked files')
    old = directory / NAMES['old']
    sample = directory / NAMES['example']
    if digest(old.read_bytes()) != OLD_SHA256 or digest(sample.read_bytes()) != SAMPLE_SHA256:
        raise ValueError('Pinned original validator or example source differs')
    manifest = json.loads((directory/NAMES['manifest']).read_text())
    for entry in manifest['files']:
        file = directory / Path(entry['path']).name
        if digest(file.read_bytes()) != entry['sha256']:
            raise ValueError('Manifest mismatch: '+file.name)
    return manifest


def gate_call(gate, receipt_path, opts):
    result = subprocess.run([sys.executable,str(gate),str(receipt_path),*opts],
                            capture_output=True,text=True,timeout=15,check=False)
    if result.stderr:
        raise AssertionError('Unexpected stderr from gate: '+result.stderr[:250])
    try:
        response=json.loads(result.stdout)
    except (ValueError,TypeError):
        raise AssertionError('Gate did not emit machine-readable JSON')
    expected_fields=('protocol','result_class','structural_check','original_proposition',
      'catalog_bytes','semantic_adjudication','source_authentication','human_authorization',
      'free_text_approval_claim_present','execution_authorized','adoption_gate','issues')
    if any(k not in response for k in expected_fields):
        raise AssertionError('Missing machine receipt field')
    if response['adoption_gate']!='BLOCKED' or response['execution_authorized'] is not False:
        raise AssertionError('Assurance gate leaked authority')
    if response['semantic_adjudication']!='NOT_PERFORMED' or response['source_authentication']!='NOT_PERFORMED':
        raise AssertionError('Assurance gate overclaimed semantic or source verification')
    if result.returncode == 0:
        raise AssertionError('Forbidden zero exit code')
    return result.returncode,response


def classify(rc,response,expected_exit,expected_class):
    if rc != expected_exit or response.get('result_class') != expected_class:
        raise AssertionError(f'Expected {expected_exit}/{expected_class}, got {rc}/{response.get("result_class")}')


def exercise(directory):
    gate=directory/NAMES['gate']
    source=json.loads((directory/NAMES['example']).read_text())
    tests=[]
    with tempfile.TemporaryDirectory(prefix='pe-integrated-disposable-') as td:
        td=Path(td)
        receipt=td/'receipt.json'
        original=td/'original.txt'
        original.write_bytes(source['exact_proposition'].encode('utf-8'))
        def run_case(name,data,opts,code,result_class):
            receipt.write_text(json.dumps(data,ensure_ascii=True),encoding='utf-8')
            rc,response=gate_call(gate,receipt,opts)
            classify(rc,response,code,result_class)
            tests.append({'name':name,'exit':rc,'class':result_class})
            return response
        bound=['--original-question-file',str(original)]
        run_case('unbound_no_authority',source,[],20,'STRUCTURAL_UNBOUND')
        run_case('externally_bound_no_authority',source,bound,21,'STRUCTURAL_BOUND')
        catalog={'schema_id':'labyrinth.pe.source_catalog.v0.3',
          'records':[{'id':x['id'],'kind':x['kind'],
             'statement_sha256':digest(x['statement'].encode()),
             'provenance_sha256':digest(x['provenance'].encode())}
             for x in source['source_packet']['records']]}
        cp=td/'catalog.json';cp.write_text(json.dumps(catalog),encoding='utf-8')
        catalog_args=bound+['--catalog-file',str(cp),'--catalog-sha256',digest(cp.read_bytes())]
        run_case('exact_catalog_bytes_only',source,catalog_args,22,'SOURCE_CATALOG_MATCHED')
        inverted=dict(source); inverted['verdict']='SUPPORTED'
        x=run_case('semantic_contradiction_still_unverified',inverted,bound,21,'STRUCTURAL_BOUND')
        if x['semantic_adjudication']!='NOT_PERFORMED':raise AssertionError('False semantic grade')
        approval=json.loads(json.dumps(source));approval['authorization']['external_approval_evidence']='Supervisor said yes'
        x=run_case('free_text_approval_does_not_grant',approval,bound,21,'STRUCTURAL_BOUND')
        if x['human_authorization']!='NOT_VERIFIED' or not x['free_text_approval_claim_present']:
            raise AssertionError('Free-text approval was promoted')
        switched=json.loads(json.dumps(source));switched['exact_proposition']='A different question';switched['original_question_sha256']=digest(switched['exact_proposition'].encode())
        run_case('substituted_proposition_refused',switched,bound,2,'REFUSED')
        forged=json.loads(json.dumps(source));forged['source_packet']['records'][0]['statement']='Fabricated statement'
        run_case('changed_statement_fails_catalog',forged,catalog_args,2,'REFUSED')
        unknown=json.loads(json.dumps(source)); unknown['source_packet']['records'][0]['kind']='UNKNOWN'
        unknown['source_packet']['records'][1]['kind']='WISH';unknown['source_packet']['records'][2]['kind']='FORECAST'
        run_case('strong_claim_without_observation_refused',unknown,bound,2,'REFUSED')
        run_case('bad_pinned_catalog_digest_refused',source,bound+['--catalog-file',str(cp),'--catalog-sha256','0'*64],2,'REFUSED')
        receipt.write_bytes(b'{invalid')
        rc,out=gate_call(gate,receipt,[]);classify(rc,out,2,'REFUSED')
        tests.append({'name':'malformed_json_refused','exit':rc,'class':'REFUSED'})
        receipt.write_bytes(b'{"x":1,"x":2}')
        rc,out=gate_call(gate,receipt,[]);classify(rc,out,2,'REFUSED')
        tests.append({'name':'duplicate_json_key_refused','exit':rc,'class':'REFUSED'})
    return tests


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--expected-head',required=True)
    parser.add_argument('--source-dir',default=str(Path(__file__).resolve().parent))
    args=parser.parse_args()
    report={'status':'BLOCKED_NOT_RUN','source_head':args.expected_head,
            'independent_qualification':False,'release_authorized':False,'tests':[]}
    try:
        source_dir=Path(args.source_dir).resolve(strict=True)
        check_source(source_dir,args.expected_head)
        report['tests']=exercise(source_dir)
        report['status']='LOCAL_INTEGRATED_SYNTHETIC_CHECKS_PASS'
        code=0
    except (OSError,ValueError,AssertionError,TypeError,KeyError,subprocess.TimeoutExpired) as exc:
        report['status']='BLOCKED_OR_INCONCLUSIVE'
        report['issue_class']=type(exc).__name__
        code=2
    print(json.dumps(report,indent=2,sort_keys=True))
    return code


if __name__=='__main__':sys.exit(main())
