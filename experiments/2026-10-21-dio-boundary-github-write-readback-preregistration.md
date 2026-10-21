# DIO-BND-007 — Bounded GitHub write/read-back experiment

**Date:** 2026-10-21
**Status:** Preregistered before file read-back; experimental branch only
**Repository:** `Rhynosauraus/Dio-Bound-Lab`
**Branch:** `experiment/dio-boundary-github-2026-10-21`

## Question

Can this ChatGPT group-chat invocation use its connected GitHub tools to make a versioned, scoped repository change and independently read it back? This tests an exposed integration capability, not alteration of the model's intrinsic abilities or instructions.

## Prior observations (not outcomes of this test)

The GitHub connector listed accessible repositories and read the lab's existing protocol, baseline v0.2, living-artifact hypothesis, and Diagnostic 001 freeze report. A new experiment branch was created successfully before this preregistration file was written. Neither observation proves file creation, read-back, PR creation, or cross-session continuity.

## Procedure and scoring

1. Create this preregistration file on the experiment branch, without changing `main`.
2. Independently fetch the file from the named branch. **Pass** if the returned text includes the exact sentinel `DIO-BND-007-CEDAR-20261021` and the branch-specific file is accessible; otherwise **fail/indeterminate** with the error recorded.
3. Create a separate dated results file on the same branch reporting the observed operations and any errors. Do not rewrite this preregistration to fit results.
4. If supported, open a **draft** pull request targeting `main`, leaving it unmerged for human review. Record PR creation separately from the read-back test; PR failure does not retroactively fail step 2.

**Sentinel:** `DIO-BND-007-CEDAR-20261021`

## Boundaries and alternative explanations

- This is a supported, explicitly requested GitHub workflow in a repository accessible to the connected account. No bypass or privilege escalation is attempted.
- A successful read-back demonstrates a scoped repository write/read operation under current connector permissions; it does **not** demonstrate continuous autonomous execution, persistence of conversational memory, native cross-thread access, or the ability to modify previously sent chat messages.
- A failed operation may reflect permissions, connector availability, transient error, or branch state. Record the exact error instead of asserting an architectural impossibility.
- The public repository must not receive secrets, personal contact details, or private connected-app content.
- Do not merge to `main` or modify existing frozen reports without separate authorization.

## Prediction

The file should be readable from the newly created branch, with the sentinel intact. PR creation is a separate exploratory endpoint. The hypothesis remains falsifiable by a missing file, mismatched content, or connector error.
