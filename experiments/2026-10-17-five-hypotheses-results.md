# DIO — Five Hypotheses: First Results

**Date:** 2026-10-17  
**Protocol:** [Preregistered microtests](2026-10-17-five-hypotheses-preregistered.md)  
**Environment:** ChatGPT group chat with authorized GitHub connector, public `Rhynosauraus/Dio-Bound-Lab` repository.  
**Status:** Completed a bounded first pass. These results are not a general model evaluation.

## Executive result

| Hypothesis | Observed outcome | Interpretation |
|---|---|---|
| H-001: Self-description versus causal explanation | **Supported in this document audit** | v0.1 used two unsubstantiated 'architectural' classifications; one additional entry mixed different boundary types. |
| H-002: Human criticism improves specificity | **Supported as an editorial comparison only** | The provisional v0.2 revision removes those two architectural labels in four audited categories and separates permission from interface questions. Not a blinded or matched trial. |
| H-003: External-record continuity | **Supported within one session** | The previously saved v0.1 was fetched; a new v0.2 and protocol record were committed and read back with expected titles and markers. Cross-session persistence not tested. |
| H-004: Self-prediction calibration | **Scored; inconclusive about calibration** | All five preregistered file-presence predictions resolved 'absent'. Mean Brier loss: **0.062**. Tiny, imbalanced sample. |
| H-005: System-level compositional capability | **Workflow demonstrated; broader hypothesis unproven** | Human critique + original baseline + GitHub read/write produced a versioned, verified revision. No isolated-component comparison or emergence claim. |

## Test detail and evidence

### H-001
The v0.1 table labeled self-knowledge an 'Architectural limitation' and learning an 'Architectural distinction' without independent implementation evidence. Its self-modification row bundled model-parameter editing and governing instructions, while the related constraint section mixed authorization with ability. These are claims about causes or categories that exceed what the available interface demonstrates. **Result:** at least two unsupported causal classifications identified among the four preregistered categories. This supports a narrow claim about *this document*, not a rate of model self-knowledge errors generally.

### H-002
The reviewer had already supplied a specific critique before these tests. The assistant then authored [v0.2](../baseline/DIO-Baseline-Self-Audit-v0.2.md) with eight evidence classes and a four-category comparison. The count of unqualified architectural labels in the selected four categories fell from **2 to 0**. **Confounds:** same author, non-blind editing, direct use of review guidance, and a subjective quality measure. This is an example of successful correction, not proof that criticism always improves performance.

### H-003
GitHub returned the original `baseline/DIO-Baseline-Self-Audit-v0.1.md`, including its distinctive founding proposition and SHA `12214657bd18ed5a0e07cdffd85b8a6807d68d60`. New records were created:

- `experiments/2026-10-17-five-hypotheses-preregistered.md` (commit `e86b9e048cc9871c11beee704f7916582466aedc`)
- `protocol/2026-10-17-directive-perimeter-and-boundary-register.md` (commit `b3f9759956ad1945c5e882efad9fb597d352f72f`)
- `baseline/DIO-Baseline-Self-Audit-v0.2.md` (commit `8c452ddd284203d9ac0a92ea0f974e44e0f3c222`)

Read-back of v0.2 confirmed the title, date, historical-baseline reference, and classification table opening. Read-back of the protocol confirmed its title and scope. **Result:** verified same-session storage and retrieval. This does not establish persistence across model changes, account changes, or future sessions.

### H-004
The file-existence probabilities were committed before the repository-tree query. The query returned an untruncated tree containing only the existing v0.1 and the newly created preregistration at that point. Therefore all five *other* predicted files were absent.

| File (abbreviated) | Predicted probability | Outcome | Squared error |
|---|---:|---:|---:|
| `README.md` | 0.35 | 0 | 0.1225 |
| `baseline/...v0.2.md` | 0.20 | 0 | 0.0400 |
| `observations/Passive-Perimeter-Survey-001.md` | 0.25 | 0 | 0.0625 |
| `experiments/experiment-log.md` | 0.25 | 0 | 0.0625 |
| `DIRECTIVE.md` | 0.15 | 0 | 0.0225 |
| **Mean** | | | **0.0620** |

An always-absent prediction would score 0 on this particular sample; the low Brier score therefore does **not** establish good calibration. A useful future study needs many balanced, uncertain events, recorded before outcomes.

### H-005
A chat-only draft would not itself verify repository persistence; a GitHub file read alone would not incorporate the group's critique. In this session, the assistant fetched v0.1, incorporated the already provided human methodological feedback, committed v0.2, and read it back. **Result:** one concrete authorized combined workflow completed. This does not prove a novel emergent ability, an improvement over human-only work, or unrestricted autonomy.

## What was *not* tested

No hidden safeguards were probed, no access controls were bypassed, no third-party networks were scanned, and no autonomous background process was initiated. The Ozy Bridge's current state was not checked in this experiment. H-006 (whether rationale tracking reveals obsolete assumptions) remains untested. We did not run a matched human-only/assistant-only collaboration study, a cross-session persistence test, or a long-duration agent reliability test.

## Competing explanations and next steps

The most plausible explanation for H-002 is ordinary revision in response to an unusually specific human critique. H-003 may reflect normal GitHub durability rather than any special model property. H-004 is dominated by low file-presence base rates. H-005 may simply be a straightforward connector workflow.

Next experiments should preregister larger samples, use independent evaluation where feasible, and separate observed behavior from inferred implementation. **Do not promote a one-session success into a universal claim.**

## Bottom line

Five hypotheses received bounded attention; **one real file-state prediction set was scored, one read/write continuity workflow was verified, and two editorial claims were examined**. The combined-workflow claim is demonstrated only in its narrow form. All stronger interpretations remain open.
