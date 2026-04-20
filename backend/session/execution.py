from __future__ import annotations

from dataclasses import dataclass

from backend.assessment.schemas import LearningParameters
from backend.shared.db.models import LearningParameter, Session


@dataclass(slots=True)
class SessionResult:
    passed: bool
    failure_reason: str | None


@dataclass(slots=True)
class SessionMetrics:
    accuracy_pct: float
    time_taken_seconds: float
    error_count: int
    step_completion_rate: float
    retry_count: int
    raw_signals: dict


def validate_protocol_adherence(completed_steps: list[str], expected_steps: list[str]) -> tuple[bool, list[str]]:
    missing: list[str] = []
    for idx, expected in enumerate(expected_steps):
        if idx >= len(completed_steps):
            missing.extend(expected_steps[idx:])
            break
        if completed_steps[idx] != expected:
            missing.append(expected)
            break
    return (len(missing) == 0, missing)


def compute_session_result(
    metrics: SessionMetrics,
    params: LearningParameters,
    adherence_ok: bool,
) -> SessionResult:
    if not adherence_ok:
        return SessionResult(passed=False, failure_reason="protocol_violation")

    if metrics.accuracy_pct < float(params.error_tolerance_threshold):
        return SessionResult(passed=False, failure_reason="metric_threshold")

    if metrics.retry_count > int(params.retry_limit):
        return SessionResult(passed=False, failure_reason="metric_threshold")

    if metrics.step_completion_rate < 1.0:
        return SessionResult(passed=False, failure_reason="incomplete_execution")

    return SessionResult(passed=True, failure_reason=None)


def should_generate_tip(
    result: SessionResult,
    session: Session,
    params: LearningParameter,
) -> bool:
    if result.passed:
        return False

    if int(getattr(session, "attempt_number", 1)) >= 2:
        return True

    metrics = session.metrics_captured or {}
    retry_count = int(metrics.get("retry_count", 0) or 0)
    if retry_count > int(params.retry_limit):
        return True

    performance_decay = float(metrics.get("performance_decay", 0) or 0)
    if performance_decay > 0.5:
        return True

    return False
