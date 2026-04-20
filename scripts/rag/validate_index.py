from __future__ import annotations

import asyncio

from openai import AsyncOpenAI
from sqlalchemy import text

from backend.shared.config import settings
from backend.shared.db.engine import SessionLocal


def _format_vector(values: list[float]) -> str:
    return "[" + ",".join(str(value) for value in values) + "]"


async def get_test_embedding(query: str) -> list[float]:
    client = AsyncOpenAI(api_key=settings.openai_api_key)
    response = await client.embeddings.create(model=settings.embedding_model, input=[query])
    return response.data[0].embedding


async def validate_index() -> None:
    async with SessionLocal() as db:
        count = (await db.execute(text("SELECT COUNT(*) FROM rag_chunks"))).scalar_one()
        print(f"Total chunks: {count}")

        test_embedding = await get_test_embedding("basic drawing technique")
        results = (
            await db.execute(
                text(
                    "SELECT content FROM rag_chunks "
                    "ORDER BY embedding <=> CAST(:v AS vector) "
                    "LIMIT 3"
                ),
                {"v": _format_vector(test_embedding)},
            )
        ).fetchall()

        print(f"Test query returned {len(results)} results")
        for index, row in enumerate(results, start=1):
            snippet = (row.content or "").replace("\n", " ")[:100]
            print(f"  Result {index}: {snippet}...")


if __name__ == "__main__":
    asyncio.run(validate_index())
