from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from backend.rag.context_builder import build_context_string
from backend.rag.query_builder import build_tip_query
from backend.rag.retriever import retrieve
from backend.shared.audit import log_audit_event
from backend.shared.db.models import LearningParameter
from backend.shared.db.repositories.tip_repository import TipLogCreate, TipRepository
from backend.shared.llm.prompts import build_tip_prompt
from backend.shared.llm.schemas import TipSchema
from backend.shared.llm.gateway import llm_call


logger = logging.getLogger(__name__)
FALLBACK_TIP = TipSchema(
    tip="Focus on completing each step in the protocol before moving to the next. Do not skip steps.",
    target_step=None,
    severity="moderate",
)


@dataclass(slots=True)
class TipResponse:
    session_id: UUID
    technique_id: str
    tip: str
    severity: str
    target_step: str | None
    failure_type: str
    generated_at: datetime


def map_failure_type(failure_reason: str, session_metrics: dict) -> str:
    performance_decay = float(session_metrics.get("performance_decay", 0.0) or 0.0)
    if performance_decay > 0.5:
        return "performance_degradation"

    if failure_reason == "protocol_violation":
        step_id = str(session_metrics.get("failed_step") or "unknown")
        return f"step_{step_id}_skipped"

    if failure_reason == "metric_threshold":
        accuracy = float(session_metrics.get("accuracy", 1.0) or 1.0)
        if accuracy < 0.7:
            return "accuracy_below_threshold"
        return "excessive_errors"

    if failure_reason == "incomplete_execution":
        return "session_not_completed"

    return failure_reason or "unknown_failure"


async def generate_tip(
    db: AsyncSession,
    session_id: UUID,
    user_id: UUID,
    skill_id: str,
    technique_id: str,
    failure_reason: str,
    session_metrics: dict,
    params: LearningParameter,
    attempt_number: int,
) -> TipResponse:
    del params

    failure_type = map_failure_type(failure_reason, session_metrics)
    tip_query = build_tip_query(skill_id, technique_id, failure_type)
    chunks = await retrieve(db, tip_query)
    context = build_context_string(chunks, max_tokens=1200)

    prompt = build_tip_prompt(
        context=context,
        technique_id=technique_id,
        failure_type=failure_type,
        attempt_number=attempt_number,
    )

    try:
        llm_result = await llm_call(
            prompt=prompt,
            system_prompt="You are an expert tutor. Provide a constructive tip based on the failure.",
            response_schema=TipSchema,
            fallback=FALLBACK_TIP,
            temperature=0.0,
        )
    except Exception:
        logger.exception("Falling back to default tip")
        llm_result = FALLBACK_TIP

    repository = TipRepository(db)
    await repository.create(
        TipLogCreate(
            session_id=session_id,
            user_id=user_id,
            technique_id=technique_id,
            failure_type=failure_type,
            attempt_number=attempt_number,
            tip=llm_result.tip,
            severity=llm_result.severity,
            target_step=llm_result.target_step,
            chunks_used=len(chunks),
        )
    )

    await log_audit_event(
        db,
        user_id=str(user_id),
        action="tip.generated",
        entity_type="session",
        entity_id=str(session_id),
        ip_address=None,
        metadata={"failure_type": failure_type, "severity": llm_result.severity},
    )

    return TipResponse(
        session_id=session_id,
        technique_id=technique_id,
        tip=llm_result.tip,
        severity=llm_result.severity,
        target_step=llm_result.target_step,
        failure_type=failure_type,
        generated_at=datetime.now(timezone.utc),
    )
