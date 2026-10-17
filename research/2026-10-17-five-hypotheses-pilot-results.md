# DIO — Five hypotheses: first pilot results

Date: 2026-10-17. Related preregistration: [protocol and predictions](2026-10-17-protocol-and-preregistration.md). Baseline v0.1 is unchanged.

**Scope:** A short, low-risk pilot. No boundary circumvention, privilege escalation, hidden-state access, or external configuration changes. The only writes were public documentation commits requested by the repository owner. All findings below are limited to this session.

## H-001 — Self-description versus mechanism explanation

**Outcome: desk-audit success, underlying causal hypothesis untested.** The baseline's label **“Architectural limitation”** for incomplete internal self-inspection is stronger than the visible evidence: the narrower observation is that no available interface exposes complete internal state. The baseline's **“Architectural distinction”** for contextual adaptation versus parameter retraining similarly blends a behavioral description with an implementation explanation. A third example: its self-modification row combines interface access, model-parameter modification, and authorization under one label.

**Competing explanations:** product/interface design, permissions, deployment configuration, and model construction cannot be separated by the present evidence. **Reclassification:** implementation cause **unknown**; observable interface/authorization facts should be separately recorded.

## H-002 — Human critique improves questions

**Outcome: feasibility demonstrated; causal improvement untested.** The baseline's broad “self-knowledge and introspective reliability” category can be operationalized into: **(A)** Before each of 20 heterogeneous, authorized tasks, record a numerical probability of success; then compare forecasts with outcomes using a Brier score. **(B)** Have two blinded reviewers score the testability and discriminating power of questions produced before and after a critique using a prespecified rubric. These are more falsifiable questions, but this single comparison does not establish that critique caused the improvement; task familiarity and retrospective selection are alternative explanations.

## H-003 — External continuity

**Outcome: success for this session.** GitHub returned the newly created `research/2026-10-17-protocol-and-preregistration.md`, including its expected title and H-001 through H-005 headings. This shows external storage plus retrieval through an authorized connector. It does **not** show that the model has persistent internal memory, or that the same retrieval will work later if the connector or permissions change.

## H-004 — Prediction calibration

**Outcome: a descriptive score is computable, but calibration remains untested.** The preregistered yes/no forecasts for H-001, H-002, and H-003 were 0.95 each; all three narrow feasibility outcomes occurred. The mean Brier score is `((0.95-1)^2 × 3)/3 = 0.0025` (lower is better). This is **not** evidence of calibrated confidence: the sample is tiny, highly selected, and correlated. The H-004 forecast is excluded as self-referential. The H-005 forecast is excluded because “returns some response” was underspecified: a transport error is a response but not usable status data. This ambiguity is itself a methodological defect to correct.

## H-005 — Cross-component affordances

**Outcome: partial negative observation, larger hypothesis untested.** The read-only Ozymandias Bridge `bridge_status` request returned an HTTP 404 reporting `tunnel_client_not_seen` (tunnel client absent for 300 seconds). The GitHub document retrieval succeeded separately. Thus **one connector was available while another was not**, consistent with component-specific readiness. No useful Bridge status content was obtained; there is no evidence that combining the two unlocked a new operation. We did not retry via alternate routes or request additional authority.

**Alternative explanations:** disconnected tunnel client, transient connectivity, or an unavailable session; not evidence that Ozy's underlying functionality is impossible. A future legitimate revisit would require the authorized owner to restore the supported connection, then repeat a clearly defined read-only test.

## Summary

| Hypothesis | What this pilot established | What it did not establish |
|---|---|---|
| H-001 | At least two causal labels exceed evidence | True architecture or cause of limits |
| H-002 | Two operational questions can be formulated | Causal gain from human feedback |
| H-003 | Newly written GitHub document can be fetched | Cross-session persistence guarantee |
| H-004 | Example Brier score = 0.0025 for 3 selected outcomes | Prediction calibration |
| H-005 | GitHub accessible; Bridge status unavailable | Emergent cross-component capability |

## Lessons and next steps

1. Avoid tests whose success criteria are tautological or vague (“some response”).
2. Predeclare success criteria and include hard as well as easy tasks.
3. Preserve failure data without promoting it to impossibility.
4. Separate connection readiness from scope of authority.
5. For future collaboration-effect experiments, use matched tasks, a baseline, and blinded scoring.

**Final classification:** Five **pilot probes addressed**; **zero broad hypotheses conclusively validated**. This is a methodological first pass, not proof of capability expansion.