from __future__ import annotations

from backend.rag.retriever import RetrievalQuery


def build_resource_query(skill_id: str, phase: str, user_query: str | None) -> RetrievalQuery:
    query_text = f"learning resources for {skill_id} {phase}"
    if user_query:
        query_text = f"{user_query} {skill_id} {phase}"

    return RetrievalQuery(
        query_text=query_text,
        skill_id=skill_id,
        phase=phase,
        technique_id=None,
        doc_type_filter=["tutorial", "resource"],
        top_k=5,
    )


def build_doubt_query(
    skill_id: str,
    phase: str | None,
    technique_id: str | None,
    user_question: str,
) -> RetrievalQuery:
    query_text = f"{user_question} {skill_id} {phase or ''} {technique_id or ''}".strip()

    return RetrievalQuery(
        query_text=query_text,
        skill_id=skill_id,
        phase=phase,
        technique_id=technique_id,
        doc_type_filter=None,
        top_k=7,
    )


def build_tip_query(skill_id: str, technique_id: str, failure_type: str) -> RetrievalQuery:
    query_text = f"correction hint {technique_id} {failure_type} common mistake fix"

    return RetrievalQuery(
        query_text=query_text,
        skill_id=skill_id,
        phase=None,
        technique_id=technique_id,
        doc_type_filter=["failure_analysis", "technique_guide"],
        top_k=3,
    )
