from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from backend.shared.config import settings
from backend.shared.db.models import RagChunk, RagConfig
from scripts.rag.chunker import DocumentChunk


async def _ensure_rag_config(db: AsyncSession) -> None:
    config = await db.scalar(select(RagConfig).where(RagConfig.id == 1))

    now = datetime.now(timezone.utc)
    if config is None:
        db.add(
            RagConfig(
                id=1,
                model_name=settings.embedding_model,
                model_version="1",
                dimension=settings.embedding_dimension,
                chunk_size=512,
                chunk_overlap=64,
                last_indexed_at=now,
                updated_at=now,
            )
        )
        return

    if config.model_name != settings.embedding_model:
        raise ValueError(
            "RAG config model mismatch. "
            f"db={config.model_name} runtime={settings.embedding_model}. Re-index required."
        )
    if config.dimension != settings.embedding_dimension:
        raise ValueError(
            "RAG config dimension mismatch. "
            f"db={config.dimension} runtime={settings.embedding_dimension}."
        )

    config.last_indexed_at = now
    config.updated_at = now


async def index_chunks(
    db: AsyncSession,
    chunks_with_embeddings: list[tuple[DocumentChunk, list[float]]],
) -> int:
    if not chunks_with_embeddings:
        await _ensure_rag_config(db)
        await db.commit()
        return 0

    await _ensure_rag_config(db)

    payload = [
        {
            "skill_id": chunk.skill_id,
            "phase": chunk.phase,
            "technique_id": chunk.technique_id,
            "doc_type": chunk.doc_type,
            "source_url": chunk.source_path,
            "chunk_index": chunk.chunk_index,
            "content": chunk.content,
            "embedding": embedding,
            "model_name": settings.embedding_model,
            "token_count": chunk.token_count,
        }
        for chunk, embedding in chunks_with_embeddings
    ]

    stmt = insert(RagChunk).values(payload)
    stmt = stmt.on_conflict_do_update(
        index_elements=["skill_id", "source_url", "chunk_index"],
        set_={
            "content": stmt.excluded.content,
            "embedding": stmt.excluded.embedding,
            "model_name": stmt.excluded.model_name,
            "token_count": stmt.excluded.token_count,
            "phase": stmt.excluded.phase,
            "technique_id": stmt.excluded.technique_id,
            "doc_type": stmt.excluded.doc_type,
        },
    )
    await db.execute(stmt)
    await db.commit()
    return len(payload)
