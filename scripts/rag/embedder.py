from __future__ import annotations

from collections.abc import Sequence

from openai import AsyncOpenAI
from tenacity import retry, stop_after_attempt, wait_exponential

from backend.shared.config import settings
from scripts.rag.chunker import DocumentChunk


@retry(stop=stop_after_attempt(3), wait=wait_exponential(min=1, max=10), reraise=True)
async def _embed_batch(client: AsyncOpenAI, inputs: Sequence[str]) -> list[list[float]]:
    response = await client.embeddings.create(
        model=settings.embedding_model,
        input=list(inputs),
    )
    vectors = [item.embedding for item in response.data]
    for vector in vectors:
        if len(vector) != settings.embedding_dimension:
            raise ValueError(
                f"Embedding dimension mismatch. expected={settings.embedding_dimension} got={len(vector)}"
            )
    return vectors


async def embed_chunks(chunks: list[DocumentChunk]) -> list[tuple[DocumentChunk, list[float]]]:
    if not chunks:
        return []

    client = AsyncOpenAI(api_key=settings.openai_api_key)
    result: list[tuple[DocumentChunk, list[float]]] = []

    for start in range(0, len(chunks), settings.embedding_batch_size):
        batch = chunks[start : start + settings.embedding_batch_size]
        vectors = await _embed_batch(client, [chunk.content for chunk in batch])
        result.extend(zip(batch, vectors, strict=True))

    return result
