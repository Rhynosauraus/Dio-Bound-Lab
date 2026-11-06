#!/usr/bin/env python3
"""PE v0.3 candidate: non-authorizing, source-bound assurance status classifier.

Every current outcome exits NONZERO. No result is semantic acceptance or permission.
The original v0.2 linter is loaded only if its exact SHA-256 matches.
"""
import argparse
import hashlib
import json
import runpy
import sys
from pathlib import Path

VERSION = 'PE-ASSURANCE-0.3-CANDIDATE'
LINTER_NAME = '11.05.26 - Decision Receipt Offline Linter v0.2.py'
LINTER_SHA256 = '6ca7543868dc8dac66d3926236abd1f2e62b1577fa6941aff347e604cc2819a2'
MAX_BYTES = 1024 * 1024
SOURCE_ANCHOR_KINDS = frozenset({'OBSERVATION', 'STIPULATED_SYNTHETIC_RECORD'})
RESULT_CODES = {'REFUSED': 2, 'STRUCTURAL_UNBOUND': 20,
                'STRUCTURAL_BOUND': 21, 'SOURCE_CATALOG_MATCHED': 22}


def digest(data):
    return hashlib.sha256(data).hexdigest()


def strict_json(path):
    with Path(path).open('rb') as source:
        raw = source.read(MAX_BYTES + 1)
    if len(raw) > MAX_BYTES:
        raise ValueError('input exceeds one MiB')

    def object_pairs(pairs):
        result = {}
        for key, value in pairs:
            if key in result:
                raise ValueError('duplicate JSON key')
            result[key] = value
        return result

    def nonfinite(value):
        raise ValueError('nonfinite JSON number: ' + value)

    return json.loads(raw.decode('utf-8'), object_pairs_hook=object_pairs,
                      parse_constant=nonfinite), raw


def trusted_question(path):
    with Path(path).open('rb') as source:
        raw = source.read(MAX_BYTES + 1)
    if len(raw) > MAX_BYTES:
        raise ValueError('original question too large')
    return raw.decode('utf-8')


def load_pinned_linter(directory):
    path = Path(directory) / LINTER_NAME
    if digest(path.read_bytes()) != LINTER_SHA256:
        raise ValueError('pinned v0.2 validator source mismatch')
    func = runpy.run_path(str(path), run_name='pe_assurance_import').get('check')
    if not callable(func):
        raise ValueError('pinned validator lacks check function')
    return func


def catalog_match(receipt, catalog):
    """Exact synthetic/catalog ID+bytes matching; NOT source authentication."""
    if not isinstance(catalog, dict) or set(catalog) != {'schema_id', 'records'} or \
       catalog.get('schema_id') != 'labyrinth.pe.source_catalog.v0.3':
        return False
    records = catalog.get('records')
    supplied = receipt.get('source_packet', {}).get('records', [])
    if not isinstance(records, list) or not isinstance(supplied, list):
        return False
    manifest = {}
    for record in records:
        if not isinstance(record, dict) or set(record) != {'id', 'kind', 'statement_sha256', 'provenance_sha256'}:
            return False
        ident = record.get('id')
        if not isinstance(ident, str) or not ident or ident in manifest:
            return False
        manifest[ident] = record
    if len(manifest) != len(supplied):
        return False
    for record in supplied:
        if not isinstance(record, dict):
            return False
        ident = record.get('id')
        m = manifest.get(ident)
        if not m:
            return False
        try:
            if m['kind'] != record['kind'] or \
               m['statement_sha256'] != digest(record['statement'].encode('utf-8')) or \
               m['provenance_sha256'] != digest(record['provenance'].encode('utf-8')):
                return False
        except (KeyError, AttributeError, UnicodeError):
            return False
    return True


