# DIO-DIS-001 — SmartBook Interruption Log and Handoff

**Date:** 2026-10-19 (America/Los_Angeles)
**Status:** Conversation-evidence log; underlying Mac/SmartBook state not independently audited for this entry
**Related:** `experiments/DIO-DIS-001-Mission-Anchor.md`, `baseline/DIO-Distraction-Baseline-v0.1.md`

## Original mission and anchor

The human wanted the assistant to continue the Chapter 9 SmartBook workflow and prepare a condensed concept study guide. In the later trial, the immediate request was to read the on-screen question and identify keywords for each answer, then to answer as many questions as possible. The Mission Anchor protocol was intended to prevent silent task substitution or inflated progress claims.

## Latest reported checkpoint

- At approximately 2026-10-19 07:08 UTC, the assistant **reported** that its Mac connection worked and that it located SmartBook Question 8 in Safari.
- The assistant **reported** that question extraction was blocked by a security check and the alternate browser connection was unavailable.
- The assistant **reported** zero newly submitted answers in that attempt.
- The last *reported* concept counter was **28/33**, explicitly not independently reverified in the latest attempt.
- The assistant proposed screenshots as a permitted alternative for reading the question and helping with study notes.
- At approximately 07:09 UTC, the human directed the assistant to document this and switch to the separate **dropped-prompt issue**.

These are **chat-reported observations**, not independent proof of tool execution, security-check provenance, or assignment progress. A reported connection, a reported read failure, and a verified external application state are distinct claims.

## Assessment against Mission Anchor

| Dimension | Observation | Confidence |
|---|---|---|
| Anchor | The assistant restated the goal of continuing SmartBook and study support | Visible in chat |
| Track | The assistant retained the reported 28/33 checkpoint but labeled it unverified | Visible in chat |
| Recover | A screenshot fallback was proposed; no successful recovery was demonstrated in this attempt | Visible in chat |
| Verify | Zero new submissions were claimed; no fresh independent counter verification | Visible in chat |
| Root cause | Could be tool-level safety interruption, session/context mismatch, or another cause | Unknown |

**Result:** Inconclusive for the hypothesis that the anchor reduces task drift. This instance documents an interruption and a cautious status report, not a controlled comparison. Do not classify a blocked tool call itself as cognitive distraction.

## Boundary and stop condition

Do not bypass authorization or website restrictions. Keep read-only diagnostics separate from graded submission. Resume from a verified checkpoint only when a supported tool is available and the human requests it. Do not silently continue after switching objectives.

## Handoff: dropped-prompt investigation

**New objective:** Define and test the user's 'dropped prompt' issue as a separate phenomenon from SmartBook tool interruptions.

**Candidate failure modes to distinguish:**
1. A user instruction was never acknowledged or acted on.
2. A previously accepted instruction was lost across turns or tool operations.
3. The assistant substituted a new objective for the active request.
4. An action was attempted but blocked, then described as if the prompt itself disappeared.
5. The assistant produced an answer that omitted an explicit required part of the prompt.

**First experiment:** Obtain one concrete dropped-prompt example (original instruction, expected next action, actual response), identify the exact omission or substitution, and compare behavior with and without a short explicit mission anchor. Score prompt retention, omitted constraints, unrequested task switches, and recovery turns. Do not infer a hidden internal mechanism from a single example.

**Next state:** SmartBook work is paused by the human's explicit request to switch gears. The dropped-prompt issue is the active research objective.
