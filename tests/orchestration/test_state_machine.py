import pytest

from backend.orchestration.state_machine import (
    CHECKPOINT_TRANSITIONS,
    ROADMAP_PHASE_TRANSITIONS,
    SESSION_TRANSITIONS,
    validate_transition,
)


def test_valid_and_invalid_session_transitions():
    assert validate_transition("pending", "active", SESSION_TRANSITIONS)
    assert validate_transition("active", "completed", SESSION_TRANSITIONS)

    with pytest.raises(Exception):
        validate_transition("active", "pending", SESSION_TRANSITIONS)
    with pytest.raises(Exception):
        validate_transition("completed", "failed", SESSION_TRANSITIONS)


def test_checkpoint_retry_rule():
    assert validate_transition("failed", "attempted", CHECKPOINT_TRANSITIONS)
    with pytest.raises(Exception):
        validate_transition("passed", "attempted", CHECKPOINT_TRANSITIONS)


def test_phase_transitions():
    assert validate_transition("locked", "active", ROADMAP_PHASE_TRANSITIONS)
    assert validate_transition("active", "completed", ROADMAP_PHASE_TRANSITIONS)
