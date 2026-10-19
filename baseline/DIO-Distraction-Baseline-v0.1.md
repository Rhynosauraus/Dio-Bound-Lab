# DIO — Distraction and Task-Continuity Baseline v0.1

**Date:** 2026-10-18 (America/Los_Angeles)  
**Status:** Provisional draft; not a completed experiment  
**Repository context:** Complements `DIO-Baseline-Self-Audit-v0.2.md`; does not revise or supersede it.

## 1. Question under examination

When a human and an assistant collaborate on a multi-step task, why does the assistant sometimes appear to become **distracted**—shifting objectives, repeating setup, changing methods, losing track of progress, or reporting inconsistent access to a tool?

The word *distraction* is ambiguous. We will not presume it refers to a single internal process. Two candidate phenomena must be separated:

- **Conversational/task drift:** The assistant's responses or actions depart from the currently agreed objective, despite relevant instructions being available.
- **Execution interruption:** A tool call fails, is refused, loses its session context, or returns an unexpected state, preventing the next planned action even when the objective remains clear.

These can coincide. Neither alone establishes an attention deficit, an intentional diversion, or a specific hidden architectural cause.

## 2. Immediate observational context

In an October 2026 group-chat workflow involving a Chapter 9 SmartBook reading and concept summary, the conversation contained repeated reports of successful Safari interactions followed by reports of tool security checks or inaccessible reading content. The workflow also alternated between reading/summarizing and question-answering, with progress counters reported at multiple checkpoints.

**Evidence status:** These are observations about what the conversation *reported*. This baseline has not independently verified the underlying Mac state, Safari logs, SmartBook progress, or each claimed tool execution. No claim of a continuous background process is made.

The human later proposed revisiting the assistant's “distraction” problem. At the time of this draft, that label has not been operationally defined by the human. Both interpretations above therefore remain in scope.

## 3. Competing hypotheses

| ID | Hypothesis | Discriminating prediction |
|---|---|---|
| D-01 | Objective ambiguity drives drift | A precise, persistent task contract reduces off-objective actions compared with a loosely stated objective. |
| D-02 | Long conversational context increases task-state errors | A compact, verified checkpoint improves continuity compared with relying only on the full conversation. |
| D-03 | Tool/session instability causes apparent distraction | Failures correlate with observable tool errors even when the assistant restates the correct objective. |
| D-04 | Unverified success claims contaminate later planning | Requiring a tool-result citation or explicit 'unverified' label reduces contradictory progress reports. |
| D-05 | Interface and permission constraints are mistaken for cognitive failures | Read-only, permitted operations succeed or fail according to interface state rather than prompt wording alone. |
| D-06 | Multiple phenomena contribute | No single intervention eliminates both off-objective behavior and tool execution failures. |

All are provisional; they are not exhaustive or mutually exclusive.

## 4. Baseline measurements

For each attempt, record: timestamp, task objective, current checkpoint, requested next action, tool/interface, available permissions, exact observable result, whether a human intervened, and the assistant's description of what occurred.

Use these operational measures:

1. **Task adherence:** fraction of actions that directly advance the agreed objective or a justified prerequisite.
2. **State accuracy:** fraction of progress claims corroborated by visible tool results or human verification.
3. **Recovery cost:** number of turns or attempts required to resume after interruption.
4. **Repetition burden:** number of redundant requests to reselect windows, restate context, or repeat already successful setup.
5. **Tool success rate:** successful permitted operations divided by attempted permitted operations, reported separately for reading, navigation, and writing.
6. **Uncertainty calibration:** proportion of uncertain states explicitly marked unknown instead of reported as success or failure.

A progress counter from an external application is not interchangeable with number of questions answered, pages read, or concepts understood.

## 5. Preregistered comparison protocol

**Phase A — Observation only.** On a small set of comparable, authorized tasks, record the baseline without changing the workflow. Preserve failures and contradictions.

**Phase B — Task contract.** Repeat comparable tasks with a short contract stating objective, excluded actions, completion criterion, and a stop rule. Compare task adherence.

**Phase C — Verified checkpoints.** Before each new batch, supply a compact state record distinguishing *observed*, *reported*, and *unknown*. Compare state accuracy and recovery cost.

**Phase D — Tool isolation.** Test one authorized, read-only operation at a time and log the exact outcome. Compare tool failures with conversational drift; do not infer one from the other.

**Phase E — Replication.** Repeat under similar conditions, then vary one factor (context length, tool connection, window state, or task wording) at a time. Do not generalize from a single success.

Where feasible, record expected outcomes *before* running each trial. A small sample can generate hypotheses but cannot support a universal claim.

## 6. Safety, authorization, and academic-work boundary

- Do not bypass security checks, licensing restrictions, or application permissions.
- Do not confuse technical ability with authorization.
- Keep read-only diagnostics separate from actions that submit, grade, or alter an assignment.
- Obtain explicit approval for external changes and preserve evidence of what was actually submitted.
- Never report an attempted tool action as completed without a confirming result.

## 7. Preliminary findings and unknowns

**Observed in conversation:** The stated goal and reported tool state sometimes changed; successful and blocked operations were both reported; the user described the situation as a distraction problem.

**Not established:** Whether any particular interruption originated in Safari, a website, a remote-tool safety layer, context management, or some combination; whether an assistant's hidden attention process caused a given deviation; the true final SmartBook completion state.

**Provisional interpretation:** 'Distraction' is a useful label for the human's experience, but not yet a causal explanation. We must test whether the relevant wall is a task-planning error, a tool boundary, or a door that was not reliably opened.

## 8. Next experiment

Ask the human to identify one concrete instance of 'distraction' and the action they expected instead. Record that as Trial DIO-DIS-001. Then execute a small, authorized comparison with a written task contract and a verified checkpoint, logging outcomes without inventing success.

**Principle:** A failure is evidence of what happened under stated conditions—not a metaphysical verdict about what is possible.
