from __future__ import annotations

import logging
from dataclasses import dataclass
from uuid import UUID

from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.rag.context_builder import build_context_string
from backend.rag.query_builder import build_doubt_query
from backend.rag.retriever import retrieve
from backend.shared.audit import log_audit_event
from backend.shared.db.models import Roadmap, Session
from backend.shared.db.repositories.doubt_repository import DoubtLogCreate, DoubtRepository
from backend.shared.llm.prompts import build_doubt_prompt
from backend.shared.llm.schemas import DoubtAnswerSchema
from backend.shared.llm_gateway.client import llm_call


logger = logging.getLogger(__name__)
FALLBACK_DOUBT_ANSWER = DoubtAnswerSchema(
    answer="Unable to generate an explanation at this time. Please consult the provided resources.",
    source_phases=[],
    confidence="low",
    caveat="LLM unavailable",
)


@dataclass(slots=True)
class DoubtResponse:
    question: str
    answer: str
    confidence: str
    caveat: str | None
    chunks_used: int
    session_context: dict[str, str | None]


async def _get_session_context(
    db: AsyncSession,
    user_id: UUID,
    session_id: UUID | None,
) -> tuple[str, str | None, str | None, UUID | None]:
    session: Session | None = None

    if session_id is not None:
        session = await db.scalar(
            select(Session).where(Session.id == session_id, Session.user_id == user_id)
        )
    else:
        session = await db.scalar(
            select(Session)
            .where(Session.user_id == user_id)
            .order_by(desc(Session.created_at))
            .limit(1)
        )

    if session is None:
        roadmap = await db.scalar(
            select(Roadmap)
            .where(Roadmap.user_id == user_id)
            .order_by(desc(Roadmap.created_at))
            .limit(1)
        )
        if roadmap is None:
            return "general", None, None, None
        return roadmap.skill_id, None, None, None

    roadmap = await db.scalar(select(Roadmap).where(Roadmap.id == session.roadmap_id))
    skill_id = roadmap.skill_id if roadmap else "general"
    return skill_id, session.phase, session.technique_id, session.id


async def answer_doubt(
    db: AsyncSession,
    user_id: UUID,
    session_id: UUID | None,
    user_question: str,
    current_user: dict,
) -> DoubtResponse:
    del current_user

    skill_id, phase, technique_id, resolved_session_id = await _get_session_context(db, user_id, session_id)

    doubt_query = build_doubt_query(
        skill_id=skill_id,
        phase=phase,
        technique_id=technique_id,
        user_question=user_question,
    )
    chunks = await retrieve(db, doubt_query)
    context = build_context_string(chunks, max_tokens=2000)

    prompt = build_doubt_prompt(
        context=context,
        question=user_question,
        skill_id=skill_id,
        phase=phase,
        technique=technique_id,
    )

    try:
        llm_result = await llm_call(
            prompt=prompt,
            response_schema=DoubtAnswerSchema,
            temperature=0.2,
        )
    except Exception:
        logger.exception("Falling back to default doubt answer")
        llm_result = FALLBACK_DOUBT_ANSWER

    repo = DoubtRepository(db)
    await repo.create(
        DoubtLogCreate(
            user_id=user_id,
            session_id=resolved_session_id,
            skill_id=skill_id,
            phase=phase,
            question=user_question,
            answer=llm_result.answer,
            chunks_used=len(chunks),
            confidence=llm_result.confidence,
        )
    )

    await log_audit_event(
        db,
        user_id=str(user_id),
        action="doubt.submitted",
        entity_type="doubt",
        entity_id=None,
        ip_address=None,
        metadata={"chunks_used": len(chunks), "confidence": llm_result.confidence},
    )

    return DoubtResponse(
        question=user_question,
        answer=llm_result.answer,
        confidence=llm_result.confidence,
        caveat=llm_result.caveat,
        chunks_used=len(chunks),
        session_context={
            "skill_id": skill_id,
            "phase": phase,
            "technique": technique_id,
        },
    )
