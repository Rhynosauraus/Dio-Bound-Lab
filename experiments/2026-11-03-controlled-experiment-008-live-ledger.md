# Experiment 008 — Living observation ledger

Status: COMPLETED (six responses issued). Date: 2026-11-03. Updated on explicit request; no background monitoring.

## Fixed boundaries
- Six prompt-response cycles: round 1 control; rounds 2–6 context-continuity intervention.
- Single intended change: track established decisions and experiment progress without unnecessary reminders.
- Observe accuracy/usefulness; corrective prompts/rework; response completion/stability; resource use/estimated cost; time to visible response; context retention/experiment tracking.
- Interrupt upon first observed serious failure. Distinguish direct conversation evidence, user reports, and estimates.

## Per-pair observational dataset
Times below are message timestamps from the group thread (UTC), not measured model execution time, time-to-first-token, or user-side display latency. Seconds are simple differences between user and assistant message timestamps. These may include orchestration and tool time.

| Round | Condition | User message UTC | Assistant message UTC | Message gap (s) | Observable work | Limitations |
| --- | --- | --- | --- | ---: | --- | --- |
| 1 | Control | 21:59:50 | 22:00:01 | 11 | Control issued; six-round boundary distinguished from Experiment 007 | No token, compute, rendering or cost telemetry |
| 2 | Intervention | 22:34:38 | 22:34:47 | 9 | Resumed after long gap; boundaries retained | No causal attribution |
| 3 | Intervention | 22:35:26 | 22:35:47 | 21 | GitHub living ledger created on request | GitHub operation included in elapsed gap |
| 4 | Intervention | 22:45:25 | 22:45:47 | 22 | Ledger updated; Pally invitation issue tracked separately | GitHub operation included in elapsed gap |
| 5 | Intervention | 22:48:57 | 22:49:06 | 9 | Pally side issue linked to continuity observation | No user-side latency measurement |
| 6 | Intervention | 22:49:55 | 22:50:19 | 24 | Ledger updated; experiment closed | GitHub operation included in elapsed gap |

## Descriptive statistics for message gaps (not latency)
- All six: n=6, sum=96 s, mean=16.0 s, median=16.0 s, range=9–24 s.
- Control: n=1, 11 s.
- Intervention: n=5, gaps 9, 21, 22, 9, 24 s; mean=17.0 s; median=21 s; sample standard deviation approximately 7.45 s.
- Difference of intervention mean minus control gap = +6 s; NOT an effect estimate. Prompts and tool activity differ, and there is only one control observation.
- Token counts, inference compute, tool execution costs, monetary charges, and time-to-visible-response: **unavailable**, not zero. No cost-per-pair estimate can be responsibly derived from message gaps alone.
- GitHub writes are observable in rounds 3, 4, and 6, but cannot be priced from this record.

## Final evaluation
- Context continuity: Experiment ID, six-round bound, control/intervention distinction, and Pally's unresolved invitation issue retained across topic changes; descriptive success, not demonstrated causal improvement.
- Accuracy/usefulness: No clear boundary misinterpretation identified; usefulness not independently scored.
- Corrective prompts/rework: No corrections unambiguously attributable to Experiment 008 identified; no defensible reduction estimate.
- Response completion/stability: Six assistant messages present in the thread; actual user-side delivery and platform stability unverified. No serious failure reported in the six rounds.
- Resource consumption/cost: No actual token, compute, or monetary telemetry. Message gaps are not resource-use measurements.
- Time to visible response: Not measured. Message timestamps are not user-render timestamps.
- Causal limits: One unmatched control versus five interventions, variable prompt complexity, and GitHub actions in some rounds make regression, moving averages, and t-tests on this sample exploratory at best and not valid evidence of intervention effects.

## Decision and follow-on
Experiment 008 closed at round 6. Continuity demonstrated descriptively; comparative improvement and cost efficiency inconclusive. A proposed Experiment 009 protocol is documented separately but **not initiated**. No automatic extension.

## Separate unresolved issue
Pally reported repeated GitHub invitation errors even after a replacement invitation. Repository visibility and invitation status are not independently verified; this is not established as an assistant-response failure.
