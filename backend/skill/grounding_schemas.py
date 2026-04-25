"""Pydantic models for grounding probe requests and responses."""

from datetime import datetime
from uuid import UUID
from pydantic import BaseModel, Field


class RecognitionProbeResponse(BaseModel):
    """User's response to recognition probe items."""
    
    items: list[bool] = Field(
        ...,
        description="List of booleans: True if user marked item as familiar",
        min_items=1,
    )


class FamiliarityProbeResponse(BaseModel):
    """User's responses to familiarity MCQ items."""
    
    answers: list[int] = Field(
        ...,
        description="List of selected answer indices (0-based)",
        min_items=1,
    )


class ConfidenceProbeResponse(BaseModel):
    """User's self-reported confidence level."""
    
    level: int = Field(
        ...,
        ge=1,
        le=5,
        description="Self-rating: 1=never tried, 2=heard of, 3=understand basics, 4=can apply, 5=can teach",
    )


class GroundingProbeResponses(BaseModel):
    """Complete set of grounding probe responses for a skill."""
    
    skill_id: str = Field(..., description="Skill being grounded")
    recognition: RecognitionProbeResponse | None = Field(None, description="Recognition probe responses")
    familiarity: FamiliarityProbeResponse | None = Field(None, description="Familiarity probe responses")
    confidence: ConfidenceProbeResponse | None = Field(None, description="Confidence probe response")


class GroundingProbeSubmit(BaseModel):
    skill_id: str
    recognition_score: float = Field(..., ge=0.0, le=1.0)
    declarative_score: float = Field(..., ge=0.0, le=1.0)
    confidence_bias: float = Field(..., ge=0.0, le=5.0)


class BaselineStateResponse(BaseModel):
    skill_id: str
    exposure_score: float
    declarative_knowledge: float
    confidence_bias: float
    adjusted_repetition_intensity: float


class BaselineSkillStateResponse(BaseModel):
    """API response for baseline skill state."""
    
    id: UUID
    skill_id: str
    user_id: UUID
    exposure_score: float = Field(..., description="Recognition score 0-1")
    declarative_score: float = Field(..., description="Familiarity MCQ score 0-1")
    confidence_score: float = Field(..., description="Self-rating normalized 0-1")
    perceived_level: float = Field(..., description="Average of three scores 0-1")
    actual_level: float = Field(..., description="Profile cognitive_capacity 0-1")
    confidence_bias: float = Field(..., description="Perceived - actual, clamped [-1, 1]")
    created_at: datetime

    model_config = {"from_attributes": True}
