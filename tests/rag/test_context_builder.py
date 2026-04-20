from __future__ import annotations

from uuid import uuid4

from backend.rag.context_builder import build_context_string
from backend.rag.retriever import RetrievedChunk


def _chunk(content: str, score: float, phase: str | None = "fundamentals") -> RetrievedChunk:
    return RetrievedChunk(
        chunk_id=uuid4(),
        skill_id="drawing",
        phase=phase,
        technique_id=None,
        doc_type="technique_guide",
        content=content,
        similarity_score=score,
    )


def test_chunks_are_ordered_by_similarity_desc() -> None:
    chunks = [
        _chunk("low", 0.71),
        _chunk("high", 0.95),
        _chunk("mid", 0.80),
    ]

    output = build_context_string(chunks, max_tokens=1000)
    assert output.find("high") < output.find("mid") < output.find("low")


def test_max_tokens_budget_is_respected() -> None:
    chunks = [_chunk("word " * 800, 0.99), _chunk("word " * 800, 0.98), _chunk("word " * 800, 0.97)]
    output = build_context_string(chunks, max_tokens=200)
    assert output.count("[Source:") <= 1


def test_output_contains_source_metadata_headers() -> None:
    output = build_context_string([_chunk("content", 0.9)], max_tokens=1000)
    assert "[Source: drawing / fundamentals / technique_guide]" in output
