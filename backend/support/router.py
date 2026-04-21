from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from backend.rag.query_builder import build_doubt_query, build_resource_query
from backend.rag.retriever import retrieve_chunks
from backend.shared.db.session import get_db_session
from backend.support.schemas import (
    DoubtAskRequest,
    DoubtAskResponse,
    SupportResourceItem,
    SupportResourcesResponse,
)

router = APIRouter()


def _fallback_answer(question: str) -> str:
    return (
        "Try isolating one sub-step and re-running with slower pacing. "
        f"If the issue persists, capture an artifact for: '{question[:80]}'."
    )


@router.post("/doubt/ask", response_model=DoubtAskResponse)
async def ask_doubt(
    payload: DoubtAskRequest,
    db_session: AsyncSession = Depends(get_db_session),
) -> DoubtAskResponse:
    try:
        query = build_doubt_query(
            skill_id=payload.skill_id,
            phase=payload.phase,
            technique_id=payload.technique_id,
            user_question=payload.question,
        )
        chunks = await retrieve_chunks(db_session, query)
    except Exception:
        chunks = []

    if not chunks:
        return DoubtAskResponse(
            answer=_fallback_answer(payload.question),
            confidence="medium",
            caveat="No grounded chunk found; using generic corrective guidance.",
            sources_used=0,
        )

    top = chunks[0]
    snippet = (top.get("content") or "").strip().replace("\n", " ")
    answer = (
        "Grounded hint: "
        f"{snippet[:220]}"
        " Focus on strict protocol order and record retry behavior before reattempt."
    )

    return DoubtAskResponse(
        answer=answer,
        confidence="high",
        caveat=None,
        sources_used=len(chunks),
    )


@router.get("/resources", response_model=SupportResourcesResponse)
async def get_resources(
    skill_id: str = Query(...),
    phase: str = Query(...),
    query: str | None = Query(None),
    db_session: AsyncSession = Depends(get_db_session),
) -> SupportResourcesResponse:
    try:
        retrieval_query = build_resource_query(skill_id=skill_id, phase=phase, user_query=query)
        chunks = await retrieve_chunks(db_session, retrieval_query)
    except Exception:
        chunks = []

    items = [
        SupportResourceItem(
            id=str(chunk.get("chunk_id")),
            doc_type=chunk.get("doc_type") or "guide",
            snippet=(chunk.get("content") or "")[:220],
            relevance=float(chunk.get("score") or 0.0),
        )
        for chunk in chunks
    ]

    if not items:
        items = [
            SupportResourceItem(
                id="fallback-1",
                doc_type="guide",
                snippet="No indexed chunks found. Retry with a narrower query or upload additional evidence.",
                relevance=0.0,
            )
        ]

    return SupportResourcesResponse(items=items)
