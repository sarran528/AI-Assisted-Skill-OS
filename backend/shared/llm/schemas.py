from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, field_validator, Field


class DoubtAnswerSchema(BaseModel):
    answer: str
    source_phases: list[str]
    confidence: Literal["high", "medium", "low"]
    caveat: str | None = None


class TipSchema(BaseModel):
    tip: str
    target_step: str | None
    severity: Literal["minor", "moderate", "critical"]

    @field_validator("tip")
    @classmethod
    def tip_max_words(cls, value: str) -> str:
        if len(value.split()) > 100:
            raise ValueError("tip must be 100 words or fewer")
        return value


class FeasibilityResult(BaseModel):
    """LLM output for skill feasibility analysis."""

    feasible: bool = Field(..., description="Whether the learner can acquire this skill")
    risk_level: Literal["low", "medium", "high"] = Field(..., description="Overall risk assessment")
    blockers: list[str] = Field(default_factory=list, description="Identified blocking factors")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Model confidence in this assessment")


class RiskItem(BaseModel):
    """Single risk identified by LLM."""

    dimension: str = Field(..., description="ProfileVector dimension affected")
    type: str = Field(..., description="Type of risk (e.g., 'motor_constraint', 'cognitive_overload')")
    severity: Literal["low", "medium", "high"] = Field(..., description="Risk severity level")


class RiskZoneResult(BaseModel):
    """LLM output for risk zone detection."""

    risks: list[RiskItem] = Field(default_factory=list, description="Identified risks")


class TimeModelResult(BaseModel):
    """LLM output for time modeling."""

    estimated_weeks: int = Field(..., ge=1, description="Total weeks to complete skill")
    hours_per_phase: dict[str, float] = Field(
        default_factory=dict, description="Estimated hours per phase"
    )
    confidence: float = Field(..., ge=0.0, le=1.0, description="Model confidence in time estimate")


class SkillModifierResult(BaseModel):
    """LLM output for skill-specific parameter modifiers."""

    technique_density_adjustment: float = Field(
        ..., description="Adjustment to technique_density (-0.3 to 0.3)"
    )
    repetition_boost: float = Field(
        ..., description="Adjustment to repetition_intensity (-0.3 to 0.3)"
    )
    notes: str = Field(default="", description="Reasoning for adjustments")

    @field_validator("technique_density_adjustment", "repetition_boost")
    @classmethod
    def clamp_modifier(cls, v: float) -> float:
        """Clamp modifiers to [-0.3, 0.3] range to handle LLM over-exuberance."""
        return max(-0.3, min(0.3, v))


# Conservative fallback instances for when LLM calls fail both attempts
DEFAULT_FEASIBILITY = FeasibilityResult(
    feasible=True, risk_level="medium", blockers=[], confidence=0.5
)

DEFAULT_RISK_ZONES = RiskZoneResult(risks=[])

DEFAULT_TIME_MODEL = TimeModelResult(estimated_weeks=12, hours_per_phase={}, confidence=0.3)

DEFAULT_SKILL_MODIFIERS = SkillModifierResult(
    technique_density_adjustment=0.0, repetition_boost=0.0, notes="Fallback defaults"
)
