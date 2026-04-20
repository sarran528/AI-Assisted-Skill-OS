"""
Pydantic models for skill template API requests and responses.
"""

from datetime import datetime
from uuid import UUID
from pydantic import BaseModel, Field


class SkillTemplateCreate(BaseModel):
    """Request model for creating a skill template."""
    
    skill_id: str = Field(..., min_length=1, max_length=64, description="Unique skill identifier")
    name: str = Field(..., min_length=5, max_length=128, description="Human-readable skill name")
    domain: str = Field(..., max_length=64, description="Domain category (art, music, programming, language, physical, other)")
    complexity_score: float = Field(..., ge=0.0, le=1.0, description="Complexity rating 0-1")
    structure: dict = Field(..., description="JSONB skill structure with phases, competencies, techniques, checkpoints")


class SkillTemplateUpdate(BaseModel):
    """Request model for updating a skill template."""
    
    name: str | None = Field(None, min_length=5, max_length=128)
    complexity_score: float | None = Field(None, ge=0.0, le=1.0)
    structure: dict | None = Field(None)


class SkillTemplateResponse(BaseModel):
    """Response model for skill template API."""
    
    id: UUID
    skill_id: str
    version: int
    name: str
    domain: str
    complexity_score: float
    structure: dict
    is_active: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class SkillListResponse(BaseModel):
    """Response model for skill list endpoint."""
    
    id: UUID
    skill_id: str
    name: str
    domain: str
    complexity_score: float
    version: int

    model_config = {"from_attributes": True}
