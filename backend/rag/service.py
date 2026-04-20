import httpx

from backend.shared.config import settings


async def embed_text(text: str) -> list[float]:
    headers = {
        "Authorization": f"Bearer {settings.openai_api_key}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": settings.embedding_model,
        "input": text,
    }
    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.post("https://api.openai.com/v1/embeddings", headers=headers, json=payload)
        response.raise_for_status()
        data = response.json()
    return data["data"][0]["embedding"]
