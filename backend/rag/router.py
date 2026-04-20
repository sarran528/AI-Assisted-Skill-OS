from fastapi import APIRouter, Request

from backend.rag.schemas import EmbeddingRequest, EmbeddingResponse
from backend.rag.service import embed_text
from backend.shared.rate_limit import limiter

router = APIRouter()


@router.post("/embeddings", response_model=EmbeddingResponse)
@limiter.limit("5/minute")
async def create_embedding(request: Request, payload: EmbeddingRequest) -> EmbeddingResponse:
	embedding = await embed_text(payload.text)
	return EmbeddingResponse(embedding=embedding)
