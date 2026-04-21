import hashlib

from scripts.rag.chunker import DocumentChunk


def _hash_to_vector(text: str, dims: int = 1536) -> list[float]:
    digest = hashlib.sha256(text.encode("utf-8")).digest()
    values = [byte / 255.0 for byte in digest]
    vector: list[float] = []
    while len(vector) < dims:
        vector.extend(values)
    return vector[:dims]


async def embed_chunks(chunks: list[DocumentChunk]) -> list[tuple[DocumentChunk, list[float]]]:
    return [(chunk, _hash_to_vector(chunk.content)) for chunk in chunks]
