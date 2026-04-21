from backend.orchestration.orchestrator import transition_session
from backend.session.execution import (
    SessionMetrics,
    compute_quality_score,
    compute_session_result,
    validate_protocol_adherence,
)


def test_validate_protocol_adherence_requires_order() -> None:
    ok, missing = validate_protocol_adherence(["1", "2", "3", "4"], ["1", "2", "3", "4"])
    assert ok is True
    assert missing == []


def test_validate_protocol_adherence_detects_missing() -> None:
    ok, missing = validate_protocol_adherence(["1", "3"], ["1", "2", "3", "4"])
    assert ok is False
    assert missing == ["2", "4"]


def test_compute_session_result_fails_when_accuracy_below_threshold() -> None:
    metrics = SessionMetrics(
        accuracy_pct=0.5,
        time_taken_seconds=120.0,
        error_count=1,
        step_completion_rate=1.0,
        retry_count=0,
        raw_signals={},
    )
    result = compute_session_result(metrics=metrics, error_tolerance_threshold=0.7, adherence_ok=True)
    assert result.passed is False
    assert result.failure_reason == "metric_threshold"


def test_transition_session_allows_only_valid_edges() -> None:
    assert transition_session("active", "completed") is True
    assert transition_session("active", "failed") is True
    assert transition_session("pending", "completed") is False


def test_compute_quality_score_is_bounded() -> None:
    metrics = SessionMetrics(
        accuracy_pct=1.5,
        time_taken_seconds=50.0,
        error_count=0,
        step_completion_rate=1.2,
        retry_count=0,
        raw_signals={},
    )
    assert compute_quality_score(metrics) == 1.0


def test_compute_session_result_fails_when_retry_limit_exceeded() -> None:
    metrics = SessionMetrics(
        accuracy_pct=0.95,
        time_taken_seconds=180.0,
        error_count=0,
        step_completion_rate=1.0,
        retry_count=6,
        raw_signals={},
    )
    result = compute_session_result(metrics=metrics, error_tolerance_threshold=0.7, adherence_ok=True)
    assert result.passed is False
    assert result.failure_reason == "retry_limit_exceeded"
