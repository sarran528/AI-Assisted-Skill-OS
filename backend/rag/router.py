from fastapi import APIRouter, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from backend.rag.query_builder import RetrievalQuery
from backend.rag.retriever import retrieve_chunks
from backend.rag.schemas import EmbeddingRequest, EmbeddingResponse, RetrievalRequest, RetrievalResponse, RetrievedChunk
from backend.rag.service import embed_text
from backend.shared.db.session import get_db_session
from backend.shared.rate_limit import limiter

router = APIRouter()


@router.post("/embeddings", response_model=EmbeddingResponse)
@limiter.limit("5/minute")
async def create_embedding(request: Request, payload: EmbeddingRequest) -> EmbeddingResponse:
	embedding = await embed_text(payload.text)
	return EmbeddingResponse(embedding=embedding)


@router.post("/retrieve", response_model=RetrievalResponse)
@limiter.limit("30/minute")
async def retrieve(
	request: Request,
	payload: RetrievalRequest,
	db_session: AsyncSession = Depends(get_db_session),
) -> RetrievalResponse:
	query_embedding = payload.query_embedding
	if query_embedding is None:
		try:
			query_embedding = await embed_text(payload.query_text)
		except Exception:
			query_embedding = None

	query = RetrievalQuery(
		query_text=payload.query_text,
		skill_id=payload.skill_id,
		phase=payload.phase,
		technique_id=payload.technique_id,
		top_k=payload.top_k,
		query_embedding=query_embedding,
	)
	chunks = await retrieve_chunks(db_session, query)
	return RetrievalResponse(chunks=[RetrievedChunk(**chunk) for chunk in chunks])
