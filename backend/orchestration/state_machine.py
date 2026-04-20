from __future__ import annotations

from backend.shared.errors import BusinessError

SESSION_TRANSITIONS = {
    "pending": ["active"],
    "active": ["completed", "failed"],
    "completed": [],
    "failed": [],
}

CHECKPOINT_TRANSITIONS = {
    "pending": ["attempted"],
    "attempted": ["passed", "failed"],
    "passed": [],
    "failed": ["attempted"],
}

ROADMAP_PHASE_TRANSITIONS = {
    "locked": ["active"],
    "active": ["completed"],
    "completed": [],
}


def validate_transition(current: str, target: str, transitions: dict[str, list[str]]) -> bool:
    if target not in transitions.get(current, []):
        raise BusinessError(
            "invalid_state_transition",
            f"Invalid state transition from '{current}' to '{target}'",
            {"current": current, "target": target},
        )
    return True
