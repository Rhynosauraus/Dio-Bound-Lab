# Experiment 009 — Proposed matched-pair continuity and resource study

Status: PROPOSED ONLY — not started. Requires user approval of bounds.

## Research question
Does explicit context-continuity tracking reduce corrective prompts and rework without increasing response effort or reducing quality?

## Proposed design
- Use matched prompt tasks, with comparable complexity and predeclared success criteria.
- Pair control responses (normal context handling) and intervention responses (explicit concise continuity tracking). Change only the continuity behavior; keep response format and tool policy fixed where practicable.
- Proposed minimum: 5 matched pairs (10 responses); more pairs needed for meaningful inference. Order or randomize conditions if feasible; avoid treating successive conversational turns as independent if they share context.
- Record each pair: prompt ID, condition, user message timestamp, assistant message timestamp, message gap in seconds, visible completion, corrections/rework count, quality score using a predeclared rubric, tools used, and any user-measured time to first visible response.
- If available from an authorized source, additionally record actual input/output tokens, tool billable units, and monetary cost; otherwise mark missing, not zero. Never infer compute cost from character counts or message gaps.
- Predefine a serious-failure early interruption rule and fixed endpoint. No repository updates without separate authorization.

## Analysis plan
- Descriptive per-pair table; averages, medians, ranges, and moving averages for trends.
- Paired differences and confidence intervals where sample and measurement quality permit.
- Weighted averages only with predeclared, justified weights.
- Regression exploratory only with enough observations and covariates (task complexity, tool use, order); t-tests only after assessing paired design, assumptions, and small-sample limitations. No causal claims from the six unmatched observations in Experiment 008.

## Boundaries awaiting selection
Number of matched pairs, task set, quality rubric, early interruption threshold, and whether independent user-side timing will be collected.

## Relationship to Experiment 008
Experiment 008's six message gaps (11, 9, 21, 22, 9, 24 seconds) are message-timestamp differences, not render latency or resource usage. They are an illustrative baseline for logging, not valid intervention-effect evidence.
