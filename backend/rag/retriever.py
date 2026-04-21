from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.rag.query_builder import RetrievalQuery
from backend.shared.db.models.rag import RagChunk


def _tokenize(text: str) -> set[str]:
    return {token.strip().lower() for token in text.split() if token.strip()}


def lexical_score(query_text: str, content: str) -> float:
    query_tokens = _tokenize(query_text)
    if not query_tokens:
        return 0.0
    content_tokens = _tokenize(content)
    overlap = query_tokens.intersection(content_tokens)
    return len(overlap) / len(query_tokens)


def _bounded(value: float) -> float:
    return max(0.0, min(1.0, value))


async def retrieve_chunks(db_session: AsyncSession, query: RetrievalQuery) -> list[dict]:
    def apply_filters(stmt):
        stmt = stmt.where(RagChunk.skill_id == query.skill_id)
        if query.phase:
            stmt = stmt.where((RagChunk.phase == query.phase) | (RagChunk.phase.is_(None)))
        if query.technique_id:
            stmt = stmt.where((RagChunk.technique_id == query.technique_id) | (RagChunk.technique_id.is_(None)))
        return stmt

    fetch_limit = max(query.top_k * 5, 25)
    ranked_rows: list[tuple[RagChunk, float | None]] = []

    if query.query_embedding:
        try:
            distance_expr = RagChunk.embedding.cosine_distance(query.query_embedding).label("distance")
            stmt = apply_filters(select(RagChunk, distance_expr)).order_by(distance_expr.asc()).limit(fetch_limit)
            result = await db_session.execute(stmt)
            ranked_rows = [(row, distance) for row, distance in result.all()]
        except Exception:
            ranked_rows = []

    if not ranked_rows:
        fallback = await db_session.execute(apply_filters(select(RagChunk)).limit(fetch_limit))
        ranked_rows = [(row, None) for row in fallback.scalars().all()]

    scored: list[tuple[float, RagChunk]] = []
    for row, distance in ranked_rows:
        lexical = lexical_score(query.query_text, row.content)
        if distance is None:
            combined_score = lexical
        else:
            semantic = _bounded(1.0 - float(distance))
            combined_score = _bounded((semantic * 0.75) + (lexical * 0.25))
        scored.append((combined_score, row))

    scored.sort(key=lambda item: item[0], reverse=True)

    return [
        {
            "chunk_id": str(row.id),
            "skill_id": row.skill_id,
            "phase": row.phase,
            "technique_id": row.technique_id,
            "doc_type": row.doc_type,
            "content": row.content,
            "score": score,
        }
        for score, row in scored[: query.top_k]
    ]
