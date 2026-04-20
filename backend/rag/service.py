from backend.rag.embedder import embed_query


async def embed_text(text: str) -> list[float]:
    return await embed_query(text)
