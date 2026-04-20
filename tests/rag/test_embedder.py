from __future__ import annotations

from types import SimpleNamespace

import pytest

from backend.shared.config import settings
from scripts.rag.chunker import DocumentChunk
from scripts.rag.embedder import _embed_batch, embed_chunks


class _FakeEmbeddingsClient:
    def __init__(self, dimension: int, fail_once: bool = False) -> None:
        self.dimension = dimension
        self.fail_once = fail_once
        self.calls = 0

    async def create(self, *, model: str, input: list[str]):  # noqa: A002
        self.calls += 1
        if self.fail_once and self.calls == 1:
            raise RuntimeError("429")
        data = [SimpleNamespace(embedding=[0.1] * self.dimension) for _ in input]
        return SimpleNamespace(data=data)


class _FakeOpenAIClient:
    def __init__(self, embeddings_client: _FakeEmbeddingsClient) -> None:
        self.embeddings = embeddings_client


def _make_chunks(count: int) -> list[DocumentChunk]:
    return [
        DocumentChunk(
            skill_id="drawing",
            phase="fundamentals",
            technique_id=None,
            doc_type="tutorial",
            source_path="drawing/fundamentals__tutorial.txt",
            chunk_index=index,
            content=f"chunk {index}",
            token_count=20,
        )
        for index in range(count)
    ]


@pytest.mark.asyncio
async def test_chunks_are_batched(monkeypatch: pytest.MonkeyPatch) -> None:
    tracker = _FakeEmbeddingsClient(dimension=settings.embedding_dimension)

    def _factory(api_key: str):
        del api_key
        return _FakeOpenAIClient(tracker)

    monkeypatch.setattr("scripts.rag.embedder.AsyncOpenAI", _factory)
    monkeypatch.setattr("scripts.rag.embedder.settings.embedding_batch_size", 100)

    chunks = _make_chunks(205)
    output = await embed_chunks(chunks)

    assert len(output) == 205
    assert tracker.calls == 3


@pytest.mark.asyncio
async def test_retry_fires_on_temporary_error() -> None:
    client = _FakeOpenAIClient(_FakeEmbeddingsClient(dimension=settings.embedding_dimension, fail_once=True))
    vectors = await _embed_batch(client, ["a", "b"])
    assert len(vectors) == 2


@pytest.mark.asyncio
async def test_dimension_validation_raises_value_error(monkeypatch: pytest.MonkeyPatch) -> None:
    tracker = _FakeEmbeddingsClient(dimension=768)

    def _factory(api_key: str):
        del api_key
        return _FakeOpenAIClient(tracker)

    monkeypatch.setattr("scripts.rag.embedder.AsyncOpenAI", _factory)

    with pytest.raises(ValueError):
        await embed_chunks(_make_chunks(1))


@pytest.mark.asyncio
async def test_return_length_matches_input(monkeypatch: pytest.MonkeyPatch) -> None:
    tracker = _FakeEmbeddingsClient(dimension=settings.embedding_dimension)

    def _factory(api_key: str):
        del api_key
        return _FakeOpenAIClient(tracker)

    monkeypatch.setattr("scripts.rag.embedder.AsyncOpenAI", _factory)

    chunks = _make_chunks(17)
    output = await embed_chunks(chunks)
    assert len(output) == len(chunks)
