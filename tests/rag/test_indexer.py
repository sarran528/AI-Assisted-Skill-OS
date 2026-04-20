from __future__ import annotations

import pytest

from scripts.rag.chunker import DocumentChunk
from scripts.rag.indexer import index_chunks


class _FakeSession:
    def __init__(self):
        self.executed = []
        self.committed = 0

    async def scalar(self, *args, **kwargs):
        del args, kwargs
        return None

    def add(self, obj):
        self.executed.append(obj)

    async def execute(self, stmt):
        self.executed.append(stmt)

    async def commit(self):
        self.committed += 1


@pytest.mark.asyncio
async def test_indexer_accepts_chunks_and_commits() -> None:
    db = _FakeSession()
    chunks = [
        (
            DocumentChunk(
                skill_id="drawing",
                phase="fundamentals",
                technique_id=None,
                doc_type="tutorial",
                source_path="drawing/fundamentals__tutorial.txt",
                chunk_index=0,
                content="chunk content",
                token_count=20,
            ),
            [0.1] * 1536,
        )
    ]

    count = await index_chunks(db, chunks)
    assert count == 1
    assert db.committed == 1
