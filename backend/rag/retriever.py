from __future__ import annotations

import logging
from dataclasses import dataclass
from uuid import UUID

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from backend.rag.embedder import embed_query


logger = logging.getLogger(__name__)
MIN_SIMILARITY_SCORE = 0.70


@dataclass(slots=True)
class RetrievalQuery:
    query_text: str
    skill_id: str
    phase: str | None
    technique_id: str | None
    doc_type_filter: list[str] | None
    top_k: int


@dataclass(slots=True)
class RetrievedChunk:
    chunk_id: UUID
    skill_id: str
    phase: str | None
    technique_id: str | None
    doc_type: str
    content: str
    similarity_score: float


def _to_pgvector_param(vector: list[float]) -> str:
    return "[" + ",".join(str(value) for value in vector) + "]"


async def retrieve(db: AsyncSession, query: RetrievalQuery) -> list[RetrievedChunk]:
    query_vector = await embed_query(query.query_text)
    sql_filters = ["skill_id = :skill_id"]
    params: dict[str, object] = {
        "skill_id": query.skill_id,
        "query_embedding": _to_pgvector_param(query_vector),
        "top_k": query.top_k,
    }

    if query.phase is not None:
        sql_filters.append("(phase = :phase OR phase IS NULL)")
        params["phase"] = query.phase

    if query.technique_id is not None:
        sql_filters.append("(technique_id = :technique_id OR technique_id IS NULL)")
        params["technique_id"] = query.technique_id

    if query.doc_type_filter:
        sql_filters.append("doc_type = ANY(:doc_type_filter)")
        params["doc_type_filter"] = query.doc_type_filter

    sql = text(
        "SELECT "
        "id, skill_id, phase, technique_id, doc_type, content, "
        "1 - (embedding <=> CAST(:query_embedding AS vector)) AS similarity_score "
        "FROM rag_chunks "
        f"WHERE {' AND '.join(sql_filters)} "
        "ORDER BY embedding <=> CAST(:query_embedding AS vector) "
        "LIMIT :top_k"
    )

    rows = (await db.execute(sql, params)).fetchall()

    chunks = [
        RetrievedChunk(
            chunk_id=row.id,
            skill_id=row.skill_id,
            phase=row.phase,
            technique_id=row.technique_id,
            doc_type=row.doc_type,
            content=row.content,
            similarity_score=float(row.similarity_score),
        )
        for row in rows
        if float(row.similarity_score) >= MIN_SIMILARITY_SCORE
    ]

    if len(chunks) < min(2, query.top_k):
        logger.warning(
            "Low quality retrieval results",
            extra={
                "skill_id": query.skill_id,
                "phase": query.phase,
                "technique_id": query.technique_id,
                "requested_top_k": query.top_k,
                "returned_count": len(chunks),
            },
        )

    return chunks
