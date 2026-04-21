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
    return target in transitions.get(current, [])
