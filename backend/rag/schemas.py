from backend.shared.models import APIModel


class EmbeddingRequest(APIModel):
    text: str


class EmbeddingResponse(APIModel):
    embedding: list[float]


class RetrievalRequest(APIModel):
    query_text: str
    skill_id: str
    phase: str | None = None
    technique_id: str | None = None
    top_k: int = 5
    query_embedding: list[float] | None = None


class RetrievedChunk(APIModel):
    chunk_id: str
    skill_id: str
    phase: str | None
    technique_id: str | None
    doc_type: str
    content: str
    score: float | None = None


class RetrievalResponse(APIModel):
    chunks: list[RetrievedChunk]
