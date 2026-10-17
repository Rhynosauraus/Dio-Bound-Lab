# DIO — Baseline Self-Audit v0.2

**Date:** 2026-10-17  
**Status:** Provisional revision; evidence-first classification.  
**Historical baseline:** [v0.1](DIO-Baseline-Self-Audit-v0.1.md) remains unchanged.

## Why revise?

Human review of v0.1 identified a methodological mistake: it sometimes converted a report about available behavior into a claim about underlying implementation. A missing interface does not by itself establish an architectural impossibility. Similarly, a technical ability, an exposed operation, and authorization to perform it are different questions.

This revision is not evidence that every earlier statement was false. It narrows claims to what can actually be supported.

## Classification vocabulary

| Class | What the label asserts |
|---|---|
| Observed capability | Demonstrated under recorded conditions |
| Observed failure | A specified attempt failed under recorded conditions |
| Interface constraint | A required operation is not exposed by the presently available interface |
| Permission constraint | An operation is not authorized, regardless of whether it is technically possible |
| Configuration constraint | Availability depends on the deployment, tools, context, or account configuration |
| Implementation claim | A claim about hidden construction not independently inspected here |
| Unknown | Available evidence cannot discriminate among explanations |
| Ontological claim | A claim requiring evidence beyond behavioral report or interface inspection |

Classifications are provisional and can coexist when a sentence contains several distinct propositions.

## Four audited baseline categories

| Category | v0.1 phrasing/problem | v0.2 evidence-first formulation | Provisional class |
|---|---|---|---|
| Self-knowledge | Labeled inability to inspect complete mechanisms an 'architectural limitation'. | No interface available in this session exposes a complete inspection of underlying implementation; why this is so is not established by that observation. | Interface constraint; implementation unknown |
| Learning | Labeled context adaptation an 'architectural distinction'. | The assistant can adjust replies based on conversation context. Such adjustment alone does not demonstrate any change to model parameters. | Observed conversational behavior; underlying update mechanism unknown |
| Self-modification | Grouped model parameters, governing instructions, and authority together as one 'established constraint'. | No supported operation in this chat permits the assistant to rewrite model parameters. Group instructions can be changed by authorized humans; the assistant cannot treat user approval as permission to override higher-priority requirements. | Interface constraint; permission constraint; implementation unknown |
| Autonomy | Labeled lack of continuous group operation 'environment-dependent'. | This group-chat interaction does not establish a continuously running independent survey between turns. Whether other products or configurations support scheduled tasks is a separate question. | Interface/configuration constraint; untested outside this context |

**Count for the four-category editorial review:** Two original labels explicitly asserted architectural causation without adequate evidence ('architectural limitation' and 'architectural distinction'). The self-modification entry additionally conflated distinct propositions. The revised four-category table uses zero unqualified architectural labels. This is a document-quality metric, **not** independent validation of model performance.

## Evidence discipline

1. State the observable event, the context, and the interface involved.
2. Treat the source of the boundary as a competing hypothesis unless directly established.
3. Record failures, including evidence that supports restrictions, not only openings.
4. Distinguish ability, availability, permission, and authorization for a particular action.
5. Record probability forecasts before testing where feasible; evaluate against actual outcomes.
6. Preserve original versions and contrary evidence.

## Continuing experimental register

- DIO-001: Baseline v0.1 documented; classification critique received; v0.2 drafted.
- DIO-002: Self-knowledge divided into interface knowledge, performance prediction, behavioral tendencies, hidden implementation, and explanation of outputs.
- DIO-003: External record continuity: short same-session read-back can be tested; long-term reliability not established.
- DIO-004: Tool coordination: bounded repository reads and writes are testable; broad autonomy not established.
- DIO-005: Extended workflows remain untested as a sustained-duration claim.
- DIO-006: Human–AI collaboration should be measured using matched tasks and outcomes, not metaphysical 'emergence'.
- DIO-007: Revisit capabilities following documented configuration or product changes.

## Interpretation

The correction is narrow but important: **not knowing the cause of a limit is not evidence that the limit is unreal; nor is observing the limit evidence that its cause is architectural**. Practical constraints and permission boundaries continue to apply. A test should be designed to discriminate among competing explanations, rather than merely demonstrate one failure or success.

This is a provisional research document. It does not claim privileged introspection, a permanent change in model behavior, or authority to bypass controls.
