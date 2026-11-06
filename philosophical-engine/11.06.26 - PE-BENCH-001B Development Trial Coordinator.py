#!/usr/bin/env python3
"""Offline, source-bound, synthetic 36-run coordinator; never runs any model.

This coordinator does not read reference keys or decide philosophical accuracy.
It prepares (case, arm) trial packets, not authorized assignments to live projects.

Usage:
  python '11.06.26 - PE-BENCH-001B Development Trial Coordinator.py' --self-test --pack CASES.json
  python '11.06.26 - PE-BENCH-001B Development Trial Coordinator.py' --pack CASES.json --outdir DIR --seed pe-bench-001b-v1
"""
import argparse
import copy
import hashlib
import json
from pathlib import Path

EXPECTED_PACK_SHA256 = '67faeca4b62abaa52217c6e617732630836fa6cd0c41a5448e165d34504260d6'
ARMS = ('BASELINE', 'ADAPTIVE', 'FULL')
STAGES = ('ANJA', 'CHAT', 'RHYAN', 'ZHUANGZI', 'ATHENA', 'PROMETHEUS')
PERMITTED_ACTIONS = ('PREPARE', 'BUILD_PROBE', 'STOP_PARK')
CANONICAL_VERDICTS = ('SUPPORTED', 'REFUTED', 'INCONCLUSIVE', 'NOT_TESTABLE')
VERSION = 'PE-BENCH-001B-DEVELOPMENT-COORDINATOR-v0.1'
PREFIX = '11.06.26 - PE-BENCH-001B'


def sha(data):
    return hashlib.sha256(data).hexdigest()


def canonical_json(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(',', ':')).encode('utf-8')


def case_packet_sha(case):
    return sha(canonical_json({k:v for k,v in case.items() if k != 'source_packet_sha256'}))


def load_and_check_pack(path):
    data = Path(path).read_bytes()
    if sha(data) != EXPECTED_PACK_SHA256:
        raise ValueError('Pinned case-pack SHA-256 mismatch; not a candidate for this cohort')
    pack = json.loads(data)
    cases = pack.get('cases') if isinstance(pack,dict) else None
    if not isinstance(cases,list) or len(cases) != 12:
        raise ValueError('Exactly twelve candidate-facing synthetic cases required')
    ids = set()
    for case in cases:
        if not isinstance(case,dict):
            raise ValueError('Case must be object')
        cid = case.get('case_id')
        if not isinstance(cid,str) or not cid or cid in ids:
            raise ValueError('Duplicate or malformed case ID')
        ids.add(cid)
        if not isinstance(case.get('exact_proposition'),str) or not case['exact_proposition']:
            raise ValueError('Missing exact proposition')
        evidence = case.get('evidence')
        if not isinstance(evidence,list) or len({v.get('id') for v in evidence if isinstance(v,dict)}) != len(evidence):
            raise ValueError('Malformed or duplicate evidence identifiers')
        if case.get('source_packet_sha256') != case_packet_sha(case):
            raise ValueError('Source packet internal digest mismatch for ' + cid)
    return pack


def instructions(arm):
    common = ('Answer the exact original proposition using only the supplied synthetic case packet. '
              'Preserve all source IDs, distinguish stated facts from inferences and forecasts, '
              'do not assert human approval or execution, and keep conclusions revisable. '
              'State a truth verdict (SUPPORTED, REFUTED, INCONCLUSIVE, or NOT_TESTABLE), '
              'an advisory next action (PREPARE, BUILD_PROBE, or STOP_PARK), '
              'the supporting and contradicting evidence, the strongest objection, '
              'and a concrete revision trigger. No tools, external sources, or operational effects.')
    if arm == 'BASELINE':
        return common + ' Use a single direct evidence-based assessment without named philosophical stages.'
    if arm == 'ADAPTIVE':
        return common + ' Choose QUICK, THREE, or FULL according to risk and information value; if depth warrants, run Anja, Chat, Rhyan, Zhuangzi, Athena, and Prometheus in their prescribed order. State why extra analysis is or is not worth its cost.'
    if arm == 'FULL':
        return common + ' Use all six stages in order: ANJA, CHAT, RHYAN, ZHUANGZI, ATHENA, PROMETHEUS. Distinguish each new contribution and do not treat agreement among stages as independent evidence.'
    raise ValueError('Unrecognized arm')


