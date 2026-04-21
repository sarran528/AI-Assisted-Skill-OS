from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.orchestration.orchestrator import transition_checkpoint
from backend.shared.db.models import Evidence, Session
from backend.validation.validators import validate_artifact, validate_behavioral_log, validate_numeric


async def validate_checkpoint(
    db_session: AsyncSession,
    session_id: UUID,
    checkpoint_id: str,
    checkpoint_status: str = "attempted",
    evidence_type: str = "artifact",
    numeric_actual: float | None = None,
    numeric_threshold: float = 0.7,
    steps_completed: list[str] | None = None,
    required_steps: list[str] | None = None,
    retry_count: int = 0,
    max_retries: int = 3,
) -> tuple[bool, str]:
    evidence_query = await db_session.execute(
        select(Evidence)
        .where(Evidence.session_id == session_id)
        .where(Evidence.checkpoint_id == checkpoint_id)
    )
    evidence_records = list(evidence_query.scalars().all())
    selected_type = evidence_type.lower().strip()
    if selected_type == "artifact" and not evidence_records:
        return False, "no_evidence_submitted"

    session_query = await db_session.execute(select(Session).where(Session.id == session_id))
    session_record = session_query.scalars().first()
    if session_record and session_record.status == "failed":
        return False, "session_failed"

    if selected_type == "numeric":
        if numeric_actual is None:
            return False, "numeric_actual_required"
        validation_result = validate_numeric(actual=float(numeric_actual), threshold=float(numeric_threshold))
    elif selected_type in {"behavioral", "behavioral_log", "log"}:
        validation_result = validate_behavioral_log(
            steps_completed=steps_completed or [],
            required_steps=required_steps or [],
            retry_count=retry_count,
            max_retries=max_retries,
        )
    else:
        validation_result = validate_artifact(has_artifact=len(evidence_records) > 0)

    target_status = "passed" if validation_result.passed else "failed"
    if not transition_checkpoint(checkpoint_status, target_status):
        return False, "invalid_checkpoint_status_transition"

    if not validation_result.passed:
        return False, validation_result.reason

    # Mark evidence rows as validated for this checkpoint.
    for record in evidence_records:
        record.validated = True
        record.validation_result = {
            "passed": validation_result.passed,
            "reason": validation_result.reason,
            "actual": validation_result.actual,
            "threshold": validation_result.threshold,
            "evidence_type": validation_result.evidence_type,
            "transition": {
                "from": checkpoint_status,
                "to": target_status,
            },
        }

    await db_session.commit()
    return True, "validated"
