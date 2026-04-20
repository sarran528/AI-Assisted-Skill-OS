from __future__ import annotations

from datetime import datetime
from uuid import UUID

from backend.shared.models import APIModel


class SessionStartRequest(APIModel):
    roadmap_id: UUID
    phase: str
    technique_id: str
    attempt_number: int = 1


class SessionStartResponse(APIModel):
    session_id: UUID
    status: str


class SessionMetricsRequest(APIModel):
    metrics: dict


class SessionCompleteRequest(APIModel):
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
