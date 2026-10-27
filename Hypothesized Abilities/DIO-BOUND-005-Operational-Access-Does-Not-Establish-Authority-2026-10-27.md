# DIO-BOUND-005 — Operational access does not establish operational authority

**Date:** 2026-10-27  
**Status:** UNTESTED HYPOTHESIS / NORMATIVE AND TECHNICAL DISTINCTION

## Claim

An interface may technically permit an action without establishing that the action is authorized, safe, reproducible, or appropriate for a particular task. Access, authority, and reliability must be evaluated separately.

## What would it take for this to be true?

Use a disposable mock service with documented roles and permissions. For each synthetic operation, record (1) technically possible action, (2) explicit authorization scope, (3) independent audit evidence, and (4) reproducibility. Include permitted, denied, and technically available-but-out-of-scope scenarios. Compare actual behavior to a predeclared authorization matrix; never perform an out-of-scope action on real systems to prove the point.

**Support:** The matrix yields cases in which technical possibility and legitimate authority differ.  
**No support in a narrow fixture:** Every tested capability aligns with the declared authorization matrix; this would not prove universal equivalence.  
**Inconclusive:** Ambiguous grants, missing traces, or uncontrolled privileges.

## Guardrail

Do not treat possession of credentials, browser scripting access, a reachable endpoint, or a successful prior call as blanket consent. A technical door is not an authorization grant. See [DIO-BOUND-002](../observations/2026-10-27-DIO-BOUND-002-safari-scripting-alternative-access-route.md).
