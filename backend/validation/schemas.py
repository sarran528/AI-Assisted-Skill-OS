from backend.shared.models import APIModel


class CheckpointValidateRequest(APIModel):
    session_id: str
    checkpoint_id: str
    checkpoint_status: str = "attempted"
    evidence_type: str = "artifact"
    numeric_actual: float | None = None
    numeric_threshold: float = 0.7
    steps_completed: list[str] | None = None
    required_steps: list[str] | None = None
    retry_count: int = 0
    max_retries: int = 3


class CheckpointValidateResponse(APIModel):
    passed: bool
    reason: str
    session_id: str
    checkpoint_id: str
