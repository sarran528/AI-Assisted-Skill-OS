from __future__ import annotations

from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, Field


class RoadmapTechnique(BaseModel):
    technique_id: str
    name: str
    session_count: int
    protocol_steps: list[str]


class RoadmapCheckpoint(BaseModel):
    checkpoint_id: str
    description: str
    evidence_type: Literal["numeric", "artifact", "behavioral_log"]
    threshold: float
    pass_criteria: str


class RoadmapPhase(BaseModel):
    phase_slug: str
    competencies: list[str]
    techniques: list[RoadmapTechnique]
    checkpoints: list[RoadmapCheckpoint]
    estimated_weeks: int
    status: Literal["locked", "active", "completed"] = "locked"


class GeneratedRoadmap(BaseModel):
    skill_id: str
    user_id: UUID
    profile_version: int
    template_version: int
    parameters_id: UUID
    phases: dict[str, RoadmapPhase]
    total_estimated_weeks: int
    fingerprint: str
    generated_at: datetime


class RoadmapGenerateRequest(BaseModel):
    skill_id: str = Field(..., min_length=1, max_length=64)


class RoadmapGenerateResponse(BaseModel):
    job_id: str
    status: Literal["queued"] = "queued"


class RoadmapResponse(BaseModel):
    roadmap_id: UUID
    skill_id: str
    user_id: UUID
    structure: dict
    fingerprint: str
    status: str


class RoadmapVerifyResponse(BaseModel):
    valid: bool
    fingerprint: str