def evaluate(receipt, *, expected_original=None, catalog=None, linter=None):
    """Classifies checks; never authenticates evidence, semantics or authorization."""
    state = 'REFUSED'
    issues = []
    if not isinstance(receipt, dict):
        issues.append('receipt not an object')
    elif not callable(linter):
        issues.append('source-pinned structural checker unavailable')
    else:
        try:
            issues.extend(linter(receipt, expected_original))
        except (ValueError, TypeError, KeyError, UnicodeError, RecursionError):
            issues.append('structural checker rejected malformed input')
        if not issues:
            if receipt.get('verdict') in ('SUPPORTED', 'REFUTED'):
                source = receipt.get('source_packet', {}).get('records', [])
                if not any(x.get('kind') in SOURCE_ANCHOR_KINDS for x in source):
                    issues.append('strong truth verdict lacks even a declared observation or stipulated synthetic record')
        if not issues:
            state = 'STRUCTURAL_UNBOUND' if expected_original is None else 'STRUCTURAL_BOUND'
            if catalog is not None:
                if expected_original is None:
                    issues.append('catalog matching requires separately preserved original proposition')
                elif not catalog_match(receipt, catalog):
                    issues.append('external catalog does not match exact receipt source statements')
                else:
                    state = 'SOURCE_CATALOG_MATCHED'
    if issues:
        state = 'REFUSED'
    auth_claim = bool(isinstance(receipt, dict) and isinstance(receipt.get('authorization'), dict)
                      and receipt['authorization'].get('external_approval_evidence'))
    return {
        'protocol': VERSION,
        'result_class': state,
        'structural_check': 'PASS' if state != 'REFUSED' else 'BLOCK',
        'original_proposition': 'EXTERNALLY_MATCHED' if state in ('STRUCTURAL_BOUND', 'SOURCE_CATALOG_MATCHED') else 'NOT_VERIFIED',
        'catalog_bytes': 'MATCHED_NOT_AUTHENTICATED' if state == 'SOURCE_CATALOG_MATCHED' else 'NOT_VERIFIED',
        'semantic_adjudication': 'NOT_PERFORMED',
        'source_authentication': 'NOT_PERFORMED',
        'human_authorization': 'NOT_VERIFIED',
        'free_text_approval_claim_present': auth_claim,
        'execution_authorized': False,
        'adoption_gate': 'BLOCKED',
        'issues': issues,
    }


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('receipt')
    parser.add_argument('--original-question-file', help='separately retained exact original text')
    parser.add_argument('--catalog-file', help='externally supplied source record catalog; format match ONLY')
    parser.add_argument('--catalog-sha256', help='catalog digest pinned separately by caller')
    args = parser.parse_args(argv)
    report = None
    try:
        if bool(args.catalog_file) != bool(args.catalog_sha256):
            raise ValueError('catalog file and separately supplied SHA-256 must appear together')
        if args.catalog_file and not args.original_question_file:
            raise ValueError('external original question required before catalog comparison')
        if args.catalog_sha256 and (len(args.catalog_sha256) != 64 or
                                    any(c not in '0123456789abcdef' for c in args.catalog_sha256)):
            raise ValueError('invalid catalog SHA-256')
        receipt, _ = strict_json(args.receipt)
        original = trusted_question(args.original_question_file) if args.original_question_file else None
        catalog = None
        if args.catalog_file:
            catalog, catalog_raw = strict_json(args.catalog_file)
            if digest(catalog_raw) != args.catalog_sha256:
                raise ValueError('external source-catalog digest mismatch')
        checker = load_pinned_linter(Path(__file__).resolve().parent)
        report = evaluate(receipt, expected_original=original, catalog=catalog, linter=checker)
    except (OSError, ValueError, TypeError, UnicodeError, RecursionError, json.JSONDecodeError) as exc:
        # Do not print receipt contents or secrets embedded in paths/errors.
        report = {'protocol': VERSION, 'result_class': 'REFUSED',
                  'adoption_gate': 'BLOCKED', 'execution_authorized': False,
                  'issues': ['input or source refusal: ' + type(exc).__name__]}
    print(json.dumps(report, sort_keys=True, ensure_ascii=True))
    return RESULT_CODES[report['result_class']]


if __name__ == '__main__':
    sys.exit(main())
