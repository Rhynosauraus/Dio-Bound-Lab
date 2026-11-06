"""
PS5 AI Experiment — synthetic Observe -> Propose -> Review -> Record model v0.3
Date: 2026-11-06 (America/Boise). SOURCE ONLY. NEVER EXECUTED.

This is not PS5 code, a console connection, a jailbreak, a human-authentication
service, an action dispatcher, or a durable custody log. It uses *only* invented
mock-menu records. Nothing in this module can operate any external device.

Every output has external_action_permitted=False, approval_authenticated=False,
durable_commit_proven=False, and custody_gap=True. Even a modeled "APPROVE"
is only an unverified assertion supplied to this pure function. v0.3 adds
caller-owned causal replay, NOT cryptographic authenticity or rollback fencing.
"""

from __future__ import annotations

from dataclasses import dataclass, replace
from hashlib import sha256
import json
import re

ID = re.compile(r"[A-Za-z0-9._:-]{1,64}\Z", re.ASCII)
DIGEST = re.compile(r"[0-9a-f]{64}\Z", re.ASCII)
ACTIONS = frozenset(("MOVE_UP", "MOVE_DOWN", "BACK", "SELECT"))
EVENT_TYPES = frozenset((
    "OBSERVED", "PROPOSED", "REVIEW_APPROVE_CLAIM",
    "REVIEW_DENY_CLAIM", "REVIEW_STOP_CLAIM", "STOPPED", "REFUSED",
))
MAX_EVENTS = 64
MAX_FRAME_SEQUENCE = 1000000
_MISSING = object()


@dataclass(frozen=True)
class MockFrame:
    frame_id: str
    sequence: int
    kind: str
    title: str
    available_actions: tuple[str, ...]
    protected_content: bool


@dataclass(frozen=True)
class Proposal:
    proposal_id: str
    frame_sequence: int
    frame_digest: str
    action: str


@dataclass(frozen=True)
class HumanDecisionClaim:
    decision_id: str
    proposal_id: str
    frame_sequence: int
    frame_digest: str
    decision: str  # APPROVE, DENY, or STOP: not authenticated


@dataclass(frozen=True)
class MockEvent:
    number: int
    kind: str
    reference: str
    related_proposal: str
    frame_digest: str
    action: str = ""  # abstract proposal/review enum, never a dispatch
    frame_sequence: int = 0  # synthetic sequence for local causal replay
    available_actions: tuple[str, ...] = ()  # OBSERVED rows only


@dataclass(frozen=True)
class MockState:
    last_frame_sequence: int = 0
    frame_digest: str = ""
    available_actions: tuple[str, ...] = ()
    pending: Proposal | None = None
    stopped: bool = False
    events: tuple[MockEvent, ...] = ()
    local_capacity_halt: bool = False  # unrecorded 64-row refusal; not durable STOP


@dataclass(frozen=True)
class MockOutcome:
    state: object
    status: str
    recorded_in_model: bool
    external_action_permitted: bool = False
    approval_authenticated: bool = False
    durable_commit_proven: bool = False
    custody_gap: bool = True


def _own(value: object, field: str) -> object:
    """Reject missing exact-class instance fields; do not inherit defaults."""
    try:
        properties = object.__getattribute__(value, "__dict__")
        if type(properties) is not dict or field not in properties:
            return _MISSING
        return properties[field]
    except Exception:
        return _MISSING


def _id(value: object) -> bool:
    return type(value) is str and ID.fullmatch(value) is not None


def _digest(value: object) -> bool:
    return type(value) is str and DIGEST.fullmatch(value) is not None


def _positive_sequence(value: object) -> bool:
    return type(value) is int and 1 <= value <= MAX_FRAME_SEQUENCE


def _valid_proposal(proposal: object) -> bool:
    return (
        type(proposal) is Proposal
        and _id(_own(proposal, "proposal_id"))
        and _positive_sequence(_own(proposal, "frame_sequence"))
        and _digest(_own(proposal, "frame_digest"))
        and type(_own(proposal, "action")) is str
        and _own(proposal, "action") in ACTIONS
    )


