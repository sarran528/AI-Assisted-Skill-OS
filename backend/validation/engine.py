from __future__ import annotations

from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from backend.assessment.schemas import LearningParameters
from backend.shared.db.repositories.evidence_repository import EvidenceRepository
from backend.validation.schemas import ValidationResult
from backend.validation.validators import (
    validate_artifact,
    validate_behavioral_log,
    validate_numeric,
)


async def validate_checkpoint(
    db: AsyncSession,
    session_id: UUID,
    checkpoint_id: str,
    params: LearningParameters,
    checkpoint_definition: dict,
) -> ValidationResult:
    evidence_records = await EvidenceRepository.get_by_checkpoint(db, session_id, checkpoint_id)
    if not evidence_records:
        return ValidationResult(
            passed=False,
            threshold=None,
            actual=None,
            reason="no_evidence_submitted",
            evidence_type=checkpoint_definition.get("evidence_type", "unknown"),
        )

    results: list[ValidationResult] = []
    for evidence in evidence_records:
        evidence_payload = dict(evidence.payload or {})
        if evidence.type == "numeric":
            result = validate_numeric(
                evidence_payload,
                threshold=float(checkpoint_definition.get("threshold", 0.0)),
                pass_criteria=checkpoint_definition.get("pass_criteria", ""),
            )
        elif evidence.type == "artifact":
            result = await validate_artifact(
                evidence_payload,
                artifact_url=evidence.artifact_url or "",
                checkpoint_description=checkpoint_definition.get("description", ""),
                pass_criteria=checkpoint_definition.get("pass_criteria", ""),
            )
        else:
            evidence_payload["retry_limit"] = int(params.retry_limit)
            result = validate_behavioral_log(
                evidence_payload,
                required_steps=checkpoint_definition.get("required_steps", []),
            )

        await EvidenceRepository.mark_validated(db, evidence.id, result.to_dict())
        results.append(result)

    if any(not item.passed for item in results):
        first_failure = next(item for item in results if not item.passed)
        return ValidationResult(
            passed=False,
            threshold=first_failure.threshold,
            actual=first_failure.actual,
            reason=first_failure.reason,
            evidence_type=first_failure.evidence_type,
        )

    first = results[0]
    return ValidationResult(
        passed=True,
        threshold=first.threshold,
        actual=first.actual,
        reason="all_evidence_passed",
        evidence_type=first.evidence_type,
    )
