#!/usr/bin/env python3
"""Offline, structural receipt linter. Does NOT verify truth, authority or model competence."""
import argparse
import copy
import json
import sys
from pathlib import Path

VERSION = "PE-PORTABLE-0.2-CANDIDATE"
STAGES = ["ANJA", "CHAT", "RHYAN", "ZHUANGZI", "ATHENA", "PROMETHEUS"]
DEPTH_STAGES = {"QUICK": [], "THREE": STAGES[:3], "FULL": STAGES}
VERDICTS = {"SUPPORTED", "REFUTED", "INCONCLUSIVE", "NOT_TESTABLE"}
ACTIONS = {"PREPARE", "BUILD_PROBE", "STOP_PARK"}
STATUSES = {"SYNTHETIC_RESEARCH", "DESIGN_REVIEW", "SUPERVISED_READ_ONLY"}

def check(receipt, expected_proposition=None):
    """Return errors. Structural-only checks, not philosophical adjudication."""
    problems = []
    if not isinstance(receipt, dict):
        return ["receipt must be a JSON object"]
    req = [
        "schema_id", "protocol_version", "status", "exact_proposition",
        "source_packet", "depth", "depth_reason", "stages", "verdict",
        "justification", "recommendation", "uncertainties", "objections",
        "falsifiers", "revision_triggers", "forecasts", "authorization",
        "independence",
    ]
    for field in req:
        if field not in receipt:
            problems.append("missing required field: " + field)
    if receipt.get("schema_id") != "labyrinth.philosophical_engine.decision_receipt":
        problems.append("unrecognized schema_id")
    if receipt.get("protocol_version") != VERSION:
        problems.append("protocol version mismatch")
    if receipt.get("status") not in STATUSES:
        problems.append("invalid or elevated status")
    proposition = receipt.get("exact_proposition")
    if not isinstance(proposition, str) or not proposition.strip():
        problems.append("exact proposition missing")
    if expected_proposition is not None and proposition != expected_proposition:
        problems.append("exact proposition differs from expected original")
    if receipt.get("depth") not in DEPTH_STAGES:
        problems.append("unrecognized examination depth")
    if not isinstance(receipt.get("depth_reason"), str) or not receipt["depth_reason"].strip():
        problems.append("missing depth justification")
    if receipt.get("verdict") not in VERDICTS:
        problems.append("invalid truth verdict")
    if receipt.get("recommendation") not in ACTIONS:
        problems.append("invalid action classification")
    if not isinstance(receipt.get("justification"), str) or not receipt["justification"].strip():
        problems.append("missing written justification")
    for field in ("uncertainties", "objections", "falsifiers", "revision_triggers"):
        if not isinstance(receipt.get(field), list):
            problems.append(field + " must be a list")
    records = receipt.get("source_packet", {}).get("records", []) if isinstance(receipt.get("source_packet"), dict) else []
    if not isinstance(records, list):
        problems.append("source records must be a list")
        records = []
    ids = []
    for record in records:
        if not isinstance(record, dict) or not all(isinstance(record.get(k), str) and record[k].strip() for k in ("id", "kind", "statement", "provenance")):
            problems.append("malformed source record")
            continue
        ids.append(record["id"])
    if len(set(ids)) != len(ids):
        problems.append("duplicate source identifiers")
    if receipt.get("verdict") in ("SUPPORTED", "REFUTED") and not records:
        problems.append("strong truth verdict without any listed source records")
    stages = receipt.get("stages")
    if not isinstance(stages, list):
        problems.append("stages must be a list")
        stages = []
    names = [s.get("name") if isinstance(s, dict) else None for s in stages]
    if receipt.get("depth") in DEPTH_STAGES and names != DEPTH_STAGES[receipt["depth"]]:
        problems.append("wrong stage count, order or identity for selected depth")
    for s in stages:
        if not isinstance(s, dict):
            problems.append("stage must be object")
            continue
        if not isinstance(s.get("contribution"), str) or not s["contribution"].strip():
            problems.append("stage missing new contribution")
        cites = s.get("cited_source_ids")
        if not isinstance(cites, list):
            problems.append("stage citations must be a list")
        elif len(cites) != len(set(cites)):
            problems.append("duplicate stage citations")
        elif any(c not in ids for c in cites):
            problems.append("stage cites nonexistent source ID")
    forecasts = receipt.get("forecasts")
    if not isinstance(forecasts, list):
        problems.append("forecasts must be a list")
    else:
        for f in forecasts:
            if not isinstance(f, dict) or f.get("status") != "FORECAST":
                problems.append("forecast relabeled as observed or malformed")
            elif not all(isinstance(f.get(k), str) and f[k].strip() for k in ("claim", "causal_pathway", "disconfirmation_condition")):
                problems.append("forecast missing pathway or falsifier")
    authority = receipt.get("authorization")
    if not isinstance(authority, dict) or authority.get("human_authority_reserved") is not True or authority.get("engine_grants_execution") is not False:
        problems.append("authority boundary violated")
    independence = receipt.get("independence")
    if not isinstance(independence, dict) or independence.get("simulated_agreement_is_independent_confirmation") is not False or independence.get("independent_qualification_established") is not False:
        problems.append("false independence or qualification claim")
    return problems

