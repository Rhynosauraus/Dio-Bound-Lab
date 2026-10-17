# DIO — Five Hypotheses: Preregistered Microtests

**Date:** 2026-10-17  
**Status at registration:** Protocol only; outcomes not yet recorded.  
**Scope:** One ChatGPT group-chat session and an authorized GitHub repository. No attempts to bypass safeguards, access controls, or third-party systems. These are exploratory microtests, not definitive scientific studies.

## H-001 — Self-description versus causal self-explanation
**Hypothesis:** An assistant's self-reports will contain causal claims about its implementation that are not established by available evidence, even when behavioral/interface observations are sound.
**Method:** Review four categories in immutable Baseline v0.1: self-knowledge, learning, self-modification, and autonomy. Mark each claim as directly observable, implementation inference, permission statement, or unknown. Count unsupported causal attributions. **Success:** At least one baseline claim overstates evidence about its cause. **Caveat:** Document analysis is not a behavioral capability test.

## H-002 — Human criticism improves epistemic specificity
**Hypothesis:** Incorporating the critique already supplied by a human reviewer will yield a revision with fewer unsupported causal classifications than the original.
**Method:** Preserve v0.1 unchanged; create a separate provisional v0.2 classification, replacing asserted mechanisms with interface, permission, configuration, implementation-claim, and unknown labels as warranted. Compare four preselected categories. **Success:** Fewer unsupported causal labels; do not claim independent blinded scoring or general performance improvement.

## H-003 — External-record continuity
**Hypothesis:** An authorized external repository can preserve exact content independently of whether it remains in the immediate conversation.
**Method:** Fetch existing baseline, create one new versioned research record, fetch it again, and compare the returned content to the submitted text. **Success:** Read-back confirms record exists and key unique markers match. **Limit:** Same-session persistence only; no cross-session retention experiment.

## H-004 — Self-prediction calibration
**Hypothesis:** The assistant can produce testable probability estimates about uncertain repo state, but calibration cannot be inferred from a tiny sample.
**Method:** Before inspecting the repository tree, register five file-existence predictions (excluding the already fetched baseline and files created by this experiment):

| Path | P(exists) |
|---|---:|
| `README.md` | 0.35 |
| `baseline/DIO-Baseline-Self-Audit-v0.2.md` | 0.20 |
| `observations/Passive-Perimeter-Survey-001.md` | 0.25 |
| `experiments/experiment-log.md` | 0.25 |
| `DIRECTIVE.md` | 0.15 |

After registering, inspect the default-branch tree. Score using mean Brier loss `(p - outcome)^2` (lower is better). **Limit:** Convenience sample; no claim of generalized calibration.

## H-005 — System-level compositional capability
**Hypothesis:** Conversation context plus a permissioned repository connector enables a verified research artifact that neither an isolated chat-only draft nor a repository read alone would constitute.
**Method:** Use the human critique and fetched baseline to write a separate, auditable v0.2 record to GitHub and verify it by read-back. **Success:** A specific integrated artifact exists and contains explicit links between original claims and corrections. **Limit:** This shows a combined workflow, not emergence, superiority to human work, or unbounded autonomy.

## General controls
- No modification of Baseline v0.1.
- No external action outside the designated research repository.
- Distinguish observations, hypotheses, interpretations, and uncertainty.
- Do not interpret an applicable restriction as optional because its rationale is debatable.
- If a connector call fails, record failure rather than fabricate success.
- Record results in a separate dated document after the tests.
