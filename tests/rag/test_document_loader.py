from __future__ import annotations

from pathlib import Path

from scripts.rag.document_loader import load_documents


def test_txt_file_loads_correctly(tmp_path: Path) -> None:
    docs_dir = tmp_path / "skill_docs"
    drawing_dir = docs_dir / "drawing"
    drawing_dir.mkdir(parents=True)

    path = drawing_dir / "fundamentals__technique_guide.txt"
    path.write_text("line one\nline two", encoding="utf-8")

    documents = load_documents(str(docs_dir))
    assert len(documents) == 1
    assert documents[0].skill_id == "drawing"
    assert documents[0].content == "line one\nline two"


def test_filename_parsing_for_phase_and_doc_type(tmp_path: Path) -> None:
    docs_dir = tmp_path / "skill_docs"
    drawing_dir = docs_dir / "drawing"
    drawing_dir.mkdir(parents=True)

    path = drawing_dir / "fundamentals__technique_guide.txt"
    path.write_text("content", encoding="utf-8")

    document = load_documents(str(docs_dir))[0]
    assert document.phase == "fundamentals"
    assert document.doc_type == "technique_guide"


def test_cross_phase_filename_maps_to_none_phase(tmp_path: Path) -> None:
    docs_dir = tmp_path / "skill_docs"
    drawing_dir = docs_dir / "drawing"
    drawing_dir.mkdir(parents=True)

    path = drawing_dir / "cross_phase__resource.txt"
    path.write_text("resource content", encoding="utf-8")

    document = load_documents(str(docs_dir))[0]
    assert document.phase is None
    assert document.doc_type == "resource"


def test_unsupported_extension_is_skipped(tmp_path: Path) -> None:
    docs_dir = tmp_path / "skill_docs"
    drawing_dir = docs_dir / "drawing"
    drawing_dir.mkdir(parents=True)

    unsupported = drawing_dir / "fundamentals__technique_guide.csv"
    unsupported.write_text("ignored", encoding="utf-8")

    documents = load_documents(str(docs_dir))
    assert documents == []
