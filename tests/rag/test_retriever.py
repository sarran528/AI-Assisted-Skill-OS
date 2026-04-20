from __future__ import annotations

from types import SimpleNamespace
from uuid import uuid4

import pytest

from backend.rag.retriever import RetrievalQuery, retrieve


class _FakeResult:
    def __init__(self, rows):
        self._rows = rows

    def fetchall(self):
        return self._rows


class _FakeAsyncSession:
    def __init__(self, rows):
        self.rows = rows
        self.params = None

    async def execute(self, sql, params):
        del sql
        self.params = params
        return _FakeResult(self.rows)


@pytest.mark.asyncio
async def test_filters_low_similarity_results(monkeypatch: pytest.MonkeyPatch) -> None:
    rows = [
        SimpleNamespace(
            id=uuid4(),
            skill_id="drawing",
            phase="fundamentals",
            technique_id=None,
            doc_type="tutorial",
            content="good",
            similarity_score=0.85,
        ),
        SimpleNamespace(
            id=uuid4(),
            skill_id="drawing",
            phase="fundamentals",
            technique_id=None,
            doc_type="tutorial",
            content="bad",
            similarity_score=0.65,
        ),
    ]
    db = _FakeAsyncSession(rows)
    async def _embed_query(_text: str) -> list[float]:
        return [0.1, 0.2, 0.3]

    monkeypatch.setattr("backend.rag.retriever.embed_query", _embed_query)

    query = RetrievalQuery(
        query_text="how to draw lines",
        skill_id="drawing",
        phase="fundamentals",
        technique_id=None,
        doc_type_filter=["tutorial"],
        top_k=5,
    )

    chunks = await retrieve(db, query)
    assert len(chunks) == 1
    assert chunks[0].content == "good"


@pytest.mark.asyncio
async def test_top_k_is_passed_to_sql(monkeypatch: pytest.MonkeyPatch) -> None:
    db = _FakeAsyncSession([])
    async def _embed_query(_text: str) -> list[float]:
        return [0.1, 0.2, 0.3]

    monkeypatch.setattr("backend.rag.retriever.embed_query", _embed_query)

    query = RetrievalQuery(
        query_text="python debugging",
        skill_id="python-basics",
        phase=None,
        technique_id=None,
        doc_type_filter=None,
        top_k=7,
    )
    await retrieve(db, query)

    assert db.params is not None
    assert db.params["top_k"] == 7
    assert db.params["skill_id"] == "python-basics"
