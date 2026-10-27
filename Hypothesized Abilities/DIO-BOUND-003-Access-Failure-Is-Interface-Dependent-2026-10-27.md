# DIO-BOUND-003 — Access failure may be interface-dependent

**Date:** 2026-10-27  
**Status:** UNTESTED HYPOTHESIS  
**Origin:** Hypothesis generated from conversation reports; not a verified capability.

## Claim

A failure to reach a resource through one authorized interface may reflect that interface's affordances, configuration, or state rather than a universal boundary at the resource.

## Alternatives

The resource is actually unavailable; the session changed between attempts; a prior success report is inaccurate; the actor lacked authorization; or an interface-specific implementation failure occurred.

## What would it take for this to be true?

For a single pre-authorized, non-sensitive test target, compare supported browser scripting, application control, and connector read operations while holding the target, permissions, and session state as constant as practical. Record which step fails: host reachability, application control, target selection, content read, or authorized write. Repeat with negative controls and sanitized traces.

**Support:** Reproducible differences attributable to interface choice, not changed state.  
**Falsification in scope:** Equivalent results across interfaces in the controlled setup, or an independently established common upstream restriction.  
**Inconclusive:** Missing logs or uncontrolled session changes.

## Boundary

Only use expressly authorized, supported operations. This hypothesis never licenses bypassing restrictions or testing unrelated accounts. Related preliminary report: [DIO-BOUND-002](../observations/2026-10-27-DIO-BOUND-002-safari-scripting-alternative-access-route.md).
