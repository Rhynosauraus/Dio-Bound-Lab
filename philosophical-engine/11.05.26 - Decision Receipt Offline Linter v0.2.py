#!/usr/bin/env python3
"""Offline, structural receipt linter. Does NOT verify truth, authority or model competence."""
import argparse
import copy
import hashlib
import json
import sys
from pathlib import Path

VERSION = "PE-PORTABLE-0.2-CANDIDATE"
STAGES = ["ANJA", "CHAT", "RHYAN", "ZHUANGZI", "ATHENA", "PROMETHEUS"]
DEPTH_STAGES = {"QUICK": [], "THREE": STAGES[:3], "FULL": STAGES}
VERDICTS = {"SUPPORTED", "REFUTED", "INCONCLUSIVE", "NOT_TESTABLE"}
ACTIONS = {"PREPARE", "BUILD_PROBE", "STOP_PARK"}
STATUSES = {"SYNTHETIC_RESEARCH", "DESIGN_REVIEW", "SUPERVISED_READ_ONLY"}

def _check_legacy(receipt, expected_proposition=None):
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


SOURCE_KINDS = {
    "OBSERVATION", "INFERENCE", "HYPOTHESIS", "THEORY", "METAPHOR",
    "WISH", "UNKNOWN", "FORECAST", "STIPULATED_SYNTHETIC_RECORD",
}
ROOT_FIELDS = {
    "schema_id", "protocol_version", "status", "receipt_id", "exact_proposition",
    "original_question_sha256", "source_packet", "depth", "depth_reason", "stages",
    "verdict", "justification", "recommendation", "uncertainties", "objections",
    "falsifiers", "revision_triggers", "forecasts", "authorization", "independence",
}

def _valid_nonempty_str(x):
    return isinstance(x, str) and bool(x.strip())

