from dataclasses import dataclass
from pathlib import Path


@dataclass
class SourceDocument:
    skill_id: str
    phase: str | None
    technique_id: str | None
    doc_type: str
    source_path: str
    content: str


def load_documents(skill_docs_dir: str) -> list[SourceDocument]:
    root = Path(skill_docs_dir)
    if not root.exists():
        return []

    documents: list[SourceDocument] = []
    for file in root.rglob("*"):
        if not file.is_file() or file.suffix.lower() not in {".txt", ".md"}:
            continue

        skill_id = file.parent.name
        stem_parts = file.stem.split("__", maxsplit=1)
        phase = None
        doc_type = "resource"
        if len(stem_parts) == 2:
            phase = None if stem_parts[0] == "cross_phase" else stem_parts[0]
            doc_type = stem_parts[1]

        documents.append(
            SourceDocument(
                skill_id=skill_id,
                phase=phase,
                technique_id=None,
                doc_type=doc_type,
                source_path=str(file),
                content=file.read_text(encoding="utf-8", errors="ignore"),
            )
        )

    return documents
