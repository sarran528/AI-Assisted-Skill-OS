from sqlalchemy import delete, insert

from backend.shared.db.engine import SessionLocal
from backend.shared.db.models.rag import RagChunk
from scripts.rag.chunker import DocumentChunk


async def index_chunks(chunks_with_embeddings: list[tuple[DocumentChunk, list[float]]]) -> int:
    if not chunks_with_embeddings:
        return 0

    async with SessionLocal() as session:
        sources = {chunk.source_path for chunk, _ in chunks_with_embeddings}
        if sources:
            await session.execute(delete(RagChunk).where(RagChunk.source_url.in_(list(sources))))

        inserted = 0
        for chunk, embedding in chunks_with_embeddings:
            await session.execute(
                insert(RagChunk).values(
                    skill_id=chunk.skill_id,
                    phase=chunk.phase,
                    technique_id=chunk.technique_id,
                    doc_type=chunk.doc_type,
                    source_url=chunk.source_path,
                    chunk_index=chunk.chunk_index,
                    content=chunk.content,
                    embedding=embedding,
                    model_name="hash-fallback",
                    token_count=chunk.token_count,
                )
            )
            inserted += 1
        await session.commit()
        return inserted
