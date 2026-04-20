from __future__ import annotations

import tiktoken

from backend.shared.config import settings
from backend.rag.retriever import RetrievedChunk


def _source_label(chunk: RetrievedChunk) -> str:
    phase = chunk.phase or "cross_phase"
    return f"[Source: {chunk.skill_id} / {phase} / {chunk.doc_type}]"


def build_context_string(chunks: list[RetrievedChunk], max_tokens: int = 2000) -> str:
    if max_tokens <= 0:
        raise ValueError("max_tokens must be positive")

    encoding = tiktoken.encoding_for_model(settings.embedding_model)
    ordered = sorted(chunks, key=lambda chunk: chunk.similarity_score, reverse=True)

    budget = 0
    parts: list[str] = []

    for chunk in ordered:
        block = f"{_source_label(chunk)}\n{chunk.content.strip()}"
        block_tokens = len(encoding.encode(block))
        if budget + block_tokens > max_tokens:
            break
        parts.append(block)
        budget += block_tokens

    return "\n\n".join(parts)