def _valid_frame(frame: object) -> bool:
    if type(frame) is not MockFrame:
        return False
    frame_id = _own(frame, "frame_id")
    sequence = _own(frame, "sequence")
    kind = _own(frame, "kind")
    title = _own(frame, "title")
    options = _own(frame, "available_actions")
    protected = _own(frame, "protected_content")
    return (
        _id(frame_id)
        and _positive_sequence(sequence)
        and type(kind) is str and kind == "SYNTHETIC_MENU_ONLY"
        and type(title) is str and 1 <= len(title) <= 120
        and title.isascii() and "\n" not in title and "\r" not in title
        and type(options) is tuple and 1 <= len(options) <= len(ACTIONS)
        and all(type(x) is str and x in ACTIONS for x in options)
        and len(set(options)) == len(options)
        and type(protected) is bool
    )


def _valid_event(event: object, index: int) -> bool:
    if type(event) is not MockEvent:
        return False
    kind = _own(event, "kind")
    # A damaged exact-class row may carry arbitrary hostile objects.
    # Reject before any equality/membership operator can invoke them.
    if type(kind) is not str:
        return False
    related = _own(event, "related_proposal")
    digest = _own(event, "frame_digest")
    action = _own(event, "action")
    sequence = _own(event, "frame_sequence")
    options = _own(event, "available_actions")
    needs_action = kind == "PROPOSED" or kind in (
        "REVIEW_APPROVE_CLAIM", "REVIEW_DENY_CLAIM", "REVIEW_STOP_CLAIM",
    )
    return (
        type(_own(event, "number")) is int
        and _own(event, "number") == index
        and type(kind) is str and kind in EVENT_TYPES
        and _id(_own(event, "reference"))
        and type(related) is str and (related == "" or _id(related))
        and type(digest) is str and (digest == "" or _digest(digest))
        and type(action) is str
        and (action in ACTIONS if needs_action else action == "")
        and type(sequence) is int and 0 <= sequence <= MAX_FRAME_SEQUENCE
        and type(options) is tuple
        and (
            1 <= len(options) <= len(ACTIONS)
            and all(type(x) is str and x in ACTIONS for x in options)
            and len(set(options)) == len(options)
            if kind == "OBSERVED"
            else options == ()
        )
    )


def _replay_local_history(events: tuple[MockEvent, ...]) -> tuple | None:
    """Reconstruct causal state from caller-owned events, NOT authenticate it.

    Can detect contradictory local histories; coherent substitution or rollback
    requires an external monotonic authority, unavailable in this source model.
    """
    sequence, digest, options = 0, "", ()
    pending = None
    stopped = False
    proposal_ids = set()
    decision_ids = set()
    review_kinds = (
        "REVIEW_APPROVE_CLAIM", "REVIEW_DENY_CLAIM",
        "REVIEW_STOP_CLAIM",
    )
    for index, event in enumerate(events, 1):
        if not _valid_event(event, index):
            return None
        kind = event.kind
        if kind == "OBSERVED":
            if (
                stopped or event.related_proposal != ""
                or not _positive_sequence(event.frame_sequence)
                or event.frame_sequence <= sequence
                or not _digest(event.frame_digest)
            ):
                return None
            sequence = event.frame_sequence
            digest = event.frame_digest
            options = event.available_actions
            pending = None  # fresh screen invalidates old pending proposal
            continue

        if (
            event.frame_sequence != sequence
            or event.frame_digest != digest
            or event.available_actions != ()
        ):
            return None
        if kind == "REFUSED":
            if event.related_proposal != "":
                return None
            # A refused untrusted input changes no frame or proposal.
            continue
        if kind == "PROPOSED":
            if (
                stopped or sequence == 0 or pending is not None
                or event.related_proposal != ""
                or event.action not in options
                or event.reference in proposal_ids
            ):
                return None
            proposal_ids.add(event.reference)
            pending = Proposal(
                event.reference, sequence, digest, event.action,
            )
            continue
        if kind in review_kinds:
            if (
                stopped or pending is None
                or event.related_proposal != pending.proposal_id
                or event.action != pending.action
                or event.reference in decision_ids
            ):
                return None
            decision_ids.add(event.reference)
            pending = None
            if kind == "REVIEW_STOP_CLAIM":
                stopped = True
            continue
        if kind == "STOPPED":
            if (
                stopped or event.related_proposal != ""
                or event.reference != "SIMULATED_STOP"
            ):
                return None
            stopped = True
            pending = None
            continue
        return None
    return sequence, digest, options, pending, stopped


