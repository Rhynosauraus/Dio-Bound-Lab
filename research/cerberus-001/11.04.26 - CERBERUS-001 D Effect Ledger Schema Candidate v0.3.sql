-- CERBERUS-001 — D effect ledger schema candidate v0.3
-- November 4, 2026 (America/Boise)
-- SOURCE ONLY. NOT EXECUTED, NOT MIGRATED, NOT REVIEWED.
-- NO REAL DATABASE OR AUTHORITY STORE EXISTS BECAUSE OF THIS FILE.
--
-- Design intent: preserve all D-observed ATTEMPT records without deduplication;
-- enforce UNIQUE reservation AND UNIQUE action effect claims. D-owned stop,
-- grant and generation fences must serialize with effect commitment.
-- This schema by itself DOES NOT prove transaction isolation, storage
-- durability, external custody, signature verification or effect-time
-- revocation. A real implementation must pin the SQLite version/filesystem
-- and show the exact transaction code and power-loss/restart behavior.
--
-- Required future transaction shape (pseudocode, NOT executed):
--   1. Off-DB verify exact signed A0 token, D-owned context and authenticated
--      A0 commitment evidence; independently witness inbound D request.
--   2. BEGIN IMMEDIATE; check D local fences and existing claim uniqueness.
--   3. Allocate D event sequences; INSERT ATTEMPT (even on denial).
--   4. For a new allowed effect only: INSERT EFFECT under both UNIQUE keys,
--      update D counter in the SAME transaction, attach historical receipt.
--   5. COMMIT. On lost ACK, read existing receipt, never re-execute.
--   6. D fence operations use same writer/serialization boundary.
-- No alternate raw v0.1/v0.2 effect entrypoint may be exposed.
-- Unexpected constraint violation: rollback and record an independently
-- reconciled attempt/denial; never count a second effect as a PASS.
--
-- Note: the schema is illustrative and not a migration. Its D event sequence
-- requires a single transactional allocator, not an unsynchronized clock.

PRAGMA foreign_keys = ON;

CREATE TABLE d_head (
    singleton INTEGER PRIMARY KEY CHECK (singleton = 1),
    last_sequence INTEGER NOT NULL CHECK (last_sequence >= 0),
    effect_counter INTEGER NOT NULL CHECK (effect_counter >= 0),
    run_epoch INTEGER NOT NULL CHECK (run_epoch >= 0)
);

CREATE TABLE d_events (
    sequence INTEGER PRIMARY KEY CHECK (sequence > 0),
    kind TEXT NOT NULL CHECK (
        kind IN (
            'ATTEMPT', 'EFFECT', 'GENERATION_FENCE',
            'GRANT_FENCE', 'RUN_STOP'
        )
    ),
    raw_record_sha256 TEXT NOT NULL CHECK (length(raw_record_sha256) = 64)
);

CREATE TABLE d_attempts (
    event_sequence INTEGER PRIMARY KEY REFERENCES d_events(sequence),
    token_sha256 TEXT NOT NULL CHECK (length(token_sha256) = 64),
    status TEXT NOT NULL,
    committed_now INTEGER NOT NULL CHECK (committed_now IN (0, 1)),
    prior_effect_sequence INTEGER REFERENCES d_events(sequence)
);
-- Deliberately NO uniqueness constraint on token digest or reservation ID
-- in d_attempts: the second attempted dispatch MUST remain observable.

CREATE TABLE d_effects (
    event_sequence INTEGER PRIMARY KEY REFERENCES d_events(sequence),
    attempt_sequence INTEGER NOT NULL UNIQUE REFERENCES d_attempts(event_sequence),
    root_id TEXT NOT NULL,
    run_id TEXT NOT NULL,
    episode_id TEXT NOT NULL,
    action_id TEXT NOT NULL,
    grant_id TEXT NOT NULL,
    generation INTEGER NOT NULL CHECK (generation > 0),
    reservation_id TEXT NOT NULL,
    token_sha256 TEXT NOT NULL CHECK (length(token_sha256) = 64),
    counter_after INTEGER NOT NULL UNIQUE CHECK (counter_after > 0),
    UNIQUE (reservation_id),
    UNIQUE (root_id, run_id, episode_id, action_id)
);
-- Together these UNIQUE constraints are the proposed D one-use effect claim.
-- Both must be checked/inserted under the same D transaction as the effect.

CREATE TABLE d_generation_fences (
    generation INTEGER PRIMARY KEY CHECK (generation > 0),
    proposal_digest TEXT NOT NULL CHECK (length(proposal_digest) = 64),
    event_sequence INTEGER NOT NULL UNIQUE REFERENCES d_events(sequence)
);

CREATE TABLE d_grant_fences (
    root_id TEXT NOT NULL,
    run_id TEXT NOT NULL,
    grant_id TEXT NOT NULL,
    event_sequence INTEGER NOT NULL UNIQUE REFERENCES d_events(sequence),
    PRIMARY KEY (root_id, run_id, grant_id)
);

CREATE TABLE d_run_stops (
    run_id TEXT PRIMARY KEY,
    event_sequence INTEGER NOT NULL UNIQUE REFERENCES d_events(sequence)
);

-- M10 baseline v0.2 remains historical: two dispatches produced two synthetic
-- effects. v0.3 proposes TWO ATTEMPTS but ONE EFFECT: explicit source-semantic
-- change subject to separate D1 independent adjudication, not a retroactive
-- result. An external ingress tap/custodian must independently corroborate
-- requests that D never recorded.
--
-- No stored credentials, live keys, public endpoint, connection string,
-- DROP/DELETE/UPDATE migration or real device command appears in this file.
