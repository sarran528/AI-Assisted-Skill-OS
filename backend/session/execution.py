from dataclasses import dataclass


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


def _bounded_score(value: float, floor: float = 0.0, ceiling: float = 1.0) -> float:
    return max(floor, min(value, ceiling))


def compute_quality_score(metrics: SessionMetrics) -> float:
    accuracy = 1.0 if metrics.accuracy_pct is None else _bounded_score(metrics.accuracy_pct)
    completion = _bounded_score(metrics.step_completion_rate)

    error_penalty = 0.0
    if metrics.error_count is not None:
        error_penalty = min(metrics.error_count * 0.1, 0.4)

    retry_penalty = min(metrics.retry_count * 0.05, 0.25)
    score = (accuracy * 0.55) + (completion * 0.45) - error_penalty - retry_penalty
    return _bounded_score(score)


def validate_protocol_adherence(completed_steps: list[str], required_steps: list[str]) -> tuple[bool, list[str]]:
    if not required_steps:
        return True, []

    missing: list[str] = []
    cursor = 0
    for required in required_steps:
        if cursor >= len(completed_steps) or completed_steps[cursor] != required:
            missing.append(required)
        else:
            cursor += 1

    return len(missing) == 0, missing


def compute_session_result(metrics: SessionMetrics, error_tolerance_threshold: float, adherence_ok: bool) -> SessionResult:
    if not adherence_ok:
        details = {**metrics.raw_signals, "quality_score": compute_quality_score(metrics)}
        return SessionResult(False, "protocol_violation", details)

    if metrics.retry_count > 5:
        details = {**metrics.raw_signals, "quality_score": compute_quality_score(metrics)}
        return SessionResult(False, "retry_limit_exceeded", details)

    if metrics.accuracy_pct is not None and metrics.accuracy_pct < error_tolerance_threshold:
        details = {**metrics.raw_signals, "quality_score": compute_quality_score(metrics)}
        return SessionResult(False, "metric_threshold", details)

    if metrics.step_completion_rate < 1.0:
        details = {**metrics.raw_signals, "quality_score": compute_quality_score(metrics)}
        return SessionResult(False, "incomplete_execution", details)

    details = {**metrics.raw_signals, "quality_score": compute_quality_score(metrics)}
    return SessionResult(True, None, details)
