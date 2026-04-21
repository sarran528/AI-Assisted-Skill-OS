from dataclasses import dataclass


@dataclass
class RetrievalQuery:
    query_text: str
    skill_id: str
    phase: str | None
    technique_id: str | None
    top_k: int
    query_embedding: list[float] | None = None


def build_resource_query(skill_id: str, phase: str, user_query: str | None) -> RetrievalQuery:
    query_text = user_query or f"learning resources for {skill_id} {phase}"
    return RetrievalQuery(
        query_text=query_text,
        skill_id=skill_id,
        phase=phase,
        technique_id=None,
        top_k=5,
        query_embedding=None,
    )


def build_doubt_query(skill_id: str, phase: str, technique_id: str, user_question: str) -> RetrievalQuery:
    return RetrievalQuery(
        query_text=f"{user_question} {skill_id} {phase} {technique_id}",
        skill_id=skill_id,
        phase=phase,
        technique_id=technique_id,
        top_k=7,
        query_embedding=None,
    )


def build_tip_query(skill_id: str, technique_id: str, failure_type: str) -> RetrievalQuery:
    return RetrievalQuery(
        query_text=f"correction hint {technique_id} {failure_type}",
        skill_id=skill_id,
        phase=None,
        technique_id=technique_id,
        top_k=3,
        query_embedding=None,
    )
