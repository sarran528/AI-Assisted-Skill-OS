from __future__ import annotations

from openai import AsyncOpenAI
from tenacity import retry, stop_after_attempt, wait_fixed

from backend.shared.config import settings
from backend.shared.errors import SystemError


@retry(stop=stop_after_attempt(2), wait=wait_fixed(1), reraise=True)
async def _embed_query_once(query_text: str) -> list[float]:
    client = AsyncOpenAI(api_key=settings.openai_api_key)
    response = await client.embeddings.create(
        model=settings.embedding_model,
        input=[query_text],
    )
    vector = response.data[0].embedding
    if len(vector) != settings.embedding_dimension:
        raise ValueError(
            f"Embedding dimension mismatch. expected={settings.embedding_dimension} got={len(vector)}"
        )
    return vector


async def embed_query(query_text: str) -> list[float]:
    try:
        return await _embed_query_once(query_text)
    except Exception as exc:  # pragma: no cover - specific SDK exceptions vary
        raise SystemError("embedding_failed", context={"provider": "openai"}) from exc
