from __future__ import annotations

from pydantic import BaseModel, Field

from backend.shared.llm.gateway import llm_call
from backend.validation.schemas import ValidationResult


class ArtifactValidationResponse(BaseModel):
    passed: bool
    confidence: float = Field(..., ge=0.0, le=1.0)
    reason: str


def _determine_metric(pass_criteria: str) -> tuple[str, str]:
    lowered = pass_criteria.lower()
    if "error" in lowered:
        return "error_count", "lte"
    if "time" in lowered or "within" in lowered:
        return "time_taken_seconds", "lte"
    return "accuracy_pct", "gte"


def validate_numeric(evidence_payload: dict, threshold: float, pass_criteria: str) -> ValidationResult:
    metric_name, direction = _determine_metric(pass_criteria)
    value = evidence_payload.get(metric_name)
    if value is None:
        return ValidationResult(
            passed=False,
            threshold=threshold,
            actual="missing",
            reason=f"missing metric: {metric_name}",
            evidence_type="numeric",
        )

    actual = float(value)
    passed = actual >= threshold if direction == "gte" else actual <= threshold
    return ValidationResult(
        passed=passed,
        threshold=threshold,
        actual=actual,
        reason="metric comparison",
        evidence_type="numeric",
    )


def validate_behavioral_log(evidence_payload: dict, required_steps: list[str]) -> ValidationResult:
    completed_steps = evidence_payload.get("steps_completed", [])
    retry_count = int(evidence_payload.get("retry_count", 0))
    max_retries = int(evidence_payload.get("retry_limit", 999))

    missing = [step for step in required_steps if step not in completed_steps]
    if missing:
        return ValidationResult(
            passed=False,
            threshold=float(len(required_steps)),
            actual=f"missing:{','.join(missing)}",
            reason="missing_required_steps",
            evidence_type="behavioral_log",
        )
    if retry_count > max_retries:
        return ValidationResult(
            passed=False,
            threshold=float(max_retries),
            actual=float(retry_count),
            reason="retry_limit_exceeded",
            evidence_type="behavioral_log",
        )

    return ValidationResult(
        passed=True,
        threshold=float(len(required_steps)),
        actual=float(len(completed_steps)),
        reason="behavioral_log_valid",
        evidence_type="behavioral_log",
    )


async def validate_artifact(
    evidence_payload: dict,
    artifact_url: str,
    checkpoint_description: str,
    pass_criteria: str,
) -> ValidationResult:
    del evidence_payload
    prompt = (
        "You are evaluating evidence for a learning checkpoint. "
        f"Checkpoint: {checkpoint_description}. "
        f"Pass criteria: {pass_criteria}. "
        f"Artifact URL: {artifact_url}. "
        "Return ONLY JSON with shape: {\"passed\": bool, \"confidence\": float, \"reason\": str}."
    )
    fallback = ArtifactValidationResponse(
        passed=False,
        confidence=0.0,
        reason="validation_unavailable",
    )

    result = await llm_call(
        prompt=prompt,
        system_prompt=(
            "You are a strict checkpoint validator. "
            "Respond only in valid JSON that matches the response schema."
        ),
        response_schema=ArtifactValidationResponse,
        fallback=fallback,
        temperature=0.0,
    )
    return ValidationResult(
        passed=bool(result.passed),
        threshold=None,
        actual=result.confidence,
        reason=result.reason,
        evidence_type="artifact",
    )
