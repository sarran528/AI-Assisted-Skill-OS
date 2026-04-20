from __future__ import annotations

from dataclasses import dataclass

import tiktoken

from backend.shared.config import settings
from scripts.rag.document_loader import SourceDocument


@dataclass(slots=True)
class DocumentChunk:
    skill_id: str
    phase: str | None
    technique_id: str | None
    doc_type: str
    source_path: str
    chunk_index: int
    content: str
    token_count: int


def chunk_document(
    doc: SourceDocument,
    chunk_size: int = 512,
    overlap: int = 64,
) -> list[DocumentChunk]:
    if chunk_size <= 0:
        raise ValueError("chunk_size must be positive")
    if overlap < 0:
        raise ValueError("overlap must be zero or positive")
    if overlap >= chunk_size:
        raise ValueError("overlap must be smaller than chunk_size")

    encoding = tiktoken.encoding_for_model(settings.embedding_model)
    tokens = encoding.encode(doc.content or "")
    if not tokens:
        return []

    step = chunk_size - overlap
    chunks: list[DocumentChunk] = []

    for chunk_index, start in enumerate(range(0, len(tokens), step)):
        token_slice = tokens[start : start + chunk_size]
        if not token_slice:
            break

        token_count = len(token_slice)
        content = encoding.decode(token_slice)

        if content.strip() and token_count >= 10:
            chunks.append(
                DocumentChunk(
                    skill_id=doc.skill_id,
                    phase=doc.phase,
                    technique_id=doc.technique_id,
                    doc_type=doc.doc_type,
                    source_path=doc.source_path,
                    chunk_index=chunk_index,
                    content=content,
                    token_count=token_count,
                )
            )

        if start + chunk_size >= len(tokens):
            break

    return chunks