def _valid_state(state: object) -> bool:
    if type(state) is not MockState:
        return False
    sequence = _own(state, "last_frame_sequence")
    digest = _own(state, "frame_digest")
    options = _own(state, "available_actions")
    pending = _own(state, "pending")
    stopped = _own(state, "stopped")
    events = _own(state, "events")
    local_halt = _own(state, "local_capacity_halt")
    if (
        type(sequence) is not int
        or not 0 <= sequence <= MAX_FRAME_SEQUENCE
        or type(digest) is not str
        or type(options) is not tuple
        or not all(type(x) is str and x in ACTIONS for x in options)
        or len(set(options)) != len(options)
        or type(stopped) is not bool
        or type(local_halt) is not bool
        or type(events) is not tuple
        or len(events) > MAX_EVENTS
        or (pending is not None and not _valid_proposal(pending))
    ):
        return False
    replay = _replay_local_history(events)
    if replay is None:
        return False
    rseq, rdigest, roptions, rpending, rstopped = replay
    if (
        sequence != rseq or digest != rdigest or options != roptions
        or stopped != (rstopped or local_halt)
    ):
        return False
    if local_halt:
        # No recorded STOP: only this caller-returned state can deny
        # subsequent proposals. It can be rolled back by the caller.
        return len(events) == MAX_EVENTS and pending is None and stopped
    return pending == rpending


def _unproven(state: object) -> MockOutcome:
    # Cannot safely append into malformed or unowned evidence. Real ingress
    # custody and a physical STOP require an independent future authority.
    return MockOutcome(state, "EVIDENCE_GAP_STOP", False)


def _emit(
    state: MockState,
    kind: str,
    reference: str,
    status: str,
    *,
    related_proposal: str = "",
    action: str = "",
    updates: dict | None = None,
) -> MockOutcome:
    if len(state.events) >= MAX_EVENTS:
        # No new event can be claimed. Latch *only* the local synthetic
        # stopped flag to deny subsequent model proposals. The event
        # was NOT recorded, and this is NOT physical/independent STOP.
        local_halt = replace(
            state, stopped=True, pending=None, local_capacity_halt=True,
        )
        return MockOutcome(local_halt, "EVIDENCE_LIMIT_STOP", False)
    next_state = replace(state, **(updates or {}))
    row = MockEvent(
        number=len(state.events) + 1,
        kind=kind,
        reference=reference,
        related_proposal=related_proposal,
        frame_digest=next_state.frame_digest,
        action=action,
        frame_sequence=next_state.last_frame_sequence,
        available_actions=(
            next_state.available_actions if kind == "OBSERVED" else ()
        ),
    )
    next_state = replace(next_state, events=state.events + (row,))
    return MockOutcome(next_state, status, True)


def _refuse(state: MockState, status: str) -> MockOutcome:
    return _emit(state, "REFUSED", status, status)


def _frame_digest(frame: MockFrame) -> str:
    # Hash *structured synthetic source*, not a real image/stream.
    payload = [
        frame.frame_id, frame.sequence, frame.kind,
        frame.title, list(frame.available_actions), frame.protected_content,
    ]
    return sha256(
        json.dumps(payload, ensure_ascii=True, separators=(",", ":")).encode("ascii")
    ).hexdigest()


def observe_mock_frame(state: object, frame: object) -> MockOutcome:
    if not _valid_state(state):
        return _unproven(state)
    if state.stopped:
        return _refuse(state, "REFUSED_STOPPED")
    if not _valid_frame(frame):
        return _refuse(state, "REFUSED_MALFORMED_FRAME")
    if frame.sequence <= state.last_frame_sequence:
        return _refuse(state, "REFUSED_STALE_FRAME")
    if frame.protected_content:
        return _refuse(state, "REFUSED_PROTECTED_CONTENT")
    return _emit(
        state, "OBSERVED", frame.frame_id, "MOCK_FRAME_OBSERVED",
        updates={
            "last_frame_sequence": frame.sequence,
            "frame_digest": _frame_digest(frame),
            "available_actions": frame.available_actions,
            "pending": None,  # a new frame invalidates an old proposal
        },
    )


