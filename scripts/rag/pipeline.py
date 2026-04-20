from __future__ import annotations

import argparse
import asyncio

from backend.shared.db.engine import SessionLocal
from scripts.rag.chunker import chunk_document
from scripts.rag.document_loader import load_documents
from scripts.rag.embedder import embed_chunks
from scripts.rag.indexer import index_chunks


async def run_pipeline(skill_docs_dir: str, dry_run: bool = False) -> None:
    documents = load_documents(skill_docs_dir)
    print(f"Loaded {len(documents)} documents")

    all_chunks = []
    for doc in documents:
        chunks = chunk_document(doc)
        all_chunks.extend(chunks)
    print(f"Generated {len(all_chunks)} chunks")

    if dry_run:
        print("Dry run - skipping embedding and indexing")
        return

    chunks_with_embeddings = await embed_chunks(all_chunks)
    async with SessionLocal() as db:
        indexed = await index_chunks(db, chunks_with_embeddings)
    print(f"Indexed {indexed} chunks")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--skill-docs-dir", default="data/skill_docs")
    args = parser.parse_args()
    asyncio.run(run_pipeline(args.skill_docs_dir, args.dry_run))
