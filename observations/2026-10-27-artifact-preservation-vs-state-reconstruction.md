# Archived artifacts are not necessarily reconstructible experimental states

**Recorded:** 2026-10-27  
**Class:** Evidence-custody observation from reported TRIDENT examinations  
**Status:** PROVISIONAL; no new archive audit performed

## Distinction

A successful archive upload proves neither that every filesystem object was included nor that the original state can be reconstructed. Regular file bytes alone may omit symlink targets, hardlink relationships, special nodes, permissions, ownership, timestamps, and ordered mutation events.

## Reported basis

Prior TRIDENT examination discussions reported that packaging omitted some special filesystem objects. This record does not independently validate the archive or its omitted entries.

## Minimum custody pattern

Preserve a separately hashed reconstruction manifest listing object paths, types, link relationships, relevant metadata, creation commands, source/fixture hashes, and synchronization traces. Store stdout/stderr, process exit status, and failure reports separately. Never infer experimental completeness from a green artifact-upload indicator.

## Discriminating experiment

Construct a synthetic tree containing the relevant object classes; inventory it before packaging, extract it in a disposable environment, then compare a fresh inventory against the frozen manifest. Record each omission or altered property and whether the exact test state can be reconstructed.

**Claim ceiling:** A missing archive object is a custody/reproducibility concern; it is not by itself a defect in the scanner under examination.
