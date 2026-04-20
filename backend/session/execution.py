from __future__ import annotations

from dataclasses import dataclass

from backend.assessment.schemas import LearningParameters


@dataclass
class SessionMetrics:
    accuracy_pct: float | None
    time_taken_seconds: float | None
    error_count: int | None
    step_completion_rate: float
    retry_count: int
    raw_signals: dict


@dataclass
class SessionResult:
    passed: bool
    failure_reason: str | None
    metric_details: dict


def validate_protocol_adherence(
    completed_steps: list[str], required_steps: list[str]
) -> tuple[bool, list[str]]:
    if not required_steps:
        return True, []

    compared_count = min(len(completed_steps), len(required_steps))
    for idx in range(compared_count):
        if completed_steps[idx] != required_steps[idx]:
            return False, [required_steps[idx]]

    if len(completed_steps) < len(required_steps):
        return False, [required_steps[len(completed_steps)]]

    return True, []


def compute_session_result(
    metrics: SessionMetrics,
    params: LearningParameters,
    adherence_ok: bool,
) -> SessionResult:
    if not adherence_ok:
        return SessionResult(
            passed=False,
            failure_reason="protocol_violation",
            metric_details={"step_completion_rate": metrics.step_completion_rate},
        )

    if (
        metrics.accuracy_pct is not None
        and metrics.accuracy_pct < float(params.error_tolerance_threshold)
    ):
        return SessionResult(
            passed=False,
            failure_reason="metric_threshold",
            metric_details={
                "accuracy_pct": metrics.accuracy_pct,
                "threshold": float(params.error_tolerance_threshold),
            },
        )

    if metrics.step_completion_rate < 1.0:
        return SessionResult(
            passed=False,
            failure_reason="incomplete_execution",
            metric_details={"step_completion_rate": metrics.step_completion_rate},
        )

    return SessionResult(
        passed=True,
        failure_reason=None,
        metric_details={
            "accuracy_pct": metrics.accuracy_pct,
            "retry_count": metrics.retry_count,
            "step_completion_rate": metrics.step_completion_rate,
        },
    )
