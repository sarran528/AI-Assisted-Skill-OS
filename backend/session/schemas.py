from __future__ import annotations

from datetime import datetime
from uuid import UUID

from backend.shared.models import APIModel


class SessionStartRequest(APIModel):
    roadmap_id: UUID | None = None
    skill_id: str | None = None
    phase: str
    technique_id: str
    attempt_number: int = 1


class SessionStartResponse(APIModel):
    session_id: UUID
    status: str


class SessionMetricsRequest(APIModel):
    session_id: UUID
    metrics: dict


class SessionCompleteRequest(APIModel):
    session_id: UUID
    completed_steps: list[str]


class SessionCompleteResponse(APIModel):
    session_id: UUID
    status: str
    passed: bool
    failure_reason: str | None
    tip_pending: bool
    tip_poll_url: str | None


class SessionStatusResponse(APIModel):
    session_id: UUID
    status: str
    phase: str
    technique_id: str
    attempt_number: int
    started_at: datetime | None
    ended_at: datetime | None


class SessionListItem(APIModel):
    session_id: UUID
    status: str
    phase: str
    score: float | None
    created_at: datetime | None


class SessionListResponse(APIModel):
    items: list[SessionListItem]
