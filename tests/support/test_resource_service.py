from __future__ import annotations

import json
from uuid import uuid4

import pytest

from backend.rag.retriever import RetrievedChunk
from backend.support.resource_service import get_resources


class _FakeRedis:
    def __init__(self, cached: str | None = None) -> None:
        self.cached = cached
        self.writes = {}

    async def get(self, key: str):
        del key
        return self.cached

    async def set(self, key: str, value: str, ex: int):
        self.writes[key] = (value, ex)

    async def aclose(self):
        return None


def _chunk(text: str, score: float) -> RetrievedChunk:
    return RetrievedChunk(
        chunk_id=uuid4(),
        skill_id="drawing",
        phase="fundamentals",
        technique_id=None,
        doc_type="tutorial",
        content=text,
        similarity_score=score,
    )


@pytest.mark.asyncio
async def test_resource_response_from_retrieved_chunks(monkeypatch: pytest.MonkeyPatch) -> None:
    fake_redis = _FakeRedis()
    monkeypatch.setattr("backend.support.resource_service.Redis.from_url", lambda *args, **kwargs: fake_redis)

    async def _llm_should_not_run(*args, **kwargs):
        del args, kwargs
        raise AssertionError("LLM should not be called by resource service")

    monkeypatch.setattr(
        "backend.support.resource_service.llm_call",
        _llm_should_not_run,
        raising=False,
    )

    async def _retrieve(db, query):
        del db, query
        return [_chunk("resource 1", 0.91), _chunk("resource 2", 0.88)]

    monkeypatch.setattr("backend.support.resource_service.retrieve", _retrieve)

    response = await get_resources(
        db=None,
        skill_id="drawing",
        phase="fundamentals",
        user_query=None,
        current_user={"user": {"id": "u1"}},
    )

    assert len(response.resources) == 2
    assert response.resources[0].relevance_score == 0.91


@pytest.mark.asyncio
async def test_cache_hit_skips_retrieve(monkeypatch: pytest.MonkeyPatch) -> None:
    payload = json.dumps(
        {
            "skill_id": "drawing",
            "phase": "fundamentals",
            "query_used": "cached query",
            "resources": [
                {
                    "title": "cached",
                    "content": "cached content",
                    "doc_type": "resource",
                    "phase": None,
                    "relevance_score": 0.95,
                }
            ],
        }
    )
    fake_redis = _FakeRedis(cached=payload)
    monkeypatch.setattr("backend.support.resource_service.Redis.from_url", lambda *args, **kwargs: fake_redis)

    called = {"retrieve": False}

    async def _retrieve(*args, **kwargs):
        called["retrieve"] = True
        return []

    monkeypatch.setattr("backend.support.resource_service.retrieve", _retrieve)

    response = await get_resources(
        db=None,
        skill_id="drawing",
        phase="fundamentals",
        user_query=None,
        current_user={"user": {"id": "u1"}},
    )

    assert called["retrieve"] is False
    assert response.resources[0].title == "cached"
