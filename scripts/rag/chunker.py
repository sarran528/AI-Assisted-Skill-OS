from dataclasses import dataclass

from scripts.rag.document_loader import SourceDocument


@dataclass
class DocumentChunk:
    skill_id: str
    phase: str | None
    technique_id: str | None
    doc_type: str
    source_path: str
    chunk_index: int
    content: str
    token_count: int


def chunk_document(doc: SourceDocument, chunk_size: int = 512, overlap: int = 64) -> list[DocumentChunk]:
    words = doc.content.split()
    if not words:
        return []

    chunks: list[DocumentChunk] = []
    start = 0
    index = 0
    while start < len(words):
        end = min(len(words), start + chunk_size)
        snippet_words = words[start:end]
        if len(snippet_words) >= 10:
            chunks.append(
                DocumentChunk(
                    skill_id=doc.skill_id,
                    phase=doc.phase,
                    technique_id=doc.technique_id,
                    doc_type=doc.doc_type,
                    source_path=doc.source_path,
                    chunk_index=index,
                    content=" ".join(snippet_words),
                    token_count=len(snippet_words),
                )
            )
            index += 1

        if end == len(words):
            break
        start = max(0, end - overlap)

    return chunks
