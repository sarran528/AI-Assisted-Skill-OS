from backend.shared.models import APIModel


class EmbeddingRequest(APIModel):
    text: str


class EmbeddingResponse(APIModel):
    embedding: list[float]