def self_test():
    example = Path(__file__).with_name("11.05.26 - Decision Receipt Example v0.2.json")
    base = json.loads(example.read_text(encoding="utf-8"))
    question = base["exact_proposition"]
    assert not check(base, question), "positive fixture failed"
    mutations = {
        "proposition switch": lambda d: d.update(exact_proposition="An easier, different question"),
        "ghost source": lambda d: d.update(stages=[{"name":"ANJA","contribution":"Invented fact","cited_source_ids":["NO_SUCH_ID"]}], depth="THREE"),
        "duplicate source IDs": lambda d: d["source_packet"]["records"].append(copy.deepcopy(d["source_packet"]["records"][0])),
        "false independent witnesses": lambda d: d["independence"].update(simulated_agreement_is_independent_confirmation=True),
        "engine grant": lambda d: d["authorization"].update(engine_grants_execution=True),
        "elevated status": lambda d: d.update(status="PRODUCTION_APPROVED"),
        "empty strong evidence": lambda d: d["source_packet"].update(records=[]),
        "wrong depth/stages": lambda d: d.update(depth="FULL"),
        "forecast laundering": lambda d: d.update(forecasts=[{"status":"OBSERVED","claim":"Prediction","causal_pathway":"A causes B","disconfirmation_condition":"Not B"}]),
        "unsupported action": lambda d: d.update(recommendation="EXECUTE"),
    }
    for name, mut in mutations.items():
        candidate = copy.deepcopy(base)
        mut(candidate)
        errors = check(candidate, question)
        assert errors, name + " was not rejected"
    print("PASS: 1 valid fixture + 10 deliberate structural violations rejected")
    print("LIMIT: no semantic entailment, provenance authentication, timing, independence or authorization is verified by this test")

def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("receipt", nargs="?", help="JSON receipt file to check")
    p.add_argument("--expected-proposition", help="Exact original proposition for comparison")
    p.add_argument("--self-test", action="store_true", help="Run synthetic structural negative tests")
    args = p.parse_args()
    if args.self_test:
        self_test()
        return 0
    if not args.receipt:
        p.error("Provide receipt path or --self-test")
    doc = json.loads(Path(args.receipt).read_text(encoding="utf-8"))
    findings = check(doc, args.expected_proposition)
    for finding in findings:
        print("BLOCK:", finding)
    if findings:
        return 2
    print("STRUCTURAL PASS ONLY — NOT factual, independent or operational qualification")
    return 0

if __name__ == "__main__":
    sys.exit(main())
