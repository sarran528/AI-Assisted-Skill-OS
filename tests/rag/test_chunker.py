from __future__ import annotations

import tiktoken

from backend.shared.config import settings
from scripts.rag.chunker import chunk_document
from scripts.rag.document_loader import SourceDocument


def _text_with_exact_tokens(token_count: int) -> str:
    encoding = tiktoken.encoding_for_model(settings.embedding_model)
    seed = "token budget generation sample " * 1000
    tokens = encoding.encode(seed)
    assert len(tokens) >= token_count
    return encoding.decode(tokens[:token_count])


def _make_document(text: str) -> SourceDocument:
    return SourceDocument(
        skill_id="drawing",
        phase="fundamentals",
        technique_id=None,
        doc_type="tutorial",
        source_path="drawing/fundamentals__tutorial.txt",
        content=text,
    )


def test_exact_512_tokens_produces_one_chunk() -> None:
    text = _text_with_exact_tokens(512)
    chunks = chunk_document(_make_document(text), chunk_size=512, overlap=64)
    assert len(chunks) == 1
    assert chunks[0].token_count == 512


def test_600_tokens_produces_two_chunks_with_overlap() -> None:
    encoding = tiktoken.encoding_for_model(settings.embedding_model)
    text = _text_with_exact_tokens(600)
    doc_tokens = encoding.encode(text)

    chunks = chunk_document(_make_document(text), chunk_size=512, overlap=64)
    assert len(chunks) == 2

    second_chunk_tokens = encoding.encode(chunks[1].content)
    assert second_chunk_tokens == doc_tokens[448:600]
    assert chunks[1].token_count == len(doc_tokens[448:600])


def test_short_chunks_are_filtered() -> None:
    text = _text_with_exact_tokens(9)
    chunks = chunk_document(_make_document(text), chunk_size=512, overlap=64)
    assert chunks == []


def test_empty_input_returns_no_chunks() -> None:
    chunks = chunk_document(_make_document(""), chunk_size=512, overlap=64)
    assert chunks == []


def test_token_count_matches_actual_count() -> None:
    encoding = tiktoken.encoding_for_model(settings.embedding_model)
    text = _text_with_exact_tokens(700)
    chunks = chunk_document(_make_document(text), chunk_size=512, overlap=64)

    for chunk in chunks:
        assert chunk.token_count == len(encoding.encode(chunk.content))
