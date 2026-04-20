from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import Field

from backend.shared.models import APIModel


class ResourceRequest(APIModel):
    skill_id: str
    phase: str
    user_query: str | None = None


class ResourceItemModel(APIModel):
    title: str
    content: str
    doc_type: str
    phase: str | None
    relevance_score: float


class ResourceResponseModel(APIModel):
    skill_id: str
    phase: str
    resources: list[ResourceItemModel]
    query_used: str


class DoubtAskRequest(APIModel):
    session_id: UUID | None = None
    user_question: str = Field(min_length=10, max_length=500)


class DoubtResponseModel(APIModel):
    question: str
    answer: str
    confidence: str
    caveat: str | None
    chunks_used: int
    session_context: dict[str, str | None]


class TipResponseModel(APIModel):
    session_id: UUID
    technique_id: str
    tip: str
    severity: str
    target_step: str | None
    failure_type: str
    generated_at: datetime


class TipPendingResponse(APIModel):
    tip_pending: bool
    session_id: UUID
