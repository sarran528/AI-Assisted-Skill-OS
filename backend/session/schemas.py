from __future__ import annotations

from typing import Any
from uuid import UUID

from pydantic import BaseModel


class SessionStartRequest(BaseModel):
    roadmap_id: UUID
    phase: str
    technique_id: str


class SessionMetricsRequest(BaseModel):
    session_id: UUID
    metrics: dict[str, Any]


class SessionCompleteRequest(BaseModel):
    session_id: UUID
    completed_steps: list[str]


class SessionResponse(BaseModel):
    session_id: UUID
    roadmap_id: UUID
    phase: str
    technique_id: str
    status: str
    failure_reason: str | None
    metrics_captured: dict[str, Any]