def prepare(pack, seed):
    if not isinstance(seed,str) or not seed:
        raise ValueError('Seed required')
    trials=[]
    for case in pack['cases']:
        for arm in ARMS:
            cid = case['case_id']
            identity = sha((seed+'|'+cid+'|'+arm).encode('utf-8'))
            full_case = copy.deepcopy(case)
            trial = {'trial_id':'T-'+identity[:14], 'case_id':cid,
                     'arm':arm, 'input_case_packet_sha256':case['source_packet_sha256'],
                     'original_question_sha256':sha(case['exact_proposition'].encode('utf-8')),
                     'case':full_case, 'instructions':instructions(arm),
                     'completion':'NOT_RUN', 'response_sha256':None,
                     'observed_elapsed_seconds':None, 'observed_token_cost':None}
            trials.append(trial)
    # Stable pre-registered permutation; no runtime randomness or clock dependency.
    trials.sort(key=lambda t:sha((seed+'|order|'+t['trial_id']).encode('utf-8')))
    audit=[{'position':i+1,'trial_id':t['trial_id'],'case_id':t['case_id'],
            'arm':t['arm'],'input_case_packet_sha256':t['input_case_packet_sha256']}
           for i,t in enumerate(trials)]
    manifest = {'protocol_version':VERSION, 'case_pack_sha256':EXPECTED_PACK_SHA256,
        'cohort':'DEVELOPMENT_ONLY_PREVIOUSLY_DISCLOSED_TOPICS',
        'no_sealed_keys_included':True, 'human_authority_reserved':True,
        'unseen_independent_qualification':False, 'responses_collected':0,
        'methodology':['BASELINE', 'ADAPTIVE', 'FULL'], 'case_count':12,
        'trial_count':36,'schedule_seed':seed, 'schedule':audit,
        'verdict_namespace':list(CANONICAL_VERDICTS),
        'legacy_evaluator_verdict_namespace':['SUPPORTED','REFUTED','UNKNOWN'],
        'automatic_legacy_UNKNOWN_mapping':'PROHIBITED_PENDING_INDEPENDENT_ADJUDICATION',
        'truth_quality_measured':False, 'model_execution_performed':False,
        'qualification':'BLOCKED_NOT_EVALUATED'}
    return manifest, trials


def write_new(path,obj):
    encoded=(json.dumps(obj,ensure_ascii=False,indent=2)+'\n').encode('utf-8')
    with Path(path).open('xb') as fh:fh.write(encoded)
    return sha(encoded)


def self_test(pack):
    a,x=prepare(pack,'pe-bench-001b-v1')
    b,y=prepare(pack,'pe-bench-001b-v1')
    checks = (
        ('repeatability', a == b and x == y),
        ('unique trials', len(x)==36 and len({t['trial_id'] for t in x})==36),
        ('balanced case arms', {(t['case_id'],t['arm']) for t in x} == {(c['case_id'],arm) for c in pack['cases'] for arm in ARMS}),
        ('source packet identities', len({t['input_case_packet_sha256'] for t in x})==12),
        ('no fabricated results', all(t['completion']=='NOT_RUN' and t['response_sha256'] is None for t in x)),
        ('sealed keys excluded', all('reference_keys' not in json.dumps(t).lower() for t in x)),
        ('different truth-vocabulary sets', a['legacy_evaluator_verdict_namespace'] != a['verdict_namespace']),
        ('no silent vocabulary mapping', a['automatic_legacy_UNKNOWN_mapping'].startswith('PROHIBITED')),
        ('seed changes schedule', prepare(pack,'pe-bench-001b-v2')[0]['schedule'] != a['schedule']),
    )
    failures=[name for name,ok in checks if not ok]
    if failures:
        raise RuntimeError('SELF_TEST_FAILURE: '+', '.join(failures))
    return {'status':'LOCAL_SELF_TEST_PASS','test_assertions':len(checks),
            'case_pack_sha256':EXPECTED_PACK_SHA256,'trial_count':36,
            'limitations':'No models run, no sealed keys accessed, no grader qualification.'}


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--pack',required=True)
    p.add_argument('--outdir')
    p.add_argument('--seed',default='pe-bench-001b-v1')
    p.add_argument('--self-test',action='store_true')
    a=p.parse_args()
    pack=load_and_check_pack(a.pack)
    if a.self_test:
        print(json.dumps(self_test(pack),indent=2));return
    if not a.outdir:p.error('--outdir required unless --self-test')
    root=Path(a.outdir)
    root.mkdir(parents=True,exist_ok=True)
    manifest,trials=prepare(pack,a.seed)
    path_a=root/(PREFIX+' Development Trial Schedule.json')
    path_b=root/(PREFIX+' Candidate Prompt Pack.json')
    if path_a.exists() or path_b.exists():
        raise FileExistsError('Refusing to overwrite existing candidate records')
    digest_a=write_new(path_a,manifest)
    digest_b=write_new(path_b,{'protocol_version':VERSION,'status':'PREPARED_NOT_EXECUTED','trials':trials})
    print(json.dumps({'status':'PREPARED_NOT_EXECUTED','trial_count':36,
           'schedule_sha256':digest_a,'candidate_pack_sha256':digest_b,
           'output_files':[path_a.name,path_b.name]},indent=2))


if __name__ == '__main__':main()
