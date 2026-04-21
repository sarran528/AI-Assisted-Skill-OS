from backend.orchestration.orchestrator import transition_checkpoint
from backend.validation.validators import validate_artifact, validate_behavioral_log, validate_numeric


def test_validate_numeric_passes_threshold() -> None:
    result = validate_numeric(actual=0.82, threshold=0.7)
    assert result.passed is True
    assert result.reason == "metric comparison"


def test_validate_behavioral_log_detects_missing_steps() -> None:
    result = validate_behavioral_log(
        steps_completed=["1", "3"],
        required_steps=["1", "2", "3"],
        retry_count=1,
        max_retries=3,
    )
    assert result.passed is False
    assert result.reason == "missing_steps_or_retry_exceeded"


def test_validate_artifact_requires_presence() -> None:
    result = validate_artifact(has_artifact=False)
    assert result.passed is False
    assert result.reason == "no_artifact"


def test_checkpoint_transition_attempted_to_passed_allowed() -> None:
    assert transition_checkpoint("attempted", "passed") is True
    assert transition_checkpoint("pending", "passed") is False
