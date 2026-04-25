from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import Field

from backend.shared.models import APIModel


class ResourceRequest(APIModel):
    skill_id: str
    phase: str
    technique_id: str | None = None
    user_query: str | None = None


class ResourceItemModel(APIModel):
    title: str
    url: str | None = None
    doc_type: str


class ResourceResponseModel(APIModel):
    skill_id: str
    phase: str
    resources: list[ResourceItemModel]
    query_used: str


class DoubtAskRequest(APIModel):
    session_id: UUID | None = None
    phase: str | None = None
    technique_id: str | None = None
    user_query: str = Field(min_length=10, max_length=500)


class DoubtResponseModel(APIModel):
    explanation: str
    sources_used: int


class TipResponseModel(APIModel):
    tip: str
    trigger_reason: str


class TipPendingResponse(APIModel):
    tip_pending: bool
    session_id: UUID
