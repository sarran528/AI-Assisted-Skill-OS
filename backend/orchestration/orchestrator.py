from backend.orchestration.state_machine import (
    CHECKPOINT_TRANSITIONS,
    ROADMAP_PHASE_TRANSITIONS,
    SESSION_TRANSITIONS,
    validate_transition,
)


def transition_session(current: str, target: str) -> bool:
    return validate_transition(current, target, SESSION_TRANSITIONS)


def transition_checkpoint(current: str, target: str) -> bool:
    return validate_transition(current, target, CHECKPOINT_TRANSITIONS)


def transition_roadmap_phase(current: str, target: str) -> bool:
    return validate_transition(current, target, ROADMAP_PHASE_TRANSITIONS)