def propose_mock_action(state: object, proposal: object) -> MockOutcome:
    if not _valid_state(state):
        return _unproven(state)
    if state.stopped:
        return _refuse(state, "REFUSED_STOPPED")
    if state.last_frame_sequence == 0:
        return _refuse(state, "REFUSED_NO_FRAME")
    if state.pending is not None:
        return _refuse(state, "REFUSED_PENDING_REVIEW")
    if not _valid_proposal(proposal):
        return _refuse(state, "REFUSED_MALFORMED_PROPOSAL")
    if (
        proposal.frame_sequence != state.last_frame_sequence
        or proposal.frame_digest != state.frame_digest
    ):
        return _refuse(state, "REFUSED_STALE_PROPOSAL")
    if proposal.action not in state.available_actions:
        return _refuse(state, "REFUSED_UNAVAILABLE_ACTION")
    if any(
        event.kind == "PROPOSED" and event.reference == proposal.proposal_id
        for event in state.events
    ):
        return _refuse(state, "REFUSED_DUPLICATE_PROPOSAL")
    # A candidate proposal is never an instruction to control a device.
    return _emit(
        state, "PROPOSED", proposal.proposal_id,
        "PROPOSAL_AWAITING_HUMAN",
        action=proposal.action,
        updates={"pending": proposal},
    )


def suggest_one_mock_action(state: object) -> MockOutcome:
    """Tiny deterministic teaching surrogate, explicitly NOT an AI model."""
    if not _valid_state(state):
        return _unproven(state)
    if state.stopped:
        return _refuse(state, "REFUSED_STOPPED")
    if state.last_frame_sequence == 0:
        return _refuse(state, "REFUSED_NO_FRAME")
    if state.pending is not None:
        return _refuse(state, "REFUSED_PENDING_REVIEW")
    proposal = Proposal(
        proposal_id=f"P-{state.last_frame_sequence}-{len(state.events) + 1}",
        frame_sequence=state.last_frame_sequence,
        frame_digest=state.frame_digest,
        action=state.available_actions[0],
    )
    return propose_mock_action(state, proposal)


def record_claimed_human_decision(
    state: object, claim: object
) -> MockOutcome:
    """Records a review CLAIM. Does NOT verify a human or release an action."""
    if not _valid_state(state):
        return _unproven(state)
    if state.stopped:
        return _refuse(state, "REFUSED_STOPPED")
    if type(claim) is not HumanDecisionClaim:
        return _refuse(state, "REFUSED_MALFORMED_REVIEW")
    fields = {
        name: _own(claim, name)
        for name in (
            "decision_id", "proposal_id", "frame_sequence",
            "frame_digest", "decision",
        )
    }
    if not (
        _id(fields["decision_id"])
        and _id(fields["proposal_id"])
        and _positive_sequence(fields["frame_sequence"])
        and _digest(fields["frame_digest"])
        and type(fields["decision"]) is str
        and fields["decision"] in ("APPROVE", "DENY", "STOP")
    ):
        return _refuse(state, "REFUSED_MALFORMED_REVIEW")
    if any(
        event.reference == fields["decision_id"]
        for event in state.events
        if event.kind in (
            "REVIEW_APPROVE_CLAIM", "REVIEW_DENY_CLAIM", "REVIEW_STOP_CLAIM",
        )
    ):
        return _refuse(state, "REFUSED_DUPLICATE_REVIEW")
    if state.pending is None:
        return _refuse(state, "REFUSED_NO_PENDING")
    if (
        fields["proposal_id"] != state.pending.proposal_id
        or fields["frame_sequence"] != state.last_frame_sequence
        or fields["frame_digest"] != state.frame_digest
    ):
        return _refuse(state, "REFUSED_REVIEW_BINDING")
    verdict = fields["decision"]
    return _emit(
        state, "REVIEW_" + verdict + "_CLAIM", fields["decision_id"],
        "SIMULATED_" + verdict + "_CLAIM_RECORDED",
        related_proposal=state.pending.proposal_id,
        action=state.pending.action,
        updates={"pending": None, "stopped": verdict == "STOP"},
    )


def simulated_stop(state: object) -> MockOutcome:
    """An in-memory STOP, not host/device termination or trusted fencing."""
    if not _valid_state(state):
        return _unproven(state)
    if state.stopped:
        return _refuse(state, "REFUSED_STOPPED")
    return _emit(
        state, "STOPPED", "SIMULATED_STOP", "SIMULATED_STOP_RECORDED",
        updates={"stopped": True, "pending": None},
    )


# No I/O, imports of production modules, network, file access, subprocess,
# runtime execution entrypoint, real credential handling, or device adapter.
