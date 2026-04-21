from dataclasses import dataclass


@dataclass
class ValidationResult:
    passed: bool
    threshold: float
    actual: float | str
    reason: str
    evidence_type: str


def validate_numeric(actual: float, threshold: float, evidence_type: str = "numeric") -> ValidationResult:
    return ValidationResult(
        passed=actual >= threshold,
        threshold=threshold,
        actual=actual,
        reason="metric comparison",
        evidence_type=evidence_type,
    )


def validate_behavioral_log(steps_completed: list[str], required_steps: list[str], retry_count: int, max_retries: int) -> ValidationResult:
    has_steps = all(step in steps_completed for step in required_steps)
    retry_ok = retry_count <= max_retries
    passed = has_steps and retry_ok
    return ValidationResult(
        passed=passed,
        threshold=float(max_retries),
        actual=f"steps={len(steps_completed)},retry={retry_count}",
        reason="behavioral-log" if passed else "missing_steps_or_retry_exceeded",
        evidence_type="behavioral_log",
    )


def validate_artifact(has_artifact: bool) -> ValidationResult:
    return ValidationResult(
        passed=has_artifact,
        threshold=1.0,
        actual="present" if has_artifact else "missing",
        reason="artifact-check" if has_artifact else "no_artifact",
        evidence_type="artifact",
    )
