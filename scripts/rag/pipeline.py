import argparse
import asyncio
import json
from pathlib import Path

from scripts.rag.chunker import chunk_document
from scripts.rag.document_loader import load_documents
from scripts.rag.embedder import embed_chunks
from scripts.rag.indexer import index_chunks


async def run_pipeline(
    skill_docs_dir: str,
    dry_run: bool = False,
    chunk_size: int = 512,
    overlap: int = 64,
    report_path: str | None = None,
) -> None:
    documents = load_documents(skill_docs_dir)
    all_chunks = []
    for document in documents:
        all_chunks.extend(chunk_document(document, chunk_size=chunk_size, overlap=overlap))

    summary = {
        "documents": len(documents),
        "chunks": len(all_chunks),
        "chunk_size": chunk_size,
        "chunk_overlap": overlap,
        "dry_run": dry_run,
    }

    print(f"Loaded {summary['documents']} docs, generated {summary['chunks']} chunks")
    if report_path:
        Path(report_path).write_text(json.dumps(summary, indent=2), encoding="utf-8")

    if dry_run:
        print("Dry run complete")
        return

    chunk_vectors = await embed_chunks(all_chunks)
    inserted = await index_chunks(chunk_vectors)
    print(f"Indexed {inserted} chunks")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--skill-docs-dir", default="data/skill_docs")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--chunk-size", type=int, default=512)
    parser.add_argument("--chunk-overlap", type=int, default=64)
    parser.add_argument("--report-path", default=None)
    args = parser.parse_args()
    asyncio.run(
        run_pipeline(
            skill_docs_dir=args.skill_docs_dir,
            dry_run=args.dry_run,
            chunk_size=args.chunk_size,
            overlap=args.chunk_overlap,
            report_path=args.report_path,
        )
    )