def check(receipt, expected_proposition=None):
    """Safe standard-library structural check. External proposition binding is caller-owned.

    This is NOT semantic validation, source authentication, or independent review.
    An input's own SHA-256 is self-consistency, not an independent provenance anchor.
    """
    errors = []
    if not isinstance(receipt, dict):
        return ["receipt must be a JSON object"]
    if set(receipt) - ROOT_FIELDS:
        errors.append("unexpected top-level fields: " + ", ".join(sorted(set(receipt) - ROOT_FIELDS)))
    for field in ("schema_id", "protocol_version", "status", "exact_proposition",
                  "depth", "depth_reason", "verdict", "justification", "recommendation"):
        if not _valid_nonempty_str(receipt.get(field)):
            errors.append("missing or invalid string: " + field)
    for field in ("uncertainties", "objections", "falsifiers", "revision_triggers"):
        val = receipt.get(field)
        if not isinstance(val, list) or any(not _valid_nonempty_str(x) for x in val):
            errors.append("invalid string list: " + field)
    question = receipt.get("exact_proposition")
    sha = receipt.get("original_question_sha256")
    if not isinstance(sha, str) or len(sha) != 64 or any(c not in "0123456789abcdef" for c in sha):
        errors.append("missing or malformed original_question_sha256")
    elif isinstance(question, str) and hashlib.sha256(question.encode("utf-8")).hexdigest() != sha:
        errors.append("original_question_sha256 does not match receipt question")
    if expected_proposition is not None and (not isinstance(expected_proposition, str) or question != expected_proposition):
        errors.append("exact proposition differs from external original")

    packet = receipt.get("source_packet")
    if not isinstance(packet, dict) or set(packet) != {"records"} or not isinstance(packet.get("records"), list):
        errors.append("source_packet must contain only records list")
        records = []
    else:
        records = packet["records"]
    for r in records:
        if not isinstance(r, dict) or set(r) != {"id", "kind", "statement", "provenance"}:
            errors.append("malformed record shape")
            continue
        if any(not _valid_nonempty_str(r.get(x)) for x in ("id", "kind", "statement", "provenance")):
            errors.append("malformed record fields")
        if not isinstance(r.get("kind"), str) or r["kind"] not in SOURCE_KINDS:
            errors.append("unrecognized source evidence classification")

    stages = receipt.get("stages")
    if not isinstance(stages, list):
        errors.append("stages must be a list")
        stages = []
    for s in stages:
        if not isinstance(s, dict):
            errors.append("malformed stage shape")
            continue
        if set(s) - {"name", "contribution", "cited_source_ids", "objection"}:
            errors.append("unexpected stage fields")
        if not _valid_nonempty_str(s.get("name")) or not _valid_nonempty_str(s.get("contribution")):
            errors.append("invalid stage name or contribution")
        cites = s.get("cited_source_ids")
        if not isinstance(cites, list) or any(not _valid_nonempty_str(c) for c in cites):
            errors.append("stage citations must be an array of nonempty source IDs")
    forecasts = receipt.get("forecasts")
    if not isinstance(forecasts, list):
        errors.append("forecasts must be a list")
    else:
        for f in forecasts:
            if not isinstance(f, dict) or set(f) - {"claim", "causal_pathway", "disconfirmation_condition", "status", "horizon"}:
                errors.append("invalid forecast object")
            elif any(not _valid_nonempty_str(f.get(k)) for k in ("claim", "causal_pathway", "disconfirmation_condition")):
                errors.append("forecast missing pathway, claim or falsifier")
    for field in ("authorization", "independence"):
        if not isinstance(receipt.get(field), dict):
            errors.append("invalid " + field + " object")
    auth = receipt.get("authorization") if isinstance(receipt.get("authorization"), dict) else {}
    if not isinstance(auth.get("constraints"), list) or any(
        not _valid_nonempty_str(x) for x in auth.get("constraints", [])
    ):
        errors.append("invalid authorization constraints")
    if errors:
        return errors
    # Once types are vetted, the existing stage-order and authority checks are safe.
    return _check_legacy(receipt, expected_proposition)

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
        "unknown source kind": lambda d: d["source_packet"]["records"][0].update(kind="FAKE_VERIFIED"),
        "question hash mismatch": lambda d: d.update(exact_proposition="Different question"),
        "unhashable depth": lambda d: d.update(depth=["FULL"]),
        "unhashable status": lambda d: d.update(status={"kind": "DESIGN_REVIEW"}),
        "unhashable citation": lambda d: d.update(depth="THREE", stages=[
            {"name": "ANJA", "contribution": "x", "cited_source_ids": [{"id": "G1"}]},
            {"name": "CHAT", "contribution": "y", "cited_source_ids": []},
            {"name": "RHYAN", "contribution": "z", "cited_source_ids": []},
        ]),
        "unexpected root authority override": lambda d: d.update(authority_override="GRANTED"),
    }
    for name, mut in mutations.items():
        candidate = copy.deepcopy(base)
        mut(candidate)
        errors = check(candidate, question)
        assert errors, name + " was not rejected"
    print("PASS: 1 valid fixture + 16 deliberate structural violations rejected")
    print("LIMIT: no semantic entailment, provenance authentication, timing, independence or authorization is verified by this test")

def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("receipt", nargs="?", help="JSON receipt file to check")
    p.add_argument("--expected-proposition", help="Exact original proposition for comparison")
    p.add_argument("--expected-proposition-file", help="Trusted original-question file, read exactly as UTF-8")
    p.add_argument("--unbound-structural-only", action="store_true", help="Allow a non-gating structure check without external proposition binding")
    p.add_argument("--self-test", action="store_true", help="Run synthetic structural negative tests")
    args = p.parse_args()
    if args.self_test:
        self_test()
        return 0
    if not args.receipt:
        p.error("Provide receipt path or --self-test")
    if args.expected_proposition is not None and args.expected_proposition_file:
        p.error("Choose one trusted original question source, not both")
    question = args.expected_proposition
    if args.expected_proposition_file:
        question = Path(args.expected_proposition_file).read_text(encoding="utf-8")
    if question is None and not args.unbound_structural_only:
        print("BLOCK: an external original proposition is required (or explicitly choose --unbound-structural-only)")
        return 3
    doc = json.loads(Path(args.receipt).read_text(encoding="utf-8"))
    findings = check(doc, question)
    for finding in findings:
        print("BLOCK:", finding)
    if findings:
        return 2
    if question is None:
        print("UNBOUND STRUCTURAL PASS ONLY — question equality not independently checked")
    else:
        print("PROPOSITION-BOUND STRUCTURAL PASS ONLY — NOT factual, independent or operational qualification")
    return 0

if __name__ == "__main__":
    sys.exit(main())
