from __future__ import annotations

from enum import Enum
from typing import FrozenSet

from app.core.exceptions import InvalidStateTransitionError


class JobState(str, Enum):
    DRAFT = "DRAFT"
    VIDEO_UPLOADED = "VIDEO_UPLOADED"
    HOOK_GENERATING = "HOOK_GENERATING"
    HOOK_PENDING_APPROVAL = "HOOK_PENDING_APPROVAL"
    HOOK_REJECTED = "HOOK_REJECTED"
    HOOK_APPROVED = "HOOK_APPROVED"
    VIDEO_EDITING = "VIDEO_EDITING"
    VIDEO_READY = "VIDEO_READY"
    WAITING_FOR_SOCIAL_CONNECTION = "WAITING_FOR_SOCIAL_CONNECTION"
    DESTINATIONS_SELECTED = "DESTINATIONS_SELECTED"
    READY_TO_PUBLISH = "READY_TO_PUBLISH"
    SCHEDULED = "SCHEDULED"
    PUBLISHING = "PUBLISHING"
    PARTIALLY_PUBLISHED = "PARTIALLY_PUBLISHED"
    PUBLISHED = "PUBLISHED"
    FAILED = "FAILED"


# Maps each state to the set of states it is allowed to transition INTO.
VALID_TRANSITIONS: dict[JobState, FrozenSet[JobState]] = {
    JobState.DRAFT: frozenset({
        JobState.VIDEO_UPLOADED,
        JobState.FAILED,
    }),
    JobState.VIDEO_UPLOADED: frozenset({
        JobState.HOOK_GENERATING,
        JobState.FAILED,
    }),
    JobState.HOOK_GENERATING: frozenset({
        JobState.HOOK_PENDING_APPROVAL,
        JobState.FAILED,
    }),
    JobState.HOOK_PENDING_APPROVAL: frozenset({
        JobState.HOOK_APPROVED,
        JobState.HOOK_REJECTED,
        JobState.FAILED,
    }),
    JobState.HOOK_REJECTED: frozenset({
        # Allow re-triggering generation after rejection
        JobState.HOOK_GENERATING,
        JobState.HOOK_PENDING_APPROVAL,
        JobState.FAILED,
    }),
    JobState.HOOK_APPROVED: frozenset({
        JobState.VIDEO_EDITING,
        JobState.FAILED,
    }),
    JobState.VIDEO_EDITING: frozenset({
        JobState.VIDEO_READY,
        JobState.FAILED,
    }),
    JobState.VIDEO_READY: frozenset({
        JobState.WAITING_FOR_SOCIAL_CONNECTION,
        JobState.DESTINATIONS_SELECTED,
        JobState.FAILED,
    }),
    JobState.WAITING_FOR_SOCIAL_CONNECTION: frozenset({
        JobState.DESTINATIONS_SELECTED,
        JobState.FAILED,
    }),
    JobState.DESTINATIONS_SELECTED: frozenset({
        JobState.READY_TO_PUBLISH,
        JobState.FAILED,
    }),
    JobState.READY_TO_PUBLISH: frozenset({
        JobState.PUBLISHING,
        JobState.SCHEDULED,
        JobState.FAILED,
    }),
    JobState.SCHEDULED: frozenset({
        JobState.PUBLISHING,
        # Allow un-scheduling back to ready
        JobState.READY_TO_PUBLISH,
        JobState.FAILED,
    }),
    JobState.PUBLISHING: frozenset({
        JobState.PUBLISHED,
        JobState.PARTIALLY_PUBLISHED,
        JobState.FAILED,
    }),
    JobState.PARTIALLY_PUBLISHED: frozenset({
        # Allow retrying failed destinations
        JobState.PUBLISHING,
        JobState.PUBLISHED,
        JobState.FAILED,
    }),
    JobState.PUBLISHED: frozenset(),   # terminal success state
    JobState.FAILED: frozenset({
        # Allow manual recovery / retry from failure
        JobState.DRAFT,
        JobState.VIDEO_UPLOADED,
        JobState.HOOK_GENERATING,
        JobState.HOOK_PENDING_APPROVAL,
        JobState.HOOK_APPROVED,
        JobState.VIDEO_EDITING,
        JobState.VIDEO_READY,
        JobState.READY_TO_PUBLISH,
        JobState.PUBLISHING,
    }),
}


class ContentJobStateMachine:
    """Encapsulates state-transition logic for a ContentJob."""

    def __init__(self, current_state: JobState | str) -> None:
        self._state = JobState(current_state) if isinstance(current_state, str) else current_state

    @property
    def state(self) -> JobState:
        return self._state

    @property
    def allowed_transitions(self) -> FrozenSet[JobState]:
        return VALID_TRANSITIONS.get(self._state, frozenset())

    def can_transition_to(self, target: JobState | str) -> bool:
        target_state = JobState(target) if isinstance(target, str) else target
        return target_state in self.allowed_transitions

    def transition(self, target: JobState | str) -> JobState:
        """Perform transition to *target*; raises InvalidStateTransitionError on failure."""
        target_state = JobState(target) if isinstance(target, str) else target
        if not self.can_transition_to(target_state):
            raise InvalidStateTransitionError(
                current_state=self._state.value,
                target_state=target_state.value,
            )
        self._state = target_state
        return self._state

    def __repr__(self) -> str:
        return f"ContentJobStateMachine(state={self._state.value!r})"
